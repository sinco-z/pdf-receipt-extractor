from pdf2image import convert_from_path
from pdf2image import pdf2image as pdf2image_module
import cv2
import numpy as np
import os
from pypdf import PdfWriter, PdfReader
import subprocess
import sys

CONVERT_BATCH_SIZE = 50


def ensure_pdf2image_windows_subprocess_hidden():
    """在 Windows 下统一隐藏 pdf2image 内部拉起的 Poppler 控制台窗口。"""
    if sys.platform != "win32":
        return

    if getattr(pdf2image_module, "_hidden_popen_patched", False):
        return

    original_popen = pdf2image_module.Popen

    def hidden_popen(*args, **kwargs):
        startupinfo = kwargs.get("startupinfo")
        if startupinfo is None:
            startupinfo = subprocess.STARTUPINFO()

        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | getattr(
            subprocess, "CREATE_NO_WINDOW", 0
        )

        return original_popen(*args, **kwargs)

    pdf2image_module.Popen = hidden_popen
    pdf2image_module._hidden_popen_patched = True


def find_content_boundaries(gray_img):
    """
    分析图像内容来确定实际的内容边界
    返回内容的上下左右边界位置
    """
    # 使用Otsu's二值化方法
    _, binary = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 获取水平投影
    h_proj = np.sum(binary, axis=1)
    
    # 设置阈值，用于判断是否为内容
    h_threshold = np.max(h_proj) * 0.01
    
    # 查找内容边界
    height = gray_img.shape[0]
    top = 0
    bottom = height - 1
    
    # 从上往下找到第一个有内容的行
    for i in range(height):
        if h_proj[i] > h_threshold:
            top = max(0, i - 15)  # 增加额外空间
            break
            
    # 从下往上找到最后一个有内容的行
    for i in range(height - 1, -1, -1):
        if h_proj[i] > h_threshold:
            bottom = min(height - 1, i + 15)
            break
            
    return top, bottom

def process_pdf_with_opencv(input_pdf, output_path, progress_callback=None):
    """
    使用OpenCV处理PDF文件，检测并分割回执单，将所有回执单保存到一个PDF文件中
    
    Args:
        input_pdf: 输入PDF文件路径
        output_path: 输出PDF文件路径
        progress_callback: 进度回调函数，接收两个参数：(进度百分比, 状态描述)
    """
    if progress_callback:
        progress_callback(0, f"正在处理PDF: {input_pdf}")

    ensure_pdf2image_windows_subprocess_hidden()
    
    # 打开原始PDF文件
    pdf_reader = PdfReader(input_pdf)
    pdf_writer = PdfWriter()
    
    # 获取总页数
    total_pages = len(pdf_reader.pages)
    
    if progress_callback:
        progress_callback(1, f"总页数: {total_pages}")

    if sys.platform == "darwin":
        convert_kwargs = {"poppler_path": "/opt/homebrew/bin"}
    else:
        convert_kwargs = {}

    # 处理每一页
    total_receipts = 0
    for batch_start in range(0, total_pages, CONVERT_BATCH_SIZE):
        batch_end = min(batch_start + CONVERT_BATCH_SIZE, total_pages)

        if progress_callback:
            progress = int((batch_start / total_pages) * 98) + 1
            progress_callback(progress, f"正在转换第 {batch_start + 1}-{batch_end} 页图像")

        images = convert_from_path(
            input_pdf,
            dpi=100,
            first_page=batch_start + 1,
            last_page=batch_end,
            **convert_kwargs,
        )

        for page_offset, img in enumerate(images):
            page_num = batch_start + page_offset

            if progress_callback:
                progress = int((page_num / total_pages) * 98) + 1
                progress_callback(progress, f"正在处理第 {page_num + 1}/{total_pages} 页")

            # 获取原始页面
            original_page = pdf_reader.pages[page_num]

            # 获取PDF页面原始尺寸
            pdf_width = float(original_page.mediabox.width)
            pdf_height = float(original_page.mediabox.height)

            # 获取图像尺寸用于坐标转换
            img_height = img.size[1]

            # 转换为OpenCV格式
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

            # 转换为灰度图
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # 使用自适应阈值处理
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 25, 15
            )

            # 进行形态学操作
            kernel = np.ones((5,5), np.uint8)
            dilated = cv2.dilate(binary, kernel, iterations=2)
            eroded = cv2.erode(dilated, kernel, iterations=1)

            # 查找轮廓
            contours, hierarchy = cv2.findContours(
                eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # 调整最小区域面积的要求
            min_area = img.size[0] * img.size[1] * 0.05

            # 过滤并排序轮廓（按垂直位置）
            valid_contours = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if 0.05 <= h / img_height <= 0.6:
                        valid_contours.append((y, y + h))  # 只保存垂直位置

            # 按y坐标排序
            valid_contours.sort()

            # 如果没有找到有效的分割区域，保留整页
            if not valid_contours:
                pdf_writer.add_page(original_page)
                total_receipts += 1
                continue
            elif len(valid_contours) == 1:
                # 检查唯一的区域是否覆盖了大部分页面
                y_start, y_end = valid_contours[0]
                coverage = (y_end - y_start) / img_height
                if coverage > 0.7:  # 如果覆盖了70%以上的页面
                    pdf_writer.add_page(original_page)
                    total_receipts += 1
                    continue

            # 处理需要分割的页面
            total_receipts += len(valid_contours)

            if progress_callback:
                progress_callback(progress, f"第 {page_num + 1} 页找到 {len(valid_contours)} 个回执单")

            # 处理每个区域
            for idx, (y_start, y_end) in enumerate(valid_contours):
                # 提取当前区域的灰度图像
                roi_gray = gray[y_start:y_end, :]

                # 分析内容边界（只分析垂直方向）
                top, bottom = find_content_boundaries(roi_gray)

                # 计算最终的裁剪区域
                final_y = y_start + top
                final_h = bottom - top

                # 添加动态边距
                margin_ratio = 0.08
                margin_vertical = int(final_h * margin_ratio)

                final_y = max(0, final_y - margin_vertical)
                final_h = min(img_height - final_y, final_h + 2 * margin_vertical)

                # 将图像坐标转换为PDF坐标（PDF坐标系从底部开始）
                pdf_y = pdf_height - ((final_y + final_h) / img_height) * pdf_height
                pdf_h = (final_h / img_height) * pdf_height

                # 创建新页面并设置裁剪框
                new_page = pdf_reader.pages[page_num]
                new_page.cropbox.lower_left = (0, pdf_y)  # 使用原始PDF的完整宽度
                new_page.cropbox.upper_right = (pdf_width, pdf_y + pdf_h)

                # 添加裁剪后的页面
                pdf_writer.add_page(new_page)

                if progress_callback:
                    progress_callback(progress, f"添加第 {page_num + 1} 页的第 {idx + 1} 个回执单")

    # 保存合并后的PDF
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'wb') as output_file:
        pdf_writer.write(output_file)
    
    if progress_callback:
        progress_callback(100, f"已保存合并后的PDF文件: {output_path}")

def main():
    try:
        # 设置输入和输出路径
        input_pdf = "./receipts.pdf"
        output_pdf = "./output_opencv/merged_receipts.pdf"
        
        # 处理所有页面
        process_pdf_with_opencv(input_pdf, output_pdf)
        print("\n处理完成！")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 

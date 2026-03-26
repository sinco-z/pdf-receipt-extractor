import os
import sys

import cv2
import numpy as np
from pypdf import PdfReader, PdfWriter

try:
    import pymupdf as fitz
except ImportError:  # pragma: no cover - compatibility fallback
    import fitz


RENDER_DPI = 100


def find_content_boundaries(gray_img):
    """
    分析图像内容来确定实际的内容边界
    返回内容的上下左右边界位置
    """
    _, binary = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    h_proj = np.sum(binary, axis=1)
    h_threshold = np.max(h_proj) * 0.01

    height = gray_img.shape[0]
    top = 0
    bottom = height - 1

    for i in range(height):
        if h_proj[i] > h_threshold:
            top = max(0, i - 15)
            break

    for i in range(height - 1, -1, -1):
        if h_proj[i] > h_threshold:
            bottom = min(height - 1, i + 15)
            break

    return top, bottom


def pixmap_to_bgr_array(pixmap):
    """将 PyMuPDF 的 pixmap 转成 OpenCV 使用的 BGR 数组。"""
    channel_count = pixmap.n
    img = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height, pixmap.width, channel_count
    )

    if channel_count == 4:
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


def process_pdf_with_pymupdf(input_pdf, output_path, progress_callback=None):
    """
    使用 PyMuPDF 渲染页面，再用 OpenCV 检测并分割回执单。
    输出逻辑与原始 Poppler 版本保持一致。
    """
    if progress_callback:
        progress_callback(0, f"正在处理PDF: {input_pdf}")

    pdf_reader = PdfReader(input_pdf)
    pdf_writer = PdfWriter()
    render_doc = fitz.open(input_pdf)

    total_pages = len(pdf_reader.pages)
    if progress_callback:
        progress_callback(1, f"总页数: {total_pages}")

    total_receipts = 0
    for page_num in range(total_pages):
        if progress_callback:
            progress = int((page_num / total_pages) * 98) + 1
            progress_callback(progress, f"正在处理第 {page_num + 1}/{total_pages} 页")

        original_page = pdf_reader.pages[page_num]
        pdf_width = float(original_page.mediabox.width)
        pdf_height = float(original_page.mediabox.height)

        pixmap = render_doc.load_page(page_num).get_pixmap(dpi=RENDER_DPI, alpha=False)
        img_height = pixmap.height
        img_width = pixmap.width

        cv_img = pixmap_to_bgr_array(pixmap)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 15
        )

        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=2)
        eroded = cv2.erode(dilated, kernel, iterations=1)

        contours, hierarchy = cv2.findContours(
            eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        min_area = img_width * img_height * 0.05

        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                if 0.05 <= h / img_height <= 0.6:
                    valid_contours.append((y, y + h))

        valid_contours.sort()

        if not valid_contours:
            pdf_writer.add_page(original_page)
            total_receipts += 1
            continue
        elif len(valid_contours) == 1:
            y_start, y_end = valid_contours[0]
            coverage = (y_end - y_start) / img_height
            if coverage > 0.7:
                pdf_writer.add_page(original_page)
                total_receipts += 1
                continue

        total_receipts += len(valid_contours)

        if progress_callback:
            progress_callback(progress, f"第 {page_num + 1} 页找到 {len(valid_contours)} 个回执单")

        for idx, (y_start, y_end) in enumerate(valid_contours):
            roi_gray = gray[y_start:y_end, :]
            top, bottom = find_content_boundaries(roi_gray)

            final_y = y_start + top
            final_h = bottom - top

            margin_ratio = 0.08
            margin_vertical = int(final_h * margin_ratio)

            final_y = max(0, final_y - margin_vertical)
            final_h = min(img_height - final_y, final_h + 2 * margin_vertical)

            pdf_y = pdf_height - ((final_y + final_h) / img_height) * pdf_height
            pdf_h = (final_h / img_height) * pdf_height

            new_page = pdf_reader.pages[page_num]
            new_page.cropbox.lower_left = (0, pdf_y)
            new_page.cropbox.upper_right = (pdf_width, pdf_y + pdf_h)
            pdf_writer.add_page(new_page)

            if progress_callback:
                progress_callback(progress, f"添加第 {page_num + 1} 页的第 {idx + 1} 个回执单")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, "wb") as output_file:
        pdf_writer.write(output_file)

    render_doc.close()

    if progress_callback:
        progress_callback(100, f"已保存合并后的PDF文件: {output_path}")


def main():
    try:
        if len(sys.argv) >= 3:
            input_pdf = sys.argv[1]
            output_pdf = sys.argv[2]
        else:
            input_pdf = "./receipts.pdf"
            output_pdf = "./output_pymupdf/merged_receipts.pdf"

        process_pdf_with_pymupdf(input_pdf, output_pdf, progress_callback=print_progress)
        print("\n处理完成！")
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


def print_progress(value, text):
    print(f"[{value:>3}%] {text}")


if __name__ == "__main__":
    main()

import os
import sys
import subprocess

def check_environment():
    """检查并安装必要的依赖"""
    try:
        # 检查是否存在 requirements.txt
        if not os.path.exists('requirements.txt'):
            print("错误：未找到 requirements.txt 文件")
            sys.exit(1)
            
        # 安装依赖
        print("安装项目依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"安装依赖时出错：{e}")
        sys.exit(1)

# 先检查环境
check_environment()

import PyInstaller.__main__

def build_with_pyinstaller():
    """使用 PyInstaller 打包"""
    try:
        # 设置打包参数
        build_args = [
            'src/pdf_splitter_gui.py',  # 主程序文件
            '--name=PDF回执单分割工具',  # 程序名称
            '--noconsole',  # 不显示控制台
            '--clean',  # 清理临时文件
            '-y',  # 允许覆盖输出目录
            '--hidden-import=PIL._tkinter_finder',  # 添加隐藏导入
            '--hidden-import=pypdf',
            '--hidden-import=cv2',
            '--hidden-import=numpy',
            '--hidden-import=split_pdf_pymupdf',
            '--hidden-import=fitz',
            '--hidden-import=pymupdf',
        ]

        # Windows 默认使用单文件模式，便于分发和自用
        if sys.platform == 'win32':
            build_args.append('--onefile')

        # 如果存在图标文件，添加图标
        if os.path.exists('app_icon.ico'):
            build_args.extend(['--icon=app_icon.ico'])
        
        # 运行PyInstaller
        print("开始打包...")
        PyInstaller.__main__.run(build_args)

        print("\n打包完成！")
        if sys.platform == 'darwin':
            print("可执行文件位于: dist/PDF回执单分割工具.app")
        elif sys.platform == 'win32':
            print("可执行文件位于: dist/PDF回执单分割工具.exe")
        else:
            print("可执行文件位于: dist/PDF回执单分割工具")
            
    except Exception as e:
        print(f"打包过程出错：{e}")
        sys.exit(1)

if __name__ == '__main__':
    build_with_pyinstaller() 

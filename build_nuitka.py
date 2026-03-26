import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

def check_environment():
    """检查并安装必要的依赖"""
    try:
        if not os.path.exists('requirements.txt'):
            print("错误：未找到 requirements.txt 文件")
            sys.exit(1)
            
        print("安装项目依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"安装依赖时出错：{e}")
        sys.exit(1)

def build():
    """跨平台打包主函数"""
    check_environment()

    # 图标处理
    icon_path = None
    if sys.platform == "darwin":
        icon_path = "app_icon.icns"
        if not os.path.exists(icon_path):
            print("警告: 未找到macOS图标文件app_icon.icns")
            icon_path = None
    elif sys.platform == "win32":
        icon_path = "app_icon.ico"
        if not os.path.exists(icon_path):
            icon_path = None

    # 构建Nuitka命令
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--follow-imports",
        "--enable-plugin=pyside6",
        "--include-package=cv2",
        "--include-package=pypdf",
        "--include-package=numpy",
        "--include-package=PIL",
        "--include-package=fitz",
        "--include-package=pymupdf",
        "--jobs=4",
        "--remove-output",
        "--assume-yes-for-downloads",
    ]
    
    # 平台特定选项
    if sys.platform == "win32":
        cmd.extend([
            "--windows-disable-console",
            "--windows-company-name=YourCompany",
            "--windows-product-name=PDF回执单分割工具",
            "--windows-file-version=1.0.0",
            "--windows-product-version=1.0.0",
            "--windows-file-description=PDF回执单自动分割工具",
        ])
        if icon_path:
            cmd.append(f"--windows-icon-from-ico={icon_path}")
    elif sys.platform == "darwin":
        cmd.extend([
            "--macos-disable-console",
            "--macos-create-app-bundle",  # 关键参数：生成.app
            "--macos-app-name=PDF回执单分割工具",
            "--macos-app-version=1.0.0",
            "--macos-sign-identity=-",  # 允许临时签名
            "--macos-target-arch=arm64"  # M系列芯片需指定
        ])
        # 仅在存在有效图标时添加参数
        if icon_path and os.path.exists(icon_path):
            cmd.append(f"--macos-app-icon={icon_path}")  # 正确参数格式
    else:
        cmd.append("--disable-console")

    cmd.append("src/pdf_splitter_gui.py")
    
    try:
        print("开始编译...")
        subprocess.check_call(cmd)
        
        # 处理输出目录
        dist_dir = Path("dist")
        dist_dir.mkdir(exist_ok=True)
        
        build_dir = Path("pdf_splitter_gui.dist")
        if build_dir.exists():
            for item in build_dir.iterdir():
                dest = dist_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            shutil.rmtree(build_dir)
        
        # 清理构建缓存
        if sys.platform == "win32":
            for dir_name in ["__pycache__", "build"]:
                if os.path.exists(dir_name):
                    shutil.rmtree(dir_name)
        
        print(f"\n打包完成！输出目录: {dist_dir}")
        
    except subprocess.CalledProcessError as e:
        print(f"打包失败，错误码: {e.returncode}")
        print("建议检查：")
        print("1. 确保所有依赖已正确安装")
        print("2. 检查图标文件格式是否符合平台要求")
        print("3. 查看Nuitka文档获取更多调试信息")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform.startswith("linux"):
        print("警告：Linux打包可能需要额外依赖库")
    elif sys.platform == "darwin":
        print("提示：macOS打包建议使用专门图标格式")

    try:
        start_time = time.time()
        build()
        end_time = time.time()
        print(f"打包完成，用时: {end_time - start_time} 秒")
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)

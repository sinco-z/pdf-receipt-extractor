import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path
import time


def find_poppler_bin_dir():
    """返回包含 pdftoppm 可执行文件的目录。"""
    exe_name = "pdftoppm.exe" if sys.platform == "win32" else "pdftoppm"
    pdftoppm_path = shutil.which(exe_name)
    if pdftoppm_path:
        poppler_dir = os.path.dirname(os.path.abspath(pdftoppm_path))
        print(f"找到已安装的 Poppler: {poppler_dir}")
        return poppler_dir

    if sys.platform != "win32":
        return None

    raw_candidates = [
        os.path.expandvars(r"%ProgramFiles%\poppler"),
        os.path.expandvars(r"%ProgramFiles%\poppler\bin"),
        os.path.expandvars(r"%ProgramFiles(x86)%\poppler"),
        os.path.expandvars(r"%ProgramFiles(x86)%\poppler\bin"),
        os.path.expandvars(r"%LocalAppData%\poppler-windows"),
        os.path.expandvars(r"%LocalAppData%\poppler-windows\Library\bin"),
        r"C:\poppler",
        r"C:\poppler\bin",
        r"C:\Program Files\poppler",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler",
        r"C:\Program Files (x86)\poppler\bin",
    ]
    raw_candidates.extend(os.environ.get("PATH", "").split(os.pathsep))

    seen_paths = set()
    for raw_path in raw_candidates:
        candidate = raw_path.strip().strip('"')
        if not candidate:
            continue

        for path in (
            candidate,
            os.path.join(candidate, "bin"),
            os.path.join(candidate, "Library", "bin"),
        ):
            normalized = os.path.normpath(path)
            if normalized in seen_paths:
                continue
            seen_paths.add(normalized)

            pdftoppm_exe = os.path.join(normalized, "pdftoppm.exe")
            if os.path.exists(pdftoppm_exe):
                print(f"找到已安装的 Poppler: {normalized}")
                return normalized

    return None


def check_poppler_installed():
    """检查系统是否已安装 Poppler"""
    return find_poppler_bin_dir()

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

def download_poppler():
    """下载并配置 Poppler（仅Windows）"""
    existing_poppler = check_poppler_installed()
    if existing_poppler:
        return existing_poppler
        
    if sys.platform != "win32":
        print("错误：非Windows系统需要手动安装Poppler！")
        print("在macOS上使用: brew install poppler")
        print("在Linux上使用: sudo apt-get install poppler-utils")
        sys.exit(1)
        
    print("下载Windows版Poppler...")
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
    zip_path = "poppler-windows.zip"
    extract_path = "poppler-windows"
    
    try:
        if not os.path.exists(zip_path):
            urllib.request.urlretrieve(poppler_url, zip_path)
        
        if not os.path.exists(extract_path):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        
        # 新增：创建临时目录并复制必要文件
        temp_poppler_dir = "temp_poppler"
        if os.path.exists(temp_poppler_dir):
            shutil.rmtree(temp_poppler_dir)
        os.makedirs(temp_poppler_dir)
        
        src_bin_dir = os.path.join(extract_path, "poppler-24.08.0", "Library", "bin")
        print(f"复制Poppler文件到临时目录: {temp_poppler_dir}")
        for file in os.listdir(src_bin_dir):
            if file.endswith(('.dll', '.exe')):
                shutil.copy2(
                    os.path.join(src_bin_dir, file),
                    os.path.join(temp_poppler_dir, file)
                )
        
        return temp_poppler_dir  # 返回临时目录路径
    except Exception as e:
        print(f"Poppler配置失败: {e}")
        sys.exit(1)

def build():
    """跨平台打包主函数"""
    check_environment()
    
    temp_poppler = None
    
    # Poppler 检查（Windows自动下载）
    if sys.platform == "win32":
        temp_poppler = download_poppler()
    elif sys.platform == "darwin":
        if not check_poppler_installed():
            print("请通过Homebrew安装Poppler：brew install poppler")
            sys.exit(1)

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
        "--include-package=pdf2image",
        "--include-package=pypdf",
        "--include-package=numpy",
        "--include-package=PIL",
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
            f"--include-data-dir={temp_poppler}=poppler"
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
        
        # 清理Windows临时文件
        if sys.platform == "win32":
            # 保留原始zip文件，只删除解压目录和临时目录
            if os.path.exists("poppler-windows"):
                shutil.rmtree("poppler-windows")
            if temp_poppler and os.path.exists(temp_poppler):
                shutil.rmtree(temp_poppler)
            # 新增：清理可能的残留文件
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

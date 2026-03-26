# PDF Receipt Splitter

一个用于自动检测和分割 PDF 文件中回执单的工具。该工具使用 PyMuPDF 将 PDF 页面渲染为图像，配合 OpenCV 进行智能检测，并通过 PyPDF 进行高质量分割，保持原始 PDF 的清晰度和特性。

## 快速开始

### 预编译版本说明

如果某个版本附带了预编译包，可以在 [Releases](https://github.com/sinco-z/pdf-receipt-extractor/releases) 页面直接下载后解压使用。

当前仓库不保证每个 Release 都提供预编译包。当前默认仅提供 Windows 和 macOS 的打包产物；Linux 用户请优先参考下方的[安装说明](#安装说明)从源码运行，或自行执行打包脚本生成本地可执行文件。

### 从源码安装

如果您希望从源码安装，请参考下方的[安装说明](#安装说明)。

## 功能特点

- 自动检测 PDF 中的回执单区域
- 智能分割并保持原始 PDF 质量
  - 保留原始 PDF 的矢量文字和压缩特性
  - 保持文档的清晰度和小体积
  - 仅裁剪高度，保持原始宽度以确保内容完整
- 支持批量处理多个回执单
- 智能识别完整回执单，避免不必要的分割
- 直观的图形用户界面
- 跨平台支持 (Windows, macOS, Linux)

## 项目结构

```
pdf-receipt-splitter/
├── src/                    # 源代码
│   ├── pdf_splitter_gui.py # GUI界面
│   ├── split_pdf_pymupdf.py # PDF处理核心逻辑
├── run_windows.bat         # Windows 启动脚本
├── build_pyinstaller.py   # PyInstaller 打包脚本 (跨平台，体积小)
├── build_nuitka.py        # Nuitka 打包脚本 (性能优先，体积大)
├── requirements.txt       # 项目依赖
└── README.md             # 项目说明
```

## 安装说明

### 环境要求

- Python 3.10 或更高版本
- 操作系统：
  - Windows 10/11
  - macOS 11.0 或更高版本
  - Linux (Ubuntu 20.04+)

### 依赖安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/sinco-z/pdf-receipt-extractor.git
   cd pdf-receipt-extractor
   ```

2. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   .\\venv\\Scripts\\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用说明

1. 运行程序：
   ```bash
   python src/pdf_splitter_gui.py
   ```

2. 在程序界面中：
   - 点击"选择PDF文件"选择要处理的PDF
   - 点击"选择输出目录"选择保存位置
   - 点击"开始处理"开始处理

### 处理说明

程序会智能处理每个页面：
1. 自动检测页面中的回执单区域
2. 智能判断是否需要分割（对于完整回执单会保持原样）
3. 保持原始PDF质量进行分割
4. 生成体积小、清晰度高的输出文件

## 打包说明

### 使用 PyInstaller (跨平台，体积小)

```bash
python build_pyinstaller.py
```

Windows 下默认生成单文件 `dist/PDF回执单分割工具.exe`。

PyInstaller 运行后同时出现 `build` 和 `dist` 是正常现象：
- `dist` 是最终产物目录
- `build` 是中间构建目录，确认打包成功后可以删除

### 使用 Nuitka (性能优先，体积大)

```bash
python build_nuitka.py
```

当前脚本会将产物整理到 `dist` 目录下，而不是 `build` 目录。

### 发布新版本

1. 使用 PyInstaller 和 Nuitka 分别构建程序
2. 将生成的文件分别压缩：
   ```bash
   # Windows
   zip -r pdf-receipt-splitter-windows.zip dist/PDF回执单分割工具.exe

   # macOS
   ditto -c -k --sequesterRsrc --keepParent \
     dist/PDF回执单分割工具.app \
     dist/pdf-receipt-splitter-macos.zip

   ```
3. 视需要在 GitHub 创建新的 Release 并上传压缩包作为 Release assets

说明：
- 打包后的二进制文件体积较大，不建议直接提交到 Git 仓库历史中
- 是否上传到 GitHub Release assets 取决于发布策略；100MB 到 300MB 级别的桌面应用安装包是常见情况
- 如果某次 Release 未附带安装包，建议在 Release 说明中明确标注“仅发布源码”
- 当前建议仅上传 Windows 和 macOS 安装包
- macOS 的 `.app` 建议使用 `ditto` 打包，通常比直接对整个 `dist/` 目录执行 `zip` 更稳妥

## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (git checkout -b feature/AmazingFeature)
3. 提交您的更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- OpenCV 团队
- PyPDF 团队
- PySide6/Qt 团队
- PyMuPDF 团队

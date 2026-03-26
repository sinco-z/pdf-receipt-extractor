@echo off
cd /d "%~dp0"

if defined POPPLER_BIN (
    if exist "%POPPLER_BIN%\pdftoppm.exe" (
        set "PATH=%POPPLER_BIN%;%PATH%"
    )
)

if defined POPPLER_PATH (
    if exist "%POPPLER_PATH%\pdftoppm.exe" (
        set "PATH=%POPPLER_PATH%;%PATH%"
    ) else (
        if exist "%POPPLER_PATH%\Library\bin\pdftoppm.exe" (
            set "PATH=%POPPLER_PATH%\Library\bin;%PATH%"
        )
    )
)

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" src\pdf_splitter_gui.py
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py src\pdf_splitter_gui.py
    ) else (
        python src\pdf_splitter_gui.py
    )
)
if errorlevel 1 pause

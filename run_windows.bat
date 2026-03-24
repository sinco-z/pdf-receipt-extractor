@echo off
cd /d "%~dp0"

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

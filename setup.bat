@echo off
echo ╔══════════════════════════════════════════════════════════╗
echo ║          ArchForge Pro — Environment Setup               ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv

echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Setup complete!
echo.
echo To run the application:
echo   .venv\Scripts\activate
echo   python main.py
echo.
echo To build the executable:
echo   pyinstaller archforge.spec
echo.
pause

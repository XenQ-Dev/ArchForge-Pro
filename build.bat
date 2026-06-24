@echo off
setlocal
title ArchForge Pro — Build

echo.
echo  ================================================
echo   ARCHFORGE PRO  //  BUILD SCRIPT
echo  ================================================
echo.

:: Activate venv
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Could not activate .venv — run this from the project root.
    pause & exit /b 1
)

:: Install / upgrade PyInstaller
echo [1/3] Checking PyInstaller...
pip install --quiet --upgrade pyinstaller

echo.
echo [2/3] Building executable...
echo.

pyinstaller --noconfirm --clean --onedir --windowed ^
  --name "ArchForgePro" ^
  --icon "app/resources/images/icon.ico" ^
  --add-data "app/resources;app/resources" ^
  --hidden-import "matplotlib.backends.backend_qtagg" ^
  --hidden-import "PyQt6.QtSvg" ^
  --collect-submodules "matplotlib" ^
  --collect-submodules "sklearn" ^
  --collect-submodules "xgboost" ^
  main.py

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed — see output above.
    pause & exit /b 1
)

echo.
echo [3/3] Copying default data folder...
if not exist "dist\ArchForgePro\data" mkdir "dist\ArchForgePro\data"

echo.
echo  ================================================
echo   BUILD COMPLETE
echo   Output: dist\ArchForgePro\ArchForgePro.exe
echo  ================================================
echo.
echo  Test the build before creating an installer:
echo    dist\ArchForgePro\ArchForgePro.exe
echo.
pause
endlocal

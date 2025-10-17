@echo off
chcp 65001 >nul
echo ================================================
echo TS Translation Tool - Build Script
echo ================================================
echo.

REM Check if in virtual environment
if not defined VIRTUAL_ENV (
    echo [WARNING] Virtual environment not detected, recommended to build in venv
echo Activating virtual environment...
    if exist ".venv\Scripts\activate.bat" (
        call ".venv\Scripts\activate.bat"
        echo Virtual environment activated
    ) else (
        echo [ERROR] Virtual environment not found, please create first
        echo Use command:
        echo python -m venv .venv
        pause
        exit /b 1
    )
)

REM Check if PyInstaller is installed
python -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo [ERROR] PyInstaller installation failed
        pause
        exit /b 1
    )
    echo PyInstaller installed successfully
)

REM Create build directories
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM Clean previous builds
if exist "build\*" (
    echo Cleaning previous build files...
    rmdir /s /q build
    mkdir build
)

if exist "dist\*" (
    echo Cleaning previous output files...
    rmdir /s /q dist
    mkdir dist
)

echo.
echo ================================================
echo Starting application build...
echo ================================================
echo.

REM Set build parameters
set APP_NAME=TsTranslationHelper
set MAIN_FILE=gui_app.py
set ICON_FILE=
set ADD_DATA=styles.qss;.
set ADD_DATA2=example_en.ts;.
set ADD_DATA3=example_en_zh.ts;.

REM Build PyInstaller command
set PYINSTALLER_CMD=pyinstaller ^
    --name=%APP_NAME% ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --add-data "%ADD_DATA%" ^
    --add-data "%ADD_DATA2%" ^
    --add-data "%ADD_DATA3%" ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=argostranslate ^
    --hidden-import=argostranslate.package ^
    --hidden-import=argostranslate.translate ^
    --hidden-import=pandas ^
    --hidden-import=lxml.etree ^
    --hidden-import=lxml._elementpath ^
    --hidden-import=pathlib ^
    --hidden-import=logging ^
    --hidden-import=sys ^
    --hidden-import=os ^
    --hidden-import=typing ^
    %MAIN_FILE%

REM Execute build command
echo Executing build command...
echo %PYINSTALLER_CMD%
echo.

%PYINSTALLER_CMD%

if errorlevel 1 (
    echo [ERROR] Build failed, please check error messages
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build completed!
echo ================================================
echo.

REM Check generated executable
if exist "dist\%APP_NAME%.exe" (
    echo [SUCCESS] Executable generated: dist\%APP_NAME%.exe
    echo File size:
    for %%I in ("dist\%APP_NAME%.exe") do echo   %%~fI - %%~zI bytes
    
    echo.
    echo [INFO] Testing application...
    echo Press Ctrl+C to stop test run
    echo.
    
    REM Test run (optional)
    set /p "test_run=Test run application? (y/n): "
    if /i "%test_run%"=="y" (
        echo Starting application...
        timeout /t 2 >nul
        start "" "dist\%APP_NAME%.exe"
    )
) else (
    echo [ERROR] Executable generation failed
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build summary
echo ================================================
echo.
echo [DONE] Build process completed
echo.
echo Generated files:
echo   - dist\%APP_NAME%.exe (main program)
echo   - build\ (temporary build files, can be deleted)
echo.
echo Usage instructions:
echo   1. Copy dist\%APP_NAME%.exe to any location
echo   2. Program will create necessary config files and resources
echo   3. First run may require downloading translation models
echo.

REM Clean temporary files (optional)
set /p "cleanup=Clean temporary build files? (y/n): "
if /i "%cleanup%"=="y" (
    echo Cleaning temporary files...
    if exist "build" rmdir /s /q build
    if exist "%APP_NAME%.spec" del "%APP_NAME%.spec"
    echo Temporary files cleaned
)

echo.
echo Press any key to exit...
pause >nul
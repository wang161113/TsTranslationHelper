@echo off
chcp 65001 >nul
echo ========================================
echo    TS文件翻译工具 - 图形界面启动器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包安装情况...
python -c "import argostranslate" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到argostranslate包，正在尝试安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        echo 请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到PyQt5包，正在尝试安装...
    pip install PyQt5
    if errorlevel 1 (
        echo 错误: PyQt5安装失败
        echo 请手动运行: pip install PyQt5
        pause
        exit /b 1
    )
)

REM 检查翻译包
echo.
echo 检查翻译包...
python -c "
import argostranslate.package
import argostranslate.translate
packages = argostranslate.package.get_installed_packages()
if not packages:
    print('警告: 未安装任何翻译包')
    print('请运行以下命令安装翻译包:')
    print('argospm update')
    print('argospm install translate-en_zh')
else:
    print('已安装的翻译包:')
    for pkg in packages:
        print(f'  {pkg.from_code} -> {pkg.to_code}')
"

REM 启动图形界面
echo.
echo 启动图形界面...
python gui_app.py

if errorlevel 1 (
    echo.
    echo 错误: 图形界面启动失败
    echo 请检查错误信息并确保所有依赖已正确安装
    pause
    exit /b 1
)

echo.
echo 程序已退出
pause
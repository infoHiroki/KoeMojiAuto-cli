@echo off
echo =====================================
echo KoemojiAuto Installer for Windows
echo =====================================
echo.

:: Pythonの確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo.
    echo Please install Python 3.9 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python is installed.
echo.

:: pipの確認と更新
echo Updating pip...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to update pip. Continuing...
)

:: インストーラ実行
echo Starting dependency installer...
echo.
python install_dependencies.py

echo.
echo =====================================
echo Installation process completed.
echo =====================================
echo.
echo To start KoemojiAuto, run:
echo   tui.bat
echo.
pause
    pause
    exit /b 1
)

echo Python is installed.
echo.

:: pipの確認と更新
echo Updating pip...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to update pip. Continuing...
)

:: インストーラ実行
echo Starting dependency installer...
echo.
python install_dependencies.py

echo.
echo =====================================
echo Installation process completed.
echo =====================================
echo.
echo To start KoemojiAuto, run:
echo   tui.bat
echo.
pause
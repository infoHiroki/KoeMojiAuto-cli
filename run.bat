@echo off
cd /d "%~dp0"
echo KOEMOJIAUTO Starting...

python koemoji.py
if errorlevel 1 (
    echo Error occurred while running koemoji.py
    pause
    exit /b 1
)

pause
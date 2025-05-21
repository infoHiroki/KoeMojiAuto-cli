@echo off
cd /d "%~dp0"
title KoeMoji
python koemoji.py
if errorlevel 1 (
    echo Error occurred. Press any key to exit.
    pause
)
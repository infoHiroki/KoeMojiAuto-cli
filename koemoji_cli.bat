@echo off
cd /d "%~dp0"
title KoeMojiAuto - Command Line Interface
python koemoji.py --cli
if errorlevel 1 (
    echo Error occurred. Press any key to exit.
    pause
)
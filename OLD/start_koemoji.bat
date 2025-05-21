@echo off
echo Starting KoemojiAuto...
start /b python "%~dp0main.py"
echo KoemojiAuto is now running in the background.
echo Check status: .\status_koemoji.bat
echo Stop: .\stop_koemoji.bat
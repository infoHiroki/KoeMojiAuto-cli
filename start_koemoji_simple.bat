@echo off
echo Starting KoemojiAuto...
start /b pythonw "%~dp0koemoji.py"
echo KoemojiAuto is now running in the background.
echo To check status or control: python koemoji.py --cli
echo To stop: python koemoji.py --stop
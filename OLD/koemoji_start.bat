@echo off
cd /d "%~dp0"
echo Starting KoemojiAuto...
start /b pythonw koemoji.py
echo KoemojiAuto is now running in the background.
echo To check status or control: python koemoji.py --cli
echo To stop: python koemoji.py --stop
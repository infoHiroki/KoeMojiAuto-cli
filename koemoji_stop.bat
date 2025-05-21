@echo off
cd /d "%~dp0"
echo Stopping KoemojiAuto...
python koemoji.py --stop
echo Stop signal sent. Program will terminate shortly.
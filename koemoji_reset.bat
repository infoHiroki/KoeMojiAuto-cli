@echo off
cd /d "%~dp0"
echo Resetting KoeMoji system state...
python koemoji.py --reset
echo Reset complete.
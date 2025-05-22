@echo off
timeout /t 1 /nobreak >nul
start "" koemoji_cli.bat
taskkill /F /FI "WINDOWTITLE eq KoeMoji*" /T >nul 2>&1
exit

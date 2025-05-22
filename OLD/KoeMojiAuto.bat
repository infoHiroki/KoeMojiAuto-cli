@echo off
echo Starting KoeMojiAuto WebUI...

:: Open browser after a delay
start /b cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:8080"

:: Start Python in the current window
echo Starting server...
echo To stop the server, press Ctrl+C or close this window.
python webui.py
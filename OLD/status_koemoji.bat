@echo off
echo KoemojiAuto Status
echo ==================

:: 停止フラグの確認
if exist stop_koemoji.flag (
    echo Status: Stopping (stop flag detected)
    goto :EOF
)

:: プロセスの確認
set RUNNING=0
for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo list ^| findstr "PID:"') do (
    wmic process %%p get commandline | findstr "main.py" > nul
    if not errorlevel 1 (
        echo Status: Running
        echo Process ID: %%p
        set RUNNING=1
    )
)

if %RUNNING% EQU 0 (
    echo Status: Not running
)
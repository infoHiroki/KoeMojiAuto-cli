@echo off
echo Stopping KoemojiAuto...

rem Create stop flag file
echo 1 > stop_koemoji.flag

echo Stop flag created.
echo Program will terminate in the next cycle (max 5 seconds)

timeout /t 5 /nobreak > nul
echo Done
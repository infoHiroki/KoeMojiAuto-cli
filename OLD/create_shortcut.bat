@echo off
echo Creating portable KoeMojiAuto shortcut...

:: Create VBScript file for shortcut creation
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\create_koemoji_shortcut.vbs"
echo Set shortcut = WshShell.CreateShortcut("%~dp0KoeMojiAuto.lnk") >> "%TEMP%\create_koemoji_shortcut.vbs"
echo shortcut.TargetPath = "cmd.exe" >> "%TEMP%\create_koemoji_shortcut.vbs"
echo shortcut.Arguments = "/c cd /d ""%~dp0"" && ""%~dp0KoeMojiAuto.bat""" >> "%TEMP%\create_koemoji_shortcut.vbs"
echo shortcut.WorkingDirectory = "%~dp0" >> "%TEMP%\create_koemoji_shortcut.vbs"
echo shortcut.IconLocation = "%~dp0static\icon.ico" >> "%TEMP%\create_koemoji_shortcut.vbs"
echo shortcut.Save >> "%TEMP%\create_koemoji_shortcut.vbs"

:: Run the VBScript file
cscript //nologo "%TEMP%\create_koemoji_shortcut.vbs"

:: Verify shortcut was created
if exist "%~dp0KoeMojiAuto.lnk" (
    echo SUCCESS: Portable shortcut created!
) else (
    echo ERROR: Failed to create portable shortcut.
)

echo.
echo Press any key to exit...
pause > nul
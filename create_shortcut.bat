@echo off
echo Creating portable KoeMoji shortcut...

:: Create VBScript file for shortcut creation
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\create_portable.vbs"
echo Set shortcut = WshShell.CreateShortcut("%~dp0KoeMoji.lnk") >> "%TEMP%\create_portable.vbs"
echo shortcut.TargetPath = "cmd.exe" >> "%TEMP%\create_portable.vbs"
echo shortcut.Arguments = "/c cd /d ""%~dp0"" && ""%~dp0run.bat""" >> "%TEMP%\create_portable.vbs"
echo shortcut.WorkingDirectory = "%~dp0" >> "%TEMP%\create_portable.vbs"
echo shortcut.IconLocation = "%~dp0icon.ico" >> "%TEMP%\create_portable.vbs"
echo shortcut.Save >> "%TEMP%\create_portable.vbs"

:: Run the VBScript file
cscript //nologo "%TEMP%\create_portable.vbs"

:: Verify shortcut was created
if exist "%~dp0KoeMoji.lnk" (
    echo SUCCESS!
) else (
    echo ERROR: Failed to create portable shortcut.
)

echo.
echo Press any key to exit...
pause > nul
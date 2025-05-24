@echo off
title KoeMoji Setup

echo ========================================
echo            KoeMoji Setup
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Installation failed
    echo Make sure Python and pip are installed
    pause
    exit /b 1
)

echo.
echo Creating folders...
if not exist "input" mkdir "input"
if not exist "output" mkdir "output"
if not exist "archive" mkdir "archive"

echo.
echo Creating config...
if not exist "config.json" (
    if exist "config.sample" (
        copy "config.sample" "config.json" >nul
    )
)

echo.
echo ========================================
echo          Setup Complete!
echo ========================================
echo.
pause

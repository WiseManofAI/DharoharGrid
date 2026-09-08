@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH.
    echo Install it from https://python.org (check "Add to PATH" during install^), then run this again.
    pause
    exit /b 1
)

python bootstrap.py
echo.
echo Bootstrap exited. Press any key to close this window.
pause >nul

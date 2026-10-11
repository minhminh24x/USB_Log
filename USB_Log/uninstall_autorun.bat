@echo off
setlocal
title Go Cai Dat Tu Dong Chay Cho USB Monitor

REM Kiem tra quyen Administrator va tu dong xin quyen UAC
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Dang yeu cau quyen Administrator...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Chuyen vao thu muc chua script
cd /d "%~dp0"

REM Thuc thi script PowerShell go cai dat
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall_autorun_pc.ps1"

echo.
pause

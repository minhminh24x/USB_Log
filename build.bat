@echo off
setlocal enabledelayedexpansion
title Bien Dich USB_Monitor.exe

echo ==========================================================
echo        TRINH BIEN DICH USB_MONITOR (PORTABLE BUILDER)
echo ==========================================================
echo.

REM 1. Kiem tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] LOI: Khong tim thay Python! Vui long cai dat Python 3.10 tro len.
    pause
    exit /b 1
)

echo [*] Python da san sang.
echo [*] Dang kiem tra thu vien PyInstaller...
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Dang cai dat PyInstaller...
    pip install pyinstaller
)

REM 2. Tao thu muc USB_Log neu chua co
if not exist "USB_Log" mkdir "USB_Log"

REM 3. Tien hanh bien dich
echo.
echo [*] Dang bien dich usb_monitor.py thanh file USB_Monitor.exe doc lap...
echo [*]Che do: --onefile --noconsole (Chay ngam, khong hien console)
echo.

python -m PyInstaller --clean --onefile --noconsole --name USB_Monitor --distpath "USB_Log" --workpath "build" --specpath "." usb_monitor.py

if %errorlevel% neq 0 (
    echo.
    echo [X] BIEN DICH THAT BAI! Vui long kiem tra lai ma nguon.
    pause
    exit /b 1
)

echo.
echo ==========================================================
echo [i] BIEN DICH THANH CONG 100%!
echo ==========================================================
echo File chay duoc tao tai: USB_Log\USB_Monitor.exe
echo.
pause

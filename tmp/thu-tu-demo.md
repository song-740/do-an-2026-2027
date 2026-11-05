# 0. Máy mới

```txt
0. Bật ShareFolder
    E:\Tung_Dvan\DO-AN\VMwareSharedFolders
    \\vmware-host\Shared Folders
1. Tắt update
2. Tắt security
3. Để ps1 trên màn
4. Cài 7zip
5. Cấu hình địa chỉ IP
6. Sử dụng Edge
7. Bật on.ps1
8. Bật view file extention

SNAPSHOT - 
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```txt
Windows Security → Virus & threat protection → Manage settings → tắt Tamper Protection, tắt luôn Real-time protection, Cloud-delivered protection và Automatic sample submission.
=====================================================================
gpedit.msc
Computer Configuration → Administrative Templates → Windows Components → Microsoft Defender Antivirus
Turn off Microsoft Defender Antivirus → Enabled
Vào thư mục Real-time Protection → Turn off real-time protection → Enabled
=====================================================================
Computer Configuration → Administrative Templates → Windows Components → File Explorer → Configure Windows Defender SmartScreen → Disabled
Computer Configuration → Administrative Templates → Windows Components → Microsoft Edge → Configure Windows Defender SmartScreen → Disabled
=====================================================================
gpupdate /force
```

```ps1
# Tự động yêu cầu quyền Administrator nếu chưa chạy dưới quyền Admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Dang khoi chay lai voi quyen Administrator..." -ForegroundColor Yellow
    Start-Process powershell.exe -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $MyInvocation.MyCommand.Path)
    Exit
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   TIEN HANH TAT WINDOWS UPDATE CHO VM    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Dung va vo hieu hoa cac dich vu lien quan den Update
$services = @("wuauserv", "UsoSvc", "BITS", "dosvc")

foreach ($svc in $services) {
    if (Get-Service -Name $svc -ErrorAction SilentlyContinue) {
        Write-Host "Dang xu ly dich vu: $svc..." -ForegroundColor Green
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
        Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
        sc.exe failure $svc reset= 0 actions= "" | Out-Null
    }
}

# 2. Vo hieu hoa Windows Update Medic Service (WaaSMedicSvc) qua Registry
# (Dich vu nay thuong bi Windows chan lenh Set-Service truc tiep)
$waasPath = "HKLM:\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc"
if (Test-Path $waasPath) {
    Write-Host "Dang vo hieu hoa Windows Update Medic Service (WaaSMedicSvc)..." -ForegroundColor Green
    Set-ItemProperty -Path $waasPath -Name "Start" -Value 4 -Type DWord
}

# 3. Thiet lap chinh sach chan Update trong Registry (tuong duong Group Policy)
$registryPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
if (-not (Test-Path $registryPath)) {
    New-Item -Path $registryPath -Force | Out-Null
}

Write-Host "Dang ap dung chinh sach Group Policy chan cap nhat..." -ForegroundColor Green
# NoAutoUpdate = 1 (Vo hieu hoa cap nhat tu dong)
Set-ItemProperty -Path $registryPath -Name "NoAutoUpdate" -Value 1 -Type DWord
# AUOptions = 2 (Neu co thong bao thi chi bao chu khong tu tai)
Set-ItemProperty -Path $registryPath -Name "AUOptions" -Value 2 -Type DWord

# 4. Vo hieu hoa cac Scheduled Tasks lien quan den Update
Write-Host "Dang vo hieu hoa cac tac vu Update Orchestrator trong Task Scheduler..." -ForegroundColor Green
$taskPaths = @(
    "\Microsoft\Windows\WindowsUpdate\",
    "\Microsoft\Windows\UpdateOrchestrator\"
)

foreach ($path in $taskPaths) {
    Get-ScheduledTask -TaskPath $path -ErrorAction SilentlyContinue | ForEach-Object {
        Disable-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath -ErrorAction SilentlyContinue | Out-Null
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DA HOAN TAT TAT WINDOWS UPDATE THANH CONG!" -ForegroundColor Green
Write-Host "Ban nen chup Snapshot lai may ao tren VMware ngay bay gio." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Read-Host -Prompt "Nhan Enter de thoat"
```

</details>


# 1. Vô đổi tên Tools/rename-ps1.ps1.txt

```ps1
Set-ExecutionPolicy -Scope Process Bypass -Force
```

```ps1
cd C:\Tools
.\rename-ps1.ps1
```

# 2. Cài Sysmon, Wireshark, Systeminformer

Cài Sysmon:

```ps1
cd C:\Tools\Prepare\Sysmon
.\install-sysmon.ps1
.\..\expand-eventlogs.ps1
```

Cài Wireshark.

Cài Systeminformer.

# 3. Bật toàn bộ và kiểm tra

```ps1
& C:\Tools\Prepare\on.ps1
```

Tắt:

```ps1
& C:\Tools\Prepare\offall.ps1
```

Kiểm tra:

```ps1
& C:\Tools\Prepare\info.ps1
```

# 4. Xuất log PS1 và WMI

PS1:

```ps1
& C:\Tools\Prepare\export_powershell.ps1
```

WMI:

```ps1
& C:\Tools\Prepare\export_wmi.ps1
```


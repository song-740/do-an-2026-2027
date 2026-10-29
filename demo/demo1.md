| Nguồn log | Trạng thái | Dung lượng tối đa | Nội dung theo dõi |
| :--- | :--- | :--- | :--- |
| Sysmon Operational | Đã bật | 256 MB | Tiến trình, kết nối mạng, Registry, WMI, hoạt động liên quan bộ nhớ |
| PowerShell Operational | Đã bật | 128 MB | Script Block Logging, đặc biệt Event ID 4104 |
| WMI-Activity Operational | Đã bật | 32 MB | Hoạt động WMI |
| TaskScheduler Operational | Đã bật | 64 MB | Hoạt động Scheduled Task |

| Nguồn | Event ID | Ý nghĩa |
|---|---|---|
| Sysmon | 1 | Process Creation |
| Sysmon | 3 | Network Connection |
| Sysmon | 7 | Image Load |
| Sysmon | 8 | CreateRemoteThread |
| Sysmon | 10 | Process Access |
| Sysmon | 11 | File Create |
| Sysmon | 12, 13, 14 | Registry Events |
| Sysmon | 19, 20, 21 | WMI Events |
| PowerShell | 4104 | Script Block Logging |
| TaskScheduler | 106, 140, 200, 201 | Đăng ký, cập nhật và thực thi Task |

# 1. Script Block Logging 4104

## 1.1. Xóa hết các bản record log

Xóa log:

```ps1
wevtutil cl "Microsoft-Windows-PowerShell/Operational"
```

Tắt hoàn toàn cái Nhật ký (Log channel) PowerShell:

```ps1
wevtutil sl "Microsoft-Windows-PowerShell/Operational" /e:false
```

Tắt Script Block Logging:

```PS1
Set-ItemProperty `
  -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
  -Name "EnableScriptBlockLogging" `
  -Value 0 `
  -Type DWord
```

## 1.2. Kiểm tra và xem

Kiểm tra cấu hình Script Block Logging (bật:1-tắt:0):

```ps1
Get-ItemProperty `
  -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
  -ErrorAction SilentlyContinue |
Select-Object EnableScriptBlockLogging

```

Kiểm tra kênh ghi log:

```PS1
Get-WinEvent -ListLog "Microsoft-Windows-PowerShell/Operational" |
Select-Object LogName, IsEnabled, RecordCount
```

Xem nội dung log:

```PS1
$out = "C:\DFIR\Evidence\PowerShell\all_scripts_4104.txt"
New-Item -ItemType Directory -Path (Split-Path $out) -Force | Out-Null

Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-PowerShell/Operational"
    Id = 4104
} -ErrorAction SilentlyContinue |
Sort-Object RecordId |
ForEach-Object {
    "========== RecordId: $($_.RecordId) | Time: $($_.TimeCreated) =========="
    "ScriptBlockId: $($_.Properties[3].Value)"
    "Part: $($_.Properties[0].Value)/$($_.Properties[1].Value)"
    $_.Properties[2].Value
    ""
} | Out-File -FilePath $out -Encoding UTF8 -Width 10000

Write-Host "Da xuat: $out"
```

# 2. Task Scheduler Logging 

## 2.1. Kiểm tra Task Scheduler Logging có đang bật không

Bật Task Scheduler Logging:

```ps1
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:true
```

Tắt Task Scheduler Logging:

```ps1
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:false
```

Kiểm tra:

```ps1
Get-WinEvent -ListLog "Microsoft-Windows-TaskScheduler/Operational" |
Select-Object LogName, IsEnabled, RecordCount,
    @{N="MaxMB";E={[math]::Round($_.MaximumSizeInBytes / 1MB, 2)}} |
Format-List
```

## 2.2. Xóa hết tất cả các Record cũ

```ps1
wevtutil clear-log "Microsoft-Windows-TaskScheduler/Operational"
```

## 2.3. Kiểm tra có task APT29 không

Kiểm tra cấu hình thực thi của Scheduled Task:

```ps1
Get-ScheduledTask -TaskName "APT29LoginTask" -ErrorAction SilentlyContinue |
Select-Object -ExpandProperty Actions |
Format-List Execute, Arguments, WorkingDirectory
```

Truy vết lịch sử hoạt động của Scheduled Task:

```ps1
Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-TaskScheduler/Operational"
    Id = 106,140,200,201
} -ErrorAction SilentlyContinue |
Where-Object {
    $_.Message -match 'APT29LoginTask|login_handler\.ps1'
} |
Select-Object TimeCreated, Id, RecordId, Message |
Format-List 
```

# 3. Sysmon

## 3.1. Kiểm tra Sysmon có đang chạy hay không

Kiểm tra Sysmon có đang chạy hay không:

```ps1
Get-Service Sysmon64,Sysmon -ErrorAction SilentlyContinue |
Select-Object Name, Status, StartType
```

Kiểm tra log Sysmon có đang ghi hay không:

```ps1
Get-WinEvent -ListLog "Microsoft-Windows-Sysmon/Operational" |
Select-Object LogName, IsEnabled, RecordCount
```

Kiểm tra những Event ID đã xuất hiện:

```ps1
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
Group-Object Id |
Sort-Object Name |
Select-Object @{N="EventID";E={[int]$_.Name}}, Count |
Format-Table -AutoSize
```

Xóa sạch log từ Sysmon:

```ps1
wevtutil clear-log "Microsoft-Windows-Sysmon/Operational"
```

Tắt ghi log của Sysmon:

```ps1
wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:false
```

Bật ghi log của Sysmon:

```ps1
wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:true
```

# 4. WMI

## 4.1. Kiểm tra dịch vụ

Kiểm tra trạng thái dịch vụ Windows Management Instrumentation (WMI):

```ps1
Get-Service Winmgmt |
Select-Object Name, DisplayName, Status, StartType |
Format-List
```

Kiểm tra trạng thái và dung lượng nhật ký WMI-Activity:

```ps1
Get-WinEvent -ListLog "Microsoft-Windows-WMI-Activity/Operational" |
Select-Object LogName, IsEnabled, RecordCount,
    @{N="MaxMB";E={[math]::Round($_.MaximumSizeInBytes / 1MB, 2)}} |
Format-List
```

Tắt WMI-log:

```ps1
wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:false
```

Bật WMI-log:

```ps1
wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:true
```

Xóa các record:

```ps1
wevtutil clear-log "Microsoft-Windows-WMI-Activity/Operational"
```

## 4.2. Xem toàn bộ nội dung của WMI Log

Xuất sang file txt:

```ps1
$out = "C:\DFIR\Evidence\WMI\all_wmi_events.txt"

New-Item -ItemType Directory -Path (Split-Path $out) -Force | Out-Null

Get-WinEvent -LogName "Microsoft-Windows-WMI-Activity/Operational" |
Sort-Object RecordId |
ForEach-Object {
    "============================================"
    "TimeCreated: $($_.TimeCreated)"
    "EventId: $($_.Id)"
    "RecordId: $($_.RecordId)"
    "Level: $($_.LevelDisplayName)"
    ""
    $_.Message
    ""
} | Out-File -FilePath $out -Encoding UTF8 -Width 10000

Write-Host "Da xuat: $out"
```

Thống kê các Event ID đang có:

```ps1
Get-WinEvent -LogName "Microsoft-Windows-WMI-Activity/Operational" |
Group-Object Id |
Sort-Object Name |
Select-Object @{N="EventID";E={[int]$_.Name}}, Count |
Format-Table -AutoSize
```

# 5. BONUS: TẮT/BẬT/XÓA TOÀN BỘ TRƯỚC KHI NẮT ĐẦU THỰC NGHIỆM

## 5.1 Tắt và xóa log

```ps1
notepad C:\offall.ps1
```

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force
& "C:\offall.ps1"
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
# ==============================================================================
# SCRIPT DON DEP LOG & TAT TINH NANG GIAM SAT (DANH CHO LAB)
# ==============================================================================

Write-Host "Dang tien hanh tat va xoa log..." -ForegroundColor Cyan

# 1. PowerShell (Script Block Logging & Log Channel)
Write-Host " -> Dang xu ly PowerShell/Operational (Script Block)..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-PowerShell/Operational" /e:false | Out-Null
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name "EnableScriptBlockLogging" -Value 0 -Type DWord -ErrorAction SilentlyContinue
wevtutil cl "Microsoft-Windows-PowerShell/Operational" | Out-Null

# 2. PowerShell (Module Logging - Event 4103)
Write-Host " -> Dang xu ly PowerShell/ModuleLogging (Event 4103)..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" -Name "EnableModuleLogging" -Value 0 -Type DWord -ErrorAction SilentlyContinue

# 3. PowerShell (Transcription - Ghi file text)
Write-Host " -> Dang xu ly PowerShell/Transcription (File text)..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" -Name "EnableTranscripting" -Value 0 -Type DWord -ErrorAction SilentlyContinue

# 4. Task Scheduler
Write-Host " -> Dang xu ly TaskScheduler/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:false | Out-Null
wevtutil clear-log "Microsoft-Windows-TaskScheduler/Operational" | Out-Null

# 5. Sysmon
Write-Host " -> Dang xu ly Sysmon/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:false | Out-Null
wevtutil clear-log "Microsoft-Windows-Sysmon/Operational" | Out-Null

# 6. WMI Activity
Write-Host " -> Dang xu ly WMI-Activity/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:false | Out-Null
wevtutil clear-log "Microsoft-Windows-WMI-Activity/Operational" | Out-Null

# ==============================================================================
# THONG BAO TREN CONSOLE (KHONG DUNG GUI)
# ==============================================================================

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "           DA HOAN TAT DON DEP LAB!               " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host " - PowerShell Log      : Da tat & Xoa" -ForegroundColor White
Write-Host " - ScriptBlockLogging  : Da tat (Registry = 0)" -ForegroundColor White
Write-Host " - ModuleLogging (4103): Da tat (Registry = 0)" -ForegroundColor White
Write-Host " - Transcription (TXT) : Da tat (Registry = 0)" -ForegroundColor White
Write-Host " - TaskScheduler Log   : Da tat & Xoa" -ForegroundColor White
Write-Host " - Sysmon Log          : Da tat & Xoa" -ForegroundColor White
Write-Host " - WMI-Activity Log    : Da tat & Xoa" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Ban co the bat dau phien test moi.`n" -ForegroundColor Green
```

```PS1
# powershell

wevtutil sl "Microsoft-Windows-PowerShell/Operational" /e:false
Set-ItemProperty `
  -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
  -Name "EnableScriptBlockLogging" `
  -Value 0 `
  -Type DWord

wevtutil cl "Microsoft-Windows-PowerShell/Operational"


# task scheduler

wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:false

wevtutil clear-log "Microsoft-Windows-TaskScheduler/Operational"

# sysmon

wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:false

wevtutil clear-log "Microsoft-Windows-Sysmon/Operational"

# WMI

wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:false

wevtutil clear-log "Microsoft-Windows-WMI-Activity/Operational"

```

</details>

## 5.2. Xem thông tin hệ thống hiện tại

Hiện thị hệ thống hiện tại:

```ps1
notepad C:\info.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>


```ps1

# ============================================================
# DFIR LOGGING STATUS - WINDOWS 10
# READ ONLY - SAFE REGISTRY CHECKS
# NO CLEAR-HOST
# ============================================================

$ErrorActionPreference = "Continue"

$LogConfigs = @(
    @{
        Name = "Sysmon"
        LogName = "Microsoft-Windows-Sysmon/Operational"
        ExpectedMB = 256
        Service = "Sysmon64"
    },
    @{
        Name = "PowerShell"
        LogName = "Microsoft-Windows-PowerShell/Operational"
        ExpectedMB = 128
        Service = ""
    },
    @{
        Name = "WMI-Activity"
        LogName = "Microsoft-Windows-WMI-Activity/Operational"
        ExpectedMB = 32
        Service = "Winmgmt"
    },
    @{
        Name = "Task Scheduler"
        LogName = "Microsoft-Windows-TaskScheduler/Operational"
        ExpectedMB = 64
        Service = "Schedule"
    }
)

# ============================================================
# REGISTRY PATHS
# ============================================================

$PolicyRoot = "SOFTWARE\Policies\Microsoft\Windows\PowerShell"

$ScriptBlockKey = "$PolicyRoot\ScriptBlockLogging"
$ModuleKey      = "$PolicyRoot\ModuleLogging"
$ModuleNamesKey = "$ModuleKey\ModuleNames"
$TranscriptKey  = "$PolicyRoot\Transcription"

# ============================================================
# SAFE REGISTRY FUNCTIONS
# ============================================================

function Read-RegistryValue {
    param(
        [string]$KeyPath,
        [string]$ValueName
    )

    $Key = $null

    try {
        $Key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
            $KeyPath,
            $false
        )

        if ($null -eq $Key) {
            return [PSCustomObject]@{
                Exists = $false
                Value = $null
                Status = "NOT SET"
                Color = "Yellow"
            }
        }

        # Check property existence BEFORE reading its value.
        $ValueNames = @($Key.GetValueNames())

        if ($ValueNames -notcontains $ValueName) {
            return [PSCustomObject]@{
                Exists = $false
                Value = $null
                Status = "NOT SET"
                Color = "Yellow"
            }
        }

        $Value = $Key.GetValue($ValueName)

        if ($Value -eq 1) {
            return [PSCustomObject]@{
                Exists = $true
                Value = $Value
                Status = "1 (ENABLED)"
                Color = "Green"
            }
        }

        if ($Value -eq 0) {
            return [PSCustomObject]@{
                Exists = $true
                Value = $Value
                Status = "0 (DISABLED)"
                Color = "Red"
            }
        }

        return [PSCustomObject]@{
            Exists = $true
            Value = $Value
            Status = "$Value (OTHER)"
            Color = "Yellow"
        }
    }
    catch {
        return [PSCustomObject]@{
            Exists = $false
            Value = $null
            Status = "READ ERROR"
            Color = "Red"
        }
    }
    finally {
        if ($null -ne $Key) {
            $Key.Close()
        }
    }
}

function Read-RegistryText {
    param(
        [string]$KeyPath,
        [string]$ValueName
    )

    $Key = $null

    try {
        $Key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
            $KeyPath,
            $false
        )

        if ($null -eq $Key) {
            return "NOT SET"
        }

        if (@($Key.GetValueNames()) -notcontains $ValueName) {
            return "NOT SET"
        }

        $Value = $Key.GetValue($ValueName)

        if ([string]::IsNullOrWhiteSpace([string]$Value)) {
            return "EMPTY"
        }

        return [string]$Value
    }
    catch {
        return "READ ERROR"
    }
    finally {
        if ($null -ne $Key) {
            $Key.Close()
        }
    }
}

function Read-ModuleNames {
    param([string]$KeyPath)

    $Key = $null

    try {
        $Key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
            $KeyPath,
            $false
        )

        if ($null -eq $Key) {
            return "NOT CONFIGURED"
        }

        $Names = @(
            foreach ($Name in $Key.GetValueNames()) {
                $Value = $Key.GetValue($Name)

                if (-not [string]::IsNullOrWhiteSpace([string]$Value)) {
                    [string]$Value
                }
            }
        )

        if ($Names.Count -eq 0) {
            return "NOT CONFIGURED"
        }

        return ($Names -join ", ")
    }
    catch {
        return "READ ERROR"
    }
    finally {
        if ($null -ne $Key) {
            $Key.Close()
        }
    }
}

# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

function Get-StatusColor {
    param([string]$Status)

    switch ($Status) {
        "ON"    { return "Green" }
        "OK"    { return "Green" }
        "OFF"   { return "Red" }
        "ERROR" { return "Red" }
        "CHECK" { return "Yellow" }
        default { return "Gray" }
    }
}

function Write-Cell {
    param(
        [string]$Text,
        [int]$Width,
        [string]$Color = "White",
        [switch]$Right
    )

    if ($null -eq $Text) {
        $Text = "N/A"
    }

    if ($Text.Length -gt $Width) {
        $Text = $Text.Substring(0, $Width)
    }

    if ($Right) {
        $Formatted = $Text.PadLeft($Width)
    }
    else {
        $Formatted = $Text.PadRight($Width)
    }

    Write-Host $Formatted -ForegroundColor $Color -NoNewline
    Write-Host "  " -NoNewline
}

function Write-RegistryStatus {
    param(
        [string]$Label,
        [object]$Result
    )

    Write-Host ("  {0,-24}: " -f $Label) -NoNewline
    Write-Host $Result.Status -ForegroundColor $Result.Color
}

function Get-ServiceState {
    param([string]$ServiceName)

    $Service = Get-Service -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if ($Service -and $Service.Status -eq "Running") {
        return "ON"
    }

    return "OFF"
}

function Get-LogFileSizeMB {
    param([string]$LogName)

    try {
        $Output = & wevtutil.exe gl $LogName 2>$null

        if ($LASTEXITCODE -ne 0) {
            return $null
        }

        $Line = $Output |
            Where-Object {
                $_ -match '^\s*logFileName:\s*(.+)$'
            } |
            Select-Object -First 1

        if (-not $Line) {
            return $null
        }

        $Path = ($Line -replace '^\s*logFileName:\s*', '').Trim()
        $Path = [Environment]::ExpandEnvironmentVariables($Path)

        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            return $null
        }

        $File = Get-Item -LiteralPath $Path `
            -Force -ErrorAction SilentlyContinue

        if ($null -eq $File) {
            return $null
        }

        return [math]::Round($File.Length / 1MB, 2)
    }
    catch {
        return $null
    }
}

# ============================================================
# READ POWERSHELL LOGGING POLICIES
# ============================================================

$ScriptBlock = Read-RegistryValue `
    -KeyPath $ScriptBlockKey `
    -ValueName "EnableScriptBlockLogging"

$ModuleLogging = Read-RegistryValue `
    -KeyPath $ModuleKey `
    -ValueName "EnableModuleLogging"

$Transcription = Read-RegistryValue `
    -KeyPath $TranscriptKey `
    -ValueName "EnableTranscripting"

$InvocationHeader = Read-RegistryValue `
    -KeyPath $TranscriptKey `
    -ValueName "EnableInvocationHeader"

$ModuleList = Read-ModuleNames `
    -KeyPath $ModuleNamesKey

$TranscriptOutput = Read-RegistryText `
    -KeyPath $TranscriptKey `
    -ValueName "OutputDirectory"

$TranscriptFolderExists = "N/A"

if ($TranscriptOutput -notin @(
    "NOT SET",
    "EMPTY",
    "READ ERROR"
)) {
    $ExpandedPath = [Environment]::ExpandEnvironmentVariables(
        $TranscriptOutput
    )

    if (Test-Path -LiteralPath $ExpandedPath -PathType Container) {
        $TranscriptFolderExists = "YES"
    }
    else {
        $TranscriptFolderExists = "NO"
    }
}

# ============================================================
# COLLECT EVENT LOG INFORMATION
# ============================================================

$Results = @(
    foreach ($Item in $LogConfigs) {

        if ($Item.Name -eq "PowerShell") {
            $Feature = if ($ScriptBlock.Value -eq 1) {
                "ON"
            }
            else {
                "OFF"
            }
        }
        else {
            $Feature = Get-ServiceState $Item.Service
        }

        try {
            $Log = Get-WinEvent `
                -ListLog $Item.LogName `
                -ErrorAction Stop

            $MaxMB = [math]::Round(
                $Log.MaximumSizeInBytes / 1MB, 2
            )

            $UsedMB = Get-LogFileSizeMB $Item.LogName

            $Percent = $null

            if ($null -ne $UsedMB -and $MaxMB -gt 0) {
                $Percent = [math]::Round(
                    ($UsedMB / $MaxMB) * 100,
                    1
                )
            }

            [PSCustomObject]@{
                Source = $Item.Name
                Log = if ($Log.IsEnabled) { "ON" } else { "OFF" }
                Feature = $Feature
                Records = $Log.RecordCount
                UsedMB = $UsedMB
                MaxMB = $MaxMB
                Percent = $Percent
                Size = if ($MaxMB -eq $Item.ExpectedMB) {
                    "OK"
                }
                else {
                    "CHECK"
                }
                Error = ""
            }
        }
        catch {
            [PSCustomObject]@{
                Source = $Item.Name
                Log = "ERROR"
                Feature = $Feature
                Records = $null
                UsedMB = $null
                MaxMB = $null
                Percent = $null
                Size = "CHECK"
                Error = $_.Exception.Message
            }
        }
    }
)

# ============================================================
# DISPLAY TABLE - DO NOT CLEAR SCREEN
# ============================================================

$Width = 102

Write-Host ""
Write-Host "  DFIR LOGGING STATUS" -ForegroundColor Cyan

Write-Host ("  Check Time: " +
    (Get-Date -Format "yyyy-MM-dd HH:mm:ss")) `
    -ForegroundColor Yellow

Write-Host ("  " + ("=" * $Width)) -ForegroundColor DarkGray

Write-Host "  " -NoNewline

Write-Cell "SOURCE" 16 "Cyan"
Write-Cell "LOG" 7 "Cyan"
Write-Cell "FEATURE" 9 "Cyan"
Write-Cell "RECORDS" 12 "Cyan" -Right
Write-Cell "USED MB" 10 "Cyan" -Right
Write-Cell "MAX MB" 10 "Cyan" -Right
Write-Cell "USAGE" 8 "Cyan" -Right
Write-Cell "SIZE" 6 "Cyan"

Write-Host ""

Write-Host ("  " + ("-" * $Width)) -ForegroundColor DarkGray

foreach ($Row in $Results) {

    $RecordText = if ($null -ne $Row.Records) {
        "{0:N0}" -f $Row.Records
    }
    else {
        "N/A"
    }

    $UsedText = if ($null -ne $Row.UsedMB) {
        "{0:N2}" -f $Row.UsedMB
    }
    else {
        "N/A"
    }

    $MaxText = if ($null -ne $Row.MaxMB) {
        "{0:N0}" -f $Row.MaxMB
    }
    else {
        "N/A"
    }

    $PercentText = if ($null -ne $Row.Percent) {
        "{0:N1}%" -f $Row.Percent
    }
    else {
        "N/A"
    }

    $UsageColor = "Gray"

    if ($null -ne $Row.Percent) {
        if ($Row.Percent -ge 90) {
            $UsageColor = "Red"
        }
        elseif ($Row.Percent -ge 70) {
            $UsageColor = "Yellow"
        }
        else {
            $UsageColor = "Green"
        }
    }

    Write-Host "  " -NoNewline

    Write-Cell $Row.Source 16 "White"
    Write-Cell $Row.Log 7 (Get-StatusColor $Row.Log)
    Write-Cell $Row.Feature 9 (Get-StatusColor $Row.Feature)
    Write-Cell $RecordText 12 "White" -Right
    Write-Cell $UsedText 10 $UsageColor -Right
    Write-Cell $MaxText 10 "White" -Right
    Write-Cell $PercentText 8 $UsageColor -Right
    Write-Cell $Row.Size 6 (Get-StatusColor $Row.Size)

    Write-Host ""
}

Write-Host ("  " + ("=" * $Width)) -ForegroundColor DarkGray

# ============================================================
# POWERSHELL LOGGING REGISTRY
# ============================================================

Write-Host ""
Write-Host "  POWERSHELL LOGGING REGISTRY" -ForegroundColor Cyan
Write-Host ("  " + ("-" * 70)) -ForegroundColor DarkGray

Write-RegistryStatus "Script Block Logging" $ScriptBlock
Write-Host "  Registry Path           : HKLM:\$ScriptBlockKey"

Write-Host ""

Write-RegistryStatus "Module Logging" $ModuleLogging
Write-Host "  Registry Path           : HKLM:\$ModuleKey"
Write-Host "  Module Names            : $ModuleList"

Write-Host ""

Write-RegistryStatus "Transcription Logging" $Transcription
Write-RegistryStatus "Invocation Header" $InvocationHeader
Write-Host "  Registry Path           : HKLM:\$TranscriptKey"
Write-Host "  Output Directory        : $TranscriptOutput"

Write-Host "  Output Folder Exists    : " -NoNewline

switch ($TranscriptFolderExists) {
    "YES" {
        Write-Host "YES" -ForegroundColor Green
    }
    "NO" {
        Write-Host "NO" -ForegroundColor Yellow
    }
    default {
        Write-Host "N/A" -ForegroundColor Gray
    }
}

# ============================================================
# LOG QUERY ERRORS
# ============================================================

$ErrorsFound = @($Results | Where-Object { $_.Error })

if ($ErrorsFound.Count -gt 0) {

    Write-Host ""
    Write-Host "  LOG QUERY ERRORS" -ForegroundColor Red

    foreach ($Item in $ErrorsFound) {
        Write-Host "  $($Item.Source): $($Item.Error)" `
            -ForegroundColor Yellow
    }
}

# ============================================================
# LEGEND
# ============================================================

Write-Host ""
Write-Host "  ON / OK  " -ForegroundColor Green -NoNewline
Write-Host "= Enabled / Correct configuration"

Write-Host "  OFF      " -ForegroundColor Red -NoNewline
Write-Host "= Disabled"

Write-Host "  CHECK    " -ForegroundColor Yellow -NoNewline
Write-Host "= Maximum size differs from expected"

Write-Host ""
Write-Host "  FEATURE: Sysmon64 / Script Block Logging / Winmgmt / Schedule"
Write-Host "  USED MB: Physical EVTX file size"
Write-Host "  USAGE: Physical EVTX size / configured maximum"
Write-Host "  NOTE: Transcription output is separate from EVTX."
Write-Host ""

```

```ps1
# ==============================================================================
# SCRIPT CHI HIEN THI TRANG THAI LOG (READ-ONLY)
# ==============================================================================

$results = @()

# 1. PowerShell
$psLog = Get-WinEvent -ListLog "Microsoft-Windows-PowerShell/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "PowerShell/Operational"
    IsEnabled   = $psLog.IsEnabled
    RecordCount = $psLog.RecordCount
}

# 2. Task Scheduler
$tsLog = Get-WinEvent -ListLog "Microsoft-Windows-TaskScheduler/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "TaskScheduler/Operational"
    IsEnabled   = $tsLog.IsEnabled
    RecordCount = $tsLog.RecordCount
}

# 3. Sysmon
$sysLog = Get-WinEvent -ListLog "Microsoft-Windows-Sysmon/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "Sysmon/Operational"
    IsEnabled   = $sysLog.IsEnabled
    RecordCount = $sysLog.RecordCount
}

# 4. WMI Activity
$wmiLog = Get-WinEvent -ListLog "Microsoft-Windows-WMI-Activity/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "WMI-Activity/Operational"
    IsEnabled   = $wmiLog.IsEnabled
    RecordCount = $wmiLog.RecordCount
}

# 5. Script Block Logging (Registry)
$sblReg = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -ErrorAction SilentlyContinue
$sblValue = if ($null -ne $sblReg.EnableScriptBlockLogging) { $sblReg.EnableScriptBlockLogging } else { "N/A" }

# ==============================================================================
# HIEN THI KET QUA RA MAN HINH CONSOLE
# ==============================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "        KET QUA KIEM TRA TRANG THAI LOG           " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$results | Format-Table -AutoSize

Write-Host ""
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host " ScriptBlockLogging Registry Value : $sblValue" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\info.ps1"
```

## 5.3. Chỉ tắt không xóa log

```ps1
notepad C:\off.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
# ==============================================================================
# SCRIPT CHI TAT LOG (KHONG XOA DU LIEU CU)
# ==============================================================================

Write-Host "Dang tien hanh TAT cac log (giu nguyen du lieu cu)..." -ForegroundColor Cyan

# 1. PowerShell
Write-Host " -> Dang tat PowerShell/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-PowerShell/Operational" /e:false | Out-Null
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name "EnableScriptBlockLogging" -Value 0 -Type DWord -ErrorAction SilentlyContinue

# 2. Task Scheduler
Write-Host " -> Dang tat TaskScheduler/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:false | Out-Null

# 3. Sysmon
Write-Host " -> Dang tat Sysmon/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:false | Out-Null

# 4. WMI Activity
Write-Host " -> Dang tat WMI-Activity/Operational..." -ForegroundColor Yellow
wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:false | Out-Null

Write-Host "Hoan tat! Dang quet lai trang thai de kiem tra...`n" -ForegroundColor Green

# ==============================================================================
# LAY THONG TIN TRANG THAI THUC TE SAU KHI CHAY
# ==============================================================================

$results = @()

# 1. PowerShell
$psLog = Get-WinEvent -ListLog "Microsoft-Windows-PowerShell/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "PowerShell/Operational"
    IsEnabled   = $psLog.IsEnabled
    RecordCount = $psLog.RecordCount
}

# 2. Task Scheduler
$tsLog = Get-WinEvent -ListLog "Microsoft-Windows-TaskScheduler/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "TaskScheduler/Operational"
    IsEnabled   = $tsLog.IsEnabled
    RecordCount = $tsLog.RecordCount
}

# 3. Sysmon
$sysLog = Get-WinEvent -ListLog "Microsoft-Windows-Sysmon/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "Sysmon/Operational"
    IsEnabled   = $sysLog.IsEnabled
    RecordCount = $sysLog.RecordCount
}

# 4. WMI Activity
$wmiLog = Get-WinEvent -ListLog "Microsoft-Windows-WMI-Activity/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "WMI-Activity/Operational"
    IsEnabled   = $wmiLog.IsEnabled
    RecordCount = $wmiLog.RecordCount
}

# 5. Script Block Logging (Registry)
$sblReg = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -ErrorAction SilentlyContinue
$sblValue = if ($null -ne $sblReg.EnableScriptBlockLogging) { $sblReg.EnableScriptBlockLogging } else { "N/A" }

# ==============================================================================
# HIEN THI KET QUA RA MAN HINH CONSOLE
# ==============================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "        KET QUA KIEM TRA TRANG THAI LOG           " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$results | Format-Table -AutoSize

Write-Host ""
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host " ScriptBlockLogging Registry Value : $sblValue" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\off.ps1"
```

## 5.5. Clear log

```ps1
notepad C:\clear.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
# ==============================================================================
# SCRIPT CHI CLEAR LOG (KHONG TAT, KHONG SUA REGISTRY)
# ==============================================================================

Write-Host "Dang tien hanh xoa toan bo du lieu log..." -ForegroundColor Cyan

# 1. PowerShell
Write-Host " -> Dang xoa PowerShell/Operational..." -ForegroundColor Yellow
wevtutil cl "Microsoft-Windows-PowerShell/Operational" | Out-Null

# 2. Task Scheduler
Write-Host " -> Dang xoa TaskScheduler/Operational..." -ForegroundColor Yellow
wevtutil cl "Microsoft-Windows-TaskScheduler/Operational" | Out-Null

# 3. Sysmon
Write-Host " -> Dang xoa Sysmon/Operational..." -ForegroundColor Yellow
wevtutil cl "Microsoft-Windows-Sysmon/Operational" | Out-Null

# 4. WMI Activity
Write-Host " -> Dang xoa WMI-Activity/Operational..." -ForegroundColor Yellow
wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" | Out-Null

# 5. Security Log (Tùy chọn - Dành cho lab)
Write-Host " -> Dang xoa Security..." -ForegroundColor Yellow
wevtutil cl "Security" | Out-Null

# 6. System Log (Tùy chọn - Dành cho lab)
Write-Host " -> Dang xoa System..." -ForegroundColor Yellow
wevtutil cl "System" | Out-Null

# 7. Application Log (Tùy chọn - Dành cho lab)
Write-Host " -> Dang xoa Application..." -ForegroundColor Yellow
wevtutil cl "Application" | Out-Null

# ==============================================================================
# THONG BAO TREN CONSOLE
# ==============================================================================

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "           DA HOAN TAT XOA LOG!                   " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host " - Cac kenh log van dang BAT (IsEnabled = True)" -ForegroundColor White
Write-Host " - Du lieu log cu da bi xoa sach (RecordCount = 0)" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Green
```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\clear.ps1"
```

## 5.4. Bật toàn bộ trước khi thực nghiệm

```ps1
notepad C:\on.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
# ==============================================================================
# SCRIPT BAT LAI TOAN BO LOG & TINH NANG GIAM SAT (DANH CHO LAB)
# ==============================================================================

Write-Host "Dang tien hanh bat lai cac log va tinh nang giam sat..." -ForegroundColor Cyan

# 1. PowerShell (Log Channel & Script Block)
wevtutil sl "Microsoft-Windows-PowerShell/Operational" /e:true | Out-Null
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name "EnableScriptBlockLogging" -Value 1 -Type DWord -ErrorAction SilentlyContinue

# 2. PowerShell (Module Logging - Event 4103)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" -Name "EnableModuleLogging" -Value 1 -Type DWord -ErrorAction SilentlyContinue

# 3. PowerShell (Transcription - Ghi file text)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" -Name "EnableTranscripting" -Value 1 -Type DWord -ErrorAction SilentlyContinue

# 4. Task Scheduler
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:true | Out-Null

# 5. Sysmon
wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:true | Out-Null

# 6. WMI Activity
wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:true | Out-Null

Write-Host "Hoan tat! Dang quet lai trang thai de kiem tra...`n" -ForegroundColor Green

# ==============================================================================
# LAY THONG TIN TRANG THAI THUC TE SAU KHI CHAY
# ==============================================================================

$results = @()

# 1. PowerShell Log
$psLog = Get-WinEvent -ListLog "Microsoft-Windows-PowerShell/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "PowerShell/Operational"
    IsEnabled   = $psLog.IsEnabled
    RecordCount = $psLog.RecordCount
}

# 2. Task Scheduler Log
$tsLog = Get-WinEvent -ListLog "Microsoft-Windows-TaskScheduler/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "TaskScheduler/Operational"
    IsEnabled   = $tsLog.IsEnabled
    RecordCount = $tsLog.RecordCount
}

# 3. Sysmon Log
$sysLog = Get-WinEvent -ListLog "Microsoft-Windows-Sysmon/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "Sysmon/Operational"
    IsEnabled   = $sysLog.IsEnabled
    RecordCount = $sysLog.RecordCount
}

# 4. WMI Activity Log
$wmiLog = Get-WinEvent -ListLog "Microsoft-Windows-WMI-Activity/Operational" -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    LogName     = "WMI-Activity/Operational"
    IsEnabled   = $wmiLog.IsEnabled
    RecordCount = $wmiLog.RecordCount
}

# 5. Lay gia tri Registry cua 3 tinh nang PowerShell
$sblReg = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -ErrorAction SilentlyContinue
$modReg = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" -ErrorAction SilentlyContinue
$traReg = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" -ErrorAction SilentlyContinue

$sblValue = if ($null -ne $sblReg.EnableScriptBlockLogging) { $sblReg.EnableScriptBlockLogging } else { "N/A" }
$modValue = if ($null -ne $modReg.EnableModuleLogging) { $modReg.EnableModuleLogging } else { "N/A" }
$traValue = if ($null -ne $traReg.EnableTranscripting) { $traReg.EnableTranscripting } else { "N/A" }

# ==============================================================================
# HIEN THI KET QUA RA MAN HINH CONSOLE
# ==============================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "        KET QUA KIEM TRA TRANG THAI LOG           " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$results | Format-Table -AutoSize

Write-Host ""
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host " ScriptBlockLogging Registry Value : $sblValue" -ForegroundColor Yellow
Write-Host " ModuleLogging Registry Value      : $modValue" -ForegroundColor Yellow
Write-Host " Transcription Registry Value      : $traValue" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\on.ps1"
```

<!-- ## 5.5. Xem toàn bộ log của powershell.

```ps1
notepad & C:\read_powershell_logs.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
# =====================================================
# READ ALL POWERSHELL OPERATIONAL EVENT RECORDS
# READ ONLY - NO CHANGES
# =====================================================

$LogName = "Microsoft-Windows-PowerShell/Operational"

try {
    $Events = @(
        Get-WinEvent -LogName $LogName -Oldest -ErrorAction Stop
    )

    Write-Host ""
    Write-Host "========== POWERSHELL EVENT LOG ==========" -ForegroundColor Cyan
    Write-Host "Total records retrieved: $($Events.Count)" -ForegroundColor Yellow

    foreach ($Event in $Events) {
        Write-Host ""
        Write-Host ("=" * 85) -ForegroundColor DarkGray

        Write-Host "Record ID : " -NoNewline
        Write-Host $Event.RecordId -ForegroundColor Yellow

        Write-Host "Event ID  : " -NoNewline
        Write-Host $Event.Id -ForegroundColor Cyan

        Write-Host "Time      : $($Event.TimeCreated)"
        Write-Host "Provider  : $($Event.ProviderName)"
        Write-Host "Process ID: $($Event.ProcessId)"
        Write-Host "Level     : $($Event.LevelDisplayName)"

        Write-Host ""
        Write-Host "MESSAGE:" -ForegroundColor Green
        Write-Host $Event.Message
    }

    Write-Host ""
    Write-Host ("=" * 85) -ForegroundColor DarkGray
    Write-Host "Completed. Retrieved $($Events.Count) records." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
```

```ps1
& "C:\read_powershell_logs.ps1"
``` -->

## 5.6. Mốc thời gian demo

```ps1
notepad C:\demo_time.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1

# ============================================================
# DFIR DEMO TIME TRACKER
# Start / End / Duration
# ============================================================

$Root = "C:\DFIR\Logs"
$StateFile = Join-Path $Root "Demo_Start.json"
$CsvFile = Join-Path $Root "Demo_Timeline.csv"

if (-not (Test-Path $Root)) {
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
}

Write-Host ""
Write-Host "========== DFIR DEMO TIME TRACKER ==========" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. START DEMO" -ForegroundColor Green
Write-Host "2. END DEMO" -ForegroundColor Yellow
Write-Host "3. VIEW HISTORY" -ForegroundColor Cyan
Write-Host ""

$Choice = Read-Host "Select (1/2/3)"

switch ($Choice) {

    "1" {
        if (Test-Path $StateFile) {
            Write-Host "A demo is already running. End it first." -ForegroundColor Yellow
            break
        }

        $Now = Get-Date

        $State = [PSCustomObject]@{
            StartTime = $Now.ToString("o")
            Computer  = $env:COMPUTERNAME
        }

        $State | ConvertTo-Json |
            Set-Content -Path $StateFile -Encoding UTF8

        Write-Host ""
        Write-Host "DEMO STARTED" -ForegroundColor Green
        Write-Host "Start time: $($Now.ToString('yyyy-MM-dd HH:mm:ss.fff zzz'))"
    }

    "2" {
        if (-not (Test-Path $StateFile)) {
            Write-Host "No active demo found." -ForegroundColor Red
            break
        }

        $State = Get-Content $StateFile -Raw | ConvertFrom-Json

        $Start = [datetimeoffset]::Parse($State.StartTime)
        $End = [datetimeoffset]::Now
        $Duration = $End - $Start

        $Record = [PSCustomObject]@{
            Computer        = $State.Computer
            StartTime       = $Start.ToString("yyyy-MM-dd HH:mm:ss.fff zzz")
            EndTime         = $End.ToString("yyyy-MM-dd HH:mm:ss.fff zzz")
            DurationSeconds = [math]::Round($Duration.TotalSeconds, 3)
            Duration        = $Duration.ToString("dd\.hh\:mm\:ss\.fff")
        }

        $Record | Export-Csv -Path $CsvFile `
            -NoTypeInformation -Encoding UTF8 -Append

        Remove-Item $StateFile -Force

        Write-Host ""
        Write-Host "DEMO COMPLETED" -ForegroundColor Green
        $Record | Format-List
        Write-Host "Saved to: $CsvFile" -ForegroundColor Cyan
    }

    "3" {
        if (Test-Path $CsvFile) {
            Import-Csv $CsvFile |
                Format-Table Computer, StartTime, EndTime, DurationSeconds -AutoSize
        }
        else {
            Write-Host "No demo history found." -ForegroundColor Yellow
        }
    }

    default {
        Write-Host "Invalid option." -ForegroundColor Red
    }
}

```

</details>

```ps1
& "C:\demo_time.ps1"
```

# 6. Xuất log

## 6.1. Log Powershell 

```ps1
notepad C:\export_powershell.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1

# ============================================================
# DFIR - POWERSHELL OPERATIONAL FORENSIC LOG EXPORT
# Source : Microsoft-Windows-PowerShell/Operational
# Output : C:\DFIR\Logs\PowerShell
# Mode   : Read-only collection
# Windows PowerShell 5.1
# ============================================================

$ErrorActionPreference = "Stop"

$LogName = "Microsoft-Windows-PowerShell/Operational"
$RootDir = "C:\DFIR\Logs\PowerShell"

# ------------------------------------------------------------
# 1. CREATE COLLECTION DIRECTORY
# ------------------------------------------------------------

$CollectionTime = Get-Date
$Timestamp = $CollectionTime.ToString("yyyyMMdd_HHmmss")
$BaseName = "PowerShell_Operational_$Timestamp"

New-Item -ItemType Directory -Path $RootDir -Force |
    Out-Null

$OutputDir = Join-Path $RootDir $BaseName
$Counter = 1

while (Test-Path -LiteralPath $OutputDir) {
    $OutputDir = Join-Path $RootDir "${BaseName}_$Counter"
    $Counter++
}

New-Item -ItemType Directory -Path $OutputDir -ErrorAction Stop |
    Out-Null

$CollectionId = Split-Path $OutputDir -Leaf

$EvtxPath = Join-Path $OutputDir "$CollectionId.evtx"
$TxtPath  = Join-Path $OutputDir "$CollectionId.txt"
$CsvPath  = Join-Path $OutputDir "$CollectionId.csv"
$HashPath = Join-Path $OutputDir "$CollectionId.sha256"

Write-Host ""
Write-Host "========== POWERSHELL FORENSIC LOG EXPORT ==========" `
    -ForegroundColor Cyan

Write-Host "Collection Time : $($CollectionTime.ToString('yyyy-MM-dd HH:mm:ss.fff zzz'))"
Write-Host "Source          : $LogName"
Write-Host "Output Folder   : $OutputDir"

# ------------------------------------------------------------
# 2. EXPORT NATIVE EVTX
# ------------------------------------------------------------

Write-Host "`n[1/4] Exporting EVTX..." -ForegroundColor Yellow

& wevtutil.exe epl $LogName $EvtxPath

if ($LASTEXITCODE -ne 0) {
    throw "EVTX export failed. Exit code: $LASTEXITCODE"
}

# ------------------------------------------------------------
# 3. READ EVENTS FROM EXPORTED SNAPSHOT
# ------------------------------------------------------------

Write-Host "[2/4] Reading PowerShell event records..." `
    -ForegroundColor Yellow

$Events = @()

try {
    $Events = @(
        Get-WinEvent -Path $EvtxPath -Oldest -ErrorAction Stop
    )
}
catch {
    if ($_.FullyQualifiedErrorId -notmatch "NoMatchingEventsFound") {
        throw
    }
}

# ------------------------------------------------------------
# 4. CREATE TXT AND CSV
# ------------------------------------------------------------

Write-Host "[3/4] Creating TXT and CSV reports..." `
    -ForegroundColor Yellow

$Header = @(
    "POWERSHELL OPERATIONAL - FORENSIC EVENT LOG REPORT"
    "Collection Time : $($CollectionTime.ToString('yyyy-MM-dd HH:mm:ss.fff zzz'))"
    "Computer        : $env:COMPUTERNAME"
    "Source          : $LogName"
    "Total Records   : $($Events.Count)"
    ("=" * 90)
)

$Header | Set-Content -LiteralPath $TxtPath -Encoding UTF8

$CsvData = @(
    foreach ($Event in $Events) {

        @(
            ""
            ("=" * 90)
            "Record ID  : $($Event.RecordId)"
            "Event ID   : $($Event.Id)"
            "Timestamp  : $($Event.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss.fff'))"
            "Provider   : $($Event.ProviderName)"
            "Process ID : $($Event.ProcessId)"
            "Level      : $($Event.LevelDisplayName)"
            ""
            "MESSAGE:"
            [string]$Event.Message
        ) | Add-Content -LiteralPath $TxtPath -Encoding UTF8

        [PSCustomObject]@{
            Computer    = $env:COMPUTERNAME
            RecordId    = $Event.RecordId
            EventId     = $Event.Id
            TimeCreated = $Event.TimeCreated.ToString("o")
            Provider    = $Event.ProviderName
            ProcessId   = $Event.ProcessId
            Level       = $Event.LevelDisplayName
            Message     = [string]$Event.Message
        }
    }
)

if ($CsvData.Count -gt 0) {
    $CsvData |
        Export-Csv -LiteralPath $CsvPath `
            -NoTypeInformation -Encoding UTF8
}
else {
    "Computer,RecordId,EventId,TimeCreated,Provider,ProcessId,Level,Message" |
        Set-Content -LiteralPath $CsvPath -Encoding UTF8
}

# ------------------------------------------------------------
# 5. GENERATE SHA256 MANIFEST
# ------------------------------------------------------------

Write-Host "[4/4] Calculating SHA256..." -ForegroundColor Yellow

$HashLines = foreach ($Path in @($EvtxPath, $TxtPath, $CsvPath)) {

    $Hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256

    "{0}  {1}" -f $Hash.Hash, (Split-Path $Path -Leaf)
}

$HashLines |
    Set-Content -LiteralPath $HashPath -Encoding ASCII

# ------------------------------------------------------------
# 6. SUMMARY
# ------------------------------------------------------------

Write-Host ""
Write-Host "========== EXPORT COMPLETED ==========" `
    -ForegroundColor Green

Write-Host "Total Records : $($Events.Count)"
Write-Host "Directory     : $OutputDir"
Write-Host ""

Get-ChildItem -LiteralPath $OutputDir -File |
    Select-Object Name,
        @{Name="SizeKB";Expression={
            [math]::Round($_.Length / 1KB, 2)
        }} |
    Format-Table -AutoSize

Write-Host ""
Write-Host "Event ID 4104 = PowerShell Script Block Logging"
Write-Host "Event ID 4103 = PowerShell Module Logging (when enabled)"
Write-Host ""

```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\export_powershell.ps1"
```

## 6.2. Log WMI

```ps1
notepad C:\export_wmi.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1

# ============================================================
# DFIR - WMI ACTIVITY FORENSIC LOG EXPORT
# Each collection creates a timestamped directory
# Windows PowerShell 5.1
# ============================================================

$ErrorActionPreference = "Stop"

$LogName = "Microsoft-Windows-WMI-Activity/Operational"
$RootDir = "C:\DFIR\Logs\WMI_Activity"

# 1. Generate collection timestamp
$CollectionTime = Get-Date
$Timestamp = $CollectionTime.ToString("yyyyMMdd_HHmmss")

$BaseName = "WMI_Activity_Operational_$Timestamp"

# 2. Create a unique directory for this collection
New-Item -ItemType Directory -Path $RootDir -Force | Out-Null

$OutputDir = Join-Path $RootDir $BaseName
$Counter = 1

while (Test-Path -LiteralPath $OutputDir) {
    $OutputDir = Join-Path $RootDir "${BaseName}_$Counter"
    $Counter++
}

New-Item -ItemType Directory -Path $OutputDir -ErrorAction Stop |
    Out-Null

# File names use the actual collection directory name
$CollectionId = Split-Path $OutputDir -Leaf

$EvtxPath = Join-Path $OutputDir "$CollectionId.evtx"
$TxtPath  = Join-Path $OutputDir "$CollectionId.txt"
$CsvPath  = Join-Path $OutputDir "$CollectionId.csv"
$HashPath = Join-Path $OutputDir "$CollectionId.sha256"

Write-Host ""
Write-Host "========== WMI ACTIVITY FORENSIC EXPORT ==========" `
    -ForegroundColor Cyan

Write-Host "Collection Time : $($CollectionTime.ToString('yyyy-MM-dd HH:mm:ss.fff zzz'))"
Write-Host "Source          : $LogName"
Write-Host "Output Folder   : $OutputDir"

# 3. Export native EVTX
Write-Host "`n[1/4] Exporting EVTX..." -ForegroundColor Yellow

& wevtutil.exe epl $LogName $EvtxPath

if ($LASTEXITCODE -ne 0) {
    throw "EVTX export failed. Exit code: $LASTEXITCODE"
}

# 4. Read events from exported EVTX snapshot
Write-Host "[2/4] Reading exported records..." -ForegroundColor Yellow

$Events = @()

try {
    $Events = @(
        Get-WinEvent -Path $EvtxPath -Oldest -ErrorAction Stop
    )
}
catch {
    if ($_.FullyQualifiedErrorId -notmatch "NoMatchingEventsFound") {
        throw
    }
}

# 5. Export detailed TXT and structured CSV
Write-Host "[3/4] Writing TXT and CSV..." -ForegroundColor Yellow

$Header = @(
    "WMI ACTIVITY - FORENSIC EVENT LOG REPORT"
    "Collection Time : $($CollectionTime.ToString('yyyy-MM-dd HH:mm:ss.fff zzz'))"
    "Computer        : $env:COMPUTERNAME"
    "Source          : $LogName"
    "Total Records   : $($Events.Count)"
    ("=" * 90)
)

$Header | Set-Content -LiteralPath $TxtPath -Encoding UTF8

$CsvData = @(
    foreach ($Event in $Events) {

        @(
            ""
            ("=" * 90)
            "Record ID  : $($Event.RecordId)"
            "Event ID   : $($Event.Id)"
            "Timestamp  : $($Event.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss.fff'))"
            "Provider   : $($Event.ProviderName)"
            "Process ID : $($Event.ProcessId)"
            "Level      : $($Event.LevelDisplayName)"
            ""
            "MESSAGE:"
            [string]$Event.Message
        ) | Add-Content -LiteralPath $TxtPath -Encoding UTF8

        [PSCustomObject]@{
            Computer    = $env:COMPUTERNAME
            RecordId    = $Event.RecordId
            EventId     = $Event.Id
            TimeCreated = $Event.TimeCreated.ToString("o")
            Provider    = $Event.ProviderName
            ProcessId   = $Event.ProcessId
            Level       = $Event.LevelDisplayName
            Message     = [string]$Event.Message
        }
    }
)

if ($CsvData.Count -gt 0) {
    $CsvData | Export-Csv -LiteralPath $CsvPath `
        -NoTypeInformation -Encoding UTF8
}
else {
    "Computer,RecordId,EventId,TimeCreated,Provider,ProcessId,Level,Message" |
        Set-Content -LiteralPath $CsvPath -Encoding UTF8
}

# 6. Generate SHA256 manifest for the three evidence files
Write-Host "[4/4] Calculating SHA256..." -ForegroundColor Yellow

$HashLines = foreach ($Path in @($EvtxPath, $TxtPath, $CsvPath)) {
    $Hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    "{0}  {1}" -f $Hash.Hash, (Split-Path $Path -Leaf)
}

$HashLines | Set-Content -LiteralPath $HashPath -Encoding ASCII

# 7. Summary
Write-Host ""
Write-Host "========== EXPORT COMPLETED ==========" -ForegroundColor Green
Write-Host "Records      : $($Events.Count)"
Write-Host "Directory    : $OutputDir"
Write-Host ""
Write-Host "Files:" -ForegroundColor Cyan

Get-ChildItem -LiteralPath $OutputDir -File |
    Select-Object Name,
        @{Name="SizeKB";Expression={[math]::Round($_.Length / 1KB, 2)}} |
    Format-Table -AutoSize

```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\export_wmi.ps1"
```

## 6.3. 

```ps1
notepad C:\export_wmi.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1

```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\on.ps1"
```

## 6.4. 

```ps1
notepad C:\export_wmi.ps1
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1

```

</details>

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force 
& "C:\on.ps1"
```
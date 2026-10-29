# 1. Cài đặt 7zip

```ps1
cd C:\Users\admin\Downloads
notepad install_dfir_tools.ps1.ps1
```

```ps1
Set-ExecutionPolicy Bypass -Scope Process -Force
& "C:\Users\admin\Downloads\install_dfir_tools.ps1"
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1

# ======================================================
# DFIR TOOLKIT - AUTOMATIC SETUP
# Windows 10 x64
# Wireshark & FTK Imager: Manual installation
# ======================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Root = "C:\DFIR"
$Tools = "$Root\Tools"
$Config = "$Root\Config"
$Logs = "$Root\Logs"
$Downloads = Join-Path $env:USERPROFILE "Downloads"

$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)

if (-not $principal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)) {
    throw "Please run PowerShell as Administrator."
}

@($Root, $Tools, $Config, $Logs) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

$Results = New-Object System.Collections.ArrayList
$Shell = New-Object -ComObject WScript.Shell

function Add-Result {
    param($Name, $Status, $Path, $Note = "")

    [void]$Results.Add([PSCustomObject]@{
        Tool = $Name
        Status = $Status
        Path = $Path
        Note = $Note
    })

    Write-Host "[$Status] $Name $Note"
}

function Get-Package {
    param([string]$File)

    $Path = Join-Path $Downloads $File

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing: $Path"
    }

    return $Path
}

function Find-Exe {
    param(
        [string]$Folder,
        [string[]]$Names
    )

    if (-not (Test-Path $Folder)) { return $null }

    foreach ($Name in $Names) {
        $Exe = Get-ChildItem $Folder -Recurse -File `
            -Filter $Name -ErrorAction SilentlyContinue |
            Select-Object -First 1

        if ($Exe) { return $Exe.FullName }
    }

    return $null
}

function Create-Shortcut {
    param(
        [string]$Name,
        [string]$Target,
        [string]$Arguments = ""
    )

    if (-not (Test-Path -LiteralPath $Target)) {
        return $false
    }

    $Link = $Shell.CreateShortcut("$Root\$Name.lnk")
    $Link.TargetPath = $Target
    $Link.Arguments = $Arguments
    $Link.WorkingDirectory = Split-Path $Target -Parent
    $Link.IconLocation = "$Target,0"
    $Link.Save()

    return $true
}

function Install-Portable {
    param(
        [string]$Package,
        [string]$Folder,
        [string]$Name,
        [string[]]$Executables
    )

    try {
        $Source = Get-Package $Package
        $Destination = Join-Path $Tools $Folder

        New-Item -ItemType Directory -Path $Destination -Force |
            Out-Null

        Expand-Archive -LiteralPath $Source `
            -DestinationPath $Destination -Force

        $Exe = Find-Exe $Destination $Executables

        if ($Exe) {
            [void](Create-Shortcut $Name $Exe)
            Add-Result $Name "READY" $Exe
        }
        else {
            Add-Result $Name "CHECK" $Destination "Executable not found."
        }
    }
    catch {
        Add-Result $Name "FAILED" "" $_.Exception.Message
    }
}

# ------------------------------------------------------
# 1. 7-ZIP
# ------------------------------------------------------

try {
    Write-Host "`n[1/9] Installing 7-Zip..."

    $Installer = Get-Package "0_7z2603-x64.exe"

    $P = Start-Process $Installer -ArgumentList "/S" `
        -Wait -PassThru

    if ($P.ExitCode -ne 0) {
        throw "Installer exit code: $($P.ExitCode)"
    }

    $Exe = "$env:ProgramFiles\7-Zip\7zFM.exe"

    if (-not (Test-Path $Exe)) {
        throw "7-Zip installation not verified."
    }

    [void](Create-Shortcut "7-Zip" $Exe)
    Add-Result "7-Zip" "READY" $Exe
}
catch {
    Add-Result "7-Zip" "FAILED" "" $_.Exception.Message
}

# ------------------------------------------------------
# 2. SYSMON
# ------------------------------------------------------

try {
    Write-Host "`n[2/9] Installing Sysmon..."

    $Destination = Join-Path $Tools "Sysmon"

    New-Item -ItemType Directory -Path $Destination -Force |
        Out-Null

    Expand-Archive `
        -LiteralPath (Get-Package "1_Sysmon.zip") `
        -DestinationPath $Destination -Force

    $PackageExe = Find-Exe $Destination @("Sysmon64.exe")

    if (-not $PackageExe) {
        throw "Sysmon64.exe not found."
    }

    $ConfigPath = Join-Path $Config "sysmon-dfir-full.xml"

    $Xml = @'
<Sysmon schemaversion="4.91">
  <HashAlgorithms>sha256</HashAlgorithms>
  <DnsLookup>false</DnsLookup>
  <CheckRevocation>false</CheckRevocation>
  <EventFiltering>
    <ProcessCreate onmatch="exclude" />
    <NetworkConnect onmatch="exclude" />
    <ProcessTerminate onmatch="exclude" />
    <ImageLoad onmatch="exclude" />
    <CreateRemoteThread onmatch="exclude" />
    <ProcessAccess onmatch="exclude" />
    <FileCreate onmatch="exclude" />
    <RegistryEvent onmatch="exclude" />
    <PipeEvent onmatch="exclude" />
    <WmiEvent onmatch="exclude" />
    <DnsQuery onmatch="exclude" />
    <ProcessTampering onmatch="exclude" />
  </EventFiltering>
</Sysmon>
'@

    [System.IO.File]::WriteAllText(
        $ConfigPath,
        $Xml,
        (New-Object System.Text.UTF8Encoding($false))
    )

    $Service = Get-Service Sysmon64 -ErrorAction SilentlyContinue

    if ($Service) {
        $InstalledExe = "$env:windir\Sysmon64.exe"
        & $InstalledExe -c $ConfigPath
    }
    else {
        & $PackageExe -accepteula -i $ConfigPath
        $InstalledExe = "$env:windir\Sysmon64.exe"
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Sysmon configuration failed."
    }

    & wevtutil.exe sl "Microsoft-Windows-Sysmon/Operational" /e:true
    if ($LASTEXITCODE -ne 0) { throw "Cannot enable Sysmon log." }

    & wevtutil.exe sl "Microsoft-Windows-Sysmon/Operational" /ms:268435456
    if ($LASTEXITCODE -ne 0) { throw "Cannot set Sysmon log size." }

    $Cmd = "$env:windir\System32\cmd.exe"
    $Args = '/k ""{0}" -c"' -f $InstalledExe

    [void](Create-Shortcut "Sysmon - Configuration" $Cmd $Args)

    Add-Result "Sysmon" "READY" $InstalledExe
}
catch {
    Add-Result "Sysmon" "FAILED" "" $_.Exception.Message
}

# ------------------------------------------------------
# 3-8. PORTABLE TOOLS
# ------------------------------------------------------

Write-Host "`n[3/9] Process Monitor"
Install-Portable "3_ProcessMonitor.zip" "ProcessMonitor" `
    "Process Monitor" @("Procmon64.exe", "Procmon.exe")

Write-Host "`n[4/9] Process Explorer"
Install-Portable "4_ProcessExplorer.zip" "ProcessExplorer" `
    "Process Explorer" @("procexp64.exe", "procexp.exe")

Write-Host "`n[5/9] PE-sieve"
Install-Portable "6_pe-sieve64.zip" "PE-sieve" `
    "PE-sieve" @("pe-sieve64.exe", "pe-sieve.exe")

Write-Host "`n[6/9] Autoruns"
Install-Portable "8_Autoruns.zip" "Autoruns" `
    "Autoruns" @("Autoruns64.exe", "Autoruns.exe")

Write-Host "`n[7/9] RegRipper"
Install-Portable "9_RegRipper.zip" "RegRipper" `
    "RegRipper" @("rr.exe", "rip.exe")

Write-Host "`n[8/9] KAPE"
Install-Portable "11_kape.zip" "KAPE" `
    "KAPE" @("gkape.exe", "kape.exe")

# ------------------------------------------------------
# 9. SYSTEM INFORMER
# ------------------------------------------------------

try {
    Write-Host "`n[9/9] Installing System Informer..."

    $Installer = Get-Package `
        "13_systeminformer-4.0.26241.138-release-setup.exe"

    $P = Start-Process $Installer `
        -ArgumentList "-install -silent" `
        -Wait -PassThru

    if ($P.ExitCode -notin @(0, 3010)) {
        throw "Installer exit code: $($P.ExitCode)"
    }

    $Paths = @(
        "$env:ProgramFiles\SystemInformer\SystemInformer.exe",
        "$env:ProgramFiles\System Informer\SystemInformer.exe",
        "$env:LOCALAPPDATA\Programs\SystemInformer\SystemInformer.exe",
        "$env:LOCALAPPDATA\Programs\System Informer\SystemInformer.exe"
    )

    $Exe = $Paths |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1

    if ($Exe) {
        [void](Create-Shortcut "System Informer" $Exe)
        Add-Result "System Informer" "READY" $Exe
    }
    else {
        Add-Result "System Informer" "CHECK" "" `
            "Installer finished but executable was not found."
    }
}
catch {
    Add-Result "System Informer" "FAILED" "" $_.Exception.Message
}

# ------------------------------------------------------
# OPTIONAL: SHORTCUTS FOR MANUALLY INSTALLED TOOLS
# ------------------------------------------------------

$WiresharkPaths = @(
    "$env:ProgramFiles\Wireshark\Wireshark.exe",
    "${env:ProgramFiles(x86)}\Wireshark\Wireshark.exe"
)

$WiresharkExe = $WiresharkPaths |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if ($WiresharkExe) {
    [void](Create-Shortcut "Wireshark" $WiresharkExe)
    Add-Result "Wireshark" "SHORTCUT" $WiresharkExe
}

$FTKPaths = @(
    "$env:ProgramFiles\AccessData\FTK Imager\FTK Imager.exe",
    "${env:ProgramFiles(x86)}\AccessData\FTK Imager\FTK Imager.exe",
    "$env:ProgramFiles\Exterro\FTK Imager\FTK Imager.exe",
    "${env:ProgramFiles(x86)}\Exterro\FTK Imager\FTK Imager.exe"
)

$FTKExe = $FTKPaths |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if ($FTKExe) {
    [void](Create-Shortcut "FTK Imager" $FTKExe)
    Add-Result "FTK Imager" "SHORTCUT" $FTKExe
}

# ------------------------------------------------------
# INSTALLATION REPORT
# ------------------------------------------------------

Write-Host "`n========== RESULTS ==========" -ForegroundColor Cyan

$Results |
Format-Table Tool, Status, Path -AutoSize

$ReportPath = Join-Path $Logs "dfir_install_report.csv"

$Results |
Export-Csv -Path $ReportPath -NoTypeInformation -Encoding UTF8

Write-Host "`nShortcuts: $Root"
Write-Host "Report: $ReportPath"
Write-Host "DONE." -ForegroundColor Green



# =============================================
# DFIR EVIDENCE STORAGE CONFIGURATION
# Windows 10 Victim
# =============================================

$Root = "C:\DFIR"

# Create evidence directories
$Folders = @(
    "Evidence\Sysmon",
    "Evidence\PowerShell",
    "Evidence\WMI",
    "Evidence\TaskScheduler",
    "Evidence\Procmon",
    "Evidence\Wireshark",
    "Evidence\Memory",
    "Evidence\Registry",
    "Evidence\KAPE",
    "Evidence\Baseline"
)

foreach ($Folder in $Folders) {
    New-Item -Path (Join-Path $Root $Folder) `
        -ItemType Directory -Force | Out-Null
}

# Configure Windows Event Log channels
$LogConfigs = @(
    @{
        Name = "Microsoft-Windows-Sysmon/Operational"
        MaxMB = 256
    },
    @{
        Name = "Microsoft-Windows-PowerShell/Operational"
        MaxMB = 128
    },
    @{
        Name = "Microsoft-Windows-WMI-Activity/Operational"
        MaxMB = 32
    },
    @{
        Name = "Microsoft-Windows-TaskScheduler/Operational"
        MaxMB = 64
    }
)

foreach ($Item in $LogConfigs) {
    $SizeBytes = [int64]($Item.MaxMB * 1MB)

    & wevtutil.exe sl $Item.Name /e:true

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Cannot enable: $($Item.Name)"
        continue
    }

    & wevtutil.exe sl $Item.Name "/ms:$SizeBytes"

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Cannot set size: $($Item.Name)"
    }
}

# Enable PowerShell Script Block Logging
$RegPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"

New-Item -Path $RegPath -Force | Out-Null

New-ItemProperty -Path $RegPath `
    -Name EnableScriptBlockLogging `
    -PropertyType DWord `
    -Value 1 `
    -Force | Out-Null

Write-Host "`nDFIR storage and logging configuration completed."

```

</details>


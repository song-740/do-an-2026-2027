## TIẾP TỤC DEMO

## SNAPSHOT

### Kiểm tra dung lượng các Event Log trước khi reset

```bash
$logs = @(
    "Microsoft-Windows-Sysmon/Operational",
    "Microsoft-Windows-PowerShell/Operational",
    "Windows PowerShell",
    "Security",
    "Microsoft-Windows-TaskScheduler/Operational"
)

foreach ($log in $logs) {
    Get-WinEvent -ListLog $log -ErrorAction SilentlyContinue |
        Select-Object LogName, RecordCount, IsEnabled,
            @{Name="SizeMB";Expression={[math]::Round($_.FileSize / 1MB, 2)}}
}
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> $logs = @(
>>     "Microsoft-Windows-Sysmon/Operational",
>>     "Microsoft-Windows-PowerShell/Operational",
>>     "Windows PowerShell",
>>     "Security",
>>     "Microsoft-Windows-TaskScheduler/Operational"
>> )
PS C:\Windows\system32>
PS C:\Windows\system32> foreach ($log in $logs) {
>>     Get-WinEvent -ListLog $log -ErrorAction SilentlyContinue |
>>         Select-Object LogName, RecordCount, IsEnabled,
>>             @{Name="SizeMB";Expression={[math]::Round($_.FileSize / 1MB, 2)}}
>> }

LogName                                     RecordCount IsEnabled SizeMB
-------                                     ----------- --------- ------
Microsoft-Windows-Sysmon/Operational              29472      True  30.07
Microsoft-Windows-PowerShell/Operational           1306      True  19.07
Windows PowerShell                                  704      True   4.07
Security                                           7927      True   7.07
Microsoft-Windows-TaskScheduler/Operational         963      True   1.07
```

</details>

### Reset 5 kênh Event Log phục vụ demo

```bash
$logs = @(
    "Microsoft-Windows-Sysmon/Operational",
    "Microsoft-Windows-PowerShell/Operational",
    "Windows PowerShell",
    "Security",
    "Microsoft-Windows-TaskScheduler/Operational"
)

foreach ($log in $logs) {
    Write-Host "`nRESET: $log" -ForegroundColor Cyan

    & wevtutil.exe cl $log

    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS" -ForegroundColor Green
    }
    else {
        Write-Host "FAILED - ExitCode: $LASTEXITCODE" -ForegroundColor Red
    }
}
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> $logs = @(
>>     "Microsoft-Windows-Sysmon/Operational",
>>     "Microsoft-Windows-PowerShell/Operational",
>>     "Windows PowerShell",
>>     "Security",
>>     "Microsoft-Windows-TaskScheduler/Operational"
>> )
PS C:\Windows\system32>
PS C:\Windows\system32> foreach ($log in $logs) {
>>     Get-WinEvent -ListLog $log -ErrorAction SilentlyContinue |
>>         Select-Object LogName, RecordCount, IsEnabled,
>>             @{Name="SizeMB";Expression={[math]::Round($_.FileSize / 1MB, 2)}}
>> }

LogName                                     RecordCount IsEnabled SizeMB
-------                                     ----------- --------- ------
Microsoft-Windows-Sysmon/Operational                 28      True   0.07
Microsoft-Windows-PowerShell/Operational             31      True   0.07
Windows PowerShell                                   15      True   0.07
Security                                             10      True   0.07
Microsoft-Windows-TaskScheduler/Operational           0      True   0.07
```

</details>

### Chuẩn bị mốc thời gian trước demo

```bash
Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff zzz"
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff zzz"
2026-10-21 09:15:51.511 +07:00
PS C:\Windows\system32> (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
2026-10-21T02:15:52.683Z
PS C:\Windows\system32>
```

</details>

### Kiểm tra file chứng cứ cũ

```bash
Get-ChildItem "C:\DFIR\Evidence" -Recurse -File -ErrorAction SilentlyContinue |
    Select-Object FullName, Length |
    Format-Table -AutoSize
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> Get-ChildItem "C:\DFIR\Evidence" -Recurse -File -ErrorAction SilentlyContinue |
>>     Select-Object FullName, Length |
>>     Format-Table -AutoSize

FullName                                                                                                          Lengt
                                                                                                                      h
--------                                                                                                          -----
C:\DFIR\Evidence\EVTX\PowerShell_Test_20261020_112611.evtx                                                        ...16
C:\DFIR\Evidence\EVTX\Security_Test_20261020_112336.evtx                                                          ...36
C:\DFIR\Evidence\EVTX\Sysmon_Followup_20261020.evtx                                                               ...92
C:\DFIR\Evidence\EVTX\Sysmon_Test_20261020_102428.evtx                                                            ...40
C:\DFIR\Evidence\EVTX\TaskScheduler_Test_20261020_112857.evtx                                                     69632
C:\DFIR\Evidence\Filesystem\sysmon-filetest.txt                                                                      65
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.AM4Y7M48.20261020170014.txt  3659
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.bWVQNQYW.20261020170516.txt   620
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.dD9DjN8F.20261020170524.txt 33120
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.kY5PHIBw.20261020164832.txt  1280
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.LfFNNb2P.20261020104530.txt  1058
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.pDdVRfJo.20261020164834.txt  2200
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.tTCL9TsS.20261020164825.txt  4211
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.xe0pFtN3.20261020164823.txt  1340
C:\DFIR\Evidence\PowerShellTranscripts\20261020\PowerShell_transcript.DESKTOP-3H9MVK0.xu48ZC1G.20261020162311.txt  6914
C:\DFIR\Evidence\PowerShellTranscripts\20261021\PowerShell_transcript.DESKTOP-3H9MVK0.gRlqyrQW.20261021042111.txt  3542
C:\DFIR\Evidence\PowerShellTranscripts\20261021\PowerShell_transcript.DESKTOP-3H9MVK0.J8ZxPHw8.20261021091108.txt     0
C:\DFIR\Evidence\PowerShellTranscripts\20261021\PowerShell_transcript.DESKTOP-3H9MVK0.QVN0FbKM.20261021042112.txt   982


PS C:\Windows\system32>
```

</details>

### Tách riêng chứng cứ cũ khỏi thư mục Evidence

```bash
$archive = "C:\DFIR\PreDemo_Archive"

New-Item -ItemType Directory -Path "$archive\EVTX" -Force | Out-Null
New-Item -ItemType Directory -Path "$archive\Filesystem" -Force | Out-Null

Move-Item "C:\DFIR\Evidence\EVTX\*.evtx" `
    "$archive\EVTX\" -ErrorAction Stop

Move-Item "C:\DFIR\Evidence\Filesystem\sysmon-filetest.txt" `
    "$archive\Filesystem\" -ErrorAction Stop

Write-Host "Archived EVTX files:" (
    @(Get-ChildItem "$archive\EVTX" -File).Count
)

Write-Host "Archived filesystem test:" (
    Test-Path "$archive\Filesystem\sysmon-filetest.txt"
)
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> $archive = "C:\DFIR\PreDemo_Archive"
PS C:\Windows\system32>
PS C:\Windows\system32> New-Item -ItemType Directory -Path "$archive\EVTX" -Force | Out-Null
PS C:\Windows\system32> New-Item -ItemType Directory -Path "$archive\Filesystem" -Force | Out-Null
PS C:\Windows\system32>
PS C:\Windows\system32> Move-Item "C:\DFIR\Evidence\EVTX\*.evtx" `
>>     "$archive\EVTX\" -ErrorAction Stop
PS C:\Windows\system32>
PS C:\Windows\system32> Move-Item "C:\DFIR\Evidence\Filesystem\sysmon-filetest.txt" `
>>     "$archive\Filesystem\" -ErrorAction Stop
PS C:\Windows\system32>
PS C:\Windows\system32> Write-Host "Archived EVTX files:" (
>>     @(Get-ChildItem "$archive\EVTX" -File).Count
>> )
Archived EVTX files: 5
PS C:\Windows\system32>
PS C:\Windows\system32> Write-Host "Archived filesystem test:" (
>>     Test-Path "$archive\Filesystem\sysmon-filetest.txt"
>> )
Archived filesystem test: True
PS C:\Windows\system32>
```

</details>

### Tách PowerShell Transcripts cũ

```bash
$source = "C:\DFIR\Evidence\PowerShellTranscripts"
$archive = "C:\DFIR\PreDemo_Archive\PowerShellTranscripts"

New-Item -ItemType Directory -Path $archive -Force | Out-Null

Get-ChildItem $source -Recurse -File -Filter "*.txt" |
ForEach-Object {
    $relative = $_.FullName.Substring($source.Length).TrimStart('\')
    $destination = Join-Path $archive $relative
    $destinationDir = Split-Path $destination -Parent

    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null

    try {
        $stream = [System.IO.File]::Open(
            $_.FullName,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
        $stream.Close()

        Move-Item -LiteralPath $_.FullName -Destination $destination -ErrorAction Stop
        Write-Host "MOVED: $relative" -ForegroundColor Green
    }
    catch {
        Write-Host "SKIPPED (locked or unavailable): $relative" -ForegroundColor Yellow
    }
}
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> $source = "C:\DFIR\Evidence\PowerShellTranscripts"
PS C:\Windows\system32> $archive = "C:\DFIR\PreDemo_Archive\PowerShellTranscripts"
PS C:\Windows\system32>
PS C:\Windows\system32> New-Item -ItemType Directory -Path $archive -Force | Out-Null
PS C:\Windows\system32>
PS C:\Windows\system32> Get-ChildItem $source -Recurse -File -Filter "*.txt" |
>> ForEach-Object {
>>     $relative = $_.FullName.Substring($source.Length).TrimStart('\')
>>     $destination = Join-Path $archive $relative
>>     $destinationDir = Split-Path $destination -Parent
>>
>>     New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
>>
>>     try {
>>         $stream = [System.IO.File]::Open(
>>             $_.FullName,
>>             [System.IO.FileMode]::Open,
>>             [System.IO.FileAccess]::ReadWrite,
>>             [System.IO.FileShare]::None
>>         )
>>         $stream.Close()
>>
>>         Move-Item -LiteralPath $_.FullName -Destination $destination -ErrorAction Stop
>>         Write-Host "MOVED: $relative" -ForegroundColor Green
>>     }
>>     catch {
>>         Write-Host "SKIPPED (locked or unavailable): $relative" -ForegroundColor Yellow
>>     }
>> }
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.AM4Y7M48.20261020170014.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.bWVQNQYW.20261020170516.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.dD9DjN8F.20261020170524.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.kY5PHIBw.20261020164832.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.LfFNNb2P.20261020104530.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.pDdVRfJo.20261020164834.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.tTCL9TsS.20261020164825.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.xe0pFtN3.20261020164823.txt
MOVED: 20261020\PowerShell_transcript.DESKTOP-3H9MVK0.xu48ZC1G.20261020162311.txt
MOVED: 20261021\PowerShell_transcript.DESKTOP-3H9MVK0.gRlqyrQW.20261021042111.txt
SKIPPED (locked or unavailable): 20261021\PowerShell_transcript.DESKTOP-3H9MVK0.J8ZxPHw8.20261021091108.txt
MOVED: 20261021\PowerShell_transcript.DESKTOP-3H9MVK0.QVN0FbKM.20261021042112.txt
```

</details>

### Kiểm tra thư mục Evidence sau khi dọn

```bash
Get-ChildItem "C:\DFIR\Evidence" -Recurse -File -ErrorAction SilentlyContinue |
    Select-Object FullName, Length, LastWriteTime |
    Format-Table -AutoSize
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> Get-ChildItem "C:\DFIR\Evidence" -Recurse -File -ErrorAction SilentlyContinue |
>>     Select-Object FullName, Length, LastWriteTime |
>>     Format-Table -AutoSize

FullName                                                                                                          Lengt
                                                                                                                      h
--------                                                                                                          -----
C:\DFIR\Evidence\PowerShellTranscripts\20261021\PowerShell_transcript.DESKTOP-3H9MVK0.J8ZxPHw8.20261021091108.txt 11062


PS C:\Windows\system32>
```

</details>

### Lưu trữ transcript cuối cùng

Đóng phiên ps1 cũ tạo phiên ps1 mới.

```bash
$source = "C:\DFIR\Evidence\PowerShellTranscripts\20261021\PowerShell_transcript.DESKTOP-3H9MVK0.J8ZxPHw8.20261021091108.txt"

$destination = "C:\DFIR\PreDemo_Archive\PowerShellTranscripts\20261021"

New-Item -ItemType Directory -Path $destination -Force | Out-Null

if (Test-Path $source) {
    try {
        Move-Item -LiteralPath $source -Destination $destination -ErrorAction Stop
        Write-Host "ARCHIVE: SUCCESS" -ForegroundColor Green
    }
    catch {
        Write-Host "ARCHIVE: FAILED" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}
else {
    Write-Host "SOURCE FILE NOT FOUND"
}
```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash
PS C:\Windows\system32> $source = "C:\DFIR\Evidence\PowerShellTranscripts\20261021\PowerShell_transcript.DESKTOP-3H9MVK0.J8ZxPHw8.20261021091108.txt"
PS C:\Windows\system32>
PS C:\Windows\system32> $destination = "C:\DFIR\PreDemo_Archive\PowerShellTranscripts\20261021"
PS C:\Windows\system32>
PS C:\Windows\system32> New-Item -ItemType Directory -Path $destination -Force | Out-Null
PS C:\Windows\system32>
PS C:\Windows\system32> if (Test-Path $source) {
>>     try {
>>         Move-Item -LiteralPath $source -Destination $destination -ErrorAction Stop
>>         Write-Host "ARCHIVE: SUCCESS" -ForegroundColor Green
>>     }
>>     catch {
>>         Write-Host "ARCHIVE: FAILED" -ForegroundColor Red
>>         Write-Host $_.Exception.Message
>>     }
>> }
ARCHIVE: SUCCESS
PS C:\Windows\system32> else {
>>     Write-Host "SOURCE FILE NOT FOUND"
>> }
else : The term 'else' is not recognized as the name of a cmdlet, function, script file, or operable program. Check
the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ else {
+ ~~~~
    + CategoryInfo          : ObjectNotFound: (else:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

PS C:\Windows\system32>
```

</details>

## SNAPSHOT LẦN 2

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>

### 

```bash

```

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```bash

```

</details>


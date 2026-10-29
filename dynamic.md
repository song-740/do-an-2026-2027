# b1

```ps1
$path = "C:\DFIR\Evidence\Sysmon\Sysmon_after_attack.evtx"

Get-WinEvent -FilterHashtable @{
    Path = $path
    Id = 1
} | Where-Object {
    $e = [xml]$_.ToXml()
    $data = @{}
    foreach ($d in $e.Event.EventData.Data) {
        $data[$d.Name] = $d.'#text'
    }

    $data.Image -like "*powershell.exe" -and
    $data.CommandLine -like "*stage1.ps1*" -and
    $data.ParentImage -like "*mshta.exe"
} | ForEach-Object {
    $e = [xml]$_.ToXml()
    $data = @{}
    foreach ($d in $e.Event.EventData.Data) {
        $data[$d.Name] = $d.'#text'
    }

    [PSCustomObject]@{
        TimeCreated     = $_.TimeCreated
        ProcessId       = $data.ProcessId
        Image           = $data.Image
        CommandLine     = $data.CommandLine
        ParentProcessId = $data.ParentProcessId
        ParentImage     = $data.ParentImage
    }
} | Format-List
```
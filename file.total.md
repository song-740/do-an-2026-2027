# Invoice_October.hta

| STT | Hành vi tấn công | MITRE ATT&CK ID | Technique / Sub-technique | Tactic |
|---|---|---|---|---|
| 1 | Client mở file Invoice_October.hta | T1204.002 | User Execution: Malicious File | Execution |
| 2 | Sử dụng mshta.exe để thực thi file HTA | T1218.005 | System Binary Proxy Execution: Mshta | Stealth |
| 3 | Thực thi VBScript và tạo đối tượng WScript.Shell | T1059.005 | Command and Scripting Interpreter: Visual Basic | Execution |
| 4 | VBScript khởi chạy powershell.exe | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution |
| 5 | PowerShell tải stage1.ps1 bằng Net.WebClient.DownloadString qua HTTP | T1105 | Ingress Tool Transfer | Command and Control |
| 6 | Thực thi nội dung tải về bằng IEX | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution |

# stage1.ps1


| STT | Hành vi trong stage1.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích ánh xạ |
|---|---|---|---|---|---|
| 1 | Kiểm tra quyền Administrator và phân nhánh thực thi | — | Không ánh xạ độc lập | — | Kiểm tra điều kiện trước khi thực hiện các hành vi tiếp theo. |
| 2 | Tạo và sửa Registry ms-settings để chuẩn bị UAC bypass | T1112 | Modify Registry | Defense Impairment / Persistence | Chỉnh sửa Registry nhằm thay đổi cách Windows xử lý lệnh. |
| 3 | Khởi chạy ComputerDefaults.exe để thử thực thi PowerShell với quyền nâng cao | T1548.002 | Abuse Elevation Control Mechanism: Bypass User Account Control | Privilege Escalation | Cố gắng vượt UAC thông qua chương trình Windows tự nâng quyền. |
| 4 | Nếu bypass không đạt, gọi PowerShell bằng RunAs và có thể hiện UAC prompt | — | Nhánh nâng quyền có xác nhận người dùng | — | Không phải bypass im lặng; không gán T1548.002 riêng cho nhánh này. |
| 5 | Tải wmi_setup.ps1 từ HTTP server 192.168.56.100:8000 | T1105 | Ingress Tool Transfer | Command and Control | Chuyển payload giai đoạn tiếp theo từ attacker server đến Client. |
| 6 | Mã hóa nội dung wmi_setup.ps1 thành Base64 và lưu ở HKCU\Software\Classes\APT29Stage1\Payload | T1027.011 | Obfuscated Files or Information: Fileless Storage | Stealth | Lưu mã PowerShell trong Registry thay vì lưu thành file .ps1 riêng. |
| 7 | Tạo khóa và giá trị Registry APT29Stage1\Payload | T1112 | Modify Registry | Defense Impairment / Persistence | Thay đổi Registry để lưu nội dung payload. |
| 8 | Đọc lại payload từ Registry và kiểm tra tính nhất quán | — | Không ánh xạ độc lập | — | Xác minh dữ liệu nội bộ trước khi giải mã và thực thi. |
| 9 | Giải mã Base64 và chuyển về chuỗi PowerShell | T1140 | Deobfuscate/Decode Files or Information | Stealth | Khôi phục mã từ nội dung Base64 đã lưu trong Registry. |
| 10 | Thực thi mã đã giải mã bằng IEX | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Chạy payload trong phiên PowerShell hiện tại mà không cần ghi lại file script. |

# wmi_setup.ps1


| STT | Thời điểm | Hành vi trong wmi_setup.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích |
|---|---|---|---|---|---|---|
| 1 | Setup | Chạy các lệnh PowerShell và CIM để cấu hình WMI | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Sử dụng PowerShell để thao tác với các đối tượng WMI. |
| 2 | Setup | Khai báo URL orchestrator.ps1 | — | Không ánh xạ độc lập | — | Khai báo URL chưa phải tải payload. |
| 3 | Setup | Tìm và thử xóa WMI Filter, Consumer, Binding cũ | T1546.003 | Event Triggered Execution: Windows Management Instrumentation Event Subscription | Persistence | Thao tác quản lý subscription cũ trước khi đăng ký mới; không tạo kỹ thuật độc lập. |
| 4 | Setup | Tạo __EventFilter với WQL theo dõi việc tạo notepad.exe | T1546.003 | Event Triggered Execution: Windows Management Instrumentation Event Subscription | Persistence | Định nghĩa điều kiện kích hoạt. |
| 5 | Setup | Tạo CommandLineEventConsumer chứa lệnh PowerShell tải orchestrator.ps1 | T1546.003 | Event Triggered Execution: Windows Management Instrumentation Event Subscription | Persistence | Định nghĩa hành động khi sự kiện xảy ra. |
| 6 | Setup | Tạo __FilterToConsumerBinding liên kết Filter và Consumer | T1546.003 | Event Triggered Execution: Windows Management Instrumentation Event Subscription | Persistence | Hoàn thiện permanent event subscription. |
| 7 | Setup | Ghi wmi_setup.log | — | Không ánh xạ độc lập | — | Ghi log nội bộ của script. |
| 8 | Trigger | WMI phát hiện một tiến trình notepad.exe mới | T1546.003 | Event Triggered Execution: Windows Management Instrumentation Event Subscription | Persistence | Điều kiện của subscription được đáp ứng. |
| 9 | Trigger | Consumer khởi chạy powershell.exe với WindowStyle Hidden | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | PowerShell thực thi lệnh được cấu hình trong Consumer. |
| 10 | Trigger | PowerShell tải orchestrator.ps1 qua HTTP từ 192.168.56.100:8000 | T1105 | Ingress Tool Transfer | Command and Control | Payload được chuyển từ attacker server đến Client khi trigger xảy ra. |
| 11 | Trigger | PowerShell dùng IEX thực thi nội dung orchestrator.ps1 | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Nội dung script được xử lý trong PowerShell mà không cần lưu riêng một file .ps1. |

# orchestrator.ps1


| STT | Hành vi trong orchestrator.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích ánh xạ |
|---|---|---|---|---|---|
| 1 | Thực thi orchestrator.ps1 bằng PowerShell sau khi WMI Consumer kích hoạt | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Sử dụng PowerShell làm môi trường điều phối các giai đoạn tấn công. |
| 2 | Đặt ExecutionPolicy Bypass trong phiên hiện tại | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Điều chỉnh chính sách thực thi trong phiên PowerShell; không mặc định coi đây là AMSI bypass. |
| 3 | Tạo lệnh tải revshell.ps1 và chuyển lệnh thành Base64 | T1027.010 | Obfuscated Files or Information: Command Obfuscation | Stealth | Mã hóa nội dung lệnh PowerShell để khó nhận diện trực tiếp trong command line. |
| 4 | Tạo PowerShell mới với -NoP, -Exec Bypass và -Enc | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Khởi chạy tiến trình PowerShell để thực thi lệnh đã mã hóa. |
| 5 | Tiến trình PowerShell mới tải revshell.ps1 qua HTTP | T1105 | Ingress Tool Transfer | Command and Control | Tải payload reverse shell từ attacker server; chỉ xác nhận khi có HTTP/process evidence. |
| 6 | Sử dụng Get-Process để tìm PID của notepad.exe | T1057 | Process Discovery | Discovery | Tìm tiến trình mục tiêu để sử dụng trong bước injection. |
| 7 | Thử AMSI bypass bằng .NET reflection và thay đổi giá trị bộ nhớ | T1562.001 | Impair Defenses: Disable or Modify Tools | Defense Impairment | Cố gắng làm suy giảm cơ chế quét AMSI; phải xác minh hiệu quả thực tế. |
| 8 | Tải Invoke-PSInject.ps1 qua HTTP vào biến PowerShell | T1105 | Ingress Tool Transfer | Command and Control | Chuyển công cụ injection từ attacker server vào Client. |
| 9 | Nạp Invoke-PSInject.ps1 bằng Invoke-Expression | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Thực thi mã công cụ injection trong phiên PowerShell hiện tại. |
| 10 | Tạo lệnh tải keylogger.ps1 và mã hóa Base64 thành stub | T1027.010 | Obfuscated Files or Information: Command Obfuscation | Stealth | Chuẩn bị encoded PowerShell stub cho giai đoạn injection. |
| 11 | Gọi Invoke-PSInject với PID của Notepad và PowerShell stub | T1055 | Process Injection | Stealth / Privilege Escalation | Yêu cầu đưa mã vào tiến trình Notepad; chưa xác định sub-technique khi chưa phân tích Invoke-PSInject.ps1. |
| 12 | Nếu mã trong tiến trình mục tiêu chạy, stub sẽ tải keylogger.ps1 | T1105 | Ingress Tool Transfer | Command and Control | Tải keylogger khi stub thực sự được thực thi trong tiến trình mục tiêu; là hành vi có điều kiện. |
| 13 | Kiểm tra Notepad còn chạy sau lời gọi injection | — | Không ánh xạ độc lập | — | Kiểm tra trạng thái tiến trình, không đủ chứng minh injection hoặc keylogger thành công. |
| 14 | Ghi orchestrator.log | — | Không ánh xạ độc lập | — | Ghi log nội bộ phục vụ theo dõi; không phải kỹ thuật ATT&CK riêng. |

# Invoke-PSInject.ps1


| STT | Hành vi trong Invoke-PSInject.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích ánh xạ |
|---|---|---|---|---|---|
| 1 | Sử dụng PowerShell để triển khai và điều phối logic injection | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | PowerShell thực thi các hàm điều khiển và thao tác bộ nhớ. |
| 2 | Nhận PowerShell stub đã mã hóa Base64 và giải mã về chuỗi lệnh | T1140 | Deobfuscate/Decode Files or Information | Stealth | Phục hồi nội dung PowerShell trước khi đưa vào PE. |
| 3 | Chọn và giải mã PE 32-bit hoặc 64-bit được nhúng trong script | T1140 | Deobfuscate/Decode Files or Information | Stealth | Giải mã dữ liệu PE Base64 thành byte trong bộ nhớ. |
| 4 | Sử dụng Reflection và dynamic delegates để truy cập Win32 API | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Triển khai chức năng thao tác tiến trình và bộ nhớ thông qua PowerShell/.NET. |
| 5 | Đưa nội dung PowerShell stub vào PE nhúng | T1055.002 | Process Injection: Portable Executable Injection | Stealth | Chuẩn bị PE được sử dụng để đưa mã vào tiến trình đích. |
| 6 | Mở handle đến tiến trình notepad.exe theo PID được orchestrator truyền vào | T1055.002 | Process Injection: Portable Executable Injection | Stealth | Truy cập tiến trình mục tiêu để chuẩn bị injection. |
| 7 | Kiểm tra kiến trúc 32-bit/64-bit của PE và tiến trình đích | — | Không ánh xạ độc lập | — | Kiểm tra điều kiện tương thích phục vụ injection. |
| 8 | Cấp phát và ghi PE vào không gian bộ nhớ của notepad.exe | T1055.002 | Process Injection: Portable Executable Injection | Stealth | Thực hiện manual mapping PE vào tiến trình khác. |
| 9 | Xử lý PE sections, relocation và import khi nạp trong bộ nhớ | T1055.002 | Process Injection: Portable Executable Injection | Stealth | Các bước hỗ trợ ánh xạ PE trong tiến trình đích. |
| 10 | Tạo remote thread để thực thi mã trong notepad.exe | T1055.002 | Process Injection: Portable Executable Injection | Stealth | Kích hoạt thực thi mã đã được đưa vào tiến trình đích. |
| 11 | Nạp PE trực tiếp từ bộ nhớ thay vì sử dụng đường dẫn DLL trên đĩa | T1620 | Reflective Code Loading | Stealth | Đặc điểm reflective/manual loading; là ánh xạ bổ sung cho cơ chế nạp mã trong memory. |
| 12 | Giải phóng một số vùng nhớ trung gian sau quá trình nạp | — | Không ánh xạ độc lập | — | Dọn tài nguyên trong quá trình thực thi; không đủ căn cứ gán kỹ thuật xóa dấu vết riêng. |
| 13 | Nếu stub thực thi thành công, tiến trình đích tiếp tục logic tải keylogger.ps1 | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Đây là hành vi có điều kiện; cần đối chiếu file keylogger.ps1 và evidence thực tế. |

# keylogger.ps1


| STT | Hành vi trong keylogger.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích ánh xạ |
|---|---|---|---|---|---|
| 1 | Thực thi mã keylogger bằng PowerShell | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | PowerShell là môi trường thực thi logic keylogging. |
| 2 | Định nghĩa lớp .NET KeyLogger và import user32.dll/GetAsyncKeyState bằng Add-Type | T1056.001 | Input Capture: Keylogging | Collection / Credential Access | Chuẩn bị phương thức truy vấn trạng thái bàn phím Windows. |
| 3 | Xây dựng bảng ánh xạ virtual key sang ký tự và phím đặc biệt | T1056.001 | Input Capture: Keylogging | Collection / Credential Access | Chuyển dữ liệu phím thành nội dung có thể đọc. |
| 4 | Lặp qua virtual key từ 8 đến 222 và gọi GetAsyncKeyState | T1056.001 | Input Capture: Keylogging | Collection / Credential Access | Liên tục kiểm tra trạng thái bàn phím để phát hiện phím được nhấn. |
| 5 | Sử dụng hashtable pressed để tránh ghi lặp khi giữ phím | T1056.001 | Input Capture: Keylogging | Collection / Credential Access | Quản lý trạng thái phím trong quá trình thu thập. |
| 6 | Sử dụng vòng lặp while(true) và Start-Sleep 30 ms để duy trì polling | T1056.001 | Input Capture: Keylogging | Collection / Credential Access | Duy trì hoạt động theo dõi bàn phím khi môi trường thực thi còn tồn tại. |
| 7 | Ghi dữ liệu phím vào C:\Users\Public\apt29\keylog.txt bằng AppendAllText | T1056.001 | Input Capture: Keylogging | Collection / Credential Access | Lưu kết quả thu thập phím trên máy Client. |
| 8 | Tập trung dữ liệu phím đã thu thập trong keylog.txt để sử dụng ở giai đoạn sau | T1074.001 | Data Staged: Local Data Staging | Collection | Dữ liệu thu thập được lưu cục bộ để phục vụ thao tác lấy hoặc chuyển dữ liệu về sau. |
| 9 | Không có lệnh truyền keylog.txt qua mạng trong file này | — | Không ánh xạ exfiltration | — | Phải phân tích login_handler.ps1 và network evidence để xác định hoạt động exfiltration. |

# revshell.ps1


| STT | Hành vi trong revshell.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích ánh xạ |
|---|---|---|---|---|---|
| 1 | PowerShell thực thi nội dung revshell.ps1 | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Sử dụng PowerShell để triển khai reverse shell và xử lý các lệnh nhận từ xa. |
| 2 | Ghi thông tin thời gian và PID vào revshell.log | — | Không ánh xạ độc lập | — | Tạo log nội bộ trước khi kết nối, không chứng minh C2 thành công. |
| 3 | Tạo outbound TCP connection đến 192.168.56.100:4444 bằng TCPClient | T1095 | Non-Application Layer Protocol | Command and Control | Sử dụng kết nối TCP trực tiếp với giao thức trao đổi lệnh tùy biến, không sử dụng HTTP hoặc HTTPS cho phiên reverse shell. |
| 4 | Sử dụng TCP port 4444 cho phiên điều khiển từ xa | T1571 (bổ sung) | Non-Standard Port | Command and Control | Cổng 4444 là cổng không thông dụng cho lưu lượng điều khiển; chỉ nên gán bổ sung khi tiêu chí phân loại cổng bất thường được xác nhận. |
| 5 | Đọc dữ liệu lệnh từ TCP stream và chuyển thành chuỗi ASCII | T1095 | Non-Application Layer Protocol | Command and Control | Nhận nội dung điều khiển từ attacker qua phiên TCP. |
| 6 | Thực thi nội dung nhận được bằng Invoke-Expression (IEX) | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Biến chuỗi lệnh từ kết nối mạng thành mã PowerShell chạy trên Windows Client. |
| 7 | Chuyển kết quả và lỗi được bắt thành chuỗi văn bản | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Thu kết quả thực thi để gửi về attacker trong cùng phiên shell. |
| 8 | Gửi kết quả thực thi qua TCP stream về Kali | T1095 | Non-Application Layer Protocol | Command and Control | Duy trì trao đổi lệnh hai chiều giữa Client và attacker. |
| 9 | Tiếp tục nhận nhiều lệnh trong vòng lặp while | T1095 | Non-Application Layer Protocol | Command and Control | Duy trì phiên tương tác C2 cho đến khi kết nối bị đóng hoặc gặp lỗi. |
| 10 | Đóng TCPClient khi vòng lặp kết thúc | — | Không ánh xạ độc lập | — | Giải phóng kết nối, không phải một kỹ thuật ATT&CK độc lập. |


# login_handler.ps1


| STT | Giai đoạn | Hành vi trong login_handler.ps1 | MITRE ATT&CK ID | Technique / Sub-technique | Tactic | Giải thích ánh xạ |
|---|---|---|---|---|---|---|
| 1 | Thực thi | Scheduled Task chạy nội dung login_handler.ps1 bằng PowerShell | T1059.001 | Command and Scripting Interpreter: PowerShell | Execution | Sử dụng PowerShell để thực hiện các thao tác xử lý và truyền dữ liệu. |
| 2 | Chuẩn bị | Khai báo đường dẫn keylog.txt và thông tin Kali TCP 5555 | — | Không ánh xạ độc lập | — | Mới khai báo biến, chưa phát sinh truy cập file hoặc kết nối mạng. |
| 3 | Kiểm tra | Kiểm tra sự tồn tại của keylog.txt bằng Test-Path | — | Không ánh xạ độc lập | — | Điều kiện quyết định có tiếp tục exfiltration hay không. |
| 4 | Thu thập dữ liệu | Đọc toàn bộ nội dung keylog.txt bằng Get-Content -Raw | T1074.001 (liên quan) | Data Staged: Local Data Staging | Collection | Truy cập dữ liệu keylogging đã được tập trung cục bộ từ giai đoạn trước; bản thân lệnh đọc không tạo thêm một lần staging mới. |
| 5 | Exfiltration | Khởi tạo TCPClient và kết nối đến Kali 192.168.56.100:5555 | T1048.003 | Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol | Exfiltration | Sử dụng kênh TCP riêng, không mã hóa, để truyền dữ liệu bên ngoài kênh C2 TCP 4444. |
| 6 | Exfiltration | Gửi hostname, tài khoản thực thi, timestamp và kích thước keylog | T1048.003 | Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol | Exfiltration | Đưa thông tin mô tả máy nguồn và dữ liệu gửi qua kết nối TCP. |
| 7 | Exfiltration | Gửi toàn bộ nội dung keylog bằng StreamWriter.Write | T1048.003 | Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol | Exfiltration | Truyền dữ liệu phím đã thu thập về máy Kali. |
| 8 | Hoàn tất truyền | Đóng TCP stream và ghi trạng thái OK hoặc FAIL | — | Không ánh xạ độc lập | — | Quản lý kết nối và ghi log; thông báo OK không chứng minh máy nhận đã lưu dữ liệu. |
| 9 | Lưu trữ | Sao chép keylog.txt vào keylog_history với tên chứa timestamp | T1074.001 | Data Staged: Local Data Staging | Collection | Duy trì bản sao cục bộ của dữ liệu đã thu thập; ở đây là bản sao lịch sử sau nỗ lực gửi. |
| 10 | Reset dữ liệu | Thử xóa keylog.txt sau khi sao lưu | T1070.004 (cân nhắc) | Indicator Removal: File Deletion | Defense Evasion / Stealth | Có thao tác xóa file, nhưng chưa đủ bằng chứng về mục đích che giấu dấu vết; không mặc định xác nhận kỹ thuật này. |
| 11 | Kết thúc | Hàm kết thúc sau một lượt xử lý | — | Không ánh xạ độc lập | — | File không tự lặp lại; lịch chạy phụ thuộc Scheduled Task. |

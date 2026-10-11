# Changelog

Tất cả những thay đổi và cập nhật quan trọng của dự án **USB Monitor & Logger** sẽ được ghi lại trong tài liệu này.

Định dạng tuân theo chuẩn [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Phiên bản áp dụng chuẩn [Semantic Versioning](https://semver.org/).

---

## [1.2.0] - 2026-10-12

### 🚀 Tính năng mới (Added)
- **Kiến trúc Win32 Event-Driven 100%:** Sử dụng trực tiếp `kernel32.ReadDirectoryChangesW` thay thế hoàn toàn vòng lặp polling `os.walk`. Mức tiêu hao CPU về đúng **0.0%**, không đọc/ghi đĩa liên tục, không gây nóng máy.
- **Hỗ trợ giám sát Container VeraCrypt:** Tự động phát hiện khi file container (ví dụ `Private.hc`) được mở khóa thành ổ ảo (ví dụ `Z:\`), ghi nhận sự kiện Mount/Unmount, tự động vẽ thêm nhánh cây thư mục của VeraCrypt vào `root.txt` và ghi log chi tiết mọi thao tác file bên trong vùng mã hóa.
- **Bộ công cụ Gỡ cài đặt (Uninstall):** Thêm file `uninstall_autorun.bat` và `uninstall_autorun_pc.ps1` cho phép gỡ bỏ hoàn toàn Scheduled Task khỏi hệ thống Windows chỉ bằng 1 cú nhấp đúp.
- **Cơ chế Single-Instance Named Mutex:** Đảm bảo chỉ có duy nhất 1 tiến trình giám sát chạy trên mỗi ổ USB, ngăn ngừa việc click chuột nhiều lần gây xung đột ghi file log.
- **Kích hoạt tức thì khi cài đặt:** Cải tiến `setup_autorun.bat` để vừa đăng ký Task Scheduler, vừa tự động bật ngầm ứng dụng ngay tại chỗ cho phiên hiện tại.
- **Nhận diện Di chuyển file thông minh (Smart Move Pairing on FAT32):** Tự động nhận diện thao tác Cut-Paste (`Ctrl + X` & `Ctrl + V`) trên phân vùng FAT32, ghép đôi sự kiện `Delete` ở thư mục nguồn và `In` ở thư mục đích thành 1 sự kiện `Move` duy nhất (`Move FolderA/file to FolderB/`).
- **Cơ chế Nhịp tim & Hồi cứu phiên khi rút USB (Heartbeat & Session Auto-Recovery):** Chạy luồng Heartbeat định kỳ mỗi 10 giây ghi lại mốc hoạt động gần nhất vào `state.json`. Khi USB bị rút đột ngột khỏi máy, thời gian rút `plug_out` và thời lượng phiên `duration_seconds` vẫn được bảo toàn chuẩn xác, không còn bị giá trị `null`. Tự động chốt lại các phiên dở dang khi cắm USB lần tiếp theo.
- **Trình biên dịch tự động 1-Click:** Thêm `build.bat` giúp lập trình viên tự động đóng gói `usb_monitor.py` thành `USB_Monitor.exe` với PyInstaller.

### 🛠️ Sửa lỗi & Tối ưu (Fixed & Optimized)
- **Sửa lỗi mã hóa Batch & PowerShell:** Chuẩn hóa toàn bộ file `.bat` và `.ps1` sang 100% pure ASCII không dấu, triệt tiêu hoàn toàn các lỗi `cmd.exe` (`'và' is not recognized...`) và lỗi PowerShell (`TerminatorExpectedAtEndOfString`).
- **Khắc phục lỗi Access Violation 64-bit:** Khai báo đầy đủ chữ ký 64-bit Win32 API (`argtypes` & `restype`) và cơ chế bounded memory buffer cho Clipboard `CF_HDROP`, ngăn ngừa lỗi crash `0xc0000005` trong `_ctypes.pyd`.
- **Định vị đường dẫn gốc chuẩn xác:** Sửa lỗi PyInstaller onefile khiến ứng dụng nhận diện nhầm ổ `C:\`, đảm bảo ứng dụng luôn gắn chặt vào ổ đĩa USB thực tế.
- **Khử trùng lặp sự kiện:** Tự động loại bỏ sự kiện `Modify` thừa ngay sau khi một file mới vừa được thêm (`In`/`Add`).

---

## [1.1.0] - 2026-10-11

### 🚀 Tính năng mới
- **Bộ đệm thông minh (Smart Debounce & Batching):** Gom nhóm sự kiện với cửa sổ 1.5 giây và ngưỡng 8 file. Khi người dùng copy hàng loạt file (ảnh, nhạc, tài liệu), hệ thống tự động gộp thành 1 dòng tóm tắt thay vì tràn ngập log.
- **Cây thư mục Folder-Only (`root.txt`):** Tạo sơ đồ cây thư mục trực quan, chỉ liệt kê folder (kết thúc bằng `/`), bỏ qua file rác và thư mục hệ thống.

---

## [1.0.0] - 2026-10-10

### 🚀 Phát hành ban đầu
- Theo dõi các thao tác file: Thêm vào (`In`), Copy ra ngoài máy (`Out`), Tạo mới (`Add`), Di chuyển (`Move`), Xóa (`Delete`).
- Đếm số lần cắm USB và ghi nhận thời lượng phiên làm việc trong `.usb_data/state.json`.
- Định dạng xuất đa dạng: Text (`log_history.txt`) và Markdown (`log_history.md`).

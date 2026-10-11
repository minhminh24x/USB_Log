# 🔌 USB Monitor & Activity Logger (Universal Portable)

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.2.0-blue.svg" alt="Version 1.2.0" />
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg?logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/CPU%20Usage-0.0%25%20(Zero--Polling)-success.svg" alt="Zero Polling" />
  <img src="https://img.shields.io/badge/VeraCrypt-Supported-9cf.svg" alt="VeraCrypt Supported" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT" />
</p>

Một giải pháp **giám sát, kiểm toán và đếm số lần cắm/rút USB di động (Portable USB Audit & Activity Logger)**, hoạt động hoàn toàn độc lập trên mọi thiết bị Windows mà **không cần cài đặt Python** hay bất kỳ phần mềm bên thứ ba nào.

Ứng dụng được thiết kế theo tiêu chuẩn **Passive Read Listener**: Tuyệt đối không can thiệp, không mã hóa và không làm thay đổi bất kỳ dữ liệu có sẵn nào trên USB của bạn.

---

## ✨ Tính Năng Nổi Bật

- ⚡ **Kiến Trúc Win32 Event-Driven 100% (Zero-Polling):** Sử dụng trực tiếp `kernel32.ReadDirectoryChangesW` từ Windows Kernel. Chỉ thức dậy khi có I/O event thực tế, **tiêu hao đúng 0.0% CPU**, không đọc/ghi đĩa liên tục gây nóng máy hay nhấp nháy đèn USB.
- 🔐 **Hỗ Trợ Giám Sát Vùng Mã Hóa VeraCrypt:** Tự động phát hiện khi container (`.hc`) được mở khóa thành ổ đĩa ảo (ví dụ `Z:\`), ghi log sự kiện Mount/Unmount và giám sát chi tiết các thao tác bên trong vùng mã hóa với tiền tố `[VeraCrypt-Z:]`.
- 🔢 **Bộ Đếm Số Lần Cắm & Thời Lượng Phiên (Session Tracking):** Tự động đếm tăng số lần cắm USB vào máy (`SESSION #1`, `#2`...), tính toán chính xác thời gian cắm (`plug_in`), thời gian rút (`plug_out`) và tổng thời lượng phiên.
- 🌳 **Cây Thư Mục Trực Quan (`root.txt`):** Tự động vẽ sơ đồ cây thư mục (chỉ gồm Folder kèm ký tự `/`), tự động làm mới mỗi khi cắm USB hoặc khi có thư mục mới được tạo/xóa.
- 📦 **Gom Nhóm Thông Minh (Smart Debounce & Batching):** Sử dụng cửa sổ 1.5 giây. Khi người dùng copy số lượng lớn file (> 8 items), hệ thống tự động gộp thành 1 dòng tóm tắt súc tích thay vì làm tràn ngập file log.
- 📋 **Phát Hiện Copy Ra Ngoài (Clipboard Out Tracking):** Bắt sự kiện người dùng nhấn `Ctrl + C` trên USB và dán ra máy tính chủ.
- 🚀 **Hỗ Trợ 100% Gỡ Cài Đặt (Uninstall):** Tích hợp sẵn bộ công cụ gỡ bỏ hoàn toàn Scheduled Task khỏi hệ thống chỉ bằng 1 cú nhấp chuột.
- 🛡️ **An Toàn Bộ Nhớ 64-bit & Single-Instance Mutex:** Sử dụng Windows Named Mutex chống chạy trùng lặp nhiều tiến trình, cấu hình bộ đệm bounded buffer ngăn ngừa triệt để lỗi crash hệ thống.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
usb_log/
├── .gitignore                   # Loại trừ file rác, cache, giữ file chạy phân phối
├── README.md                    # Tài liệu giới thiệu tổng quan & hướng dẫn
├── LICENSE                      # Giấy phép mã nguồn mở MIT
├── CHANGELOG.md                 # Lịch sử cập nhật phiên bản chi tiết
├── VERSION                      # Phiên bản hiện tại (1.2.0)
├── requirements.txt             # Thư viện build (pyinstaller)
├── build.bat                    # Script 1-click tự động biên dịch USB_Monitor.exe
├── usb_monitor.py               # Toàn bộ mã nguồn Engine cốt lõi
│
├── USB_Log/                     # THƯ MỤC PHÂN PHỐI PORTABLE (Copy vào USB)
│   ├── USB_Monitor.exe          # Bản chạy độc lập 8.5MB (chạy ngầm, không cần Python)
│   ├── setup_autorun.bat        # [1-Click] Cài tự động chạy khi cắm USB vào máy
│   ├── setup_autorun_pc.ps1     # Script PowerShell đăng ký Task Scheduler
│   ├── uninstall_autorun.bat    # [1-Click] GỠ CÀI ĐẶT tự động chạy khỏi máy tính
│   ├── uninstall_autorun_pc.ps1 # Script PowerShell gỡ bỏ Task Scheduler & dừng tiến trình
│   ├── create_stealth_usb.ps1   # Công cụ thiết lập chế độ tàng hình (System/Hidden)
│   ├── HUONG_DAN_SU_DUNG.md     # Hướng dẫn sử dụng chi tiết (Markdown)
│   └── HUONG_DAN_SU_DUNG.txt    # Hướng dẫn nhanh cho người dùng cuối
│
└── docs/                        # Tài liệu kỹ thuật nâng cao
    ├── ARCHITECTURE.md          # Chi tiết kỹ thuật Win32 Event-Driven & VeraCrypt
    └── ROADMAP.md               # Tầm nhìn scale dự án (GUI, Cloud Alert, Encryption)
```

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh

### Bước 1: Sao chép vào USB
Tải hoặc copy toàn bộ thư mục **`USB_Log/`** vào thư mục gốc trên USB của bạn (ví dụ: `E:\USB_Log`).

### Bước 2: Chọn 1 trong 3 cách vận hành

#### CÁCH 1: Khởi chạy tức thì bằng chuột (Quick Run)
* Mở thư mục `E:\USB_Log`.
* Nhấp đúp chuột vào file **`USB_Monitor.exe`**.
* Ứng dụng sẽ tự động ẩn xuống chạy ngầm trong Windows, ghi nhận phiên cắm và bắt đầu ghi log.

#### CÁCH 2: Khởi chạy bằng lệnh hoặc script (Command Line)
* **Bằng PowerShell:**
  ```powershell
  Start-Process "E:\USB_Log\USB_Monitor.exe" -WindowStyle Hidden
  ```
* **Bằng CMD:**
  ```cmd
  start "" /B "E:\USB_Log\USB_Monitor.exe"
  ```

#### CÁCH 3: Cài đặt tự động chạy 100% khi cắm USB vào máy (Permanent Auto-Run)
* Dành cho máy tính cá nhân: **Cứ cắm chiếc USB này vào là máy tính tự động bật ngầm ứng dụng**, không cần phải mở thủ công.
* **Thao tác:** Mở `E:\USB_Log`, nhấp đúp vào **`setup_autorun.bat`** *(chọn Yes khi UAC hỏi quyền Admin)*.
* **Hoàn tất!** Script sẽ đăng ký tác vụ trong Windows Task Scheduler và tự kích hoạt luôn ứng dụng cho phiên hiện tại.

---

## 🗑️ Cách Gỡ Cài Đặt (Uninstall)

Khi bạn muốn hủy tính năng tự động chạy trên một máy tính nào đó:
1. **Cách 1 (Nhanh nhất):** Mở thư mục `USB_Log` trên USB, nhấp đúp vào **`uninstall_autorun.bat`**.
2. **Cách 2 (Thủ công):** Mở PowerShell với quyền Administrator và chạy lệnh:
   ```powershell
   schtasks /delete /tn AutoLaunch_USB_Logger /f
   ```

---

## 📊 Xem Lại Nhật Ký Trên USB

Toàn bộ kết quả được lưu trữ an toàn trong thư mục **`E:\USB_Log\USB_Logs\`**:

1. **Sơ đồ cây thư mục:** Mở file **`root.txt`** để xem phân cấp folder trên USB (kết thúc bằng dấu `/`).
2. **Nhật ký thao tác:**
   - [log_history.txt](file:///d:/Code/01_Playground/usb_log/USB_Log/USB_Logs/log_history.txt): File nhật ký văn bản.
   - [log_history.md](file:///d:/Code/01_Playground/usb_log/USB_Log/USB_Logs/log_history.md): File nhật ký định dạng Markdown trực quan.
3. **Bộ đếm phiên:** Mở file `E:\USB_Log\.usb_data\state.json` để xem chi tiết lịch sử từng lần cắm.

*Ví dụ định dạng log:*
```text
================================================================================
SESSION #1 | PLUG-IN: 2026/10/12 01:34:09 | DRIVE: [E:] (KINGSTON (FAT32))
TỔNG SỐ LẦN CẮM ĐẾN NAY: 1 LẦN
================================================================================

2026/10/12 01:34:56 In Document/report.pdf
2026/10/12 01:34:58 Delete Trash/temp.tmp
2026/10/12 01:35:10 Out Media/video_demo.mp4
2026/10/12 01:36:00 In Music/ and 50 items (.mp3)
2026/10/12 01:37:05 [VeraCrypt] Đã MOUNT Container thành ổ đĩa [Z:] (SECURE_DATA)
2026/10/12 01:37:20 [VeraCrypt-Z:] In Private_Docs/contract.docx
2026/10/12 01:40:00 [VeraCrypt] Đã UNMOUNT Container khỏi ổ đĩa [Z:]
```

---

## 🛠️ Hướng Dẫn Dành Cho Lập Trình Viên (Build từ Source)

Nếu bạn muốn chỉnh sửa mã nguồn hoặc tự biên dịch lại file `.exe`:

1. **Yêu cầu:** Python 3.10 trở lên trên Windows.
2. **Cài đặt thư viện:**
   ```cmd
   pip install -r requirements.txt
   ```
3. **Biên dịch 1-Click bằng Batch script:**
   Chỉ cần nhấp đúp vào **`build.bat`** (hoặc chạy lệnh):
   ```cmd
   python -m PyInstaller --clean --onefile --noconsole --name USB_Monitor --distpath USB_Log usb_monitor.py
   ```
4. File nhị phân độc lập sẽ được xuất tự động vào: `USB_Log\USB_Monitor.exe`.

---

## 🗺️ Tầm Nhìn Phát Triển & Mở Rộng (Roadmap)

Dự án có lộ trình phát triển rõ ràng với các mục tiêu tiếp theo:
- **v2.0:** Mã hóa file log đầu cuối (AES-256-GCM), giao diện Web Dashboard / Tray GUI xem timeline trực quan.
- **v2.5:** Gửi cảnh báo tức thì qua Telegram Bot / Discord Webhook khi có hành vi bất thường.
- **v3.0:** Mở rộng đa nền tảng Linux (`inotify`) và macOS (`FSEvents`).

👉 Xem chi tiết tại [docs/ROADMAP.md](file:///d:/Code/01_Playground/usb_log/docs/ROADMAP.md).

---

## 📄 Bản Quyền & Giấy Phép (License)

Dự án được phân phối dưới giấy phép mã nguồn mở **MIT License**. Bạn được toàn quyền sử dụng, sửa đổi và phân phối lại cho mục đích cá nhân hoặc thương mại. Xem chi tiết tại tệp [LICENSE](file:///d:/Code/01_Playground/usb_log/LICENSE).

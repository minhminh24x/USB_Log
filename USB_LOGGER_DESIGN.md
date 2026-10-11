# TÀI LIỆU THIẾT KẾ & TỔNG HỢP: HỆ THỐNG GHI LOG VÀ ĐẾM LẦN CẮM USB (PORTABLE)

> **Mô hình hoạt động:** Ứng dụng Portable chạy trực tiếp từ USB (tương tự cơ chế của VeraCrypt Portable), không cần cài đặt, tự động nhận diện ổ đĩa USB hiện tại, ghi log file ra/vào và đếm chính xác số lần cắm/rút.

---

## 1. TỔNG QUAN YÊU CẦU & MỤC TIÊU

| Tiêu chí | Mô tả chi tiết |
| :--- | :--- |
| **Môi trường chạy** | Chạy trực tiếp từ USB (Portable), không cần cài đặt dependencies hay runtime. |
| **Ghi nhận thay đổi file** | Bắt đầy đủ các sự kiện: `In` (chép vào), `Out` (chép ra ngoài), `Add` (tạo mới), `Move` (di chuyển/đổi tên), `Delete` (xóa). |
| **Quy chuẩn định dạng** | - Thời gian chuẩn: `YYYY/MM/DD HH:mm:ss`<br>- Thư mục luôn có hậu tố `/` (ví dụ: `Photo/`, `Secret/`)<br>- File có đầy đủ phần mở rộng (ví dụ: `image.png`, `Mov04.mp4`). |
| **Gom nhóm thông minh (Batching)** | Khi phát hiện thao tác hàng loạt (nhiều file trong cùng thư mục), tự động gộp log để chống tràn (ví dụ: `In Photo/ and 105 images (.png, .jpg)`). |
| **Đếm số lần cắm/rút USB** | Tự động tăng biến đếm số lần cắm (Plug-in Count) mỗi phiên, ghi nhận thời gian cắm vào và thời gian rút/tắt (Session Duration). |
| **Định dạng xuất log** | Hỗ trợ đồng thời hoặc tùy chọn: `.txt`, `.md`, `.json`, `.xlsx`. |

---

## 2. CƠ CHẾ HOẠT ĐỘNG KIỂU PORTABLE (TƯƠNG TỰ VERACRYPT)

### 2.1. Cách thức khởi tạo & Tự định vị
* Khi người dùng mở file chạy (ví dụ `USB_Monitor.exe`) trên USB:
  1. **Tự định vị ổ đĩa (Self Root Detection):** Ứng dụng lấy đường dẫn thực thi của chính nó (`GetModuleFileName` hoặc `AppDomain.CurrentDomain.BaseDirectory`), trích xuất ký tự ổ đĩa (ví dụ `E:\`, `F:\`).
  2. **Tải trạng thái lịch sử:** Đọc file dữ liệu nội bộ `data/state.json` (nằm trên USB) để đọc số lần cắm trước đó.
  3. **Khởi tạo phiên mới (Session Start):** 
     * `Plug Count = Plug Count + 1`
     * Ghi nhận mốc thời gian cắm: `Plug-in: 2026/10/11 23:30:00`.
     * Cập nhật ngay lập tức vào file trạng thái để tránh mất dữ liệu nếu bị rút đột ngột.
  4. **Kích hoạt trình lắng nghe (File System Watcher):** Bắt đầu theo dõi toàn bộ cây thư mục trên USB.
  5. **Chạy ngầm (Silent / System Tray):** Ẩn cửa sổ Console, chỉ hiển thị biểu tượng icon nhỏ góc dưới thanh tác vụ (Tray Icon) để không làm phiền người dùng.

### 2.2. Các cơ chế kích hoạt tự động (Auto-run Solutions)
Do hệ điều hành Windows đã vô hiệu hóa tính năng tự chạy (`autorun.inf`) từ thời Windows 7 để ngăn chặn mã độc, dưới đây là các phương án khả thi để phần mềm **tự động chạy** mà không cần mở thủ công:

#### A. Đối với máy tính cá nhân / máy quen thuộc (Tự động 100% cực kỳ dễ)
* **Phương án 1 (Windows Task Scheduler - Khuyên dùng):** 
  * Cấu hình 1 tác vụ chạy ngầm trên Windows lắng nghe sự kiện cắm thiết bị lưu trữ (`Event ID: 2003` hoặc `2100` tại `Microsoft-Windows-DriverFrameworks-UserMode/Operational`).
  * Ngay khi phát hiện ổ USB được cắm vào, Windows tự động kích hoạt file `USB_Monitor.exe` ngầm mà không cần người dùng thao tác.
* **Phương án 2 (Background Agent):** 
  * Cài 1 service hoặc script siêu nhẹ (chạy cùng Windows Startup) chuyên theo dõi ổ đĩa USB, cứ phát hiện cắm USB là gọi tiến trình ghi log.

#### B. Đối với máy lạ / máy người khác (Không can thiệp cấu hình trước)
* **Phương án 3 (Kỹ thuật ngụy trang Icon / Stealth Wrapper):**
  * Đổi icon của file thực thi thành **Icon Thư mục màu vàng** và đặt tên hấp dẫn như `Documents/`, `Photos/` hoặc `Data/`.
  * Khi người khác cắm USB vào, thói quen tự nhiên là nhấp đúp để mở thư mục.
  * Khi click: Ứng dụng âm thầm kích hoạt ghi log ở chế độ nền, đồng thời tự động mở cửa sổ thư mục thật ra màn hình $\rightarrow$ Người dùng không hề nhận ra sự khác biệt.
* **Phương án 4 (Phần cứng USB HID / BadUSB - Tự gõ lệnh trong 0.2s):**
  * Sử dụng vi điều khiển USB (như Raspberry Pi Pico hoặc Digispark).
  * Cắm vào máy tính, nó đóng giả làm bàn phím và tự động bấm tổ hợp `Win + R` -> gõ lệnh chạy file ẩn trên USB -> `Enter` chỉ trong 0.2 giây.
* **Phương án 5 (USB Phần cứng độc lập - Raspberry Pi Zero):**
  * Thiết bị tự chạy bằng CPU và HĐH riêng bên trong USB, hoạt động trên mọi máy tính và thiết bị (TV, Mac, Linux) mà không cần phụ thuộc hệ điều hành chủ.

---

## 3. CƠ CHẾ ĐẾM SỐ LẦN CẮM - RÚT USB (PLUG-IN / PLUG-OUT COUNTER)

### 3.1. Cấu trúc lưu trữ trạng thái (`state.json`)
File này được lưu trong thư mục con ẩn trên USB (ví dụ: `.usb_data/state.json`):

```json
{
  "device_id": "USB_FLASH_A8B1C2",
  "total_plug_count": 14,
  "first_seen": "2026/10/01 08:15:20",
  "last_seen": "2026/10/11 23:25:51",
  "history": [
    {
      "session_id": 13,
      "plug_in": "2026/10/10 14:00:10",
      "plug_out": "2026/10/10 16:45:22",
      "duration_seconds": 9912,
      "files_in": 12,
      "files_out": 2,
      "files_deleted": 0
    },
    {
      "session_id": 14,
      "plug_in": "2026/10/11 23:25:51",
      "plug_out": null,
      "duration_seconds": null,
      "files_in": 0,
      "files_out": 0,
      "files_deleted": 0
    }
  ]
}
```

### 3.2. Bắt sự kiện rút USB (Plug-out / Session Termination)
Do USB có thể bị rút đột ngột (Unsafe Eject) hoặc máy tính tắt:
* **Chiến lược Heartbeat / Flushing:** Cứ mỗi 10 giây một lần, phần mềm cập nhật `last_heartbeat` vào state file. Nếu bị rút đột ngột, phiên đó vẫn lưu được xấp xỉ thời gian hoạt động.
* **Bắt tín hiệu đóng an toàn:** Lắng nghe các thông điệp hệ thống:
  * `WM_QUERYENDSESSION` / `WM_ENDSESSION` (khi Windows tắt/khởi động lại).
  * `WM_DEVICECHANGE` (khi người dùng chọn "Safely Remove Hardware").
  * Sự kiện tắt ứng dụng: Lập tức ghi mốc `Plug-out: YYYY/MM/DD HH:mm:ss`, tính thời gian phiên và đóng file log an toàn.

---

## 4. CHI TIẾT LOGIC GHI LOG CÁC HÀNH ĐỘNG FILE

### 4.1. Định dạng mẫu chuẩn (Specification)

```text
================================================================================
SESSION #14 | PLUG-IN: 2026/10/11 23:25:51 | DRIVE: [E:\]
TOTAL PLUG COUNT TO DATE: 14 LẦN
================================================================================

2026/10/11 23:26:01 Add Photo/
2026/10/11 23:26:15 Move image.png Photo/ to Secret/
2026/10/11 23:26:30 In Movie/
2026/10/11 23:26:32 In Mov04.mp4
2026/10/11 23:27:00 Out Secret/
2026/10/11 23:27:01 Out note.txt
2026/10/11 23:28:10 Delete gay.txt
2026/10/11 23:28:12 Delete Home/
2026/10/11 23:29:45 In Photo/ and 105 images (.png, .jpg)
2026/10/11 23:30:10 Delete Cache/ and 45 files

================================================================================
SESSION #14 ENDED | PLUG-OUT: 2026/10/11 23:35:20 | DURATION: 00:09:29
================================================================================
```

### 4.2. Phân loại sự kiện & Quy tắc định dạng
1. **Thư mục (Directory):** Luôn tự động gắn dấu `/` ở cuối (ví dụ `Photo/`, `Movie/`, `Secret/`).
2. **File đơn lẻ:** Giữ nguyên phần mở rộng (ví dụ `image.png`, `note.txt`).
3. **Phân biệt Hành động:**
   * `Add <Target>`: Tạo mới thư mục hoặc file rỗng trực tiếp trên USB.
   * `In <Target>`: Chép một file hoặc thư mục từ bên ngoài vào USB (phát hiện qua chuỗi sự kiện `Created` + `Modified/Written`).
   * `Out <Target>`: Chép ra ngoài (bắt thông qua Clipboard `CF_HDROP` khi user copy từ USB rồi dán ra máy tính).
   * `Move <Name> <FromFolder/> to <ToFolder/>`: Đổi vị trí hoặc đổi tên file/folder.
   * `Delete <Target>`: Xóa file hoặc thư mục.

### 4.3. Thuật toán gom nhóm (Debounce & Aggregation Window)
Khi người dùng copy cả 1 thư mục chứa hàng trăm file (ví dụ 105 ảnh), hệ điều hành sẽ bắn ra 105 sự kiện `Create` liên tục trong vài giây. Nếu ghi từng dòng sẽ gây giật lag và tràn log.

* **Thuật toán xử lý:**
  1. Sự kiện phát sinh được đưa vào một **Event Buffer** (hàng đợi bộ nhớ đệm).
  2. Đồng hồ đếm lùi **Time Window = 1.5 giây** (Debounce Timer).
  3. Khi không còn sự kiện mới trong 1.5s, tiến hành quét nhóm:
     * Nhóm theo: `Thư mục cha` + `Hành động (In/Delete/...)`.
     * Nếu số lượng file trong cùng thư mục `> THRESHOLD` (mặc định = 10 file):
       * Thống kê các định dạng đuôi file phổ biến (ví dụ: `.png`, `.jpg`, `.raw`).
       * Xuất dòng log tóm tắt:
         `YYYY/MM/DD HH:mm:ss In Photo/ and 105 images (.png, .jpg)`
     * Nếu `<= THRESHOLD`: Ghi chi tiết từng file bình thường.
### 4.4. Tính năng Cây Thư Mục USB (`root.txt` - Snapshot Chỉ Thư Mục)
Nhằm giúp người dùng nắm bắt nhanh sơ đồ cấu trúc phân vùng dữ liệu của USB mà không cần mở duyệt từng file:

* **Nguyên lý hoạt động:**
  1. Mỗi khi cắm USB vào máy, hệ thống tự động quét nhanh toàn bộ các nút thư mục con trên USB (quá trình mất chưa tới 0.02 giây).
  2. Ghi đè (refresh) vào duy nhất một file **`USB_Logs/root.txt`**.
  3. Nếu trong phiên làm việc có thao tác tạo thêm thư mục mới (`Add`) hoặc xóa thư mục (`Delete`), file `root.txt` sẽ **tự động cập nhật lại ngay lập tức**.
* **Đặc tính kỹ thuật:**
  * **Chỉ quét Thư mục (Folder Only):** Hoàn toàn bỏ qua các file dữ liệu, giúp dung lượng file `root.txt` chỉ 1-2KB và hiển thị cực kỳ gọn gàng.
  * **Hậu tố chuẩn `/`:** Mọi thư mục đều có đuôi `/` đúng quy chuẩn thiết kế (`Documents/`, `Photos/`).
  * **Bộ lọc bảo vệ tàng hình:** Tự động loại bỏ các thư mục nội bộ và hệ thống (`.system/`, `.usb_data/`, `USB_Logs/`, `$RECYCLE.BIN/`, `System Volume Information/`).
* **Định dạng mẫu của file `root.txt`:**
  ```text
  ================================================================================
  CÂY THƯ MỤC USB (CHỈ HIỂN THỊ FOLDER)
  CẬP NHẬT LẦN CUỐI: 2026/10/12 00:20:15 | PHIÊN CẮM: #15
  Ổ ĐĨA: E:\ (USB_STORAGE) | TỔNG SỐ THƯ MỤC: 8
  ================================================================================

  E:/
  ├── Documents/
  │   ├── Cong_viec/
  │   └── Ca_nhan/
  ├── Photos/
  │   ├── 2025/
  │   └── 2026/
  ├── Movies/
  └── Secret/
  ```

### 4.5. Module Giám Sát Mở Rộng: Ổ Đĩa Ảo Mã Hóa VeraCrypt
Đặc biệt tối ưu hóa cho người dùng sử dụng VeraCrypt (như file container `Private.hc`):

* **Vấn đề kỹ thuật:** Khi chưa mount, file container chỉ là một khối dữ liệu nhị phân mã hóa nguyên khối. Nhưng khi người dùng nhập mật khẩu và mount ra ổ đĩa ảo (ví dụ `Z:\`), mọi file mật nằm trên ổ ảo `Z:\` chứ không nằm trên ổ USB gốc `E:\`.
* **Cơ chế phát hiện tự động (Auto-Detection):**
  1. Engine liên tục kiểm tra danh sách ổ đĩa logic trên Windows (`GetLogicalDrives`).
  2. Ngay khi phát hiện có ổ đĩa mới xuất hiện (do VeraCrypt mount ra):
     * Ghi nhận log: `YYYY/MM/DD HH:mm:ss [VeraCrypt] Đã MOUNT Container thành ổ đĩa [Z:] (FAT32/NTFS)`.
     * Tự động khởi tạo một luồng quan sát phụ gắn trực tiếp vào ổ đĩa ảo `Z:\`.
  3. Mọi thao tác thêm/xóa/sửa/copy bên trong ổ ảo VeraCrypt được ghi nhận chi tiết với tiền tố:
     * `YYYY/MM/DD HH:mm:ss [VeraCrypt-Z:] In Secret_Folder/`
     * `YYYY/MM/DD HH:mm:ss [VeraCrypt-Z:] In pass.docx`
     * `YYYY/MM/DD HH:mm:ss [VeraCrypt-Z:] Out pass.docx`
     * `YYYY/MM/DD HH:mm:ss [VeraCrypt-Z:] Delete note.txt`
  4. **Cập nhật cây thư mục `root.txt`:** Trong thời gian container đang mount, sơ đồ cây thư mục của vùng mã hóa cũng được vẽ bổ sung vào file `root.txt`.
  5. **Khi người dùng Unmount container:**
     * Ghi nhận log: `YYYY/MM/DD HH:mm:ss [VeraCrypt] Đã UNMOUNT Container khỏi ổ đĩa [Z:]`.
     * Tự động gỡ bỏ trình theo dõi ổ ảo và cập nhật lại `root.txt`.

---

## 5. CÔNG NGHỆ ĐỀ XUẤT CHO BẢN PORTABLE

Để đạt được tiêu chí **chạy mượt mà, độc lập, không cần cài đặt**, có 2 ngôn ngữ phù hợp nhất:

### Lựa chọn tối ưu nhất: **C# (.NET 8 Native AOT)** hoặc **C++ Win32**
* **Tại sao nên dùng:**
  * Biên dịch thành **1 file `.exe` độc lập duy nhất** (Single-file executable, dung lượng chỉ khoảng 5MB - 12MB).
  * Chạy trực tiếp trên Windows 10/11 mà **không đòi hỏi máy tính cài bất kỳ runtime hay thư viện nào**.
  * Tận dụng tối đa Windows API (`ReadDirectoryChangesW`, `AddClipboardFormatListener`, `RegisterDeviceNotification`).
  * Tốc độ phản hồi microsecond, mức tiêu hao RAM cực thấp (< 25MB).

### Lựa chọn thay thế: **Python Standalone (PyInstaller One-File)**
* **Tại sao cân nhắc:** Phát triển cực nhanh, sẵn có các thư viện xử lý Excel (`pandas`, `openpyxl`), JSON, Markdown.
* **Nhược điểm:** File `.exe` đóng gói khoảng 30MB - 40MB và khởi động ban đầu chậm hơn C# khoảng 1-2 giây.

---

## 6. CẤU TRÚC THƯ MỤC TRÊN USB KHI TRIỂN KHAI

```text
USB_DRIVE (E:\)
├── USB_Monitor.exe          <-- File chạy Portable duy nhất (người dùng click mở)
├── USB_Logs/                <-- Thư mục chứa log xuất ra
│   ├── log_history.txt      <-- Log dạng Text
│   ├── log_history.md       <-- Log dạng Markdown
│   ├── log_history.json     <-- Log dạng JSON (phục vụ lập trình / lọc dữ liệu)
│   └── log_history.xlsx     <-- Log dạng Excel (có màu sắc, lọc theo ngày/phiên)
└── .usb_data/               <-- Thư mục ẩn lưu trạng thái
    └── state.json           <-- Lưu số lần cắm, cấu hình ngưỡng gom nhóm
```

---

## 8. HƯỚNG DẪN HOÀN THIỆN: CẤU HÌNH TRÊN USB KINGSTON 128GB DATATRAVELER EXODIA M (DTXM/128GB)

> **Phân tích thiết bị trên hình:**
> - **Model:** Kingston DataTraveler Exodia M 128GB (USB 3.2 Gen 1 - DTXM/128GB).
> - **Đặc tính kỹ thuật:** Đây là dòng USB Flash Drive thương mại tiêu chuẩn (NAND Flash + Controller USB thông thường). Tốc độ đọc ~100MB/s, ghi ~10MB/s.
> - **Định dạng tối ưu:** Khuyên dùng **NTFS** (hỗ trợ file >4GB, bảo mật thư mục ẩn hệ thống `attrib +s +h`, và có USN Journal giúp bắt sự kiện file cực nhạy).

---

### PHẦN A: TRƯỜNG HỢP 1 - TỰ ĐỘNG CHẠY 100% TRÊN MÁY TÍNH CỦA BẠN (TASK SCHEDULER & EVENT VIEWER)

Trên các máy tính của bạn (máy cá nhân, máy làm việc), bạn chỉ cần thiết lập **1 lần duy nhất trong 30 giây**. Sau đó, mỗi khi cắm chiếc Kingston 128GB vào, phần mềm sẽ **tự động bật ngầm 100%**, đếm lần cắm và ghi log mà không cần bấm gì.

#### 1. Nguyên lý hoạt động
Khi chiếc USB Kingston được cắm vào cổng USB, Windows Driver Framework phát sinh một sự kiện hệ thống:
* **Log Name:** `Microsoft-Windows-DriverFrameworks-UserMode/Operational`
* **Event ID:** `2003` hoặc `2100` (Pnp or Device Arrival)
* **Thông tin nhận diện:** Chuỗi Vendor/Product ID chứa `Kingston` hoặc Volume Serial Number của chiếc USB này.

#### 2. Kịch bản cài đặt tự động 1-Click bằng PowerShell (`setup_autorun_pc.ps1`)
Chạy PowerShell với quyền Administrator và thực thi file `setup_autorun_pc.ps1` (đã có sẵn trong thư mục dự án):

```powershell
# Chạy cài đặt tự động 1 click:
.\setup_autorun_pc.ps1
```

*Cơ chế bên trong file `setup_autorun_pc.ps1`:*
* Tự động bật kênh Log `Microsoft-Windows-DriverFrameworks-UserMode/Operational`.
* Sử dụng định dạng XML chuẩn của Windows Task Scheduler với `Event ID 2003 / 2100` để bắt chính xác thời điểm cắm USB.
* Chạy hoàn toàn ngầm (`-WindowStyle Hidden`), tự quét tìm ký tự ổ USB (E:, F:,...) và kích hoạt tiến trình ghi log.

#### 3. Trải nghiệm thực tế
* Bạn cắm USB Kingston vào $\rightarrow$ Windows phát hiện thiết bị $\rightarrow$ Task Scheduler tìm thấy ổ USB $\rightarrow$ Kích hoạt `USB_Monitor` ở chế độ `Hidden`.
* Số lần cắm tự động tăng lên 1, file log bắt đầu theo dõi mọi thao tác.
* Khi bạn rút USB, ứng dụng tự động chốt phiên làm việc và đóng file log an toàn.

---

### PHẦN B: TRƯỜNG HỢP 2 - CẮM VÀO MÁY LẠ / MÁY NGƯỜI KHÁC VỚI USB KINGSTON NÀY

Vì chiếc **Kingston DTXM/128GB** là USB lưu trữ tiêu chuẩn (không phải BadUSB hay Raspberry Pi), hệ điều hành của máy lạ sẽ **chặn hoàn toàn việc tự chạy ngầm độc lập**.

👉 **Giải pháp tối ưu và thực tế nhất:** Áp dụng **Kỹ thuật Seamless Launcher (Thư mục ngụy trang tàng hình)**.

#### 1. Cấu trúc tổ chức file trên USB Kingston 128GB
Format USB sang định dạng **NTFS**, sau đó tổ chức dữ liệu như sau:

```text
KINGSTON_128GB (E:\)
│
├── 📁 Tai_Lieu/                        <-- SHORTCUT HOẶC LAUNCHER ĐƯỢC ĐỔI ICON THÀNH FOLDER VÀNG
│   (Người lạ nhìn vào tưởng là thư mục chứa tài liệu/ảnh của bạn và sẽ bấm mở)
│
└── 📁 .system/                          <-- THƯ MỤC ẨN HỆ THỐNG (Ẩn bằng thuộc tính attrib +s +h)
    ├── usb_monitor.py (hoặc .exe)      <-- Phần mềm ghi log chính
    ├── launcher.vbs                     <-- Script kích hoạt tàng hình
    ├── 📁 Real_Data/                    <-- Nơi bạn lưu dữ liệu thật (Ảnh, Word, Video...)
    ├── 📁 USB_Logs/                     <-- Nơi lưu log (.txt, .md, .json, .xlsx)
    └── 📁 .usb_data/                    <-- Nơi lưu state.json (số lần cắm)
```

#### 2. Cơ chế kích hoạt kép (Dual-Action Execution)
Khi người khác cắm USB vào máy của họ:
1. Họ mở ổ USB ra và chỉ nhìn thấy duy nhất mục **`📁 Tai_Lieu`** (hoặc `📁 Photos`).
2. Họ **nhấp đúp chuột** vào đó để xem file bên trong:
   * **Hành động ngầm (0.05 giây):** Hệ thống kích hoạt trình ghi log chạy ngầm hoàn toàn, biến đếm số lần cắm tăng thêm 1, tiến trình ghi log bắt đầu.
   * **Hành động hiển thị:** Cửa sổ Windows Explorer của thư mục thật `E:\.system\Real_Data` lập tức bật lên trước mắt họ.
3. **Kết quả:** Người dùng xem, copy, sửa, xóa file hoàn toàn bình thường mà **không hề hay biết** rằng mọi hành vi đang được ghi lại chi tiết vào file log trong thư mục ẩn!

#### 3. Cách tạo file Launcher tàng hình (`launcher.vbs`)
File này dùng để kích hoạt ứng dụng mà **không hề hiện bất kỳ màn hình đen console nào**:

```vbscript
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 1. Chạy ngầm phần mềm ghi log USB_Monitor
If fso.FileExists(currentDir & "\USB_Monitor.exe") Then
    WshShell.Run Chr(34) & currentDir & "\USB_Monitor.exe" & Chr(34), 0, False
ElseIf fso.FileExists(currentDir & "\usb_monitor.py") Then
    WshShell.Run "python " & Chr(34) & currentDir & "\usb_monitor.py" & Chr(34), 0, False
End If

' 2. Mở thư mục dữ liệu thật cho người dùng xem bình thường
WshShell.Run "explorer.exe " & Chr(34) & currentDir & "\Real_Data" & Chr(34), 1, False
```

#### 4. Cách ẩn giấu thư mục `.system` tuyệt đối trên Windows
Mở CMD tại ổ USB và chạy lệnh:
```cmd
attrib +s +h +r "E:\.system"
```
* Lệnh này biến `.system` thành **Thư mục Hệ thống được bảo vệ (Protected Operating System Folder)**.
* Cho dù máy tính của người lạ có bật tùy chọn *"Show hidden files, folders, and drives"* trong Windows Explorer, thư mục `.system` này **vẫn biến mất hoàn toàn** và không thể nhìn thấy!

---

## 9. TỔNG KẾT SO SÁNH 2 TRƯỜNG HỢP VỚI CHIẾC USB KINGSTON 128GB

| Tiêu chí | Trường hợp 1 (Máy của bạn) | Trường hợp 2 (Máy lạ / Người khác) |
| :--- | :--- | :--- |
| **Thao tác khi cắm** | Cắm vào là xong (Tự động 100%) | Người lạ nhấp đúp vào thư mục `Tai_Lieu` |
| **Công nghệ kích hoạt** | Windows Task Scheduler + Event Log | Kỹ thuật Seamless Launcher + VBScript |
| **Ghi nhận Plug Count** | Tự động ngay khi cắm | Tăng ngay khi người lạ mở thư mục |
| **Ghi nhận Log file** | Toàn bộ từ lúc cắm đến lúc rút | Bắt đầu từ lúc người lạ mở thư mục |
| **Độ an toàn / Tàng hình** | Chạy ngầm trong tiến trình Windows | Ngụy trang 100% bằng Icon thư mục vàng |

---

## 10. HƯỚNG DẪN THỰC HÀNH TỪ A - Z (QUICK START)

Khi bạn chép toàn bộ thư mục **`USB_Log`** vào ổ USB (ví dụ: `E:\USB_Log`), chiếc USB của bạn trở thành một bộ công cụ di động độc lập. Dưới đây là **3 cách vận hành**:

### Cách 1: Khởi chạy tức thì bằng chuột (Quick Run / Test)
* Mở ổ USB, đi vào thư mục `E:\USB_Log`.
* **Nhấp đúp chuột vào file `USB_Monitor.exe`**.
* Ứng dụng sẽ tự động ẩn xuống chạy ngầm trong tiến trình Windows:
  * Tự động tăng số lần cắm (Plug Count) trong phiên.
  * Tự động quét toàn bộ cây thư mục trên USB (`Document/`, `Media/`, `Music/`, `VeraCrypt/`,...) và tạo file `E:\USB_Log\USB_Logs\root.txt`.
  * Bắt đầu theo dõi mọi hành vi copy file ra/vào.

### Cách 2: Khởi chạy bằng câu lệnh ngầm (PowerShell / CMD)
* Mở PowerShell và gõ:
  ```powershell
  Start-Process "E:\USB_Log\USB_Monitor.exe" -WindowStyle Hidden
  ```
* Hoặc chạy bằng CMD:
  ```cmd
  start "" /B "E:\USB_Log\USB_Monitor.exe"
  ```

### Cách 3: Cài đặt Tự động chạy vĩnh viễn trên máy tính (Permanent Auto-run)
* Mở thư mục `E:\USB_Log` trên USB.
* Nhấp chuột phải vào file **`setup_autorun_pc.ps1`** $\rightarrow$ Chọn **Run with PowerShell** *(chọn Yes khi hỏi quyền Administrator)*.
* **Kết quả:** Windows Task Scheduler trên máy tính đó sẽ được ghi nhớ tác vụ `AutoLaunch_USB_Logger`.
  * Kể từ đó, mỗi khi cắm USB vào máy này, Windows sẽ **tự động gọi file `E:\USB_Log\USB_Monitor.exe`** chạy ngầm 100%.
  * Mang sang máy khác, bạn chỉ cần chạy lại file script này 1 lần trên máy đó là xong.

---

## 11. CÂU HỎI THƯỜNG GẶP & XỬ LÝ SỰ CỐ (FAQ)

### Q1: Làm thế nào để xem file Log khi thư mục `.system` đang bị ẩn hoàn toàn?
* **Cách 1:** Mở Windows Explorer, click vào thanh địa chỉ ở trên cùng và gõ:
  `E:\.system\USB_Logs` rồi nhấn `Enter`. Cửa sổ chứa toàn bộ file log `.txt`, `.md`, `.json` sẽ hiện ra ngay lập tức.
* **Cách 2:** Chạy lệnh bỏ ẩn trong CMD:
  `attrib -s -h "E:\.system"`

### Q2: Muốn đóng gói `usb_monitor.py` thành 1 file `.exe` độc lập thì làm thế nào?
* Trong thư mục dự án, chạy lệnh:
  ```powershell
  pip install pyinstaller
  pyinstaller --noconsole --onefile usb_monitor.py -n USB_Monitor
  ```
* File `USB_Monitor.exe` sinh ra trong thư mục `dist/` có thể copy thẳng vào USB và chạy độc lập trên mọi máy Windows không cần cài Python.

### Q3: Nếu muốn gỡ bỏ tính năng tự động chạy trên máy tính thì làm thế nào?
* Chạy lệnh PowerShell với quyền Administrator:
  ```powershell
  schtasks /delete /tn AutoLaunch_Kingston_Logger /f
  ```

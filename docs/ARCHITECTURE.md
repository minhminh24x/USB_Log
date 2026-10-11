# 🏛️ Kiến Trúc Hệ Thống (System Architecture & Technical Design)

Tài liệu này mô tả chi tiết kiến trúc kỹ thuật nội bộ của **USB Monitor & Logger**, giải thích các quyết định thiết kế (Design Decisions) và cách thức hoạt động ở tầng thấp của hệ điều hành Windows.

---

## 1. Tổng Quan Kiến Trúc

Hệ thống hoạt động theo mô hình **Event-Driven Non-Intrusive Engine**:

```
+---------------------------------------------------------------------------------+
|                                WINDOWS KERNEL                                   |
|   +-----------------------+     +-------------------+     +-----------------+   |
|   |  I/O Completion Port  |     |  User32 Clipboard |     | EventLog ID 2003|   |
|   | (File System Changes) |     |    (CF_HDROP)     |     |   (USB Plug-in) |   |
+---+-----------+-----------+-----+---------+---------+-----+--------+------------+
                |                           |                            |
                v                           v                            v
+---------------+---------------------------+----------------------------+--------+
|                                USB MONITOR ENGINE                               |
|                                                                                 |
|   +-----------------------+     +-------------------+     +-----------------+   |
|   | ReadDirectoryChangesW |     |   Clipboard Out   |     | Windows Task    |   |
|   |     Worker Thread     |     |  Listener Thread  |     |   Scheduler     |   |
|   +-----------+-----------+     +---------+---------+     +--------+--------+   |
|               |                           |                            |        |
|               +-------------> + <---------+                            |        |
|                               |                                        |        |
|                               v                                        |        |
|               +-------------------------------+                        |        |
|               | Smart Debounce Buffer (1.5s)  |                        |        |
|               | - Aggregation (> 8 items)     |                        |        |
|               | - In/Modify Deduplication     |                        |        |
|               +---------------+---------------+                        |        |
|                               |                                        |        |
|                               v                                        v        |
|               +-------------------------------+     +-----------------------+   |
|               |   Log Writers (TXT / MD / JSON)|     | VeraCrypt Lifecycle   |   |
|               |   Folder Tree Generator       |     | Dynamic Drive Watcher |   |
|               +-------------------------------+     +-----------------------+   |
+---------------------------------------------------------------------------------+
```

---

## 2. Chi Tiết Các Phân Hệ Cốt Lõi

### 2.1. Kernel-Level File System Watcher (`kernel32.ReadDirectoryChangesW`)
- **Tại sao không dùng Polling (`os.walk`):**
  - Quét đĩa định kỳ qua USB 2.0/3.0 đối với hàng chục ngàn file gây nghẽn băng thông I/O, tiêu tốn 100% CPU trên một luồng và làm đèn USB nhấp nháy liên tục.
- **Giải pháp Event-Driven:**
  - Mở handle thư mục gốc với cờ `FILE_LIST_DIRECTORY` và `FILE_FLAG_BACKUP_SEMANTICS`.
  - Đăng ký lắng nghe đệ quy toàn bộ cây thư mục qua `kernel32.ReadDirectoryChangesW`.
  - Luồng lắng nghe tự động chuyển sang trạng thái Sleep (Blocked) và chỉ được đánh thức bởi kernel khi Windows thực sự có thay đổi trên đĩa.
  - **Mức tiêu hao tài nguyên:** Đúng **0.0% CPU** và **0 byte đọc đĩa** khi không có thao tác file.

### 2.2. Dynamic VeraCrypt Lifecycle Watcher
- Độc lập phát hiện khi người dùng mở khóa container mã hóa (`.hc`):
  - Chu kỳ 2 giây kiểm tra mặt nạ bit các ổ đĩa qua `kernel32.GetLogicalDrives()`.
  - Khi phát hiện ổ đĩa mới xuất hiện (ví dụ `Z:\`):
    1. Ghi nhận sự kiện Mount kèm tên nhãn ổ đĩa.
    2. Tự động sinh ra một luồng `ReadDirectoryChangesW` riêng biệt gắn chặt vào `Z:\`.
    3. Thêm tiền tố `[VeraCrypt-Z:]` vào mọi sự kiện xảy ra bên trong ổ ảo.
    4. Cập nhật nhánh thư mục của VeraCrypt vào file `root.txt`.
  - Khi container bị Unmount:
    1. Ghi nhận sự kiện Unmount.
    2. Hủy handle bằng `kernel32.CancelIoEx` và đóng luồng giám sát.
    3. Xóa nhánh VeraCrypt khỏi `root.txt`.

### 2.3. Safe Clipboard Out Listener
- **Nguyên lý:** Khi người dùng nhấn `Ctrl + C` trên USB và dán ra Desktop:
  - Clipboard của Windows sẽ chứa định dạng `CF_HDROP` (danh sách đường dẫn file).
  - Ứng dụng đọc cấu trúc `DROPFILES` qua `user32.GetClipboardData`.
  - So sánh đường dẫn file: Nếu file bắt đầu bằng ký tự ổ đĩa USB hoặc ổ đĩa VeraCrypt, hệ thống ghi nhận sự kiện `Out`.
- **An toàn bộ nhớ 64-bit:**
  - Khai báo kiểu dữ liệu 64-bit đầy đủ cho `GetClipboardData` (`HANDLE`), `GlobalLock` (`LPVOID`), `GlobalSize` (`SIZE_T`).
  - Đọc dữ liệu giới hạn chặt chẽ theo kích thước bộ nhớ cấp phát (`GlobalSize`) để ngăn ngừa triệt để lỗi **Access Violation (0xc0000005)**.

### 2.4. Smart Debounce & Grouping Buffer
- **Cửa sổ thời gian:** 1.5 giây.
- **Quy tắc gom nhóm:**
  - Nếu số lượng file trong cùng thư mục cha $\le 8$: Ghi chi tiết từng file.
  - Nếu số lượng file $> 8$: Gộp lại thành một dòng tóm tắt duy nhất:
    ```text
    2026/10/12 01:25:00 In Music/ and 50 items (.mp3)
    ```
- **Khử trùng lặp `Modify`:** Khi một file mới được tạo, hệ thống thường nhận cả sự kiện `Added` và `Modified`. Bộ đệm tự động loại bỏ các sự kiện `Modify` thừa trong cùng chu kỳ, giữ nhật ký luôn súc tích và dễ đọc.

### 2.5. Windows Task Scheduler Event Trigger (Zero Background Service)
- **Cơ chế:** Hoàn toàn KHÔNG cài đặt Background Service hay chạy Service daemon thường trực gây tốn RAM hệ thống.
- **Kỹ thuật:** Đăng ký một tác vụ trong Windows Task Scheduler với Event Trigger:
  - **Log:** `Microsoft-Windows-DriverFrameworks-UserMode/Operational`
  - **Event ID:** `2003` hoặc `2100` (Sự kiện cắm thiết bị lưu trữ USB mới vào hệ thống).
  - **Hành động:** Khi có sự kiện cắm USB, Windows tự động kích hoạt script PowerShell quét tìm ổ USB và khởi chạy ngầm `USB_Monitor.exe`.

### 2.6. Smart Move Pairing on FAT32 (Nhận Diện Cut-Paste & Di Chuyển File)
- **Đặc thù của hệ thống FAT32:**
  - Khác với NTFS có Transactional Object ID, trên hệ thống tệp FAT32 (định dạng phổ biến nhất của USB), khi người dùng thực hiện thao tác **Cut (`Ctrl + X`) $\rightarrow$ Paste (`Ctrl + V`)** hoặc kéo thả file giữa hai thư mục:
  - Trình điều khiển `fastfat.sys` của Windows không phát ra mã `FILE_ACTION_RENAMED` mà chia thành 2 sự kiện độc lập:
    1. `FILE_ACTION_REMOVED` (`Delete`) tại thư mục nguồn.
    2. `FILE_ACTION_ADDED` (`In`) tại thư mục đích.
- **Thuật toán ghép cặp thông minh:**
  - Trong cửa sổ Debounce 1.5 giây, hệ thống tự động quét và đối chiếu các cặp sự kiện `Delete` và `In`/`Add`:
  - Nếu phát hiện cùng tên tệp cơ sở (`basename`) trên cùng một ổ đĩa USB, hệ thống tự động hợp nhất thành **1 sự kiện `Move` duy nhất**:
    ```text
    2026/10/12 01:49:04 Move Music/song.mp3 to Music/Remix/
    ```

### 2.7. Đánh Giá Độ An Toàn Phần Cứng & Tuổi Thọ Chip Nhớ (NAND Flash & Wear Leveling)
- **Không can thiệp phân vùng (Partitions):**
  - Ứng dụng hoạt động ở tầng File System thông thường (tương tự Notepad hay Media Player).
  - Tuyệt đối không can thiệp Partition Table, MBR, GPT, Volume Boot Record hay gọi các hàm `diskpart`/`format`.
- **Tối ưu hao mòn chip nhớ Flash (P/E Cycles):**
  - NAND Flash chỉ hao mòn khi có thao tác **Ghi (Write/Program)** hoặc **Xóa (Erase)**. Thao tác Đọc (Read) không ảnh hưởng tuổi thọ.
  - Khi rảnh rỗi (Idle): Ứng dụng ngủ hoàn toàn (Blocked on Win32 Kernel), **0 byte đọc/ghi đĩa**, chip xử lý USB mát và không nhấp nháy đèn.
  - Khi có thao tác file: Chỉ append 1 dòng text (~80 bytes). Toàn bộ dữ liệu ghi trong 1 ngày sử dụng bình thường **chưa tới 0.05 MB (50 KB)**.
  - So với việc người dùng copy 1 bài hát (10 MB) hay 1 video (1 GB), lượng dữ liệu USB_Log ghi nhỏ hơn hàng trăm nghìn lần, hoàn toàn không ảnh hưởng đến tuổi thọ 5 - 10 năm của chip nhớ.
- **An toàn khi rút USB đột ngột (Sudden Unplug):**
  - Mọi thao tác ghi log đều mở, flush dữ liệu và đóng handle ngay lập tức trong thời gian **< 1ms**.
  - Trong 99.99% thời gian cắm USB, file log luôn ở trạng thái đóng (closed), không giữ handle dang dở, ngăn ngừa nguy cơ hỏng bảng FAT.

---

## 3. Khả Năng Mở Rộng & Tương Thích

| Hệ Điều Hành | Trạng Thái | Công Nghệ Cốt Lõi |
| :--- | :--- | :--- |
| **Windows 10 / 11** | Sẵn sàng (v1.2) | Win32 API, `ReadDirectoryChangesW`, Task Scheduler XML |
| **Windows 7 / 8 / 8.1** | Tương thích ngược | Win32 API, fallback PowerShell v3.0+ |
| **Linux (Roadmap)** | Kế hoạch v3.0 | `inotify`, `systemd` user service / `udev` rule |
| **macOS (Roadmap)** | Kế hoạch v3.0 | `FSEvents`, `launchd` plist agent |

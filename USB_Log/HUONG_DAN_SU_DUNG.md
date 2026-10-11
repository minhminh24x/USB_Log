# HƯỚNG DẪN SỬ DỤNG BỘ CÔNG CỤ GHI LOG & ĐẾM LẦN CẮM USB (UNIVERSAL)

> **Mô hình triển khai:** Thư mục `USB_Log` được chép trực tiếp vào USB (ví dụ: `E:\USB_Log`). Chiếc USB của bạn trở thành một thiết bị mang theo trọn bộ công cụ giám sát, có thể mang sang bất kỳ máy tính Windows nào để sử dụng.

---

## 📦 Danh sách file trong thư mục `USB_Log`

| Tên file | Mô tả |
| :--- | :--- |
| 🚀 **`USB_Monitor.exe`** | **Ứng dụng lõi độc lập:** Tự động giám sát toàn bộ USB, đếm số lần cắm/rút, quét vẽ cây thư mục snapshot (`root.txt`), ghi log thao tác file (`In`, `Out`, `Delete`, `Move`, `Add`). Không cần cài đặt Python. |
| ⚙️ **`setup_autorun_pc.ps1`** | **Script cấu hình Auto-run:** Cài đặt Windows Task Scheduler để máy tính tự động kích hoạt `USB_Monitor.exe` ngầm 100% mỗi khi cắm USB vào. |
| 📁 **`create_stealth_usb.ps1`** | **Script cấu hình ngụy trang tàng hình:** Tự tạo shortcut thư mục `Tai_Lieu` và ẩn hệ thống toàn bộ công cụ giám sát. |
| 📄 **`HUONG_DAN_SU_DUNG.txt`** | File hướng dẫn định dạng Text thuần, mở đọc được trên mọi máy bằng Notepad. |
| 📖 **`HUONG_DAN_SU_DUNG.md`** | File tài liệu định dạng Markdown chi tiết. |

---

## 🛠️ CHI TIẾT 3 CÁCH KHỞI CHẠY VÀ SỬ DỤNG

Sau khi bạn đã chép cả thư mục `USB_Log` vào trong USB (ví dụ nằm tại `E:\USB_Log`):

---

### CÁCH 1: KHỞI CHẠY TỨC THÌ BẰNG CHUỘT (QUICK RUN / TEST)
*Dành cho trường hợp bạn muốn bật giám sát ngay lập tức trên bất kỳ máy nào mà không cần cài đặt gì:*

1. Mở ổ USB, đi vào thư mục **`USB_Log`** (đường dẫn: `E:\USB_Log`).
2. **Nhấp đúp chuột (Double click)** vào file **`USB_Monitor.exe`**.
3. **Hiện tượng diễn ra:**
   * Phần mềm sẽ tự động ẩn xuống chạy ngầm trong tiến trình Windows.
   * Tự động tăng số lần cắm (Plug Count) trong phiên.
   * Tự động quét toàn bộ cây thư mục trên USB (`Document/`, `Media/`, `Music/`, `VeraCrypt/`,...) và tạo file `E:\USB_Log\USB_Logs\root.txt`.
   * Bắt đầu theo dõi mọi hành vi copy file ra/vào.

---

### CÁCH 2: KHỞI CHẠY BẰNG DÒNG LỆNH POWERSHELL / CMD / FILE BAT
*Dành cho trường hợp bạn muốn gọi chạy ngầm hoàn toàn hoặc tích hợp vào các script tự động khác:*

#### A. Chạy bằng PowerShell:
Mở PowerShell và dán lệnh sau (thay `E` bằng ký tự ổ USB):
```powershell
Start-Process "E:\USB_Log\USB_Monitor.exe" -WindowStyle Hidden
```

#### B. Chạy bằng CMD:
Mở Command Prompt và gõ:
```cmd
start "" /B "E:\USB_Log\USB_Monitor.exe"
```

#### C. Tạo phím tắt 1-click tự động chạy ngầm (`start_silent.vbs`):
Bạn có thể tạo 1 file `start_silent.vbs` lưu ngay trong `E:\USB_Log` với nội dung:
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "USB_Monitor.exe", 0, False
```
*Mỗi lần muốn bật, bạn chỉ cần nhấp đúp vào file `.vbs` này là app sẽ chạy ngầm tàng hình 100% không chớp màn hình.*

---

### CÁCH 3: CÀI ĐẶT TỰ ĐỘNG CHẠY 100% KHI CẮM VÀO MÁY (PERMANENT AUTO-RUN)
*Dành cho máy tính cá nhân hoặc các máy tính mà bạn muốn: **Cứ cắm chiếc USB này vào là máy tính tự bật ngầm trình ghi log**, không bao giờ phải nhớ mở thủ công nữa.*

1. Cắm USB vào máy tính muốn thiết lập.
2. Mở thư mục `E:\USB_Log`.
3. **Nhấp đúp chuột (Double-click) vào file `setup_autorun.bat`** *(hoặc chuột phải chọn Run as administrator)*.
   * File batch này sẽ tự động yêu cầu quyền Administrator (UAC), tự động mở khóa chính sách chặn script của Windows và giữ màn hình không bị tắt.
4. **Kết quả:**
   * Script sẽ đăng ký một tác vụ trong Windows Task Scheduler mang tên `AutoLaunch_USB_Logger`.
   * Tác vụ này tự động lắng nghe sự kiện cắm USB qua Event ID hệ thống (`2003 / 2100`).
   * **Từ giây phút này:** Cứ mỗi lần bạn cắm chiếc USB này vào máy tính đó, Windows sẽ **tự động gọi file `E:\USB_Log\USB_Monitor.exe`** chạy ngầm 100%.
5. **Cài cho nhiều máy:** Sau này mang USB sang máy tính thứ 2, thứ 3... bạn chỉ cần thực hiện lại bước 3 trên máy đó là xong.

> [!TIP]
> **Cách gỡ cài đặt tự động chạy (Uninstall):**
> Khi bạn muốn hủy tính năng tự động chạy trên máy tính đó:
> 1. **Cách 1 (Nhanh nhất):** Nhấp đúp vào file **`uninstall_autorun.bat`** trong thư mục `USB_Log` (nó sẽ tự động dừng tiến trình và xóa Task khỏi Windows).
> 2. **Cách 2 (Thủ công):** Mở PowerShell (Run as Administrator) và chạy lệnh:
>    ```powershell
>    schtasks /delete /tn AutoLaunch_USB_Logger /f
>    ```

---

## 🔍 CÁCH XEM LẠI NHẬT KÝ VÀ CÂY THƯ MỤC TRÊN USB

Toàn bộ kết quả được gom gọn gàng trong thư mục: **`E:\USB_Log\USB_Logs\`**:

1. **Xem sơ đồ cây thư mục:** Mở file **`root.txt`**
   * Chỉ hiển thị các thư mục kèm đuôi `/`.
   * Tự động làm mới mỗi khi cắm USB hoặc khi có thư mục mới được tạo/xóa.
2. **Xem chi tiết file ra / vào:**
   * Mở file **`log_history.txt`** (xem dạng text đơn giản).
   * Mở file **`log_history.md`** (xem dạng Markdown đẹp mắt).
   * Mở file **`log_history.json`** (dành cho phần mềm xử lý dữ liệu).
3. **Xem tổng số lần cắm:** Mở file `E:\USB_Log\.usb_data\state.json`.

---

## 🔐 TÍNH NĂNG ĐẶC BIỆT: GIÁM SÁT Ổ ĐĨA ẢO VERACRYPT

Nếu bạn sử dụng file container mã hóa của VeraCrypt (ví dụ: `Private.hc`):
* **Khi chưa mở:** Hệ thống bảo vệ file container, ghi log nếu có ai copy ra ngoài (`Out Private.hc`) hoặc xóa/sửa file.
* **Khi bạn Mount container (ví dụ mở khóa thành ổ ảo `Z:\`):**
  * Ứng dụng tự động phát hiện ổ đĩa ảo mới và ghi nhận: `[VeraCrypt] Đã MOUNT Container thành ổ đĩa [Z:]`.
  * **Tự động theo dõi các file bên trong vùng mã hóa:** Mọi thao tác tạo, copy hay xóa file bên trong ổ ảo `Z:\` sẽ được ghi lại chi tiết với tiền tố `[VeraCrypt-Z:] In ...`, `[VeraCrypt-Z:] Out ...`.
  * Khi bạn Unmount ổ ảo: Ứng dụng ghi nhận `[VeraCrypt] Đã UNMOUNT Container khỏi ổ đĩa [Z:]`.
  * Sơ đồ thư mục của vùng mã hóa cũng được tự động vẽ bổ sung vào file `root.txt` trong lúc container đang mở!

---

## 🛡️ CAM KẾT AN TOÀN DỮ LIỆU
* Phần mềm hoạt động ở chế độ **Passive Read Listener** (chỉ lắng nghe sự kiện hệ điều hành báo về).
* **Tuyệt đối KHÔNG sửa đổi, KHÔNG mã hóa và KHÔNG xóa** bất kỳ dữ liệu sẵn có nào trên USB của bạn (`Document`, `Media`, `VeraCrypt`, `Private.hc`,...).
* **Không cần format USB**, cứ để nguyên dữ liệu và chạy bình thường.

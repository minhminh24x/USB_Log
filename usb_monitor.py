import os
import sys
import time
import json
import atexit
import signal
import threading
from datetime import datetime
from collections import defaultdict
import ctypes
from ctypes import wintypes

# Đảm bảo in tiếng Việt an toàn trên console Windows không bị lỗi bảng mã charmap
if sys.platform == "win32":
    try:
        if sys.stdout:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

# Windows API constants & 64-bit safe ctypes definitions
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

FILE_LIST_DIRECTORY = 0x0001
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE_VALUE = -1

FILE_NOTIFY_CHANGE_FILE_NAME   = 0x0001
FILE_NOTIFY_CHANGE_DIR_NAME    = 0x0002
FILE_NOTIFY_CHANGE_ATTRIBUTES  = 0x0004
FILE_NOTIFY_CHANGE_SIZE        = 0x0008
FILE_NOTIFY_CHANGE_LAST_WRITE  = 0x0010

# Khai báo chuẩn xác 64-bit argtypes & restype để chống lỗi 0xc0000005 Access Violation
kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
]
kernel32.CreateFileW.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

kernel32.CancelIoEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
kernel32.CancelIoEx.restype = wintypes.BOOL

kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE

kernel32.GetLogicalDrives.argtypes = []
kernel32.GetLogicalDrives.restype = wintypes.DWORD

kernel32.GetVolumeInformationW.argtypes = [
    wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD
]
kernel32.GetVolumeInformationW.restype = wintypes.BOOL

kernel32.ReadDirectoryChangesW.argtypes = [
    wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, wintypes.BOOL,
    wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p, ctypes.c_void_p
]
kernel32.ReadDirectoryChangesW.restype = wintypes.BOOL

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL

user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE

kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
kernel32.GlobalLock.restype = ctypes.c_void_p

kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
kernel32.GlobalUnlock.restype = wintypes.BOOL

kernel32.GlobalSize.argtypes = [wintypes.HANDLE]
kernel32.GlobalSize.restype = ctypes.c_size_t

class DROPFILES(ctypes.Structure):
    _fields_ = [
        ("pFiles", wintypes.DWORD),
        ("pt", wintypes.POINT),
        ("fNC", wintypes.BOOL),
        ("fWide", wintypes.BOOL)
    ]


class USBMonitorEngine:
    def __init__(self, target_drive=None):
        # 1. Tự xác định thư mục gốc cần theo dõi (Universal Drive Resolver)
        if target_drive:
            self.root_dir = os.path.abspath(target_drive)
        else:
            if getattr(sys, 'frozen', False):
                app_path = sys.executable
            else:
                app_path = os.path.abspath(__file__)
            
            app_dir = os.path.dirname(os.path.abspath(app_path))
            drive_prefix = os.path.splitdrive(app_dir)[0]
            drive_root = (drive_prefix + "\\") if drive_prefix else app_dir

            # Nếu file nằm trên USB:
            # - Ngay ở root (E:\USB_Monitor.exe)
            # - Hoặc trong thư mục con trực tiếp (E:\USB_Log\..., E:\.system\...)
            parent_dir = os.path.abspath(os.path.join(app_dir, ".."))
            if app_dir.lower() == drive_root.lower():
                self.root_dir = drive_root
            elif parent_dir.lower() == drive_root.lower():
                self.root_dir = drive_root
            else:
                # Nếu đang ở thư mục dev lồng sâu (vd: D:\Code\...\usb_log)
                self.root_dir = app_dir

        self.drive_letter = os.path.splitdrive(self.root_dir)[0]
        self.volume_info = self._get_volume_label(self.drive_letter)

        # 2. Cơ chế Single-Instance Mutex (Tránh mở trùng lặp nhiều tiến trình ngầm)
        clean_drive = self.drive_letter.replace(":", "") if self.drive_letter else "APP"
        mutex_name = f"Global\\USB_Monitor_Instance_{clean_drive}"
        self.instance_mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            safe_print(f"[!] Da co mot tien trinh USB_Monitor dang chay cho [{self.drive_letter}]. Thoat de tranh trung lap.")
            sys.exit(0)

        # 3. Thư mục lưu trữ dữ liệu và log
        if os.path.exists(os.path.join(self.root_dir, "USB_Log")):
            self.system_dir = os.path.join(self.root_dir, "USB_Log")
        elif os.path.exists(os.path.join(self.root_dir, ".system")):
            self.system_dir = os.path.join(self.root_dir, ".system")
        else:
            self.system_dir = self.root_dir

        self.data_dir = os.path.join(self.system_dir, ".usb_data")
        self.logs_dir = os.path.join(self.system_dir, "USB_Logs")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.state_file = os.path.join(self.data_dir, "state.json")
        self.txt_log_file = os.path.join(self.logs_dir, "log_history.txt")
        self.md_log_file = os.path.join(self.logs_dir, "log_history.md")
        self.root_tree_file = os.path.join(self.logs_dir, "root.txt")

        self.is_running = True
        self.session_id = 0
        self.plug_count = 0
        self.session_start_time = None

        # Danh sách handle để đóng khi thoát
        self.active_handles = {}  # {drive_path: hDir}

        # Bộ đệm sự kiện (Debounce / Aggregation Buffer)
        self.event_buffer = []
        self.buffer_lock = threading.Lock()
        self.debounce_timer = None
        self.BATCH_THRESHOLD = 8
        self.DEBOUNCE_INTERVAL = 1.5

        # Theo dõi ổ đĩa ảo VeraCrypt
        self.initial_drives = set(self._get_logical_drives())
        self.active_veracrypt_drives = {}  # {drive_path: thread}

        # Khởi tạo phiên cắm USB
        self._init_session()

    def _get_logical_drives(self):
        """Lấy danh sách các ổ đĩa logic hiện có trên máy tính."""
        drives = []
        try:
            bitmask = kernel32.GetLogicalDrives()
            for i in range(26):
                if bitmask & (1 << i):
                    drives.append(f"{chr(ord('A') + i)}:\\")
        except Exception:
            pass
        return drives

    def _get_volume_label(self, drive):
        """Tự động lấy tên nhãn và định dạng phân vùng của ổ đĩa."""
        try:
            vol_buf = ctypes.create_unicode_buffer(1024)
            fs_buf = ctypes.create_unicode_buffer(1024)
            drive_path = drive.rstrip("\\") + "\\"
            res = kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(drive_path),
                vol_buf, 1024,
                None, None, None,
                fs_buf, 1024
            )
            if res and vol_buf.value:
                return f"{vol_buf.value} ({fs_buf.value})"
            elif res and fs_buf.value:
                return f"USB_DRIVE ({fs_buf.value})"
        except Exception:
            pass
        return "USB_STORAGE"

    def _get_timestamp(self):
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def generate_folder_tree(self):
        """Tạo sơ đồ cây thư mục (chỉ gồm folder, kết thúc bằng /) ghi vào root.txt."""
        ignored_names = {
            ".system", ".usb_data", "usb_logs", "usb_log", "usb-log", "$recycle.bin", 
            "system volume information", "__pycache__", "build", "dist"
        }

        def should_ignore(dir_name):
            d_lower = dir_name.lower()
            return d_lower in ignored_names or d_lower.startswith(".")

        def build_tree(current_dir, prefix=""):
            lines = []
            try:
                entries = sorted([
                    d for d in os.listdir(current_dir) 
                    if os.path.isdir(os.path.join(current_dir, d)) and not should_ignore(d)
                ])
            except Exception:
                return lines

            count = len(entries)
            for index, entry in enumerate(entries):
                is_last = (index == count - 1)
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{entry}/")
                sub_prefix = prefix + ("    " if is_last else "│   ")
                sub_path = os.path.join(current_dir, entry)
                lines.extend(build_tree(sub_path, sub_prefix))
            return lines

        tree_lines = build_tree(self.root_dir)
        total_folders = len(tree_lines)
        
        drive_display = self.drive_letter if self.drive_letter else self.root_dir
        if not drive_display.endswith(("\\", "/")):
            drive_display += "/"

        header = [
            "=" * 80,
            "CÂY THƯ MỤC USB (CHỈ HIỂN THỊ FOLDER)",
            f"CẬP NHẬT LẦN CUỐI: {self._get_timestamp()} | PHIÊN CẮM: #{self.session_id}",
            f"Ổ ĐĨA: {self.drive_letter} ({self.volume_info}) | TỔNG SỐ THƯ MỤC: {total_folders}",
            "=" * 80,
            "",
            f"{drive_display.replace('\\', '/')}"
        ]
        content = "\n".join(header + tree_lines) + "\n"

        # Nếu có ổ đĩa ảo VeraCrypt đang mount, vẽ thêm nhánh cây thư mục của container
        for vc_drive in sorted(self.active_veracrypt_drives.keys()):
            if os.path.exists(vc_drive):
                vc_label = self._get_volume_label(vc_drive)
                vc_lines = build_tree(vc_drive)
                header_vc = [
                    "",
                    "-" * 80,
                    f"VÙNG MÃ HÓA VERACRYPT [{vc_drive.rstrip('\\')}] ({vc_label}) - {len(vc_lines)} THƯ MỤC",
                    "-" * 80,
                    f"{vc_drive.replace('\\', '/')}"
                ]
                content += "\n".join(header_vc + vc_lines) + "\n"

        try:
            with open(self.root_tree_file, "w", encoding="utf-8") as f:
                f.write(content)
            safe_print(f"[+] Da cap nhat cay thu muc vao {self.root_tree_file} ({total_folders} thu muc)")
        except Exception as e:
            safe_print(f"[!] Loi ghi file root.txt: {e}")

    def _init_session(self):
        """Khởi tạo phiên mới và tăng bộ đếm số lần cắm USB."""
        state = {
            "device_name": self.volume_info,
            "total_plug_count": 0,
            "sessions": []
        }
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                pass

        state["device_name"] = self.volume_info
        state["total_plug_count"] = state.get("total_plug_count", 0) + 1
        self.plug_count = state["total_plug_count"]
        self.session_id = len(state.get("sessions", [])) + 1
        self.session_start_time = datetime.now()

        current_session = {
            "session_id": self.session_id,
            "plug_in": self._get_timestamp(),
            "plug_out": None,
            "duration_seconds": None,
            "drive": self.drive_letter,
            "volume_info": self.volume_info
        }
        state.setdefault("sessions", []).append(current_session)

        # Lưu ngay trạng thái cắm để bảo toàn dữ liệu nếu bị rút đột ngột
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        header_msg = (
            f"\n{'='*80}\n"
            f"SESSION #{self.session_id} | PLUG-IN: {current_session['plug_in']} | DRIVE: [{self.drive_letter}] ({self.volume_info})\n"
            f"TỔNG SỐ LẦN CẮM ĐẾN NAY: {self.plug_count} LẦN\n"
            f"{'='*80}\n"
        )
        self._write_raw_log(header_msg)
        safe_print(header_msg)

        # Quét và tạo snapshot cây thư mục
        self.generate_folder_tree()

    def close_session(self):
        """Đóng phiên làm việc an toàn khi rút USB hoặc dừng ứng dụng."""
        if not self.is_running:
            return
        self.is_running = False

        # Hủy các I/O đang pending trên ReadDirectoryChangesW
        for drive_path, hDir in list(self.active_handles.items()):
            try:
                kernel32.CancelIoEx(hDir, None)
                kernel32.CloseHandle(hDir)
            except Exception:
                pass
        self.active_handles.clear()

        # Flush buffer còn sót
        self._flush_buffer_now()

        plug_out_time = datetime.now()
        duration = int((plug_out_time - self.session_start_time).total_seconds()) if self.session_start_time else 0
        duration_str = str(plug_out_time - self.session_start_time).split(".")[0] if self.session_start_time else "00:00:00"

        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                if state.get("sessions"):
                    state["sessions"][-1]["plug_out"] = self._get_timestamp()
                    state["sessions"][-1]["duration_seconds"] = duration
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        footer_msg = (
            f"\n{'='*80}\n"
            f"SESSION #{self.session_id} KẾT THÚC | PLUG-OUT: {self._get_timestamp()} | THỜI LƯỢNG: {duration_str}\n"
            f"{'='*80}\n"
        )
        self._write_raw_log(footer_msg)
        safe_print(footer_msg)

        # Giải phóng Mutex
        if hasattr(self, 'instance_mutex') and self.instance_mutex:
            try:
                kernel32.CloseHandle(self.instance_mutex)
            except Exception:
                pass

    def _write_raw_log(self, text):
        try:
            with open(self.txt_log_file, "a", encoding="utf-8") as f:
                f.write(text + "\n")
            with open(self.md_log_file, "a", encoding="utf-8") as f:
                f.write(f"```text\n{text.strip()}\n```\n\n" if text.startswith("=") else f"`{text.strip()}`\n\n")
        except Exception as e:
            safe_print(f"[!] Loi ghi log: {e}")

    def log_entry(self, action, target_path, extra_info=""):
        """Ghi nhận sự kiện vào hàng đợi thông minh (Debounce Buffer)."""
        p_lower = target_path.lower()
        if any(x in p_lower for x in (".system", ".usb_data", "usb_logs", "usb_log", "usb-log", "$recycle.bin", "system volume information")):
            return

        with self.buffer_lock:
            self.event_buffer.append({
                "time": self._get_timestamp(),
                "action": action,
                "path": target_path,
                "extra": extra_info
            })

            if self.debounce_timer:
                self.debounce_timer.cancel()
            self.debounce_timer = threading.Timer(self.DEBOUNCE_INTERVAL, self._flush_buffer_now)
            self.debounce_timer.start()

    def _format_target(self, path, is_dir=False):
        try:
            rel_path = os.path.relpath(path, self.root_dir).replace("\\", "/")
        except Exception:
            rel_path = path.replace("\\", "/")
            
        if is_dir or path.endswith(("\\", "/")):
            return rel_path.rstrip("/") + "/"
        return rel_path

    def _flush_buffer_now(self):
        """Xử lý và gom nhóm sự kiện trong bộ đệm."""
        with self.buffer_lock:
            events = list(self.event_buffer)
            self.event_buffer.clear()

        if not events:
            return

        # Khử trùng lặp: Nếu trong đợt này đã có In hoặc Add cho 1 file, bỏ qua các Modify thừa
        added_paths = {ev["path"] for ev in events if ev["action"] in ("In", "Add")}
        filtered_events = []
        for ev in events:
            if ev["action"] == "Modify" and ev["path"] in added_paths:
                continue
            filtered_events.append(ev)
        events = filtered_events

        groups = defaultdict(list)
        for ev in events:
            p = ev["path"]
            folder = os.path.dirname(p)
            groups[(ev["action"], folder)].append(ev)

        has_folder_change = False

        for (action, folder), item_list in groups.items():
            folder_formatted = self._format_target(folder, is_dir=True) if folder else ""
            
            # Nếu vượt quá ngưỡng gom nhóm (> 8 item) -> Ghi 1 dòng tóm tắt
            if len(item_list) > self.BATCH_THRESHOLD:
                ts = item_list[0]["time"]
                ext_counts = defaultdict(int)
                for item in item_list:
                    _, ext = os.path.splitext(item["path"])
                    ext = ext.lower() if ext else "no-ext"
                    ext_counts[ext] += 1
                
                ext_str = ", ".join([f"{ext}" for ext in ext_counts.keys() if ext != "no-ext"][:3])
                summary = f"{ts} {action} {folder_formatted} and {len(item_list)} items ({ext_str if ext_str else 'mixed'})"
                safe_print(summary)
                self._write_raw_log(summary)
            else:
                for item in item_list:
                    ts = item["time"]
                    is_dir = os.path.isdir(item["path"]) if os.path.exists(item["path"]) else item["path"].endswith(("/", "\\"))
                    formatted = self._format_target(item["path"], is_dir=is_dir)
                    if action == "Move" and item.get("extra"):
                        extra_formatted = self._format_target(item["extra"], is_dir=is_dir)
                        line = f"{ts} Move {formatted} to {extra_formatted}"
                    else:
                        line = f"{ts} {action} {formatted}"
                    safe_print(line)
                    self._write_raw_log(line)

            if any(ev["path"].endswith(("/", "\\")) or (os.path.isdir(ev["path"]) if os.path.exists(ev["path"]) else False) for ev in item_list):
                has_folder_change = True

        if has_folder_change:
            self.generate_folder_tree()

    def _watch_directory_events(self, watch_path, tag=""):
        """Worker sử dụng kernel32.ReadDirectoryChangesW (Zero-polling, Event-driven 100%)."""
        hDir = kernel32.CreateFileW(
            watch_path,
            FILE_LIST_DIRECTORY,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            None
        )

        if hDir == INVALID_HANDLE_VALUE or not hDir:
            safe_print(f"[!] Khong the mo handle giam sat cho {watch_path}")
            return

        self.active_handles[watch_path] = hDir
        buf = ctypes.create_string_buffer(65536)
        bytes_ret = wintypes.DWORD()
        flags = (
            FILE_NOTIFY_CHANGE_FILE_NAME |
            FILE_NOTIFY_CHANGE_DIR_NAME |
            FILE_NOTIFY_CHANGE_SIZE |
            FILE_NOTIFY_CHANGE_LAST_WRITE
        )

        old_rename_name = None

        while self.is_running:
            success = kernel32.ReadDirectoryChangesW(
                hDir,
                buf,
                65536,
                True,  # Watch subtree recursively
                flags,
                ctypes.byref(bytes_ret),
                None,
                None
            )

            if not success or bytes_ret.value == 0:
                break

            offset = 0
            while offset < bytes_ret.value:
                next_offset = int.from_bytes(buf[offset:offset+4], byteorder="little")
                action_code = int.from_bytes(buf[offset+4:offset+8], byteorder="little")
                fn_len = int.from_bytes(buf[offset+8:offset+12], byteorder="little")
                rel_name = buf[offset+12:offset+12+fn_len].decode("utf-16le")
                full_path = os.path.join(watch_path, rel_name)

                action_prefix = f"{tag} " if tag else ""

                if action_code == 1:  # Added
                    is_dir = os.path.isdir(full_path) if os.path.exists(full_path) else False
                    act = f"{action_prefix}Add" if is_dir else f"{action_prefix}In"
                    self.log_entry(act, full_path + ("/" if is_dir else ""))
                elif action_code == 2:  # Removed
                    self.log_entry(f"{action_prefix}Delete", full_path)
                elif action_code == 3:  # Modified
                    if os.path.isfile(full_path) or not os.path.exists(full_path):
                        self.log_entry(f"{action_prefix}Modify", full_path)
                elif action_code == 4:  # Renamed Old Name
                    old_rename_name = full_path
                elif action_code == 5:  # Renamed New Name
                    is_dir = os.path.isdir(full_path) if os.path.exists(full_path) else False
                    if old_rename_name:
                        self.log_entry(f"{action_prefix}Move", old_rename_name, extra_info=full_path)
                        old_rename_name = None
                    else:
                        act = f"{action_prefix}Add" if is_dir else f"{action_prefix}In"
                        self.log_entry(act, full_path)

                if next_offset == 0:
                    break
                offset += next_offset

        try:
            kernel32.CloseHandle(hDir)
        except Exception:
            pass

    def _listen_clipboard_out(self):
        """Giám sát Clipboard Windows an toàn bộ nhớ 100% để phát hiện thao tác Out."""
        CF_HDROP = 15
        last_files = set()

        while self.is_running:
            try:
                if user32.OpenClipboard(None):
                    try:
                        h_drop = user32.GetClipboardData(CF_HDROP)
                        if h_drop:
                            size = kernel32.GlobalSize(h_drop)
                            if size > ctypes.sizeof(DROPFILES):
                                p_drop = kernel32.GlobalLock(h_drop)
                                if p_drop:
                                    try:
                                        drop = DROPFILES.from_address(p_drop)
                                        if drop.fWide and drop.pFiles < size:
                                            raw = ctypes.string_at(p_drop + drop.pFiles, size - drop.pFiles)
                                            files = [
                                                s.strip() for s in raw.decode("utf-16le", errors="ignore").split("\x00")
                                                if s.strip()
                                            ]
                                            current_clip = set(files)
                                            for fpath in current_clip:
                                                if fpath.upper().startswith(self.drive_letter.upper()) and fpath not in last_files:
                                                    self.log_entry("Out", fpath)
                                                else:
                                                    for vc_d in list(self.active_veracrypt_drives.keys()):
                                                        if fpath.upper().startswith(vc_d.upper()) and fpath not in last_files:
                                                            self.log_entry(f"[VeraCrypt-{vc_d.rstrip('\\')}] Out", fpath)
                                            last_files = current_clip
                                    finally:
                                        kernel32.GlobalUnlock(h_drop)
                    finally:
                        user32.CloseClipboard()
            except Exception:
                pass
            time.sleep(1.0)

    def _monitor_veracrypt_lifecycle(self):
        """Phát hiện động các container VeraCrypt được Mount / Unmount trên hệ thống."""
        while self.is_running:
            try:
                curr_logical = set(self._get_logical_drives())

                # 1. Phát hiện container mới được Mount
                for d in curr_logical:
                    if d not in self.initial_drives and d.upper() != self.root_dir.upper():
                        if d not in self.active_veracrypt_drives and os.path.exists(d):
                            v_label = self._get_volume_label(d)
                            mount_msg = f"{self._get_timestamp()} [VeraCrypt] Đã MOUNT Container thành ổ đĩa [{d.rstrip('\\')}] ({v_label})"
                            safe_print(f"[+] {mount_msg}")
                            self._write_raw_log(mount_msg)

                            tag = f"[VeraCrypt-{d.rstrip('\\')}]"
                            t_vc = threading.Thread(
                                target=self._watch_directory_events, 
                                args=(d, tag), 
                                daemon=True
                            )
                            t_vc.start()
                            self.active_veracrypt_drives[d] = t_vc
                            self.generate_folder_tree()

                # 2. Phát hiện container bị Unmount
                for d in list(self.active_veracrypt_drives.keys()):
                    if d not in curr_logical or not os.path.exists(d):
                        unmount_msg = f"{self._get_timestamp()} [VeraCrypt] Đã UNMOUNT Container khỏi ổ đĩa [{d.rstrip('\\')}]"
                        safe_print(f"[-] {unmount_msg}")
                        self._write_raw_log(unmount_msg)

                        # Hủy handle của ổ đĩa vừa rút
                        if d in self.active_handles:
                            try:
                                kernel32.CancelIoEx(self.active_handles[d], None)
                                kernel32.CloseHandle(self.active_handles[d])
                            except Exception:
                                pass
                            del self.active_handles[d]

                        del self.active_veracrypt_drives[d]
                        self.generate_folder_tree()

            except Exception:
                pass
            time.sleep(2.0)

    def run(self):
        """Khởi động toàn bộ luồng giám sát Windows ReadDirectoryChangesW."""
        safe_print(f"[*] Dang theo doi o dia: {self.root_dir} (Event-driven Zero-Polling)...")

        # Luồng 1: Clipboard Out
        t_clip = threading.Thread(target=self._listen_clipboard_out, daemon=True)
        t_clip.start()

        # Luồng 2: VeraCrypt Lifecycle Manager
        t_vc = threading.Thread(target=self._monitor_veracrypt_lifecycle, daemon=True)
        t_vc.start()

        # Luồng 3: Giám sát chính trên ổ USB
        t_main_watch = threading.Thread(
            target=self._watch_directory_events, 
            args=(self.root_dir, ""), 
            daemon=True
        )
        t_main_watch.start()

        # Giữ main thread cho đến khi nhận tín hiệu tắt hoặc ổ USB bị rút
        while self.is_running:
            time.sleep(1.0)
            # Kiểm tra xem ổ USB có còn tồn tại không
            if not os.path.exists(self.root_dir):
                safe_print(f"[-] O dia {self.root_dir} da bi ngat ket noi.")
                break

        self.close_session()


if __name__ == "__main__":
    monitor = USBMonitorEngine()

    def signal_handler(sig, frame):
        safe_print("\n[*] Nhan tin hieu dung, dang luu phien lam viec an toan...")
        monitor.close_session()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(monitor.close_session)

    try:
        monitor.run()
    except KeyboardInterrupt:
        monitor.close_session()

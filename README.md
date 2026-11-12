# TP-Link Router Discovery & Recovery Toolkit

Công cụ quản trị và chẩn đoán mạng nội bộ chuyên dụng trên hệ điều hành **Ubuntu Linux**, hỗ trợ tự động dò tìm, nhận diện và cung cấp hướng dẫn khôi phục quyền quản trị router TP-Link thuộc sở hữu của bạn mà không thực hiện các hành vi tấn công phá hoại.

---

## 1. Giới thiệu & Triết lý an toàn

Khi quản trị thiết bị mạng gia đình hoặc văn phòng, nhiều tình huống khiến người quản trị mất quyền truy cập (mật khẩu Wi-Fi bị đổi, IP quản trị LAN bị đổi, router lắp ở vị trí khó tiếp cận như cột/tường cao).

**Nguyên tắc an toàn (Security by Design):**
- **KHÔNG** thực hiện brute-force mật khẩu hoặc tấn công từ điển.
- **KHÔNG** crack handshake WPA/WPA2/WPA3.
- **KHÔNG** deauthentication attack, WPS PIN brute-force hoặc exploit lỗ hổng firmware.
- **KHÔNG** bypass xác thực hoặc tự ý sửa đổi file cấu hình thiết bị.
- **KHÔNG** gửi bất kỳ dữ liệu nhạy cảm nào ra Internet.
- **CHỈ** sử dụng giao thức chuẩn (ARP, ICMP ping sweep, TCP connect check, HTTP/HTTPS banner) để xác định sự hiện diện và trạng thái của router trên mạng LAN được phép quản lý.

---

## 2. Cấu trúc thư mục dự án

```
router-recovery-tool/
├── router_tool.py                  # Điểm khởi chạy CLI chính
├── requirements.txt                # Thư viện phụ thuộc Python
├── README.md                       # Hướng dẫn chi tiết
├── config/
│   └── vendors.json                # Cơ sở dữ liệu MAC OUI TP-Link & nhà sản xuất
├── modules/
│   ├── network_discovery.py        # Phát hiện interface, IP, gateway, subnet, ARP
│   ├── arp_scanner.py              # Quét subnet tìm live hosts (Scapy & ping sweep)
│   ├── port_scanner.py             # Kiểm tra cổng dịch vụ TCP (80, 443, 8080, v.v.)
│   ├── admin_interface.py          # Kiểm tra HTTP/HTTPS, tiêu đề, chữ ký TP-Link
│   ├── router_identifier.py        # Tính toán điểm tin cậy & nhận diện router
│   ├── recovery_assistant.py       # Hướng dẫn tương tác theo tình huống A - E
│   └── reporter.py                 # Xuất báo cáo màu CLI, JSON, TXT
├── tests/
│   ├── test_network_discovery.py   # Kiểm thử module network discovery
│   ├── test_router_identifier.py   # Kiểm thử module nhận diện router
│   ├── test_admin_interface.py     # Kiểm thử module phân tích giao diện web
│   └── test_recovery_assistant.py  # Kiểm thử kịch bản khôi phục
└── reports/                        # Thư mục lưu báo cáo scan JSON / TXT
```

---

## 3. Cài đặt trên Ubuntu Linux

### Bước 1: Yêu cầu môi trường
- Ubuntu 20.04 / 22.04 / 24.04 LTS
- Python 3.10 trở lên
- `iproute2` (đã có sẵn mặc định trên Ubuntu)

### Bước 2: Tạo môi trường ảo và cài đặt thư viện
```bash
cd /home/yang/Desktop/yanglynk/wifi/router-recovery-tool

# Tạo virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

---

## 4. Hướng dẫn sử dụng CLI

### 4.1. Khám phá toàn diện mạng LAN (`discover`)
Tự động tìm interface chính, quét dải mạng, kiểm tra các cổng quản trị và nhận diện thiết bị TP-Link cùng độ tin cậy (Confidence Level):
```bash
python3 router_tool.py discover
```
*Tùy chọn:* Chỉ định interface và xuất báo cáo tự động:
```bash
python3 router_tool.py discover -i enp3s0 --format json
```

### 4.2. Quét nhanh các thiết bị trong dải mạng (`scan`)
Liệt kê các thiết bị đang hoạt động, địa chỉ IP, MAC và Hostname:
```bash
# Quét subnet mặc định của interface hiện tại:
python3 router_tool.py scan

# Quét trên interface hoặc subnet tùy chọn:
python3 router_tool.py scan --interface wlp0s20f3 --subnet 192.168.1.0/24
```

### 4.3. Nhận diện sâu một IP nghi ngờ (`identify`)
Kiểm tra MAC OUI, cổng quản trị, tiêu đề HTTP và đánh giá độ tin cậy TP-Link (High / Medium / Low / None):
```bash
python3 router_tool.py identify --ip 192.168.1.1
```

### 4.4. Phân tích chi tiết giao diện web quản trị (`inspect`)
Thu thập HTTP status code, chuỗi chuyển hướng (redirect chain), Server header, tiêu đề trang và chữ ký model:
```bash
python3 router_tool.py inspect --ip 192.168.1.1
```

### 4.5. Trợ lý hướng dẫn khôi phục (`assist`)
Cung cấp giải pháp xử lý theo từng trường hợp cụ thể:
```bash
# Chế độ tương tác qua menu:
python3 router_tool.py assist

# Xem nhanh theo từng trường hợp (A, B, C, D, E):
python3 router_tool.py assist --case A
python3 router_tool.py assist --case B
python3 router_tool.py assist --case C
python3 router_tool.py assist --case D
python3 router_tool.py assist --case E
```

### 4.6. Xuất báo cáo (`report`)
Xuất kết quả chẩn đoán ra file JSON hoặc văn bản TXT trong thư mục `reports/`:
```bash
python3 router_tool.py report --format json
python3 router_tool.py report --format txt -o reports/my_network_report.txt
```

---

## 5. Các kịch bản khôi phục (Recovery Scenarios)

| Tình huống | Mô tả | Hướng giải quyết chính |
|---|---|---|
| **Case A** | Vào được trang quản trị nhưng quên mật khẩu | Thử tài khoản mặc định theo model (`admin/admin` cho dòng cũ); sử dụng nút "Forgot Password?"; đăng nhập qua app di động TP-Link Tether nếu trước đây đã gán TP-Link ID; xem mật khẩu đã lưu trên trình duyệt. |
| **Case B** | Tìm được IP quản trị nhưng không có thông tin đăng nhập | Thử truy cập qua HTTP (80/8080) và HTTPS (443/8443) ở chế độ ẩn danh (Incognito); dùng tên miền nội bộ `tplinkwifi.net` hoặc `tplinklogin.net`. |
| **Case C** | Không thấy IP quản trị trong subnet hiện tại | Cắm trực tiếp dây cáp LAN vào router; gia hạn DHCP (`dhclient`); gán IP tĩnh tạm thời (ví dụ `192.168.0.100/24`) để rà soát dải mạng phụ nếu router đang chạy ở chế độ Access Point. |
| **Case D** | Không kết nối được Wi-Fi | Sử dụng cáp Ethernet cắm vào cổng LAN (không cần mật khẩu Wi-Fi); hoặc trích xuất mật khẩu Wi-Fi đã lưu trên các thiết bị cũ (Android/iOS/Windows/Linux). |
| **Case E** | Hướng dẫn Factory Reset chi tiết theo từng dòng phần cứng | Hướng dẫn reset nút cứng cho Archer Series (giữ 8-10 giây), dòng TL-WR (giữ 6-8 giây), dòng Mesh Deco (giữ 1 giây). **Đặc biệt với dòng Outdoor trên cột (CPE210/510):** Hướng dẫn dùng nút *Remote Reset* trên cục nguồn PoE Injector trong nhà mà không cần phải trèo lên cột điện! |

---

## 6. Chạy Unit Tests

Bộ kiểm thử được viết bằng `pytest`, kiểm tra toàn diện các module:
```bash
source .venv/bin/activate
PYTHONPATH=router-recovery-tool pytest router-recovery-tool/tests/ -v
```
Kết quả kiểm thử: **13/13 tests PASSED**.

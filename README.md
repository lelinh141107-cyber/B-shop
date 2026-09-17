# 🥑 Bơ Shop - Pure Python

Bản này làm lại bằng **Python thuần**, không dùng Flask và không cần `pip install` thư viện nào. Có website responsive, sản phẩm, giỏ hàng, đặt hàng, SQLite và gửi email Gmail qua SMTP.

## Chạy trên Windows
1. Cài Python 3.10+.
2. Mở thư mục này bằng VS Code.
3. Mở Terminal tại đúng thư mục có `app.py`.
4. Chạy:

```powershell
python app.py
```

Hoặc bấm đúp `run_windows.bat`.

Mở trên máy tính: `http://127.0.0.1:5000`

## Điện thoại cùng Wi-Fi
Khi app chạy, Terminal sẽ in ra địa chỉ kiểu `http://192.168.x.x:5000`. Điện thoại kết nối cùng Wi-Fi với máy tính rồi mở địa chỉ đó.

Nếu Windows Firewall hỏi quyền, chọn cho phép Python trên mạng Private để điện thoại truy cập.

## Gmail
Mở `.env` và thay duy nhất:

```env
EMAIL_PASSWORD=PASTE_NEW_GMAIL_APP_PASSWORD_HERE
```

bằng **App Password mới của Google**. Không dùng mật khẩu Gmail thường và không chia sẻ `.env`.

App tự bỏ khoảng trắng trong App Password. Đơn hàng được lưu vào `data/orders.db` trước; sau đó mới gửi email. Nếu email lỗi, đơn vẫn được lưu.

## Dữ liệu
Đơn hàng nằm trong `data/orders.db` (SQLite). Không cần cài SQLite riêng.

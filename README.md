# Ứng Dụng Smart Travel

Một ứng dụng du lịch toàn diện cung cấp tính năng đặt tour, bản đồ, quản lý người dùng và các đề xuất dựa trên trí tuệ nhân tạo.

## Cấu Trúc Thư Mục

- src/frontend: Chứa mã nguồn giao diện người dùng (HTML, CSS, JS).
- src/backend: Chứa mã nguồn backend viết bằng Python (API, tích hợp cơ sở dữ liệu, xử lý AI).

## Hướng Dẫn Sử Dụng

### Frontend
Vui lòng kiểm tra src/frontend/README.md hoặc đơn giản là mở file index.html bằng trình duyệt web của bạn.

### Backend
1. Di chuyển đến thư mục src/backend
2. Cài đặt các thư viện phụ thuộc: pip install -r requirements.txt
3. Chạy máy chủ: python main.py hoặc uvicorn main:app --reload (nếu sử dụng FastAPI).

## Các Tính Năng Chính
- Bản đồ và chỉ đường
- Đặt tour du lịch
- Quản lý người dùng
- Thanh toán
- Bảng điều khiển dành cho quản trị viên
- Đề xuất chuyến đi thông minh (dự kiến)

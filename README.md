# Ứng Dụng Smart Travel

Một ứng dụng du lịch toàn diện cung cấp tính năng đặt tour, bản đồ, quản lý người dùng và các đề xuất dựa trên trí tuệ nhân tạo.

## Cấu Trúc Thư Mục

- src/frontend: Chứa mã nguồn giao diện người dùng (HTML, CSS, JS).
- src/backend: Chứa mã nguồn backend viết bằng Python (API, tích hợp cơ sở dữ liệu, xử lý AI).

## Hướng Dẫn Sử Dụng

### Chạy bằng Docker (Backend + MongoDB)
1. Đảm bảo bạn đã cài Docker Desktop và đang chạy.
2. Chạy MongoDB bằng Docker:
   ```powershell
   docker pull mongo:6
   docker run -d --name smart-travel-mongo -p 27017:27017 -v smart_travel_data:/data/db mongo:6
   ```
3. Thiết lập biến môi trường backend trong `src/backend/.env` (mặc định đã có):
   ```env
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=smart_travel
   ```
4. Chạy backend (trong thư mục `src/backend`):
   ```powershell
   pip install -r requirements.txt
   python main.py
   ```
   Hoặc:
   ```powershell
   uvicorn main:app --reload
   ```

### Kiểm tra MongoDB
```powershell
docker exec -it smart-travel-mongo mongosh
```
```javascript
show dbs
use smart_travel
show collections
```

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

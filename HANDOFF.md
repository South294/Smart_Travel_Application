# Handoff - Smart Travel Admin (May 19, 2026)

## Tổng quan
- Thiết lập và chạy MongoDB bằng Docker, seed dữ liệu demo.
- Hoàn thiện luồng đăng nhập phân biệt Admin/User, khóa truy cập admin với user thường.
- Tách toàn bộ admin frontend vào `src/frontend/admin/`.
- Mở rộng admin API để quản lý users, guides, bookings, settings.
- Bổ sung dữ liệu demo cho guides, bookings, settings.

## Backend cập nhật
- Auth/login: trả role để điều hướng admin.
- Admin API mới:
  - `GET /api/admin/users` (list users)
  - `PATCH /api/admin/users/{id}/status` (khóa/mở user)
  - `GET /api/admin/guides` (list guides)
  - `GET /api/admin/bookings` (list bookings, có `tour_title`)
  - `PATCH /api/admin/bookings/{id}/status` (confirm/cancel)
  - `GET /api/admin/settings`
  - `PUT /api/admin/settings`
- Chặn user bị khóa trong `get_current_user`.
- Seed demo: guides pending/approved, bookings demo, admin settings demo.

## Frontend admin cập nhật
- Tách admin UI:
  - `src/frontend/admin/index.html`
  - `src/frontend/admin/js/admin.js`
  - `src/frontend/admin/css/admin.css`
- Tabbar chỉnh màu active theo theme, không bị “mất” khi bấm.
- Dashboard tương tác:
  - Card thống kê click chuyển tab.
  - Tab tuần/tháng thay đổi summary.
  - “Xem tất cả” mở modal hoạt động.
  - Data demo cho báo cáo, hoạt động, top tours.
- Quản lý Tour:
  - Bảng demo, nút “Làm mới” + loading.
  - Modal chi tiết tour.
- Quản lý Booking:
  - Hiển thị dữ liệu DB.
  - Nút Duyệt/Hủy (pending) -> gọi API update status.
- Quản lý Guides:
  - Duyệt/từ chối từ tab “Duyệt yêu cầu”.
  - Danh sách guide đầy đủ trong tab “Hướng dẫn viên”.
- Cài đặt hệ thống:
  - Toggle + nút lưu (persist DB).

## Dữ liệu demo
- Guides: 1 pending + 1 approved (tạo qua seed).
- Bookings: 3 bản ghi demo (confirmed/pending/cancelled).
- Settings: maintenance/auto approve/email booking.

## Lệnh chạy nhanh
```powershell
cd D:\Project\Smart_Travel_Application-test\src\backend
python seed_db.py
python main.py
```

## Ghi chú
- Admin account tạo bằng seed (ENV `ADMIN_EMAIL`, `ADMIN_PASSWORD`).
- Admin UI truy cập: `src/frontend/admin/index.html`.

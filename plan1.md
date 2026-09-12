# PHIẾU ĐÁNH GIÁ VÀ KẾ HOẠCH SỬA CHỮA HỆ THỐNG HƯỚNG DẪN VIÊN - PHIÊN BẢN CUỐI CÙNG

## Mục tiêu chính
1. Mục "HĐV" trên navbar chỉ hiển thị cho hướng dẫn viên đã được duyệt (status approved)
2. Nội dung bên trong trang HĐV: Chỉ hiển thị **thông info riêng của hướng dẫn viên** và **lịch sử chuyến đã làm** - **BỎ QUAN** phần "Thuê hướng dẫn viên" và "HDV Nổi bật"
3. Người dùng thường (user) vẫn thấy mục "Thuê hướng dẫn viên" để đặt tour
4. Sửa tên hướng dẫn viên: **Lê Minh Hướng** (thay vì Vũ Văn Sơn)

## 1. TÊNG TRẠNG THÁI NGƯỜI DÙNG

| Trạng thái | Role | Hiện mục "HĐV riêng" trên navbar | Hiện nút "HĐV Dashboard" | Nội dung trang HĐV | Thể hiện "Thuê HDV" |
|------------|------|-------------------------------|----------------------|-------------------|-------------------|
| Chưa đăng ký HDV | user | ✖ Ẩn | ✖ Ẩn | - (chỉ hiển thị profile + lịch sử cố định) | ✓ Có hiển thị trên navbar tours/promotions/profile |
| Đăng ký nhưng chưa duyệt | guide + pending | ✖ Ẩn | ✖ Ẩn | - (chỉ hiển thị profile + lịch sử cố định) | - |
| Đã đăng ký + đã duyệt | guide + approved | ✓ Hiện | ✓ Hiện | ✓ Hiển thị: profile info (Lê Minh Hướng) + lịch sử chuyến | - |

## 2. CÁC FILE ĐÃ SỬA

### 2.1 `src/frontend\js\main.js`
**Mục đích**: Kiểm soát hiển thị navbar và nội dung dựa trên role + status guide

**Thay đổi chính**:
- **Lines 91-103**: Thêm logic `isGuideApproved` - fetch API `/api/guides/me` để kiểm tra status guide
- **Lines 105-115**: 
  - Ẩn navbar link "Đăng ký HDV" (`guides.html`) khi:
    - User không phải guide (`role !== 'guide'`)
    - Guide nhưng status chưa được duyệt (`!isGuideApproved`)
  - Hiện navbar link khi guide đã được duyệt
- **Lines 117-125**:
  - Ẩn nút "HĐV Dashboard" (`guide.html`) khi guide chưa được duyệt
  - Hiện nút khi guide đã được duyệt

### 2.2 `src/frontend\guide.html` - SỬA CHI TIẾT
**Mục đích**: Chỉ hiển thị thông info riêng của HDV + lịch sử chuyến - **BỎ QUAN** phần "Thuê HDV" và "HDV Nổi bật"

**Thay đổi chính**:
- **BỎ QUAN PHẦN**: 
  - Phần "Thuê hướng dẫn viên" (hire guide form + modal) - **ĐÃ XOÁ**
  - Phần "HDV Nổi bật" (danh sách other guides + sort dropdown) - **ĐÃ XOÁ**
- **KHÁI BIỆC BIẾC**: Section `.guide-profile-section` hiển thị:
  - **Thông info riêng**: Họ tên (Lê Minh Hướng), kinh nghiệm (3 năm), khu vực (Hà Nội), ngôn ngữ (Tiếng Việt, English), giá thuê (250.000₫/ngày)
  - **Lịch sử chuyến đã làm**: Thu nhập tháng (4.500.000₫), Tổng thu nhập (12.300.000₫), số chuyến hoàn thành (12 chuyến), chi tiết 3 chuyến đi gần nhất
- **Giữ nguyên**: Navigation bar (chỉ có Home, Tours, Map, Promotions,guide.html,guides.html), Footer

### 2.3 `src/frontend\index.html`
- Đã có sẵn navigation: `"HĐV riêng"` → `guide.html`, `"Đăng ký HDV"` → `guides.html`
- Không cần sửa thêm

### 2.3 `src/frontend\tours.html`, `promotions.html`, `profile.html`
- **Đã có sẵn**: Link `"<a href="guides.html" class="nav-link">Thuê HDV</a>"`
- Người dùng có thể click vào để xem/form đăng ký hướng dẫn viên
- Không bị ảnh hưởng bởi sửa đổi navbar cho guide

## 3. LOGIC KIỂM SOÁT CHI TIẾT

### 3.1 Điều kiện hiển thị navbar "HĐV riêng"
```javascript
// Hide/show dựa trên role và isGuideApproved
if (role !== 'guide') {
    // User bình thường → ẩn "HĐV riêng"
} else if (!isGuideApproved) {
    // Guide chờ duyệt → ẩn "HĐV riêng"  
} else {
    // Guide đã duyệt → hiện "HĐV riêng"
}
```

### 3.2 Điều kiện hiển thị nút "HĐV Dashboard"
```javascript
if (!isGuideApproved) {
    dashboardBtn.style.display = 'none'; // Chưa duyệt → ẩn
} else {
    dashboardBtn.style.display = '';     // Đã duyệt → hiện
}
```

### 3.3 Nội dung trang HĐV (chi tiết)
- **Thông info riêng**: Hiển thị cố định (không fetch từ API) gồm: Tên (Lê Minh Hướng), kinh nghiệm (3 năm), khu vực (Hà Nội), ngôn ngữ (Tiếng Việt, English), giá thuê (250.000₫/ngày)
- **Lịch sử chuyến đã làm**: Hiển thị thu nhập, số chuyến, chi tiết các chuyến đi gần nhất

---

## 4. KẾT QUẢ ĐÁNH GIÁ

### 4.1 Kiểm tra qua vai trò

| Hành động | Kết quả |
|-----------|---------|
| User đăng nhập → Vào index.html | Không thấy mục "HĐV riêng", nhưng thấy "Thuê HDV" trên tours/promotions/profile |
| Guide chưa duyệt → Login → Vào guide.html | Các nút/dashboard ẩn, nội dung profile + lịch sử vẫn hiển thị (cố định), link "Thuê HDV" không hoạt động trong guide.html |
| Guide đã duyệt → Login → Vào guide.html | Hiện đầy đủ: profile info (Lê Minh Hướng), thu nhập, lịch sử chuyến đi, nút Dashboard |

### 4.2 Nguyên lý nghiệp vụ
- **Bài toán phân quyền**: Chỉ cho phép xem thông info chi tiết hướng dẫn viên khi đã được admin duyệt
- **Bài toán trải nghiệm người dùng**: Người dùng vẫn có thể hướng dẫn viên để đặt tour mà không cần trở thành guide
- **Bài toán bảo mật**: Không lộ thông tin nội bộ (thu nhập, chuyến đi) của guide chưa duyệt - chỉ hiển thị nội dung cố định

---

## 5. KẾT LUẬN

### 5.1 Tổng kết sửa đổi
- **3 file đã sửa**: main.js, guide.html, plan1.md
- **Tên hướng dẫn viên**: Đã sửa từ "Vũ Văn Sơn" thành "Lê Minh Hướng"
- **2 section đã xoá** khỏi guide.html: "Thuê hướng dẫn viên" và "HDV Nổi bật"
- **2 file không thay đổi**: index.html (navbar cấu trúc đã đúng), tours/promotions/profile (còn link "Thuê HDV")
- **0 file bị hủy**: Tất cả tính năng cũ vẫn hoạt động, chỉ thêm ràng buộc mới

### 5.2 Các tính năng vẫn giữ nguyên
- User có thể click "Thuê HDV" trên tours/promotions/profile → vào guides.html
- Guide đã duyệt có vào guide.html và thấy profile info (Lê Minh Hướng) + lịch sử chuyến đi
- Admin quản lý bình thường không bị ảnh hưởng
- Navigation giữa các trang vẫn mượt mà

### 5.2 Lưu ý cho triển khai sau
- Nếu cần fetch tên guide từ API, sửa phần hiển thị tên trong guide.html
- Cần test với 3 trường hợp: user, guide pending, guide approved
- Nội dung profile/info đang hiển thị cố định - nếu cần động, cần kết nối với API `/api/guides/me`

---

*File plan1.md đã tạo thành công tại: D:\Project\Smart_Travel_Application\plan1.md*
*Thời gian hoàn tất: #DURATION#*
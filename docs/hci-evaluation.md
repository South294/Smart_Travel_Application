# Định hướng HCI SmartTravel

## 1. Vấn đề người dùng

Người đi du lịch tự túc thường mất nhiều thời gian để chọn địa điểm, xây dựng lịch trình, tìm tour phù hợp và tìm hướng dẫn viên đáng tin cậy. Thông tin nằm rải rác ở nhiều kênh, còn việc kiểm tra chất lượng và tình trạng sẵn sàng của hướng dẫn viên chưa rõ ràng.

## 2. Người dùng mục tiêu

- Khách du lịch tự túc cần đặt tour và hỗ trợ địa phương trong một quy trình ngắn.
- Người am hiểu địa phương muốn đăng ký làm hướng dẫn viên và nhận chuyến phù hợp.
- Admin cần xét duyệt hồ sơ, quản lý tour và phân công minh bạch.

## 3. Kịch bản demo chính

1. User đăng ký hoặc đăng nhập.
2. User xem tour, mở danh sách hướng dẫn viên và gửi yêu cầu thuê.
3. User đăng ký làm hướng dẫn viên; hồ sơ chuyển sang `pending`.
4. Admin xem hồ sơ và duyệt; hồ sơ chuyển sang `approved`.
5. Admin chọn tour chưa phân công và gán cho hướng dẫn viên đã duyệt.
6. Guide mở Cổng HDV, xem chuyến đang hoạt động và lịch sử công việc.

## 4. Tiêu chí đánh giá usability

| Tiêu chí | Cách đo | Mục tiêu demo |
|---|---|---|
| Hoàn thành tác vụ | Tỷ lệ user hoàn tất tìm tour và gửi yêu cầu | >= 90% |
| Thời gian thao tác | Từ trang chủ đến gửi yêu cầu thuê HDV | <= 2 phút |
| Lỗi quyền truy cập | User thường mở dashboard guide | 0 trường hợp xem được dữ liệu riêng |
| Nhận biết trạng thái | User phân biệt pending, approved, rejected | >= 90% trả lời đúng |
| Tính nhất quán | Admin chọn tour có sẵn thay vì tạo tour ảo | 100% assignment có `tour_id` |

## 5. Câu hỏi đánh giá sau demo

- Bạn có biết bước tiếp theo sau khi gửi yêu cầu không?
- Trạng thái hồ sơ hướng dẫn viên có dễ hiểu không?
- Bạn có tìm thấy tour và hướng dẫn viên mà không cần quay lại nhiều lần không?
- Thông tin nào khiến bạn tin tưởng hoặc chưa tin tưởng một hướng dẫn viên?

## 6. Phạm vi hiện tại và giới hạn

Đây là prototype phục vụ demo HCI. Tính năng đặt lại mật khẩu, thanh toán production và lưu trữ tài liệu định danh cần được hoàn thiện thêm trước khi triển khai thực tế.

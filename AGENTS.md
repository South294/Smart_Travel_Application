# SMART TRAVEL APPLICATION - AGENT CORE INVARIANTS

## 1. RÀNG BUỘC QUYỀN THAY ĐỔI MÃ NGUỒN GỐC
- TUYỆT ĐỐI KHÔNG SỬA ĐỔI BẤT KỲ MÃ NGUỒN GỐC NÀO CỦA DỰ ÁN (toàn bộ thư mục `src/`, các tệp `test_routes.py`, `test_business_flows.py`, v.v.) khi CHƯA ĐƯỢC SỰ CHO PHÉP RÕ RÀNG TỪ NGƯỜI DÙNG.
- Khi cần thay đổi, phải trình bày phương án, phạm vi ảnh hưởng và đợi người dùng đồng ý trước khi thực hiện.

## 2. RÀNG BUỘC NGÔN NGỮ VÀ KHÔNG COMMENT CODE
- Khi giao tiếp và phản hồi trong dự án này, CHỈ ĐƯỢC DÙNG TIẾNG VIỆT 100%.
- TUYỆT ĐỐI KHÔNG COMMENT CODE: Khi viết, sửa đổi hoặc sinh code (Python, JavaScript, HTML, CSS, v.v.), nghiêm cấm chèn bất kỳ comment nào (không `#`, không `//`, không `/* */`, không `<!-- -->`). Mọi dòng mã phải tự tường minh.

## 3. CHU TRÌNH THỰC THI CHUẨN XÁC (DETERMINISTIC AGENT LOOP)
1. Khám phá (Discovery): Kiểm tra cấu trúc, schema, router và lời gọi API liên quan.
2. Trình bày & Xin phép: Bắt buộc xin phép người dùng trước khi can thiệp vào mã nguồn gốc.
3. Phẫu thuật chính xác (Surgical Patching): Sửa đổi đúng phạm vi đã được phê duyệt, kiểm tra cú pháp trước khi lưu.
4. Xác minh bắt buộc (Mandatory Verification): Chạy test suite (`pytest -v` và `python test_routes.py`), đảm bảo 100% test PASSED.

## 4. FASTAPI & MONGODB EXECUTION RULES
- Sử dụng Motor async (`app.db.mongodb.get_db`). Nghiêm cấm dùng PyMongo blocking đồng bộ trong request flow.
- BSON ObjectId: Luôn dùng `validate_object_id` từ `app.routers.helpers`. Cấm khởi tạo raw `ObjectId(id_str)`. Mọi response serialize `_id` sang `id` chuỗi ký tự.
- Payload và response phải ánh xạ tương ứng với Pydantic schema tại `app/schemas/`.

## 5. QUY TẮC NGHIỆP VỤ (BUSINESS INVARIANTS)
- Booking: Ngày khởi hành `travel_date` phải từ ngày hiện tại trở đi; tour phải tồn tại và `is_active == True`.
- Voucher: Kiểm tra điều kiện hiệu lực `is_active == True`, `expiry_date` chưa quá hạn.
- Payment: Kiểm tra idempotency khi xử lý callback VNPay, không cập nhật lại đơn đã thanh toán.
- Guides: Chỉ tài khoản hướng dẫn viên có `status == "approved"` mới được phân công tour hoặc truy cập dashboard.

## 6. BẢO TOÀN CONTRACT VÀ FRONTEND
- Không đổi đường dẫn các endpoint đang được frontend gọi (`src/frontend/js/*.js` và `src/frontend/admin/js/*.js`).
- Giữ nguyên cơ chế xác thực `Authorization: Bearer <token>` lưu trong `localStorage`.
- Không tự ý sửa đổi class, id của các phần tử DOM trong HTML.

## 7. RÀNG BUỘC KHÔNG TỰ Ý KIỂM THỬ HOẶC MỞ TRÌNH DUYỆT
- TUYỆT ĐỐI KHÔNG TỰ Ý MỞ ĐỂ TEST DỰ ÁN (không tự ý mở trình duyệt, browser subagent hoặc chạy test suite) khi CHƯA ĐƯỢC SỰ CHO PHÉP RÕ RÀNG TỪ NGƯỜI DÙNG.
- Chỉ thực hiện kiểm thử khi người dùng yêu cầu hoặc đồng ý rõ ràng.

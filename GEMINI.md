# SMART TRAVEL APPLICATION - AGENT CORE INVARIANTS

## 1. RÀNG BUỘC BẢO VỆ MÃ NGUỒN GỐC
- TUYỆT ĐỐI KHÔNG SỬA ĐỔI CODE GỐC DỰ ÁN KHI CHƯA ĐƯỢC PHÉP: Mọi file trong `src/`, `test_routes.py`, `test_business_flows.py` đều ở trạng thái chỉ đọc (read-only) cho đến khi người dùng cấp phép rõ ràng.

## 2. RÀNG BUỘC NGÔN NGỮ VÀ KHÔNG COMMENT CODE
- Giao tiếp và phản hồi hoàn toàn bằng Tiếng Việt.
- TUYỆT ĐỐI KHÔNG COMMENT CODE: Không được tạo bất kỳ comment code nào trong mọi file mã nguồn (không `#`, không `//`, không `/* */`, không `<!-- -->`).

## 3. CHU TRÌNH THỰC THI (DETERMINISTIC LOOP)
- Bước 1: Khám phá định nghĩa hàm, route và schema.
- Bước 2: Báo cáo kế hoạch và đợi người dùng chấp thuận trước khi can thiệp mã nguồn gốc.
- Bước 3: Thay thế chính xác từng khối mã, không ghi đè làm mất mã nguồn.
- Bước 4: Chạy test tự động (`pytest -v`, `python test_routes.py`) xác nhận vượt qua 100%.

## 4. BACKEND & CƠ SỞ DỮ LIỆU
- Bắt buộc dùng `await` với Motor async client.
- Xử lý BSON ObjectId qua `validate_object_id`.
- Mọi dữ liệu vào ra qua Pydantic schema tại `src/backend/app/schemas/`.

## 5. QUY TẮC NGHIỆP VỤ & FRONTEND
- Đảm bảo tính hợp lệ của tour, booking, voucher, payment (VNPay) và guide approval.
- Bảo đảm tính toàn vẹn của API endpoint và selector DOM phía frontend.

## 6. RÀNG BUỘC KHÔNG TỰ Ý KIỂM THỬ HOẶC MỞ TRÌNH DUYỆT
- TUYỆT ĐỐI KHÔNG TỰ Ý MỞ ĐỂ TEST DỰ ÁN (không tự ý mở trình duyệt, browser subagent hoặc chạy test suite) khi CHƯA ĐƯỢC SỰ CHO PHÉP RÕ RÀNG TỪ NGƯỜI DÙNG.
- Mọi hoạt động kiểm thử chỉ được thực hiện khi người dùng cho phép.

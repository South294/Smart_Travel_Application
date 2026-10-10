import re
from typing import Optional, List, Dict, Any
from app.services.ai_knowledge import LOCATION_ALIASES, CANONICAL_CITY_NAMES

def _casual_reply(message: str) -> Optional[str]:
    normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", "", message.lower()).strip()
    if re.fullmatch(r"(alo|hello|hi|hey|chào|xin chào|chao|ê|ơi)( bạn| bot| ai)?", normalized):
        return "Chào bạn! Mình là trợ lý du lịch SmartTravel. Bạn đang muốn tìm hiểu điểm đến, xem cẩm nang du lịch hay muốn tìm một tour phù hợp cho chuyến đi sắp tới?"
    if any(phrase in normalized for phrase in ["cảm ơn", "cam on", "thanks", "thank you"]):
        return "Rất vui được hỗ trợ bạn! Chúc bạn có những chuyến đi thật trọn vẹn và nhiều trải nghiệm đáng nhớ cùng SmartTravel."
    if any(phrase in normalized for phrase in ["bạn là ai", "ban la ai", "giúp được gì", "giup duoc gi", "ban lam gi"]):
        return "Mình là trợ lý du lịch thông minh SmartTravel. Mình có thể cung cấp cẩm nang danh lam thắng cảnh, thời tiết thời gian thực của 63 tỉnh thành Việt Nam, gợi ý lịch trình chi tiết và kết nối các tour du lịch có thật trên hệ thống. Bạn đang dự định đi đâu?"
    if normalized in {"tạm biệt", "tam biet", "bye", "goodbye"}:
        return "Tạm biệt bạn! Chúc bạn một ngày tốt lành và hẹn gặp lại bạn trong những chuyến hành trình tiếp theo cùng SmartTravel!"
    return None


def _coverage_reply(message: str) -> Optional[str]:
    normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", " ", message.lower()).strip()
    patterns = [
        r"63\s*(tỉnh|tinh)",
        r"(đủ|du|toàn bộ|toan bo|tất cả|tat ca)\s*(các\s*)?(tỉnh|tinh)",
        r"(bao nhiêu|bao nhieu)\s*(tỉnh|tinh)",
        r"(dữ liệu|du lieu|thông tin|thong tin).*(63|tỉnh thành|tinh thanh|toàn quốc|toan quoc)",
        r"(hỗ trợ|ho tro|có|co).*(63|tỉnh thành|tinh thanh|toàn quốc|toan quoc)",
        r"(phạm vi|pham vi).*(hỗ trợ|ho tro|dữ liệu|du lieu|tỉnh|tinh)"
    ]
    if any(re.search(pattern, normalized) for pattern in patterns):
        return (
            "Dạ chắc chắn rồi ạ! Trợ lý SmartTravel được trang bị đầy đủ cẩm nang du lịch, thời tiết thời gian thực và thông tin địa danh của toàn bộ 63 tỉnh thành trên khắp lãnh thổ Việt Nam:\n\n"
            "• Miền Bắc: Hà Nội, Quảng Ninh (Hạ Long), Ninh Bình, Hải Phòng, Phú Thọ, Lào Cai (Sa Pa), Hà Giang, Cao Bằng, Sơn La (Mộc Châu), Hòa Bình, Tuyên Quang, Lạng Sơn...\n"
            "• Miền Trung & Tây Nguyên: Thừa Thiên Huế, Đà Nẵng, Quảng Nam (Hội An), Bình Định (Quy Nhơn), Phú Yên, Khánh Hòa (Nha Trang), Ninh Thuận, Bình Thuận, Lâm Đồng (Đà Lạt), Kon Tum (Măng Đen), Đắk Lắk...\n"
            "• Miền Nam: TP. Hồ Chí Minh, Bà Rịa - Vũng Tàu, Tây Ninh, Cần Thơ, An Giang, Bến Tre, Bạc Liêu, Cà Mau, Kiên Giang (Phú Quốc)...\n\n"
            "Hệ thống cũng đang mở bán các tour du lịch thực tế với giá ưu đãi minh bạch. Bạn có thể gõ tên bất kỳ tỉnh thành nào bạn muốn đến, hoặc tham khảo các tour nổi bật bên dưới để mình tư vấn cụ thể nhé!"
        )
    return None


def _feature_reply(message: str) -> Optional[str]:
    normalized = message.lower()
    if any(phrase in normalized for phrase in ["hướng dẫn viên", "huong dan vien", "hdv", "thuê hdv", "thue hdv", "tìm hdv", "tim hdv"]):
        return (
            "SmartTravel cung cấp dịch vụ 'Thuê Hướng Dẫn Viên' bản địa uy tín tại mục 'Thuê HDV' trên thanh điều hướng:\n\n"
            "• Đội ngũ HDV đều đã được ban quản trị kiểm duyệt hồ sơ căn cước công dân (CCCD/KYC) và kiểm tra nghiệp vụ du lịch nghiêm ngặt.\n"
            "• Bạn có thể lọc HDV theo tỉnh thành, ngôn ngữ giao tiếp (Tiếng Việt, Anh, Pháp, Hàn...) và số năm kinh nghiệm.\n"
            "• Xem mức phí thuê theo ngày minh bạch, đánh giá thực tế từ các đoàn khách trước và gửi yêu cầu đặt lịch trực tiếp."
        )
    if any(phrase in normalized for phrase in ["khuyến mãi", "khuyen mai", "voucher", "mã giảm giá", "ma giam gia", "ưu đãi", "uu dai", "giảm giá", "giam gia"]):
        return (
            "Bạn có thể vào mục 'Khuyến mãi' trên thanh menu để nhận các mã giảm giá hấp dẫn khi đặt tour trên SmartTravel:\n\n"
            "• Mã giảm trực tiếp từ 10% đến 30% giá trị tour hoặc voucher giảm tiền mặt đến 500.000đ.\n"
            "• Khi tiến hành đặt tour, bạn chỉ cần nhập mã voucher vào ô 'Mã giảm giá' tại trang thanh toán để được khấu trừ ngay lập tức.\n"
            "• Bạn cũng có thể đăng ký tài khoản thành viên để lưu trữ và quản lý các voucher cá nhân trong ví ưu đãi."
        )
    if any(phrase in normalized for phrase in ["bản đồ", "ban do", "map", "xem bản đồ"]):
        return (
            "Tính năng 'Bản đồ' trên website SmartTravel mang đến trải nghiệm trực quan toàn diện:\n\n"
            "• Định vị tọa độ và xem vị trí các điểm du lịch nổi tiếng trên khắp 63 tỉnh thành Việt Nam.\n"
            "• Xem điều kiện thời tiết, nhiệt độ thời gian thực được đồng bộ trực tiếp từ trạm khí tượng.\n"
            "• Dễ dàng tìm kiếm và lên lộ trình di chuyển tối ưu cho chuyến đi."
        )
    if any(phrase in normalized for phrase in ["cách đặt tour", "cach dat tour", "đặt tour thế nào", "dat tour the nao", "thanh toán", "thanh toan", "vnpay", "hủy tour", "huy tour", "quy trình đặt"]):
        return (
            "Quy trình đặt tour và thanh toán trên website SmartTravel rất đơn giản, nhanh chóng và an toàn:\n\n"
            "1. Chọn tour: Truy cập mục 'Tour du lịch' hoặc bấm xem chi tiết các tour do trợ lý AI gợi ý.\n"
            "2. Điền thông tin: Chọn ngày khởi hành mong muốn, số lượng hành khách và thông tin liên hệ.\n"
            "3. Áp dụng ưu đãi: Nhập mã voucher khuyến mãi (nếu có) để nhận giảm giá.\n"
            "4. Thanh toán: Xác nhận và thanh toán trực tuyến qua cổng VNPay bảo mật (hỗ trợ quét mã VNPAY-QR, thẻ ATM nội địa hoặc thẻ quốc tế)."
        )
    if any(phrase in normalized for phrase in ["web có gì", "trang web", "smarttravel", "dự án", "tính năng", "chức năng", "website có gì"]):
        return (
            "SmartTravel là hệ thống du lịch thông minh toàn diện, tích hợp các dịch vụ cốt lõi:\n\n"
            "• Đặt tour du lịch trực tuyến: Đa dạng các hành trình biển đảo, nghỉ dưỡng, văn hóa lịch sử và khám phá thiên nhiên với giá niêm yết rõ ràng.\n"
            "• Thuê Hướng dẫn viên bản địa: Kết nối HDV chuyên nghiệp đã được chứng thực định danh CCCD/KYC.\n"
            "• Bản đồ & Thời tiết 63 tỉnh thành: Cập nhật liên tục thời tiết thực tế để bạn chọn thời điểm du lịch lý tưởng.\n"
            "• Khuyến mãi & Thanh toán an toàn: Kho voucher phong phú và thanh toán trực tuyến qua VNPay."
        )
    return None


def _needs_travel_guidance(message: str) -> bool:
    normalized = message.lower()
    return any(keyword in normalized for keyword in [
        "tour", "du lịch", "du lich", "đi đâu", "di dau", "lịch trình", "lich trinh",
        "ngân sách", "ngan sach", "tham quan", "đặt tour", "dat tour", "kỳ nghỉ", "ky nghi",
        "thì sao", "thi sao", "có gì", "co gi", "chơi gì", "choi gi", "ăn gì", "an gi",
        "tư vấn", "tu van", "gợi ý", "goi y", "chuyến đi", "chuyen di",
    ])


def _is_weather_request(message: str) -> bool:
    normalized = message.lower()
    return "thời tiết" in normalized or "thoi tiet" in normalized or "mưa không" in normalized or "mua khong" in normalized


def _guidance_reply(message: str, city: str, max_budget: Optional[float]) -> Optional[str]:
    if not _needs_travel_guidance(message):
        return None
    if not city and max_budget is not None:
        return f"Ngân sách {max_budget:,.0f}đ của bạn rất tuyệt vời! Bạn đang muốn tìm tour hoặc khám phá tỉnh thành nào (ví dụ: Hà Giang, Đà Nẵng, Đà Lạt, Sa Pa, Phú Quốc, Nha Trang, Ninh Bình...)?"
    return None


def _extract_budget(message: str) -> Optional[float]:
    normalized = message.lower().replace(" ", "")
    match = re.search(r"(?:dưới|duoi|tốiđa|toida|khôngquá|khongqua|\bgiá\b|\bgia\b)\D{0,8}(\d[\d.,]*)\s*(triệu|tr|k|nghìn|nghin)?", normalized)
    if not match:
        match = re.search(r"(\d[\d.,]*)\s*(triệu|tr)\b", normalized)
    if not match:
        return None
    amount_text = match.group(1)
    unit = match.group(2) or ""
    if unit:
        amount = float(amount_text.replace(",", "."))
    elif re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", amount_text):
        amount = float(amount_text.replace(".", "").replace(",", ""))
    else:
        amount = float(amount_text.replace(",", "."))
    if unit in {"triệu", "tr"}:
        amount *= 1_000_000
    elif unit in {"k", "nghìn", "nghin"}:
        amount *= 1_000
    elif amount < 1000:
        amount *= 1_000_000
    return amount


def _extract_city(message: str, requested_city: Optional[str]) -> str:
    if requested_city and requested_city.strip():
        req = requested_city.strip().lower()
        if req in CANONICAL_CITY_NAMES:
            return CANONICAL_CITY_NAMES[req]
        for key, aliases in LOCATION_ALIASES.items():
            if any(alias in req for alias in aliases):
                return CANONICAL_CITY_NAMES.get(key, requested_city.strip())
        return requested_city.strip()

    lowered = message.lower()
    matches = []
    for key, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            escaped = re.escape(alias)
            match = re.search(r"(?<![a-zA-ZÀ-ỹ0-9])" + escaped + r"(?![a-zA-ZÀ-ỹ0-9])", lowered)
            if match:
                matches.append((len(alias), CANONICAL_CITY_NAMES.get(key, key.title())))
    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]
    return ""


def _extract_route(message: str, requested_city: Optional[str]) -> Optional[Dict[str, Any]]:
    lowered = message.lower()
    if not re.search(r"\btừ\b", lowered) or not re.search(r"\b(?:đến|tới)\b", lowered):
        return None

    city_hits = []
    for key, aliases in LOCATION_ALIASES.items():
        canonical = CANONICAL_CITY_NAMES.get(key, key.title())
        for alias in [key] + aliases:
            match = re.search(r"(?<![a-zA-ZÀ-ỹ0-9])" + re.escape(alias) + r"(?![a-zA-ZÀ-ỹ0-9])", lowered)
            if match:
                city_hits.append((match.start(), match.end(), canonical))
                break

    city_hits.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    ordered_cities = []
    for _, _, city in city_hits:
        if city not in ordered_cities:
            ordered_cities.append(city)

    destination = _extract_city(message, requested_city)
    if requested_city and requested_city.strip():
        destination = _extract_city("", requested_city)
    if destination and destination not in ordered_cities:
        ordered_cities.append(destination)
    if len(ordered_cities) < 2:
        return None

    return {
        "origin": ordered_cities[0],
        "destination": destination or ordered_cities[-1],
        "stops": ordered_cities[1:-1],
    }



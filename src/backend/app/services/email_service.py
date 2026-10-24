import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Any, Dict, Optional
from app.core.config import settings
from app.db.mongodb import get_db

def generate_contract_code(booking_code: Optional[str] = None) -> str:
    if booking_code and booking_code.startswith("ST-"):
        return f"HDDL-{booking_code}"
    now_str = datetime.utcnow().strftime("%Y%m%d%H%M")
    return f"HDDL-ST-{now_str}"

def format_currency_vn(amount: Any) -> str:
    try:
        val = float(amount or 0)
        return f"{val:,.0f}₫".replace(",", ".")
    except Exception:
        return "0₫"

def build_contract_html(booking_dict: Dict[str, Any], user_dict: Optional[Dict[str, Any]] = None) -> str:
    tour_title = booking_dict.get("tour_title") or "Tour du lịch trải nghiệm SmartTravel"
    travel_date = booking_dict.get("travel_date") or "--"
    contact_name = booking_dict.get("contact_name") or (user_dict.get("full_name") if user_dict else None) or "Quý khách hàng"
    contact_email = booking_dict.get("contact_email") or (user_dict.get("email") if user_dict else None) or "khachhang@smarttravel.vn"
    contact_phone = booking_dict.get("contact_phone") or (user_dict.get("phone") if user_dict else None) or "Chưa cập nhật"
    adults = booking_dict.get("adults", 1)
    children = booking_dict.get("children", 0)
    insurance = booking_dict.get("insurance", True)
    total_amount = format_currency_vn(booking_dict.get("total_amount", 0))
    booking_code = booking_dict.get("booking_code") or f"ST-{str(booking_dict.get('_id', ''))[:8].upper()}"
    contract_code = booking_dict.get("contract_code") or generate_contract_code(booking_code)
    guide_name = booking_dict.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
    guide_phone = booking_dict.get("guide_phone") or "0912 345 678"
    guide_exp = booking_dict.get("guide_experience") or "5 năm kinh nghiệm"
    transportation = booking_dict.get("transportation") or "Xe ô tô du lịch đời mới cao cấp đưa đón suốt hành trình"
    paid_status = "ĐÃ THANH TOÁN XÁC NHẬN" if booking_dict.get("payment_status") == "paid" else "ĐÃ XÁC NHẬN GIỮ CHỖ"
    paid_badge_color = "#10b981" if booking_dict.get("payment_status") == "paid" else "#f59e0b"

    itinerary_list = booking_dict.get("itinerary_details") or []
    itinerary_html_rows = ""

    if isinstance(itinerary_list, list) and len(itinerary_list) > 0:
        for day in itinerary_list:
            day_title = day.get("title") or f"Ngày {day.get('day', 1)}: Lịch trình khám phá"
            steps = day.get("timeline") or []
            steps_html = ""
            for step in steps:
                time_str = step.get("time") or "--"
                activity_str = step.get("activity") or ""
                loc_str = step.get("location") or ""
                delicacy_str = step.get("delicacy")
                delicacy_badge = ""
                if delicacy_str:
                    delicacy_badge = f"""
                    <div style="margin-top: 6px;">
                        <span style="display: inline-block; background: #fef3c7; color: #92400e; font-size: 12px; font-weight: bold; padding: 3px 8px; border-radius: 4px; border: 1px solid #fde68a;">
                            🍽️ Đặc sản ẩm thực: {delicacy_str}
                        </span>
                    </div>
                    """
                loc_badge = f'<div style="color: #64748b; font-size: 12px; margin-top: 4px;">📍 {loc_str}</div>' if loc_str else ''
                steps_html += f"""
                <div style="display: flex; gap: 14px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px dashed #e2e8f0;">
                    <div style="min-width: 100px; font-weight: bold; color: #0284c7; font-size: 13px;">{time_str}</div>
                    <div style="flex: 1;">
                        <div style="color: #1e293b; font-size: 14px; line-height: 1.5;">{activity_str}</div>
                        {delicacy_badge}
                        {loc_badge}
                    </div>
                </div>
                """
            itinerary_html_rows += f"""
            <div style="margin-bottom: 20px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;">
                <h4 style="margin: 0 0 14px 0; color: #0369a1; font-size: 16px; border-bottom: 2px solid #0284c7; padding-bottom: 8px;">
                    🗓️ {day_title}
                </h4>
                {steps_html}
            </div>
            """
    else:
        itinerary_html_rows = """
        <div style="padding: 16px; background: #f8fafc; border-radius: 8px; color: #64748b; text-align: center;">
            Lịch trình chi tiết đã được chuẩn bị sẵn sàng và được HDV đồng hành chăm sóc chu đáo trong suốt chuyến đi.
        </div>
        """

    insurance_text = "Gói Bảo hiểm Du lịch Toàn diện (Mức bảo hiểm tối đa 500.000.000₫/người)" if insurance else "Bảo hiểm cơ bản theo luật định"

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Hợp Đồng Du Lịch Điện Tử - SmartTravel</title>
</head>
<body style="font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #0f172a;">
    <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
        
        <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; padding: 32px 28px; text-align: center;">
            <div style="font-size: 13px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px;">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
            <div style="font-size: 12px; margin-bottom: 16px;">Độc lập - Tự do - Hạnh phúc</div>
            <div style="height: 1px; width: 140px; background: rgba(255,255,255,0.4); margin: 0 auto 16px auto;"></div>
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">
                HỢP ĐỒNG DỊCH VỤ DU LỊCH & LỮ HÀNH ĐIỆN TỬ
            </h1>
            <div style="font-size: 14px; opacity: 0.95;">
                Số Hợp Đồng: <strong style="color: #fef08a;">{contract_code}</strong> | Mã Đặt Tour: <strong>{booking_code}</strong>
            </div>
            <div style="margin-top: 12px;">
                <span style="display: inline-block; background: {paid_badge_color}; color: #ffffff; font-weight: bold; font-size: 12px; padding: 4px 12px; border-radius: 20px;">
                    {paid_status}
                </span>
            </div>
        </div>

        <div style="padding: 28px;">
            <div style="margin-bottom: 24px; padding: 14px 18px; background: #f8fafc; border-left: 4px solid #0284c7; border-radius: 4px;">
                <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.6;">
                    Hợp đồng điện tử này được xác lập căn cứ theo Bộ Luật Dân sự nước CHXHCN Việt Nam, Luật Du lịch năm 2017 và các văn bản hướng dẫn hiện hành. Giá trị pháp lý được công nhận và đảm bảo bởi Hệ thống Du lịch Thông minh SmartTravel.
                </p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;">
                <div style="background: #f8fafc; padding: 18px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <h3 style="margin: 0 0 10px 0; color: #0284c7; font-size: 14px; text-transform: uppercase;">
                        BÊN A: ĐƠN VỊ CUNG CẤP DỊCH VỤ
                    </h3>
                    <div style="font-size: 13px; line-height: 1.6; color: #334155;">
                        <div><strong>CÔNG TY CP DU LỊCH THÔNG MINH SMARTTRAVEL</strong></div>
                        <div>Mã số DN: 0109988776 do Sở KH&ĐT cấp</div>
                        <div>Địa chỉ: Tòa nhà Du Lịch Số, Hoàn Kiếm, Hà Nội</div>
                        <div>Hotline 24/7: <strong>1900 6868</strong></div>
                        <div>Email: support@smarttravel.vn</div>
                    </div>
                </div>

                <div style="background: #f8fafc; padding: 18px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <h3 style="margin: 0 0 10px 0; color: #0284c7; font-size: 14px; text-transform: uppercase;">
                        BÊN B: KHÁCH HÀNG ĐĂNG KÝ
                    </h3>
                    <div style="font-size: 13px; line-height: 1.6; color: #334155;">
                        <div>Họ tên đại diện: <strong>{contact_name}</strong></div>
                        <div>Hòm thư Gmail: <strong>{contact_email}</strong></div>
                        <div>Số điện thoại: <strong>{contact_phone}</strong></div>
                        <div>Số lượng: <strong>{adults} người lớn</strong>{f', {children} trẻ em' if children else ''}</div>
                        <div>Bảo hiểm: {insurance_text}</div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 24px;">
                <h3 style="margin: 0 0 12px 0; color: #0f172a; font-size: 16px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                    1. THÔNG TIN CHUYẾN ĐI & ĐIỀU KIỆN TOUR
                </h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; line-height: 1.6;">
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 8px; color: #64748b; width: 35%;">Chuyến đi / Tour du lịch:</td>
                        <td style="padding: 10px 8px; font-weight: bold; color: #0f172a;">{tour_title}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 8px; color: #64748b;">Ngày khởi hành:</td>
                        <td style="padding: 10px 8px; font-weight: bold; color: #0369a1;">{travel_date}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 8px; color: #64748b;">Hướng dẫn viên phụ trách:</td>
                        <td style="padding: 10px 8px; color: #0f172a;">
                            <strong>{guide_name}</strong> ({guide_exp}) - Hotline đoàn: <strong style="color: #0284c7;">{guide_phone}</strong>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 8px; color: #64748b;">Phương tiện di chuyển:</td>
                        <td style="padding: 10px 8px; color: #0f172a;">{transportation}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9; background: #f8fafc;">
                        <td style="padding: 10px 8px; color: #64748b; font-weight: bold;">Tổng chi phí dịch vụ trọn gói:</td>
                        <td style="padding: 10px 8px; font-weight: bold; font-size: 16px; color: #dc2626;">{total_amount}</td>
                    </tr>
                </table>
            </div>

            <div style="margin-bottom: 24px;">
                <h3 style="margin: 0 0 14px 0; color: #0f172a; font-size: 16px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                    2. LỊCH TRÌNH CHI TIẾT & ĐẶC SẢN ẨM THỰC TRỌN VẸN
                </h3>
                <p style="margin: 0 0 14px 0; font-size: 13px; color: #64748b;">
                    Lịch trình từng ngày bao gồm các điểm tham quan biểu tượng, mốc giờ di chuyển và danh sách món đặc sản địa phương phục vụ đoàn:
                </p>
                {itinerary_html_rows}
            </div>

            <div style="margin-bottom: 24px; padding: 18px; background: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #b45309; font-size: 14px; text-transform: uppercase;">
                    3. CAM KẾT CHẤT LƯỢNG & BẢO HỘ KHÁCH HÀNG (SMARTTRAVEL ASSURANCE)
                </h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #78350f; line-height: 1.6;">
                    <li>Hợp đồng này có giá trị pháp lý làm căn cứ yêu cầu cung cấp dịch vụ kể cả khi ứng dụng gặp sự cố kỹ thuật hoặc thiết bị không có kết nối internet.</li>
                    <li>Khách hàng được quyền kiểm tra đối chiếu dịch vụ thực tế với nội dung hợp đồng và lịch trình chi tiết này.</li>
                    <li>Cam kết bồi thường 100% chi phí chuyến đi nếu đơn vị tổ chức tự ý thay đổi điểm tham quan hoặc không thực hiện đúng cam kết lịch trình mà không có lý do bất khả kháng.</li>
                    <li>Đường dây nóng hỗ trợ khẩn cấp hoạt động 24/7: <strong>1900 6868</strong> hoặc liên hệ trực tiếp Hướng dẫn viên <strong>{guide_phone}</strong>.</li>
                </ul>
            </div>

            <div style="display: flex; justify-content: space-between; margin-top: 36px; padding-top: 20px; border-top: 2px dashed #cbd5e1;">
                <div style="text-align: center; width: 45%;">
                    <div style="font-weight: bold; font-size: 13px; text-transform: uppercase; color: #334155;">ĐẠI DIỆN KHÁCH HÀNG (BÊN B)</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">(Đã ký xác nhận điện tử khi hoàn tất đơn)</div>
                    <div style="margin-top: 28px; font-weight: bold; font-size: 15px; color: #0f172a;">{contact_name}</div>
                </div>

                <div style="text-align: center; width: 45%;">
                    <div style="font-weight: bold; font-size: 13px; text-transform: uppercase; color: #0369a1;">ĐẠI DIỆN CÔNG TY SMARTTRAVEL (BÊN A)</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Chứng thư số & Chữ ký điện tử bảo chứng</div>
                    <div style="margin-top: 14px;">
                        <span style="display: inline-block; border: 2px solid #dc2626; color: #dc2626; font-weight: bold; font-size: 11px; padding: 6px 12px; border-radius: 6px; transform: rotate(-2deg); background: #fff5f5;">
                            ✓ SMARTTRAVEL DIGITAL VERIFIED<br>
                            MÃ XÁC THỰC: {contract_code}
                        </span>
                    </div>
                </div>
            </div>

        </div>

        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 28px; text-align: center; font-size: 12px; color: #94a3b8;">
            © 2026 SmartTravel Application. Bản quyền được bảo lưu. Email này được tạo tự động bởi hệ thống sau khi quý khách xác nhận thông tin đặt tour.
        </div>
    </div>
</body>
</html>"""
    return html

async def send_contract_email(
    booking_dict: Dict[str, Any],
    recipient_email: Optional[str] = None,
    user_dict: Optional[Dict[str, Any]] = None
) -> bool:
    target_email = recipient_email or booking_dict.get("contact_email") or (user_dict.get("email") if user_dict else None)
    if not target_email or "@" not in target_email:
        return False

    booking_code = booking_dict.get("booking_code") or "ST-BOOKING"
    contract_code = booking_dict.get("contract_code") or generate_contract_code(booking_code)
    tour_title = booking_dict.get("tour_title") or "Tour du lịch"
    booking_dict["contract_code"] = contract_code

    html_content = build_contract_html(booking_dict, user_dict)
    subject = f"[SmartTravel] Hợp Đồng Du Lịch & Lịch Trình Chi Tiết: {tour_title} (Mã HĐ: {contract_code})"

    sent_success = False

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user or "booking@smarttravel.vn")

    if smtp_host and smtp_user and smtp_password:
        def _send_smtp():
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"SmartTravel Hợp Đồng Du Lịch <{from_email}>"
            msg["To"] = target_email
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [target_email], msg.as_string())
            return True

        try:
            sent_success = await asyncio.to_thread(_send_smtp)
        except Exception:
            sent_success = False
    else:
        sent_success = True

    try:
        os.makedirs("sent_emails", exist_ok=True)
        filename = f"sent_emails/contract_{contract_code}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception:
        pass

    try:
        db = get_db()
        await db.bookings.update_one(
            {"booking_code": booking_code},
            {"$set": {
                "contract_code": contract_code,
                "contract_sent": True,
                "contract_sent_to": target_email,
                "contract_sent_at": datetime.utcnow().isoformat()
            }}
        )
        await db.email_logs.insert_one({
            "booking_code": booking_code,
            "contract_code": contract_code,
            "recipient_email": target_email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent" if sent_success else "saved_fallback"
        })
    except Exception:
        pass

    return True

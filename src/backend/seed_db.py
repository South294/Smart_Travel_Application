import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import pymongo
import bcrypt
from datetime import datetime

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "smart_travel")

def hash_pw(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

async def seed_database():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]

    try:
        await client.admin.command("ping")
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return

    await db.tours.create_index([("geo_location", pymongo.GEOSPHERE)])
    await db.tours.create_index("slug", unique=True)
    await db.tours.create_index("category")
    await db.tours.create_index("is_active")
    await db.users.create_index("email", unique=True)
    await db.vouchers.create_index("code", unique=True)
    await db.vouchers.create_index("is_active")
    await db.bookings.create_index("user_id")
    await db.bookings.create_index("tour_id")
    await db.bookings.create_index("status")
    await db.guides.create_index("user_id")
    await db.guides.create_index("status")
    print("Indexes created.")

    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@smarttravel.vn")
    admin_user = await db.users.find_one({"email": admin_email})
    if not admin_user:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_pw(admin_password),
            "full_name": "Admin SmartTravel",
            "phone": "0901000000",
            "birth_date": "1990-01-15",
            "gender": "nam",
            "address": "Hà Nội",
            "role": "admin",
            "preferences": [],
            "custom_preferences": [],
            "saved_vouchers": [],
            "settings": {
                "email_notifications": True,
                "sms_notifications": False,
                "ai_personalization": True,
                "language": "vi"
            },
            "avatar_url": "",
            "created_at": datetime.utcnow().isoformat()
        })
        print("Admin seeded.")
    else:
        print("Admin already exists.")

    demo_users = [
        {
            "email": "son.vu@gmail.com",
            "password_hash": hash_pw("123456"),
            "full_name": "Vũ Văn Sơn",
            "phone": "0912345678",
            "birth_date": "1998-05-20",
            "gender": "nam",
            "address": "Mộc Châu, Sơn La",
            "role": "user",
            "preferences": ["núi", "trekking", "khám phá"],
            "custom_preferences": ["thích cắm trại", "chụp ảnh thiên nhiên"],
            "saved_vouchers": [],
            "settings": {"email_notifications": True, "sms_notifications": False, "ai_personalization": True, "language": "vi"},
            "avatar_url": "",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "email": "nam.nguyen@gmail.com",
            "password_hash": hash_pw("123456"),
            "full_name": "Nguyễn Thanh Nam",
            "phone": "0987654321",
            "birth_date": "1995-11-10",
            "gender": "nam",
            "address": "Hà Nội",
            "role": "user",
            "preferences": ["biển", "ẩm thực", "nghỉ dưỡng"],
            "custom_preferences": ["khách sạn gần biển", "hải sản tươi sống"],
            "saved_vouchers": [],
            "settings": {"email_notifications": True, "sms_notifications": True, "ai_personalization": True, "language": "vi"},
            "avatar_url": "",
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    for demo_user in demo_users:
        await db.users.update_one(
            {"email": demo_user["email"]},
            {"$set": demo_user},
            upsert=True
        )

    tours = [
        {
            "title": "Vịnh Hạ Long 2 ngày 1 đêm - Du thuyền đẳng cấp",
            "slug": "vinh-ha-long",
            "category": "sea",
            "location": "Quảng Ninh",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2500000,
            "discount_price": 2200000,
            "rating": 4.9,
            "review_count": 1420,
            "images": ["https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "sea"],
            "is_active": True,
            "lat": 20.9101,
            "lng": 107.1839,
            "geo_location": {"type": "Point", "coordinates": [107.1839, 20.9101]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Mộc Châu Mộng Mơ - Đồi chè & Thác Dải Yếm 3N2Đ",
            "slug": "moc-chau-mong-mo",
            "category": "mountain",
            "location": "Sơn La",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3500000,
            "discount_price": 2800000,
            "rating": 4.8,
            "review_count": 980,
            "images": ["https://images.unsplash.com/photo-1622300025619-a1b7e4522944?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "mountain"],
            "is_active": True,
            "lat": 20.8320,
            "lng": 104.6328,
            "geo_location": {"type": "Point", "coordinates": [104.6328, 20.8320]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Trekking Sapa - Chinh phục Đỉnh Fansipan 3N2Đ",
            "slug": "trekking-sapa-fansipan",
            "category": "mountain",
            "location": "Lào Cai",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3200000,
            "discount_price": 2890000,
            "rating": 4.9,
            "review_count": 1250,
            "images": ["https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "adventure", "mountain", "trekking"],
            "is_active": True,
            "lat": 22.3364,
            "lng": 103.8438,
            "geo_location": {"type": "Point", "coordinates": [103.8438, 22.3364]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Hà Giang Loop - Cung đèo Hạnh Phúc 4N3Đ",
            "slug": "ha-giang-loop",
            "category": "mountain",
            "location": "Hà Giang",
            "duration_days": 4,
            "duration_nights": 3,
            "price": 3800000,
            "discount_price": 3400000,
            "rating": 4.9,
            "review_count": 2300,
            "images": ["https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "adventure", "best-seller", "mountain"],
            "is_active": True,
            "lat": 23.2753,
            "lng": 104.9843,
            "geo_location": {"type": "Point", "coordinates": [104.9843, 23.2753]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Đà Nẵng - Cầu Vàng Bà Nà Hills & Bán đảo Sơn Trà 3N2Đ",
            "slug": "da-nang-ba-na-hills",
            "category": "sight",
            "location": "Đà Nẵng",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3900000,
            "discount_price": 3450000,
            "rating": 4.9,
            "review_count": 3100,
            "images": ["https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "resort", "sight"],
            "is_active": True,
            "lat": 16.0544,
            "lng": 108.2022,
            "geo_location": {"type": "Point", "coordinates": [108.2022, 16.0544]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Hội An Cổ Kính - Thuyền hoa đăng & Rừng Dừa Bảy Mẫu",
            "slug": "hoi-an-di-san",
            "category": "sight",
            "location": "Quảng Nam",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1400000,
            "discount_price": 1150000,
            "rating": 4.8,
            "review_count": 1850,
            "images": ["https://images.unsplash.com/photo-1557750255-c76072a7aaeb?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "sight", "hot"],
            "is_active": True,
            "lat": 15.8801,
            "lng": 108.3380,
            "geo_location": {"type": "Point", "coordinates": [108.3380, 15.8801]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Cố Đô Huế - Di sản Hoàng cung & Ca Huế Sông Hương 2N1Đ",
            "slug": "hue-co-kinh",
            "category": "sight",
            "location": "Thừa Thiên Huế",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1900000,
            "discount_price": 1650000,
            "rating": 4.7,
            "review_count": 920,
            "images": ["https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "heritage", "sight"],
            "is_active": True,
            "lat": 16.4637,
            "lng": 107.5909,
            "geo_location": {"type": "Point", "coordinates": [107.5909, 16.4637]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Nha Trang Biển Xanh - Lặn ngắm San hô Hòn Mun 3N2Đ",
            "slug": "nha-trang-bien-dao",
            "category": "sea",
            "location": "Khánh Hòa",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3600000,
            "discount_price": 3100000,
            "rating": 4.8,
            "review_count": 1680,
            "images": ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "sea", "adventure"],
            "is_active": True,
            "lat": 12.2388,
            "lng": 109.1967,
            "geo_location": {"type": "Point", "coordinates": [109.1967, 12.2388]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Quy Nhơn - Kỳ Co Eo Gió Thiên Đường Biển Đảo 3N2Đ",
            "slug": "quy-nhon-ky-co",
            "category": "sea",
            "location": "Bình Định",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 2800000,
            "discount_price": 2400000,
            "rating": 4.8,
            "review_count": 1120,
            "images": ["https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "hot", "best-seller"],
            "is_active": True,
            "lat": 13.7820,
            "lng": 109.2194,
            "geo_location": {"type": "Point", "coordinates": [109.2194, 13.7820]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Đà Lạt Ngàn Hoa - Săn mây Đồi Chè & Cắm trại Hồ Tuyền Lâm 3N2Đ",
            "slug": "da-lat-san-may",
            "category": "mountain",
            "location": "Lâm Đồng",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 2900000,
            "discount_price": 2500000,
            "rating": 4.9,
            "review_count": 3400,
            "images": ["https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "mountain", "resort"],
            "is_active": True,
            "lat": 11.9404,
            "lng": 108.4583,
            "geo_location": {"type": "Point", "coordinates": [108.4583, 11.9404]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Phú Quốc Đảo Ngọc - Lặn biển ngắm San hô & Grand World 4N3Đ",
            "slug": "phu-quoc-sunset-san-ho",
            "category": "sea",
            "location": "Kiên Giang",
            "duration_days": 4,
            "duration_nights": 3,
            "price": 5200000,
            "discount_price": 4600000,
            "rating": 4.9,
            "review_count": 2890,
            "images": ["https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "luxury", "sea"],
            "is_active": True,
            "lat": 10.2899,
            "lng": 103.9840,
            "geo_location": {"type": "Point", "coordinates": [103.9840, 10.2899]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Ninh Bình Tràng An - Bái Đính Tuyệt Tình Cốc 2N1Đ",
            "slug": "ninh-binh-trang-an",
            "category": "sight",
            "location": "Ninh Bình",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1800000,
            "discount_price": 1490000,
            "rating": 4.8,
            "review_count": 1450,
            "images": ["https://images.unsplash.com/photo-1508873535684-277a3cbcc4e8?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "UNESCO", "sight", "hot"],
            "is_active": True,
            "lat": 20.2506,
            "lng": 105.9745,
            "geo_location": {"type": "Point", "coordinates": [105.9745, 20.2506]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Miền Tây Sông Nước - Chợ Nổi Cái Răng & Vườn Trái Cây 2N1Đ",
            "slug": "can-tho-cho-noi",
            "category": "sight",
            "location": "Cần Thơ",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1350000,
            "discount_price": 1150000,
            "rating": 4.7,
            "review_count": 870,
            "images": ["https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "food", "sight"],
            "is_active": True,
            "lat": 10.0452,
            "lng": 105.7469,
            "geo_location": {"type": "Point", "coordinates": [105.7469, 10.0452]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Măng Đen - Nàng Thơ Kon Tum & Thác Pa Sỹ 3N2Đ",
            "slug": "mang-den-tay-nguyen",
            "category": "mountain",
            "location": "Kon Tum",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3100000,
            "discount_price": 2750000,
            "rating": 4.8,
            "review_count": 640,
            "images": ["https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=960&q=80"],
            "tags": ["mountain", "eco", "hot"],
            "is_active": True,
            "lat": 14.6067,
            "lng": 108.2897,
            "geo_location": {"type": "Point", "coordinates": [108.2897, 14.6067]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Hà Nội Khám Phá - 36 Phố Cổ & Văn Miếu Quốc Tử Giám 1N",
            "slug": "ha-noi-pho-co",
            "category": "sight",
            "location": "Hà Nội",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 550000,
            "discount_price": 450000,
            "rating": 4.8,
            "review_count": 1820,
            "images": ["https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "sight", "food"],
            "is_active": True,
            "lat": 21.0285,
            "lng": 105.8542,
            "geo_location": {"type": "Point", "coordinates": [105.8542, 21.0285]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Côn Đảo Huyền Bí - Viếng Nghĩa Trang Hàng Dương 3N2Đ",
            "slug": "con-dao-huyen-bi",
            "category": "sea",
            "location": "Bà Rịa - Vũng Tàu",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 6200000,
            "discount_price": 5600000,
            "rating": 4.9,
            "review_count": 910,
            "images": ["https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "cultural", "hot"],
            "is_active": True,
            "lat": 8.6835,
            "lng": 106.6067,
            "geo_location": {"type": "Point", "coordinates": [106.6067, 8.6835]},
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    for tour in tours:
        await db.tours.update_one(
            {"slug": tour["slug"]},
            {"$set": tour},
            upsert=True
        )
    print(f"Tours seeded/updated: {len(tours)} records.")

    vouchers = [
        {
            "code": "SUMMER20",
            "title": "Chào Hè Sôi Động - Giảm 20% Tour Biển",
            "description": "Áp dụng cho tất cả các tour du lịch biển tại Hạ Long, Nha Trang, Phú Quốc. Tối đa giảm 500.000₫.",
            "discount_type": "percent",
            "discount_value": 20,
            "max_discount": 500000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "NEWUSER100K",
            "title": "Giảm 100K cho chuyến đi đầu tiên",
            "description": "Giảm trực tiếp 100.000₫ cho tất cả các hành trình khởi hành trong năm.",
            "discount_type": "fixed",
            "discount_value": 100000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "TREK500K",
            "title": "Khám Phá Rừng Cao - Giảm 500.000₫",
            "description": "Ưu đãi đặc quyền cho các tour leo núi và trekking Sapa, Mộc Châu, Hà Giang.",
            "discount_type": "fixed",
            "discount_value": 500000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "SAFEFREE",
            "title": "Tặng Gói Bảo Hiểm Du Lịch Toàn Diện",
            "description": "Miễn phí hoàn toàn gói bảo hiểm du lịch trị giá 300.000₫ cho toàn bộ đoàn khách.",
            "discount_type": "free_insurance",
            "discount_value": 300000,
            "expiry_date": "2026-12-31",
            "is_active": True
        }
    ]
    for voucher in vouchers:
        await db.vouchers.update_one(
            {"code": voucher["code"]},
            {"$set": voucher},
            upsert=True
        )
    print(f"Vouchers seeded/updated: {len(vouchers)} records.")

    son_user = await db.users.find_one({"email": "son.vu@gmail.com"})
    nam_user = await db.users.find_one({"email": "nam.nguyen@gmail.com"})
    if son_user:
        await db.guides.update_one(
            {"user_id": str(son_user["_id"])},
            {"$set": {
                "user_id": str(son_user["_id"]),
                "name": "Vũ Văn Sơn",
                "experience_years": 5,
                "price_per_day": 800000,
                "areas": ["Mộc Châu", "Sapa", "Hà Giang"],
                "languages": ["Tiếng Việt", "English"],
                "bio": "Hướng dẫn viên chuyên nghiệp miền núi phía Bắc, 5 năm kinh nghiệm dẫn đoàn trekking Fansipan và Hà Giang Loop.",
                "id_front_url": "",
                "id_back_url": "",
                "status": "approved",
                "created_at": datetime.utcnow().isoformat()
            }},
            upsert=True
        )
    if nam_user:
        await db.guides.update_one(
            {"user_id": str(nam_user["_id"])},
            {"$set": {
                "user_id": str(nam_user["_id"]),
                "name": "Nguyễn Thanh Nam",
                "experience_years": 4,
                "price_per_day": 750000,
                "areas": ["Đà Nẵng", "Hội An", "Huế"],
                "languages": ["Tiếng Việt", "English"],
                "bio": "Chuyên gia văn hóa miền Trung, am hiểu ẩm thực địa phương và lịch sử di sản Cố đô.",
                "id_front_url": "",
                "id_back_url": "",
                "status": "approved",
                "created_at": datetime.utcnow().isoformat()
            }},
            upsert=True
        )

    settings_doc = await db.settings.find_one({"key": "admin"})
    if not settings_doc:
        await db.settings.insert_one({
            "key": "admin",
            "value": {
                "maintenance_mode": False,
                "auto_approve_guides": True,
                "email_new_booking": True
            }
        })

    if son_user:
        tour_sapa = await db.tours.find_one({"slug": "trekking-sapa-fansipan"})
        tour_hagiang = await db.tours.find_one({"slug": "ha-giang-loop"})
        if tour_sapa and tour_hagiang:
            await db.bookings.update_one(
                {"user_id": str(son_user["_id"]), "tour_id": str(tour_sapa["_id"])},
                {"$set": {
                    "tour_id": str(tour_sapa["_id"]),
                    "travel_date": "2026-05-10",
                    "adults": 2,
                    "children": 0,
                    "insurance": True,
                    "coupon_code": "TREK500K",
                    "payment_method": "bank_transfer",
                    "contact_phone": "0912345678",
                    "note": "Chuẩn bị gậy trekking",
                    "user_id": str(son_user["_id"]),
                    "status": "completed",
                    "total_amount": 5400000,
                    "created_at": datetime.utcnow().isoformat()
                }},
                upsert=True
            )
            await db.bookings.update_one(
                {"user_id": str(son_user["_id"]), "tour_id": str(tour_hagiang["_id"])},
                {"$set": {
                    "tour_id": str(tour_hagiang["_id"]),
                    "travel_date": "2026-07-15",
                    "adults": 1,
                    "children": 0,
                    "insurance": True,
                    "coupon_code": None,
                    "payment_method": "credit_card",
                    "contact_phone": "0912345678",
                    "note": "Đi xe cào cào",
                    "user_id": str(son_user["_id"]),
                    "status": "confirmed",
                    "total_amount": 3550000,
                    "created_at": datetime.utcnow().isoformat()
                }},
                upsert=True
            )

    if nam_user:
        tour_halong = await db.tours.find_one({"slug": "vinh-ha-long"})
        tour_danang = await db.tours.find_one({"slug": "da-nang-ba-na-hills"})
        if tour_halong and tour_danang:
            await db.bookings.update_one(
                {"user_id": str(nam_user["_id"]), "tour_id": str(tour_halong["_id"])},
                {"$set": {
                    "tour_id": str(tour_halong["_id"]),
                    "travel_date": "2026-04-20",
                    "adults": 2,
                    "children": 1,
                    "insurance": True,
                    "coupon_code": "SUMMER20",
                    "payment_method": "e_wallet",
                    "contact_phone": "0987654321",
                    "note": "Ăn hải sản",
                    "user_id": str(nam_user["_id"]),
                    "status": "completed",
                    "total_amount": 5100000,
                    "created_at": datetime.utcnow().isoformat()
                }},
                upsert=True
            )
            await db.bookings.update_one(
                {"user_id": str(nam_user["_id"]), "tour_id": str(tour_danang["_id"])},
                {"$set": {
                    "tour_id": str(tour_danang["_id"]),
                    "travel_date": "2026-08-01",
                    "adults": 2,
                    "children": 0,
                    "insurance": False,
                    "coupon_code": None,
                    "payment_method": "bank_transfer",
                    "contact_phone": "0987654321",
                    "note": "Khách sạn gần bãi biển Mỹ Khê",
                    "user_id": str(nam_user["_id"]),
                    "status": "confirmed",
                    "total_amount": 6900000,
                    "created_at": datetime.utcnow().isoformat()
                }},
                upsert=True
            )

    client.close()
    print("Seed completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())

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
            "location": "Hạ Long, Quảng Ninh",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2500000,
            "discount_price": 2200000,
            "rating": 4.9,
            "review_count": 1420,
            "images": ["https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "sea", "hạ long", "quảng ninh"],
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
            "location": "Mộc Châu, Sơn La",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3500000,
            "discount_price": 2800000,
            "rating": 4.8,
            "review_count": 980,
            "images": ["https://images.unsplash.com/photo-1622300025619-a1b7e4522944?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "mountain", "mộc châu", "sơn la"],
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
            "location": "Sa Pa, Lào Cai",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3200000,
            "discount_price": 2890000,
            "rating": 4.9,
            "review_count": 1250,
            "images": ["https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "adventure", "mountain", "trekking", "sa pa", "sapa", "lào cai"],
            "is_active": True,
            "lat": 22.3364,
            "lng": 103.8438,
            "geo_location": {"type": "Point", "coordinates": [103.8438, 22.3364]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Sa Pa Bản Cát Cát & Cổng Trời Đèo Ô Quy Hồ Săn Mây 2N1Đ",
            "slug": "sapa-cat-cat-o-quy-ho",
            "category": "mountain",
            "location": "Sa Pa, Lào Cai",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2100000,
            "discount_price": 1850000,
            "rating": 4.8,
            "review_count": 1640,
            "images": ["https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "sa pa", "sapa", "mountain", "cát cát", "ô quy hồ", "resort"],
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
            "location": "Hội An, Quảng Nam",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1400000,
            "discount_price": 1150000,
            "rating": 4.8,
            "review_count": 1850,
            "images": ["https://images.unsplash.com/photo-1557750255-c76072a7aaeb?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "sight", "hot", "hội an", "quảng nam"],
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
            "location": "Huế, Thừa Thiên Huế",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1900000,
            "discount_price": 1650000,
            "rating": 4.7,
            "review_count": 920,
            "images": ["https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "heritage", "sight", "huế"],
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
            "location": "Nha Trang, Khánh Hòa",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3600000,
            "discount_price": 3100000,
            "rating": 4.8,
            "review_count": 1680,
            "images": ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "sea", "adventure", "nha trang", "khánh hòa", "hòn mun"],
            "is_active": True,
            "lat": 12.2388,
            "lng": 109.1967,
            "geo_location": {"type": "Point", "coordinates": [109.1967, 12.2388]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Nha Trang Du Thuyền Vịnh Biển & Tổ Hợp Giải Trí VinWonders 1N",
            "slug": "nha-trang-vinwonders-vinh-bien",
            "category": "sea",
            "location": "Nha Trang, Khánh Hòa",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 1350000,
            "discount_price": 1100000,
            "rating": 4.9,
            "review_count": 1980,
            "images": ["https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "sea", "nha trang", "vinwonders", "hòn tre"],
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
            "location": "Quy Nhơn, Bình Định",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 2800000,
            "discount_price": 2400000,
            "rating": 4.8,
            "review_count": 1120,
            "images": ["https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "hot", "best-seller", "quy nhơn", "kỳ co", "eo gió", "bình định"],
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
            "location": "Đà Lạt, Lâm Đồng",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 2900000,
            "discount_price": 2500000,
            "rating": 4.9,
            "review_count": 3400,
            "images": ["https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "mountain", "resort", "đà lạt", "lâm đồng", "cầu đất"],
            "is_active": True,
            "lat": 11.9404,
            "lng": 108.4583,
            "geo_location": {"type": "Point", "coordinates": [108.4583, 11.9404]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Đà Lạt City Tour - Đỉnh Langbiang & Máng Trượt Thác Datanla 1N",
            "slug": "da-lat-langbiang-datanla",
            "category": "mountain",
            "location": "Đà Lạt, Lâm Đồng",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 750000,
            "discount_price": 650000,
            "rating": 4.9,
            "review_count": 1850,
            "images": ["https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "đà lạt", "lâm đồng", "langbiang", "datanla", "mountain"],
            "is_active": True,
            "lat": 11.9404,
            "lng": 108.4583,
            "geo_location": {"type": "Point", "coordinates": [108.4583, 11.9404]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Đà Lạt Chill - Nông Trại Cún Puppy Farm & Vườn Dâu Tây 2N1Đ",
            "slug": "da-lat-puppy-farm-vuon-dau",
            "category": "mountain",
            "location": "Đà Lạt, Lâm Đồng",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1950000,
            "discount_price": 1690000,
            "rating": 4.8,
            "review_count": 1420,
            "images": ["https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "đà lạt", "lâm đồng", "puppy farm", "dâu tây", "resort"],
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
            "location": "Phú Quốc, Kiên Giang",
            "duration_days": 4,
            "duration_nights": 3,
            "price": 5200000,
            "discount_price": 4600000,
            "rating": 4.9,
            "review_count": 2890,
            "images": ["https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "luxury", "sea", "phú quốc", "kiên giang", "grand world"],
            "is_active": True,
            "lat": 10.2899,
            "lng": 103.9840,
            "geo_location": {"type": "Point", "coordinates": [103.9840, 10.2899]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Phú Quốc Cano 4 Đảo Hoang Sơ & Cáp Treo Vượt Biển Hòn Thơm 1N",
            "slug": "phu-quoc-cano-4-dao",
            "category": "sea",
            "location": "Phú Quốc, Kiên Giang",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 1200000,
            "discount_price": 950000,
            "rating": 4.9,
            "review_count": 2150,
            "images": ["https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "sea", "phú quốc", "kiên giang", "hòn thơm", "bãi sao"],
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
            "location": "Ninh Bình, Tràng An",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1800000,
            "discount_price": 1490000,
            "rating": 4.8,
            "review_count": 1450,
            "images": ["https://images.unsplash.com/photo-1508873535684-277a3cbcc4e8?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "UNESCO", "sight", "hot", "ninh bình", "tràng an"],
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
            "location": "Cần Thơ, Miền Tây",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1350000,
            "discount_price": 1150000,
            "rating": 4.7,
            "review_count": 870,
            "images": ["https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "food", "sight", "cần thơ", "chợ nổi"],
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
            "location": "Măng Đen, Kon Tum",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3100000,
            "discount_price": 2750000,
            "rating": 4.8,
            "review_count": 640,
            "images": ["https://images.unsplash.com/photo-1511497584788-87676104235f?auto=format&fit=crop&w=960&q=80"],
            "tags": ["mountain", "eco", "hot", "măng đen", "kon tum"],
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
            "tags": ["cultural", "sight", "food", "hà nội", "phố cổ"],
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
            "location": "Côn Đảo, Bà Rịa - Vũng Tàu",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 6200000,
            "discount_price": 5600000,
            "rating": 4.9,
            "review_count": 910,
            "images": ["https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "cultural", "hot", "côn đảo"],
            "is_active": True,
            "lat": 8.6835,
            "lng": 106.6067,
            "geo_location": {"type": "Point", "coordinates": [106.6067, 8.6835]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Đà Lạt Săn Mây Cầu Đất - Vườn Ánh Sáng Lumiere & Cà Phê Mê Linh 1N",
            "slug": "da-lat-san-may-cau-dat",
            "category": "mountain",
            "location": "Đà Lạt, Lâm Đồng",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 850000,
            "discount_price": 680000,
            "rating": 4.9,
            "review_count": 2180,
            "images": ["https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=960&q=80"],
            "tags": ["hot", "best-seller", "đà lạt", "lâm đồng", "cầu đất", "săn mây"],
            "is_active": True,
            "lat": 11.9404,
            "lng": 108.4583,
            "geo_location": {"type": "Point", "coordinates": [108.4583, 11.9404]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Trekking Rừng Thông Đà Lạt - Thác Hang Cọp & Chèo SUP Hồ Tuyền Lâm 2N1Đ",
            "slug": "da-lat-trekking-cheo-sup",
            "category": "mountain",
            "location": "Đà Lạt, Lâm Đồng",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2200000,
            "discount_price": 1850000,
            "rating": 4.8,
            "review_count": 1340,
            "images": ["https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80"],
            "tags": ["adventure", "trekking", "đà lạt", "lâm đồng", "hồ tuyền lâm"],
            "is_active": True,
            "lat": 11.9404,
            "lng": 108.4583,
            "geo_location": {"type": "Point", "coordinates": [108.4583, 11.9404]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Phú Quốc Nghỉ Dưỡng Thượng Lưu - Vinpearl Safari & Grand World Không Ngủ 3N2Đ",
            "slug": "phu-quoc-vinpearl-safari",
            "category": "sea",
            "location": "Phú Quốc, Kiên Giang",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 4800000,
            "discount_price": 4200000,
            "rating": 4.9,
            "review_count": 2760,
            "images": ["https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=960&q=80"],
            "tags": ["luxury", "resort", "phú quốc", "kiên giang", "safari", "grand world"],
            "is_active": True,
            "lat": 10.2899,
            "lng": 103.9840,
            "geo_location": {"type": "Point", "coordinates": [103.9840, 10.2899]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Sa Pa Mùa Lúa Chín - Thung Lũng Mường Hoa & Bản Tả Van Homestay 2N1Đ",
            "slug": "sapa-muong-hoa-ta-van",
            "category": "mountain",
            "location": "Sa Pa, Lào Cai",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2000000,
            "discount_price": 1750000,
            "rating": 4.8,
            "review_count": 1580,
            "images": ["https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "mountain", "sa pa", "sapa", "lào cai", "mường hoa"],
            "is_active": True,
            "lat": 22.3364,
            "lng": 103.8438,
            "geo_location": {"type": "Point", "coordinates": [103.8438, 22.3364]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Nha Trang Khám Phá Vịnh Vĩnh Hy - Hang Rái & Vườn Nho Ninh Thuận 1N",
            "slug": "nha-trang-vinh-hy-hang-rai",
            "category": "sea",
            "location": "Nha Trang, Khánh Hòa",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 1050000,
            "discount_price": 890000,
            "rating": 4.8,
            "review_count": 1420,
            "images": ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sight", "sea", "nha trang", "khánh hòa", "vịnh vĩnh hy"],
            "is_active": True,
            "lat": 12.2388,
            "lng": 109.1967,
            "geo_location": {"type": "Point", "coordinates": [109.1967, 12.2388]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Đà Nẵng - Cù Lao Chàm Lặn Ngắm San Hô & Phố Cổ Hội An 2N1Đ",
            "slug": "da-nang-cu-lao-cham-hoi-an",
            "category": "sea",
            "location": "Đà Nẵng",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2250000,
            "discount_price": 1890000,
            "rating": 4.9,
            "review_count": 2490,
            "images": ["https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "cultural", "hot", "đà nẵng", "hội an", "cù lao chàm"],
            "is_active": True,
            "lat": 16.0544,
            "lng": 108.2022,
            "geo_location": {"type": "Point", "coordinates": [108.2022, 16.0544]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Vịnh Lan Hạ - Đảo Cát Bà Chèo Thuyền Kayak & Làng Chài Cái Bèo 2N1Đ",
            "slug": "vinh-lan-ha-cat-ba",
            "category": "sea",
            "location": "Hạ Long, Quảng Ninh",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2700000,
            "discount_price": 2350000,
            "rating": 4.9,
            "review_count": 1890,
            "images": ["https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "kayak", "hạ long", "quảng ninh", "lan hạ", "cát bà"],
            "is_active": True,
            "lat": 20.9101,
            "lng": 107.1839,
            "geo_location": {"type": "Point", "coordinates": [107.1839, 20.9101]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Ninh Bình Trong Ngày - Tuyệt Tình Cốc, Tam Cốc Bích Động & Hang Múa 1N",
            "slug": "ninh-binh-trong-ngay",
            "category": "sight",
            "location": "Ninh Bình, Tràng An",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 990000,
            "discount_price": 850000,
            "rating": 4.8,
            "review_count": 1630,
            "images": ["https://images.unsplash.com/photo-1508873535684-277a3cbcc4e8?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sight", "cultural", "ninh bình", "tràng an", "hang múa"],
            "is_active": True,
            "lat": 20.2506,
            "lng": 105.9745,
            "geo_location": {"type": "Point", "coordinates": [105.9745, 20.2506]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Vũng Tàu Nghỉ Dưỡng - Hải Đăng Cổ, Tượng Chúa Kito & Bánh Khọt 2N1Đ",
            "slug": "vung-tau-nghi-duong",
            "category": "sea",
            "location": "Vũng Tàu",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1650000,
            "discount_price": 1450000,
            "rating": 4.7,
            "review_count": 1280,
            "images": ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "resort", "vũng tàu", "hải đăng"],
            "is_active": True,
            "lat": 10.4114,
            "lng": 107.1362,
            "geo_location": {"type": "Point", "coordinates": [107.1362, 10.4114]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Phan Thiết Mũi Né - Đồi Cát Bay, Bàu Trắng & Làng Chài Xưa 2N1Đ",
            "slug": "phan-thiet-mui-ne-doi-cat",
            "category": "sea",
            "location": "Phan Thiết, Bình Thuận",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2250000,
            "discount_price": 1950000,
            "rating": 4.8,
            "review_count": 1750,
            "images": ["https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "resort", "phan thiết", "mũi né", "bàu trắng"],
            "is_active": True,
            "lat": 10.9274,
            "lng": 108.1018,
            "geo_location": {"type": "Point", "coordinates": [108.1018, 10.9274]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Sài Gòn Sắc Màu - Dinh Độc Lập, Địa Đạo Củ Chi & Du Thuyền Sông Sài Gòn 1N",
            "slug": "sai-gon-sac-mau-cu-chi",
            "category": "sight",
            "location": "Hồ Chí Minh",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 890000,
            "discount_price": 750000,
            "rating": 4.8,
            "review_count": 1940,
            "images": ["https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "sight", "hồ chí minh", "sài gòn", "củ chi"],
            "is_active": True,
            "lat": 10.8231,
            "lng": 106.6297,
            "geo_location": {"type": "Point", "coordinates": [106.6297, 10.8231]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Phú Thọ Cội Nguồn Dân Tộc - Khu Di Tích Đền Hùng & Đồi Chè Long Cốc 2N1Đ",
            "slug": "phu-tho-den-hung-long-coc",
            "category": "cultural",
            "location": "Phú Thọ",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1650000,
            "discount_price": 1390000,
            "rating": 4.9,
            "review_count": 1520,
            "images": ["https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "heritage", "phú thọ", "đền hùng", "long cốc", "hot"],
            "is_active": True,
            "lat": 21.3917,
            "lng": 105.3211,
            "geo_location": {"type": "Point", "coordinates": [105.3211, 21.3917]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Cao Bằng Non Nước - Thác Bản Giốc Hùng Vĩ & Suối Lê-nin Pác Bó 3N2Đ",
            "slug": "cao-bang-ban-gioc-pac-bo",
            "category": "mountain",
            "location": "Cao Bằng",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 2850000,
            "discount_price": 2490000,
            "rating": 4.9,
            "review_count": 1820,
            "images": ["https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=960&q=80"],
            "tags": ["mountain", "cultural", "cao bằng", "bản giốc", "pác bó"],
            "is_active": True,
            "lat": 22.6667,
            "lng": 106.2500,
            "geo_location": {"type": "Point", "coordinates": [106.2500, 22.6667]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Quảng Bình Kỳ Vĩ - Động Thiên Đường & Suối Nước Moọc 3N2Đ",
            "slug": "quang-binh-thien-duong-mooc",
            "category": "sight",
            "location": "Quảng Bình",
            "duration_days": 3,
            "duration_nights": 2,
            "price": 3100000,
            "discount_price": 2750000,
            "rating": 4.9,
            "review_count": 2100,
            "images": ["https://images.unsplash.com/photo-1508873535684-277a3cbcc4e8?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sight", "adventure", "quảng bình", "phong nha", "thiên đường"],
            "is_active": True,
            "lat": 17.4689,
            "lng": 106.6225,
            "geo_location": {"type": "Point", "coordinates": [106.6225, 17.4689]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Phú Yên Hoa Vàng Trên Cỏ Xanh - Ghềnh Đá Đĩa & Mũi Điện Bãi Môn 2N1Đ",
            "slug": "phu-yen-ghenh-da-dia-mui-dien",
            "category": "sea",
            "location": "Phú Yên",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1950000,
            "discount_price": 1690000,
            "rating": 4.8,
            "review_count": 1670,
            "images": ["https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sea", "sight", "phú yên", "ghềnh đá đĩa", "mũi điện"],
            "is_active": True,
            "lat": 13.0881,
            "lng": 109.3094,
            "geo_location": {"type": "Point", "coordinates": [109.3094, 13.0881]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Tây Ninh Nóc Nhà Nam Bộ - Chinh Phục Núi Bà Đen & Tòa Thánh 1N",
            "slug": "tay-ninh-nui-ba-den",
            "category": "mountain",
            "location": "Tây Ninh",
            "duration_days": 1,
            "duration_nights": 0,
            "price": 850000,
            "discount_price": 690000,
            "rating": 4.8,
            "review_count": 1450,
            "images": ["https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=960&q=80"],
            "tags": ["mountain", "cultural", "tây ninh", "núi bà đen"],
            "is_active": True,
            "lat": 11.3000,
            "lng": 106.1000,
            "geo_location": {"type": "Point", "coordinates": [106.1000, 11.3000]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "An Giang Sông Nước - Rừng Tràm Trà Sư & Miếu Bà Chúa Xứ Núi Sam 2N1Đ",
            "slug": "an-giang-tra-su-nui-sam",
            "category": "sight",
            "location": "An Giang",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 1850000,
            "discount_price": 1550000,
            "rating": 4.8,
            "review_count": 1780,
            "images": ["https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=960&q=80"],
            "tags": ["cultural", "sight", "an giang", "trà sư", "châu đốc"],
            "is_active": True,
            "lat": 10.3833,
            "lng": 105.4167,
            "geo_location": {"type": "Point", "coordinates": [105.4167, 10.3833]},
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "title": "Cà Mau Đất Mũi - Cột Mốc Tọa Độ GPS 0001 & Rừng Đước U Minh 2N1Đ",
            "slug": "ca-mau-dat-mui-gps0001",
            "category": "sight",
            "location": "Cà Mau",
            "duration_days": 2,
            "duration_nights": 1,
            "price": 2100000,
            "discount_price": 1850000,
            "rating": 4.9,
            "review_count": 1390,
            "images": ["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=960&q=80"],
            "tags": ["sight", "cultural", "cà mau", "đất mũi"],
            "is_active": True,
            "lat": 9.1833,
            "lng": 105.1500,
            "geo_location": {"type": "Point", "coordinates": [105.1500, 9.1833]},
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    for tour in tours:
        tags = [str(tag).lower() for tag in tour.get("tags", [])]
        tour.setdefault("indoor", any(tag in tags for tag in ["indoor", "museum", "food"]))
        tour.setdefault("outdoor", not tour["indoor"])
        tour.setdefault("best_weather", ["rain"] if tour["indoor"] else ["clear", "cloudy"])
        tour.setdefault("estimated_duration_hours", tour["duration_days"] * 8)
        tour.setdefault("difficulty_level", "easy" if "mountain" not in tags and "trekking" not in tags else "moderate")
        tour.setdefault("suitable_for_children", "trekking" not in tags)
        tour.setdefault("suitable_for_elderly", "trekking" not in tags)
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
            "code": "TREK1999",
            "title": "Lên Rừng Vượt Thác - Đồng Giá Khám Phá Tây Bắc",
            "description": "Trải nghiệm trekking Sapa, Mộc Châu, Hà Giang dành cho nhóm từ 2 người trở lên. Tiết kiệm lên đến 35%.",
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
        },
        {
            "code": "VIETNAM500",
            "title": "Hành Trình Di Sản - Giảm 500.000₫ Đơn Từ 3 Triệu",
            "description": "Ưu đãi chào đón thành viên mới khám phá nét đẹp văn hóa cố đô Huế, Hội An, Tràng An Ninh Bình.",
            "discount_type": "fixed",
            "discount_value": 500000,
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
            "code": "DALATFLOWER",
            "title": "Đà Lạt Ngàn Hoa - Giảm 15% Tour Cao Nguyên",
            "description": "Áp dụng cho toàn bộ các tour du lịch săn mây và check-in Đà Lạt, tối đa 400.000₫.",
            "discount_type": "percent",
            "discount_value": 15,
            "max_discount": 400000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "PHUQUOCVIP",
            "title": "Phú Quốc Đảo Ngọc - Giảm 500.000₫ Tour Nghỉ Dưỡng",
            "description": "Đặc quyền nghỉ dưỡng sang trọng tại Grand World, Hòn Thơm và lặn ngắm san hô đảo ngọc.",
            "discount_type": "fixed",
            "discount_value": 500000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "WEEKEND150K",
            "title": "Khởi Hành Cuối Tuần - Giảm Trực Tiếp 150.000₫",
            "description": "Tận hưởng kỳ nghỉ cuối tuần trọn vẹn cùng bạn bè với mức giá ưu đãi hấp dẫn.",
            "discount_type": "fixed",
            "discount_value": 150000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "FAMILYTOUR",
            "title": "Gắn Kết Gia Đình - Giảm 10% Tour Đoàn Nhóm",
            "description": "Áp dụng cho các đơn đặt tour từ 3 khách người lớn trở lên, giảm tối đa 600.000₫.",
            "discount_type": "percent",
            "discount_value": 10,
            "max_discount": 600000,
            "expiry_date": "2026-12-31",
            "is_active": True
        },
        {
            "code": "COMBO300K",
            "title": "Combo Tiết Kiệm - Giảm 300.000₫ Tour & Khách Sạn",
            "description": "Ưu đãi khi đặt tour trọn gói bao gồm dịch vụ lưu trú và di chuyển thuận tiện.",
            "discount_type": "fixed",
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

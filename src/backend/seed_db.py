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

    users_count = await db.users.count_documents({})
    if users_count == 0:
        print("Seeding users...")
        users = [
            {
                "email": "admin@smarttravel.vn",
                "password_hash": hash_pw("admin123"),
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
            },
            {
                "email": "son.vu@gmail.com",
                "password_hash": hash_pw("123456"),
                "full_name": "Vũ Văn Sơn",
                "phone": "0912345678",
                "birth_date": "1998-05-20",
                "gender": "nam",
                "address": "Mộc Châu, Sơn La",
                "role": "user",
                "preferences": ["núi", "trekking"],
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
                "preferences": ["biển", "ẩm thực"],
                "custom_preferences": [],
                "saved_vouchers": [],
                "settings": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "ai_personalization": True,
                    "language": "vi"
                },
                "avatar_url": "",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        await db.users.insert_many(users)
        print(f"Users seeded: {len(users)} records (admin + 2 users).")
    else:
        print("Users already exist.")

    tours_count = await db.tours.count_documents({})
    if tours_count == 0:
        print("Seeding tours...")
        tours = [
            {
                "title": "Hồ Hoàn Kiếm",
                "slug": "ho-hoan-kiem",
                "category": "sight",
                "location": "Hà Nội",
                "duration_days": 1,
                "duration_nights": 0,
                "price": 0,
                "rating": 4.9,
                "review_count": 5200,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Thap_Rua.jpg/960px-Thap_Rua.jpg"],
                "tags": ["hot"],
                "is_active": True,
                "lat": 21.0285,
                "lng": 105.8542,
                "geo_location": {"type": "Point", "coordinates": [105.8542, 21.0285]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Văn Miếu Quốc Tử Giám",
                "slug": "van-mieu",
                "category": "sight",
                "location": "Hà Nội",
                "duration_days": 1,
                "duration_nights": 0,
                "price": 30000,
                "rating": 4.8,
                "review_count": 4500,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Hanoi_Temple_of_Literature_%28cropped%29.jpg/960px-Hanoi_Temple_of_Literature_%28cropped%29.jpg"],
                "tags": ["cultural"],
                "is_active": True,
                "lat": 21.0294,
                "lng": 105.8355,
                "geo_location": {"type": "Point", "coordinates": [105.8355, 21.0294]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Vịnh Hạ Long 2 ngày 1 đêm",
                "slug": "vinh-ha-long",
                "category": "sea",
                "location": "Quảng Ninh",
                "duration_days": 2,
                "duration_nights": 1,
                "price": 2500000,
                "discount_price": 2200000,
                "rating": 4.9,
                "review_count": 1200,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Ha_Long_Bay_in_2019.jpg/960px-Ha_Long_Bay_in_2019.jpg"],
                "tags": ["hot", "best-seller"],
                "is_active": True,
                "lat": 20.9101,
                "lng": 107.1839,
                "geo_location": {"type": "Point", "coordinates": [107.1839, 20.9101]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Mộc Châu Mộng Mơ - Tour 3N2Đ",
                "slug": "moc-chau-mong-mo",
                "category": "mountain",
                "location": "Sơn La",
                "duration_days": 3,
                "duration_nights": 2,
                "price": 3500000,
                "discount_price": 2800000,
                "rating": 4.8,
                "review_count": 890,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Thacbac3.jpg/960px-Thacbac3.jpg"],
                "tags": ["hot", "best-seller"],
                "is_active": True,
                "lat": 20.8320,
                "lng": 104.6328,
                "geo_location": {"type": "Point", "coordinates": [104.6328, 20.8320]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Du thuyền Vịnh Hạ Long 5 Sao",
                "slug": "du-thuyen-ha-long-5-sao",
                "category": "sea",
                "location": "Quảng Ninh",
                "duration_days": 2,
                "duration_nights": 1,
                "price": 4200000,
                "rating": 4.8,
                "review_count": 750,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Ha_Long_Bay_in_2019.jpg/960px-Ha_Long_Bay_in_2019.jpg"],
                "tags": ["luxury"],
                "is_active": True,
                "lat": 20.9101,
                "lng": 107.1839,
                "geo_location": {"type": "Point", "coordinates": [107.1839, 20.9101]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Combo Cát Bà - Đảo Ngọc 4N3Đ",
                "slug": "combo-cat-ba",
                "category": "sea",
                "location": "Hải Phòng",
                "duration_days": 4,
                "duration_nights": 3,
                "price": 7200000,
                "discount_price": 5500000,
                "rating": 4.7,
                "review_count": 620,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Cat_Ba_town.JPG/960px-Cat_Ba_town.JPG"],
                "tags": ["discount"],
                "is_active": True,
                "lat": 20.7273,
                "lng": 106.9833,
                "geo_location": {"type": "Point", "coordinates": [106.9833, 20.7273]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Trekking Sapa - Chinh phục Fansipan",
                "slug": "trekking-sapa-fansipan",
                "category": "mountain",
                "location": "Lào Cai",
                "duration_days": 3,
                "duration_nights": 2,
                "price": 3200000,
                "rating": 4.9,
                "review_count": 1050,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Thacbac3.jpg/960px-Thacbac3.jpg"],
                "tags": ["hot", "adventure"],
                "is_active": True,
                "lat": 22.3364,
                "lng": 103.8438,
                "geo_location": {"type": "Point", "coordinates": [103.8438, 22.3364]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Tam Đảo All-Inclusive 2N1Đ",
                "slug": "tam-dao-all-inclusive",
                "category": "mountain",
                "location": "Vĩnh Phúc",
                "duration_days": 2,
                "duration_nights": 1,
                "price": 6800000,
                "rating": 4.6,
                "review_count": 440,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Thacbac3.jpg/960px-Thacbac3.jpg"],
                "tags": ["luxury", "resort"],
                "is_active": True,
                "lat": 21.4576,
                "lng": 105.6469,
                "geo_location": {"type": "Point", "coordinates": [105.6469, 21.4576]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Hà Giang Loop - Phượt 4N3Đ",
                "slug": "ha-giang-loop",
                "category": "mountain",
                "location": "Hà Giang",
                "duration_days": 4,
                "duration_nights": 3,
                "price": 3800000,
                "rating": 4.9,
                "review_count": 2100,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Thacbac3.jpg/960px-Thacbac3.jpg"],
                "tags": ["hot", "adventure", "best-seller"],
                "is_active": True,
                "lat": 23.2753,
                "lng": 104.9843,
                "geo_location": {"type": "Point", "coordinates": [104.9843, 23.2753]},
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Ninh Bình - Tràng An 2N1Đ",
                "slug": "ninh-binh-trang-an",
                "category": "sight",
                "location": "Ninh Bình",
                "duration_days": 2,
                "duration_nights": 1,
                "price": 1800000,
                "rating": 4.7,
                "review_count": 980,
                "images": ["https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Thacbac3.jpg/960px-Thacbac3.jpg"],
                "tags": ["cultural", "UNESCO"],
                "is_active": True,
                "lat": 20.2506,
                "lng": 105.9745,
                "geo_location": {"type": "Point", "coordinates": [105.9745, 20.2506]},
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        await db.tours.insert_many(tours)
        print(f"Tours seeded: {len(tours)} records.")
    else:
        print("Tours already exist.")

    vouchers_count = await db.vouchers.count_documents({})
    if vouchers_count == 0:
        print("Seeding vouchers...")
        vouchers = [
            {
                "code": "SUMMER20",
                "title": "Chào Hè Sôi Động - Giảm 20% Tour Biển",
                "description": "Áp dụng cho tất cả các tour du lịch biển tại Hạ Long, Cát Bà, Đồ Sơn. Tối đa giảm 500.000₫.",
                "discount_type": "percent",
                "discount_value": 20,
                "max_discount": 500000,
                "expiry_date": "2026-06-30",
                "is_active": True
            },
            {
                "code": "NEWUSER100K",
                "title": "Giảm 100K cho người mới",
                "description": "Giảm trực tiếp 100.000đ cho chuyến đi đầu tiên.",
                "discount_type": "fixed",
                "discount_value": 100000,
                "expiry_date": "2026-12-31",
                "is_active": True
            },
            {
                "code": "TREK1999",
                "title": "Lên Rừng Vượt Thác - Đồng giá siêu rẻ",
                "description": "Trải nghiệm các tour Trekking Mộc Châu, Sapa, Hà Giang với mức giá đồng giá 1.999.000₫.",
                "discount_type": "fixed",
                "discount_value": 1999000,
                "expiry_date": "2026-07-15",
                "is_active": True
            },
            {
                "code": "SAFEFREE",
                "title": "Tặng Gói Bảo Hiểm Toàn Diện",
                "description": "Nhận ngay gói bảo hiểm du lịch toàn diện trị giá 300.000₫ khi đặt bất kỳ tour nào.",
                "discount_type": "free_insurance",
                "discount_value": 300000,
                "expiry_date": "2026-12-31",
                "is_active": True
            }
        ]
        await db.vouchers.insert_many(vouchers)
        print(f"Vouchers seeded: {len(vouchers)} records.")
    else:
        print("Vouchers already exist.")

    guides_count = await db.guides.count_documents({})
    if guides_count == 0:
        print("Seeding guides...")
        son_user = await db.users.find_one({"email": "son.vu@gmail.com"})
        if son_user:
            guide = {
                "user_id": str(son_user["_id"]),
                "name": "Vũ Văn Sơn",
                "experience_years": 5,
                "price_per_day": 800000,
                "areas": ["Mộc Châu", "Sapa", "Hà Giang"],
                "languages": ["Tiếng Việt", "English"],
                "bio": "Hướng dẫn viên chuyên tour trekking Miền Bắc, 5 năm kinh nghiệm dẫn đoàn.",
                "id_front_url": "",
                "id_back_url": "",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
            await db.guides.insert_one(guide)
            print("Guide seeded: 1 record (pending).")
    else:
        print("Guides already exist.")

    client.close()
    print("Seed completed!")

if __name__ == "__main__":
    asyncio.run(seed_database())

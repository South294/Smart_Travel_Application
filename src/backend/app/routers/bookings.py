from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.mongodb import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.routers.deps import get_current_user
from app.routers.helpers import validate_object_id, serialize_booking
from app.services.ai_knowledge import (
    CITY_HIGHLIGHTS,
    CITY_FOOD_AND_PLAY,
    build_google_maps_route_url,
)
from datetime import datetime
import secrets
from typing import List, Optional

router = APIRouter()

def build_trip_itinerary_and_route(tour: dict, guide_name: str) -> dict:
    title = tour.get("title", "")
    location = tour.get("location", "")
    loc_clean = location.strip().lower()
    title_clean = title.strip().lower()

    KNOWN_CITIES = {
        "phú quốc": ("Phú Quốc", "TP. Hồ Chí Minh"),
        "sa pa": ("Sa Pa", "Hà Nội"),
        "sapa": ("Sa Pa", "Hà Nội"),
        "hà giang": ("Hà Giang", "Hà Nội"),
        "hạ long": ("Hạ Long", "Hà Nội"),
        "nha trang": ("Nha Trang", "TP. Hồ Chí Minh"),
        "đà lạt": ("Đà Lạt", "TP. Hồ Chí Minh"),
        "mộc châu": ("Mộc Châu", "Hà Nội"),
        "tam đảo": ("Tam Đảo", "Hà Nội"),
        "ninh bình": ("Ninh Bình", "Hà Nội"),
        "hà nội": ("Hà Nội", "Nhà hát Lớn Hà Nội"),
        "hồ chí minh": ("TP. Hồ Chí Minh", "Chợ Bến Thành"),
        "đà nẵng": ("Đà Nẵng", "Sân bay Đà Nẵng"),
        "hội an": ("Hội An", "Đà Nẵng"),
        "huế": ("Huế", "Đà Nẵng"),
        "vũng tàu": ("Vũng Tàu", "TP. Hồ Chí Minh"),
        "cần thơ": ("Cần Thơ", "TP. Hồ Chí Minh"),
        "quy nhơn": ("Quy Nhơn", "TP. Hồ Chí Minh"),
        "phú yên": ("Phú Yên", "TP. Hồ Chí Minh"),
        "mũi né": ("Mũi Né", "TP. Hồ Chí Minh"),
        "phan thiết": ("Phan Thiết", "TP. Hồ Chí Minh"),
        "mai châu": ("Mai Châu", "Hà Nội"),
        "cao bằng": ("Cao Bằng", "Hà Nội"),
        "phú thọ": ("Phú Thọ", "Hà Nội"),
        "quảng bình": ("Quảng Bình", "Hà Nội")
    }

    matched_city = None
    for k, v in KNOWN_CITIES.items():
        if k in loc_clean or k in title_clean:
            matched_city = v
            break

    if matched_city:
        destination = matched_city[0]
        origin = matched_city[1]
        trip_type = "single_destination" if destination == "Hà Nội" or destination == "TP. Hồ Chí Minh" else "inter_provincial"
    else:
        destination = location if location else "Điểm đến trải nghiệm"
        origin = "Điểm hẹn trung tâm"
        trip_type = "single_destination"

    transportation = "Xe du lịch đời mới 16-29 chỗ trang bị máy lạnh, wifi, nước suối và khăn lạnh suốt hành trình"
    if any(k in loc_clean or k in title_clean for k in ["biển", "đảo", "vịnh", "phú quốc", "nha trang", "hạ long", "côn đảo"]):
        transportation = "Xe ô tô du lịch điều hòa cao cấp đón trả + Cano cao tốc / Thuyền du lịch chuyên dụng đạt chuẩn an toàn"
    elif any(k in loc_clean or k in title_clean for k in ["hà giang", "trekking", "phượt", "đèo", "fansipan", "núi"]):
        transportation = "Xe Limousine chất lượng cao đưa đón hai chiều + Xe máy đời mới kèm mũ bảo hiểm chuyên dụng cho cung đường đèo"

    dest_key = destination.strip().lower()
    city_info = None
    for k, v in CITY_HIGHLIGHTS.items():
        if k in dest_key or dest_key in k:
            city_info = v
            break

    food_info = None
    for k, v in CITY_FOOD_AND_PLAY.items():
        if k in dest_key or dest_key in k:
            food_info = v
            break

    spots = city_info.get("spots", []) if city_info else []
    spot1 = spots[0] if len(spots) > 0 else f"Thắng cảnh nổi tiếng {destination}"
    spot2 = spots[1] if len(spots) > 1 else f"Khu du lịch sinh thái {destination}"
    spot3 = spots[2] if len(spots) > 2 else f"Điểm ngắm hoàng hôn và check-in {destination}"

    delicacies = food_info.get("delicacies", []) if food_info else []
    delicacies_text = ", ".join(delicacies[:3]) if delicacies else f"Ẩm thực đặc sản {destination}"

    restaurants = food_info.get("famous_restaurants", []) if food_info else []
    res1 = restaurants[0] if len(restaurants) > 0 else f"Nhà hàng ẩm thực truyền thống {destination}"
    res2 = restaurants[1] if len(restaurants) > 1 else f"Nhà hàng đặc sản địa phương {destination}"

    entertainment = food_info.get("entertainment_spots", []) if food_info else []
    ent1 = entertainment[0] if len(entertainment) > 0 else f"Trải nghiệm cảnh sắc và văn hóa {destination}"

    itinerary_details = []
    if trip_type == "inter_provincial":
        timeline_items = [
            {
                "time": "07:30 - 08:30",
                "activity": f"Tập trung và khởi hành từ {origin}. Xe du lịch cao cấp đón quý khách tại điểm hẹn. Hướng dẫn viên {guide_name} đón đoàn, phổ biến lịch trình và phát nước uống đóng chai.",
                "type": "departure",
                "location": origin
            },
            {
                "time": "09:30 - 10:30",
                "activity": f"Di chuyển đến {destination}. Dừng chân tại trạm nghỉ ngơi giải lao, thưởng thức bữa sáng nhẹ và chiêm ngưỡng cảnh quan trên cung đường kết nối.",
                "type": "transit",
                "location": f"Tuyến đường đến {destination}"
            },
            {
                "time": "10:30 - 12:00",
                "activity": f"Đến {destination}. Hướng dẫn viên {guide_name} đưa đoàn tham quan danh thắng biểu tượng: {spot1}. Check-in chụp ảnh và tìm hiểu nét đẹp văn hóa.",
                "type": "sightseeing",
                "location": spot1
            },
            {
                "time": "12:00 - 13:30",
                "activity": f"Dùng bữa trưa đậm đà phong vị bản địa tại {res1}. Thưởng thức thực đơn đặc sản: {delicacies_text}. Quý khách nghỉ ngơi tại chỗ.",
                "type": "dining",
                "location": res1
            },
            {
                "time": "14:00 - 17:00",
                "activity": f"Tiếp tục hành trình tham quan {spot2}. Trải nghiệm hoạt động: {ent1} cùng sự hướng dẫn và thuyết minh văn hóa của HDV {guide_name}.",
                "type": "sightseeing",
                "location": spot2
            },
            {
                "time": "17:30 - 19:00",
                "activity": f"Ghé thăm {spot3}, tận hưởng không khí trong lành, ngắm hoàng hôn và mua sắm đặc sản chính gốc làm quà cho người thân.",
                "type": "sightseeing",
                "location": spot3
            },
            {
                "time": "19:00 - 20:30",
                "activity": f"Thưởng thức bữa tối ngon miệng tại {res2} với các món ẩm thực địa phương đặc sắc trong không gian thư giãn.",
                "type": "dining",
                "location": res2
            },
            {
                "time": "20:30 - 22:00",
                "activity": f"Xe du lịch và HDV {guide_name} đưa quý khách trở về khách sạn nghỉ ngơi hoặc trả về điểm đón ban đầu. Kết thúc lịch trình an toàn và trọn vẹn.",
                "type": "return",
                "location": origin
            }
        ]
        itinerary_details.append({
            "day": 1,
            "title": f"Hành trình trọn gói khám phá {destination}",
            "timeline": timeline_items
        })
        route_map_url = build_google_maps_route_url(origin=origin, destination=destination, waypoints=[spot1, res1, spot2])
    else:
        timeline_items = [
            {
                "time": "08:00 - 08:30",
                "activity": f"Hướng dẫn viên {guide_name} và xe du lịch đón quý khách tại điểm hẹn trung tâm {destination}. Phổ biến lịch trình và bắt đầu hành trình.",
                "type": "departure",
                "location": destination
            },
            {
                "time": "09:00 - 11:30",
                "activity": f"Khám phá danh thắng nổi tiếng: {spot1}. Thưởng ngoạn cảnh sắc tuyệt đẹp, chụp ảnh check-in và nghe thuyết minh văn hóa.",
                "type": "sightseeing",
                "location": spot1
            },
            {
                "time": "11:30 - 13:00",
                "activity": f"Dùng bữa trưa tại {res1}. Thưởng thức thực đơn đặc sản địa phương: {delicacies_text}. Nghỉ ngơi giải lao giữa ngày.",
                "type": "dining",
                "location": res1
            },
            {
                "time": "13:30 - 16:30",
                "activity": f"Di chuyển đến {spot2}. Trải nghiệm hoạt động: {ent1}. Khám phá không gian sinh thái và đời sống văn hóa đặc sắc.",
                "type": "sightseeing",
                "location": spot2
            },
            {
                "time": "17:00 - 18:30",
                "activity": f"Ghé thăm {spot3}, thưởng ngoạn hoàng hôn tuyệt đẹp và tự do mua sắm đặc sản chính gốc làm quà.",
                "type": "sightseeing",
                "location": spot3
            },
            {
                "time": "18:30 - 20:00",
                "activity": f"Thưởng thức bữa tối ẩm thực đặc sắc tại {res2} với không gian ấm cúng, thư thái.",
                "type": "dining",
                "location": res2
            },
            {
                "time": "20:00 - 20:30",
                "activity": f"Xe và HDV {guide_name} đưa quý khách về lại điểm đón / khách sạn. Kết thúc hành trình trọn vẹn trong ngày.",
                "type": "return",
                "location": destination
            }
        ]
        itinerary_details.append({
            "day": 1,
            "title": f"Khám phá toàn diện danh thắng & ẩm thực tại {destination}",
            "timeline": timeline_items
        })
        route_map_url = build_google_maps_route_url(origin=spot1, destination=res2, waypoints=[res1, spot2, spot3])

    return {
        "trip_type": trip_type,
        "transportation": transportation,
        "itinerary_details": itinerary_details,
        "route_map_url": route_map_url
    }

@router.post("", response_model=BookingResponse)
async def create_booking(booking: BookingCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    tour_oid = validate_object_id(booking.tour_id)
    tour = await db.tours.find_one({"_id": tour_oid, "is_active": True})
    if not tour:
        raise HTTPException(status_code=404, detail="Tour không tồn tại hoặc đã ngừng bán")

    try:
        travel_date = datetime.strptime(booking.travel_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ngày khởi hành không hợp lệ") from exc
    if travel_date < datetime.utcnow().date():
        raise HTTPException(status_code=400, detail="Ngày khởi hành phải từ hôm nay trở đi")
    if booking.payment_method not in {"credit_card", "e_wallet", "bank_transfer", "qr"}:
        raise HTTPException(status_code=400, detail="Phương thức thanh toán không hợp lệ")

    price_per_person = tour.get("discount_price") or tour.get("price", 0)
    total_amount = (price_per_person * booking.adults) + ((price_per_person * 0.5) * booking.children)

    if booking.insurance:
        insurance_per_person = 150000
        total_amount += insurance_per_person * (booking.adults + booking.children)

    if booking.coupon_code:
        voucher = await db.vouchers.find_one({
            "code": booking.coupon_code,
            "is_active": True,
            "$or": [
                {"expiry_date": {"$exists": False}},
                {"expiry_date": None},
                {"expiry_date": {"$gte": datetime.utcnow().date().isoformat()}}
            ]
        })
        if voucher:
            if voucher["discount_type"] == "percent":
                discount = total_amount * (voucher["discount_value"] / 100)
                max_disc = voucher.get("max_discount")
                if max_disc and discount > max_disc:
                    discount = max_disc
                total_amount -= discount
            elif voucher["discount_type"] == "fixed":
                total_amount -= voucher["discount_value"]
            elif voucher["discount_type"] == "free_insurance":
                total_amount -= min(voucher["discount_value"], insurance_per_person * (booking.adults + booking.children) if booking.insurance else 0)

    if total_amount < 0:
        total_amount = 0

    guide = None
    if booking.guide_id:
        try:
            guide_oid = validate_object_id(booking.guide_id)
            guide = await db.guides.find_one({"_id": guide_oid, "status": "approved"})
        except Exception:
            guide = None
    if not guide and tour.get("guide_id"):
        try:
            guide = await db.guides.find_one({"_id": tour["guide_id"], "status": "approved"})
        except Exception:
            guide = None
    if not guide:
        guide = await db.guides.find_one({"status": "approved"})

    guide_name = guide.get("name") if guide else "Vũ Văn Sơn (HDV SmartTravel)"
    guide_phone = guide.get("phone", "0912 345 678") if guide else "0912 345 678"
    guide_exp = f"{guide.get('experience_years', 5)} năm kinh nghiệm" if guide else "5 năm kinh nghiệm"

    itinerary_data = build_trip_itinerary_and_route(tour, guide_name)

    booking_dict = booking.model_dump()
    booking_dict["user_id"] = current_user["id"]
    is_free = float(price_per_person or 0) == 0
    if is_free:
        total_amount = 0
    booking_dict["status"] = "confirmed" if is_free else "pending"
    booking_dict["payment_status"] = "paid" if is_free else "unpaid"
    booking_dict["total_amount"] = total_amount
    booking_dict["created_at"] = datetime.utcnow().isoformat()
    booking_dict["booking_code"] = f"ST-{secrets.token_hex(4).upper()}"
    booking_dict["is_free"] = is_free
    booking_dict["paid_at"] = booking_dict["created_at"] if is_free else None
    booking_dict["payment_provider"] = "free" if is_free else None
    booking_dict["guide_id"] = str(guide["_id"]) if guide else None
    booking_dict["guide_name"] = guide_name
    booking_dict["guide_phone"] = guide_phone
    booking_dict["guide_experience"] = guide_exp
    booking_dict["trip_type"] = itinerary_data["trip_type"]
    booking_dict["transportation"] = itinerary_data["transportation"]
    booking_dict["itinerary_details"] = itinerary_data["itinerary_details"]
    booking_dict["route_map_url"] = itinerary_data["route_map_url"]

    result = await db.bookings.insert_one(booking_dict)
    booking_dict["id"] = str(result.inserted_id)
    return booking_dict

@router.get("/me", response_model=List[BookingResponse])
async def get_my_bookings(
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    offset = (page - 1) * page_size if (page is not None and page_size is not None) else skip
    max_items = page_size if page_size is not None else limit

    cursor = db.bookings.find({"user_id": current_user["id"]}).skip(offset)
    if max_items is not None:
        cursor = cursor.limit(max_items)

    bookings = []
    async for doc in cursor:
        booking = serialize_booking(doc)
        tour_title = None
        tour = None
        if booking.get("tour_id"):
            try:
                tour = await db.tours.find_one({"_id": validate_object_id(booking["tour_id"])})
            except Exception:
                tour = None
            if tour:
                tour_title = tour.get("title")
                booking["tour_location"] = tour.get("location")
                booking["tour_lat"] = tour.get("lat")
                booking["tour_lng"] = tour.get("lng")
        if tour_title:
            booking["tour_title"] = tour_title
        if tour and (not booking.get("itinerary_details") or not booking.get("guide_name")):
            guide_name = booking.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
            itinerary_data = build_trip_itinerary_and_route(tour, guide_name)
            booking.setdefault("guide_name", guide_name)
            booking.setdefault("guide_phone", "0912 345 678")
            booking.setdefault("guide_experience", "5 năm kinh nghiệm")
            booking.setdefault("trip_type", itinerary_data["trip_type"])
            booking.setdefault("transportation", itinerary_data["transportation"])
            booking.setdefault("itinerary_details", itinerary_data["itinerary_details"])
            booking.setdefault("route_map_url", itinerary_data["route_map_url"])
        bookings.append(booking)
    return bookings

@router.get("/{id}", response_model=BookingResponse)
async def get_booking(id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    oid = validate_object_id(id)
    booking = await db.bookings.find_one({"_id": oid})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt")
    if booking["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập")
    booking_res = serialize_booking(booking)
    if booking_res.get("tour_id") and (not booking_res.get("itinerary_details") or not booking_res.get("guide_name")):
        try:
            tour = await db.tours.find_one({"_id": validate_object_id(booking_res["tour_id"])})
        except Exception:
            tour = None
        if tour:
            guide_name = booking_res.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
            itinerary_data = build_trip_itinerary_and_route(tour, guide_name)
            booking_res.setdefault("tour_title", tour.get("title"))
            booking_res.setdefault("tour_location", tour.get("location"))
            booking_res.setdefault("guide_name", guide_name)
            booking_res.setdefault("guide_phone", "0912 345 678")
            booking_res.setdefault("guide_experience", "5 năm kinh nghiệm")
            booking_res.setdefault("trip_type", itinerary_data["trip_type"])
            booking_res.setdefault("transportation", itinerary_data["transportation"])
            booking_res.setdefault("itinerary_details", itinerary_data["itinerary_details"])
            booking_res.setdefault("route_map_url", itinerary_data["route_map_url"])
    return booking_res

@router.patch("/{id}/cancel")
async def cancel_booking(id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    oid = validate_object_id(id)
    booking = await db.bookings.find_one({"_id": oid})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt")
    if booking["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập")

    if booking.get("status") in {"cancelled", "completed"}:
        raise HTTPException(status_code=400, detail="Đơn đặt không thể hủy ở trạng thái hiện tại")
    await db.bookings.update_one({"_id": oid}, {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow().isoformat()}})
    return {"message": "Hủy đơn đặt thành công"}

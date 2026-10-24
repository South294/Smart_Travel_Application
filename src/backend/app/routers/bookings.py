from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.mongodb import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.routers.deps import get_current_user
from app.routers.helpers import validate_object_id, serialize_booking
from app.services.itinerary_service import (
    build_tour_itinerary,
    generate_tour_itinerary_sync,
)
from app.services.email_service import (
    generate_contract_code,
    send_contract_email,
    build_contract_html,
)
import asyncio
from datetime import datetime
import secrets
from typing import List, Optional

router = APIRouter()

def build_trip_itinerary_and_route(tour: dict, guide_name: str) -> dict:
    title = tour.get("title", "")
    location = tour.get("location", "")
    duration_days = tour.get("duration_days") or 1
    return generate_tour_itinerary_sync(title, location, duration_days=duration_days, guide_name=guide_name)

def generate_tour_itinerary(title: str, location: str, guide_name: str = "Vũ Văn Sơn (HDV SmartTravel)") -> dict:
    return generate_tour_itinerary_sync(title, location, duration_days=1, guide_name=guide_name)

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

    duration_days = tour.get("duration_days") or 1
    itinerary_data = await build_tour_itinerary(
        tour_title=tour.get("title", ""),
        locations=[tour.get("location", "")],
        duration_days=duration_days,
        guide_name=guide_name,
        is_combo=False
    )

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
    booking_dict["contact_name"] = booking.contact_name or current_user.get("full_name") or "Quý khách hàng"
    booking_dict["contact_email"] = booking.contact_email or current_user.get("email")
    booking_dict["contract_code"] = generate_contract_code(booking_dict["booking_code"])
    booking_dict["contract_sent"] = False

    result = await db.bookings.insert_one(booking_dict)
    booking_dict["id"] = str(result.inserted_id)
    try:
        asyncio.create_task(send_contract_email(booking_dict, user_dict=current_user))
    except Exception:
        pass
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
        if booking.get("is_combo") and (not booking.get("itinerary_details") or not booking.get("guide_name")):
            combo_items = booking.get("combo_items", [])
            locations = [item.get("location", "") for item in combo_items if item.get("location")]
            titles = [item.get("title", "") for item in combo_items if item.get("title")]
            combo_title = " - ".join(titles) if titles else "Combo du lịch"
            guide_name = booking.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
            itinerary_data = generate_tour_itinerary_sync(combo_title, " - ".join(locations), duration_days=max(1, len(combo_items)), guide_name=guide_name)
            booking.setdefault("tour_title", f"Combo Du Lịch ({len(combo_items)} Điểm Đến)")
            booking.setdefault("tour_location", " - ".join(locations))
            booking.setdefault("guide_name", guide_name)
            booking.setdefault("guide_phone", "0912 345 678")
            booking.setdefault("guide_experience", "5 năm kinh nghiệm dẫn đoàn")
            booking.setdefault("trip_type", "inter_provincial")
            booking.setdefault("transportation", itinerary_data["transportation"])
            booking.setdefault("itinerary_details", itinerary_data["itinerary_details"])
            booking.setdefault("route_map_url", itinerary_data["route_map_url"])
        elif tour and (not booking.get("itinerary_details") or not booking.get("guide_name")):
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
    if booking_res.get("is_combo") and (not booking_res.get("itinerary_details") or not booking_res.get("guide_name")):
        combo_items = booking_res.get("combo_items", [])
        locations = [item.get("location", "") for item in combo_items if item.get("location")]
        titles = [item.get("title", "") for item in combo_items if item.get("title")]
        combo_title = " - ".join(titles) if titles else "Combo du lịch"
        guide_name = booking_res.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
        itinerary_data = generate_tour_itinerary_sync(combo_title, " - ".join(locations), duration_days=max(1, len(combo_items)), guide_name=guide_name)
        booking_res.setdefault("tour_title", f"Combo Du Lịch ({len(combo_items)} Điểm Đến)")
        booking_res.setdefault("tour_location", " - ".join(locations))
        booking_res.setdefault("guide_name", guide_name)
        booking_res.setdefault("guide_phone", "0912 345 678")
        booking_res.setdefault("guide_experience", "5 năm kinh nghiệm dẫn đoàn")
        booking_res.setdefault("trip_type", "inter_provincial")
        booking_res.setdefault("transportation", itinerary_data["transportation"])
        booking_res.setdefault("itinerary_details", itinerary_data["itinerary_details"])
        booking_res.setdefault("route_map_url", itinerary_data["route_map_url"])
    elif booking_res.get("tour_id") and (not booking_res.get("itinerary_details") or not booking_res.get("guide_name")):
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

@router.get("/{id}/contract")
async def get_booking_contract(id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    oid = validate_object_id(id)
    booking = await db.bookings.find_one({"_id": oid})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt")
    if booking["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập")

    if booking.get("tour_id") and (not booking.get("itinerary_details") or not booking.get("tour_title")):
        try:
            tour = await db.tours.find_one({"_id": validate_object_id(booking["tour_id"])})
            if tour:
                booking.setdefault("tour_title", tour.get("title"))
                booking.setdefault("tour_location", tour.get("location"))
                if not booking.get("itinerary_details"):
                    guide_name = booking.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
                    itin = build_trip_itinerary_and_route(tour, guide_name)
                    booking.setdefault("itinerary_details", itin["itinerary_details"])
                    booking.setdefault("guide_name", guide_name)
                    booking.setdefault("transportation", itin["transportation"])
        except Exception:
            pass

    contract_html = build_contract_html(booking, current_user)
    contract_code = booking.get("contract_code") or generate_contract_code(booking.get("booking_code"))
    return {
        "booking_id": id,
        "booking_code": booking.get("booking_code"),
        "contract_code": contract_code,
        "contact_email": booking.get("contact_email") or current_user.get("email"),
        "contract_html": contract_html,
        "html": contract_html
    }

@router.post("/{id}/send-contract-email")
async def resend_contract_email(id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    oid = validate_object_id(id)
    booking = await db.bookings.find_one({"_id": oid})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt")
    if booking["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập")

    if booking.get("tour_id") and (not booking.get("itinerary_details") or not booking.get("tour_title")):
        try:
            tour = await db.tours.find_one({"_id": validate_object_id(booking["tour_id"])})
            if tour:
                booking.setdefault("tour_title", tour.get("title"))
                booking.setdefault("tour_location", tour.get("location"))
                if not booking.get("itinerary_details"):
                    guide_name = booking.get("guide_name") or "Vũ Văn Sơn (HDV SmartTravel)"
                    itin = build_trip_itinerary_and_route(tour, guide_name)
                    booking.setdefault("itinerary_details", itin["itinerary_details"])
                    booking.setdefault("guide_name", guide_name)
                    booking.setdefault("transportation", itin["transportation"])
        except Exception:
            pass

    target_email = booking.get("contact_email") or current_user.get("email")
    success = await send_contract_email(booking, recipient_email=target_email, user_dict=current_user)
    return {
        "message": f"Đã gửi hợp đồng du lịch và lịch trình chi tiết tới {target_email}",
        "success": success,
        "email": target_email
    }

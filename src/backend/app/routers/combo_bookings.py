from datetime import datetime
import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.db.mongodb import get_db
from app.routers.deps import get_current_user
from app.routers.helpers import validate_object_id
from app.services.itinerary_service import build_tour_itinerary
from app.schemas.combo import ComboBookingCreate, ComboBookingResponse

router = APIRouter()
VALID_PAYMENT_METHODS = {"credit_card", "e_wallet", "bank_transfer", "qr"}


@router.post("", response_model=ComboBookingResponse)
async def create_combo_booking(payload: ComboBookingCreate, current_user: dict = Depends(get_current_user)):
    if payload.payment_method not in VALID_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="Phương thức thanh toán không hợp lệ")
    db = get_db()
    item_ids = [validate_object_id(item.tour_id) for item in payload.items]
    tours = await db.tours.find({"_id": {"$in": item_ids}, "is_active": True}).to_list(len(item_ids))
    tours_by_id = {str(tour["_id"]): tour for tour in tours}
    if len(tours_by_id) != len(set(item.tour_id for item in payload.items)):
        raise HTTPException(status_code=404, detail="Một hoặc nhiều tour trong combo không còn được bán")

    combo_items = []
    total_amount = 0.0
    for item in payload.items:
        try:
            travel_date = datetime.strptime(item.travel_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Ngày khởi hành trong combo không hợp lệ") from exc
        if travel_date < datetime.utcnow().date():
            raise HTTPException(status_code=400, detail="Ngày khởi hành phải từ hôm nay trở đi")
        tour = tours_by_id[item.tour_id]
        unit_price = float(tour.get("discount_price") or tour.get("price") or 0)
        total_amount += unit_price * payload.adults + unit_price * 0.5 * payload.children
        combo_items.append({
            "tour_id": item.tour_id,
            "title": tour.get("title", "Tour"),
            "location": tour.get("location", ""),
            "travel_date": item.travel_date,
            "unit_price": unit_price,
        })

    if payload.insurance:
        total_amount += 150000 * (payload.adults + payload.children)
    if payload.coupon_code:
        voucher = await db.vouchers.find_one({
            "code": payload.coupon_code,
            "is_active": True,
            "$or": [{"expiry_date": {"$exists": False}}, {"expiry_date": None}, {"expiry_date": {"$gte": datetime.utcnow().date().isoformat()}}],
        })
        if voucher:
            if voucher.get("discount_type") == "percent":
                discount = total_amount * float(voucher.get("discount_value", 0)) / 100
                total_amount -= min(discount, float(voucher.get("max_discount") or discount))
            elif voucher.get("discount_type") == "fixed":
                total_amount -= float(voucher.get("discount_value", 0))

    total_amount = max(0, total_amount)
    now = datetime.utcnow().isoformat()

    locations = [item["location"] for item in combo_items if item.get("location")]
    titles = [item["title"] for item in combo_items if item.get("title")]
    combo_title = " - ".join(titles) if titles else "Combo du lịch"
    duration_days = max(1, len(combo_items))
    itinerary_data = await build_tour_itinerary(
        tour_title=combo_title,
        locations=locations,
        duration_days=duration_days,
        guide_name="Vũ Văn Sơn (HDV SmartTravel)",
        is_combo=True
    )
    sorted_destinations = itinerary_data.get("sorted_destinations", locations)

    booking = {
        "user_id": current_user["id"],
        "tour_id": combo_items[0]["tour_id"],
        "tour_ids": [item["tour_id"] for item in combo_items],
        "combo_items": combo_items,
        "travel_date": combo_items[0]["travel_date"],
        "adults": payload.adults,
        "children": payload.children,
        "insurance": payload.insurance,
        "coupon_code": payload.coupon_code,
        "payment_method": payload.payment_method,
        "contact_phone": payload.contact_phone,
        "note": payload.note,
        "total_amount": total_amount,
        "status": "confirmed" if total_amount == 0 else "pending",
        "payment_status": "paid" if total_amount == 0 else "unpaid",
        "payment_provider": "free" if total_amount == 0 else None,
        "paid_at": now if total_amount == 0 else None,
        "created_at": now,
        "booking_code": f"ST-C{secrets.token_hex(4).upper()}",
        "is_combo": True,
        "is_free": total_amount == 0,
        "tour_title": f"Combo Du Lịch ({len(combo_items)} Điểm Đến)",
        "tour_location": " - ".join(sorted_destinations if isinstance(sorted_destinations, list) else locations),
        "guide_name": "Vũ Văn Sơn (HDV SmartTravel)",
        "guide_phone": "0912 345 678",
        "guide_experience": "5 năm kinh nghiệm dẫn đoàn",
        "transportation": itinerary_data["transportation"],
        "trip_type": "inter_provincial",
        "itinerary_details": itinerary_data["itinerary_details"],
        "route_map_url": itinerary_data["route_map_url"],
    }
    result = await db.bookings.insert_one(booking)
    return {"id": str(result.inserted_id), **{key: booking[key] for key in ["booking_code", "tour_ids", "combo_items", "adults", "children", "total_amount", "payment_status", "status", "payment_method", "created_at"]}, "items": combo_items}

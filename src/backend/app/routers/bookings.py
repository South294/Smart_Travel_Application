from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.routers.deps import get_current_user
from app.routers.helpers import validate_object_id, serialize_booking
from datetime import datetime
from typing import List

router = APIRouter()

@router.post("", response_model=BookingResponse)
async def create_booking(booking: BookingCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    tour_oid = validate_object_id(booking.tour_id)
    tour = await db.tours.find_one({"_id": tour_oid})
    if not tour:
        raise HTTPException(status_code=404, detail="Không tìm thấy tour")

    price_per_person = tour.get("discount_price") or tour.get("price", 0)
    total_amount = (price_per_person * booking.adults) + ((price_per_person * 0.5) * booking.children)

    if booking.insurance:
        insurance_per_person = 150000
        total_amount += insurance_per_person * (booking.adults + booking.children)

    if booking.coupon_code:
        voucher = await db.vouchers.find_one({"code": booking.coupon_code, "is_active": True})
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

    booking_dict = booking.model_dump()
    booking_dict["user_id"] = current_user["id"]
    booking_dict["status"] = "pending"
    booking_dict["total_amount"] = total_amount
    booking_dict["created_at"] = datetime.utcnow().isoformat()

    result = await db.bookings.insert_one(booking_dict)
    booking_dict["id"] = str(result.inserted_id)
    return booking_dict

@router.get("/me", response_model=List[BookingResponse])
async def get_my_bookings(current_user: dict = Depends(get_current_user)):
    db = get_db()
    cursor = db.bookings.find({"user_id": current_user["id"]})
    bookings = []
    async for doc in cursor:
        booking = serialize_booking(doc)
        tour_title = None
        if booking.get("tour_id"):
            tour = await db.tours.find_one({"_id": validate_object_id(booking["tour_id"])})
            if tour:
                tour_title = tour.get("title")
        if tour_title:
            booking["tour_title"] = tour_title
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
    return serialize_booking(booking)

@router.patch("/{id}/cancel")
async def cancel_booking(id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    oid = validate_object_id(id)
    booking = await db.bookings.find_one({"_id": oid})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt")
    if booking["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập")

    await db.bookings.update_one({"_id": oid}, {"$set": {"status": "cancelled"}})
    return {"message": "Hủy đơn đặt thành công"}

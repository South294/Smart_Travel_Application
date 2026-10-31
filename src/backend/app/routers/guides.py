from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.schemas.guide import GuideCreate, GuideResponse, GuideUpdate, GuideRequestCreate, TripStatusUpdate
from app.routers.deps import get_current_user, get_current_admin_user
from app.routers.helpers import validate_object_id, serialize_guide
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.get("", response_model=List[GuideResponse])
async def get_guides():
    db = get_db()
    cursor = db.guides.find({"status": "approved"})
    guides = []
    async for doc in cursor:
        guides.append(serialize_guide(doc))
    return guides

@router.get("/all", response_model=List[GuideResponse])
async def get_all_guides(admin: dict = Depends(get_current_admin_user)):
    """Admin: List all guides including pending and rejected"""
    db = get_db()
    cursor = db.guides.find()
    guides = []
    async for doc in cursor:
        guides.append(serialize_guide(doc))
    return guides

@router.post("/apply", response_model=GuideResponse)
async def apply_guide(guide: GuideCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    if guide.cccd_number:
        if not guide.cccd_number.isdigit() or len(guide.cccd_number) != 12:
            raise HTTPException(status_code=400, detail="Số CCCD phải gồm đúng 12 chữ số")

    cccd_status = "verified" if (guide.cccd_number and guide.id_front_url and guide.id_back_url and guide.portrait_url) else "unverified"

    existing = await db.guides.find_one({"user_id": current_user["id"]})
    if existing:
        if existing.get("status") != "rejected":
            raise HTTPException(status_code=400, detail="Bạn đã gửi hồ sơ rồi")

        guide_dict = guide.model_dump()
        guide_dict.update({
            "status": "pending",
            "cccd_status": cccd_status,
            "created_at": datetime.utcnow().isoformat()
        })
        await db.guides.update_one({"_id": existing["_id"]}, {"$set": guide_dict})
        updated = await db.guides.find_one({"_id": existing["_id"]})
        return serialize_guide(updated)

    guide_dict = guide.model_dump()
    guide_dict["user_id"] = current_user["id"]
    guide_dict["status"] = "pending"
    guide_dict["cccd_status"] = cccd_status
    guide_dict["created_at"] = datetime.utcnow().isoformat()

    result = await db.guides.insert_one(guide_dict)
    guide_dict["id"] = str(result.inserted_id)
    return guide_dict

@router.get("/me")
async def get_my_guide_profile(current_user: dict = Depends(get_current_user)):
    db = get_db()
    guide = await db.guides.find_one({"user_id": current_user["id"]})
    if not guide:
        raise HTTPException(status_code=404, detail="Bạn chưa đăng ký hướng dẫn viên")
    return serialize_guide(guide)

@router.get("/me/dashboard")
async def get_guide_dashboard(current_user: dict = Depends(get_current_user)):
    db = get_db()
    guide = await db.guides.find_one({"user_id": current_user["id"], "status": "approved"})
    if not guide:
        raise HTTPException(status_code=403, detail="Tài khoản chưa được duyệt hướng dẫn viên")

    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    cursor = db.guide_assignments.find({"guide_id": guide["_id"]}).sort("trip_date", -1)

    trips = []
    active_trips = []
    total_trips_month = 0
    total_earnings_month = 0
    async for doc in cursor:
        trip_date = doc.get("trip_date")
        status = doc.get("status", "assigned")
        if status == "completed" and isinstance(trip_date, str) and trip_date.startswith(current_month):
            total_trips_month += 1
            total_earnings_month += float(doc.get("earning", 0))
        trip = {
            "id": str(doc.get("_id")),
            "tour_id": str(doc.get("tour_id", "")),
            "tour_title": doc.get("tour_title", "Tour"),
            "destination": doc.get("destination", ""),
            "trip_date": trip_date,
            "earning": doc.get("earning", 0),
            "status": status
        }
        if status in ("assigned", "in_progress", "departed"):
            active_trips.append(trip)
        elif status == "completed":
            trips.append(trip)

    return {
        "guide": serialize_guide(guide),
        "stats": {
            "trips_month": total_trips_month,
            "earnings_month": total_earnings_month,
            "active_trips": len(active_trips)
        },
        "active_trips": active_trips,
        "history": trips
    }

@router.get("/me/requests")
async def get_guide_requests(current_user: dict = Depends(get_current_user)):
    db = get_db()
    guide = await db.guides.find_one({"user_id": current_user["id"], "status": "approved"})
    if not guide:
        raise HTTPException(status_code=403, detail="Tài khoản chưa được duyệt hướng dẫn viên")

    cursor = db.guide_requests.find({"guide_id": guide["_id"], "status": "pending"})
    requests = []
    async for doc in cursor:
        requests.append({
            "id": str(doc.get("_id")),
            "customer_name": doc.get("customer_name", "Khách hàng"),
            "customer_phone": doc.get("customer_phone", ""),
            "destination": doc.get("destination", ""),
            "trip_date": doc.get("trip_date"),
            "note": doc.get("note", "")
        })
    return requests

@router.post("/requests")
async def create_guide_request(payload: GuideRequestCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    guide_oid = validate_object_id(payload.guide_id)
    guide = await db.guides.find_one({"_id": guide_oid, "status": "approved"})
    if not guide:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")

    request_doc = {
        "guide_id": guide_oid,
        "customer_id": current_user.get("id"),
        "customer_name": current_user.get("full_name") or current_user.get("email") or "Khách hàng",
        "customer_phone": payload.customer_phone or current_user.get("phone", ""),
        "destination": payload.destination,
        "trip_date": payload.trip_date,
        "note": payload.note or "",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    result = await db.guide_requests.insert_one(request_doc)
    return {"message": "Đã gửi yêu cầu hướng dẫn viên", "id": str(result.inserted_id)}

@router.get("/{id}", response_model=GuideResponse)
async def get_guide(id: str):
    db = get_db()
    oid = validate_object_id(id)
    guide = await db.guides.find_one({"_id": oid})
    if not guide or guide.get("status") != "approved":
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")
    return serialize_guide(guide)

@router.patch("/{id}/approve")
async def approve_guide(id: str, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(id)
    result = await db.guides.update_one({"_id": oid}, {"$set": {"status": "approved"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")
    guide = await db.guides.find_one({"_id": oid})
    if guide and guide.get("user_id"):
        user_oid = validate_object_id(str(guide.get("user_id")))
        await db.users.update_one({"_id": user_oid}, {"$set": {"role": "guide"}})
    return {"message": "Đã duyệt hồ sơ hướng dẫn viên"}

@router.patch("/{id}/reject")
async def reject_guide(id: str, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(id)
    result = await db.guides.update_one({"_id": oid}, {"$set": {"status": "rejected"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")
    return {"message": "Đã từ chối hồ sơ hướng dẫn viên"}

@router.get("/unassigned-tours")
async def get_unassigned_tours(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.tours.find({"guide_id": {"$exists": False}})
    tours = []
    async for doc in cursor:
        tours.append({
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "category": doc.get("category", ""),
            "price": doc.get("price", 0),
            "location": doc.get("location", "")
        })
    return tours

@router.get("/assignments/{assignment_id}/passengers")
async def get_assignment_passengers(assignment_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    guide = await db.guides.find_one({"user_id": current_user["id"], "status": "approved"})
    if not guide and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Tài khoản chưa được duyệt hướng dẫn viên")

    assign_oid = validate_object_id(assignment_id)
    assignment = await db.guide_assignments.find_one({"_id": assign_oid})
    if not assignment:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyến đi được phân công")

    if current_user.get("role") != "admin" and str(assignment.get("guide_id")) != str(guide["_id"]):
        raise HTTPException(status_code=403, detail="Bạn không phụ trách chuyến đi này")

    tour_id_val = str(assignment.get("tour_id"))
    trip_date = assignment.get("trip_date")
    query = {
        "status": {"$in": ["confirmed", "pending"]},
        "$or": [
            {"tour_id": tour_id_val},
            {"combo_items.tour_id": tour_id_val}
        ]
    }
    if trip_date:
        query["travel_date"] = trip_date

    cursor = db.bookings.find(query)
    passengers = []
    async for doc in cursor:
        passengers.append({
            "booking_id": str(doc["_id"]),
            "booking_code": doc.get("booking_code") or ("ST-" + str(doc["_id"])[-6:].upper()),
            "customer_name": doc.get("contact_name") or "Khách hàng",
            "customer_phone": doc.get("contact_phone", ""),
            "customer_email": doc.get("contact_email", ""),
            "adults": doc.get("adults", 1),
            "children": doc.get("children", 0),
            "checked_in": doc.get("checked_in", False),
            "checkin_time": doc.get("checkin_time"),
            "payment_status": doc.get("payment_status", "pending"),
            "status": doc.get("status", "pending")
        })

    return {
        "assignment_id": assignment_id,
        "tour_title": assignment.get("tour_title", "Tour"),
        "trip_date": trip_date,
        "status": assignment.get("status", "assigned"),
        "passengers": passengers,
        "total_passengers": len(passengers),
        "checked_in_count": sum(1 for p in passengers if p["checked_in"])
    }

@router.post("/checkin/{booking_id}")
async def checkin_passenger(booking_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    guide = await db.guides.find_one({"user_id": current_user["id"], "status": "approved"})
    if not guide and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Tài khoản chưa được duyệt hướng dẫn viên")

    b_oid = validate_object_id(booking_id)
    booking = await db.bookings.find_one({"_id": b_oid})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt của hành khách")

    now_str = datetime.utcnow().isoformat()
    await db.bookings.update_one(
        {"_id": b_oid},
        {"$set": {"checked_in": True, "checkin_time": now_str}}
    )

    return {
        "message": "Điểm danh hành khách thành công",
        "booking_id": booking_id,
        "checked_in": True,
        "checkin_time": now_str
    }

@router.patch("/assignments/{assignment_id}/status")
async def update_trip_status(assignment_id: str, payload: TripStatusUpdate, current_user: dict = Depends(get_current_user)):
    if payload.status not in ("assigned", "in_progress", "departed", "completed"):
        raise HTTPException(status_code=400, detail="Trạng thái chuyến đi không hợp lệ")

    db = get_db()
    guide = await db.guides.find_one({"user_id": current_user["id"], "status": "approved"})
    if not guide and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Tài khoản chưa được duyệt hướng dẫn viên")

    assign_oid = validate_object_id(assignment_id)
    assignment = await db.guide_assignments.find_one({"_id": assign_oid})
    if not assignment:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyến đi được phân công")

    if current_user.get("role") != "admin" and str(assignment.get("guide_id")) != str(guide["_id"]):
        raise HTTPException(status_code=403, detail="Bạn không phụ trách chuyến đi này")

    await db.guide_assignments.update_one(
        {"_id": assign_oid},
        {"$set": {"status": payload.status, "updated_at": datetime.utcnow().isoformat()}}
    )

    if payload.status == "completed":
        tour_id_val = str(assignment.get("tour_id"))
        trip_date = assignment.get("trip_date")
        query = {
            "$or": [
                {"tour_id": tour_id_val},
                {"combo_items.tour_id": tour_id_val}
            ]
        }
        if trip_date:
            query["travel_date"] = trip_date
        await db.bookings.update_many(query, {"$set": {"status": "completed"}})

    return {
        "message": "Cập nhật trạng thái chuyến đi thành công",
        "assignment_id": assignment_id,
        "status": payload.status
    }

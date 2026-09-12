from fastapi import APIRouter, Depends, HTTPException, Query, Body
from app.db.mongodb import get_db
from app.schemas.guide import GuideCreate, GuideResponse, GuideUpdate, GuideRequestCreate
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
    existing = await db.guides.find_one({"user_id": current_user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Bạn đã gửi hồ sơ rồi")

    guide_dict = guide.model_dump()
    guide_dict["user_id"] = current_user["id"]
    guide_dict["status"] = "pending"
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
            "tour_title": doc.get("tour_title", "Tour"),
            "destination": doc.get("destination", ""),
            "trip_date": trip_date,
            "earning": doc.get("earning", 0),
            "status": status
        }
        if status in ("assigned", "in_progress"):
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

@router.patch("/{id}/assign-tour")
async def assign_tour_to_guide(
    id: str, 
    tour_id: str = Query(...), 
    admin: dict = Depends(get_current_admin_user)
):
    """Admin: Assign a tour to a guide"""
    db = get_db()
    oid = validate_object_id(id)
    tour_oid = validate_object_id(tour_id)
    
    # Check tour exists and not already assigned
    tour = await db.tours.find_one({"_id": tour_oid})
    if not tour:
        raise HTTPException(status_code=404, detail="Không tìm thấy tour")
    
    # Check tour already has a guide
    if tour.get("guide_id"):
        raise HTTPException(status_code=400, detail="Tour đã được phân công cho hướng dẫn viên khác")
    
    # Assign tour to guide
    await db.tours.update_one({"_id": tour_oid}, {"$set": {"guide_id": oid}})
    
    # Create assignment record
    assignment_doc = {
        "guide_id": oid,
        "tour_id": tour_oid,
        "status": "assigned",
        "assigned_at": datetime.utcnow().isoformat(),
        "assigned_by": admin.get("email", "admin")
    }
    await db.guide_assignments.insert_one(assignment_doc)
    
    return {
        "message": "Đã phân công tour cho hướng dẫn viên",
        "guide_id": str(oid),
        "tour_id": tour_id
    }

@router.post("/assign", response_model=dict)
async def assign_guide_tour(
    payload: dict = Body(...),
    admin: dict = Depends(get_current_admin_user)
):
    """Admin: Assign a tour to a guide (JSON)"""
    db = get_db()
    guide_id = payload.get("guide_id")
    tour_title = payload.get("tour_title")
    destination = payload.get("destination")
    trip_date = payload.get("trip_date")
    earning = float(payload.get("earning", 0))
    
    if not guide_id or not tour_title or not destination or not trip_date:
        raise HTTPException(status_code=400, detail="Thiếu thông tin bắt buộc")
    
    oid = validate_object_id(guide_id)
    
    # Check guide exists and is approved
    guide = await db.guides.find_one({"_id": oid, "status": "approved"})
    if not guide:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên hoặc chưa được duyệt")
    
    # Create new tour assigned to this guide
    tour_doc = {
        "title": tour_title,
        "slug": tour_title.lower().replace(" ", "-"),
        "category": "Đa dạng",  # default category
        "location": destination,
        "duration_days": 2,  # default
        "duration_nights": 1,
        "price": earning,
        "discount_price": None,
        "rating": 0.0,
        "review_count": 0,
        "images": [],
        "tags": [],
        "is_active": True,
        "lat": None,
        "lng": None,
        "geo_location": None,
        "guide_id": str(oid)
    }
    result = await db.tours.insert_one(tour_doc)
    
    # Create assignment record
    assignment_doc = {
        "guide_id": oid,
        "tour_id": result.inserted_id,
        "tour_title": tour_title,
        "destination": destination,
        "trip_date": trip_date,
        "earning": earning,
        "status": "assigned",
        "assigned_at": datetime.utcnow().isoformat(),
        "assigned_by": admin.get("email", "admin")
    }
    await db.guide_assignments.insert_one(assignment_doc)
    
    return {
        "message": "Đã tạo tour và phân công cho hướng dẫn viên",
        "guide_id": str(oid),
        "tour_id": str(result.inserted_id),
        "tour_title": tour_title
    }

@router.get("/unassigned-tours")
async def get_unassigned_tours(admin: dict = Depends(get_current_admin_user)):
    """Admin: List tours not assigned to any guide"""
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

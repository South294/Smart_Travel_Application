from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.schemas.guide import GuideCreate, GuideResponse, GuideRequestCreate
from app.routers.deps import get_current_user, get_current_admin_user
from app.routers.helpers import validate_object_id, serialize_guide
from typing import List
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

@router.get("/{id}", response_model=GuideResponse)
async def get_guide(id: str):
    db = get_db()
    oid = validate_object_id(id)
    guide = await db.guides.find_one({"_id": oid})
    if not guide:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")
    return serialize_guide(guide)

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
    cursor = db.guide_assignments.find({"guide_id": guide["_id"], "status": "completed"})

    trips = []
    total_trips_month = 0
    total_earnings_month = 0
    async for doc in cursor:
        trip_date = doc.get("trip_date")
        if isinstance(trip_date, str) and trip_date.startswith(current_month):
            total_trips_month += 1
            total_earnings_month += float(doc.get("earning", 0))
        trips.append({
            "id": str(doc.get("_id")),
            "tour_title": doc.get("tour_title", "Tour"),
            "destination": doc.get("destination", ""),
            "trip_date": trip_date,
            "earning": doc.get("earning", 0),
            "status": doc.get("status", "completed")
        })

    return {
        "guide": serialize_guide(guide),
        "stats": {
            "trips_month": total_trips_month,
            "earnings_month": total_earnings_month
        },
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

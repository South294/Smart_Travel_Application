from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.mongodb import get_db
from app.routers.deps import get_current_admin_user
from app.routers.helpers import serialize_user, serialize_booking, serialize_guide, validate_object_id

router = APIRouter()

class UserStatusUpdate(BaseModel):
    is_active: bool

class AdminSettingsUpdate(BaseModel):
    maintenance_mode: bool = False
    auto_approve_guides: bool = True
    email_new_booking: bool = True

class BookingStatusUpdate(BaseModel):
    status: str

class GuideAssignmentCreate(BaseModel):
    guide_id: str
    tour_title: str
    destination: str
    trip_date: str
    earning: float = 0

@router.get("/dashboard")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    users_count = await db.users.count_documents({})
    tours_count = await db.tours.count_documents({})
    bookings_count = await db.bookings.count_documents({})
    pending_guides = await db.guides.count_documents({"status": "pending"})

    return {
        "users_count": users_count,
        "tours_count": tours_count,
        "bookings_count": bookings_count,
        "pending_guides_count": pending_guides
    }

@router.get("/users")
async def get_all_users(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.users.find({}, {"password_hash": 0})
    users = []
    async for doc in cursor:
        users.append(serialize_user(doc))
    return users

@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, payload: UserStatusUpdate, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(user_id)
    if str(admin.get("id")) == user_id:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản admin")
    target = await db.users.find_one({"_id": oid})
    if target and target.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản admin khác")
    result = await db.users.update_one({"_id": oid}, {"$set": {"is_active": payload.is_active}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    return {"message": "Cập nhật trạng thái thành công"}

@router.get("/bookings")
async def get_all_bookings(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.bookings.find()
    bookings = []
    async for doc in cursor:
        booking = serialize_booking(doc)
        tour = await db.tours.find_one({"_id": validate_object_id(booking["tour_id"])}) if booking.get("tour_id") else None
        if tour:
            booking["tour_title"] = tour.get("title", "Tour")
        bookings.append(booking)
    return bookings

@router.patch("/bookings/{booking_id}/status")
async def update_booking_status(booking_id: str, payload: BookingStatusUpdate, admin: dict = Depends(get_current_admin_user)):
    if payload.status not in {"pending", "confirmed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
    db = get_db()
    oid = validate_object_id(booking_id)
    result = await db.bookings.update_one({"_id": oid}, {"$set": {"status": payload.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy booking")
    return {"message": "Cập nhật trạng thái booking thành công"}

@router.get("/guides/pending")
async def get_pending_guides(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.guides.find({"status": "pending"})
    guides = []
    async for doc in cursor:
        guides.append(serialize_guide(doc))
    return guides

@router.get("/guides")
async def get_all_guides(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.guides.find()
    guides = []
    async for doc in cursor:
        guides.append(serialize_guide(doc))
    return guides

@router.post("/guides/assign")
async def create_guide_assignment(payload: GuideAssignmentCreate, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    guide_oid = validate_object_id(payload.guide_id)
    guide = await db.guides.find_one({"_id": guide_oid, "status": "approved"})
    if not guide:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")

    assignment = {
        "guide_id": guide_oid,
        "tour_title": payload.tour_title,
        "destination": payload.destination,
        "trip_date": payload.trip_date,
        "earning": payload.earning,
        "status": "completed"
    }

    result = await db.guide_assignments.insert_one(assignment)
    return {"message": "Đã tạo chuyến cho hướng dẫn viên", "id": str(result.inserted_id)}

@router.get("/settings")
async def get_admin_settings(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    doc = await db.settings.find_one({"key": "admin"})
    if not doc:
        return {
            "maintenance_mode": False,
            "auto_approve_guides": True,
            "email_new_booking": True
        }
    return doc.get("value", {})

@router.put("/settings")
async def update_admin_settings(payload: AdminSettingsUpdate, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    await db.settings.update_one(
        {"key": "admin"},
        {"$set": {"key": "admin", "value": payload.model_dump()}},
        upsert=True
    )
    return {"message": "Cập nhật cài đặt thành công"}

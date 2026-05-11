from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.schemas.guide import GuideCreate, GuideResponse
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

@router.patch("/{id}/approve")
async def approve_guide(id: str, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(id)
    result = await db.guides.update_one({"_id": oid}, {"$set": {"status": "approved"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")
    return {"message": "Đã duyệt hồ sơ hướng dẫn viên"}

@router.patch("/{id}/reject")
async def reject_guide(id: str, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(id)
    result = await db.guides.update_one({"_id": oid}, {"$set": {"status": "rejected"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hướng dẫn viên")
    return {"message": "Đã từ chối hồ sơ hướng dẫn viên"}

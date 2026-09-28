from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.routers.deps import get_current_user
from app.routers.helpers import serialize_user, validate_object_id
from app.schemas.user import UserUpdate, UserPreferencesUpdate, UserSettingsUpdate, UserCCCDVerificationRequest, UserCCCDVerificationResponse
from datetime import datetime

router = APIRouter()

@router.get("/me")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    return serialize_user(current_user)

@router.put("/me")
async def update_user_profile(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        return {"message": "Không có dữ liệu cập nhật"}

    user_oid = validate_object_id(current_user["id"])
    await db.users.update_one({"_id": user_oid}, {"$set": update_data})
    return {"message": "Cập nhật hồ sơ thành công"}

@router.put("/me/preferences")
async def update_user_preferences(data: UserPreferencesUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_oid = validate_object_id(current_user["id"])
    await db.users.update_one(
        {"_id": user_oid},
        {"$set": {"preferences": data.preferences, "custom_preferences": data.custom_preferences}}
    )
    return {"message": "Cập nhật sở thích thành công"}

@router.put("/me/settings")
async def update_user_settings(data: UserSettingsUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_oid = validate_object_id(current_user["id"])
    await db.users.update_one(
        {"_id": user_oid},
        {"$set": {"settings": data.settings.model_dump()}}
    )
    return {"message": "Cập nhật cài đặt thành công"}

@router.post("/me/cccd-verify", response_model=UserCCCDVerificationResponse)
async def verify_user_cccd(data: UserCCCDVerificationRequest, current_user: dict = Depends(get_current_user)):
    if not data.cccd_number.isdigit() or len(data.cccd_number) != 12:
        raise HTTPException(status_code=400, detail="Số CCCD phải gồm đúng 12 chữ số")
    now = datetime.utcnow().isoformat()
    cccd_info = {
        "number": data.cccd_number,
        "full_name": data.full_name,
        "birth_date": data.birth_date or "",
        "gender": data.gender or "",
        "id_front_url": data.id_front_url,
        "id_back_url": data.id_back_url,
        "portrait_url": data.portrait_url,
        "status": "verified",
        "verified_at": now
    }
    db = get_db()
    user_oid = validate_object_id(current_user["id"])
    await db.users.update_one({"_id": user_oid}, {"$set": {"cccd": cccd_info}})
    return {
        "message": "Xác thực CCCD thành công",
        "cccd_status": "verified",
        "verified_at": now
    }

@router.get("/me/cccd-status")
async def get_user_cccd_status(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_oid = validate_object_id(current_user["id"])
    user = await db.users.find_one({"_id": user_oid})
    cccd_info = user.get("cccd") if user else None
    if not cccd_info:
        return {"is_verified": False, "status": "unverified", "cccd": None}
    masked_number = cccd_info.get("number", "")
    if len(masked_number) == 12:
        masked_number = masked_number[:4] + "****" + masked_number[8:]
    return {
        "is_verified": cccd_info.get("status") == "verified",
        "status": cccd_info.get("status", "unverified"),
        "cccd": {
            "number": masked_number,
            "full_name": cccd_info.get("full_name", ""),
            "verified_at": cccd_info.get("verified_at", "")
        }
    }

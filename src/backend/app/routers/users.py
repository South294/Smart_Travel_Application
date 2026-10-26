from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.core.security import hash_password, verify_password
from app.routers.deps import get_current_user
from app.routers.helpers import serialize_user, validate_object_id
from app.schemas.auth import ChangePasswordRequest
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

@router.post("/me/change-password")
async def change_user_password(data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    db = get_db()
    user_oid = validate_object_id(current_user["id"])
    user = await db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    if not verify_password(data.old_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    if data.old_password == data.new_password:
        raise HTTPException(status_code=400, detail="Mật khẩu mới không được trùng với mật khẩu hiện tại")
    await db.users.update_one(
        {"_id": user_oid},
        {"$set": {"password_hash": hash_password(data.new_password)}}
    )
    return {"message": "Đổi mật khẩu thành công"}

@router.post("/me/cccd-verify", response_model=UserCCCDVerificationResponse)
async def verify_user_cccd(data: UserCCCDVerificationRequest, current_user: dict = Depends(get_current_user)):
    if not data.cccd_number.isdigit() or len(data.cccd_number) != 12:
        raise HTTPException(status_code=400, detail="Số CCCD phải gồm đúng 12 chữ số")
    valid_prefixes = ("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,", "data:image/jpg;base64,", "http://", "https://")
    for img_field, img_val in (("Mặt trước", data.id_front_url), ("Mặt sau", data.id_back_url), ("Chân dung", data.portrait_url)):
        if len(img_val) > 7000000:
            raise HTTPException(status_code=400, detail=f"Ảnh {img_field} vượt quá dung lượng tối đa cho phép (5MB)")
        if not any(img_val.startswith(p) for p in valid_prefixes):
            raise HTTPException(status_code=400, detail=f"Định dạng ảnh {img_field} không hợp lệ")
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

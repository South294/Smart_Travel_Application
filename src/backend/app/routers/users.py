from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_db
from app.routers.deps import get_current_user
from app.routers.helpers import serialize_user, validate_object_id
from app.schemas.user import UserUpdate, UserPreferencesUpdate, UserSettingsUpdate

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

from fastapi import APIRouter, HTTPException
from app.db.mongodb import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from datetime import datetime

router = APIRouter()

@router.post("/register")
async def register(data: RegisterRequest):
    db = get_db()
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")

    user_dict = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "phone": "",
        "birth_date": "",
        "gender": "",
        "address": "",
        "role": "user",
        "preferences": [],
        "custom_preferences": [],
        "saved_vouchers": [],
        "settings": {
            "email_notifications": True,
            "sms_notifications": False,
            "ai_personalization": True,
            "language": "vi"
        },
        "avatar_url": "",
        "created_at": datetime.utcnow().isoformat()
    }

    result = await db.users.insert_one(user_dict)
    return {"message": "Đăng ký thành công", "user_id": str(result.inserted_id)}

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    db = get_db()
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không đúng")

    token = create_access_token(data={"sub": user["email"], "role": user["role"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

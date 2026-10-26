import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from app.db.mongodb import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, RegisterOTPRequest, LoginRequest, TokenResponse, ResetPasswordRequest, ForgotPasswordRequest
from app.services.email_service import send_otp_email

router = APIRouter()

@router.post("/register-otp")
async def send_register_otp(data: RegisterOTPRequest):
    db = get_db()
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký tài khoản")

    otp_code = str(secrets.randbelow(900000) + 100000)
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    hashed_otp = hash_password(otp_code)

    await db.email_verifications.update_one(
        {"email": data.email},
        {"$set": {
            "email": data.email,
            "otp_hash": hashed_otp,
            "expires_at": expires_at,
            "created_at": datetime.utcnow().isoformat()
        }},
        upsert=True
    )

    sent = await send_otp_email(data.email, otp_code, data.full_name)
    response_payload = {
        "message": "Mã xác thực OTP đã được gửi đến email của bạn và có hiệu lực trong 10 phút."
    }
    if not sent:
        response_payload["otp_demo"] = otp_code
    return response_payload

@router.post("/register")
async def register(data: RegisterRequest):
    db = get_db()
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")

    if data.otp:
        record = await db.email_verifications.find_one({"email": data.email})
        if not record or not record.get("otp_hash"):
            raise HTTPException(status_code=400, detail="Vui lòng yêu cầu mã xác thực OTP trước khi đăng ký")
        expires_at_str = record.get("expires_at")
        if expires_at_str and datetime.fromisoformat(expires_at_str) < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Mã xác thực OTP đã hết hạn. Vui lòng nhận mã mới.")
        if not verify_password(data.otp, record.get("otp_hash", "")):
            raise HTTPException(status_code=400, detail="Mã xác thực OTP không chính xác")
        await db.email_verifications.delete_one({"email": data.email})
    else:
        pending = await db.email_verifications.find_one({"email": data.email})
        if pending and pending.get("otp_hash"):
            expires_at_str = pending.get("expires_at")
            if expires_at_str and datetime.fromisoformat(expires_at_str) >= datetime.utcnow():
                raise HTTPException(status_code=400, detail="Vui lòng nhập mã OTP đã được gửi về email của bạn")

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
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")

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

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    db = get_db()
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
    otp_code = str(secrets.randbelow(900000) + 100000)
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    hashed_otp = hash_password(otp_code)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"reset_otp": hashed_otp, "reset_otp_expires_at": expires_at}}
    )
    return {
        "message": "Mã xác thực OTP đã được gửi và có hiệu lực trong 10 phút.",
        "otp_demo": otp_code
    }

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    db = get_db()
    user = await db.users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")
    if user.get("is_active") is False:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
    stored_otp = user.get("reset_otp")
    expires_at_str = user.get("reset_otp_expires_at")
    if not stored_otp or not expires_at_str:
        raise HTTPException(status_code=400, detail="Yêu cầu đặt lại mật khẩu chưa được khởi tạo hoặc mã OTP đã bị vô hiệu")
    if datetime.fromisoformat(expires_at_str) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Mã OTP đã hết hạn. Vui lòng yêu cầu mã xác thực mới.")
    if not verify_password(data.otp, stored_otp):
        raise HTTPException(status_code=400, detail="Mã xác thực OTP không chính xác")
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": hash_password(data.new_password)},
            "$unset": {"reset_otp": "", "reset_otp_expires_at": ""}
        }
    )
    return {"message": "Đặt lại mật khẩu thành công. Bạn có thể đăng nhập ngay bây giờ."}

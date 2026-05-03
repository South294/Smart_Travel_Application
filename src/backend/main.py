from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Smart Travel API",
    description="Hệ thống Backend cho dự án Du Lịch Thông Minh. Hỗ trợ tích hợp OpenStreetMap, AI và quản lý dữ liệu.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str


fake_users_db = {}

@app.get("/", tags=["General"])
async def read_root():
    return {
        "app": "Smart Travel API",
        "status": "Running",
        "message": "Chào mừng bạn đến với hệ thống API của dự án Du lịch thông minh!"
    }

@app.post("/api/register", tags=["Authentication"])
async def register(user: UserCreate):

    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")
    
    from security import hash_password
    hashed_pwd = hash_password(user.password)
    

    fake_users_db[user.email] = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_pwd,
        "role": "user"
    }
    
    return {"message": "Đăng ký thành công!", "email": user.email}

@app.post("/api/login", tags=["Authentication"])
async def login(user: UserLogin):

    db_user = fake_users_db.get(user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không chính xác.")
    
    from security import verify_password, create_access_token
    from datetime import timedelta
    import os
    

    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không chính xác.")
    

    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    access_token = create_access_token(
        data={"sub": user.email, "role": db_user["role"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "email": db_user["email"],
            "full_name": db_user["full_name"],
            "role": db_user["role"]
        }
    }

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    try:
        return HealthResponse(status="healthy", message="Tất cả các dịch vụ đang hoạt động tốt.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Hệ thống đang gặp sự cố nội bộ.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

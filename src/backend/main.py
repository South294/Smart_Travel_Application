from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Smart Travel API",
    description="Hệ thống Backend cho dự án Du Lịch Thông Minh. Hỗ trợ tích hợp Google Maps, AI và quản lý dữ liệu.",
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

@app.get("/", tags=["General"])
async def read_root():
    return {
        "app": "Smart Travel API",
        "status": "Running",
        "message": "Chào mừng bạn đến với hệ thống API của dự án Du lịch thông minh!"
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

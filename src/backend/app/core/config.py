from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Travel API"
    VERSION: str = "1.0.0"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "smart_travel"
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "smart-travel-development-secret-change-before-production-2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5500")
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    VNPAY_TMN_CODE: str = ""
    VNPAY_HASH_SECRET: str = ""
    VNPAY_PAYMENT_URL: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    VNPAY_RETURN_URL: str = "http://localhost:8000/api/payments/vnpay/return"
    PAYMENT_FRONTEND_URL: str = "http://localhost:5500/checkout.html"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Travel API"
    VERSION: str = "1.0.0"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "smart_travel"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5500")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


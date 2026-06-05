from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Travel API"
    VERSION: str = "1.0.0"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "smart_travel"
    SECRET_KEY: str = "9a3f2d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_ORIGIN: str = "http://localhost:5500"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


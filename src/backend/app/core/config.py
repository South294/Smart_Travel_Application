from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Travel API"
    VERSION: str = "1.0.0"
    MONGODB_URI: str
    MONGODB_DB: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_ORIGIN: str = "http://localhost:5500"

    class Config:
        env_file = ".env"

settings = Settings()

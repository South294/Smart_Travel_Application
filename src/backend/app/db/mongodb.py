from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoClientManager:
    client: AsyncIOMotorClient = None
    db = None

db_manager = MongoClientManager()

async def connect_to_mongo():
    db_manager.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_manager.db = db_manager.client[settings.MONGODB_DB]
    print(f"Connected to MongoDB at {settings.MONGODB_URI}, database: {settings.MONGODB_DB}")

async def close_mongo_connection():
    if db_manager.client:
        db_manager.client.close()
        print("Closed MongoDB connection.")

def get_db():
    return db_manager.db

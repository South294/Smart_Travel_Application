from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, users, tours, bookings, vouchers, guides, admin
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_db
import pymongo

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    db = get_db()
    if db is not None:
        await db.tours.create_index([("geo_location", pymongo.GEOSPHERE)])
        await db.tours.create_index("slug", unique=True)
        await db.tours.create_index("category")
        await db.tours.create_index("is_active")
        await db.users.create_index("email", unique=True)
        await db.vouchers.create_index("code", unique=True)
        await db.vouchers.create_index("is_active")
        await db.bookings.create_index("user_id")
        await db.bookings.create_index("tour_id")
        await db.bookings.create_index("status")
        await db.guides.create_index("user_id")
        await db.guides.create_index("status")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(tours.router, prefix="/api/tours", tags=["Tours"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(vouchers.router, prefix="/api/vouchers", tags=["Vouchers"])
app.include_router(guides.router, prefix="/api/guides", tags=["Guides"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {"message": "Smart Travel API is running", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

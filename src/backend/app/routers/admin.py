from fastapi import APIRouter, Depends
from app.db.mongodb import get_db
from app.routers.deps import get_current_admin_user
from app.routers.helpers import serialize_user, serialize_booking, serialize_guide

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    users_count = await db.users.count_documents({})
    tours_count = await db.tours.count_documents({})
    bookings_count = await db.bookings.count_documents({})
    pending_guides = await db.guides.count_documents({"status": "pending"})

    return {
        "users_count": users_count,
        "tours_count": tours_count,
        "bookings_count": bookings_count,
        "pending_guides_count": pending_guides
    }

@router.get("/users")
async def get_all_users(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.users.find({}, {"password_hash": 0})
    users = []
    async for doc in cursor:
        users.append(serialize_user(doc))
    return users

@router.get("/bookings")
async def get_all_bookings(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.bookings.find()
    bookings = []
    async for doc in cursor:
        bookings.append(serialize_booking(doc))
    return bookings

@router.get("/guides/pending")
async def get_pending_guides(admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    cursor = db.guides.find({"status": "pending"})
    guides = []
    async for doc in cursor:
        guides.append(serialize_guide(doc))
    return guides

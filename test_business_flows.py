import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from bson import ObjectId
from fastapi import HTTPException

BACKEND_DIR = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import bookings as bookings_router
from app.routers import guides as guides_router
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.booking import BookingCreate
from app.schemas.guide import GuideCreate


class FakeResult:
    def __init__(self, inserted_id=None, matched_count=1):
        self.inserted_id = inserted_id or ObjectId()
        self.matched_count = matched_count


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, *_args):
        return self

    def __aiter__(self):
        self.iterator = iter(self.documents)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    @staticmethod
    def matches(document, query):
        for key, expected in query.items():
            actual = document.get(key)
            if isinstance(expected, dict):
                if "$exists" in expected and (key in document) != expected["$exists"]:
                    return False
            elif actual != expected:
                return False
        return True

    async def find_one(self, query, *_args):
        for document in self.documents:
            if self.matches(document, query):
                return document
        return None

    async def insert_one(self, document):
        document.setdefault("_id", ObjectId())
        self.documents.append(document)
        return FakeResult(document["_id"])

    async def update_one(self, query, update, **_kwargs):
        for document in self.documents:
            if self.matches(document, query):
                document.update(update.get("$set", {}))
                return FakeResult(document["_id"], 1)
        return FakeResult(matched_count=0)

    def find(self, query=None, *_args):
        query = query or {}
        return FakeCursor([doc for doc in self.documents if self.matches(doc, query)])


class FakeDatabase:
    def __init__(self):
        self.users = FakeCollection()
        self.guides = FakeCollection()
        self.tours = FakeCollection()
        self.bookings = FakeCollection()
        self.guide_assignments = FakeCollection()


class BusinessFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_can_register_and_login(self):
        database = FakeDatabase()
        with patch.object(auth_router, "get_db", return_value=database):
            await auth_router.register(RegisterRequest(
                email="user@example.com",
                password="password123",
                full_name="Test User",
            ))
            response = await auth_router.login(LoginRequest(
                email="user@example.com",
                password="password123",
            ))

        self.assertEqual(response["token_type"], "bearer")
        self.assertEqual(response["user"]["email"], "user@example.com")

    async def test_pending_guide_cannot_open_dashboard(self):
        database = FakeDatabase()
        user_id = str(ObjectId())
        database.guides.documents.append({
            "_id": ObjectId(),
            "user_id": user_id,
            "name": "Pending Guide",
            "status": "pending",
            "experience_years": 2,
            "price_per_day": 300000,
            "areas": ["Ha Noi"],
            "languages": ["Vietnamese"],
            "bio": "Local guide",
            "created_at": datetime.utcnow().isoformat(),
        })

        with patch.object(guides_router, "get_db", return_value=database):
            with self.assertRaises(HTTPException) as context:
                await guides_router.get_guide_dashboard({"id": user_id, "role": "user"})

        self.assertEqual(context.exception.status_code, 403)

    async def test_approved_guide_can_open_dashboard(self):
        database = FakeDatabase()
        user_id = str(ObjectId())
        database.guides.documents.append({
            "_id": ObjectId(),
            "user_id": user_id,
            "name": "Approved Guide",
            "status": "approved",
            "experience_years": 5,
            "price_per_day": 500000,
            "areas": ["Ha Noi"],
            "languages": ["Vietnamese"],
            "bio": "Local guide",
            "created_at": datetime.utcnow().isoformat(),
        })

        with patch.object(guides_router, "get_db", return_value=database):
            response = await guides_router.get_guide_dashboard({"id": user_id, "role": "guide"})

        self.assertEqual(response["guide"]["status"], "approved")
        self.assertEqual(response["stats"]["active_trips"], 0)

    async def test_admin_can_approve_pending_guide(self):
        database = FakeDatabase()
        guide_id = ObjectId()
        user_id = ObjectId()
        database.guides.documents.append({
            "_id": guide_id,
            "user_id": str(user_id),
            "name": "Pending Guide",
            "status": "pending",
            "experience_years": 2,
            "price_per_day": 300000,
            "areas": ["Ha Noi"],
            "languages": ["Vietnamese"],
            "bio": "Local guide",
            "created_at": datetime.utcnow().isoformat(),
        })
        database.users.documents.append({"_id": user_id, "role": "user"})

        with patch.object(guides_router, "get_db", return_value=database):
            response = await guides_router.approve_guide(str(guide_id), {"email": "admin@example.com"})

        self.assertEqual(response["message"], "Đã duyệt hồ sơ hướng dẫn viên")
        self.assertEqual(database.guides.documents[0]["status"], "approved")
        self.assertEqual(database.users.documents[0]["role"], "guide")

    async def test_user_can_create_booking_for_existing_tour(self):
        database = FakeDatabase()
        tour_id = ObjectId()
        database.tours.documents.append({
            "_id": tour_id,
            "title": "Ha Noi Heritage",
            "is_active": True,
            "price": 1000000,
        })
        booking = BookingCreate(
            tour_id=str(tour_id),
            travel_date=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            adults=2,
            children=1,
            payment_method="credit_card",
            contact_phone="0900000000",
        )

        with patch.object(bookings_router, "get_db", return_value=database):
            response = await bookings_router.create_booking(booking, {"id": "user-a", "role": "user"})

        self.assertEqual(response["user_id"], "user-a")
        self.assertEqual(response["total_amount"], 2500000)

    async def test_admin_assigns_existing_tour_to_approved_guide(self):
        database = FakeDatabase()
        guide_id = ObjectId()
        tour_id = ObjectId()
        database.guides.documents.append({"_id": guide_id, "status": "approved"})
        database.tours.documents.append({
            "_id": tour_id,
            "title": "Mountain Escape",
            "location": "Sapa",
            "is_active": True,
        })
        payload = admin_router.GuideAssignmentCreate(
            guide_id=str(guide_id),
            tour_id=str(tour_id),
            trip_date="2026-10-01",
            earning=500000,
        )

        with patch.object(admin_router, "get_db", return_value=database):
            response = await admin_router.create_guide_assignment(
                payload,
                {"email": "admin@example.com"},
            )

        self.assertEqual(response["tour_id"], str(tour_id))
        self.assertEqual(database.tours.documents[0]["guide_id"], guide_id)
        self.assertEqual(database.guide_assignments.documents[0]["status"], "assigned")

    async def test_user_cannot_read_another_users_booking(self):
        database = FakeDatabase()
        booking_id = ObjectId()
        database.bookings.documents.append({
            "_id": booking_id,
            "user_id": str(ObjectId()),
            "tour_id": str(ObjectId()),
            "travel_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "adults": 1,
            "children": 0,
            "insurance": False,
            "payment_method": "credit_card",
            "contact_phone": "0900000000",
            "status": "pending",
            "total_amount": 100000,
            "created_at": datetime.utcnow().isoformat(),
        })

        with patch.object(bookings_router, "get_db", return_value=database):
            with self.assertRaises(HTTPException) as context:
                await bookings_router.get_booking(str(booking_id), {"id": str(ObjectId()), "role": "user"})

        self.assertEqual(context.exception.status_code, 403)

    async def test_booking_for_missing_tour_returns_not_found(self):
        database = FakeDatabase()
        booking = BookingCreate(
            tour_id=str(ObjectId()),
            travel_date=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            adults=1,
            children=0,
            payment_method="credit_card",
            contact_phone="0900000000",
        )

        with patch.object(bookings_router, "get_db", return_value=database):
            with self.assertRaises(HTTPException) as context:
                await bookings_router.create_booking(booking, {"id": str(ObjectId()), "role": "user"})

        self.assertEqual(context.exception.status_code, 404)

    async def test_non_admin_cannot_use_admin_guard(self):
        with self.assertRaises(HTTPException) as context:
            await admin_router.get_current_admin_user({"id": str(ObjectId()), "role": "user"})

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()

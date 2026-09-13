from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.db.mongodb import get_db
from app.schemas.tour import TourCreate, TourUpdate, TourResponse, TourRecommendationResponse
from app.routers.deps import get_current_admin_user, get_optional_current_user
from app.routers.helpers import validate_object_id, serialize_tour
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.get("", response_model=List[TourResponse])
async def get_tours(
    category: Optional[str] = None,
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(50)
):
    db = get_db()
    query = {"is_active": True}
    if category:
        query["category"] = category

    if lat is not None and lng is not None:
        query["geo_location"] = {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius_km * 1000
            }
        }

    cursor = db.tours.find(query)
    tours = []
    async for doc in cursor:
        tours.append(serialize_tour(doc))
    return tours

@router.get("/hot", response_model=List[TourResponse])
async def get_hot_tours(limit: int = Query(8, ge=1, le=30)):
    db = get_db()
    query = {
        "is_active": True,
        "$or": [
            {"tags": {"$in": ["hot", "best-seller"]}},
            {"rating": {"$gte": 4.8}}
        ]
    }
    cursor = db.tours.find(query).sort([("rating", -1), ("review_count", -1)]).limit(limit)
    tours = []
    async for doc in cursor:
        tours.append(serialize_tour(doc))
    if len(tours) < limit:
        existing_ids = {t["id"] for t in tours}
        fallback_cursor = db.tours.find({"is_active": True, "_id": {"$nin": [validate_object_id(tid) for tid in existing_ids]}}).sort("rating", -1).limit(limit - len(tours))
        async for doc in fallback_cursor:
            tours.append(serialize_tour(doc))
    return tours

@router.get("/recommendations", response_model=List[TourRecommendationResponse])
async def get_tour_recommendations(
    max_budget: Optional[float] = Query(None, ge=0),
    category: Optional[str] = None,
    preferences: Optional[str] = None,
    limit: int = Query(8, ge=1, le=30),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    db = get_db()
    user_prefs = set()
    if current_user:
        for p in current_user.get("preferences", []):
            user_prefs.add(str(p).strip().lower())
        for cp in current_user.get("custom_preferences", []):
            user_prefs.add(str(cp).strip().lower())

    if preferences:
        for item in preferences.split(","):
            cleaned = item.strip().lower()
            if cleaned:
                user_prefs.add(cleaned)

    booked_tour_ids = set()
    history_categories = set()
    avg_spending = 0.0

    if current_user:
        user_bookings = db.bookings.find({
            "user_id": current_user["id"],
            "status": {"$in": ["confirmed", "completed", "pending"]}
        })
        booking_amounts = []
        async for b in user_bookings:
            tid = b.get("tour_id")
            if tid:
                booked_tour_ids.add(str(tid))
            amt = b.get("total_amount")
            if amt and float(amt) > 0:
                booking_amounts.append(float(amt))

        if booked_tour_ids:
            booked_oids = [validate_object_id(tid) for tid in booked_tour_ids if tid]
            cursor_hist = db.tours.find({"_id": {"$in": booked_oids}})
            async for ht in cursor_hist:
                cat = ht.get("category")
                if cat:
                    history_categories.add(cat.lower())

        if booking_amounts:
            avg_spending = sum(booking_amounts) / len(booking_amounts)

    if not max_budget and avg_spending > 0:
        effective_budget = avg_spending * 1.3
    else:
        effective_budget = max_budget

    cursor = db.tours.find({"is_active": True})
    scored_tours = []

    category_aliases = {
        "biển": "sea",
        "biển đảo": "sea",
        "sea": "sea",
        "núi": "mountain",
        "núi rừng": "mountain",
        "mountain": "mountain",
        "văn hóa": "sight",
        "di sản": "sight",
        "sight": "sight",
        "trekking": "mountain",
        "ẩm thực": "sight",
        "nghỉ dưỡng": "sea"
    }

    norm_category = category.lower() if category else None
    if norm_category and norm_category in category_aliases:
        norm_category = category_aliases[norm_category]

    async for doc in cursor:
        tour = serialize_tour(doc)
        tid = tour.get("id")
        price = float(tour.get("discount_price") or tour.get("price") or 0)
        t_cat = (tour.get("category") or "").lower()
        t_loc = (tour.get("location") or "").lower()
        t_tags = [str(t).lower() for t in tour.get("tags", [])]

        score = 50.0
        reasons = []

        if effective_budget and effective_budget > 0:
            if price <= effective_budget:
                score += 25.0
                reasons.append("Vừa vặn với ngân sách của bạn")
            else:
                ratio = (price - effective_budget) / effective_budget
                score -= min(40.0, ratio * 35.0)
        elif price > 0:
            score += 10.0

        if norm_category:
            if t_cat == norm_category:
                score += 28.0
                reasons.append("Đúng danh mục yêu thích")
            else:
                score -= 10.0

        matched_pref = False
        for pref in user_prefs:
            mapped_cat = category_aliases.get(pref, pref)
            if mapped_cat == t_cat or pref in t_cat or pref in t_loc or any(pref in tag for tag in t_tags):
                score += 16.0
                matched_pref = True

        if matched_pref:
            reasons.append("Khớp với sở thích cá nhân")

        if t_cat in history_categories:
            score += 15.0
            reasons.append("Hợp phong cách các chuyến đi trước")

        if tid in booked_tour_ids:
            score -= 12.0

        rating = float(tour.get("rating") or 4.5)
        score += rating * 3.5

        if any(tag in ["hot", "best-seller"] for tag in t_tags):
            score += 9.0
            if not reasons:
                reasons.append("Điểm đến đang thịnh hành")

        match_pct = int(min(99, max(65, score)))
        if not reasons:
            reasons.append("Lựa chọn nổi bật được đánh giá cao")

        tour["match_score"] = round(score, 1)
        tour["match_reason"] = " • ".join(reasons[:2])
        tour["match_percentage"] = match_pct
        scored_tours.append(tour)

    scored_tours.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_tours[:limit]

@router.get("/{id}", response_model=TourResponse)
async def get_tour(id: str):
    db = get_db()
    oid = validate_object_id(id)
    tour = await db.tours.find_one({"_id": oid, "is_active": True})
    if not tour:
        raise HTTPException(status_code=404, detail="Không tìm thấy tour")
    return serialize_tour(tour)

@router.post("", response_model=TourResponse)
async def create_tour(tour: TourCreate, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    tour_dict = tour.model_dump()
    if tour.lat is not None and tour.lng is not None and not tour.geo_location:
        tour_dict["geo_location"] = {
            "type": "Point",
            "coordinates": [tour.lng, tour.lat]
        }
    tour_dict["created_at"] = datetime.utcnow().isoformat()
    result = await db.tours.insert_one(tour_dict)
    tour_dict["id"] = str(result.inserted_id)
    return tour_dict

@router.put("/{id}", response_model=TourResponse)
async def update_tour(id: str, tour_update: TourUpdate, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(id)
    update_data = {k: v for k, v in tour_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Không có dữ liệu cập nhật")

    result = await db.tours.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy tour")

    updated_tour = await db.tours.find_one({"_id": oid})
    return serialize_tour(updated_tour)

@router.delete("/{id}")
async def delete_tour(id: str, admin: dict = Depends(get_current_admin_user)):
    db = get_db()
    oid = validate_object_id(id)
    result = await db.tours.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy tour")
    return {"message": "Xóa tour thành công"}

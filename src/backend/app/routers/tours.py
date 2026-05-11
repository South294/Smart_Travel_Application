from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.mongodb import get_db
from app.schemas.tour import TourCreate, TourUpdate, TourResponse
from app.routers.deps import get_current_admin_user
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
    query = {}
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

@router.get("/{id}", response_model=TourResponse)
async def get_tour(id: str):
    db = get_db()
    oid = validate_object_id(id)
    tour = await db.tours.find_one({"_id": oid})
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

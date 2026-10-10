import math
from typing import Dict, List, Tuple

from fastapi import APIRouter, HTTPException

from app.db.mongodb import get_db
from app.schemas.route import RoutePlanRequest, RoutePlanResponse, RoutePoint, RouteTour

router = APIRouter()

import re

KNOWN_POINTS: Dict[str, Tuple[str, float, float]] = {
    "hà nội": ("Hà Nội", 21.0285, 105.8542),
    "hải phòng": ("Hải Phòng", 20.8449, 106.6881),
    "quảng ninh": ("Quảng Ninh", 20.9500, 107.0833),
    "hạ long": ("Hạ Long", 20.9101, 107.1839),
    "bắc ninh": ("Bắc Ninh", 21.1861, 106.0763),
    "hà nam": ("Hà Nam", 20.5835, 105.9230),
    "phủ lý": ("Phủ Lý", 20.5453, 105.9130),
    "hải dương": ("Hải Dương", 20.9373, 106.3146),
    "hưng yên": ("Hưng Yên", 20.6464, 106.0511),
    "nam định": ("Nam Định", 20.4388, 106.1621),
    "thái bình": ("Thái Bình", 20.4463, 106.3366),
    "ninh bình": ("Ninh Bình", 20.2506, 105.9740),
    "tam cốc": ("Tam Cốc", 20.2173, 105.9368),
    "tràng an": ("Tràng An", 20.2509, 105.8961),
    "bái đính": ("Bái Đính", 20.2767, 105.8422),
    "vĩnh phúc": ("Vĩnh Phúc", 21.3089, 105.6049),
    "tam đảo": ("Tam Đảo", 21.4550, 105.6420),
    "phú thọ": ("Phú Thọ", 21.3917, 105.3211),
    "hà giang": ("Hà Giang", 22.8233, 104.9839),
    "cao bằng": ("Cao Bằng", 22.6667, 106.2500),
    "bắc kạn": ("Bắc Kạn", 22.1472, 105.8347),
    "tuyên quang": ("Tuyên Quang", 21.8236, 105.2144),
    "lào cai": ("Lào Cai", 22.4856, 103.9707),
    "sa pa": ("Sa Pa", 22.3364, 103.8438),
    "sapa": ("Sa Pa", 22.3364, 103.8438),
    "yên bái": ("Yên Bái", 21.7167, 104.8667),
    "thái nguyên": ("Thái Nguyên", 21.5942, 105.8481),
    "lạng sơn": ("Lạng Sơn", 21.8536, 106.7628),
    "bắc giang": ("Bắc Giang", 21.2731, 106.1947),
    "điện biên": ("Điện Biên", 21.3833, 103.0167),
    "lai châu": ("Lai Châu", 22.3964, 103.4589),
    "sơn la": ("Sơn La", 21.3256, 103.9189),
    "mộc châu": ("Mộc Châu", 20.8439, 104.6473),
    "hòa bình": ("Hòa Bình", 20.8172, 105.3381),
    "mai châu": ("Mai Châu", 20.6589, 105.0811),
    "thanh hóa": ("Thanh Hóa", 19.8067, 105.7852),
    "nghệ an": ("Nghệ An", 18.6734, 105.6813),
    "vinh": ("Vinh", 18.6734, 105.6813),
    "hà tĩnh": ("Hà Tĩnh", 18.3428, 105.9058),
    "quảng bình": ("Quảng Bình", 17.4689, 106.6225),
    "đồng hới": ("Đồng Hới", 17.4689, 106.6225),
    "quảng trị": ("Quảng Trị", 16.7417, 107.1856),
    "thừa thiên huế": ("Thừa Thiên Huế", 16.4637, 107.5909),
    "huế": ("Huế", 16.4637, 107.5909),
    "đà nẵng": ("Đà Nẵng", 16.0544, 108.2022),
    "quảng nam": ("Quảng Nam", 15.5667, 108.4833),
    "hội an": ("Hội An", 15.8801, 108.3380),
    "quảng ngãi": ("Quảng Ngãi", 15.1206, 108.7922),
    "bình định": ("Bình Định", 13.7829, 109.2197),
    "quy nhơn": ("Quy Nhơn", 13.7829, 109.2197),
    "phú yên": ("Phú Yên", 13.0881, 109.3094),
    "tuy hòa": ("Tuy Hòa", 13.0881, 109.3094),
    "khánh hòa": ("Khánh Hòa", 12.2388, 109.1967),
    "nha trang": ("Nha Trang", 12.2388, 109.1967),
    "ninh thuận": ("Ninh Thuận", 11.5667, 108.9833),
    "phan rang": ("Phan Rang", 11.5667, 108.9833),
    "bình thuận": ("Bình Thuận", 10.9274, 108.1018),
    "phan thiết": ("Phan Thiết", 10.9274, 108.1018),
    "mũi né": ("Mũi Né", 10.9330, 108.2870),
    "kon tum": ("Kon Tum", 14.3500, 108.0000),
    "măng đen": ("Măng Đen", 14.6067, 108.2897),
    "gia lai": ("Gia Lai", 13.9833, 108.0000),
    "pleiku": ("Pleiku", 13.9833, 108.0000),
    "đắk lắk": ("Đắk Lắk", 12.6667, 108.0500),
    "buôn ma thuột": ("Buôn Ma Thuột", 12.6667, 108.0500),
    "đắk nông": ("Đắk Nông", 12.0000, 107.6833),
    "lâm đồng": ("Lâm Đồng", 11.9404, 108.4583),
    "đà lạt": ("Đà Lạt", 11.9404, 108.4583),
    "bình phước": ("Bình Phước", 11.7500, 106.9000),
    "tây ninh": ("Tây Ninh", 11.3000, 106.1000),
    "bình dương": ("Bình Dương", 11.1667, 106.6667),
    "đồng nai": ("Đồng Nai", 10.9500, 106.8167),
    "bà rịa": ("Bà Rịa", 10.4967, 107.1683),
    "vũng tàu": ("Vũng Tàu", 10.4114, 107.1362),
    "côn đảo": ("Côn Đảo", 8.6835, 106.6067),
    "hồ chí minh": ("TP. Hồ Chí Minh", 10.8231, 106.6297),
    "sài gòn": ("Sài Gòn", 10.8231, 106.6297),
    "long an": ("Long An", 10.5333, 106.4000),
    "tiền giang": ("Tiền Giang", 10.3500, 106.3500),
    "mỹ tho": ("Mỹ Tho", 10.3500, 106.3500),
    "bến tre": ("Bến Tre", 10.2333, 106.3833),
    "trà vinh": ("Trà Vinh", 9.9333, 106.3333),
    "vĩnh long": ("Vĩnh Long", 10.2500, 105.9667),
    "đồng tháp": ("Đồng Tháp", 10.4667, 105.6333),
    "an giang": ("An Giang", 10.3833, 105.4167),
    "châu đốc": ("Châu Đốc", 10.7000, 105.1167),
    "kiên giang": ("Kiên Giang", 10.0167, 105.0833),
    "phú quốc": ("Phú Quốc", 10.2899, 103.9840),
    "cần thơ": ("Cần Thơ", 10.0452, 105.7469),
    "hậu giang": ("Hậu Giang", 9.7833, 105.4667),
    "sóc trăng": ("Sóc Trăng", 9.6000, 105.9667),
    "bạc liêu": ("Bạc Liêu", 9.2833, 105.7167),
    "cà mau": ("Cà Mau", 9.1833, 105.1500),
}


def _normalise(value: str) -> str:
    return " ".join(value.lower().strip().split())


async def _resolve_point(value: str) -> Tuple[str, float, float]:
    key = _normalise(value)
    point = KNOWN_POINTS.get(key)
    if point:
        return point
    for name, point in KNOWN_POINTS.items():
        if name in key or key in name:
            return point
    db = get_db()
    if db is not None:
        tour = await db.tours.find_one({
            "is_active": True,
            "$or": [
                {"location": {"$regex": re.escape(key), "$options": "i"}},
                {"title": {"$regex": re.escape(key), "$options": "i"}}
            ],
            "lat": {"$ne": None},
            "lng": {"$ne": None}
        })
        if tour and tour.get("lat") and tour.get("lng"):
            return (tour.get("location") or value.title(), float(tour["lat"]), float(tour["lng"]))
    raise HTTPException(status_code=400, detail=f"Chưa có tọa độ cho địa điểm: {value}")


def _distance_km(first: Tuple[float, float], second: Tuple[float, float]) -> float:
    lat1, lng1 = map(math.radians, first)
    lat2, lng2 = map(math.radians, second)
    delta_lat = lat2 - lat1
    delta_lng = lng2 - lng1
    radius = 6371
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    return radius * 2 * math.asin(math.sqrt(value))


def _segment_distance_km(point: Tuple[float, float], start: Tuple[float, float], end: Tuple[float, float]) -> float:
    lat_scale = 111
    lng_scale = 111 * math.cos(math.radians((start[0] + end[0]) / 2))
    px, py = point[0] * lat_scale, point[1] * lng_scale
    ax, ay = start[0] * lat_scale, start[1] * lng_scale
    bx, by = end[0] * lat_scale, end[1] * lng_scale
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    factor = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + factor * dx), py - (ay + factor * dy))


def _build_points(origin: Tuple[str, float, float], destination: Tuple[str, float, float]) -> List[RoutePoint]:
    origin_key = _normalise(origin[0])
    destination_key = _normalise(destination[0])
    middle: List[Tuple[str, float, float]] = []
    if origin_key == "hà nội" and destination_key == "ninh bình":
        middle = [KNOWN_POINTS["phủ lý"]]
    if origin_key == "ninh bình" and destination_key == "hà nội":
        middle = [KNOWN_POINTS["phủ lý"]]
    raw_points = [origin, *middle, destination]
    points: List[RoutePoint] = []
    for index, point in enumerate(raw_points):
        previous = raw_points[index - 1] if index else None
        minutes = round(_distance_km((previous[1], previous[2]), (point[1], point[2])) / 45 * 60) if previous else 0
        points.append(RoutePoint(
            name=point[0], latitude=point[1], longitude=point[2],
            role="origin" if index == 0 else "destination" if index == len(raw_points) - 1 else "stop",
            order=index + 1, estimated_minutes_from_previous=minutes,
        ))
    return points


@router.post("/plan", response_model=RoutePlanResponse)
async def plan_route(request: RoutePlanRequest):
    origin = await _resolve_point(request.origin)
    destination = await _resolve_point(request.destination)
    points = _build_points(origin, destination)
    coordinates = [(point.latitude, point.longitude) for point in points]
    distance = sum(_distance_km(coordinates[index - 1], coordinate) for index, coordinate in enumerate(coordinates) if index)
    db = get_db()
    tours: List[RouteTour] = []
    if db is not None:
        cursor = db.tours.find({"is_active": True})
        async for tour in cursor:
            if tour.get("lat") is None or tour.get("lng") is None:
                continue
            tour_point = min(points, key=lambda point: _distance_km((point.latitude, point.longitude), (tour["lat"], tour["lng"])))
            route_distance = min(
                _segment_distance_km((tour["lat"], tour["lng"]), coordinates[index - 1], coordinates[index])
                for index in range(1, len(coordinates))
            )
            if route_distance <= request.max_tour_distance_km:
                tours.append(RouteTour(
                    tour_id=str(tour["_id"]), title=tour.get("title", "Tour"), location=tour.get("location", ""),
                    price=float(tour.get("discount_price") or tour.get("price") or 0), rating=float(tour.get("rating") or 0),
                    image_url=(tour.get("images") or [None])[0], route_point=tour_point.name,
                    distance_to_route_km=round(route_distance, 1),
                ))
    tours.sort(key=lambda tour: (-tour.rating, tour.distance_to_route_km))
    return RoutePlanResponse(
        origin=origin[0], destination=destination[0], distance_km=round(distance, 1),
        duration_minutes=round(distance / 45 * 60), points=points, tours=tours[:30],
        message=f"Tuyến {origin[0]} → {destination[0]} đi qua {', '.join(point.name for point in points[1:-1]) or 'đường trực tiếp'}.",
    )

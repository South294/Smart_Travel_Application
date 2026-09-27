import math
from typing import Dict, List, Tuple

from fastapi import APIRouter, HTTPException

from app.db.mongodb import get_db
from app.schemas.route import RoutePlanRequest, RoutePlanResponse, RoutePoint, RouteTour

router = APIRouter()

KNOWN_POINTS: Dict[str, Tuple[str, float, float]] = {
    "hà nội": ("Hà Nội", 21.0285, 105.8542),
    "hà nam": ("Hà Nam", 20.5835, 105.9230),
    "phủ lý": ("Phủ Lý", 20.5453, 105.9130),
    "ninh bình": ("Ninh Bình", 20.2506, 105.9740),
    "tam cốc": ("Tam Cốc", 20.2173, 105.9368),
    "tràng an": ("Tràng An", 20.2509, 105.8961),
    "bái đính": ("Bái Đính", 20.2767, 105.8422),
    "nam định": ("Nam Định", 20.4388, 106.1621),
    "hạ long": ("Hạ Long", 20.9101, 107.1839),
    "đà nẵng": ("Đà Nẵng", 16.0544, 108.2022),
    "huế": ("Huế", 16.4637, 107.5909),
    "hội an": ("Hội An", 15.8801, 108.3380),
}


def _normalise(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _point_for(value: str) -> Tuple[str, float, float]:
    key = _normalise(value)
    point = KNOWN_POINTS.get(key)
    if point:
        return point
    for name, point in KNOWN_POINTS.items():
        if name in key or key in name:
            return point
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
    origin = _point_for(request.origin)
    destination = _point_for(request.destination)
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

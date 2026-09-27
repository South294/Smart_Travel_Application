from typing import List, Optional

from pydantic import BaseModel, Field


class RoutePlanRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    travel_date: Optional[str] = Field(default=None, max_length=20)
    adults: int = Field(default=1, ge=1, le=50)
    children: int = Field(default=0, ge=0, le=50)
    max_tour_distance_km: float = Field(default=15, gt=0, le=100)


class RoutePoint(BaseModel):
    name: str
    latitude: float
    longitude: float
    role: str
    order: int
    estimated_minutes_from_previous: int = 0


class RouteTour(BaseModel):
    tour_id: str
    title: str
    location: str
    price: float = 0
    rating: float = 0
    image_url: Optional[str] = None
    route_point: str
    distance_to_route_km: float


class RoutePlanResponse(BaseModel):
    origin: str
    destination: str
    distance_km: float
    duration_minutes: int
    points: List[RoutePoint]
    tours: List[RouteTour]
    message: str

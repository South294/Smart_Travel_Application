from pydantic import BaseModel, Field
from typing import List, Optional

class LocationInfo(BaseModel):
    type: str = "Point"
    coordinates: List[float]

class TourBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1)
    location: str = Field(min_length=1)
    duration_days: int = Field(ge=1)
    duration_nights: int = Field(ge=0)
    price: float = Field(ge=0)
    discount_price: Optional[float] = Field(default=None, ge=0)
    rating: float = Field(default=0.0, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    images: List[str] = []
    tags: List[str] = []
    is_active: bool = True
    lat: Optional[float] = None
    lng: Optional[float] = None
    geo_location: Optional[LocationInfo] = None

class TourCreate(TourBase):
    pass

class TourUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    discount_price: Optional[float] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)

class TourResponse(TourBase):
    id: str

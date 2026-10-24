from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

VALID_PAYMENT_METHODS = ["credit_card", "e_wallet", "bank_transfer", "qr"]

class BookingBase(BaseModel):
    tour_id: str = Field(min_length=1)
    travel_date: str = Field(min_length=1)
    adults: int = Field(ge=1)
    children: int = Field(default=0, ge=0)
    insurance: bool = False
    coupon_code: Optional[str] = None
    payment_method: str = Field(min_length=1)
    contact_phone: str = Field(min_length=1)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    note: Optional[str] = None
    guide_id: Optional[str] = None
    guide_note: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: str
    user_id: str
    status: str
    total_amount: float
    payment_status: str = "unpaid"
    created_at: str
    booking_code: Optional[str] = None
    contract_code: Optional[str] = None
    contract_sent: bool = False
    paid_at: Optional[str] = None
    is_free: bool = False
    tour_title: Optional[str] = None
    tour_location: Optional[str] = None
    tour_lat: Optional[float] = None
    tour_lng: Optional[float] = None
    guide_name: Optional[str] = None
    guide_phone: Optional[str] = None
    guide_experience: Optional[str] = None
    transportation: Optional[str] = None
    trip_type: Optional[str] = None
    route_map_url: Optional[str] = None
    itinerary_details: Optional[List[Dict[str, Any]]] = None

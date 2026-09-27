from pydantic import BaseModel, Field
from typing import Optional

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
    note: Optional[str] = None

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
    paid_at: Optional[str] = None
    is_free: bool = False
    tour_title: Optional[str] = None
    tour_location: Optional[str] = None
    tour_lat: Optional[float] = None
    tour_lng: Optional[float] = None

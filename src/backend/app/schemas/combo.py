from typing import List, Optional

from pydantic import BaseModel, Field


class ComboItem(BaseModel):
    tour_id: str = Field(min_length=1)
    travel_date: str = Field(min_length=1)


class ComboBookingCreate(BaseModel):
    items: List[ComboItem] = Field(min_length=1, max_length=20)
    adults: int = Field(default=1, ge=1)
    children: int = Field(default=0, ge=0)
    insurance: bool = False
    coupon_code: Optional[str] = None
    payment_method: str = Field(min_length=1)
    contact_phone: str = Field(min_length=1)
    note: Optional[str] = None


class ComboBookingResponse(BaseModel):
    id: str
    booking_code: str
    tour_ids: List[str]
    items: List[dict]
    adults: int
    children: int
    total_amount: float
    payment_status: str
    status: str
    payment_method: str
    created_at: str

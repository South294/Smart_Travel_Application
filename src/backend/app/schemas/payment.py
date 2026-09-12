from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    booking_id: str = Field(min_length=1)


class PaymentCreateResponse(BaseModel):
    mode: str
    payment_url: str
    booking_id: str

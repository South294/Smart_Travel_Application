from pydantic import BaseModel, Field
from typing import Optional

class VoucherBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    discount_type: str = Field(min_length=1)
    discount_value: float = Field(gt=0)
    expiry_date: str = Field(min_length=1)
    is_active: bool = True
    max_discount: Optional[float] = Field(default=None, ge=0)

class VoucherCreate(VoucherBase):
    pass

class VoucherResponse(VoucherBase):
    id: str

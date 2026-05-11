from pydantic import BaseModel, Field
from typing import List, Optional

class GuideBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    experience_years: int = Field(ge=0)
    price_per_day: float = Field(ge=0)
    areas: List[str] = Field(min_length=1)
    languages: List[str] = Field(min_length=1)
    bio: str = Field(min_length=1)
    id_front_url: Optional[str] = None
    id_back_url: Optional[str] = None

class GuideCreate(GuideBase):
    pass

class GuideUpdate(BaseModel):
    status: str

class GuideResponse(GuideBase):
    id: str
    user_id: str
    status: str
    created_at: str

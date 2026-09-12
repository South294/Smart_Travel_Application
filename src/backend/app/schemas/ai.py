from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)


class WeatherSnapshot(BaseModel):
    city: str
    condition: str = "unknown"
    temperature: Optional[float] = None
    description: Optional[str] = None


class Recommendation(BaseModel):
    tour_id: str
    title: str
    reason: str
    estimated_price: float = 0
    image_url: Optional[str] = None
    location: str


class ChatResponse(BaseModel):
    message: str
    recommendations: List[Recommendation] = []
    weather: WeatherSnapshot

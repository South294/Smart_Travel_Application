import json
import re
from typing import Any, Dict, List
from time import monotonic

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.db.mongodb import get_db
from app.schemas.ai import ChatRequest, ChatResponse, Recommendation, WeatherSnapshot

router = APIRouter()
_weather_cache: Dict[str, tuple] = {}
_chat_requests: Dict[str, List[float]] = {}
CHAT_LIMIT = 20
CHAT_WINDOW_SECONDS = 60


def _weather_condition(weather: Dict[str, Any]) -> str:
    main = str(weather.get("weather", [{}])[0].get("main", "")).lower()
    temperature = weather.get("main", {}).get("temp")
    if "rain" in main or "drizzle" in main or "thunder" in main:
        return "rain"
    if isinstance(temperature, (int, float)) and temperature >= 32:
        return "hot"
    if isinstance(temperature, (int, float)) and temperature <= 18:
        return "cool"
    if "cloud" in main:
        return "cloudy"
    if "clear" in main:
        return "clear"
    return "unknown"


async def _get_weather(city: str) -> WeatherSnapshot:
    cache_key = city.strip().lower()
    cached = _weather_cache.get(cache_key)
    if cached and monotonic() - cached[0] < 600:
        return cached[1]
    if not settings.OPENWEATHER_API_KEY:
        return WeatherSnapshot(city=city, condition="unknown")

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "vi",
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                f"{settings.OPENWEATHER_BASE_URL}/weather", params=params
            )
        response.raise_for_status()
        data = response.json()
        snapshot = WeatherSnapshot(
            city=data.get("name", city),
            condition=_weather_condition(data),
            temperature=data.get("main", {}).get("temp"),
            description=data.get("weather", [{}])[0].get("description"),
        )
        _weather_cache[cache_key] = (monotonic(), snapshot)
        return snapshot
    except (httpx.HTTPError, ValueError, KeyError):
        return WeatherSnapshot(city=city, condition="unknown")


async def _find_tours(city: str, weather: WeatherSnapshot) -> List[Dict[str, Any]]:
    db = get_db()
    if db is None:
        return []

    query: Dict[str, Any] = {"is_active": True}
    if city:
        query["location"] = {"$regex": re.escape(city), "$options": "i"}

    tours = await db.tours.find(query).sort([("rating", -1), ("review_count", -1)]).to_list(30)
    if not tours and city:
        tours = await db.tours.find({"is_active": True}).sort(
            [("rating", -1), ("review_count", -1)]
        ).to_list(30)

    if weather.condition == "rain":
        indoor_tours = [tour for tour in tours if tour.get("indoor") is True]
        if indoor_tours:
            tours = indoor_tours + [tour for tour in tours if tour not in indoor_tours]

    return tours[:24]


def _tour_context(tours: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "tour_id": str(tour.get("_id")),
            "title": tour.get("title", "Tour"),
            "location": tour.get("location", ""),
            "price": tour.get("discount_price", tour.get("price", 0)),
            "rating": tour.get("rating", 0),
            "tags": tour.get("tags", []),
            "indoor": tour.get("indoor", False),
            "image_url": (tour.get("images") or [None])[0],
        }
        for tour in tours
    ]


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("Gemini returned invalid JSON")
        return json.loads(match.group(0))


async def _ask_gemini(request: ChatRequest, weather: WeatherSnapshot, tours: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Chưa cấu hình GEMINI_API_KEY trong backend/.env")

    prompt = {
        "user_query": request.message,
        "weather": weather.model_dump(),
        "tour_catalog": _tour_context(tours),
        "instructions": [
            "Trả về duy nhất JSON hợp lệ, không markdown.",
            "Chỉ đề xuất tour có tour_id trong tour_catalog.",
            "Không thay đổi giá và không bịa thêm tour.",
            "Nếu thời tiết là rain, ưu tiên tour indoor=true.",
            "Viết câu trả lời bằng tiếng Việt, ngắn gọn và hữu ích.",
            "Chọn tối đa 8 tour phù hợp nhất nếu catalog có đủ dữ liệu.",
        ],
        "output_schema": {
            "message": "string",
            "recommendations": [
                {
                    "tour_id": "string from tour_catalog",
                    "reason": "string",
                }
            ],
        },
    }
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(endpoint, json=payload)
        if response.status_code in (401, 403):
            raise HTTPException(status_code=502, detail="Gemini từ chối API key. Hãy kiểm tra GEMINI_API_KEY.")
        if response.status_code == 404:
            raise HTTPException(status_code=502, detail=f"Gemini không tìm thấy model {settings.GEMINI_MODEL}.")
        if response.status_code == 429:
            raise HTTPException(status_code=502, detail="Gemini đã hết quota hoặc vượt giới hạn request.")
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)
    except HTTPException:
        raise
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Không thể nhận phản hồi hợp lệ từ Gemini") from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    client_key = http_request.client.host if http_request.client else "unknown"
    now = monotonic()
    recent = [timestamp for timestamp in _chat_requests.get(client_key, []) if now - timestamp < CHAT_WINDOW_SECONDS]
    if len(recent) >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail="Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau một phút.")
    recent.append(now)
    _chat_requests[client_key] = recent
    city = request.city.strip() if request.city else ""
    weather = await _get_weather(city or "Hà Nội")
    tours = await _find_tours(city, weather)
    catalog_by_id = {str(tour.get("_id")): tour for tour in tours}
    ai_result = await _ask_gemini(request, weather, tours)

    recommendations = []
    for item in ai_result.get("recommendations", []):
        tour = catalog_by_id.get(str(item.get("tour_id")))
        if not tour:
            continue
        recommendations.append(
            Recommendation(
                tour_id=str(tour["_id"]),
                title=tour.get("title", "Tour"),
                reason=item.get("reason", "Phù hợp với yêu cầu của bạn."),
                estimated_price=tour.get("discount_price", tour.get("price", 0)),
                image_url=(tour.get("images") or [None])[0],
                location=tour.get("location", ""),
            )
        )

    return ChatResponse(
        message=ai_result.get("message", "Mình đã tìm thấy một số lựa chọn phù hợp."),
        recommendations=recommendations,
        weather=weather,
    )

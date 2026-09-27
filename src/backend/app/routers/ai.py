import json
import re
import asyncio
from typing import Any, Dict, List, Optional
from time import monotonic

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from app.core.config import settings
from app.db.mongodb import get_db
from app.schemas.ai import ChatRequest, ChatResponse, ItineraryDay, Recommendation, WeatherSnapshot

router = APIRouter()
_weather_cache: Dict[str, tuple] = {}
_chat_requests: Dict[str, List[float]] = {}
CHAT_LIMIT = 20
CHAT_WINDOW_SECONDS = 60
CHAT_HISTORY_LIMIT = 12
CITY_COORDINATES = {
    "hà nội": (21.0285, 105.8542),
    "đà nẵng": (16.0544, 108.2022),
    "hồ chí minh": (10.8231, 106.6297),
    "nha trang": (12.2388, 109.1967),
    "đà lạt": (11.9404, 108.4583),
    "phú quốc": (10.2899, 103.9840),
    "hạ long": (20.9101, 107.1839),
    "sa pa": (22.3364, 103.8438),
    "sapa": (22.3364, 103.8438),
    "huế": (16.4637, 107.5909),
    "mũi né": (10.9330, 108.2870),
    "quy nhơn": (13.7829, 109.2197),
    "cần thơ": (10.0452, 105.7469),
    "hội an": (15.8801, 108.3380),
    "vũng tàu": (10.4114, 107.1362),
    "tam đảo": (21.4550, 105.6420),
}


def _weather_from_open_meteo(city: str, data: Dict[str, Any]) -> WeatherSnapshot:
    current = data.get("current", {})
    code = current.get("weather_code")
    if code in {0, 1}:
        condition, description = "clear", "Trời quang"
    elif code in {2, 3, 45, 48}:
        condition, description = "cloudy", "Nhiều mây"
    elif code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}:
        condition, description = "rain", "Có mưa"
    elif code in {71, 73, 75, 77}:
        condition, description = "cool", "Trời lạnh"
    else:
        condition, description = "unknown", "Đang cập nhật"
    temperature = current.get("temperature_2m")
    if isinstance(temperature, (int, float)):
        if temperature >= 32:
            condition = "hot"
        elif temperature <= 18 and condition == "unknown":
            condition = "cool"
    return WeatherSnapshot(
        city=city,
        condition=condition,
        temperature=temperature,
        description=description,
    )


def _cached_weather(city: str) -> WeatherSnapshot:
    cached = _weather_cache.get(city.strip().lower())
    return cached[1] if cached else WeatherSnapshot(city=city, condition="unknown")


def _casual_reply(message: str) -> Optional[str]:
    normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", "", message.lower()).strip()
    if re.fullmatch(r"(alo|hello|hi|hey|chào|xin chào|chao|ê|ơi)( bạn| bot| ai)?", normalized):
        return "Chào bạn! Mình là trợ lý SmartTravel. Hôm nay bạn muốn trò chuyện, tìm cảm hứng du lịch hay tìm một tour cụ thể?"
    if any(phrase in normalized for phrase in ["cảm ơn", "cam on", "thanks", "thank you"]):
        return "Rất vui được hỗ trợ bạn. Khi cần tìm điểm đến, tour hoặc lịch trình, cứ nhắn cho mình nhé."
    if any(phrase in normalized for phrase in ["bạn là ai", "ban la ai", "giúp được gì", "giup duoc gi"]):
        return "Mình có thể giúp bạn chọn điểm đến, xem thời tiết, tìm tour theo ngân sách và lên lịch trình phù hợp. Bạn đang muốn đi đâu?"
    if normalized in {"tạm biệt", "tam biet", "bye", "goodbye"}:
        return "Tạm biệt bạn. Chúc bạn có một hành trình thật vui và nhiều kỷ niệm đẹp!"
    return None


def _needs_travel_guidance(message: str) -> bool:
    normalized = message.lower()
    return any(keyword in normalized for keyword in [
        "tour", "du lịch", "du lich", "đi đâu", "di dau", "lịch trình", "lich trinh",
        "ngân sách", "ngan sach", "tham quan", "đặt tour", "dat tour", "kỳ nghỉ", "ky nghi",
    ])


def _is_weather_request(message: str) -> bool:
    normalized = message.lower()
    return "thời tiết" in normalized or "thoi tiet" in normalized or "mưa không" in normalized or "mua khong" in normalized


def _guidance_reply(message: str, city: str, max_budget: Optional[float]) -> Optional[str]:
    if not _needs_travel_guidance(message):
        return None
    if not city and max_budget is None:
        return "Mình rất sẵn lòng giúp bạn lên chuyến đi. Bạn đang muốn khám phá thành phố nào, đi trong bao lâu và dự kiến ngân sách khoảng bao nhiêu?"
    if not city:
        return "Ngân sách của bạn đã rõ rồi. Bạn muốn tìm tour ở thành phố hoặc điểm đến nào?"
    if max_budget is None and any(word in message.lower() for word in ["tour", "đặt", "dat", "ngân sách", "ngan sach"]):
        return f"{city} là một lựa chọn thú vị đấy. Bạn muốn ưu tiên tour tiết kiệm, nghỉ dưỡng hay khám phá? Nếu cho mình biết ngân sách, mình sẽ lọc chính xác hơn."
    return None


def _extract_budget(message: str) -> Optional[float]:
    normalized = message.lower().replace(" ", "")
    match = re.search(r"(?:dưới|duoi|tốiđa|toida|khôngquá|khongqua)\D{0,8}(\d[\d.,]*)\s*(triệu|tr|k|nghìn|nghin)?", normalized)
    if not match:
        return None
    amount_text = match.group(1)
    unit = match.group(2) or ""
    if unit:
        amount = float(amount_text.replace(",", "."))
    elif re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", amount_text):
        amount = float(amount_text.replace(".", "").replace(",", ""))
    else:
        amount = float(amount_text.replace(",", "."))
    if unit in {"triệu", "tr"}:
        amount *= 1_000_000
    elif unit in {"k", "nghìn", "nghin"}:
        amount *= 1_000
    elif amount < 1000:
        amount *= 1_000_000
    return amount


def _extract_city(message: str, requested_city: Optional[str]) -> str:
    if requested_city and requested_city.strip():
        return requested_city.strip()
    known_cities = [
        "Hà Nội", "Đà Nẵng", "Hồ Chí Minh", "Nha Trang", "Đà Lạt",
        "Phú Quốc", "Hạ Long", "Sa Pa", "Sapa", "Huế", "Mũi Né",
        "Quy Nhơn", "Cần Thơ", "Hội An", "Vũng Tàu", "Tam Đảo",
    ]
    lowered = message.lower()
    for city in known_cities:
        if city.lower() in lowered:
            return city
    return ""


async def _load_history(session_id: Optional[str]) -> List[Dict[str, str]]:
    if not session_id:
        return []
    db = get_db()
    if db is None:
        return []
    session = await db.chat_sessions.find_one({"session_id": session_id})
    return session.get("messages", [])[-CHAT_HISTORY_LIMIT:] if session else []


async def _save_history(session_id: Optional[str], user_message: str, assistant_message: str) -> None:
    if not session_id:
        return
    db = get_db()
    if db is None:
        return
    await db.chat_sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": assistant_message},
                    ],
                    "$slice": -CHAT_HISTORY_LIMIT,
                }
            },
            "$set": {"updated_at": monotonic()},
        },
        upsert=True,
    )


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
    coordinates = CITY_COORDINATES.get(cache_key)
    if coordinates:
        params = {
            "latitude": coordinates[0],
            "longitude": coordinates[1],
            "current": "temperature_2m,weather_code",
            "timezone": "Asia/Bangkok",
        }
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            snapshot = _weather_from_open_meteo(city, response.json())
            _weather_cache[cache_key] = (monotonic(), snapshot)
            return snapshot
        except (httpx.HTTPError, ValueError, KeyError):
            return _cached_weather(city)

    if not settings.OPENWEATHER_API_KEY:
        return WeatherSnapshot(city=city, condition="unknown")

    params = {
        "q": city,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "vi",
    }
    try:
        async with httpx.AsyncClient(timeout=3) as client:
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


async def _find_tours(city: str, weather: WeatherSnapshot, max_budget: Optional[float] = None) -> List[Dict[str, Any]]:
    db = get_db()
    if db is None:
        return []

    query: Dict[str, Any] = {"is_active": True}
    if city:
        query["location"] = {"$regex": re.escape(city), "$options": "i"}

    tours = await db.tours.find(query).sort([("rating", -1), ("review_count", -1)]).to_list(30)
    if not tours and city and max_budget is None:
        tours = await db.tours.find({"is_active": True}).sort(
            [("rating", -1), ("review_count", -1)]
        ).to_list(30)

    if max_budget is not None:
        tours = [
            tour for tour in tours
            if float(tour.get("discount_price") or tour.get("price") or 0) <= max_budget
        ]

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
            "outdoor": tour.get("outdoor", True),
            "best_weather": tour.get("best_weather", []),
            "estimated_duration_hours": tour.get("estimated_duration_hours"),
            "difficulty_level": tour.get("difficulty_level"),
            "suitable_for_children": tour.get("suitable_for_children", True),
            "suitable_for_elderly": tour.get("suitable_for_elderly", True),
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


async def _ask_gemini(
    request: ChatRequest,
    weather: WeatherSnapshot,
    tours: List[Dict[str, Any]],
    history: List[Dict[str, str]],
    max_budget: Optional[float],
) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Chưa cấu hình GEMINI_API_KEY trong backend/.env")

    prompt = {
        "user_query": request.message,
        "conversation_history": history,
        "max_budget": max_budget,
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
            "itinerary": [
                {
                    "day": "positive integer",
                    "title": "string",
                    "activities": ["string"],
                }
            ],
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


def _fallback_result(tours: List[Dict[str, Any]], weather: WeatherSnapshot, max_budget: Optional[float]) -> Dict[str, Any]:
    if not tours:
        message = "Mình chưa tìm thấy tour phù hợp với điều kiện hiện tại. Bạn thử nới rộng điểm đến hoặc ngân sách nhé."
    elif max_budget is not None:
        message = f"Mình đã lọc các tour trong ngân sách {max_budget:,.0f}đ. Bạn có thể xem những lựa chọn phù hợp dưới đây."
    else:
        message = "Mình đã lọc những tour nổi bật phù hợp với điểm đến và thời tiết hiện tại."
    return {
        "message": message,
        "itinerary": [],
        "recommendations": [
            {"tour_id": str(tour.get("_id")), "reason": "Được lọc từ dữ liệu tour đang hoạt động."}
            for tour in tours[:8]
        ],
    }


@router.get("/weather", response_model=WeatherSnapshot)
async def weather(city: str = Query("Hà Nội", min_length=1, max_length=100)):
    try:
        return await asyncio.wait_for(_get_weather(city.strip()), timeout=3.5)
    except asyncio.TimeoutError:
        return _cached_weather(city.strip())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    client_key = http_request.client.host if http_request.client else "unknown"
    now = monotonic()
    recent = [timestamp for timestamp in _chat_requests.get(client_key, []) if now - timestamp < CHAT_WINDOW_SECONDS]
    if len(recent) >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail="Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau một phút.")
    recent.append(now)
    _chat_requests[client_key] = recent
    city = _extract_city(request.message, request.city)
    max_budget = _extract_budget(request.message)
    casual_reply = _casual_reply(request.message)
    if casual_reply:
        response = ChatResponse(
            message=casual_reply,
            recommendations=[],
            itinerary=[],
            weather=_cached_weather(city or "Hà Nội"),
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    guidance_reply = _guidance_reply(request.message, city, max_budget)
    if guidance_reply:
        response = ChatResponse(
            message=guidance_reply,
            recommendations=[],
            itinerary=[],
            weather=_cached_weather(city or "Hà Nội"),
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    try:
        weather = await asyncio.wait_for(_get_weather(city or "Hà Nội"), timeout=3.5)
    except asyncio.TimeoutError:
        weather = _cached_weather(city or "Hà Nội")
    if _is_weather_request(request.message):
        weather_text = weather.description or "Mình chưa lấy được dữ liệu thời tiết mới nhất."
        temperature_text = f" Nhiệt độ hiện tại khoảng {round(weather.temperature)}°C." if weather.temperature is not None else ""
        response = ChatResponse(
            message=f"Thời tiết ở {weather.city}: {weather_text}.{temperature_text}",
            recommendations=[],
            itinerary=[],
            weather=weather,
        )
        await _save_history(request.session_id, request.message, response.message)
        return response
    tours = await _find_tours(city, weather, max_budget)
    catalog_by_id = {str(tour.get("_id")): tour for tour in tours}
    history = await _load_history(request.session_id)
    try:
        ai_result = await _ask_gemini(request, weather, tours, history, max_budget)
    except HTTPException:
        ai_result = _fallback_result(tours, weather, max_budget)

    recommendations = []
    raw_recommendations = ai_result.get("recommendations") or []
    for item in raw_recommendations:
        if not isinstance(item, dict):
            continue
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

    itinerary = []
    raw_itinerary = ai_result.get("itinerary") or []
    for item in raw_itinerary:
        if not isinstance(item, dict):
            continue
        try:
            day = int(item.get("day"))
        except (TypeError, ValueError):
            continue
        activities = item.get("activities", [])
        if not isinstance(activities, list):
            activities = [str(activities)]
        itinerary.append(
            ItineraryDay(
                day=max(1, day),
                title=str(item.get("title") or f"Ngày {day}"),
                activities=[str(activity) for activity in activities[:8]],
            )
        )

    response = ChatResponse(
        message=ai_result.get("message", "Mình đã tìm thấy một số lựa chọn phù hợp."),
        recommendations=recommendations,
        itinerary=itinerary[:7],
        weather=weather,
    )
    await _save_history(request.session_id, request.message, response.message)
    return response

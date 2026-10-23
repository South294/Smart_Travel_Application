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
from app.services.ai_knowledge import (
    CITY_HIGHLIGHTS,
    CITY_FOOD_AND_PLAY,
    LOCATION_ALIASES,
    build_google_maps_route_url,
    build_google_maps_search_url,
)
from app.services.weather_service import _get_weather, _cached_weather
from app.services.nlp_service import (
    _casual_reply,
    _coverage_reply,
    _feature_reply,
    _guidance_reply,
    _is_weather_request,
    _extract_budget,
    _extract_city,
    _extract_route,
)


router = APIRouter()
_chat_requests: Dict[str, List[float]] = {}
CHAT_LIMIT = 20
CHAT_WINDOW_SECONDS = 60
CHAT_HISTORY_LIMIT = 12


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




async def _find_tours(city: str, weather: WeatherSnapshot, max_budget: Optional[float] = None) -> List[Dict[str, Any]]:
    db = get_db()
    if db is None:
        return []

    query: Dict[str, Any] = {"is_active": True}
    if city:
        key = city.strip().lower()
        aliases = LOCATION_ALIASES.get(key, [key, city.strip()])
        regex_patterns = [re.escape(alias) for alias in aliases]
        pattern_str = "|".join(regex_patterns)
        query["$or"] = [
            {"location": {"$regex": pattern_str, "$options": "i"}},
            {"title": {"$regex": pattern_str, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": pattern_str, "$options": "i"}}},
            {"description": {"$regex": pattern_str, "$options": "i"}},
        ]

    tours = await db.tours.find(query).sort([("rating", -1), ("review_count", -1)]).to_list(40)

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
    route: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Chưa cấu hình GEMINI_API_KEY trong backend/.env")

    city = route["destination"] if route else _extract_city(request.message, request.city)
    key = city.lower() if city else ""
    city_guide = CITY_HIGHLIGHTS.get(key, {})
    food_and_play = CITY_FOOD_AND_PLAY.get(key, {})

    prompt = {
        "user_query": request.message,
        "destination": city,
        "route": route or {},
        "destination_guide": city_guide,
        "destination_food_and_play": food_and_play,
        "conversation_history": history,
        "max_budget": max_budget,
        "weather": weather.model_dump(),
        "tour_catalog": _tour_context(tours),
        "instructions": [
            "Trả về duy nhất JSON hợp lệ, không markdown.",
            "Trả lời câu hỏi của người dùng thật đầy đủ, nhiệt tình, logic và tuyệt đối chính xác về địa lý Việt Nam.",
            "Tập trung gợi ý các danh lam thắng cảnh nổi bật, điểm check-in hấp dẫn, các món ăn đặc sản truyền thống và danh sách quán ăn ngon nổi tiếng tại địa phương.",
            "Tuyệt đối không vẽ đường đi Google Maps và không sinh lịch trình timeline chi tiết, vì lịch trình chi tiết và phương tiện đưa đón được bảo mật độc quyền cho khách hàng sau khi đặt tour.",
            "Nhắc nhở người dùng nên đặt tour trọn gói trên hệ thống để có hướng dẫn viên chuyên nghiệp đi cùng, được cấp phương tiện ô tô/cano di chuyển và mở khóa toàn bộ lộ trình chi tiết.",
            "Chỉ đề xuất các tour có tour_id nằm trong tour_catalog. Tuyệt đối không bịa đặt tour hoặc id ảo.",
            "Nếu tour_catalog rỗng, để recommendations là mảng rỗng [] và thông báo rõ ràng rằng hiện hệ thống chưa mở bán tour trọn gói trực tiếp tại điểm đến này.",
            "Nếu thời tiết mưa, nhắc người dùng mang ô và ưu tiên các điểm trong nhà.",
            "Viết câu trả lời bằng tiếng Việt hấp dẫn và tự nhiên.",
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


def _fallback_result(
    city: str,
    tours: List[Dict[str, Any]],
    weather: WeatherSnapshot,
    max_budget: Optional[float],
    route: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    key = city.strip().lower() if city else ""
    info = None
    if key:
        info = CITY_HIGHLIGHTS.get(key)
        if not info:
            for k, v in CITY_HIGHLIGHTS.items():
                if k in key or key in k:
                    info = v
                    break

    food_play = CITY_FOOD_AND_PLAY.get(key)
    food_play_section = ""
    if food_play:
        delicacies = ", ".join(food_play.get("delicacies", []))
        restaurants = "\n".join([f"  • {r}" for r in food_play.get("famous_restaurants", [])[:4]])
        entertainment = "\n".join([f"  • {e}" for e in food_play.get("entertainment_spots", [])[:4]])
        food_play_section = (
            f"\n\n🍜 Ẩm thực & Quán ăn ngon tại {city}:\n"
            f"• Món đặc sản nên thử: {delicacies}\n"
            f"• Quán ăn ngon gợi ý:\n{restaurants}\n\n"
            f"🎡 Khu vui chơi & Giải trí nổi bật:\n{entertainment}"
        )

    if info:
        title = info.get("title", f"Khám phá {city}")
        intro = info.get("intro", f"{city} là điểm đến tuyệt vời với cảnh quan thiên nhiên và trải nghiệm đặc sắc.")
        spots = info.get("spots", [])
        spot_lines = "\n".join([f"• {spot}" for spot in spots])

        weather_tip = ""
        if weather.condition == "rain":
            weather_tip = f"\n\nThời tiết hiện tại ở {weather.city} có mưa rải rác ({round(weather.temperature) if weather.temperature is not None else '--'}°C). Bạn nên chuẩn bị theo ô hoặc áo mưa tiện lợi, và ưu tiên ghé thăm các điểm tham quan trong nhà hoặc các quán cà phê ngắm cảnh tuyệt đẹp."
        elif weather.condition == "cool":
            weather_tip = f"\n\nThời tiết hiện tại se lạnh mát mẻ ({round(weather.temperature) if weather.temperature is not None else '--'}°C), vô cùng lý tưởng cho các hoạt động dã ngoại ngoài trời, săn mây và chụp ảnh check-in."
        elif weather.condition in {"clear", "hot"}:
            weather_tip = f"\n\nThời tiết hiện tại nắng ráo trong xanh ({round(weather.temperature) if weather.temperature is not None else '--'}°C), rất thuận lợi cho việc di chuyển khám phá các danh thắng nổi tiếng."

        if tours:
            conclusion = f"\n\n👉 Để xem toàn bộ lộ trình di chuyển chi tiết từng giờ, phương tiện đưa đón chất lượng cao và có hướng dẫn viên chuyên nghiệp đồng hành, bạn hãy bấm 'Xem chi tiết' và Đặt tour ngay bên dưới nhé:"
            recommendations = [
                {
                    "tour_id": str(tour.get("_id")),
                    "reason": f"Tour khám phá {city} nổi bật, đánh giá {tour.get('rating', 4.9)}⭐ với dịch vụ trọn gói chu đáo.",
                }
                for tour in tours[:6]
            ]
        else:
            conclusion = f"\n\nHiện tại hệ thống SmartTravel đang chuẩn bị mở bán thêm các tour trọn gói mới tại {city}. Bạn có thể lưu lại các danh lam thắng cảnh và địa chỉ quán ăn ngon trên để lên kế hoạch khám phá nhé!"
            recommendations = []

        message = f"🌟 {title}\n\n{intro}\n\n{spot_lines}{food_play_section}{weather_tip}{conclusion}"
        return {
            "message": message,
            "itinerary": [],
            "recommendations": recommendations,
            "map_url": None,
        }


    if city and not tours:
        return {
            "message": f"🌟 Khám phá {city}\n\n{city} là điểm đến mang nhiều nét đẹp thiên nhiên và văn hóa đặc trưng. Hiện tại hệ thống SmartTravel chưa mở bán tour trọn gói tại {city}, nhưng bạn hoàn toàn có thể tự túc lên kế hoạch khám phá các danh lam thắng cảnh và ẩm thực địa phương đặc sắc nơi đây.",
            "itinerary": [],
            "recommendations": [],
        }

    if tours and not city:
        if max_budget is not None:
            message = f"Dựa trên ngân sách tối ưu {max_budget:,.0f}đ của bạn, SmartTravel xin chọn lọc các tour du lịch chất lượng cao có sẵn trên hệ thống:"
        else:
            message = "Chào bạn! Dưới đây là các tour du lịch được đánh giá cao nhất đang có trên hệ thống SmartTravel. Bạn có thể bấm xem chi tiết từng tour hoặc đặt vé trực tiếp:"
        return {
            "message": message,
            "itinerary": [],
            "recommendations": [
                {
                    "tour_id": str(tour.get("_id")),
                    "reason": f"Tour du lịch {tour.get('location', '')} nổi bật, đánh giá {tour.get('rating', 4.8)} sao.",
                }
                for tour in tours[:6]
            ],
        }

    return {
        "message": "SmartTravel luôn sẵn sàng đồng hành cùng bạn trên khắp 63 tỉnh thành Việt Nam! Bạn có thể cho mình biết điểm đến mong muốn (ví dụ: Đà Lạt, Sa Pa, Hà Giang, Phú Thọ, Nha Trang, Phú Quốc...) hoặc khoảng ngân sách để mình hỗ trợ chu đáo nhất nhé.",
        "itinerary": [],
        "recommendations": [],
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

    route = _extract_route(request.message, request.city)
    city = route["destination"] if route else _extract_city(request.message, request.city)
    max_budget = _extract_budget(request.message)

    coverage_reply = _coverage_reply(request.message)
    if coverage_reply:
        weather_snapshot = _cached_weather("Hà Nội")
        tours = await _find_tours("", weather_snapshot, None)
        recommendations = [
            Recommendation(
                tour_id=str(tour["_id"]),
                title=tour.get("title", "Tour"),
                reason=f"Tour du lịch {tour.get('location', '')} chất lượng cao, đánh giá {tour.get('rating', 4.9)}⭐.",
                estimated_price=tour.get("discount_price", tour.get("price", 0)),
                image_url=(tour.get("images") or [None])[0],
                location=tour.get("location", ""),
            )
            for tour in tours[:6]
        ]
        response = ChatResponse(
            message=coverage_reply,
            recommendations=recommendations,
            itinerary=[],
            weather=weather_snapshot,
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    feature_reply = _feature_reply(request.message)
    if feature_reply:
        response = ChatResponse(
            message=feature_reply,
            recommendations=[],
            itinerary=[],
            weather=_cached_weather(city or "Hà Nội"),
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

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
        weather_snapshot = await asyncio.wait_for(_get_weather(city or "Hà Nội"), timeout=3.5)
    except asyncio.TimeoutError:
        weather_snapshot = _cached_weather(city or "Hà Nội")

    if _is_weather_request(request.message):
        weather_text = weather_snapshot.description or "Mình chưa lấy được dữ liệu thời tiết mới nhất."
        temperature_text = f" Nhiệt độ hiện tại khoảng {round(weather_snapshot.temperature)}°C." if weather_snapshot.temperature is not None else ""
        response = ChatResponse(
            message=f"Thời tiết ở {weather_snapshot.city}: {weather_text}.{temperature_text}",
            recommendations=[],
            itinerary=[],
            weather=weather_snapshot,
        )
        await _save_history(request.session_id, request.message, response.message)
        return response

    if route and route.get("origin") and route.get("destination"):
        origin_tours = await _find_tours(route["origin"], weather_snapshot, max_budget)
        dest_tours = await _find_tours(route["destination"], weather_snapshot, max_budget)
        combined_tours = []
        seen_ids = set()
        for tour in origin_tours[:2] + dest_tours[:4]:
            tid = str(tour.get("_id"))
            if tid not in seen_ids:
                seen_ids.add(tid)
                combined_tours.append(tour)
        tours = combined_tours or dest_tours
    else:
        tours = await _find_tours(city, weather_snapshot, max_budget)
    catalog_by_id = {str(tour.get("_id")): tour for tour in tours}
    history = await _load_history(request.session_id)

    ai_result = None
    if settings.GEMINI_API_KEY:
        try:
            ai_result = await _ask_gemini(request, weather_snapshot, tours, history, max_budget, route)
        except Exception:
            ai_result = None

    if not ai_result:
        ai_result = _fallback_result(city, tours, weather_snapshot, max_budget, route)

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

    response = ChatResponse(
        message=ai_result.get("message", "Mình đã tìm thấy một số lựa chọn phù hợp."),
        recommendations=recommendations,
        itinerary=[],
        weather=weather_snapshot,
        map_url=None,
    )
    await _save_history(request.session_id, request.message, response.message)
    return response


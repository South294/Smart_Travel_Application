import re
import json
from typing import Any, Dict, List, Optional, Tuple
import httpx
from app.core.config import settings
from app.services.ai_knowledge import (
    CITY_HIGHLIGHTS,
    CITY_FOOD_AND_PLAY,
    CITY_COORDINATES,
    LOCATION_ALIASES,
    build_google_maps_route_url,
)

KNOWN_CITIES = {
    "phú quốc": ("Phú Quốc", "TP. Hồ Chí Minh"),
    "sa pa": ("Sa Pa", "Hà Nội"),
    "sapa": ("Sa Pa", "Hà Nội"),
    "hà giang": ("Hà Giang", "Hà Nội"),
    "hạ long": ("Hạ Long", "Hà Nội"),
    "nha trang": ("Nha Trang", "TP. Hồ Chí Minh"),
    "đà lạt": ("Đà Lạt", "TP. Hồ Chí Minh"),
    "mộc châu": ("Mộc Châu", "Hà Nội"),
    "tam đảo": ("Tam Đảo", "Hà Nội"),
    "ninh bình": ("Ninh Bình", "Hà Nội"),
    "hà nội": ("Hà Nội", "Nhà hát Lớn Hà Nội"),
    "hồ chí minh": ("TP. Hồ Chí Minh", "Chợ Bến Thành"),
    "đà nẵng": ("Đà Nẵng", "Sân bay Đà Nẵng"),
    "hội an": ("Hội An", "Đà Nẵng"),
    "huế": ("Huế", "Đà Nẵng"),
    "vũng tàu": ("Vũng Tàu", "TP. Hồ Chí Minh"),
    "cần thơ": ("Cần Thơ", "TP. Hồ Chí Minh"),
    "quy nhơn": ("Quy Nhơn", "TP. Hồ Chí Minh"),
    "phú yên": ("Phú Yên", "TP. Hồ Chí Minh"),
    "mũi né": ("Mũi Né", "TP. Hồ Chí Minh"),
    "phan thiết": ("Phan Thiết", "TP. Hồ Chí Minh"),
    "mai châu": ("Mai Châu", "Hà Nội"),
    "cao bằng": ("Cao Bằng", "Hà Nội"),
    "phú thọ": ("Phú Thọ", "Hà Nội"),
    "quảng bình": ("Quảng Bình", "Hà Nội"),
}

def resolve_city_name(text: str) -> str:
    cleaned = (text or "").strip().lower()
    for alias_key, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            if alias in cleaned:
                for k, v in KNOWN_CITIES.items():
                    if k in alias_key or alias_key in k:
                        return v[0]
                return alias_key.title()
    for k, v in KNOWN_CITIES.items():
        if k in cleaned:
            return v[0]
    return text.strip() if text else "Điểm đến trải nghiệm"

def get_city_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    cleaned = city_name.strip().lower()
    for k, coords in CITY_COORDINATES.items():
        if k in cleaned or cleaned in k:
            return coords
    for alias_key, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            if alias in cleaned:
                if alias_key in CITY_COORDINATES:
                    return CITY_COORDINATES[alias_key]
    return None

def sort_destinations_geographically(destinations: List[str]) -> List[str]:
    unique_dests = []
    seen = set()
    for d in destinations:
        resolved = resolve_city_name(d)
        if resolved and resolved not in seen:
            seen.add(resolved)
            unique_dests.append(resolved)

    if len(unique_dests) <= 1:
        return unique_dests

    with_coords = []
    without_coords = []
    for d in unique_dests:
        coords = get_city_coordinates(d)
        if coords:
            with_coords.append((d, coords[0], coords[1]))
        else:
            without_coords.append(d)

    if with_coords:
        with_coords.sort(key=lambda x: x[1], reverse=True)
        sorted_dests = [item[0] for item in with_coords]
        sorted_dests.extend(without_coords)
        return sorted_dests

    return unique_dests

def get_city_data(city_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    cleaned = city_name.strip().lower()
    matched_highlights = {}
    matched_food = {}
    for k, v in CITY_HIGHLIGHTS.items():
        if k in cleaned or cleaned in k:
            matched_highlights = v
            break
    for k, v in CITY_FOOD_AND_PLAY.items():
        if k in cleaned or cleaned in k:
            matched_food = v
            break
    return matched_highlights, matched_food

def get_transportation_text(destinations: List[str], title: str) -> str:
    combined = " ".join(destinations).lower() + " " + (title or "").lower()
    if any(k in combined for k in ["biển", "đảo", "vịnh", "phú quốc", "nha trang", "hạ long", "côn đảo"]):
        return "Xe ô tô du lịch điều hòa cao cấp đón trả + Cano cao tốc / Thuyền du lịch chuyên dụng đạt chuẩn an toàn"
    if any(k in combined for k in ["hà giang", "trekking", "phượt", "đèo", "fansipan", "núi", "sapa", "mộc châu"]):
        return "Xe Limousine chất lượng cao đưa đón hai chiều + Phương tiện chuyên dụng cho cung đường đồi núi"
    return "Xe du lịch đời mới chất lượng cao trang bị máy lạnh, wifi, nước suối và khăn lạnh suốt hành trình"

def synthesize_detailed_itinerary(
    tour_title: str,
    destinations: Any,
    duration_days: int = 1,
    guide_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    days_count = max(1, int(duration_days) if duration_days else 1)
    actual_guide = guide_name if guide_name else "Vũ Văn Sơn (HDV SmartTravel)"
    if isinstance(destinations, str):
        dests = [resolve_city_name(destinations)]
    elif isinstance(destinations, list) and len(destinations) > 0:
        dests = [resolve_city_name(d) for d in destinations if d]
    else:
        dests = ["Hà Nội"]
    if not dests:
        dests = ["Hà Nội"]
    itinerary_details = []

    for day_idx in range(1, days_count + 1):
        target_city = dests[(day_idx - 1) % len(dests)]
        highlights, food = get_city_data(target_city)

        spots = highlights.get("spots", [])
        delicacies = food.get("delicacies", [])
        restaurants = food.get("famous_restaurants", [])
        entertainments = food.get("entertainment_spots", [])

        spot_morning = spots[0] if len(spots) > 0 else f"Danh thắng văn hóa {target_city}"
        spot_afternoon = spots[1] if len(spots) > 1 else f"Khu du lịch sinh thái {target_city}"
        spot_sunset = spots[2] if len(spots) > 2 else f"Điểm ngắm hoàng hôn và check-in {target_city}"

        lunch_delicacy = ", ".join(delicacies[:2]) if len(delicacies) >= 2 else (delicacies[0] if delicacies else f"Đặc sản truyền thống {target_city}")
        dinner_delicacy = ", ".join(delicacies[2:4]) if len(delicacies) >= 4 else (delicacies[1] if len(delicacies) > 1 else lunch_delicacy)

        lunch_restaurant = restaurants[0] if len(restaurants) > 0 else f"Nhà hàng ẩm thực bản địa {target_city}"
        dinner_restaurant = restaurants[1] if len(restaurants) > 1 else f"Nhà hàng đặc sản truyền thống {target_city}"

        fun_activity = entertainments[0] if len(entertainments) > 0 else f"Khám phá cảnh sắc văn hóa {target_city}"

        timeline = []
        if day_idx == 1:
            timeline.append({
                "time": "07:30 - 08:30",
                "type": "departure",
                "activity": f"Tập trung và khởi hành. Hướng dẫn viên {actual_guide} đón đoàn, phổ biến lịch trình chi tiết và cung cấp nước uống tinh khiết.",
                "location": f"Điểm đón trung tâm - Khởi hành đi {target_city}",
                "delicacy": "Điểm tâm sáng nhẹ trên hành trình"
            })
            timeline.append({
                "time": "09:00 - 11:30",
                "type": "sightseeing",
                "activity": f"Đến {target_city}. Hướng dẫn viên đưa đoàn tham quan danh thắng biểu tượng: {spot_morning}. Check-in chụp ảnh và tìm hiểu nét đẹp lịch sử văn hóa.",
                "location": spot_morning,
                "delicacy": None
            })
        else:
            timeline.append({
                "time": "07:30 - 08:30",
                "type": "dining",
                "activity": f"Bắt đầu ngày mới tại {target_city}. Thưởng thức bữa sáng phong vị địa phương và nhâm nhi cà phê sáng.",
                "location": f"Khách sạn / Điểm tâm sáng {target_city}",
                "delicacy": delicacies[0] if delicacies else f"Điểm tâm sáng đặc sản {target_city}"
            })
            timeline.append({
                "time": "09:00 - 11:30",
                "type": "sightseeing",
                "activity": f"Hành trình khám phá trọng điểm: {spot_morning}. Nghe HDV {actual_guide} thuyết minh các câu chuyện văn hóa và lịch sử hào hùng.",
                "location": spot_morning,
                "delicacy": None
            })

        timeline.append({
            "time": "11:30 - 13:00",
            "type": "dining",
            "activity": f"Thưởng thức bữa trưa đậm đà phong vị tại {lunch_restaurant}. Thực đơn nổi bật với món đặc sản trứ danh: {lunch_delicacy}. Quý khách nghỉ ngơi tại chỗ.",
            "location": lunch_restaurant,
            "delicacy": lunch_delicacy
        })

        timeline.append({
            "time": "13:30 - 16:30",
            "type": "sightseeing",
            "activity": f"Buổi chiều tiếp tục trải nghiệm tại {spot_afternoon}. Khám phá hoạt động nổi bật: {fun_activity}.",
            "location": spot_afternoon,
            "delicacy": None
        })

        timeline.append({
            "time": "17:00 - 18:30",
            "type": "sightseeing",
            "activity": f"Ghé thăm {spot_sunset}. Tận hưởng không gian lộng gió, ngắm hoàng hôn tuyệt đẹp và tự do chọn mua đặc sản chính gốc làm quà cho gia đình.",
            "location": spot_sunset,
            "delicacy": None
        })

        timeline.append({
            "time": "18:30 - 20:00",
            "type": "dining",
            "activity": f"Bữa tối ấm cúng tại {dinner_restaurant}. Thưởng thức thực đơn đặc sản tinh hoa: {dinner_delicacy}.",
            "location": dinner_restaurant,
            "delicacy": dinner_delicacy
        })

        if day_idx == days_count:
            timeline.append({
                "time": "20:00 - 21:30",
                "type": "return",
                "activity": f"Xe du lịch và HDV {actual_guide} đưa quý khách trở về điểm hẹn ban đầu. Kết thúc chuyến du lịch trọn vẹn và an toàn.",
                "location": f"Trở về điểm đón - Kết thúc hành trình {tour_title}",
                "delicacy": None
            })
        else:
            timeline.append({
                "time": "20:00 - 22:00",
                "type": "sightseeing",
                "activity": f"Tự do khám phá phố đêm lung linh tại {target_city}, dạo chợ đêm hoặc nghỉ ngơi thư giãn tại khách sạn.",
                "location": f"Trung tâm phố đêm {target_city}",
                "delicacy": None
            })

        day_title = f"Ngày {day_idx}: Khám phá danh thắng & ẩm thực đặc sản {target_city}"
        itinerary_details.append({
            "day": day_idx,
            "title": day_title,
            "location": target_city,
            "food": {
                "dishes": delicacies,
                "restaurants": restaurants,
                "lunch": lunch_delicacy,
                "dinner": dinner_delicacy
            },
            "timeline": timeline
        })

    return itinerary_details

async def ask_gemini_itinerary(
    tour_title: str,
    destinations: List[str],
    duration_days: int = 1,
    guide_name: str = "Vũ Văn Sơn (HDV SmartTravel)",
) -> Optional[List[Dict[str, Any]]]:
    if not settings.GEMINI_API_KEY:
        return None

    prompt_data = {
        "tour_title": tour_title,
        "destinations": destinations,
        "duration_days": duration_days,
        "guide_name": guide_name,
        "instructions": [
            "Trả về JSON là mảng các ngày (mỗi ngày có: day, title, location, timeline).",
            "Mỗi mục trong timeline gồm: time, type (departure, sightseeing, dining, transit, return), activity, location, delicacy.",
            "Tập trung nêu thật chi tiết: đi địa danh cụ thể nào, ăn món đặc sản truyền thống nào và ăn tại quán/nhà hàng nổi tiếng nào của địa phương đó.",
            "Không markdown, trả về JSON mảng hợp lệ."
        ]
    }

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": json.dumps(prompt_data, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(endpoint, json=payload)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
    except Exception:
        pass

    return None

async def build_tour_itinerary(
    tour_title: str,
    locations: List[str],
    duration_days: int = 1,
    guide_name: str = "Vũ Văn Sơn (HDV SmartTravel)",
    is_combo: bool = False,
) -> Dict[str, Any]:
    sorted_dests = sort_destinations_geographically(locations) if is_combo else [resolve_city_name(l) for l in locations if l]
    if not sorted_dests:
        sorted_dests = ["Hà Nội"]

    primary_destination = sorted_dests[0]
    matched_city = None
    for k, v in KNOWN_CITIES.items():
        if k in primary_destination.lower():
            matched_city = v
            break

    if matched_city:
        destination = matched_city[0]
        origin = matched_city[1]
        trip_type = "single_destination" if destination in ("Hà Nội", "TP. Hồ Chí Minh") and len(sorted_dests) == 1 else "inter_provincial"
    else:
        destination = primary_destination
        origin = "Điểm hẹn trung tâm"
        trip_type = "single_destination" if len(sorted_dests) == 1 else "inter_provincial"

    transportation = get_transportation_text(sorted_dests, tour_title)

    itinerary_details = None
    if settings.GEMINI_API_KEY:
        try:
            itinerary_details = await ask_gemini_itinerary(
                tour_title=tour_title,
                destinations=sorted_dests,
                duration_days=duration_days,
                guide_name=guide_name,
            )
        except Exception:
            itinerary_details = None

    if not itinerary_details:
        itinerary_details = synthesize_detailed_itinerary(
            tour_title=tour_title,
            destinations=sorted_dests,
            duration_days=duration_days,
            guide_name=guide_name,
        )

    waypoints = sorted_dests[1:] if len(sorted_dests) > 1 else None
    route_map_url = build_google_maps_route_url(origin=origin, destination=sorted_dests[-1], waypoints=waypoints)

    return {
        "trip_type": trip_type,
        "transportation": transportation,
        "itinerary_details": itinerary_details,
        "route_map_url": route_map_url,
        "sorted_destinations": sorted_dests,
    }

def generate_tour_itinerary_sync(
    title: str,
    location: str,
    duration_days: int = 1,
    guide_name: str = "Vũ Văn Sơn (HDV SmartTravel)",
) -> Dict[str, Any]:
    dest = resolve_city_name(location) or resolve_city_name(title)
    itinerary_details = synthesize_detailed_itinerary(
        tour_title=title,
        destinations=[dest],
        duration_days=duration_days,
        guide_name=guide_name,
    )
    transportation = get_transportation_text([dest], title)
    matched_city = None
    for k, v in KNOWN_CITIES.items():
        if k in dest.lower():
            matched_city = v
            break
    origin = matched_city[1] if matched_city else "Điểm hẹn trung tâm"
    trip_type = "single_destination" if dest in ("Hà Nội", "TP. Hồ Chí Minh") else "inter_provincial"
    route_map_url = build_google_maps_route_url(origin=origin, destination=dest)

    return {
        "trip_type": trip_type,
        "transportation": transportation,
        "itinerary_details": itinerary_details,
        "route_map_url": route_map_url,
    }

from typing import Any, Dict, Optional
from time import monotonic
import httpx
from app.core.config import settings
from app.schemas.ai import WeatherSnapshot
from app.services.ai_knowledge import CITY_COORDINATES

_weather_cache: Dict[str, tuple] = {}

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
    if not coordinates:
        for k, coords in CITY_COORDINATES.items():
            if k in cache_key or cache_key in k:
                coordinates = coords
                break
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



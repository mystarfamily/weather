import httpx
import typer

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def get_location(city: str) -> dict:
    """通过城市名获取经纬度"""
    logger.debug(f"查询城市位置：{city}")
    response = httpx.get(
        settings.geocoding_url,
        params={
            "name": city,
            "count": 1,
            "language": settings.request_language,
        },
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("results"):
        logger.warning(f"找不到城市：{city}")
        raise typer.BadParameter(f"找不到城市：{city}，请检查城市名称")
    location = data["results"][0]
    logger.debug(f"找到城市：{location['name']}, {location.get('country', '')}")
    return location


def get_weather(lat: float, lon: float) -> dict:
    """通过经纬度获取天气"""
    logger.debug(f"查询天气：lat={lat}, lon={lon}")
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
    }
    response = httpx.get(
        settings.weather_url,
        params=params,
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    logger.debug("天气数据获取成功")
    return response.json()


WEATHER_CODES = {
    0: "晴天",
    1: "晴间多云",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "冻雾",
    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "小阵雨",
    81: "中阵雨",
    82: "大阵雨",
    95: "雷阵雨",
}


def parse_weather(location: dict, data: dict) -> dict:
    current = data["current"]
    code = current["weather_code"]
    return {
        "city": location["name"],
        "country": location.get("country", ""),
        "temp_c": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "description": WEATHER_CODES.get(code, "未知"),
        "wind_speed": current["wind_speed_10m"],
    }

from __future__ import annotations

import time
from typing import Any, List, Tuple

import httpx

from .config import settings
from .logging import get_logger
from .models import ForecastDay, WeatherReport

# 简单内存缓存：{ cache_key: (timestamp, WeatherReport) }
_cache: dict[str, tuple[float, WeatherReport]] = {}

CACHE_TTL = 600  # 缓存 10 分钟（单位：秒）

logger = get_logger(__name__)

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """获取全局 AsyncClient 实例"""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.request_timeout,
        )
        logger.debug("创建全局 AsyncClient 实例")
    return _client


async def close_client() -> None:
    """关闭全局 AsyncClient"""
    global _client
    if _client is not None:
        await _client.aclose()
        logger.debug("关闭全局 AsyncClient 实例")
        _client = None


async def _api_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """统一封装 API GET 请求"""
    client = get_client()
    resp = await client.get(path, params={**params, "key": settings.qweather_key})
    resp.raise_for_status()

    data: dict[str, Any] = resp.json()
    if str(data.get("code")) != "200":
        logger.error(f"接口错误码: {data.get('code')}")
        raise RuntimeError(f"接口错误码: {data.get('code')}")
    return data


async def lookup_city(location: str) -> Tuple[str, str]:
    """查询城市名称与 ID"""
    logger.info(f"查询城市: {location}")
    data = await _api_get("/geo/v2/city/lookup", {"location": location})

    locations: List[dict[str, Any]] = data.get("location", [])
    if not locations:
        raise RuntimeError("未找到匹配的城市")

    loc = locations[0]
    city_name: str = loc["name"]
    city_id: str = loc["id"]

    logger.debug(f"匹配城市: {city_name} ({city_id})")
    return city_name, city_id


async def get_location(location: str | None = None) -> dict[str, Any]:
    """
    解析并返回 location 信息字典
    """
    if not location:
        logger.debug("get_location: 使用 auto:ip 自动定位")
        city_name, city_id = await lookup_city("auto:ip")
        return {"city": city_name, "id": city_id}

    # 尝试解析经纬度
    try:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) == 2:
            lat = float(parts[0])
            lon = float(parts[1])
            loc_str = f"{lon},{lat}"
            logger.debug("get_location: 解析到经纬度 %s,%s", lat, lon)
            city_name, city_id = await lookup_city(loc_str)
            return {"city": city_name, "id": city_id, "lat": lat, "lon": lon}
    except Exception:
        logger.debug("get_location: 传入字符串不是经纬度，按城市名处理")

    # 按城市名查询
    city_name, city_id = await lookup_city(location)
    return {"city": city_name, "id": city_id}


def get_from_cache(key: str) -> WeatherReport | None:
    """从缓存读取"""
    entry = _cache.get(key)
    if not entry:
        return None

    ts, data = entry
    if time.time() - ts > CACHE_TTL:
        _cache.pop(key, None)
        return None

    logger.info(f"缓存命中: {key}")
    return data


def save_to_cache(key: str, data: WeatherReport) -> None:
    """写入缓存"""
    _cache[key] = (time.time(), data)
    logger.debug(f"缓存写入: {key}")


async def get_weather(location: str | dict[str, Any] | None = None) -> WeatherReport:
    """获取天气预报"""
    logger.info(f"获取天气: location={location}")

    loc_id: str | None = None
    city_name: str | None = None

    if isinstance(location, dict):
        loc_id = location.get("id")
        city_name = location.get("city")

    if not location:
        cache_key = "auto:ip"
        city_name, location_id = await lookup_city("auto:ip")
    else:
        if isinstance(location, dict) and loc_id:
            cache_key = f"id:{loc_id}"
            location_id = loc_id
            city_name = city_name or "未知"
        else:
            if isinstance(location, dict) and city_name:
                lookup_input: str = city_name
            else:
                lookup_input = str(location)
            cache_key = lookup_input
            city_name, location_id = await lookup_city(lookup_input)

    cached = get_from_cache(cache_key)
    if cached:
        logger.success(f"使用缓存数据: {cached.city}")
        return cached

    data = await _api_get("/v7/weather/7d", {"location": location_id, "lang": "zh"})

    daily_list: List[dict[str, Any]] = data["daily"]

    forecast: List[ForecastDay] = [
        ForecastDay(
            date=day["fxDate"],
            day_text=day["textDay"],
            night_text=day["textNight"],
            temp_max=day["tempMax"],
            temp_min=day["tempMin"],
            humidity=day["humidity"],
            wind_dir=day["windDirDay"],
            wind_speed=day["windSpeedDay"],
        )
        for day in daily_list
    ]

    report = WeatherReport(city=city_name, forecast=forecast)

    save_to_cache(cache_key, report)

    logger.success(f"成功获取 {city_name} 的 7 天预报")
    return report

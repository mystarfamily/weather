# src/app/api.py
from typing import Tuple

import httpx

from .config import settings
from .logging import get_logger
from .models import ForecastDay, WeatherReport

import time

# 简单内存缓存：{ cache_key: (timestamp, WeatherReport) }
_cache: dict[str, tuple[float, WeatherReport]] = {}

CACHE_TTL = 600  # 缓存 10 分钟（单位：秒）

logger = get_logger(__name__)

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.request_timeout,
        )
        logger.debug("创建全局 AsyncClient 实例")
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        logger.debug("关闭全局 AsyncClient 实例")
        _client = None


async def _api_get(path: str, params: dict) -> dict:
    client = get_client()
    resp = await client.get(path, params={**params, "key": settings.qweather_key})
    resp.raise_for_status()
    data = resp.json()
    if str(data.get("code")) != "200":
        logger.error(f"接口错误码: {data.get('code')}")
        raise RuntimeError(f"接口错误码: {data.get('code')}")
    return data


async def lookup_city(location: str) -> Tuple[str, str]:
    logger.info(f"查询城市: {location}")
    data = await _api_get("/geo/v2/city/lookup", {"location": location})
    if not data.get("location"):
        raise RuntimeError("未找到匹配的城市")
    loc = data["location"][0]
    city_name, city_id = loc["name"], loc["id"]
    logger.debug(f"匹配城市: {city_name} ({city_id})")
    return city_name, city_id
    # 在 lookup_city 之后添加


async def get_location(location: str | None = None) -> dict:
    """
    解析并返回 location 信息字典，结构示例：
    {
        "city": "上海",
        "id": "101020100",
        "lat": 31.23,        # 若可用则包含
        "lon": 121.47        # 若可用则包含
    }

    - location is None: 使用 "auto:ip" 自动定位
    - location is a string: 传入 city 名称或 "lat,lon" 字符串
    """
    # 使用自动定位
    if not location:
        logger.debug("get_location: 使用 auto:ip 自动定位")
        city_name, city_id = await lookup_city("auto:ip")
        return {"city": city_name, "id": city_id}

    # 如果传入的是经纬度 "lat,lon"，直接传给 lookup_city（和风支持）
    # 否则当作城市名查询
    try:
        # 简单判断是否为经纬度格式 "lat,lon"
        parts = [p.strip() for p in location.split(",")]
        if len(parts) == 2:
            # 尝试把两部分转换为 float，若成功则视为经纬度
            lat = float(parts[0])
            lon = float(parts[1])
            loc_str = f"{lon},{lat}"  # 和风的 location 通常是 "lon,lat" 或直接 "lat,lon" 均可尝试
            logger.debug("get_location: 解析到经纬度 %s,%s", lat, lon)
            city_name, city_id = await lookup_city(loc_str)
            return {"city": city_name, "id": city_id, "lat": lat, "lon": lon}
    except Exception:
        # 解析失败则继续按城市名处理
        logger.debug("get_location: 传入字符串不是经纬度，按城市名处理")

    # 按城市名查询
    city_name, city_id = await lookup_city(location)
    return {"city": city_name, "id": city_id}


def get_from_cache(key: str) -> WeatherReport | None:
    entry = _cache.get(key)
    if not entry:
        return None

    ts, data = entry
    if time.time() - ts > CACHE_TTL:
        # 缓存过期
        _cache.pop(key, None)
        return None

    logger.info(f"缓存命中: {key}")
    return data


def save_to_cache(key: str, data: WeatherReport):
    _cache[key] = (time.time(), data)
    logger.debug(f"缓存写入: {key}")


async def get_weather(location: str | dict | None = None) -> WeatherReport:
    logger.info(f"获取天气: location={location}")

    # 规范化 location，支持 None / str / dict
    # 如果传入 dict，尝试从中取 id 或 city
    if isinstance(location, dict):
        loc_id = location.get("id")
        city_name = location.get("city")
    else:
        loc_id = None
        city_name = None

    # 自动定位或解析字符串输入
    if not location:
        cache_key = "auto:ip"
        city_name, location_id = await lookup_city("auto:ip")
    else:
        # 如果传入的是 dict 且包含 id，则直接使用
        if isinstance(location, dict) and loc_id:
            cache_key = f"id:{loc_id}"
            location_id = loc_id
            city_name = city_name or "未知"
        else:
            # 如果传入 dict 但没有 id，尝试用 city 字段
            if isinstance(location, dict) and city_name:
                lookup_input = city_name
            else:
                # 传入的是字符串（城市名或经纬度）
                lookup_input = location  # type: ignore
            cache_key = str(lookup_input)
            city_name, location_id = await lookup_city(lookup_input)

    # 先查缓存（cache_key 必须是可哈希的字符串）
    cached = get_from_cache(cache_key)
    if cached:
        logger.success(f"使用缓存数据: {cached.city}")
        return cached

    # 请求 API（使用 location_id）
    data = await _api_get("/v7/weather/7d", {"location": location_id, "lang": "zh"})

    forecast = [
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
        for day in data["daily"]
    ]

    report = WeatherReport(city=city_name, forecast=forecast)

    # 写入缓存
    save_to_cache(cache_key, report)

    logger.success(f"成功获取 {city_name} 的 7 天预报")
    return report

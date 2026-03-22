import pytest
import respx
import httpx

from app.api import get_location, get_weather, parse_weather


MOCK_LOCATION_RESPONSE = {
    "results": [
        {
            "name": "上海",
            "country": "中国",
            "latitude": 31.22222,
            "longitude": 121.45806,
        }
    ]
}

MOCK_WEATHER_RESPONSE = {
    "current": {
        "temperature_2m": 20.0,
        "apparent_temperature": 19.5,
        "relative_humidity_2m": 60,
        "weather_code": 2,
        "wind_speed_10m": 10.0,
    }
}


@respx.mock
def test_get_location_success():
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json=MOCK_LOCATION_RESPONSE)
    )
    result = get_location("Shanghai")
    assert result["name"] == "上海"
    assert result["latitude"] == 31.22222


@respx.mock
def test_get_location_not_found():
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    with pytest.raises(Exception):
        get_location("unknowncity123")


@respx.mock
def test_get_weather_success():
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=MOCK_WEATHER_RESPONSE)
    )
    result = get_weather(31.22222, 121.45806)
    assert result["current"]["temperature_2m"] == 20.0


def test_parse_weather():
    location = {"name": "上海", "country": "中国"}
    result = parse_weather(location, MOCK_WEATHER_RESPONSE)
    assert result["city"] == "上海"
    assert result["temp_c"] == 20.0
    assert result["description"] == "多云"
    assert result["humidity"] == 60

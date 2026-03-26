import httpx
import pytest
import respx

from app.api import get_weather
from app.config import settings


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_success():
    geo_route = respx.get(f"{settings.base_url}/geo/v2/city/lookup").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "200",
                "location": [
                    {"name": "北京", "id": "101010100"},
                ],
            },
        )
    )

    weather_route = respx.get(f"{settings.base_url}/v7/weather/7d").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "200",
                "daily": [
                    {
                        "fxDate": "2025-06-01",
                        "textDay": "晴",
                        "textNight": "多云",
                        "tempMax": "30",
                        "tempMin": "20",
                        "humidity": "50",
                        "windDirDay": "东北风",
                        "windSpeedDay": "10",
                    }
                ],
            },
        )
    )

    report = await get_weather("北京")

    assert geo_route.called
    assert weather_route.called
    assert report.city == "北京"
    assert len(report.forecast) == 1
    assert report.forecast[0].day_text == "晴"

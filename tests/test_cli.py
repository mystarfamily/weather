import respx
import httpx
from typer.testing import CliRunner

from app.cli import app
from tests.test_api import MOCK_LOCATION_RESPONSE, MOCK_WEATHER_RESPONSE

runner = CliRunner()


@respx.mock
def test_cli_success():
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json=MOCK_LOCATION_RESPONSE)
    )
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=MOCK_WEATHER_RESPONSE)
    )
    result = runner.invoke(app, ["Shanghai"])
    assert result.exit_code == 0
    assert "上海" in result.output


@respx.mock
def test_cli_city_not_found():
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    result = runner.invoke(app, ["unknowncity123"])
    assert result.exit_code != 0

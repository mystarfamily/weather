from app.models import WeatherReport, ForecastDay
from app.renderer import render, weekday, get_icon


def test_weekday_valid():
    assert weekday("2025-06-01").startswith("周")


def test_get_icon():
    assert get_icon("小雨") != "🌡"


def test_render_runs(capsys):
    report = WeatherReport(
        city="北京",
        forecast=[
            ForecastDay(
                date="2025-06-01",
                day_text="晴",
                night_text="多云",
                temp_max="30",
                temp_min="20",
                humidity="50",
                wind_dir="东北风",
                wind_speed="10",
            )
        ],
    )
    render(report)
    captured = capsys.readouterr()
    assert "北京" in captured.out

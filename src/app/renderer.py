from datetime import date

from rich.console import Console
from rich.table import Table

from .logging import get_logger
from .models import WeatherReport

console = Console()
logger = get_logger(__name__)

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

ICONS = {
    "晴": "☀ ",
    "多云": "⛅",
    "阴": "☁ ",
    "雨": "🌧",
    "阵雨": "🌦",
    "雷": "⛈",
    "雪": "❄ ",
    "雾": "🌫",
    "霾": "🌫",
}


def weekday(date_str: str) -> str:
    try:
        d = date.fromisoformat(date_str)
        return WEEKDAYS[d.weekday()]
    except ValueError:
        return "    "


def get_icon(text: str) -> str:
    for key, icon in ICONS.items():
        if key in text:
            return icon
    return "🌡"


def render(report: WeatherReport) -> None:
    logger.info(f"渲染天气表格: {report.city}")

    table = Table(title=f"📍 {report.city} — 未来七天天气预报", show_lines=True)

    table.add_column("日期", justify="center")
    table.add_column("星期", justify="center")
    table.add_column("白天", justify="center")
    table.add_column("夜间", justify="center")
    table.add_column("最高温", justify="right")
    table.add_column("最低温", justify="right")
    table.add_column("湿度", justify="right")
    table.add_column("风向", justify="center")
    table.add_column("风速", justify="right")

    today = date.today().isoformat()

    for day in report.forecast:
        icon = get_icon(day.day_text)
        mark = "⭐" if day.date == today else ""

        table.add_row(
            day.date,
            weekday(day.date),
            f"{icon} {day.day_text}",
            day.night_text,
            f"{day.temp_max}°",
            f"{day.temp_min}°",
            f"{day.humidity}%",
            day.wind_dir,
            f"{day.wind_speed} km/h {mark}",
        )

    console.print(table)

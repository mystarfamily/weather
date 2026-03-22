import typer
from rich.console import Console
from rich.table import Table

from app.api import get_location, get_weather, parse_weather
from app.logger import get_logger

app = typer.Typer()
console = Console()
logger = get_logger(__name__)


@app.command()
def main(city: str = typer.Argument(..., help="城市名称，例如：Beijing")):
    """查询城市天气"""
    logger.info(f"开始查询城市天气：{city}")
    with console.status(f"正在查询 {city} 的天气..."):
        location = get_location(city)
        data = get_weather(location["latitude"], location["longitude"])
        weather = parse_weather(location, data)

    logger.info(f"查询成功：{weather['city']} {weather['temp_c']}°C")

    table = Table(title=f"🌤 {weather['city']}, {weather['country']}")
    table.add_column("项目", style="cyan")
    table.add_column("数值", style="green")

    table.add_row("天气", weather["description"])
    table.add_row("温度", f"{weather['temp_c']}°C")
    table.add_row("体感温度", f"{weather['feels_like']}°C")
    table.add_row("湿度", f"{weather['humidity']}%")
    table.add_row("风速", f"{weather['wind_speed']} km/h")

    console.print(table)

from __future__ import annotations

import sys
from typing import Any, Dict, Optional

import anyio
import typer
from loguru import logger

from .api import close_client, get_location, get_weather
from .config import settings
from .models import WeatherReport
from .renderer import render

app = typer.Typer(help="Weather CLI")


def setup_logging(level: str) -> None:
    """配置日志级别"""
    logger.remove()
    logger.add(sys.stderr, level=level)


async def main(city: Optional[str]) -> None:
    """
    CLI 主逻辑（异步）
    - city: 用户输入的城市名或 None
    """
    if city is None:
        logger.debug("未指定城市，开始自动定位")
        location: Dict[str, Any] = await get_location()
    else:
        location = {"city": city}

    report: WeatherReport = await get_weather(location)
    render(report)
    await close_client()


@app.command()
def run(
    city: Optional[str] = typer.Argument(None, help="城市名或经纬度"),
    debug: bool = typer.Option(False, "--debug", "-d", help="开启调试日志"),
) -> None:
    """
    CLI 入口函数（同步）
    """

    if not settings.qweather_key:
        typer.secho(
            "❌ 未检测到 WEATHER_QWEATHER_KEY，请在 .env 中填写你的和风天气 API Key",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # Typer 会保证 city 是 str 或 None，不需要 isinstance 检查
    typer.echo(f"查询城市: {city}")

    if debug:
        setup_logging("DEBUG")
        logger.debug("Debug 模式已启用（来自命令行开关）")
    else:
        setup_logging(getattr(settings, "log_level", "INFO"))

    # 运行异步主逻辑
    anyio.run(main, city)


if __name__ == "__main__":
    app()

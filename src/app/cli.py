# src/app/cli.py
import sys
import anyio
import typer
from loguru import logger

# 替换为你项目中实际的异步函数和渲染函数
# 例如: from .api import get_location, get_weather, close_client
#         from .renderer import render
from .api import get_location, get_weather, close_client
from .renderer import render
from .config import settings

# 必须在装饰器之前定义 app
app = typer.Typer(help="Weather CLI")


def setup_logging(level: str):
    logger.remove()
    logger.add(sys.stderr, level=level)


async def main(city: str | None):
    # 在调用 get_weather(location) 之前确保 location 已定义
    if city is None:
        logger.debug("未指定城市，开始自动定位")
        location = await get_location()  # 假设返回 dict 或对象
    else:
        # 将 city 包装成 get_weather 期望的结构
        location = {"city": city}

    report = await get_weather(location)
    render(report)
    await close_client()


@app.command()
def run(
    city: str = typer.Argument(None, help="城市名或经纬度"),
    debug: bool = typer.Option(False, "--debug", "-d", help="开启调试日志"),
):

    if not settings.qweather_key:
        typer.secho(
            "❌ 未检测到 WEATHER_QWEATHER_KEY，请在 .env 中填写你的和风天气 API Key",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # 如果 city 不是字符串（例如 ArgumentInfo），说明脚本被直接调用，交给 Typer 解析
    if not isinstance(city, str):
        app()
        return

    typer.echo(f"查询城市: {city}")
    """
    查询天气（示例：weather 上海 或 weather "116.41,39.92"）
    使用 --debug 或 -d 开启 DEBUG 日志。
    """
    # 日志级别设置
    if debug:
        setup_logging("DEBUG")
        logger.debug("Debug 模式已启用（来自命令行开关）")
    else:
        setup_logging(getattr(settings, "log_level", "INFO"))

    # 将 city 传入异步 main
    anyio.run(main, city)


if __name__ == "__main__":
    app()

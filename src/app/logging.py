from loguru import logger
import sys
from pathlib import Path

from .config import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
    "| <level>{level}</level> "
    "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
    "- <level>{message}</level>",
)

logger.add(
    LOG_DIR / "weather.log",
    rotation="5 MB",
    retention="7 days",
    level=settings.log_level,
    encoding="utf-8",
    enqueue=True,
)


def get_logger(name: str):
    return logger.bind(module=name)

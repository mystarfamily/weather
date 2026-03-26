# 从 .env 文件或环境变量中加载应用配置，并提供默认值

"""
让你的应用配置：
• 可集中管理
• 可自动从环境变量读取
• 可有默认值
• 可类型检查
• 可轻松扩展
适合 CLI 工具、Web 服务、微服务等场景。
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    qweather_key: str = ""
    base_url: str = "https://pw5ctvrmex.re.qweatherapi.com"
    request_timeout: float = 10.0
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="WEATHER_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator("qweather_key")
    def validate_key(cls, v: str) -> str:
        """校验 API Key 是否有效"""
        if not v or v.strip() == "" or "your_qweather_api_key_here" in v:
            raise ValueError(
                "❌ 未检测到有效的 WEATHER_QWEATHER_KEY，请在 .env 中填写你的和风天气 API Key"
            )
        return v


settings = Settings()

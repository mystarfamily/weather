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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # API 配置
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    weather_url: str = "https://api.open-meteo.com/v1/forecast"

    # 请求配置
    request_timeout: int = 10
    request_language: str = "zh"

    # 应用配置
    app_name: str = "Weather CLI"
    debug: bool = False


settings = Settings()

print(settings)

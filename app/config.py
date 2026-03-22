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

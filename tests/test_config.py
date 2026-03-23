from app.config import Settings


def test_settings_env_prefix(monkeypatch):
    monkeypatch.setenv("WEATHER_QWEATHER_KEY", "test-key")
    s = Settings()
    assert s.qweather_key == "test-key"

from src.services.weather_api import fetch_weather


def test_fetch_weather_no_key(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    data = fetch_weather("Chicago")
    assert data.get("ok") is False
    assert data.get("error") == "NO_API_KEY"



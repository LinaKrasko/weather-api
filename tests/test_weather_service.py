import pytest

from app.cache.ttl_cache import TTLCache
from app.services.weather_service import WeatherService


class FakeWeatherClient:
    async def fetch_current_weather(self, city: str) -> dict:
        return {
            "name": city,
            "main": {"temp": 12.3, "humidity": 81},
            "weather": [{"description": "cloudy"}],
        }


class FakeStorage:
    async def save(self, city: str, weather: dict) -> str:
        return f"data/{city}_123.json"


class FakeEventLogger:
    async def log(self, city: str, timestamp: int, file_path: str, cache_hit: bool) -> None:
        return None


@pytest.mark.asyncio
async def test_weather_service_returns_mapped_weather():
    service = WeatherService(
        client=FakeWeatherClient(),
        cache=TTLCache(ttl_seconds=300),
        storage=FakeStorage(),
        event_logger=FakeEventLogger(),
    )

    result = await service.get_weather("London")

    assert result["city"] == "London"
    assert "temp_c" in result

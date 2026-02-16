import asyncio
import pytest

from app.cache.ttl_cache import TTLCache
from app.services.weather_service import WeatherService


class FakeWeatherClient:
    def __init__(self, payload: dict, delay_seconds: float = 0.0):
        self.payload = payload
        self.delay_seconds = delay_seconds
        self.calls = 0
        self.calls_by_city: dict[str, int] = {}

    async def fetch_current_weather(self, city: str) -> dict:
        self.calls += 1
        self.calls_by_city[city] = self.calls_by_city.get(city, 0) + 1
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        payload = self.payload
        if isinstance(payload, dict) and city in payload:
            return payload[city]
        return payload


class FakeStorage:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def save(self, city: str, weather: dict) -> str:
        self.calls.append((city, weather))
        return f"data/{city}_123.json"


class FakeEventLogger:
    def __init__(self):
        self.calls: list[dict] = []

    async def log(self, city: str, timestamp: int, file_path: str, cache_hit: bool) -> None:
        self.calls.append(
            {
                "city": city,
                "timestamp": timestamp,
                "file_path": file_path,
                "cache_hit": cache_hit,
            }
        )


@pytest.mark.asyncio
async def test_get_weather_cache_miss_fetches_stores_and_logs():
    client = FakeWeatherClient(
        {
            "name": "London",
            "main": {"temp": 12.3, "humidity": 81},
            "weather": [{"description": "cloudy"}],
        }
    )
    storage = FakeStorage()
    logger = FakeEventLogger()
    service = WeatherService(client=client, cache=TTLCache(ttl_seconds=300), storage=storage, event_logger=logger)

    result = await service.get_weather("London")

    assert client.calls == 1
    assert result["city"] == "London"
    assert result["temp_c"] == 12.3
    assert len(storage.calls) == 1
    assert storage.calls[0][0] == "London"
    assert len(logger.calls) == 1
    assert logger.calls[0]["cache_hit"] is False
    assert logger.calls[0]["city"] == "London"


@pytest.mark.asyncio
async def test_get_weather_cache_hit_skips_client_and_logs_cache_hit():
    client = FakeWeatherClient(
        {
            "name": "Paris",
            "main": {"temp": 18.0, "humidity": 60},
            "weather": [{"description": "sunny"}],
        }
    )
    storage = FakeStorage()
    logger = FakeEventLogger()
    service = WeatherService(client=client, cache=TTLCache(ttl_seconds=300), storage=storage, event_logger=logger)

    first = await service.get_weather("Paris")
    second = await service.get_weather("Paris")

    assert client.calls == 1
    assert first == second
    assert len(storage.calls) == 1
    assert len(logger.calls) == 2
    assert logger.calls[0]["cache_hit"] is False
    assert logger.calls[1]["cache_hit"] is True
    assert logger.calls[1]["file_path"] == "cache"


@pytest.mark.asyncio
async def test_get_weather_for_cities_uses_cache_on_second_call():
    client = FakeWeatherClient(
        {
            "Rome": {
                "name": "Rome",
                "main": {"temp": 12.0, "humidity": 40},
                "weather": [{"description": "clear sky"}],
            }
        },
    )
    storage = FakeStorage()
    logger = FakeEventLogger()
    service = WeatherService(client=client, cache=TTLCache(ttl_seconds=300), storage=storage, event_logger=logger)

    first = await service.get_weather_for_cities(["Rome"])
    second = await service.get_weather_for_cities(["Rome"])

    assert client.calls == 1
    assert first == second
    weather = first["weather"][0]
    assert weather["city"] == "Rome"
    assert weather["temp_c"] == 12.0
    assert weather["humidity"] == 40
    assert len(storage.calls) == 1
    assert len(logger.calls) == 2
    assert logger.calls[0]["cache_hit"] is False
    assert logger.calls[1]["cache_hit"] is True
    assert logger.calls[1]["file_path"] == "cache"


@pytest.mark.asyncio
async def test_get_weather_for_cities_checks_cache_per_city():
    client = FakeWeatherClient(
        {
            "London": {
                "name": "London",
                "main": {"temp": 8.0, "humidity": 70},
                "weather": [{"description": "cloudy"}],
            },
            "Paris": {
                "name": "Paris",
                "main": {"temp": 10.0, "humidity": 65},
                "weather": [{"description": "sunny"}],
            },
        },
    )
    storage = FakeStorage()
    logger = FakeEventLogger()
    service = WeatherService(client=client, cache=TTLCache(ttl_seconds=300), storage=storage, event_logger=logger)

    await service.get_weather_for_cities(["London"])
    result = await service.get_weather_for_cities(["London", "Paris"])

    assert len(result["weather"]) == 2
    assert [item["city"] for item in result["weather"]] == ["London", "Paris"]
    assert client.calls_by_city["London"] == 1
    assert client.calls_by_city["Paris"] == 1

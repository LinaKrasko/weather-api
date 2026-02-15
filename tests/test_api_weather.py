from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.clients.weather_client import CityNotFound
from app.main import app
from app.rate_limit.in_memory_rate_limiter import InMemoryRateLimiter


class FakeNotFoundService:
    async def get_weather(self, city: str) -> dict:
        raise CityNotFound(f"City not found: {city}")

    async def get_weather_for_cities(self, cities: list[str]) -> dict:
        raise CityNotFound(f"City not found: {cities[0]}")


def test_weather_endpoint_returns_404_for_invalid_city(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "weather_service", FakeNotFoundService())
        monkeypatch.setattr(app.state, "weather_rate_limiter", InMemoryRateLimiter(max_requests=1000, window_seconds=60))

        response = client.get("/weather", params={"city": "NoSuchCity"})

        assert response.status_code == 404
        assert response.json() == {"detail": "City not found: NoSuchCity"}


class FakeOkService:
    async def get_weather(self, city: str) -> dict:
        return {
            "city": city,
            "timestamp": 1,
            "temp_c": 10.0,
            "humidity": 70,
            "description": "clear sky",
            "source": "test",
        }

    async def get_weather_for_cities(self, cities: list[str]) -> dict:
        return {
            "requested_cities": cities,
            "weather": [self.get_weather_sync(city) for city in cities],
        }

    def get_weather_sync(self, city: str) -> dict:
        return {
            "city": city,
            "timestamp": 1,
            "temp_c": 10.0,
            "humidity": 70,
            "description": "clear sky",
            "source": "test",
        }


def test_weather_endpoint_returns_429_when_rate_limit_exceeded(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "weather_service", FakeOkService())
        monkeypatch.setattr(app.state, "weather_rate_limiter", InMemoryRateLimiter(max_requests=1, window_seconds=60))
        monkeypatch.setattr(app.state, "weather_settings", SimpleNamespace(trust_proxy_headers=True))

        first = client.get("/weather", params={"city": "London"}, headers={"x-forwarded-for": "1.2.3.4"})
        second = client.get("/weather", params={"city": "London"}, headers={"x-forwarded-for": "1.2.3.4"})

        assert first.status_code == 200
        assert second.status_code == 429
        assert second.json() == {"detail": "Rate limit exceeded"}


def test_weather_endpoint_ignores_x_forwarded_for_when_not_trusted(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "weather_service", FakeOkService())
        monkeypatch.setattr(app.state, "weather_rate_limiter", InMemoryRateLimiter(max_requests=1, window_seconds=60))
        monkeypatch.setattr(app.state, "weather_settings", SimpleNamespace(trust_proxy_headers=False))

        first = client.get("/weather", params={"city": "London"}, headers={"x-forwarded-for": "1.2.3.4"})
        second = client.get("/weather", params={"city": "London"}, headers={"x-forwarded-for": "9.9.9.9"})

        assert first.status_code == 200
        assert second.status_code == 429


def test_multi_city_weather_endpoint_returns_200(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "weather_service", FakeOkService())
        monkeypatch.setattr(app.state, "weather_rate_limiter", InMemoryRateLimiter(max_requests=1000, window_seconds=60))

        response = client.get(
            "/weather/cities",
            params=[("cities", "London"), ("cities", "Paris")],
        )

        assert response.status_code == 200
        body = response.json()
        assert body["requested_cities"] == ["London", "Paris"]
        assert len(body["weather"]) == 2


def test_multi_city_weather_endpoint_rejects_more_than_3_cities(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "weather_service", FakeOkService())
        monkeypatch.setattr(app.state, "weather_rate_limiter", InMemoryRateLimiter(max_requests=1000, window_seconds=60))

        response = client.get(
            "/weather/cities",
            params=[("cities", "London"), ("cities", "Paris"), ("cities", "Berlin"), ("cities", "Rome")],
        )

        assert response.status_code == 400

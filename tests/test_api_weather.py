from fastapi.testclient import TestClient

from app.main import app


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
            "weather": [await self.get_weather(city) for city in cities],
        }


def test_weather_endpoint_smoke(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "weather_service", FakeOkService())
        response = client.get("/weather", params={"city": "London"})
        assert response.status_code == 200

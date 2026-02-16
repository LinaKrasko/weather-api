import asyncio
import time
from typing import Any
from app.clients.weather_client import WeatherClient
from app.cache.ttl_cache import TTLCache
from app.storage.weather_storage import WeatherStorage
from app.events.weather_event_logger import WeatherEventLogger
from app.services.weather_mapper import WeatherMapper

class WeatherService:
    def __init__(
        self,
        client: WeatherClient,
        cache: TTLCache,
        storage: WeatherStorage,
        event_logger: WeatherEventLogger,
        mapper: WeatherMapper | None = None,
    ):
        self.client = client
        self.cache = cache
        self.storage = storage
        self.event_logger = event_logger
        self.mapper = mapper or WeatherMapper()

    async def get_weather(self, city: str) -> dict[str, Any]:
        cache_key = city.strip().lower()
        cached = await self.cache.get(cache_key)
        if cached is not None:
            await self._log_cache_hit(cached, city)
            return cached

        raw = await self.client.fetch_current_weather(city)
        weather = self.mapper.map_current(raw, city)

        await self.cache.set(cache_key, weather)
        await self._persist_and_log_miss(weather, city)
        return weather

    async def get_weather_for_cities(self, cities: list[str]) -> dict[str, Any]:
        weather_items = await asyncio.gather(*(self.get_weather(city) for city in cities))
        return {
            "requested_cities": cities,
            "weather": weather_items,
        }

    async def _log_cache_hit(self, payload: dict[str, Any], city: str) -> None:
        await self.event_logger.log(
            city=payload.get("city", city),
            timestamp=payload.get("timestamp", int(time.time())),
            file_path="cache",
            cache_hit=True,
        )

    async def _persist_and_log_miss(self, payload: dict[str, Any], city: str) -> None:
        payload_city = payload.get("city", city)
        file_path = await self.storage.save(payload_city, payload)
        await self.event_logger.log(
            city=payload_city,
            timestamp=payload["timestamp"],
            file_path=file_path,
            cache_hit=False,
        )

    async def close(self) -> None:
        if hasattr(self.client, "close"):
            await self.client.close()

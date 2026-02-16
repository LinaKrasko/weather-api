import time
from typing import Any, Mapping

OPENWEATHERMAP_SOURCE = "openweathermap"


class WeatherMapper:
    def __init__(self, source: str = OPENWEATHERMAP_SOURCE) -> None:
        self.source = source

    def map_current(self, raw: Mapping[str, Any], requested_city: str) -> dict[str, Any]:
        city = self._resolve_city(raw, requested_city)
        main = raw.get("main") or {}
        temp_c = main.get("temp")
        humidity = main.get("humidity")
        description = self._first_weather_description(raw)

        return {
            "city": city,
            "timestamp": self._now_ts(),
            "temp_c": temp_c,
            "humidity": humidity,
            "description": description,
            "source": self.source,
        }

    def _resolve_city(self, raw: Mapping[str, Any], fallback: str) -> str:
        name = raw.get("name")
        return name if isinstance(name, str) and name.strip() else fallback

    def _first_weather_description(self, raw: Mapping[str, Any]) -> str | None:
        weather_list = raw.get("weather")
        if not isinstance(weather_list, list) or not weather_list:
            return None

        first = weather_list[0]
        if not isinstance(first, dict):
            return None

        desc = first.get("description")
        return desc if isinstance(desc, str) and desc.strip() else None

    def _now_ts(self) -> int:
        return int(time.time())

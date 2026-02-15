import time
from typing import Any


class WeatherMapper:
    def map_current(self, raw: dict[str, Any], city: str) -> dict[str, Any]:
        return {
            "city": raw.get("name", city),
            "timestamp": int(time.time()),
            "temp_c": raw.get("main", {}).get("temp"),
            "humidity": raw.get("main", {}).get("humidity"),
            "description": (raw.get("weather") or [{}])[0].get("description"),
            "source": "openweathermap",
        }

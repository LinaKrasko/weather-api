import asyncio
import json
import re
import time
from pathlib import Path
from app.storage.weather_storage import WeatherStorage


class WeatherFileStorage(WeatherStorage):
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    async def save(self, city: str, weather: dict) -> str:
        file_path = self.data_dir / self._build_filename(city)

        await asyncio.to_thread(self._write_json, file_path, weather)
        return str(file_path)

    def _build_filename(self, city: str) -> str:
        return f"{self._safe_city(city)}_{self._timestamp_ms()}.json"

    @staticmethod
    def _timestamp_ms() -> int:
        return int(time.time() * 1000)

    def _write_json(self, file_path: Path, weather: dict) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(weather, f, ensure_ascii=True, indent=2)

    @staticmethod
    def _safe_city(city: str) -> str:
        normalized = city.strip().lower().replace(" ", "_")
        cleaned = re.sub(r"[^a-z0-9_]+", "", normalized)
        return cleaned or "unknown_city"

import asyncio
import sqlite3
import time
from pathlib import Path
from app.events.weather_event_logger import WeatherEventLogger


class SqliteWeatherEventLogger(WeatherEventLogger):
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._initialize_db()

    async def log(self, city: str, timestamp: int, file_path: str, cache_hit: bool) -> None:
        await asyncio.to_thread(self._insert_event, city, timestamp, file_path, cache_hit)

    def _initialize_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    weather_timestamp INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    cache_hit INTEGER NOT NULL,
                    logged_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def _insert_event(self, city: str, timestamp: int, file_path: str, cache_hit: bool) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_events (city, weather_timestamp, file_path, cache_hit, logged_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (city, timestamp, file_path, int(cache_hit), int(time.time())),
            )
            conn.commit()

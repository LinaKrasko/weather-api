from abc import ABC, abstractmethod


class WeatherEventLogger(ABC):
    @abstractmethod
    async def log(self, city: str, timestamp: int, file_path: str, cache_hit: bool) -> None:
        """Log weather request metadata for audit/analytics."""
        raise NotImplementedError

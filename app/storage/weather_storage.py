from abc import ABC, abstractmethod


class WeatherStorage(ABC):
    @abstractmethod
    async def save(self, city: str, weather: dict) -> str:
        """Persist a weather payload and return its path/identifier."""
        raise NotImplementedError

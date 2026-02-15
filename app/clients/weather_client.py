import httpx
from app.core.settings import Settings, get_settings

class CityNotFound(Exception):
    pass

class UpstreamError(Exception):
    pass

class WeatherClient:
    def __init__(self, api_key: str, base_url: str, units: str = "metric"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.units = units
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0))

    async def fetch_current_weather(self, city: str) -> dict:
        url = f"{self.base_url}/weather"
        params = {"q": city, "appid": self.api_key, "units": self.units}
        return await self._fetch(url, params, city)

    async def _fetch(self, url: str, params: dict, city: str) -> dict:
        try:
            resp = await self._client.get(url, params=params)
        except httpx.TimeoutException as e:
            raise UpstreamError("OpenWeatherMap timeout") from e
        except httpx.HTTPError as e:
            raise UpstreamError("OpenWeatherMap HTTP error") from e

        if resp.status_code == 404:
            raise CityNotFound(f"City not found: {city}")
        if resp.status_code >= 400:
            raise UpstreamError(f"OpenWeatherMap error: {resp.status_code}")

        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()

def build_weather_client(settings: Settings | None = None) -> WeatherClient:
    config = settings or get_settings()
    return WeatherClient(
        api_key=config.openweather_api_key,
        base_url=config.openweather_base_url,
        units=config.weather_units,
    )

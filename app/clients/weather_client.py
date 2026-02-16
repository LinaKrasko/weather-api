import httpx
from app.core.settings import Settings, get_settings

OPENWEATHER_TIMEOUT_SECONDS = 5.0
OPENWEATHER_CONNECT_TIMEOUT_SECONDS = 3.0
NOT_FOUND_STATUS = 404
CLIENT_ERROR_STATUS = 400


class CityNotFound(Exception):
    pass

class UpstreamError(Exception):
    pass

class WeatherClient:
    def __init__(self, api_key: str, base_url: str, units: str = "metric"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.units = units
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(OPENWEATHER_TIMEOUT_SECONDS, connect=OPENWEATHER_CONNECT_TIMEOUT_SECONDS)
        )

    async def fetch_current_weather(self, city: str) -> dict:
        url = f"{self.base_url}/weather"
        params = {"q": city, "appid": self.api_key, "units": self.units}
        return await self._fetch_current_weather_payload(url=url, params=params, city=city)

    async def _fetch_current_weather_payload(self, url: str, params: dict, city: str) -> dict:
        response = await self._request(url=url, params=params)
        self._raise_for_status(response=response, city=city)
        return response.json()

    async def _request(self, url: str, params: dict) -> httpx.Response:
        try:
            return await self._client.get(url, params=params)
        except httpx.TimeoutException as e:
            raise UpstreamError("OpenWeatherMap timeout") from e
        except httpx.HTTPError as e:
            raise UpstreamError("OpenWeatherMap HTTP error") from e

    def _raise_for_status(self, response: httpx.Response, city: str) -> None:
        if response.status_code == NOT_FOUND_STATUS:
            raise CityNotFound(f"City not found: {city}")
        if response.status_code >= CLIENT_ERROR_STATUS:
            raise UpstreamError(f"OpenWeatherMap error: {response.status_code}")

    async def close(self) -> None:
        await self._client.aclose()

def build_weather_client(settings: Settings | None = None) -> WeatherClient:
    config = settings or get_settings()
    return WeatherClient(
        api_key=config.openweather_api_key,
        base_url=config.openweather_base_url,
        units=config.weather_units,
    )

import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_APP_ENV = "local"
DEFAULT_OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
DEFAULT_WEATHER_UNITS = "metric"
DEFAULT_DATA_DIR = "data"
DEFAULT_EVENTS_DB_PATH = "data/weather_events.db"
DEFAULT_CACHE_TTL_SECONDS = 300
DEFAULT_RATE_LIMIT_REQUESTS = 60
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_env: str = Field(default=DEFAULT_APP_ENV, alias="APP_ENV")
    openweather_api_key: str = Field(alias="OPENWEATHER_API_KEY")
    openweather_base_url: str = Field(default=DEFAULT_OPENWEATHER_BASE_URL, alias="OPENWEATHER_BASE_URL")
    weather_units: str = Field(default=DEFAULT_WEATHER_UNITS, alias="WEATHER_UNITS")
    data_dir: str = Field(default=DEFAULT_DATA_DIR, alias="DATA_DIR")
    events_db_path: str = Field(default=DEFAULT_EVENTS_DB_PATH, alias="EVENTS_DB_PATH")
    cache_ttl_seconds: int = Field(default=DEFAULT_CACHE_TTL_SECONDS, alias="CACHE_TTL_SECONDS", gt=0)
    rate_limit_requests: int = Field(default=DEFAULT_RATE_LIMIT_REQUESTS, alias="RATE_LIMIT_REQUESTS", gt=0)
    rate_limit_window_seconds: int = Field(default=DEFAULT_RATE_LIMIT_WINDOW_SECONDS, alias="RATE_LIMIT_WINDOW_SECONDS", gt=0)
    trust_proxy_headers: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")


def _env_file() -> str:
    app_env = os.getenv("APP_ENV", DEFAULT_APP_ENV)
    return f".env.{app_env}"


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=_env_file(), _env_file_encoding="utf-8")

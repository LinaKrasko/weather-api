import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    openweather_api_key: str = Field(alias="OPENWEATHER_API_KEY")
    openweather_base_url: str = Field(default="https://api.openweathermap.org/data/2.5", alias="OPENWEATHER_BASE_URL")
    weather_units: str = Field(default="metric", alias="WEATHER_UNITS")
    data_dir: str = Field(default="data", alias="DATA_DIR")
    events_db_path: str = Field(default="data/weather_events.db", alias="EVENTS_DB_PATH")
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS", gt=0)
    rate_limit_requests: int = Field(default=60, alias="RATE_LIMIT_REQUESTS", gt=0)
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS", gt=0)
    trust_proxy_headers: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")


def _env_files() -> str:
    app_env = os.getenv("APP_ENV", "local")
    return f".env.{app_env}"


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=_env_files(), _env_file_encoding="utf-8")

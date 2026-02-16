from fastapi import APIRouter, Query, HTTPException, Request, FastAPI
from typing import Awaitable, Callable, Any
from app.clients.weather_client import build_weather_client, CityNotFound, UpstreamError
from app.services.weather_service import WeatherService
from app.cache.ttl_cache import TTLCache
from app.storage.weather_file_storage import WeatherFileStorage
from app.events.sqlite_weather_event_logger import SqliteWeatherEventLogger
from app.rate_limit.in_memory_rate_limiter import InMemoryRateLimiter, RateLimitExceeded
from app.core.settings import get_settings
from app.schemas.weather import WeatherResponse, MultiCityWeatherResponse

router = APIRouter(tags=["Weather"])
MAX_CITIES_PER_REQUEST = 3
INVALID_CITIES_DETAIL = "Provide between 1 and 3 unique non-empty cities."


def init_weather_api_state(app: FastAPI) -> None:
    settings = get_settings()
    app.state.weather_settings = settings
    app.state.weather_service = WeatherService(
        build_weather_client(settings),
        TTLCache(ttl_seconds=settings.cache_ttl_seconds),
        WeatherFileStorage(data_dir=settings.data_dir),
        SqliteWeatherEventLogger(db_path=settings.events_db_path),
    )
    app.state.weather_rate_limiter = InMemoryRateLimiter(
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    settings = request.app.state.weather_settings
    if settings.trust_proxy_headers and forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def close_weather_api_resources(app: FastAPI) -> None:
    service = getattr(app.state, "weather_service", None)
    if service is not None and hasattr(service, "close"):
        await service.close()


async def _execute_weather_operation(operation: Callable[[], Awaitable[Any]]) -> Any:
    try:
        return await operation()
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except CityNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UpstreamError as e:
        raise HTTPException(status_code=502, detail=str(e))


def _normalize_cities(cities: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for city in cities:
        value = city.strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(value)
    return normalized


async def _run_with_rate_limit(request: Request, operation: Callable[[], Awaitable[Any]]) -> Any:
    await request.app.state.weather_rate_limiter.check(_client_ip(request))
    return await operation()


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Get current weather by city",
    description="Returns current weather for a single city. Uses cache when available and applies per-client rate limiting.",
    responses={
        404: {"description": "City not found"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "Upstream weather provider failure"},
    },
)
async def get_weather(request: Request, city: str = Query(..., min_length=1)):
    async def _operation():
        return await request.app.state.weather_service.get_weather(city)
    return await _execute_weather_operation(lambda: _run_with_rate_limit(request, _operation))


@router.get(
    "/weather/cities",
    response_model=MultiCityWeatherResponse,
    summary="Get current weather for up to 3 cities",
    description="Returns current weather for 1 to 3 cities. Each city is resolved independently and checked against cache before any upstream fetch.",
    responses={
        400: {"description": "Invalid city list"},
        404: {"description": "City not found"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "Upstream weather provider failure"},
    },
)
async def get_weather_for_cities(
    request: Request,
    cities: list[str] = Query(..., description="Provide 1-3 cities using repeated query params."),
):
    normalized = _normalize_cities(cities)

    if not normalized or len(normalized) > MAX_CITIES_PER_REQUEST:
        raise HTTPException(status_code=400, detail=INVALID_CITIES_DETAIL)

    async def _operation():
        return await request.app.state.weather_service.get_weather_for_cities(cities=normalized)
    return await _execute_weather_operation(lambda: _run_with_rate_limit(request, _operation))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.weather import router as weather_router, close_weather_api_resources, init_weather_api_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_weather_api_state(app)
    try:
        yield
    finally:
        await close_weather_api_resources(app)

app = FastAPI(
    title="Weather Service API",
    description="FastAPI service for current weather data (single and multiple cities) with caching, storage, logging, and rate limiting.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(weather_router)

import os
from app.core.settings import get_settings


os.environ.setdefault("OPENWEATHER_API_KEY", "test-key")
os.environ.setdefault("CACHE_TTL_SECONDS", "300")
os.environ.setdefault("DATA_DIR", "data")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "60")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "60")
os.environ.setdefault("TRUST_PROXY_HEADERS", "false")
os.environ.setdefault("APP_ENV", "ci-test")

get_settings.cache_clear()

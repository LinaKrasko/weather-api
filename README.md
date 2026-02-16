# Weather Service API (FastAPI)

Simple async weather service that fetches data from OpenWeatherMap and demonstrates:
- async I/O
- 5-minute caching
- local file storage (S3-style abstraction)
- local event logging (DynamoDB-style abstraction)
- rate limiting
- Docker + CI

## Features
- `GET /weather?city=...` for current weather
- `GET /weather/cities?cities=City1&cities=City2` for current weather (up to 3 cities per request)
- Cache with TTL (`CACHE_TTL_SECONDS`, default `300`)
- Saves JSON files on cache miss in `DATA_DIR`
- Logs events to SQLite (`EVENTS_DB_PATH`)
- Simple per-IP rate limiting
- CI on push/PR via GitHub Actions

## Project Structure
- `app/main.py`: FastAPI app bootstrap
- `app/api/weather.py`: API routes and HTTP error mapping
- `app/clients/weather_client.py`: async OpenWeatherMap client
- `app/services/weather_service.py`: core business logic and caching
- `app/cache/ttl_cache.py`: in-memory TTL cache
- `app/storage/`: storage abstraction + local file implementation
- `app/events/`: logging abstraction + SQLite implementation
- `app/rate_limit/`: in-memory rate limiter
- `app/core/settings.py`: centralized typed configuration
- `tests/`: pytest suite

## Configuration
The app loads config from:
1. `.env.<APP_ENV>` (for example `.env.local`)

Default `APP_ENV` is `local`.

Use `.env.example` as a template.

Important variables:
- `OPENWEATHER_API_KEY` (required)
- `OPENWEATHER_BASE_URL`
- `WEATHER_UNITS`
- `CACHE_TTL_SECONDS`
- `DATA_DIR`
- `EVENTS_DB_PATH`
- `RATE_LIMIT_REQUESTS`
- `RATE_LIMIT_WINDOW_SECONDS`
- `TRUST_PROXY_HEADERS`

### API Key Per Environment
- `local` (`.env.local`): set your real OpenWeather key in `OPENWEATHER_API_KEY`.
- `ci-test` (`.env.ci-test`): uses `test-key` placeholder because tests mock external calls.
- `prod` (`.env.prod`): keep placeholder in file and inject real `OPENWEATHER_API_KEY` from runtime/secret manager (do not commit real key).

## Prerequisites
- Docker Desktop (or Docker Engine + Compose) installed and running
- Internet access (required to call OpenWeather API)
- OpenWeather API key
- Port `8000` available on your machine

## Run with Docker
### Getting Started (Checkout)
1. Clone repository:
```bash
git clone <your-repo-url>
```
2. Enter project directory:
```bash
cd Weather
```

3. Create your local env file from template:
```bash
python scripts/setup.py
```
What the setup script does:
- checks that `.env.example` exists
- creates `.env.local` from `.env.example` only if missing
- does not overwrite an existing `.env.local`
- prints next steps (set API key, run Docker)
4. Generate OpenWeather API key:
- Create/sign in account at https://openweathermap.org/
- Open **API keys** page and create/copy a key
- Note: a new key can take a few minutes to become active
5. Edit `.env.local` and set:
```env
APP_ENV=local
OPENWEATHER_API_KEY=your_real_key_here
```
6. Start with Docker:
```bash
docker compose up --build
```
7. Open docs:
- `http://localhost:8000/docs`

## API Usage
- Interactive API documentation: `http://localhost:8000/docs`
- Use `/docs` as the source of truth for endpoint parameters, response shapes, and error models.

## Testing
Run all tests:
```bash
python -m pytest -q
```

What tests cover:
1. `tests/test_ttl_cache.py`
- cache value returned before expiry
- cache value expires after TTL

2. `tests/test_weather_service.py`
- weather cache miss saves file and logs miss
- weather cache hit skips new file save and logs cache hit
- multi-city weather behavior and per-city cache checks

3. `tests/test_api_weather.py`
- API returns `404` for city not found
- API returns `429` when rate limit is exceeded
- `/weather/cities` success and `400` validation case for too many cities

## CI/CD
GitHub Actions CI is configured in `.github/workflows/ci.yml`.
It runs automatically on:
- `push`
- `pull_request`

## Quick Verification Checklist
1. Open Swagger docs:
- `http://localhost:8000/docs`
2. Call single-city endpoint:
- `GET /weather?city=Paris`
3. Call multi-city endpoint:
- `GET /weather/cities?cities=Rehovot&cities=Paris`
4. Confirm JSON files are saved under `DATA_DIR` (`data/` by default).
5. Confirm SQLite events are written to `EVENTS_DB_PATH` (`data/weather_events.db` by default).

## Troubleshooting
1. `{"detail":"OpenWeatherMap error: 401"}`
- API key is missing/invalid or not active yet.
- Check `.env.local` and wait a few minutes after creating a new key.
- Restart containers:
```bash
docker compose down
docker compose up --build
```

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
- Per-client rate limiting (`RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`)
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

## API Examples
Use Postman with `GET` requests:

1. Current weather (single city)
- Method: `GET`
- URL: `http://localhost:8000/weather`
- Query Params:
  - `city=London`

2. Current weather (multiple cities, up to 3)
- Method: `GET`
- URL: `http://localhost:8000/weather/cities`
- Query Params:
  - `cities=London`
  - `cities=Paris`

Notes:
- In Postman, add `cities` key multiple times (one value per city).
- You can still test interactively from `http://localhost:8000/docs`.

## Response Types and Examples
1. `GET /weather?city=London`
- Response type: JSON object
- Example:
```json
{
  "city": "London",
  "timestamp": 1771174431,
  "temp_c": 4.51,
  "humidity": 98,
  "description": "light intensity drizzle",
  "source": "openweathermap"
}
```

2. `GET /weather/cities?cities=Rehovot&cities=Paris`
- Response type: JSON object containing an array of weather objects
- Example:
```json
{
  "requested_cities": ["Rehovot", "Paris"],
  "weather": [
    {
      "city": "Rehovot",
      "timestamp": 1771174431,
      "temp_c": 19.23,
      "humidity": 53,
      "description": "clear sky",
      "source": "openweathermap"
    },
    {
      "city": "Paris",
      "timestamp": 1771174431,
      "temp_c": 4.51,
      "humidity": 98,
      "description": "light intensity drizzle",
      "source": "openweathermap"
    }
  ]
}
```

## Saved Data Examples
1. JSON file saved in `DATA_DIR` (example file `paris_1771174431211.json`):
```json
{
  "city": "Paris",
  "timestamp": 1771174431,
  "temp_c": 4.51,
  "humidity": 98,
  "description": "light intensity drizzle",
  "source": "openweathermap"
}
```

2. SQLite event row in `weather_events` table (example values):
```text
id=23
city=Paris
weather_timestamp=1771174431
file_path=cache
cache_hit=1
logged_at=1771174431
```

## Negative Path Results
1. Too many cities:
- Request: `/weather/cities?cities=London&cities=Paris&cities=Berlin&cities=Rome`
- Status: `400`
- Response:
```json
{
  "detail": "Provide between 1 and 3 unique non-empty cities."
}
```

2. Invalid city:
- Status: `404`
- Response example:
```json
{
  "detail": "City not found: NoSuchCity"
}
```

3. Rate limit exceeded:
- Status: `429`
- Response:
```json
{
  "detail": "Rate limit exceeded"
}
```

4. Upstream provider failure:
- Status: `502`
- Response example:
```json
{
  "detail": "OpenWeatherMap error: 401"
}
```

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
- concurrent weather requests behavior without single-flight dedupe
- multi-city weather behavior and per-city cache checks

3. `tests/test_api_weather.py`
- API returns `404` for city not found
- API returns `429` when rate limit is exceeded
- trusted/untrusted proxy-header behavior for client IP detection
- `/weather/cities` success and `400` validation case for too many cities

## CI/CD
GitHub Actions workflow: `.github/workflows/ci.yml`

Triggers:
- `push`
- `pull_request`

Job:
1. checkout repo
2. setup Python 3.11
3. install requirements
4. run `pytest`

## Notes
- Rate limiting is per client IP.
- `x-forwarded-for` is used only when `TRUST_PROXY_HEADERS=true`.
- In-memory cache/rate-limiter state resets on process restart.

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

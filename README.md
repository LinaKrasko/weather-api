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
- Saves every response to JSON file in `DATA_DIR`
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
cp .env.example .env.local
```
Windows PowerShell:
```powershell
Copy-Item .env.example .env.local
```
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
docker-compose up --build
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

## Testing
Run all tests:
```bash
python -m pytest -q
```

Current suite covers:
- cache TTL behavior
- service cache miss/hit flow
- concurrent weather requests without single-flight dedupe
- API error mapping (`404`, `429`)
- multi-city weather endpoint behavior

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

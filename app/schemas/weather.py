from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    city: str = Field(..., description="City name resolved by the weather provider.")
    timestamp: int = Field(..., description="Unix timestamp when the weather payload was generated.")
    temp_c: float | None = Field(None, description="Current temperature in Celsius.")
    humidity: int | None = Field(None, description="Current relative humidity percentage.")
    description: str | None = Field(None, description="Human-readable weather description.")
    source: str = Field(..., description="Upstream weather provider identifier.")


class MultiCityWeatherResponse(BaseModel):
    requested_cities: list[str] = Field(..., description="Normalized city list requested by the client.")
    weather: list[WeatherResponse] = Field(..., description="Current weather payload per requested city.")

from dataclasses import dataclass
from typing import List


@dataclass
class ForecastDay:
    date: str
    day_text: str
    night_text: str
    temp_max: str
    temp_min: str
    humidity: str
    wind_dir: str
    wind_speed: str


@dataclass
class WeatherReport:
    city: str
    forecast: List[ForecastDay]

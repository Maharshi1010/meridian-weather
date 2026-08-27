import requests
from datetime import datetime, timezone, timedelta
from django.conf import settings

BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"


class WeatherAPIError(Exception):
    pass


def _get(url, params):
    params = {**params, "appid": settings.OPENWEATHER_API_KEY, "units": "metric"}
    response = requests.get(url, params=params, timeout=8)

    if response.status_code == 401:
        raise WeatherAPIError(
            "Invalid or missing API key. Check OPENWEATHER_API_KEY in your .env file."
        )
    if response.status_code == 404:
        raise WeatherAPIError("City not found. Check the spelling and try again.")
    if not response.ok:
        raise WeatherAPIError(f"Weather service error ({response.status_code}). Try again shortly.")

    return response.json()


def geocode_city(city_name):
    """Turn a typed city name into (lat, lon, name, country) using the Geocoding API."""
    results = _get(GEO_URL, {"q": city_name, "limit": 1})
    if not results:
        raise WeatherAPIError("City not found. Check the spelling and try again.")
    place = results[0]
    return {
        "name": place["name"],
        "country": place.get("country", ""),
        "lat": place["lat"],
        "lon": place["lon"],
    }


def get_current_weather(lat, lon):
    """Current conditions for a coordinate pair."""
    data = _get(f"{BASE_URL}/weather", {"lat": lat, "lon": lon})

    # OpenWeatherMap gives raw UTC timestamps and this city's offset from UTC
    city_tz = timezone(timedelta(seconds=data.get("timezone", 0)))

    return {
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "temp_min": round(data["main"]["temp_min"]),
        "temp_max": round(data["main"]["temp_max"]),
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "wind_deg": data["wind"].get("deg", 0),
        "visibility_km": round(data.get("visibility", 0) / 1000, 1),
        "condition": data["weather"][0]["main"],
        "description": data["weather"][0]["description"].title(),
        "icon": data["weather"][0]["icon"],
        "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"], tz=city_tz).replace(tzinfo=None),
        "sunset": datetime.fromtimestamp(data["sys"]["sunset"], tz=city_tz).replace(tzinfo=None),
        "name": data.get("name", ""),
        "country": data["sys"].get("country", ""),
        "dt": datetime.fromtimestamp(data["dt"], tz=city_tz).replace(tzinfo=None),
    }


def get_forecast(lat, lon):
    """
    5-day / 3-hour forecast, collapsed down to one representative
    entry per day (the reading closest to midday) so the UI can show
    a clean 5-card forecast strip instead of 40 raw data points.
    """
    data = _get(f"{BASE_URL}/forecast", {"lat": lat, "lon": lon})

    # Same fix as get_current_weather: use this city's own UTC offset
    city_tz = timezone(timedelta(seconds=data.get("city", {}).get("timezone", 0)))

    days = {}
    for entry in data["list"]:
        dt = datetime.fromtimestamp(entry["dt"], tz=city_tz).replace(tzinfo=None)
        day_key = dt.date()
        hour_distance = abs(dt.hour - 13)  # prefer the slot nearest 1pm

        if day_key not in days or hour_distance < days[day_key]["_hour_distance"]:
            days[day_key] = {
                "date": dt,
                "temp": round(entry["main"]["temp"]),
                "temp_min": round(entry["main"]["temp_min"]),
                "temp_max": round(entry["main"]["temp_max"]),
                "condition": entry["weather"][0]["main"],
                "description": entry["weather"][0]["description"].title(),
                "icon": entry["weather"][0]["icon"],
                "humidity": entry["main"]["humidity"],
                "wind_speed": entry["wind"]["speed"],
                "_hour_distance": hour_distance,
            }

    ordered = sorted(days.values(), key=lambda d: d["date"])
    for d in ordered:
        d.pop("_hour_distance")
    return ordered[:5]

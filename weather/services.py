import requests
from datetime import datetime
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
    data = _get(f"{BASE_URL}/weather", {"lat": lat, "lon": lon})
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
        "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]),
        "sunset": datetime.fromtimestamp(data["sys"]["sunset"]),
        "name": data.get("name", ""),
        "country": data["sys"].get("country", ""),
        "dt": datetime.fromtimestamp(data["dt"]),
    }


def get_forecast(lat, lon):
    data = _get(f"{BASE_URL}/forecast", {"lat": lat, "lon": lon})

    days = {}
    for entry in data["list"]:
        dt = datetime.fromtimestamp(entry["dt"])
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

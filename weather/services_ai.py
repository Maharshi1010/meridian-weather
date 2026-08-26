"""
Thin client around the Groq API (fast, free-tier inference for open models
like Llama). Same philosophy as services.py: views never call the AI SDK
directly, they call functions here. This file's one hard rule is that the
model is only ever asked to *describe* weather data it's handed - never to
predict or invent numbers itself. That keeps it accurate no matter what it
says, since the actual forecast still comes entirely from OpenWeatherMap.
"""

from groq import Groq
from django.conf import settings

_client = None


def _get_client():
    """Lazily create the Groq client so a missing key doesn't crash imports."""
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            return None
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


class AIUnavailableError(Exception):
    """Raised when the AI summary can't be generated (no key, API error, etc.)."""
    pass


def summarize_weather(current, place):
    """
    Turn a current-weather dict (from services.get_current_weather) into a
    short, friendly 1-2 sentence summary. Returns plain text with no markdown.
    """
    client = _get_client()
    if client is None:
        raise AIUnavailableError("AI summaries aren't configured (missing GROQ_API_KEY).")

    prompt = f"""You are a concise weather assistant. Using ONLY the data below,
write exactly 1-2 short, friendly sentences describing the weather and one
practical suggestion (umbrella, layers, good time to go outside, etc).
Do not invent any numbers not given below. No markdown, no headers, plain text only.

Location: {place['name']}, {place.get('country', '')}
Condition: {current['description']}
Temperature: {current['temp']}°C (feels like {current['feels_like']}°C)
High/Low: {current['temp_max']}°C / {current['temp_min']}°C
Humidity: {current['humidity']}%
Wind speed: {current['wind_speed']} m/s
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
            reasoning_effort="low",
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise AIUnavailableError(f"AI summary temporarily unavailable: {exc}") from exc


def answer_question(current, place, question, forecast=None):
    """
    Answer a free-form user question about the weather, grounded ONLY in the
    already-fetched current/forecast data - never inventing numbers. If the
    question can't be answered from the given data (e.g. asks about a
    different city, or something unrelated to weather), the model is told
    to say so plainly rather than guess.
    """
    client = _get_client()
    if client is None:
        raise AIUnavailableError("AI answers aren't configured (missing GROQ_API_KEY).")

    forecast_lines = ""
    if forecast:
        forecast_lines = "\n5-day outlook:\n" + "\n".join(
            f"- {'Today' if i == 0 else day['date'].strftime('%A')}: "
            f"{day['description']}, high {day['temp_max']}°C / low {day['temp_min']}°C, "
            f"humidity {day['humidity']}%, wind {day['wind_speed']} m/s"
            for i, day in enumerate(forecast)
        )

    prompt = f"""You are a helpful weather assistant answering a question about
{place['name']}, {place.get('country', '')}. Answer in 1-3 short, friendly
sentences using ONLY the data below. Do not invent any numbers not given here.
If the question can't be answered from this data, say so plainly instead of
guessing. No markdown, plain text only.

Current conditions:
Condition: {current['description']}
Temperature: {current['temp']}°C (feels like {current['feels_like']}°C)
High/Low today: {current['temp_max']}°C / {current['temp_min']}°C
Humidity: {current['humidity']}%
Wind speed: {current['wind_speed']} m/s
{forecast_lines}

Question: {question}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
            reasoning_effort="low",
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise AIUnavailableError(f"AI answer temporarily unavailable: {exc}") from exc

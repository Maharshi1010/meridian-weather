from groq import Groq
from django.conf import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            return None
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


class AIUnavailableError(Exception):
    pass


def summarize_weather(current, place):
    client = _get_client()
    if client is None:
        raise AIUnavailableError("AI summaries aren't configured (missing GROQ_API_KEY).")

    prompt = f"""You are a concise weather assistant. Using ONLY the data below,
write exactly 1-2 short, friendly sentences describing the weather and one
practical suggestion (umbrella, layers, good time to go outside, etc).
Do not invent any numbers not given below. No markdown, no headers, plain text only.

Location: {place['name']}, {place.get('country', '')}
Condition: {current['description']}
Temperature: {current['temp']}C (feels like {current['feels_like']}C)
High/Low: {current['temp_max']}C / {current['temp_min']}C
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

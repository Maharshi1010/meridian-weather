import json

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import SavedCity
from . import services
from . import services_ai


def _get_session_key(request):
    """Every visitor gets a session even without logging in - we use
    that session's key to know which favorites belong to them."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def home(request):
    city_query = request.GET.get('city', '').strip()
    session_key = _get_session_key(request)

    context = {
        'favorites': SavedCity.objects.filter(session_key=session_key),
        'query': city_query,
    }

    # Default to a sensible city on first load so the page never looks empty
    if not city_query:
        city_query = 'Pune'

    try:
        place = services.geocode_city(city_query)
        current = services.get_current_weather(place['lat'], place['lon'])
        forecast = services.get_forecast(place['lat'], place['lon'])

        is_daytime = current['sunrise'] <= current['dt'] <= current['sunset']

        # AI summary is a nice-to-have, not critical - if it fails (missing key,
        # API hiccup, etc.) the page still works fine without it.
        ai_summary = None
        try:
            ai_summary = services_ai.summarize_weather(current, place)
        except services_ai.AIUnavailableError:
            pass

        context.update({
            'place': place,
            'current': current,
            'forecast': forecast,
            'daytime': 'day' if is_daytime else 'night',
            'ai_summary': ai_summary,
            'is_favorite': SavedCity.objects.filter(
                session_key=session_key, name=place['name'], country=place['country']
            ).exists(),
        })
    except services.WeatherAPIError as exc:
        messages.error(request, str(exc))

    return render(request, 'weather/home.html', context)


@require_POST
def add_favorite(request):
    session_key = _get_session_key(request)
    name = request.POST.get('name')
    country = request.POST.get('country', '')
    lat = request.POST.get('lat')
    lon = request.POST.get('lon')

    if name and lat and lon:
        SavedCity.objects.get_or_create(
            session_key=session_key, name=name, country=country,
            defaults={'latitude': float(lat), 'longitude': float(lon)},
        )
        messages.success(request, f"{name} added to your favorites.")

    return redirect(f'/?city={name}')


@require_POST
def remove_favorite(request, favorite_id):
    session_key = _get_session_key(request)
    SavedCity.objects.filter(id=favorite_id, session_key=session_key).delete()
    messages.success(request, "Removed from favorites.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def ask_ai(request):
    """
    Answers a free-form question about the weather at a given city, using
    JSON in and out so the frontend can call this without a full page reload.
    Re-fetches weather data server-side rather than trusting anything the
    client sends about current conditions, so the AI is always grounded in
    a fresh, real reading - not something a user could tamper with.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    question = (payload.get('question') or '').strip()
    city_name = (payload.get('city') or '').strip()

    if not question:
        return JsonResponse({'error': 'Please type a question.'}, status=400)
    if not city_name:
        return JsonResponse({'error': 'No city selected.'}, status=400)
    if len(question) > 300:
        return JsonResponse({'error': 'That question is too long.'}, status=400)

    try:
        place = services.geocode_city(city_name)
        current = services.get_current_weather(place['lat'], place['lon'])
        forecast = services.get_forecast(place['lat'], place['lon'])
        answer = services_ai.answer_question(current, place, question, forecast=forecast)
        return JsonResponse({'answer': answer})
    except services.WeatherAPIError as exc:
        return JsonResponse({'error': str(exc)}, status=502)
    except services_ai.AIUnavailableError as exc:
        return JsonResponse({'error': str(exc)}, status=503)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import SavedCity
from . import services


def _get_session_key(request):
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

        context.update({
            'place': place,
            'current': current,
            'forecast': forecast,
            'daytime': 'day' if is_daytime else 'night',
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

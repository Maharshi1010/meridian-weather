# Meridian — Weather Station

A Django + PostgreSQL weather app. Search any city for current conditions and a
5-day forecast, and save favorite cities for quick access.

## How it's built:

```
weather_app/
├── manage.py                  # Django's command-line entry point
├── requirements.txt           # Python packages this project needs
├── .env.example                # Template for your secret config (copy to .env)
├── weatherproject/             # PROJECT settings — the container
│   ├── settings.py             # DB config, installed apps, API key loading
│   └── urls.py                 # Root URL routing
└── weather/                    # APP — the actual feature
    ├── models.py                # SavedCity — the one thing we store in Postgres
    ├── services.py               # Talks to the OpenWeatherMap API
    ├── views.py                  # Connects requests -> services -> templates
    ├── urls.py                   # This app's routes (/, /favorites/add/, ...)
    ├── admin.py                  # Lets you view saved cities in Django admin
    ├── templates/weather/        # HTML (base.html + home.html)
    └── static/weather/           # CSS + JS
```

**Why weather data isn't stored in the database:** weather changes constantly, so
saving it would just go stale. Only your *favorite city list* lives in Postgres —
the actual conditions are fetched live from OpenWeatherMap every time you load
the page.

## 1. Prerequisites

- Python 3.10+
- PostgreSQL installed and running locally
- A free OpenWeatherMap API key: https://openweathermap.org/api
  (sign up → API keys tab → copy the default key. It can take a few minutes to activate.)

## 2. Set up a virtual environment

```bash
cd weather_app
python -m venv venv

# Activate it:
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

## 3. Create the PostgreSQL database

Open `psql` (or pgAdmin) and run:

```sql
CREATE DATABASE weather_db;
```

Use whatever Postgres username/password you already have — you'll put them in `.env` next.

## 4. Configure your environment

```bash
cp .env.example .env
```

Open `.env` and fill in:
- `OPENWEATHER_API_KEY` — your real key from step 1
- `DB_USER` / `DB_PASSWORD` — your local Postgres credentials
- Leave `DB_NAME=weather_db` (or change it to match what you created)

`.env` is already in `.gitignore` — it will never get committed to version control.

## 5. Run migrations

This creates the `SavedCity` table (and Django's built-in tables) inside your Postgres database:

```bash
python manage.py migrate
```

## 6. (Optional) Create an admin account

Lets you view saved cities at `/admin/`:

```bash
python manage.py createsuperuser
```

## 7. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** — search a city, and you should see live weather.

## How the request flow works, end to end

1. You type a city and hit "Read station" → browser sends `GET /?city=Tokyo`
2. `views.home()` receives it, calls `services.geocode_city("Tokyo")` to get coordinates
3. `services.get_current_weather()` and `services.get_forecast()` call OpenWeatherMap
   with those coordinates and return clean Python dictionaries
4. The view passes that data into `home.html`, which renders the temperature,
   wind compass, forecast cards, etc.
5. If you click "Save station," a POST request goes to `/favorites/add/`, which
   writes a row into the `SavedCity` Postgres table, tied to your browser session

## Deploying later

When you're ready to deploy (Render, Railway, etc.), you'll mainly need to:
- Set `DJANGO_DEBUG=False` and add your real domain to `DJANGO_ALLOWED_HOSTS`
- Point `DB_HOST`/`DB_USER`/etc. at your hosted Postgres instance
- Run `python manage.py collectstatic` so static files (CSS/JS) get served properly
- Use a real WSGI server (e.g. `gunicorn weatherproject.wsgi`) instead of `runserver`

We can walk through this together when you get there.

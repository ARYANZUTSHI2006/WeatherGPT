# Atmos — Weather, made clear

A standalone recreation of the hosted Atmos weather dashboard. Built with Python standard-library WSGI, HTML, CSS and vanilla JavaScript. The reference design is recreated, not copied from the original Work source.

## Features
- Worldwide city search and browser geolocation; Celsius/Fahrenheit display
- Current conditions, next 12 hours and selectable 7-day forecasts
- Model-derived air quality (US AQI, PM2.5 and PM10)
- Free English/Hindi briefings, tone and detail controls, source JSON
- Separate official US NWS alerts and threshold-based weather guidance
- Responsive UI, loading/error states, cached API requests

## Run locally (Windows / VS Code)

```powershell
py app.py
```

Open http://127.0.0.1:5000. On macOS/Linux use `python3 app.py`. No third-party packages are required locally.

No API key is required. Internet access is required for live forecast data. Open-Meteo's free service is subject to its terms and usage limits; review them before commercial use.

## Deploy from GitHub

Upload this folder's contents to a repository. Deploy on a Python-capable hosting provider (e.g. Render) with build command `pip install -r requirements.txt` (empty dependency list) and start command `python app.py` (or install Gunicorn separately and use `gunicorn app:app` for production). Use the provider's assigned PORT. GitHub Pages alone cannot run Python. Do not commit secrets or virtual environments.

## Architecture and prompt engineering

Browser → Python JSON API → Open-Meteo geocoding/forecast/air quality or NWS alerts. The free briefing is a deterministic context-injection template with tone, language, and detail controls; it is not an LLM response. See `PROMPTS.md` for an optional LLM design, not implemented in this build. Unlike the reference app, this recreation has no MET Norway fallback or live LLM mode.

## Tests

`python -m unittest discover -s tests -v`

Tests use mocked upstream data to validate routes and errors without internet. For live testing, search for Delhi, London, and New York, change units, select a forecast day, switch language/tone, inspect source metrics, and verify alert status. Browser location requires permission and a secure context (HTTPS or localhost).

## Data and limitations

- Forecasts and geocoding: https://open-meteo.com/
- Air quality: CAMS via Open-Meteo (modeled values, not station observations)
- Official US alerts: https://www.weather.gov/documentation/services-web-api
- India: https://mausam.imd.gov.in/ (external authority link, not an integrated alert feed)
- Other locations: alert coverage is unknown; consult the relevant national authority.
- Weather guidance is not an official warning or a disaster prediction. Missing data never means conditions are safe. Forecasts cached for five minutes; alerts for one minute. Browser geolocation does not determine the country in this build, so its official alert coverage stays unknown until a city is selected.

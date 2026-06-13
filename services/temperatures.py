# -*- coding: utf-8 -*-

import logging
import json
import os
import time
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from flask import Blueprint
from collections import OrderedDict

temperatures_api = Blueprint('temperatures_api', __name__)

logger = logging.getLogger(__name__)

_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.abspath(os.path.join(_FILE_DIR, '..'))

# Optional commercial Open-Meteo API key. When present, the dedicated customer
# endpoint is used (commercial-use licence). Otherwise fall back to the free,
# non-commercial endpoint for development.
try:
    OPENMETEO_KEY = open(os.path.join(_PROJECT_DIR, "openmeteo.key")).read().strip()
except Exception:
    OPENMETEO_KEY = None

if OPENMETEO_KEY:
    OPEN_METEO_BASE_URL = "https://customer-api.open-meteo.com/v1/dwd-icon"
else:
    OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/dwd-icon"

# Last upstream interaction, for /v1/status diagnostics.
_health = {"last_success": None, "last_error": None, "last_error_at": None}


def _record_success():
    _health["last_success"] = int(time.time())


def _record_error(message):
    _health["last_error"] = message
    _health["last_error_at"] = int(time.time())


def get_health():
    from collections import OrderedDict as _OD
    from urllib.parse import urlparse as _up
    return _OD([
        ("commercial", OPENMETEO_KEY is not None),
        ("upstream", _up(OPEN_METEO_BASE_URL).hostname),
        ("last_success", _health["last_success"]),
        ("last_error", _health["last_error"]),
        ("last_error_at", _health["last_error_at"]),
    ])


# Fetch temperature forecast from Open-Meteo DWD ICON API.
def fetch_temperature_forecast(lat: float, lon: float) -> dict:
    url = (
        f"{OPEN_METEO_BASE_URL}"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&hourly=temperature_2m"
        f"&timezone=auto"
        f"&forecast_days=2"
        f"&timeformat=unixtime"
    )

    if OPENMETEO_KEY:
        url += f"&apikey={OPENMETEO_KEY}"

    with urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise Exception(f"Open-Meteo API returned status {response.status}")
        return json.loads(response.read().decode())

def format_temperature_response(data: dict) -> str:
    hourly = data.get('hourly', {})
    hourly_times = hourly.get('time', [])
    hourly_temps = hourly.get('temperature_2m', [])

    if len(hourly_temps) < 47 or len(hourly_times) < 47:
        raise ValueError("Insufficient hourly data received (need at least 47)")

    result = OrderedDict()
    result['first_date'] = hourly_times[0]
    result['temperatures'] = [round(t * 10) for t in hourly_temps]

    return json.dumps(result, separators=(',', ':'))

# Get hourly temperature forecast for today and tomorrow.
#
# Parameters:
# * lat: Latitude (-90 to 90)
# * lon: Longitude (-180 to 180)
#
# Returns:
# * JSON with first_date (UTC timestamp of local midnight) and a flat
#   temperatures array of 47-49 temperature integers in 10ths of degree Celsius.
@temperatures_api.route('/v1/temperatures/<lat>/<lon>', methods=['GET'])
def temperatures(lat, lon):
    def inner(lat_str, lon_str):
        try:
            lat = float(lat_str)
        except ValueError:
            return '{"error":"Invalid latitude format"}', 400

        try:
            lon = float(lon_str)
        except ValueError:
            return '{"error":"Invalid longitude format"}', 400

        if not (-90 <= lat <= 90):
            return '{"error":"Latitude must be between -90 and 90"}', 400

        if not (-180 <= lon <= 180):
            return '{"error":"Longitude must be between -180 and 180"}', 400

        # Fetch and format temperature data
        try:
            data = fetch_temperature_forecast(lat, lon)
            response = format_temperature_response(data)
            _record_success()
            return response, 200
        except HTTPError as e:
            logger.error(f"Open-Meteo HTTP error: {e.code} - {e.reason}")
            _record_error(f"HTTPError: {e.code} {e.reason}")
            if e.code == 400:
                return '{"error":"Invalid coordinates"}', 400
            return '{"error":"Weather service unavailable"}', 503
        except URLError as e:
            logger.error(f"Open-Meteo connection error: {e.reason}")
            _record_error(f"URLError: {e.reason}")
            return '{"error":"Weather service unavailable"}', 503
        except ValueError as e:
            logger.error(f"Data parsing error: {e}")
            _record_error(f"ValueError: {e}")
            return '{"error":"Invalid response from weather service"}', 503
        except Exception as e:
            logger.error(f"Unexpected error fetching temperatures: {e}", exc_info=True)
            _record_error(f"{type(e).__name__}: {e}")
            return '{"error":"Internal server error"}', 500

    resp, status = inner(lat, lon)
    return resp, status, {'Content-Type': 'application/json; charset=utf-8'}

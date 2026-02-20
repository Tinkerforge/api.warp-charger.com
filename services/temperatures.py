# -*- coding: utf-8 -*-

import logging
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from flask import Blueprint
from datetime import datetime, timezone
from collections import OrderedDict

temperatures_api = Blueprint('temperatures_api', __name__)

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/dwd-icon"


# Fetch temperature forecast from Open-Meteo DWD ICON API.
def fetch_temperature_forecast(lat: float, lon: float) -> dict:
    url = (
        f"{OPEN_METEO_BASE_URL}"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&hourly=temperature_2m"
        f"&timezone=UTC"
        f"&forecast_days=2"
        f"&timeformat=unixtime"
    )

    with urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise Exception(f"Open-Meteo API returned status {response.status}")
        return json.loads(response.read().decode())

def format_temperature_response(data: dict) -> str:
    daily = data.get('daily', {})
    times = daily.get('time', [])
    temp_max = daily.get('temperature_2m_max', [])
    temp_min = daily.get('temperature_2m_min', [])

    if len(times) < 2 or len(temp_max) < 2 or len(temp_min) < 2:
        raise ValueError("Insufficient forecast data received")

    # Compute daily averages from hourly temperature data (24 values per day)
    hourly = data.get('hourly', {})
    hourly_temps = hourly.get('temperature_2m', [])

    if len(hourly_temps) < 48:
        raise ValueError("Insufficient hourly data received")

    def day_avg(day_idx):
        start = day_idx * 24
        day_temps = hourly_temps[start:start + 24]
        return round(sum(day_temps) / len(day_temps), 1)

    def day_data(idx):
        od = OrderedDict()
        od['date'] = times[idx]
        od['min'] = temp_min[idx]
        od['max'] = temp_max[idx]
        od['avg'] = day_avg(idx)
        return od

    result = OrderedDict()
    result['today'] = day_data(0)
    result['tomorrow'] = day_data(1)

    return json.dumps(result, separators=(',', ':'))

# Get temperature forecast (min, max, avg) for today and tomorrow.
#
# Parameters:
# * lat: Latitude (-90 to 90)
# * lon: Longitude (-180 to 180)
#
# Returns:
# * JSON with today and tomorrow temperature data.
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
            return response, 200
        except HTTPError as e:
            logger.error(f"Open-Meteo HTTP error: {e.code} - {e.reason}")
            if e.code == 400:
                return '{"error":"Invalid coordinates"}', 400
            return '{"error":"Weather service unavailable"}', 503
        except URLError as e:
            logger.error(f"Open-Meteo connection error: {e.reason}")
            return '{"error":"Weather service unavailable"}', 503
        except ValueError as e:
            logger.error(f"Data parsing error: {e}")
            return '{"error":"Invalid response from weather service"}', 503
        except Exception as e:
            logger.error(f"Unexpected error fetching temperatures: {e}", exc_info=True)
            return '{"error":"Internal server error"}', 500

    resp, status = inner(lat, lon)
    return resp, status, {'Content-Type': 'application/json; charset=utf-8'}

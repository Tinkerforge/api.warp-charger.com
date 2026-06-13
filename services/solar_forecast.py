# -*- coding: utf-8 -*-

# Solar / PV yield forecast service.
#
# This is a server-side replacement for the firmware's direct use of the free
# forecast.solar "Public" tier (1 h resolution, 12 calls/h per IP).
# We derive the PV yield ourselves from the high
# resolution DWD ICON modeld via the Open-Meteo API and its
# global_tilted_irradiance (GTI) variable.
#
# Two endpoints are offered:
#
#   GET /estimate/<lat>/<lon>/<dec>/<az>/<kwp>
#       forecast.solar-compatible response. Existing firmware works unchanged by
#       only pointing its "api_url" at https://api.warp-charger.com/.
#
#   GET /v1/solar_forecast/<lat>/<lon>/<dec>/<az>/<wp>
#       Clean WARP-native response matching the firmware push schema
#       ({first_date, resolution, forecast:[Wh per hour]}).
#
# Both share an in-memory cache. The cache is keyed on the *quantized*
# coordinates and panel orientation and stores the orientation-specific
# irradiance (Wh/m² per hour). The actual peak power (wp) is applied at response
# time, so two installations that differ only in size share one upstream call.
#
# NOTE: like day_ahead_prices, the in-memory cache assumes gunicorn runs with a
# single worker (-w 1).

import json
import logging
import os
import threading
import time
from collections import OrderedDict
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from flask import Blueprint

solar_forecast_api = Blueprint('solar_forecast_api', __name__)

logger = logging.getLogger(__name__)

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(FILE_DIR, '..'))

# Optional commercial Open-Meteo API key. If present, the dedicated customer
# endpoint is used (commercial-use licence, no daily rate limit). If absent we
# fall back to the non-commercial endpoint for development.
try:
    OPENMETEO_KEY = open(os.path.join(PROJECT_DIR, "openmeteo.key")).read().strip()
except Exception:
    OPENMETEO_KEY = None

if OPENMETEO_KEY:
    OPEN_METEO_BASE_URL = "https://customer-api.open-meteo.com/v1/dwd-icon"
else:
    OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/dwd-icon"


# Performance ratio: lumps inverter, wiring, soiling and temperature losses into
# a single constant. ~0.85 is a typical value for a well installed rooftop
# system in Germany. Could be refined by local temperatur factor.
PERFORMANCE_RATIO = 0.85

# Number of forecast hours returned (today + tomorrow). The firmware buckets the
# forecast.solar response into 48 hourly slots (today + tomorrow) and the push
# schema is capped at 49 entries, so 48 is the natural horizon.
HORIZON_HOURS = 48

# We request more days than HORIZON_HOURS needs. GTI is a "preceding hour mean",
# so the energy of clock-hour k is sample k+1; to fill 48 hours we need 49
# samples. 3 days (72 samples) gives ample headroom.
FORECAST_DAYS = 3


# Quantization of the cache key. The values are coarse enough to collapse many
# nearby/identical installations onto one upstream call, while staying well
# below the spatial resolution of the underlying weather model.
# NOTE: The quantization currently uses the full precision.
#       We need to do some testing if it is worthwile to reduce the precision.
LAT_LON_QUANT = 0.0001 # degrees (~7m-11m)
TILT_QUANT = 1         # degrees
AZIMUTH_QUANT = 1      # degrees

# Align roughly with the ICON model update cadence (every 3 h). A device polls
# at most every ~2 h, so it never sees data older than one model run.
CACHE_TTL_SECONDS = 3 * 3600

# Hard cap on cache entries to bound memory; evicted least-recently-fetched.
MAX_CACHE_ENTRIES = 50000

# key (tuple) -> dict(first_date, utc_offset, gti, place, fetched)
_cache = OrderedDict()
_cache_lock = threading.Lock()


def _quantize(value, step):
    return round(value / step) * step


def _cache_key(lat, lon, dec, az):
    return (
        round(_quantize(lat, LAT_LON_QUANT), 4),
        round(_quantize(lon, LAT_LON_QUANT), 4),
        int(_quantize(dec, TILT_QUANT)),
        int(_quantize(az, AZIMUTH_QUANT)),
    )


def _build_url(lat, lon, dec, az):
    url = (
        f"{OPEN_METEO_BASE_URL}"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&hourly=global_tilted_irradiance"
        f"&tilt={dec}"
        f"&azimuth={az}"
        f"&timezone=auto"
        f"&forecast_days={FORECAST_DAYS}"
        f"&timeformat=unixtime"
    )
    if OPENMETEO_KEY:
        url += f"&apikey={OPENMETEO_KEY}"
    return url


def fetch_irradiance(lat, lon, dec, az):
    """Fetch the tilted-plane irradiance forecast from Open-Meteo.

    Returns a dict with:
      * first_date:  unix timestamp (GMT) of local midnight today
      * utc_offset:  timezone offset in seconds (to derive local wall-clock)
      * gti:         list of Wh/m² per hour (preceding-hour mean), aligned so
                     that gti[i] is the energy during (time[i]-1h, time[i]]
      * place:       human readable location string (timezone name)
    """
    url = _build_url(lat, lon, dec, az)
    with urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise Exception(f"Open-Meteo API returned status {response.status}")
        data = json.loads(response.read().decode())

    hourly = data.get('hourly', {})
    times = hourly.get('time', [])
    gti = hourly.get('global_tilted_irradiance', [])

    if not times or not gti or len(times) != len(gti):
        raise ValueError("Open-Meteo response missing or malformed hourly GTI data")

    # Null values (e.g. before sunrise) are reported as None -> treat as 0.
    gti = [float(v) if v is not None else 0.0 for v in gti]

    return {
        'first_date': int(times[0]),
        'utc_offset': int(data.get('utc_offset_seconds', 0)),
        'gti': gti,
        'place': data.get('timezone', f"{lat},{lon}"),
    }


def get_cached_irradiance(lat, lon, dec, az):
    """Return a (possibly cached) irradiance entry for the quantized request."""
    key = _cache_key(lat, lon, dec, az)
    now = time.time()

    with _cache_lock:
        entry = _cache.get(key)
        if entry is not None and (now - entry['fetched']) < CACHE_TTL_SECONDS:
            _cache.move_to_end(key)
            return entry

    # Fetch outside the lock (network IO). With -w 1 a small amount of duplicate
    # work on a cold cache is acceptable and keeps the lock contention-free.
    qlat, qlon, qdec, qaz = key
    entry = fetch_irradiance(qlat, qlon, qdec, qaz)
    entry['fetched'] = now

    with _cache_lock:
        _cache[key] = entry
        _cache.move_to_end(key)
        while len(_cache) > MAX_CACHE_ENTRIES:
            _cache.popitem(last=False)

    return entry


def compute_forecast(entry, wp):
    """Convert cached irradiance into a list of Wh produced per clock hour.

    forecast[k] = energy during the clock hour starting at first_date + k*3600.

    Because GTI is a preceding-hour mean, the energy of clock-hour k equals the
    sample at index k+1 (the hour *ending* at first_date + (k+1)*3600).
    """
    gti = entry['gti']
    factor = (wp / 1000.0) * PERFORMANCE_RATIO  # Wh per (Wh/m²)
    forecast = []
    for k in range(HORIZON_HOURS):
        src = k + 1
        if src >= len(gti):
            break
        forecast.append(int(round(gti[src] * factor)))
    return forecast


class ParamError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def _parse_common(lat_str, lon_str, dec_str, az_str):
    try:
        lat = float(lat_str)
    except ValueError:
        raise ParamError("Invalid latitude format", 404)
    try:
        lon = float(lon_str)
    except ValueError:
        raise ParamError("Invalid longitude format", 404)
    try:
        dec = float(dec_str)
    except ValueError:
        raise ParamError("Invalid declination format", 422)
    try:
        az = float(az_str)
    except ValueError:
        raise ParamError("Invalid azimuth format", 422)

    if not (-90 <= lat <= 90):
        raise ParamError("Latitude must be between -90 and 90", 404)
    if not (-180 <= lon <= 180):
        raise ParamError("Longitude must be between -180 and 180", 404)
    if not (0 <= dec <= 90):
        raise ParamError("Declination must be between 0 and 90", 422)
    if not (-180 <= az <= 180):
        raise ParamError("Azimuth must be between -180 and 180", 422)

    return lat, lon, dec, az


def _parse_power(power_str, scale):
    """Parse the peak-power path segment and return watt-peak.

    scale=1000 for kWp segments (compat endpoint), scale=1 for Wp segments.
    """
    try:
        value = float(power_str)
    except ValueError:
        raise ParamError("Invalid power format", 422)
    wp = value * scale
    if not (0 < wp <= 100_000_000):
        raise ParamError("Power out of range", 422)
    return wp


def format_forecast_solar_response(entry, forecast):
    """Build a forecast.solar-compatible JSON string.

    The firmware reads result.watt_hours_period (keyed by local "YYYY-MM-DD
    HH:MM:SS"), message.code, message.info.place and message.ratelimit.period.
    """
    # Local wall-clock of the first slot = local midnight today.
    local_midnight = entry['first_date'] + entry['utc_offset']

    watt_hours_period = OrderedDict()
    for k, wh in enumerate(forecast):
        local_ts = local_midnight + k * 3600
        tm = time.gmtime(local_ts)
        key = time.strftime("%Y-%m-%d %H:%M:%S", tm)
        watt_hours_period[key] = wh

    result = OrderedDict()
    result['watt_hours_period'] = watt_hours_period

    message = OrderedDict()
    message['code'] = 0
    message['type'] = 'success'
    message['text'] = ''
    message['info'] = OrderedDict([('place', entry['place'])])
    # period drives the firmware's next poll: next_check = now + period*2/60 min.
    # 3600 s => the firmware polls again in ~2 h, matching our cache cadence.
    message['ratelimit'] = OrderedDict([
        ('period', 3600),
        ('limit', 100),
        ('remaining', 100),
    ])

    od = OrderedDict()
    od['result'] = result
    od['message'] = message
    return json.dumps(od, separators=(',', ':'))


@solar_forecast_api.route('/estimate/<lat>/<lon>/<dec>/<az>/<kwp>', methods=['GET'])
def estimate(lat, lon, dec, az, kwp):
    def inner():
        try:
            flat, flon, fdec, faz = _parse_common(lat, lon, dec, az)
            wp = _parse_power(kwp, 1000)  # kWp segment
        except ParamError as e:
            return json.dumps({"message": {"code": e.status, "type": "error", "text": e.message}}), e.status

        try:
            entry = get_cached_irradiance(flat, flon, fdec, faz)
            forecast = compute_forecast(entry, wp)
            return format_forecast_solar_response(entry, forecast), 200
        except HTTPError as e:
            logger.error(f"Open-Meteo HTTP error: {e.code} - {e.reason}")
            return '{"error":"Forecast service unavailable"}', 503
        except (URLError, ValueError) as e:
            logger.error(f"Open-Meteo error: {e}")
            return '{"error":"Forecast service unavailable"}', 503
        except Exception as e:
            logger.error(f"Unexpected error in solar forecast estimate: {e}", exc_info=True)
            return '{"error":"Internal server error"}', 500

    resp, status = inner()
    return resp, status, {'Content-Type': 'application/json; charset=utf-8'}


def format_native_response(entry, forecast):
    od = OrderedDict()
    od['first_date'] = entry['first_date']
    od['resolution'] = 60  # minutes
    od['forecast'] = forecast  # Wh per hour
    return json.dumps(od, separators=(',', ':'))


@solar_forecast_api.route('/v1/solar_forecast/<lat>/<lon>/<dec>/<az>/<wp>', methods=['GET'])
def solar_forecast(lat, lon, dec, az, wp):
    def inner():
        try:
            flat, flon, fdec, faz = _parse_common(lat, lon, dec, az)
            wpeak = _parse_power(wp, 1)  # Wp segment
        except ParamError as e:
            return '{"error":"' + e.message + '"}', e.status

        try:
            entry = get_cached_irradiance(flat, flon, fdec, faz)
            forecast = compute_forecast(entry, wpeak)
            return format_native_response(entry, forecast), 200
        except HTTPError as e:
            logger.error(f"Open-Meteo HTTP error: {e.code} - {e.reason}")
            return '{"error":"Forecast service unavailable"}', 503
        except (URLError, ValueError) as e:
            logger.error(f"Open-Meteo error: {e}")
            return '{"error":"Forecast service unavailable"}', 503
        except Exception as e:
            logger.error(f"Unexpected error in solar forecast: {e}", exc_info=True)
            return '{"error":"Internal server error"}', 500

    resp, status = inner()
    return resp, status, {'Content-Type': 'application/json; charset=utf-8'}

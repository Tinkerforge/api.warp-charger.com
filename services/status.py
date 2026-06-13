# -*- coding: utf-8 -*-

# Diagnostic status endpoint.
#
#   GET /v1/status             -> full status report
#   GET /v1/status?check=1     -> additionally performs a (cached) live request to
#                                 the configured Open-Meteo upstream to confirm the
#                                 API key is accepted (openmeteo_key_valid)

import json
import threading
import time
from collections import OrderedDict
from urllib.request import urlopen

from flask import Blueprint, request

from . import temperatures, solar_forecast, day_ahead_prices

status_api = Blueprint('status_api', __name__)

# The live key probe is cached so that this public endpoint cannot be abused to
# generate unbounded upstream traffic.
_PROBE_TTL = 600  # seconds
_probe_lock = threading.Lock()
_probe = {"ts": 0.0, "valid": None}


def _probe_key():
    now = time.time()
    with _probe_lock:
        if _probe["valid"] is not None and (now - _probe["ts"]) < _PROBE_TTL:
            return _probe["valid"]

    base = solar_forecast.OPEN_METEO_BASE_URL
    url = (f"{base}?latitude=51.88&longitude=8.63"
           f"&hourly=temperature_2m&forecast_days=1&timeformat=unixtime")
    if solar_forecast.OPENMETEO_KEY:
        url += f"&apikey={solar_forecast.OPENMETEO_KEY}"

    valid = False
    try:
        with urlopen(url, timeout=10) as r:
            valid = (r.status == 200)
    except Exception:
        valid = False

    with _probe_lock:
        _probe["ts"] = now
        _probe["valid"] = valid
    return valid


@status_api.route('/v1/status', methods=['GET'])
def status():
    od = OrderedDict()
    od['now'] = int(time.time())
    od['solar_forecast'] = solar_forecast.get_health()
    od['temperatures'] = temperatures.get_health()
    od['day_ahead_prices'] = day_ahead_prices.get_health()
    if request.args.get('check') == '1':
        od['openmeteo_key_valid'] = _probe_key()

    return json.dumps(od, separators=(',', ':')), 200, \
        {'Content-Type': 'application/json; charset=utf-8'}

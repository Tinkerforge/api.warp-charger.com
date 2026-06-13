# -*- coding: utf-8 -*-

# Diagnostic status endpoint.
#
#   GET /v1/status             -> full status report (JSON)
#   GET /v1/status?check=1     -> additionally performs a (cached) live request to
#                                 the configured Open-Meteo upstream to confirm the
#                                 API key is accepted (openmeteo_key_valid)
#   GET /status                -> human-readable HTML status page (?check=1 also works)

import datetime
import json
import threading
import time
from collections import OrderedDict
from urllib.request import urlopen

from flask import Blueprint, abort, redirect, render_template, request

from . import temperatures, solar_forecast, day_ahead_prices
from i18n import get_translations, detect_language, SUPPORTED_LANGUAGES

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


def build_status(check=False):
    od = OrderedDict()
    od['now'] = int(time.time())
    od['solar_forecast'] = solar_forecast.get_health()
    od['temperatures'] = temperatures.get_health()
    od['day_ahead_prices'] = day_ahead_prices.get_health()
    if check:
        od['openmeteo_key_valid'] = _probe_key()
    return od


@status_api.route('/v1/status', methods=['GET'])
def status():
    od = build_status(check=request.args.get('check') == '1')
    return json.dumps(od, separators=(',', ':')), 200, \
        {'Content-Type': 'application/json; charset=utf-8'}


@status_api.route('/status', methods=['GET'])
def status_page_redirect():
    lang = detect_language(request.headers.get('Accept-Language', ''))
    suffix = '?check=1' if request.args.get('check') == '1' else ''
    return redirect(f'/{lang}/status{suffix}')


@status_api.route('/<lang>/status', methods=['GET'])
def status_page(lang):
    if lang not in SUPPORTED_LANGUAGES:
        abort(404)
    check = request.args.get('check') == '1'
    od = build_status(check=check)
    t = get_translations(lang)
    return render_template('status.html', s=od, check=check, t=t, lang=lang)


@status_api.app_template_filter('ts')
def _fmt_ts(value):
    if not value:
        return '\u2014'  # em dash
    return datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d %H:%M:%S')


@status_api.app_template_filter('ago')
def _fmt_ago(value):
    if not value:
        return ''
    delta = int(time.time()) - int(value)
    future = delta < 0
    delta = abs(delta)
    if delta < 60:
        s = f"{delta}s"
    elif delta < 3600:
        s = f"{delta // 60}m {delta % 60}s"
    elif delta < 86400:
        s = f"{delta // 3600}h {(delta % 3600) // 60}m"
    else:
        s = f"{delta // 86400}d {(delta % 86400) // 3600}h"
    return f"in {s}" if future else f"{s} ago"

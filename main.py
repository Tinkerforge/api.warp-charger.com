#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from services import day_ahead_prices, temperatures, solar_forecast, status
from i18n import get_translations, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from flask import Flask, Blueprint, render_template, request, redirect, abort
import logging
import os
import threading
import time
import socket

DEFAULT_PORT = 5002


def _detect_language():
    accept = request.headers.get('Accept-Language', '')
    best_lang = DEFAULT_LANGUAGE
    best_q = -1
    for part in accept.split(','):
        part = part.strip()
        if ';' in part:
            lang_tag, q_str = part.split(';', 1)
            try:
                q = float(q_str.strip().replace('q=', ''))
            except ValueError:
                q = 0
        else:
            lang_tag = part
            q = 1.0
        lang_tag = lang_tag.strip().split('-')[0].lower()
        if lang_tag in SUPPORTED_LANGUAGES and q > best_q:
            best_lang = lang_tag
            best_q = q
    return best_lang


main_api = Blueprint('main_api', __name__)

@main_api.route("/")
def home_redirect():
    lang = _detect_language()
    return redirect(f'/{lang}/')

@main_api.route("/<lang>/")
def home(lang):
    if lang not in SUPPORTED_LANGUAGES:
        abort(404)
    t = get_translations(lang)
    return render_template('index.html', t=t, lang=lang)

def backend_tasks():
    global running
    day_ahead_prices.update()
    running = True

    while running:
        time.sleep(5*60)
        try:
            day_ahead_prices.update()
        except:
            logging.error("Exception during day ahead price update", exc_info=True)

# Flask init
app = Flask(__name__)
app.register_blueprint(main_api)
app.register_blueprint(day_ahead_prices.day_ahead_prices_api)
app.register_blueprint(temperatures.temperatures_api)
app.register_blueprint(solar_forecast.solar_forecast_api)
app.register_blueprint(status.status_api)
app.config["JSON_SORT_KEYS"] = False

port = int(os.environ.get('PORT', DEFAULT_PORT))
running = False

backend_thread = threading.Thread(target=backend_tasks)
logging.basicConfig(filename='debug.log', level=logging.DEBUG, format="[%(asctime)s %(levelname)-8s%(filename)s:%(lineno)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
backend_thread.start()

# Wait for first data update
while not running:
    time.sleep(1)

def _find_free_port(start):
    p = start
    while True:
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('::', p))
            s.close()
            return p
        except OSError:
            print(f"Port {p} already in use, trying {p + 1}")
            p += 1


if __name__ == "__main__":
    import local_https
    from werkzeug.serving import make_server
    from werkzeug.debug import DebuggedApplication

    # Pick free ports for the plain-HTTP and HTTPS listeners.
    port = _find_free_port(port)
    os.environ['PORT'] = str(port)
    https_port = _find_free_port(local_https.DEFAULT_HTTPS_PORT)

    # Auto-generate (or reuse) a self-signed cert covering this machine's LAN IPs
    # so an ESP32 can be told to trust it (see upload_cert.py).
    cert_path, key_path, ips, regenerated = local_https.ensure_cert()

    app.debug = True
    wsgi = DebuggedApplication(app, evalex=True)

    http_srv = make_server('0.0.0.0', port, wsgi, threaded=True)
    https_srv = make_server('0.0.0.0', https_port, wsgi, threaded=True,
                            ssl_context=(cert_path, key_path))

    print(f" * HTTP  on http://0.0.0.0:{port}/")
    print(f" * HTTPS on https://0.0.0.0:{https_port}/  (self-signed)")
    if ips:
        for ip in ips:
            print(f"     reachable at  https://{ip}:{https_port}/")
        print(f" * Upload the cert to an ESP32:  ./upload_cert.py <esp-ip>")
    else:
        print(" * Warning: no non-loopback IPv4 address detected for the HTTPS cert")
    if regenerated:
        print(" * (generated a fresh self-signed certificate)")

    http_thread = threading.Thread(target=http_srv.serve_forever, daemon=True)
    http_thread.start()
    try:
        https_srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        https_srv.shutdown()
        http_srv.shutdown()

    running = False
    backend_thread.join()

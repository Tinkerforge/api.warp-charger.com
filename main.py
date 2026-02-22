#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from services import day_ahead_prices, temperatures
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
app.config["JSON_SORT_KEYS"] = False

port = int(os.environ.get('PORT', DEFAULT_PORT))
running = False

backend_thread = threading.Thread(target=backend_tasks)
logging.basicConfig(filename='debug.log', level=logging.DEBUG, format="[%(asctime)s %(levelname)-8s%(filename)s:%(lineno)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
backend_thread.start()

# Wait for first data update
while not running:
    time.sleep(1)

if __name__ == "__main__":
    # Only scan for a free port in the main process, not in the
    # reloader child (which inherits PORT via the environment).
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        while True:
            try:
                s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                s.bind(('::', port))
                s.close()
                break
            except OSError:
                print(f"Port {port} already in use, trying {port + 1}")
                port += 1
        os.environ['PORT'] = str(port)
        print(f" * Running on http://localhost:{port}/")

    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=port)

    running = False
    backend_thread.join()

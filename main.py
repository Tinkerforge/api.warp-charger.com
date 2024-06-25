#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from services import day_ahead_prices
from flask import Flask, Blueprint
import logging
import os
import threading
import time

DEFAULT_PORT = 5000

main_api = Blueprint('main_api', __name__)
@main_api.route("/")
def home():
    return "<html>This is api.warp-charger.com.</br>This API is used by WARP Chargers to obtain relevant public information like day ahead prices.</html>"

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
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=port)

    running = False
    backend_thread.join()

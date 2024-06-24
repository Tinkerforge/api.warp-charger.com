#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sqlite3
import entsoe
from entsoe import EntsoePandasClient
import pandas as pd
from flask import Flask, jsonify, g
from datetime import datetime, timedelta

DEFAULT_PORT = 5000
FILE_DIR = os.path.dirname(os.path.realpath(__file__))
PROJET_DIR = os.path.abspath(os.path.join(FILE_DIR, '..'))
WARP_DB_FILE = os.path.join(PROJET_DIR, "warp.db")
ENTSOE_KEY = open(os.path.join(PROJET_DIR, "entsoe.key")).read().strip()

logger = logging.getLogger(__name__)

# Flask init
app = Flask(__name__)
port = int(os.environ.get('PORT', DEFAULT_PORT))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(WARP_DB_FILE)
    return db

# TODO: Only allow one update per x minutes per date
def update_day_ahead_prices(country, resolution, date):
    try:
        # Currently only DE_LU is supported
        if country in ('de', 'lu'):
            country_code = 'DE_LU'
        elif country == 'at':
            country_code = 'AT'
        else:
            logging.warning("Country not supported: {0}".format(country))
            return None

        start  = pd.Timestamp(date, tz='Europe/Berlin')
        end    = start + timedelta(minutes=60*24-1)
        client = EntsoePandasClient(api_key=ENTSOE_KEY)
        ts     = client.query_day_ahead_prices('DE_LU', start=start, end=end, resolution=resolution)
        data   = ts.to_list()
        # Check if data has valid number of entries
        if resolution == '15min' and len(data) != 4*24:
            logging.warning("Invalid number of entries for 15min: {0}".format(len(data)))
            return None
        if resolution == '60min' and len(data) != 24:
            logging.warning("Invalid number of entries for 60min: {0}".format(len(data)))
            return None

        # convert from cent in float to centicent in int
        data_str = ','.join([str(int(i*100)) for i in data])
        logging.debug("Discovered new day ahead prices for {0}: {1}".format(date, data_str))

        con = get_db()
        cur = con.cursor()
        logging.debug("Inserting new day ahead prices for {0} into sqlite".format(date))
        cur.execute("INSERT INTO day_ahead_prices (country, resolution, date, data) VALUES (?, ?, ?, ?)", (country, resolution, date, data_str))
        con.commit()
    except entsoe.exceptions.NoMatchingDataError:
        logging.debug('No matching data in entso-e database found for date {0}'.format(date))
        return None
    except:
        logging.error("Exception during entso-e query", exc_info=True)
        return None

    return data_str

def get_day_ahead_prices(country, resolution, date):
    cur = get_db().cursor()
    res = cur.execute("SELECT data FROM day_ahead_prices WHERE country = ? AND resolution = ? AND date = ?", (country, resolution, date))
    data = res.fetchone()
    logging.debug("data sqlite: {0}".format(data))
    if data == None:
        logging.debug("No data found in sqlite for date {0}".format(date))
        data = update_day_ahead_prices(country, resolution, date)
        logging.debug("data entso-e: {0}".format(data))
    return data

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def home():
    return "<html>This is api.warp-charger.com.</br>This API can be used by WARP Charger to obtain relevant public information like day ahead prices."

# TODO: Rate limite per IP
@app.route('/day_ahead_prices/<country>/<resolution>/<date>', methods=['GET'])
def day_ahead_prices(country, resolution, date):
    country    = country.lower()
    resolution = resolution.lower()

    if not country in ('de', 'lu', 'at'):
        logging.info("Country not supported: {0}".format(country))
        return jsonify({"error": "Country not supported"}), 400
    if not resolution in('15min', '60min'):
        logging.info("Resolution not supported: {0}".format(resolution))
        return jsonify({"error": "Resolution not supported"}), 400
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logging.info("Date format not supported: {0}".format(date))
        return jsonify({"error": "Date format not supported"}), 400

    prices = get_day_ahead_prices(country, resolution, date)
    if prices == None:
        return jsonify({"error": "Data not found (too far into the future?)"}), 404

    return jsonify({"date": date, "prices": prices}), 200


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host="0.0.0.0", port=port)

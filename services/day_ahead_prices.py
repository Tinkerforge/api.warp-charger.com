# -*- coding: utf-8 -*-

import logging
import os
from urllib.request import urlopen
from xml.etree import ElementTree
import pandas as pd
from flask import Blueprint
from datetime import datetime, timedelta, timezone
import time
import json
from collections import OrderedDict
import re

day_ahead_prices_api = Blueprint('day_ahead_prices_api', __name__)

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
PROJET_DIR = os.path.abspath(os.path.join(FILE_DIR, '..'))
WARP_DB_FILE = os.path.join(PROJET_DIR, "warp.db")
ENTSOE_KEY = open(os.path.join(PROJET_DIR, "entsoe.key")).read().strip()

logger = logging.getLogger(__name__)

DAY_AHEAD_PRICE_NOT_FOUND   = '{"error":"Data not found"}', 404
DAY_AHEAD_PRICE_DE_LU_15MIN = 0
DAY_AHEAD_PRICE_DE_LU_60MIN = 1
DAY_AHEAD_PRICE_AT_15MIN    = 2
DAY_AHEAD_PRICE_AT_60MIN    = 3

def daps():
    yield DAY_AHEAD_PRICE_DE_LU_15MIN, '10Y1001A1001A82H', 'PT15M' # DE_LU
    yield DAY_AHEAD_PRICE_DE_LU_60MIN, '10Y1001A1001A82H', 'PT60M' # DE_LU
    yield DAY_AHEAD_PRICE_AT_15MIN,    '10YAT-APG------L', 'PT15M' # AT
    yield DAY_AHEAD_PRICE_AT_60MIN,    '10YAT-APG------L', 'PT60M' # AT

dap_list = [DAY_AHEAD_PRICE_NOT_FOUND]*4

def parse_timeseries(xml_text, resolution, value_key='price.amount'):
    resolution_map = {
        'PT60M': pd.Timedelta(60, 'min'),
        'P1Y'  : pd.Timedelta(365,'day'),
        'PT15M': pd.Timedelta(15, 'min'),
        'PT30M': pd.Timedelta(30, 'min'),
        'P1D'  : pd.Timedelta(1,  'day'),
        'P7D'  : pd.Timedelta(7,  'day'),
        'P1M'  : pd.Timedelta(30, 'day'),
    }
    pdres       = resolution_map[resolution]
    time_stamps = []
    values      = []
    xml_text    = re.sub(' xmlns="[^"]+"', '', xml_text, count=1) #Remove namespace
    root        = ElementTree.fromstring(xml_text)
    for time_serie in root.findall('TimeSeries'):
        #curve_type = time_serie.find('curveType').text
        for period in time_serie.findall('Period'):
            start_time = pd.Timestamp(period.find('timeInterval').find('start').text)
            if period.find('resolution').text == resolution:
                for point in period.findall('Point'):
                    position = int(point.find('position').text)-1
                    value    = float(point.find(value_key).text)
                    time_stamps.append(start_time+position*pdres)
                    values.append(value)

    # Fill ts with missing values
    ts = pd.Series(data=values,index=time_stamps)
    if len(ts) == 0:
        return ts
    return ts.resample(pdres).ffill()

def get_dayahead_prices(api_key: str, area_code: str, start: datetime, end: datetime, resolution: str):
    fmt = '%Y%m%d%H00'  # Minutes must be 00, otherwise "HTTP 400 bad request" is returned.
    url = f'https://web-api.tp.entsoe.eu/api?securityToken={api_key}&documentType=A44&in_Domain={area_code}' \
          f'&out_Domain={area_code}&periodStart={start.strftime(fmt)}&periodEnd={end.strftime(fmt)}'

    with urlopen(url) as response:  # Raises URLError
        if response.status != 200:
            raise Exception(f"{response.status=}")
        xml_str = response.read().decode()
        result = parse_timeseries(xml_str, resolution)

    return result

def update_day_ahead_prices(country_code, resolution):
    logging.debug("Getting day ahead prices for country {0} with resolution {1}".format(country_code, resolution))
    try:
        start = pd.Timestamp.today(tz='Europe/Berlin').replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)

        ts     = get_dayahead_prices(ENTSOE_KEY, country_code, start, end, resolution)
        data   = ts.to_list()
        # Check if data has valid number of entries
        if resolution == '15min' and len(data) < 23*4:
            logging.warning("Invalid number of entries for 15min: {0}".format(len(data)))
            return None
        if resolution == '60min' and len(data) < 23:
            logging.warning("Invalid number of entries for 60min: {0}".format(len(data)))
            return None

        # convert from cent in float to centicent in int
        first_date_ts = int(start.timestamp())
        prices = [int(i*100) for i in data]
        # If we got day ahead prices ask again tomorrow, else ask again today
        if (resolution == '15min' and len(data) < 25*4) or (resolution == '60min' and len(data) < 25):
            next_date = start.replace(hour=13, minute=30, second=0, microsecond=0)
        else:
            next_date = (start + timedelta(days=1)).replace(hour=13, minute=30, second=0, microsecond=0)
        next_date_ts = int(next_date.timestamp())
        logging.debug("Discovered new day ahead prices for {0}/{1}: {2}, next: {3}/{4}".format(str(start), str(first_date_ts), str(prices), str(next_date), str(next_date_ts)))

    except:
        logging.error("Exception during entso-e query", exc_info=True)
        return None

    # Generate odered json without spaces
    od = OrderedDict()
    od['first_date'] = first_date_ts
    od['prices']     = prices
    od['next_date']  = next_date_ts
    return json.dumps(od, separators=(',', ':')), 200

def update_day_ahead_prices_with_retry(country_code, resolution, retries=5):
    for retry in range(retries):
        value = update_day_ahead_prices(country_code, resolution)
        if value != None:
            return value
        # Wait one minute more with every retry 
        time.sleep(60*retry)
    return DAY_AHEAD_PRICE_NOT_FOUND

def is_update_necessary(dap, min_price_list_length):
    try:
        if dap == None:
            logging.debug("Update because dap == None")
            return True

        if type(dap) != tuple:
            logging.debug("Update because dap != tuple ({0})".format(str(dap)))
            return True

        if dap == DAY_AHEAD_PRICE_NOT_FOUND:
            logging.debug("Update because dap == DAY_AHEAD_PRICE_NOT_FOUND")
            return True

        dap0_dict = json.loads(dap[0])
        dap0_next_date = dap0_dict.get('next_date')
        dap0_prices = dap0_dict.get('prices')
        if (dap0_next_date == None) or (dap0_prices == None):
            logging.debug("Update because JSON malformed ({0})".format(str(dap)))
            return True

        d1 = int(dap0_next_date) - 60*30 # try update 30 minutes before the wallboxes
        d2 = int(datetime.now().timestamp())
        if d1 < d2:
            logging.debug("Update because {0} < {1}".format(d1, d2))
            return True

        # Check if price list only contains one day of prices
        # In that case we did not get the day ahead prices the last time we updated the data
        d1 = len(dap0_prices)
        d2 = min_price_list_length
        if d1 < d2:
            logging.debug("Update because price list too small {0} < {1}".format(d1, d2))
            return True

        logging.debug("No update necessary")
        return False
    except:
        logging.error("Exception during entso-e query", exc_info=True)
        return True

def update():
    for dap, country_code, resolution in daps():
        logging.debug("Check update for {0} {1}".format(country_code, resolution))
        if is_update_necessary(dap_list[dap], 25 if resolution == 'PT60M' else 25*4):
            dap_list[dap] = update_day_ahead_prices_with_retry(country_code, resolution)

# TODO: Rate limit per IP
@day_ahead_prices_api.route('/v1/day_ahead_prices/<country>/<resolution>', methods=['GET'])
def day_ahead_prices(country, resolution):
    def inner(country, resolution):
        country    = country.lower()
        resolution = resolution.lower()

        if not country in ('de', 'lu', 'at'):
            logging.info("Country not supported: {0}".format(country))
            return '{"error":"Country not supported"}', 400
        if not resolution in('15min', '60min'):
            logging.info("Resolution not supported: {0}".format(resolution))
            return '{"error":"Resolution not supported"}', 400

        if country in ('de', 'lu') and resolution == '15min':
            return dap_list[DAY_AHEAD_PRICE_DE_LU_15MIN]
        elif country in ('de', 'lu') and resolution == '60min':
            return dap_list[DAY_AHEAD_PRICE_DE_LU_60MIN]
        elif country == 'at' and resolution == '15min':
            return dap_list[DAY_AHEAD_PRICE_AT_15MIN]
        elif country == 'at' and resolution == '60min':
            return dap_list[DAY_AHEAD_PRICE_AT_60MIN]

        logging.error("Reached unreachable code")
        return '{"error":"Unknown error"}', 404
    resp, status = inner(country, resolution)
    return resp, status, {'Content-Type': 'application/json; charset=utf-8'}

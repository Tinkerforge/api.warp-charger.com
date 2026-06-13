# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
import services.solar_forecast as sf
from services.solar_forecast import (
    solar_forecast_api,
    compute_forecast,
    PERFORMANCE_RATIO,
    HORIZON_HOURS,
)


def make_open_meteo_response(gti=None, first_date=1699916400, utc_offset=3600,
                             timezone='Europe/Berlin', count=72):
    """Build a mocked Open-Meteo /v1/dwd-icon GTI response as a urlopen mock.

    Default first_date (1699916400) + utc_offset (3600) == 1699920000, which is
    local midnight (2023-11-14 00:00 local), matching how Open-Meteo aligns the
    series start to local midnight.
    """
    if gti is None:
        # simple deterministic ramp
        gti = [float(i) for i in range(count)]
    times = [first_date + i * 3600 for i in range(len(gti))]
    body = {
        'latitude': 52.5,
        'longitude': 13.4,
        'utc_offset_seconds': utc_offset,
        'timezone': timezone,
        'hourly': {
            'time': times,
            'global_tilted_irradiance': gti,
        },
        'hourly_units': {'global_tilted_irradiance': 'W/m²'},
    }
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps(body).encode()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class SolarForecastTestBase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(solar_forecast_api)
        self.client = self.app.test_client()
        # Ensure a clean cache for every test.
        sf._cache.clear()


class TestInputValidation(SolarForecastTestBase):

    def test_invalid_latitude(self):
        r = self.client.get('/estimate/abc/8.6/30/0/5')
        self.assertEqual(r.status_code, 404)

    def test_latitude_out_of_range(self):
        r = self.client.get('/estimate/91/8.6/30/0/5')
        self.assertEqual(r.status_code, 404)

    def test_longitude_out_of_range(self):
        r = self.client.get('/estimate/51/181/30/0/5')
        self.assertEqual(r.status_code, 404)

    def test_declination_out_of_range(self):
        r = self.client.get('/estimate/51/8.6/91/0/5')
        self.assertEqual(r.status_code, 422)

    def test_azimuth_out_of_range(self):
        r = self.client.get('/estimate/51/8.6/30/181/5')
        self.assertEqual(r.status_code, 422)

    def test_zero_power_rejected(self):
        r = self.client.get('/estimate/51/8.6/30/0/0')
        self.assertEqual(r.status_code, 422)

    def test_native_invalid_latitude(self):
        r = self.client.get('/v1/solar_forecast/abc/8.6/30/0/5000')
        self.assertEqual(r.status_code, 404)


class TestUpstreamURL(SolarForecastTestBase):

    def test_url_contains_gti_tilt_azimuth(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            sf.fetch_irradiance(51.9, 8.6, 30, 0)
            url = mock_urlopen.call_args[0][0]
            self.assertIn('latitude=51.9', url)
            self.assertIn('longitude=8.6', url)
            self.assertIn('hourly=global_tilted_irradiance', url)
            self.assertIn('tilt=30', url)
            self.assertIn('azimuth=0', url)
            self.assertIn('timezone=auto', url)
            self.assertIn('timeformat=unixtime', url)


class TestYieldModel(SolarForecastTestBase):

    def test_preceding_hour_shift_and_scale(self):
        # gti[i] = i. forecast[k] must equal gti[k+1] scaled by wp/1000 * PR.
        entry = {
            'first_date': 1700000000,
            'utc_offset': 3600,
            'gti': [float(i) for i in range(72)],
            'place': 'Europe/Berlin',
        }
        wp = 5000  # 5 kWp
        forecast = compute_forecast(entry, wp)
        self.assertEqual(len(forecast), HORIZON_HOURS)
        for k in range(HORIZON_HOURS):
            expected = int(round((k + 1) * (wp / 1000.0) * PERFORMANCE_RATIO))
            self.assertEqual(forecast[k], expected)

    def test_none_gti_treated_as_zero(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            gti = [None] * 72
            gti[12] = 800.0
            mock_urlopen.return_value = make_open_meteo_response(gti=gti)
            entry = sf.fetch_irradiance(51.9, 8.6, 30, 0)
            self.assertEqual(entry['gti'][0], 0.0)
            forecast = compute_forecast(entry, 1000)
            # gti index 12 -> clock hour 11
            self.assertEqual(forecast[11], int(round(800.0 * PERFORMANCE_RATIO)))


class TestEstimateEndpoint(SolarForecastTestBase):

    def test_estimate_forecast_solar_format(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            r = self.client.get('/estimate/51.88/8.63/30/0/5')
            self.assertEqual(r.status_code, 200)
            data = json.loads(r.data)
            # message block the firmware relies on
            self.assertEqual(data['message']['code'], 0)
            self.assertEqual(data['message']['ratelimit']['period'], 3600)
            # firmware stores limit/remaining as int8 -> must fit -128..127
            rl = data['message']['ratelimit']
            self.assertTrue(-128 <= rl['limit'] <= 127)
            self.assertTrue(0 < rl['remaining'] <= 127)
            self.assertIn('place', data['message']['info'])
            # result block
            whp = data['result']['watt_hours_period']
            self.assertTrue(len(whp) > 0)
            # keys must be "YYYY-MM-DD HH:MM:SS" in local wall-clock; first key is
            # local midnight (utc_offset 3600 => first_date+3600).
            first_key = next(iter(whp))
            self.assertRegex(first_key, r'^\d{4}-\d{2}-\d{2} \d{2}:00:00$')
            self.assertTrue(first_key.endswith('00:00:00'))

    def test_estimate_response_fits_firmware_buffer(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            r = self.client.get('/estimate/51.88/8.63/30/0/10')
            # firmware json buffer is 8192 bytes
            self.assertLess(len(r.data), 8192)


class TestNativeEndpoint(SolarForecastTestBase):

    def test_native_format(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            r = self.client.get('/v1/solar_forecast/51.88/8.63/30/0/5000')
            self.assertEqual(r.status_code, 200)
            data = json.loads(r.data)
            self.assertEqual(data['first_date'], 1699916400)
            self.assertEqual(data['resolution'], 60)
            self.assertEqual(len(data['forecast']), HORIZON_HOURS)
            self.assertTrue(all(isinstance(v, int) for v in data['forecast']))


class TestCaching(SolarForecastTestBase):

    def test_cache_avoids_second_fetch(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            self.client.get('/estimate/51.880/8.630/30/0/5')
            # same quantized cell, different power -> still cached
            self.client.get('/estimate/51.882/8.628/30/0/9')
            self.assertEqual(mock_urlopen.call_count, 1)

    def test_distinct_cells_fetch_separately(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            self.client.get('/estimate/51.0/8.0/30/0/5')
            self.client.get('/estimate/52.5/9.0/30/0/5')
            self.assertEqual(mock_urlopen.call_count, 2)

    def test_power_scales_linearly_from_cache(self):
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.return_value = make_open_meteo_response()
            r5 = self.client.get('/v1/solar_forecast/51.0/8.0/30/0/5000')
            r10 = self.client.get('/v1/solar_forecast/51.0/8.0/30/0/10000')
            f5 = json.loads(r5.data)['forecast']
            f10 = json.loads(r10.data)['forecast']
            # 10 kWp should produce ~2x of 5 kWp (allowing integer rounding)
            for a, b in zip(f5, f10):
                self.assertAlmostEqual(b, 2 * a, delta=1)


class TestUpstreamErrors(SolarForecastTestBase):

    def test_upstream_failure_returns_503(self):
        from urllib.error import URLError
        with patch('services.solar_forecast.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = URLError('boom')
            r = self.client.get('/estimate/51.0/8.0/30/0/5')
            self.assertEqual(r.status_code, 503)


if __name__ == '__main__':
    unittest.main()

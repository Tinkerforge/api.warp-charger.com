# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
import services.status as status_mod
from services.status import status_api


class TestStatusEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(status_api)
        self.client = self.app.test_client()
        # reset probe cache between tests
        status_mod._probe.update({"ts": 0.0, "valid": None})

    def test_commercial_mode_reported(self):
        with patch.object(status_mod.solar_forecast, 'OPENMETEO_KEY', 'secret'), \
             patch.object(status_mod.solar_forecast, 'OPEN_METEO_BASE_URL',
                          'https://customer-api.open-meteo.com/v1/dwd-icon'), \
             patch.object(status_mod.temperatures, 'OPENMETEO_KEY', 'secret'), \
             patch.object(status_mod.temperatures, 'OPEN_METEO_BASE_URL',
                          'https://customer-api.open-meteo.com/v1/dwd-icon'):
            r = self.client.get('/v1/status')
            self.assertEqual(r.status_code, 200)
            d = json.loads(r.data)
            self.assertTrue(d['solar_forecast']['commercial'])
            self.assertEqual(d['solar_forecast']['upstream'], 'customer-api.open-meteo.com')
            self.assertTrue(d['temperatures']['commercial'])
            # secret must never leak
            self.assertNotIn('secret', r.data.decode())

    def test_free_mode_reported(self):
        with patch.object(status_mod.solar_forecast, 'OPENMETEO_KEY', None), \
             patch.object(status_mod.solar_forecast, 'OPEN_METEO_BASE_URL',
                          'https://api.open-meteo.com/v1/dwd-icon'), \
             patch.object(status_mod.temperatures, 'OPENMETEO_KEY', None), \
             patch.object(status_mod.temperatures, 'OPEN_METEO_BASE_URL',
                          'https://api.open-meteo.com/v1/dwd-icon'):
            r = self.client.get('/v1/status')
            d = json.loads(r.data)
            self.assertFalse(d['solar_forecast']['commercial'])
            self.assertEqual(d['solar_forecast']['upstream'], 'api.open-meteo.com')
            self.assertNotIn('openmeteo_key_valid', d)

    def test_check_runs_live_probe(self):
        with patch.object(status_mod, '_probe_key', return_value=True) as mock_probe:
            r = self.client.get('/v1/status?check=1')
            d = json.loads(r.data)
            self.assertTrue(d['openmeteo_key_valid'])
            mock_probe.assert_called_once()

    def test_day_ahead_prices_health_present(self):
        r = self.client.get('/v1/status')
        d = json.loads(r.data)
        self.assertIn('day_ahead_prices', d)
        dap = d['day_ahead_prices']
        # sources currently served (15min DE/LU and AT)
        self.assertIn('de_lu_15min', dap)
        self.assertIn('at_15min', dap)
        for rec in dap.values():
            for field in ('serving_data', 'source_used', 'last_success',
                          'entsoe_entries', 'fallback_attempted',
                          'consecutive_failures', 'last_error', 'last_error_at'):
                self.assertIn(field, rec)
        self.assertIn('now', d)


if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import services.day_ahead_prices as dap


class TestDayAheadHealth(unittest.TestCase):
    def setUp(self):
        dap._health.clear()

    def test_entsoe_source_recorded(self):
        series = pd.Series([0.05] * 96)  # full day of 15min data
        with patch.object(dap, 'get_dayahead_prices', return_value=series):
            res = dap.update_day_ahead_prices('10YAT-APG------L', 'PT15M',
                                              dap.DAY_AHEAD_PRICE_AT_15MIN)
        self.assertIsNotNone(res)
        h = dap._health[dap.DAY_AHEAD_PRICE_AT_15MIN]
        self.assertEqual(h['source_used'], 'entsoe')
        self.assertEqual(h['entsoe_entries'], 96)
        self.assertFalse(h['fallback_attempted'])
        self.assertIsNotNone(h['last_success'])
        self.assertEqual(h['consecutive_failures'], 0)
        self.assertIsNone(h['last_error'])

    def test_fallback_used_recorded(self):
        series = pd.Series([0.05] * 10)  # too few -> triggers fallback
        with patch.object(dap, 'get_dayahead_prices', return_value=series), \
             patch.object(dap, 'fallback_get_prices_de_lu', return_value=[5.0] * 96):
            res = dap.update_day_ahead_prices('10Y1001A1001A82H', 'PT15M',
                                              dap.DAY_AHEAD_PRICE_DE_LU_15MIN)
        self.assertIsNotNone(res)
        h = dap._health[dap.DAY_AHEAD_PRICE_DE_LU_15MIN]
        self.assertTrue(h['fallback_attempted'])
        self.assertEqual(h['fallback_entries'], 96)
        self.assertEqual(h['source_used'], 'fallback')
        self.assertEqual(h['entsoe_entries'], 10)

    def test_error_recorded(self):
        with patch.object(dap, 'get_dayahead_prices', side_effect=Exception("boom")):
            res = dap.update_day_ahead_prices('10YAT-APG------L', 'PT15M',
                                              dap.DAY_AHEAD_PRICE_AT_15MIN)
        self.assertIsNone(res)
        h = dap._health[dap.DAY_AHEAD_PRICE_AT_15MIN]
        self.assertIn('boom', h['last_error'])
        self.assertIsNotNone(h['last_error_at'])
        self.assertEqual(h['consecutive_failures'], 1)
        self.assertIsNone(h['source_used'])

    def test_get_health_structure(self):
        report = dap.get_health()
        self.assertIn('de_lu_15min', report)
        self.assertIn('at_15min', report)
        self.assertIn('serving_data', report['de_lu_15min'])


if __name__ == '__main__':
    unittest.main()

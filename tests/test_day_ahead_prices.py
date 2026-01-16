# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from datetime import datetime, timedelta
import pandas as pd


class TestDayAheadPricesAPI(unittest.TestCase):
    """Unit tests for the day_ahead_prices API endpoint."""

    def setUp(self):
        """Set up test client with mocked dap_list."""
        # Import inside setUp to allow patching
        from services.day_ahead_prices import day_ahead_prices_api, DAY_AHEAD_PRICE_NOT_FOUND

        self.app = Flask(__name__)
        self.app.register_blueprint(day_ahead_prices_api)
        self.client = self.app.test_client()
        self.DAY_AHEAD_PRICE_NOT_FOUND = DAY_AHEAD_PRICE_NOT_FOUND

    # -------------------------------------------------------------------------
    # Input Validation Tests
    # -------------------------------------------------------------------------

    def test_unsupported_country(self):
        """Test that unsupported country returns 400 error."""
        response = self.client.get('/v1/day_ahead_prices/fr/15min')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Country not supported')

    def test_unsupported_country_us(self):
        """Test that US country code returns 400 error."""
        response = self.client.get('/v1/day_ahead_prices/us/15min')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Country not supported')

    def test_unsupported_resolution(self):
        """Test that unsupported resolution returns 400 error."""
        response = self.client.get('/v1/day_ahead_prices/de/30min')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Resolution not supported')

    def test_unsupported_resolution_hourly(self):
        """Test that 'hourly' resolution returns 400 error."""
        response = self.client.get('/v1/day_ahead_prices/de/hourly')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Resolution not supported')

    def test_country_case_insensitive(self):
        """Test that country parameter is case insensitive."""
        with patch('services.day_ahead_prices.dap_list', self._mock_dap_list()):
            # Test uppercase
            response = self.client.get('/v1/day_ahead_prices/DE/15min')
            self.assertEqual(response.status_code, 200)

            # Test mixed case
            response = self.client.get('/v1/day_ahead_prices/De/15min')
            self.assertEqual(response.status_code, 200)

    def test_resolution_case_insensitive(self):
        """Test that resolution parameter is case insensitive."""
        with patch('services.day_ahead_prices.dap_list', self._mock_dap_list()):
            # Test uppercase
            response = self.client.get('/v1/day_ahead_prices/de/15MIN')
            self.assertEqual(response.status_code, 200)

            # Test mixed case
            response = self.client.get('/v1/day_ahead_prices/de/15Min')
            self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # Supported Country/Resolution Combinations
    # -------------------------------------------------------------------------

    def test_de_15min_returns_correct_data(self):
        """Test that DE 15min returns data from correct index."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/de/15min')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['first_date'], 1700000000)
            self.assertIn('prices', data)

    def test_lu_15min_returns_same_as_de(self):
        """Test that LU 15min returns same data as DE (same market)."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response_de = self.client.get('/v1/day_ahead_prices/de/15min')
            response_lu = self.client.get('/v1/day_ahead_prices/lu/15min')

            self.assertEqual(response_de.status_code, 200)
            self.assertEqual(response_lu.status_code, 200)
            self.assertEqual(response_de.data, response_lu.data)

    def test_de_60min_returns_correct_data(self):
        """Test that DE 60min returns data from correct index."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/de/60min')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            # 60min data should have different prices than 15min
            self.assertEqual(data['first_date'], 1700000000)

    def test_at_15min_returns_correct_data(self):
        """Test that AT 15min returns data from correct index."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/at/15min')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['first_date'], 1700000000)

    def test_at_60min_returns_correct_data(self):
        """Test that AT 60min returns data from correct index."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/at/60min')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['first_date'], 1700000000)

    # -------------------------------------------------------------------------
    # Response Format Tests
    # -------------------------------------------------------------------------

    def test_response_content_type(self):
        """Test that response has correct content type."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/de/15min')
            self.assertEqual(response.content_type, 'application/json; charset=utf-8')

    def test_response_structure(self):
        """Test that successful response has correct structure."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/de/15min')
            data = json.loads(response.data)

            self.assertIn('first_date', data)
            self.assertIn('prices', data)
            self.assertIn('next_date', data)

            self.assertIsInstance(data['first_date'], int)
            self.assertIsInstance(data['prices'], list)
            self.assertIsInstance(data['next_date'], int)

    def test_prices_are_integers(self):
        """Test that all prices in response are integers (centicents)."""
        mock_list = self._mock_dap_list()
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/de/15min')
            data = json.loads(response.data)

            for price in data['prices']:
                self.assertIsInstance(price, int)

    # -------------------------------------------------------------------------
    # Data Not Found Tests
    # -------------------------------------------------------------------------

    def test_data_not_found_returns_404(self):
        """Test that missing data returns 404 error."""
        from services.day_ahead_prices import DAY_AHEAD_PRICE_NOT_FOUND
        mock_list = [DAY_AHEAD_PRICE_NOT_FOUND] * 4
        with patch('services.day_ahead_prices.dap_list', mock_list):
            response = self.client.get('/v1/day_ahead_prices/de/15min')
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Data not found')

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _mock_dap_list(self):
        """Create a mock dap_list with valid data for all indices."""
        valid_response = (
            '{"first_date":1700000000,"prices":[1000,1100,1200,1300],"next_date":1700100000}',
            200
        )
        return [valid_response] * 4


class TestParseTimeseries(unittest.TestCase):
    """Unit tests for the parse_timeseries function."""

    def test_parse_15min_resolution(self):
        """Test parsing XML with 15-minute resolution."""
        from services.day_ahead_prices import parse_timeseries

        xml_text = self._create_mock_xml('PT15M', [
            ('1', '10.50'),
            ('2', '11.00'),
            ('3', '11.50'),
            ('4', '12.00'),
        ])

        result = parse_timeseries(xml_text, 'PT15M')

        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result.iloc[0], 10.50)
        self.assertAlmostEqual(result.iloc[1], 11.00)
        self.assertAlmostEqual(result.iloc[2], 11.50)
        self.assertAlmostEqual(result.iloc[3], 12.00)

    def test_parse_60min_resolution(self):
        """Test parsing XML with 60-minute resolution."""
        from services.day_ahead_prices import parse_timeseries

        xml_text = self._create_mock_xml('PT60M', [
            ('1', '50.00'),
            ('2', '55.00'),
        ])

        result = parse_timeseries(xml_text, 'PT60M')

        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result.iloc[0], 50.00)
        self.assertAlmostEqual(result.iloc[1], 55.00)

    def test_parse_empty_xml(self):
        """Test parsing XML with no data points."""
        from services.day_ahead_prices import parse_timeseries

        xml_text = '''<?xml version="1.0" encoding="UTF-8"?>
        <Publication_MarketDocument>
        </Publication_MarketDocument>'''

        result = parse_timeseries(xml_text, 'PT15M')

        self.assertEqual(len(result), 0)

    def test_parse_removes_namespace(self):
        """Test that XML namespace is properly removed."""
        from services.day_ahead_prices import parse_timeseries

        xml_text = '''<?xml version="1.0" encoding="UTF-8"?>
        <Publication_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3">
            <TimeSeries>
                <Period>
                    <timeInterval>
                        <start>2024-01-01T00:00Z</start>
                    </timeInterval>
                    <resolution>PT15M</resolution>
                    <Point>
                        <position>1</position>
                        <price.amount>10.00</price.amount>
                    </Point>
                </Period>
            </TimeSeries>
        </Publication_MarketDocument>'''

        result = parse_timeseries(xml_text, 'PT15M')

        self.assertEqual(len(result), 1)

    def test_parse_handles_duplicates(self):
        """Test that duplicate timestamps are handled."""
        from services.day_ahead_prices import parse_timeseries

        # Create XML with duplicate position (same timestamp)
        xml_text = '''<?xml version="1.0" encoding="UTF-8"?>
        <Publication_MarketDocument>
            <TimeSeries>
                <Period>
                    <timeInterval>
                        <start>2024-01-01T00:00Z</start>
                    </timeInterval>
                    <resolution>PT15M</resolution>
                    <Point>
                        <position>1</position>
                        <price.amount>10.00</price.amount>
                    </Point>
                </Period>
            </TimeSeries>
            <TimeSeries>
                <Period>
                    <timeInterval>
                        <start>2024-01-01T00:00Z</start>
                    </timeInterval>
                    <resolution>PT15M</resolution>
                    <Point>
                        <position>1</position>
                        <price.amount>20.00</price.amount>
                    </Point>
                </Period>
            </TimeSeries>
        </Publication_MarketDocument>'''

        result = parse_timeseries(xml_text, 'PT15M')

        # Should keep first occurrence
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0], 10.00)

    def _create_mock_xml(self, resolution, points):
        """Create mock ENTSO-E XML response."""
        points_xml = '\n'.join([
            f'''                    <Point>
                        <position>{pos}</position>
                        <price.amount>{price}</price.amount>
                    </Point>'''
            for pos, price in points
        ])

        return f'''<?xml version="1.0" encoding="UTF-8"?>
        <Publication_MarketDocument>
            <TimeSeries>
                <Period>
                    <timeInterval>
                        <start>2024-01-01T00:00Z</start>
                    </timeInterval>
                    <resolution>{resolution}</resolution>
{points_xml}
                </Period>
            </TimeSeries>
        </Publication_MarketDocument>'''


class TestIsUpdateNecessary(unittest.TestCase):
    """Unit tests for the is_update_necessary function."""

    def test_update_necessary_when_none(self):
        """Test that update is necessary when dap is None."""
        from services.day_ahead_prices import is_update_necessary

        result = is_update_necessary(None, 26)
        self.assertTrue(result)

    def test_update_necessary_when_not_tuple(self):
        """Test that update is necessary when dap is not a tuple."""
        from services.day_ahead_prices import is_update_necessary

        result = is_update_necessary("not a tuple", 26)
        self.assertTrue(result)

    def test_update_necessary_when_not_found(self):
        """Test that update is necessary when dap is NOT_FOUND."""
        from services.day_ahead_prices import is_update_necessary, DAY_AHEAD_PRICE_NOT_FOUND

        result = is_update_necessary(DAY_AHEAD_PRICE_NOT_FOUND, 26)
        self.assertTrue(result)

    def test_update_necessary_when_malformed_json(self):
        """Test that update is necessary when JSON is malformed."""
        from services.day_ahead_prices import is_update_necessary

        malformed = ('{"invalid": "json"}', 200)
        result = is_update_necessary(malformed, 26)
        self.assertTrue(result)

    def test_update_necessary_when_price_list_too_small(self):
        """Test that update is necessary when price list is too small."""
        from services.day_ahead_prices import is_update_necessary

        # Create data with only 10 prices, but require 26
        future_date = int((datetime.now() + timedelta(hours=2)).timestamp())
        small_list = (
            f'{{"first_date":1700000000,"prices":[1,2,3,4,5,6,7,8,9,10],"next_date":{future_date}}}',
            200
        )

        result = is_update_necessary(small_list, 26)
        self.assertTrue(result)

    def test_update_necessary_when_next_date_passed(self):
        """Test that update is necessary when next_date has passed."""
        from services.day_ahead_prices import is_update_necessary

        # Set next_date to the past
        past_date = int((datetime.now() - timedelta(hours=1)).timestamp())
        prices = [100] * 30  # Enough prices
        past_data = (
            f'{{"first_date":1700000000,"prices":{json.dumps(prices)},"next_date":{past_date}}}',
            200
        )

        result = is_update_necessary(past_data, 26)
        self.assertTrue(result)

    def test_no_update_when_data_fresh(self):
        """Test that no update is needed when data is fresh."""
        from services.day_ahead_prices import is_update_necessary

        # Set next_date to far future
        future_date = int((datetime.now() + timedelta(hours=5)).timestamp())
        prices = [100] * 30  # Enough prices
        fresh_data = (
            f'{{"first_date":1700000000,"prices":{json.dumps(prices)},"next_date":{future_date}}}',
            200
        )

        result = is_update_necessary(fresh_data, 26)
        self.assertFalse(result)

    def test_update_checks_30_min_before_next_date(self):
        """Test that update triggers 30 minutes before next_date."""
        from services.day_ahead_prices import is_update_necessary

        # Set next_date to 20 minutes from now (should trigger because of 30 min buffer)
        near_future = int((datetime.now() + timedelta(minutes=20)).timestamp())
        prices = [100] * 30
        data = (
            f'{{"first_date":1700000000,"prices":{json.dumps(prices)},"next_date":{near_future}}}',
            200
        )

        result = is_update_necessary(data, 26)
        self.assertTrue(result)


class TestUpdateDayAheadPricesWithRetry(unittest.TestCase):
    """Unit tests for the update_day_ahead_prices_with_retry function."""

    def test_returns_on_first_success(self):
        """Test that function returns immediately on success."""
        from services.day_ahead_prices import update_day_ahead_prices_with_retry

        mock_result = ('{"first_date":1700000000,"prices":[100],"next_date":1700100000}', 200)

        with patch('services.day_ahead_prices.update_day_ahead_prices', return_value=mock_result):
            with patch('services.day_ahead_prices.time.sleep') as mock_sleep:
                result = update_day_ahead_prices_with_retry('TEST', 'PT15M', retries=5)

                self.assertEqual(result, mock_result)
                mock_sleep.assert_not_called()

    def test_retries_on_failure(self):
        """Test that function retries on failure."""
        from services.day_ahead_prices import update_day_ahead_prices_with_retry

        mock_result = ('{"first_date":1700000000,"prices":[100],"next_date":1700100000}', 200)

        # Fail twice, then succeed
        with patch('services.day_ahead_prices.update_day_ahead_prices',
                   side_effect=[None, None, mock_result]):
            with patch('services.day_ahead_prices.time.sleep'):
                result = update_day_ahead_prices_with_retry('TEST', 'PT15M', retries=5)

                self.assertEqual(result, mock_result)

    def test_returns_not_found_after_max_retries(self):
        """Test that function returns NOT_FOUND after max retries."""
        from services.day_ahead_prices import update_day_ahead_prices_with_retry, DAY_AHEAD_PRICE_NOT_FOUND

        with patch('services.day_ahead_prices.update_day_ahead_prices', return_value=None):
            with patch('services.day_ahead_prices.time.sleep'):
                result = update_day_ahead_prices_with_retry('TEST', 'PT15M', retries=3)

                self.assertEqual(result, DAY_AHEAD_PRICE_NOT_FOUND)

    def test_sleep_increases_with_retries(self):
        """Test that sleep time increases with each retry."""
        from services.day_ahead_prices import update_day_ahead_prices_with_retry

        with patch('services.day_ahead_prices.update_day_ahead_prices', return_value=None):
            with patch('services.day_ahead_prices.time.sleep') as mock_sleep:
                update_day_ahead_prices_with_retry('TEST', 'PT15M', retries=4)

                # Sleep should be called with 0, 60, 120, 180 (60*retry)
                calls = [call[0][0] for call in mock_sleep.call_args_list]
                self.assertEqual(calls, [0, 60, 120, 180])


class TestDaps(unittest.TestCase):
    """Unit tests for the daps generator function."""

    def test_daps_yields_expected_countries(self):
        """Test that daps yields the expected country configurations."""
        from services.day_ahead_prices import daps, DAY_AHEAD_PRICE_DE_LU_15MIN, DAY_AHEAD_PRICE_AT_15MIN

        result = list(daps())

        # Check that we have entries for DE_LU and AT
        indices = [r[0] for r in result]
        self.assertIn(DAY_AHEAD_PRICE_DE_LU_15MIN, indices)
        self.assertIn(DAY_AHEAD_PRICE_AT_15MIN, indices)

    def test_daps_country_codes(self):
        """Test that daps uses correct ENTSO-E country codes."""
        from services.day_ahead_prices import daps

        result = list(daps())
        country_codes = [r[1] for r in result]

        # DE_LU area code
        self.assertIn('10Y1001A1001A82H', country_codes)
        # AT area code
        self.assertIn('10YAT-APG------L', country_codes)


if __name__ == '__main__':
    unittest.main()

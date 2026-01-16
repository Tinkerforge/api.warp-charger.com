# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from services.temperatures import temperatures_api, fetch_temperature_forecast, format_temperature_response


class TestTemperaturesAPI(unittest.TestCase):
    """Unit tests for the temperatures API endpoint."""

    def setUp(self):
        """Set up test client."""
        self.app = Flask(__name__)
        self.app.register_blueprint(temperatures_api)
        self.client = self.app.test_client()

    # -------------------------------------------------------------------------
    # Input Validation Tests
    # -------------------------------------------------------------------------

    def test_invalid_latitude_format(self):
        """Test that non-numeric latitude returns 400 error."""
        response = self.client.get('/v1/temperatures/abc/13.41')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid latitude format')

    def test_invalid_longitude_format(self):
        """Test that non-numeric longitude returns 400 error."""
        response = self.client.get('/v1/temperatures/52.52/xyz')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid longitude format')

    def test_latitude_out_of_range_high(self):
        """Test that latitude > 90 returns 400 error."""
        response = self.client.get('/v1/temperatures/91/13.41')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Latitude must be between -90 and 90')

    def test_latitude_out_of_range_low(self):
        """Test that latitude < -90 returns 400 error."""
        response = self.client.get('/v1/temperatures/-91/13.41')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Latitude must be between -90 and 90')

    def test_longitude_out_of_range_high(self):
        """Test that longitude > 180 returns 400 error."""
        response = self.client.get('/v1/temperatures/52.52/181')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Longitude must be between -180 and 180')

    def test_longitude_out_of_range_low(self):
        """Test that longitude < -180 returns 400 error."""
        response = self.client.get('/v1/temperatures/52.52/-181')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Longitude must be between -180 and 180')

    def test_boundary_latitude_values(self):
        """Test that boundary latitude values (90, -90) are accepted."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = self._mock_open_meteo_response()

            # Test latitude = 90
            response = self.client.get('/v1/temperatures/90/0')
            self.assertEqual(response.status_code, 200)

            # Test latitude = -90
            response = self.client.get('/v1/temperatures/-90/0')
            self.assertEqual(response.status_code, 200)

    def test_boundary_longitude_values(self):
        """Test that boundary longitude values (180, -180) are accepted."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = self._mock_open_meteo_response()

            # Test longitude = 180
            response = self.client.get('/v1/temperatures/0/180')
            self.assertEqual(response.status_code, 200)

            # Test longitude = -180
            response = self.client.get('/v1/temperatures/0/-180')
            self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # Successful Response Tests
    # -------------------------------------------------------------------------

    def test_successful_response_structure(self):
        """Test that successful response has correct structure."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = self._mock_open_meteo_response()

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json; charset=utf-8')

            data = json.loads(response.data)

            # Check top-level keys
            self.assertIn('today', data)
            self.assertIn('tomorrow', data)

            # Check today structure
            self.assertIn('date', data['today'])
            self.assertIn('min', data['today'])
            self.assertIn('max', data['today'])
            self.assertIn('avg', data['today'])

            # Check tomorrow structure
            self.assertIn('date', data['tomorrow'])
            self.assertIn('min', data['tomorrow'])
            self.assertIn('max', data['tomorrow'])
            self.assertIn('avg', data['tomorrow'])

    def test_successful_response_values(self):
        """Test that response values are correctly extracted from API data."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_data = self._mock_open_meteo_response(
                today_min=2.0, today_max=8.0,
                tomorrow_min=-1.0, tomorrow_max=5.0,
                today_date=1700000000, tomorrow_date=1700086400
            )
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            data = json.loads(response.data)

            # Check today values
            self.assertEqual(data['today']['date'], 1700000000)
            self.assertEqual(data['today']['min'], 2.0)
            self.assertEqual(data['today']['max'], 8.0)
            self.assertEqual(data['today']['avg'], 5.0)  # (2 + 8) / 2

            # Check tomorrow values
            self.assertEqual(data['tomorrow']['date'], 1700086400)
            self.assertEqual(data['tomorrow']['min'], -1.0)
            self.assertEqual(data['tomorrow']['max'], 5.0)
            self.assertEqual(data['tomorrow']['avg'], 2.0)  # (-1 + 5) / 2

    def test_average_calculation_rounding(self):
        """Test that average is correctly rounded to 1 decimal place."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            # 3.3 + 7.8 = 11.1 / 2 = 5.55 -> should round to 5.5 or 5.6
            mock_data = self._mock_open_meteo_response(
                today_min=3.3, today_max=7.8,
                tomorrow_min=0.0, tomorrow_max=0.0
            )
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            data = json.loads(response.data)

            # (3.3 + 7.8) / 2 = 5.55, rounded to 5.5 or 5.6
            self.assertIn(data['today']['avg'], [5.5, 5.6])

    def test_negative_temperatures(self):
        """Test that negative temperatures are handled correctly."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_data = self._mock_open_meteo_response(
                today_min=-15.5, today_max=-5.0,
                tomorrow_min=-20.0, tomorrow_max=-10.0
            )
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            data = json.loads(response.data)

            self.assertEqual(data['today']['min'], -15.5)
            self.assertEqual(data['today']['max'], -5.0)
            self.assertEqual(data['today']['avg'], -10.2)  # (-15.5 + -5.0) / 2 = -10.25 -> -10.2

    # -------------------------------------------------------------------------
    # Error Handling Tests
    # -------------------------------------------------------------------------

    def test_api_http_error_400(self):
        """Test handling of HTTP 400 error from Open-Meteo."""
        with patch('services.temperatures.urlopen') as mock_urlopen:
            from urllib.error import HTTPError
            mock_urlopen.side_effect = HTTPError(
                url='http://test.com',
                code=400,
                msg='Bad Request',
                hdrs={},
                fp=None
            )

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid coordinates')

    def test_api_http_error_500(self):
        """Test handling of HTTP 500 error from Open-Meteo."""
        with patch('services.temperatures.urlopen') as mock_urlopen:
            from urllib.error import HTTPError
            mock_urlopen.side_effect = HTTPError(
                url='http://test.com',
                code=500,
                msg='Internal Server Error',
                hdrs={},
                fp=None
            )

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Weather service unavailable')

    def test_api_connection_error(self):
        """Test handling of connection errors."""
        with patch('services.temperatures.urlopen') as mock_urlopen:
            from urllib.error import URLError
            mock_urlopen.side_effect = URLError('Connection refused')

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Weather service unavailable')

    def test_insufficient_forecast_data(self):
        """Test handling when API returns insufficient data."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            # Return data with only 1 day instead of 2
            mock_fetch.return_value = {
                'daily': {
                    'time': [1700000000],  # Only 1 day
                    'temperature_2m_max': [8.0],
                    'temperature_2m_min': [2.0]
                }
            }

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid response from weather service')

    def test_missing_daily_data(self):
        """Test handling when API returns no daily data."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = {}

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid response from weather service')

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _mock_open_meteo_response(self, today_min=2.0, today_max=8.0,
                                   tomorrow_min=-1.0, tomorrow_max=5.0,
                                   today_date=1700000000, tomorrow_date=1700086400):
        """Create a mock Open-Meteo API response."""
        return {
            'latitude': 52.52,
            'longitude': 13.419998,
            'generationtime_ms': 0.06,
            'utc_offset_seconds': 3600,
            'timezone': 'Europe/Berlin',
            'timezone_abbreviation': 'CET',
            'elevation': 38.0,
            'daily_units': {
                'time': 'unixtime',
                'temperature_2m_max': '°C',
                'temperature_2m_min': '°C'
            },
            'daily': {
                'time': [today_date, tomorrow_date],
                'temperature_2m_max': [today_max, tomorrow_max],
                'temperature_2m_min': [today_min, tomorrow_min]
            }
        }


class TestFormatTemperatureResponse(unittest.TestCase):
    """Unit tests for the format_temperature_response function."""

    def test_format_response_order(self):
        """Test that JSON keys are in correct order."""
        data = {
            'daily': {
                'time': [1700000000, 1700086400],
                'temperature_2m_max': [8.0, 5.0],
                'temperature_2m_min': [2.0, -1.0]
            }
        }
        result = format_temperature_response(data)

        # Check that the JSON string has keys in expected order
        # today should come before tomorrow
        self.assertLess(result.find('"today"'), result.find('"tomorrow"'))

        # Within each day, date should come first
        parsed = json.loads(result)
        today_keys = list(parsed['today'].keys())
        self.assertEqual(today_keys, ['date', 'min', 'max', 'avg'])


class TestFetchTemperatureForecast(unittest.TestCase):
    """Unit tests for the fetch_temperature_forecast function."""

    def test_fetch_builds_correct_url(self):
        """Test that the correct URL is built for the API call."""
        with patch('services.temperatures.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps({
                'daily': {
                    'time': [1700000000, 1700086400],
                    'temperature_2m_max': [8.0, 5.0],
                    'temperature_2m_min': [2.0, -1.0]
                }
            }).encode()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response

            fetch_temperature_forecast(52.52, 13.41)

            # Check the URL that was called
            call_args = mock_urlopen.call_args
            url = call_args[0][0]

            self.assertIn('latitude=52.52', url)
            self.assertIn('longitude=13.41', url)
            self.assertIn('daily=temperature_2m_max,temperature_2m_min', url)
            self.assertIn('timezone=auto', url)
            self.assertIn('forecast_days=2', url)
            self.assertIn('timeformat=unixtime', url)


if __name__ == '__main__':
    unittest.main()

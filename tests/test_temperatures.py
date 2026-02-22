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
        """Test that successful response has correct flat structure."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = self._mock_open_meteo_response()

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json; charset=utf-8')

            data = json.loads(response.data)

            # Check top-level keys
            self.assertIn('first_date', data)
            self.assertIn('hourly', data)
            self.assertEqual(len(data), 2)

            # Check hourly array
            self.assertIsInstance(data['hourly'], list)
            self.assertEqual(len(data['hourly']), 48)

            # Check first_date is the first timestamp
            self.assertIsInstance(data['first_date'], int)

    def test_successful_response_values(self):
        """Test that response values are correctly extracted and converted to 10ths of degree."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            hourly = [5.0] * 24 + [2.0] * 24
            mock_data = self._mock_open_meteo_response(
                first_date=1700000000, hourly=hourly
            )
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            data = json.loads(response.data)

            # Check first_date
            self.assertEqual(data['first_date'], 1700000000)

            # Check hourly values (5.0°C = 50 tenths, 2.0°C = 20 tenths)
            self.assertEqual(data['hourly'][:24], [50] * 24)
            self.assertEqual(data['hourly'][24:], [20] * 24)

    def test_temperatures_are_integers_in_tenths(self):
        """Test that temperatures are properly converted to integer tenths of degree."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            hourly = [12.3, -5.7, 0.0, 25.9, -0.1, 0.1, -15.5, 30.2] + [10.0] * 40
            mock_data = self._mock_open_meteo_response(hourly=hourly)
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            data = json.loads(response.data)

            # Check specific conversions
            self.assertEqual(data['hourly'][0], 123)   # 12.3 * 10
            self.assertEqual(data['hourly'][1], -57)   # -5.7 * 10
            self.assertEqual(data['hourly'][2], 0)     # 0.0 * 10
            self.assertEqual(data['hourly'][3], 259)   # 25.9 * 10
            self.assertEqual(data['hourly'][4], -1)    # -0.1 * 10
            self.assertEqual(data['hourly'][5], 1)     # 0.1 * 10
            self.assertEqual(data['hourly'][6], -155)  # -15.5 * 10
            self.assertEqual(data['hourly'][7], 302)   # 30.2 * 10

            # All values must be integers
            for t in data['hourly']:
                self.assertIsInstance(t, int)

    def test_negative_temperatures(self):
        """Test that negative temperatures are handled correctly."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            hourly = [-15.5] * 24 + [-20.0] * 24
            mock_data = self._mock_open_meteo_response(hourly=hourly)
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            data = json.loads(response.data)

            self.assertEqual(data['hourly'][:24], [-155] * 24)
            self.assertEqual(data['hourly'][24:], [-200] * 24)

    # -------------------------------------------------------------------------
    # DST Tests (variable array sizes)
    # -------------------------------------------------------------------------

    def test_dst_spring_forward_47_values(self):
        """Test that 47 hourly values (spring forward: 23 + 24) are accepted."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_data = self._mock_open_meteo_response(hours=47)
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data['hourly']), 47)

    def test_dst_fall_back_49_values(self):
        """Test that 49 hourly values (fall back: 25 + 24) are accepted."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_data = self._mock_open_meteo_response(hours=49)
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data['hourly']), 49)

    def test_normal_48_values(self):
        """Test that 48 hourly values (normal: 24 + 24) are accepted."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_data = self._mock_open_meteo_response(hours=48)
            mock_fetch.return_value = mock_data

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data['hourly']), 48)

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

    def test_insufficient_hourly_data(self):
        """Test handling when API returns insufficient hourly data (< 47)."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = {
                'hourly': {
                    'time': [1700000000 + i * 3600 for i in range(20)],
                    'temperature_2m': [5.0] * 20
                }
            }

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid response from weather service')

    def test_exactly_46_values_rejected(self):
        """Test that 46 hourly values (below minimum 47) are rejected."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = {
                'hourly': {
                    'time': [1700000000 + i * 3600 for i in range(46)],
                    'temperature_2m': [5.0] * 46
                }
            }

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid response from weather service')

    def test_missing_hourly_data(self):
        """Test handling when API returns no hourly data."""
        with patch('services.temperatures.fetch_temperature_forecast') as mock_fetch:
            mock_fetch.return_value = {}

            response = self.client.get('/v1/temperatures/52.52/13.41')
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid response from weather service')

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _mock_open_meteo_response(self, first_date=1700000000, hourly=None, hours=48):
        """Create a mock Open-Meteo API response with hourly data.

        Args:
            first_date: UTC timestamp of the first hourly slot (local midnight).
            hourly: List of temperature floats. If None, generates a default ramp.
            hours: Number of hourly values (47-49 for DST, 48 normal). Only used
                   when hourly is None.
        """
        if hourly is None:
            hourly = [5.0 + 3.0 * (i / max(hours - 1, 1)) for i in range(hours)]

        hourly_times = [first_date + i * 3600 for i in range(len(hourly))]

        return {
            'latitude': 52.52,
            'longitude': 13.419998,
            'generationtime_ms': 0.06,
            'utc_offset_seconds': 3600,
            'timezone': 'Europe/Berlin',
            'timezone_abbreviation': 'CET',
            'elevation': 38.0,
            'hourly_units': {
                'time': 'unixtime',
                'temperature_2m': '°C'
            },
            'hourly': {
                'time': hourly_times,
                'temperature_2m': hourly
            }
        }


class TestFormatTemperatureResponse(unittest.TestCase):
    """Unit tests for the format_temperature_response function."""

    def test_format_response_key_order(self):
        """Test that JSON keys are in correct order: first_date, hourly."""
        hourly_temps = [5.0] * 48
        hourly_times = [1700000000 + i * 3600 for i in range(48)]
        data = {
            'hourly': {
                'time': hourly_times,
                'temperature_2m': hourly_temps
            }
        }
        result = format_temperature_response(data)

        # first_date should come before hourly
        self.assertLess(result.find('"first_date"'), result.find('"hourly"'))

        parsed = json.loads(result)
        keys = list(parsed.keys())
        self.assertEqual(keys, ['first_date', 'hourly'])

    def test_format_response_array_length_48(self):
        """Test that a 48-value response preserves all values."""
        hourly_temps = [10.0] * 48
        hourly_times = [1700000000 + i * 3600 for i in range(48)]
        data = {
            'hourly': {
                'time': hourly_times,
                'temperature_2m': hourly_temps
            }
        }
        result = format_temperature_response(data)
        parsed = json.loads(result)

        self.assertEqual(len(parsed['hourly']), 48)

    def test_format_response_array_length_47(self):
        """Test that a 47-value response (spring forward) preserves all values."""
        hourly_temps = [10.0] * 47
        hourly_times = [1700000000 + i * 3600 for i in range(47)]
        data = {
            'hourly': {
                'time': hourly_times,
                'temperature_2m': hourly_temps
            }
        }
        result = format_temperature_response(data)
        parsed = json.loads(result)

        self.assertEqual(len(parsed['hourly']), 47)

    def test_format_response_array_length_49(self):
        """Test that a 49-value response (fall back) preserves all values."""
        hourly_temps = [10.0] * 49
        hourly_times = [1700000000 + i * 3600 for i in range(49)]
        data = {
            'hourly': {
                'time': hourly_times,
                'temperature_2m': hourly_temps
            }
        }
        result = format_temperature_response(data)
        parsed = json.loads(result)

        self.assertEqual(len(parsed['hourly']), 49)

    def test_format_first_date_from_hourly_times(self):
        """Test that first_date is taken from the first hourly timestamp."""
        hourly_temps = [10.0] * 48
        first_date = 1700000000
        hourly_times = [first_date + i * 3600 for i in range(48)]
        data = {
            'hourly': {
                'time': hourly_times,
                'temperature_2m': hourly_temps
            }
        }
        result = format_temperature_response(data)
        parsed = json.loads(result)

        self.assertEqual(parsed['first_date'], first_date)


class TestFetchTemperatureForecast(unittest.TestCase):
    """Unit tests for the fetch_temperature_forecast function."""

    def test_fetch_builds_correct_url(self):
        """Test that the correct URL is built for the API call."""
        with patch('services.temperatures.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = json.dumps({
                'hourly': {
                    'time': [1700000000 + i * 3600 for i in range(48)],
                    'temperature_2m': [5.0] * 48
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
            self.assertIn('hourly=temperature_2m', url)
            self.assertIn('timezone=auto', url)
            self.assertIn('forecast_days=2', url)
            self.assertIn('timeformat=unixtime', url)
            # Should NOT contain daily params
            self.assertNotIn('daily=', url)
            # Should NOT use UTC timezone
            self.assertNotIn('timezone=UTC', url)


if __name__ == '__main__':
    unittest.main()

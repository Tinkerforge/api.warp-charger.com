api.warp-charger.com
====================

Public API server used by WARP Chargers and Energy Managers to obtain
day-ahead electricity prices and temperature forecasts.

Live at https://api.warp-charger.com


API Endpoints
-------------

Day-Ahead Prices
~~~~~~~~~~~~~~~~

::

    GET /v1/day_ahead_prices/<country>/<resolution>

Returns day-ahead electricity spot prices sourced from the ENTSO-E
Transparency Platform.

============== ========================= =========================================
Parameter      Values                    Description
============== ========================= =========================================
``country``    ``de``, ``lu``, ``at``     Bidding zone (DE and LU share a zone)
``resolution`` ``15min``, ``60min``       Price interval granularity
============== ========================= =========================================

Example::

    curl https://api.warp-charger.com/v1/day_ahead_prices/de/15min

Response::

    {
      "first_date": 1771455600,
      "prices": [8780, 8330, ...],
      "next_date": 1771590600
    }

- ``first_date`` -- UTC unix timestamp of the first price interval
- ``prices`` -- array of integers in centicent/MWh (multiply by 0.00001 for EUR/kWh)
- ``next_date`` -- UTC unix timestamp indicating when fresh data should be available

Temperature Forecast
~~~~~~~~~~~~~~~~~~~~

::

    GET /v1/temperatures/<lat>/<lon>

Returns min/max/avg temperature forecast for today and tomorrow using the
DWD ICON model (via Open-Meteo). The average is computed from 24 hourly
temperature values.

=========== =================== ============================
Parameter   Range               Description
=========== =================== ============================
``lat``     ``-90`` to ``90``   Latitude (decimal degrees)
``lon``     ``-180`` to ``180`` Longitude (decimal degrees)
=========== =================== ============================

Example::

    curl https://api.warp-charger.com/v1/temperatures/51.93/8.63

Response::

    {
      "today":    {"date": 1771369200, "min": 8.2, "max": 14.7, "avg": 11.3},
      "tomorrow": {"date": 1771455600, "min": 7.1, "max": 13.9, "avg": 10.2}
    }

Temperatures are in degrees Celsius. The ``avg`` field is the mean of 24
hourly temperature values for the day.


Setup
-----

::

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

An ENTSO-E API key must be placed in ``entsoe.key`` (single line, no
trailing newline).

Run in development mode::

    python main.py

Run in production (behind a reverse proxy)::

    ./start.sh

Tests::

    ./run_all_tests.sh

Repository Overview
-------------------

.. DO NOT EDIT THIS OVERVIEW MANUALLY! CHANGE https://github.com/Tinkerforge/esp32-firmware/repo_overview.rst AND COPY THAT BLOCK INTO ALL REPOS LISTED BELOW. TODO: AUTOMATE THIS

Software
~~~~~~~~
- `esp32-firmware <https://github.com/Tinkerforge/esp32-firmware>`__  **Please report any issues concerning WARP hard- and software here!** Source code of the ESP32 firmware shared between all WARP Chargers and Energy Managers

- `tfjson <https://github.com/Tinkerforge/tfjson>`__ SAX style JSON serializer and deserializer
- `tfmodbustcp <https://github.com/Tinkerforge/tfmodbustcp>`__ Modbus TCP server and client implementation
- `tfocpp <https://github.com/Tinkerforge/tfocpp>`__ OCPP 1.6 implementation
- `tftools <https://github.com/Tinkerforge/tftools>`__ Miscellaneous tools and helpers

- `esp32-remote-access <https://github.com/Tinkerforge/esp32-remote-access>`__ Source code of the my.warp-charger.com remote access server

- `warp-charger <https://github.com/Tinkerforge/warp-charger>`__ The source code of (docs.)warp-charger.com and the printed manual, released firmwares, datasheets and documents, as well as some tools and hardware design files
- `api.warp-charger.com <https://github.com/Tinkerforge/api.warp-charger.com>`__ Serves APIs that are used by WARP Chargers to obtain relevant public information like day ahead prices
- `vislog.warp-charger.com <https://github.com/Tinkerforge/vislog.warp-charger.com>`__ Visualizes WARP Charger logs and EVSE debug protocols
- `dbus-warp-charger <https://github.com/Tinkerforge/dbus-warp-charger>`__ Integrates WARP Chargers into a Victron Energy Venus OS device (e.g. Cerbo GX)

WARP Charger Hardware
~~~~~~~~~~~~~~~~~~~~~~

- `esp32-brick <https://github.com/Tinkerforge/esp32-brick>`__ Hardware design files of the ESP32 Brick
- `evse-bricklet <https://github.com/Tinkerforge/evse-bricklet>`__  Firmware source code and hardware design files of the EVSE Bricklet
- `rs485-bricklet <https://github.com/Tinkerforge/rs485-bricklet>`__ Firmware source code and hardware design files of the RS485 Bricklet


WARP2 Charger Hardware
~~~~~~~~~~~~~~~~~~~~~~

- `esp32-ethernet-brick <https://github.com/Tinkerforge/esp32-ethernet-brick>`__ Hardware design files of the ESP32 Ethernet Brick
- `evse-v2-bricklet <https://github.com/Tinkerforge/evse-v2-bricklet>`__ Firmware source code and hardware design files of the EVSE 2.0 Bricklet
- `nfc-bricklet <https://github.com/Tinkerforge/nfc-bricklet>`__ Firmware source code and hardware design files of the NFC Bricklet

WARP3 Charger Hardware
~~~~~~~~~~~~~~~~~~~~~~

- `warp-esp32-ethernet-brick <https://github.com/Tinkerforge/warp-esp32-ethernet-brick>`__ Hardware design files of the WARP ESP32 Ethernet Brick
- `evse-v3-bricklet <https://github.com/Tinkerforge/evse-v3-bricklet>`__ Firmware source code and hardware design files of the EVSE 3.0 Bricklet
- `nfc-bricklet <https://github.com/Tinkerforge/nfc-bricklet>`__ Firmware source code and hardware design files of the NFC Bricklet

WARP Energy Manager Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `esp32-ethernet-brick <https://github.com/Tinkerforge/esp32-ethernet-brick>`__ Hardware design files of the ESP32 Ethernet Brick
- `warp-energy-manager-bricklet <https://github.com/Tinkerforge/warp-energy-manager-bricklet>`__ Firmware source code and hardware design files of the WARP Energy Manager Bricklet

WARP Energy Manager 2.0 Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `esp32-ethernet-brick <https://github.com/Tinkerforge/esp32-ethernet-brick>`__ Hardware design files of the ESP32 Ethernet Brick
- `warp-energy-manager-v2-bricklet <https://github.com/Tinkerforge/warp-energy-manager-v2-bricklet>`__ Firmware source code and hardware design files of the WARP Energy Manager 2.0 Bricklet
- `warp-front-panel-bricklet <https://github.com/Tinkerforge/warp-front-panel-bricklet>`__ Firmware source code and hardware design files of the WARP Front Panel Bricklet

Forked/patched projects
~~~~~~~~~~~~~~~~~~~~~~~

- `arduino-esp32 <https://github.com/Tinkerforge/arduino-esp32>`__
- `esp32-arduino-libs <https://github.com/Tinkerforge/esp32-arduino-libs>`__
- `WireGuard-ESP32-Arduino <https://github.com/Tinkerforge/WireGuard-ESP32-Arduino>`__

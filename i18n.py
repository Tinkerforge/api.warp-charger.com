# -*- coding: utf-8 -*-
"""Internationalization strings for api.warp-charger.com"""

SUPPORTED_LANGUAGES = ['de', 'en']
DEFAULT_LANGUAGE = 'de'

TRANSLATIONS = {
    'de': {
        # --- page ---
        'page_title': 'api.warp-charger.com',
        'subtitle': '\u00d6ffentliche API f\u00fcr WARP Charger und Energy Manager zum Abruf von Day-Ahead-Strompreisen und Temperaturvorhersagen.',

        # --- sections ---
        'endpoints': 'Endpunkte',
        'errors': 'Fehler',

        # --- day ahead prices ---
        'dap_description': 'Gibt Day-Ahead-Strompreise von der ENTSO-E Transparency Platform zur\u00fcck.',
        'dap_param_header': 'Parameter',
        'dap_values_header': 'Werte',
        'dap_description_header': 'Beschreibung',
        'dap_country_desc': 'Gebotszone (DE/LU teilen sich eine Zone)',
        'dap_resolution_desc': 'Zeitliche Aufl\u00f6sung der Preise',
        'dap_example': 'Beispiel',
        'dap_response': 'Antwort',
        'dap_comment_first_date': 'Start-Zeitstempel (UTC)',
        'dap_comment_prices': 'Centicent/MWh (1/100 ct/kWh = Preis * 0,00001 EUR/kWh)',
        'dap_comment_next_date': 'Wann erneut abfragen (UTC)',
        'dap_note': 'Preise sind ganzzahlige Werte in Centicent pro MWh. Umrechnung in EUR/kWh: mit 0,00001 multiplizieren. Daten umfassen typischerweise heute und morgen (verf\u00fcgbar nach ca. 13:00 MEZ).',

        # --- temperatures ---
        'temp_description': 'Gibt st\u00fcndliche Temperaturvorhersagen f\u00fcr heute und morgen zur\u00fcck (DWD ICON-Modell via Open-Meteo). Daten sind auf die lokale Mitternacht der aus den Koordinaten abgeleiteten Zeitzone ausgerichtet.',
        'temp_param_header': 'Parameter',
        'temp_range_header': 'Bereich',
        'temp_description_header': 'Beschreibung',
        'temp_lat_desc': 'Breitengrad (Dezimalgrad)',
        'temp_lon_desc': 'L\u00e4ngengrad (Dezimalgrad)',
        'temp_example': 'Beispiel',
        'temp_response': 'Antwort',
        'temp_comment_first_date': 'UTC-Zeitstempel der lokalen Mitternacht heute',
        'temp_comment_temperatures': '47\u201349 Werte in Zehntel \u00b0C',
        'temp_note': 'Temperaturen sind ganzzahlige Werte in Zehntel Grad Celsius (z.B. <code>123</code> = 12,3\u00a0\u00b0C). Das <code>temperatures</code>-Array enth\u00e4lt 47\u201349 Werte (einer pro Stunde, f\u00fcr heute + morgen). Die Array-Gr\u00f6\u00dfe variiert durch Zeitumstellungen: 47 (Sommerzeit), 48 (normal) oder 49 (Winterzeit).',

        # --- errors ---
        'errors_description': 'Alle Fehler werden als JSON mit einem <code>error</code>-Feld und einem passenden HTTP-Statuscode zur\u00fcckgegeben.',

        # --- common ---
        'toggle_theme': 'Dunkel-/Hellmodus umschalten',
        'switch_language': 'Switch to English',
        'lang_code': 'de',
        'footer_ecosystem': 'Teil des WARP Charger \u00d6kosystems',
        'footer_source': 'Quellcode auf GitHub',
        'footer_legal_info': 'Impressum',
        'footer_privacy': 'Datenschutz',
        'footer_terms': 'AGB',
    },
    'en': {
        # --- page ---
        'page_title': 'api.warp-charger.com',
        'subtitle': 'Public API used by WARP Chargers and Energy Managers to obtain day-ahead electricity prices and temperature forecasts.',

        # --- sections ---
        'endpoints': 'Endpoints',
        'errors': 'Errors',

        # --- day ahead prices ---
        'dap_description': 'Returns day-ahead electricity spot prices from the ENTSO-E Transparency Platform.',
        'dap_param_header': 'Parameter',
        'dap_values_header': 'Values',
        'dap_description_header': 'Description',
        'dap_country_desc': 'Bidding zone (DE/LU share a zone)',
        'dap_resolution_desc': 'Price interval granularity',
        'dap_example': 'Example',
        'dap_response': 'Response',
        'dap_comment_first_date': 'start timestamp (UTC)',
        'dap_comment_prices': 'centicent/MWh (1/100 ct/kWh = price * 0.00001 EUR/kWh)',
        'dap_comment_next_date': 'when to fetch again (UTC)',
        'dap_note': 'Prices are integers in centicent per MWh. To convert to EUR/kWh: multiply by 0.00001. Data typically covers today plus the next day (available after ~13:00 CET).',

        # --- temperatures ---
        'temp_description': 'Returns hourly temperature forecast covering today and tomorrow (DWD ICON model via Open-Meteo). Data is aligned to local midnight of the geographic timezone derived from the coordinates.',
        'temp_param_header': 'Parameter',
        'temp_range_header': 'Range',
        'temp_description_header': 'Description',
        'temp_lat_desc': 'Latitude (decimal degrees)',
        'temp_lon_desc': 'Longitude (decimal degrees)',
        'temp_example': 'Example',
        'temp_response': 'Response',
        'temp_comment_first_date': 'UTC timestamp of local midnight today',
        'temp_comment_temperatures': '47\u201349 values in 10ths of \u00b0C',
        'temp_note': 'Temperatures are integers in 10ths of a degree Celsius (e.g. <code>123</code> = 12.3\u00a0\u00b0C). The <code>temperatures</code> array contains 47\u201349 values (one per hour, covering today + tomorrow). Array size varies due to DST transitions: 47 (spring forward), 48 (normal), or 49 (fall back).',

        # --- errors ---
        'errors_description': 'All errors are returned as JSON with an <code>error</code> field and an appropriate HTTP status code.',

        # --- common ---
        'toggle_theme': 'Toggle dark/light mode',
        'switch_language': 'Auf Deutsch wechseln',
        'lang_code': 'en',
        'footer_ecosystem': 'Part of the WARP Charger ecosystem',
        'footer_source': 'Source on GitHub',
        'footer_legal_info': 'Legal Info',
        'footer_privacy': 'Privacy Notice',
        'footer_terms': 'Terms & Conditions',
    },
}


def get_translations(lang):
    """Return the translation dict for the given language code."""
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    return TRANSLATIONS[lang]

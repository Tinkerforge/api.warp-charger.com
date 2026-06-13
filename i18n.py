# -*- coding: utf-8 -*-
"""Internationalization strings for api.warp-charger.com"""

SUPPORTED_LANGUAGES = ['de', 'en']
DEFAULT_LANGUAGE = 'de'

TRANSLATIONS = {
    'de': {
        # --- page ---
        'page_title': 'api.warp-charger.com',
        'subtitle': '\u00d6ffentliche API f\u00fcr WARP Charger und Energy Manager zum Abruf von Day-Ahead-Strompreisen, Temperatur- und PV-Ertragsvorhersagen.',

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

        # --- solar forecast ---
        'solar_testing_badge': 'Test',
        'solar_testing': 'Hinweis: Dieser Endpunkt befindet sich derzeit nur im Testbetrieb und kann sich \u00e4ndern oder ausfallen. Noch nicht f\u00fcr den produktiven Einsatz verwenden.',
        'solar_description': 'Gibt eine st\u00fcndliche PV-Ertragsprognose f\u00fcr heute und morgen zur\u00fcck.  Daten sind auf die lokale Mitternacht der aus den Koordinaten abgeleiteten Zeitzone ausgerichtet.',
        'solar_param_header': 'Parameter',
        'solar_range_header': 'Bereich',
        'solar_description_header': 'Beschreibung',
        'solar_lat_desc': 'Breitengrad (Dezimalgrad)',
        'solar_lon_desc': 'L\u00e4ngengrad (Dezimalgrad)',
        'solar_dec_desc': 'Modulneigung (0\u00b0 = waagerecht, 90\u00b0 = senkrecht)',
        'solar_az_desc': 'Ausrichtung (0\u00b0 = S\u00fcd, -90\u00b0 = Ost, 90\u00b0 = West, \u00b1180\u00b0 = Nord)',
        'solar_wp_desc': 'Installierte Spitzenleistung in Watt-Peak',
        'solar_example': 'Beispiel',
        'solar_response': 'Antwort',
        'solar_comment_first_date': 'UTC-Zeitstempel der lokalen Mitternacht heute',
        'solar_comment_resolution': 'Aufl\u00f6sung in Minuten (immer 60)',
        'solar_comment_forecast': 'Wh pro Stunde (heute + morgen)',
        'solar_note': 'Der Ertrag wird ganzzahlig in Wattstunden pro Stunde zur\u00fcckgegeben. Das <code>forecast</code>-Array enth\u00e4lt bis zu 48 Werte (einer pro Stunde, f\u00fcr heute + morgen). Ein zus\u00e4tzlicher, forecast.solar-kompatibler Endpunkt <code>/estimate/&lt;lat&gt;/&lt;lon&gt;/&lt;dec&gt;/&lt;az&gt;/&lt;kWp&gt;</code> steht f\u00fcr bestehende Firmware bereit.',


        # --- status ---
        'status_title': 'Dienststatus',
        'status_generated': 'Erstellt',
        'status_json': 'JSON',
        'status_api_docs': 'API-Dokumentation',
        'status_weather_heading': 'Wetter & Solar (Open-Meteo)',
        'status_key_check': 'Live-API-Key-Pr\u00fcfung:',
        'status_key_accepted': 'Key akzeptiert',
        'status_key_rejected': 'Key abgelehnt',
        'status_col_service': 'Dienst',
        'status_col_mode': 'Modus',
        'status_col_upstream': 'Upstream',
        'status_col_last_success': 'Letzter Erfolg',
        'status_col_last_error': 'Letzter Fehler',
        'status_solar_forecast': 'Solarprognose',
        'status_temperatures': 'Temperaturen',
        'status_cached': 'zwischengespeichert',
        'status_commercial': 'kommerziell',
        'status_free': 'kostenlos',
        'status_never': 'nie',
        'status_none': 'keine',
        'status_dap_heading': 'Day-Ahead-Preise (ENTSO-E)',
        'status_col_zone': 'Zone',
        'status_col_serving': 'Auslieferung',
        'status_col_source': 'Quelle',
        'status_col_prices': 'Preise',
        'status_col_entsoe_fallback': 'ENTSO-E / Fallback',
        'status_col_fails': 'Fehler',
        'status_yes': 'ja',
        'status_no': 'nein',
        'status_not_tried': 'nicht versucht',
        'status_fallback': 'Fallback',
        'status_note': 'Zeiten in Serverzeit. Diagnosedaten werden im Speicher gehalten und beim Neustart zur\u00fcckgesetzt.',

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
        'subtitle': 'Public API used by WARP Chargers and Energy Managers to obtain day-ahead electricity prices, temperature and PV yield forecasts.',

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

        # --- solar forecast ---
        'solar_testing_badge': 'Testing',
        'solar_testing': 'Note: This endpoint is currently for testing only and may change or be unavailable. Do not rely on it in production yet.',
        'solar_description': 'Returns an hourly PV yield forecast covering today and tomorrow. Data is aligned to local midnight of the geographic timezone derived from the coordinates.',
        'solar_param_header': 'Parameter',
        'solar_range_header': 'Range',
        'solar_description_header': 'Description',
        'solar_lat_desc': 'Latitude (decimal degrees)',
        'solar_lon_desc': 'Longitude (decimal degrees)',
        'solar_dec_desc': 'Panel tilt (0\u00b0 = horizontal, 90\u00b0 = vertical)',
        'solar_az_desc': 'Azimuth (0\u00b0 = south, -90\u00b0 = east, 90\u00b0 = west, \u00b1180\u00b0 = north)',
        'solar_wp_desc': 'Installed peak power in watt-peak',
        'solar_example': 'Example',
        'solar_response': 'Response',
        'solar_comment_first_date': 'UTC timestamp of local midnight today',
        'solar_comment_resolution': 'Resolution in minutes (always 60)',
        'solar_comment_forecast': 'Wh per hour (today + tomorrow)',
        'solar_note': 'Yield is returned as integers in watt-hours per hour. The <code>forecast</code> array contains up to 48 values (one per hour, covering today + tomorrow). A forecast.solar-compatible endpoint <code>/estimate/&lt;lat&gt;/&lt;lon&gt;/&lt;dec&gt;/&lt;az&gt;/&lt;kWp&gt;</code> is also available for existing firmware.',


        # --- status ---
        'status_title': 'Service Status',
        'status_generated': 'Generated',
        'status_json': 'JSON',
        'status_api_docs': 'API docs',
        'status_weather_heading': 'Weather & Solar (Open-Meteo)',
        'status_key_check': 'Live API key check:',
        'status_key_accepted': 'key accepted',
        'status_key_rejected': 'key rejected',
        'status_col_service': 'Service',
        'status_col_mode': 'Mode',
        'status_col_upstream': 'Upstream',
        'status_col_last_success': 'Last success',
        'status_col_last_error': 'Last error',
        'status_solar_forecast': 'Solar forecast',
        'status_temperatures': 'Temperatures',
        'status_cached': 'cached',
        'status_commercial': 'commercial',
        'status_free': 'free',
        'status_never': 'never',
        'status_none': 'none',
        'status_dap_heading': 'Day-Ahead Prices (ENTSO-E)',
        'status_col_zone': 'Zone',
        'status_col_serving': 'Serving',
        'status_col_source': 'Source',
        'status_col_prices': 'Prices',
        'status_col_entsoe_fallback': 'ENTSO-E / fallback',
        'status_col_fails': 'Fails',
        'status_yes': 'yes',
        'status_no': 'no',
        'status_not_tried': 'not tried',
        'status_fallback': 'fallback',
        'status_note': 'Times are server-local. Diagnostics are kept in memory and reset when the service restarts.',

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


def detect_language(accept_language):
    """Pick the best supported language from an Accept-Language header value."""
    best_lang = DEFAULT_LANGUAGE
    best_q = -1.0
    for part in (accept_language or '').split(','):
        part = part.strip()
        if not part:
            continue
        if ';' in part:
            lang_tag, q_str = part.split(';', 1)
            try:
                q = float(q_str.strip().replace('q=', ''))
            except ValueError:
                q = 0.0
        else:
            lang_tag = part
            q = 1.0
        lang_tag = lang_tag.strip().split('-')[0].lower()
        if lang_tag in SUPPORTED_LANGUAGES and q > best_q:
            best_lang = lang_tag
            best_q = q
    return best_lang

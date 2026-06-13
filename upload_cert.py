#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Upload the local self-signed HTTPS certificate to an ESP32 (WARP charger /
# energy manager) so it can trust this machine as a custom solar-forecast
# server, and (optionally) point its solar-forecast module at the local HTTPS
# server for easy end-to-end testing.
#
# Usage:
#   ./upload_cert.py <esp-ip> [options]
#
# Options:
#   --cert-id N        Certificate slot to use on the device (default: lowest free)
#   --name NAME        Certificate name on the device (default: warp-api-local)
#   --https-port P     HTTPS port this machine serves on (default: $HTTPS_PORT or 5443)
#   --no-configure     Only upload the cert; do not touch the solar_forecast config
#   --regen            Force regeneration of the local self-signed certificate
#
# The certificate is the same one ./main.py serves over HTTPS.

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import local_https

CERT_NAME_DEFAULT = "warp-api-local"


def api_get(host, path, timeout=5):
    with urlopen(Request(f"http://{host}/{path}"), timeout=timeout) as r:
        return json.loads(r.read().decode())


def api_put(host, path, payload, timeout=10):
    req = Request(f"http://{host}/{path}", data=json.dumps(payload).encode(),
                  method="PUT", headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def pick_cert_id(host, requested):
    state = api_get(host, "certs/state")
    used = {c["id"]: c.get("name", "") for c in state.get("certs", [])}
    if requested is not None:
        if requested in used:
            print(f"  cert id {requested} already used (name={used[requested]!r}); replacing it")
            api_put(host, "certs/remove", {"id": requested})
        return requested
    for i in range(0, 64):
        if i not in used:
            return i
    raise RuntimeError("No free certificate slot on device")


def main():
    parser = argparse.ArgumentParser(description="Upload local HTTPS cert to an ESP32")
    parser.add_argument("esp_ip", help="IP address of the ESP32")
    parser.add_argument("--cert-id", type=int, default=None)
    parser.add_argument("--name", default=CERT_NAME_DEFAULT)
    parser.add_argument("--https-port", type=int, default=local_https.DEFAULT_HTTPS_PORT)
    parser.add_argument("--no-configure", action="store_true")
    parser.add_argument("--regen", action="store_true")
    args = parser.parse_args()

    host = args.esp_ip

    # Make sure the certificate exists (same one main.py serves over HTTPS).
    _, _, ips, regenerated = local_https.ensure_cert(force=args.regen)
    cert_pem = local_https.read_public_cert()
    if regenerated:
        print("NOTE: generated a fresh self-signed certificate.")
        print("      (Re)start ./main.py so its HTTPS server uses this certificate.\n")

    # Sanity check: device reachable?
    try:
        ver = api_get(host, "info/version")
        print(f"Device {host}: firmware {ver.get('firmware')}, config {ver.get('config_type')}")
    except (URLError, HTTPError) as e:
        print(f"ERROR: cannot reach device at {host}: {e}")
        sys.exit(1)

    # Which local IP will the device use to reach us (for the api_url)?
    pc_ip = local_https.ip_towards(host)
    if pc_ip not in ips:
        print(f"WARNING: source IP {pc_ip} towards the device is not in the cert SAN "
              f"({', '.join(ips)}). Run with --regen and restart ./main.py.")
    api_url = f"https://{pc_ip}:{args.https_port}/"

    # Upload the certificate.
    cert_id = pick_cert_id(host, args.cert_id)
    print(f"Uploading certificate as id {cert_id} (name={args.name!r}) ...")
    try:
        api_put(host, "certs/add", {"id": cert_id, "name": args.name, "cert": cert_pem})
    except HTTPError as e:
        print(f"ERROR: certs/add failed: {e.code} {e.read().decode(errors='replace')}")
        sys.exit(1)
    certs = api_get(host, "certs/state").get("certs", [])
    print(f"  device now has certs: {certs}")

    if args.no_configure:
        print("\nDone (cert uploaded; solar_forecast config left unchanged).")
        print(f"To use it: set solar_forecast api_url={api_url} , cert_id={cert_id} , source=0")
        return

    # Point the solar-forecast module at the local HTTPS server (pull mode).
    try:
        cfg = api_get(host, "solar_forecast/config")
    except (URLError, HTTPError) as e:
        print(f"\nCert uploaded, but solar_forecast module not available: {e}")
        return
    cfg["enable"] = True
    cfg["source"] = 0
    cfg["api_url"] = api_url
    cfg["cert_id"] = cert_id
    api_put(host, "solar_forecast/config_update", cfg)
    print(f"\nConfigured solar_forecast to pull from {api_url} (cert_id={cert_id}).")
    print("Final config:", api_get(host, "solar_forecast/config"))
    print("\nMake sure ./main.py is running (HTTP+HTTPS) and at least one PV plane is enabled.")
    print("Note: on UNSIGNED firmware builds the pull path returns hardcoded test data;")
    print("      a signed/release build is required to actually fetch from this server.")


if __name__ == "__main__":
    main()

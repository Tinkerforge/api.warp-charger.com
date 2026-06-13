# -*- coding: utf-8 -*-

# Helpers for serving the API locally over HTTPS with an auto-generated
# self-signed certificate. Used by main.py (to start an HTTPS listener when run
# directly) and by upload_cert.py (to push the public cert to an ESP32 so it can
# trust this machine as a custom solar-forecast server).

import ipaddress
import os
import socket
import subprocess

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

CERT_PATH = os.path.join(FILE_DIR, "local_https_cert.pem")
KEY_PATH = os.path.join(FILE_DIR, "local_https_key.pem")
_SAN_STAMP_PATH = os.path.join(FILE_DIR, "local_https_cert.san")

# Default HTTPS port for the local dev server (override with HTTPS_PORT env var).
DEFAULT_HTTPS_PORT = int(os.environ.get("HTTPS_PORT", "5443"))

CERT_CN = "warp-api-local"


def get_local_ipv4s():
    """Return a sorted list of this machine's local IPv4 addresses.

    Excludes loopback (127.*) and link-local (169.254.*). The address that the
    OS would use to reach the public internet is always included first if found.
    """
    ips = set()

    # Primary: the source address of the default route.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    # All configured IPv4 addresses (Linux `ip` tool), so the cert covers every
    # interface the ESP32 might route to.
    try:
        out = subprocess.check_output(["ip", "-4", "-o", "addr", "show"], text=True)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "inet":
                ips.add(parts[3].split("/")[0])
    except Exception:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ips.add(info[4][0])
        except Exception:
            pass

    result = []
    for ip in ips:
        try:
            addr = ipaddress.IPv4Address(ip)
        except ValueError:
            continue
        if addr.is_loopback or addr.is_link_local:
            continue
        result.append(ip)
    return sorted(result)


def ip_towards(target):
    """Return the local source IP the OS would use to reach `target`."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target, 80))
        return s.getsockname()[0]
    finally:
        s.close()


def _san_string(ips):
    entries = [f"IP:{ip}" for ip in ips] + ["IP:127.0.0.1", "DNS:localhost"]
    return ",".join(entries)


def ensure_cert(force=False):
    """Make sure a self-signed cert covering the local IPs exists.

    Returns (cert_path, key_path, ips, regenerated).
    Requires the `openssl` CLI.
    """
    ips = get_local_ipv4s()
    san = _san_string(ips)

    have_san = None
    if os.path.exists(_SAN_STAMP_PATH):
        try:
            have_san = open(_SAN_STAMP_PATH).read().strip()
        except Exception:
            have_san = None

    up_to_date = (
        not force
        and os.path.exists(CERT_PATH)
        and os.path.exists(KEY_PATH)
        and have_san == san
    )
    if up_to_date:
        return CERT_PATH, KEY_PATH, ips, False

    subprocess.check_call([
        "openssl", "req", "-x509",
        "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
        "-days", "3650", "-nodes",
        "-subj", f"/CN={CERT_CN}",
        "-addext", f"subjectAltName={san}",
        "-keyout", KEY_PATH,
        "-out", CERT_PATH,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(_SAN_STAMP_PATH, "w") as f:
        f.write(san)

    return CERT_PATH, KEY_PATH, ips, True


def read_public_cert():
    """Return the PEM-encoded public certificate (ensuring it exists first)."""
    if not os.path.exists(CERT_PATH):
        ensure_cert()
    return open(CERT_PATH).read()

"""Lightweight exchange reachability probe for kill-switch health (NO-LIVE, public API).

Uses a configurable HTTPS GET (default: Kraken public ``SystemStatus``) so operators
get a real connectivity signal without API keys. Optional env disables the probe for
air-gapped CI or sandboxes.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple

_DEFAULT_PROBE_URL = "https://api.kraken.com/0/public/SystemStatus"
_PROBE_DISABLED_ENV = "PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED"
_PROBE_URL_ENV = "PEAK_KILL_SWITCH_EXCHANGE_PROBE_URL"
_TIMEOUT_ENV = "PEAK_KILL_SWITCH_EXCHANGE_PROBE_TIMEOUT_S"


def is_exchange_probe_disabled() -> bool:
    raw = os.environ.get(_PROBE_DISABLED_ENV, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def probe_exchange_http_public() -> Tuple[bool, Dict[str, Any]]:
    """
    GET a public exchange URL; treat 2xx as connected.

    Returns
    -------
    connected:
        True if HTTP response status is 2xx.
    meta:
        ``probe_url``, ``probe_http_status`` or ``probe_error`` / ``probe_error_type``.
    """
    url = (os.environ.get(_PROBE_URL_ENV) or _DEFAULT_PROBE_URL).strip() or _DEFAULT_PROBE_URL
    try:
        timeout = float(os.environ.get(_TIMEOUT_ENV, "5") or "5")
    except ValueError:
        timeout = 5.0
    timeout = max(0.5, min(timeout, 60.0))

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Peak_Trade-KillSwitch-Health/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            ok = 200 <= code < 300
            return ok, {
                "probe_url": url,
                "probe_http_status": code,
                "exchange_connected_source": "http_probe",
            }
    except urllib.error.HTTPError as e:
        return False, {
            "probe_url": url,
            "probe_http_status": e.code,
            "probe_error": str(e),
            "probe_error_type": type(e).__name__,
            "exchange_connected_source": "http_probe",
        }
    except Exception as e:
        return False, {
            "probe_url": url,
            "probe_error": str(e),
            "probe_error_type": type(e).__name__,
            "exchange_connected_source": "http_probe",
        }


__all__ = ["is_exchange_probe_disabled", "probe_exchange_http_public"]

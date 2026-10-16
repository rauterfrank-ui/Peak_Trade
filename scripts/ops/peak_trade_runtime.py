#!/usr/bin/env python3
"""Retired presentation operator entrypoint (fail-closed).

CAPABILITY_O8 retains contract metadata only. Local dashboard / HTTP supervisor
paths are retired; Safari + OKX replace presentation observation.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    payload = {
        "ok": False,
        "code": "PRESENTATION_OPERATOR_ENTRY_RETIRED_FAIL_CLOSED",
        "capability_id": "CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1",
        "presentation_http_host_retired": True,
        "o2_dashboard_supervisor_retired": True,
        "network_session_started": False,
        "orders_submitted": False,
        "credentials_used": False,
        "authorization_consumed": False,
        "detail": "Use productive full-core entrypoints; presentation operator CLI retired.",
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

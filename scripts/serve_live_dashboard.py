#!/usr/bin/env python3
"""Retired live dashboard HTTP entry (fail-closed)."""

from __future__ import annotations

import json
import sys


def main() -> int:
    sys.stdout.write(
        json.dumps(
            {
                "ok": False,
                "code": "PRESENTATION_LIVE_DASHBOARD_RETIRED",
                "detail": "src.live.web presentation stack retired.",
            },
            sort_keys=True,
        )
        + "\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

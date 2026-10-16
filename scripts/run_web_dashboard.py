#!/usr/bin/env python3
"""Retired presentation dashboard entry (fail-closed)."""

from __future__ import annotations

import json
import sys


def main() -> int:
    sys.stdout.write(
        json.dumps(
            {
                "ok": False,
                "code": "PRESENTATION_WEB_DASHBOARD_RETIRED",
                "detail": "Use OKX Safari observation; local WebUI retired.",
            },
            sort_keys=True,
        )
        + "\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

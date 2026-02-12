#!/usr/bin/env python3
"""
Safe JSON parser for Prometheus API responses.

Why:
- Prometheus queries in operator scripts sometimes see transient empty / non-JSON bodies
  (e.g., warmup, networking hiccups, partial reads).
- We want deterministic diagnostics instead of a raw JSONDecodeError traceback.

Contract:
- Reads bytes from stdin.
- Exits 0 if JSON parses and has {"status":"success"}.
- Exits 1 otherwise, printing a short diagnostic to stderr:
  - first 200 bytes (printable)
  - exception type/message (if any)

This helper is token-policy safe: it does not print env vars or secrets, only body prefix.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    raw_bytes = sys.stdin.buffer.read() or b""
    head = raw_bytes[:200]
    try:
        txt = raw_bytes.decode("utf-8", errors="replace")
        doc = json.loads(txt)
        if not isinstance(doc, dict) or doc.get("status") != "success":
            raise ValueError("not a success JSON payload")
        # Print canonical JSON to stdout for downstream processors.
        sys.stdout.write(txt)
        return 0
    except Exception as e:
        sys.stderr.write(f"prom_json_parse_error={type(e).__name__}:{e}\n")
        sys.stderr.write("prom_body_first_200_bytes:\n")
        sys.stderr.write(head.decode("utf-8", errors="replace") + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

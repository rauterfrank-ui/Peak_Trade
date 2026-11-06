#!/usr/bin/env python3
"""
Emit deterministic sample AI Live JSONL events (v=1 canonical format).

Usage:
  python3 scripts/obs/emit_ai_live_sample_events.py --out logs/ai/ai_events.jsonl --n 50 --interval-ms 200

Determinism:
- No random/uuid: values computed deterministically from index
- decision/reason/action: repeating pattern (accept/reject/noop)
- latency_ms: deterministic per decision
- run_id default "demo", component default "execution_watch" (override via flags)
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def _ts_utc_z(epoch_s: float) -> str:
    dt = datetime.fromtimestamp(epoch_s, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _decision(i: int) -> str:
    return ["accept", "reject", "noop"][i % 3]


def _reason(decision: str) -> str:
    if decision == "accept":
        return "none"
    if decision == "reject":
        return "risk_limit"
    return "no_signal"


def _action(decision: str) -> str:
    if decision == "accept":
        return "submit"
    return "none"


def _latency_ms(decision: str) -> float:
    if decision == "accept":
        return 85.0
    if decision == "reject":
        return 10.0
    return 2.0


def main() -> int:
    p = argparse.ArgumentParser(description="Emit deterministic AI Live sample events (v=1 JSONL)")
    p.add_argument("--out", required=True, help="Output JSONL path (will be overwritten).")
    p.add_argument("--n", type=int, default=50, help="Number of events to emit.")
    p.add_argument("--interval-ms", type=int, default=200, help="Interval between events in ms.")
    p.add_argument("--run-id", default="demo", help="Run ID label (default: demo).")
    p.add_argument(
        "--component", default="execution_watch", help="Component label (default: execution_watch)."
    )
    args = p.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    base = time.time()
    run_id = str(args.run_id or "demo").strip() or "demo"
    component = str(args.component or "execution_watch").strip() or "execution_watch"

    # Append-only to match tailing semantics (no truncation).
    with out.open("a", encoding="utf-8") as f:
        for i in range(max(0, int(args.n))):
            d = _decision(i)
            ev = {
                "v": 1,
                "ts_utc": _ts_utc_z(base + (i * (max(args.interval_ms, 0) / 1000.0))),
                "component": component,
                "run_id": run_id,
                "event": "decision",
                "decision": d,
                "reason": _reason(d),
                "latency_ms": _latency_ms(d),
                "action": _action(d),
            }
            f.write(json.dumps(ev, separators=(",", ":"), ensure_ascii=False) + "\n")
            f.flush()
            if args.interval_ms > 0 and i < int(args.n) - 1:
                time.sleep(args.interval_ms / 1000.0)

    print(f"Wrote {int(args.n)} events to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

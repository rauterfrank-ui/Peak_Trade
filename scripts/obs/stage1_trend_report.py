#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import datetime as dt
import json
import sys

# Add repo root to Python path for src imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from src.utils.report_paths import get_reports_root

RE_NEW_ALERTS = re.compile(r"New-alerts heuristic.*\*\*(\d+)\*\*", re.I)
RE_LEGACY = re.compile(r"Legacy-keyword hits.*\*\*(\d+)\*\*", re.I)
RE_ACTIONS = re.compile(r"ack/snooze/resolve/silence.*\*\*(\d+)\*\*", re.I)
RE_CRITICAL = re.compile(r"Severity top:.*critical['\"]:\s*(\d+)", re.I)


def read_int(pat, text):
    m = pat.search(text)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="reports/obs/stage1", help="Snapshot directory")
    ap.add_argument(
        "--reports-root",
        default=None,
        help="Reports root directory (overrides ENV PEAK_REPORTS_DIR and default logic)",
    )
    ap.add_argument("--days", type=int, default=14, help="How many most recent days")
    args = ap.parse_args()

    # Phase 16L: Support --reports-root for Docker/CI use
    if args.reports_root:
        d = pathlib.Path(args.reports_root).resolve() / "obs" / "stage1"
    elif args.dir == "reports/obs/stage1":
        # Default case: use smart resolution (respects PEAK_REPORTS_DIR)
        d = get_reports_root() / "obs" / "stage1"
    else:
        # Custom --dir specified: use as-is
        d = pathlib.Path(args.dir)
    files = sorted(d.glob("*_snapshot.md"))
    files = files[-args.days :] if len(files) > args.days else files

    rows = []
    for fp in files:
        txt = fp.read_text(encoding="utf-8", errors="replace")
        day = fp.name.split("_snapshot.md")[0]
        rows.append(
            {
                "day": day,
                "new_alerts_24h": read_int(RE_NEW_ALERTS, txt),
                "legacy_hits": read_int(RE_LEGACY, txt),
                "operator_actions": read_int(RE_ACTIONS, txt),
                "critical_alerts": read_int(RE_CRITICAL, txt) or 0,
            }
        )

    today = dt.date.today().isoformat()
    print("# Peak_Trade — Stage 1 Trend Report")
    print()
    print(f"- Generated: {today}")
    print(f"- Snapshots: {len(rows)} (last {args.days} requested)")
    print()
    print("| Day | New alerts (24h) | Legacy hits | Operator actions |")
    print("|---|---:|---:|---:|")
    for r in rows:
        print(
            f"| {r['day']} | {r['new_alerts_24h'] if r['new_alerts_24h'] is not None else 'n/a'} | "
            f"{r['legacy_hits'] if r['legacy_hits'] is not None else 'n/a'} | "
            f"{r['operator_actions'] if r['operator_actions'] is not None else 'n/a'} |"
        )

    # quick Go/No-Go hint
    new_alerts_sum = sum((r["new_alerts_24h"] or 0) for r in rows)
    critical_days = sum(1 for r in rows if (r.get("critical_alerts") or 0) > 0)
    parse_error_days = 0  # not tracked yet
    operator_action_days = sum(1 for r in rows if (r.get("operator_actions") or 0) > 0)

    print()
    print("## Quick signal")
    if new_alerts_sum == 0:
        print("- ✅ Keine neuen Alerts im gewählten Zeitraum (heuristisch).")
    else:
        print(
            f"- ⚠️ Neue Alerts im Zeitraum (heuristisch): {new_alerts_sum} → Ursachenanalyse empfohlen."
        )

    # Phase 16K: Compute go_no_go heuristic
    go_no_go = "GO"
    reasons = []

    if critical_days > 0:
        go_no_go = "NO_GO"
        reasons.append(f"critical alerts on {critical_days} days")
    elif new_alerts_sum > 5:
        go_no_go = "HOLD"
        reasons.append(f"new_alerts_total={new_alerts_sum} > threshold(5)")
    elif parse_error_days > 0:
        go_no_go = "HOLD"
        reasons.append(f"parse_error_days={parse_error_days}")

    if not reasons:
        reasons.append("all checks passed")

    # Phase 16K: Write JSON trend
    now_utc = dt.datetime.now(dt.timezone.utc)
    json_trend = {
        "schema_version": 1,
        "generated_at_utc": now_utc.isoformat(),
        "range": {
            "days": len(rows),
            "start": rows[0]["day"] if rows else None,
            "end": rows[-1]["day"] if rows else None,
        },
        "series": [
            {
                "date": r["day"],
                "new_alerts": r["new_alerts_24h"] or 0,
                "critical_alerts": r.get("critical_alerts") or 0,
                "parse_errors": 0,  # not tracked yet
                "operator_actions": r.get("operator_actions") or 0,
            }
            for r in rows
        ],
        "rollups": {
            "new_alerts_total": new_alerts_sum,
            "new_alerts_avg": new_alerts_sum / len(rows) if rows else 0.0,
            "critical_days": critical_days,
            "parse_error_days": parse_error_days,
            "operator_action_days": operator_action_days,
            "go_no_go": go_no_go,
            "reasons": reasons,
        },
    }

    json_out_path = d / "stage1_trend.json"
    json_out_path.write_text(json.dumps(json_trend, indent=2), encoding="utf-8")
    print()
    print(f"✅ Wrote JSON trend: {json_out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse, pathlib, re, datetime as dt

RE_NEW_ALERTS = re.compile(r"New-alerts heuristic.*\*\*(\d+)\*\*", re.I)
RE_LEGACY     = re.compile(r"Legacy-keyword hits.*\*\*(\d+)\*\*", re.I)
RE_ACTIONS    = re.compile(r"ack/snooze/resolve/silence.*\*\*(\d+)\*\*", re.I)

def read_int(pat, text):
    m = pat.search(text)
    return int(m.group(1)) if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="reports/obs/stage1", help="Snapshot directory")
    ap.add_argument("--days", type=int, default=14, help="How many most recent days")
    args = ap.parse_args()

    d = pathlib.Path(args.dir)
    files = sorted(d.glob("*_snapshot.md"))
    files = files[-args.days:] if len(files) > args.days else files

    rows = []
    for fp in files:
        txt = fp.read_text(encoding="utf-8", errors="replace")
        day = fp.name.split("_snapshot.md")[0]
        rows.append({
            "day": day,
            "new_alerts_24h": read_int(RE_NEW_ALERTS, txt),
            "legacy_hits": read_int(RE_LEGACY, txt),
            "operator_actions": read_int(RE_ACTIONS, txt),
        })

    today = dt.date.today().isoformat()
    print("# Peak_Trade — Stage 1 Trend Report")
    print()
    print(f"- Generated: {today}")
    print(f"- Snapshots: {len(rows)} (last {args.days} requested)")
    print()
    print("| Day | New alerts (24h) | Legacy hits | Operator actions |")
    print("|---|---:|---:|---:|")
    for r in rows:
        print(f"| {r['day']} | {r['new_alerts_24h'] if r['new_alerts_24h'] is not None else 'n/a'} | "
              f"{r['legacy_hits'] if r['legacy_hits'] is not None else 'n/a'} | "
              f"{r['operator_actions'] if r['operator_actions'] is not None else 'n/a'} |")

    # quick Go/No-Go hint
    new_alerts_sum = sum((r["new_alerts_24h"] or 0) for r in rows)
    print()
    print("## Quick signal")
    if new_alerts_sum == 0:
        print("- ✅ Keine neuen Alerts im gewählten Zeitraum (heuristisch).")
    else:
        print(f"- ⚠️ Neue Alerts im Zeitraum (heuristisch): {new_alerts_sum} → Ursachenanalyse empfohlen.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from collections import Counter

# Add repo root to Python path for src imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from src.utils.md_helpers import ensure_section_insert_at_top, pick_first_existing


def parse_ts(d):
    for k in ["ts", "timestamp", "time", "created_at", "at", "datetime", "ts_utc", "timestamp_utc"]:
        if k in d and d[k] not in (None, ""):
            v = d[k]
            if isinstance(v, (int, float)):
                if v > 1e12:
                    v = v / 1000.0
                try:
                    return dt.datetime.fromtimestamp(v, tz=dt.timezone.utc)
                except (ValueError, OSError, OverflowError):
                    return None
            if isinstance(v, str):
                s = v.strip().replace("Z", "+00:00")
                if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", s):
                    s = s.replace(" ", "T")
                try:
                    return dt.datetime.fromisoformat(s).astimezone(dt.timezone.utc)
                except (ValueError, OSError):
                    return None
    return None


def pick(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="Repo root (default: .)")
    ap.add_argument("--out-dir", default="reports/obs/stage1", help="Output dir")
    ap.add_argument("--max-depth", type=int, default=10, help="Find max depth")
    ap.add_argument("--max-files", type=int, default=8, help="Parse most recent N files")
    ap.add_argument(
        "--legacy-regex",
        default=r"(legacy|risk[_ -]?limit|old[_ -]?alert|v1|previous)",
        help="Regex heuristic for legacy lines",
    )
    ap.add_argument(
        "--fail-on-new-alerts",
        action="store_true",
        help="Exit nonzero if new alerts in last 24h detected (best-effort)",
    )
    args = ap.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    out_dir = (repo / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    now = dt.datetime.now(dt.timezone.utc)
    cut_24h = now - dt.timedelta(hours=24)

    # Find candidate files
    cands = []
    for p in repo.rglob("*.jsonl"):
        # crude depth limiter
        try:
            rel_parts = p.relative_to(repo).parts
        except Exception:
            continue
        if len(rel_parts) > args.max_depth:
            continue
        sp = str(p).lower()
        if any(
            k in sp for k in ["alert", "alerts", "telemetry", "event", "events", "history", "obs"]
        ):
            try:
                st = p.stat()
            except Exception:
                continue
            cands.append((st.st_mtime, st.st_size, p))

    cands.sort(reverse=True)
    files = [p for _, __, p in cands[: args.max_files]]

    TS_KEYS = ["ts", "timestamp", "time", "created_at", "at", "datetime", "ts_utc", "timestamp_utc"]
    RULE_KEYS = ["rule_id", "rule", "rule_name", "name", "id", "source"]
    SEV_KEYS = ["severity", "level", "sev"]
    TYPE_KEYS = ["event_type", "type", "kind", "name"]

    legacy_kw = re.compile(args.legacy_regex, re.I)

    total_lines = 0
    last24_events = 0
    legacy_hits = 0

    sev_24 = Counter()
    rules_24 = Counter()
    types_24 = Counter()

    first_ts = None
    last_ts = None

    # "new alerts" best-effort: type contains "alert" and is within 24h
    new_alerts_24 = 0

    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    total_lines += 1
                    if legacy_kw.search(line):
                        legacy_hits += 1

                    try:
                        d = json.loads(line)
                    except Exception:
                        continue

                    ts = parse_ts(d)
                    if ts:
                        first_ts = ts if first_ts is None else min(first_ts, ts)
                        last_ts = ts if last_ts is None else max(last_ts, ts)

                    if ts and ts >= cut_24h:
                        last24_events += 1
                        sev = pick(d, SEV_KEYS) or "unknown_sev"
                        rule = pick(d, RULE_KEYS) or "unknown_rule"
                        typ = pick(d, TYPE_KEYS) or "unknown_type"
                        sev_24[str(sev)] += 1
                        rules_24[str(rule)] += 1
                        types_24[str(typ)] += 1
                        if re.search(r"alert", str(typ), re.I):
                            new_alerts_24 += 1
        except Exception:
            continue

    date_str = now.astimezone(dt.timezone.utc).date().isoformat()
    out_path = out_dir / f"{date_str}_snapshot.md"

    def fmt_top(c, n):
        return c.most_common(n)

    actions = sum(
        v for k, v in types_24.items() if re.search(r"(ack|snooze|resolve|silence)", k, re.I)
    )

    # Write report
    lines = []
    lines.append("# Peak_Trade — Stage 1 (DRY-RUN) Daily Snapshot\n")
    lines.append(f"- Reported at (UTC): {now.isoformat()}\n")
    lines.append(f"- Window (last 24h): {cut_24h.isoformat()} → {now.isoformat()}\n")

    lines.append("\n## Candidate JSONL files (newest first)\n")
    if files:
        for fp in files:
            try:
                st = fp.stat()
                lines.append(f"- {fp.relative_to(repo)} ({st.st_size / 1024 / 1024:.2f} MB)\n")
            except Exception:
                lines.append(f"- {fp}\n")
    else:
        lines.append("- (none found)\n")

    lines.append("\n## Summary\n")
    lines.append(f"- Total JSONL lines scanned (best-effort): **{total_lines}**\n")
    lines.append(f"- Lines within last 24h (timestamped, best-effort): **{last24_events}**\n")
    if first_ts and last_ts:
        lines.append(
            f"- Timestamp span detected: **{first_ts.isoformat()} → {last_ts.isoformat()}**\n"
        )
    else:
        lines.append("- Timestamp span detected: *(none / schema differs)*\n")
    lines.append(
        f"- Legacy-keyword hits (heuristic): **{legacy_hits}**  _(regex: {args.legacy_regex})_\n"
    )
    lines.append(
        f"- New-alerts heuristic (last 24h, event_type contains 'alert'): **{new_alerts_24}**\n"
    )

    lines.append("\n## Last 24h breakdown (best-effort)\n")
    lines.append(f"- Severity top: {fmt_top(sev_24, 8)}\n")
    lines.append(f"- Event types top: {fmt_top(types_24, 10)}\n")
    lines.append(f"- Rules top: {fmt_top(rules_24, 12)}\n")

    lines.append("\n## Operator actions (heuristic)\n")
    lines.append(f"- ack/snooze/resolve/silence in last 24h: **{actions}**\n")

    out_path.write_text("".join(lines), encoding="utf-8")

    print(f"✅ Wrote: {out_path}")
    print(f"   New-alerts heuristic (24h): {new_alerts_24}")
    if args.fail_on_new_alerts and new_alerts_24 > 0:
        # 2 = actionable warning (matches your ops style)
        sys.exit(2)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        rows.append(json.loads(s))
    return rows


def _as_int(v: Any, default: int = -1) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _tail(rows: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    if n <= 0:
        return rows
    return rows[-n:]


def _pct(ok: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100.0 * ok / total, 2)


def compute_alerts(rows: List[Dict[str, Any]]) -> List[str]:
    alerts: List[str] = []
    if not rows:
        alerts.append("NO_DATA: registry empty")
        return alerts

    last = rows[-1]

    if _as_int(last.get("ops_status_exit"), -1) != 0:
        alerts.append("OPS_STATUS_FAIL: ops_status_exit != 0")

    if (last.get("prbi_decision") or "").strip() != "READY_FOR_LIVE_PILOT":
        alerts.append("PRBI_NOT_READY: prbi_decision != READY_FOR_LIVE_PILOT")

    if (last.get("prbg_status") or "").strip() != "OK":
        alerts.append("PRBG_STATUS_NOT_OK: prbg_status != OK")

    if _as_int(last.get("prbg_error_count"), 0) > 0:
        alerts.append("PRBG_ERRORS_PRESENT: prbg_error_count > 0")

    # Detect sample_size drop vs median of last 10 (if enough)
    window = rows[-10:] if len(rows) >= 10 else rows
    sizes = [_as_int(r.get("prbg_sample_size"), -1) for r in window]
    sizes = [x for x in sizes if x >= 0]
    if sizes:
        sizes_sorted = sorted(sizes)
        median = sizes_sorted[len(sizes_sorted) // 2]
        last_size = _as_int(last.get("prbg_sample_size"), -1)
        if last_size >= 0 and median > 0 and last_size < int(0.5 * median):
            alerts.append(f"PRBG_SAMPLE_SIZE_DROP: last={last_size} median10={median}")

    return alerts


def render_md(rows: List[Dict[str, Any]], alerts: List[str], limit: int, generated_at: str) -> str:
    total = len(rows)
    ok_ops = sum(1 for r in rows if _as_int(r.get("ops_status_exit"), -1) == 0)
    ok_prbi = sum(1 for r in rows if (r.get("prbi_decision") or "") == "READY_FOR_LIVE_PILOT")
    ok_prbg = sum(1 for r in rows if (r.get("prbg_status") or "") == "OK")
    err_free = sum(1 for r in rows if _as_int(r.get("prbg_error_count"), 0) == 0)

    view = _tail(rows, limit)
    lines: List[str] = []
    lines.append(f"# DONE Registry Trend Report — {generated_at}")
    lines.append(f"- rows_total: **{total}**")
    lines.append(f"- window_tail: **{min(limit, total)}**")
    lines.append("")
    lines.append("## Health Rates (overall)")
    lines.append(f"- ops_status_exit==0: **{ok_ops}/{total}** ({_pct(ok_ops, total)}%)")
    lines.append(f"- prbi READY_FOR_LIVE_PILOT: **{ok_prbi}/{total}** ({_pct(ok_prbi, total)}%)")
    lines.append(f"- prbg_status OK: **{ok_prbg}/{total}** ({_pct(ok_prbg, total)}%)")
    lines.append(f"- prbg_error_count==0: **{err_free}/{total}** ({_pct(err_free, total)}%)")
    lines.append("")
    lines.append("## Alerts (computed on latest)")
    if alerts:
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Tail (most recent first)")
    lines.append(
        "| ts_utc | ops_exit | prbi_decision | prbi_score | prbg_status | prbg_sample_size | prbg_anom | prbg_err | sha256_ok |"
    )
    lines.append("|---|---:|---|---:|---|---:|---:|---:|---|")
    for r in reversed(view):
        lines.append(
            "| {ts} | {ops} | {pdec} | {pscore} | {pstat} | {psz} | {anom} | {err} | {sha} |".format(
                ts=r.get("ts_utc", "__MISSING__"),
                ops=_as_int(r.get("ops_status_exit"), -1),
                pdec=r.get("prbi_decision", "__MISSING__"),
                pscore=_as_int(r.get("prbi_score"), -1),
                pstat=r.get("prbg_status", "__MISSING__"),
                psz=_as_int(r.get("prbg_sample_size"), -1),
                anom=_as_int(r.get("prbg_anomaly_count"), -1),
                err=_as_int(r.get("prbg_error_count"), -1),
                sha=str(bool(r.get("sha256_ok", False))),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--registry",
        default="out/ops/registry/morning_one_shot_done_registry.jsonl",
        help="Input JSONL registry (untracked)",
    )
    ap.add_argument(
        "--outdir",
        default="out/ops/registry/reports",
        help="Output directory (untracked)",
    )
    ap.add_argument("--limit", type=int, default=30, help="Tail window size")
    args = ap.parse_args()

    reg = Path(args.registry)
    rows = _read_jsonl(reg)
    generated_at = _now_utc_iso()
    alerts = compute_alerts(rows)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    md = render_md(rows, alerts, args.limit, generated_at)
    (outdir / "trend_report_latest.md").write_text(md, encoding="utf-8")

    summary = {
        "generated_at_utc": generated_at,
        "rows_total": len(rows),
        "window_tail": min(args.limit, len(rows)),
        "alerts": alerts,
    }
    (outdir / "trend_report_latest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(str(outdir / "trend_report_latest.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

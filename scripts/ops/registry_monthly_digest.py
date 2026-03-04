from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _parse_ts_utc_compact(s: str) -> Optional[datetime]:
    # expects like 20260304T195027Z
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Row:
    ts_utc: datetime
    prbi_decision: str
    prbi_score: Optional[int]
    ops_status_exit: Optional[int]
    prbg_status: str
    prbg_sample_size: Optional[int]
    prbg_anomaly_count: Optional[int]
    prbg_error_count: Optional[int]
    evidence_dir: str
    done_path: str
    sha256_ok: Optional[bool]


def load_registry(path: Path) -> List[Row]:
    rows: List[Row] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        ts = _parse_ts_utc_compact(str(obj.get("ts_utc", "")))
        if ts is None:
            continue
        rows.append(
            Row(
                ts_utc=ts,
                prbi_decision=str(obj.get("prbi_decision", "")),
                prbi_score=(
                    int(obj["prbi_score"])
                    if "prbi_score" in obj and obj["prbi_score"] is not None
                    else None
                ),
                ops_status_exit=(
                    int(obj["ops_status_exit"])
                    if "ops_status_exit" in obj and obj["ops_status_exit"] is not None
                    else None
                ),
                prbg_status=str(obj.get("prbg_status", "")),
                prbg_sample_size=(
                    int(obj["prbg_sample_size"])
                    if "prbg_sample_size" in obj and obj["prbg_sample_size"] is not None
                    else None
                ),
                prbg_anomaly_count=(
                    int(obj["prbg_anomaly_count"])
                    if "prbg_anomaly_count" in obj and obj["prbg_anomaly_count"] is not None
                    else None
                ),
                prbg_error_count=(
                    int(obj["prbg_error_count"])
                    if "prbg_error_count" in obj and obj["prbg_error_count"] is not None
                    else None
                ),
                evidence_dir=str(obj.get("evidence_dir", "")),
                done_path=str(obj.get("done_path", "")),
                sha256_ok=(
                    bool(obj["sha256_ok"])
                    if "sha256_ok" in obj and obj["sha256_ok"] is not None
                    else None
                ),
            )
        )
    rows.sort(key=lambda r: r.ts_utc)
    return rows


def _pct(n: int, d: int) -> str:
    if d <= 0:
        return "n/a"
    return f"{(100.0 * n / d):.0f}%"


def _minmax(vals: List[int]) -> Tuple[Optional[int], Optional[int]]:
    if not vals:
        return None, None
    return min(vals), max(vals)


def build_monthly_digest(rows: List[Row], window_days: int) -> Dict[str, Any]:
    now = _now_utc()
    start = now - timedelta(days=window_days)
    window = [r for r in rows if r.ts_utc >= start]

    total = len(window)
    ops_ok = sum(1 for r in window if r.ops_status_exit == 0)
    prbi_ready = sum(1 for r in window if r.prbi_decision == "READY_FOR_LIVE_PILOT")
    prbg_ok = sum(1 for r in window if r.prbg_status == "OK")
    prbg_err_free = sum(
        1
        for r in window
        if (r.prbg_anomaly_count in (0, None)) and (r.prbg_error_count in (0, None))
    )

    sample_sizes = [r.prbg_sample_size for r in window if isinstance(r.prbg_sample_size, int)]
    sample_sizes_i = [int(x) for x in sample_sizes if x is not None]
    ss_min, ss_max = _minmax(sample_sizes_i)

    tail = window[-min(total, 10) :] if total else []
    tail_rows: List[Dict[str, Any]] = []
    for r in tail:
        tail_rows.append(
            {
                "ts_utc": r.ts_utc.strftime("%Y%m%dT%H%M%SZ"),
                "prbi_decision": r.prbi_decision,
                "prbi_score": r.prbi_score,
                "ops_status_exit": r.ops_status_exit,
                "prbg_status": r.prbg_status,
                "prbg_sample_size": r.prbg_sample_size,
                "prbg_anomaly_count": r.prbg_anomaly_count,
                "prbg_error_count": r.prbg_error_count,
            }
        )

    return {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "window_days": window_days,
        "rows_total": total,
        "rates": {
            "ops_ok": {"num": ops_ok, "den": total, "pct": _pct(ops_ok, total)},
            "prbi_ready": {"num": prbi_ready, "den": total, "pct": _pct(prbi_ready, total)},
            "prbg_ok": {"num": prbg_ok, "den": total, "pct": _pct(prbg_ok, total)},
            "prbg_err_free": {
                "num": prbg_err_free,
                "den": total,
                "pct": _pct(prbg_err_free, total),
            },
        },
        "prbg_sample_size": {"min": ss_min, "max": ss_max},
        "tail": tail_rows,
    }


def render_md(rep: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Registry Monthly Digest")
    lines.append("")
    lines.append(f"- generated_at: {rep['generated_at']}")
    lines.append(f"- window_days: {rep['window_days']}")
    lines.append(f"- rows_total: {rep['rows_total']}")
    lines.append("")
    lines.append("## Rates")
    for k, v in rep["rates"].items():
        lines.append(f"- {k}: {v['num']}/{v['den']} ({v['pct']})")
    lines.append("")
    lines.append("## PRBG sample_size")
    lines.append(f"- min: {rep['prbg_sample_size']['min']}")
    lines.append(f"- max: {rep['prbg_sample_size']['max']}")
    lines.append("")
    lines.append("## Tail")
    if not rep["tail"]:
        lines.append("(none)")
        return "\n".join(lines) + "\n"
    lines.append(
        "| ts_utc | prbi_decision | prbi_score | ops_status_exit | prbg_status | prbg_sample_size | prbg_anomaly_count | prbg_error_count |"
    )
    lines.append("|---|---|---:|---:|---|---:|---:|---:|")
    for r in rep["tail"]:
        lines.append(
            f"| {r['ts_utc']} | {r['prbi_decision']} | {r['prbi_score']} | {r['ops_status_exit']} | {r['prbg_status']} | {r['prbg_sample_size']} | {r['prbg_anomaly_count']} | {r['prbg_error_count']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--registry",
        default="out/ops/registry/morning_one_shot_done_registry.jsonl",
    )
    ap.add_argument("--outdir", default="out/ops/registry/reports")
    ap.add_argument("--days", type=int, default=30, help="Window size in days (default 30).")
    args = ap.parse_args()

    reg = Path(args.registry)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_registry(reg)
    rep = build_monthly_digest(rows, window_days=int(args.days))

    md_path = outdir / "monthly_digest_latest.md"
    js_path = outdir / "monthly_digest_latest.json"
    md_path.write_text(render_md(rep), encoding="utf-8")
    js_path.write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(str(md_path))
    print(str(js_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

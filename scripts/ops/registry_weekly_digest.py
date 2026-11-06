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


def weekly_digest(rows: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
    # Use appended_at_utc if present; otherwise include all rows.
    cutoff = None
    now = datetime.now(timezone.utc)
    if days > 0:
        cutoff = now.timestamp() - days * 24 * 3600

    selected: List[Dict[str, Any]] = []
    for r in rows:
        ts = r.get("appended_at_utc")
        if not ts or not cutoff:
            selected.append(r)
            continue
        try:
            t = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
            if t >= cutoff:
                selected.append(r)
        except Exception:
            selected.append(r)

    total = len(selected)
    ops_ok = sum(1 for r in selected if _as_int(r.get("ops_status_exit"), -1) == 0)
    prbi_ready = sum(
        1 for r in selected if (r.get("prbi_decision") or "") == "READY_FOR_LIVE_PILOT"
    )
    prbg_ok = sum(1 for r in selected if (r.get("prbg_status") or "") == "OK")
    prbg_err_free = sum(1 for r in selected if _as_int(r.get("prbg_error_count"), 0) == 0)

    sizes = [_as_int(r.get("prbg_sample_size"), -1) for r in selected]
    sizes = [x for x in sizes if x >= 0]
    size_min = min(sizes) if sizes else -1
    size_max = max(sizes) if sizes else -1

    return {
        "generated_at_utc": _now_utc_iso(),
        "days": days,
        "rows_total": total,
        "ops_ok": ops_ok,
        "prbi_ready": prbi_ready,
        "prbg_ok": prbg_ok,
        "prbg_err_free": prbg_err_free,
        "prbg_sample_size_min": size_min,
        "prbg_sample_size_max": size_max,
    }


def render_md(d: Dict[str, Any]) -> str:
    total = int(d["rows_total"])

    def pct(x: int) -> float:
        return round(100.0 * x / total, 2) if total else 0.0

    lines: List[str] = []
    lines.append(f"# Weekly Digest — {d['generated_at_utc']}")
    lines.append(f"- window_days: **{d['days']}**")
    lines.append(f"- rows_total: **{total}**")
    lines.append("")
    lines.append("## Rates")
    lines.append(f"- ops_ok: **{d['ops_ok']}/{total}** ({pct(int(d['ops_ok']))}%)")
    lines.append(f"- prbi_ready: **{d['prbi_ready']}/{total}** ({pct(int(d['prbi_ready']))}%)")
    lines.append(f"- prbg_ok: **{d['prbg_ok']}/{total}** ({pct(int(d['prbg_ok']))}%)")
    lines.append(
        f"- prbg_err_free: **{d['prbg_err_free']}/{total}** ({pct(int(d['prbg_err_free']))}%)"
    )
    lines.append("")
    lines.append("## PRBG sample_size range")
    lines.append(f"- min: **{d['prbg_sample_size_min']}**")
    lines.append(f"- max: **{d['prbg_sample_size_max']}**")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--registry",
        default="out/ops/registry/morning_one_shot_done_registry.jsonl",
        help="Input JSONL registry (untracked)",
    )
    ap.add_argument(
        "--days",
        type=int,
        default=7,
        help="Digest window in days (by appended_at_utc)",
    )
    ap.add_argument(
        "--outdir",
        default="out/ops/registry/reports",
        help="Output directory (untracked)",
    )
    args = ap.parse_args()

    reg = Path(args.registry)
    rows = _read_jsonl(reg)
    d = weekly_digest(rows, args.days)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "weekly_digest_latest.md").write_text(render_md(d), encoding="utf-8")
    (outdir / "weekly_digest_latest.json").write_text(
        json.dumps(d, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(str(outdir / "weekly_digest_latest.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

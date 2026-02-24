import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_events_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_events_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _load_events_csv(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            out.append(dict(row))
    return out


def _infer_format(path: Path) -> str:
    s = path.suffix.lower()
    if s == ".jsonl":
        return "jsonl"
    if s == ".csv":
        return "csv"
    return "json"


def _boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "t")


def _is_error(evt: dict[str, Any]) -> bool:
    if _boolish(evt.get("is_error")):
        return True
    lvl = (
        (str(evt.get("level") or evt.get("severity") or evt.get("log_level") or "")).strip().lower()
    )
    if lvl in ("error", "fatal", "critical"):
        return True
    et = (str(evt.get("event_type") or evt.get("type") or "")).strip().lower()
    if et in ("order_error", "fill_error", "exchange_error"):
        return True
    return False


def _is_anomaly(evt: dict[str, Any]) -> bool:
    if _boolish(evt.get("is_anomaly")):
        return True
    et = (str(evt.get("event_type") or evt.get("type") or "")).strip().lower()
    if et in (
        "rate_limit",
        "reconnect",
        "timeout",
        "partial_fill",
        "cancel_replace",
        "order_reject",
    ):
        return True
    lvl = (
        (str(evt.get("level") or evt.get("severity") or evt.get("log_level") or "")).strip().lower()
    )
    if lvl in ("warning", "warn"):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Produce execution_evidence.json/.md from event samples (NO_TRADE)."
    )
    ap.add_argument("--out-dir", default="reports/status")
    ap.add_argument(
        "--input",
        default=None,
        help="Optional events path (offline): JSON array, JSONL, or CSV.",
    )
    ap.add_argument(
        "--input-format",
        default="auto",
        choices=["auto", "json", "jsonl", "csv"],
        help="Input format (auto|json|jsonl|csv)",
    )
    ap.add_argument(
        "--mock-profile",
        default="missing",
        choices=["ok", "anomalies", "errors", "missing"],
    )
    ap.add_argument("--window-start", default=None)
    ap.add_argument("--window-end", default=None)
    args = ap.parse_args()

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    generated_at = _now()
    window_start = args.window_start or generated_at
    window_end = args.window_end or generated_at

    status = "MISSING_INPUT"
    anomaly_count = 0
    error_count = 0
    sample_size = 0
    notes: list[str] = []

    if args.input:
        p = Path(args.input)
        if p.exists():
            fmt = args.input_format
            if fmt == "auto":
                fmt = _infer_format(p)
            if fmt == "json":
                events = _load_events_json(p)
            elif fmt == "jsonl":
                events = _load_events_jsonl(p)
            elif fmt == "csv":
                events = _load_events_csv(p)
            else:
                events = _load_events_json(p)
            sample_size = len(events)
            anomaly_count = sum(1 for e in events if _is_anomaly(e))
            error_count = sum(1 for e in events if _is_error(e))
            status = "OK"
        else:
            notes.append("INPUT_PATH_NOT_FOUND")
    else:
        # deterministic mock profiles for pipeline validation only
        if args.mock_profile == "ok":
            status = "OK"
            sample_size = 100
            anomaly_count = 0
            error_count = 0
        elif args.mock_profile == "anomalies":
            status = "OK"
            sample_size = 100
            anomaly_count = 3
            error_count = 0
        elif args.mock_profile == "errors":
            status = "OK"
            sample_size = 100
            anomaly_count = 0
            error_count = 2
        else:
            status = "MISSING_INPUT"
            sample_size = 0
            anomaly_count = 0
            error_count = 0

    out = {
        "generated_at": generated_at,
        "status": status,
        "window_start": window_start,
        "window_end": window_end,
        "sample_size": sample_size,
        "anomaly_count": anomaly_count,
        "error_count": error_count,
        "notes": notes,
    }

    (outdir / "execution_evidence.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    md = [
        "# Execution Evidence",
        f"- generated_at: {generated_at}",
        f"- status: **{status}**",
        f"- window_start: {window_start}",
        f"- window_end: {window_end}",
        "",
        "## Counts",
        f"- sample_size: {sample_size}",
        f"- anomaly_count: {anomaly_count}",
        f"- error_count: {error_count}",
        "",
        "## Notes",
        *(["- (none)"] if not notes else [f"- {x}" for x in notes]),
    ]
    (outdir / "execution_evidence.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # Producer must never block uploads; non-OK status is conveyed in the artifact.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

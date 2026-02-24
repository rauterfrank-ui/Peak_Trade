import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_events(p: Path) -> list[dict[str, Any]]:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Produce execution_evidence.json/.md from event samples (NO_TRADE)."
    )
    ap.add_argument("--out-dir", default="reports/status")
    ap.add_argument("--input", default=None, help="Optional events JSON array path (offline).")
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
            events = _load_events(p)
            sample_size = len(events)
            anomaly_count = sum(1 for e in events if e.get("is_anomaly") is True)
            error_count = sum(1 for e in events if e.get("is_error") is True)
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

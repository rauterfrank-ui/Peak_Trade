import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Live dry-run checklist (NO_TRADE only).")
    ap.add_argument("--stability", required=True, help="Path to stability_gate.json")
    ap.add_argument("--readiness", required=True, help="Path to live_readiness_scorecard.json")
    ap.add_argument("--out-dir", default="out/ops")
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    hard_fail: list[str] = []
    notes: list[str] = []

    stab_p = Path(args.stability)
    read_p = Path(args.readiness)
    if not stab_p.exists():
        hard_fail.append("MISSING_STABILITY_GATE")
    if not read_p.exists():
        hard_fail.append("MISSING_LIVE_READINESS")

    if not hard_fail:
        stab = load_json(stab_p)
        read = load_json(read_p)
        if not bool(stab.get("overall_ok")):
            hard_fail.append("STABILITY_GATE_FAIL")
        if read.get("decision") != "GO":
            hard_fail.append("READINESS_NOT_GO")

    # Safety assertion: always NO_TRADE (this tool must never enable live)
    notes.append("SAFETY: This checklist performs NO_TRADE actions only.")

    ok = len(hard_fail) == 0
    md = [
        "# Live Dry-Run Checklist",
        f"- timestamp: {ts}",
        f"- ok: **{ok}**",
        "",
        "## Hard Failures",
        *(["- (none)"] if not hard_fail else [f"- {x}" for x in hard_fail]),
        "",
        "## Notes",
        *[f"- {x}" for x in notes],
    ]

    out_path = out_dir / f"live_dryrun_checklist_{ts}.md"
    out_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

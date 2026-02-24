from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(p: str) -> dict[str, Any]:
    path = Path(p)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Live Pilot readiness scorecard (operational).")
    ap.add_argument("--out-dir", default="reports/status")
    ap.add_argument("--stability", required=True)
    ap.add_argument("--live-readiness", required=True)
    ap.add_argument("--shadow-testnet", required=True)
    ap.add_argument("--execution-evidence", required=True)
    ap.add_argument("--min-sample-size", type=int, default=100)
    ap.add_argument("--max-anomalies", type=int, default=0)
    args = ap.parse_args()

    hard: list[str] = []
    warn: list[str] = []
    score = 100

    stab = _load(args.stability)
    live = _load(args.live_readiness)
    st = _load(args.shadow_testnet)
    exe = _load(args.execution_evidence)

    if not bool(stab.get("overall_ok")):
        hard.append("STABILITY_GATE_FAIL")
    if live.get("decision") != "GO":
        hard.append("LIVE_READINESS_NOT_GO")
    if st.get("decision") != "READY_FOR_TESTNET":
        hard.append("SHADOW_TESTNET_NOT_READY")

    ex_status = exe.get("status", "UNKNOWN")
    if ex_status != "OK":
        hard.append(f"EXEC_EVIDENCE_{ex_status}")

    errors = int(exe.get("error_count", 0))
    anomalies = int(exe.get("anomaly_count", 0))
    sample = int(exe.get("sample_size", 0))

    if errors > 0:
        hard.append("EXECUTION_ERRORS_PRESENT")

    if sample < int(args.min_sample_size):
        warn.append("INSUFFICIENT_SAMPLE_SIZE")
        score -= 15

    if anomalies > int(args.max_anomalies):
        warn.append("ANOMALIES_ABOVE_THRESHOLD")
        score -= min(25, anomalies)

    if score < 0:
        score = 0

    if hard:
        decision = "NO_GO"
        score = 0
    else:
        decision = "READY_FOR_LIVE_PILOT" if (score >= 85 and not warn) else "CONTINUE_TESTNET"

    out = {"score": score, "decision": decision, "hard_blocks": hard, "warnings": warn}
    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "live_pilot_scorecard.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    md = [
        "# Live Pilot Scorecard",
        f"- decision: **{decision}**",
        f"- score: **{score}**",
        "",
        "## Hard Blocks",
        *(["- (none)"] if not hard else [f"- {x}" for x in hard]),
        "",
        "## Warnings",
        *(["- (none)"] if not warn else [f"- {x}" for x in warn]),
    ]
    (outdir / "live_pilot_scorecard.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    return 0 if decision == "READY_FOR_LIVE_PILOT" else 2


if __name__ == "__main__":
    raise SystemExit(main())

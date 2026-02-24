from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional


def _load(p: Optional[str]) -> Optional[dict[str, Any]]:
    if not p:
        return None
    path = Path(p)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Shadow/Testnet readiness scorecard (operational).")
    ap.add_argument("--out-dir", default="reports/status")
    ap.add_argument("--stability", required=True)
    ap.add_argument("--live-readiness", required=True)
    ap.add_argument(
        "--execution-evidence",
        default=None,
        help="Optional execution evidence JSON (future).",
    )
    ap.add_argument("--ready-threshold", type=int, default=85)
    args = ap.parse_args()

    hard_blocks: list[str] = []
    warnings: list[str] = []
    score = 100

    stab = _load(args.stability)
    live = _load(args.live_readiness)
    exe = _load(args.execution_evidence)

    if stab is None:
        hard_blocks.append("MISSING_STABILITY_GATE")
    if live is None:
        hard_blocks.append("MISSING_LIVE_READINESS")

    if hard_blocks:
        score = 0
        decision = "NO_GO"
    else:
        if not bool(stab.get("overall_ok")):
            hard_blocks.append("STABILITY_GATE_FAIL")
        if live.get("decision") != "GO":
            hard_blocks.append("LIVE_READINESS_NOT_GO")

        if hard_blocks:
            score = 0
            decision = "NO_GO"
        else:
            if exe is None:
                warnings.append("MISSING_EXECUTION_EVIDENCE")
                score -= 10
            else:
                ex_status = exe.get("status", "UNKNOWN")
                if ex_status != "OK":
                    warnings.append(f"EXECUTION_EVIDENCE_{ex_status}")
                    score -= 10
                anomalies = int(exe.get("anomaly_count", 0))
                errors = int(exe.get("error_count", 0))
                if errors > 0:
                    warnings.append("EXECUTION_ERRORS_PRESENT")
                    score -= 25
                if anomalies > 0:
                    warnings.append("EXECUTION_ANOMALIES_PRESENT")
                    score -= min(20, anomalies)

            if score < 0:
                score = 0

            if score >= int(args.ready_threshold) and not warnings:
                decision = "READY_FOR_TESTNET"
            elif score >= 60:
                decision = "CONTINUE_SHADOW"
            else:
                decision = "NO_GO"

    out = {
        "score": score,
        "decision": decision,
        "hard_blocks": hard_blocks,
        "warnings": warnings,
    }

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "shadow_testnet_scorecard.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    md = [
        "# Shadow/Testnet Readiness Scorecard",
        f"- decision: **{decision}**",
        f"- score: **{score}**",
        "",
        "## Hard Blocks",
        *(["- (none)"] if not hard_blocks else [f"- {x}" for x in hard_blocks]),
        "",
        "## Warnings",
        *(["- (none)"] if not warnings else [f"- {x}" for x in warnings]),
    ]
    (outdir / "shadow_testnet_scorecard.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return 0 if decision == "READY_FOR_TESTNET" else 2


if __name__ == "__main__":
    raise SystemExit(main())

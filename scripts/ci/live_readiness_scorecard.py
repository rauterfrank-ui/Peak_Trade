from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

if __package__:
    from .stability_gate import PRK_REPORT_FILES, read_stability_gate_ages
else:
    from stability_gate import PRK_REPORT_FILES, read_stability_gate_ages


def _read(p: str) -> bytes | None:
    path = Path(p)
    if not path.exists():
        return None
    return path.read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute operational live-readiness scorecard from artifacts."
    )
    ap.add_argument("--out-dir", default="reports/status")
    ap.add_argument("--stability", required=True, help="Path to stability_gate.json")
    ap.add_argument("--status", required=True, help="Path to prj_status_latest.json")
    ap.add_argument("--health", required=True, help="Path to prj_health_summary.json")
    ap.add_argument("--go-threshold", type=int, default=85)
    args = ap.parse_args()

    hard_blocks: list[str] = []
    warnings: list[str] = []

    stability_data = _read(args.stability)
    status_data = _read(args.status)
    health_data = _read(args.health)
    stability = json.loads(stability_data) if stability_data is not None else None
    status = json.loads(status_data) if status_data is not None else None
    health = json.loads(health_data) if health_data is not None else None

    if stability is None:
        hard_blocks.append("MISSING_STABILITY_GATE")
    if status is None:
        hard_blocks.append("MISSING_STATUS_JSON")
    if health is None:
        hard_blocks.append("MISSING_HEALTH_JSON")

    score = 100

    if hard_blocks:
        score = 0
        decision = "NO_GO"
    else:
        stability_error, ages = read_stability_gate_ages(stability)
        if not stability_error and "evidence_scope" in stability:
            if any(
                data is None or sha256(data).hexdigest() != stability["prk_report_sha256"][name]
                for name, data in zip(PRK_REPORT_FILES, (status_data, health_data), strict=True)
            ):
                stability_error = "PRK_REPORT_BINDING_MISMATCH"
        if stability_error:
            hard_blocks.append(stability_error)
            score = 0
            decision = "NO_GO"
        else:
            hs = health.get("status", "UNKNOWN")
            if hs == "NO_SUCCESS":
                hard_blocks.append("PRK_NO_SUCCESS")
                score = 0
                decision = "NO_GO"
            elif health.get("policy_action") == "NO_TRADE":
                hard_blocks.append("PRK_NO_TRADE")
                score = 0
                decision = "NO_GO"
            else:
                if ages["PR-K"] > 24:
                    warnings.append("PRK_AGE_GT_24H")
                    score -= 10
                if ages["PR-J"] > 12:
                    warnings.append("PRJ_AGE_GT_12H")
                    score -= 10

                if hs == "STALE":
                    warnings.append("HEALTH_STALE")
                    score -= 15
                elif hs != "OK":
                    warnings.append(f"HEALTH_{hs}")
                    score -= 5

                if score < 0:
                    score = 0

                decision = (
                    "GO" if (score >= int(args.go_threshold) and not hard_blocks) else "NO_GO"
                )

    out = {
        "score": score,
        "decision": decision,
        "hard_blocks": hard_blocks,
        "warnings": warnings,
        "stability_evidence_scope": stability.get("evidence_scope")
        if isinstance(stability, dict)
        else None,
    }

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "live_readiness_scorecard.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    md = [
        "# Live Readiness Scorecard",
        f"- decision: **{decision}**",
        f"- score: **{score}**",
        "",
        "## Hard Blocks",
        *(["- (none)"] if not hard_blocks else [f"- {x}" for x in hard_blocks]),
        "",
        "## Warnings",
        *(["- (none)"] if not warnings else [f"- {x}" for x in warnings]),
    ]
    (outdir / "live_readiness_scorecard.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    return 0 if decision == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())

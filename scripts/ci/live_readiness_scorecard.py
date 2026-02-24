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

    stability = _load(args.stability)
    status = _load(args.status)
    health = _load(args.health)

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
        overall_ok = bool(stability.get("overall_ok"))
        if not overall_ok:
            hard_blocks.append("STABILITY_GATE_FAIL")
            score = 0
            decision = "NO_GO"
        else:
            hs = health.get("status", "UNKNOWN")
            if hs == "NO_SUCCESS":
                hard_blocks.append("PRK_NO_SUCCESS")
                score = 0
                decision = "NO_GO"
            else:
                # soft scoring
                prk_age = None
                prj_age = None
                for r in stability.get("results", []):
                    if r.get("name") == "PR-K":
                        prk_age = r.get("age_hours")
                    if r.get("name") == "PR-J":
                        prj_age = r.get("age_hours")

                if prk_age is None:
                    warnings.append("MISSING_PRK_AGE")
                    score -= 10
                else:
                    if prk_age > 24:
                        warnings.append("PRK_AGE_GT_24H")
                        score -= 10
                    if prk_age > 36:
                        warnings.append("PRK_AGE_GT_36H")
                        score -= 20

                if prj_age is None:
                    warnings.append("MISSING_PRJ_AGE")
                    score -= 10
                else:
                    if prj_age > 12:
                        warnings.append("PRJ_AGE_GT_12H")
                        score -= 10
                    if prj_age > 36:
                        warnings.append("PRJ_AGE_GT_36H")
                        score -= 20

                if hs == "STALE":
                    warnings.append("HEALTH_STALE")
                    score -= 15
                elif hs != "OK":
                    warnings.append(f"HEALTH_{hs}")
                    score -= 5

                if score < 0:
                    score = 0

                decision = (
                    "GO"
                    if (score >= int(args.go_threshold) and not hard_blocks)
                    else "NO_GO"
                )

    out = {
        "score": score,
        "decision": decision,
        "hard_blocks": hard_blocks,
        "warnings": warnings,
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

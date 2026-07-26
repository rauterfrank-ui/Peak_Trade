#!/usr/bin/env python3
"""Fail-closed Development evaluation runner stub for Momentum V2 vol-scaled v1.

This capability prepares the one-shot Development path but does NOT authorize or
execute evaluation. A separate explicit operator GO is required before any run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRY_POINT = (
    REPO_ROOT / "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "development_evaluation_entry_point_binding_v1.json"
)
REQUIRED_EXEC_GO = (
    "GO_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
)


def main(argv: list[str] | None = None) -> int:
    _ = argv
    payload = json.loads(ENTRY_POINT.read_text(encoding="utf-8"))
    report = {
        "status": "BLOCKED_DEVELOPMENT_EVALUATION_UNAUTHORIZED",
        "hypothesis_id": payload.get("hypothesis_id"),
        "development_evaluation_authorized": payload.get("development_evaluation_authorized"),
        "development_run_slot_available": payload.get("development_run_slot_available"),
        "development_run_slot_consumed": payload.get("run_slot_consumed"),
        "required_operator_go_for_execution": REQUIRED_EXEC_GO,
        "holdout_accessed": False,
        "sealed_accessed": False,
        "evaluation_executed": False,
        "message": (
            "Development evaluation capability is prepared but unauthorized in this "
            "slice. Do not execute without a separate explicit operator GO."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

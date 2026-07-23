#!/usr/bin/env python3
"""Canonical DEVELOPMENT evaluation entry point for CSLRVC v1 (definition/binding only).

This script is a fail-closed placeholder. Strategy implementation and productive
evaluation are unauthorized in the PREREGISTRATION_ONLY slice. No panel load,
no runner start, no run-slot consumption.
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "CSLRVC v1 DEVELOPMENT evaluation entry point "
            "(definition/binding only; evaluation unauthorized)."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("preflight", "dry-validate", "evaluate"),
        default="preflight",
    )
    parser.add_argument("--authorize-single-development-evaluation", default="")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--shadow", action="store_true")
    parser.add_argument("--testnet", action="store_true")
    parser.add_argument("--scheduler", action="store_true")
    args = parser.parse_args(argv)

    payload = {
        "status": "FAIL_CLOSED",
        "reason": "DEFINITION_ONLY_ENTRY_POINT_UNAUTHORIZED_NO_EVALUATION_IN_THIS_SLICE",
        "strategy_identity": "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1",
        "hypothesis_id": "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1",
        "development_evaluation_executed": False,
        "development_run_count": 0,
        "run_slot_consumed": False,
        "holdout_accessed": False,
        "live_authorized": False,
        "orders": False,
        "mode": args.mode,
    }
    if args.live or args.shadow or args.testnet or args.scheduler:
        payload["reason"] = "RUNTIME_FLAG_REJECTED"
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

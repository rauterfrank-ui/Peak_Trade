#!/usr/bin/env python3
"""§11.13.5.Z2M ratify one-shot authenticated trade-fee GET path. No HTTP by default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_fee_reserve_rates_rebind_get_path_v1 import (  # noqa: E402
    EXECUTE_OWNER_GO,
    OWNER_GO,
    classify_fee_reserve_rates_rebind_get_path_v1,
    ratify_fee_reserve_rates_rebind_get_path_v1,
)

REPO_ROOT = _REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--ratify-execution-path", action="store_true")
    parser.add_argument("--execute-trade-fee-get", action="store_true")
    args = parser.parse_args(argv)
    if args.execute_trade_fee_get:
        print("TRADE_FEE_GET_NOT_AUTHORIZED_BY_THIS_RATIFY_GO", file=sys.stderr)
        print(f"SEPARATE_EXECUTE_OWNER_GO_REQUIRED:{EXECUTE_OWNER_GO}", file=sys.stderr)
        return 2
    if args.owner_go != OWNER_GO:
        print(f"OWNER_GO_MISMATCH:{args.owner_go}", file=sys.stderr)
        return 2
    if not args.ratify_execution_path:
        print("RATIFY_FLAG_REQUIRED", file=sys.stderr)
        return 2
    classification = classify_fee_reserve_rates_rebind_get_path_v1()
    ratification = ratify_fee_reserve_rates_rebind_get_path_v1(owner_go=args.owner_go)
    result = {
        "BOUND_ORIGIN_MAIN_SHA": args.bound_origin_main_sha,
        "EVIDENCE_CALL_EXECUTED": False,
        "EVIDENCE_CALL_COUNT": 0,
        "PRODUCTION_NETWORK_CALL_EXECUTED": False,
        "SECRET_VALUE_EXPOSED": False,
        "classification": classification,
        "ratification": ratification,
    }
    print("FEE_RESERVE_RATES_REBIND_GET_PATH_RATIFICATION=")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

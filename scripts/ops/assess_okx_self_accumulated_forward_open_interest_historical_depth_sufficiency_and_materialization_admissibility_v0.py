#!/usr/bin/env python3
"""Assess self-accumulated forward OI historical depth sufficiency and materialization admissibility v0.

Offline-only. No network, materialization, or economic evaluation.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_HISTORICAL_DEPTH_SUFFICIENCY_AND_MATERIALIZATION_ADMISSIBILITY_CONTRACT_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (  # noqa: E402
    CONFIRM_GO,
    assessment_to_dict_v0,
    assess_materialization_admissibility_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Assess self-accumulated OI historical depth sufficiency and "
            "materialization admissibility v0"
        )
    )
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--as-of-utc", required=True)
    parser.add_argument("--enabled", action="store_true")
    args = parser.parse_args()

    if not args.enabled:
        _die("DEFAULT_OFF_ENABLED_FLAG_REQUIRED")
    if args.confirm_go_token != CONFIRM_GO:
        _die(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")

    result = assess_materialization_admissibility_v0(
        archive_root=args.archive_root,
        as_of_utc=args.as_of_utc,
    )
    print(json.dumps(assessment_to_dict_v0(result), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

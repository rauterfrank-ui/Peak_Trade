#!/usr/bin/env python3
"""Offline contract CLI for INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.

Evaluates readiness discovery and one offline observation cycle.
Never starts wallclock sessions, never contacts brokers, never grants GO.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from src.ops.integrated_paper_shadow_observation_session_v1.entrypoint_v1 import (  # noqa: E402
    run_integrated_paper_shadow_observation_cycle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (  # noqa: E402
    produce_paper_shadow_observation_readiness_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.session_lifecycle_v1 import (  # noqa: E402
    plan_observation_session_lifecycle_v1,
    refuse_wallclock_session_execution_v1,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Offline Integrated Paper-Shadow Observation contract evaluator "
            "(no wallclock session, no network, no orders, no Operator-GO)."
        )
    )
    p.add_argument(
        "--mode",
        default="observation",
        help="Must be 'observation' (fail-closed otherwise).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON on stdout.",
    )
    p.add_argument(
        "--attempt-wallclock",
        action="store_true",
        help="Forbidden: proves wallclock execution is refused.",
    )
    p.add_argument(
        "--force-readiness-pass",
        action="store_true",
        help="Forbidden: readiness producer rejects forced PASS.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readiness = produce_paper_shadow_observation_readiness_v1(
        repo_root=_REPO_ROOT,
        force_pass=bool(args.force_readiness_pass),
    )
    lifecycle = plan_observation_session_lifecycle_v1()
    cycle = run_integrated_paper_shadow_observation_cycle_v1(
        mode=args.mode,
        reference_price=Decimal("3500"),
        intended_side="HOLD",
    )
    wallclock_refused = True
    if args.attempt_wallclock:
        try:
            refuse_wallclock_session_execution_v1()
            wallclock_refused = False
        except Exception:
            wallclock_refused = True

    payload = {
        "readiness": readiness.to_dict(),
        "lifecycle": lifecycle.to_dict(),
        "cycle": cycle.to_dict(),
        "wallclock_refused": wallclock_refused,
        "paper_shadow_observation_authorized": False,
        "orders_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"PAPER_SHADOW_OBSERVATION_READINESS_PASS="
            f"{str(readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS).lower()}"
        )
        print("PAPER_SHADOW_OBSERVATION_AUTHORIZED=false")
        print(f"CYCLE_TERMINAL_STATUS={cycle.terminal_status}")
        print(f"WALLCLOCK_REFUSED={str(wallclock_refused).lower()}")
        print(f"AUTHORITY_EFFECT={readiness.authority_effect}")
        for b in readiness.readiness_blockers:
            print(f"READINESS_BLOCKER={b}")
    # Exit 0 when contract evaluation completed fail-closed correctly.
    # Readiness may be false; that is expected without Operator-GO contract.
    if cycle.terminal_status not in {"PASS", "FAIL_CLOSED"}:
        return 2
    if args.attempt_wallclock and not wallclock_refused:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

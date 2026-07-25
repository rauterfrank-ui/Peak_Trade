#!/usr/bin/env python3
"""Operator CLI: canonical OKX Futures Shadow no-order cycle v0.

Fail-closed by default. Requires explicit ``--mode shadow``.
Does not submit orders, start schedulers/daemons, or mutate capital.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from src.ops.bounded_futures_testnet_venue_binding_v0 import (  # noqa: E402
    PRODUCTION_INSTRUMENT_ID,
)
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (  # noqa: E402
    result_to_machine_lines,
    run_okx_futures_shadow_no_order_cycle_v0,
    serialize_okx_futures_shadow_no_order_cycle_result_v0,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run one bounded OKX Futures Shadow no-order cycle "
            "(offline canonical owners only; no order submission)."
        )
    )
    p.add_argument(
        "--mode",
        required=True,
        help="Must be exactly 'shadow' (fail-closed otherwise).",
    )
    p.add_argument(
        "--instrument-id",
        default=PRODUCTION_INSTRUMENT_ID,
        help=f"Canonical non-BTC OKX Futures instrument (default: {PRODUCTION_INSTRUMENT_ID}).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result on stdout (default: machine lines).",
    )
    p.add_argument(
        "--live-enabled",
        action="store_true",
        help="Forbidden flag — forces fail-closed when set.",
    )
    p.add_argument(
        "--order-submission-enabled",
        action="store_true",
        help="Forbidden flag — forces fail-closed when set.",
    )
    p.add_argument(
        "--testnet-order-submission-enabled",
        action="store_true",
        help="Forbidden flag — forces fail-closed when set.",
    )
    p.add_argument(
        "--capital-change-enabled",
        action="store_true",
        help="Forbidden flag — forces fail-closed when set.",
    )
    p.add_argument(
        "--scheduler-enabled",
        action="store_true",
        help="Forbidden flag — forces fail-closed when set.",
    )
    p.add_argument(
        "--daemon-enabled",
        action="store_true",
        help="Forbidden flag — forces fail-closed when set.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode=args.mode,
        instrument_id=args.instrument_id,
        live_enabled=bool(args.live_enabled),
        order_submission_enabled=bool(args.order_submission_enabled),
        testnet_order_submission_enabled=bool(args.testnet_order_submission_enabled),
        capital_change_enabled=bool(args.capital_change_enabled),
        scheduler_enabled=bool(args.scheduler_enabled),
        daemon_enabled=bool(args.daemon_enabled),
    )
    if args.json:
        print(json.dumps(serialize_okx_futures_shadow_no_order_cycle_result_v0(result), indent=2))
    else:
        for line in result_to_machine_lines(result):
            print(line)
    return 0 if result.terminal_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

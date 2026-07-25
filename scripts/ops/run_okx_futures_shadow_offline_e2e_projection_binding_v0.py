#!/usr/bin/env python3
"""Operator CLI: OKX Futures Shadow offline e2e projection binding v0.

Composes readiness gate → canonical no-order cycle → durable projection → verify.
Offline, fail-closed. No orders, network, scheduler, or activation.
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
from src.ops.okx_futures_shadow_offline_e2e_projection_binding_v0 import (  # noqa: E402
    BINDING_STATUS_BLOCKED,
    BINDING_STATUS_PASS,
    result_to_machine_lines,
    run_okx_futures_shadow_offline_e2e_projection_binding_v0,
)

EXIT_PASS = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Bind OKX Futures Shadow no-order cycle to Shadow Preparation "
            "Readiness offline projection pipeline (offline, no order submission)."
        )
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository root for readiness evaluation and projection I/O.",
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
        "--output-path",
        default=None,
        help="Optional relative readiness projection output path (repo-rooted).",
    )
    p.add_argument(
        "--config-path",
        type=Path,
        default=None,
        help="Optional path to readiness gate config TOML.",
    )
    p.add_argument(
        "--evaluated-at",
        default=None,
        help="Optional ISO-8601 evaluation timestamp.",
    )
    p.add_argument(
        "--as-of",
        default=None,
        help="Optional ISO-8601 verifier as-of timestamp.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result on stdout (default: machine lines).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_okx_futures_shadow_offline_e2e_projection_binding_v0(
        repo_root=Path(args.repo_root),
        output_path=args.output_path,
        config_path=args.config_path,
        evaluated_at=args.evaluated_at,
        as_of=args.as_of,
        mode=args.mode,
        instrument_id=args.instrument_id,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        for line in result_to_machine_lines(result):
            print(line)
    if result.binding_status == BINDING_STATUS_PASS:
        return EXIT_PASS
    if result.binding_status == BINDING_STATUS_BLOCKED:
        return EXIT_BLOCKED
    return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())

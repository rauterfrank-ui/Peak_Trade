#!/usr/bin/env python3
"""Run bounded cross-sectional panel fetch preflight (2 instruments max).

Research-only technical preflight. No economic evaluation, no promotion.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_bounded_panel_fetch_v0 import (  # noqa: E402
    GO_TOKEN,
    run_bounded_panel_preflight_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", required=True, help=f"Required GO token: {GO_TOKEN}")
    parser.add_argument(
        "--staging-root",
        type=Path,
        help="Fresh preflight staging root (must not exist)",
    )
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
        help="Archive root for default preflight staging location",
    )
    parser.add_argument("--max-instruments", type=int, default=2)
    parser.add_argument("--preflight-only", action="store_true", default=True)
    args = parser.parse_args()

    if args.confirm != GO_TOKEN:
        _die(f"ERR: confirm_go_token_required:{GO_TOKEN}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    staging_root = args.staging_root
    if staging_root is None:
        staging_root = (
            args.durable_evidence_root
            / "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
            / f"extended_chronological_preflight_v0_{ts_slug}"
        )

    result = run_bounded_panel_preflight_v0(
        confirm=args.confirm,
        staging_root=staging_root,
        max_instruments=args.max_instruments,
        preflight_only=args.preflight_only,
    )
    print(json.dumps({"preflight_result": result.__dict__}, indent=2, sort_keys=True))
    if result.fail_reason or result.status.value != "PREFLIGHT_COMPLETE":
        _die(f"ERR: preflight_failed:{result.status.value}:{result.fail_reason}", 1)


if __name__ == "__main__":
    main()

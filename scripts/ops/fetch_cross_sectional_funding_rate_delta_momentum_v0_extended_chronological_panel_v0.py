#!/usr/bin/env python3
"""Fetch extended chronological panel for cross-sectional funding-rate delta momentum v0.

Public OKX PT1H fetch only. No credentials. Operator GO required.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import fetch_cross_sectional_bound_period_historical_pt1h_sources_v0 as fetch_mod  # noqa: E402
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (  # noqa: E402
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
)

CONFIRM_GO = "GO_BOUNDED_PRE_EVALUATION_PANEL_EXTENSION_AND_IMPLEMENTATION_SCOPE_RATIFICATION_V0"
fetch_mod.CONFIRM_TOKEN = CONFIRM_GO
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--target-staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--period-start-utc", default=PANEL_CALENDAR_START_UTC)
    parser.add_argument("--period-end-utc", default=PANEL_CALENDAR_END_UTC)
    args = parser.parse_args()
    if args.confirm != CONFIRM_GO:
        print(f"ERR: confirm_go_token_required:{CONFIRM_GO}", file=sys.stderr)
        raise SystemExit(2)
    result = fetch_mod.run_historical_fetch(
        confirm=CONFIRM_GO,
        target_staging_root=args.target_staging_root,
        durable_evidence_root=args.durable_evidence_root,
        period_start_utc=args.period_start_utc,
        period_end_utc=args.period_end_utc,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

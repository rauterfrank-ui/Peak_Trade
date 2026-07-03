#!/usr/bin/env python3
"""Materialize bound funding panel for funding-rate delta momentum v0 extended calendar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import (
    materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 as funding_mod,
)  # noqa: E402
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    INFRASTRUCTURE_GO_TOKEN,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
funding_mod.CONFIRM_GO = CONFIRM_GO
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()
    result = funding_mod.materialize_bound_panel_funding_dataset_v0(
        confirm=args.confirm,
        staging_root=args.staging_root,
        skip_fetch=args.skip_fetch,
    )
    manifest_path = args.staging_root / "panel" / "panel_funding_dataset_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["dataset_extension"] = "extended_chronological_with_funding_v1"
        manifest["panel_id"] = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

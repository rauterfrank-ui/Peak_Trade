#!/usr/bin/env python3
"""STEP30A bounded adapter for OKX ETH-USDT-SWAP dataset v2 staging.

Narrow wrapper over verified raw staging promotion runner.
No economic evaluation execution.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.stage_step30a_okx_inst_eth_usdt_perp_dataset_v2_from_raw_staging_v0 import (
    CONFIRM_GO as PROMOTION_CONFIRM_GO,
    DEFAULT_DURABLE_EVIDENCE_ROOT,
    DEFAULT_TARGET_DATASET_ROOT,
    STEP30A_FROZEN_HOLDOUT_END_UTC,
    STEP30A_FROZEN_HOLDOUT_START_UTC,
    STEP30A_STAGING_WINDOW_DAYS,
    run_step30a_dataset_v2_promotion_v0,
)

ADAPTER_CONFIRM_GO = (
    "GO_BOUNDED_STEP30A_RSI_REVERSION_V1_EXTENDED_HOLDOUT_SEPARATED_FUTURES_ECONOMIC_RESEARCH_V0"
)

STEP30A_DATASET_V2_WINDOW_DAYS = STEP30A_STAGING_WINDOW_DAYS
STEP30A_DATASET_V2_TARGET_ROOT = DEFAULT_TARGET_DATASET_ROOT
STEP30A_DURABLE_EVIDENCE_ROOT = DEFAULT_DURABLE_EVIDENCE_ROOT

STEP29M_FROZEN_HOLDOUT_START_UTC = STEP30A_FROZEN_HOLDOUT_START_UTC
STEP29M_FROZEN_HOLDOUT_END_UTC = STEP30A_FROZEN_HOLDOUT_END_UTC


class Step30aDatasetIngestionError(ValueError):
    """Fail-closed adapter contract error."""


def _validate_holdout_constants_match_step29m_v1() -> None:
    if STEP30A_FROZEN_HOLDOUT_START_UTC != STEP29M_FROZEN_HOLDOUT_START_UTC:
        raise Step30aDatasetIngestionError("holdout_start_not_matching_step29m_frozen_constant")
    if STEP30A_FROZEN_HOLDOUT_END_UTC != STEP29M_FROZEN_HOLDOUT_END_UTC:
        raise Step30aDatasetIngestionError("holdout_end_not_matching_step29m_frozen_constant")


def run_step30a_dataset_v2_backward_extension_ingestion_v0(
    *,
    confirm_go_token: str,
    skip_network: bool = False,
    raw_staging_root: Optional[Path] = None,
) -> Mapping[str, Any]:
    if confirm_go_token != ADAPTER_CONFIRM_GO:
        raise Step30aDatasetIngestionError("confirm_go_token_mismatch")
    if not skip_network:
        raise Step30aDatasetIngestionError(
            "network_ingestion_forbidden_use_verified_raw_staging_promotion"
        )

    _validate_holdout_constants_match_step29m_v1()

    result = run_step30a_dataset_v2_promotion_v0(
        confirm_go_token=PROMOTION_CONFIRM_GO,
        raw_staging_root=raw_staging_root,
        target_dataset_root=STEP30A_DATASET_V2_TARGET_ROOT,
        durable_evidence_root=STEP30A_DURABLE_EVIDENCE_ROOT,
    )
    result = dict(result)
    result["step30a_confirm_go"] = ADAPTER_CONFIRM_GO
    result["step30a_dataset_window_days"] = STEP30A_DATASET_V2_WINDOW_DAYS
    result["step30a_target_dataset_root"] = str(STEP30A_DATASET_V2_TARGET_ROOT)
    result["step30a_durable_evidence_root"] = str(STEP30A_DURABLE_EVIDENCE_ROOT)
    result["step30a_frozen_holdout_start_utc"] = STEP30A_FROZEN_HOLDOUT_START_UTC
    result["step30a_frozen_holdout_end_utc"] = STEP30A_FROZEN_HOLDOUT_END_UTC
    optional_warning = result.get("optional_warning")
    if optional_warning is not None:
        result["step30a_optional_warning"] = optional_warning
    return result


def _emit_machine_lines(payload: Mapping[str, Any]) -> None:
    lines = [
        f"STEP30A_CONFIRM_GO={ADAPTER_CONFIRM_GO}",
        f"STEP30A_DATASET_V2_WINDOW_DAYS={STEP30A_DATASET_V2_WINDOW_DAYS}",
        f"STEP30A_TARGET_DATASET_ROOT={STEP30A_DATASET_V2_TARGET_ROOT}",
        f"STEP30A_DURABLE_EVIDENCE_ROOT={STEP30A_DURABLE_EVIDENCE_ROOT}",
    ]
    optional_warning = payload.get("step30a_optional_warning")
    if optional_warning is not None:
        lines.append(f"STEP30A_OPTIONAL_WARNING={optional_warning}")
    for line in lines:
        print(line)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="STEP30A bounded dataset v2 backward extension ingestion adapter."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        choices=[ADAPTER_CONFIRM_GO],
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Offline contract path using verified raw staging only.",
    )
    parser.add_argument("--raw-staging-root", type=Path, default=None)
    ns = parser.parse_args(argv)
    result = run_step30a_dataset_v2_backward_extension_ingestion_v0(
        confirm_go_token=ns.confirm_go_token,
        skip_network=ns.skip_network,
        raw_staging_root=ns.raw_staging_root,
    )
    _emit_machine_lines(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

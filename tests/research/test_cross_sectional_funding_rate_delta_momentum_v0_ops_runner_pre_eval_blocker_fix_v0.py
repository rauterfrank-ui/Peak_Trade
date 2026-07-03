"""Contract tests for delta-momentum v0 ops-runner pre-evaluation blocker fixes."""

from __future__ import annotations

import importlib
from pathlib import Path

from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    EXPECTED_ORIGIN_MAIN_SHA,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

EXPECTED_ORIGIN_MAIN = "525cd82535cd7c65f4cdbca282094e4fc174b0fe"
MISSING_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)


def test_expected_origin_main_sha_matches_post_pr4809_merge_head() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == EXPECTED_ORIGIN_MAIN


def test_ops_runner_materialize_import_contract() -> None:
    materialize_mod = importlib.import_module(
        "scripts.ops.materialize_cross_sectional_funding_rate_delta_momentum_v0_bound_panel_funding_dataset_v0"
    )
    assert callable(materialize_mod.materialize_bound_panel_funding_dataset_v0)

    runner_mod = importlib.import_module(
        "scripts.ops.run_cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0"
    )
    assert runner_mod.materialize_bound_panel_funding_dataset_v0 is (
        materialize_mod.materialize_bound_panel_funding_dataset_v0
    )


def test_missing_extended_chronological_staging_remains_fail_closed() -> None:
    binding = materialize_versioned_research_binding_v0()
    result = materialize_bound_funding_panel_dataset_v0(
        MISSING_STAGING_ROOT,
        period_binding=binding["period_binding"],
        expected_data_digest=binding["data_digest"],
    )
    assert result.status is MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED
    assert "MISSING_PANEL_STAGING" in result.reason_codes

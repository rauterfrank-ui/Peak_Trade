"""Contract tests for delta-momentum v0 ops-runner pre-evaluation blocker fixes."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING,
    FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH,
    ORIGIN_MAIN_SHA_BINDING_ENV_VAR,
    SHA_GUARD_STATUS_PASS,
    resolve_actual_repo_shas_v0,
    verify_origin_main_sha_guard_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
STALE_SHA_0179009507 = "0179009507d0841e155adc60fa347a3208329670"
STALE_SHA_525CD825 = "525cd82535cd7c65f4cdbca282094e4fc174b0fe"
MISSING_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)


def test_missing_origin_main_sha_binding_fails_closed() -> None:
    guard = verify_origin_main_sha_guard_v0(
        repo_root=_REPO_ROOT,
        expected_origin_main_sha=None,
        env={},
    )
    assert guard.passed is False
    assert guard.sha_guard_status == FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING
    assert FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING in guard.fail_reasons


def test_wrong_origin_main_sha_binding_fails_closed() -> None:
    guard = verify_origin_main_sha_guard_v0(
        repo_root=_REPO_ROOT,
        expected_origin_main_sha=STALE_SHA_525CD825,
        binding_source="test_fixture",
    )
    assert guard.passed is False
    assert guard.sha_guard_status == FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH
    assert FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH in guard.fail_reasons
    assert guard.expected_origin_main_sha == STALE_SHA_525CD825
    assert guard.actual_origin_main_sha != STALE_SHA_525CD825


def test_matching_origin_main_sha_binding_reaches_dataset_gate() -> None:
    _, actual_origin_main = resolve_actual_repo_shas_v0(_REPO_ROOT)
    guard = verify_origin_main_sha_guard_v0(
        repo_root=_REPO_ROOT,
        expected_origin_main_sha=actual_origin_main,
        binding_source="test_fixture",
    )
    assert guard.passed is True
    assert guard.sha_guard_status == SHA_GUARD_STATUS_PASS

    binding = materialize_versioned_research_binding_v0()
    result = materialize_bound_funding_panel_dataset_v0(
        MISSING_STAGING_ROOT,
        period_binding=binding["period_binding"],
        expected_data_digest=binding["data_digest"],
    )
    assert result.status is MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED
    assert "MISSING_PANEL_STAGING" in result.reason_codes


def test_runner_context_has_no_hardcoded_stale_origin_main_sha() -> None:
    execution_mod = importlib.import_module(
        "src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0"
    )
    runner_mod = importlib.import_module(
        "scripts.ops.run_cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0"
    )
    execution_source = inspect.getsource(execution_mod)
    runner_source = inspect.getsource(runner_mod)

    assert STALE_SHA_0179009507 not in execution_source
    assert STALE_SHA_525CD825 not in execution_source
    assert STALE_SHA_0179009507 not in runner_source
    assert STALE_SHA_525CD825 not in runner_source
    assert not hasattr(execution_mod, "EXPECTED_ORIGIN_MAIN_SHA")
    assert ORIGIN_MAIN_SHA_BINDING_ENV_VAR == "EXPECTED_ORIGIN_MAIN_SHA"


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

"""Contract tests for CS MA-crossover panel rank-rotation v0 binding completion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
    compute_instrument_score_v0,
    rank_scores_deterministic_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0 import (
    BINDING_SCHEMA_VERSION,
    CONFIG_REL_PATH,
    INSTRUMENT_COUNT,
    OPERATOR_GO_BINDING_RATIFICATION,
    OPERATOR_GO_ECONOMIC_EVALUATION,
    PANEL_DATASET_DIGEST,
    PANEL_DATASET_ID,
    ROW_COUNT_TOTAL,
    STRATEGY_ID,
    STRATEGY_VERSION,
    WINDOW_END_UTC,
    WINDOW_START_UTC,
    BindingMaterializationVerdict,
    BindingRatificationStatus,
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


def test_binding_materialization_complete() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.verdict == BindingMaterializationVerdict.COMPLETE
    assert result.ratification_status == BindingRatificationStatus.BINDINGS_RATIFIED
    assert result.validation_verdict == ValidationVerdict.ACCEPTED_COMPLETE
    assert result.fail_reasons == ()


def test_strategy_and_scope_identity(complete_binding: dict) -> None:
    assert complete_binding["strategy_id"] == STRATEGY_ID
    assert complete_binding["strategy_version"] == STRATEGY_VERSION
    assert (
        complete_binding["research_scope"] == "cross_sectional_ma_crossover_panel_rank_rotation/v0"
    )
    assert complete_binding["schema_version"] == BINDING_SCHEMA_VERSION
    assert complete_binding["operator_go_token_binding_ratification"] == (
        OPERATOR_GO_BINDING_RATIFICATION
    )
    assert complete_binding["operator_go_token_economic_evaluation"] == (
        OPERATOR_GO_ECONOMIC_EVALUATION
    )


def test_dataset_and_universe_bindings(complete_binding: dict) -> None:
    dataset = complete_binding["panel_dataset_binding"]
    assert dataset["dataset_id"] == PANEL_DATASET_ID
    assert dataset["dataset_digest"] == PANEL_DATASET_DIGEST
    assert dataset["row_count_total"] == ROW_COUNT_TOTAL
    assert complete_binding["pit_universe_binding"]["instrument_count"] == INSTRUMENT_COUNT
    assert complete_binding["pit_universe_binding"]["bitcoin_excluded"] is True
    assert complete_binding["pit_universe_binding"]["futures_only"] is True


def test_period_and_ma_parameter_bindings(complete_binding: dict) -> None:
    period = complete_binding["period_binding"]
    assert period["window_start_utc"] == WINDOW_START_UTC
    assert period["window_end_utc"] == WINDOW_END_UTC
    params = complete_binding["parameter_binding"]["parameters"]
    assert params["fast_window"] == 20
    assert params["slow_window"] == 50
    assert params["max_active_instruments"] == 1
    assert params["entry_rank_threshold"] == 1
    assert complete_binding["parameter_binding"]["underlying_signal_binding"] == (
        "ma_crossover/v1@inst-eth-usdt-perp"
    )


def test_cost_and_economic_policy_bindings(complete_binding: dict) -> None:
    cost = complete_binding["cost_execution_binding"]
    assert cost["fee_model_binding"]["fee_bps_per_side"] == 10.0
    assert cost["slippage_model_binding"]["slippage_bps_per_side"] == 5.0
    assert cost["funding_model_binding"]["bind"] is True
    policy = complete_binding["economic_policy_binding"]
    assert policy["economic_validity_policy_version"] == ECONOMIC_VALIDITY_POLICY_VERSION
    assert policy["post_result_threshold_change_forbidden"] is True


def test_terminal_underlying_retry_block(complete_binding: dict) -> None:
    assert (
        complete_binding["system_constraints"]["unchanged_single_instrument_retry_blocked"] is True
    )
    assert complete_binding["terminal_underlying_signal_binding"] == (
        "ma_crossover/v1@inst-eth-usdt-perp"
    )
    assert (
        "ma_crossover/v1@inst-eth-usdt-perp"
        in complete_binding["terminal_failed_binding_exclusions"]
    )


def test_ranking_semantics_validator_accepts_complete_binding(complete_binding: dict) -> None:
    validation = validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0(
        complete_binding["binding"]
    )
    assert validation.valid is True
    assert validation.verdict == ValidationVerdict.ACCEPTED_COMPLETE


def test_score_formula_deterministic_ranking() -> None:
    closes_a = [100.0 + i * 0.5 for i in range(60)]
    closes_b = [100.0 - i * 0.1 for i in range(60)]
    score_a = compute_instrument_score_v0(
        "inst-a",
        closes_a,
        fast_window=20,
        slow_window=50,
        signal_lag_bars=1,
        epoch_index=59,
    )
    score_b = compute_instrument_score_v0(
        "inst-b",
        closes_b,
        fast_window=20,
        slow_window=50,
        signal_lag_bars=1,
        epoch_index=59,
    )
    assert score_a is not None and score_b is not None
    ranked = rank_scores_deterministic_v0([score_b, score_a])
    assert ranked[0].instrument_id == "inst-a"
    assert score_a.score > score_b.score
    assert SCORE_FORMULA_VERSION == "canonical_ma_crossover_normalized_spread_v0"


def test_config_rel_path_exists_after_materialization(complete_binding: dict) -> None:
    assert CONFIG_REL_PATH.endswith(".json")
    assert complete_binding["binding_digest"]
    assert complete_binding["config_digest"]
    assert complete_binding["data_digest"]
    assert complete_binding["implementation_digest"]
    assert complete_binding["material_difference_digest"]
    assert len(complete_binding["binding_digest"]) == 64

"""Contract tests for cross-sectional funding-rate persistence reversal filter v0 binding completion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_scoring_v0 import (
    DECAY_STABILITY_MIN_RATIO,
    FUNDING_SIGNAL_LAG,
    FundingPersistenceLeg,
    MIN_PERSISTENCE_EPOCHS,
    MIN_PERSISTENCE_SCORE_FOR_ENTRY,
    PERSISTENCE_LOOKBACK_K,
    REVERSAL_RISK_LOOKBACK_K,
    FundingPersistenceScoreResultV0,
    funding_cashflow_provenance_marker_v0,
    score_input_provenance_marker_v0,
    select_funding_persistence_extreme_single_leg_v0,
)
from src.research.cross_sectional_funding_rate_rank_delta_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0 as materialize_rank_delta_binding_v0,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_versioned_research_binding_v0 import (
    BINDING_SCHEMA_VERSION,
    CONFIG_REL_PATH,
    FEE_BPS_PER_SIDE,
    PANEL_DATASET_ID,
    PANEL_WARMUP_BARS,
    PERIOD_BINDING_ID,
    ROUNDTRIP_COST_BPS,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingMaterializationVerdict,
    BindingRatificationStatus,
    build_cost_execution_binding_v0,
    compute_material_difference_digest_v0,
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
    write_versioned_research_binding_artifacts_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


def test_binding_materialization_complete_and_ratified() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.verdict == BindingMaterializationVerdict.COMPLETE
    assert result.ratification_status == BindingRatificationStatus.BINDINGS_RATIFIED
    assert result.validation_verdict == ValidationVerdict.ACCEPTED_COMPLETE
    assert result.fail_reasons == ()


def test_strategy_identity(complete_binding: dict) -> None:
    assert complete_binding["strategy_id"] == STRATEGY_ID
    assert complete_binding["strategy_version"] == STRATEGY_VERSION
    assert (
        complete_binding["research_hypothesis_id"]
        == "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_NON_BITCOIN_PERPETUALS_V0"
    )


def test_frozen_score_parameters(complete_binding: dict) -> None:
    params = complete_binding["parameter_binding"]["parameters"]
    assert params["persistence_lookback_k"] == PERSISTENCE_LOOKBACK_K == 4
    assert params["reversal_risk_lookback_k"] == REVERSAL_RISK_LOOKBACK_K == 2
    assert params["signal_lag_bars"] == FUNDING_SIGNAL_LAG == 1
    assert params["min_persistence_epochs"] == MIN_PERSISTENCE_EPOCHS == 3
    assert params["decay_stability_min_ratio"] == DECAY_STABILITY_MIN_RATIO == 0.6
    assert params["min_persistence_score_for_entry"] == MIN_PERSISTENCE_SCORE_FOR_ENTRY == 0.5
    assert PANEL_WARMUP_BARS == 8


def test_required_binding_digests_present(complete_binding: dict) -> None:
    assert complete_binding["implementation_digest"]
    assert complete_binding["config_digest"]
    assert complete_binding["data_digest"]
    assert complete_binding["material_difference_digest"]
    assert complete_binding["binding_digest"]
    digest_bindings = complete_binding["binding"]["digest_bindings"]
    for key in (
        "implementation_digest",
        "config_digest",
        "data_digest",
        "material_difference_digest",
    ):
        assert digest_bindings[key]["status"] == "BOUND"
        assert digest_bindings[key]["value"]


def test_material_difference_digest_stable() -> None:
    assert compute_material_difference_digest_v0() == compute_material_difference_digest_v0()


def test_futures_only_constraints(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False


def test_panel_dataset_binding_extended_calendar(complete_binding: dict) -> None:
    binding = complete_binding["panel_dataset_binding"]
    assert binding["dataset_id"] == PANEL_DATASET_ID
    assert binding["dataset_extension"] == "extended_chronological_with_funding_v1"
    assert binding["funding_usage"] == "funding_rate_for_persistence_reversal_computation"
    assert binding["warmup_bars"] == PANEL_WARMUP_BARS == 8


def test_data_digest_matches_rank_delta_v0(complete_binding: dict) -> None:
    rank_delta_binding = materialize_rank_delta_binding_v0()
    assert complete_binding["data_digest"] == rank_delta_binding["data_digest"]


def test_period_binding_non_overlap(complete_binding: dict) -> None:
    binding = complete_binding["period_binding"]
    assert binding["period_binding_id"] == PERIOD_BINDING_ID
    assert binding["training_end"] < binding["validation_start"]
    assert binding["validation_end"] < binding["out_of_sample_start"]


def test_cost_binding_non_zero() -> None:
    binding = build_cost_execution_binding_v0()
    assert binding["fee_model_binding"]["fee_bps_per_side"] == FEE_BPS_PER_SIDE
    assert binding["execution_model_binding"]["roundtrip_cost_bps"] == ROUNDTRIP_COST_BPS
    assert binding["implicit_zero_cost_forbidden"] is True


def test_economic_policy_minimum_trade_count(complete_binding: dict) -> None:
    policy = complete_binding["economic_policy_binding"]
    assert policy["economic_validity_policy_version"] == ECONOMIC_VALIDITY_POLICY_VERSION
    assert policy["policy_lowering_forbidden"] is True
    assert policy["minimum_trade_count"] == 50


def test_score_cashflow_provenance_separation() -> None:
    assert score_input_provenance_marker_v0() != funding_cashflow_provenance_marker_v0()
    assert "persistence_reversal_filter" in score_input_provenance_marker_v0()


def test_persistence_score_and_selection() -> None:
    scores = [
        FundingPersistenceScoreResultV0(
            instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
            persistence_score=0.75,
            decay_stability=0.8,
            combined_score=0.6,
            mean_funding=-0.0002,
            max_consecutive_same_sign_epochs=3,
            reversal_blocked=False,
            warmup_complete=True,
        ),
        FundingPersistenceScoreResultV0(
            instrument_id="okx:linear_perpetual:SOL:USDT:USDT:perp",
            persistence_score=0.5,
            decay_stability=0.7,
            combined_score=0.35,
            mean_funding=0.0003,
            max_consecutive_same_sign_epochs=2,
            reversal_blocked=False,
            warmup_complete=True,
        ),
    ]
    selection = select_funding_persistence_extreme_single_leg_v0(scores)
    assert selection.leg in {
        FundingPersistenceLeg.LONG_CROWDED_SHORT_REVERSAL,
        FundingPersistenceLeg.SHORT_CROWDED_LONG_REVERSAL,
    }
    assert selection.instrument_id is not None


def test_write_binding_artifacts(tmp_path: Path) -> None:
    config_path, ranking_path = write_versioned_research_binding_artifacts_v0(tmp_path)
    assert config_path.exists()
    assert ranking_path.exists()
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == BINDING_SCHEMA_VERSION
    assert payload["strategy_id"] == STRATEGY_ID

"""Contract tests for cross-sectional funding-rate carry v0 binding completion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_carry_scoring_v0 import (
    FundingCarryLeg,
    compute_instrument_funding_score_v0,
    select_funding_extreme_single_leg_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0 import (
    BINDING_SCHEMA_VERSION,
    CONFIG_REL_PATH,
    FEE_BPS_PER_SIDE,
    PANEL_DATASET_ID,
    PERIOD_BINDING_ID,
    ROUNDTRIP_COST_BPS,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingMaterializationVerdict,
    BindingRatificationStatus,
    build_cost_execution_binding_v0,
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
    write_versioned_research_binding_artifacts_v0,
)
from src.research.cross_sectional_funding_rate_panel_field_materialization_v0 import (
    materialize_funding_field_for_panel_v0,
)
from src.research.cross_sectional_funding_rate_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
)
from tests.research.fixtures.cross_sectional_funding_rate_carry_v0.fixture_builder import (
    build_funding_rates_for_panel_v0,
    build_synthetic_ohlcv_panel_v0,
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
        == "CROSS_SECTIONAL_FUNDING_RATE_CARRY_NON_BITCOIN_PERPETUALS_V0"
    )


def test_required_binding_digests_present(complete_binding: dict) -> None:
    assert complete_binding["implementation_digest"]
    assert complete_binding["config_digest"]
    assert complete_binding["data_digest"]
    assert complete_binding["binding_digest"]
    digest_bindings = complete_binding["binding"]["digest_bindings"]
    for key in ("implementation_digest", "config_digest", "data_digest"):
        assert digest_bindings[key]["status"] == "BOUND"
        assert digest_bindings[key]["value"]


def test_futures_only_constraints(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False
    assert constraints["spot_allowed"] is False
    assert constraints["synthetic_spot_allowed"] is False


def test_panel_dataset_binding_includes_funding_field(complete_binding: dict) -> None:
    binding = complete_binding["panel_dataset_binding"]
    assert binding["dataset_id"] == PANEL_DATASET_ID
    assert "funding_rate" in binding["funding_fields"]
    assert binding["narrow_adapter"] == "pit_okx_pt1h_panel_funding_field_materialization.v0"


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


def test_economic_policy_unchanged(complete_binding: dict) -> None:
    policy = complete_binding["economic_policy_binding"]
    assert policy["economic_validity_policy_version"] == ECONOMIC_VALIDITY_POLICY_VERSION
    assert policy["policy_lowering_forbidden"] is True


def test_funding_panel_adapter_materializes_field() -> None:
    panel = build_synthetic_ohlcv_panel_v0()
    funding = build_funding_rates_for_panel_v0(panel)
    result = materialize_funding_field_for_panel_v0(panel, funding)
    assert result.funding_field == "funding_rate"
    assert len(result.series) == 5
    assert all(bar.funding_rate for series in result.series for bar in series.bars)


def test_funding_extreme_selection_picks_leg() -> None:
    panel = build_synthetic_ohlcv_panel_v0()
    funding = build_funding_rates_for_panel_v0(panel)
    materialized = materialize_funding_field_for_panel_v0(panel, funding)
    scores = []
    for series in materialized.series:
        rates = [float(bar.funding_rate) for bar in series.bars]
        score = compute_instrument_funding_score_v0(
            series.instrument_id,
            rates,
            funding_smoothing_window_bars=1,
            signal_lag_bars=1,
            epoch_index=len(rates) - 1,
        )
        if score is not None:
            scores.append(score)
    selection = select_funding_extreme_single_leg_v0(scores)
    assert selection.leg in {FundingCarryLeg.LONG_LOW, FundingCarryLeg.SHORT_HIGH}
    assert selection.instrument_id is not None


def test_write_binding_artifacts(tmp_path: Path) -> None:
    config_path, ranking_path = write_versioned_research_binding_artifacts_v0(tmp_path)
    assert config_path.exists()
    assert ranking_path.exists()
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == BINDING_SCHEMA_VERSION

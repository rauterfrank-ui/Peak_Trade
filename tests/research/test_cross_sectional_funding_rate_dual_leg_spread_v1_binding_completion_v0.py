"""Contract tests for cross-sectional funding-rate dual-leg spread v1 binding completion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_binding_v1 import (
    PR4925_EXCLUDED_SELECTION_MODE,
    SELECTION_MODE,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (
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
    build_cost_execution_binding_v1,
    materialize_and_validate_versioned_research_binding_v1,
    materialize_versioned_research_binding_v1,
    write_versioned_research_binding_artifacts_v1,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_binding_validator_v1 import (
    ValidationVerdict,
)
from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_v0 import (
    SELECTION_MODE as PR4925_SELECTION_MODE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def complete_binding() -> dict:
    return materialize_versioned_research_binding_v1()


def test_binding_materialization_complete_and_ratified() -> None:
    result = materialize_and_validate_versioned_research_binding_v1()
    assert result.verdict == BindingMaterializationVerdict.COMPLETE
    assert result.ratification_status == BindingRatificationStatus.BINDINGS_RATIFIED
    assert result.validation_verdict == ValidationVerdict.ACCEPTED_COMPLETE
    assert result.fail_reasons == ()


def test_strategy_identity(complete_binding: dict) -> None:
    assert complete_binding["strategy_id"] == STRATEGY_ID
    assert complete_binding["strategy_version"] == STRATEGY_VERSION
    assert (
        complete_binding["research_hypothesis_id"]
        == "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_NON_BITCOIN_PERPETUALS_V1"
    )


def test_material_difference_vs_pr4925_explicit(complete_binding: dict) -> None:
    direction = complete_binding["binding"]["direction_semantics"]
    assert direction["selection_mode"] == SELECTION_MODE
    assert direction["selection_mode"] != PR4925_SELECTION_MODE
    assert direction["selection_mode"] != PR4925_EXCLUDED_SELECTION_MODE
    assert direction["dual_leg_simultaneous_required"] is True
    assert direction["single_slot_rotation"] is False
    assert complete_binding["material_difference_vs_pr4925_confirmed"] is True
    assert "funding_delta_lookback_k" not in complete_binding["parameter_binding"]["parameters"]


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


def test_panel_dataset_binding_extended_calendar(complete_binding: dict) -> None:
    binding = complete_binding["panel_dataset_binding"]
    assert binding["dataset_id"] == PANEL_DATASET_ID
    assert binding["dataset_extension"] == "extended_chronological_with_funding_v1"
    assert binding["panel_calendar_start_utc"] == "2024-05-01T00:00:00Z"
    assert binding["panel_calendar_end_utc"] == "2024-09-01T00:00:00Z"


def test_period_binding_non_overlap(complete_binding: dict) -> None:
    binding = complete_binding["period_binding"]
    assert binding["period_binding_id"] == PERIOD_BINDING_ID
    assert binding["training_end"] < binding["validation_start"]
    assert binding["validation_end"] < binding["out_of_sample_start"]


def test_cost_binding_non_zero() -> None:
    binding = build_cost_execution_binding_v1()
    assert binding["fee_model_binding"]["fee_bps_per_side"] == FEE_BPS_PER_SIDE
    assert binding["execution_model_binding"]["roundtrip_cost_bps"] == ROUNDTRIP_COST_BPS
    assert binding["implicit_zero_cost_forbidden"] is True


def test_economic_policy_minimum_trade_count(complete_binding: dict) -> None:
    policy = complete_binding["economic_policy_binding"]
    assert policy["economic_validity_policy_version"] == ECONOMIC_VALIDITY_POLICY_VERSION
    assert policy["policy_lowering_forbidden"] is True
    assert policy["minimum_trade_count"] == 50


def test_no_evaluation_executed_flag(complete_binding: dict) -> None:
    assert complete_binding["economic_evaluation_executed"] is False
    assert complete_binding["authority_effect"] == "NONE"
    assert complete_binding["runtime_effect"] == "NONE"


def test_fail_closed_on_missing_digest() -> None:
    binding = materialize_versioned_research_binding_v1()["binding"]
    binding["digest_bindings"]["config_digest"] = {"status": "REQUIRED_UNBOUND"}
    from src.research.cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_binding_validator_v1 import (
        validate_funding_rate_dual_leg_spread_ranking_semantics_binding_v1,
    )

    result = validate_funding_rate_dual_leg_spread_ranking_semantics_binding_v1(binding)
    assert result.valid is False
    assert any("DIGEST_BINDING_UNBOUND" in reason for reason in result.fail_reasons)


def test_write_binding_artifacts(tmp_path: Path) -> None:
    config_path, ranking_path = write_versioned_research_binding_artifacts_v1(tmp_path)
    assert config_path.exists()
    assert ranking_path.exists()
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == BINDING_SCHEMA_VERSION
    assert payload["strategy_id"] == STRATEGY_ID
    assert payload["strategy_version"] == STRATEGY_VERSION

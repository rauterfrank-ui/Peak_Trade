"""Contract tests for extreme carry/reversion v0 binding readiness slice."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_funding_rate_extreme_carry_reversion_absolute_funding_extreme_binding_v0 import (
    AbsoluteFundingExtremeBindingStatus,
    evaluate_absolute_funding_extreme_binding_v0,
    materialize_absolute_funding_extreme_binding_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_cost_survival_binding_v0 import (
    ROUNDTRIP_COST_BPS,
    CostSurvivalBindingStatus,
    evaluate_cost_survival_binding_v0,
    materialize_cost_survival_binding_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness_v0 import (
    AUTHORITY_EFFECT,
    BindingRatificationStatus,
    BindingReadinessVerdict,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    evaluate_scope_binding_readiness_v0,
    materialize_binding_readiness_envelope_v0,
    ratify_binding_readiness_envelope_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

PASS_PANEL = (
    ("ETH-USDT-SWAP", 0.00001),
    ("SOL-USDT-SWAP", 0.00001),
    ("AVAX-USDT-SWAP", 0.00001),
    ("DOGE-USDT-SWAP", 0.00001),
    ("LINK-USDT-SWAP", 0.00100),
)

BELOW_THRESHOLD_PANEL = (
    ("ETH-USDT-SWAP", 0.00005),
    ("SOL-USDT-SWAP", 0.00004),
    ("AVAX-USDT-SWAP", 0.00003),
    ("DOGE-USDT-SWAP", 0.00002),
    ("LINK-USDT-SWAP", 0.00006),
)


def test_absolute_funding_extreme_binding_materialized() -> None:
    binding = materialize_absolute_funding_extreme_binding_v0()
    assert binding["feature_kind"] == "absolute_funding_extreme"
    assert binding["status"] == "BOUND"
    assert binding["authority_effect"] == "NONE"


def test_absolute_funding_extreme_pass_with_dislocation() -> None:
    result = evaluate_absolute_funding_extreme_binding_v0(PASS_PANEL, epoch_index=1)
    assert result.status is AbsoluteFundingExtremeBindingStatus.PASS
    assert result.reason_code == "absolute_funding_extreme_pass"
    assert result.selected_instrument_id == "LINK-USDT-SWAP"
    assert result.selected_abs_zscore is not None
    assert result.selected_abs_zscore >= 1.0


def test_absolute_funding_extreme_fail_below_threshold() -> None:
    result = evaluate_absolute_funding_extreme_binding_v0(
        BELOW_THRESHOLD_PANEL,
        epoch_index=1,
    )
    assert result.status is AbsoluteFundingExtremeBindingStatus.FAIL
    assert result.reason_code in {
        "absolute_dislocation_below_threshold",
        "percentile_dislocation_below_threshold",
    }


def test_absolute_funding_extreme_blocked_when_panel_missing() -> None:
    result = evaluate_absolute_funding_extreme_binding_v0([], epoch_index=1)
    assert result.status is AbsoluteFundingExtremeBindingStatus.BLOCKED
    assert result.reason_code == "missing_panel_funding_rates"


def test_cost_survival_binding_materialized() -> None:
    binding = materialize_cost_survival_binding_v0()
    assert binding["feature_kind"] == "cost_survival"
    assert binding["status"] == "BOUND"
    assert binding["cost_execution_binding"]["implicit_zero_cost_forbidden"] is True


def test_cost_survival_pass_with_positive_net_edge() -> None:
    result = evaluate_cost_survival_binding_v0(
        expected_carry_bps=100.0,
        funding_drag_bps=5.0,
    )
    assert result.status is CostSurvivalBindingStatus.PASS
    assert result.reason_code == "cost_survival_pass"
    assert result.net_edge_bps == pytest.approx(100.0 - ROUNDTRIP_COST_BPS - 5.0)


def test_cost_survival_fail_when_cost_drag_dominates() -> None:
    result = evaluate_cost_survival_binding_v0(
        expected_carry_bps=10.0,
        funding_drag_bps=5.0,
    )
    assert result.status is CostSurvivalBindingStatus.FAIL
    assert result.reason_code == "net_edge_insufficient"


def test_cost_survival_blocked_when_funding_unknown() -> None:
    result = evaluate_cost_survival_binding_v0(
        expected_carry_bps=100.0,
        funding_drag_bps=None,
    )
    assert result.status is CostSurvivalBindingStatus.BLOCKED
    assert result.reason_code == "funding_drag_unknown"


def test_cost_survival_blocked_when_cost_model_incomplete() -> None:
    broken_binding = materialize_cost_survival_binding_v0()
    broken_binding["cost_execution_binding"] = {"execution_model_binding": {}}
    result = evaluate_cost_survival_binding_v0(
        expected_carry_bps=100.0,
        funding_drag_bps=5.0,
        binding=broken_binding,
    )
    assert result.status is CostSurvivalBindingStatus.BLOCKED
    assert result.reason_code == "cost_model_incomplete"


def test_scope_readiness_fail_closed_until_both_bindings_pass() -> None:
    blocked = evaluate_scope_binding_readiness_v0()
    assert blocked.scope_readiness is False
    assert blocked.verdict is BindingReadinessVerdict.FAIL_CLOSED
    assert blocked.ratification_status is BindingRatificationStatus.FAIL_CLOSED_NOT_RATIFIED
    assert blocked.absolute_funding_extreme_status is AbsoluteFundingExtremeBindingStatus.BLOCKED
    assert blocked.cost_survival_status is CostSurvivalBindingStatus.BLOCKED
    assert blocked.evaluation_execution_authorized is False
    assert blocked.economic_evaluation_executed is False
    assert blocked.runtime_authority_granted is False
    assert blocked.promotion_authority_granted is False
    assert blocked.order_authority_granted is False


def test_scope_readiness_pass_when_both_bindings_pass() -> None:
    ready = evaluate_scope_binding_readiness_v0(
        panel_funding_rates=PASS_PANEL,
        expected_carry_bps=100.0,
        funding_drag_bps=5.0,
        epoch_index=1,
    )
    assert ready.scope_readiness is True
    assert ready.verdict is BindingReadinessVerdict.READY
    assert ready.ratification_status is BindingRatificationStatus.BINDINGS_RATIFIED
    assert ready.absolute_funding_extreme_status is AbsoluteFundingExtremeBindingStatus.PASS
    assert ready.cost_survival_status is CostSurvivalBindingStatus.PASS
    assert ready.evaluation_infrastructure_ready is False
    assert ready.evaluation_execution_authorized is False


def test_scope_readiness_stays_false_if_only_one_binding_passes() -> None:
    partial = evaluate_scope_binding_readiness_v0(
        panel_funding_rates=PASS_PANEL,
        expected_carry_bps=10.0,
        funding_drag_bps=5.0,
        epoch_index=1,
    )
    assert partial.scope_readiness is False
    assert partial.absolute_funding_extreme_status is AbsoluteFundingExtremeBindingStatus.PASS
    assert partial.cost_survival_status is CostSurvivalBindingStatus.FAIL


def test_binding_readiness_envelope_identity_and_no_authority() -> None:
    envelope = materialize_binding_readiness_envelope_v0()
    assert envelope["strategy_id"] == STRATEGY_ID
    assert envelope["strategy_version"] == STRATEGY_VERSION
    assert envelope["authority_effect"] == AUTHORITY_EFFECT
    assert envelope["runtime_effect"] == RUNTIME_EFFECT
    assert envelope["economic_evaluation_executed"] is False
    assert envelope["runtime_authority_granted"] is False
    assert envelope["binding_ratified"] is False
    assert envelope["scope_readiness"] is False


def test_ratify_binding_readiness_envelope_v0() -> None:
    ratified = ratify_binding_readiness_envelope_v0(
        panel_funding_rates=PASS_PANEL,
        expected_carry_bps=100.0,
        funding_drag_bps=5.0,
        epoch_index=1,
    )
    assert ratified["binding_ratified"] is True
    assert ratified["scope_readiness"] is True
    assert ratified["absolute_funding_extreme_status"] == "PASS"
    assert ratified["cost_survival_status"] == "PASS"
    assert ratified["blockers"] == []

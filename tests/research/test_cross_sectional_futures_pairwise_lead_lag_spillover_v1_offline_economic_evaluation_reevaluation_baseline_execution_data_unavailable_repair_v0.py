"""Repair contract tests for pairwise spillover baseline cost-binding normalization v0."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_cost_execution_binding_normalization_v0 import (
    normalize_cost_execution_binding_for_backtest_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    _normalize_cost_execution_binding_for_backtest_v0 as lead_lag_normalize_cost_binding_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    REASON_BASELINE_BACKTEST_OWNER_INVOKED,
    REEVALUATION_BASELINE_EXECUTION_GO_TOKEN,
    run_baseline_offline_economic_evaluation_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    _run_pairwise_spillover_single_slot_orchestrator_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_BASELINE_EXEC_GO = REEVALUATION_BASELINE_EXECUTION_GO_TOKEN


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


@pytest.fixture(name="panel_series")
def fixture_panel_series():
    return build_synthetic_panel_series_v0(bar_count=40, end="2024-06-01T02:00:00Z")


class TestSharedNormalizerReuse:
    def test_pairwise_binding_normalizes_fee_and_slippage_aliases(
        self, complete_binding: dict
    ) -> None:
        raw = complete_binding["cost_execution_binding"]
        normalized = normalize_cost_execution_binding_for_backtest_v0(raw)
        assert normalized["fee_model_binding"] == raw["fee_binding"]
        assert normalized["slippage_model_binding"] == raw["slippage_binding"]
        assert normalized["funding_model_binding"] == raw["funding_binding"]
        assert normalized["fee_model_binding"]["fee_bps_per_side"] > 0
        assert normalized["slippage_model_binding"]["slippage_bps_per_side"] > 0

    def test_fee_model_binding_passthrough_unchanged(self, complete_binding: dict) -> None:
        raw = dict(complete_binding["cost_execution_binding"])
        raw["fee_model_binding"] = {"fee_bps_per_side": 10.0, "fee_model_version": "x"}
        raw["slippage_model_binding"] = {
            "slippage_bps_per_side": 5.0,
            "slippage_model_version": "y",
        }
        assert normalize_cost_execution_binding_for_backtest_v0(raw) == raw

    def test_lead_lag_wrapper_matches_shared_normalizer(self, complete_binding: dict) -> None:
        raw = complete_binding["cost_execution_binding"]
        assert lead_lag_normalize_cost_binding_v0(
            raw
        ) == normalize_cost_execution_binding_for_backtest_v0(raw)


class TestBacktestOwnerContract:
    def test_pairwise_binding_does_not_trigger_implicit_zero_cost_forbidden(
        self,
        complete_binding: dict,
        panel_series,
    ) -> None:
        orchestrator = _run_pairwise_spillover_single_slot_orchestrator_v0(
            panel_series=panel_series,
            versioned_binding=complete_binding,
        )
        backtest = run_single_slot_panel_backtest_v0(
            orchestrator,
            panel_series,
            cost_execution_binding=normalize_cost_execution_binding_for_backtest_v0(
                complete_binding["cost_execution_binding"]
            ),
        )
        assert backtest.roundtrip_cost_bps > 0
        assert backtest.trade_count >= 0


class TestBaselineExecutionRepair:
    def test_baseline_path_invokes_backtest_with_normalized_cost_binding(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            panel_series=panel_series,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.blocked is False
        assert result.actual_baseline_backtest_call_present is True
        assert result.baseline_backtest_owner_call_count == 1
        assert REASON_BASELINE_BACKTEST_OWNER_INVOKED in result.reason_codes

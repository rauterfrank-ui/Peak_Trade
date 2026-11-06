"""Binding-compatibility contract tests for level-rank economic viability evidence materializer v0."""

from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.economic_validity_policy_v1 import (
    EconomicValidityEvaluationStatus,
    EconomicValidityGateEvaluationV1,
)
from src.research.cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    REASON_CONFLICTING_FEE_BINDINGS,
    REASON_CONFLICTING_INSTRUMENT_BINDINGS,
    REASON_FEE_BINDING_MISSING,
    REASON_INSTRUMENT_BINDING_MISSING,
    RUNTIME_EFFECT,
    EconomicClassification,
    EconomicViabilityEvidenceBindingResolutionError,
    CrossSectionalRobustnessMetricsV0,
    materialize_economic_viability_evidence,
    resolve_economic_viability_binding_references_v0,
)
from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    RobustnessStageResultsV0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    SingleSlotBacktestResultV0,
)

EXPECTED_BINDING_DIGEST = "b7099d17af888dabebf14a63797729f807f866d265aeb5095c385541222fc2f2"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _minimal_backtest() -> SingleSlotBacktestResultV0:
    equity = pd.Series(
        [10000.0, 9990.0], index=pd.to_datetime(["2024-05-01", "2024-05-02"], utc=True)
    )
    return SingleSlotBacktestResultV0(
        wiring_version="v0",
        initial_cash=10000.0,
        final_equity=9990.0,
        gross_return=-0.001,
        net_return=-0.001,
        trade_count=1,
        turnover=1.0,
        fee_drag=1.0,
        slippage_impact=0.5,
        roundtrip_cost_bps=20.0,
        equity_curve=equity,
        trades=pd.DataFrame(),
        stats={"expectancy": -10.0, "profit_factor": 0.0, "sharpe": -1.0, "sortino": -1.0},
        authority_effect=AUTHORITY_EFFECT,
    )


def _minimal_robustness() -> RobustnessStageResultsV0:
    return RobustnessStageResultsV0(
        wiring_version="v0",
        walk_forward_results=(),
        monte_carlo_summary={"metric_quantiles": {"total_return": {"p50": -0.001}}},
        stress_results={"scenarios": []},
        parameter_sensitivity_status="NOT_EXECUTED",
        authority_effect=AUTHORITY_EFFECT,
    )


def _minimal_robustness_metrics() -> CrossSectionalRobustnessMetricsV0:
    return CrossSectionalRobustnessMetricsV0(
        walk_forward_pass_ratio=0.0,
        out_of_sample_pass_ratio=0.0,
        monte_carlo_pass_ratio=0.0,
        stress_failure_count=0,
        parameter_robustness_pass=True,
        parameter_neighbor_degradation=0.0,
    )


def _minimal_gate() -> EconomicValidityGateEvaluationV1:
    return EconomicValidityGateEvaluationV1(
        gates_pass=False,
        reason_codes=("METRIC_MISSING_trade_count",),
        policy_threshold_status="BLOCKED",
        evaluation_status=EconomicValidityEvaluationStatus.BLOCKED,
    )


def _materialize_with_envelope(envelope: dict) -> dict:
    return materialize_economic_viability_evidence(
        ratification={"ratification_digest": "abc123"},
        versioned_binding=envelope,
        materialization_root=Path("/tmp/materialization"),
        panel_data_digest=envelope.get("data_digest", "0" * 64),
        backtest=_minimal_backtest(),
        robustness=_minimal_robustness(),
        robustness_metrics=_minimal_robustness_metrics(),
        gate_evaluation=_minimal_gate(),
        economic_classification=EconomicClassification.INCONCLUSIVE,
        ops_config={"config_digest": envelope.get("config_digest", "0" * 64)},
    )


@pytest.fixture(name="level_rank_binding")
def fixture_level_rank_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="legacy_binding")
def fixture_legacy_binding() -> dict:
    envelope = copy.deepcopy(materialize_versioned_research_binding_v0())
    envelope.pop("pit_universe_binding", None)
    return envelope


def test_level_rank_binding_digest_unchanged(level_rank_binding: dict) -> None:
    assert level_rank_binding["binding_digest"] == EXPECTED_BINDING_DIGEST


def test_level_rank_production_materializer_path_without_monkeypatch(
    level_rank_binding: dict,
) -> None:
    evidence = _materialize_with_envelope(level_rank_binding)
    assert evidence["schema_version"].startswith(
        "economic_viability_evidence_cross_sectional_open_interest_level_rank_v0"
    )
    assert "manifest_digest" in evidence
    assert evidence["binding_references"]["pit_universe_binding"] is not None


def test_level_rank_pit_universe_and_fee_binding_pass(level_rank_binding: dict) -> None:
    evidence = _materialize_with_envelope(level_rank_binding)
    refs = evidence["binding_references"]
    assert "pit_universe_binding" in refs
    assert refs["pit_universe_binding"] == level_rank_binding["pit_universe_binding"]
    assert refs["instrument_binding"] == level_rank_binding["pit_universe_binding"]
    assert refs["fee_binding"] == level_rank_binding["cost_execution_binding"]["fee_binding"]
    assert refs["fee_model_binding"] == level_rank_binding["cost_execution_binding"]["fee_binding"]
    assert evidence["authority_effect"] == "NONE"
    assert evidence["runtime_effect"] == "NONE"


def test_legacy_instrument_and_fee_model_binding_pass(legacy_binding: dict) -> None:
    evidence = _materialize_with_envelope(legacy_binding)
    refs = evidence["binding_references"]
    assert refs["instrument_binding"] == legacy_binding["instrument_binding"]
    assert (
        refs["fee_model_binding"] == legacy_binding["cost_execution_binding"]["fee_model_binding"]
    )
    assert "pit_universe_binding" not in refs
    assert "fee_binding" not in refs


def test_missing_instrument_and_universe_binding_fail_closed(level_rank_binding: dict) -> None:
    envelope = copy.deepcopy(level_rank_binding)
    envelope.pop("pit_universe_binding", None)
    with pytest.raises(EconomicViabilityEvidenceBindingResolutionError) as exc_info:
        resolve_economic_viability_binding_references_v0(envelope)
    assert exc_info.value.reason_code == REASON_INSTRUMENT_BINDING_MISSING


def test_missing_fee_binding_fail_closed(level_rank_binding: dict) -> None:
    envelope = copy.deepcopy(level_rank_binding)
    cost = dict(envelope["cost_execution_binding"])
    cost.pop("fee_binding", None)
    envelope["cost_execution_binding"] = cost
    with pytest.raises(EconomicViabilityEvidenceBindingResolutionError) as exc_info:
        resolve_economic_viability_binding_references_v0(envelope)
    assert exc_info.value.reason_code == REASON_FEE_BINDING_MISSING


def test_conflicting_instrument_bindings_fail_closed(level_rank_binding: dict) -> None:
    envelope = copy.deepcopy(level_rank_binding)
    envelope["instrument_binding"] = {"binding_version": "legacy-conflict"}
    with pytest.raises(EconomicViabilityEvidenceBindingResolutionError) as exc_info:
        resolve_economic_viability_binding_references_v0(envelope)
    assert exc_info.value.reason_code == REASON_CONFLICTING_INSTRUMENT_BINDINGS


def test_conflicting_fee_bindings_fail_closed(level_rank_binding: dict) -> None:
    envelope = copy.deepcopy(level_rank_binding)
    cost = dict(envelope["cost_execution_binding"])
    cost["fee_model_binding"] = {"fee_model_version": "conflict", "fee_bps_per_side": 99}
    envelope["cost_execution_binding"] = cost
    with pytest.raises(EconomicViabilityEvidenceBindingResolutionError) as exc_info:
        resolve_economic_viability_binding_references_v0(envelope)
    assert exc_info.value.reason_code == REASON_CONFLICTING_FEE_BINDINGS


def test_deterministic_repeated_materialization(level_rank_binding: dict) -> None:
    first = _materialize_with_envelope(level_rank_binding)
    second = _materialize_with_envelope(level_rank_binding)
    assert first["manifest_digest"] == second["manifest_digest"]


def test_materializer_to_binder_roundtrip_pass(level_rank_binding: dict) -> None:
    resolved = resolve_economic_viability_binding_references_v0(level_rank_binding)
    evidence = _materialize_with_envelope(level_rank_binding)
    refs = evidence["binding_references"]
    assert refs["instrument_binding"] == resolved["instrument_binding"]
    assert refs["fee_model_binding"] == resolved["fee_model_binding"]
    assert refs["pit_universe_binding"] == resolved["pit_universe_binding"]

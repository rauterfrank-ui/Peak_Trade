"""Phase 9 Canonical Portfolio Learning v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_portfolio_learning_v1 import (
    AUTONOMOUS_ALLOCATION_APPLY,
    CanonicalPortfolioLearningRequestV1,
    DISPOSITION_ELIGIBLE,
    DISPOSITION_INELIGIBLE,
    DISPOSITION_REJECTED_COMPARABILITY,
    PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG,
    PORTFOLIO_LEARNING_CAN_PROMOTE,
    PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY,
    PORTFOLIO_LEARNING_PRESENT,
    PROMOTION_AUTHORITY,
    PairwiseObservationV1,
    PortfolioLearningValidationError,
    PortfolioMemberV1,
    PortfolioPolicyV1,
    STATUS_ELIGIBLE,
    STATUS_INELIGIBLE,
    STATUS_OBSERVED,
    STRATEGY_AND_PORTFOLIO_OPTIMIZATION_SEPARATED,
    StrategyLayerObservationV1,
    build_canonical_portfolio_learning_v1,
    canonical_record_payload_v1,
    validate_canonical_portfolio_learning_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    METRIC_DEFINITION_VERSION,
    SCHEMA_VERSION as ROBUSTNESS_SUITE_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_portfolio_learning_v1.py"
_GIT_SHA = "41e79ec6cab6584f597fdfac1ab4d7e8ac9be42c"
_CREATED_AT = "2026-08-18T12:00:00Z"
_TIME_HORIZON = {"end": "2024-12-31T00:00:00Z", "start": "2020-01-01T00:00:00Z"}
_MARKET_UNIVERSE = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _identity(**overrides: Any) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "git_sha": _GIT_SHA,
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": "ma_crossover.v1",
        "strategy_params": {"slow": 50, "fast": 10},
        "dataset_digest": _digest("dataset"),
        "feature_pipeline_digest": _digest("features"),
        "fee_model_digest": _digest("fee"),
        "slippage_model_digest": _digest("slippage"),
        "funding_model_digest": _digest("funding"),
        "risk_policy_digest": _digest("risk"),
        "portfolio_digest": _digest("portfolio"),
        "split_policy_digest": _digest("split"),
        "market_context_contract_digest": _digest("market-context"),
        "bull_bear_logic_digest": _digest("bull-bear"),
        "state_switch_logic_digest": _digest("state-switch"),
        "survival_logic_digest": _digest("survival"),
        "suitability_logic_digest": _digest("suitability"),
        "double_play_logic_digest": _digest("double-play"),
        "entry_position_exit_logic_digest": _digest("entry-position-exit"),
        "seed": 7,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return build_canonical_experiment_identity_v1(CanonicalExperimentIdentityRequestV1(**payload))


def _candidate(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> ComparisonCandidateV1:
    payload: dict[str, Any] = {
        "experiment_identity": identity or _identity(),
        "robustness_suite_version": ROBUSTNESS_SUITE_VERSION,
        "metric_definitions": METRIC_DEFINITION_VERSION,
        "time_horizon": dict(_TIME_HORIZON),
        "market_universe": list(_MARKET_UNIVERSE),
        "experiment_id": None,
        "evidence_refs": (),
    }
    payload.update(overrides)
    return ComparisonCandidateV1(**payload)


def _experiment_id(identity: Mapping[str, Any] | None = None, **overrides: Any) -> str:
    record = identity or _identity(**overrides)
    return derive_experiment_id_v1(str(record["identity_digest"]))


def _strategy_layer(**overrides: Any) -> StrategyLayerObservationV1:
    payload = {
        "signal_quality": 0.9,
        "execution_robustness": 0.85,
        "parameter_stability": 0.8,
        "regime_suitability": 0.75,
    }
    payload.update(overrides)
    return StrategyLayerObservationV1(**payload)


def _policy(**overrides: Any) -> PortfolioPolicyV1:
    payload = {
        "max_pairwise_abs_correlation": 0.6,
        "max_concentration": 0.6,
        "min_diversification": 0.2,
        "max_abs_portfolio_drawdown": 0.2,
        "max_turnover": 1.0,
        "min_capacity": 1000.0,
        "min_allocation_stability": 0.5,
        "max_risk_contribution": 0.7,
    }
    payload.update(overrides)
    return PortfolioPolicyV1(**payload)


def _member(
    identity: Mapping[str, Any] | None = None,
    *,
    weight: float = 0.5,
    **overrides: Any,
) -> PortfolioMemberV1:
    payload = {
        "candidate": _candidate(identity),
        "weight": weight,
        "strategy_layer": _strategy_layer(),
        "marginal_risk": 0.04,
        "risk_contribution": 0.5,
        "fee_drag": 0.001,
        "slippage": 0.0005,
    }
    payload.update(overrides)
    return PortfolioMemberV1(**payload)


def _pair(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    correlation: float = 0.2,
    covariance: float = 0.0004,
) -> PairwiseObservationV1:
    return PairwiseObservationV1(
        left_experiment_id=_experiment_id(left),
        right_experiment_id=_experiment_id(right),
        correlation=correlation,
        covariance=covariance,
    )


def _request(**overrides: Any) -> CanonicalPortfolioLearningRequestV1:
    left = _identity()
    right = _identity(seed=11, strategy_identity="rsi_reversion.v1")
    left_id = _experiment_id(left)
    right_id = _experiment_id(right)
    payload: dict[str, Any] = {
        "members": (_member(left, weight=0.5), _member(right, weight=0.5)),
        "pairwise": (_pair(left, right),),
        "diversification": 0.4,
        "concentration": 0.5,
        "portfolio_drawdown": -0.08,
        "turnover": 0.3,
        "capacity": 5000.0,
        "allocation_stability": 0.8,
        "policy": _policy(),
        "evidence_refs": [
            {"kind": "EXPERIMENT_RECORD", "ref": left_id, "digest": _digest("left-record")},
            {"kind": "EXPERIMENT_RECORD", "ref": right_id, "digest": _digest("right-record")},
        ],
        "created_at": _CREATED_AT,
        "metric_definitions": METRIC_DEFINITION_VERSION,
        "robustness_suite_version": ROBUSTNESS_SUITE_VERSION,
    }
    payload.update(overrides)
    return CanonicalPortfolioLearningRequestV1(**payload)


def test_comparable_portfolio_is_eligible_and_layers_are_separated() -> None:
    record = build_canonical_portfolio_learning_v1(_request())
    assert record["completeness"] == "COMPLETE"
    assert record["overall_disposition"] == DISPOSITION_ELIGIBLE
    assert record["portfolio_learning_present"] is True
    assert record["strategy_and_portfolio_optimization_separated"] is True
    assert record["applied_allocation"] is False
    assert record["autonomous_allocation_apply"] is False
    for item in record["member_results"]:
        assert item["strategy_layer_status"] == STATUS_OBSERVED
        assert item["portfolio_component_status"] == STATUS_ELIGIBLE
        assert item["strategy_layer_status"] != item["portfolio_component_status"]
        assert "signal_quality" in item["strategy_layer"]
    validate_canonical_portfolio_learning_v1(record)


def test_identical_inputs_and_member_order_are_deterministic() -> None:
    left = _identity()
    right = _identity(seed=11, strategy_identity="rsi_reversion.v1")
    first = canonical_record_payload_v1(build_canonical_portfolio_learning_v1(_request()))
    reversed_members = _request(
        members=(_member(right, weight=0.5), _member(left, weight=0.5)),
        pairwise=(_pair(right, left),),
    )
    second = canonical_record_payload_v1(build_canonical_portfolio_learning_v1(reversed_members))
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)
    assert first["evaluation_identity"] == second["evaluation_identity"]


def test_strong_single_strategy_is_not_automatic_portfolio_component() -> None:
    left = _identity()
    right = _identity(seed=11, strategy_identity="rsi_reversion.v1")
    strong = _strategy_layer(
        signal_quality=0.99,
        execution_robustness=0.99,
        parameter_stability=0.99,
        regime_suitability=0.99,
    )
    record = build_canonical_portfolio_learning_v1(
        _request(
            members=(
                _member(left, weight=0.5, strategy_layer=strong),
                _member(right, weight=0.5, strategy_layer=strong),
            ),
            pairwise=(_pair(left, right, correlation=0.95, covariance=0.02),),
        )
    )
    assert record["overall_disposition"] == DISPOSITION_INELIGIBLE
    assert "max_pairwise_abs_correlation" in record["gate_failures"]
    for item in record["member_results"]:
        assert item["strategy_layer"]["signal_quality"] == 0.99
        assert item["strategy_layer_status"] == STATUS_OBSERVED
        assert item["portfolio_component_status"] == STATUS_INELIGIBLE


def test_concentration_and_risk_contribution_are_evaluated() -> None:
    left = _identity()
    right = _identity(seed=11, strategy_identity="rsi_reversion.v1")
    record = build_canonical_portfolio_learning_v1(
        _request(
            members=(
                _member(left, weight=0.8, risk_contribution=0.8),
                _member(right, weight=0.2, risk_contribution=0.2),
            ),
            concentration=0.8,
        )
    )
    assert record["overall_disposition"] == DISPOSITION_INELIGIBLE
    assert "max_concentration" in record["gate_failures"]
    assert "max_risk_contribution" in record["gate_failures"]
    assert record["portfolio_metrics"]["concentration"] == 0.8
    assert record["portfolio_metrics"]["diversification"] == 0.4


def test_missing_correlation_and_fee_drag_fail_closed() -> None:
    with pytest.raises(PortfolioLearningValidationError, match="pairwise correlation"):
        build_canonical_portfolio_learning_v1(_request(pairwise=()))
    with pytest.raises(PortfolioLearningValidationError, match="silent zero defaults"):
        left = _identity()
        right = _identity(seed=11, strategy_identity="rsi_reversion.v1")
        build_canonical_portfolio_learning_v1(
            _request(
                members=(
                    _member(left, weight=0.5, fee_drag=None),
                    _member(right, weight=0.5),
                )
            )
        )


def test_incomparable_members_are_rejected_not_ranked() -> None:
    left = _identity()
    right = _identity(
        seed=11, strategy_identity="rsi_reversion.v1", fee_model_digest=_digest("other-fee")
    )
    record = build_canonical_portfolio_learning_v1(
        _request(
            members=(_member(left, weight=0.5), _member(right, weight=0.5)),
            pairwise=(_pair(left, right),),
            evidence_refs=[
                {
                    "kind": "EXPERIMENT_RECORD",
                    "ref": _experiment_id(left),
                    "digest": _digest("left-record"),
                },
                {
                    "kind": "EXPERIMENT_RECORD",
                    "ref": _experiment_id(right),
                    "digest": _digest("right-record"),
                },
            ],
        )
    )
    assert record["overall_disposition"] == DISPOSITION_REJECTED_COMPARABILITY
    assert record["overall_status"] == "EVALUATION_REJECTED"
    assert record["member_results"][0]["portfolio_component_status"] == (
        DISPOSITION_REJECTED_COMPARABILITY
    )


def test_single_member_portfolio_fails_closed() -> None:
    left = _identity()
    with pytest.raises(PortfolioLearningValidationError, match="at least two portfolio members"):
        build_canonical_portfolio_learning_v1(
            _request(
                members=(_member(left, weight=1.0),),
                pairwise=(),
                concentration=1.0,
                evidence_refs=[
                    {
                        "kind": "EXPERIMENT_RECORD",
                        "ref": _experiment_id(left),
                        "digest": _digest("left-record"),
                    }
                ],
            )
        )


def test_reuses_phase_4_tokens_and_phase_5_comparability() -> None:
    record = build_canonical_portfolio_learning_v1(_request())
    assert record["metric_definitions"] == METRIC_DEFINITION_VERSION
    assert record["robustness_suite_version"] == ROBUSTNESS_SUITE_VERSION
    assert record["comparison_ssot_version"] == "canonical_comparison_ssot_v1"
    with pytest.raises(PortfolioLearningValidationError, match="Phase 4 token"):
        build_canonical_portfolio_learning_v1(_request(metric_definitions="other_metrics_v1"))


def test_no_runtime_live_config_promotion_or_phase_10_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "src.core.peak_config",
        "src.governance.promotion_loop",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.live",
        "src.live.live_gates",
        "src.risk",
        "src.risk.component_var",
        "src.trading",
        "src.experiments.canonical_robustness_suite_v1",
        "src.experiments.canonical_champion_challenger_v1",
        "src.experiments.canonical_reality_gap_store_v1",
        "src.experiments.canonical_regime_aware_evaluation_v1",
        "src.experiments.portfolio_robustness",
        "src.experiments.portfolio_presets",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
    }
    assert forbidden_imports.isdisjoint(imported)
    for token in (
        "config/live_overrides",
        "config/auto/",
        "load_config_with_live_overrides",
        "submit_order(",
        "apply_proposals_to_live_overrides",
        "write_live_config(",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "FUNDING_AUTHORIZED",
        "promote_to_live(",
        "create_confirm_token(",
        "use_confirm_token(",
        "Phase 10",
        "Automated Offline Research",
    ):
        assert token not in source
    record = build_canonical_portfolio_learning_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["overall_disposition"] = DISPOSITION_ELIGIBLE  # type: ignore[index]
    assert PORTFOLIO_LEARNING_PRESENT is True
    assert STRATEGY_AND_PORTFOLIO_OPTIMIZATION_SEPARATED is True
    assert PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY is False
    assert PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG is False
    assert PORTFOLIO_LEARNING_CAN_PROMOTE is False
    assert AUTONOMOUS_ALLOCATION_APPLY is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert record["portfolio_learning_can_submit_order"] is False
    assert record["portfolio_learning_can_fund"] is False
    assert record["portfolio_learning_can_increase_risk"] is False
    assert record["portfolio_learning_can_increase_leverage"] is False
    assert record["portfolio_learning_can_authorize_canary"] is False
    assert record["portfolio_learning_can_promote_to_live"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_portfolio_learning_v1
    )

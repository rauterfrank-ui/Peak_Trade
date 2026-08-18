"""Phase 11 Canonical Meta-Learning v1 contract tests."""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    build_canonical_failure_memory_record_v1,
    canonical_record_payload as failure_record_payload,
)
from src.experiments.canonical_meta_learning_v1 import (
    AUTONOMOUS_PROMOTION,
    CANONICAL_QUESTIONS,
    CanonicalMetaLearningRequestV1,
    CLAIM_STRENGTH_NONE,
    CLAIM_STRENGTH_WEAK,
    CLAIM_TYPE_ASSOCIATION,
    CLAIM_TYPE_NONE,
    CORRELATION_IS_NOT_CAUSALITY,
    EVIDENCE_INSUFFICIENT_EVIDENCE,
    EVIDENCE_INSUFFICIENT_SAMPLE,
    EVIDENCE_REJECTED_COMPARABILITY,
    HISTORICAL_RECORD_MUTATION,
    META_LEARNING_AUTHORITY,
    META_LEARNING_CAN_MUTATE_LIVE_CONFIG,
    META_LEARNING_CAN_PROMOTE,
    META_LEARNING_HAS_RUNTIME_AUTHORITY,
    META_LEARNING_PRESENT,
    MetaLearningExperimentUnitV1,
    MetaLearningLaterOutcomeV1,
    MetaLearningPolicyV1,
    MetaLearningValidationError,
    PHASE_12_STARTED,
    PROMOTION_AUTHORITY,
    QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION,
    QUESTION_COST_MODEL_REALITY_UNDERESTIMATION,
    QUESTION_PARAMETER_REGION_REPEATED_OVERFIT,
    QUESTION_REGIME_RECURRING_FAILURE_MODES,
    QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION,
    QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL,
    build_canonical_meta_learning_v1,
    canonical_meta_learning_policy_v1,
    canonical_record_payload_v1,
    validate_canonical_meta_learning_v1,
)
from src.experiments.canonical_reality_gap_store_v1 import (
    CanonicalRealityGapRecordRequestV1,
    OBSERVED_SURFACE_SHADOW,
    RealityGapDimensionV1,
    build_canonical_reality_gap_record_v1,
    canonical_record_payload as reality_gap_record_payload,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_meta_learning_v1.py"
_GIT_SHA = "7c36858bb6b9ed036bba901170d370b61a805110"
_CREATED_AT = "2026-08-18T14:00:00Z"
_EVIDENCE_AT = "2026-08-18T12:00:00Z"
_LATER_AT = "2026-08-18T13:00:00Z"
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
        "seed": 11,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return build_canonical_experiment_identity_v1(CanonicalExperimentIdentityRequestV1(**payload))


def _policy(**overrides: Any) -> MetaLearningPolicyV1:
    payload: dict[str, Any] = {
        "evaluation_policy_version": "canonical_meta_learning_policy_v1",
        "min_sample_size_descriptive": 2,
        "min_sample_size_associative": 2,
        "min_recurrence_count": 2,
        "min_parameter_stability": 0.5,
    }
    payload.update(overrides)
    return MetaLearningPolicyV1(**payload)


def _unit(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> MetaLearningExperimentUnitV1:
    payload: dict[str, Any] = {
        "experiment_identity": identity or _identity(),
        "evidence_created_at": _EVIDENCE_AT,
        "strategy_family": "ma_crossover",
        "hypothesis_id": "hyp.ma-crossover.v1",
        "hypothesis_kind": "trend_following",
        "search_space_id": "search.ma.v1",
        "parameter_region": {"fast": 10, "slow": 50},
        "regime": "high_vol",
        "time_horizon": dict(_TIME_HORIZON),
        "market_universe": list(_MARKET_UNIVERSE),
        "robustness_test_statuses": {
            "TRAIN_VALIDATION_HOLDOUT": "PASS",
            "WALK_FORWARD": "PASS",
            "ROLLING_OOS": "PASS",
        },
        "backtest_metrics": {"sharpe": 1.2},
        "research_path_id": "path.offline.v1",
        "parameter_stability": 0.9,
        "later_outcome": MetaLearningLaterOutcomeV1(
            observed_surface=OBSERVED_SURFACE_SHADOW,
            metric_name="sharpe",
            value=0.8,
            observed_at=_LATER_AT,
        ),
    }
    payload.update(overrides)
    return MetaLearningExperimentUnitV1(**payload)


def _failure(
    identity: Mapping[str, Any],
    *,
    failure_class: str = "REJECTED_OVERFIT",
    regime: str = "high_vol",
    created_at: str = _EVIDENCE_AT,
) -> Mapping[str, Any]:
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    gate = {
        "REJECTED_OVERFIT": "OVERFIT_GATE",
        "REJECTED_COST_SENSITIVITY": "COST_SENSITIVITY_GATE",
        "REJECTED_REGIME_CONCENTRATION": "REGIME_CONCENTRATION_GATE",
        "REJECTED_REALITY_GAP": "REALITY_GAP_GATE",
    }[failure_class]
    return build_canonical_failure_memory_record_v1(
        CanonicalFailureMemoryRecordRequestV1(
            experiment_identity=identity,
            hypothesis_id="hyp.ma-crossover.v1",
            failure_class=failure_class,
            failed_gate=gate,
            rejection_reason=failure_class,
            regime=regime,
            parameter_region={"fast": 10, "slow": 50},
            cost_sensitivity={"fee_stress": 0.25},
            instability_indicators={"fold_sign_flips": 3},
            evidence_refs=[
                {
                    "kind": "EXPERIMENT_RECORD",
                    "ref": experiment_id,
                    "digest": _digest(f"experiment-record-{experiment_id}"),
                }
            ],
            created_at=created_at,
            robustness_policy_digest=_digest("robustness-policy"),
        )
    )


def _gap(
    identity: Mapping[str, Any],
    *,
    expected: float = 0.001,
    observed: float = 0.02,
    threshold: float = 0.001,
    created_at: str = _LATER_AT,
) -> Mapping[str, Any]:
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    return build_canonical_reality_gap_record_v1(
        CanonicalRealityGapRecordRequestV1(
            experiment_identity=identity,
            observed_surface=OBSERVED_SURFACE_SHADOW,
            metric_definitions="canonical_robustness_metrics_v1",
            threshold_policy_digest=_digest("threshold-policy"),
            gap_dimensions=(
                RealityGapDimensionV1(
                    name="fee",
                    expected=expected,
                    observed=observed,
                    threshold=threshold,
                    unit="ratio",
                ),
            ),
            evidence_refs=[
                {
                    "kind": "EXPERIMENT_RECORD",
                    "ref": experiment_id,
                    "digest": _digest(f"gap-record-{experiment_id}"),
                }
            ],
            created_at=created_at,
        )
    )


def _request(
    identities: Sequence[Mapping[str, Any]] | None = None,
    **overrides: Any,
) -> CanonicalMetaLearningRequestV1:
    if identities is None:
        identities = (_identity(seed=11), _identity(seed=12))
    units = tuple(_unit(identity) for identity in identities)
    payload: dict[str, Any] = {
        "units": units,
        "created_at": _CREATED_AT,
        "policy": _policy(),
        "failure_records": tuple(_failure(identity) for identity in identities),
        "reality_gap_records": tuple(_gap(identity) for identity in identities),
    }
    payload.update(overrides)
    return CanonicalMetaLearningRequestV1(**payload)


def _question(record: Mapping[str, Any], question_id: str) -> Mapping[str, Any]:
    return next(item for item in record["questions"] if item["question_id"] == question_id)


def test_same_inputs_yield_identical_lineage_bound_result() -> None:
    first = build_canonical_meta_learning_v1(_request())
    second = build_canonical_meta_learning_v1(_request())
    validate_canonical_meta_learning_v1(first)
    assert first["meta_learning_identity"] == second["meta_learning_identity"]
    assert canonical_record_payload_v1(first) == canonical_record_payload_v1(second)
    assert deterministic_json_dumps(canonical_record_payload_v1(first)) == deterministic_json_dumps(
        canonical_record_payload_v1(second)
    )
    lineage = first["input_lineage"]
    assert lineage["contract_versions"]["meta_learning"] == "canonical_meta_learning_v1"
    assert lineage["contract_versions"]["comparison_ssot"] == "canonical_comparison_ssot_v1"
    assert lineage["contract_versions"]["metric_definitions"] == "canonical_robustness_metrics_v1"
    assert lineage["contract_versions"]["robustness_suite"] == "canonical_robustness_suite_v1"
    assert lineage["experiment_ids"] == sorted(lineage["experiment_ids"])
    assert first["ranked_experiment_ids"] == []
    assert first["champion_experiment_id"] is None
    assert [item["question_id"] for item in first["questions"]] == list(CANONICAL_QUESTIONS)


def test_version_drift_and_empty_inputs_fail_closed() -> None:
    with pytest.raises(MetaLearningValidationError, match="units must not be empty"):
        build_canonical_meta_learning_v1(_request(units=()))
    with pytest.raises(MetaLearningValidationError, match="Phase 4 token"):
        build_canonical_meta_learning_v1(_request(metric_definitions="other_metrics_v1"))
    with pytest.raises(MetaLearningValidationError, match="Phase 4 token"):
        build_canonical_meta_learning_v1(
            _request(units=(_unit(_identity(), metric_definitions="other_metrics_v1"),))
        )


def test_missing_evidence_is_insufficient_not_zero_default() -> None:
    identities = (_identity(seed=21), _identity(seed=22))
    units = tuple(
        _unit(
            identity,
            robustness_test_statuses={"TRAIN_VALIDATION_HOLDOUT": "PASS"},
            backtest_metrics={"sharpe": 1.1},
            later_outcome=None,
            parameter_stability=None,
            research_path_id=None,
        )
        for identity in identities
    )
    record = build_canonical_meta_learning_v1(
        _request(identities=identities, units=units, failure_records=(), reality_gap_records=())
    )
    oos = _question(record, QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL)
    assert oos["evidence_status"] == EVIDENCE_INSUFFICIENT_EVIDENCE
    assert oos["missing_evidence_count"] == 2
    assert oos["claim_type"] == CLAIM_TYPE_NONE
    cost = _question(record, QUESTION_COST_MODEL_REALITY_UNDERESTIMATION)
    assert cost["evidence_status"] == EVIDENCE_INSUFFICIENT_EVIDENCE
    metric = _question(record, QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION)
    assert metric["evidence_status"] == EVIDENCE_INSUFFICIENT_EVIDENCE
    assert "0.0" not in str(cost["findings"])


def test_incomparable_evidence_is_not_jointly_aggregated() -> None:
    left = _identity(seed=31)
    right = _identity(seed=32, dataset_digest=_digest("dataset-b"))
    record = build_canonical_meta_learning_v1(_request(identities=(left, right)))
    assert len(record["comparable_cohorts"]) == 2
    assert record["ranked_experiment_ids"] == []
    left_id = derive_experiment_id_v1(str(left["identity_digest"]))
    right_id = derive_experiment_id_v1(str(right["identity_digest"]))
    for question in record["questions"]:
        for finding in question["findings"]:
            ids = set(finding["experiment_ids"])
            assert not {left_id, right_id}.issubset(ids)
        if question["findings"]:
            assert question["rejected_comparability_count"] == 2
    oos = _question(record, QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL)
    assert oos["evidence_status"] in {
        EVIDENCE_INSUFFICIENT_SAMPLE,
        EVIDENCE_INSUFFICIENT_EVIDENCE,
        EVIDENCE_REJECTED_COMPARABILITY,
    }
    assert oos["claim_strength"] != "STRONG"


def test_small_sample_does_not_emit_strong_or_associative_claims() -> None:
    identities = (_identity(seed=41),)
    record = build_canonical_meta_learning_v1(
        _request(
            identities=identities,
            units=(_unit(identities[0]),),
            failure_records=(_failure(identities[0]),),
            reality_gap_records=(_gap(identities[0]),),
            policy=canonical_meta_learning_policy_v1(),
        )
    )
    for question in record["questions"]:
        assert question["claim_strength"] in {CLAIM_STRENGTH_NONE, CLAIM_STRENGTH_WEAK}
        assert question["claim_strength"] != "STRONG"
        assert question["claim_type"] != "CAUSAL"
        assert question["causal_claim"] is False
        if question["question_id"] in {
            QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION,
            QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION,
        }:
            assert question["evidence_status"] == EVIDENCE_INSUFFICIENT_SAMPLE
            assert question["claim_type"] == CLAIM_TYPE_NONE
            assert question["research_proposals"] == []


def test_association_is_not_upgraded_to_causality() -> None:
    identities = (_identity(seed=51), _identity(seed=52))
    units = tuple(
        _unit(
            identity,
            robustness_test_statuses={
                "TRAIN_VALIDATION_HOLDOUT": "PASS",
                "WALK_FORWARD": "FAIL",
                "ROLLING_OOS": "FAIL",
            },
        )
        for identity in identities
    )
    record = build_canonical_meta_learning_v1(
        _request(
            identities=identities,
            units=units,
            reality_gap_records=tuple(_gap(i) for i in identities),
        )
    )
    association = _question(record, QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION)
    assert association["evidence_status"] == "COMPUTED"
    assert association["claim_type"] == CLAIM_TYPE_ASSOCIATION
    assert association["claim_strength"] == CLAIM_STRENGTH_WEAK
    assert association["causal_claim"] is False
    assert association["correlation_is_not_causality"] is True
    assert CORRELATION_IS_NOT_CAUSALITY is True
    for finding in association["findings"]:
        assert finding["causal_claim"] is False
        assert finding["claim_type"] == CLAIM_TYPE_ASSOCIATION
        assert finding.get("causal") is None
    assert all(proposal["kind"] != "PROMOTE" for proposal in record["research_proposals"])


def test_recurring_failure_modes_are_aggregated() -> None:
    identities = (_identity(seed=61), _identity(seed=62))
    failures = tuple(
        _failure(identity, failure_class="REJECTED_REGIME_CONCENTRATION", regime="high_vol")
        for identity in identities
    )
    record = build_canonical_meta_learning_v1(
        _request(identities=identities, failure_records=failures)
    )
    question = _question(record, QUESTION_REGIME_RECURRING_FAILURE_MODES)
    assert question["evidence_status"] == "COMPUTED"
    assert question["findings"]
    finding = question["findings"][0]
    assert finding["regime"] == "high_vol"
    assert finding["failure_class"] == "REJECTED_REGIME_CONCENTRATION"
    assert finding["occurrence_count"] == 2
    assert finding["recurring"] is True
    overfit = _question(record, QUESTION_PARAMETER_REGION_REPEATED_OVERFIT)
    assert overfit["findings"] == [] or overfit["evidence_status"] == EVIDENCE_INSUFFICIENT_EVIDENCE


def test_cost_model_reality_gap_underestimation_is_detected() -> None:
    identities = (_identity(seed=71), _identity(seed=72))
    gaps = tuple(
        _gap(identity, expected=0.001, observed=0.04, threshold=0.002) for identity in identities
    )
    record = build_canonical_meta_learning_v1(
        _request(identities=identities, reality_gap_records=gaps)
    )
    question = _question(record, QUESTION_COST_MODEL_REALITY_UNDERESTIMATION)
    assert question["evidence_status"] == "COMPUTED"
    assert question["findings"]
    finding = question["findings"][0]
    assert finding["dimension"] == "fee"
    assert finding["underestimation_count"] == 2
    assert finding["cost_model_digest"] == identities[0]["fee_model_digest"]
    kinds = {item["kind"] for item in record["research_proposals"]}
    assert "INVESTIGATE" in kinds
    assert "PROMOTE" not in kinds


def test_research_output_remains_research_only() -> None:
    record = build_canonical_meta_learning_v1(_request())
    assert record["meta_learning_authority"] == "RESEARCH_ONLY"
    assert record["promotion_authority"] == "NONE"
    assert record["autonomous_promotion"] is False
    assert record["autonomous_champion_swap"] is False
    assert record["ranked_experiment_ids"] == []
    assert record["champion_experiment_id"] is None
    for proposal in record["research_proposals"]:
        assert proposal["authority"] == "RESEARCH_ONLY"
        assert proposal["promotion_authority"] == "NONE"
        assert proposal["applies_to_champion"] is False
        assert proposal["kind"] in {
            "PRIORITIZE_RESEARCH",
            "DEPRIORITIZE_RESEARCH",
            "INVESTIGATE",
            "RETEST_WITH_EXPLICIT_REASON",
        }


def test_historical_records_are_not_mutated() -> None:
    identities = (_identity(seed=81), _identity(seed=82))
    failure = failure_record_payload(_failure(identities[0]))
    gap = reality_gap_record_payload(_gap(identities[0]))
    failure_copy = copy.deepcopy(failure)
    gap_copy = copy.deepcopy(gap)
    build_canonical_meta_learning_v1(
        _request(
            identities=identities,
            failure_records=(failure, _failure(identities[1])),
            reality_gap_records=(gap, _gap(identities[1])),
        )
    )
    assert failure == failure_copy
    assert gap == gap_copy
    assert HISTORICAL_RECORD_MUTATION is False


def test_lookahead_later_outcome_fails_closed() -> None:
    with pytest.raises(MetaLearningValidationError, match="lookahead"):
        build_canonical_meta_learning_v1(
            _request(
                units=(
                    _unit(
                        _identity(seed=11),
                        later_outcome=MetaLearningLaterOutcomeV1(
                            observed_surface=OBSERVED_SURFACE_SHADOW,
                            metric_name="sharpe",
                            value=0.8,
                            observed_at="2026-08-18T11:00:00Z",
                        ),
                    ),
                    _unit(_identity(seed=12)),
                )
            )
        )


def test_unbound_failure_record_fails_closed() -> None:
    identities = (_identity(seed=91), _identity(seed=92))
    foreign = _identity(seed=93, dataset_digest=_digest("foreign"))
    with pytest.raises(MetaLearningValidationError, match="not in the input experiment set"):
        build_canonical_meta_learning_v1(
            _request(identities=identities, failure_records=(_failure(foreign),))
        )


def test_no_runtime_live_config_promotion_or_trading_core_paths() -> None:
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
        "src.trading",
        "src.trading.master_v2",
        "src.experiments.canonical_champion_challenger_v1",
        "src.experiments.canonical_portfolio_learning_v1",
        "src.experiments.canonical_regime_aware_evaluation_v1",
        "src.experiments.canonical_automated_offline_research_loop_v1",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
        "src.meta.learning_loop.canary_micro_live_readiness_v1",
        "src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1",
    }
    assert forbidden_imports.isdisjoint(imported)
    for token in (
        "config/live_overrides",
        "config/auto/",
        "load_config_with_live_overrides",
        "submit_order(",
        "apply_proposals_to_live_overrides",
        "write_live_config(",
        "LIVE_AUTHORIZED=true",
        "TESTNET_AUTHORIZED=true",
        "FUNDING_AUTHORIZED",
        "promote_to_live(",
        "create_confirm_token(",
        "use_confirm_token(",
        "BEST_SHARPE",
        "rank_comparable_candidates_v1",
        "CLAIM_STRENGTH_STRONG",
    ):
        assert token not in source
    record = build_canonical_meta_learning_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["overall_status"] = "META_LEARNING_COMPLETE"  # type: ignore[index]
    assert META_LEARNING_PRESENT is True
    assert META_LEARNING_HAS_RUNTIME_AUTHORITY is False
    assert META_LEARNING_CAN_MUTATE_LIVE_CONFIG is False
    assert META_LEARNING_CAN_PROMOTE is False
    assert AUTONOMOUS_PROMOTION is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert META_LEARNING_AUTHORITY == "RESEARCH_ONLY"
    assert PHASE_12_STARTED is False
    assert record["meta_learning_can_submit_order"] is False
    assert record["meta_learning_can_fund"] is False
    assert record["meta_learning_can_increase_risk"] is False
    assert record["meta_learning_can_increase_leverage"] is False
    assert record["meta_learning_can_authorize_canary"] is False
    assert record["meta_learning_can_promote_to_live"] is False
    assert record["learning_may_autonomously_replace_core_logic"] is False
    assert record["phase_12_started"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_meta_learning_v1
    )


def test_phase_0_to_10_authority_invariants_remain_fail_closed() -> None:
    from src.experiments.canonical_automated_offline_research_loop_v1 import (
        AUTOMATED_RUNTIME_AUTHORITY,
        RESEARCH_LOOP_CAN_PROMOTE,
        RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY,
    )
    from src.experiments.canonical_champion_challenger_v1 import AUTONOMOUS_CHAMPION_SWAP
    from src.experiments.canonical_comparison_ssot_v1 import COMPARISON_SSOT_CAN_PROMOTE
    from src.experiments.canonical_experiment_identity_v1 import (
        EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY,
    )
    from src.experiments.canonical_portfolio_learning_v1 import (
        AUTONOMOUS_ALLOCATION_APPLY,
        PORTFOLIO_LEARNING_CAN_PROMOTE,
    )

    assert EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY is False
    assert COMPARISON_SSOT_CAN_PROMOTE is False
    assert AUTONOMOUS_CHAMPION_SWAP is False
    assert RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY is False
    assert RESEARCH_LOOP_CAN_PROMOTE is False
    assert AUTOMATED_RUNTIME_AUTHORITY is False
    assert AUTONOMOUS_ALLOCATION_APPLY is False
    assert PORTFOLIO_LEARNING_CAN_PROMOTE is False

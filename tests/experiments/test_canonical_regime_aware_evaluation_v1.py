"""Phase 8 Canonical Regime-Aware Evaluation v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_regime_aware_evaluation_v1 import (
    BULL_BEAR_DECISION_QUALITY_EVALUABLE,
    ATTRIBUTION_NOT_ATTRIBUTABLE,
    ATTRIBUTION_STRATEGY_EDGE,
    ATTRIBUTION_TIMING_ERROR,
    BullBearDecisionQualityV1,
    CANONICAL_CORE_LOGIC_ATTRIBUTION_PRESENT,
    CanonicalRegimeAwareEvaluationRequestV1,
    CoreLogicAttributionV1,
    FAMILY_BULL_BEAR,
    FAMILY_TREND_RANGE,
    MAPPING_MODE_EXPLICIT,
    MAPPING_MODE_SEPARATION,
    PROMOTION_AUTHORITY,
    QUALITY_CORRECT,
    QUALITY_TOO_LATE,
    REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG,
    REGIME_AWARE_EVALUATION_CAN_PROMOTE,
    REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY,
    REGIME_AWARE_EVALUATION_PRESENT,
    REGIME_LOOKAHEAD_BLOCKED,
    REGIME_MAPPING_EXPLICIT,
    REQUIRED_ATTRIBUTION_STAGES,
    REQUIRED_REGIME_FAMILIES,
    STAGE_BULL_BEAR,
    RegimeAwareEvaluationError,
    RegimeMappingContractV1,
    RegimeMappingRuleV1,
    RegimeSliceV1,
    build_canonical_regime_aware_evaluation_v1,
    canonical_record_payload,
    validate_canonical_regime_aware_evaluation_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    METRIC_DEFINITION_VERSION,
    SCHEMA_VERSION as ROBUSTNESS_SUITE_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_regime_aware_evaluation_v1.py"
_GIT_SHA = "defa59f12813b961d6edce11c7ead91c6e369950"
_CREATED_AT = "2026-08-17T22:00:00Z"
_DECISION_AT = "2026-08-17T12:00:00Z"
_LABEL_AT = "2026-08-17T11:59:59Z"
_EVALUATION_AT = "2026-08-17T22:00:00Z"
_CORE_DIGEST_FIELDS = (
    "trading_decision_core_digest",
    "market_context_contract_digest",
    "bull_bear_logic_digest",
    "state_switch_logic_digest",
    "survival_logic_digest",
    "suitability_logic_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
)
_FAMILY_LABELS = {
    "TREND_RANGE": "trend",
    "VOLATILITY": "high",
    "BULL_BEAR": "bull",
    "LIQUIDITY_STATE": "thin",
    "SPREAD_REGIME": "wide",
    "FUNDING_REGIME": "positive",
    "CRASH_STATE": "normal",
    "RISK_ON_OFF": "risk-on",
    "VOLATILITY_CLUSTERING": "clustered",
    "VENUE_MICROSTRUCTURE_STATE": "continuous",
}


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


def _slice(family: str, label: str, **overrides: Any) -> RegimeSliceV1:
    payload: dict[str, Any] = {
        "family": family,
        "label": label,
        "decision_as_of": _DECISION_AT,
        "label_as_of": _LABEL_AT,
        "return_value": 0.01,
        "sharpe": 0.8,
        "drawdown": -0.04,
        "turnover": 0.2,
        "fee_drag": 0.001,
        "slippage": 0.0005,
        "failure_rate": 0.1,
        "sample_size": 12,
    }
    payload.update(overrides)
    return RegimeSliceV1(**payload)


def _slices() -> tuple[RegimeSliceV1, ...]:
    return tuple(_slice(family, label) for family, label in _FAMILY_LABELS.items())


def _mapping(*, mode: str = MAPPING_MODE_EXPLICIT) -> RegimeMappingContractV1:
    if mode == MAPPING_MODE_SEPARATION:
        return RegimeMappingContractV1(
            mapping_mode=MAPPING_MODE_SEPARATION,
            research_regime_taxonomy="canonical_research_regime_taxonomy_v1",
            runtime_regime_taxonomy="canonical_runtime_regime_taxonomy_v1",
            documented_separation_reason="research_and_runtime_taxonomies_are_distinct",
        )
    return RegimeMappingContractV1(
        mapping_mode=MAPPING_MODE_EXPLICIT,
        research_regime_taxonomy="canonical_research_regime_taxonomy_v1",
        runtime_regime_taxonomy="canonical_runtime_regime_taxonomy_v1",
        mappings=tuple(
            RegimeMappingRuleV1(research_label=label, runtime_label=f"runtime-{label}")
            for label in _FAMILY_LABELS.values()
        ),
    )


def _attribution() -> tuple[CoreLogicAttributionV1, ...]:
    return tuple(
        CoreLogicAttributionV1(
            stage=stage,
            attribution_class=(
                ATTRIBUTION_TIMING_ERROR
                if stage == STAGE_BULL_BEAR
                else ATTRIBUTION_NOT_ATTRIBUTABLE
            ),
            sample_size=12,
            decision_as_of=_DECISION_AT,
            label_as_of=_LABEL_AT,
        )
        for stage in REQUIRED_ATTRIBUTION_STAGES
    )


def _quality() -> tuple[BullBearDecisionQualityV1, ...]:
    return (
        BullBearDecisionQualityV1(
            predicted_class="bull",
            realized_class="bull",
            quality=QUALITY_CORRECT,
            sample_size=8,
            decision_as_of=_DECISION_AT,
            label_as_of=_LABEL_AT,
            evaluation_as_of=_EVALUATION_AT,
        ),
        BullBearDecisionQualityV1(
            predicted_class="bear",
            realized_class="bull",
            quality=QUALITY_TOO_LATE,
            sample_size=4,
            decision_as_of=_DECISION_AT,
            label_as_of=_LABEL_AT,
            evaluation_as_of=_EVALUATION_AT,
        ),
    )


def _request(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> CanonicalRegimeAwareEvaluationRequestV1:
    identity = identity or _identity()
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    payload: dict[str, Any] = {
        "experiment_identity": identity,
        "mapping_contract": _mapping(),
        "regime_slices": _slices(),
        "core_logic_attribution": _attribution(),
        "bull_bear_decision_quality": _quality(),
        "evidence_refs": [
            {
                "kind": "EXPERIMENT_RECORD",
                "ref": experiment_id,
                "digest": _digest("experiment-record"),
            }
        ],
        "created_at": _CREATED_AT,
        "metric_definitions": METRIC_DEFINITION_VERSION,
        "robustness_suite_version": ROBUSTNESS_SUITE_VERSION,
        "experiment_id": None,
    }
    payload.update(overrides)
    return CanonicalRegimeAwareEvaluationRequestV1(**payload)


def test_valid_record_round_trip_preserves_identity_and_exit_gates() -> None:
    identity = _identity()
    record = build_canonical_regime_aware_evaluation_v1(_request(identity))
    assert record["completeness"] == "COMPLETE"
    assert record["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    assert canonical_record_payload(record["experiment_identity"]) == canonical_record_payload(
        identity
    )
    for field_name in _CORE_DIGEST_FIELDS:
        assert record["experiment_identity"][field_name] == identity[field_name]
    assert record["canonical_trading_decision_core_bound"] is True
    assert record["regime_aware_evaluation_present"] is True
    assert record["regime_mapping_explicit"] is True
    assert record["regime_lookahead_blocked"] is True
    assert record["canonical_core_logic_attribution_present"] is True
    assert record["bull_bear_decision_quality_evaluable"] is True
    assert {item["family"] for item in record["regime_slices"]} == set(REQUIRED_REGIME_FAMILIES)
    validate_canonical_regime_aware_evaluation_v1(record)


def test_identical_inputs_are_deterministic() -> None:
    first = canonical_record_payload(build_canonical_regime_aware_evaluation_v1(_request()))
    second = canonical_record_payload(build_canonical_regime_aware_evaluation_v1(_request()))
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)
    assert first["evaluation_identity"] == second["evaluation_identity"]


def test_reuses_phase_4_metric_and_robustness_tokens() -> None:
    record = build_canonical_regime_aware_evaluation_v1(_request())
    assert record["metric_definitions"] == METRIC_DEFINITION_VERSION
    assert record["robustness_suite_version"] == ROBUSTNESS_SUITE_VERSION
    with pytest.raises(RegimeAwareEvaluationError, match="Phase 4 token"):
        build_canonical_regime_aware_evaluation_v1(_request(metric_definitions="other_metrics_v1"))


def test_missing_family_fails_closed() -> None:
    slices = tuple(item for item in _slices() if item.family != FAMILY_TREND_RANGE)
    with pytest.raises(RegimeAwareEvaluationError, match="required regime families missing"):
        build_canonical_regime_aware_evaluation_v1(_request(regime_slices=slices))


def test_missing_or_defaulted_fee_and_slippage_fail_closed() -> None:
    with pytest.raises(RegimeAwareEvaluationError, match="silent zero defaults"):
        build_canonical_regime_aware_evaluation_v1(
            _request(
                regime_slices=(_slice(FAMILY_TREND_RANGE, "trend", fee_drag=None),)
                + tuple(item for item in _slices() if item.family != FAMILY_TREND_RANGE)
            )
        )
    with pytest.raises(RegimeAwareEvaluationError, match="silent zero defaults"):
        build_canonical_regime_aware_evaluation_v1(
            _request(
                regime_slices=(_slice(FAMILY_TREND_RANGE, "trend", slippage=None),)
                + tuple(item for item in _slices() if item.family != FAMILY_TREND_RANGE)
            )
        )
    record = build_canonical_regime_aware_evaluation_v1(
        _request(
            regime_slices=(_slice(FAMILY_TREND_RANGE, "trend", fee_drag=0.0, slippage=0.0),)
            + tuple(item for item in _slices() if item.family != FAMILY_TREND_RANGE)
        )
    )
    trend = next(item for item in record["regime_slices"] if item["family"] == FAMILY_TREND_RANGE)
    assert trend["fee_drag"] == 0.0
    assert trend["slippage"] == 0.0


def test_lookahead_into_decision_labels_fails_closed() -> None:
    with pytest.raises(RegimeAwareEvaluationError, match="lookahead is forbidden"):
        build_canonical_regime_aware_evaluation_v1(
            _request(
                regime_slices=(
                    _slice(FAMILY_TREND_RANGE, "trend", label_as_of="2026-08-17T12:00:01Z"),
                )
                + tuple(item for item in _slices() if item.family != FAMILY_TREND_RANGE)
            )
        )


def test_silent_research_runtime_identity_fails_closed() -> None:
    with pytest.raises(RegimeAwareEvaluationError, match="pairwise mapping rules"):
        build_canonical_regime_aware_evaluation_v1(
            _request(
                mapping_contract=RegimeMappingContractV1(
                    mapping_mode=MAPPING_MODE_EXPLICIT,
                    research_regime_taxonomy="canonical_research_regime_taxonomy_v1",
                    runtime_regime_taxonomy="canonical_research_regime_taxonomy_v1",
                )
            )
        )
    with pytest.raises(RegimeAwareEvaluationError, match="silently identical"):
        build_canonical_regime_aware_evaluation_v1(
            _request(
                mapping_contract=RegimeMappingContractV1(
                    mapping_mode=MAPPING_MODE_SEPARATION,
                    research_regime_taxonomy="same_taxonomy_v1",
                    runtime_regime_taxonomy="same_taxonomy_v1",
                    documented_separation_reason="research_and_runtime_taxonomies_are_distinct",
                )
            )
        )


def test_explicit_mapping_and_documented_separation_are_accepted() -> None:
    mapped = build_canonical_regime_aware_evaluation_v1(_request())
    assert mapped["mapping_contract"]["mapping_mode"] == MAPPING_MODE_EXPLICIT
    separated = build_canonical_regime_aware_evaluation_v1(
        _request(mapping_contract=_mapping(mode=MAPPING_MODE_SEPARATION))
    )
    assert separated["mapping_contract"]["mapping_mode"] == MAPPING_MODE_SEPARATION
    assert separated["mapping_contract"]["mappings"] == []


def test_core_logic_attribution_binds_phase_1_digests_without_invention() -> None:
    identity = _identity()
    record = build_canonical_regime_aware_evaluation_v1(_request(identity))
    by_stage = {item["stage"]: item for item in record["core_logic_attribution"]}
    assert set(by_stage) == set(REQUIRED_ATTRIBUTION_STAGES)
    assert by_stage[STAGE_BULL_BEAR]["attribution_class"] == ATTRIBUTION_TIMING_ERROR
    assert by_stage[STAGE_BULL_BEAR]["identity_digest"] == identity["bull_bear_logic_digest"]
    assert by_stage["ECONOMIC_OUTCOME"]["attribution_class"] == ATTRIBUTION_NOT_ATTRIBUTABLE
    assert "identity_digest" not in by_stage["ECONOMIC_OUTCOME"]
    incomplete = tuple(item for item in _attribution() if item.stage != STAGE_BULL_BEAR)
    with pytest.raises(RegimeAwareEvaluationError, match="required attribution stages missing"):
        build_canonical_regime_aware_evaluation_v1(_request(core_logic_attribution=incomplete))


def test_bull_bear_decision_quality_is_evaluable() -> None:
    record = build_canonical_regime_aware_evaluation_v1(_request())
    qualities = {item["quality"] for item in record["bull_bear_decision_quality"]}
    assert QUALITY_CORRECT in qualities
    assert QUALITY_TOO_LATE in qualities
    assert record["bull_bear_decision_quality_evaluable"] is True
    with pytest.raises(RegimeAwareEvaluationError, match="bull_bear_decision_quality observations"):
        build_canonical_regime_aware_evaluation_v1(_request(bull_bear_decision_quality=()))


def test_global_only_pnl_grouping_is_not_sufficient() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "MARKET_CONTEXT" in source
    assert "BULL_BEAR_CLASSIFICATION" in source
    assert "STATE_SWITCH" in source
    assert "SURVIVAL" in source
    assert "SUITABILITY" in source
    assert "DOUBLE_PLAY" in source
    assert "ENTRY_POSITION_EXIT" in source
    bull_only = tuple(item for item in _slices() if item.family == FAMILY_BULL_BEAR)
    with pytest.raises(RegimeAwareEvaluationError, match="required regime families missing"):
        build_canonical_regime_aware_evaluation_v1(_request(regime_slices=bull_only))


def test_no_runtime_live_config_promotion_or_phase_9_paths() -> None:
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
        "scripts.run_learning_apply_cycle",
        "src.live",
        "src.trading",
        "src.trading.master_v2",
        "src.risk",
        "src.experiments.canonical_robustness_suite_v1",
        "src.experiments.canonical_comparison_ssot_v1",
        "src.experiments.canonical_champion_challenger_v1",
        "src.experiments.canonical_reality_gap_store_v1",
        "src.experiments.regime_sweeps",
        "src.regime.canonical_regime_meta_gated_selection_v1",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.runtime_observation_feedback_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
        "src.meta.learning_loop.canary_micro_live_readiness_v1",
        "src.experiments.live_session_registry",
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
        "Phase 9",
        "Portfolio Learning",
    ):
        assert token not in source
    record = build_canonical_regime_aware_evaluation_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["regime_aware_evaluation_present"] = False  # type: ignore[index]
    assert REGIME_AWARE_EVALUATION_PRESENT is True
    assert REGIME_MAPPING_EXPLICIT is True
    assert REGIME_LOOKAHEAD_BLOCKED is True
    assert CANONICAL_CORE_LOGIC_ATTRIBUTION_PRESENT is True
    assert BULL_BEAR_DECISION_QUALITY_EVALUABLE is True
    assert REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY is False
    assert REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG is False
    assert REGIME_AWARE_EVALUATION_CAN_PROMOTE is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert record["regime_aware_evaluation_can_mutate_live_config"] is False
    assert record["regime_aware_evaluation_can_submit_order"] is False
    assert record["regime_aware_evaluation_can_fund"] is False
    assert record["regime_aware_evaluation_can_increase_risk"] is False
    assert record["regime_aware_evaluation_can_increase_leverage"] is False
    assert record["regime_aware_evaluation_can_authorize_canary"] is False
    assert record["regime_aware_evaluation_can_promote_to_live"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_regime_aware_evaluation_v1
    )
    assert ATTRIBUTION_STRATEGY_EDGE in source

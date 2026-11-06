"""Phase 12 Canonical Advanced Search v1 contract tests."""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_advanced_search_v1 import (
    ADVANCED_SEARCH_AUTHORITY,
    ADVANCED_SEARCH_PRESENT,
    AUTONOMOUS_PROMOTION,
    AdvancedSearchValidationError,
    BEST_SHARPE_IS_NOT_AUTO_WINNER,
    CanonicalAdvancedSearchRequestV1,
    PHASE_13_STARTED,
    PROMOTION_AUTHORITY,
    SEARCH_CAN_PROMOTE,
    SEARCH_HAS_RUNTIME_AUTHORITY,
    SEARCH_IS_AUTHORITY_MECHANISM,
    SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
    STATUS_BUDGET_EXCLUDED,
    STATUS_DEPRIORITIZED_KNOWN_FAILURE,
    STATUS_PROPOSED,
    STATUS_REJECTED_DUPLICATE_WITHOUT_RETEST,
    SUPPORTED_SEARCH_METHODS,
    SearchAxisV1,
    SearchSpaceV1,
    build_canonical_advanced_search_v1,
    canonical_advanced_search_constraint_v1,
    canonical_advanced_search_objective_v1,
    canonical_record_payload_v1,
    validate_canonical_advanced_search_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    build_canonical_failure_memory_record_v1,
)
from src.experiments.canonical_meta_learning_v1 import (
    META_LEARNING_AUTHORITY,
    PROPOSAL_PRIORITIZE_RESEARCH,
    PROMOTION_AUTHORITY as META_PROMOTION_AUTHORITY,
    QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL,
)
from src.experiments.canonical_reality_gap_store_v1 import (
    CanonicalRealityGapRecordRequestV1,
    OBSERVED_SURFACE_SHADOW,
    RealityGapDimensionV1,
    build_canonical_reality_gap_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_advanced_search_v1.py"
_GIT_SHA = "fc059d1285be55e433a9ca59e89ce187e7a4b363"
_CREATED_AT = "2026-08-18T15:00:00Z"
_EVIDENCE_AT = "2026-08-18T14:00:00Z"
_PARENT_HYPOTHESIS_ID = "hyp.ma-crossover.v1"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _identity_request(**overrides: Any) -> CanonicalExperimentIdentityRequestV1:
    payload: dict[str, Any] = {
        "git_sha": _GIT_SHA,
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": "ma_crossover.v1",
        "strategy_params": {"fast": 10, "slow": 50},
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
        "seed": 12,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return CanonicalExperimentIdentityRequestV1(**payload)


def _identity(**overrides: Any) -> Mapping[str, Any]:
    return build_canonical_experiment_identity_v1(_identity_request(**overrides))


def _space(**overrides: Any) -> SearchSpaceV1:
    payload: dict[str, Any] = {
        "search_space_id": "search.ma.v1",
        "axes": (
            SearchAxisV1(name="fast", values=(10, 15)),
            SearchAxisV1(name="slow", values=(50, 100)),
        ),
    }
    payload.update(overrides)
    return SearchSpaceV1(**payload)


def _signal(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "applies_to_champion": False,
        "authority": META_LEARNING_AUTHORITY,
        "kind": PROPOSAL_PRIORITIZE_RESEARCH,
        "promotion_authority": META_PROMOTION_AUTHORITY,
        "proposal_id": _digest("proposal.ma-crossover"),
        "question_id": QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL,
        "reason": "prioritize-ma-crossover-family",
        "target": "ma_crossover",
        "target_kind": "strategy_family",
    }
    payload.update(overrides)
    return payload


def _failure(
    identity: Mapping[str, Any],
    *,
    hypothesis_id: str = _PARENT_HYPOTHESIS_ID,
    failure_class: str = "REJECTED_OVERFIT",
    parameter_region: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    gate = {
        "REJECTED_OVERFIT": "OVERFIT_GATE",
        "REJECTED_TAIL_RISK": "TAIL_RISK_GATE",
        "REJECTED_REALITY_GAP": "REALITY_GAP_GATE",
    }[failure_class]
    return build_canonical_failure_memory_record_v1(
        CanonicalFailureMemoryRecordRequestV1(
            experiment_identity=identity,
            hypothesis_id=hypothesis_id,
            failure_class=failure_class,
            failed_gate=gate,
            rejection_reason=failure_class,
            regime="high_vol",
            parameter_region=dict(parameter_region or {"fast": 15, "slow": 50}),
            cost_sensitivity={"fee_stress": 0.25},
            instability_indicators={"fold_sign_flips": 3},
            evidence_refs=[
                {
                    "kind": "EXPERIMENT_RECORD",
                    "ref": experiment_id,
                    "digest": _digest(f"experiment-record-{experiment_id}"),
                }
            ],
            created_at=_EVIDENCE_AT,
            robustness_policy_digest=_digest("robustness-policy"),
        )
    )


def _gap(identity: Mapping[str, Any]) -> Mapping[str, Any]:
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
                    expected=0.001,
                    observed=0.02,
                    threshold=0.001,
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
            created_at=_EVIDENCE_AT,
        )
    )


def _request(**overrides: Any) -> CanonicalAdvancedSearchRequestV1:
    payload: dict[str, Any] = {
        "identity_template": _identity_request(),
        "search_space": _space(),
        "search_method": SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
        "search_method_version": "canonical_advanced_search_method_v1",
        "seed": 12,
        "budget": 4,
        "search_space_cardinality_limit": 16,
        "objective": canonical_advanced_search_objective_v1(),
        "constraint": canonical_advanced_search_constraint_v1(),
        "created_at": _CREATED_AT,
        "parent_hypothesis_id": _PARENT_HYPOTHESIS_ID,
        "lineage_kind": "ROOT",
        "hypothesis_kind": "trend_following",
        "strategy_family": "ma_crossover",
        "regime": "high_vol",
        "robustness_policy_digest": _digest("robustness-policy"),
    }
    payload.update(overrides)
    return CanonicalAdvancedSearchRequestV1(**payload)


def test_deterministic_search_proposal_generation() -> None:
    first = build_canonical_advanced_search_v1(_request())
    second = build_canonical_advanced_search_v1(_request())
    validate_canonical_advanced_search_v1(first)
    assert first["search_identity"] == second["search_identity"]
    assert canonical_record_payload_v1(first) == canonical_record_payload_v1(second)
    assert deterministic_json_dumps(canonical_record_payload_v1(first)) == deterministic_json_dumps(
        canonical_record_payload_v1(second)
    )
    assert first["search_method"] == SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH
    assert first["supported_search_mechanisms"] == list(SUPPORTED_SEARCH_METHODS)
    assert len(first["candidates"]) == 4
    assert {item["status"] for item in first["candidates"]} == {STATUS_PROPOSED}
    assert first["overall_status"] == "SEARCH_COMPLETE"
    assert first["ranked_experiment_ids"] == []
    assert first["champion_experiment_id"] is None


def test_canonical_identity_binding_is_required() -> None:
    record = build_canonical_advanced_search_v1(_request())
    template = _identity()
    for candidate in record["candidates"]:
        identity = candidate["experiment_identity"]
        assert identity["completeness"] == "COMPLETE"
        assert identity["fee_model_digest"] == template["fee_model_digest"]
        assert identity["slippage_model_digest"] == template["slippage_model_digest"]
        assert identity["funding_model_digest"] == template["funding_model_digest"]
        assert identity["risk_policy_digest"] == template["risk_policy_digest"]
        assert identity["split_policy_digest"] == template["split_policy_digest"]
        assert identity["trading_decision_core_digest"] == template["trading_decision_core_digest"]
        assert identity["seed"] == 12
        assert candidate["experiment_id"] == derive_experiment_id_v1(
            str(identity["identity_digest"])
        )
        assert candidate["hypothesis_fingerprint"]
    missing_fee = replace(_identity_request(), fee_model_digest="unavailable")
    with pytest.raises(
        AdvancedSearchValidationError, match="COMPLETE Canonical Experiment Identity"
    ):
        build_canonical_advanced_search_v1(_request(identity_template=missing_fee))


def test_search_space_validation_fails_closed() -> None:
    with pytest.raises(AdvancedSearchValidationError, match="forbidden search dimension"):
        build_canonical_advanced_search_v1(
            _request(
                search_space=_space(
                    axes=(
                        SearchAxisV1(name="leverage", values=(1, 2)),
                        SearchAxisV1(name="fast", values=(10, 15)),
                    )
                )
            )
        )
    with pytest.raises(AdvancedSearchValidationError, match="cardinality exceeds"):
        build_canonical_advanced_search_v1(_request(search_space_cardinality_limit=3))
    with pytest.raises(AdvancedSearchValidationError, match="duplicate search axis"):
        build_canonical_advanced_search_v1(
            _request(
                search_space=_space(
                    axes=(
                        SearchAxisV1(name="fast", values=(10, 15)),
                        SearchAxisV1(name="fast", values=(20, 25)),
                    )
                )
            )
        )


def test_constraint_enforcement_rejects_authority_relaxation() -> None:
    loose = replace(canonical_advanced_search_constraint_v1(), cannot_increase_risk=False)
    with pytest.raises(AdvancedSearchValidationError, match="cannot_increase_risk must be true"):
        build_canonical_advanced_search_v1(_request(constraint=loose))
    loose_objective = replace(
        canonical_advanced_search_objective_v1(), sharpe_is_not_auto_winner=False
    )
    with pytest.raises(
        AdvancedSearchValidationError, match="sharpe_is_not_auto_winner must be true"
    ):
        build_canonical_advanced_search_v1(_request(objective=loose_objective))


def test_failure_memory_known_region_is_deprioritized_not_silently_omitted() -> None:
    failed_identity = _identity(strategy_params={"fast": 15, "slow": 50})
    record = build_canonical_advanced_search_v1(
        _request(failure_records=(_failure(failed_identity),))
    )
    statuses = {item["parameter_region"]["fast"]: item["status"] for item in record["candidates"]}
    by_region = {
        (item["parameter_region"]["fast"], item["parameter_region"]["slow"]): item
        for item in record["candidates"]
    }
    known = by_region[(15, 50)]
    assert known["status"] == STATUS_DEPRIORITIZED_KNOWN_FAILURE
    assert known["failure_signals"]["known_rejected_parameter_region"] is True
    assert known["failure_signals"]["known_robustness_failure"] is True
    assert known["offline_experiment_request"] is None
    assert any(item["status"] == STATUS_PROPOSED for item in record["candidates"])
    assert record["search_evidence"]["deprioritized_known_failure_count"] == 1
    assert statuses[10] == STATUS_PROPOSED


def test_duplicate_hypothesis_without_retest_is_rejected() -> None:
    baseline = build_canonical_advanced_search_v1(_request())
    proposed = next(item for item in baseline["candidates"] if item["status"] == STATUS_PROPOSED)
    identity = proposed["experiment_identity"]
    record = build_canonical_advanced_search_v1(
        _request(
            failure_records=(
                _failure(
                    identity,
                    hypothesis_id=str(proposed["hypothesis_id"]),
                    parameter_region=proposed["parameter_region"],
                ),
            )
        )
    )
    duplicate = next(
        item for item in record["candidates"] if item["hypothesis_id"] == proposed["hypothesis_id"]
    )
    assert duplicate["status"] == STATUS_REJECTED_DUPLICATE_WITHOUT_RETEST
    assert duplicate["duplicate_assessment"]["detected"] is True
    assert duplicate["duplicate_assessment"]["automatic_research_ban"] is False
    retried = build_canonical_advanced_search_v1(
        _request(
            failure_records=(
                _failure(
                    identity,
                    hypothesis_id=str(proposed["hypothesis_id"]),
                    parameter_region=proposed["parameter_region"],
                ),
            ),
            retest_reason="explicit-retest-after-policy-review",
        )
    )
    retried_match = next(
        item for item in retried["candidates"] if item["hypothesis_id"] == proposed["hypothesis_id"]
    )
    assert retried_match["status"] in {STATUS_PROPOSED, STATUS_BUDGET_EXCLUDED}


def test_meta_learning_signals_bind_and_change_priority_not_authority() -> None:
    record = build_canonical_advanced_search_v1(
        _request(
            meta_learning_signals=(_signal(),),
            meta_learning_identity=_digest("meta-learning-record"),
        )
    )
    assert record["input_lineage"]["meta_learning_identity"] == _digest("meta-learning-record")
    assert all(item["search_priority_score"] == 20 for item in record["candidates"])
    assert all(item["matched_meta_learning_proposal_ids"] for item in record["candidates"])
    assert record["search_can_promote"] is False
    assert record["search_is_authority_mechanism"] is False
    with pytest.raises(AdvancedSearchValidationError, match="meta_learning_identity"):
        build_canonical_advanced_search_v1(_request(meta_learning_signals=(_signal(),)))


def test_budget_excludes_without_silent_omission() -> None:
    record = build_canonical_advanced_search_v1(_request(budget=1))
    statuses = [item["status"] for item in record["candidates"]]
    assert statuses.count(STATUS_PROPOSED) == 1
    assert statuses.count(STATUS_BUDGET_EXCLUDED) == 3
    assert len(record["offline_experiment_requests"]) == 1
    assert len(record["parameter_region_proposals"]) == 4
    proposed = next(item for item in record["candidates"] if item["status"] == STATUS_PROPOSED)
    assert proposed["offline_experiment_request"]["executed"] is False
    assert proposed["offline_experiment_request"]["loop_started"] is False
    assert proposed["offline_experiment_request"]["schema_version"] == (
        "canonical_automated_offline_research_loop_v1"
    )


def test_reality_gap_signal_deprioritizes_matching_region() -> None:
    gap_identity = _identity(strategy_params={"fast": 10, "slow": 100})
    record = build_canonical_advanced_search_v1(_request(reality_gap_records=(_gap(gap_identity),)))
    by_region = {
        (item["parameter_region"]["fast"], item["parameter_region"]["slow"]): item
        for item in record["candidates"]
    }
    hit = by_region[(10, 100)]
    assert hit["status"] == STATUS_DEPRIORITIZED_KNOWN_FAILURE
    assert hit["failure_signals"]["known_reality_gap_failure"] is True


def test_unknown_and_unsupported_methods_fail_closed() -> None:
    with pytest.raises(AdvancedSearchValidationError, match="unsupported"):
        build_canonical_advanced_search_v1(_request(search_method="OPTUNA"))
    with pytest.raises(AdvancedSearchValidationError, match="unknown search_method"):
        build_canonical_advanced_search_v1(_request(search_method="RANDOM_WALK"))
    with pytest.raises(AdvancedSearchValidationError, match="must be a positive int"):
        build_canonical_advanced_search_v1(_request(budget=0))


def test_parent_bound_lineage_requires_parent_identity() -> None:
    parent = _identity(strategy_identity="parent.ma.v1")
    with pytest.raises(AdvancedSearchValidationError, match="parent_experiment_identity"):
        build_canonical_advanced_search_v1(_request(lineage_kind="PARENT_BOUND"))
    record = build_canonical_advanced_search_v1(
        _request(lineage_kind="PARENT_BOUND", parent_experiment_identity=parent)
    )
    for candidate in record["candidates"]:
        assert candidate["experiment_identity"]["parent_lineage"]["kind"] == "PARENT_BOUND"
        assert (
            candidate["experiment_identity"]["parent_lineage"]["parent_lineage_ref"]
            == parent["identity_digest"]
        )


def test_no_autonomous_promotion_live_config_or_authority_paths() -> None:
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
        "src.experiments.canonical_comparison_ssot_v1",
        "src.experiments.canonical_portfolio_learning_v1",
        "src.experiments.canonical_regime_aware_evaluation_v1",
        "src.experiments.canonical_automated_offline_research_loop_v1",
        "src.experiments.canonical_robustness_suite_v1",
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
        "BEST_SHARPE =>",
        "rank_comparable_candidates_v1",
        "run_canonical_automated_offline_research_loop_v1",
        "random.seed",
        "numpy.random",
    ):
        assert token not in source
    record = build_canonical_advanced_search_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["overall_status"] = "SEARCH_COMPLETE"  # type: ignore[index]
    cloned = copy.deepcopy(canonical_record_payload_v1(record))
    cloned["search_can_promote"] = True
    with pytest.raises(AdvancedSearchValidationError, match="search_can_promote must be false"):
        validate_canonical_advanced_search_v1(cloned)
    assert ADVANCED_SEARCH_PRESENT is True
    assert SEARCH_HAS_RUNTIME_AUTHORITY is False
    assert SEARCH_IS_AUTHORITY_MECHANISM is False
    assert SEARCH_CAN_PROMOTE is False
    assert AUTONOMOUS_PROMOTION is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert ADVANCED_SEARCH_AUTHORITY == "RESEARCH_ONLY"
    assert BEST_SHARPE_IS_NOT_AUTO_WINNER is True
    assert PHASE_13_STARTED is False
    assert record["search_can_submit_order"] is False
    assert record["search_can_fund"] is False
    assert record["search_can_increase_risk"] is False
    assert record["search_can_increase_leverage"] is False
    assert record["search_can_authorize_canary"] is False
    assert record["search_can_promote_to_live"] is False
    assert record["search_can_write_live_config"] is False
    assert record["search_can_write_testnet_config"] is False
    assert record["search_can_create_confirm_token"] is False
    assert record["search_can_use_confirm_token"] is False
    assert record["search_can_arm"] is False
    assert record["search_can_enable"] is False
    assert record["search_can_replace_productive_champion"] is False
    assert record["learning_may_autonomously_replace_core_logic"] is False
    assert record["phase_13_started"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_advanced_search_v1
    )


def test_phase_1_to_11_authority_invariants_remain_fail_closed() -> None:
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
    from src.experiments.canonical_meta_learning_v1 import (
        META_LEARNING_CAN_PROMOTE,
        META_LEARNING_HAS_RUNTIME_AUTHORITY,
        PHASE_12_STARTED,
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
    assert META_LEARNING_HAS_RUNTIME_AUTHORITY is False
    assert META_LEARNING_CAN_PROMOTE is False
    assert PHASE_12_STARTED is False

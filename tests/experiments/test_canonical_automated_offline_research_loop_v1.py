"""Phase 10 Canonical Automated Offline Research Loop v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_automated_offline_research_loop_v1 import (
    AUTOMATED_OFFLINE_RESEARCH_LOOP,
    AUTOMATED_RUNTIME_AUTHORITY,
    AUTONOMOUS_PROMOTION,
    CANONICAL_LOOP_STEPS,
    CanonicalAutomatedOfflineResearchLoopRequestV1,
    LOOP_COMPLETE,
    LOOP_FAILED,
    OfflineExperimentObservationsV1,
    PROMOTION_AUTHORITY,
    RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG,
    RESEARCH_LOOP_CAN_PROMOTE,
    RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY,
    RESEARCH_LOOP_PRESENT,
    ResearchHypothesisCandidateV1,
    AutomatedOfflineResearchLoopValidationError,
    canonical_record_payload_v1,
    run_canonical_automated_offline_research_loop_v1,
    validate_canonical_automated_offline_research_loop_v1,
    _bind_experiment_memory,
)
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_experiment_memory_v1 import (
    ExperimentRecordConflictError,
    derive_experiment_id_v1,
)
from src.experiments.canonical_identity_bound_offline_observation_binding_v1 import (
    OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
    STATUS_BOUND,
)
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_reality_gap_store_v1 import (
    OBSERVED_SURFACE_SHADOW,
    RealityGapDimensionV1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    METRIC_DEFINITION_VERSION,
    SCHEMA_VERSION as ROBUSTNESS_SUITE_VERSION,
    canonical_robustness_policy_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_automated_offline_research_loop_v1.py"
_GIT_SHA = "562345af2153fa0c659ca261a71a9191b4b7210e"
_CREATED_AT = "2026-08-18T12:40:00Z"
_TIME_HORIZON = {"end": "2024-12-31T00:00:00Z", "start": "2020-01-01T00:00:00Z"}
_MARKET_UNIVERSE = ("BTC-USDT-SWAP", "ETH-USDT-SWAP")
_RETURNS = [0.01, -0.004, 0.006, -0.002, 0.005, -0.003, 0.007, -0.001] * 4
_HYPOTHESIS_ID = "hyp.ma-crossover.v1"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _identity_request(**overrides: Any) -> CanonicalExperimentIdentityRequestV1:
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
    return CanonicalExperimentIdentityRequestV1(**payload)


def _identity(**overrides: Any) -> Mapping[str, Any]:
    return build_canonical_experiment_identity_v1(_identity_request(**overrides))


def _candidate(
    identity: Mapping[str, Any] | None = None, **overrides: Any
) -> ComparisonCandidateV1:
    payload: dict[str, Any] = {
        "experiment_identity": identity or _identity(seed=7, strategy_identity="champion.v1"),
        "robustness_suite_version": ROBUSTNESS_SUITE_VERSION,
        "metric_definitions": METRIC_DEFINITION_VERSION,
        "time_horizon": dict(_TIME_HORIZON),
        "market_universe": list(_MARKET_UNIVERSE),
        "experiment_id": None,
        "evidence_refs": (),
    }
    payload.update(overrides)
    return ComparisonCandidateV1(**payload)


def _hypothesis(**overrides: Any) -> ResearchHypothesisCandidateV1:
    payload: dict[str, Any] = {
        "hypothesis_id": _HYPOTHESIS_ID,
        "identity_request": _identity_request(),
        "parameter_region": {"fast": 10, "slow": 50},
        "regime": "mixed",
        "candidate_ref": "candidate.ma-crossover.v1",
        "strategy_family": "ma_crossover",
        "time_horizon": dict(_TIME_HORIZON),
        "market_universe": list(_MARKET_UNIVERSE),
    }
    payload.update(overrides)
    return ResearchHypothesisCandidateV1(**payload)


def _complete_metrics() -> dict[str, float]:
    return {
        "exposure": 0.4,
        "fee_drag": 0.01,
        "funding_sensitivity": 0.02,
        "max_dd": 0.08,
        "oos_stability": 0.85,
        "parameter_stability": 0.9,
        "profit_factor": 1.4,
        "regime_concentration": 0.35,
        "sample_size": 32.0,
        "sharpe": 1.2,
        "slippage_sensitivity": 0.04,
        "sortino": 1.5,
        "tail_risk": 0.07,
        "turnover": 0.2,
    }


def _complete_observations(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "bad_tick_stress": {"bad_tick_count": 0, "max_abs_return": 0.04},
        "cost_stress": {
            "baseline": {"sharpe": 1.2},
            "fee": {"sharpe": 1.0},
            "funding": {"sharpe": 1.05},
            "slippage": {"sharpe": 1.02},
        },
        "embargo": {"embargo_bars": 2, "sample_size": 16, "test_sharpe": 1.0, "train_sharpe": 1.2},
        "latency_stress": {"baseline": {"sharpe": 1.2}, "stressed": {"sharpe": 1.1}},
        "liquidity_stress": {"baseline": {"sharpe": 1.2}, "stressed": {"sharpe": 1.08}},
        "metrics": _complete_metrics(),
        "missing_data_stress": {"missing_fraction": 0.0, "sharpe": 1.2},
        "multiple_testing": {
            "alpha": 0.05,
            "correction": "BONFERRONI",
            "discoveries": 1,
            "family_size": 1,
            "p_value": 0.01,
        },
        "parameter_sensitivity": {
            "center": {"fast": 10.0, "sharpe": 1.2},
            "points": [
                {"fast": 10.0, "sharpe": 1.2},
                {"fast": 12.0, "sharpe": 1.15},
            ],
        },
        "purged_split": {
            "purge_bars": 2,
            "sample_size": 16,
            "test_sharpe": 1.0,
            "train_sharpe": 1.2,
        },
        "regime_stress": {
            "regimes": {
                "high_vol": {"sample_size": 16, "sharpe": 0.9},
                "low_vol": {"sample_size": 16, "sharpe": 1.1},
            }
        },
        "returns": list(_RETURNS),
        "risk_stress": {"baseline": {"max_dd": 0.08}, "stressed": {"max_dd": 0.12}},
        "split_metrics": {
            "holdout": {"sample_size": 16, "sharpe": 1.0},
            "train": {"sample_size": 32, "sharpe": 1.2},
            "validation": {"sample_size": 16, "sharpe": 1.1},
        },
        "spread_stress": {"baseline": {"sharpe": 1.2}, "stressed": {"sharpe": 1.09}},
        "walk_forward_windows": [
            {"sample_size": 16, "test_sharpe": 1.0, "train_sharpe": 1.2},
            {"sample_size": 16, "test_sharpe": 0.95, "train_sharpe": 1.1},
        ],
    }
    payload.update(overrides)
    return payload


def _observations(**overrides: Any) -> OfflineExperimentObservationsV1:
    payload: dict[str, Any] = {
        "metrics": {"sharpe": 1.25, "max_drawdown": -0.12},
        "robustness_results": {"walk_forward": {"passed": True, "folds": 4}},
        "regime_results": {"high_vol": {"sharpe": 0.4}},
        "artifacts": [
            {
                "kind": "REPO_RELATIVE",
                "ref": "docs/ops/specs/CANONICAL_EXPERIMENT_IDENTITY_V1.md",
                "digest": _digest("artifact"),
                "media_type": "text/markdown",
            }
        ],
        "robustness_observations": _complete_observations(),
        "robustness_policy": canonical_robustness_policy_v1(),
    }
    payload.update(overrides)
    return OfflineExperimentObservationsV1(**payload)


def _dimension(
    name: str = "fee",
    *,
    expected: float = 0.001,
    observed: float = 0.0012,
    threshold: float = 0.001,
    unit: str = "ratio",
) -> RealityGapDimensionV1:
    return RealityGapDimensionV1(
        name=name,
        expected=expected,
        observed=observed,
        threshold=threshold,
        unit=unit,
    )


def _request(**overrides: Any) -> CanonicalAutomatedOfflineResearchLoopRequestV1:
    payload: dict[str, Any] = {
        "hypotheses": (_hypothesis(),),
        "selected_hypothesis_id": _HYPOTHESIS_ID,
        "created_at": _CREATED_AT,
        "experiment_observations": _observations(),
        "champion": _candidate(),
        "champion_score": 1.0,
        "challenger_score": 1.2,
        "gap_dimensions": (_dimension(),),
        "observed_surface": OBSERVED_SURFACE_SHADOW,
        "threshold_policy_digest": _digest("threshold-policy"),
    }
    payload.update(overrides)
    return CanonicalAutomatedOfflineResearchLoopRequestV1(**payload)


def _step_status(record: Mapping[str, Any]) -> dict[str, str]:
    return {item["step_id"]: item["status"] for item in record["step_results"]}


def test_complete_loop_reuses_phase_owners_and_is_deterministic() -> None:
    first = run_canonical_automated_offline_research_loop_v1(_request())
    second = run_canonical_automated_offline_research_loop_v1(_request())
    assert first["overall_status"] == LOOP_COMPLETE
    assert [item["step_id"] for item in first["step_results"]] == list(CANONICAL_LOOP_STEPS)
    assert all(item["status"] == "COMPLETE" for item in first["step_results"])
    selected_identity = _identity()
    assert first["selected_experiment_id"] == derive_experiment_id_v1(
        str(selected_identity["identity_digest"])
    )
    champion_identity = _identity(seed=7, strategy_identity="champion.v1")
    assert first["champion_experiment_id"] == derive_experiment_id_v1(
        str(champion_identity["identity_digest"])
    )
    assert first["comparison_result"]["overall_comparability"] == "COMPARABLE"
    assert first["challenger_report"]["research_recommendation"] == "CHALLENGER_RESEARCH_PREFERRED"
    assert first["challenger_report"]["champion_state"]["swapped"] is False
    assert first["robustness_evidence"]["aggregate_status"] == "PASS"
    assert first["reality_gap_record"]["overall_disposition"] == "WITHIN_THRESHOLD"
    assert first["failure_records"] == []
    binding = first["observation_binding"]
    assert binding["status"] == STATUS_BOUND
    assert binding["observation_owner"] == OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1
    assert binding["identity_digest"] == selected_identity["identity_digest"]
    assert binding["experiment_id"] == first["selected_experiment_id"]
    assert binding["identity_reinterpreted"] is False
    assert binding["promotion_apply_allowed"] is False
    assert binding["bounded_auto_allowed"] is False
    assert binding["runtime_authority_effect"] is False
    assert (
        first["experiment_record"]["experiment_identity"]["identity_digest"]
        == selected_identity["identity_digest"]
    )
    validate_canonical_automated_offline_research_loop_v1(first)
    assert canonical_record_payload_v1(first) == canonical_record_payload_v1(second)
    assert deterministic_json_dumps(canonical_record_payload_v1(first)) == deterministic_json_dumps(
        canonical_record_payload_v1(second)
    )


def test_unknown_or_ambiguous_hypothesis_selection_fails_closed() -> None:
    with pytest.raises(AutomatedOfflineResearchLoopValidationError, match="exactly one candidate"):
        run_canonical_automated_offline_research_loop_v1(
            _request(selected_hypothesis_id="hyp.missing.v1")
        )
    duplicate = (_hypothesis(), _hypothesis())
    with pytest.raises(AutomatedOfflineResearchLoopValidationError, match="exactly one candidate"):
        run_canonical_automated_offline_research_loop_v1(_request(hypotheses=duplicate))
    with pytest.raises(AutomatedOfflineResearchLoopValidationError, match="must not be empty"):
        run_canonical_automated_offline_research_loop_v1(_request(hypotheses=()))
    with pytest.raises(AutomatedOfflineResearchLoopValidationError, match="selection_policy"):
        run_canonical_automated_offline_research_loop_v1(_request(selection_policy="PICK_FIRST"))


def test_incomparable_champion_fails_comparability_and_updates_failure_memory() -> None:
    mismatched = _candidate(_identity(seed=7, dataset_digest=_digest("dataset-b")))
    record = run_canonical_automated_offline_research_loop_v1(_request(champion=mismatched))
    assert record["overall_status"] == LOOP_FAILED
    assert _step_status(record)["COMPARABILITY_CHECK"] == "FAILED"
    assert record["comparison_result"]["overall_comparability"] == "COMPARISON_REJECTED"
    assert record["challenger_report"]["research_recommendation"] == "REJECTED_COMPARABILITY"
    assert record["challenger_report"]["ranked_experiment_ids"] == []
    classes = {item["failure_class"] for item in record["failure_records"]}
    assert "REJECTED_COMPARABILITY" in classes


def test_reality_gap_rejection_fails_loop_without_runtime_authority() -> None:
    record = run_canonical_automated_offline_research_loop_v1(
        _request(gap_dimensions=(_dimension(observed=0.05, threshold=0.001),))
    )
    assert record["overall_status"] == LOOP_FAILED
    assert _step_status(record)["REALITY_GAP_REPORT_GENERATION"] == "FAILED"
    assert record["reality_gap_record"]["overall_disposition"] == "REJECTED_REALITY_GAP"
    classes = {item["failure_class"] for item in record["failure_records"]}
    assert "REJECTED_REALITY_GAP" in classes
    assert record["automated_runtime_authority"] is False
    assert record["reality_gap_record"]["observed_surface_is_not_authorization"] is True


def test_duplicate_hypothesis_requires_explicit_retest_reason() -> None:
    failed = run_canonical_automated_offline_research_loop_v1(
        _request(gap_dimensions=(_dimension(observed=0.05, threshold=0.001),))
    )
    existing = failed["failure_records"]
    assert existing
    with pytest.raises(AutomatedOfflineResearchLoopValidationError, match="explicit retest_reason"):
        run_canonical_automated_offline_research_loop_v1(
            _request(existing_failure_records=existing)
        )
    retried = run_canonical_automated_offline_research_loop_v1(
        _request(
            existing_failure_records=existing,
            retest_reason="parameter-region-changed-cost-model",
            gap_dimensions=(_dimension(observed=0.05, threshold=0.001),),
        )
    )
    assert retried["duplicate_assessment"]["detected"] is True
    assert retried["duplicate_assessment"]["automatic_research_ban"] is False
    assert retried["overall_status"] == LOOP_FAILED


def test_optional_persist_uses_canonical_append_only_stores(tmp_path: Path) -> None:
    experiment_store = CanonicalExperimentMemoryStoreV1(tmp_path / "experiments")
    failure_store = CanonicalFailureMemoryStoreV1(tmp_path / "failures")
    gap_store = CanonicalRealityGapStoreV1(tmp_path / "gaps")
    record = run_canonical_automated_offline_research_loop_v1(
        _request(
            experiment_memory_store=experiment_store,
            failure_memory_store=failure_store,
            reality_gap_store=gap_store,
            gap_dimensions=(_dimension(observed=0.05, threshold=0.001),),
        )
    )
    experiment_id = str(record["selected_experiment_id"])
    assert experiment_store.exists(experiment_id) is True
    assert record["persist"]["experiment_record_id"] == experiment_id
    assert (
        record["persist"]["reality_gap_record_id"]
        == record["reality_gap_record"]["reality_gap_record_id"]
    )
    assert record["persist"]["failure_record_ids"]
    for failure_record_id in record["persist"]["failure_record_ids"]:
        assert failure_store.exists(failure_record_id) is True


def test_reuses_phase_4_tokens() -> None:
    record = run_canonical_automated_offline_research_loop_v1(_request())
    assert record["research_metadata"]["metric_definitions"] == METRIC_DEFINITION_VERSION
    assert record["research_metadata"]["robustness_suite_version"] == ROBUSTNESS_SUITE_VERSION
    assert record["research_metadata"]["comparison_ssot_version"] == "canonical_comparison_ssot_v1"
    with pytest.raises(AutomatedOfflineResearchLoopValidationError, match="Phase 4 token"):
        run_canonical_automated_offline_research_loop_v1(
            _request(metric_definitions="other_metrics_v1")
        )


def test_no_runtime_live_config_promotion_or_authority_paths() -> None:
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
        "src.experiments.canonical_portfolio_learning_v1",
        "src.experiments.canonical_regime_aware_evaluation_v1",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
        "src.meta.learning_loop.canary_micro_live_readiness_v1",
        "src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1",
    }
    assert forbidden_imports.isdisjoint(imported)
    assert "src.experiments.canonical_identity_bound_offline_observation_binding_v1" in imported
    assert "bind_canonical_identity_bound_offline_observation_v1" in source
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
        "BEST_SHARPE",
    ):
        assert token not in source
    record = run_canonical_automated_offline_research_loop_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["overall_status"] = LOOP_COMPLETE  # type: ignore[index]
    assert AUTOMATED_OFFLINE_RESEARCH_LOOP is True
    assert AUTOMATED_RUNTIME_AUTHORITY is False
    assert RESEARCH_LOOP_PRESENT is True
    assert RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY is False
    assert RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG is False
    assert RESEARCH_LOOP_CAN_PROMOTE is False
    assert AUTONOMOUS_PROMOTION is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert record["research_loop_can_submit_order"] is False
    assert record["research_loop_can_fund"] is False
    assert record["research_loop_can_increase_risk"] is False
    assert record["research_loop_can_increase_leverage"] is False
    assert record["research_loop_can_authorize_canary"] is False
    assert record["research_loop_can_promote_to_live"] is False
    assert record["autonomous_champion_swap"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        run_canonical_automated_offline_research_loop_v1
    )


def _bind_direct(**overrides: Any) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    identity = overrides.pop("identity", _identity())
    selected = overrides.pop("selected", _hypothesis())
    request = overrides.pop("request", _request())
    if identity is None:
        experiment_id = overrides.pop("experiment_id", _digest("missing-experiment"))
    else:
        experiment_id = overrides.pop(
            "experiment_id", derive_experiment_id_v1(str(identity["identity_digest"]))
        )
    fingerprint = overrides.pop("fingerprint", _digest("hypothesis"))
    return _bind_experiment_memory(
        request=request,
        identity=identity,
        experiment_id=experiment_id,
        fingerprint=fingerprint,
        selected=selected,
        created_at=_CREATED_AT,
        **overrides,
    )


def test_offline_execution_consumes_identity_binding_for_complete_observation() -> None:
    identity = _identity()
    record, binding = _bind_direct(identity=identity)
    assert binding["status"] == STATUS_BOUND
    assert record["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    assert record["experiment_identity"]["identity_digest"] == identity["identity_digest"]
    assert binding["identity_digest"] == identity["identity_digest"]
    assert binding["identity_reinterpreted"] is False


def test_incomplete_identity_is_rejected_by_consumed_binding() -> None:
    identity = dict(_identity())
    identity["completeness"] = "INCOMPLETE"
    with pytest.raises(
        AutomatedOfflineResearchLoopValidationError, match="REJECTED_INCOMPLETE_IDENTITY"
    ):
        _bind_direct(identity=identity)


def test_missing_identity_is_rejected_by_consumed_binding() -> None:
    with pytest.raises(
        AutomatedOfflineResearchLoopValidationError, match="REJECTED_MISSING_DIMENSION"
    ):
        _bind_direct(identity=None)


def test_malformed_observation_is_rejected_by_consumed_binding() -> None:
    with pytest.raises(
        AutomatedOfflineResearchLoopValidationError,
        match="offline experiment observation binding failed",
    ):
        _bind_direct(request=_request(experiment_observations=_observations(artifacts="bad")))


def test_identity_digest_is_passed_through_unchanged() -> None:
    identity = _identity()
    record, binding = _bind_direct(identity=identity)
    assert record["experiment_identity"]["identity_digest"] == identity["identity_digest"]
    assert binding["identity_digest"] == identity["identity_digest"]
    assert binding["experiment_id"] == record["experiment_id"]
    loop = run_canonical_automated_offline_research_loop_v1(_request())
    assert loop["observation_binding"]["identity_digest"] == identity["identity_digest"]
    assert loop["selected_experiment_id"] == record["experiment_id"]


def test_phase2_divergent_duplicate_persist_remains_fail_closed(tmp_path: Path) -> None:
    store = CanonicalExperimentMemoryStoreV1(tmp_path / "experiments")
    first = run_canonical_automated_offline_research_loop_v1(
        _request(experiment_memory_store=store)
    )
    assert store.exists(str(first["selected_experiment_id"])) is True
    with pytest.raises(ExperimentRecordConflictError, match="divergent"):
        run_canonical_automated_offline_research_loop_v1(
            _request(
                experiment_memory_store=store,
                experiment_observations=_observations(
                    metrics={"sharpe": 0.01, "max_drawdown": -0.9}
                ),
            )
        )
    stored = store.get(str(first["selected_experiment_id"]))
    assert stored["metrics"]["sharpe"] == 1.25

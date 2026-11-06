"""Phase 4 Canonical Robustness Suite v1 contract tests."""

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
from src.experiments.canonical_failure_memory_store_v1 import (
    RECORD_FILENAME,
    CanonicalFailureMemoryStoreV1,
)
from src.experiments.canonical_failure_memory_v1 import canonical_record_payload as failure_payload
from src.experiments.canonical_robustness_suite_v1 import (
    ALL_CATALOG_TESTS,
    DEFERRED_STATISTICAL_CONTROLS,
    METRIC_DEFINITION_VERSION,
    REQUIRED_ROBUSTNESS_TESTS,
    ROBUSTNESS_SUITE_CAN_PROMOTE,
    ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY,
    SINGLE_METRIC_PROMOTION,
    CanonicalRobustnessSuiteRequestV1,
    RobustnessSuiteValidationError,
    build_canonical_robustness_evidence_v1,
    build_failure_records_for_failed_gates_v1,
    canonical_record_payload,
    canonical_robustness_policy_v1,
    derive_robustness_suite_identity_v1,
    validate_canonical_robustness_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITE_MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_robustness_suite_v1.py"
_GIT_SHA = "e763bf1bf133afab1c3850a6bbaafde6f83e39d2"
_RETURNS = [0.01, -0.004, 0.006, -0.002, 0.005, -0.003, 0.007, -0.001] * 4


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


def _bound_ref(digest: str) -> dict[str, str]:
    return {"kind": "IDENTITY_DIGEST_BOUND", "digest": digest}


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


def _request(
    identity: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> CanonicalRobustnessSuiteRequestV1:
    identity = identity or _identity()
    payload: dict[str, Any] = {
        "experiment_identity": identity,
        "candidate_ref": "candidate.ma-crossover.v1",
        "dataset_ref": _bound_ref(str(identity["dataset_digest"])),
        "split_policy_ref": _bound_ref(str(identity["split_policy_digest"])),
        "cost_model_ref": _bound_ref(str(identity["cost_model_digest"])),
        "risk_policy_ref": _bound_ref(str(identity["risk_policy_digest"])),
        "seed": int(identity["seed"]),
        "created_at": "2026-08-17T19:00:00Z",
        "robustness_policy": canonical_robustness_policy_v1(),
        "observations": _complete_observations(),
        "hypothesis_id": "hyp.ma-crossover.v1",
        "regime": "mixed",
        "parameter_region": {"fast": 10, "slow": 50},
        "metric_definition_version": METRIC_DEFINITION_VERSION,
        "experiment_id": None,
        "promotion_intent": "FORBIDDEN",
    }
    payload.update(overrides)
    return CanonicalRobustnessSuiteRequestV1(**payload)


def _status_by_id(evidence: Mapping[str, Any]) -> dict[str, str]:
    return {item["test_id"]: item["status"] for item in evidence["test_results"]}


def test_deterministic_identity_same_input_same_evidence() -> None:
    first = canonical_record_payload(build_canonical_robustness_evidence_v1(_request()))
    second = canonical_record_payload(build_canonical_robustness_evidence_v1(_request()))
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)
    identity = _identity()
    evidence = build_canonical_robustness_evidence_v1(_request(identity))
    expected = derive_robustness_suite_identity_v1(
        experiment_id=str(evidence["experiment_id"]),
        candidate_ref="candidate.ma-crossover.v1",
        robustness_policy_digest=str(evidence["robustness_policy_digest"]),
        observations_digest=str(evidence["observations_digest"]),
        seed=7,
        metric_definition_version=METRIC_DEFINITION_VERSION,
    )
    assert evidence["robustness_suite_identity"] == expected
    validate_canonical_robustness_evidence_v1(evidence)
    assert evidence["experiment_id"] == derive_experiment_id_v1(str(identity["identity_digest"]))
    assert {item["test_id"] for item in evidence["test_results"]} == set(ALL_CATALOG_TESTS)
    assert evidence["aggregate_status"] == "PASS"
    assert evidence["single_metric_promotion"] is False
    assert evidence["promotion_authority"] == "NONE"


def test_changed_critical_input_changes_identity() -> None:
    baseline = build_canonical_robustness_evidence_v1(_request())
    changed_seed_identity = _identity(seed=11)
    changed_seed = build_canonical_robustness_evidence_v1(_request(changed_seed_identity, seed=11))
    changed_dataset_identity = _identity(dataset_digest=_digest("dataset-b"))
    changed_dataset = build_canonical_robustness_evidence_v1(
        _request(
            changed_dataset_identity,
            dataset_ref=_bound_ref(str(changed_dataset_identity["dataset_digest"])),
        )
    )
    changed_obs = build_canonical_robustness_evidence_v1(
        _request(observations=_complete_observations(returns=[0.02, -0.01] * 16))
    )
    identities = {
        baseline["robustness_suite_identity"],
        changed_seed["robustness_suite_identity"],
        changed_dataset["robustness_suite_identity"],
        changed_obs["robustness_suite_identity"],
    }
    assert len(identities) == 4
    assert baseline["integrity"]["content_sha256"] != changed_obs["integrity"]["content_sha256"]


def test_walk_forward_and_cost_and_parameter_and_data_quality_paths() -> None:
    passing = build_canonical_robustness_evidence_v1(_request())
    statuses = _status_by_id(passing)
    assert statuses["WALK_FORWARD"] == "PASS"
    assert statuses["ROLLING_OOS"] == "PASS"
    assert statuses["FEE_STRESS"] == "PASS"
    assert statuses["PARAMETER_SENSITIVITY"] == "PASS"
    assert statuses["MISSING_DATA_STRESS"] == "PASS"
    collapsed = build_canonical_robustness_evidence_v1(
        _request(
            observations=_complete_observations(
                walk_forward_windows=[{"sample_size": 16, "test_sharpe": 0.1, "train_sharpe": 1.2}],
                cost_stress={
                    "baseline": {"sharpe": 1.2},
                    "fee": {"sharpe": 0.1},
                    "funding": {"sharpe": 1.05},
                    "slippage": {"sharpe": 1.02},
                },
                parameter_sensitivity={
                    "center": {"fast": 10.0, "sharpe": 1.2},
                    "points": [
                        {"fast": 10.0, "sharpe": 1.2},
                        {"fast": 12.0, "sharpe": -0.4},
                    ],
                },
                missing_data_stress={"missing_fraction": 0.2, "sharpe": 0.4},
                bad_tick_stress={"bad_tick_count": 3, "max_abs_return": 0.9},
            )
        )
    )
    failed = _status_by_id(collapsed)
    assert failed["WALK_FORWARD"] == "FAIL"
    assert failed["FEE_STRESS"] == "FAIL"
    assert failed["PARAMETER_SENSITIVITY"] == "FAIL"
    assert failed["MISSING_DATA_STRESS"] == "FAIL"
    assert failed["BAD_TICK_STRESS"] == "FAIL"
    assert collapsed["aggregate_status"] == "FAIL"
    assert "WALK_FORWARD" in collapsed["failed_gates"]
    assert "FEE_STRESS" in collapsed["failed_gates"]


def test_missing_required_evidence_is_blocked_not_pass() -> None:
    evidence = build_canonical_robustness_evidence_v1(_request(observations={}))
    statuses = _status_by_id(evidence)
    assert evidence["aggregate_status"] == "BLOCKED"
    assert statuses["SINGLE_METRIC_PROMOTION_GUARD"] == "PASS"
    assert statuses["WALK_FORWARD"] == "BLOCKED_MISSING_CAPABILITY"
    assert statuses["MONTE_CARLO"] == "BLOCKED_MISSING_CAPABILITY"
    assert evidence["evidence_dimensions"]["sortino"]["status"] == "MISSING"
    assert evidence["evidence_dimensions"]["sharpe"]["status"] == "MISSING"
    for test_id in DEFERRED_STATISTICAL_CONTROLS:
        assert statuses[test_id] == "BLOCKED_MISSING_CAPABILITY"
        reason = next(
            item["reason"] for item in evidence["test_results"] if item["test_id"] == test_id
        )
        assert "not implemented" in reason.lower()


def test_single_metric_promotion_is_forbidden() -> None:
    promoted = build_canonical_robustness_evidence_v1(
        _request(promotion_intent="PROMOTE", observations={"metrics": {"sharpe": 4.0}})
    )
    statuses = _status_by_id(promoted)
    assert statuses["SINGLE_METRIC_PROMOTION_GUARD"] == "FAIL"
    assert promoted["single_metric_promotion"] is False
    assert promoted["promotion_authority"] == "NONE"
    assert promoted["robustness_suite_can_promote"] is False
    guard_reason = next(
        item["reason"]
        for item in promoted["test_results"]
        if item["test_id"] == "SINGLE_METRIC_PROMOTION_GUARD"
    )
    assert "BEST_SHARPE" in guard_reason
    assert ROBUSTNESS_SUITE_CAN_PROMOTE is False
    assert SINGLE_METRIC_PROMOTION is False


def test_failure_memory_integration_does_not_overwrite(tmp_path: Path) -> None:
    store = CanonicalFailureMemoryStoreV1(tmp_path / "failure-memory")
    first = build_canonical_robustness_evidence_v1(
        _request(
            observations=_complete_observations(
                cost_stress={
                    "baseline": {"sharpe": 1.2},
                    "fee": {"sharpe": 0.05},
                    "funding": {"sharpe": 1.05},
                    "slippage": {"sharpe": 1.02},
                }
            )
        )
    )
    records = build_failure_records_for_failed_gates_v1(first)
    assert records
    stored = store.append(records[0])
    dest = tmp_path / "failure-memory" / str(stored["failure_record_id"]) / RECORD_FILENAME
    original = dest.read_text(encoding="utf-8")
    store.append(records[0])
    assert dest.read_text(encoding="utf-8") == original
    later = build_canonical_robustness_evidence_v1(
        _request(
            created_at="2026-08-17T20:00:00Z",
            observations=_complete_observations(
                cost_stress={
                    "baseline": {"sharpe": 1.2},
                    "fee": {"sharpe": 0.05},
                    "funding": {"sharpe": 1.05},
                    "slippage": {"sharpe": 1.02},
                }
            ),
        )
    )
    later_records = build_failure_records_for_failed_gates_v1(later)
    stored_later = store.append(later_records[0])
    assert stored_later["failure_record_id"] != stored["failure_record_id"]
    assert dest.read_text(encoding="utf-8") == original
    assert failure_payload(store.get(str(stored["failure_record_id"]))) == failure_payload(stored)
    assert stored["failure_class"] == "REJECTED_COST_SENSITIVITY"
    assert stored["experiment_id"] == first["experiment_id"]


def test_no_runtime_live_or_config_mutation_paths() -> None:
    source = SUITE_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "src.core.peak_config",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "scripts.run_learning_apply_cycle",
        "src.live",
        "src.trading",
        "src.trading.master_v2",
        "src.risk",
        "src.backtest.walkforward",
        "src.backtest.parameter_sensitivity_v1",
        "src.experiments.canonical_experiment_memory_store_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
    }
    assert forbidden_imports.isdisjoint(imported)
    for token in (
        "config/live_overrides",
        "load_config_with_live_overrides",
        "submit_order(",
        "apply_proposals_to_live_overrides",
        "write_live_config(",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "FUNDING_AUTHORIZED",
    ):
        assert token not in source
    evidence = build_canonical_robustness_evidence_v1(_request())
    assert ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY is False
    assert evidence["robustness_suite_has_runtime_authority"] is False
    assert evidence["robustness_suite_can_mutate_live_config"] is False
    assert evidence["robustness_suite_can_submit_order"] is False
    assert evidence["robustness_suite_can_fund"] is False
    assert evidence["robustness_suite_can_authorize_canary"] is False
    assert evidence["self_learning_self_authorizing_separation"] is True
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_robustness_evidence_v1
    )


def test_frozen_evidence_and_bound_refs() -> None:
    identity = _identity()
    evidence = build_canonical_robustness_evidence_v1(_request(identity))
    assert isinstance(evidence, MappingProxyType)
    with pytest.raises(TypeError):
        evidence["aggregate_status"] = "PASS"  # type: ignore[index]
    assert evidence["dataset_ref"]["digest"] == identity["dataset_digest"]
    assert evidence["cost_model_ref"]["digest"] == identity["cost_model_digest"]
    assert evidence["split_policy_ref"]["digest"] == identity["split_policy_digest"]
    assert evidence["risk_policy_ref"]["digest"] == identity["risk_policy_digest"]
    with pytest.raises(RobustnessSuiteValidationError, match="not bound"):
        build_canonical_robustness_evidence_v1(_request(experiment_id=_digest("unrelated")))
    with pytest.raises(RobustnessSuiteValidationError, match="seed must match"):
        build_canonical_robustness_evidence_v1(_request(seed=99))


def test_required_catalog_is_complete_and_deferred_controls_are_not_fake_pass() -> None:
    evidence = build_canonical_robustness_evidence_v1(_request())
    assert tuple(item["test_id"] for item in evidence["test_results"]) == ALL_CATALOG_TESTS
    for test_id in REQUIRED_ROBUSTNESS_TESTS:
        assert _status_by_id(evidence)[test_id] == "PASS"
    for test_id in DEFERRED_STATISTICAL_CONTROLS:
        item = next(row for row in evidence["test_results"] if row["test_id"] == test_id)
        assert item["status"] == "BLOCKED_MISSING_CAPABILITY"
        assert item["status"] != "PASS"
    source = SUITE_MODULE_PATH.read_text(encoding="utf-8")
    assert "def deflated_sharpe" not in source
    assert "def probabilistic_sharpe" not in source
    assert "def white_reality_check" not in source
    assert "def spa_test" not in source

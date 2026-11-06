"""Phase 5 Canonical Comparison SSOT v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_comparison_ssot_v1 import (
    CHAMPION_CHALLENGER_IMPLEMENTED,
    COMPARISON_DIMENSIONS,
    COMPARISON_SSOT_CAN_PROMOTE,
    COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE,
    COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY,
    CanonicalComparisonRankingRequestV1,
    CanonicalComparisonRequestV1,
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
    ComparisonValidationError,
    CompatibilityRuleV1,
    OVERALL_COMPARABLE,
    OVERALL_REJECTED,
    RANKING_REASON_NON_COMPARABLE,
    RANKING_STATUS_RANKED,
    RANKING_STATUS_REJECTED,
    build_canonical_comparison_result_v1,
    canonical_record_payload,
    rank_comparable_candidates_v1,
    validate_canonical_comparison_result_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

ROBUSTNESS_SUITE_VERSION = "canonical_robustness_suite_v1"
METRIC_DEFINITION_VERSION = "canonical_robustness_metrics_v1"

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_comparison_ssot_v1.py"
_GIT_SHA = "e763bf1bf133afab1c3850a6bbaafde6f83e39d2"
_CREATED_AT = "2026-08-17T21:00:00Z"
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


def _compare(
    left: ComparisonCandidateV1 | None = None,
    right: ComparisonCandidateV1 | None = None,
    **overrides: Any,
) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "left": left or _candidate(),
        "right": right or _candidate(_identity(seed=11)),
        "created_at": _CREATED_AT,
        "compatibility_contract": None,
    }
    payload.update(overrides)
    return build_canonical_comparison_result_v1(CanonicalComparisonRequestV1(**payload))


def _status_by_dimension(result: Mapping[str, Any]) -> dict[str, str]:
    return {item["dimension"]: item["status"] for item in result["dimension_results"]}


def test_identical_comparison_inputs_are_comparable() -> None:
    result = _compare()
    validate_canonical_comparison_result_v1(result)
    assert result["overall_comparability"] == OVERALL_COMPARABLE
    assert result["rejection_reasons"] == []
    assert tuple(item["dimension"] for item in result["dimension_results"]) == COMPARISON_DIMENSIONS
    assert set(_status_by_dimension(result).values()) == {"IDENTICAL"}
    assert result["left_experiment_id"] != result["right_experiment_id"]
    left_identity = _identity()
    assert result["left_experiment_id"] == derive_experiment_id_v1(
        str(left_identity["identity_digest"])
    )


@pytest.mark.parametrize(
    ("dimension", "overrides"),
    [
        ("dataset_identity", {"dataset_digest": _digest("dataset-b")}),
        ("split_policy", {"split_policy_digest": _digest("split-b")}),
        ("fee_model", {"fee_model_digest": _digest("fee-b")}),
        ("slippage_model", {"slippage_model_digest": _digest("slippage-b")}),
        ("funding_model", {"funding_model_digest": _digest("funding-b")}),
        ("risk_policy", {"risk_policy_digest": _digest("risk-b")}),
        ("portfolio_constraints", {"portfolio_digest": _digest("portfolio-b")}),
    ],
)
def test_identity_dimension_mismatch_is_rejected(dimension: str, overrides: dict[str, str]) -> None:
    result = _compare(right=_candidate(_identity(seed=11, **overrides)))
    assert result["overall_comparability"] == OVERALL_REJECTED
    assert _status_by_dimension(result)[dimension] == "MISMATCH"
    assert f"{dimension}:MISMATCH" in result["rejection_reasons"]
    for other, status in _status_by_dimension(result).items():
        if other != dimension:
            assert status == "IDENTICAL"


def test_robustness_suite_version_mismatch_is_rejected() -> None:
    result = _compare(
        right=_candidate(
            _identity(seed=11), robustness_suite_version="canonical_robustness_suite_v0"
        )
    )
    assert result["overall_comparability"] == OVERALL_REJECTED
    assert _status_by_dimension(result)["robustness_suite_version"] == "MISMATCH"
    assert "robustness_suite_version:MISMATCH" in result["rejection_reasons"]


def test_metric_definition_mismatch_is_rejected() -> None:
    result = _compare(right=_candidate(_identity(seed=11), metric_definitions="other_metrics_v1"))
    assert result["overall_comparability"] == OVERALL_REJECTED
    assert _status_by_dimension(result)["metric_definitions"] == "MISMATCH"
    assert "metric_definitions:MISMATCH" in result["rejection_reasons"]


def test_time_horizon_mismatch_is_rejected() -> None:
    result = _compare(
        right=_candidate(
            _identity(seed=11),
            time_horizon={"end": "2023-12-31T00:00:00Z", "start": "2021-01-01T00:00:00Z"},
        )
    )
    assert result["overall_comparability"] == OVERALL_REJECTED
    assert _status_by_dimension(result)["time_horizon"] == "MISMATCH"
    assert "time_horizon:MISMATCH" in result["rejection_reasons"]


def test_market_universe_mismatch_is_rejected() -> None:
    result = _compare(right=_candidate(_identity(seed=11), market_universe=("BTC-USDT-SWAP",)))
    assert result["overall_comparability"] == OVERALL_REJECTED
    assert _status_by_dimension(result)["market_universe"] == "MISMATCH"
    assert "market_universe:MISMATCH" in result["rejection_reasons"]


@pytest.mark.parametrize(
    "missing",
    [
        {"robustness_suite_version": None},
        {"metric_definitions": None},
        {"time_horizon": None},
        {"market_universe": None},
        {"robustness_suite_version": "unknown"},
        {"market_universe": "unknown"},
        {"time_horizon": "default"},
        {"metric_definitions": "implicit"},
    ],
)
def test_missing_required_dimension_is_fail_closed_rejected(missing: dict[str, Any]) -> None:
    result = _compare(right=_candidate(_identity(seed=11), **missing))
    assert result["overall_comparability"] == OVERALL_REJECTED
    statuses = _status_by_dimension(result)
    assert "MISSING" in statuses.values()
    assert any(reason.endswith(":MISSING") for reason in result["rejection_reasons"])
    assert result["comparison_ssot_can_rank_non_comparable"] is False


def test_versioned_compatibility_contract_can_make_pair_comparable() -> None:
    left = _candidate()
    right = _candidate(
        _identity(seed=11),
        robustness_suite_version="canonical_robustness_suite_v1_compat",
    )
    rejected = _compare(left=left, right=right)
    assert rejected["overall_comparability"] == OVERALL_REJECTED
    contract = ComparisonCompatibilityContractV1(
        contract_version="canonical_comparison_compatibility.v1",
        rules=(
            CompatibilityRuleV1(
                dimension="robustness_suite_version",
                left_value=ROBUSTNESS_SUITE_VERSION,
                right_value="canonical_robustness_suite_v1_compat",
            ),
        ),
    )
    comparable = _compare(left=left, right=right, compatibility_contract=contract)
    assert comparable["overall_comparability"] == OVERALL_COMPARABLE
    assert _status_by_dimension(comparable)["robustness_suite_version"] == "COMPATIBLE"
    assert comparable["compatibility_contract_version"] == "canonical_comparison_compatibility.v1"
    assert comparable["rejection_reasons"] == []


def test_non_comparable_candidate_cannot_be_ranked() -> None:
    left = _candidate()
    comparable_right = _candidate(_identity(seed=11))
    mismatched = _candidate(_identity(seed=13, dataset_digest=_digest("dataset-b")))
    left_id = derive_experiment_id_v1(str(_identity()["identity_digest"]))
    right_id = derive_experiment_id_v1(str(_identity(seed=11)["identity_digest"]))
    mismatched_id = derive_experiment_id_v1(
        str(_identity(seed=13, dataset_digest=_digest("dataset-b"))["identity_digest"])
    )
    comparable_ranking = rank_comparable_candidates_v1(
        CanonicalComparisonRankingRequestV1(
            candidates=(left, comparable_right),
            scores={left_id: 1.2, right_id: 0.8},
            created_at=_CREATED_AT,
        )
    )
    assert comparable_ranking["ranking_status"] == RANKING_STATUS_RANKED
    assert comparable_ranking["ranked_experiment_ids"] == [left_id, right_id]
    rejected = rank_comparable_candidates_v1(
        CanonicalComparisonRankingRequestV1(
            candidates=(left, comparable_right, mismatched),
            scores={left_id: 1.2, right_id: 0.8, mismatched_id: 9.9},
            created_at=_CREATED_AT,
        )
    )
    assert rejected["ranking_status"] == RANKING_STATUS_REJECTED
    assert rejected["ranking_reason"] == RANKING_REASON_NON_COMPARABLE
    assert rejected["ranked_experiment_ids"] == []
    assert any("dataset_identity:MISMATCH" in reason for reason in rejected["rejection_reasons"])
    assert rejected["comparison_ssot_can_rank_non_comparable"] is False
    assert CHAMPION_CHALLENGER_IMPLEMENTED is False


def test_comparison_result_is_deterministic() -> None:
    first = canonical_record_payload(_compare())
    second = canonical_record_payload(_compare())
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)
    reversed_order_universe = _compare(
        right=_candidate(_identity(seed=11), market_universe=("ETH-USDT-SWAP", "BTC-USDT-SWAP"))
    )
    assert reversed_order_universe["overall_comparability"] == OVERALL_COMPARABLE
    assert _status_by_dimension(reversed_order_universe)["market_universe"] == "IDENTICAL"
    validate_canonical_comparison_result_v1(_compare())


def test_no_runtime_live_or_config_mutation_paths() -> None:
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
        "src.governance.promotion_loop.engine",
        "src.execution",
        "scripts.run_learning_apply_cycle",
        "src.live",
        "src.trading",
        "src.trading.master_v2",
        "src.risk",
        "src.experiments.canonical_robustness_suite_v1",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
        "src.experiments.canonical_experiment_memory_store_v1",
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
        "champion_challenger_select",
        "promote_to_live(",
    ):
        assert token not in source
    result = _compare()
    assert isinstance(result, MappingProxyType)
    with pytest.raises(TypeError):
        result["overall_comparability"] = OVERALL_COMPARABLE  # type: ignore[index]
    assert COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY is False
    assert COMPARISON_SSOT_CAN_PROMOTE is False
    assert COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE is False
    assert result["comparison_ssot_has_runtime_authority"] is False
    assert result["comparison_ssot_can_mutate_live_config"] is False
    assert result["comparison_ssot_can_submit_order"] is False
    assert result["comparison_ssot_can_fund"] is False
    assert result["comparison_ssot_can_authorize_canary"] is False
    assert result["champion_challenger_implemented"] is False
    assert result["self_learning_self_authorizing_separation"] is True
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        build_canonical_comparison_result_v1
    )
    with pytest.raises(ComparisonValidationError, match="not bound"):
        _compare(left=_candidate(experiment_id=_digest("unrelated")))

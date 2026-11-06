"""Phase 6 Canonical Champion-Challenger v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_champion_challenger_v1 import (
    AUTONOMOUS_CHAMPION_SWAP,
    CHAMPION_CHALLENGER_CAN_PROMOTE,
    CHAMPION_CHALLENGER_HAS_RUNTIME_AUTHORITY,
    CHAMPION_CHALLENGER_PRESENT,
    CanonicalChampionChallengerRequestV1,
    DISPOSITION_INFERIOR,
    DISPOSITION_REJECTED_COMPARABILITY,
    DISPOSITION_RESEARCH_PREFERRED,
    DISPOSITION_TIE,
    PROMOTION_AUTHORITY,
    canonical_record_payload_v1,
    evaluate_canonical_champion_challenger_v1,
)
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
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
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_champion_challenger_v1.py"
_GIT_SHA = "e763bf1bf133afab1c3850a6bbaafde6f83e39d2"
_CREATED_AT = "2026-08-17T22:00:00Z"
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


def _evaluate(
    champion: ComparisonCandidateV1 | None = None,
    challengers: tuple[ComparisonCandidateV1, ...] | None = None,
    scores: Mapping[str, float] | None = None,
) -> Mapping[str, Any]:
    champion = champion or _candidate()
    if challengers is None:
        challengers = (_candidate(_identity(seed=11)),)
    if scores is None:
        scores = {
            _experiment_id(): 1.0,
            _experiment_id(_identity(seed=11)): 1.2,
        }
    return evaluate_canonical_champion_challenger_v1(
        CanonicalChampionChallengerRequestV1(
            champion=champion,
            challengers=challengers,
            scores=scores,
            created_at=_CREATED_AT,
        )
    )


def _disposition_by_id(result: Mapping[str, Any]) -> dict[str, str]:
    return {
        item["challenger_experiment_id"]: item["disposition"]
        for item in result["challenger_results"]
    }


def test_champion_and_comparable_challenger_can_be_evaluated() -> None:
    result = _evaluate()
    champion_id = _experiment_id()
    challenger_id = _experiment_id(_identity(seed=11))
    assert result["overall_status"] == "EVALUATION_COMPLETE"
    assert result["champion_experiment_id"] == champion_id
    assert result["challenger_experiment_ids"] == [challenger_id]
    assert champion_id in result["ranked_experiment_ids"]
    assert challenger_id in result["ranked_experiment_ids"]
    assert result["comparison_ssot_version"] == "canonical_comparison_ssot_v1"


def test_multiple_comparable_challengers_are_deterministic() -> None:
    challengers = (
        _candidate(_identity(seed=11)),
        _candidate(_identity(seed=13)),
    )
    scores = {
        _experiment_id(): 1.0,
        _experiment_id(_identity(seed=11)): 0.4,
        _experiment_id(_identity(seed=13)): 0.7,
    }
    first = canonical_record_payload_v1(_evaluate(challengers=challengers, scores=scores))
    second = canonical_record_payload_v1(_evaluate(challengers=challengers, scores=scores))
    assert first == second
    assert first["research_recommendation"] == DISPOSITION_INFERIOR
    assert set(first["ranked_experiment_ids"]) == {
        _experiment_id(),
        _experiment_id(_identity(seed=11)),
        _experiment_id(_identity(seed=13)),
    }


def test_identical_inputs_yield_deterministic_output() -> None:
    first = canonical_record_payload_v1(_evaluate())
    second = canonical_record_payload_v1(_evaluate())
    assert deterministic_json_dumps(first) == deterministic_json_dumps(second)


def test_incomparable_challenger_is_fail_closed_and_not_ranked() -> None:
    mismatched = _candidate(_identity(seed=11, dataset_digest=_digest("dataset-b")))
    result = _evaluate(
        challengers=(mismatched,),
        scores={
            _experiment_id(): 1.0,
            _experiment_id(_identity(seed=11, dataset_digest=_digest("dataset-b"))): 9.9,
        },
    )
    challenger_id = _experiment_id(_identity(seed=11, dataset_digest=_digest("dataset-b")))
    assert result["research_recommendation"] == DISPOSITION_REJECTED_COMPARABILITY
    assert result["ranked_experiment_ids"] == []
    assert _disposition_by_id(result)[challenger_id] == DISPOSITION_REJECTED_COMPARABILITY
    assert result["overall_status"] == "EVALUATION_REJECTED"


def test_mixed_set_does_not_silently_rank_incomparable_challenger() -> None:
    comparable = _candidate(_identity(seed=11))
    incomparable = _candidate(_identity(seed=13, dataset_digest=_digest("dataset-b")))
    comparable_id = _experiment_id(_identity(seed=11))
    incomparable_id = _experiment_id(_identity(seed=13, dataset_digest=_digest("dataset-b")))
    champion_id = _experiment_id()
    result = _evaluate(
        challengers=(comparable, incomparable),
        scores={champion_id: 1.0, comparable_id: 1.4, incomparable_id: 9.9},
    )
    assert incomparable_id not in result["ranked_experiment_ids"]
    assert comparable_id in result["ranked_experiment_ids"]
    assert champion_id in result["ranked_experiment_ids"]
    assert _disposition_by_id(result)[incomparable_id] == DISPOSITION_REJECTED_COMPARABILITY
    assert _disposition_by_id(result)[comparable_id] == DISPOSITION_RESEARCH_PREFERRED
    assert result["research_recommendation"] == DISPOSITION_RESEARCH_PREFERRED


def test_robustness_and_metric_mismatch_is_rejected_by_comparison_ssot() -> None:
    robustness_mismatch = _candidate(
        _identity(seed=11), robustness_suite_version="canonical_robustness_suite_v0"
    )
    metric_mismatch = _candidate(_identity(seed=13), metric_definitions="other_metrics_v1")
    robustness_id = _experiment_id(_identity(seed=11))
    metric_id = _experiment_id(_identity(seed=13))
    robustness_result = _evaluate(
        challengers=(robustness_mismatch,),
        scores={_experiment_id(): 1.0, robustness_id: 2.0},
    )
    metric_result = _evaluate(
        challengers=(metric_mismatch,),
        scores={_experiment_id(): 1.0, metric_id: 2.0},
    )
    assert _disposition_by_id(robustness_result)[robustness_id] == (
        DISPOSITION_REJECTED_COMPARABILITY
    )
    assert (
        "robustness_suite_version:MISMATCH"
        in robustness_result["pair_results"][0]["rejection_reasons"]
    )
    assert _disposition_by_id(metric_result)[metric_id] == DISPOSITION_REJECTED_COMPARABILITY
    assert "metric_definitions:MISMATCH" in metric_result["pair_results"][0]["rejection_reasons"]
    assert robustness_result["ranked_experiment_ids"] == []
    assert metric_result["ranked_experiment_ids"] == []


def test_challenger_can_receive_research_recommendation() -> None:
    result = _evaluate()
    challenger_id = _experiment_id(_identity(seed=11))
    assert _disposition_by_id(result)[challenger_id] == DISPOSITION_RESEARCH_PREFERRED
    assert result["research_recommendation"] == DISPOSITION_RESEARCH_PREFERRED


def test_research_recommendation_does_not_mutate_champion_state() -> None:
    champion_id = _experiment_id()
    result = _evaluate()
    assert result["champion_experiment_id"] == champion_id
    assert result["champion_state"]["champion_experiment_id"] == champion_id
    assert result["champion_state"]["mutated"] is False
    assert result["champion_state"]["swapped"] is False
    assert result["autonomous_champion_swap"] is False
    assert AUTONOMOUS_CHAMPION_SWAP is False


def test_tie_is_inconclusive_not_a_winner() -> None:
    challenger_id = _experiment_id(_identity(seed=11))
    result = _evaluate(scores={_experiment_id(): 1.1, challenger_id: 1.1})
    assert _disposition_by_id(result)[challenger_id] == DISPOSITION_TIE
    assert result["research_recommendation"] == DISPOSITION_TIE
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "BEST_SHARPE" not in source
    assert "BEST_SHARPE => WINNER" not in source


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
        "scripts.run_learning_apply_cycle",
        "src.live",
        "src.trading",
        "src.trading.master_v2",
        "src.risk",
        "src.experiments.canonical_robustness_suite_v1",
        "src.meta.learning_loop.comparison_ssot_v1",
        "src.meta.learning_loop.bridge",
        "src.meta.learning_loop.emitter",
        "src.meta.learning_loop.canary_micro_live_readiness_v1",
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
    ):
        assert token not in source
    result = _evaluate()
    assert isinstance(result, MappingProxyType)
    with pytest.raises(TypeError):
        result["research_recommendation"] = DISPOSITION_RESEARCH_PREFERRED  # type: ignore[index]
    assert CHAMPION_CHALLENGER_PRESENT is True
    assert CHAMPION_CHALLENGER_HAS_RUNTIME_AUTHORITY is False
    assert CHAMPION_CHALLENGER_CAN_PROMOTE is False
    assert PROMOTION_AUTHORITY == "NONE"
    assert result["champion_challenger_can_mutate_live_config"] is False
    assert result["champion_challenger_can_submit_order"] is False
    assert result["champion_challenger_can_fund"] is False
    assert result["champion_challenger_can_increase_risk"] is False
    assert result["champion_challenger_can_increase_leverage"] is False
    assert result["champion_challenger_can_authorize_canary"] is False
    assert result["champion_challenger_can_promote_to_live"] is False
    assert "apply_proposals_to_live_overrides" not in inspect.getsource(
        evaluate_canonical_champion_challenger_v1
    )

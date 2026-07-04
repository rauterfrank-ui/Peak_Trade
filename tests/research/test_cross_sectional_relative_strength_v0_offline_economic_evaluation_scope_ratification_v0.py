"""Contract tests for cross-sectional relative-strength v0 scope definition and binding ratification."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (
    AUTHORITY_EFFECT,
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_EXECUTED,
    ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
    HYPOTHESIS_ID,
    OPERATOR_GO_TOKEN,
    PROHIBITED_ACTIONS,
    REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION,
    RUNTIME_EFFECT,
    RUNTIME_REWIRE_ADMISSIBLE,
    SCOPE_CLASSIFICATION,
    STRATEGY_ID,
    STRATEGY_VERSION,
    TERMINAL_FAILED_BINDING_EXCLUSIONS,
    ValidationVerdictEnum,
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
    validate_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def versioned_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture
def ratification(versioned_binding: dict) -> dict:
    return materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=versioned_binding,
    )


def test_module_constants_fail_closed(ratification: dict) -> None:
    assert ECONOMIC_EVALUATION_AUTHORIZED is False
    assert ECONOMIC_EVALUATION_EXECUTED is False
    assert ECONOMIC_VALIDITY_OFFLINE_GATE_PASS is False
    assert RUNTIME_REWIRE_ADMISSIBLE is False
    assert OPERATOR_GO_TOKEN.startswith("GO_NEW_RESEARCH_SCOPE_")
    assert SCOPE_CLASSIFICATION.endswith("_V0")
    assert ratification["economic_evaluation_authorized"] is False
    assert ratification["no_evaluation_until_scope_ratified"] is True
    assert ratification["no_new_candidate_hold_global_status"] == "ACTIVE"
    assert ratification["no_new_candidate_hold_exception"] is True


def test_strategy_and_hypothesis_binding(ratification: dict) -> None:
    assert ratification["strategy_id"] == STRATEGY_ID
    assert ratification["strategy_version"] == STRATEGY_VERSION
    assert ratification["hypothesis_id"] == HYPOTHESIS_ID
    assert ratification["futures_only"] is True
    assert ratification["bitcoin_direction_allowed"] is False


def test_required_bindings_matrix_complete(ratification: dict) -> None:
    matrix = ratification["required_bindings_matrix"]
    for field in REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION:
        assert field in matrix
        assert matrix[field]["status"] in {"BOUND", "COMPLETE"}
    assert ratification["all_required_bindings_ratified"] is True


def test_terminal_failed_bindings_excluded(ratification: dict) -> None:
    exclusions = set(ratification["terminal_failed_binding_exclusions"])
    assert "cross_sectional_funding_rate_carry/v0" in exclusions
    assert "trend_following/v1" in exclusions
    assert TERMINAL_FAILED_BINDING_EXCLUSIONS == tuple(
        ratification["terminal_failed_binding_exclusions"]
    )


def test_prohibited_actions_include_runtime_and_evaluation(ratification: dict) -> None:
    prohibited = set(PROHIBITED_ACTIONS)
    for action in (
        "BACKTEST_EXECUTION",
        "WALK_FORWARD_EXECUTION",
        "MONTE_CARLO_EXECUTION",
        "STRESS_EXECUTION",
        "RUNTIME",
        "SHADOW",
        "PAPER",
        "TESTNET",
        "ORDERS",
        "FAILED_BINDING_RETRY",
    ):
        assert action in prohibited
    assert ratification["authority_effect"] == AUTHORITY_EFFECT == "NONE"
    assert ratification["runtime_effect"] == RUNTIME_EFFECT == "NONE"


def test_validate_accepts_materialized_ratification(
    ratification: dict, versioned_binding: dict
) -> None:
    result = validate_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        ratification,
        expected_binding=versioned_binding,
    )
    assert result.verdict == ValidationVerdictEnum.ACCEPTED
    assert result.fail_reasons == ()


def test_validate_rejects_authorized_evaluation(ratification: dict) -> None:
    mutated = dict(ratification)
    mutated["economic_evaluation_authorized"] = True
    result = validate_cross_sectional_offline_economic_evaluation_scope_ratification_v0(mutated)
    assert result.verdict == ValidationVerdictEnum.REJECTED
    assert "ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE" in result.fail_reasons

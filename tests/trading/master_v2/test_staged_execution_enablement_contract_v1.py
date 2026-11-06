"""Contract: Staged Execution Enablement v1 validate/evaluate static semantics.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy

import pytest

from trading.master_v2.decision_packet_fixtures_v1 import (
    sample_staged_execution_enablement_input_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    STAGED_EXECUTION_ENABLEMENT_LAYER_VERSION,
    ExecutionStageV1,
    StagedExecutionEnablementDecisionV1,
    StagedExecutionEnablementInputV1,
    evaluate_staged_execution_enablement_v1,
    validate_staged_execution_enablement_input_v1,
)

_EXPECTED_STAGE_VALUES = frozenset(
    {
        "backtest",
        "research",
        "testnet",
        "live_gated",
        "live_authorized",
    }
)
_EXPECTED_REASON_CODES = frozenset({"OK", "BLOCKED"})


def _assert_decision_contract(d: StagedExecutionEnablementDecisionV1) -> None:
    assert d.layer_version == STAGED_EXECUTION_ENABLEMENT_LAYER_VERSION
    assert isinstance(d.can_progress, bool)
    assert isinstance(d.reason_code, str) and d.reason_code
    assert d.reason_code in _EXPECTED_REASON_CODES


def _evaluate_without_mutation(
    inp: StagedExecutionEnablementInputV1,
) -> StagedExecutionEnablementDecisionV1:
    original = copy.deepcopy(inp)
    d = evaluate_staged_execution_enablement_v1(inp)
    assert inp == original
    return d


def test_execution_stage_v1_enum_values_contract() -> None:
    values = {s.value for s in ExecutionStageV1}
    assert values == _EXPECTED_STAGE_VALUES
    for stage in ExecutionStageV1:
        assert isinstance(stage, ExecutionStageV1)
        assert stage.value == stage


def test_validate_valid_baseline_input_passes() -> None:
    inp = sample_staged_execution_enablement_input_v1()
    validate_staged_execution_enablement_input_v1(inp)


def test_evaluate_valid_baseline_can_progress_true() -> None:
    inp = sample_staged_execution_enablement_input_v1()
    d = _evaluate_without_mutation(inp)
    _assert_decision_contract(d)
    assert inp.current_stage is ExecutionStageV1.RESEARCH
    assert inp.requested_stage is ExecutionStageV1.BACKTEST
    assert d.can_progress is True
    assert d.reason_code == "OK"


def test_evaluate_same_stage_not_progressable() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.BACKTEST,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    d = _evaluate_without_mutation(inp)
    _assert_decision_contract(d)
    assert d.can_progress is False
    assert d.reason_code == "BLOCKED"


def test_evaluate_progressable_different_stages() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    d = _evaluate_without_mutation(inp)
    _assert_decision_contract(d)
    assert d.can_progress is True
    assert d.reason_code == "OK"


def test_evaluate_live_gated_to_live_authorized_without_ack_blocked() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.LIVE_GATED,
        requested_stage=ExecutionStageV1.LIVE_AUTHORIZED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    d = _evaluate_without_mutation(inp)
    _assert_decision_contract(d)
    assert d.can_progress is False
    assert d.reason_code == "BLOCKED"


def test_evaluate_live_gated_to_live_authorized_with_ack_eligible_only() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.LIVE_GATED,
        requested_stage=ExecutionStageV1.LIVE_AUTHORIZED,
        safety_decision_allowed=True,
        live_authority_acknowledged=True,
    )
    d = _evaluate_without_mutation(inp)
    _assert_decision_contract(d)
    assert d.can_progress is True
    assert d.reason_code == "OK"


def test_evaluate_safety_decision_allowed_false_blocks_progress() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=False,
    )
    d = _evaluate_without_mutation(inp)
    _assert_decision_contract(d)
    assert d.can_progress is False
    assert d.reason_code == "OK"


def test_validate_invalid_current_stage_type_raises() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    bad = copy.copy(inp)
    object.__setattr__(bad, "current_stage", "research")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="stages must be ExecutionStageV1"):
        validate_staged_execution_enablement_input_v1(bad)


def test_validate_invalid_requested_stage_type_raises() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    bad = copy.copy(inp)
    object.__setattr__(bad, "requested_stage", 42)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="stages must be ExecutionStageV1"):
        validate_staged_execution_enablement_input_v1(bad)


def test_validate_invalid_safety_decision_allowed_raises() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    bad = copy.copy(inp)
    object.__setattr__(bad, "safety_decision_allowed", None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="safety_decision_allowed must be bool"):
        validate_staged_execution_enablement_input_v1(bad)


def test_validate_invalid_live_authority_acknowledged_raises() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.LIVE_GATED,
        requested_stage=ExecutionStageV1.LIVE_AUTHORIZED,
        safety_decision_allowed=True,
        live_authority_acknowledged=True,
    )
    bad = copy.copy(inp)
    object.__setattr__(bad, "live_authority_acknowledged", "yes")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="live_authority_acknowledged must be bool"):
        validate_staged_execution_enablement_input_v1(bad)


def test_evaluate_fail_closed_on_invalid_input() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    bad = copy.copy(inp)
    object.__setattr__(bad, "current_stage", None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="stages must be ExecutionStageV1"):
        evaluate_staged_execution_enablement_v1(bad)


def test_reason_code_stable_for_blocked_and_ok_paths() -> None:
    blocked = _evaluate_without_mutation(
        StagedExecutionEnablementInputV1(
            current_stage=ExecutionStageV1.TESTNET,
            requested_stage=ExecutionStageV1.TESTNET,
            safety_decision_allowed=True,
        )
    )
    ok = _evaluate_without_mutation(
        StagedExecutionEnablementInputV1(
            current_stage=ExecutionStageV1.TESTNET,
            requested_stage=ExecutionStageV1.LIVE_GATED,
            safety_decision_allowed=True,
        )
    )
    assert blocked.reason_code == "BLOCKED"
    assert ok.reason_code == "OK"


def test_deterministic_evaluation_repeat() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.TESTNET,
        safety_decision_allowed=True,
    )
    first = evaluate_staged_execution_enablement_v1(inp)
    second = evaluate_staged_execution_enablement_v1(inp)
    assert first == second


def test_non_authorizing_can_progress_true_is_static_only() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
    )
    d = _evaluate_without_mutation(inp)
    assert d.can_progress is True
    assert isinstance(d, StagedExecutionEnablementDecisionV1)
    assert not hasattr(d, "authorized")
    assert not hasattr(d, "execution_started")
    assert not hasattr(d, "armed")
    assert not hasattr(d, "promoted")

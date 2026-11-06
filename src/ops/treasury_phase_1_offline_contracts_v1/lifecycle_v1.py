"""Treasury Phase-1 typed lifecycle. OUTCOME_UNKNOWN is not failure and not retryable."""

from __future__ import annotations

from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    OUTCOME_UNKNOWN_IS_FAILURE,
    OUTCOME_UNKNOWN_SAFE_TO_RETRY,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasuryLifecycleError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    MUTATION_OPERATION_KINDS,
    TreasuryIntentRecordV1,
    TreasuryLifecycleStateV1,
    TreasuryLifecycleTransitionV1,
    TreasuryOperationKindV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.validators_v1 import (
    validate_lifecycle_state_v1,
    validate_timezone_aware_timestamp_v1,
)

_S = TreasuryLifecycleStateV1

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    _S.INTENT_RECORDED.value: frozenset(
        {
            _S.REMOTE_ATTEMPT_RECORDED.value,
            _S.RECONCILIATION_REQUIRED.value,
            _S.ECONOMIC_EFFECT_RECONCILED.value,
        }
    ),
    _S.REMOTE_ATTEMPT_RECORDED.value: frozenset(
        {
            _S.REMOTE_PENDING.value,
            _S.REMOTE_TERMINAL_SUCCESS.value,
            _S.REMOTE_TERMINAL_FAILURE.value,
            _S.OUTCOME_UNKNOWN.value,
            _S.RECONCILIATION_REQUIRED.value,
        }
    ),
    _S.REMOTE_PENDING.value: frozenset(
        {
            _S.REMOTE_TERMINAL_SUCCESS.value,
            _S.REMOTE_TERMINAL_FAILURE.value,
            _S.OUTCOME_UNKNOWN.value,
            _S.RECONCILIATION_REQUIRED.value,
        }
    ),
    _S.REMOTE_TERMINAL_SUCCESS.value: frozenset(
        {
            _S.RECONCILIATION_REQUIRED.value,
            _S.ECONOMIC_EFFECT_RECONCILED.value,
        }
    ),
    _S.REMOTE_TERMINAL_FAILURE.value: frozenset(
        {
            _S.RECONCILIATION_REQUIRED.value,
            _S.ECONOMIC_EFFECT_RECONCILED.value,
        }
    ),
    _S.OUTCOME_UNKNOWN.value: frozenset(
        {
            _S.REMOTE_PENDING.value,
            _S.REMOTE_TERMINAL_SUCCESS.value,
            _S.REMOTE_TERMINAL_FAILURE.value,
            _S.RECONCILIATION_REQUIRED.value,
            _S.OUTCOME_UNKNOWN.value,
        }
    ),
    _S.RECONCILIATION_REQUIRED.value: frozenset(
        {
            _S.ECONOMIC_EFFECT_RECONCILED.value,
            _S.OUTCOME_UNKNOWN.value,
            _S.RECONCILIATION_REQUIRED.value,
        }
    ),
    _S.ECONOMIC_EFFECT_RECONCILED.value: frozenset(),
}

FORBIDDEN_RETRY_FROM = frozenset(
    {
        _S.OUTCOME_UNKNOWN.value,
        _S.REMOTE_ATTEMPT_RECORDED.value,
        _S.REMOTE_PENDING.value,
        _S.REMOTE_TERMINAL_SUCCESS.value,
        _S.ECONOMIC_EFFECT_RECONCILED.value,
        _S.RECONCILIATION_REQUIRED.value,
    }
)


def allowed_transitions_v1() -> dict[str, frozenset[str]]:
    return {key: frozenset(value) for key, value in ALLOWED_TRANSITIONS.items()}


def assert_transition_allowed_v1(
    *,
    record: TreasuryIntentRecordV1,
    transition: TreasuryLifecycleTransitionV1,
) -> None:
    from_state = validate_lifecycle_state_v1(transition.from_state)
    to_state = validate_lifecycle_state_v1(transition.to_state)
    if from_state != record.lifecycle_state:
        raise TreasuryLifecycleError("TRANSITION_FROM_STATE_MISMATCH")
    if transition.intent_id != record.intent_id:
        raise TreasuryLifecycleError("TRANSITION_INTENT_MISMATCH")
    allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise TreasuryLifecycleError("ILLEGAL_LIFECYCLE_TRANSITION")
    if to_state == _S.REMOTE_ATTEMPT_RECORDED.value:
        if record.operation_kind not in MUTATION_OPERATION_KINDS:
            raise TreasuryLifecycleError("NON_MUTATION_CANNOT_REMOTE_ATTEMPT")
        if record.durable is not True:
            raise TreasuryLifecycleError("DURABLE_INTENT_REQUIRED_BEFORE_REMOTE")
    if from_state == _S.OUTCOME_UNKNOWN.value and to_state == _S.REMOTE_ATTEMPT_RECORDED.value:
        raise TreasuryLifecycleError("OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY")
    if to_state == _S.REMOTE_ATTEMPT_RECORDED.value and from_state in FORBIDDEN_RETRY_FROM:
        raise TreasuryLifecycleError("RETRY_FROM_BLOCKING_STATE_DENIED")
    if from_state == _S.ECONOMIC_EFFECT_RECONCILED.value:
        raise TreasuryLifecycleError("TERMINAL_ECONOMIC_EFFECT_MONOTONIC")
    if (
        from_state == _S.REMOTE_TERMINAL_SUCCESS.value
        and to_state == _S.REMOTE_TERMINAL_SUCCESS.value
    ):
        raise TreasuryLifecycleError("TERMINAL_SUCCESS_NOT_REAPPLICABLE")
    if record.operation_kind == TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value:
        if to_state in {
            _S.REMOTE_ATTEMPT_RECORDED.value,
            _S.REMOTE_PENDING.value,
            _S.REMOTE_TERMINAL_SUCCESS.value,
            _S.REMOTE_TERMINAL_FAILURE.value,
        }:
            raise TreasuryLifecycleError("DEPOSIT_OBSERVATION_NOT_MUTATION_LIFECYCLE")
    if record.operation_kind == TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value:
        if to_state in {_S.REMOTE_TERMINAL_SUCCESS.value, _S.ECONOMIC_EFFECT_RECONCILED.value}:
            raise TreasuryLifecycleError("DEPOSIT_ADDRESS_RETRIEVAL_NOT_ECONOMIC_EFFECT")
    confirmation = transition.confirmation_fingerprint
    if confirmation != "" and record.destination_fingerprint != "":
        if confirmation != record.destination_fingerprint:
            raise TreasuryLifecycleError("DESTINATION_CONFIRMATION_MISMATCH")
    validate_timezone_aware_timestamp_v1(
        transition.local_observation_at, field="LOCAL_OBSERVATION_AT"
    )
    if OUTCOME_UNKNOWN_IS_FAILURE is True or OUTCOME_UNKNOWN_SAFE_TO_RETRY is True:
        raise TreasuryLifecycleError("OUTCOME_UNKNOWN_SEMANTICS_DRIFT")


def reconciliation_status_for_state_v1(state: str) -> str:
    if state == _S.ECONOMIC_EFFECT_RECONCILED.value:
        return "RECONCILED_NOT_RISK_ADMISSIBLE"
    if state == _S.OUTCOME_UNKNOWN.value:
        return "UNKNOWN_NOT_FAILED"
    if state == _S.RECONCILIATION_REQUIRED.value:
        return "RECONCILIATION_REQUIRED"
    if state in {
        _S.REMOTE_ATTEMPT_RECORDED.value,
        _S.REMOTE_PENDING.value,
        _S.REMOTE_TERMINAL_SUCCESS.value,
        _S.REMOTE_TERMINAL_FAILURE.value,
    }:
        return "UNRECONCILED"
    return "NOT_STARTED"

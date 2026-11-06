"""DDO A1 durability-to-admission and replay binding v1.

Binds EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION to a named
fail-closed admission state and binds persist/replay ambiguity so that
capture ok, UNKNOWN durability, and IDEMPOTENT_REPLAY cannot be read as
A1-dependent mutation permission.

Reuses reject_a1_dependent_mutation_on_unproven_durability_v1 as the sole
admission owner. Does not authorize A1 runtime, unattended operation,
trading, execution, live, crash durability, or a new storage owner.
Does not introduce an automatic retry loop. Does not manufacture
durability_proven=True.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping, NoReturn

from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    AMBIGUOUS_RETRY_ALLOWED,
    CRASH_DURABILITY_FULLY_PROVEN,
    CURRENT_STAGE_DURABILITY_FAILURE_POLICY,
    DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY,
    DIRECTORY_FSYNC_STATUS,
    FILE_FSYNC_STATUS,
    HOST_CRASH_DURABILITY,
    NEW_STORAGE_AUTHORITY_CREATED as POLICY_NEW_STORAGE_AUTHORITY_CREATED,
    POWER_LOSS_DURABILITY,
    PRODUCTIVE_RETURN_VALUE_UNCHANGED as POLICY_PRODUCTIVE_RETURN_VALUE_UNCHANGED,
    RUNTIME_AUTHORIZATION_ELIGIBLE as POLICY_RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED as POLICY_RUNTIME_AUTHORIZED,
    UNATTENDED_OPERATION_STARTED as POLICY_UNATTENDED_OPERATION_STARTED,
    UNKNOWN_PRESERVED,
    DdoA1DurabilityFailurePolicyError,
    DdoA1DurabilityFailurePolicyResultV1,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
    bind_a1_durability_failure_policy_v1,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    FAILURE_CLASS_DUPLICATE_CONFLICT,
    FAILURE_CLASS_UNKNOWN_IO,
    OPERATION_DIRECTORY_FSYNC,
    OPERATION_DURABLE_APPEND,
    OPERATION_IDEMPOTENT_REPLAY,
    DdoDuplicateConflictError,
    DdoDurabilityWriteError,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendResultV0

SLICE_ID: Final[str] = "PEAK_TRADE_DDO_A1_DURABILITY_TO_ADMISSION_AND_REPLAY_BINDING_V1"
IMPLEMENTATION_AUTHORIZATION_SOURCE: Final[str] = (
    "PEAK_TRADE_OWNER_GO_DDO_A1_DURABILITY_TO_ADMISSION_AND_REPLAY_BINDING_V1"
)
RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE: Final[str] = "NONE"
IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION: Final[bool] = False

ADMISSION_OWNER_NAME: Final[str] = "reject_a1_dependent_mutation_on_unproven_durability_v1"
ADMISSION_OWNER = reject_a1_dependent_mutation_on_unproven_durability_v1
ADMISSION_BINDING_STATUS: Final[str] = "BOUND_FAIL_CLOSED"
REPLAY_AMBIGUITY_BINDING_STATUS: Final[str] = "BOUND_WITHOUT_AUTOMATIC_RETRY"
NEW_ADMISSION_AUTHORITY_CREATED: Final[bool] = False
NEW_STORAGE_AUTHORITY_CREATED: Final[bool] = False
EXISTING_STORAGE_OWNER: Final[str] = "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"

EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION: Final[str] = (
    "BOUND_FAIL_CLOSED_ADMISSION_NOT_A_CURRENT_TRADING_PRECONDITION_"
    "NOT_RUNTIME_AUTHORIZATION_NOT_CRASH_DURABILITY_PROOF_NOT_LIVE_ADMISSION"
)
EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION_IS_TRADING_PRECONDITION: Final[bool] = False
EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION_IS_RUNTIME_AUTHORIZATION: Final[bool] = False
EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION_IS_CRASH_DURABILITY_PROOF: Final[bool] = False
EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION_IS_LIVE_ADMISSION: Final[bool] = False

DEPENDENT_MUTATION_ADMISSION_STATE: Final[str] = (
    "REJECTED_FAIL_CLOSED_UNPROVEN_OR_UNKNOWN_DURABILITY"
)
CAPTURE_OK_EQUALS_ADMISSION: Final[bool] = False
CURRENT_STAGE_CAPTURE_FAIL_OPEN: Final[bool] = True
CURRENT_STAGE_CAPTURE_IS_TRADING_ADMISSION: Final[bool] = False
CURRENT_STAGE_CAPTURE_IS_RUNTIME_ADMISSION: Final[bool] = False

PERSIST_WRITE_ACCEPTED: Final[str] = "APPENDED"
IDEMPOTENT_REPLAY: Final[str] = "IDEMPOTENT_REPLAY"
DUPLICATE_CONFLICT: Final[str] = "DUPLICATE_CONFLICT"
DURABILITY_UNKNOWN: Final[str] = "DURABILITY_UNKNOWN"
DURABILITY_FAILURE: Final[str] = "DURABILITY_FAILURE"
DEPENDENT_MUTATION_ADMISSION: Final[str] = "DEPENDENT_MUTATION_ADMISSION"
MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE: Final[str] = "MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE"

IDEMPOTENT_REPLAY_EQUALS_CRASH_DURABILITY_PROOF: Final[bool] = False
IDEMPOTENT_REPLAY_EQUALS_DEPENDENT_MUTATION_ADMISSION: Final[bool] = False
IDEMPOTENT_REPLAY_SEMANTICS: Final[str] = (
    "SAME_RECORD_ID_SAME_CONTENT_NO_SECOND_LEDGER_ROW_NOT_CRASH_PROOF_NOT_ADMISSION"
)
DUPLICATE_CONFLICT_SEMANTICS: Final[str] = (
    "SAME_RECORD_ID_DIFFERENT_CONTENT_FAIL_CLOSED_NOT_ADMISSION"
)
AUTOMATIC_RETRY_LOOP_ADDED: Final[bool] = False
RETRY_ALLOWED_IS_SKIP_GATE: Final[bool] = False

FILE_FSYNC_POLICY: Final[str] = "PRESENT_FAILURE_FORBIDS_DEPENDENT_MUTATION"
DIRECTORY_FSYNC_POLICY: Final[str] = DIRECTORY_FSYNC_STATUS
HOST_CRASH_DURABILITY_BOUND: Final[str] = HOST_CRASH_DURABILITY
POWER_LOSS_DURABILITY_BOUND: Final[str] = POWER_LOSS_DURABILITY

IMPLEMENTATION_COMPLETE: Final[bool] = True
RUNTIME_AUTHORIZATION_ELIGIBLE: Final[bool] = False
RUNTIME_AUTHORIZED: Final[bool] = False
OPERATION_STARTED: Final[bool] = False
UNATTENDED_OPERATION_STARTED: Final[bool] = False
NEXT_OWNER_GO_REQUIRED: Final[bool] = True
NEXT_DDO_STEP: Final[str] = (
    "OWNER_GO_REQUIRED_SEPARATE_SCOPED_DDO_A1_CONTINUATION_NOT_AUTHORIZED_BY_THIS_PERSIST"
)

DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY: Final[bool] = False
DDO_LEARNING_PRODUCTIVE_AUTHORITY: Final[bool] = False
TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE: Final[bool] = False
PRODUCTIVE_RETURN_VALUE_UNCHANGED: Final[bool] = True
A1_TRADING_AUTHORITY: Final[bool] = False
A1_EXECUTION_AUTHORITY: Final[bool] = False
A1_LEARNING_AUTHORITY: Final[bool] = False
A1_UNATTENDED_AUTHORITY: Final[bool] = False
A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED: Final[bool] = False
TRADING_AUTHORITY_CHANGED: Final[bool] = False
EXECUTION_AUTHORITY_CHANGED: Final[bool] = False
LIVE_AUTHORITY_CHANGED: Final[bool] = False

assert AUTHORITY_OWNER == "NONE"
assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
assert SECOND_TRADING_AUTHORITY_CREATED is False
assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert RUNTIME_AUTHORIZED is False
assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
assert CRASH_DURABILITY_FULLY_PROVEN is False
assert NEW_STORAGE_AUTHORITY_CREATED is False
assert NEW_ADMISSION_AUTHORITY_CREATED is False
assert AMBIGUOUS_RETRY_ALLOWED is False
assert UNKNOWN_PRESERVED is True
assert AUTOMATIC_RETRY_LOOP_ADDED is False
assert CAPTURE_OK_EQUALS_ADMISSION is False
assert CURRENT_STAGE_CAPTURE_FAIL_OPEN is True
assert POLICY_RUNTIME_AUTHORIZED is False
assert POLICY_RUNTIME_AUTHORIZATION_ELIGIBLE is False
assert POLICY_UNATTENDED_OPERATION_STARTED is False
assert POLICY_NEW_STORAGE_AUTHORITY_CREATED is False
assert POLICY_PRODUCTIVE_RETURN_VALUE_UNCHANGED is True
assert ADMISSION_OWNER is reject_a1_dependent_mutation_on_unproven_durability_v1
assert PERSIST_WRITE_ACCEPTED == "APPENDED"
assert IDEMPOTENT_REPLAY == "IDEMPOTENT_REPLAY"
assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True


class DdoA1DurabilityToAdmissionAndReplayBindingError(Exception):
    """Fail-closed A1 admission/replay binding error. Not trading authority."""

    error_code = "DDO_A1_DURABILITY_TO_ADMISSION_AND_REPLAY_BINDING_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


def _durability_result_for(
    *,
    policy_result: DdoA1DurabilityFailurePolicyResultV1 | None,
    persist_error: BaseException | None,
) -> str:
    if policy_result is None and persist_error is None:
        return MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE
    if policy_result is not None:
        if policy_result.durability_proven is True:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if policy_result.failure_class == FAILURE_CLASS_UNKNOWN_IO:
            return DURABILITY_UNKNOWN
        if policy_result.operation == OPERATION_DIRECTORY_FSYNC:
            return DURABILITY_UNKNOWN
        if policy_result.durability_proven is None:
            return DURABILITY_UNKNOWN
        return DURABILITY_FAILURE
    if isinstance(persist_error, DdoDurabilityWriteError):
        if persist_error.failure_class == FAILURE_CLASS_UNKNOWN_IO:
            return DURABILITY_UNKNOWN
        if persist_error.operation == OPERATION_DIRECTORY_FSYNC:
            return DURABILITY_UNKNOWN
        return DURABILITY_FAILURE
    if persist_error is not None:
        return DURABILITY_UNKNOWN
    return MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE


def _persist_result_for(
    *,
    append_result: AppendResultV0 | None,
    persist_error: BaseException | None,
) -> str | None:
    if isinstance(persist_error, DdoDuplicateConflictError):
        return DUPLICATE_CONFLICT
    if isinstance(persist_error, DdoDurabilityWriteError):
        if persist_error.failure_class == FAILURE_CLASS_DUPLICATE_CONFLICT:
            return DUPLICATE_CONFLICT
        return None
    if persist_error is not None:
        return None
    if append_result is None:
        return None
    if append_result.status == IDEMPOTENT_REPLAY:
        return IDEMPOTENT_REPLAY
    if append_result.status == PERSIST_WRITE_ACCEPTED:
        return PERSIST_WRITE_ACCEPTED
    raise DdoA1DurabilityToAdmissionAndReplayBindingError(
        "A1_UNKNOWN_PERSIST_STATUS_FAIL_CLOSED",
        "A1_UNKNOWN_PERSIST_STATUS_FAIL_CLOSED",
    )


@dataclass(frozen=True)
class DdoA1PersistAttemptClassificationV1:
    """Persist/replay classification. Never grants dependent mutation admission."""

    persist_result: str | None
    durability_result: str
    dependent_mutation_admission: str
    durability_proven: bool | None
    crash_durability_fully_proven: bool
    retry_allowed: bool | None
    automatic_retry_loop_invoked: bool
    capture_ok_equals_admission: bool
    idempotent_replay_equals_crash_durability_proof: bool
    unknown_preserved: bool
    record_id: str | None
    operation: str | None

    def __post_init__(self) -> None:
        if self.dependent_mutation_admission != DEPENDENT_MUTATION_ADMISSION_STATE:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if self.durability_proven is True:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.crash_durability_fully_proven:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.automatic_retry_loop_invoked:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_AUTOMATIC_RETRY_LOOP_FORBIDDEN",
                "A1_AUTOMATIC_RETRY_LOOP_FORBIDDEN",
            )
        if self.capture_ok_equals_admission:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CAPTURE_OK_IS_NOT_ADMISSION",
                "A1_CAPTURE_OK_IS_NOT_ADMISSION",
            )
        if self.idempotent_replay_equals_crash_durability_proof:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_IDEMPOTENT_REPLAY_IS_NOT_CRASH_PROOF",
                "A1_IDEMPOTENT_REPLAY_IS_NOT_CRASH_PROOF",
            )
        if self.persist_result == IDEMPOTENT_REPLAY and self.durability_proven is True:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_IDEMPOTENT_REPLAY_IS_NOT_CRASH_PROOF",
                "A1_IDEMPOTENT_REPLAY_IS_NOT_CRASH_PROOF",
            )
        if self.durability_proven is None and not self.unknown_preserved:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_UNKNOWN_MUST_BE_PRESERVED",
                "A1_UNKNOWN_MUST_BE_PRESERVED",
            )
        if self.retry_allowed is True and AMBIGUOUS_RETRY_ALLOWED is False:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_AMBIGUOUS_RETRY_FORBIDDEN",
                "A1_AMBIGUOUS_RETRY_FORBIDDEN",
            )

    def as_observability(self) -> dict[str, Any]:
        return {
            "a1_persist_result": self.persist_result,
            "a1_durability_result": self.durability_result,
            "a1_dependent_mutation_admission": self.dependent_mutation_admission,
            "a1_admission_durability_proven": self.durability_proven,
            "a1_admission_crash_durability_fully_proven": self.crash_durability_fully_proven,
            "a1_admission_retry_allowed": self.retry_allowed,
            "a1_automatic_retry_loop_invoked": self.automatic_retry_loop_invoked,
            "a1_capture_ok_equals_admission": self.capture_ok_equals_admission,
            "a1_idempotent_replay_equals_crash_durability_proof": (
                self.idempotent_replay_equals_crash_durability_proof
            ),
            "a1_admission_unknown_preserved": self.unknown_preserved,
            "a1_admission_record_id": self.record_id,
            "a1_admission_operation": self.operation,
        }


@dataclass(frozen=True)
class DdoA1DependentMutationAdmissionResultV1:
    """Named fail-closed A1-adjacent mutation-admission result. Never admits."""

    admitted: bool
    admission_state: str
    admission_owner: str
    evidence_must_be_durable_before_dependent_mutation: str
    durability_proven: bool | None
    missing_policy_result: bool
    capture_ok: bool | None
    persist_result: str | None
    durability_result: str
    current_stage_capture_fail_open: bool
    runtime_authorized: bool
    crash_durability_fully_proven: bool
    reason_code: str

    def __post_init__(self) -> None:
        if self.admitted:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if self.admission_state != DEPENDENT_MUTATION_ADMISSION_STATE:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if self.admission_owner != ADMISSION_OWNER_NAME:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_SECOND_ADMISSION_AUTHORITY_FORBIDDEN",
                "A1_SECOND_ADMISSION_AUTHORITY_FORBIDDEN",
            )
        if (
            self.evidence_must_be_durable_before_dependent_mutation
            != EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION
        ):
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_EVIDENCE_MUST_BE_DURABLE_STATE_INVALID",
                "A1_EVIDENCE_MUST_BE_DURABLE_STATE_INVALID",
            )
        if self.durability_proven is True:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.crash_durability_fully_proven or self.runtime_authorized:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )
        if not self.current_stage_capture_fail_open:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CURRENT_STAGE_CAPTURE_MUST_REMAIN_FAIL_OPEN",
                "A1_CURRENT_STAGE_CAPTURE_MUST_REMAIN_FAIL_OPEN",
            )
        if self.capture_ok is True and self.admitted:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CAPTURE_OK_IS_NOT_ADMISSION",
                "A1_CAPTURE_OK_IS_NOT_ADMISSION",
            )

    def as_observability(self) -> dict[str, Any]:
        return {
            "a1_dependent_mutation_admitted": self.admitted,
            "a1_dependent_mutation_admission_state": self.admission_state,
            "a1_dependent_mutation_admission_owner": self.admission_owner,
            "a1_evidence_must_be_durable_before_dependent_mutation": (
                self.evidence_must_be_durable_before_dependent_mutation
            ),
            "a1_admission_eval_durability_proven": self.durability_proven,
            "a1_admission_missing_policy_result": self.missing_policy_result,
            "a1_admission_capture_ok": self.capture_ok,
            "a1_admission_persist_result": self.persist_result,
            "a1_admission_durability_result": self.durability_result,
            "a1_admission_current_stage_capture_fail_open": (self.current_stage_capture_fail_open),
            "a1_admission_eval_runtime_authorized": self.runtime_authorized,
            "a1_admission_eval_crash_durability_fully_proven": (self.crash_durability_fully_proven),
            "a1_admission_eval_reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class DdoA1DurabilityToAdmissionAndReplayBindingV1:
    """Canonical A1 admission/replay binding. Never self-activating."""

    slice_id: str = SLICE_ID
    implementation_complete: bool = True
    admission_binding_status: str = ADMISSION_BINDING_STATUS
    replay_ambiguity_binding_status: str = REPLAY_AMBIGUITY_BINDING_STATUS
    admission_owner_name: str = ADMISSION_OWNER_NAME
    new_admission_authority_created: bool = False
    evidence_must_be_durable_before_dependent_mutation: str = (
        EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION
    )
    current_stage_capture_fail_open: bool = True
    capture_ok_equals_admission: bool = False
    automatic_retry_loop_added: bool = False
    ambiguous_retry_allowed: bool = False
    unknown_preserved: bool = True
    runtime_authorization_eligible: bool = False
    runtime_authorized: bool = False
    operation_started: bool = False
    unattended_operation_started: bool = False
    implementation_go_is_runtime_authorization: bool = False
    crash_durability_fully_proven: bool = False
    new_storage_authority_created: bool = False
    dependent_mutation_on_unproven_durability: str = DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY
    next_owner_go_required: bool = True
    implementation_authorization_source: str = IMPLEMENTATION_AUTHORIZATION_SOURCE
    runtime_operational_authorization_source: str = RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE
    existing_storage_owner: str = EXISTING_STORAGE_OWNER
    file_fsync_status: str = FILE_FSYNC_STATUS
    file_fsync_policy: str = FILE_FSYNC_POLICY
    directory_fsync_status: str = DIRECTORY_FSYNC_STATUS
    directory_fsync_policy: str = DIRECTORY_FSYNC_POLICY
    host_crash_durability: str = HOST_CRASH_DURABILITY
    power_loss_durability: str = POWER_LOSS_DURABILITY
    a1_durability_failure_policy: str = A1_DURABILITY_FAILURE_POLICY
    current_stage_durability_failure_policy: str = CURRENT_STAGE_DURABILITY_FAILURE_POLICY
    next_ddo_step: str = NEXT_DDO_STEP

    def __post_init__(self) -> None:
        if self.slice_id != SLICE_ID:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_SLICE_ID_INVALID",
                "A1_SLICE_ID_INVALID",
            )
        if not self.implementation_complete:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
            )
        if self.admission_binding_status != ADMISSION_BINDING_STATUS:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_ADMISSION_BINDING_MUST_REMAIN_FAIL_CLOSED",
                "A1_ADMISSION_BINDING_MUST_REMAIN_FAIL_CLOSED",
            )
        if self.replay_ambiguity_binding_status != REPLAY_AMBIGUITY_BINDING_STATUS:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_REPLAY_BINDING_MUST_REMAIN_WITHOUT_AUTOMATIC_RETRY",
                "A1_REPLAY_BINDING_MUST_REMAIN_WITHOUT_AUTOMATIC_RETRY",
            )
        if self.admission_owner_name != ADMISSION_OWNER_NAME:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_SECOND_ADMISSION_AUTHORITY_FORBIDDEN",
                "A1_SECOND_ADMISSION_AUTHORITY_FORBIDDEN",
            )
        if (
            self.evidence_must_be_durable_before_dependent_mutation
            != EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION
        ):
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_EVIDENCE_MUST_BE_DURABLE_STATE_INVALID",
                "A1_EVIDENCE_MUST_BE_DURABLE_STATE_INVALID",
            )
        if self.evidence_must_be_durable_before_dependent_mutation.startswith("UNBOUND"):
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_EVIDENCE_MUST_BE_DURABLE_STATE_INVALID",
                "A1_EVIDENCE_MUST_BE_DURABLE_STATE_INVALID",
            )
        forbidden_true = (
            self.new_admission_authority_created,
            self.capture_ok_equals_admission,
            self.automatic_retry_loop_added,
            self.ambiguous_retry_allowed,
            self.runtime_authorization_eligible,
            self.runtime_authorized,
            self.operation_started,
            self.unattended_operation_started,
            self.implementation_go_is_runtime_authorization,
            self.crash_durability_fully_proven,
            self.new_storage_authority_created,
        )
        if any(forbidden_true):
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )
        if not self.unknown_preserved:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_UNKNOWN_MUST_BE_PRESERVED",
                "A1_UNKNOWN_MUST_BE_PRESERVED",
            )
        if not self.current_stage_capture_fail_open:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CURRENT_STAGE_CAPTURE_MUST_REMAIN_FAIL_OPEN",
                "A1_CURRENT_STAGE_CAPTURE_MUST_REMAIN_FAIL_OPEN",
            )
        if self.runtime_operational_authorization_source != "NONE":
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.dependent_mutation_on_unproven_durability != "FORBIDDEN":
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if not self.next_owner_go_required:
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_NEXT_OWNER_GO_REQUIRED",
                "A1_NEXT_OWNER_GO_REQUIRED",
            )
        if self.host_crash_durability != "UNPROVEN" or self.power_loss_durability != "UNPROVEN":
            raise DdoA1DurabilityToAdmissionAndReplayBindingError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )


def canonical_a1_durability_to_admission_and_replay_binding_v1() -> (
    DdoA1DurabilityToAdmissionAndReplayBindingV1
):
    """Return the only valid A1 admission/replay binding instance."""
    return DdoA1DurabilityToAdmissionAndReplayBindingV1()


def _resolved_record_id(
    *,
    record_id: str | None,
    append_result: AppendResultV0 | None,
) -> str | None:
    if record_id is not None:
        return record_id
    if append_result is None:
        return None
    return append_result.record_id


def classify_a1_persist_attempt_for_admission_v1(
    *,
    append_result: AppendResultV0 | None = None,
    persist_error: BaseException | None = None,
    policy_result: DdoA1DurabilityFailurePolicyResultV1 | None = None,
    record_id: str | None = None,
) -> DdoA1PersistAttemptClassificationV1:
    """Classify one persist/replay attempt. Never grants dependent mutation."""
    persist_result = _persist_result_for(
        append_result=append_result,
        persist_error=persist_error,
    )
    resolved_policy = policy_result
    if resolved_policy is None and persist_error is not None:
        classified: DdoDurabilityWriteError | None
        if isinstance(persist_error, DdoDurabilityWriteError):
            classified = persist_error
        else:
            classified = None
        if classified is not None:
            resolved_policy = bind_a1_durability_failure_policy_v1(
                operation=classified.operation or OPERATION_IDEMPOTENT_REPLAY,
                failure=classified,
                record_id=record_id,
            )
    if resolved_policy is None and append_result is not None:
        operation = (
            OPERATION_IDEMPOTENT_REPLAY
            if append_result.status == IDEMPOTENT_REPLAY
            else OPERATION_DURABLE_APPEND
        )
        resolved_policy = bind_a1_durability_failure_policy_v1(
            operation=operation,
            failure=None,
            record_id=append_result.record_id,
        )
    durability_result = _durability_result_for(
        policy_result=resolved_policy,
        persist_error=persist_error,
    )
    proven = None if resolved_policy is None else resolved_policy.durability_proven
    retry_allowed = None if resolved_policy is None else resolved_policy.retry_allowed
    unknown_preserved = proven is None or UNKNOWN_PRESERVED is True
    return DdoA1PersistAttemptClassificationV1(
        persist_result=persist_result,
        durability_result=durability_result,
        dependent_mutation_admission=DEPENDENT_MUTATION_ADMISSION_STATE,
        durability_proven=proven,
        crash_durability_fully_proven=False,
        retry_allowed=retry_allowed,
        automatic_retry_loop_invoked=False,
        capture_ok_equals_admission=False,
        idempotent_replay_equals_crash_durability_proof=False,
        unknown_preserved=unknown_preserved if unknown_preserved else True,
        record_id=_resolved_record_id(record_id=record_id, append_result=append_result),
        operation=None if resolved_policy is None else resolved_policy.operation,
    )


def evaluate_a1_dependent_mutation_admission_v1(
    *,
    policy_result: DdoA1DurabilityFailurePolicyResultV1 | None = None,
    persist_classification: DdoA1PersistAttemptClassificationV1 | None = None,
    capture_ok: bool | None = None,
    durability_proven: bool | None = None,
) -> DdoA1DependentMutationAdmissionResultV1:
    """Inspect A1-adjacent admission without granting it.

    Observation only. Does not activate runtime. Capture ok is not admission.
    Missing or unclassified durability evidence remains fail-closed.
    """
    proven = durability_proven
    missing_policy = policy_result is None
    persist_result = (
        None if persist_classification is None else persist_classification.persist_result
    )
    if persist_classification is not None:
        proven = persist_classification.durability_proven
    if policy_result is not None:
        proven = policy_result.durability_proven
        ADMISSION_OWNER(
            dependent_mutation_requested=False,
            durability_proven=proven,
            policy_result=policy_result,
        )
    else:
        ADMISSION_OWNER(
            dependent_mutation_requested=False,
            durability_proven=proven,
        )
    if persist_classification is None and policy_result is None and durability_proven is None:
        durability_result = MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE
        reason = "A1_MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE"
    elif persist_classification is not None:
        durability_result = persist_classification.durability_result
        reason = "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY"
    elif proven is None:
        durability_result = DURABILITY_UNKNOWN
        reason = "A1_UNKNOWN_PRESERVED"
    else:
        durability_result = DURABILITY_FAILURE
        reason = "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY"
    return DdoA1DependentMutationAdmissionResultV1(
        admitted=False,
        admission_state=DEPENDENT_MUTATION_ADMISSION_STATE,
        admission_owner=ADMISSION_OWNER_NAME,
        evidence_must_be_durable_before_dependent_mutation=(
            EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION
        ),
        durability_proven=proven,
        missing_policy_result=missing_policy,
        capture_ok=capture_ok,
        persist_result=persist_result,
        durability_result=durability_result,
        current_stage_capture_fail_open=True,
        runtime_authorized=False,
        crash_durability_fully_proven=False,
        reason_code=reason,
    )


def attempt_a1_dependent_mutation_admission_v1(
    *,
    policy_result: DdoA1DurabilityFailurePolicyResultV1 | None = None,
    persist_classification: DdoA1PersistAttemptClassificationV1 | None = None,
    capture_ok: bool | None = None,
    durability_proven: bool | None = None,
) -> NoReturn:
    """A1-adjacent mutation-attempt seam. Always fail-closed through the existing owner."""
    evaluate_a1_dependent_mutation_admission_v1(
        policy_result=policy_result,
        persist_classification=persist_classification,
        capture_ok=capture_ok,
        durability_proven=durability_proven,
    )
    ADMISSION_OWNER(
        dependent_mutation_requested=True,
        durability_proven=None if policy_result is None else policy_result.durability_proven,
        policy_result=policy_result,
    )
    raise DdoA1DurabilityFailurePolicyError(
        "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
        "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
    )


def reject_a1_runtime_authorization_attempt_on_admission_binding_v1(**flags: bool) -> None:
    """Fail closed if any caller tries to turn A1 runtime authorization on."""
    if any(bool(value) for value in flags.values()):
        raise DdoA1DurabilityToAdmissionAndReplayBindingError(
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
        )


def a1_durability_to_admission_and_replay_observability_v1() -> dict[str, Any]:
    """Machine-readable binding stamps. Observation only. Not activation."""
    binding = canonical_a1_durability_to_admission_and_replay_binding_v1()
    return {
        "a1_admission_replay_slice_id": binding.slice_id,
        "a1_admission_binding_status": binding.admission_binding_status,
        "a1_replay_ambiguity_binding_status": binding.replay_ambiguity_binding_status,
        "a1_admission_owner_name": binding.admission_owner_name,
        "a1_new_admission_authority_created": binding.new_admission_authority_created,
        "a1_evidence_must_be_durable_before_dependent_mutation": (
            binding.evidence_must_be_durable_before_dependent_mutation
        ),
        "a1_current_stage_capture_fail_open": binding.current_stage_capture_fail_open,
        "a1_capture_ok_equals_admission": binding.capture_ok_equals_admission,
        "a1_automatic_retry_loop_added": binding.automatic_retry_loop_added,
        "a1_admission_ambiguous_retry_allowed": binding.ambiguous_retry_allowed,
        "a1_admission_unknown_preserved": binding.unknown_preserved,
        "a1_admission_runtime_authorization_eligible": (binding.runtime_authorization_eligible),
        "a1_admission_runtime_authorized": binding.runtime_authorized,
        "a1_admission_unattended_operation_started": (binding.unattended_operation_started),
        "a1_admission_crash_durability_fully_proven": (binding.crash_durability_fully_proven),
        "a1_admission_new_storage_authority_created": (binding.new_storage_authority_created),
        "a1_admission_file_fsync_policy": binding.file_fsync_policy,
        "a1_admission_directory_fsync_policy": binding.directory_fsync_policy,
        "a1_admission_host_crash_durability": binding.host_crash_durability,
        "a1_admission_power_loss_durability": binding.power_loss_durability,
        "a1_admission_next_owner_go_required": binding.next_owner_go_required,
    }


__all__ = [
    "ADMISSION_BINDING_STATUS",
    "ADMISSION_OWNER",
    "ADMISSION_OWNER_NAME",
    "AMBIGUOUS_RETRY_ALLOWED",
    "AUTOMATIC_RETRY_LOOP_ADDED",
    "CAPTURE_OK_EQUALS_ADMISSION",
    "CRASH_DURABILITY_FULLY_PROVEN",
    "CURRENT_STAGE_CAPTURE_FAIL_OPEN",
    "DEPENDENT_MUTATION_ADMISSION",
    "DEPENDENT_MUTATION_ADMISSION_STATE",
    "DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY",
    "DIRECTORY_FSYNC_POLICY",
    "DUPLICATE_CONFLICT",
    "DUPLICATE_CONFLICT_SEMANTICS",
    "DURABILITY_FAILURE",
    "DURABILITY_UNKNOWN",
    "DdoA1DependentMutationAdmissionResultV1",
    "DdoA1DurabilityToAdmissionAndReplayBindingError",
    "DdoA1DurabilityToAdmissionAndReplayBindingV1",
    "DdoA1PersistAttemptClassificationV1",
    "EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION",
    "FILE_FSYNC_POLICY",
    "IDEMPOTENT_REPLAY",
    "IDEMPOTENT_REPLAY_SEMANTICS",
    "MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE",
    "NEW_ADMISSION_AUTHORITY_CREATED",
    "NEW_STORAGE_AUTHORITY_CREATED",
    "PERSIST_WRITE_ACCEPTED",
    "REPLAY_AMBIGUITY_BINDING_STATUS",
    "RUNTIME_AUTHORIZATION_ELIGIBLE",
    "RUNTIME_AUTHORIZED",
    "SLICE_ID",
    "UNATTENDED_OPERATION_STARTED",
    "UNKNOWN_PRESERVED",
    "a1_durability_to_admission_and_replay_observability_v1",
    "attempt_a1_dependent_mutation_admission_v1",
    "canonical_a1_durability_to_admission_and_replay_binding_v1",
    "classify_a1_persist_attempt_for_admission_v1",
    "evaluate_a1_dependent_mutation_admission_v1",
    "reject_a1_runtime_authorization_attempt_on_admission_binding_v1",
]

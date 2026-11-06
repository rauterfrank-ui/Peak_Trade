"""DDO A1 durability failure policy binding v1.

Typed fail-closed policy for durability-relevant persistence failures.
Binds A1_DURABILITY_FAILURE_POLICY without authorizing A1 runtime,
unattended operation, trading, execution, live, or a new storage owner.
Crash durability remains unproven. UNKNOWN is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DURABILITY_FAILURE_CLASSES,
    FAILURE_CLASS_CONCURRENT_WRITER,
    FAILURE_CLASS_CORRUPTION_UNREADABLE,
    FAILURE_CLASS_DUPLICATE_CONFLICT,
    FAILURE_CLASS_FILESYSTEM_CAPACITY,
    FAILURE_CLASS_PATH_TYPE_INVALID,
    FAILURE_CLASS_PERMISSION_ACCESS,
    FAILURE_CLASS_SERIALIZATION_VALIDATION,
    FAILURE_CLASS_UNKNOWN_IO,
    FAILURE_CLASS_UNSUPPORTED_SCHEMA,
    OPERATION_DIRECTORY_FSYNC,
    OPERATION_DURABLE_APPEND,
    OPERATION_FILE_FSYNC,
    OPERATION_IDEMPOTENT_REPLAY,
    OPERATION_LEDGER_LOAD,
    OPERATION_LEDGER_OPEN_CREATE,
    OPERATION_PARENT_MKDIR,
    OPERATION_SERIALIZE_VALIDATE,
    OPERATION_WRITE,
    OPERATION_WRITER_LOCK,
    DdoDurabilityWriteError,
)

SLICE_ID: Final[str] = "PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1"
IMPLEMENTATION_AUTHORIZATION_SOURCE: Final[str] = (
    "PEAK_TRADE_OWNER_GO_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1"
)
RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE: Final[str] = "NONE"
IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION: Final[bool] = False

A1_DURABILITY_FAILURE_POLICY: Final[str] = (
    "BOUND_FAIL_CLOSED_DEPENDENT_MUTATION_FORBIDDEN_ON_UNPROVEN_DURABILITY"
)
CURRENT_STAGE_DURABILITY_FAILURE_POLICY: Final[str] = (
    "FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE"
)

DURABILITY_SUCCESS_CONDITION: Final[str] = (
    "APPEND_OR_IDEMPOTENT_REPLAY_AFTER_FILE_FSYNC_DIRECTORY_FSYNC_ATTEMPTED"
)
DURABILITY_FAILURE_CONDITION: Final[str] = (
    "CLASSIFIED_DURABILITY_WRITE_ERROR_OR_SHORT_WRITE_OR_FSYNC_FAILURE"
)
DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY: Final[str] = "FORBIDDEN"
AMBIGUOUS_RETRY_ALLOWED: Final[bool] = False
UNKNOWN_PRESERVED: Final[bool] = True
PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING: Final[bool] = False
NEW_STORAGE_AUTHORITY_CREATED: Final[bool] = False
EXISTING_STORAGE_OWNER: Final[str] = "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"

EVIDENCE_STATUS_PRIMARY_LEDGER: Final[str] = "DURABLE_PRIMARY_EVIDENCE"
EVIDENCE_STATUS_DIAGNOSTIC: Final[str] = "BEST_EFFORT_DIAGNOSTIC_SIGNAL"
EVIDENCE_STATUS_IN_MEMORY: Final[str] = "IN_MEMORY_CURRENT_PROCESS_ERROR_STATE"
EVIDENCE_STATUS_EXTERNAL_STRUCTURED: Final[str] = "EXTERNALLY_RETURNED_STRUCTURED_FAILURE"
EVIDENCE_STATUS_APPEND_ACKNOWLEDGED_UNPROVEN: Final[str] = (
    "APPEND_ACKNOWLEDGED_CRASH_DURABILITY_UNPROVEN"
)

REASON_SUCCESS_UNPROVEN: Final[str] = "APPEND_ACKNOWLEDGED_CRASH_DURABILITY_UNPROVEN"
REASON_DEPENDENT_MUTATION_FORBIDDEN: Final[str] = (
    "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY"
)
REASON_AMBIGUOUS_RETRY_FORBIDDEN: Final[str] = "A1_AMBIGUOUS_RETRY_FORBIDDEN"
REASON_UNKNOWN_PRESERVED: Final[str] = "A1_UNKNOWN_PRESERVED"

FILE_FSYNC_STATUS: Final[str] = "PRESENT"
DIRECTORY_FSYNC_STATUS: Final[str] = "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"
HOST_CRASH_DURABILITY: Final[str] = "UNPROVEN"
POWER_LOSS_DURABILITY: Final[str] = "UNPROVEN"
CRASH_DURABILITY_FULLY_PROVEN: Final[bool] = False
DURABILITY_CLASS: Final[str] = "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
ATOMIC_WRITE_MODEL: Final[str] = "ENFORCED_O_APPEND_JSONL_LINE"
ATOMIC_REPLACE_IMPLEMENTED: Final[bool] = False

IMPLEMENTATION_COMPLETE: Final[bool] = True
RUNTIME_AUTHORIZATION_ELIGIBLE: Final[bool] = False
RUNTIME_AUTHORIZED: Final[bool] = False
OPERATION_STARTED: Final[bool] = False
UNATTENDED_OPERATION_STARTED: Final[bool] = False
NEXT_OWNER_GO_REQUIRED: Final[bool] = True
NEXT_DDO_STEP: Final[str] = (
    "OWNER_GO_REQUIRED_SEPARATE_SCOPED_DDO_A1_CONTINUATION_NOT_AUTHORIZED_BY_THIS_PERSIST"
)

MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY: Final[bool] = True
DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY: Final[bool] = False
DDO_LEARNING_PRODUCTIVE_AUTHORITY: Final[bool] = False
TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE: Final[bool] = False
PRODUCTIVE_RETURN_VALUE_UNCHANGED: Final[bool] = True
A1_TRADING_AUTHORITY: Final[bool] = False
A1_EXECUTION_AUTHORITY: Final[bool] = False
A1_LEARNING_AUTHORITY: Final[bool] = False
A1_UNATTENDED_AUTHORITY: Final[bool] = False
A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED: Final[bool] = False

FAILURE_CLASSES_BOUND: Final[frozenset[str]] = DURABILITY_FAILURE_CLASSES

_AMBIGUOUS_SIDE_EFFECT_OPERATIONS: Final[frozenset[str]] = frozenset(
    {
        OPERATION_WRITE,
        OPERATION_FILE_FSYNC,
        OPERATION_DIRECTORY_FSYNC,
        OPERATION_DURABLE_APPEND,
    }
)
_RECOVERY_REQUIRED_OPERATIONS: Final[frozenset[str]] = frozenset(
    {
        OPERATION_WRITE,
        OPERATION_FILE_FSYNC,
        OPERATION_DIRECTORY_FSYNC,
        OPERATION_LEDGER_LOAD,
        OPERATION_DURABLE_APPEND,
    }
)
_RECOVERY_REQUIRED_CLASSES: Final[frozenset[str]] = frozenset(
    {
        FAILURE_CLASS_CORRUPTION_UNREADABLE,
        FAILURE_CLASS_UNKNOWN_IO,
        FAILURE_CLASS_PATH_TYPE_INVALID,
        FAILURE_CLASS_PERMISSION_ACCESS,
        FAILURE_CLASS_FILESYSTEM_CAPACITY,
    }
)

assert AUTHORITY_OWNER == "NONE"
assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
assert SECOND_TRADING_AUTHORITY_CREATED is False
assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert RUNTIME_AUTHORIZED is False
assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
assert CRASH_DURABILITY_FULLY_PROVEN is False
assert NEW_STORAGE_AUTHORITY_CREATED is False
assert AMBIGUOUS_RETRY_ALLOWED is False
assert UNKNOWN_PRESERVED is True
assert PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING is False
assert A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED is False


class DdoA1DurabilityFailurePolicyError(Exception):
    """Fail-closed A1 durability failure-policy error. Not trading authority."""

    error_code = "DDO_A1_DURABILITY_FAILURE_POLICY_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class DdoA1DurabilityFailurePolicyResultV1:
    """Deterministic per-operation A1 durability failure-policy result."""

    operation: str
    failure_class: str | None
    reason_code: str
    durability_proven: bool | None
    append_acknowledged: bool
    dependent_mutation_allowed: bool
    retry_allowed: bool | None
    recovery_required: bool
    evidence_status: str
    diagnostic_signal_equivalent_to_primary: bool
    primary_ledger_failure_masked_by_logging: bool
    underlying_exception_type: str | None
    errno_code: int | None
    record_id: str | None
    crash_durability_fully_proven: bool
    unknown_preserved: bool
    current_stage_capture_fail_open: bool = True

    def __post_init__(self) -> None:
        if self.dependent_mutation_allowed:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if self.durability_proven is True:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.crash_durability_fully_proven:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.retry_allowed is True and self.operation in _AMBIGUOUS_SIDE_EFFECT_OPERATIONS:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_AMBIGUOUS_RETRY_FORBIDDEN",
                "A1_AMBIGUOUS_RETRY_FORBIDDEN",
            )
        if self.diagnostic_signal_equivalent_to_primary:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING",
                "A1_PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING",
            )
        if self.primary_ledger_failure_masked_by_logging:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING",
                "A1_PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING",
            )
        if self.durability_proven is None and not self.unknown_preserved:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_UNKNOWN_MUST_BE_PRESERVED",
                "A1_UNKNOWN_MUST_BE_PRESERVED",
            )
        if self.retry_allowed is None and not self.unknown_preserved:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_UNKNOWN_MUST_BE_PRESERVED",
                "A1_UNKNOWN_MUST_BE_PRESERVED",
            )

    def as_observability(self) -> dict[str, Any]:
        return {
            "a1_failure_policy_operation": self.operation,
            "a1_failure_policy_failure_class": self.failure_class,
            "a1_failure_policy_reason_code": self.reason_code,
            "a1_failure_policy_durability_proven": self.durability_proven,
            "a1_failure_policy_append_acknowledged": self.append_acknowledged,
            "a1_failure_policy_dependent_mutation_allowed": self.dependent_mutation_allowed,
            "a1_failure_policy_retry_allowed": self.retry_allowed,
            "a1_failure_policy_recovery_required": self.recovery_required,
            "a1_failure_policy_evidence_status": self.evidence_status,
            "a1_failure_policy_diagnostic_equivalent_to_primary": (
                self.diagnostic_signal_equivalent_to_primary
            ),
            "a1_failure_policy_primary_masked_by_logging": (
                self.primary_ledger_failure_masked_by_logging
            ),
            "a1_failure_policy_underlying_exception_type": self.underlying_exception_type,
            "a1_failure_policy_errno_code": self.errno_code,
            "a1_failure_policy_record_id": self.record_id,
            "a1_failure_policy_crash_durability_fully_proven": (self.crash_durability_fully_proven),
            "a1_failure_policy_unknown_preserved": self.unknown_preserved,
        }


@dataclass(frozen=True)
class DdoA1DurabilityFailurePolicyBindingV1:
    """Canonical A1 durability failure-policy binding. Never self-activating."""

    slice_id: str = SLICE_ID
    implementation_complete: bool = True
    a1_durability_failure_policy: str = A1_DURABILITY_FAILURE_POLICY
    current_stage_durability_failure_policy: str = CURRENT_STAGE_DURABILITY_FAILURE_POLICY
    runtime_authorization_eligible: bool = False
    runtime_authorized: bool = False
    operation_started: bool = False
    unattended_operation_started: bool = False
    implementation_go_is_runtime_authorization: bool = False
    crash_durability_fully_proven: bool = False
    new_storage_authority_created: bool = False
    ambiguous_retry_allowed: bool = False
    unknown_preserved: bool = True
    primary_ledger_failure_masked_by_logging: bool = False
    dependent_mutation_on_unproven_durability: str = DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY
    next_owner_go_required: bool = True
    implementation_authorization_source: str = IMPLEMENTATION_AUTHORIZATION_SOURCE
    runtime_operational_authorization_source: str = RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE
    existing_storage_owner: str = EXISTING_STORAGE_OWNER
    file_fsync_status: str = FILE_FSYNC_STATUS
    directory_fsync_status: str = DIRECTORY_FSYNC_STATUS
    host_crash_durability: str = HOST_CRASH_DURABILITY
    power_loss_durability: str = POWER_LOSS_DURABILITY
    durability_class: str = DURABILITY_CLASS
    next_ddo_step: str = NEXT_DDO_STEP

    def __post_init__(self) -> None:
        if self.slice_id != SLICE_ID:
            raise DdoA1DurabilityFailurePolicyError("A1_SLICE_ID_INVALID", "A1_SLICE_ID_INVALID")
        if not self.implementation_complete:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
            )
        if self.a1_durability_failure_policy != A1_DURABILITY_FAILURE_POLICY:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_DURABILITY_FAILURE_POLICY_MUST_REMAIN_BOUND",
                "A1_DURABILITY_FAILURE_POLICY_MUST_REMAIN_BOUND",
            )
        if self.a1_durability_failure_policy == "UNBOUND_NOT_AUTHORIZED":
            raise DdoA1DurabilityFailurePolicyError(
                "A1_DURABILITY_FAILURE_POLICY_MUST_REMAIN_BOUND",
                "A1_DURABILITY_FAILURE_POLICY_MUST_REMAIN_BOUND",
            )
        forbidden_true = (
            self.runtime_authorization_eligible,
            self.runtime_authorized,
            self.operation_started,
            self.unattended_operation_started,
            self.implementation_go_is_runtime_authorization,
            self.crash_durability_fully_proven,
            self.new_storage_authority_created,
            self.ambiguous_retry_allowed,
            self.primary_ledger_failure_masked_by_logging,
        )
        if any(forbidden_true):
            raise DdoA1DurabilityFailurePolicyError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )
        if not self.unknown_preserved:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_UNKNOWN_MUST_BE_PRESERVED",
                "A1_UNKNOWN_MUST_BE_PRESERVED",
            )
        if self.runtime_operational_authorization_source != "NONE":
            raise DdoA1DurabilityFailurePolicyError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.dependent_mutation_on_unproven_durability != "FORBIDDEN":
            raise DdoA1DurabilityFailurePolicyError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if not self.next_owner_go_required:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_NEXT_OWNER_GO_REQUIRED",
                "A1_NEXT_OWNER_GO_REQUIRED",
            )


def canonical_a1_durability_failure_policy_binding_v1() -> DdoA1DurabilityFailurePolicyBindingV1:
    """Return the only valid A1 durability failure-policy binding instance."""
    return DdoA1DurabilityFailurePolicyBindingV1()


def reject_a1_dependent_mutation_on_unproven_durability_v1(
    *,
    dependent_mutation_requested: bool = False,
    durability_proven: bool | None = None,
    policy_result: DdoA1DurabilityFailurePolicyResultV1 | None = None,
) -> None:
    """Fail closed if any caller tries to mutate on unproven durability.

    This is the sole A1-dependent-mutation admission owner. A later binding
    may consume this helper; it must not create a second admission authority.
    `durability_proven is True` remains an overclaim under the current policy,
    which deliberately never produces True while crash durability is unproven.
    """
    proven = durability_proven
    if policy_result is not None:
        if durability_proven is not None and durability_proven != policy_result.durability_proven:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        proven = policy_result.durability_proven
        if policy_result.dependent_mutation_allowed:
            raise DdoA1DurabilityFailurePolicyError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
    if dependent_mutation_requested:
        raise DdoA1DurabilityFailurePolicyError(
            "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
        )
    if proven is True:
        raise DdoA1DurabilityFailurePolicyError(
            "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
        )


def reject_a1_runtime_authorization_attempt_v1(**flags: bool) -> None:
    """Fail closed if any caller tries to turn A1 runtime authorization on."""
    if any(bool(value) for value in flags.values()):
        raise DdoA1DurabilityFailurePolicyError(
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
        )


def _retry_allowed_for(
    *,
    success: bool,
    operation: str,
    failure: DdoDurabilityWriteError | None,
) -> bool | None:
    if success:
        return False
    if operation in _AMBIGUOUS_SIDE_EFFECT_OPERATIONS:
        return False if AMBIGUOUS_RETRY_ALLOWED is False else None
    if failure is None:
        return False
    return failure.retryable


def _durability_proven_for(
    *,
    success: bool,
    operation: str,
    failure_class: str | None,
) -> bool | None:
    if success:
        return None
    if failure_class == FAILURE_CLASS_UNKNOWN_IO:
        return None
    if operation == OPERATION_DIRECTORY_FSYNC:
        return None
    return False


def _append_acknowledged_for(*, success: bool, operation: str) -> bool:
    if success:
        return True
    return operation == OPERATION_DIRECTORY_FSYNC


def _recovery_required_for(
    *,
    success: bool,
    operation: str,
    failure_class: str | None,
) -> bool:
    if success:
        return False
    if failure_class in {
        FAILURE_CLASS_SERIALIZATION_VALIDATION,
        FAILURE_CLASS_DUPLICATE_CONFLICT,
        FAILURE_CLASS_CONCURRENT_WRITER,
        FAILURE_CLASS_UNSUPPORTED_SCHEMA,
    }:
        return failure_class in {FAILURE_CLASS_UNSUPPORTED_SCHEMA}
    if operation in _RECOVERY_REQUIRED_OPERATIONS:
        return True
    return failure_class in _RECOVERY_REQUIRED_CLASSES


def _reason_code_for(
    *,
    success: bool,
    failure: DdoDurabilityWriteError | None,
    durability_proven: bool | None,
    retry_allowed: bool | None,
) -> str:
    if success:
        return REASON_SUCCESS_UNPROVEN
    if failure is None:
        return REASON_UNKNOWN_PRESERVED
    if durability_proven is None or retry_allowed is None:
        return str(failure)
    return str(failure)


def bind_a1_durability_failure_policy_v1(
    *,
    operation: str,
    failure: DdoDurabilityWriteError | None = None,
    record_id: str | None = None,
) -> DdoA1DurabilityFailurePolicyResultV1:
    """Bind one durability operation to the A1 failure policy. Not activation."""
    success = failure is None
    failure_class = None if failure is None else failure.failure_class
    if failure is not None and failure_class not in DURABILITY_FAILURE_CLASSES:
        failure_class = FAILURE_CLASS_UNKNOWN_IO
    resolved_operation = operation
    if failure is not None and failure.operation:
        resolved_operation = failure.operation
    durability_proven = _durability_proven_for(
        success=success,
        operation=resolved_operation,
        failure_class=failure_class,
    )
    retry_allowed = _retry_allowed_for(
        success=success,
        operation=resolved_operation,
        failure=failure,
    )
    unknown_preserved = durability_proven is None or retry_allowed is None
    if success:
        evidence_status = EVIDENCE_STATUS_APPEND_ACKNOWLEDGED_UNPROVEN
        underlying_type: str | None = None
        errno_code: int | None = None
    else:
        evidence_status = EVIDENCE_STATUS_EXTERNAL_STRUCTURED
        underlying_type = None if failure is None else type(failure).__name__
        errno_code = None if failure is None else failure.errno_code
    return DdoA1DurabilityFailurePolicyResultV1(
        operation=resolved_operation,
        failure_class=failure_class,
        reason_code=_reason_code_for(
            success=success,
            failure=failure,
            durability_proven=durability_proven,
            retry_allowed=retry_allowed,
        ),
        durability_proven=durability_proven,
        append_acknowledged=_append_acknowledged_for(
            success=success,
            operation=resolved_operation,
        ),
        dependent_mutation_allowed=False,
        retry_allowed=retry_allowed,
        recovery_required=_recovery_required_for(
            success=success,
            operation=resolved_operation,
            failure_class=failure_class,
        ),
        evidence_status=evidence_status,
        diagnostic_signal_equivalent_to_primary=False,
        primary_ledger_failure_masked_by_logging=False,
        underlying_exception_type=underlying_type,
        errno_code=errno_code,
        record_id=record_id,
        crash_durability_fully_proven=False,
        unknown_preserved=unknown_preserved if unknown_preserved else True,
        current_stage_capture_fail_open=True,
    )


def a1_failure_class_policy_v1(failure_class: str, *, operation: str) -> Mapping[str, Any]:
    """Named per-class policy view. Uses existing DURABILITY_FAILURE_CLASSES only."""
    if failure_class not in DURABILITY_FAILURE_CLASSES:
        failure_class = FAILURE_CLASS_UNKNOWN_IO
    synthetic = DdoDurabilityWriteError(
        failure_class,
        failure_class,
        retryable=None if failure_class == FAILURE_CLASS_UNKNOWN_IO else False,
        operation=operation,
    )
    result = bind_a1_durability_failure_policy_v1(operation=operation, failure=synthetic)
    return result.as_observability()


def a1_durability_failure_policy_observability_v1() -> dict[str, Any]:
    """Machine-readable binding stamps. Observation only. Not activation."""
    binding = canonical_a1_durability_failure_policy_binding_v1()
    return {
        "a1_durability_failure_policy_slice_id": binding.slice_id,
        "a1_durability_failure_policy": binding.a1_durability_failure_policy,
        "a1_durability_failure_policy_implementation_complete": (binding.implementation_complete),
        "a1_current_stage_durability_failure_policy": (
            binding.current_stage_durability_failure_policy
        ),
        "a1_failure_policy_runtime_authorization_eligible": (
            binding.runtime_authorization_eligible
        ),
        "a1_failure_policy_runtime_authorized": binding.runtime_authorized,
        "a1_failure_policy_operation_started": binding.unattended_operation_started,
        "a1_failure_policy_crash_durability_fully_proven": (binding.crash_durability_fully_proven),
        "a1_failure_policy_dependent_mutation_on_unproven_durability": (
            binding.dependent_mutation_on_unproven_durability
        ),
        "a1_failure_policy_ambiguous_retry_allowed": binding.ambiguous_retry_allowed,
        "a1_failure_policy_unknown_preserved": binding.unknown_preserved,
        "a1_failure_policy_primary_masked_by_logging": (
            binding.primary_ledger_failure_masked_by_logging
        ),
        "a1_failure_policy_new_storage_authority_created": (binding.new_storage_authority_created),
        "a1_failure_policy_next_owner_go_required": binding.next_owner_go_required,
        "a1_failure_policy_file_fsync_status": binding.file_fsync_status,
        "a1_failure_policy_directory_fsync_status": binding.directory_fsync_status,
        "a1_failure_policy_host_crash_durability": binding.host_crash_durability,
        "a1_failure_policy_power_loss_durability": binding.power_loss_durability,
    }


__all__ = [
    "A1_DURABILITY_FAILURE_POLICY",
    "AMBIGUOUS_RETRY_ALLOWED",
    "CRASH_DURABILITY_FULLY_PROVEN",
    "CURRENT_STAGE_DURABILITY_FAILURE_POLICY",
    "DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY",
    "DdoA1DurabilityFailurePolicyBindingV1",
    "DdoA1DurabilityFailurePolicyError",
    "DdoA1DurabilityFailurePolicyResultV1",
    "FAILURE_CLASSES_BOUND",
    "OPERATION_DIRECTORY_FSYNC",
    "OPERATION_DURABLE_APPEND",
    "OPERATION_FILE_FSYNC",
    "OPERATION_IDEMPOTENT_REPLAY",
    "OPERATION_LEDGER_LOAD",
    "OPERATION_LEDGER_OPEN_CREATE",
    "OPERATION_PARENT_MKDIR",
    "OPERATION_SERIALIZE_VALIDATE",
    "OPERATION_WRITE",
    "OPERATION_WRITER_LOCK",
    "PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING",
    "SLICE_ID",
    "UNKNOWN_PRESERVED",
    "a1_durability_failure_policy_observability_v1",
    "a1_failure_class_policy_v1",
    "bind_a1_durability_failure_policy_v1",
    "canonical_a1_durability_failure_policy_binding_v1",
    "reject_a1_dependent_mutation_on_unproven_durability_v1",
    "reject_a1_runtime_authorization_attempt_v1",
]

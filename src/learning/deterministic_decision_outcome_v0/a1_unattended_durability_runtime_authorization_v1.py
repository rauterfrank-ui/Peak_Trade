"""DDO A1 unattended durability runtime-authorization adjudication v1.

Typed fail-closed eligibility object. Implementation Owner-GO is not
runtime authorization and does not start unattended operation.
Crash durability remains unproven on the existing O_APPEND ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    A1_EXECUTION_AUTHORITY,
    A1_LEARNING_AUTHORITY,
    A1_TRADING_AUTHORITY,
    A1_UNATTENDED_AUTHORITY,
    A1_UNATTENDED_DURABILITY_POLICY_DEFINED,
    A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION as A1_POLICY_IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE as A1_POLICY_RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    canonical_a1_unattended_durability_policy_boundary_v1,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)

SLICE_ID: Final[str] = "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_V1"
IMPLEMENTATION_AUTHORIZATION_SOURCE: Final[str] = (
    "PEAK_TRADE_OWNER_GO_DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_V1"
)
RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE: Final[str] = "NONE"
AUTHORIZATION_SOURCE: Final[str] = "NONE"
AUTHORIZATION_SOURCE_CLASS: Final[str] = "NONE"
AUTHORIZATION_SOURCE_FOUND: Final[bool] = True
IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION: Final[bool] = False

DURABILITY_CLASS: Final[str] = "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
ATOMIC_WRITE_STATUS: Final[str] = "PARTIAL"
FILE_FSYNC_STATUS: Final[str] = "PRESENT"
DIRECTORY_FSYNC_STATUS: Final[str] = "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"
CRASH_DURABILITY_FULLY_PROVEN: Final[bool] = False
APPEND_ONLY_STATUS: Final[str] = "ENFORCED_O_APPEND"
RENAME_ATOMIC_REPLACE_PRESENT: Final[bool] = False

IMPLEMENTATION_COMPLETE: Final[bool] = True
PRECONDITIONS_PROVEN: Final[bool] = False
RUNTIME_AUTHORIZATION_ELIGIBLE: Final[bool] = False
RUNTIME_AUTHORIZED: Final[bool] = False
OPERATION_STARTED: Final[bool] = False
UNATTENDED_OPERATION_STARTED: Final[bool] = False
NEXT_OWNER_GO_REQUIRED: Final[bool] = True

A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED_AFTER: Final[bool] = False
A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED: Final[bool] = False
A1_DURABILITY_FAILURE_POLICY_REMAINS_UNBOUND: Final[str] = "UNBOUND_NOT_AUTHORIZED"

EXISTING_STORAGE_OWNER: Final[str] = "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
NEW_STORAGE_AUTHORITY_CREATED: Final[bool] = False
MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY: Final[bool] = True
DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY: Final[bool] = False
DDO_LEARNING_PRODUCTIVE_AUTHORITY: Final[bool] = False
TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE: Final[bool] = False
PRODUCTIVE_RETURN_VALUE_UNCHANGED: Final[bool] = True

AUTHORIZATION_FAILURE_REASON: Final[str] = "A1_RUNTIME_AUTHORIZATION_PRECONDITIONS_UNPROVEN"
NEXT_DDO_STEP: Final[str] = (
    "PEAK_TRADE_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1"
)

assert AUTHORITY_OWNER == "NONE"
assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
assert SECOND_TRADING_AUTHORITY_CREATED is False
assert CAPTURE_FAILURE_CHANGES_DECISION is False
assert A1_UNATTENDED_DURABILITY_POLICY_DEFINED is True
assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False
assert A1_POLICY_IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert A1_POLICY_RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
assert A1_TRADING_AUTHORITY is False
assert A1_EXECUTION_AUTHORITY is False
assert A1_LEARNING_AUTHORITY is False
assert A1_UNATTENDED_AUTHORITY is False
assert A1_DURABILITY_FAILURE_POLICY == (
    "BOUND_FAIL_CLOSED_DEPENDENT_MUTATION_FORBIDDEN_ON_UNPROVEN_DURABILITY"
)
assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert RUNTIME_AUTHORIZED is False
assert OPERATION_STARTED is False
assert CRASH_DURABILITY_FULLY_PROVEN is False
assert NEW_STORAGE_AUTHORITY_CREATED is False


class DdoA1RuntimeAuthorizationError(Exception):
    """Fail-closed A1 runtime-authorization error. Not trading authority."""

    error_code = "DDO_A1_RUNTIME_AUTHORIZATION_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class DdoA1UnattendedDurabilityRuntimeAuthorizationV1:
    """Canonical A1 runtime-authorization adjudication. Never self-activating."""

    slice_id: str = SLICE_ID
    implementation_complete: bool = True
    preconditions_proven: bool = False
    runtime_authorization_eligible: bool = False
    runtime_authorized: bool = False
    operation_started: bool = False
    unattended_operation_started: bool = False
    implementation_go_is_runtime_authorization: bool = False
    authorization_source_found: bool = True
    authorization_source: str = AUTHORIZATION_SOURCE
    authorization_source_class: str = AUTHORIZATION_SOURCE_CLASS
    runtime_operational_authorization_source: str = RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE
    durability_class: str = DURABILITY_CLASS
    atomic_write_status: str = ATOMIC_WRITE_STATUS
    file_fsync_status: str = FILE_FSYNC_STATUS
    directory_fsync_status: str = DIRECTORY_FSYNC_STATUS
    crash_durability_fully_proven: bool = False
    rename_atomic_replace_present: bool = False
    next_owner_go_required: bool = True
    authorization_failure_reason: str = AUTHORIZATION_FAILURE_REASON
    implementation_authorization_source: str = IMPLEMENTATION_AUTHORIZATION_SOURCE
    existing_storage_owner: str = EXISTING_STORAGE_OWNER
    new_storage_authority_created: bool = False

    def __post_init__(self) -> None:
        if self.slice_id != SLICE_ID:
            raise DdoA1RuntimeAuthorizationError("A1_SLICE_ID_INVALID", "A1_SLICE_ID_INVALID")
        if not self.implementation_complete:
            raise DdoA1RuntimeAuthorizationError(
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
            )
        forbidden_true = (
            self.preconditions_proven,
            self.runtime_authorization_eligible,
            self.runtime_authorized,
            self.operation_started,
            self.unattended_operation_started,
            self.implementation_go_is_runtime_authorization,
            self.crash_durability_fully_proven,
            self.rename_atomic_replace_present,
            self.new_storage_authority_created,
        )
        if any(forbidden_true):
            raise DdoA1RuntimeAuthorizationError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )
        if self.runtime_operational_authorization_source != "NONE":
            raise DdoA1RuntimeAuthorizationError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.authorization_source != "NONE" or self.authorization_source_class != "NONE":
            raise DdoA1RuntimeAuthorizationError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.durability_class != "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE":
            raise DdoA1RuntimeAuthorizationError(
                "A1_DURABILITY_CLASS_MUST_REMAIN_NOT_PROVABLE",
                "A1_DURABILITY_CLASS_MUST_REMAIN_NOT_PROVABLE",
            )
        if self.directory_fsync_status != DIRECTORY_FSYNC_STATUS:
            raise DdoA1RuntimeAuthorizationError(
                "A1_DIRECTORY_FSYNC_STATUS_INVALID",
                "A1_DIRECTORY_FSYNC_STATUS_INVALID",
            )
        if not self.next_owner_go_required:
            raise DdoA1RuntimeAuthorizationError(
                "A1_NEXT_OWNER_GO_REQUIRED",
                "A1_NEXT_OWNER_GO_REQUIRED",
            )
        policy = canonical_a1_unattended_durability_policy_boundary_v1()
        if policy.runtime_authorized or policy.unattended_authority:
            raise DdoA1RuntimeAuthorizationError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )


def canonical_a1_unattended_durability_runtime_authorization_v1() -> (
    DdoA1UnattendedDurabilityRuntimeAuthorizationV1
):
    """Return the only valid A1 runtime-authorization adjudication instance."""
    return DdoA1UnattendedDurabilityRuntimeAuthorizationV1()


def reject_a1_runtime_authorization_activation_v1(**flags: bool) -> None:
    """Fail closed if any caller tries to turn A1 runtime authorization on."""
    if any(bool(value) for value in flags.values()):
        raise DdoA1RuntimeAuthorizationError(
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
        )


def a1_runtime_authorization_observability_v1() -> dict[str, Any]:
    """Machine-readable adjudication stamps. Observation only. Not activation."""
    adjudication = canonical_a1_unattended_durability_runtime_authorization_v1()
    return {
        "a1_runtime_authorization_slice_id": adjudication.slice_id,
        "a1_implementation_complete": adjudication.implementation_complete,
        "a1_preconditions_proven": adjudication.preconditions_proven,
        "a1_runtime_authorization_eligible": adjudication.runtime_authorization_eligible,
        "a1_unattended_durability_runtime_authorized": adjudication.runtime_authorized,
        "a1_operation_started": adjudication.operation_started,
        "a1_unattended_operation_started": adjudication.unattended_operation_started,
        "a1_implementation_go_is_runtime_authorization": (
            adjudication.implementation_go_is_runtime_authorization
        ),
        "a1_runtime_operational_authorization_source": (
            adjudication.runtime_operational_authorization_source
        ),
        "a1_authorization_source": adjudication.authorization_source,
        "a1_authorization_source_class": adjudication.authorization_source_class,
        "a1_durability_class": adjudication.durability_class,
        "a1_atomic_write_status": adjudication.atomic_write_status,
        "a1_file_fsync_status": adjudication.file_fsync_status,
        "a1_directory_fsync_status": adjudication.directory_fsync_status,
        "a1_crash_durability_fully_proven": adjudication.crash_durability_fully_proven,
        "a1_authorization_failure_reason": adjudication.authorization_failure_reason,
        "a1_next_owner_go_required": adjudication.next_owner_go_required,
        "a1_new_storage_authority_created": adjudication.new_storage_authority_created,
    }

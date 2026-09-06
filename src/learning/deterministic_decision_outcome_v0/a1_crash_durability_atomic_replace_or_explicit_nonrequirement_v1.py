"""DDO A1 crash-durability atomic-replace-or-nonrequirement adjudication v1.

Typed fail-closed contract. Does not implement tempfile/rename, does not
create a new storage owner, and does not authorize A1 runtime.
Full crash durability remains unproven on the existing O_APPEND ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    A1_EXECUTION_AUTHORITY,
    A1_LEARNING_AUTHORITY,
    A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED,
    A1_TRADING_AUTHORITY,
    A1_UNATTENDED_AUTHORITY,
    A1_UNATTENDED_DURABILITY_POLICY_DEFINED,
    A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED,
)
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_runtime_authorization_v1 import (
    AUTHORIZATION_SOURCE as A1_RUNTIME_AUTHORIZATION_SOURCE,
    CRASH_DURABILITY_FULLY_PROVEN as A1_RUNTIME_CRASH_DURABILITY_FULLY_PROVEN,
    DIRECTORY_FSYNC_STATUS as A1_RUNTIME_DIRECTORY_FSYNC_STATUS,
    DURABILITY_CLASS as A1_RUNTIME_DURABILITY_CLASS,
    RENAME_ATOMIC_REPLACE_PRESENT as A1_RUNTIME_RENAME_ATOMIC_REPLACE_PRESENT,
    RUNTIME_AUTHORIZATION_ELIGIBLE as A1_RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED as A1_RUNTIME_AUTHORIZED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE as A1_RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)

SLICE_ID: Final[str] = (
    "PEAK_TRADE_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1"
)
IMPLEMENTATION_AUTHORIZATION_SOURCE: Final[str] = (
    "PEAK_TRADE_OWNER_GO_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1"
)
RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE: Final[str] = "NONE"
IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION: Final[bool] = False

ADJUDICATION_CLASS: Final[str] = "PLATFORM_FULL_GUARANTEE_STILL_NOT_PROVABLE"
CRASH_DURABILITY_REQUIREMENT_SOURCE_FOUND: Final[bool] = True
CRASH_DURABILITY_REQUIREMENT_SOURCE: Final[str] = (
    "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1_SECTION_8_AND_A1_RUNTIME_AUTHORIZATION_PRECONDITION"
)
CRASH_DURABILITY_REQUIRED_FOR_WHAT: Final[str] = (
    "STRONG_DURABLE_AUTHORITY_CLAIM_AND_A1_RUNTIME_AUTHORIZATION_ELIGIBILITY"
)
DEPENDENT_MUTATION_CLASS: Final[str] = (
    "A1_UNATTENDED_RUNTIME_AUTHORIZATION_AND_RISK_INCREASING_DURABLE_PRECONDITION"
)
DEPENDENT_MUTATION_CURRENTLY_AUTHORIZED: Final[bool] = False
EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION: Final[str] = (
    "UNBOUND_FAIL_CLOSED_NOT_A_CURRENT_TRADING_PRECONDITION"
)
CRASH_DURABILITY_REQUIRED: Final[bool] = True
EXPLICIT_NONREQUIREMENT_PROVEN: Final[bool] = False
NONREQUIREMENT_SOURCE_FOUND: Final[bool] = False
NONREQUIREMENT_SOURCE: Final[str] = "NONE"

ATOMIC_WRITE_MODEL: Final[str] = "ENFORCED_O_APPEND_JSONL_LINE"
ATOMIC_REPLACE_REQUIRED: Final[bool] = False
ATOMIC_REPLACE_IMPLEMENTED: Final[bool] = False
ATOMIC_REPLACE_INCOMPATIBLE_WITH_APPEND_ONLY: Final[bool] = True
RENAME_ATOMIC_REPLACE_PRESENT: Final[bool] = False
APPEND_ONLY_STATUS: Final[str] = "ENFORCED_O_APPEND"

ATOMIC_WRITE_STATUS: Final[str] = "PARTIAL"
FILE_FSYNC_STATUS: Final[str] = "PRESENT"
DIRECTORY_FSYNC_STATUS: Final[str] = "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"
PROCESS_RESTART_DURABILITY: Final[str] = "BEST_EFFORT_FILE_FSYNC_NOT_FULLY_PROVEN"
HOST_CRASH_DURABILITY: Final[str] = "UNPROVEN"
FILESYSTEM_COMMIT_DURABILITY: Final[str] = "UNPROVEN"
POWER_LOSS_DURABILITY: Final[str] = "UNPROVEN"
CRASH_DURABILITY_FULLY_PROVEN: Final[bool] = False
DURABILITY_CLASS: Final[str] = "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"

DURABILITY_PROOF_SCOPE: Final[str] = "DDO_APPEND_ONLY_JSONL_LEDGER_ON_POSIX_FILESYSTEM"
PROCESS_CRASH: Final[str] = "FILE_FSYNC_PRESENT_DIRECTORY_FSYNC_ATTEMPTED_NO_HARD_GUARANTEE"
HOST_REBOOT: Final[str] = "UNPROVEN"
POWER_LOSS: Final[str] = "UNPROVEN_PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
FILESYSTEM_ASSUMPTIONS: Final[str] = "POSIX_O_APPEND_PLUS_FSYNC_NO_UNIVERSAL_DIR_DURABILITY"
OS_ASSUMPTIONS: Final[str] = "DARWIN_AND_LINUX_POSIX_NO_CROSS_FS_HARD_PROOF"
STORAGE_HARDWARE_ASSUMPTIONS: Final[str] = "UNKNOWN_NOT_ASSUMED_BARRIER_DEVICE"
ACKNOWLEDGED_WRITE_BOUNDARY: Final[str] = (
    "SUCCESSFUL_APPEND_RETURNS_ONLY_AFTER_FILE_FSYNC_AND_ATTEMPTED_DIR_FSYNC"
)
RECOVERY_PROCEDURE: Final[str] = "LOAD_HASH_CHAIN_FAIL_CLOSED_ON_TRUNCATION_CORRUPTION_DUPLICATE"
CORRUPTION_DETECTION: Final[str] = "PRESENT"
PARTIAL_WRITE_DETECTION: Final[str] = "PRESENT_ON_LOAD"
DUPLICATE_WRITE_DETECTION: Final[str] = "PRESENT"

EXISTING_STORAGE_OWNER: Final[str] = "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
NEW_STORAGE_AUTHORITY_REQUIRED: Final[bool] = False
NEW_STORAGE_AUTHORITY_CREATED: Final[bool] = False

IMPLEMENTATION_COMPLETE: Final[bool] = True
CRASH_DURABILITY_PRECONDITION_PROVEN: Final[bool] = False
OTHER_RUNTIME_PRECONDITIONS_PROVEN: Final[bool] = False
PRECONDITIONS_PROVEN: Final[bool] = False
RUNTIME_AUTHORIZATION_ELIGIBLE: Final[bool] = False
RUNTIME_AUTHORIZED: Final[bool] = False
OPERATION_STARTED: Final[bool] = False
UNATTENDED_OPERATION_STARTED: Final[bool] = False
NEXT_OWNER_GO_REQUIRED: Final[bool] = True

MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY: Final[bool] = True
DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY: Final[bool] = False
DDO_LEARNING_PRODUCTIVE_AUTHORITY: Final[bool] = False
TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE: Final[bool] = False
PRODUCTIVE_RETURN_VALUE_UNCHANGED: Final[bool] = True

AUTHORIZATION_FAILURE_REASON: Final[str] = (
    "A1_CRASH_DURABILITY_PLATFORM_FULL_GUARANTEE_STILL_NOT_PROVABLE"
)
NEXT_DDO_STEP: Final[str] = "PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1"

assert AUTHORITY_OWNER == "NONE"
assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
assert SECOND_TRADING_AUTHORITY_CREATED is False
assert CAPTURE_FAILURE_CHANGES_DECISION is False
assert A1_UNATTENDED_DURABILITY_POLICY_DEFINED is True
assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False
assert A1_TRADING_AUTHORITY is False
assert A1_EXECUTION_AUTHORITY is False
assert A1_LEARNING_AUTHORITY is False
assert A1_UNATTENDED_AUTHORITY is False
assert A1_DURABILITY_FAILURE_POLICY == "UNBOUND_NOT_AUTHORIZED"
assert A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED is False
assert A1_RUNTIME_AUTHORIZED is False
assert A1_RUNTIME_AUTHORIZATION_ELIGIBLE is False
assert A1_RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
assert A1_RUNTIME_AUTHORIZATION_SOURCE == "NONE"
assert A1_RUNTIME_CRASH_DURABILITY_FULLY_PROVEN is False
assert A1_RUNTIME_RENAME_ATOMIC_REPLACE_PRESENT is False
assert A1_RUNTIME_DURABILITY_CLASS == "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
assert A1_RUNTIME_DIRECTORY_FSYNC_STATUS == DIRECTORY_FSYNC_STATUS
assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert RUNTIME_AUTHORIZED is False
assert OPERATION_STARTED is False
assert CRASH_DURABILITY_FULLY_PROVEN is False
assert EXPLICIT_NONREQUIREMENT_PROVEN is False
assert ATOMIC_REPLACE_IMPLEMENTED is False
assert NEW_STORAGE_AUTHORITY_CREATED is False


class DdoA1CrashDurabilityAdjudicationError(Exception):
    """Fail-closed A1 crash-durability adjudication error. Not trading authority."""

    error_code = "DDO_A1_CRASH_DURABILITY_ADJUDICATION_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1:
    """Canonical A1 crash-durability adjudication. Never self-activating."""

    slice_id: str = SLICE_ID
    adjudication_class: str = ADJUDICATION_CLASS
    implementation_complete: bool = True
    crash_durability_precondition_proven: bool = False
    other_runtime_preconditions_proven: bool = False
    preconditions_proven: bool = False
    runtime_authorization_eligible: bool = False
    runtime_authorized: bool = False
    operation_started: bool = False
    unattended_operation_started: bool = False
    implementation_go_is_runtime_authorization: bool = False
    explicit_nonrequirement_proven: bool = False
    atomic_replace_required: bool = False
    atomic_replace_implemented: bool = False
    rename_atomic_replace_present: bool = False
    crash_durability_fully_proven: bool = False
    new_storage_authority_created: bool = False
    next_owner_go_required: bool = True
    atomic_write_model: str = ATOMIC_WRITE_MODEL
    file_fsync_status: str = FILE_FSYNC_STATUS
    directory_fsync_status: str = DIRECTORY_FSYNC_STATUS
    process_restart_durability: str = PROCESS_RESTART_DURABILITY
    host_crash_durability: str = HOST_CRASH_DURABILITY
    power_loss_durability: str = POWER_LOSS_DURABILITY
    durability_class: str = DURABILITY_CLASS
    authorization_failure_reason: str = AUTHORIZATION_FAILURE_REASON
    implementation_authorization_source: str = IMPLEMENTATION_AUTHORIZATION_SOURCE
    runtime_operational_authorization_source: str = RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE
    existing_storage_owner: str = EXISTING_STORAGE_OWNER

    def __post_init__(self) -> None:
        if self.slice_id != SLICE_ID:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_SLICE_ID_INVALID",
                "A1_SLICE_ID_INVALID",
            )
        if not self.implementation_complete:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
            )
        if self.adjudication_class != ADJUDICATION_CLASS:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_ADJUDICATION_CLASS_MUST_REMAIN_NOT_PROVABLE",
                "A1_ADJUDICATION_CLASS_MUST_REMAIN_NOT_PROVABLE",
            )
        forbidden_true = (
            self.crash_durability_precondition_proven,
            self.other_runtime_preconditions_proven,
            self.preconditions_proven,
            self.runtime_authorization_eligible,
            self.runtime_authorized,
            self.operation_started,
            self.unattended_operation_started,
            self.implementation_go_is_runtime_authorization,
            self.explicit_nonrequirement_proven,
            self.atomic_replace_required,
            self.atomic_replace_implemented,
            self.rename_atomic_replace_present,
            self.crash_durability_fully_proven,
            self.new_storage_authority_created,
        )
        if any(forbidden_true):
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.runtime_operational_authorization_source != "NONE":
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.durability_class != DURABILITY_CLASS:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_DURABILITY_CLASS_MUST_REMAIN_NOT_PROVABLE",
                "A1_DURABILITY_CLASS_MUST_REMAIN_NOT_PROVABLE",
            )
        if self.directory_fsync_status != DIRECTORY_FSYNC_STATUS:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_DIRECTORY_FSYNC_STATUS_INVALID",
                "A1_DIRECTORY_FSYNC_STATUS_INVALID",
            )
        if self.atomic_write_model != ATOMIC_WRITE_MODEL:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_ATOMIC_WRITE_MODEL_MUST_REMAIN_O_APPEND",
                "A1_ATOMIC_WRITE_MODEL_MUST_REMAIN_O_APPEND",
            )
        if not self.next_owner_go_required:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_NEXT_OWNER_GO_REQUIRED",
                "A1_NEXT_OWNER_GO_REQUIRED",
            )
        if A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED or A1_UNATTENDED_AUTHORITY:
            raise DdoA1CrashDurabilityAdjudicationError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )


def canonical_a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1() -> (
    DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1
):
    """Return the only valid A1 crash-durability adjudication instance."""
    return DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1()


def reject_a1_crash_durability_overclaim_v1(**flags: bool) -> None:
    """Fail closed if any caller tries to claim proven crash durability."""
    if any(bool(value) for value in flags.values()):
        raise DdoA1CrashDurabilityAdjudicationError(
            "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
        )


def a1_crash_durability_adjudication_observability_v1() -> dict[str, Any]:
    """Machine-readable adjudication stamps. Observation only. Not activation."""
    adjudication = canonical_a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1()
    return {
        "a1_crash_durability_slice_id": adjudication.slice_id,
        "a1_crash_durability_adjudication_class": adjudication.adjudication_class,
        "a1_crash_durability_implementation_complete": adjudication.implementation_complete,
        "a1_crash_durability_precondition_proven": (
            adjudication.crash_durability_precondition_proven
        ),
        "a1_other_runtime_preconditions_proven": adjudication.other_runtime_preconditions_proven,
        "a1_explicit_nonrequirement_proven": adjudication.explicit_nonrequirement_proven,
        "a1_atomic_replace_required": adjudication.atomic_replace_required,
        "a1_atomic_replace_implemented": adjudication.atomic_replace_implemented,
        "a1_atomic_write_model": adjudication.atomic_write_model,
        "a1_process_restart_durability": adjudication.process_restart_durability,
        "a1_host_crash_durability": adjudication.host_crash_durability,
        "a1_power_loss_durability": adjudication.power_loss_durability,
        "a1_crash_durability_fully_proven": adjudication.crash_durability_fully_proven,
        "a1_crash_durability_runtime_authorization_eligible": (
            adjudication.runtime_authorization_eligible
        ),
        "a1_crash_durability_runtime_authorized": adjudication.runtime_authorized,
        "a1_crash_durability_operation_started": adjudication.unattended_operation_started,
        "a1_crash_durability_authorization_failure_reason": (
            adjudication.authorization_failure_reason
        ),
        "a1_crash_durability_next_owner_go_required": adjudication.next_owner_go_required,
        "a1_crash_durability_new_storage_authority_created": (
            adjudication.new_storage_authority_created
        ),
    }

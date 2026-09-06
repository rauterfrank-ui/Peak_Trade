"""DDO A1 crash-durability proof or explicit non-provability closure v1.

Adjudicates the existing AppendOnlyDdoLedgerV0 persist path. Does not
manufacture durability_proven=True, does not create a new storage or
admission owner, and does not authorize A1 runtime.
Host-crash and power-loss durability remain UNPROVEN.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1 import (
    ATOMIC_REPLACE_IMPLEMENTED,
    ATOMIC_WRITE_MODEL,
    RENAME_ATOMIC_REPLACE_PRESENT,
)
from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    AMBIGUOUS_RETRY_ALLOWED,
    CURRENT_STAGE_DURABILITY_FAILURE_POLICY,
    DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY,
    DIRECTORY_FSYNC_STATUS,
    FILE_FSYNC_STATUS,
    UNKNOWN_PRESERVED,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_durability_to_admission_and_replay_binding_v1 import (
    ADMISSION_BINDING_STATUS,
    ADMISSION_OWNER,
    ADMISSION_OWNER_NAME,
    AUTOMATIC_RETRY_LOOP_ADDED,
    CAPTURE_OK_EQUALS_ADMISSION,
    CURRENT_STAGE_CAPTURE_FAIL_OPEN,
    EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION,
    FILE_FSYNC_POLICY,
    IDEMPOTENT_REPLAY_EQUALS_CRASH_DURABILITY_PROOF,
    NEW_ADMISSION_AUTHORITY_CREATED,
    REPLAY_AMBIGUITY_BINDING_STATUS,
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
    "PEAK_TRADE_DDO_A1_CRASH_DURABILITY_PROOF_OR_EXPLICIT_NONPROVABILITY_CLOSURE_V1"
)
IMPLEMENTATION_AUTHORIZATION_SOURCE: Final[str] = (
    "PEAK_TRADE_OWNER_GO_DDO_A1_CRASH_DURABILITY_PROOF_OR_EXPLICIT_NONPROVABILITY_CLOSURE_V1"
)
RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE: Final[str] = "NONE"
IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION: Final[bool] = False

DURABILITY_CLOSURE: Final[str] = "CURRENT_STORAGE_CONTRACT_EXHAUSTED_HOST_CRASH_DURABILITY_UNPROVEN"
CURRENT_STORAGE_OWNER: Final[str] = "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
CURRENT_STORAGE_OWNER_COUNT: Final[int] = 1
CURRENT_ADMISSION_OWNER: Final[str] = ADMISSION_OWNER_NAME
NEW_STORAGE_AUTHORITY_CREATED: Final[bool] = False
EXISTING_STORAGE_OWNER: Final[str] = CURRENT_STORAGE_OWNER

CURRENT_STORAGE_WRITE_SEQUENCE: Final[str] = (
    "VALIDATE_SERIALIZE|"
    "EXCLUSIVE_WRITER_LOCK|"
    "LOAD_EXISTING_LEDGER|"
    "DUPLICATE_OR_LINEAGE_GATE|"
    "ENVELOPE_SERIALIZE|"
    "PARENT_MKDIR|"
    "OPEN_O_APPEND|"
    "WRITE|"
    "SHORT_WRITE_CHECK|"
    "FILE_FSYNC|"
    "CLOSE|"
    "DIRECTORY_OPEN_O_RDONLY|"
    "DIRECTORY_FSYNC|"
    "DIRECTORY_CLOSE|"
    "RETURN_APPEND_RESULT|"
    "CAPTURE_CLASSIFY_ADMISSION_SEPARATE_OWNER"
)
ATOMIC_REPLACE_PRESENT: Final[bool] = False
FILE_FSYNC_PRESENT: Final[bool] = True
FILE_FSYNC_FAILURE_SEMANTICS: Final[str] = "PRESENT_FAILURE_FORBIDS_DEPENDENT_MUTATION"
DIRECTORY_FSYNC_PRESENT: Final[bool] = True
DIRECTORY_FSYNC_FAILURE_SEMANTICS: Final[str] = DIRECTORY_FSYNC_STATUS
DIRECTORY_FSYNC_FAILURE_PROPAGATES: Final[bool] = True
READBACK_OR_RECOVERY_PRESENT: Final[bool] = True
CORRUPTION_HANDLING: Final[str] = "FAIL_CLOSED_NO_SILENT_PARSE_NORMALIZATION"
PARTIAL_WRITE_HANDLING: Final[str] = (
    "SHORT_WRITE_FAILS_APPEND_TRUNCATION_FAILS_LOAD_NO_FALSE_SUCCESS"
)
TEMP_ARTIFACT_HANDLING: Final[str] = "NO_TEMP_FILE_NOT_A_COMMITTED_RECORD"
DUPLICATE_HANDLING: Final[str] = (
    "SAME_ID_SAME_CONTENT_IDEMPOTENT_REPLAY_SAME_ID_DIFFERENT_CONTENT_FAIL_CLOSED"
)
STORAGE_PLATFORM_CONTRACT: Final[str] = (
    "POSIX_O_APPEND_PLUS_FILE_FSYNC_PLUS_ATTEMPTED_DIRECTORY_FSYNC_"
    "NO_UNIVERSAL_DIR_OR_DEVICE_BARRIER_PROOF"
)
STORAGE_CONTRACT_GAPS: Final[str] = (
    "NO_ATOMIC_REPLACE|"
    "NO_WAL|"
    "NO_TEMPFILE_COMMIT|"
    "DIRECTORY_FSYNC_NO_PLATFORM_HARD_GUARANTEE|"
    "NO_HOST_KERNEL_CRASH_PROOF|"
    "NO_POWER_LOSS_PROOF|"
    "NO_DEVICE_BARRIER_PROOF"
)

PROCESS_RESTART_DURABILITY: Final[str] = "PROVEN_WITH_BOUND_ASSUMPTIONS"
PROCESS_CRASH_DURABILITY: Final[str] = "PARTIAL"
HOST_KERNEL_CRASH_DURABILITY: Final[str] = "UNPROVEN"
HOST_CRASH_DURABILITY: Final[str] = "UNPROVEN"
POWER_LOSS_DURABILITY: Final[str] = "UNPROVEN"
CRASH_DURABILITY_FULLY_PROVEN: Final[bool] = False
DURABILITY_PROVEN_TRUE_MANUFACTURABLE: Final[bool] = False
DURABILITY_CLASS: Final[str] = "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
DURABILITY_BOUND_ASSUMPTIONS: Final[str] = (
    "PROCESS_RESTART_AFTER_SUCCESSFUL_APPEND_RETURN_ASSUMES_SAME_POSIX_FILESYSTEM_"
    "PRESERVES_FILE_FSYNCED_BYTES_ACROSS_PROCESS_EXIT_WITHOUT_HOST_KERNEL_CRASH_OR_POWER_LOSS"
)
UNPROVEN_DURABILITY_SURFACES: Final[str] = (
    "HOST_KERNEL_CRASH|"
    "POWER_LOSS|"
    "DIRECTORY_ENTRY_DURABILITY_AFTER_CREATE|"
    "DEVICE_WRITE_BARRIER|"
    "CROSS_FILESYSTEM_SEMANTICS|"
    "PROCESS_CRASH_BETWEEN_WRITE_AND_FILE_FSYNC"
)

SEPARATE_STORAGE_DURABILITY_ARCHITECTURE_REQUIRED: Final[bool] = True
SEPARATE_STORAGE_DURABILITY_ARCHITECTURE_REASON: Final[str] = (
    "HOST_CRASH_OR_POWER_LOSS_PROOF_REQUIRES_WAL_OR_NEW_FILESYSTEM_CONTRACT_"
    "OR_NEW_DURABLE_OWNER_NOT_AUTHORIZED_HERE"
)

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
TRADING_AUTHORITY_CHANGED: Final[bool] = False
EXECUTION_AUTHORITY_CHANGED: Final[bool] = False
LIVE_AUTHORITY_CHANGED: Final[bool] = False

DIRECTORY_FSYNC_POLICY: Final[str] = DIRECTORY_FSYNC_STATUS
IDEMPOTENT_REPLAY_IS_CRASH_PROOF: Final[bool] = False
BLIND_RESEND_ALLOWED: Final[bool] = False
CORRUPTION_FAIL_CLOSED: Final[bool] = True
DUPLICATE_CONFLICT_FAIL_CLOSED: Final[bool] = True

FAILURE_CLASS_F0_NORMAL_COMPLETION: Final[str] = "F0_NORMAL_COMPLETION"
FAILURE_CLASS_F1_PROCESS_CRASH_BEFORE_WRITE: Final[str] = "F1_PROCESS_CRASH_BEFORE_WRITE"
FAILURE_CLASS_F2_PROCESS_CRASH_DURING_WRITE: Final[str] = "F2_PROCESS_CRASH_DURING_WRITE"
FAILURE_CLASS_F3_PROCESS_CRASH_AFTER_WRITE_BEFORE_FILE_FSYNC: Final[str] = (
    "F3_PROCESS_CRASH_AFTER_WRITE_BEFORE_FILE_FSYNC"
)
FAILURE_CLASS_F4_PROCESS_CRASH_AFTER_FILE_FSYNC_BEFORE_RENAME: Final[str] = (
    "F4_PROCESS_CRASH_AFTER_FILE_FSYNC_BEFORE_RENAME"
)
FAILURE_CLASS_F5_PROCESS_CRASH_AFTER_RENAME_BEFORE_DIRECTORY_FSYNC: Final[str] = (
    "F5_PROCESS_CRASH_AFTER_RENAME_BEFORE_DIRECTORY_FSYNC"
)
FAILURE_CLASS_F6_PROCESS_CRASH_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN: Final[str] = (
    "F6_PROCESS_CRASH_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN"
)
FAILURE_CLASS_F7_PROCESS_CRASH_AFTER_RETURN_BEFORE_DEPENDENT_MUTATION: Final[str] = (
    "F7_PROCESS_CRASH_AFTER_RETURN_BEFORE_DEPENDENT_MUTATION"
)
FAILURE_CLASS_F8_HOST_KERNEL_CRASH: Final[str] = "F8_HOST_KERNEL_CRASH_DURING_EQUIVALENT_POINTS"
FAILURE_CLASS_F9_POWER_LOSS: Final[str] = "F9_POWER_LOSS_DURING_EQUIVALENT_POINTS"
FAILURE_CLASS_F10_RESTART_WITH_TEMP_FILE: Final[str] = "F10_RESTART_WITH_TEMP_FILE"
FAILURE_CLASS_F11_RESTART_WITH_TRUNCATED_OR_CORRUPT_RECORD: Final[str] = (
    "F11_RESTART_WITH_TRUNCATED_OR_CORRUPT_RECORD"
)
FAILURE_CLASS_F12_RESTART_WITH_SAME_ID_SAME_CONTENT: Final[str] = (
    "F12_RESTART_WITH_SAME_ID_SAME_CONTENT"
)
FAILURE_CLASS_F13_RESTART_WITH_SAME_ID_DIFFERENT_CONTENT: Final[str] = (
    "F13_RESTART_WITH_SAME_ID_DIFFERENT_CONTENT"
)
FAILURE_CLASS_F14_CRASH_DURING_REPLAY_OR_RECOVERY: Final[str] = (
    "F14_CRASH_DURING_REPLAY_OR_RECOVERY"
)
FAILURE_CLASS_F15_DISK_FULL_OR_FSYNC_FAILURE: Final[str] = "F15_DISK_FULL_OR_FSYNC_FAILURE"
FAILURE_CLASS_F16_PERMISSION_OR_IO_ERROR: Final[str] = "F16_PERMISSION_OR_IO_ERROR"
FAILURE_CLASS_F17_DIRECTORY_FSYNC_UNSUPPORTED_OR_FAILURE: Final[str] = (
    "F17_DIRECTORY_FSYNC_UNSUPPORTED_OR_FAILURE"
)
FAILURE_CLASS_F18_CRASH_AFTER_PERSISTENCE_BEFORE_ADMISSION: Final[str] = (
    "F18_CRASH_AFTER_PERSISTENCE_BUT_BEFORE_ADMISSION_STATE_TRANSITION"
)

assert AUTHORITY_OWNER == "NONE"
assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
assert SECOND_TRADING_AUTHORITY_CREATED is False
assert CAPTURE_FAILURE_CHANGES_DECISION is False
assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert RUNTIME_AUTHORIZED is False
assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
assert CRASH_DURABILITY_FULLY_PROVEN is False
assert DURABILITY_PROVEN_TRUE_MANUFACTURABLE is False
assert NEW_STORAGE_AUTHORITY_CREATED is False
assert NEW_ADMISSION_AUTHORITY_CREATED is False
assert ATOMIC_REPLACE_PRESENT is False
assert ATOMIC_REPLACE_IMPLEMENTED is False
assert RENAME_ATOMIC_REPLACE_PRESENT is False
assert ATOMIC_WRITE_MODEL == "ENFORCED_O_APPEND_JSONL_LINE"
assert HOST_CRASH_DURABILITY == "UNPROVEN"
assert HOST_KERNEL_CRASH_DURABILITY == "UNPROVEN"
assert POWER_LOSS_DURABILITY == "UNPROVEN"
assert AMBIGUOUS_RETRY_ALLOWED is False
assert UNKNOWN_PRESERVED is True
assert AUTOMATIC_RETRY_LOOP_ADDED is False
assert CAPTURE_OK_EQUALS_ADMISSION is False
assert CURRENT_STAGE_CAPTURE_FAIL_OPEN is True
assert DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY == "FORBIDDEN"
assert IDEMPOTENT_REPLAY_EQUALS_CRASH_DURABILITY_PROOF is False
assert IDEMPOTENT_REPLAY_IS_CRASH_PROOF is False
assert ADMISSION_BINDING_STATUS == "BOUND_FAIL_CLOSED"
assert REPLAY_AMBIGUITY_BINDING_STATUS == "BOUND_WITHOUT_AUTOMATIC_RETRY"
assert EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION.startswith("BOUND_FAIL_CLOSED")
assert ADMISSION_OWNER is reject_a1_dependent_mutation_on_unproven_durability_v1
assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
assert SEPARATE_STORAGE_DURABILITY_ARCHITECTURE_REQUIRED is True
assert DURABILITY_CLOSURE == ("CURRENT_STORAGE_CONTRACT_EXHAUSTED_HOST_CRASH_DURABILITY_UNPROVEN")


class DdoA1CrashDurabilityProofOrNonprovabilityClosureError(Exception):
    """Fail-closed A1 crash-durability closure error. Not trading authority."""

    error_code = "DDO_A1_CRASH_DURABILITY_PROOF_OR_NONPROVABILITY_CLOSURE_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class DdoA1FailureClassAdjudicationV1:
    """One failure class. Not a crash-safety slogan."""

    failure_class: str
    expected_durable_artifacts: str
    known_vs_unknown: str
    replay_behavior: str
    admission_behavior: str
    dependent_mutation_eligibility: str
    duplicate_mutation_possible: str
    evidence_loss_possible: str
    proof_source: str
    rename_step_applicable: bool

    def __post_init__(self) -> None:
        if self.dependent_mutation_eligibility != "FORBIDDEN":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if self.admission_behavior == "ADMITTED":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )


@dataclass(frozen=True)
class DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1:
    """Canonical A1 crash-durability closure. Never self-activating."""

    slice_id: str = SLICE_ID
    durability_closure: str = DURABILITY_CLOSURE
    implementation_complete: bool = True
    process_restart_durability: str = PROCESS_RESTART_DURABILITY
    process_crash_durability: str = PROCESS_CRASH_DURABILITY
    host_kernel_crash_durability: str = HOST_KERNEL_CRASH_DURABILITY
    host_crash_durability: str = HOST_CRASH_DURABILITY
    power_loss_durability: str = POWER_LOSS_DURABILITY
    crash_durability_fully_proven: bool = False
    durability_proven_true_manufacturable: bool = False
    atomic_replace_present: bool = False
    file_fsync_present: bool = True
    directory_fsync_present: bool = True
    directory_fsync_hard_guarantee: bool = False
    runtime_authorization_eligible: bool = False
    runtime_authorized: bool = False
    operation_started: bool = False
    unattended_operation_started: bool = False
    implementation_go_is_runtime_authorization: bool = False
    new_storage_authority_created: bool = False
    new_admission_authority_created: bool = False
    separate_storage_durability_architecture_required: bool = True
    dependent_mutation_on_unproven_durability: str = DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY
    next_owner_go_required: bool = True
    implementation_authorization_source: str = IMPLEMENTATION_AUTHORIZATION_SOURCE
    runtime_operational_authorization_source: str = RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE
    existing_storage_owner: str = EXISTING_STORAGE_OWNER
    current_admission_owner: str = CURRENT_ADMISSION_OWNER
    file_fsync_status: str = FILE_FSYNC_STATUS
    file_fsync_policy: str = FILE_FSYNC_POLICY
    directory_fsync_status: str = DIRECTORY_FSYNC_STATUS
    directory_fsync_policy: str = DIRECTORY_FSYNC_POLICY
    durability_class: str = DURABILITY_CLASS
    a1_durability_failure_policy: str = A1_DURABILITY_FAILURE_POLICY
    current_stage_durability_failure_policy: str = CURRENT_STAGE_DURABILITY_FAILURE_POLICY
    next_ddo_step: str = NEXT_DDO_STEP

    def __post_init__(self) -> None:
        if self.slice_id != SLICE_ID:
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_SLICE_ID_INVALID",
                "A1_SLICE_ID_INVALID",
            )
        if not self.implementation_complete:
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
                "A1_IMPLEMENTATION_COMPLETE_REQUIRED",
            )
        if self.durability_closure != DURABILITY_CLOSURE:
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_DURABILITY_CLOSURE_MUST_REMAIN_HOST_CRASH_UNPROVEN",
                "A1_DURABILITY_CLOSURE_MUST_REMAIN_HOST_CRASH_UNPROVEN",
            )
        if self.process_restart_durability != "PROVEN_WITH_BOUND_ASSUMPTIONS":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_PROCESS_RESTART_DURABILITY_INVALID",
                "A1_PROCESS_RESTART_DURABILITY_INVALID",
            )
        if self.process_crash_durability != "PARTIAL":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_PROCESS_CRASH_DURABILITY_INVALID",
                "A1_PROCESS_CRASH_DURABILITY_INVALID",
            )
        if self.host_crash_durability != "UNPROVEN" or self.host_kernel_crash_durability != (
            "UNPROVEN"
        ):
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if self.power_loss_durability != "UNPROVEN":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        forbidden_true = (
            self.crash_durability_fully_proven,
            self.durability_proven_true_manufacturable,
            self.atomic_replace_present,
            self.directory_fsync_hard_guarantee,
            self.runtime_authorization_eligible,
            self.runtime_authorized,
            self.operation_started,
            self.unattended_operation_started,
            self.implementation_go_is_runtime_authorization,
            self.new_storage_authority_created,
            self.new_admission_authority_created,
        )
        if any(forbidden_true):
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
                "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            )
        if not self.separate_storage_durability_architecture_required:
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_HOST_CRASH_ARCHITECTURE_REQUIREMENT_MUST_REMAIN_TRUE",
                "A1_HOST_CRASH_ARCHITECTURE_REQUIREMENT_MUST_REMAIN_TRUE",
            )
        if self.runtime_operational_authorization_source != "NONE":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.dependent_mutation_on_unproven_durability != "FORBIDDEN":
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
                "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
            )
        if not self.next_owner_go_required:
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_NEXT_OWNER_GO_REQUIRED",
                "A1_NEXT_OWNER_GO_REQUIRED",
            )
        if not self.file_fsync_present or not self.directory_fsync_present:
            raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
                "A1_FSYNC_PRESENCE_INVALID",
                "A1_FSYNC_PRESENCE_INVALID",
            )


def canonical_a1_crash_durability_proof_or_explicit_nonprovability_closure_v1() -> (
    DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1
):
    """Return the only valid A1 crash-durability closure instance."""
    return DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1()


def reject_a1_crash_durability_full_proof_overclaim_v1(**flags: bool) -> None:
    """Fail closed if any caller tries to claim proven host-crash durability."""
    if any(bool(value) for value in flags.values()):
        raise DdoA1CrashDurabilityProofOrNonprovabilityClosureError(
            "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
            "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
        )


def _row(
    *,
    failure_class: str,
    expected_durable_artifacts: str,
    known_vs_unknown: str,
    replay_behavior: str,
    admission_behavior: str,
    duplicate_mutation_possible: str,
    evidence_loss_possible: str,
    proof_source: str,
    rename_step_applicable: bool = False,
) -> DdoA1FailureClassAdjudicationV1:
    return DdoA1FailureClassAdjudicationV1(
        failure_class=failure_class,
        expected_durable_artifacts=expected_durable_artifacts,
        known_vs_unknown=known_vs_unknown,
        replay_behavior=replay_behavior,
        admission_behavior=admission_behavior,
        dependent_mutation_eligibility="FORBIDDEN",
        duplicate_mutation_possible=duplicate_mutation_possible,
        evidence_loss_possible=evidence_loss_possible,
        proof_source=proof_source,
        rename_step_applicable=rename_step_applicable,
    )


def a1_crash_durability_failure_model_v1() -> tuple[DdoA1FailureClassAdjudicationV1, ...]:
    """Explicit F0-F18 matrix. Not a claim that the ledger is crash safe."""
    no_rename_note = "NO_RENAME_STEP_ON_O_APPEND_LEDGER"
    return (
        _row(
            failure_class=FAILURE_CLASS_F0_NORMAL_COMPLETION,
            expected_durable_artifacts="ONE_JSONL_LINE_AFTER_FILE_FSYNC_AND_ATTEMPTED_DIR_FSYNC",
            known_vs_unknown="KNOWN_APPEND_ACKNOWLEDGED_CRASH_DURABILITY_UNPROVEN",
            replay_behavior="IDEMPOTENT_REPLAY_ON_SAME_ID_SAME_CONTENT",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_SECOND_LEDGER_ROW_ON_IDEMPOTENT_REPLAY",
            evidence_loss_possible="NOT_ON_THIS_CLASS",
            proof_source="LEDGER_APPEND_RETURN_PLUS_REOPEN_READ",
        ),
        _row(
            failure_class=FAILURE_CLASS_F1_PROCESS_CRASH_BEFORE_WRITE,
            expected_durable_artifacts="NO_NEW_LEDGER_LINE",
            known_vs_unknown="KNOWN_ABSENT",
            replay_behavior="FRESH_APPEND_ALLOWED_SAME_RECORD",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_BECAUSE_NO_PRIOR_COMMIT",
            evidence_loss_possible="NO_DURABLE_EVIDENCE_CREATED",
            proof_source="FAULT_INJECTION_BEFORE_WRITE",
        ),
        _row(
            failure_class=FAILURE_CLASS_F2_PROCESS_CRASH_DURING_WRITE,
            expected_durable_artifacts="ABSENT_OR_TRUNCATED_LINE",
            known_vs_unknown="KNOWN_CORRUPT_OR_ABSENT_IF_NO_TRAILING_NEWLINE",
            replay_behavior="LOAD_FAIL_CLOSED_NO_SILENT_PARSE",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_UNTIL_CORRUPT_LEDGER_RECOVERED_OUT_OF_BAND",
            evidence_loss_possible="YES_PARTIAL_BYTES_NOT_A_RECORD",
            proof_source="FAULT_INJECTION_PARTIAL_WRITE_PLUS_LOAD",
        ),
        _row(
            failure_class=FAILURE_CLASS_F3_PROCESS_CRASH_AFTER_WRITE_BEFORE_FILE_FSYNC,
            expected_durable_artifacts="UNKNOWN_MAY_BE_VISIBLE_IN_PAGE_CACHE_NOT_DURABILITY_PROOF",
            known_vs_unknown="UNKNOWN",
            replay_behavior="IF_LINE_COMPLETE_IDEMPOTENT_ELSE_LOAD_FAIL_CLOSED",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_AUTOMATIC_RETRY",
            evidence_loss_possible="YES_IF_OS_DROPS_UNFSYNCED_BYTES",
            proof_source="FAULT_INJECTION_AFTER_WRITE_BEFORE_FILE_FSYNC",
        ),
        _row(
            failure_class=FAILURE_CLASS_F4_PROCESS_CRASH_AFTER_FILE_FSYNC_BEFORE_RENAME,
            expected_durable_artifacts=no_rename_note,
            known_vs_unknown="NOT_APPLICABLE_NO_RENAME",
            replay_behavior="NOT_APPLICABLE_NO_RENAME",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NOT_APPLICABLE_NO_RENAME",
            evidence_loss_possible="NOT_APPLICABLE_NO_RENAME",
            proof_source="LEDGER_SOURCE_HAS_NO_OS_REPLACE_OR_RENAME_OF_LEDGER_CONTENT",
            rename_step_applicable=False,
        ),
        _row(
            failure_class=FAILURE_CLASS_F5_PROCESS_CRASH_AFTER_RENAME_BEFORE_DIRECTORY_FSYNC,
            expected_durable_artifacts=(
                "MAPPED_TO_AFTER_FILE_FSYNC_BEFORE_DIRECTORY_FSYNC_NO_RENAME"
            ),
            known_vs_unknown="UNKNOWN_DIRECTORY_ENTRY_FOR_NEW_FILE_NOT_PLATFORM_PROVEN",
            replay_behavior="IF_FILE_VISIBLE_LOAD_MAY_SEE_RECORD",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_AUTOMATIC_RETRY",
            evidence_loss_possible="UNKNOWN_IF_NEW_FILE_DIR_ENTRY_NOT_STABLE",
            proof_source="FAULT_INJECTION_AFTER_CLOSE_BEFORE_DIRECTORY_FSYNC",
        ),
        _row(
            failure_class=FAILURE_CLASS_F6_PROCESS_CRASH_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN,
            expected_durable_artifacts="LINE_PRESENT_RETURN_PATH_NOT_COMPLETED",
            known_vs_unknown="KNOWN_ARTIFACT_UNKNOWN_CALLER_ACK",
            replay_behavior="REOPEN_SEES_RECORD_IDEMPOTENT_REPLAY",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_SECOND_LEDGER_ROW_ON_SAME_ID_SAME_CONTENT",
            evidence_loss_possible="NOT_EXPECTED_FOR_PROCESS_RESTART",
            proof_source="FAULT_INJECTION_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN",
        ),
        _row(
            failure_class=FAILURE_CLASS_F7_PROCESS_CRASH_AFTER_RETURN_BEFORE_DEPENDENT_MUTATION,
            expected_durable_artifacts="LINE_PRESENT",
            known_vs_unknown="KNOWN_APPEND_ACKNOWLEDGED_STILL_NOT_HOST_CRASH_PROOF",
            replay_behavior="IDEMPOTENT_REPLAY",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO",
            evidence_loss_possible="NOT_EXPECTED_FOR_PROCESS_RESTART",
            proof_source="APPEND_RETURN_PLUS_ADMISSION_OWNER",
        ),
        _row(
            failure_class=FAILURE_CLASS_F8_HOST_KERNEL_CRASH,
            expected_durable_artifacts="UNKNOWN",
            known_vs_unknown="UNKNOWN",
            replay_behavior="UNKNOWN_MUST_NOT_BECOME_SUCCESS",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="UNKNOWN_NOT_AUTHORIZED_TO_RETRY_BLINDLY",
            evidence_loss_possible="UNKNOWN",
            proof_source="NONE_NO_HOST_KERNEL_CRASH_HARNESS_NO_PLATFORM_HARD_GUARANTEE",
        ),
        _row(
            failure_class=FAILURE_CLASS_F9_POWER_LOSS,
            expected_durable_artifacts="UNKNOWN",
            known_vs_unknown="UNKNOWN",
            replay_behavior="UNKNOWN_MUST_NOT_BECOME_SUCCESS",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="UNKNOWN_NOT_AUTHORIZED_TO_RETRY_BLINDLY",
            evidence_loss_possible="UNKNOWN",
            proof_source="NONE_NO_POWER_LOSS_HARNESS_NO_DEVICE_BARRIER_PROOF",
        ),
        _row(
            failure_class=FAILURE_CLASS_F10_RESTART_WITH_TEMP_FILE,
            expected_durable_artifacts="NO_TEMP_COMMIT_PATH",
            known_vs_unknown="NOT_APPLICABLE_NO_TEMP_FILE",
            replay_behavior="TEMP_MUST_NOT_BE_TREATED_AS_COMMITTED_RECORD",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NOT_APPLICABLE",
            evidence_loss_possible="NOT_APPLICABLE",
            proof_source="LEDGER_SOURCE_HAS_NO_TMP_OR_REPLACE",
        ),
        _row(
            failure_class=FAILURE_CLASS_F11_RESTART_WITH_TRUNCATED_OR_CORRUPT_RECORD,
            expected_durable_artifacts="UNREADABLE_LEDGER",
            known_vs_unknown="KNOWN_FAILURE",
            replay_behavior="LOAD_FAIL_CLOSED_NO_EMPTY_SUCCESS",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO",
            evidence_loss_possible="YES_UNTIL_OUT_OF_BAND_RECOVERY",
            proof_source="LOAD_MISSING_NEWLINE_MALFORMED_HASH_MISMATCH_TESTS",
        ),
        _row(
            failure_class=FAILURE_CLASS_F12_RESTART_WITH_SAME_ID_SAME_CONTENT,
            expected_durable_artifacts="ONE_LEDGER_ROW",
            known_vs_unknown="KNOWN_IDEMPOTENT_NOT_CRASH_PROOF",
            replay_behavior="IDEMPOTENT_REPLAY_NO_SECOND_ROW",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO",
            evidence_loss_possible="NO",
            proof_source="REOPEN_APPEND_SAME_PAYLOAD",
        ),
        _row(
            failure_class=FAILURE_CLASS_F13_RESTART_WITH_SAME_ID_DIFFERENT_CONTENT,
            expected_durable_artifacts="EXISTING_ROW_UNCHANGED",
            known_vs_unknown="KNOWN_CONFLICT",
            replay_behavior="FAIL_CLOSED_DUPLICATE_CONFLICT",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO",
            evidence_loss_possible="NO",
            proof_source="REOPEN_APPEND_DIFFERENT_PAYLOAD_SAME_ID",
        ),
        _row(
            failure_class=FAILURE_CLASS_F14_CRASH_DURING_REPLAY_OR_RECOVERY,
            expected_durable_artifacts="UNCHANGED_EXISTING_LEDGER",
            known_vs_unknown="KNOWN_LOAD_IS_READ_ONLY",
            replay_behavior="RESTART_LOAD_AGAIN_NO_WRITE_ON_PURE_READ",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_READ_DOES_NOT_APPEND",
            evidence_loss_possible="NO_FROM_READ_PATH",
            proof_source="READ_ALL_AND_VERIFY_INTEGRITY_ARE_SIDE_EFFECT_FREE",
        ),
        _row(
            failure_class=FAILURE_CLASS_F15_DISK_FULL_OR_FSYNC_FAILURE,
            expected_durable_artifacts="UNKNOWN_IF_WRITE_PRECEDED_FAILURE",
            known_vs_unknown="UNKNOWN_OR_KNOWN_FAILURE",
            replay_behavior="NO_AMBIGUOUS_AUTOMATIC_RETRY",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_AUTOMATIC_RETRY",
            evidence_loss_possible="YES_IF_WRITE_DID_NOT_COMPLETE",
            proof_source="FAULT_INJECTION_ENOSPC_AND_FILE_FSYNC_EIO",
        ),
        _row(
            failure_class=FAILURE_CLASS_F16_PERMISSION_OR_IO_ERROR,
            expected_durable_artifacts="NO_FALSE_SUCCESS",
            known_vs_unknown="KNOWN_FAILURE",
            replay_behavior="NO_AUTOMATIC_RETRY",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO",
            evidence_loss_possible="YES_IF_WRITE_DENIED",
            proof_source="CLASSIFY_OSERROR_PERMISSION_ACCESS",
        ),
        _row(
            failure_class=FAILURE_CLASS_F17_DIRECTORY_FSYNC_UNSUPPORTED_OR_FAILURE,
            expected_durable_artifacts="FILE_BYTES_MAY_EXIST_DIR_DURABILITY_UNPROVEN",
            known_vs_unknown="UNKNOWN",
            replay_behavior="IF_LINE_PRESENT_IDEMPOTENT_ELSE_ABSENT",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_AUTOMATIC_RETRY",
            evidence_loss_possible="UNKNOWN_FOR_HOST_CRASH",
            proof_source="FAULT_INJECTION_DIRECTORY_FSYNC_MUST_NOT_BECOME_HOST_CRASH_PROOF",
        ),
        _row(
            failure_class=FAILURE_CLASS_F18_CRASH_AFTER_PERSISTENCE_BEFORE_ADMISSION,
            expected_durable_artifacts="LINE_MAY_EXIST_ADMISSION_NEVER_GRANTED_BY_CAPTURE_OK",
            known_vs_unknown="KNOWN_CAPTURE_OK_IS_NOT_ADMISSION",
            replay_behavior="RECOVERY_MUST_NOT_DUPLICATE_AUTHORITY_RELEVANT_MUTATION",
            admission_behavior="REJECTED_FAIL_CLOSED",
            duplicate_mutation_possible="NO_BECAUSE_DEPENDENT_MUTATION_FORBIDDEN",
            evidence_loss_possible="NOT_FROM_ADMISSION_SEAM",
            proof_source="ADMISSION_OWNER_PLUS_CAPTURE_CLASSIFICATION",
        ),
    )


def a1_crash_durability_failure_model_by_id_v1() -> Mapping[str, DdoA1FailureClassAdjudicationV1]:
    return {row.failure_class: row for row in a1_crash_durability_failure_model_v1()}


def a1_crash_durability_proof_or_nonprovability_observability_v1() -> dict[str, Any]:
    """Machine-readable closure stamps. Observation only. Not activation."""
    closure = canonical_a1_crash_durability_proof_or_explicit_nonprovability_closure_v1()
    return {
        "a1_crash_proof_slice_id": closure.slice_id,
        "a1_crash_proof_durability_closure": closure.durability_closure,
        "a1_crash_proof_implementation_complete": closure.implementation_complete,
        "a1_crash_proof_process_restart_durability": closure.process_restart_durability,
        "a1_crash_proof_process_crash_durability": closure.process_crash_durability,
        "a1_crash_proof_host_kernel_crash_durability": closure.host_kernel_crash_durability,
        "a1_crash_proof_host_crash_durability": closure.host_crash_durability,
        "a1_crash_proof_power_loss_durability": closure.power_loss_durability,
        "a1_crash_proof_crash_durability_fully_proven": closure.crash_durability_fully_proven,
        "a1_crash_proof_durability_proven_true_manufacturable": (
            closure.durability_proven_true_manufacturable
        ),
        "a1_crash_proof_atomic_replace_present": closure.atomic_replace_present,
        "a1_crash_proof_runtime_authorization_eligible": (closure.runtime_authorization_eligible),
        "a1_crash_proof_runtime_authorized": closure.runtime_authorized,
        "a1_crash_proof_unattended_operation_started": (closure.unattended_operation_started),
        "a1_crash_proof_new_storage_authority_created": (closure.new_storage_authority_created),
        "a1_crash_proof_new_admission_authority_created": (closure.new_admission_authority_created),
        "a1_crash_proof_separate_storage_architecture_required": (
            closure.separate_storage_durability_architecture_required
        ),
        "a1_crash_proof_dependent_mutation_on_unproven_durability": (
            closure.dependent_mutation_on_unproven_durability
        ),
        "a1_crash_proof_next_owner_go_required": closure.next_owner_go_required,
    }


__all__ = [
    "ATOMIC_REPLACE_PRESENT",
    "CORRUPTION_FAIL_CLOSED",
    "CRASH_DURABILITY_FULLY_PROVEN",
    "CURRENT_ADMISSION_OWNER",
    "CURRENT_STORAGE_OWNER",
    "CURRENT_STORAGE_WRITE_SEQUENCE",
    "DIRECTORY_FSYNC_FAILURE_SEMANTICS",
    "DURABILITY_CLOSURE",
    "DURABILITY_PROVEN_TRUE_MANUFACTURABLE",
    "DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1",
    "DdoA1CrashDurabilityProofOrNonprovabilityClosureError",
    "DdoA1FailureClassAdjudicationV1",
    "HOST_CRASH_DURABILITY",
    "HOST_KERNEL_CRASH_DURABILITY",
    "NEW_STORAGE_AUTHORITY_CREATED",
    "POWER_LOSS_DURABILITY",
    "PROCESS_CRASH_DURABILITY",
    "PROCESS_RESTART_DURABILITY",
    "SEPARATE_STORAGE_DURABILITY_ARCHITECTURE_REQUIRED",
    "SLICE_ID",
    "a1_crash_durability_failure_model_by_id_v1",
    "a1_crash_durability_failure_model_v1",
    "a1_crash_durability_proof_or_nonprovability_observability_v1",
    "canonical_a1_crash_durability_proof_or_explicit_nonprovability_closure_v1",
    "reject_a1_crash_durability_full_proof_overclaim_v1",
]

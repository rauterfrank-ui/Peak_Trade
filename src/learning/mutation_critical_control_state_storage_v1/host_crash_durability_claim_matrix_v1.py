"""Explicit durability claim matrix for mutation-critical control state.

HOST_CRASH_DURABILITY is not derived from PROCESS_KILL_DURABILITY.
POWER_LOSS_DURABILITY remains UNPROVEN in this workpackage.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from src.learning.mutation_critical_control_state_storage_v1.durability_primitives_v1 import (
    file_durability_primitive_name_v1,
)


@dataclass(frozen=True)
class DurabilityClaimV1:
    claim: str
    required_mechanism: str
    current_implementation: str
    current_test: str
    failure_model: str
    proven: bool
    evidence: str
    gap: str
    overclaim_risk: str


def _claim(
    *,
    claim: str,
    required_mechanism: str,
    current_implementation: str,
    current_test: str,
    failure_model: str,
    proven: bool,
    evidence: str,
    gap: str,
    overclaim_risk: str,
) -> DurabilityClaimV1:
    return DurabilityClaimV1(
        claim=claim,
        required_mechanism=required_mechanism,
        current_implementation=current_implementation,
        current_test=current_test,
        failure_model=failure_model,
        proven=proven,
        evidence=evidence,
        gap=gap,
        overclaim_risk=overclaim_risk,
    )


PROCESS_RESTART_DURABILITY_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="PROCESS_RESTART_DURABILITY",
    required_mechanism=(
        "COMMIT_FRAME_PLUS_FILE_DURABILITY_SYSCALL_THEN_REOPEN_READS_SAME_IDENTITY"
    ),
    current_implementation=(
        "MutationCriticalControlStateWalAdapterV1.commit writes COMMIT frame, "
        "requests file durability, attempts directory durability, then reopen "
        "reconstructs committed records"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_wal_adapter_v1.py"
        "::test_clean_reopen_and_restart_after_successful_commit"
    ),
    failure_model="PROCESS_EXIT_AFTER_SUCCESSFUL_COMMIT_RETURN_NO_HOST_CRASH",
    proven=True,
    evidence=(
        "in-process close/reopen plus OS-process SIGKILL after commit; "
        "bound assumption that the same POSIX filesystem preserves "
        "durability-syscall-returned bytes across process exit"
    ),
    gap="Does not cover host-kernel crash or power-loss",
    overclaim_risk="Calling process-restart evidence a host-crash proof",
)

PROCESS_KILL_DURABILITY_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="PROCESS_KILL_DURABILITY",
    required_mechanism=("OS_SIGKILL_BEFORE_OR_AFTER_COMMIT_BOUNDARY_THEN_NEW_PROCESS_REOPEN"),
    current_implementation=(
        "tests/learning/_ddo_a1_control_state_wal_process_child_v1.py plus "
        "SIGKILL after commit, after prepare, and before prepare"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_"
        "durable_storage_crash_reproof_v1.py"
    ),
    failure_model="OS_PROCESS_SIGKILL_NOT_HOST_KERNEL_CRASH",
    proven=True,
    evidence="subprocess SIGKILL then adapter reopen in parent process",
    gap="SIGKILL is not a host-kernel crash and is not power-loss",
    overclaim_risk="PROCESS_KILL_IS_HOST_CRASH_PROOF",
)

HOST_CRASH_DURABILITY_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="HOST_CRASH_DURABILITY",
    required_mechanism=("HOST_KERNEL_CRASH_OR_EQUIVALENT_STABLE_MEDIA_PROOF_AFTER_COMMIT_POINT"),
    current_implementation=(
        "file durability via "
        + file_durability_primitive_name_v1()
        + " when available else OS_FSYNC; directory durability attempted after "
        "header/journal create and after prepare/commit; no kernel-crash harness"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_host_crash_durability_closure_v1.py"
        "::test_host_crash_durability_remains_unproven_after_syscall_success"
    ),
    failure_model="F8_HOST_KERNEL_CRASH_DURING_EQUIVALENT_POINTS",
    proven=False,
    evidence=("local syscall probe and unit/SIGKILL tests; none induce a host-kernel crash"),
    gap=(
        "NO_HOST_KERNEL_CRASH_HARNESS|NO_DEVICE_WRITE_BARRIER_PROOF|"
        "SYSCALL_SUCCESS_IS_NOT_STABLE_MEDIA_PROOF"
    ),
    overclaim_risk=(
        "Treating F_FULLFSYNC or os.fsync success, POSIX docs, or SIGKILL as host-crash proof"
    ),
)

POWER_LOSS_DURABILITY_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="POWER_LOSS_DURABILITY",
    required_mechanism="POWER_LOSS_OR_EQUIVALENT_DEVICE_CACHE_FLUSH_PROOF",
    current_implementation="Not implemented. Not attempted in this workpackage.",
    current_test="none_power_loss_harness",
    failure_model="F9_POWER_LOSS_DURING_EQUIVALENT_POINTS",
    proven=False,
    evidence="explicit non-attempt; POWER_LOSS_PROOF_ENVIRONMENT_PRESENT=false",
    gap="NO_POWER_LOSS_HARNESS|NO_DEVICE_CACHE_FLUSH_PROOF",
    overclaim_risk="Deriving power-loss from host-crash or fsync success",
)

FILESYSTEM_CORRUPTION_TOLERANCE_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="FILESYSTEM_CORRUPTION_TOLERANCE",
    required_mechanism="DETECT_CORRUPT_STATE_AND_FAIL_CLOSED_NO_SILENT_REPAIR",
    current_implementation=(
        "frame magic, length prefix, SHA-256 trailer, frame_hash, schema/version, "
        "header owner/medium checks"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_wal_adapter_v1.py"
        "::test_corrupt_record_fail_closed"
    ),
    failure_model="F11_RESTART_WITH_TRUNCATED_OR_CORRUPT_RECORD",
    proven=True,
    evidence="bit-flip of payload and commit frame fails open() closed",
    gap="Detection only; no repair and no host-crash origin proof",
    overclaim_risk="Calling fail-closed detection crash durability",
)

TORN_WRITE_DETECTION_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="TORN_WRITE_DETECTION",
    required_mechanism="LENGTH_PREFIXED_FRAME_SCAN_CLASSIFIES_PARTIAL_LAST_FRAME",
    current_implementation="WAL scanner returns torn=True on short trailing frame",
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_wal_adapter_v1.py"
        "::test_failure_during_prepare_is_incomplete_not_committed"
    ),
    failure_model="F2_PROCESS_CRASH_DURING_WRITE",
    proven=True,
    evidence="partial_write_then_raise at prepare/payload/commit write boundaries",
    gap="Injection is in-process; not a host-crash torn-write proof",
    overclaim_risk="Equating torn-write classification with durable commit",
)

ATOMIC_REPLACEMENT_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="ATOMIC_REPLACEMENT",
    required_mechanism="SAME_FILESYSTEM_TEMP_WRITE_THEN_ATOMIC_REPLACE_THEN_DIR_DURABILITY",
    current_implementation=(
        "NOT used. Bound protocol is PREPARE_PAYLOAD_THEN_COMMIT_FRAME append-only WAL"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_"
        "durable_storage_crash_reproof_v1.py"
        "::test_reproof_does_not_create_second_storage_authority_or_atomic_replace"
    ),
    failure_model="F4_F5_ATOMIC_REPLACE_NOT_IN_BOUND_PROTOCOL",
    proven=False,
    evidence="ATOMIC_REPLACE_INTRODUCED=false; os.replace probe is capability-only",
    gap="WAL commit identity is the COMMIT frame, not a directory rename",
    overclaim_risk="Claiming atomic replace while using append-only frames",
)

DIRECTORY_ENTRY_DURABILITY_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="DIRECTORY_ENTRY_DURABILITY",
    required_mechanism=(
        "DIRECTORY_DURABILITY_SYSCALL_AFTER_CREATE_AND_AFTER_COMMIT_WITH_STABLE_MEDIA_PROOF"
    ),
    current_implementation=(
        "directory durability syscall after HEADER create, new journal create, "
        "prepare, and commit; commit return fail-closes if the attempt fails"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_wal_adapter_v1.py"
        "::test_directory_fsync_failure_is_unknown_not_committed_success"
    ),
    failure_model="F5_AFTER_PUBLICATION_BEFORE_DIRECTORY_DURABILITY",
    proven=False,
    evidence="syscall invoked and fail-closed on error; no host-crash harness",
    gap="NO_PLATFORM_HARD_GUARANTEE|NO_HOST_CRASH_PROOF_OF_DIRECTORY_ENTRY",
    overclaim_risk="Treating directory fsync/F_FULLFSYNC success as proven entry durability",
)

RESTART_STATE_RECONSTRUCTION_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="RESTART_STATE_RECONSTRUCTION",
    required_mechanism="DETERMINISTIC_FRAME_SCAN_REBUILDS_COMMITTED_B_C_D_IDENTITY",
    current_implementation="open() scans journal and installs only complete PREPARE+PAYLOAD+COMMIT",
    current_test=(
        "tests/learning/test_ddo_a1_mutation_critical_control_state_wal_adapter_v1.py"
        "::test_startup_reconstruction_preserves_b_c_d_classes"
    ),
    failure_model="PROCESS_RESTART_AFTER_CLEAN_COMMIT",
    proven=True,
    evidence="reopen loads B/C/D records with exact record_id and content_hash",
    gap="Reconstruction after host-crash/power-loss is unproven",
    overclaim_risk="Calling restart reconstruction a host-crash proof",
)

AMBIGUOUS_MUTATION_DETECTION_CLAIM: Final[DurabilityClaimV1] = _claim(
    claim="AMBIGUOUS_MUTATION_DETECTION",
    required_mechanism=(
        "INCOMPLETE_OR_UNKNOWN_COMMIT_DENIES_DEPENDENT_MUTATION_NO_AUTOMATIC_RETRY"
    ),
    current_implementation=(
        "incomplete tx classified and not applied; directory-durability failure "
        "raises UNKNOWN in-process; A1 admission owner forbids dependent mutation "
        "while host-crash unproven"
    ),
    current_test=(
        "tests/learning/test_ddo_a1_host_crash_durability_closure_v1.py"
        "::test_k_incomplete_restart_denies_dependent_mutation"
    ),
    failure_model="F7_F18_AFTER_PERSISTENCE_BEFORE_DEPENDENT_MUTATION",
    proven=True,
    evidence="incomplete reopen plus reject_a1_dependent_mutation_on_unproven_durability_v1",
    gap="In-process directory-fsync UNKNOWN is not a durable ambiguity bit after restart",
    overclaim_risk="Treating recovered COMMIT frames as host-crash-proven committed state",
)

DURABILITY_CLAIM_MATRIX_V1: Final[Mapping[str, DurabilityClaimV1]] = MappingProxyType(
    {
        PROCESS_RESTART_DURABILITY_CLAIM.claim: PROCESS_RESTART_DURABILITY_CLAIM,
        PROCESS_KILL_DURABILITY_CLAIM.claim: PROCESS_KILL_DURABILITY_CLAIM,
        HOST_CRASH_DURABILITY_CLAIM.claim: HOST_CRASH_DURABILITY_CLAIM,
        POWER_LOSS_DURABILITY_CLAIM.claim: POWER_LOSS_DURABILITY_CLAIM,
        FILESYSTEM_CORRUPTION_TOLERANCE_CLAIM.claim: FILESYSTEM_CORRUPTION_TOLERANCE_CLAIM,
        TORN_WRITE_DETECTION_CLAIM.claim: TORN_WRITE_DETECTION_CLAIM,
        ATOMIC_REPLACEMENT_CLAIM.claim: ATOMIC_REPLACEMENT_CLAIM,
        DIRECTORY_ENTRY_DURABILITY_CLAIM.claim: DIRECTORY_ENTRY_DURABILITY_CLAIM,
        RESTART_STATE_RECONSTRUCTION_CLAIM.claim: RESTART_STATE_RECONSTRUCTION_CLAIM,
        AMBIGUOUS_MUTATION_DETECTION_CLAIM.claim: AMBIGUOUS_MUTATION_DETECTION_CLAIM,
    }
)

REQUIRED_CLAIM_NAMES: Final[tuple[str, ...]] = (
    "PROCESS_RESTART_DURABILITY",
    "PROCESS_KILL_DURABILITY",
    "HOST_CRASH_DURABILITY",
    "POWER_LOSS_DURABILITY",
    "FILESYSTEM_CORRUPTION_TOLERANCE",
    "TORN_WRITE_DETECTION",
    "ATOMIC_REPLACEMENT",
    "DIRECTORY_ENTRY_DURABILITY",
    "RESTART_STATE_RECONSTRUCTION",
    "AMBIGUOUS_MUTATION_DETECTION",
)

assert tuple(DURABILITY_CLAIM_MATRIX_V1) == REQUIRED_CLAIM_NAMES
assert DURABILITY_CLAIM_MATRIX_V1["HOST_CRASH_DURABILITY"].proven is False
assert DURABILITY_CLAIM_MATRIX_V1["POWER_LOSS_DURABILITY"].proven is False
assert DURABILITY_CLAIM_MATRIX_V1["ATOMIC_REPLACEMENT"].proven is False
assert DURABILITY_CLAIM_MATRIX_V1["DIRECTORY_ENTRY_DURABILITY"].proven is False
assert DURABILITY_CLAIM_MATRIX_V1["PROCESS_KILL_DURABILITY"].proven is True
assert "HOST_CRASH" not in PROCESS_KILL_DURABILITY_CLAIM.failure_model

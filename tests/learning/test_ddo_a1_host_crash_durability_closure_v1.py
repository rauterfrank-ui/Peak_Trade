"""DDO A1 host-crash durability closure tests.

Failure models A-K are labeled separately. SIGKILL is PROCESS_KILL
evidence only. Syscall success is not HOST_CRASH_DURABILITY proof.
POWER_LOSS is not attempted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    DdoA1DurabilityFailurePolicyError,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.durability_primitives_v1 import (
    PRIMITIVE_F_FULLFSYNC,
    PRIMITIVE_OS_FSYNC,
    file_durability_primitive_name_v1,
    request_fd_durability_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateCorruptionError,
    ControlStateUnknownError,
    ControlStateValidationError,
    MutationCriticalControlStateStorageError,
)
from src.learning.mutation_critical_control_state_storage_v1.fault_injection_v1 import (
    BOUNDARY_AFTER_COMMIT_BEFORE_RETURN,
    BOUNDARY_COMMIT_DIRECTORY_FSYNC,
    BOUNDARY_COMMIT_FILE_FSYNC,
    BOUNDARY_DURING_COMMIT_WRITE,
    BOUNDARY_DURING_PAYLOAD_WRITE,
    ControlStateWalFaultInjectorV1,
    FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
    control_state_wal_fault_injection_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.host_crash_durability_claim_matrix_v1 import (
    DURABILITY_CLAIM_MATRIX_V1,
    REQUIRED_CLAIM_NAMES,
)
from src.learning.mutation_critical_control_state_storage_v1.host_crash_durability_closure_v1 import (
    ADMISSION_TRUE,
    ATOMIC_REPLACE_INTRODUCED,
    ATOMIC_REPLACE_PROVEN,
    DEPENDENT_MUTATION_ALLOWED,
    DIRECTORY_FSYNC_IMPLEMENTED,
    DIRECTORY_FSYNC_PROVEN,
    DIRECTORY_FSYNC_REQUIRED,
    DURABILITY_PROVEN_EFFECTIVE,
    EXECUTION_REACHABLE,
    EXISTING_STORAGE_AUTHORITY_REUSED,
    HOST_CRASH_DURABILITY,
    HOST_CRASH_PROOF_BASIS,
    HOST_CRASH_PROOF_ENVIRONMENT_PRESENT,
    HOST_CRASH_PROOF_LIMITATIONS,
    NEW_STORAGE_AUTHORITY_CREATED,
    POWER_LOSS_DURABILITY,
    POWER_LOSS_PROOF_BASIS,
    PROCESS_KILL_IS_HOST_CRASH_PROOF,
    PRODUCTIVE_HOST_BINDING,
    SUPERVISOR_ACTIVATED,
    SYSCALL_SUCCESS_IS_HOST_CRASH_PROOF,
    WIRE_SEND_REACHABLE,
)
from src.learning.mutation_critical_control_state_storage_v1.host_filesystem_capability_v1 import (
    probe_host_filesystem_capability_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.records_v1 import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
    STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION,
)
from src.learning.mutation_critical_control_state_storage_v1.wal_adapter_v1 import (
    FRAME_MAGIC,
    MutationCriticalControlStateWalAdapterV1,
    RECOVERY_CLEAN,
    RECOVERY_INCOMPLETE,
    RECOVERY_TORN,
    STATUS_COMMITTED,
    STATUS_IDEMPOTENT_REPLAY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/DDO_A1_HOST_CRASH_DURABILITY_CLOSURE_V1.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
CLOSURE_HEADING = "### 11.13.5 Parallel-track DDO A1 host-crash durability closure persist"
REPROOF_HEADING = (
    "### 11.13.5 Parallel-track DDO A1 mutation-critical control-state "
    "durable storage implementation and crash reproof persist"
)
Z2DB_HEADING = (
    "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
)


def _record(
    record_id: str,
    *,
    payload: dict[str, Any] | None = None,
    state_class: str = STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
) -> dict[str, Any]:
    return {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "state_class": state_class,
        "payload": payload or {"state": "armed_false", "reason": "host_crash_closure"},
        "correlation_id": "host-crash-corr",
        "depends_on_record_id": None,
    }


def test_claim_matrix_separates_process_kill_from_host_crash() -> None:
    assert tuple(DURABILITY_CLAIM_MATRIX_V1) == REQUIRED_CLAIM_NAMES
    host = DURABILITY_CLAIM_MATRIX_V1["HOST_CRASH_DURABILITY"]
    kill = DURABILITY_CLAIM_MATRIX_V1["PROCESS_KILL_DURABILITY"]
    power = DURABILITY_CLAIM_MATRIX_V1["POWER_LOSS_DURABILITY"]
    assert host.proven is False
    assert power.proven is False
    assert kill.proven is True
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert PROCESS_KILL_IS_HOST_CRASH_PROOF is False
    assert SYSCALL_SUCCESS_IS_HOST_CRASH_PROOF is False
    assert "HOST_CRASH" not in kill.failure_model
    assert host.failure_model.startswith("F8_HOST_KERNEL_CRASH")
    assert DURABILITY_CLAIM_MATRIX_V1["ATOMIC_REPLACEMENT"].proven is False
    assert DURABILITY_CLAIM_MATRIX_V1["DIRECTORY_ENTRY_DURABILITY"].proven is False


def test_closure_does_not_create_second_storage_or_activate_runtime() -> None:
    assert EXISTING_STORAGE_AUTHORITY_REUSED is True
    assert NEW_STORAGE_AUTHORITY_CREATED is False
    assert ATOMIC_REPLACE_INTRODUCED is False
    assert ATOMIC_REPLACE_PROVEN is False
    assert DIRECTORY_FSYNC_REQUIRED is True
    assert DIRECTORY_FSYNC_IMPLEMENTED is True
    assert DIRECTORY_FSYNC_PROVEN is False
    assert PRODUCTIVE_HOST_BINDING is False
    assert ADMISSION_TRUE is False
    assert SUPERVISOR_ACTIVATED is False
    assert EXECUTION_REACHABLE is False
    assert WIRE_SEND_REACHABLE is False
    assert DEPENDENT_MUTATION_ALLOWED is False
    assert DURABILITY_PROVEN_EFFECTIVE is False
    assert HOST_CRASH_PROOF_BASIS == "NONE"
    assert POWER_LOSS_PROOF_BASIS == "NONE"
    assert "NO_HOST_KERNEL_CRASH_HARNESS" in HOST_CRASH_PROOF_LIMITATIONS


def test_host_probe_does_not_guess_fstype_from_platform_and_does_not_prove_host_crash(
    tmp_path: Path,
) -> None:
    cap = probe_host_filesystem_capability_v1(tmp_path / "store")
    assert cap.host_crash_durability == "UNPROVEN"
    assert cap.power_loss_durability == "UNPROVEN"
    assert cap.host_crash_proof_environment_present is False
    assert HOST_CRASH_PROOF_ENVIRONMENT_PRESENT is False
    if cap.kernel_sysname == "Darwin":
        assert cap.filesystem_personality not in {cap.kernel_sysname, "Darwin", "macOS"}
    else:
        assert cap.filesystem_personality != "DARWIN_GUESSED"
    assert cap.file_durability_primitive in {PRIMITIVE_F_FULLFSYNC, PRIMITIVE_OS_FSYNC}
    assert cap.file_durability_syscall_succeeded is True
    assert cap.directory_durability_syscall_succeeded is True
    assert cap.atomic_replace_same_filesystem_succeeded is True
    assert cap.temp_and_target_same_device is True
    assert "PROCESS_KILL_IS_NOT_HOST_CRASH" in cap.limitations


def test_durability_primitive_is_fullfsync_when_available(tmp_path: Path) -> None:
    import fcntl
    import os

    path = tmp_path / "prim.bin"
    fd = os.open(str(path), os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, b"primitive")
        primitive = request_fd_durability_v1(fd)
    finally:
        os.close(fd)
    if hasattr(fcntl, "F_FULLFSYNC"):
        assert primitive == PRIMITIVE_F_FULLFSYNC
        assert file_durability_primitive_name_v1() == PRIMITIVE_F_FULLFSYNC
    else:
        assert primitive == PRIMITIVE_OS_FSYNC
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert SYSCALL_SUCCESS_IS_HOST_CRASH_PROOF is False


def test_b_process_kill_before_commit_is_process_kill_not_host_crash(tmp_path: Path) -> None:
    import os
    import signal
    import subprocess
    import sys
    import time

    child = REPO_ROOT / "tests/learning/_ddo_a1_control_state_wal_process_child_v1.py"
    root = tmp_path / "wal-b"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.Popen(
        [
            sys.executable,
            str(child),
            "--root",
            str(root),
            "--mode",
            "prepare_then_wait",
            "--record-id",
            "rec-b",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 8.0
        ready = root / "PROCESS_CHILD_READY"
        while time.monotonic() < deadline:
            if ready.is_file():
                break
            if proc.poll() is not None:
                raise AssertionError(f"child_exited_before_ready code={proc.returncode}")
            time.sleep(0.05)
        else:
            raise AssertionError("child_ready_timeout")
        proc.send_signal(signal.SIGKILL)
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-b")
    assert report.status == RECOVERY_INCOMPLETE
    assert report.durability_proven is False
    assert PROCESS_KILL_IS_HOST_CRASH_PROOF is False
    assert HOST_CRASH_DURABILITY == "UNPROVEN"


def test_c_process_kill_after_commit_is_process_kill_not_host_crash(tmp_path: Path) -> None:
    import os
    import signal
    import subprocess
    import sys
    import time

    child = REPO_ROOT / "tests/learning/_ddo_a1_control_state_wal_process_child_v1.py"
    root = tmp_path / "wal-c"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.Popen(
        [
            sys.executable,
            str(child),
            "--root",
            str(root),
            "--mode",
            "commit_then_wait",
            "--record-id",
            "rec-c",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 8.0
        ready = root / "PROCESS_CHILD_READY"
        while time.monotonic() < deadline:
            if ready.is_file():
                break
            if proc.poll() is not None:
                raise AssertionError(f"child_exited_before_ready code={proc.returncode}")
            time.sleep(0.05)
        else:
            raise AssertionError("child_ready_timeout")
        proc.send_signal(signal.SIGKILL)
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        loaded = wal.get("rec-c")
    assert report.status == RECOVERY_CLEAN
    assert loaded["record_id"] == "rec-c"
    assert report.durability_proven is False
    assert PROCESS_KILL_IS_HOST_CRASH_PROOF is False
    assert HOST_CRASH_DURABILITY == "UNPROVEN"


def test_a_normal_committed_write_plus_restart(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-a")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        result = wal.commit_record(record)
        assert result.status == STATUS_COMMITTED
        assert result.host_crash_durability == "UNPROVEN"
        identity = (result.record_id, result.content_hash, result.sequence)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        loaded = wal.get("rec-a")
    assert report.status == RECOVERY_CLEAN
    assert report.durability_proven is False
    assert (loaded["record_id"], loaded["content_hash"], loaded["sequence"]) == identity


def test_d_failure_during_payload_write_is_torn_not_committed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        injector = ControlStateWalFaultInjectorV1(
            boundary=BOUNDARY_DURING_PAYLOAD_WRITE,
            action=FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
        )
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(MutationCriticalControlStateStorageError),
        ):
            wal.prepare(_record("rec-d"))
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        assert report.status == RECOVERY_TORN
        assert report.committed_count == 0
        assert report.durability_proven is False


def test_e_failure_before_commit_frame_leaves_incomplete(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-e")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_DURING_COMMIT_WRITE)
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(MutationCriticalControlStateStorageError),
        ):
            wal.commit(prepared.transaction_id, record)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        assert report.status in {RECOVERY_INCOMPLETE, RECOVERY_TORN}
        assert report.committed_count == 0
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-e")


def test_f_failure_after_file_durability_before_directory_durability(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-f")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_COMMIT_DIRECTORY_FSYNC)
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(ControlStateUnknownError, match="DIRECTORY_FSYNC_UNKNOWN"),
        ):
            wal.commit(prepared.transaction_id, record)
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-f")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        loaded = wal.get("rec-f")
    assert report.durability_proven is False
    assert loaded["record_id"] == "rec-f"
    assert HOST_CRASH_DURABILITY == "UNPROVEN"


def test_g_truncated_and_corrupt_state_fail_closed(tmp_path: Path) -> None:
    torn_root = tmp_path / "wal-torn"
    with MutationCriticalControlStateWalAdapterV1(torn_root) as wal:
        wal.commit_record(_record("rec-g-torn"))
        journal = wal.journal_path()
        data = journal.read_bytes()
    journal.write_bytes(data[:-7])
    with MutationCriticalControlStateWalAdapterV1(torn_root) as wal:
        report = wal.recovery_report()
        assert report.torn_write_detected is True
        assert report.durability_proven is False
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-g-torn")
    corrupt_root = tmp_path / "wal-corrupt"
    with MutationCriticalControlStateWalAdapterV1(corrupt_root) as wal:
        wal.commit_record(_record("rec-g-corrupt"))
        path = wal.journal_path()
        flipped = bytearray(path.read_bytes())
    flipped[flipped.find(FRAME_MAGIC) + 14] ^= 0xFF
    path.write_bytes(bytes(flipped))
    with pytest.raises(ControlStateCorruptionError):
        MutationCriticalControlStateWalAdapterV1(corrupt_root).open()


def test_h_stale_committed_plus_newer_incomplete_mutation(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    first = _record("rec-h1", payload={"n": 1})
    second = _record("rec-h2", payload={"n": 2})
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        committed = wal.commit_record(first)
        wal.prepare(second)
        identity = committed.content_hash
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        loaded = wal.get("rec-h1")
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-h2")
    assert report.status == RECOVERY_INCOMPLETE
    assert loaded["content_hash"] == identity
    assert report.silent_repair_performed is False
    assert report.durability_proven is False


def test_i_duplicate_replay_is_not_host_crash_proof(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-i")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        first = wal.commit_record(record)
        second = wal.commit_record(record)
    assert first.status == STATUS_COMMITTED
    assert second.status == STATUS_IDEMPOTENT_REPLAY
    assert first.host_crash_durability == "UNPROVEN"
    assert second.host_crash_durability == "UNPROVEN"


def test_j_restart_reconstructs_uniquely_committed_state(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        result = wal.commit_record(_record("rec-j"))
        identity = (result.record_id, result.content_hash)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        loaded = wal.get("rec-j")
        report = wal.recovery_report()
    assert (loaded["record_id"], loaded["content_hash"]) == identity
    assert report.status == RECOVERY_CLEAN
    assert report.durability_proven is False


def test_k_incomplete_restart_denies_dependent_mutation(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-k", state_class=STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.prepare(record)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-k")
    assert report.status == RECOVERY_INCOMPLETE
    assert DEPENDENT_MUTATION_ALLOWED is False
    reject_a1_dependent_mutation_on_unproven_durability_v1()
    with pytest.raises(
        DdoA1DurabilityFailurePolicyError,
        match="A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
    ):
        reject_a1_dependent_mutation_on_unproven_durability_v1(dependent_mutation_requested=True)
    with pytest.raises(
        DdoA1DurabilityFailurePolicyError,
        match="A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
    ):
        reject_a1_dependent_mutation_on_unproven_durability_v1(durability_proven=True)


def test_after_commit_before_return_recovers_committed_without_durability_proven(
    tmp_path: Path,
) -> None:
    root = tmp_path / "wal"
    record = _record("rec-after-return")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_AFTER_COMMIT_BEFORE_RETURN)
        with control_state_wal_fault_injection_v1(injector), pytest.raises(OSError):
            wal.commit(prepared.transaction_id, record)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        loaded = wal.get("rec-after-return")
    assert loaded["record_id"] == "rec-after-return"
    assert report.durability_proven is False
    assert HOST_CRASH_DURABILITY == "UNPROVEN"


def test_commit_file_durability_failure_is_not_success(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-file-sync")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_COMMIT_FILE_FSYNC)
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(MutationCriticalControlStateStorageError),
        ):
            wal.commit(prepared.transaction_id, record)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        assert wal.recovery_report().durability_proven is False


def test_wal_has_no_tempfile_atomic_replace_path() -> None:
    adapter_src = (
        REPO_ROOT / "src/learning/mutation_critical_control_state_storage_v1/wal_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "os.replace" not in adapter_src
    assert "os.rename" not in adapter_src
    assert ATOMIC_REPLACE_INTRODUCED is False


def test_canonical_persist_spec_and_navigation() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    runbook = MASTER_RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    atlas = ATLAS_CATALOG.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in spec
    assert "POWER_LOSS_DURABILITY=UNPROVEN" in spec
    assert "PROCESS_KILL_IS_HOST_CRASH_PROOF=false" in spec
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in spec
    assert "DEPENDENT_MUTATION_ALLOWED=false" in spec
    assert "ADMISSION_TRUE=false" in spec
    assert CLOSURE_HEADING in runbook
    reproof = runbook.index(REPROOF_HEADING)
    closure = runbook.index(CLOSURE_HEADING)
    z2db = runbook.index(Z2DB_HEADING)
    assert reproof < closure < z2db
    section = runbook[closure:z2db]
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in section
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in section
    assert "DDO_A1_HOST_CRASH_DURABILITY_CLOSURE_V1.md" in mot
    assert "DDO_A1_HOST_CRASH_DURABILITY_CLOSURE_ROLE=NAVIGATION_POINTER_ONLY" in mot
    assert "Host-crash durability remains UNPROVEN" in atlas

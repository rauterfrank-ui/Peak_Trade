"""Mutation-critical control-state WAL adapter proofs.

Epistemic names only. Host-crash and power-loss remain UNPROVEN.
These tests prove process-restart durability, process-crash failure
handling, torn-write detection, corruption fail-closed, and transaction
recovery. They do not prove HOST_CRASH_DURABILITY or POWER_LOSS_DURABILITY.
"""

from __future__ import annotations

import errno
import json
from pathlib import Path
from typing import Any

import pytest

from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateAmbiguousRetryError,
    ControlStateConcurrentWriterError,
    ControlStateCorruptionError,
    ControlStateDuplicateConflictError,
    ControlStateFutureOnlyError,
    ControlStateMissingDependencyError,
    ControlStatePermissionError,
    ControlStateSchemaMismatchError,
    ControlStateStorageFullError,
    ControlStateUnknownError,
    ControlStateVersionMismatchError,
    ControlStateWrongOwnerError,
    MutationCriticalControlStateStorageError,
)
from src.learning.mutation_critical_control_state_storage_v1.fault_injection_v1 import (
    BOUNDARY_BEFORE_PREPARE,
    BOUNDARY_COMMIT_DIRECTORY_FSYNC,
    BOUNDARY_COMMIT_FILE_FSYNC,
    BOUNDARY_DURING_COMMIT_WRITE,
    BOUNDARY_DURING_PAYLOAD_WRITE,
    BOUNDARY_DURING_PREPARE_WRITE,
    BOUNDARY_LOCK_OPEN,
    BOUNDARY_MKDIR,
    BOUNDARY_PREPARE_FILE_FSYNC,
    ControlStateWalFaultInjectorV1,
    FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
    control_state_wal_fault_injection_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.medium_binding_v1 import (
    CRASH_DURABILITY_FULLY_PROVEN,
    HOST_CRASH_DURABILITY,
    POWER_LOSS_DURABILITY,
    STORAGE_MEDIUM,
)
from src.learning.mutation_critical_control_state_storage_v1.records_v1 import (
    FUTURE_ONLY_STATE_CLASSES,
    IMPLEMENTED_STATE_CLASSES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STATE_CLASS_A_OBSERVATION_ONLY_EVIDENCE,
    STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
    STATE_CLASS_C_EXECUTION_ACTION_IDENTITY,
    STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION,
    STATE_CLASS_E_RECONCILIATION_OBLIGATION,
)
from src.learning.mutation_critical_control_state_storage_v1.serialization_v1 import (
    compute_content_hash_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.wal_adapter_v1 import (
    FRAME_MAGIC,
    MutationCriticalControlStateWalAdapterV1,
    RECOVERY_INCOMPLETE,
    RECOVERY_TORN,
    STATUS_COMMITTED,
    STATUS_IDEMPOTENT_REPLAY,
    STATUS_PREPARED,
)


def _record(
    record_id: str,
    *,
    state_class: str = STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
    payload: dict[str, Any] | None = None,
    depends_on: str | None = None,
    correlation_id: str | None = "corr-1",
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "state_class": state_class,
        "payload": payload or {"state": "armed_false", "reason": "offline_only"},
        "correlation_id": correlation_id,
        "depends_on_record_id": depends_on,
    }
    return body


def test_canonical_roundtrip_and_deterministic_hash(tmp_path: Path) -> None:
    record = _record("rec-roundtrip")
    first = compute_content_hash_v1(record)
    second = compute_content_hash_v1(record)
    assert first == second
    with MutationCriticalControlStateWalAdapterV1(tmp_path / "wal") as wal:
        result = wal.commit_record(record)
        assert result.status == STATUS_COMMITTED
        loaded = wal.get("rec-roundtrip")
        assert loaded["content_hash"] == first
        assert loaded["state_class"] == STATE_CLASS_B_SUPERVISOR_CONTROL_STATE
        assert result.host_crash_durability == "UNPROVEN"
        assert result.power_loss_durability == "UNPROVEN"
        assert result.crash_durability_fully_proven is False


def test_clean_reopen_and_restart_after_successful_commit(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-restart")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(record)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        assert report.silent_repair_performed is False
        assert report.durability_proven is False
        assert wal.get("rec-restart")["record_id"] == "rec-restart"
        assert list(wal.read_all())[0]["record_id"] == "rec-restart"


def test_crash_before_prepare_leaves_store_empty(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_BEFORE_PREPARE)
        with control_state_wal_fault_injection_v1(injector), pytest.raises(OSError):
            wal.prepare(_record("rec-before-prepare"))
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        assert wal.read_all() == ()
        assert wal.recovery_report().committed_count == 0


def test_failure_during_prepare_is_incomplete_not_committed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        injector = ControlStateWalFaultInjectorV1(
            boundary=BOUNDARY_DURING_PREPARE_WRITE,
            action=FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
        )
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(MutationCriticalControlStateStorageError),
        ):
            wal.prepare(_record("rec-prepare-fail"))
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        assert report.torn_write_detected is True
        assert report.status == RECOVERY_TORN
        assert report.committed_count == 0
        assert report.silent_repair_performed is False


def test_incomplete_payload_write_is_torn_not_success(tmp_path: Path) -> None:
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
            wal.prepare(_record("rec-payload-torn"))
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        assert report.torn_write_detected is True
        assert wal.read_all() == ()
        assert wal.journal_path().stat().st_size > 0


def test_commit_failure_does_not_install_record(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-commit-fail")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        assert prepared.status == STATUS_PREPARED
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
        with pytest.raises(Exception, match="RECORD_NOT_FOUND"):
            wal.get("rec-commit-fail")


def test_commit_file_fsync_failure_is_not_success(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-fsync")
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
        assert wal.recovery_report().silent_repair_performed is False


def test_directory_fsync_failure_is_unknown_not_committed_success(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-dir-fsync")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_COMMIT_DIRECTORY_FSYNC)
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(ControlStateUnknownError, match="DIRECTORY_FSYNC_UNKNOWN"),
        ):
            wal.commit(prepared.transaction_id, record)
        with pytest.raises(Exception, match="RECORD_NOT_FOUND"):
            wal.get("rec-dir-fsync")


def test_prepare_file_fsync_failure_is_not_prepared_success(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_PREPARE_FILE_FSYNC)
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(MutationCriticalControlStateStorageError),
        ):
            wal.prepare(_record("rec-prep-fsync"))


def test_corrupt_record_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("rec-ok"))
        path = wal.journal_path()
        data = bytearray(path.read_bytes())
    payload_index = bytes(data).find(b"rec-ok")
    data[payload_index] = data[payload_index] ^ 0xFF
    path.write_bytes(bytes(data))
    with pytest.raises(ControlStateCorruptionError):
        MutationCriticalControlStateWalAdapterV1(root).open()


def test_corrupt_commit_frame_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("rec-commit-corrupt"))
        path = wal.journal_path()
        data = bytearray(path.read_bytes())
    magic_hits = [i for i in range(len(data) - 7) if data[i : i + 8] == FRAME_MAGIC]
    assert len(magic_hits) >= 3
    last = magic_hits[-1]
    data[last + 14] ^= 0xFF
    path.write_bytes(bytes(data))
    with pytest.raises(ControlStateCorruptionError):
        MutationCriticalControlStateWalAdapterV1(root).open()


def test_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("rec-schema"))
        header = json.loads(wal.header_path().read_text(encoding="utf-8"))
    header["schema_name"] = "wrong_schema"
    wal.header_path().write_text(json.dumps(header), encoding="utf-8")
    with pytest.raises(ControlStateSchemaMismatchError):
        MutationCriticalControlStateWalAdapterV1(root).open()


def test_version_mismatch_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("rec-version"))
        header = json.loads(wal.header_path().read_text(encoding="utf-8"))
    header["schema_version"] = "v0"
    wal.header_path().write_text(json.dumps(header), encoding="utf-8")
    with pytest.raises(ControlStateVersionMismatchError):
        MutationCriticalControlStateWalAdapterV1(root).open()


def test_missing_dependency_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        with pytest.raises(ControlStateMissingDependencyError, match="MISSING_DEPENDENCY"):
            wal.commit_record(_record("rec-child", depends_on="rec-missing"))


def test_duplicate_same_id_same_content_is_idempotent_replay(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-dup")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        first = wal.commit_record(record)
        second = wal.commit_record(record)
        assert first.status == STATUS_COMMITTED
        assert second.status == STATUS_IDEMPOTENT_REPLAY
        assert len(wal.read_all()) == 1


def test_duplicate_same_id_conflicting_content_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("rec-conflict", payload={"n": 1}))
        with pytest.raises(ControlStateDuplicateConflictError, match="DUPLICATE_CONFLICT"):
            wal.commit_record(_record("rec-conflict", payload={"n": 2}))


def test_concurrent_writer_rejected(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    first = MutationCriticalControlStateWalAdapterV1(root)
    first.open()
    try:
        second = MutationCriticalControlStateWalAdapterV1(root)
        with pytest.raises(ControlStateConcurrentWriterError):
            second.open()
    finally:
        first.close()


def test_startup_reconstruction_preserves_b_c_d_classes(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("b1", state_class=STATE_CLASS_B_SUPERVISOR_CONTROL_STATE))
        wal.commit_record(_record("c1", state_class=STATE_CLASS_C_EXECUTION_ACTION_IDENTITY))
        wal.commit_record(_record("d1", state_class=STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION))
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        classes = {item["record_id"]: item["state_class"] for item in wal.read_all()}
        assert classes == {
            "b1": STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
            "c1": STATE_CLASS_C_EXECUTION_ACTION_IDENTITY,
            "d1": STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION,
        }
        assert IMPLEMENTED_STATE_CLASSES == set(classes.values())


def test_recovery_from_incomplete_transaction_does_not_apply(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-incomplete")
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.prepare(record)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        assert report.status == RECOVERY_INCOMPLETE
        assert report.incomplete_transaction_ids
        assert report.silent_repair_performed is False
        assert wal.read_all() == ()


def test_storage_permission_failure(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    wal = MutationCriticalControlStateWalAdapterV1(root)
    injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_LOCK_OPEN, errno_code=errno.EACCES)
    with control_state_wal_fault_injection_v1(injector), pytest.raises(ControlStatePermissionError):
        wal.open()


def test_storage_full_simulation(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        injector = ControlStateWalFaultInjectorV1(
            boundary=BOUNDARY_DURING_PREPARE_WRITE, errno_code=errno.ENOSPC
        )
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(ControlStateStorageFullError),
        ):
            wal.prepare(_record("rec-full"))


def test_mkdir_permission_failure(tmp_path: Path) -> None:
    root = tmp_path / "nope" / "wal"
    wal = MutationCriticalControlStateWalAdapterV1(root)
    injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_MKDIR, errno_code=errno.EACCES)
    with control_state_wal_fault_injection_v1(injector), pytest.raises(ControlStatePermissionError):
        wal.open()


def test_no_automatic_retry_after_ambiguous_mutation_class_record(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    record = _record("rec-amb", state_class=STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        prepared = wal.prepare(record)
        injector = ControlStateWalFaultInjectorV1(boundary=BOUNDARY_COMMIT_DIRECTORY_FSYNC)
        with (
            control_state_wal_fault_injection_v1(injector),
            pytest.raises(ControlStateUnknownError),
        ):
            wal.commit(prepared.transaction_id, record)
        with pytest.raises(ControlStateAmbiguousRetryError, match="AMBIGUOUS_RETRY_FORBIDDEN"):
            wal.retry_after_ambiguous(record)
        with pytest.raises(ControlStateAmbiguousRetryError):
            wal.prepare(record)


def test_future_only_and_observation_owner_rejected(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        with pytest.raises(ControlStateWrongOwnerError):
            wal.commit_record(_record("obs", state_class=STATE_CLASS_A_OBSERVATION_ONLY_EVIDENCE))
        with pytest.raises(ControlStateFutureOnlyError):
            wal.commit_record(_record("recon", state_class=STATE_CLASS_E_RECONCILIATION_OBLIGATION))
        for state_class in FUTURE_ONLY_STATE_CLASSES:
            with pytest.raises(ControlStateFutureOnlyError):
                wal.commit_record(_record(f"f-{state_class}", state_class=state_class))


def test_header_missing_with_journal_is_corrupt(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        wal.commit_record(_record("rec-header"))
        header = wal.header_path()
    header.unlink()
    with pytest.raises(ControlStateCorruptionError, match="HEADER_MISSING_JOURNAL_PRESENT"):
        MutationCriticalControlStateWalAdapterV1(root).open()


def test_durability_claims_remain_unproven(tmp_path: Path) -> None:
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert STORAGE_MEDIUM == "CUSTOM_FILE_WAL_JOURNAL_V1"
    with MutationCriticalControlStateWalAdapterV1(tmp_path / "wal") as wal:
        result = wal.commit_record(_record("rec-claims"))
        assert result.host_crash_durability == "UNPROVEN"
        assert result.power_loss_durability == "UNPROVEN"
        assert result.crash_durability_fully_proven is False
        assert wal.recovery_report().durability_proven is False

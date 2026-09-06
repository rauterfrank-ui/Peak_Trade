"""Isolated custom-file WAL adapter for mutation-critical control state.

No productive host binding. No DDO ledger reuse as owner. No SQLite.
Host-crash and power-loss durability remain UNPROVEN.
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.mutation_critical_control_state_storage_v1.authority_v1 import (
    STORAGE_OWNER_NAME,
)
from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateAmbiguousRetryError,
    ControlStateConcurrentWriterError,
    ControlStateCorruptionError,
    ControlStateDuplicateConflictError,
    ControlStateMissingDependencyError,
    ControlStateSchemaMismatchError,
    ControlStateUnknownError,
    ControlStateValidationError,
    ControlStateVersionMismatchError,
    MutationCriticalControlStateStorageError,
    classify_oserror_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.fault_injection_v1 import (
    BOUNDARY_AFTER_COMMIT_BEFORE_RETURN,
    BOUNDARY_BEFORE_PREPARE,
    BOUNDARY_COMMIT_DIRECTORY_FSYNC,
    BOUNDARY_COMMIT_FILE_FSYNC,
    BOUNDARY_DURING_COMMIT_WRITE,
    BOUNDARY_DURING_PAYLOAD_WRITE,
    BOUNDARY_DURING_PREPARE_WRITE,
    BOUNDARY_LOCK_OPEN,
    BOUNDARY_MKDIR,
    BOUNDARY_PREPARE_DIRECTORY_FSYNC,
    BOUNDARY_PREPARE_FILE_FSYNC,
    FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
    apply_wal_fault_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.medium_binding_v1 import (
    COMMIT_POINT,
    CRASH_DURABILITY_FULLY_PROVEN,
    HOST_CRASH_DURABILITY,
    POWER_LOSS_DURABILITY,
    PROCESS_CRASH_DURABILITY,
    PROCESS_RESTART_DURABILITY,
    STORAGE_MEDIUM,
)
from src.learning.mutation_critical_control_state_storage_v1.records_v1 import (
    AMBIGUOUS_MUTATION_CLASSES,
    SCHEMA_VERSION,
    validate_control_state_record_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.serialization_v1 import (
    canonical_json_dumps_v1,
    sha256_bytes_v1,
    sha256_hex_v1,
)

HEADER_FILENAME: Final[str] = "HEADER.json"
JOURNAL_FILENAME: Final[str] = "control_state.wal"
LOCK_FILENAME: Final[str] = "WRITER.lock"
FRAME_MAGIC: Final[bytes] = b"PTCSWAL1"
FRAME_SCHEMA_NAME: Final[str] = "mutation_critical_control_state_wal_frame_v1"
FRAME_SCHEMA_VERSION: Final[str] = "v1"
HEADER_SCHEMA_NAME: Final[str] = "mutation_critical_control_state_wal_header_v1"
HEADER_SCHEMA_VERSION: Final[str] = "v1"
FENCING_TOKEN_UNBOUND: Final[str] = "UNBOUND"

STATUS_COMMITTED: Final[str] = "COMMITTED"
STATUS_IDEMPOTENT_REPLAY: Final[str] = "IDEMPOTENT_REPLAY"
STATUS_PREPARED: Final[str] = "PREPARED"
STATUS_INCOMPLETE_TRANSACTION: Final[str] = "INCOMPLETE_TRANSACTION"
STATUS_TORN_WRITE: Final[str] = "TORN_WRITE"
STATUS_DIRECTORY_FSYNC_UNKNOWN: Final[str] = "DIRECTORY_FSYNC_UNKNOWN"

RECOVERY_CLEAN: Final[str] = "CLEAN"
RECOVERY_INCOMPLETE: Final[str] = "INCOMPLETE_TRANSACTION"
RECOVERY_TORN: Final[str] = "TORN_WRITE"

_IN_PROCESS_LOCKS: dict[str, threading.Lock] = {}
_IN_PROCESS_GUARD = threading.Lock()


def _in_process_lock(path_key: str) -> threading.Lock:
    with _IN_PROCESS_GUARD:
        lock = _IN_PROCESS_LOCKS.get(path_key)
        if lock is None:
            lock = threading.Lock()
            _IN_PROCESS_LOCKS[path_key] = lock
        return lock


@dataclass(frozen=True)
class PrepareResultV1:
    status: str
    transaction_id: str
    record_id: str
    content_hash: str


@dataclass(frozen=True)
class CommitResultV1:
    status: str
    transaction_id: str
    record_id: str
    content_hash: str
    sequence: int
    durability_class: str
    process_restart_durability: str
    process_crash_durability: str
    host_crash_durability: str
    power_loss_durability: str
    crash_durability_fully_proven: bool
    commit_point: str


@dataclass(frozen=True)
class RecoveryReportV1:
    status: str
    committed_count: int
    incomplete_transaction_ids: tuple[str, ...]
    torn_write_detected: bool
    silent_repair_performed: bool
    durability_proven: bool


class MutationCriticalControlStateWalAdapterV1:
    """Single-writer framed WAL. Isolated. Offline only."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._lock_fd: int | None = None
        self._in_process: threading.Lock | None = None
        self._journal_fd: int | None = None
        self._open = False
        self._committed: dict[str, dict[str, Any]] = {}
        self._sequence = 0
        self._incomplete: list[str] = []
        self._prepared: dict[str, dict[str, Any]] = {}
        self._torn = False
        self._ambiguous_unresolved: set[str] = set()

    @property
    def root(self) -> Path:
        return self._root

    def writer_lock_path(self) -> Path:
        return self._root / LOCK_FILENAME

    def header_path(self) -> Path:
        return self._root / HEADER_FILENAME

    def journal_path(self) -> Path:
        return self._root / JOURNAL_FILENAME

    def open(self) -> RecoveryReportV1:
        if self._open:
            raise ControlStateValidationError("ADAPTER_ALREADY_OPEN")
        in_process = _in_process_lock(str(self._root))
        if not in_process.acquire(blocking=False):
            raise ControlStateConcurrentWriterError("CONCURRENT_WRITER_VIOLATION")
        self._in_process = in_process
        try:
            try:
                apply_wal_fault_v1(BOUNDARY_MKDIR)
                self._root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise classify_oserror_v1(exc, operation="mkdir") from exc
            try:
                apply_wal_fault_v1(BOUNDARY_LOCK_OPEN)
                self._lock_fd = os.open(str(self.writer_lock_path()), os.O_CREAT | os.O_RDWR, 0o644)
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ControlStateConcurrentWriterError("CONCURRENT_WRITER_VIOLATION") from exc
            except OSError as exc:
                raise classify_oserror_v1(exc, operation="writer_lock") from exc
            self._ensure_header()
            report = self._recover()
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            try:
                self._journal_fd = os.open(str(self.journal_path()), flags, 0o644)
                os.lseek(self._journal_fd, 0, os.SEEK_END)
            except OSError as exc:
                raise classify_oserror_v1(exc, operation="journal_open") from exc
            self._open = True
            return report
        except Exception:
            self._release_locks()
            raise

    def close(self) -> None:
        if self._journal_fd is not None:
            try:
                os.close(self._journal_fd)
            except OSError:
                pass
            self._journal_fd = None
        self._release_locks()
        self._open = False

    def __enter__(self) -> MutationCriticalControlStateWalAdapterV1:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def prepare(self, record: Mapping[str, Any]) -> PrepareResultV1:
        self._require_open()
        apply_wal_fault_v1(BOUNDARY_BEFORE_PREPARE)
        normalized = validate_control_state_record_v1(record)
        self._reject_ambiguous_retry(normalized)
        existing = self._committed.get(normalized["record_id"])
        if existing is not None:
            if existing["content_hash"] == normalized["content_hash"]:
                return PrepareResultV1(
                    status=STATUS_IDEMPOTENT_REPLAY,
                    transaction_id=f"replay:{normalized['record_id']}",
                    record_id=normalized["record_id"],
                    content_hash=normalized["content_hash"],
                )
            raise ControlStateDuplicateConflictError(
                f"DUPLICATE_CONFLICT:{normalized['record_id']}"
            )
        depends = normalized.get("depends_on_record_id")
        if depends is not None and depends not in self._committed:
            raise ControlStateMissingDependencyError(f"MISSING_DEPENDENCY:{depends}")
        transaction_id = f"tx-{uuid.uuid4().hex}"
        prepare_frame = self._frame(
            frame_type="PREPARE",
            transaction_id=transaction_id,
            record=normalized,
        )
        payload_frame = self._frame(
            frame_type="PAYLOAD",
            transaction_id=transaction_id,
            record=normalized,
        )
        self._append_frame(prepare_frame, BOUNDARY_DURING_PREPARE_WRITE)
        self._fsync_journal(BOUNDARY_PREPARE_FILE_FSYNC)
        self._append_frame(payload_frame, BOUNDARY_DURING_PAYLOAD_WRITE)
        self._fsync_journal(BOUNDARY_PREPARE_FILE_FSYNC)
        self._fsync_directory(BOUNDARY_PREPARE_DIRECTORY_FSYNC)
        self._prepared[transaction_id] = dict(normalized)
        return PrepareResultV1(
            status=STATUS_PREPARED,
            transaction_id=transaction_id,
            record_id=normalized["record_id"],
            content_hash=normalized["content_hash"],
        )

    def commit(self, transaction_id: str, record: Mapping[str, Any]) -> CommitResultV1:
        self._require_open()
        if transaction_id.startswith("replay:"):
            normalized = validate_control_state_record_v1(record)
            existing = self._committed[normalized["record_id"]]
            return self._commit_result(
                STATUS_IDEMPOTENT_REPLAY,
                transaction_id,
                existing,
            )
        if transaction_id not in self._prepared:
            raise ControlStateValidationError(f"UNKNOWN_TRANSACTION:{transaction_id}")
        normalized = validate_control_state_record_v1(record)
        if self._prepared[transaction_id]["content_hash"] != normalized["content_hash"]:
            raise ControlStateDuplicateConflictError(
                f"PREPARE_COMMIT_CONTENT_MISMATCH:{transaction_id}"
            )
        self._reject_ambiguous_retry(normalized)
        existing = self._committed.get(normalized["record_id"])
        if existing is not None:
            if existing["content_hash"] == normalized["content_hash"]:
                return self._commit_result(
                    STATUS_IDEMPOTENT_REPLAY,
                    transaction_id,
                    existing,
                )
            raise ControlStateDuplicateConflictError(
                f"DUPLICATE_CONFLICT:{normalized['record_id']}"
            )
        commit_frame = self._frame(
            frame_type="COMMIT",
            transaction_id=transaction_id,
            record=normalized,
        )
        self._append_frame(commit_frame, BOUNDARY_DURING_COMMIT_WRITE)
        self._fsync_journal(BOUNDARY_COMMIT_FILE_FSYNC)
        directory_ok = self._fsync_directory(BOUNDARY_COMMIT_DIRECTORY_FSYNC, unknown_ok=True)
        apply_wal_fault_v1(BOUNDARY_AFTER_COMMIT_BEFORE_RETURN)
        if not directory_ok:
            if normalized["state_class"] in AMBIGUOUS_MUTATION_CLASSES:
                self._ambiguous_unresolved.add(normalized["record_id"])
            raise ControlStateUnknownError(STATUS_DIRECTORY_FSYNC_UNKNOWN)
        installed = dict(normalized)
        self._sequence += 1
        installed["sequence"] = self._sequence
        installed["transaction_id"] = transaction_id
        self._committed[normalized["record_id"]] = installed
        self._prepared.pop(transaction_id, None)
        return self._commit_result(STATUS_COMMITTED, transaction_id, installed)

    def commit_record(self, record: Mapping[str, Any]) -> CommitResultV1:
        prepared = self.prepare(record)
        return self.commit(prepared.transaction_id, record)

    def retry_after_ambiguous(self, record: Mapping[str, Any]) -> None:
        normalized = validate_control_state_record_v1(record)
        raise ControlStateAmbiguousRetryError(
            f"AMBIGUOUS_RETRY_FORBIDDEN:{normalized['record_id']}"
        )

    def get(self, record_id: str) -> MappingProxyType[str, Any]:
        self._require_open()
        if record_id not in self._committed:
            raise ControlStateValidationError(f"RECORD_NOT_FOUND:{record_id}")
        return MappingProxyType(self._committed[record_id])

    def read_all(self) -> tuple[MappingProxyType[str, Any], ...]:
        self._require_open()
        ordered = sorted(self._committed.values(), key=lambda item: int(item["sequence"]))
        return tuple(MappingProxyType(item) for item in ordered)

    def recovery_report(self) -> RecoveryReportV1:
        self._require_open()
        status = RECOVERY_CLEAN
        if self._torn:
            status = RECOVERY_TORN
        elif self._incomplete:
            status = RECOVERY_INCOMPLETE
        return RecoveryReportV1(
            status=status,
            committed_count=len(self._committed),
            incomplete_transaction_ids=tuple(self._incomplete),
            torn_write_detected=self._torn,
            silent_repair_performed=False,
            durability_proven=False,
        )

    def _require_open(self) -> None:
        if not self._open or self._journal_fd is None:
            raise ControlStateValidationError("ADAPTER_NOT_OPEN")

    def _reject_ambiguous_retry(self, record: dict[str, Any]) -> None:
        if record["record_id"] in self._ambiguous_unresolved:
            raise ControlStateAmbiguousRetryError(
                f"AMBIGUOUS_RETRY_FORBIDDEN:{record['record_id']}"
            )

    def _commit_result(
        self,
        status: str,
        transaction_id: str,
        record: Mapping[str, Any],
    ) -> CommitResultV1:
        return CommitResultV1(
            status=status,
            transaction_id=transaction_id,
            record_id=str(record["record_id"]),
            content_hash=str(record["content_hash"]),
            sequence=int(record["sequence"]),
            durability_class="PROCESS_RESTART_AND_PROCESS_CRASH_FAILURE_HANDLING_NOT_HOST_CRASH",
            process_restart_durability=PROCESS_RESTART_DURABILITY,
            process_crash_durability=PROCESS_CRASH_DURABILITY,
            host_crash_durability=HOST_CRASH_DURABILITY,
            power_loss_durability=POWER_LOSS_DURABILITY,
            crash_durability_fully_proven=CRASH_DURABILITY_FULLY_PROVEN,
            commit_point=COMMIT_POINT,
        )

    def _frame(
        self,
        *,
        frame_type: str,
        transaction_id: str,
        record: Mapping[str, Any],
    ) -> dict[str, Any]:
        body = {
            "schema_name": FRAME_SCHEMA_NAME,
            "schema_version": FRAME_SCHEMA_VERSION,
            "frame_type": frame_type,
            "transaction_id": transaction_id,
            "record_id": record["record_id"],
            "state_class": record["state_class"],
            "content_hash": record["content_hash"],
            "record": dict(record) if frame_type != "COMMIT" else None,
        }
        body["frame_hash"] = sha256_hex_v1(canonical_json_dumps_v1(body))
        return body

    def _encode_frame(self, frame: Mapping[str, Any]) -> bytes:
        body = canonical_json_dumps_v1(frame).encode("utf-8")
        return FRAME_MAGIC + len(body).to_bytes(4, "big") + body + sha256_bytes_v1(body)

    def _append_frame(self, frame: Mapping[str, Any], write_boundary: str) -> None:
        encoded = self._encode_frame(frame)
        assert self._journal_fd is not None
        try:
            injector = apply_wal_fault_v1(write_boundary)
            if injector is not None and injector.action == FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE:
                cut = max(1, len(encoded) // 3)
                os.write(self._journal_fd, encoded[:cut])
                raise OSError(injector.errno_code, f"injected_wal_fault:{write_boundary}")
            written = os.write(self._journal_fd, encoded)
            if written != len(encoded):
                raise MutationCriticalControlStateStorageError("SHORT_WRITE")
        except OSError as exc:
            raise classify_oserror_v1(exc, operation="journal_write") from exc

    def _fsync_journal(self, boundary: str) -> None:
        assert self._journal_fd is not None
        try:
            apply_wal_fault_v1(boundary)
            os.fsync(self._journal_fd)
        except OSError as exc:
            raise classify_oserror_v1(exc, operation="journal_fsync") from exc

    def _fsync_directory(self, boundary: str, *, unknown_ok: bool = False) -> bool:
        try:
            apply_wal_fault_v1(boundary)
        except OSError as exc:
            if unknown_ok:
                return False
            raise classify_oserror_v1(exc, operation="directory_fsync") from exc
        try:
            dir_fd = os.open(str(self._root), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError as exc:
            if unknown_ok:
                return False
            raise classify_oserror_v1(exc, operation="directory_fsync") from exc
        return True

    def _ensure_header(self) -> None:
        path = self.header_path()
        journal_exists = self.journal_path().exists() and self.journal_path().stat().st_size > 0
        if not path.exists() and journal_exists:
            raise ControlStateCorruptionError("HEADER_MISSING_JOURNAL_PRESENT")
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ControlStateCorruptionError("HEADER_CORRUPT") from exc
            if payload.get("schema_name") != HEADER_SCHEMA_NAME:
                raise ControlStateSchemaMismatchError("HEADER_SCHEMA_MISMATCH")
            if payload.get("schema_version") != HEADER_SCHEMA_VERSION:
                raise ControlStateVersionMismatchError("HEADER_VERSION_MISMATCH")
            if payload.get("storage_owner") != STORAGE_OWNER_NAME:
                raise ControlStateSchemaMismatchError("HEADER_OWNER_MISMATCH")
            if payload.get("storage_medium") != STORAGE_MEDIUM:
                raise ControlStateSchemaMismatchError("HEADER_MEDIUM_MISMATCH")
            if payload.get("record_schema_version") != SCHEMA_VERSION:
                raise ControlStateVersionMismatchError("HEADER_RECORD_VERSION_MISMATCH")
            return
        header = {
            "schema_name": HEADER_SCHEMA_NAME,
            "schema_version": HEADER_SCHEMA_VERSION,
            "storage_owner": STORAGE_OWNER_NAME,
            "storage_medium": STORAGE_MEDIUM,
            "record_schema_version": SCHEMA_VERSION,
            "fencing_token": FENCING_TOKEN_UNBOUND,
            "silent_repair": False,
            "silent_migration": False,
        }
        encoded = canonical_json_dumps_v1(header).encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(str(path), flags, 0o644)
            try:
                os.write(fd, encoded)
                os.fsync(fd)
            finally:
                os.close(fd)
        except FileExistsError:
            return
        except OSError as exc:
            raise classify_oserror_v1(exc, operation="header_create") from exc

    def _recover(self) -> RecoveryReportV1:
        journal = self.journal_path()
        if not journal.exists():
            return RecoveryReportV1(
                status=RECOVERY_CLEAN,
                committed_count=0,
                incomplete_transaction_ids=(),
                torn_write_detected=False,
                silent_repair_performed=False,
                durability_proven=False,
            )
        try:
            data = journal.read_bytes()
        except OSError as exc:
            raise classify_oserror_v1(exc, operation="journal_read") from exc
        frames, torn = self._scan_frames(data)
        by_tx: dict[str, dict[str, dict[str, Any]]] = {}
        for frame in frames:
            by_tx.setdefault(frame["transaction_id"], {})[frame["frame_type"]] = frame
        incomplete: list[str] = []
        committed: dict[str, dict[str, Any]] = {}
        sequence = 0
        for transaction_id, parts in by_tx.items():
            if "COMMIT" in parts:
                commit = parts["COMMIT"]
                payload = parts.get("PAYLOAD")
                prepare = parts.get("PREPARE")
                if payload is None or prepare is None:
                    raise ControlStateCorruptionError(
                        f"COMMIT_WITHOUT_PREPARE_OR_PAYLOAD:{transaction_id}"
                    )
                record = payload.get("record")
                if not isinstance(record, dict):
                    raise ControlStateCorruptionError(f"PAYLOAD_RECORD_MISSING:{transaction_id}")
                normalized = validate_control_state_record_v1(record)
                if normalized["content_hash"] != commit["content_hash"]:
                    raise ControlStateCorruptionError(
                        f"COMMIT_CONTENT_HASH_MISMATCH:{transaction_id}"
                    )
                existing = committed.get(normalized["record_id"])
                if existing is not None:
                    if existing["content_hash"] != normalized["content_hash"]:
                        raise ControlStateDuplicateConflictError(
                            f"DUPLICATE_CONFLICT:{normalized['record_id']}"
                        )
                    continue
                depends = normalized.get("depends_on_record_id")
                if depends is not None and depends not in committed:
                    raise ControlStateMissingDependencyError(f"MISSING_DEPENDENCY:{depends}")
                sequence += 1
                installed = dict(normalized)
                installed["sequence"] = sequence
                installed["transaction_id"] = transaction_id
                committed[normalized["record_id"]] = installed
            else:
                incomplete.append(transaction_id)
        self._committed = committed
        self._sequence = sequence
        self._incomplete = incomplete
        self._torn = torn
        status = RECOVERY_CLEAN
        if torn:
            status = RECOVERY_TORN
        elif incomplete:
            status = RECOVERY_INCOMPLETE
        return RecoveryReportV1(
            status=status,
            committed_count=len(committed),
            incomplete_transaction_ids=tuple(incomplete),
            torn_write_detected=torn,
            silent_repair_performed=False,
            durability_proven=False,
        )

    def _scan_frames(self, data: bytes) -> tuple[list[dict[str, Any]], bool]:
        frames: list[dict[str, Any]] = []
        offset = 0
        while offset < len(data):
            remaining = len(data) - offset
            if remaining < 12:
                return frames, True
            magic = data[offset : offset + 8]
            if magic != FRAME_MAGIC:
                raise ControlStateCorruptionError("JOURNAL_MAGIC_MISMATCH")
            body_len = int.from_bytes(data[offset + 8 : offset + 12], "big")
            frame_end = offset + 12 + body_len + 32
            if frame_end > len(data):
                return frames, True
            body = data[offset + 12 : offset + 12 + body_len]
            checksum = data[offset + 12 + body_len : frame_end]
            if sha256_bytes_v1(body) != checksum:
                raise ControlStateCorruptionError("JOURNAL_FRAME_CHECKSUM_MISMATCH")
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ControlStateCorruptionError("JOURNAL_FRAME_JSON_CORRUPT") from exc
            if payload.get("schema_name") != FRAME_SCHEMA_NAME:
                raise ControlStateSchemaMismatchError("FRAME_SCHEMA_MISMATCH")
            if payload.get("schema_version") != FRAME_SCHEMA_VERSION:
                raise ControlStateVersionMismatchError("FRAME_VERSION_MISMATCH")
            expected_hash = payload.get("frame_hash")
            hashed = dict(payload)
            hashed.pop("frame_hash", None)
            if expected_hash != sha256_hex_v1(canonical_json_dumps_v1(hashed)):
                raise ControlStateCorruptionError("FRAME_HASH_MISMATCH")
            frames.append(payload)
            offset = frame_end
        return frames, False

    def _release_locks(self) -> None:
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None
        if self._in_process is not None:
            try:
                self._in_process.release()
            except RuntimeError:
                pass
            self._in_process = None

"""Append-only offline DDO ledger v0.

No network, no runtime hook, no auto-capture, no side effect outside the
explicit ledger path. Silent overwrite is forbidden.
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Iterator, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_ATTRIBUTION_RECORD,
    SCHEMA_NAME_AUTONOMY_CYCLE,
    SCHEMA_NAME_CANDIDATE_ARTIFACT,
    SCHEMA_NAME_CANONICAL_EXPERIMENT_IDENTITY_REF,
    SCHEMA_NAME_COUNTERFACTUAL_RECORD,
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_DEPLOYMENT_RECORD,
    SCHEMA_NAME_DRIFT_ASSESSMENT,
    SCHEMA_NAME_DRIFT_OBSERVATION,
    SCHEMA_NAME_DRIFT_POLICY,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
    SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
    SCHEMA_NAME_HEALTH_SNAPSHOT,
    SCHEMA_NAME_INCIDENT_RECORD,
    SCHEMA_NAME_KNOWN_GOOD_REFERENCE,
    SCHEMA_NAME_LEARNING_HYPOTHESIS,
    SCHEMA_NAME_LEDGER_ENVELOPE,
    SCHEMA_NAME_OUTCOME_RECORD,
    SCHEMA_NAME_PROMOTION_ELIGIBILITY,
    SCHEMA_NAME_PROMOTION_POLICY,
    SCHEMA_NAME_RELEASE_ARTIFACT,
    SCHEMA_NAME_ROLLBACK_RECORD,
    SCHEMA_NAME_VALIDATION_EVIDENCE_PACK,
    SCHEMA_VERSION_ATTRIBUTION_RECORD_V0,
    SCHEMA_VERSION_AUTONOMY_CYCLE_V0,
    SCHEMA_VERSION_CANDIDATE_ARTIFACT_V0,
    SCHEMA_VERSION_CANONICAL_EXPERIMENT_IDENTITY_REF_V0,
    SCHEMA_VERSION_COUNTERFACTUAL_RECORD_V0,
    SCHEMA_VERSION_DECISION_EVENT_V0,
    SCHEMA_VERSION_DEPLOYMENT_RECORD_V0,
    SCHEMA_VERSION_DRIFT_ASSESSMENT_V0,
    SCHEMA_VERSION_DRIFT_OBSERVATION_V0,
    SCHEMA_VERSION_DRIFT_POLICY_V0,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    SCHEMA_VERSION_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_V1,
    SCHEMA_VERSION_HEALTH_SNAPSHOT_V0,
    SCHEMA_VERSION_INCIDENT_RECORD_V0,
    SCHEMA_VERSION_KNOWN_GOOD_REFERENCE_V0,
    SCHEMA_VERSION_LEARNING_HYPOTHESIS_V0,
    SCHEMA_VERSION_LEDGER_ENVELOPE_V0,
    SCHEMA_VERSION_OUTCOME_RECORD_V0,
    SCHEMA_VERSION_PROMOTION_ELIGIBILITY_V0,
    SCHEMA_VERSION_PROMOTION_POLICY_V0,
    SCHEMA_VERSION_RELEASE_ARTIFACT_V0,
    SCHEMA_VERSION_ROLLBACK_RECORD_V0,
    SCHEMA_VERSION_VALIDATION_EVIDENCE_PACK_V0,
    require_event_time_utc,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    validate_double_play_entry_exit_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.section_11_14_flatten_pre_lease_observation_v1 import (
    validate_section_11_14_flatten_pre_lease_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.drift_contracts_v0 import (
    validate_drift_assessment_record_v0,
    validate_drift_observation_record_v0,
    validate_drift_policy_v0,
    validate_known_good_reference_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoConcurrentWriterError,
    DdoDuplicateConflictError,
    DdoDurabilityWriteError,
    DdoIntegrityError,
    DdoLedgerCorruptionError,
    DdoMalformedRecordError,
    DdoSilentOverwriteError,
    DdoUnsupportedSchemaVersionError,
    DdoValidationError,
    FAILURE_CLASS_UNKNOWN_IO,
    OPERATION_DIRECTORY_FSYNC,
    OPERATION_FILE_FSYNC,
    OPERATION_LEDGER_OPEN_CREATE,
    OPERATION_PARENT_MKDIR,
    OPERATION_WRITE,
    OPERATION_WRITER_LOCK,
    classify_oserror_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    validate_attribution_record_v0,
    validate_counterfactual_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.experiment_identity_binding_v0 import (
    validate_canonical_experiment_identity_ref_v0,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    validate_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    validate_candidate_artifact_v0,
    validate_learning_hypothesis_v0,
    validate_validation_evidence_pack_v0,
)
from src.learning.deterministic_decision_outcome_v0.lineage_v0 import validate_record_lineage_v0
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import validate_outcome_record_v0
from src.learning.deterministic_decision_outcome_v0.promotion_records_v0 import (
    validate_deployment_record_v0,
    validate_promotion_eligibility_record_v0,
    validate_promotion_policy_v0,
    validate_release_artifact_v0,
    validate_rollback_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonical_json_dumps_v0,
    compute_content_hash_v0,
    sha256_hex_v0,
)
from src.learning.deterministic_decision_outcome_v0.supervisor_records_v0 import (
    validate_autonomy_cycle_record_v0,
    validate_health_snapshot_v0,
)

GENESIS_LEDGER_HASH: Final[str] = "GENESIS"
LEDGER_FILENAME_DEFAULT: Final[str] = "ddo_ledger_v0.jsonl"
_WRITER_LOCK_SUFFIX: Final[str] = ".writer.lock"
_IN_PROCESS_APPEND_LOCKS: dict[str, threading.Lock] = {}
_IN_PROCESS_APPEND_LOCKS_GUARD = threading.Lock()

# Test-only write-boundary fault injection. Productive callers never set this.
# Default None is a no-op: no extra I/O, no swallowed errors, no temp files.
BOUNDARY_BEFORE_WRITE: Final[str] = "before_write"
BOUNDARY_DURING_WRITE: Final[str] = "during_write"
BOUNDARY_AFTER_WRITE_BEFORE_FILE_FSYNC: Final[str] = "after_write_before_file_fsync"
BOUNDARY_FILE_FSYNC: Final[str] = "file_fsync"
BOUNDARY_AFTER_FILE_FSYNC_BEFORE_CLOSE: Final[str] = "after_file_fsync_before_close"
BOUNDARY_AFTER_CLOSE_BEFORE_DIRECTORY_FSYNC: Final[str] = "after_close_before_directory_fsync"
BOUNDARY_DIRECTORY_FSYNC: Final[str] = "directory_fsync"
BOUNDARY_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN: Final[str] = "after_directory_fsync_before_return"
FAULT_ACTION_RAISE: Final[str] = "raise"
FAULT_ACTION_SHORT_WRITE: Final[str] = "short_write"
FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE: Final[str] = "partial_write_then_raise"
_LEDGER_WRITE_BOUNDARIES: Final[frozenset[str]] = frozenset(
    {
        BOUNDARY_BEFORE_WRITE,
        BOUNDARY_DURING_WRITE,
        BOUNDARY_AFTER_WRITE_BEFORE_FILE_FSYNC,
        BOUNDARY_FILE_FSYNC,
        BOUNDARY_AFTER_FILE_FSYNC_BEFORE_CLOSE,
        BOUNDARY_AFTER_CLOSE_BEFORE_DIRECTORY_FSYNC,
        BOUNDARY_DIRECTORY_FSYNC,
        BOUNDARY_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN,
    }
)
_LEDGER_FAULT_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        FAULT_ACTION_RAISE,
        FAULT_ACTION_SHORT_WRITE,
        FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
    }
)


class DdoLedgerFaultInjectorV1:
    """Deterministic test-only fault at one write-path boundary. Not a storage owner."""

    def __init__(
        self,
        *,
        boundary: str,
        action: str,
        errno_code: int = 5,
    ) -> None:
        if boundary not in _LEDGER_WRITE_BOUNDARIES:
            raise DdoValidationError(f"UNKNOWN_LEDGER_FAULT_BOUNDARY:{boundary}")
        if action not in _LEDGER_FAULT_ACTIONS:
            raise DdoValidationError(f"UNKNOWN_LEDGER_FAULT_ACTION:{action}")
        if action in {FAULT_ACTION_SHORT_WRITE, FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE}:
            if boundary != BOUNDARY_DURING_WRITE:
                raise DdoValidationError("LEDGER_FAULT_SHORT_WRITE_REQUIRES_DURING_WRITE")
        self.boundary = boundary
        self.action = action
        self.errno_code = errno_code
        self.fired = False

    def consume(self, boundary: str) -> bool:
        if boundary != self.boundary or self.fired:
            return False
        self.fired = True
        return True


_LEDGER_FAULT_INJECTOR: ContextVar[DdoLedgerFaultInjectorV1 | None] = ContextVar(
    "ddo_ledger_fault_injector_v1", default=None
)


def _raise_injected_oserror(injector: DdoLedgerFaultInjectorV1, boundary: str) -> None:
    raise OSError(injector.errno_code, f"injected_ledger_fault:{boundary}")


def _apply_ledger_fault_v1(boundary: str) -> None:
    injector = _LEDGER_FAULT_INJECTOR.get()
    if injector is None:
        return
    if not injector.consume(boundary):
        return
    if injector.action == FAULT_ACTION_RAISE:
        _raise_injected_oserror(injector, boundary)


@contextmanager
def ddo_ledger_fault_injection_v1(
    injector: DdoLedgerFaultInjectorV1,
) -> Iterator[DdoLedgerFaultInjectorV1]:
    """Install a test-only ledger fault. Productive code must not call this."""
    token: Token[DdoLedgerFaultInjectorV1 | None] = _LEDGER_FAULT_INJECTOR.set(injector)
    try:
        yield injector
    finally:
        _LEDGER_FAULT_INJECTOR.reset(token)


_VALIDATORS = {
    (SCHEMA_NAME_DECISION_EVENT, SCHEMA_VERSION_DECISION_EVENT_V0): validate_decision_event_v0,
    (SCHEMA_NAME_INCIDENT_RECORD, SCHEMA_VERSION_INCIDENT_RECORD_V0): validate_incident_record_v0,
    (SCHEMA_NAME_OUTCOME_RECORD, SCHEMA_VERSION_OUTCOME_RECORD_V0): validate_outcome_record_v0,
    (SCHEMA_NAME_COUNTERFACTUAL_RECORD, SCHEMA_VERSION_COUNTERFACTUAL_RECORD_V0): (
        validate_counterfactual_record_v0
    ),
    (SCHEMA_NAME_ATTRIBUTION_RECORD, SCHEMA_VERSION_ATTRIBUTION_RECORD_V0): (
        validate_attribution_record_v0
    ),
    (SCHEMA_NAME_LEARNING_HYPOTHESIS, SCHEMA_VERSION_LEARNING_HYPOTHESIS_V0): (
        validate_learning_hypothesis_v0
    ),
    (SCHEMA_NAME_CANDIDATE_ARTIFACT, SCHEMA_VERSION_CANDIDATE_ARTIFACT_V0): (
        validate_candidate_artifact_v0
    ),
    (SCHEMA_NAME_VALIDATION_EVIDENCE_PACK, SCHEMA_VERSION_VALIDATION_EVIDENCE_PACK_V0): (
        validate_validation_evidence_pack_v0
    ),
    (
        SCHEMA_NAME_PROMOTION_POLICY,
        SCHEMA_VERSION_PROMOTION_POLICY_V0,
    ): validate_promotion_policy_v0,
    (SCHEMA_NAME_PROMOTION_ELIGIBILITY, SCHEMA_VERSION_PROMOTION_ELIGIBILITY_V0): (
        validate_promotion_eligibility_record_v0
    ),
    (
        SCHEMA_NAME_RELEASE_ARTIFACT,
        SCHEMA_VERSION_RELEASE_ARTIFACT_V0,
    ): validate_release_artifact_v0,
    (SCHEMA_NAME_DEPLOYMENT_RECORD, SCHEMA_VERSION_DEPLOYMENT_RECORD_V0): (
        validate_deployment_record_v0
    ),
    (SCHEMA_NAME_ROLLBACK_RECORD, SCHEMA_VERSION_ROLLBACK_RECORD_V0): validate_rollback_record_v0,
    (SCHEMA_NAME_AUTONOMY_CYCLE, SCHEMA_VERSION_AUTONOMY_CYCLE_V0): (
        validate_autonomy_cycle_record_v0
    ),
    (SCHEMA_NAME_HEALTH_SNAPSHOT, SCHEMA_VERSION_HEALTH_SNAPSHOT_V0): validate_health_snapshot_v0,
    (
        SCHEMA_NAME_CANONICAL_EXPERIMENT_IDENTITY_REF,
        SCHEMA_VERSION_CANONICAL_EXPERIMENT_IDENTITY_REF_V0,
    ): validate_canonical_experiment_identity_ref_v0,
    (
        SCHEMA_NAME_DRIFT_OBSERVATION,
        SCHEMA_VERSION_DRIFT_OBSERVATION_V0,
    ): validate_drift_observation_record_v0,
    (
        SCHEMA_NAME_DRIFT_ASSESSMENT,
        SCHEMA_VERSION_DRIFT_ASSESSMENT_V0,
    ): validate_drift_assessment_record_v0,
    (
        SCHEMA_NAME_KNOWN_GOOD_REFERENCE,
        SCHEMA_VERSION_KNOWN_GOOD_REFERENCE_V0,
    ): validate_known_good_reference_v0,
    (SCHEMA_NAME_DRIFT_POLICY, SCHEMA_VERSION_DRIFT_POLICY_V0): validate_drift_policy_v0,
    (
        SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION,
        SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_OBSERVATION_V1,
    ): validate_double_play_entry_exit_observation_v1,
    (
        SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
        SCHEMA_VERSION_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION_V1,
    ): validate_section_11_14_flatten_pre_lease_observation_v1,
}

_KNOWN_SCHEMA_NAMES = {schema for schema, _version in _VALIDATORS}


@dataclass(frozen=True)
class AppendResultV0:
    status: str
    record_id: str
    content_hash: str
    sequence: int
    ledger_entry_hash: str


def validate_canonical_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    schema_name = payload.get("schema_name")
    schema_version = payload.get("schema_version")
    validator = _VALIDATORS.get((str(schema_name), str(schema_version)))
    if validator is None:
        if schema_name in _KNOWN_SCHEMA_NAMES:
            raise DdoUnsupportedSchemaVersionError(
                f"UNSUPPORTED_SCHEMA_VERSION:{schema_name}:{schema_version!r}"
            )
        raise DdoValidationError(f"UNKNOWN_RECORD_SCHEMA:{schema_name!r}")
    return validator(payload)


def _record_type_for_schema(schema_name: str) -> str:
    if schema_name not in _KNOWN_SCHEMA_NAMES:
        raise DdoValidationError(f"UNKNOWN_RECORD_TYPE:{schema_name}")
    return schema_name


def _envelope_chain_material(
    *,
    sequence: int,
    prev_ledger_hash: str,
    record_id: str,
    schema_name: str,
    schema_version: str,
    content_hash: str,
) -> dict[str, Any]:
    return {
        "content_hash": content_hash,
        "prev_ledger_hash": prev_ledger_hash,
        "record_id": record_id,
        "schema_name": schema_name,
        "schema_version": schema_version,
        "sequence": sequence,
    }


def compute_ledger_entry_hash_v0(
    *,
    sequence: int,
    prev_ledger_hash: str,
    record_id: str,
    schema_name: str,
    schema_version: str,
    content_hash: str,
) -> str:
    return sha256_hex_v0(
        canonical_json_dumps_v0(
            _envelope_chain_material(
                sequence=sequence,
                prev_ledger_hash=prev_ledger_hash,
                record_id=record_id,
                schema_name=schema_name,
                schema_version=schema_version,
                content_hash=content_hash,
            )
        )
    )


def _decode_envelope_line(line: str, *, expected_sequence: int) -> dict[str, Any]:
    text = line[:-1] if line.endswith("\n") else line
    if not text or text.strip() != text:
        raise DdoMalformedRecordError("MALFORMED_LEDGER_LINE")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DdoMalformedRecordError("MALFORMED_LEDGER_JSON") from exc
    if not isinstance(payload, dict):
        raise DdoMalformedRecordError("MALFORMED_LEDGER_OBJECT")
    if payload.get("envelope_schema_name") != SCHEMA_NAME_LEDGER_ENVELOPE:
        raise DdoLedgerCorruptionError("UNKNOWN_ENVELOPE_SCHEMA")
    if payload.get("envelope_schema_version") != SCHEMA_VERSION_LEDGER_ENVELOPE_V0:
        raise DdoUnsupportedSchemaVersionError(
            f"UNSUPPORTED_SCHEMA_VERSION:{SCHEMA_NAME_LEDGER_ENVELOPE}:"
            f"{payload.get('envelope_schema_version')!r}"
        )
    if payload.get("sequence") != expected_sequence:
        raise DdoLedgerCorruptionError(
            f"SEQUENCE_GAP:expected={expected_sequence}:got={payload.get('sequence')!r}"
        )
    inner = payload.get("payload")
    if not isinstance(inner, dict):
        raise DdoMalformedRecordError("ENVELOPE_PAYLOAD_MISSING")
    try:
        record = validate_canonical_record_v0(inner)
    except DdoValidationError as exc:
        if str(exc) == "CONTENT_HASH_MISMATCH":
            raise DdoIntegrityError("PAYLOAD_CONTENT_HASH_MISMATCH") from exc
        raise DdoMalformedRecordError(str(exc)) from exc
    if record["record_id"] != payload.get("record_id"):
        raise DdoIntegrityError("ENVELOPE_RECORD_ID_MISMATCH")
    if record["schema_name"] != payload.get("schema_name"):
        raise DdoIntegrityError("ENVELOPE_SCHEMA_NAME_MISMATCH")
    if record["schema_version"] != payload.get("schema_version"):
        raise DdoIntegrityError("ENVELOPE_SCHEMA_VERSION_MISMATCH")
    if record["content_hash"] != payload.get("content_hash"):
        raise DdoIntegrityError("ENVELOPE_CONTENT_HASH_MISMATCH")
    recomputed = compute_content_hash_v0(record)
    if recomputed != record["content_hash"]:
        raise DdoIntegrityError("PAYLOAD_CONTENT_HASH_MISMATCH")
    return {"envelope": payload, "record": dict(record)}


def _in_process_append_lock(path_key: str) -> threading.Lock:
    with _IN_PROCESS_APPEND_LOCKS_GUARD:
        return _IN_PROCESS_APPEND_LOCKS.setdefault(path_key, threading.Lock())


class AppendOnlyDdoLedgerV0:
    """File-backed append-only JSONL ledger for DDO v0 records."""

    def __init__(self, ledger_path: Path | str) -> None:
        path = Path(ledger_path)
        if not path.is_absolute():
            raise DdoValidationError("LEDGER_PATH_MUST_BE_ABSOLUTE")
        if path.exists() and path.is_dir():
            raise DdoValidationError("LEDGER_PATH_MUST_BE_FILE")
        self._path = path

    @property
    def ledger_path(self) -> Path:
        return self._path

    def writer_lock_path(self) -> Path:
        return Path(str(self._path) + _WRITER_LOCK_SUFFIX)

    def append(
        self,
        payload: Mapping[str, Any],
        *,
        ingested_at_utc: str | None = None,
    ) -> AppendResultV0:
        record = validate_canonical_record_v0(payload)
        with self._exclusive_writer():
            return self._append_locked(record, ingested_at_utc=ingested_at_utc)

    def _append_locked(
        self,
        record: Mapping[str, Any],
        *,
        ingested_at_utc: str | None,
    ) -> AppendResultV0:
        envelopes, by_id = self._load()
        existing = by_id.get(str(record["record_id"]))
        if existing is not None:
            if existing["content_hash"] == record["content_hash"]:
                env = next(
                    item["envelope"]
                    for item in envelopes
                    if item["record"]["record_id"] == record["record_id"]
                )
                return AppendResultV0(
                    status="IDEMPOTENT_REPLAY",
                    record_id=str(record["record_id"]),
                    content_hash=str(record["content_hash"]),
                    sequence=int(env["sequence"]),
                    ledger_entry_hash=str(env["ledger_entry_hash"]),
                )
            raise DdoDuplicateConflictError(f"DUPLICATE_RECORD_ID_CONFLICT:{record['record_id']}")
        validate_record_lineage_v0(record, existing_by_id=by_id)
        if ingested_at_utc is not None:
            require_event_time_utc(ingested_at_utc, "ingested_at_utc")
        sequence = len(envelopes) + 1
        prev = (
            GENESIS_LEDGER_HASH
            if not envelopes
            else str(envelopes[-1]["envelope"]["ledger_entry_hash"])
        )
        entry_hash = compute_ledger_entry_hash_v0(
            sequence=sequence,
            prev_ledger_hash=prev,
            record_id=str(record["record_id"]),
            schema_name=str(record["schema_name"]),
            schema_version=str(record["schema_version"]),
            content_hash=str(record["content_hash"]),
        )
        envelope = {
            "content_hash": record["content_hash"],
            "envelope_schema_name": SCHEMA_NAME_LEDGER_ENVELOPE,
            "envelope_schema_version": SCHEMA_VERSION_LEDGER_ENVELOPE_V0,
            "ingested_at_utc": ingested_at_utc,
            "ledger_entry_hash": entry_hash,
            "payload": dict(record),
            "prev_ledger_hash": prev,
            "record_id": record["record_id"],
            "record_type": _record_type_for_schema(str(record["schema_name"])),
            "schema_name": record["schema_name"],
            "schema_version": record["schema_version"],
            "sequence": sequence,
        }
        line = canonical_json_dumps_v0(envelope) + "\n"
        self._append_line(line)
        return AppendResultV0(
            status="APPENDED",
            record_id=str(record["record_id"]),
            content_hash=str(record["content_hash"]),
            sequence=sequence,
            ledger_entry_hash=entry_hash,
        )

    @contextmanager
    def _exclusive_writer(self) -> Iterator[None]:
        path_key = str(self._path)
        in_process = _in_process_append_lock(path_key)
        if not in_process.acquire(blocking=False):
            raise DdoConcurrentWriterError(
                "CONCURRENT_WRITER_VIOLATION",
                operation=OPERATION_WRITER_LOCK,
            )
        lock_fd: int | None = None
        try:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise classify_oserror_v0(exc, operation=OPERATION_PARENT_MKDIR) from exc
            lock_path = self.writer_lock_path()
            try:
                lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise DdoConcurrentWriterError(
                    "CONCURRENT_WRITER_VIOLATION",
                    operation=OPERATION_WRITER_LOCK,
                ) from exc
            except OSError as exc:
                raise classify_oserror_v0(exc, operation=OPERATION_WRITER_LOCK) from exc
            yield
        finally:
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                except OSError:
                    pass
                os.close(lock_fd)
            in_process.release()

    def read_all(self) -> tuple[MappingProxyType[str, Any], ...]:
        envelopes, _by_id = self._load()
        return tuple(MappingProxyType(item["record"]) for item in envelopes)

    def get(self, record_id: str) -> MappingProxyType[str, Any]:
        ident = require_record_id(record_id, "record_id")
        _envelopes, by_id = self._load()
        if ident not in by_id:
            raise DdoValidationError(f"RECORD_NOT_FOUND:{ident}")
        return MappingProxyType(by_id[ident])

    def verify_integrity(self) -> None:
        self._load()

    def _load(self) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        if not self._path.exists():
            return [], {}
        if self._path.is_dir():
            raise DdoSilentOverwriteError("LEDGER_PATH_IS_DIRECTORY")
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise DdoLedgerCorruptionError("LEDGER_UNREADABLE") from exc
        if text == "":
            return [], {}
        if not text.endswith("\n"):
            raise DdoLedgerCorruptionError("LEDGER_MISSING_TRAILING_NEWLINE")
        envelopes: list[dict[str, Any]] = []
        by_id: dict[str, dict[str, Any]] = {}
        prev_hash = GENESIS_LEDGER_HASH
        for index, line in enumerate(text.splitlines(keepends=True), start=1):
            decoded = _decode_envelope_line(line, expected_sequence=index)
            envelope = decoded["envelope"]
            if envelope.get("prev_ledger_hash") != prev_hash:
                raise DdoLedgerCorruptionError("LEDGER_CHAIN_BREAK")
            expected_entry = compute_ledger_entry_hash_v0(
                sequence=int(envelope["sequence"]),
                prev_ledger_hash=str(envelope["prev_ledger_hash"]),
                record_id=str(envelope["record_id"]),
                schema_name=str(envelope["schema_name"]),
                schema_version=str(envelope["schema_version"]),
                content_hash=str(envelope["content_hash"]),
            )
            if envelope.get("ledger_entry_hash") != expected_entry:
                raise DdoIntegrityError("LEDGER_ENTRY_HASH_MISMATCH")
            record_id = str(decoded["record"]["record_id"])
            if record_id in by_id:
                raise DdoLedgerCorruptionError(f"DUPLICATE_RECORD_ID_IN_LEDGER:{record_id}")
            validate_record_lineage_v0(decoded["record"], existing_by_id=by_id)
            envelopes.append(decoded)
            by_id[record_id] = decoded["record"]
            prev_hash = str(envelope["ledger_entry_hash"])
        return envelopes, by_id

    def _append_line(self, line: str) -> None:
        encoded = line.encode("utf-8")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise classify_oserror_v0(exc, operation=OPERATION_PARENT_MKDIR) from exc
        if self._path.exists() and not self._path.is_file():
            raise DdoSilentOverwriteError("LEDGER_PATH_NOT_FILE")
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        try:
            fd = os.open(str(self._path), flags, 0o644)
        except OSError as exc:
            raise classify_oserror_v0(exc, operation=OPERATION_LEDGER_OPEN_CREATE) from exc
        try:
            try:
                _apply_ledger_fault_v1(BOUNDARY_BEFORE_WRITE)
                written = self._write_encoded(fd, encoded)
            except OSError as exc:
                raise classify_oserror_v0(exc, operation=OPERATION_WRITE) from exc
            if written != len(encoded):
                raise DdoDurabilityWriteError(
                    FAILURE_CLASS_UNKNOWN_IO,
                    "UNKNOWN_UNCLASSIFIED_IO_FAILURE",
                    retryable=None,
                    operation=OPERATION_WRITE,
                )
            try:
                _apply_ledger_fault_v1(BOUNDARY_AFTER_WRITE_BEFORE_FILE_FSYNC)
            except OSError as exc:
                raise classify_oserror_v0(exc, operation=OPERATION_WRITE) from exc
            try:
                _apply_ledger_fault_v1(BOUNDARY_FILE_FSYNC)
                os.fsync(fd)
            except OSError as exc:
                raise classify_oserror_v0(exc, operation=OPERATION_FILE_FSYNC) from exc
            try:
                _apply_ledger_fault_v1(BOUNDARY_AFTER_FILE_FSYNC_BEFORE_CLOSE)
            except OSError as exc:
                raise classify_oserror_v0(exc, operation=OPERATION_FILE_FSYNC) from exc
        finally:
            os.close(fd)
        try:
            _apply_ledger_fault_v1(BOUNDARY_AFTER_CLOSE_BEFORE_DIRECTORY_FSYNC)
        except OSError as exc:
            raise classify_oserror_v0(exc, operation=OPERATION_FILE_FSYNC) from exc
        dir_fd: int | None = None
        try:
            dir_fd = os.open(str(self._path.parent), os.O_RDONLY)
            _apply_ledger_fault_v1(BOUNDARY_DIRECTORY_FSYNC)
            os.fsync(dir_fd)
            _apply_ledger_fault_v1(BOUNDARY_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN)
        except OSError as exc:
            raise classify_oserror_v0(exc, operation=OPERATION_DIRECTORY_FSYNC) from exc
        finally:
            if dir_fd is not None:
                os.close(dir_fd)

    def _write_encoded(self, fd: int, encoded: bytes) -> int:
        injector = _LEDGER_FAULT_INJECTOR.get()
        if injector is not None and injector.consume(BOUNDARY_DURING_WRITE):
            if injector.action == FAULT_ACTION_SHORT_WRITE:
                if not encoded:
                    return 0
                return 1 if len(encoded) > 1 else 0
            if injector.action == FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE:
                cut = max(1, len(encoded) // 2)
                os.write(fd, encoded[:cut])
                _raise_injected_oserror(injector, BOUNDARY_DURING_WRITE)
            _raise_injected_oserror(injector, BOUNDARY_DURING_WRITE)
        return os.write(fd, encoded)

"""Recovery authorization, durable transition journal and ACTIVE attestation.

Trust boundary: the approval secret lives only in the environment variable named
by ``approval_code_env`` (default ``KILL_SWITCH_APPROVAL_CODE``). It is never
logged, never accepted via argv and never persisted. Persisted records carry
HMAC-SHA256 tags derived from that secret, so a state or journal file written
without the secret cannot attest ACTIVE.

The journal is append-only. KILL events are appended without the state lock and
without the secret (a kill must never depend on either). An ACTIVE state is only
attested while the last transition in the journal is the signed
RECOVERY_COMPLETED event bound to it, directly preceded by its signed
RECOVERY_REQUESTED event. Any later KILL, any replayed (duplicated) event and any
copied or restored older ACTIVE file therefore fails verification.

Not covered: a writer that truncates the journal *and* restores an older ACTIVE
state file together. There is no external monotonic anchor in the CURRENT
filesystem boundary to detect such a joint rollback.

This module is stdlib-only and does not write kill-switch state.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

DEFAULT_APPROVAL_CODE_ENV = "KILL_SWITCH_APPROVAL_CODE"
JOURNAL_DIRNAME = "audit"
JOURNAL_FILENAME = "kill_switch_transition_journal_v1.jsonl"
MAX_JOURNAL_LINE_BYTES = 3500

KIND_KILL = "KILL"
KIND_RECOVERY_REQUESTED = "RECOVERY_REQUESTED"
KIND_RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
KIND_RECOVERY_DENIED = "RECOVERY_DENIED"
TRANSITION_KINDS = frozenset({KIND_KILL, KIND_RECOVERY_REQUESTED, KIND_RECOVERY_COMPLETED})
JOURNAL_KINDS = TRANSITION_KINDS | {KIND_RECOVERY_DENIED}

_KEY_CONTEXT = b"peak_trade.kill_switch.recovery_attestation.v1"
_TAG_HEX_LEN = 64

ACTIVE_RECORD_KEYS = (
    "request_id",
    "requested_event_id",
    "completed_event_id",
    "recovery_started_at",
    "completed_at",
    "attestation",
)


class JournalError(RuntimeError):
    """Journal unreadable, torn, inconsistent or not writable (fail-closed)."""


# --------------------------------------------------------------------------- secret


def resolve_approval_secret(env_var: Optional[str] = None) -> Optional[str]:
    name = str(env_var or "").strip() or DEFAULT_APPROVAL_CODE_ENV
    value = os.environ.get(name, "")
    return value if value.strip() else None


def approval_code_matches(expected: Optional[str], provided: Optional[str]) -> bool:
    """Constant-time match. Missing or blank expected/provided never match."""
    if not isinstance(expected, str) or not expected.strip():
        return False
    if not isinstance(provided, str) or not provided.strip():
        return False
    return hmac.compare_digest(expected.encode("utf-8"), provided.encode("utf-8"))


def derive_attestation_key(secret: Optional[str]) -> Optional[bytes]:
    if not isinstance(secret, str) or not secret.strip():
        return None
    return hmac.new(secret.encode("utf-8"), _KEY_CONTEXT, hashlib.sha256).digest()


def attestation_key_from_env(env_var: Optional[str] = None) -> Optional[bytes]:
    return derive_attestation_key(resolve_approval_secret(env_var))


def _canonical_bytes(fields: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(fields), sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_fields(key: bytes, fields: Mapping[str, Any]) -> str:
    return hmac.new(key, _canonical_bytes(fields), hashlib.sha256).hexdigest()


def verify_fields(key: Optional[bytes], fields: Mapping[str, Any], tag: object) -> bool:
    if key is None or not isinstance(tag, str) or len(tag) != _TAG_HEX_LEN:
        return False
    return hmac.compare_digest(sign_fields(key, fields), tag)


def _bound_state_path(state_file: Path | str) -> str:
    return str(Path(state_file).resolve())


def requested_event_fields(state_file: Path | str, event: Mapping[str, Any]) -> dict:
    return {
        "kind": KIND_RECOVERY_REQUESTED,
        "event_id": event.get("event_id"),
        "request_id": event.get("request_id"),
        "recovery_started_at": event.get("recovery_started_at"),
        "cooldown_seconds": event.get("cooldown_seconds"),
        "approved_by": event.get("approved_by"),
        "state_path": _bound_state_path(state_file),
    }


def completed_event_fields(state_file: Path | str, event: Mapping[str, Any]) -> dict:
    return {
        "kind": KIND_RECOVERY_COMPLETED,
        "event_id": event.get("event_id"),
        "request_id": event.get("request_id"),
        "parent_event_id": event.get("parent_event_id"),
        "completed_at": event.get("completed_at"),
        "approved_by": event.get("approved_by"),
        "state_path": _bound_state_path(state_file),
    }


def active_record_fields(state_file: Path | str, record: Mapping[str, Any]) -> dict:
    return {
        "state": "ACTIVE",
        "request_id": record.get("request_id"),
        "requested_event_id": record.get("requested_event_id"),
        "completed_event_id": record.get("completed_event_id"),
        "recovery_started_at": record.get("recovery_started_at"),
        "completed_at": record.get("completed_at"),
        "state_path": _bound_state_path(state_file),
    }


def new_identifier() -> str:
    return uuid.uuid4().hex


def parse_naive_utc(value: object) -> Optional[datetime]:
    """Writer timestamps are naive UTC ISO strings; anything else is invalid."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return None
    return parsed


# --------------------------------------------------------------------------- journal


def journal_path_for_state_file(state_file: Path | str) -> Path:
    return Path(state_file).parent / JOURNAL_DIRNAME / JOURNAL_FILENAME


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class TransitionJournal:
    """Append-only JSONL journal; one ``os.write`` + ``fsync`` per event."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def append(self, record: Mapping[str, Any]) -> dict:
        event = dict(record)
        if event.get("kind") not in JOURNAL_KINDS:
            raise JournalError("JOURNAL_EVENT_KIND_INVALID")
        event.setdefault("event_id", new_identifier())
        event.setdefault("timestamp", datetime.utcnow().isoformat())
        line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if len(line) > MAX_JOURNAL_LINE_BYTES:
            raise JournalError("JOURNAL_LINE_TOO_LARGE")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        created = not self.path.exists()
        fd = os.open(str(self.path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            if os.write(fd, line) != len(line):
                raise JournalError("JOURNAL_SHORT_WRITE")
            os.fsync(fd)
        finally:
            os.close(fd)
        if created:
            _fsync_dir(self.path.parent)
        return event

    def exists(self) -> bool:
        return self.path.is_file()

    def read_events(self) -> list[dict]:
        if not self.path.is_file():
            return []
        try:
            raw = self.path.read_bytes()
        except OSError as exc:
            raise JournalError("JOURNAL_UNREADABLE") from exc
        if raw and not raw.endswith(b"\n"):
            raise JournalError("JOURNAL_TORN_TAIL")
        events: list[dict] = []
        seen: set[str] = set()
        for line in raw.splitlines():
            try:
                event = json.loads(line)
            except ValueError as exc:
                raise JournalError("JOURNAL_LINE_UNREADABLE") from exc
            if not isinstance(event, dict) or event.get("kind") not in JOURNAL_KINDS:
                raise JournalError("JOURNAL_EVENT_INVALID")
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                raise JournalError("JOURNAL_EVENT_ID_MISSING")
            if event_id in seen:
                raise JournalError("JOURNAL_DUPLICATE_EVENT_ID")
            seen.add(event_id)
            events.append(event)
        return events


def last_transition_index(events: Sequence[Mapping[str, Any]], before: Optional[int] = None) -> int:
    """Index of the last transition event (DENIED entries are skipped), or -1."""
    idx = (len(events) if before is None else before) - 1
    while idx >= 0 and events[idx].get("kind") not in TRANSITION_KINDS:
        idx -= 1
    return idx


# --------------------------------------------------------------------------- verification


@dataclass(frozen=True)
class AttestationCheckV1:
    verified: bool
    reason: str


def _fail(reason: str) -> AttestationCheckV1:
    return AttestationCheckV1(False, reason)


def verify_pending_request_binding(
    *,
    state_file: Path | str,
    events: Sequence[Mapping[str, Any]],
    recovery: Mapping[str, Any],
    key: Optional[bytes],
) -> AttestationCheckV1:
    """The last transition must be the signed REQUESTED event of ``recovery``."""
    idx = last_transition_index(events)
    if idx < 0:
        return _fail("JOURNAL_REQUEST_NOT_LAST_TRANSITION")
    event = events[idx]
    if event.get("kind") != KIND_RECOVERY_REQUESTED:
        return _fail("JOURNAL_TRANSITION_AFTER_REQUEST")
    if event.get("event_id") != recovery.get("requested_event_id"):
        return _fail("JOURNAL_REQUEST_EVENT_MISMATCH")
    if event.get("request_id") != recovery.get("request_id"):
        return _fail("JOURNAL_REQUEST_ID_MISMATCH")
    if event.get("recovery_started_at") != recovery.get("recovery_started_at"):
        return _fail("JOURNAL_REQUEST_TIMESTAMP_MISMATCH")
    if not verify_fields(key, requested_event_fields(state_file, event), event.get("tag")):
        return _fail("JOURNAL_REQUEST_TAG_INVALID")
    same_request = [
        e
        for e in events
        if e.get("kind") == KIND_RECOVERY_REQUESTED
        and e.get("request_id") == event.get("request_id")
    ]
    if len(same_request) != 1:
        return _fail("JOURNAL_REQUEST_ID_REUSED")
    return AttestationCheckV1(True, "REQUEST_BINDING_VERIFIED")


def verify_active_attestation(
    *,
    state_file: Path | str,
    payload: Mapping[str, Any],
    key: Optional[bytes],
    events: Optional[Sequence[Mapping[str, Any]]] = None,
) -> AttestationCheckV1:
    """Full provenance check of a persisted ACTIVE state (fail-closed)."""
    if key is None:
        return _fail("ACTIVE_ATTESTATION_KEY_UNAVAILABLE")
    if str(payload.get("state") or "").strip().upper() != "ACTIVE":
        return _fail("ACTIVE_ATTESTATION_STATE_NOT_ACTIVE")
    record = payload.get("recovery")
    if not isinstance(record, dict) or any(
        not isinstance(record.get(k), str) or not record.get(k) for k in ACTIVE_RECORD_KEYS
    ):
        return _fail("ACTIVE_ATTESTATION_MISSING")
    if not verify_fields(key, active_record_fields(state_file, record), record.get("attestation")):
        return _fail("ACTIVE_ATTESTATION_INVALID")
    if events is None:
        try:
            events = TransitionJournal(journal_path_for_state_file(state_file)).read_events()
        except JournalError as exc:
            return _fail(f"ACTIVE_{exc}")
    idx = last_transition_index(events)
    if idx < 0:
        return _fail("ACTIVE_JOURNAL_MISSING_COMPLETION")
    completed = events[idx]
    if completed.get("kind") != KIND_RECOVERY_COMPLETED:
        return _fail("ACTIVE_SUPERSEDED_BY_LATER_TRANSITION")
    if completed.get("event_id") != record.get("completed_event_id"):
        return _fail("ACTIVE_COMPLETION_EVENT_MISMATCH")
    if completed.get("request_id") != record.get("request_id"):
        return _fail("ACTIVE_COMPLETION_REQUEST_MISMATCH")
    if completed.get("parent_event_id") != record.get("requested_event_id"):
        return _fail("ACTIVE_COMPLETION_PARENT_MISMATCH")
    if completed.get("completed_at") != record.get("completed_at"):
        return _fail("ACTIVE_COMPLETION_TIMESTAMP_MISMATCH")
    if not verify_fields(key, completed_event_fields(state_file, completed), completed.get("tag")):
        return _fail("ACTIVE_COMPLETION_TAG_INVALID")
    completions = [
        e
        for e in events
        if e.get("kind") == KIND_RECOVERY_COMPLETED
        and e.get("request_id") == record.get("request_id")
    ]
    if len(completions) != 1:
        return _fail("ACTIVE_COMPLETION_REPLAYED")
    request = verify_pending_request_binding(
        state_file=state_file,
        events=events[:idx],
        recovery=record,
        key=key,
    )
    if not request.verified:
        return _fail(f"ACTIVE_{request.reason}")
    return AttestationCheckV1(True, "ACTIVE_ATTESTATION_VERIFIED")


def verify_active_attestation_from_env(
    state_file: Path | str, payload: Mapping[str, Any], env_var: Optional[str] = None
) -> AttestationCheckV1:
    return verify_active_attestation(
        state_file=state_file, payload=payload, key=attestation_key_from_env(env_var)
    )


def active_state_superseded_by_journal(state_file: Path | str, payload: Mapping[str, Any]) -> bool:
    """Secret-free structural check for ACTIVE readers.

    True (block) when a journal exists and is unreadable, or its last transition
    is not the completion this ACTIVE state claims. No journal: False (the
    durable state file alone decides, as before).
    """
    journal = TransitionJournal(journal_path_for_state_file(state_file))
    if not journal.exists():
        return False
    try:
        events = journal.read_events()
    except JournalError:
        return True
    idx = last_transition_index(events)
    if idx < 0:
        return False
    last = events[idx]
    if last.get("kind") != KIND_RECOVERY_COMPLETED:
        return True
    record = payload.get("recovery")
    if not isinstance(record, dict):
        return True
    return last.get("event_id") != record.get("completed_event_id")


__all__ = [
    "ACTIVE_RECORD_KEYS",
    "AttestationCheckV1",
    "DEFAULT_APPROVAL_CODE_ENV",
    "JOURNAL_FILENAME",
    "JournalError",
    "KIND_KILL",
    "KIND_RECOVERY_COMPLETED",
    "KIND_RECOVERY_DENIED",
    "KIND_RECOVERY_REQUESTED",
    "TransitionJournal",
    "active_record_fields",
    "active_state_superseded_by_journal",
    "approval_code_matches",
    "attestation_key_from_env",
    "completed_event_fields",
    "derive_attestation_key",
    "journal_path_for_state_file",
    "last_transition_index",
    "new_identifier",
    "parse_naive_utc",
    "requested_event_fields",
    "resolve_approval_secret",
    "sign_fields",
    "verify_active_attestation",
    "verify_active_attestation_from_env",
    "verify_fields",
    "verify_pending_request_binding",
]

"""Bounded recovery: fence → reconcile → resume (no alpha authority).

Reuses O2 supervisor lifecycle fencing/single-writer semantics. Does not invent
a parallel supervision stack or alter trading/alpha authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    ConflictingWriterError,
    DuplicateSessionError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    ProcessIdentityV1,
    SessionRecordV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import (
    LauncherSingleWriterV1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    DEFAULT_BOUNDED_RETRY_LIMIT,
    DEFAULT_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS,
    RECOVERY_INVARIANTS,
    SAFETY_INVARIANTS,
)


class RecoveryErrorV1(RuntimeError):
    """Fail-closed recovery contract violation."""


@dataclass
class PersistedRuntimeCursorV1:
    """Minimal persisted runtime cursor for offline recovery proofs."""

    session_id: str
    repository_sha: str
    config_digest: str
    market_observation_epoch: int = 0
    bar_finalization_count: int = 0
    read_model_commit_count: int = 0
    confirmation_advance_count: int = 0
    fill_count: int = 0
    evidence_cursor: int = 0
    state_commit_position: int = 0
    fenced: bool = False
    reconciled: bool = False
    processing_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "market_observation_epoch": int(self.market_observation_epoch),
            "bar_finalization_count": int(self.bar_finalization_count),
            "read_model_commit_count": int(self.read_model_commit_count),
            "confirmation_advance_count": int(self.confirmation_advance_count),
            "fill_count": int(self.fill_count),
            "evidence_cursor": int(self.evidence_cursor),
            "state_commit_position": int(self.state_commit_position),
            "fenced": bool(self.fenced),
            "reconciled": bool(self.reconciled),
            "processing_allowed": bool(self.processing_allowed),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PersistedRuntimeCursorV1":
        return cls(
            session_id=str(raw["session_id"]),
            repository_sha=str(raw["repository_sha"]),
            config_digest=str(raw["config_digest"]),
            market_observation_epoch=int(raw.get("market_observation_epoch") or 0),
            bar_finalization_count=int(raw.get("bar_finalization_count") or 0),
            read_model_commit_count=int(raw.get("read_model_commit_count") or 0),
            confirmation_advance_count=int(raw.get("confirmation_advance_count") or 0),
            fill_count=int(raw.get("fill_count") or 0),
            evidence_cursor=int(raw.get("evidence_cursor") or 0),
            state_commit_position=int(raw.get("state_commit_position") or 0),
            fenced=bool(raw.get("fenced") or False),
            reconciled=bool(raw.get("reconciled") or False),
            processing_allowed=bool(raw.get("processing_allowed") or False),
        )


def write_persisted_cursor_v1(path: Path, cursor: PersistedRuntimeCursorV1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cursor.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def load_persisted_cursor_v1(path: Path) -> PersistedRuntimeCursorV1:
    return PersistedRuntimeCursorV1.from_dict(json.loads(path.read_text(encoding="utf-8")))


def fence_session_before_recovery_v1(cursor: PersistedRuntimeCursorV1) -> PersistedRuntimeCursorV1:
    """Fence failed/active session before any recovery resume."""
    cursor.fenced = True
    cursor.processing_allowed = False
    cursor.reconciled = False
    return cursor


def reconcile_persisted_state_before_resume_v1(
    cursor: PersistedRuntimeCursorV1,
    *,
    expected_session_id: str,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> PersistedRuntimeCursorV1:
    if not cursor.fenced:
        raise RecoveryErrorV1("SESSION_NOT_FENCED_BEFORE_RECONCILIATION")
    if cursor.session_id != expected_session_id:
        raise RecoveryErrorV1("SESSION_ID_RECONCILIATION_MISMATCH")
    if cursor.repository_sha != expected_repository_sha:
        raise RecoveryErrorV1("REPOSITORY_SHA_RECONCILIATION_MISMATCH")
    if cursor.config_digest != expected_config_digest:
        raise RecoveryErrorV1("CONFIG_DIGEST_RECONCILIATION_MISMATCH")
    cursor.reconciled = True
    return cursor


def resume_after_reconciliation_v1(cursor: PersistedRuntimeCursorV1) -> PersistedRuntimeCursorV1:
    if not cursor.fenced:
        raise RecoveryErrorV1("SESSION_NOT_FENCED_BEFORE_RESUME")
    if not cursor.reconciled:
        raise RecoveryErrorV1("RECONCILIATION_REQUIRED_BEFORE_RESUME")
    if SAFETY_INVARIANTS["HEALTH_HAS_ALPHA_AUTHORITY"]:
        raise RecoveryErrorV1("RECOVERY_MUST_NOT_HAVE_ALPHA_AUTHORITY")
    if RECOVERY_INVARIANTS["RECOVERY_HAS_ALPHA_AUTHORITY"]:
        raise RecoveryErrorV1("RECOVERY_MUST_NOT_HAVE_ALPHA_AUTHORITY")
    cursor.processing_allowed = True
    return cursor


def bounded_retry_policy_v1(
    *,
    attempt: int,
    retry_limit: int = DEFAULT_BOUNDED_RETRY_LIMIT,
    automatic_recovery_allowed: bool,
) -> dict[str, Any]:
    if not automatic_recovery_allowed:
        return {
            "ok": True,
            "retry_allowed": False,
            "owner_action_required": True,
            "attempt": int(attempt),
            "retry_limit": int(retry_limit),
        }
    allowed = int(attempt) < int(retry_limit)
    return {
        "ok": True,
        "retry_allowed": allowed,
        "owner_action_required": not allowed,
        "attempt": int(attempt),
        "retry_limit": int(retry_limit),
    }


def advance_cursor_idempotent_v1(
    cursor: PersistedRuntimeCursorV1,
    *,
    field_name: str,
    proposed_value: int,
) -> dict[str, Any]:
    """Advance a monotonic cursor only when proposed value is strictly greater."""
    if not cursor.processing_allowed:
        raise RecoveryErrorV1("PROCESSING_NOT_ALLOWED_BEFORE_RESUME")
    current = int(getattr(cursor, field_name))
    proposed = int(proposed_value)
    if proposed < current:
        raise RecoveryErrorV1(f"CURSOR_REGRESSION:{field_name}:{proposed}<{current}")
    if proposed == current:
        return {
            "ok": True,
            "advanced": False,
            "field": field_name,
            "value": current,
            "duplicate_blocked": True,
        }
    setattr(cursor, field_name, proposed)
    cursor.state_commit_position = max(cursor.state_commit_position, proposed)
    return {
        "ok": True,
        "advanced": True,
        "field": field_name,
        "value": proposed,
        "duplicate_blocked": False,
    }


def recover_from_persisted_active_state_v1(
    cursor_path: Path,
    *,
    expected_session_id: str,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    """Offline recovery path: fence → reconcile → resume from persisted cursor."""
    cursor = load_persisted_cursor_v1(cursor_path)
    fence_session_before_recovery_v1(cursor)
    write_persisted_cursor_v1(cursor_path, cursor)
    reconcile_persisted_state_before_resume_v1(
        cursor,
        expected_session_id=expected_session_id,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    resume_after_reconciliation_v1(cursor)
    write_persisted_cursor_v1(cursor_path, cursor)
    return {
        "ok": True,
        "session_fenced_before_recovery": True,
        "reconciliation_before_resume": True,
        "processing_allowed": cursor.processing_allowed,
        "cursor": cursor.to_dict(),
        "recovery_has_alpha_authority": False,
        "invariants": dict(RECOVERY_INVARIANTS),
    }


def fence_o2_session_v1(launcher: CanonicalLocalLauncherV1, session_id: str) -> dict[str, Any]:
    """Reuse O2 recover to fence stale/failed sessions before resume."""
    result = launcher.recover(session_id)
    return {
        "ok": True,
        "session_fenced_before_recovery": True,
        "o2_recover": result,
        "action": result.get("action"),
    }


def assert_single_writer_enforced_v1(registry_root: Path, session_id: str) -> dict[str, Any]:
    first = LauncherSingleWriterV1(registry_root, session_id=session_id)
    first.acquire()
    conflict = False
    try:
        second = LauncherSingleWriterV1(registry_root, session_id=f"{session_id}-other")
        try:
            second.acquire()
        except ConflictingWriterError:
            conflict = True
        else:
            second.release()
            raise RecoveryErrorV1("SINGLE_WRITER_NOT_ENFORCED")
    finally:
        first.release()
    return {"ok": True, "single_writer_enforced": conflict}


def inject_stale_pid_identity_v1(record: SessionRecordV1) -> SessionRecordV1:
    """Replace live identity with a synthetic stale PID for offline safety proofs."""
    record.process_identity = ProcessIdentityV1(
        pid=1,
        pgid=1,
        process_start_identity="STALE_START_IDENTITY_O6",
        cmdline_fingerprint="stale-o6-cmdline",
    )
    return record


def graceful_shutdown_timeout_outcome_v1(
    *,
    stopped: bool,
    escalated: bool,
    graceful_timeout_seconds: float = DEFAULT_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return {
        "ok": True,
        "stopped": bool(stopped),
        "escalated": bool(escalated),
        "graceful_timeout_seconds": float(graceful_timeout_seconds),
        "graceful_shutdown_proven": bool(stopped),
        "timeout_path_classified": bool(escalated) or bool(stopped),
    }


@dataclass
class RecoveryHarnessPathsV1:
    repository_root: Path
    state_root: Path
    log_root: Path
    evidence_root: Path
    cursor_path: Path
    extra: dict[str, Any] = field(default_factory=dict)

    def to_launcher_paths(self) -> LauncherPathsV1:
        return LauncherPathsV1(
            repository_root=self.repository_root,
            state_root=self.state_root,
            log_root=self.log_root,
            evidence_root=self.evidence_root,
        )

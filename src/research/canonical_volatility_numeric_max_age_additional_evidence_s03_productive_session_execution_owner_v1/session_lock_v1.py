"""Exclusive S03 session lock with ownership-checked cleanup."""

from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    SCHEMA_SESSION_LOCK,
    S03_LOCK_FILENAME,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    S03ScopeBindingsV1,
    SessionLockRecordV1,
    sha256_hex_canonical,
)

MonotonicClock = Callable[[], float]


def default_owner_identity_v1() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


class S03SessionLockV1:
    """File lock under S03 evidence root; no silent stale takeover."""

    def __init__(
        self,
        *,
        session_dir: Path,
        bindings: S03ScopeBindingsV1,
        monotonic_clock: MonotonicClock,
        process_id: Optional[int] = None,
        owner_identity: Optional[str] = None,
        wall_clock_utc: Optional[Callable[[], str]] = None,
    ) -> None:
        self.session_dir = Path(session_dir)
        self.lock_path = self.session_dir / S03_LOCK_FILENAME
        self.bindings = bindings
        self._clock = monotonic_clock
        self.process_id = int(os.getpid() if process_id is None else process_id)
        self.owner_identity = owner_identity or default_owner_identity_v1()
        self._wall = wall_clock_utc or (
            lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        self._record: Optional[SessionLockRecordV1] = None
        self._held = False

    @property
    def held(self) -> bool:
        return self._held

    @property
    def record(self) -> Optional[SessionLockRecordV1]:
        return self._record

    def acquire(self) -> SessionLockRecordV1:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        if self.lock_path.exists():
            existing = self._read_lock()
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                f"session_lock_busy:owner={existing.get('owner_identity')}"
                f":pid={existing.get('process_id')}"
            )
        record = SessionLockRecordV1(
            campaign_id=self.bindings.campaign_id,
            session_id=self.bindings.session_id,
            preregistration_id=self.bindings.preregistration_id,
            preregistration_digest=self.bindings.preregistration_digest,
            authorization_id=self.bindings.authorization_id,
            authorization_digest=self.bindings.authorization_digest,
            repository_sha=self.bindings.repository_sha,
            process_id=self.process_id,
            owner_identity=self.owner_identity,
            created_at_utc=str(self._wall()),
            monotonic_start_reference=float(self._clock()),
            session_scope=self.bindings.session_scope,
            venue=self.bindings.venue,
            instrument=self.bindings.instrument,
        )
        payload = {
            "schema": SCHEMA_SESSION_LOCK,
            **record.to_dict(),
        }
        payload["lock_digest"] = sha256_hex_canonical(payload)
        tmp = self.lock_path.with_suffix(".lock.tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.lock_path)
        self._record = record
        self._held = True
        return record

    def assert_ownership(self) -> None:
        if not self._held or self._record is None:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("lock_not_held")
        on_disk = self._read_lock()
        if int(on_disk.get("process_id") or -1) != self.process_id:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("lock_ownership_mismatch_pid")
        if str(on_disk.get("owner_identity") or "") != self.owner_identity:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                "lock_ownership_mismatch_identity"
            )
        if str(on_disk.get("session_id") or "") != self.bindings.session_id:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("lock_ownership_mismatch_session")

    def release(self) -> bool:
        if not self._held:
            return False
        self.assert_ownership()
        self.lock_path.unlink(missing_ok=False)
        self._held = False
        return True

    def _read_lock(self) -> dict[str, Any]:
        try:
            return json.loads(self.lock_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                f"session_lock_unreadable:{exc}"
            ) from exc

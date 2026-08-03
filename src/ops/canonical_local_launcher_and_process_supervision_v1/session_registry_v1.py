"""Durable session registry for O2 (not live_session_registry)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    ACTIVE_BY_MODE_DIRNAME,
    ACTIVE_LIFECYCLE_STATES,
    REGISTRY_DIRNAME,
    SESSION_STATE_FILENAME,
    SESSIONS_DIRNAME,
    TRANSITIONS_FILENAME,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
    DuplicateSessionError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    LifecycleTransitionV1,
    SessionRecordV1,
)


def resolve_registry_root(state_root: Path) -> Path:
    return Path(state_root) / REGISTRY_DIRNAME


class SessionRegistryV1:
    def __init__(self, state_root: Path) -> None:
        self.state_root = Path(state_root)
        self.registry_root = resolve_registry_root(self.state_root)
        self.sessions_dir = self.registry_root / SESSIONS_DIRNAME
        self.active_by_mode_dir = self.registry_root / ACTIVE_BY_MODE_DIRNAME

    def ensure_layout(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.active_by_mode_dir.mkdir(parents=True, exist_ok=True)

    def session_dir(self, session_id: str) -> Path:
        return self.sessions_dir / session_id

    def session_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / SESSION_STATE_FILENAME

    def transitions_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / TRANSITIONS_FILENAME

    def active_mode_path(self, mode: str) -> Path:
        safe = mode.replace("/", "_")
        return self.active_by_mode_dir / f"{safe}.json"

    def load_session(self, session_id: str) -> Optional[SessionRecordV1]:
        path = self.session_path(session_id)
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return SessionRecordV1.from_dict(raw)

    def write_session(self, record: SessionRecordV1) -> Path:
        self.ensure_layout()
        directory = self.session_dir(record.session_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = self.session_path(record.session_id)
        tmp = path.with_suffix(".tmp")
        payload = json.dumps(record.to_dict(), sort_keys=True, indent=2) + "\n"
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(path)
        return path

    def append_transition(self, transition: LifecycleTransitionV1) -> None:
        self.ensure_layout()
        directory = self.session_dir(transition.session_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = self.transitions_path(transition.session_id)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(transition.to_dict(), sort_keys=True) + "\n")
            fh.flush()

    def get_active_session_id_for_mode(self, mode: str) -> Optional[str]:
        path = self.active_mode_path(mode)
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        session_id = str(raw.get("session_id") or "")
        return session_id or None

    def claim_mode(self, *, mode: str, session_id: str, now_unix: float) -> None:
        self.ensure_layout()
        existing_id = self.get_active_session_id_for_mode(mode)
        if existing_id and existing_id != session_id:
            existing = self.load_session(existing_id)
            if existing is not None and existing.lifecycle_state in ACTIVE_LIFECYCLE_STATES:
                raise DuplicateSessionError(
                    f"mode={mode}:existing_session={existing_id}:state={existing.lifecycle_state}",
                    payload={"mode": mode, "existing_session_id": existing_id},
                )
        path = self.active_mode_path(mode)
        tmp = path.with_suffix(".tmp")
        payload = {
            "mode": mode,
            "session_id": session_id,
            "claimed_at_unix": float(now_unix),
        }
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def release_mode(self, *, mode: str, session_id: str) -> None:
        path = self.active_mode_path(mode)
        if not path.is_file():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)
            return
        if str(raw.get("session_id") or "") == session_id:
            path.unlink(missing_ok=True)

    def transition(
        self,
        record: SessionRecordV1,
        *,
        new_state: str,
        reason_code: str,
        now_unix: Optional[float] = None,
        evidence_reference: str = "",
    ) -> SessionRecordV1:
        ts = float(now_unix if now_unix is not None else time.time())
        previous = record.lifecycle_state
        transition = LifecycleTransitionV1(
            timestamp_unix=ts,
            previous_state=previous,
            new_state=new_state,
            reason_code=reason_code,
            session_id=record.session_id,
            process_identity=(record.process_identity.to_dict() if record.process_identity else {}),
            evidence_reference=evidence_reference,
        )
        self.append_transition(transition)
        record.lifecycle_state = new_state
        record.updated_at_unix = ts
        record.last_reason_code = reason_code
        self.write_session(record)
        return record

    def list_session_ids(self) -> list[str]:
        self.ensure_layout()
        return sorted(p.name for p in self.sessions_dir.iterdir() if p.is_dir())

    def require_session(self, session_id: str) -> SessionRecordV1:
        record = self.load_session(session_id)
        if record is None:
            raise CanonicalLauncherError("SESSION_NOT_FOUND", session_id)
        return record

    def dump_summary(self) -> dict[str, Any]:
        return {
            "registry_root": str(self.registry_root),
            "session_ids": self.list_session_ids(),
        }

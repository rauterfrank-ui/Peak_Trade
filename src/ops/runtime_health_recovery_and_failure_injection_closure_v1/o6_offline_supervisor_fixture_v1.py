"""O6-owned offline supervisor fixture for failure-injection proofs.

Mirrors bounded O2 supervisor registry/recover semantics without importing O2 or
spawning dashboard HTTP workers. Evidence/test-only; not productive authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

REGISTRY_DIRNAME = "o6_offline_supervisor_v1"
SESSIONS_DIRNAME = "sessions"
ACTIVE_BY_MODE_DIRNAME = "active_by_mode"
SESSION_STATE_FILENAME = "session_state_v1.json"
TRANSITIONS_FILENAME = "transitions.jsonl"
WRITER_LOCK_FILENAME = "supervisor_writer.lock"
SINGLE_WRITER_IDENTITY = "peak_trade.o6_offline_supervisor_single_writer_v1"

ACTIVE_LIFECYCLE_STATES = frozenset(
    {"PREFLIGHT", "ENV_VALIDATED", "AUTH_VALIDATED", "STARTING", "RUNNING", "DEGRADED", "STOPPING"}
)

SCHEMA_VERSION = "o6_offline_supervisor_fixture_v1"
CAPABILITY_ID = "CAPABILITY_O6_OFFLINE_SUPERVISOR_FIXTURE_V1"
SUPERVISION_BACKEND = "o6_offline_fixture"
SUPERVISOR_IDENTITY = "peak_trade.o6_offline_supervisor_fixture_v1"


class O6OfflineSupervisorError(RuntimeError):
    def __init__(
        self, code: str, detail: str = "", *, payload: Optional[dict[str, Any]] = None
    ) -> None:
        self.code = code
        self.detail = detail
        self.payload = payload or {}
        super().__init__(f"{code}:{detail}" if detail else code)


class PreflightFailedError(O6OfflineSupervisorError):
    pass


class DuplicateSessionError(O6OfflineSupervisorError):
    pass


class ConflictingWriterError(O6OfflineSupervisorError):
    pass


class ProcessIdentityMismatchError(O6OfflineSupervisorError):
    pass


@dataclass
class O6OfflineSupervisorPathsV1:
    repository_root: Path
    state_root: Path
    log_root: Path
    evidence_root: Path


@dataclass
class LifecycleTransitionV1:
    timestamp_unix: float
    previous_state: str
    new_state: str
    reason_code: str
    session_id: str
    process_identity: dict[str, Any] = field(default_factory=dict)
    evidence_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessIdentityV1:
    pid: int
    pgid: int
    process_start_identity: str
    cmdline_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ProcessIdentityV1:
        return cls(
            pid=int(raw["pid"]),
            pgid=int(raw["pgid"]),
            process_start_identity=str(raw["process_start_identity"]),
            cmdline_fingerprint=str(raw.get("cmdline_fingerprint") or ""),
        )


@dataclass
class SessionRecordV1:
    schema_version: str
    capability_id: str
    session_id: str
    mode: str
    lifecycle_state: str
    repository_sha: str
    config_digest: str
    config_path: str
    supervisor_identity: str
    supervision_backend: str
    supervisor_instance_id: str
    process_identity: Optional[ProcessIdentityV1]
    log_root: str
    state_root: str
    evidence_root: str
    heartbeat_path: str
    created_at_unix: float
    updated_at_unix: float
    o1_environment_policy_id: str = ""
    o1_parent_environment_digest: str = ""
    o1_effective_environment_digest: str = ""
    last_reason_code: str = ""
    recovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.process_identity is None:
            payload["process_identity"] = None
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SessionRecordV1:
        identity_raw = raw.get("process_identity")
        identity = (
            ProcessIdentityV1.from_dict(identity_raw) if isinstance(identity_raw, dict) else None
        )
        return cls(
            schema_version=str(raw["schema_version"]),
            capability_id=str(raw["capability_id"]),
            session_id=str(raw["session_id"]),
            mode=str(raw["mode"]),
            lifecycle_state=str(raw["lifecycle_state"]),
            repository_sha=str(raw["repository_sha"]),
            config_digest=str(raw["config_digest"]),
            config_path=str(raw.get("config_path") or ""),
            supervisor_identity=str(raw["supervisor_identity"]),
            supervision_backend=str(raw["supervision_backend"]),
            supervisor_instance_id=str(raw["supervisor_instance_id"]),
            process_identity=identity,
            log_root=str(raw["log_root"]),
            state_root=str(raw["state_root"]),
            evidence_root=str(raw.get("evidence_root") or ""),
            heartbeat_path=str(raw["heartbeat_path"]),
            created_at_unix=float(raw["created_at_unix"]),
            updated_at_unix=float(raw["updated_at_unix"]),
            o1_environment_policy_id=str(raw.get("o1_environment_policy_id") or ""),
            o1_parent_environment_digest=str(raw.get("o1_parent_environment_digest") or ""),
            o1_effective_environment_digest=str(raw.get("o1_effective_environment_digest") or ""),
            last_reason_code=str(raw.get("last_reason_code") or ""),
            recovered=bool(raw.get("recovered") or False),
        )


def _run_ps(pid: int, fmt: str) -> str:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", fmt],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    lines = [ln.strip() for ln in completed.stdout.splitlines() if ln.strip()]
    if len(lines) < 2:
        return lines[0] if lines else ""
    return " ".join(lines[1:]).strip()


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    state = _run_ps(pid, "state=") or _run_ps(pid, "stat=")
    if not state:
        return False
    if state[0].upper() == "Z":
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return state[0].upper() != "Z"
    except OSError:
        return False
    return True


def read_process_start_identity(pid: int) -> str:
    for fmt in ("lstart=", "lstart", "etime=", "etime"):
        value = _run_ps(pid, fmt)
        if value:
            return value
    return ""


def read_cmdline_fingerprint(pid: int) -> str:
    raw = _run_ps(pid, "args=") or _run_ps(pid, "command=")
    if not raw:
        return ""
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()


def read_pgid(pid: int) -> Optional[int]:
    raw = _run_ps(pid, "pgid=")
    if not raw:
        try:
            return os.getpgid(pid)
        except OSError:
            return None
    try:
        return int(raw.split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def verify_process_identity(expected: ProcessIdentityV1) -> ProcessIdentityV1:
    if not process_alive(expected.pid):
        raise ProcessIdentityMismatchError(
            f"pid_dead:{expected.pid}",
            payload=expected.to_dict(),
        )
    pgid = read_pgid(expected.pid)
    if pgid is None:
        raise ProcessIdentityMismatchError(f"pgid_unreadable:{expected.pid}")
    start_identity = read_process_start_identity(expected.pid)
    if not start_identity:
        raise ProcessIdentityMismatchError(f"start_identity_unreadable:{expected.pid}")
    observed = ProcessIdentityV1(
        pid=int(expected.pid),
        pgid=int(pgid),
        process_start_identity=start_identity,
        cmdline_fingerprint=read_cmdline_fingerprint(expected.pid),
    )
    if observed.pgid != expected.pgid:
        raise ProcessIdentityMismatchError(
            f"pgid_mismatch:expected={expected.pgid}:observed={observed.pgid}",
        )
    if observed.process_start_identity != expected.process_start_identity:
        raise ProcessIdentityMismatchError("process_start_identity_mismatch")
    if (
        expected.cmdline_fingerprint
        and observed.cmdline_fingerprint
        and expected.cmdline_fingerprint != observed.cmdline_fingerprint
    ):
        raise ProcessIdentityMismatchError("cmdline_fingerprint_mismatch")
    return observed


@dataclass
class O6OfflineSingleWriterV1:
    registry_root: Path
    writer_identity: str = SINGLE_WRITER_IDENTITY
    session_id: str = "default"
    _held: bool = False

    @property
    def lock_path(self) -> Path:
        return Path(self.registry_root) / WRITER_LOCK_FILENAME

    def acquire(self, *, now_unix: Optional[float] = None) -> None:
        root = Path(self.registry_root)
        root.mkdir(parents=True, exist_ok=True)
        lock = self.lock_path
        payload = {
            "writer_identity": self.writer_identity,
            "session_id": self.session_id,
            "pid": os.getpid(),
            "acquired_at_unix": float(now_unix if now_unix is not None else time.time()),
        }
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(lock), flags, 0o644)
        except FileExistsError as exc:
            existing: dict[str, Any] = {}
            try:
                existing = json.loads(lock.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                existing = {"raw": "UNREADABLE"}
            raise ConflictingWriterError(f"existing={existing}", payload=existing) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._held = True

    def release(self) -> None:
        if not self._held:
            return
        lock = self.lock_path
        if lock.is_file():
            try:
                existing = json.loads(lock.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                existing = {}
            if (
                existing.get("writer_identity") == self.writer_identity
                and existing.get("session_id") == self.session_id
            ):
                lock.unlink(missing_ok=True)
        self._held = False

    def __enter__(self) -> O6OfflineSingleWriterV1:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.release()


class O6OfflineSessionRegistryV1:
    def __init__(self, state_root: Path) -> None:
        self.state_root = Path(state_root)
        self.registry_root = self.state_root / REGISTRY_DIRNAME
        self.sessions_dir = self.registry_root / SESSIONS_DIRNAME
        self.active_by_mode_dir = self.registry_root / ACTIVE_BY_MODE_DIRNAME

    def ensure_layout(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.active_by_mode_dir.mkdir(parents=True, exist_ok=True)

    def session_dir(self, session_id: str) -> Path:
        return self.sessions_dir / session_id

    def session_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / SESSION_STATE_FILENAME

    def load_session(self, session_id: str) -> Optional[SessionRecordV1]:
        path = self.session_path(session_id)
        if not path.is_file():
            return None
        return SessionRecordV1.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def write_session(self, record: SessionRecordV1) -> Path:
        self.ensure_layout()
        directory = self.session_dir(record.session_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = self.session_path(record.session_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(record.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        tmp.replace(path)
        return path

    def append_transition(self, transition: LifecycleTransitionV1) -> None:
        self.ensure_layout()
        directory = self.session_dir(transition.session_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / TRANSITIONS_FILENAME
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(transition.to_dict(), sort_keys=True) + "\n")
            fh.flush()

    def get_active_session_id_for_mode(self, mode: str) -> Optional[str]:
        path = self.active_by_mode_dir / f"{mode.replace('/', '_')}.json"
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
        path = self.active_by_mode_dir / f"{mode.replace('/', '_')}.json"
        tmp = path.with_suffix(".tmp")
        payload = {"mode": mode, "session_id": session_id, "claimed_at_unix": float(now_unix)}
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def release_mode(self, *, mode: str, session_id: str) -> None:
        path = self.active_by_mode_dir / f"{mode.replace('/', '_')}.json"
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
        )
        self.append_transition(transition)
        record.lifecycle_state = new_state
        record.updated_at_unix = ts
        record.last_reason_code = reason_code
        self.write_session(record)
        return record

    def require_session(self, session_id: str) -> SessionRecordV1:
        record = self.load_session(session_id)
        if record is None:
            raise O6OfflineSupervisorError("SESSION_NOT_FOUND", session_id)
        return record


@dataclass
class O6OfflineSupervisorFixtureV1:
    paths: O6OfflineSupervisorPathsV1
    registry: O6OfflineSessionRegistryV1 = field(init=False)

    def __post_init__(self) -> None:
        self.registry = O6OfflineSessionRegistryV1(self.paths.state_root)

    def preflight(
        self,
        *,
        mode: str,
        session_id: str,
        config_path: Path,
        repository_sha: str,
    ) -> dict[str, Any]:
        if not Path(config_path).is_file():
            raise PreflightFailedError("CONFIG_MISSING", str(config_path))
        return {
            "ok": True,
            "mode": mode,
            "session_id": session_id,
            "repository_sha": repository_sha,
            "config_path": str(config_path),
        }

    def start(
        self,
        *,
        mode: str = "dashboard-only",
        session_id: str,
        config_path: Path,
        repository_sha: str,
        config_digest: str = "",
    ) -> dict[str, Any]:
        self.preflight(
            mode=mode,
            session_id=session_id,
            config_path=config_path,
            repository_sha=repository_sha,
        )
        existing_id = self.registry.get_active_session_id_for_mode(mode)
        if existing_id:
            existing = self.registry.load_session(existing_id)
            if existing is not None and existing.lifecycle_state in ACTIVE_LIFECYCLE_STATES:
                raise DuplicateSessionError(
                    f"active_session={existing_id}",
                    payload={"existing_session_id": existing_id},
                )
        raise O6OfflineSupervisorError(
            "SPAWN_NOT_IMPLEMENTED_OFFLINE_FIXTURE",
            "O6 offline fixture does not spawn HTTP workers",
        )

    def _mark_stale_and_release(self, record: SessionRecordV1, *, reason: str) -> SessionRecordV1:
        record.recovered = True
        self.registry.transition(record, new_state="STOPPED", reason_code=reason)
        self.registry.release_mode(mode=record.mode, session_id=record.session_id)
        record.process_identity = None
        self.registry.write_session(record)
        return record

    def recover(self, session_id: str) -> dict[str, Any]:
        with O6OfflineSingleWriterV1(self.registry.registry_root, session_id=session_id):
            record = self.registry.require_session(session_id)
            self.registry.transition(
                record, new_state="RECOVERING", reason_code="RECOVER_REQUESTED"
            )
            if record.process_identity is None:
                self.registry.transition(
                    record, new_state="STOPPED", reason_code="RECOVER_NO_PROCESS"
                )
                self.registry.release_mode(mode=record.mode, session_id=record.session_id)
                record.recovered = True
                self.registry.write_session(record)
                return {
                    "ok": True,
                    "action": "CLEARED_NO_PROCESS",
                    "session": record.to_dict(),
                }
            try:
                verify_process_identity(record.process_identity)
                self.registry.transition(
                    record, new_state="RUNNING", reason_code="RECOVER_IDENTITY_OK"
                )
                return {
                    "ok": True,
                    "action": "NO_OP_PROCESS_HEALTHY",
                    "session": record.to_dict(),
                }
            except ProcessIdentityMismatchError:
                record = self._mark_stale_and_release(record, reason="RECOVER_STALE_PID")
                return {
                    "ok": True,
                    "action": "CLEARED_STALE_PID",
                    "session": record.to_dict(),
                }


def build_offline_supervisor_fixture_v1(tmp: Path) -> tuple[O6OfflineSupervisorFixtureV1, Path]:
    config = tmp / "config" / "o6.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('{"schema":"o6_offline_fixture","mode":"dashboard-only"}\n', encoding="utf-8")
    paths = O6OfflineSupervisorPathsV1(
        repository_root=tmp / "repo",
        state_root=tmp / "state",
        log_root=tmp / "logs",
        evidence_root=tmp / "evidence",
    )
    paths.repository_root.mkdir(parents=True, exist_ok=True)
    return O6OfflineSupervisorFixtureV1(paths=paths), config

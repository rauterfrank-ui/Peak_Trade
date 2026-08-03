"""O2 lifecycle control plane: preflight/start/status/health/stop/restart/recover."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    AUTHORIZED_MODES,
    CAPABILITY_ID,
    DEFAULT_ESCALATION_KILL_TIMEOUT_SECONDS,
    DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS,
    DEFAULT_HEALTH_STALE_SECONDS,
    HEARTBEAT_FILENAME,
    MODE_DASHBOARD_ONLY,
    SAFETY_INVARIANTS,
    SCAFFOLD_MARKER_FILENAME,
    SCHEMA_VERSION,
    SETSID_CLI_REQUIRED,
    SUPERVISION_BACKEND,
    SUPERVISOR_IDENTITY,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
    DuplicateSessionError,
    ModeUnauthorizedError,
    PreflightFailedError,
    ProcessIdentityMismatchError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    ProcessIdentityV1,
    SessionRecordV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_group_v1 import (
    assert_no_setsid_cli_dependency,
    python_executable,
    spawn_detached_process_group,
    terminate_process_group,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    process_alive,
    verify_process_identity,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.session_registry_v1 import (
    SessionRegistryV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import (
    LauncherSingleWriterV1,
)
from src.ops.canonical_runtime_environment_contract_v1 import (
    ENVIRONMENT_POLICY_ID,
    run_canonical_environment_preflight_v1,
)


@dataclass(frozen=True)
class LauncherPathsV1:
    repository_root: Path
    state_root: Path
    log_root: Path
    evidence_root: Path


def compute_config_digest_v1(config_path: Path) -> str:
    data = Path(config_path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def resolve_repository_sha(repository_root: Path, explicit: Optional[str] = None) -> str:
    if explicit:
        return str(explicit).strip()
    head = repository_root / ".git" / "HEAD"
    if head.is_file():
        # Worktree .git may be a file pointing elsewhere; prefer git via env-free read.
        content = head.read_text(encoding="utf-8").strip()
        if content.startswith("ref:"):
            ref = content.split(" ", 1)[1].strip()
            ref_path = repository_root / ".git" / ref
            if ref_path.is_file():
                return ref_path.read_text(encoding="utf-8").strip()
        elif len(content) >= 40:
            return content
    # gitdir pointer (worktree)
    git_file = repository_root / ".git"
    if git_file.is_file():
        line = git_file.read_text(encoding="utf-8").strip()
        if line.startswith("gitdir:"):
            gitdir = Path(line.split(":", 1)[1].strip())
            head2 = gitdir / "HEAD"
            if head2.is_file():
                content = head2.read_text(encoding="utf-8").strip()
                if content.startswith("ref:"):
                    ref = content.split(" ", 1)[1].strip()
                    ref_path = gitdir / ref
                    if ref_path.is_file():
                        return ref_path.read_text(encoding="utf-8").strip()
                elif len(content) >= 40:
                    return content
    raise CanonicalLauncherError("REPOSITORY_SHA_UNRESOLVED", str(repository_root))


def _minimal_allowlist_parent(
    *,
    repository_sha: str,
    config_path: str,
    config_digest: str,
    session_id: str,
    log_root: str,
    state_root: str,
    evidence_root: str,
    mode: str,
) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(Path(__file__).resolve().parents[3]),
        "PYTHONUNBUFFERED": "1",
        "MPLCONFIGDIR": str(Path(state_root) / "mpl"),
        "HOME": os.environ.get("HOME", str(Path(state_root) / "home")),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "PEAK_TRADE_RUNTIME_MODE": mode,
        "PEAK_TRADE_REPOSITORY_SHA": repository_sha,
        "PEAK_TRADE_CONFIG_PATH": config_path,
        "PEAK_TRADE_CONFIG_DIGEST": config_digest,
        "PEAK_TRADE_SESSION_ID": session_id,
        "PEAK_TRADE_AUTHORIZATION_ARTIFACT_PATH": str(
            Path(state_root) / "unused_authorization.json"
        ),
        "PEAK_TRADE_CONFIRM_TOKEN_FILE": str(Path(state_root) / "unused_confirm_token"),
        "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK": "0",
        "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT": str(Path(state_root) / "archive"),
        "PEAK_TRADE_LOG_ROOT": log_root,
        "PEAK_TRADE_STATE_ROOT": state_root,
        "PEAK_TRADE_EVIDENCE_ROOT": evidence_root,
        "PEAK_TRADE_ENVIRONMENT_POLICY_ID": ENVIRONMENT_POLICY_ID,
    }


class CanonicalLocalLauncherV1:
    """Repository-owned supervision backend for the O2 MVP (dashboard-only)."""

    def __init__(self, paths: LauncherPathsV1) -> None:
        self.paths = paths
        self.registry = SessionRegistryV1(paths.state_root)
        assert_no_setsid_cli_dependency()

    def preflight(
        self,
        *,
        mode: str,
        session_id: str,
        config_path: Path,
        repository_sha: Optional[str] = None,
        config_digest: Optional[str] = None,
        parent_environ: Optional[Mapping[str, str]] = None,
    ) -> dict[str, Any]:
        if mode not in AUTHORIZED_MODES:
            raise ModeUnauthorizedError(mode)
        if SETSID_CLI_REQUIRED:
            raise CanonicalLauncherError("PLATFORM_PORTABILITY_FAILURE", "SETSID_CLI_REQUIRED")
        if shutil.which("setsid") is not None:
            # Presence is fine; dependency is forbidden.
            pass
        sha = resolve_repository_sha(self.paths.repository_root, repository_sha)
        cfg = Path(config_path)
        if not cfg.is_file():
            raise CanonicalLauncherError("CONFIG_PATH_MISSING", str(cfg))
        digest = config_digest or compute_config_digest_v1(cfg)
        parent = (
            dict(parent_environ)
            if parent_environ is not None
            else _minimal_allowlist_parent(
                repository_sha=sha,
                config_path=str(cfg.resolve()),
                config_digest=digest,
                session_id=session_id,
                log_root=str(self.paths.log_root),
                state_root=str(self.paths.state_root),
                evidence_root=str(self.paths.evidence_root),
                mode=mode,
            )
        )
        o1 = run_canonical_environment_preflight_v1(
            parent,
            stage="O2_LAUNCHER_PREFLIGHT",
            include_macos_portability=True,
            build_effective=True,
        )
        if not o1.ok:
            raise PreflightFailedError(
                ",".join(o1.blockers),
                payload=o1.to_dict(),
            )
        return {
            "ok": True,
            "capability_id": CAPABILITY_ID,
            "mode": mode,
            "session_id": session_id,
            "repository_sha": sha,
            "config_path": str(cfg.resolve()),
            "config_digest": digest,
            "supervision_backend": SUPERVISION_BACKEND,
            "setsid_cli_required": False,
            "macos_portability_proven": True,
            "o1_preflight": o1.to_dict(),
            "safety_invariants": dict(SAFETY_INVARIANTS),
            "lifecycle_state": "ENV_VALIDATED",
        }

    def start(
        self,
        *,
        mode: str = MODE_DASHBOARD_ONLY,
        session_id: Optional[str] = None,
        config_path: Path,
        repository_sha: Optional[str] = None,
        config_digest: Optional[str] = None,
        parent_environ: Optional[Mapping[str, str]] = None,
        force_ignore_sigterm_for_test: bool = False,
        graceful_timeout_seconds: float = DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        del graceful_timeout_seconds  # reserved for stop/restart symmetry
        sid = session_id or f"o2-{uuid.uuid4().hex[:12]}"
        preflight = self.preflight(
            mode=mode,
            session_id=sid,
            config_path=config_path,
            repository_sha=repository_sha,
            config_digest=config_digest,
            parent_environ=parent_environ,
        )
        now = time.time()
        with LauncherSingleWriterV1(self.registry.registry_root, session_id=sid):
            self.registry.ensure_layout()
            # Duplicate session / mode guard
            existing_id = self.registry.get_active_session_id_for_mode(mode)
            if existing_id:
                existing = self.registry.load_session(existing_id)
                if existing is not None and existing.process_identity is not None:
                    try:
                        verify_process_identity(existing.process_identity)
                        raise DuplicateSessionError(
                            f"live_session={existing_id}",
                            payload={"existing_session_id": existing_id},
                        )
                    except ProcessIdentityMismatchError:
                        # Stale active pointer — recover then continue.
                        self._mark_stale_and_release(existing, reason="STALE_BEFORE_START")
                elif existing is not None and existing.lifecycle_state in {
                    "STARTING",
                    "RUNNING",
                    "DEGRADED",
                }:
                    raise DuplicateSessionError(
                        f"active_without_identity={existing_id}",
                        payload={"existing_session_id": existing_id},
                    )

            existing_same = self.registry.load_session(sid)
            if existing_same is not None:
                if existing_same.lifecycle_state in {"STOPPED", "FAILED", "OFF"}:
                    # Reclaim after stop/recover/restart — identity binding must still match.
                    if (
                        existing_same.repository_sha != str(preflight["repository_sha"])
                        or existing_same.config_digest != str(preflight["config_digest"])
                        or existing_same.mode != mode
                    ):
                        raise CanonicalLauncherError(
                            "REPOSITORY_OR_CONFIG_IDENTITY_MISMATCH",
                            (
                                f"existing_sha={existing_same.repository_sha}:"
                                f"new_sha={preflight['repository_sha']}:"
                                f"existing_digest={existing_same.config_digest}:"
                                f"new_digest={preflight['config_digest']}"
                            ),
                        )
                else:
                    raise DuplicateSessionError(f"session_id_exists={sid}")

            self.registry.claim_mode(mode=mode, session_id=sid, now_unix=now)
            session_dir = self.registry.session_dir(sid)
            session_dir.mkdir(parents=True, exist_ok=True)
            log_dir = Path(self.paths.log_root) / sid
            log_dir.mkdir(parents=True, exist_ok=True)
            heartbeat_path = session_dir / HEARTBEAT_FILENAME
            marker_path = session_dir / SCAFFOLD_MARKER_FILENAME

            created_at = float(existing_same.created_at_unix) if existing_same is not None else now
            record = SessionRecordV1(
                schema_version=SCHEMA_VERSION,
                capability_id=CAPABILITY_ID,
                session_id=sid,
                mode=mode,
                lifecycle_state="OFF",
                repository_sha=str(preflight["repository_sha"]),
                config_digest=str(preflight["config_digest"]),
                config_path=str(preflight["config_path"]),
                supervisor_identity=SUPERVISOR_IDENTITY,
                supervision_backend=SUPERVISION_BACKEND,
                supervisor_instance_id=f"{SUPERVISOR_IDENTITY}:{os.getpid()}:{uuid.uuid4().hex[:8]}",
                process_identity=None,
                log_root=str(log_dir),
                state_root=str(self.paths.state_root),
                evidence_root=str(self.paths.evidence_root),
                heartbeat_path=str(heartbeat_path),
                created_at_unix=created_at,
                updated_at_unix=now,
                o1_environment_policy_id=ENVIRONMENT_POLICY_ID,
                o1_parent_environment_digest=str(
                    preflight["o1_preflight"]["parent_environment_digest"]
                ),
                o1_effective_environment_digest=str(
                    preflight["o1_preflight"]["effective_environment_digest"]
                ),
                safety_invariants=dict(SAFETY_INVARIANTS),
                last_reason_code="CREATED",
                recovered=bool(existing_same.recovered) if existing_same else False,
            )
            self.registry.write_session(record)
            self.registry.transition(record, new_state="PREFLIGHT", reason_code="PREFLIGHT_OK")
            self.registry.transition(
                record, new_state="ENV_VALIDATED", reason_code="O1_ENV_VALIDATED"
            )
            # O2 MVP does not consume authorization; skip AUTH_VALIDATED as pass-through note.
            self.registry.transition(
                record, new_state="STARTING", reason_code="SPAWN_DASHBOARD_SCAFFOLD"
            )

            # Rebuild effective env via O1 for the child (values not in preflight dict).
            o1_parent = (
                dict(parent_environ)
                if parent_environ is not None
                else _minimal_allowlist_parent(
                    repository_sha=str(preflight["repository_sha"]),
                    config_path=str(preflight["config_path"]),
                    config_digest=str(preflight["config_digest"]),
                    session_id=sid,
                    log_root=str(self.paths.log_root),
                    state_root=str(self.paths.state_root),
                    evidence_root=str(self.paths.evidence_root),
                    mode=mode,
                )
            )
            o1_full = run_canonical_environment_preflight_v1(
                o1_parent,
                stage="O2_CHILD_ENV_BUILD",
                include_macos_portability=True,
                build_effective=True,
            )
            if not o1_full.ok:
                self.registry.transition(record, new_state="FAILED", reason_code="CHILD_ENV_FAILED")
                self.registry.release_mode(mode=mode, session_id=sid)
                raise PreflightFailedError(",".join(o1_full.blockers), payload=o1_full.to_dict())

            from src.ops.canonical_runtime_environment_contract_v1 import (
                build_or_raise_effective_runtime_environment_v1,
            )

            effective_environ = build_or_raise_effective_runtime_environment_v1(o1_parent)
            argv = [
                python_executable(),
                "-m",
                "src.ops.canonical_local_launcher_and_process_supervision_v1.dashboard_scaffold_worker_v1",
                "--session-id",
                sid,
                "--heartbeat-path",
                str(heartbeat_path),
                "--marker-path",
                str(marker_path),
            ]
            if force_ignore_sigterm_for_test:
                argv.append("--ignore-sigterm")

            try:
                identity = spawn_detached_process_group(
                    argv,
                    env=effective_environ,
                    cwd=self.paths.repository_root,
                    stdout_path=log_dir / "stdout.log",
                    stderr_path=log_dir / "stderr.log",
                )
            except Exception as exc:
                self.registry.transition(
                    record, new_state="FAILED", reason_code=f"SPAWN_FAILED:{exc}"
                )
                self.registry.release_mode(mode=mode, session_id=sid)
                raise

            record.process_identity = identity
            self.registry.write_session(record)
            # Wait briefly for heartbeat/marker
            deadline = time.time() + 3.0
            while time.time() < deadline:
                if heartbeat_path.is_file() and marker_path.is_file():
                    break
                time.sleep(0.05)
            self.registry.transition(record, new_state="RUNNING", reason_code="CHILD_RUNNING")
            return {
                "ok": True,
                "session": record.to_dict(),
                "preflight": preflight,
            }

    def _mark_stale_and_release(self, record: SessionRecordV1, *, reason: str) -> SessionRecordV1:
        record.recovered = True
        self.registry.transition(record, new_state="STOPPED", reason_code=reason)
        self.registry.release_mode(mode=record.mode, session_id=record.session_id)
        record.process_identity = None
        self.registry.write_session(record)
        return record

    def status(self, session_id: str) -> dict[str, Any]:
        record = self.registry.require_session(session_id)
        alive = False
        identity_ok = False
        identity_error = ""
        if record.process_identity is not None:
            try:
                verify_process_identity(record.process_identity)
                alive = True
                identity_ok = True
            except ProcessIdentityMismatchError as exc:
                identity_error = str(exc)
                alive = process_alive(record.process_identity.pid)
        return {
            "ok": True,
            "session_id": session_id,
            "lifecycle_state": record.lifecycle_state,
            "mode": record.mode,
            "repository_sha": record.repository_sha,
            "config_digest": record.config_digest,
            "process_alive": alive,
            "identity_ok": identity_ok,
            "identity_error": identity_error,
            "process_identity": (
                record.process_identity.to_dict() if record.process_identity else None
            ),
            "supervision_backend": record.supervision_backend,
            "safety_invariants": dict(record.safety_invariants),
        }

    def health(
        self, session_id: str, *, stale_seconds: float = DEFAULT_HEALTH_STALE_SECONDS
    ) -> dict[str, Any]:
        status = self.status(session_id)
        record = self.registry.require_session(session_id)
        heartbeat: dict[str, Any] = {}
        heartbeat_path = Path(record.heartbeat_path)
        if heartbeat_path.is_file():
            try:
                heartbeat = json.loads(heartbeat_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                heartbeat = {"corrupt": True}
        ts = float(heartbeat.get("ts_unix") or 0.0)
        fresh = bool(ts and (time.time() - ts) <= float(stale_seconds))
        healthy = bool(
            status["process_alive"]
            and status["identity_ok"]
            and record.lifecycle_state == "RUNNING"
            and fresh
            and heartbeat.get("healthy") is True
        )
        return {
            "ok": True,
            "healthy": healthy,
            "fresh_heartbeat": fresh,
            "heartbeat": heartbeat,
            "status": status,
        }

    def stop(
        self,
        session_id: str,
        *,
        graceful_timeout_seconds: float = DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS,
        kill_timeout_seconds: float = DEFAULT_ESCALATION_KILL_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        with LauncherSingleWriterV1(self.registry.registry_root, session_id=session_id):
            record = self.registry.require_session(session_id)
            if record.process_identity is None:
                self.registry.transition(record, new_state="STOPPED", reason_code="ALREADY_STOPPED")
                self.registry.release_mode(mode=record.mode, session_id=session_id)
                return {
                    "ok": True,
                    "stopped": True,
                    "escalated": False,
                    "session": record.to_dict(),
                }
            try:
                verify_process_identity(record.process_identity)
            except ProcessIdentityMismatchError:
                record = self._mark_stale_and_release(record, reason="STALE_ON_STOP")
                return {
                    "ok": True,
                    "stopped": True,
                    "escalated": False,
                    "stale_recovered": True,
                    "session": record.to_dict(),
                }
            self.registry.transition(record, new_state="STOPPING", reason_code="STOP_REQUESTED")
            result = terminate_process_group(
                record.process_identity,
                graceful_timeout_seconds=graceful_timeout_seconds,
                kill_timeout_seconds=kill_timeout_seconds,
            )
            record.stop_escalated = bool(result.get("escalated"))
            record.process_identity = None
            self.registry.transition(
                record,
                new_state="STOPPED",
                reason_code="STOP_ESCALATED" if record.stop_escalated else "STOP_GRACEFUL",
            )
            self.registry.release_mode(mode=record.mode, session_id=session_id)
            return {
                "ok": True,
                "stopped": True,
                "escalated": record.stop_escalated,
                "termination": result,
                "session": record.to_dict(),
            }

    def restart(
        self,
        session_id: str,
        *,
        parent_environ: Optional[Mapping[str, str]] = None,
        graceful_timeout_seconds: float = DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS,
        kill_timeout_seconds: float = DEFAULT_ESCALATION_KILL_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        record = self.registry.require_session(session_id)
        stop_result = self.stop(
            session_id,
            graceful_timeout_seconds=graceful_timeout_seconds,
            kill_timeout_seconds=kill_timeout_seconds,
        )
        start_result = self.start(
            mode=record.mode,
            session_id=session_id,
            config_path=Path(record.config_path),
            repository_sha=record.repository_sha,
            config_digest=record.config_digest,
            parent_environ=parent_environ,
        )
        return {"ok": True, "stop": stop_result, "start": start_result}

    def recover(self, session_id: str) -> dict[str, Any]:
        """Minimal recover: fence stale PID/registry; do not auto-restart."""
        with LauncherSingleWriterV1(self.registry.registry_root, session_id=session_id):
            record = self.registry.require_session(session_id)
            self.registry.transition(
                record, new_state="RECOVERING", reason_code="RECOVER_REQUESTED"
            )
            if record.process_identity is None:
                self.registry.transition(
                    record, new_state="STOPPED", reason_code="RECOVER_NO_PROCESS"
                )
                self.registry.release_mode(mode=record.mode, session_id=session_id)
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

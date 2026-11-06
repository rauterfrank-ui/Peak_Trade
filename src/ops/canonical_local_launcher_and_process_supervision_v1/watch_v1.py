"""Bounded O2 process checks and opt-in dashboard-only technical restart.

Uses the existing launcher for every process effect. No trading-host admission,
authorization renewal, kill-switch reset, notification service or new daemon.
"""

import json
from hashlib import sha256
import math
from pathlib import Path
import time
from typing import Callable

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    DEFAULT_BOUNDED_RETRY_LIMIT,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.evidence_v1 import write_json
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.recovery_v1 import (
    bounded_retry_policy_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_notice_v1 import (
    record_runtime_notice_v1,
)

from .constants_v1 import DEFAULT_HEALTH_STALE_SECONDS, MODE_DASHBOARD_ONLY
from .errors_v1 import CanonicalLauncherError, ModeUnauthorizedError
from .lifecycle_v1 import CanonicalLocalLauncherV1, compute_config_digest_v1, resolve_repository_sha
from .single_writer_v1 import LauncherSingleWriterV1

WATCH_STATE_FILENAME = "process_watch_state_v1.json"


def _state_digest_v1(state: dict) -> str:
    material = {key: value for key, value in state.items() if key != "integrity_digest"}
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _save_watch_state_v1(path: Path, state: dict) -> None:
    state["integrity_digest"] = _state_digest_v1(state)
    write_json(path, state)


def watch_registered_session_v1(
    launcher: CanonicalLocalLauncherV1,
    *,
    session_id: str,
    duration_seconds: float,
    interval_seconds: float,
    restart_on_failure: bool = False,
    stale_seconds: float = DEFAULT_HEALTH_STALE_SECONDS,
    time_fn: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict:
    """Monitor an already registered session for an explicit finite time budget.

    Restart attempts are durable and cumulative for this session/binding, not
    reset when this command/process is restarted. Interrupted uncertain actions
    require owner reconciliation unless current health proves a ready worker.
    """
    if (
        not all(
            math.isfinite(v) and v > 0 for v in (duration_seconds, interval_seconds, stale_seconds)
        )
        or not 0.001 <= interval_seconds <= 60
        or not math.isfinite(duration_seconds / interval_seconds)
        or type(restart_on_failure) is not bool
    ):
        raise CanonicalLauncherError("INVALID_PROCESS_WATCH_BOUNDS")
    initial = launcher.registry.require_session(session_id)
    if initial.mode != MODE_DASHBOARD_ONLY:
        raise ModeUnauthorizedError(initial.mode)
    binding = {
        "session_id": session_id,
        "repository_sha": initial.repository_sha,
        "config_digest": initial.config_digest,
        "mode": initial.mode,
    }
    root = launcher.registry.session_dir(session_id)
    notice_root = root / "process_watch_evidence_v1"
    state_path = root / WATCH_STATE_FILENAME
    state = {"binding": binding, "restart_attempts": 0, "in_progress": False}

    def notice(reason, action, required, notification_kind=None, **extra):
        return record_runtime_notice_v1(
            evidence_root=notice_root,
            component="CANONICAL_O2_PROCESS_WATCH",
            run_id=session_id,
            reason_code=reason,
            action=action,
            owner_action_required=required,
            notification_kind=notification_kind,
            extra={"restart_attempts": state["restart_attempts"], **extra},
        )

    def blocked(reason, action):
        notice(reason, action, True, notification_kind="FAULT", automatic_restart_allowed=False)
        return {
            "ok": False,
            "reason_code": reason,
            "owner_action_required": True,
            "recovery_action": action,
            "restart_attempts": state["restart_attempts"],
            "watch_running": False,
            "post_allowed": False,
        }

    # Separate monitor exclusion within the existing registry owner. The global
    # launcher writer remains available for operator stop/start while we wait.
    with LauncherSingleWriterV1(root / "process_watch_exclusion_v1", session_id=session_id):
        try:
            if state_path.exists():
                try:
                    stored = json.loads(state_path.read_text(encoding="utf-8"))
                except (ValueError, TypeError):
                    return blocked(
                        "PROCESS_WATCH_STATE_UNPROVEN",
                        "Preserve and reconcile the malformed watch receipt before restarting.",
                    )
                if (
                    not isinstance(stored, dict)
                    or stored.get("integrity_digest") != _state_digest_v1(stored)
                    or stored.get("binding") != binding
                    or type(stored.get("restart_attempts")) is not int
                    or not 0 <= stored["restart_attempts"] <= DEFAULT_BOUNDED_RETRY_LIMIT
                    or type(stored.get("in_progress")) is not bool
                ):
                    return blocked(
                        "PROCESS_WATCH_STATE_UNPROVEN",
                        "Preserve and reconcile the existing watch receipt before restarting.",
                    )
                state = stored
            else:
                if (notice_root / "runtime_liveness_events_v1.jsonl").exists():
                    return blocked(
                        "PROCESS_WATCH_STATE_MISSING",
                        "Restore the proven prior watch budget; do not reset attempts by removing its receipt.",
                    )
                _save_watch_state_v1(state_path, state)
            started_at = float(time_fn())
            notice(
                "PROCESS_WATCH_STARTED",
                "Check the registered process within the explicit watch budget.",
                False,
                restart_on_failure=restart_on_failure,
            )
            # Also bounds a broken/injected monotonic clock or no-op sleeper.
            for _ in range(math.ceil(duration_seconds / interval_seconds) + 1):
                if float(time_fn()) - started_at >= duration_seconds:
                    break
                current = launcher.registry.require_session(session_id)
                if {key: getattr(current, key) for key in binding} != binding:
                    return blocked(
                        "PROCESS_WATCH_BINDING_CHANGED",
                        "Inspect the new session/config binding; do not restart from an old observation.",
                    )
                if current.lifecycle_state != "RUNNING":
                    if state["in_progress"]:
                        return blocked(
                            "PROCESS_WATCH_RESTART_OUTCOME_UNCERTAIN",
                            "Reconcile the interrupted stop/start before another attempt.",
                        )
                    if current.lifecycle_state not in {"STOPPED", "OFF"}:
                        return blocked(
                            "PROCESS_WATCH_LIFECYCLE_REQUIRES_OWNER",
                            "Inspect the failed, starting or locked lifecycle; do not clear its safety state.",
                        )
                    notice(
                        "PROCESS_WATCH_SESSION_NOT_RUNNING",
                        "Honor the owner's stopped/locked lifecycle; do not restart automatically.",
                        False,
                    )
                    return {
                        "ok": True,
                        "reason_code": "PROCESS_WATCH_SESSION_NOT_RUNNING",
                        "restart_attempts": state["restart_attempts"],
                        "watch_running": False,
                    }
                health = launcher.health(session_id, stale_seconds=stale_seconds)
                if health["healthy"]:
                    if state["in_progress"]:
                        notice(
                            "PROCESS_WATCH_READY_CONFIRMED",
                            "Current registered worker is ready; keep the spent attempt budget.",
                            False,
                            notification_kind="RECOVERED"
                            if state.get("mail_incident_id")
                            else None,
                            incident_id=state.get("mail_incident_id"),
                            recovery_scope="DASHBOARD_PROCESS_HEARTBEAT",
                        )
                        state["in_progress"] = False
                        _save_watch_state_v1(state_path, state)
                else:
                    reason = health["reason_code"]
                    if (
                        reason
                        not in {
                            "PROCESS_DEAD",
                            "HEARTBEAT_STALE",
                            "WORKER_REPORTS_UNHEALTHY",
                        }
                        or current.process_identity is None
                    ):
                        return blocked(
                            reason,
                            "Reconcile process/heartbeat identity before any process signal or restart.",
                        )
                    if state["in_progress"]:
                        return blocked(
                            "PROCESS_WATCH_RESTART_OUTCOME_UNCERTAIN",
                            "Reconcile the interrupted stop/start and current registry before another attempt.",
                        )
                    retry = bounded_retry_policy_v1(
                        attempt=state["restart_attempts"],
                        automatic_recovery_allowed=restart_on_failure,
                    )
                    if not retry["retry_allowed"]:
                        return blocked(
                            "PROCESS_WATCH_RESTART_LIMIT" if restart_on_failure else reason,
                            (
                                "Diagnose and repair the cause, then explicitly stop this session and start a new dashboard-only session ID. Preserve the old budget and evidence."
                                if restart_on_failure
                                else "Inspect the dashboard worker. Technical restart requires an explicitly opted-in watch and validated process/config identity."
                            ),
                        )
                    # Validate before spending an attempt or stopping a worker.
                    if (
                        resolve_repository_sha(launcher.paths.repository_root)
                        != current.repository_sha
                    ):
                        return blocked(
                            "PROCESS_WATCH_REVISION_CHANGED",
                            "Reconcile the repository revision before a technical restart.",
                        )
                    if compute_config_digest_v1(Path(current.config_path)) != current.config_digest:
                        return blocked(
                            "PROCESS_WATCH_CONFIG_CHANGED",
                            "Restore or explicitly rebind the config; the watched worker was not stopped.",
                        )
                    launcher.preflight(
                        mode=current.mode,
                        session_id=session_id,
                        config_path=Path(current.config_path),
                        repository_sha=current.repository_sha,
                        config_digest=current.config_digest,
                    )
                    if float(time_fn()) - started_at >= duration_seconds:
                        break
                    state["restart_attempts"] += 1
                    state["in_progress"] = True
                    _save_watch_state_v1(state_path, state)
                    fault_notice = notice(
                        "PROCESS_WATCH_RESTART_ATTEMPT",
                        "Restart this exact registered dashboard worker through O2 and recheck readiness.",
                        False,
                        observed_process=current.process_identity.to_dict(),
                        trigger=reason,
                        notification_kind="FAULT",
                        recovery_scope="DASHBOARD_PROCESS_HEARTBEAT",
                    )
                    state["mail_incident_id"] = fault_notice["event_id"]
                    _save_watch_state_v1(state_path, state)
                    # Recheck the registry epoch/lifecycle while acquiring O2's
                    # writer, so an operator replacement/stop is never killed.
                    launcher.restart(
                        session_id,
                        expected_process_identity=current.process_identity,
                        expected_lifecycle_states=("RUNNING",),
                    )
                    verified = launcher.health(session_id, stale_seconds=stale_seconds)
                    if not verified["healthy"]:
                        return blocked(
                            "PROCESS_WATCH_RESTART_NOT_READY",
                            "Inspect the started worker; readiness is unproven and the attempt remains spent.",
                        )
                    notice(
                        "PROCESS_WATCH_RESTART_READY",
                        "Registered dashboard worker is ready; continue within the same watch budget.",
                        False,
                        notification_kind="RECOVERED" if state.get("mail_incident_id") else None,
                        incident_id=state.get("mail_incident_id"),
                        recovery_scope="DASHBOARD_PROCESS_HEARTBEAT",
                    )
                    state["in_progress"] = False
                    _save_watch_state_v1(state_path, state)
                remaining = duration_seconds - (float(time_fn()) - started_at)
                if remaining > 0:
                    sleep_fn(min(interval_seconds, remaining))
            notice(
                "PROCESS_WATCH_BOUND_REACHED",
                "This bounded watch has ended; continued monitoring requires another explicitly started watch or an installed service.",
                True,
            )
            return {
                "ok": True,
                "reason_code": "PROCESS_WATCH_BOUND_REACHED",
                "restart_attempts": state["restart_attempts"],
                "watch_running": False,
                "host_stopped_by_watch_end": False,
                "post_allowed": False,
            }
        except Exception as exc:
            try:
                notice(
                    getattr(exc, "code", "PROCESS_WATCH_FAILURE"),
                    "Inspect watch/registry evidence and reconcile uncertain process state before another restart.",
                    True,
                    exception_type=type(exc).__name__,
                )
            except OSError:
                pass  # local notice writer logs failure; preserve original error
            raise

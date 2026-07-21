"""In-process lifecycle observability: heartbeat, progress, signals, exceptions."""

from __future__ import annotations

import os
import signal
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.evaluation_runner_lifecycle_observability_v1.atomic_io_v1 import (
    atomic_write_json_v1,
    read_json_if_present_v1,
)
from src.research.evaluation_runner_lifecycle_observability_v1.classification_v1 import (
    DEATH_CLASS_PERSISTENCE_FAILURE,
    DEATH_CLASS_SIGNAL,
    DEATH_CLASS_UNKNOWN,
    DEATH_CLASS_WORKER_EXCEPTION,
    classify_incomplete_run_v1,
)
from src.research.evaluation_runner_lifecycle_observability_v1.constants_v1 import (
    EXCEPTION_FILENAME,
    HEARTBEAT_FILENAME,
    MAX_EXCEPTION_MESSAGE_CHARS,
    MAX_MEMBER_ID_CHARS,
    MAX_TRACEBACK_CHARS,
    PHASE_COMPLETE,
    PHASE_INIT,
    PHASE_MEMBER,
    PHASE_PERSIST,
    PHASE_TERMINAL_FAILURE,
    PROGRESS_FILENAME,
    RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
    SCHEMA_VERSION,
    TERMINAL_DIAGNOSTICS_FILENAME,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _safe_member_id(member_id: str | None) -> str | None:
    if member_id is None:
        return None
    # Keep identifiers short; never dump paths or payloads.
    cleaned = str(member_id).replace("\n", " ").replace("\r", " ").strip()
    return _truncate(cleaned, MAX_MEMBER_ID_CHARS)


class EvaluationRunnerLifecycleObservabilityV1:
    """Persist runner progress/heartbeat/terminal process diagnostics fail-closed."""

    def __init__(
        self,
        diagnostics_dir: Path,
        *,
        run_id: str,
        pid: int | None = None,
    ) -> None:
        self.diagnostics_dir = Path(diagnostics_dir)
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = str(run_id)
        self.pid = int(pid if pid is not None else os.getpid())
        self._handlers_installed = False
        self._previous_handlers: dict[int, Any] = {}
        self._completed = False
        self.last_confirmed_phase: str | None = PHASE_INIT
        self.last_confirmed_member_index: int | None = None
        self.last_confirmed_member_id: str | None = None
        self.members_total: int | None = None
        self._write_heartbeat(phase=PHASE_INIT, note="lifecycle_attached")

    @property
    def heartbeat_path(self) -> Path:
        return self.diagnostics_dir / HEARTBEAT_FILENAME

    @property
    def progress_path(self) -> Path:
        return self.diagnostics_dir / PROGRESS_FILENAME

    @property
    def terminal_path(self) -> Path:
        return self.diagnostics_dir / TERMINAL_DIAGNOSTICS_FILENAME

    @property
    def exception_path(self) -> Path:
        return self.diagnostics_dir / EXCEPTION_FILENAME

    def install_signal_handlers(self) -> None:
        """Install catchable signal handlers that persist terminal diagnostics."""
        if self._handlers_installed:
            return
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            previous = signal.getsignal(sig)
            self._previous_handlers[int(sig)] = previous

            def _handler(
                signum: int,
                _frame: Any,
                *,
                _sig: int = int(sig),
            ) -> None:
                try:
                    name = signal.Signals(signum).name
                except ValueError:
                    name = f"SIGNAL_{signum}"
                self.record_signal_termination(signal_name=name, signum=signum)
                # Re-raise default termination after durable write.
                signal.signal(signum, signal.SIG_DFL)
                os.kill(os.getpid(), signum)

            signal.signal(sig, _handler)
        self._handlers_installed = True

    def uninstall_signal_handlers(self) -> None:
        if not self._handlers_installed:
            return
        for sig_num, previous in self._previous_handlers.items():
            try:
                signal.signal(sig_num, previous)
            except (ValueError, OSError):
                pass
        self._previous_handlers.clear()
        self._handlers_installed = False

    def _base_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "pid": self.pid,
            "updated_at_utc": _utc_now(),
            "last_confirmed_phase": self.last_confirmed_phase,
            "last_confirmed_member_index": self.last_confirmed_member_index,
            "last_confirmed_member_id": self.last_confirmed_member_id,
            "members_total": self.members_total,
            "completed": self._completed,
            "auto_rerun_allowed": False,
            "auto_resume_allowed": False,
        }

    def _write_heartbeat(self, *, phase: str, note: str | None = None) -> None:
        payload = self._base_payload()
        payload["phase"] = phase
        payload["heartbeat"] = True
        if note:
            payload["note"] = note
        atomic_write_json_v1(self.heartbeat_path, payload)

    def record_member_progress(
        self,
        *,
        phase: str,
        member_index: int,
        members_total: int,
        member_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Atomically persist last confirmed member (durable, not stdout-only)."""
        self.last_confirmed_phase = phase or PHASE_MEMBER
        self.last_confirmed_member_index = int(member_index)
        self.last_confirmed_member_id = _safe_member_id(member_id)
        self.members_total = int(members_total)
        progress = self._base_payload()
        progress["phase"] = self.last_confirmed_phase
        progress["member_index"] = self.last_confirmed_member_index
        progress["member_id"] = self.last_confirmed_member_id
        progress["members_total"] = self.members_total
        progress["progress_confirmed"] = True
        if extra:
            # Shallow, non-sensitive extras only (counts / flags).
            for key in sorted(extra):
                if key.startswith("_"):
                    continue
                value = extra[key]
                if isinstance(value, (bool, int, float, str)) or value is None:
                    progress[key] = value
        atomic_write_json_v1(self.progress_path, progress)
        self._write_heartbeat(phase=self.last_confirmed_phase, note="member_progress")

    def record_persist_phase(self, *, note: str = "persist_boundary") -> None:
        self.last_confirmed_phase = PHASE_PERSIST
        self._write_heartbeat(phase=PHASE_PERSIST, note=note)

    def mark_complete(self) -> None:
        self._completed = True
        self.last_confirmed_phase = PHASE_COMPLETE
        payload = self._base_payload()
        payload["phase"] = PHASE_COMPLETE
        payload["result_status"] = "COMPLETE"
        atomic_write_json_v1(self.progress_path, payload)
        self._write_heartbeat(phase=PHASE_COMPLETE, note="run_complete")
        self.uninstall_signal_handlers()

    def record_exception(self, exc: BaseException) -> dict[str, Any]:
        tb = _truncate(traceback.format_exc(), MAX_TRACEBACK_CHARS)
        message = _truncate(str(exc), MAX_EXCEPTION_MESSAGE_CHARS)
        exc_type = type(exc).__name__
        payload = {
            **self._base_payload(),
            "exception_type": exc_type,
            "exception_message_truncated": message,
            "traceback_truncated": tb,
        }
        atomic_write_json_v1(self.exception_path, payload)
        terminal = self.write_terminal_infrastructure_failure(
            death_class=DEATH_CLASS_WORKER_EXCEPTION,
            exception_type=exc_type,
            exception_message_truncated=message,
            exit_code=1,
            signal_name=None,
            extra={"traceback_truncated": tb},
        )
        return terminal

    def record_signal_termination(self, *, signal_name: str, signum: int) -> dict[str, Any]:
        return self.write_terminal_infrastructure_failure(
            death_class=DEATH_CLASS_SIGNAL,
            exception_type=None,
            exception_message_truncated=None,
            exit_code=-int(signum),
            signal_name=signal_name,
            extra={"signum": int(signum)},
        )

    def record_persistence_failure(self, exc: BaseException) -> dict[str, Any]:
        message = _truncate(str(exc), MAX_EXCEPTION_MESSAGE_CHARS)
        return self.write_terminal_infrastructure_failure(
            death_class=DEATH_CLASS_PERSISTENCE_FAILURE,
            exception_type=type(exc).__name__,
            exception_message_truncated=message,
            exit_code=1,
            signal_name=None,
            extra={"persistence_failure": True},
        )

    def write_terminal_infrastructure_failure(
        self,
        *,
        death_class: str,
        exception_type: str | None,
        exception_message_truncated: str | None,
        exit_code: int | None,
        signal_name: str | None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        progress = read_json_if_present_v1(self.progress_path) or {}
        phase = progress.get("phase", self.last_confirmed_phase)
        member_index = progress.get("member_index", self.last_confirmed_member_index)
        member_id = progress.get("member_id", self.last_confirmed_member_id)
        members_total = progress.get("members_total", self.members_total)
        classified = classify_incomplete_run_v1(
            death_class=death_class,
            last_confirmed_phase=phase,
            last_confirmed_member_index=member_index,
            last_confirmed_member_id=member_id,
            members_total=members_total,
            exception_type=exception_type,
            exception_message_truncated=exception_message_truncated,
            exit_code=exit_code,
            signal_name=signal_name,
            extra=extra,
        )
        self.last_confirmed_phase = PHASE_TERMINAL_FAILURE
        terminal = {
            **self._base_payload(),
            **classified,
            "result_class": RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            "death_class_fallback_if_unobserved": DEATH_CLASS_UNKNOWN,
            "phase": PHASE_TERMINAL_FAILURE,
        }
        atomic_write_json_v1(self.terminal_path, terminal)
        self._write_heartbeat(phase=PHASE_TERMINAL_FAILURE, note=death_class)
        return terminal

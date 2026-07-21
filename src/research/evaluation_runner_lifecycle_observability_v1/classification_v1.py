"""Fail-closed classification for incomplete / dead evaluation runner processes."""

from __future__ import annotations

import signal
from typing import Any, Mapping

from src.research.evaluation_runner_lifecycle_observability_v1.constants_v1 import (
    AUTO_RERUN_ALLOWED,
    AUTO_RESUME_ALLOWED,
    RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
)

INCONCLUSIVE_INFRASTRUCTURE_FAILURE = RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE

DEATH_CLASS_CLEAN_EXIT = "CLEAN_EXIT"
DEATH_CLASS_NONZERO_EXIT = "NONZERO_EXIT"
DEATH_CLASS_SIGNAL = "SIGNAL_TERMINATION"
DEATH_CLASS_NO_RESULT_EOF = "NO_RESULT_ABRUPT_EOF"
DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT = "TIMEOUT_OR_MISSING_HEARTBEAT"
DEATH_CLASS_WORKER_EXCEPTION = "WORKER_EXCEPTION"
DEATH_CLASS_PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE_AFTER_MEMBER"
DEATH_CLASS_UNKNOWN = "UNKNOWN_PROCESS_DEATH"


def _signal_name_from_negative_returncode(returncode: int) -> str | None:
    # POSIX convention used by subprocess: -N means killed by signal N.
    if returncode >= 0:
        return None
    sig_num = -returncode
    try:
        return signal.Signals(sig_num).name
    except ValueError:
        return f"SIGNAL_{sig_num}"


def normalize_process_exit_v1(
    *,
    returncode: int | None,
    signal_name: str | None = None,
) -> dict[str, Any]:
    """Normalize exit code / signal into a machine-readable death record."""
    if returncode is None and not signal_name:
        return {
            "exit_code": None,
            "signal_name": None,
            "death_class": DEATH_CLASS_UNKNOWN,
            "process_completed": False,
        }
    resolved_signal = signal_name or (
        _signal_name_from_negative_returncode(returncode) if returncode is not None else None
    )
    if resolved_signal:
        return {
            "exit_code": returncode,
            "signal_name": resolved_signal,
            "death_class": DEATH_CLASS_SIGNAL,
            "process_completed": False,
        }
    assert returncode is not None
    if returncode == 0:
        return {
            "exit_code": 0,
            "signal_name": None,
            "death_class": DEATH_CLASS_CLEAN_EXIT,
            "process_completed": True,
        }
    return {
        "exit_code": returncode,
        "signal_name": None,
        "death_class": DEATH_CLASS_NONZERO_EXIT,
        "process_completed": False,
    }


def classify_incomplete_run_v1(
    *,
    death_class: str,
    last_confirmed_phase: str | None,
    last_confirmed_member_index: int | None,
    last_confirmed_member_id: str | None,
    members_total: int | None,
    exception_type: str | None = None,
    exception_message_truncated: str | None = None,
    exit_code: int | None = None,
    signal_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify an incomplete evaluation as infrastructure-inconclusive (no rerun)."""
    payload: dict[str, Any] = {
        "result_class": RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
        "economic_verdict": "NOT_EVALUATED",
        "rerun_allowed": AUTO_RERUN_ALLOWED,
        "resume_allowed": AUTO_RESUME_ALLOWED,
        "auto_rerun_executed": False,
        "death_class": death_class,
        "last_confirmed_phase": last_confirmed_phase,
        "last_confirmed_member_index": last_confirmed_member_index,
        "last_confirmed_member_id": last_confirmed_member_id,
        "members_total": members_total,
        "exception_type": exception_type,
        "exception_message_truncated": exception_message_truncated,
        "exit_code": exit_code,
        "signal_name": signal_name,
        "fail_closed": True,
    }
    if extra:
        for key, value in extra.items():
            if key not in payload:
                payload[key] = value
    return payload

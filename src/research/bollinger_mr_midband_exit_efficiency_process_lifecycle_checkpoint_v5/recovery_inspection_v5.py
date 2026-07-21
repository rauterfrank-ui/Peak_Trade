"""Read-only recovery inspection for V5 lifecycle checkpoints.

Recovery inspection is diagnostic-only. It must not mutate run-slot state,
authorize a rerun, or promote partial metrics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.checkpoint_v5 import (
    assert_checkpoint_does_not_reclaim_run_slot,
    read_checkpoint_v5,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.constants_v5 import (
    AUTO_RERUN_ALLOWED,
    AUTO_RESUME_ALLOWED,
    ECONOMIC_VERDICT_NOT_EVALUATED,
    LIFECYCLE_STATE_TERMINAL_COMMITTED,
    PARTIAL_METRICS_AUTHORITATIVE,
    RECOVERY_DIAGNOSTICS_FILENAME,
    RECOVERY_INSPECTION_MUTATES_STATE,
    RESULT_CLASS_INFRASTRUCTURE_FAILURE,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.state_machine_v5 import (
    is_lifecycle_terminal,
)


class RecoveryInspectionError(ValueError):
    """Fail-closed recovery inspection error."""


def classify_dead_process_before_terminal_v5(
    *,
    checkpoint: Mapping[str, Any] | None,
    process_alive: bool,
) -> dict[str, Any]:
    """Dead process before TERMINAL_COMMITTED => INFRASTRUCTURE_FAILURE."""
    if process_alive:
        raise RecoveryInspectionError("PROCESS_STILL_ALIVE_NOT_DEAD_CLASSIFICATION")
    progress = (checkpoint or {}).get("progress") if isinstance(checkpoint, Mapping) else None
    lifecycle_state = None
    if isinstance(progress, Mapping):
        lifecycle_state = progress.get("lifecycle_state")
    if lifecycle_state == LIFECYCLE_STATE_TERMINAL_COMMITTED:
        raise RecoveryInspectionError("ALREADY_LIFECYCLE_TERMINAL")
    return {
        "result_class": RESULT_CLASS_INFRASTRUCTURE_FAILURE,
        "economic_verdict": ECONOMIC_VERDICT_NOT_EVALUATED,
        "diagnostic_class": "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL",
        "lifecycle_state": lifecycle_state,
        "lifecycle_terminal": False,
        "rerun_allowed": AUTO_RERUN_ALLOWED,
        "resume_allowed": AUTO_RESUME_ALLOWED,
        "partial_metrics_authoritative": PARTIAL_METRICS_AUTHORITATIVE,
        "recovery_inspection_mutates_state": RECOVERY_INSPECTION_MUTATES_STATE,
        "fail_closed": True,
    }


def inspect_recovery_readonly_v5(diagnostics_dir: Path) -> dict[str, Any]:
    checkpoint = read_checkpoint_v5(diagnostics_dir)
    if checkpoint is not None:
        assert_checkpoint_does_not_reclaim_run_slot(checkpoint)
    progress = (checkpoint or {}).get("progress") if isinstance(checkpoint, Mapping) else None
    lifecycle_state = progress.get("lifecycle_state") if isinstance(progress, Mapping) else None
    return {
        "diagnostics_dir": str(diagnostics_dir),
        "checkpoint_present": checkpoint is not None,
        "lifecycle_state": lifecycle_state,
        "lifecycle_terminal": bool(lifecycle_state and is_lifecycle_terminal(str(lifecycle_state))),
        "auto_rerun_allowed": AUTO_RERUN_ALLOWED,
        "auto_resume_allowed": AUTO_RESUME_ALLOWED,
        "partial_metrics_authoritative": PARTIAL_METRICS_AUTHORITATIVE,
        "recovery_inspection_mutates_state": False,
        "run_slot_reclaim_attempted": False,
        "authoritative_metrics_promoted": False,
        "recovery_diagnostics_filename": RECOVERY_DIAGNOSTICS_FILENAME,
        "checkpoint": checkpoint,
    }


def distinguish_summary_metrics_v5(
    *,
    panel_complete: bool,
    lifecycle_terminal: bool,
    partial_diagnostic_counters: Mapping[str, Any] | None = None,
    complete_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Complete metrics are authoritative only after panel+lifecycle terminal."""
    authoritative = bool(panel_complete and lifecycle_terminal)
    return {
        "complete_metrics_authoritative": authoritative,
        "partial_diagnostic_counters_authoritative": False,
        "partial_diagnostic_counters": dict(partial_diagnostic_counters or {}),
        "complete_metrics": dict(complete_metrics or {}) if authoritative else None,
        "partial_metrics_must_not_promote_to_baseline_treatment_or_delta": True,
    }

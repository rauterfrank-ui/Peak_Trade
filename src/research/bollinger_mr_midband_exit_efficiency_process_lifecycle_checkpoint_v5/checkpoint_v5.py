"""Atomic checkpoint persistence for V5 process-lifecycle observability.

Checkpoints are diagnostic-only. Persisting a checkpoint MUST NOT authorize an
automatic rerun or reclaim/create another run slot.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.constants_v5 import (
    AUTO_RERUN_ALLOWED,
    AUTO_RESUME_ALLOWED,
    CHECKPOINT_AUTHORIZES_RERUN,
    CHECKPOINT_CAN_RECLAIM_RUN_SLOT,
    CHECKPOINT_FILENAME,
    PARTIAL_METRICS_AUTHORITATIVE,
    REQUIRED_PROGRESS_METADATA_FIELDS,
    SCHEMA_VERSION,
    SURFACE_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.state_machine_v5 import (
    assert_known_lifecycle_state,
    build_progress_metadata,
)
from src.research.evaluation_runner_lifecycle_observability_v1.atomic_io_v1 import (
    atomic_write_json_v1,
    read_json_if_present_v1,
)


class CheckpointContractError(ValueError):
    """Fail-closed checkpoint contract error."""


def checkpoint_path(diagnostics_dir: Path) -> Path:
    return Path(diagnostics_dir) / CHECKPOINT_FILENAME


def assert_progress_metadata_complete(progress: Mapping[str, Any]) -> None:
    missing = [k for k in REQUIRED_PROGRESS_METADATA_FIELDS if k not in progress]
    if missing:
        raise CheckpointContractError(f"PROGRESS_METADATA_MISSING:{','.join(missing)}")
    assert_known_lifecycle_state(str(progress.get("lifecycle_state")))


def commit_checkpoint_v5(
    diagnostics_dir: Path,
    *,
    progress: Mapping[str, Any],
    extra_diagnostics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically persist a lifecycle checkpoint (temp + fsync + replace)."""
    assert_progress_metadata_complete(progress)
    normalized = build_progress_metadata(
        run_id=str(progress["run_id"]),
        process_id=progress.get("process_id"),
        started_at=str(progress["started_at"]),
        last_heartbeat_at=str(progress["last_heartbeat_at"]),
        current_member_index=progress.get("current_member_index"),
        completed_member_count=int(progress["completed_member_count"]),
        total_member_count=progress.get("total_member_count"),
        last_completed_member_id=progress.get("last_completed_member_id"),
        lifecycle_state=str(progress["lifecycle_state"]),
        checkpoint_sequence=int(progress["checkpoint_sequence"]),
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "surface_id": SURFACE_ID,
        "progress": normalized,
        "auto_rerun_allowed": AUTO_RERUN_ALLOWED,
        "auto_resume_allowed": AUTO_RESUME_ALLOWED,
        "checkpoint_authorizes_rerun": CHECKPOINT_AUTHORIZES_RERUN,
        "checkpoint_can_reclaim_run_slot": CHECKPOINT_CAN_RECLAIM_RUN_SLOT,
        "partial_metrics_authoritative": PARTIAL_METRICS_AUTHORITATIVE,
        "run_slot_claim_mutation": False,
        "evaluation_run_count_mutation": False,
    }
    if extra_diagnostics:
        safe_extra: dict[str, Any] = {}
        for key, value in extra_diagnostics.items():
            if key.startswith("_"):
                continue
            if isinstance(value, (bool, int, float, str)) or value is None:
                safe_extra[key] = value
        payload["diagnostics"] = safe_extra
    path = checkpoint_path(diagnostics_dir)
    atomic_write_json_v1(path, payload)
    return payload


def read_checkpoint_v5(diagnostics_dir: Path) -> dict[str, Any] | None:
    return read_json_if_present_v1(checkpoint_path(diagnostics_dir))


def assert_checkpoint_does_not_reclaim_run_slot(checkpoint: Mapping[str, Any]) -> None:
    if checkpoint.get("checkpoint_can_reclaim_run_slot") is not False:
        raise CheckpointContractError("CHECKPOINT_MUST_NOT_RECLAIM_RUN_SLOT")
    if checkpoint.get("checkpoint_authorizes_rerun") is not False:
        raise CheckpointContractError("CHECKPOINT_MUST_NOT_AUTHORIZE_RERUN")
    if checkpoint.get("auto_rerun_allowed") is not False:
        raise CheckpointContractError("CHECKPOINT_AUTO_RERUN_MUST_BE_FALSE")
    if checkpoint.get("run_slot_claim_mutation") is not False:
        raise CheckpointContractError("CHECKPOINT_MUST_NOT_MUTATE_RUN_SLOT")
    if checkpoint.get("evaluation_run_count_mutation") is not False:
        raise CheckpointContractError("CHECKPOINT_MUST_NOT_MUTATE_RUN_COUNT")

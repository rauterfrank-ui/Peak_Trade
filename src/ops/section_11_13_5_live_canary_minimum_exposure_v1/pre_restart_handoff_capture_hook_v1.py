"""Unique LIVE_ORDER lifecycle hook for §11.14 pre-restart handoff capture.

This is the sole productive runtime caller of
`commit_handoff_after_bound_fill_before_restart_v1`. It sits on the Live
canary path after proven identity-bound venue fill and before
`SupervisorLifecycle.restart`. It does not GET. It does not POST. It does
not invent a bound fill. It does not capture at ACK. Current Live/wire
gates remain false.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    evaluate_productive_capture_gates_v1,
    validate_capture_window_timestamps_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    commit_handoff_after_bound_fill_before_restart_v1,
)


def run_capture_hook_after_bound_fill_before_restart_v1(
    *,
    storage_root: Path,
    bound_fill_proven: bool,
    bound_fill_kind: object,
    bound_fill_identity: Mapping[str, Any],
    peak_trade_owned_resulting_current_position_qty: object,
    source_kind: object,
    unit: object,
    restart_already_occurred: bool,
    restart_not_yet_occurred_proven: bool,
    bound_fill_proven_at: object,
    capture_started_at: object,
    attempt_identity: object,
    restart_boundary_at: object | None = None,
    extra_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    gates = evaluate_productive_capture_gates_v1(
        bound_fill_proven=bound_fill_proven,
        bound_fill_kind=bound_fill_kind,
        bound_fill_identity=bound_fill_identity,
        peak_trade_owned_resulting_current_position_qty=(
            peak_trade_owned_resulting_current_position_qty
        ),
        source_kind=source_kind,
        unit=unit,
        restart_already_occurred=restart_already_occurred,
        restart_not_yet_occurred_proven=restart_not_yet_occurred_proven,
        bound_fill_proven_at=bound_fill_proven_at,
        capture_started_at=capture_started_at,
        restart_boundary_at=restart_boundary_at,
        attempt_identity=attempt_identity,
        extra_fields=extra_fields,
    )
    ack = commit_handoff_after_bound_fill_before_restart_v1(
        storage_root=storage_root,
        **gates["writer_kwargs"],
    )
    committed_at = str((ack.get("record") or {}).get("captured_at_utc") or "").strip()
    window = validate_capture_window_timestamps_v1(
        bound_fill_proven_at=bound_fill_proven_at,
        capture_started_at=capture_started_at,
        capture_committed_at=committed_at,
        restart_boundary_at=restart_boundary_at,
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_CAPTURE_HOOK_RESULT_V1",
        "PRODUCTIVE_CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "PRODUCTIVE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "HOOK_ORDERING_PROVEN": True,
        "BOUND_FILL_BEFORE_HOOK_PROVEN": True,
        "HOOK_BEFORE_RESTART_PROVEN": True,
        "DURABLE_SUCCESS_ACK": ack.get("DURABLE_SUCCESS_ACK"),
        "IDEMPOTENT_REPLAY": ack.get("IDEMPOTENT_REPLAY"),
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "capture_window": window,
        "identity": dict(gates["identity"]),
        "writer_ack": ack,
    }

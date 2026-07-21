"""Focused tests for V5 process-lifecycle checkpoint scaffold (definition-only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5 import (
    IMPORT_DOES_NOT_ACCESS_PANEL_DATA,
    IMPORT_DOES_NOT_CLAIM_RUN_SLOT,
    IMPORT_DOES_NOT_START_RUNNER,
    PACKAGE_MARKER,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.checkpoint_v5 import (
    assert_checkpoint_does_not_reclaim_run_slot,
    commit_checkpoint_v5,
    read_checkpoint_v5,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.constants_v5 import (
    LIFECYCLE_STATE_CHECKPOINT_COMMITTED,
    LIFECYCLE_STATE_MEMBER_COMPLETED,
    LIFECYCLE_STATE_MEMBER_STARTED,
    LIFECYCLE_STATE_NOT_STARTED,
    LIFECYCLE_STATE_PREFLIGHT_RUNNING,
    LIFECYCLE_STATE_RUNNER_STARTED,
    LIFECYCLE_STATE_TERMINAL_COMMITTED,
    MONOTONIC_LIFECYCLE_STATES,
    PARTIAL_METRICS_AUTHORITATIVE,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.import_safety_v5 import (
    assert_no_runner_entrypoint_on_import,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.recovery_inspection_v5 import (
    classify_dead_process_before_terminal_v5,
    distinguish_summary_metrics_v5,
    inspect_recovery_readonly_v5,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.state_machine_v5 import (
    LifecycleStateError,
    assert_monotonic_transition,
    build_progress_metadata,
)


def test_import_does_not_start_runner() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert IMPORT_DOES_NOT_START_RUNNER is True
    assert IMPORT_DOES_NOT_CLAIM_RUN_SLOT is True
    assert IMPORT_DOES_NOT_ACCESS_PANEL_DATA is True
    assert_no_runner_entrypoint_on_import()


def test_monotonic_lifecycle_transitions() -> None:
    assert MONOTONIC_LIFECYCLE_STATES[0] == LIFECYCLE_STATE_NOT_STARTED
    assert MONOTONIC_LIFECYCLE_STATES[-1] == LIFECYCLE_STATE_TERMINAL_COMMITTED
    assert_monotonic_transition(
        from_state=LIFECYCLE_STATE_NOT_STARTED,
        to_state=LIFECYCLE_STATE_PREFLIGHT_RUNNING,
    )
    assert_monotonic_transition(
        from_state=LIFECYCLE_STATE_MEMBER_STARTED,
        to_state=LIFECYCLE_STATE_MEMBER_COMPLETED,
    )
    assert_monotonic_transition(
        from_state=LIFECYCLE_STATE_CHECKPOINT_COMMITTED,
        to_state=LIFECYCLE_STATE_MEMBER_STARTED,
    )
    with pytest.raises(LifecycleStateError):
        assert_monotonic_transition(
            from_state=LIFECYCLE_STATE_RUNNER_STARTED,
            to_state=LIFECYCLE_STATE_NOT_STARTED,
        )
    with pytest.raises(LifecycleStateError):
        assert_monotonic_transition(
            from_state=LIFECYCLE_STATE_TERMINAL_COMMITTED,
            to_state=LIFECYCLE_STATE_MEMBER_STARTED,
        )


def test_atomic_checkpoint_contract(tmp_path: Path) -> None:
    progress = build_progress_metadata(
        run_id="run-test",
        process_id=123,
        started_at="2026-07-21T00:00:00Z",
        last_heartbeat_at="2026-07-21T00:01:00Z",
        current_member_index=0,
        completed_member_count=0,
        total_member_count=46,
        last_completed_member_id=None,
        lifecycle_state=LIFECYCLE_STATE_RUNNER_STARTED,
        checkpoint_sequence=1,
    )
    payload = commit_checkpoint_v5(tmp_path, progress=progress)
    assert payload["auto_rerun_allowed"] is False
    assert payload["checkpoint_authorizes_rerun"] is False
    assert payload["checkpoint_can_reclaim_run_slot"] is False
    assert payload["partial_metrics_authoritative"] is False
    assert payload["run_slot_claim_mutation"] is False
    loaded = read_checkpoint_v5(tmp_path)
    assert loaded is not None
    assert loaded["progress"]["checkpoint_sequence"] == 1
    assert_checkpoint_does_not_reclaim_run_slot(loaded)


def test_dead_process_classified_infrastructure_failure(tmp_path: Path) -> None:
    progress = build_progress_metadata(
        run_id="run-dead",
        process_id=999,
        started_at="2026-07-21T00:00:00Z",
        last_heartbeat_at="2026-07-21T00:05:00Z",
        current_member_index=1,
        completed_member_count=1,
        total_member_count=46,
        last_completed_member_id="1INCH-USDT-SWAP",
        lifecycle_state=LIFECYCLE_STATE_CHECKPOINT_COMMITTED,
        checkpoint_sequence=2,
    )
    commit_checkpoint_v5(tmp_path, progress=progress)
    checkpoint = read_checkpoint_v5(tmp_path)
    result = classify_dead_process_before_terminal_v5(
        checkpoint=checkpoint,
        process_alive=False,
    )
    assert result["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert result["economic_verdict"] == "NOT_EVALUATED"
    assert result["rerun_allowed"] is False
    assert result["partial_metrics_authoritative"] is False


def test_partial_metrics_remain_non_authoritative() -> None:
    assert PARTIAL_METRICS_AUTHORITATIVE is False
    summary = distinguish_summary_metrics_v5(
        panel_complete=False,
        lifecycle_terminal=False,
        partial_diagnostic_counters={"baseline_members_completed": 1},
        complete_metrics={"net_return_after_costs": 0.01},
    )
    assert summary["complete_metrics_authoritative"] is False
    assert summary["partial_diagnostic_counters_authoritative"] is False
    assert summary["complete_metrics"] is None
    assert summary["partial_metrics_must_not_promote_to_baseline_treatment_or_delta"] is True


def test_recovery_inspection_readonly_no_slot_reclaim(tmp_path: Path) -> None:
    progress = build_progress_metadata(
        run_id="run-recovery",
        process_id=42,
        started_at="2026-07-21T00:00:00Z",
        last_heartbeat_at="2026-07-21T00:02:00Z",
        current_member_index=0,
        completed_member_count=0,
        total_member_count=46,
        last_completed_member_id=None,
        lifecycle_state=LIFECYCLE_STATE_MEMBER_STARTED,
        checkpoint_sequence=1,
    )
    commit_checkpoint_v5(tmp_path, progress=progress)
    report = inspect_recovery_readonly_v5(tmp_path)
    assert report["recovery_inspection_mutates_state"] is False
    assert report["run_slot_reclaim_attempted"] is False
    assert report["authoritative_metrics_promoted"] is False
    assert report["auto_rerun_allowed"] is False

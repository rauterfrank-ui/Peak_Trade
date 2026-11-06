"""Reduce/Exit must retain their meaning at the entry-only sizing boundary."""

from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    DECISION_POSITION_MANAGEMENT,
    POSITION_MANAGEMENT_HANDOFF_REQUIRED,
    current_productive_decision_class_v1,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from tests.ops.test_current_productive_occupied_scope_continuity_v1 import _cycle
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
)


def _assert_management_not_entry_or_hold(replay):
    assert current_productive_decision_class_v1(replay) == DECISION_POSITION_MANAGEMENT
    result = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        decision_epoch="offline-regression",
    )
    assert result.decision_class == DECISION_POSITION_MANAGEMENT
    assert result.replay is replay
    assert result.called is False
    assert result.get_count == 0
    assert result.venue_plan_authorized is False
    assert result.first_blocker == POSITION_MANAGEMENT_HANDOFF_REQUIRED
    assert result.permit_created == "false"
    assert result.post_count == "0"


@pytest.mark.parametrize("outcome", ["reduce", "exit"])
def test_management_outcome_never_receives_hold_plan_authorization(outcome):
    replay = SimpleNamespace(evidence=SimpleNamespace(decision_outcome=outcome))
    _assert_management_not_entry_or_hold(replay)
    assert replay.evidence.decision_outcome == outcome


@pytest.mark.parametrize("direction", [1, -1])
def test_safety_exit_after_natural_entry_preserves_exit_and_requires_execution_handoff(
    tmp_path, direction
):
    cursor = None
    for step in range(3):
        entry = _cycle(tmp_path, direction=direction, step=step, incoming=cursor)
        assert entry.replay_pass == "true", entry.fail_reasons
        cursor = entry.outgoing_cursor
    assert entry.decision_outcome == ("enter_long" if direction == 1 else "enter_short")
    exit_cycle = _cycle(
        tmp_path,
        direction=direction,
        step=3,
        incoming=cursor,
        occupied=True,
        explicit_killstate_active=True,
    )
    assert exit_cycle.replay_pass == "true", exit_cycle.fail_reasons
    assert exit_cycle.decision_outcome == "exit"
    assert "safety_exit" in exit_cycle.replay.evidence.reason_codes
    _assert_management_not_entry_or_hold(exit_cycle.replay)

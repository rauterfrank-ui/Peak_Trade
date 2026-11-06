"""Offline regression for the entry → occupied-position scope handoff."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    persist_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
    ensure_productive_layered_core_episode_store_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_layered_core_bind_wiring_v1 import (
    productive_layered_core_bind_cycle_kwargs_v1,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import provenance_for_bound_v1
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _f1_m9_cycle_ledger_kwargs_v1,
    _produced_g17_producer,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState


def _cycle(
    root,
    *,
    direction=1,
    step=0,
    incoming=None,
    occupied=False,
    event_time_base=1_700_000_000.0,
    explicit_killstate_active=False,
    position_episode_binding=None,
    position_episode_scope=None,
):
    bound = _bound()
    closes = tuple(1000.0 + direction * 20.0 * i / 99 for i in range(100))
    mark = 1000.0 + direction * (0.0 if step == 0 else 20.0 + 1.2 * (step - 1))
    ts = event_time_base + step * 60.0
    if position_episode_binding is not None and position_episode_scope is None:
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeScopeV1,
        )

        position_episode_scope = PositionEpisodeScopeV1(
            "test-account", "INTERNAL_SIMULATED_EXECUTION"
        )
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id=f"occupied-continuity:{direction}:{step}",
        observed_unix=ts + 1.0,
        mark_px=mark,
        index_px=mark * 0.995,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=12345.0,
        open_interest=1000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=ts,
        venue_flat=not occupied,
        existing_position_side=(
            ExistingPositionSide.LONG if direction == 1 else ExistingPositionSide.SHORT
        )
        if occupied
        else ExistingPositionSide.NONE,
        incoming_cursor=incoming,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=bound.instrument_id),
        explicit_killstate_active=explicit_killstate_active,
        position_episode_binding=position_episode_binding,
        position_episode_scope=position_episode_scope,
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound, mark_px=mark, index_px=mark * 0.995
        ),
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound,
        ),
        **productive_layered_core_bind_cycle_kwargs_v1(
            layered_core_store_root=root,
            incoming_cursor=incoming,
        ),
        **_f1_m9_cycle_ledger_kwargs_v1(),
    )
    if result.outgoing_cursor is not None:
        assert not ensure_productive_layered_core_episode_store_v1(
            store_root=root,
            bound_instrument=bound,
            mark_price_m_t=mark,
            finalized_closes=closes,
            last_finalized_event_ts_unix=ts,
            outgoing_cursor=result.outgoing_cursor,
        )
    return result


@pytest.mark.parametrize("direction,decision", [(1, "ENTER_LONG"), (-1, "ENTER_SHORT")])
def test_natural_entry_continues_scope_when_position_becomes_occupied(
    tmp_path: Path,
    direction: int,
    decision: str,
):
    cursor = None
    for step in range(3):
        cycle = _cycle(tmp_path, direction=direction, step=step, incoming=cursor)
        assert cycle.replay_pass == "true", cycle.fail_reasons
        cursor = cycle.outgoing_cursor
        assert cursor is not None
    assert cycle.decision_outcome == decision.lower()
    scope_id = cursor.existing_scope.scope_id
    for step in (3, 4):
        prior = cursor
        persist_current_productive_sidestate_confirmation_cursor_v1(prior, store_root=tmp_path)
        incoming = load_current_productive_sidestate_confirmation_cursor_v1(tmp_path)
        cycle = _cycle(tmp_path, direction=direction, step=step, incoming=incoming, occupied=True)
        assert cycle.replay_pass == "true", cycle.fail_reasons
        assert cycle.decision_outcome not in {"enter_long", "enter_short"}
        assert cycle.cursor_restore_status == "restored"
        cursor = cycle.outgoing_cursor
        assert cursor is not None
        assert cursor.existing_scope.scope_id == scope_id
        assert cursor.now_tick == prior.now_tick + 1
        assert cycle.replay.intermediate.scope_event is not None
        assert cursor.runtime_scope_state is not None


@pytest.mark.parametrize("state", [SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE])
def test_active_state_restores_only_when_position_is_occupied(tmp_path: Path, state):
    cursor = replace(_cycle(tmp_path).outgoing_cursor, side_state=state)
    kwargs = dict(
        expected_instrument_id=cursor.instrument_id,
        expected_venue_native_id=cursor.venue_native_id,
    )
    occupied = restore_current_productive_sidestate_confirmation_cursor_v1(
        cursor.to_dict(),
        venue_flat=False,
        **kwargs,
    )
    assert occupied.disposition.value == "restored"
    assert occupied.cursor.side_state is state
    assert occupied.cursor.existing_scope == cursor.existing_scope
    assert occupied.cursor.runtime_scope_state == cursor.runtime_scope_state
    assert occupied.cursor.scope_confirmation == cursor.scope_confirmation
    flat = restore_current_productive_sidestate_confirmation_cursor_v1(
        cursor,
        venue_flat=True,
        **kwargs,
    )
    assert flat.cursor is None
    assert flat.reason_code == "CURSOR_ACTIVE_SIDESTATE_WHILE_FLAT"


@pytest.mark.parametrize(
    "invalid",
    ["missing", "foreign", "foreign_native", "foreign_scope", "no_scope", "corrupt", "stale"],
)
def test_occupied_position_never_restarts_from_unusable_state(tmp_path: Path, invalid):
    cursor = _cycle(tmp_path).outgoing_cursor
    if invalid == "missing":
        incoming = None
    elif invalid == "foreign":
        incoming = replace(cursor, instrument_id="foreign-future")
    elif invalid == "foreign_native":
        incoming = replace(cursor, venue_native_id="foreign-native")
    elif invalid == "foreign_scope":
        incoming = replace(
            cursor, existing_scope=replace(cursor.existing_scope, instrument_id="foreign-future")
        )
    elif invalid == "no_scope":
        incoming = replace(cursor, existing_scope=None)
    elif invalid == "stale":
        incoming = replace(cursor, trading_epoch=cursor.last_evaluated_trading_epoch)
    else:
        incoming = {"side_state": "invalid"}
    cycle = _cycle(tmp_path, step=1, incoming=incoming, occupied=True)
    assert cycle.replay_pass == "false"
    assert cycle.replay is None
    assert cycle.outgoing_cursor is None

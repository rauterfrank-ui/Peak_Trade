"""Offline P2: occupied cycles keep a valid cursor; flat ACTIVE stays refused."""

from __future__ import annotations

from dataclasses import replace

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    restore_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    provenance_for_bound_v1,
)
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _INSTRUMENT,
    _bound,
    _f1_m9_cycle_ledger_kwargs_v1,
    _produced_g17_producer,
    _strong_uptrend_closes,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState


def _occupied_cycle(
    *,
    cycle_id: str,
    incoming_cursor: object | None = None,
    instrument_id: str = _INSTRUMENT,
    event_ts_unix: float = 1_700_000_000.0,
):
    path = _strong_uptrend_closes()
    last = float(path[-1])
    bound = _bound(instrument_id=instrument_id)
    index_px = last * 0.995
    return run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id=cycle_id,
        observed_unix=float(event_ts_unix) + 100.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=path,
        last_finalized_event_ts_unix=float(event_ts_unix),
        venue_flat=False,
        existing_position_side=ExistingPositionSide.LONG,
        incoming_cursor=incoming_cursor,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=instrument_id),
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound,
            mark_px=last,
            index_px=index_px,
        ),
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound,
            session_id=cycle_id,
        ),
        **_f1_m9_cycle_ledger_kwargs_v1(),
    )


def _two_occupied_cycles():
    first = _occupied_cycle(cycle_id="p2-occupied-1", event_ts_unix=1_700_000_000.0)
    assert first.cursor_restore_status == "missing"
    assert first.outgoing_cursor is not None
    assert first.replay is not None
    second = _occupied_cycle(
        cycle_id="p2-occupied-2",
        incoming_cursor=first.outgoing_cursor,
        event_ts_unix=1_700_000_060.0,
    )
    return first, second


def test_occupied_cycles_preserve_epoch_scope_and_c3() -> None:
    first, second = _two_occupied_cycles()
    prior = first.outgoing_cursor
    assert prior is not None
    assert second.cursor_restore_status == "restored"
    assert second.outgoing_cursor is not None
    assert second.replay is not None
    assert second.replay.intermediate is not None
    assert second.outgoing_cursor.trading_epoch == prior.trading_epoch + 1
    assert second.outgoing_cursor.last_evaluated_trading_epoch == prior.trading_epoch
    assert second.replay.intermediate.runtime_scope_reinitialized is False
    assert prior.runtime_scope_state is not None
    before = second.replay.intermediate.runtime_scope_state_before
    assert before.anchor_price == prior.runtime_scope_state.anchor_price
    assert before.current_hysteresis_band == prior.runtime_scope_state.current_hysteresis_band
    assert prior.scope_confirmation.candidate_kind is None
    assert (
        second.outgoing_cursor.scope_confirmation.candidate_count
        == prior.scope_confirmation.candidate_count
    )
    assert (
        second.outgoing_cursor.scope_confirmation.last_evaluated_trading_epoch
        >= prior.scope_confirmation.last_evaluated_trading_epoch
    )


def test_missing_cursor_stays_missing_and_does_not_invent_history() -> None:
    missing = restore_current_productive_sidestate_confirmation_cursor_v1(
        None,
        expected_instrument_id=_INSTRUMENT,
        expected_venue_native_id=_INSTRUMENT,
        venue_flat=False,
    )
    assert missing.disposition.value == "missing"
    assert missing.cursor is None
    assert missing.fail_closed is False
    first = _occupied_cycle(cycle_id="p2-missing")
    assert first.cursor_restore_status == "missing"
    assert first.outgoing_cursor is not None
    assert first.outgoing_cursor.trading_epoch == 2
    assert first.outgoing_cursor.last_evaluated_trading_epoch == 1


def test_foreign_instrument_cursor_is_rejected() -> None:
    first = _occupied_cycle(cycle_id="p2-foreign-source")
    assert first.outgoing_cursor is not None
    foreign = replace(
        first.outgoing_cursor,
        instrument_id="inst-foreign",
        venue_native_id="inst-foreign",
        trading_epoch=7,
        last_evaluated_trading_epoch=6,
        now_tick=7,
    )
    refused = restore_current_productive_sidestate_confirmation_cursor_v1(
        foreign,
        expected_instrument_id=_INSTRUMENT,
        expected_venue_native_id=_INSTRUMENT,
        venue_flat=False,
    )
    assert refused.disposition.value == "refused_mismatch"
    assert refused.cursor is None
    assert refused.reason_code == "CURSOR_INSTRUMENT_MISMATCH"
    cycle = _occupied_cycle(cycle_id="p2-foreign-cycle", incoming_cursor=foreign)
    assert cycle.cursor_restore_status == "refused_mismatch"
    assert cycle.outgoing_cursor is not None
    assert cycle.outgoing_cursor.instrument_id == _INSTRUMENT
    assert cycle.outgoing_cursor.trading_epoch == 2
    assert cycle.outgoing_cursor.trading_epoch != foreign.trading_epoch + 1


def test_flat_active_cursor_stays_refused_and_occupied_active_restores() -> None:
    first = _occupied_cycle(cycle_id="p2-active-source")
    assert first.outgoing_cursor is not None
    active = replace(first.outgoing_cursor, side_state=SideState.LONG_ACTIVE)
    flat = restore_current_productive_sidestate_confirmation_cursor_v1(
        active,
        expected_instrument_id=_INSTRUMENT,
        expected_venue_native_id=_INSTRUMENT,
        venue_flat=True,
    )
    assert flat.disposition.value == "refused_stale"
    assert flat.cursor is None
    assert flat.reason_code == "CURSOR_ACTIVE_SIDESTATE_WHILE_FLAT"
    occupied = restore_current_productive_sidestate_confirmation_cursor_v1(
        active,
        expected_instrument_id=_INSTRUMENT,
        expected_venue_native_id=_INSTRUMENT,
        venue_flat=False,
    )
    assert occupied.disposition.value == "restored"
    assert occupied.cursor is not None
    assert occupied.cursor.trading_epoch == active.trading_epoch
    assert occupied.cursor.runtime_scope_state == active.runtime_scope_state
    assert occupied.cursor.scope_confirmation == active.scope_confirmation


def test_corrupt_cursor_stays_fail_closed() -> None:
    corrupt = restore_current_productive_sidestate_confirmation_cursor_v1(
        {"schema_name": "not-a-cursor"},
        expected_instrument_id=_INSTRUMENT,
        expected_venue_native_id=_INSTRUMENT,
        venue_flat=False,
    )
    assert corrupt.disposition.value == "fail_closed_corrupt"
    assert corrupt.cursor is None
    assert corrupt.fail_closed is True
    cycle = _occupied_cycle(
        cycle_id="p2-corrupt",
        incoming_cursor={"schema_name": "not-a-cursor"},
    )
    assert cycle.replay is None
    assert cycle.outgoing_cursor is None
    assert cycle.cursor_restore_status == "fail_closed_corrupt"
    assert cycle.fail_reasons

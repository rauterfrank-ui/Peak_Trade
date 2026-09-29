"""F1/M9 governed seam + G17 + Master-V2 cold start and restart (LANE_1 semantics)."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)


from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_LINEAGE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from tests.ops._current_productive_f1_m9_durable_seam_fixture_v1 import (
    materialize_f1_m9_runtime_applied_seam_ledgers_v1,
)
from tests.ops.test_current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    CAPTURE_TS,
    _bound,
    _mark_payload,
)


def test_fresh_lane_cold_start_then_restart_preserves_cursor_lineage(tmp_path: Path) -> None:
    f1_m9 = materialize_f1_m9_runtime_applied_seam_ledgers_v1(tmp_path / "f1_m9")
    g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path / "g17",
        bound_instrument=_bound(),
        mark_candles_payload=_mark_payload(),
        receive_or_capture_timestamp=CAPTURE_TS,
    )
    assert g17.producer is not None
    closes = tuple(100.0 + i * 0.01 for i in range(80))
    last = float(closes[-1])
    index_px = last * 0.995
    bound = _bound()
    ledger_kw = {
        "f1_m9_productive_apply_ledger_paths": f1_m9["apply_ledger_paths"],
        "f1_m9_threshold_ledger_paths": f1_m9["threshold_ledger_paths"],
    }
    cold = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="f1-m9-cold-start",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        incoming_cursor=None,
        g17_typed_vol_producer=g17.producer,
        **ledger_kw,
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id or bound.instrument_id),
            mark_px=float(last),
            index_px=float(index_px),
        ),
    )
    assert cold.input_blocker == ""
    assert cold.outgoing_cursor is not None
    assert cold.outgoing_cursor.lineage_id == CURSOR_LINEAGE_ID
    assert cold.outgoing_cursor.trading_epoch == 2

    warm = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="f1-m9-restart",
        observed_unix=1_700_000_160.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_060.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        incoming_cursor=cold.outgoing_cursor,
        g17_typed_vol_producer=g17.producer,
        **ledger_kw,
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id or bound.instrument_id),
            mark_px=float(last),
            index_px=float(index_px),
        ),
    )
    assert warm.input_blocker == ""
    assert warm.cursor_restore_status == "restored"
    assert warm.outgoing_cursor is not None
    assert warm.outgoing_cursor.trading_epoch == cold.outgoing_cursor.trading_epoch + 1


def test_missing_seam_fail_closed_without_g17(tmp_path: Path) -> None:
    f1_m9 = materialize_f1_m9_runtime_applied_seam_ledgers_v1(tmp_path / "f1_m9")
    closes = tuple(100.0 + i * 0.01 for i in range(80))
    last = float(closes[-1])
    index_px = last * 0.995
    bound = _bound()
    cycle = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="f1-m9-no-g17",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=None,
        f1_m9_productive_apply_ledger_paths=f1_m9["apply_ledger_paths"],
        f1_m9_threshold_ledger_paths=f1_m9["threshold_ledger_paths"],
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id or bound.instrument_id),
            mark_px=float(last),
            index_px=float(index_px),
        ),
    )
    assert cycle.replay is not None
    assert cycle.replay.replay_pass is False
    assert cycle.outgoing_cursor is None

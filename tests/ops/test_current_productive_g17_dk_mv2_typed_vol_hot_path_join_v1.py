"""DK/MV2 typed-volatility hot-path join — JOIN-1 + JOIN-2 handoff tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    CMC_BINDING_PERFORMED,
    JOIN_OWNER,
    PACKAGE_MARKER,
    PRESENCE_GATE_MUTATED,
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    TYPED_VOLATILITY_ESTIMATE_MISSING_REASON,
)
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _mark_row,
    _sixty_one_samples,
)

CANON = "ADA-USDT-SWAP"
NATIVE = "ADA-USDT-SWAP"
CAPTURE_TS = "1700000061000"


def _bound() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=CANON,
        venue_native_id=NATIVE,
        ranking_snapshot_id="rank-dk-g17",
        ranking_integrity_digest="rank-dk-g17-digest",
        universe_snapshot_id="uni-dk-g17",
        selection_id="sel-dk-g17",
        selection_integrity_digest="sel-dk-g17-digest",
        selection_state="SELECTED",
    )


def _mark_payload(*, rows: list[list[str]] | None = None) -> dict:
    if rows is None:
        rows = list(reversed([_mark_row(i) for i in range(61)]))
    return {"code": "0", "msg": "", "data": rows}


def test_constants_and_authority_frozen() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert JOIN_OWNER.endswith("current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1")
    assert CMC_BINDING_PERFORMED is False
    assert PRESENCE_GATE_MUTATED is False


def test_missing_mark_payload_fail_closed(tmp_path: Path) -> None:
    result = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path,
        bound_instrument=_bound(),
        mark_candles_payload=None,
        receive_or_capture_timestamp=CAPTURE_TS,
    )
    assert result.fail_closed is True
    assert result.producer is None
    assert result.extraction_failure_codes


def test_insufficient_marks_fail_closed_no_silent_default(tmp_path: Path) -> None:
    short_rows = list(reversed([_mark_row(i) for i in range(10)]))
    result = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path,
        bound_instrument=_bound(),
        mark_candles_payload=_mark_payload(rows=short_rows),
        receive_or_capture_timestamp=CAPTURE_TS,
    )
    assert result.fail_closed is True
    assert result.producer is None


def test_incomplete_bound_identity_fail_closed(tmp_path: Path) -> None:
    result = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path,
        bound_instrument=BoundInstrumentV1(
            instrument_id="",
            venue_native_id="",
            ranking_snapshot_id="r",
            ranking_integrity_digest="d",
            universe_snapshot_id="u",
            selection_id="s",
            selection_integrity_digest="sd",
            selection_state="SELECTED",
        ),
        mark_candles_payload=_mark_payload(),
        receive_or_capture_timestamp=CAPTURE_TS,
    )
    assert result.fail_closed is True
    assert result.reason_code in {
        "CHECKPOINT_BOUND_IDENTITY_INCOMPLETE",
        "G17_MARK_SAMPLE_EXTRACTION_FAIL_CLOSED",
    }


def test_sufficient_marks_produce_estimate_and_mv2_accepts(tmp_path: Path) -> None:
    join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path,
        bound_instrument=_bound(),
        mark_candles_payload=_mark_payload(),
        receive_or_capture_timestamp=CAPTURE_TS,
    )
    assert join.fail_closed is False
    assert join.producer is not None
    assert join.estimate_present is True
    port = join.producer.output_port_v1()
    assert port.outcome == TypedRuntimeProducerOutcomeV1.PRODUCED
    closes = tuple(100.0 + i * 0.01 for i in range(80))
    last = float(closes[-1])
    cycle = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=_bound(),
        cycle_id="dk-g17-hot-path-proof",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=last,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=join.producer,
    )
    assert cycle.input_blocker == ""
    assert cycle.replay is not None
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON not in cycle.fail_reasons


def test_dk_cycle_payload_uses_same_sample_factory() -> None:
    samples = _sixty_one_samples(
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
    )
    assert len(samples) == 61
    assert samples[0].venue == DEFAULT_VENUE
    assert ENDPOINT_HISTORY_MARK_PRICE_CANDLES.startswith("/api/v5/")

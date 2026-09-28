"""Productive Master-V2 optional DDO learning capture join."""

from __future__ import annotations

from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.capture_v0 import SEAM_MASTER_V2_EVIDENCE
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    build_provenance_from_resolved_cmc_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from tests.ops.test_current_productive_g17_typed_vol_cmc_bind_v1 import _closes
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _apply,
    _sixty_one_samples,
)


def _cycle_kwargs(*, cycle_id: str, tmp_path: Path) -> dict:
    created = _apply(tmp_path, samples=_sixty_one_samples())
    closes = _closes()
    last = float(closes[-1])
    index_px = last * 0.995
    bound = BoundInstrumentV1(
        instrument_id="inst-eth-usdt-perp",
        venue_native_id="ETH-USDT-SWAP",
        ranking_snapshot_id="rank-ddo-cap",
        ranking_integrity_digest="rank-ddo-cap-digest",
        universe_snapshot_id="uni-ddo-cap",
        selection_id="sel-ddo-cap",
        selection_integrity_digest="sel-ddo-cap-digest",
        selection_state="SELECTED",
    )
    return {
        "bound_instrument": bound,
        "cycle_id": cycle_id,
        "observed_unix": 1_700_000_100.0,
        "mark_px": last,
        "index_px": index_px,
        "bid_px": last - 0.5,
        "ask_px": last + 0.5,
        "volume": 12_345.0,
        "open_interest": 1_000.0,
        "funding_rate": 0.0001,
        "finalized_closes": closes,
        "last_finalized_event_ts_unix": 1_700_000_000.0,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE,
        "g17_typed_vol_producer": created.producer,
        "ddo_durable_evidence_ledger_path": tmp_path / "ddo_productive_capture.jsonl",
        "canonical_price_provenance": build_provenance_from_resolved_cmc_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id),
            mark_px=last,
            index_px=index_px,
            index_source=INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
        ),
    }


def test_master_v2_cycle_records_ddo_capture_when_ledger_bound(tmp_path: Path) -> None:
    result = run_current_productive_master_v2_runtime_cycle_v1(
        **_cycle_kwargs(cycle_id="ddo-cap-1", tmp_path=tmp_path)
    )
    summary = result.ddo_capture_summary
    assert summary is not None
    assert summary.get("ok") is True
    assert summary.get("skipped") is not True
    ledger_path = tmp_path / "ddo_productive_capture.jsonl"
    assert ledger_path.is_file()
    text = ledger_path.read_text(encoding="utf-8")
    assert SEAM_MASTER_V2_EVIDENCE in text or "master_v2" in text


def test_master_v2_cycle_without_ledger_has_no_ddo_summary(tmp_path: Path) -> None:
    kwargs = _cycle_kwargs(cycle_id="ddo-cap-2", tmp_path=tmp_path)
    kwargs.pop("ddo_durable_evidence_ledger_path")
    result = run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    assert result.ddo_capture_summary is None

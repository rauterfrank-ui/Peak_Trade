"""Cap24 per-lane canonical price provenance compose tests."""

from __future__ import annotations

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.cap24_lane_canonical_price_provenance_compose_v1 import (
    Cap24LaneCanonicalPriceProvenanceComposeError,
    build_n5_lane_canonical_price_provenance_from_cap24_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def _bound(native: str) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=f"okx:test:{native}",
        venue_native_id=native,
        universe_snapshot_id="u1",
        ranking_snapshot_id="r1",
        ranking_integrity_digest="d1",
        selection_id="sel1",
        selection_integrity_digest="sd1",
        selection_state="SELECTED",
    )


def _pair(native: str) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    bound = _bound(native)
    slot = IsolatedLaneSlotV1(
        lane_id="LANE_1",
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root="/tmp/lane",
        universe_snapshot_id="u1",
        ranking_snapshot_id="r1",
        ranking_integrity_digest="d1",
    )
    return slot, bound


def test_build_aligns_native_id_to_cap24_mark_sidecar() -> None:
    native = "SOL-USDT-SWAP"
    by_lane = build_n5_lane_canonical_price_provenance_from_cap24_v1(
        {"LANE_1": _pair(native)},
        {native: "100.5"},
        index_px=99.5,
    )
    prov = by_lane["LANE_1"]
    assert prov.venue_native_id == native
    assert prov.mark_px == 100.5
    assert prov.index_px == 99.5


def test_missing_sidecar_fail_closed() -> None:
    with pytest.raises(Cap24LaneCanonicalPriceProvenanceComposeError, match="SIDEcar_MISSING"):
        build_n5_lane_canonical_price_provenance_from_cap24_v1(
            {"LANE_1": _pair("ETH-USDT-SWAP")},
            {},
            index_px=99.5,
        )

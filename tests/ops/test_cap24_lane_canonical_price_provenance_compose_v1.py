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


@pytest.mark.parametrize("fault", [None, "price", "native", "missing"])
def test_cap24_preserves_original_source_clock_and_checks_value_identity(fault):
    from dataclasses import replace
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    )

    native = "SOL-USDT-SWAP"
    source = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=dict(
            code="0", data=[dict(instId=native, markPx="100.5", idxPx="99.5", ts="1794225600000")]
        ),
        venue_native_id=native,
        mark_acquired_at_utc="2026-11-09T12:00:00Z",
    )
    supplied = {"LANE_1": source}
    if fault == "price":
        supplied["LANE_1"] = replace(source, mark_px=101)
    elif fault == "native":
        supplied["LANE_1"] = replace(source, venue_native_id="ETH-USDT-SWAP")
    elif fault == "missing":
        supplied = {}

    def build():
        return build_n5_lane_canonical_price_provenance_from_cap24_v1(
            {"LANE_1": _pair(native)},
            {native: "100.5"},
            index_px=99.5,
            source_provenance_by_lane=supplied,
        )

    if fault:
        with pytest.raises(Cap24LaneCanonicalPriceProvenanceComposeError):
            build()
    else:
        result = build()["LANE_1"]
        assert result is source
        assert result.require_current_mark_clock_v1(observed_unix=1794225601) == 1794225600

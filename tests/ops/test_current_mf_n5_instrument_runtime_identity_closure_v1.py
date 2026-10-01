"""N≤5 instrument runtime identity closure — D1–D6 invariant tests."""

from __future__ import annotations

import json
import math
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError,
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.c1_fanout_v1 import (
    C1FanoutError,
    resolve_per_lane_c1_payloads_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.compose_v1 import (
    InstrumentRuntimeIdentityClosureError,
    compose_per_lane_n5_identity_closure_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_C1_FANOUT_SHARED_FORBIDDEN,
    FAILURE_C1_INSTRUMENT_MISMATCH,
    FAILURE_C1_LANE_MISSING,
    FAILURE_DUPLICATE_INSTRUMENT_OWNERSHIP,
    FAILURE_LANE_GENERATION_STALE,
    FAILURE_POSITION_SHARED_FORBIDDEN,
    FAILURE_RECONCILIATION_GLOBAL,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    POST_ALLOWED,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lane_generation_v1 import (
    LaneGenerationError,
    ensure_lane_generation_safe_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lifecycle_v1 import (
    LaneLifecycleMode,
    evaluate_lane_lifecycle_for_instrument_v1,
    pin_open_positions_in_membership_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.ownership_v1 import (
    LaneOwnershipError,
    assert_lane_ownership_index_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
    PerLanePositionTruthError,
    resolve_all_lane_position_truths_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    Cap22ProvenanceV1,
    build_membership_context_artifact_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)

ORIGIN_SHA = "89bda2857035ae104e6758eb582c8c892f3237d5"
C1_TS = float(PREVIOUS_C1_VENUE_EVENT_TIME) + 60.0


def _bound(*, lane_id: str, native: str | None = None) -> BoundInstrumentV1:
    nid = native or f"VENUE-{lane_id}"
    return BoundInstrumentV1(
        instrument_id=f"INST-{lane_id}",
        venue_native_id=nid,
        ranking_snapshot_id="rank-shared",
        ranking_integrity_digest="rank-digest-shared",
        universe_snapshot_id="uni-shared",
        selection_id=f"sel-{lane_id}",
        selection_integrity_digest=f"sel-digest-{lane_id}",
        selection_state="SELECTED",
    )


def _pair(tmp_path: Path, lane_id: str, *, native: str | None = None):
    bound = _bound(lane_id=lane_id, native=native)
    root = lane_state_root_for(topology_state_root_base=tmp_path, lane_id=lane_id)
    slot = IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=root,
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    return slot, bound


def _candles(*, inst_id: str, last_ts_ms: int, close: float) -> dict:
    rows = []
    for index in range(8):
        ts = str(last_ts_ms - (7 - index) * 60_000)
        px = f"{close - (7 - index) * 0.5:.4f}"
        rows.append([ts, px, px, px, px, "10", "100", "USDT", "1"])
    return {"code": "0", "instId": inst_id, "data": rows}


def _g17(instrument_id: str, venue_native_id: str) -> object:
    venue = "OKX"
    t0 = float(PREVIOUS_C1_VENUE_EVENT_TIME) - 3600.0
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=venue,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_native_id,
        persistence_path=None,
    )
    for index in range(61):
        sample = MarketSampleIdentityV1(
            venue=venue,
            canonical_instrument_id=instrument_id,
            venue_instrument_id=venue_native_id,
            event_time=EventTimeInstantV1(unix_seconds=t0 + float(index * 60)),
            mark_price=100.0 * math.exp(0.001 * index),
        )
        producer.ingest_finalized_pt1m_mark_sample_v1(
            sample=sample,
            transport=ObservationTransportMetadataV1(receive_time=t0 + index * 60 + 0.5),
        )
    return producer


def _positions_payload(*rows: tuple[str, str, float]) -> dict:
    data = [{"instId": inst, "posSide": side, "pos": str(qty)} for inst, side, qty in rows]
    return {
        "POSITIONS": {"code": "0", "data": data},
        "PENDING": {"code": "0", "data": []},
        "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
    }


def test_authority_pins_unchanged() -> None:
    assert POST_ALLOWED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert N_GT_1_ENABLED is False


def test_i1_i2_ownership_duplicate_instrument() -> None:
    a = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1", bound=_bound(lane_id="LANE_1")
    )
    b = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_2",
        bound=BoundInstrumentV1(
            instrument_id="INST-LANE_1",
            venue_native_id="VENUE-B",
            ranking_snapshot_id="r",
            ranking_integrity_digest="d",
            universe_snapshot_id="u",
            selection_id="s2",
            selection_integrity_digest="sd2",
            selection_state="SELECTED",
        ),
    )
    with pytest.raises(LaneOwnershipError) as exc:
        assert_lane_ownership_index_v1({"LANE_1": a, "LANE_2": b})
    assert exc.value.failure_code == FAILURE_DUPLICATE_INSTRUMENT_OWNERSHIP


def test_d1_shared_c1_multi_native_fail_closed() -> None:
    ids = {
        "LANE_1": OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="A")
        ),
        "LANE_2": OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id="LANE_2", bound=_bound(lane_id="LANE_2", native="B")
        ),
    }
    with pytest.raises(C1FanoutError) as exc:
        resolve_per_lane_c1_payloads_v1(
            identities=ids,
            candles_payload=_candles(inst_id="A", last_ts_ms=int(C1_TS * 1000), close=100.0),
            candles_payload_by_lane=None,
        )
    assert exc.value.failure_code == FAILURE_C1_FANOUT_SHARED_FORBIDDEN


def test_d1_wrong_inst_id_tag_fail_closed() -> None:
    ids = {
        "LANE_1": OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="VENUE-A")
        ),
    }
    with pytest.raises(C1FanoutError) as exc:
        resolve_per_lane_c1_payloads_v1(
            identities=ids,
            candles_payload=_candles(inst_id="VENUE-B", last_ts_ms=int(C1_TS * 1000), close=100.0),
            candles_payload_by_lane=None,
        )
    assert exc.value.failure_code == FAILURE_C1_INSTRUMENT_MISMATCH


def test_d2_per_lane_position_long_flat() -> None:
    ids = {
        "LANE_1": OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="VENUE-A")
        ),
        "LANE_2": OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id="LANE_2", bound=_bound(lane_id="LANE_2", native="VENUE-B")
        ),
    }
    occ = _positions_payload(("VENUE-A", "long", 1.0))
    truths = resolve_all_lane_position_truths_v1(
        identities=ids,
        occupancy_payloads=occ,
        global_venue_flat=True,
        global_existing_position_side=ExistingPositionSide.NONE,
        multi_lane=True,
    )
    assert truths["LANE_1"].existing_position_side == ExistingPositionSide.LONG
    assert truths["LANE_1"].venue_flat is False
    assert truths["LANE_2"].status == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1"


def test_d2_shared_position_multi_native_forbidden(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1", native="VENUE-A"),
        "LANE_2": _pair(tmp_path, "LANE_2", native="VENUE-B"),
    }
    with pytest.raises(InstrumentRuntimeIdentityClosureError) as exc:
        compose_per_lane_n5_identity_closure_v1(
            pairs,
            candles_payload=None,
            candles_payload_by_lane={
                "LANE_1": _candles(inst_id="VENUE-A", last_ts_ms=int(C1_TS * 1000), close=100.0),
                "LANE_2": _candles(inst_id="VENUE-B", last_ts_ms=int(C1_TS * 1000), close=110.0),
            },
            occupancy_payloads=_occupancy_absent(),
            observed_portfolio=None,
            venue_flat=False,
            existing_position_side=ExistingPositionSide.LONG,
            last_finalized_event_ts_unix=C1_TS,
            finalized_closes=(100.0,),
        )
    assert exc.value.failure_code == FAILURE_POSITION_SHARED_FORBIDDEN


def _occupancy_absent() -> dict:
    return {
        "POSITIONS": {"code": "0", "data": []},
        "PENDING": {"code": "0", "data": []},
        "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
    }


def test_d4_lane_generation_purge_on_rebind(tmp_path: Path) -> None:
    lane_root = tmp_path / "LANE_1"
    lane_root.mkdir()
    cursor = lane_root / "current_productive_sidestate_confirmation_cursor_v1.json"
    cursor.write_text('{"instrument_id":"OLD"}', encoding="utf-8")
    ident_a = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="VENUE-A")
    )
    ensure_lane_generation_safe_v1(lane_state_root=lane_root, identity=ident_a)
    ident_b = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1",
        bound=BoundInstrumentV1(
            instrument_id="INST-OTHER",
            venue_native_id="VENUE-Z",
            ranking_snapshot_id="r",
            ranking_integrity_digest="d",
            universe_snapshot_id="u",
            selection_id="s",
            selection_integrity_digest="sd",
            selection_state="SELECTED",
        ),
    )
    ensure_lane_generation_safe_v1(lane_state_root=lane_root, identity=ident_b)
    assert not cursor.is_file()


def test_d5_membership_pin_open_position() -> None:
    prov = Cap22ProvenanceV1.from_dict(
        {
            "ranking_event_time": "2023-11-14T22:13:20Z",
            "ranking_integrity_digest": "65c6ae446d9b55b095f236271329392bd6d8e747caba1b145cd55f7fd49f3a9f",
            "ranking_policy_id": "productive_futures_universe_structural_ranking_v1",
            "ranking_policy_version": "v1",
            "ranking_schema_version": "productive_futures_ranking_snapshot.v1",
            "ranking_snapshot_id": "pfr_evidence_cap22_v1",
            "snapshot_state": "VALID",
            "source_file_sha256": "abc" * 21 + "abcd",
            "source_relative_path": CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
            "top20_candidate_context_limit": 20,
            "universe_snapshot_id": "gfu_21fc493c5de33aca",
        }
    )
    membership = build_membership_context_artifact_v1(
        ordered_instrument_ids=("INST-A",),
        cap22_provenance=prov,
        bootstrap=True,
        prior_membership_reference=None,
    )
    portfolio = PortfolioTruthSnapshotV1(
        positions=(
            PositionTruthV1.from_signed(instrument_id="INST-OPEN", signed_quantity=Decimal("1")),
        )
    )
    pinned = pin_open_positions_in_membership_v1(membership, portfolio=portfolio)
    assert "INST-OPEN" in pinned.ordered_instrument_ids


def test_d5_draining_when_dropped_while_open() -> None:
    pin = evaluate_lane_lifecycle_for_instrument_v1(
        instrument_id="INST-X",
        in_current_membership=False,
        venue_flat=False,
        reconciled=True,
    )
    assert pin.mode == LaneLifecycleMode.DRAINING
    assert pin.retain_in_membership is True


def test_d6_global_stale_fail_closed() -> None:
    pairs = {"LANE_1": _pair(Path("/tmp/unused"), "LANE_1")}
    portfolio = PortfolioTruthSnapshotV1(stale=True)
    with pytest.raises(InstrumentRuntimeIdentityClosureError) as exc:
        compose_per_lane_n5_identity_closure_v1(
            pairs,
            candles_payload=_candles(
                inst_id="VENUE-LANE_1", last_ts_ms=int(C1_TS * 1000), close=100.0
            ),
            candles_payload_by_lane=None,
            occupancy_payloads=_occupancy_absent(),
            observed_portfolio=portfolio,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            last_finalized_event_ts_unix=C1_TS,
            finalized_closes=(100.0,),
        )
    assert exc.value.failure_code == FAILURE_RECONCILIATION_GLOBAL


def test_invoke_two_lanes_distinct_c1(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1", native="VENUE-A"),
        "LANE_2": _pair(tmp_path, "LANE_2", native="VENUE-B"),
    }
    mark = 100.0
    prov_a = build_provenance_from_governed_synthetic_close_mark_and_index_v1(
        venue_native_id="VENUE-A", mark_px=mark, index_px=99.5
    )
    prov_b = build_provenance_from_governed_synthetic_close_mark_and_index_v1(
        venue_native_id="VENUE-B", mark_px=mark + 10.0, index_px=99.5 + 10.0
    )
    results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        pairs,
        origin_main_sha=ORIGIN_SHA,
        cycle_id_prefix="n5-id",
        observed_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME) + 1.0,
        mark_px=mark,
        index_px=99.5,
        bid_px=99.0,
        ask_px=101.0,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0,
        finalized_closes=(98.0, 99.0, 100.0),
        last_finalized_event_ts_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        candles_payload=None,
        candles_payload_by_lane={
            "LANE_1": _candles(inst_id="VENUE-A", last_ts_ms=int(C1_TS * 1000), close=mark),
            "LANE_2": _candles(inst_id="VENUE-B", last_ts_ms=int(C1_TS * 1000), close=mark + 10.0),
        },
        canonical_price_provenance_by_lane={
            "LANE_1": prov_a,
            "LANE_2": prov_b,
        },
        occupancy_payloads=_occupancy_absent(),
        g17_typed_vol_producers={
            "LANE_1": _g17("INST-LANE_1", "VENUE-A"),
            "LANE_2": _g17("INST-LANE_2", "VENUE-B"),
        },
    )
    assert set(results) == {"LANE_1", "LANE_2"}
    assert results["LANE_1"].native_id == "VENUE-A"
    assert results["LANE_2"].native_id == "VENUE-B"


def test_invoke_missing_lane_c1_fail_closed(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1", native="VENUE-A"),
        "LANE_2": _pair(tmp_path, "LANE_2", native="VENUE-B"),
    }
    with pytest.raises(FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError) as exc:
        invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            pairs,
            origin_main_sha=ORIGIN_SHA,
            cycle_id_prefix="n5-id",
            observed_unix=1.0,
            mark_px=100.0,
            index_px=99.5,
            bid_px=99.0,
            ask_px=101.0,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            finalized_closes=(100.0,),
            last_finalized_event_ts_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME),
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            candles_payload=None,
            candles_payload_by_lane={
                "LANE_1": _candles(inst_id="VENUE-A", last_ts_ms=int(C1_TS * 1000), close=100.0),
            },
            canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
                venue_native_id="VENUE-A", mark_px=100.0, index_px=99.5
            ),
        )
    assert exc.value.failure_code == FAILURE_C1_LANE_MISSING


def test_n1_regression_single_lane_shared_c1(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    mark = 100.0
    invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        pairs,
        origin_main_sha=ORIGIN_SHA,
        cycle_id_prefix="n1",
        observed_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME) + 1.0,
        mark_px=mark,
        index_px=99.5,
        bid_px=99.0,
        ask_px=101.0,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0,
        finalized_closes=(98.0, 99.0, 100.0),
        last_finalized_event_ts_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        candles_payload=_candles(inst_id="VENUE-LANE_1", last_ts_ms=int(C1_TS * 1000), close=mark),
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id="VENUE-LANE_1", mark_px=mark, index_px=99.5
        ),
        g17_typed_vol_producers={"LANE_1": _g17("INST-LANE_1", "VENUE-LANE_1")},
    )

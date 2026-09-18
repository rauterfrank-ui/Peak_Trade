"""CURRENT MF N=5 occupied-lane pin consumer-join tests."""

from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
    GovernedCap23PinAdapterError,
    build_governed_cap23_pin_v1,
)
from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.constants_v1 import (
    ADAPTER_MAY_WRITE_CAP23_SELECTION,
    PIN_IS_SELECTION_AUTHORITY,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.constants_v1 import (
    RECOVERY_MODE_RESTART,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
    recover_durable_lane_assignment_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_EMPTY,
    OWNER as TOPOLOGY_OWNER,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    FAILURE_CROSS_UNIVERSE,
    FAILURE_PROVENANCE_MISMATCH,
    IsolatedLaneTopologyError,
    IsolatedLaneTopologyV1,
    build_occupied_lane_pins_v1,
)
from src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_MAPPING_AUTHORITY,
    JOIN_MEMBERSHIP_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_PIN_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    LANE_MAPPING_OWNER,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    PIN_BUILDER_OWNER,
    RECOVERED_CONSUMER_OWNER,
)
from src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.consumer_v1 import (
    consume_occupied_lane_pins_v1,
)
from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.constants_v1 import (
    FORBIDDEN_CALL_GRAPH_TARGETS as RECOVERED_FORBIDDEN_CALL_GRAPH_TARGETS,
    OWNER as RECOVERED_OWNER,
)
from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1 import (
    consume_recovered_isolated_lane_topology_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    build_membership_context_artifact_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import (
    SCHEMA_VERSION as PIN_SCHEMA_VERSION,
    GovernedCap23InstrumentPinV1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
)

REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
JOIN_SOURCE = Path("src/ops/current_mf_n5_occupied_lane_pin_consumer_join_v1/consumer_v1.py")
RECOVERED_SOURCE = Path("src/ops/current_mf_n5_recovered_topology_consumer_join_v1/consumer_v1.py")
JOIN_CONSUME_PATH = (
    "src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.consumer_v1"
    ".consume_recovered_isolated_lane_topology_v1"
)
JOIN_BUILD_PATH = (
    "src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.consumer_v1"
    ".build_occupied_lane_pins_v1"
)
RECOVER_PATH = (
    "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
    ".recover_durable_lane_assignment_v1"
)


def _perp(inst_id: str, *, base: str | None = None) -> dict:
    token = inst_id.split("-", 1)[0]
    cc = base or token
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": cc,
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": cc,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{cc}-USDT",
        "expTime": "",
    }


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _ranking(rows: list[dict], *, source_event: str = SOURCE_EVENT) -> dict:
    mark_ids = [r["instId"] for r in rows]
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=source_event,
    ).snapshot.to_dict()
    return produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot.to_dict()


def _five_ranking() -> dict:
    return _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("LINK-USDT-SWAP", base="LINK"),
            _perp("APT-USDT-SWAP", base="APT"),
        ]
    )


def _row(ranking: dict, native: str) -> dict:
    return next(c for c in ranking["ranked_candidates"] if c["venue_native_id"] == native)


def _cid(ranking: dict, native: str) -> str:
    return str(_row(ranking, native)["canonical_instrument_id"])


def _membership(ranking: dict, instruments: list[str], *, bootstrap: bool = True, prior=None):
    provenance = Cap22ProvenanceV1(
        ranking_snapshot_id=str(ranking["ranking_snapshot_id"]),
        ranking_schema_version=str(ranking["schema_version"]),
        ranking_integrity_digest=str(ranking["integrity_digest"]),
        ranking_event_time=str(ranking["event_time"]),
        universe_snapshot_id=str(ranking["universe_snapshot_id"]),
        ranking_policy_id=str(ranking["ranking_policy_id"]),
        ranking_policy_version=str(ranking["ranking_policy_version"]),
        source_relative_path="tests/ops/synthetic_membership_provenance",
        source_file_sha256="ab" * 32,
        snapshot_state=str(ranking["snapshot_state"]),
        top20_candidate_context_limit=int(ranking["top20_candidate_context_limit"]),
    )
    return build_membership_context_artifact_v1(
        ordered_instrument_ids=instruments,
        cap22_provenance=provenance,
        bootstrap=bootstrap,
        prior_membership_reference=prior,
    )


def _held_writer(tmp_path: Path) -> DurableLaneAssignmentSingleWriterV1:
    writer = DurableLaneAssignmentSingleWriterV1(state_root=checkpoint_root_for(tmp_path))
    writer.acquire()
    return writer


def _join(ranking: dict, instruments: list[str], tmp_path: Path, *, writer, prior=None):
    bootstrap = prior is None
    membership = _membership(
        ranking,
        instruments,
        bootstrap=bootstrap,
        prior=None if prior is None else prior.membership_instance_id,
    )
    return consume_occupied_lane_pins_v1(
        membership=membership,
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        writer=writer,
    )


def test_authority_signature_and_writer_bounds() -> None:
    assert OWNER == "ops.current_mf_n5_occupied_lane_pin_consumer_join_v1"
    assert LANE_MAPPING_OWNER == TOPOLOGY_OWNER
    assert PIN_BUILDER_OWNER == TOPOLOGY_OWNER
    assert RECOVERED_CONSUMER_OWNER == RECOVERED_OWNER
    assert JOIN_RANKING_AUTHORITY is False
    assert JOIN_MEMBERSHIP_AUTHORITY is False
    assert JOIN_MAPPING_AUTHORITY is False
    assert JOIN_PERSISTENCE_AUTHORITY is False
    assert JOIN_PIN_AUTHORITY is False
    assert JOIN_CAP23_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert PARALLEL_AUTHORITY_CREATED is False
    assert CROSS_UNIVERSE_SELECTION is False
    assert CROSS_UNIVERSE_PIN is False
    assert CROSS_UNIVERSE_REPLACEMENT is False
    assert CROSS_UNIVERSE_FALLBACK is False
    assert CROSS_UNIVERSE_CANDIDATE_BORROWING is False
    assert CROSS_UNIVERSE_RERANKING is False
    assert MULTI_UNIVERSE_MERGE is False
    assert INSTRUMENT_ID_ALONE_SUFFICIENT is False
    assert MF_PRODUCTIVE_JOIN is False
    assert FIVE_LANE_RUNTIME_CREATED is False
    assert FIVE_LANE_CONTINUOUS_HOST_JOIN is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert HOST_JOIN is False
    assert MF_SINGLE_EGRESS_REWIRED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CAP23_CHANGE_REQUIRED is False
    assert CAP24_CHANGE_REQUIRED is False
    assert MASTER_V2_CHANGE_REQUIRED is False
    assert DOUBLE_PLAY_CHANGE_REQUIRED is False
    assert MAX_POSITIONS_EFFECTIVE == CAP23_MAX_POSITIONS == CAP24_MAX_POSITIONS == 1
    join_sig = inspect.signature(consume_occupied_lane_pins_v1)
    consume_sig = inspect.signature(consume_recovered_isolated_lane_topology_v1)
    assert list(join_sig.parameters) == list(consume_sig.parameters)
    assert list(join_sig.parameters) == [
        "membership",
        "ranking_snapshot",
        "topology_state_root_base",
        "writer",
    ]
    assert "prior_topology" not in join_sig.parameters
    assert "recovery_mode" not in join_sig.parameters
    assert "topology" not in join_sig.parameters
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    assert "writer.acquire" not in source
    assert "writer.release" not in source
    assert "consume_recovered_isolated_lane_topology_v1" in source
    assert "build_occupied_lane_pins_v1" in source
    recovered_source = RECOVERED_SOURCE.read_text(encoding="utf-8")
    assert "build_occupied_lane_pins_v1" in RECOVERED_FORBIDDEN_CALL_GRAPH_TARGETS
    assert "build_occupied_lane_pins_v1" not in recovered_source


def test_exact_6595_return_identity_passed_to_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    consume_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
    build_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
    real_consume = consume_recovered_isolated_lane_topology_v1
    real_build = build_occupied_lane_pins_v1

    def _spy_consume(**kwargs):
        result = real_consume(**kwargs)
        consume_holder["obj"] = result
        return result

    def _spy_build(topology, *, ranking_snapshot):
        build_holder["obj"] = topology
        return real_build(topology, ranking_snapshot=ranking_snapshot)

    monkeypatch.setattr(JOIN_CONSUME_PATH, _spy_consume)
    monkeypatch.setattr(JOIN_BUILD_PATH, _spy_build)
    writer = _held_writer(tmp_path)
    try:
        _join(ranking, [a, b], tmp_path, writer=writer)
    finally:
        writer.release()
    assert consume_holder["obj"] is not None
    assert build_holder["obj"] is consume_holder["obj"]


def test_exact_current_ranking_object_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    consume_rank: dict[str, object] = {}
    build_rank: dict[str, object] = {}
    real_consume = consume_recovered_isolated_lane_topology_v1
    real_build = build_occupied_lane_pins_v1

    def _spy_consume(**kwargs):
        consume_rank["obj"] = kwargs["ranking_snapshot"]
        return real_consume(**kwargs)

    def _spy_build(topology, *, ranking_snapshot):
        build_rank["obj"] = ranking_snapshot
        return real_build(topology, ranking_snapshot=ranking_snapshot)

    monkeypatch.setattr(JOIN_CONSUME_PATH, _spy_consume)
    monkeypatch.setattr(JOIN_BUILD_PATH, _spy_build)
    writer = _held_writer(tmp_path)
    try:
        consume_occupied_lane_pins_v1(
            membership=_membership(ranking, [a]),
            ranking_snapshot=ranking,
            topology_state_root_base=tmp_path,
            writer=writer,
        )
    finally:
        writer.release()
    assert consume_rank["obj"] is ranking
    assert build_rank["obj"] is ranking
    assert build_rank["obj"] is consume_rank["obj"]


def test_restart_ranking_advance_cannot_bypass_current_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    recovered_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
    consume_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
    build_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
    real_recover = recover_durable_lane_assignment_v1
    real_consume = consume_recovered_isolated_lane_topology_v1
    real_build = build_occupied_lane_pins_v1

    def _spy_recover(**kwargs):
        result = real_recover(**kwargs)
        recovered_holder["obj"] = result
        return result

    def _spy_consume(**kwargs):
        result = real_consume(**kwargs)
        consume_holder["obj"] = result
        return result

    def _spy_build(topology, *, ranking_snapshot):
        build_holder["obj"] = topology
        build_holder["ranking"] = ranking_snapshot
        return real_build(topology, ranking_snapshot=ranking_snapshot)

    monkeypatch.setattr(RECOVER_PATH, _spy_recover)
    monkeypatch.setattr(JOIN_CONSUME_PATH, _spy_consume)
    monkeypatch.setattr(JOIN_BUILD_PATH, _spy_build)
    writer = _held_writer(tmp_path)
    try:
        first_pins = _join(ranking, [a, b], tmp_path, writer=writer)
        first_topology = consume_holder["obj"]
        assert first_topology is not None
        advanced = dict(ranking)
        advanced["ranking_snapshot_id"] = str(ranking["ranking_snapshot_id"]) + "-advance"
        advanced["integrity_digest"] = "cd" * 32
        recovered_holder.clear()
        consume_holder.clear()
        build_holder.clear()
        second_pins = consume_occupied_lane_pins_v1(
            membership=_membership(
                advanced, [a, b], bootstrap=False, prior=first_topology.membership_instance_id
            ),
            ranking_snapshot=advanced,
            topology_state_root_base=tmp_path,
            writer=writer,
        )
    finally:
        writer.release()
    assert recovered_holder["obj"] is not None
    assert consume_holder["obj"] is not None
    assert build_holder["obj"] is consume_holder["obj"]
    assert build_holder["obj"] is not recovered_holder["obj"]
    assert build_holder["ranking"] is advanced
    assert consume_holder["obj"].ranking_snapshot_id == advanced["ranking_snapshot_id"]
    assert recovered_holder["obj"].ranking_snapshot_id == ranking["ranking_snapshot_id"]
    assert {lane_id: pin.ranking_snapshot_id for lane_id, pin in second_pins.items()} == {
        lane_id: advanced["ranking_snapshot_id"] for lane_id in first_pins
    }
    assert set(second_pins) == set(first_pins) == {"LANE_1", "LANE_2"}


def test_occupied_slots_produce_governed_pins_only(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    writer = _held_writer(tmp_path)
    try:
        pins = _join(ranking, [a, b], tmp_path, writer=writer)
        topology = recover_durable_lane_assignment_v1(
            topology_state_root_base=tmp_path,
            recovery_mode=RECOVERY_MODE_RESTART,
        )
    finally:
        writer.release()
    assert topology is not None
    assert set(pins) == {"LANE_1", "LANE_2"}
    for lane_id, pin in pins.items():
        slot = next(item for item in topology.slots if item.lane_id == lane_id)
        assert isinstance(pin, GovernedCap23InstrumentPinV1)
        assert pin.schema_version == PIN_SCHEMA_VERSION
        assert pin.canonical_instrument_id == slot.canonical_instrument_id
        assert pin.lane_state_root == slot.lane_state_root
        assert pin.universe_snapshot_id == ranking["universe_snapshot_id"]
        assert pin.ranking_snapshot_id == ranking["ranking_snapshot_id"]
        assert pin.ranking_integrity_digest == ranking["integrity_digest"]
        assert pin.pin_is_selection_authority is PIN_IS_SELECTION_AUTHORITY is False
        assert pin.adapter_may_write_cap23_selection is ADAPTER_MAY_WRITE_CAP23_SELECTION is False


def test_empty_slots_do_not_acquire_pins_and_all_empty_is_empty_map(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    writer = _held_writer(tmp_path)
    try:
        pins = _join(ranking, [a, b], tmp_path, writer=writer)
        topology = recover_durable_lane_assignment_v1(
            topology_state_root_base=tmp_path,
            recovery_mode=RECOVERY_MODE_RESTART,
        )
    finally:
        writer.release()
    assert topology is not None
    assert set(pins) == {"LANE_1", "LANE_2"}
    assert "LANE_3" not in pins
    assert "LANE_4" not in pins
    assert "LANE_5" not in pins
    empty_ids = {slot.lane_id for slot in topology.slots if slot.occupancy == OCCUPANCY_EMPTY}
    assert empty_ids == {"LANE_3", "LANE_4", "LANE_5"}
    assert set(LANE_IDS) - set(pins) == empty_ids
    assert len(pins) == topology.occupied_count

    empty_root = tmp_path / "empty"
    empty_writer = _held_writer(empty_root)
    try:
        empty_pins = _join(ranking, [], empty_root, writer=empty_writer)
    finally:
        empty_writer.release()
    assert empty_pins == {}


def test_universe_ranking_digest_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    real_consume = consume_recovered_isolated_lane_topology_v1

    def _foreign_universe(**kwargs):
        result = real_consume(**kwargs)
        return replace(result, universe_snapshot_id="foreign-universe")

    monkeypatch.setattr(JOIN_CONSUME_PATH, _foreign_universe)
    writer = _held_writer(tmp_path)
    try:
        with pytest.raises(IsolatedLaneTopologyError) as universe_exc:
            _join(ranking, [a], tmp_path, writer=writer)
        assert universe_exc.value.failure_code == FAILURE_CROSS_UNIVERSE
    finally:
        writer.release()

    digest_root = tmp_path / "digest"

    def _foreign_ranking(**kwargs):
        result = real_consume(**kwargs)
        return replace(result, ranking_snapshot_id="foreign-ranking")

    monkeypatch.setattr(JOIN_CONSUME_PATH, _foreign_ranking)
    digest_writer = _held_writer(digest_root)
    try:
        with pytest.raises(IsolatedLaneTopologyError) as ranking_exc:
            _join(ranking, [a], digest_root, writer=digest_writer)
        assert ranking_exc.value.failure_code == FAILURE_PROVENANCE_MISMATCH
    finally:
        digest_writer.release()


def test_no_cap23_produce_or_persist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "produce_single_selected_future_v1",
        "produce_from_ranking_state_root_v1",
        "persist_selection_bundle_atomic_v1",
    ):
        assert forbidden not in source
    fired: list[str] = []

    def _boom(*_args, **_kwargs):
        fired.append("cap23")
        raise AssertionError("Cap23 producer must not run")

    monkeypatch.setattr(
        "src.ops.single_selected_future_policy_v1.selection_v1.produce_single_selected_future_v1",
        _boom,
    )
    monkeypatch.setattr(
        "src.ops.single_selected_future_policy_v1.producer_v1.produce_from_ranking_state_root_v1",
        _boom,
    )
    monkeypatch.setattr(
        "src.ops.single_selected_future_policy_v1.persistence_v1.persist_selection_bundle_atomic_v1",
        _boom,
    )
    writer = _held_writer(tmp_path)
    try:
        pins = _join(ranking, [a], tmp_path, writer=writer)
    finally:
        writer.release()
    assert fired == []
    assert set(pins) == {"LANE_1"}


def test_complete_forbidden_call_graph() -> None:
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    expected = {
        "apply_isolated_lane_topology_v1",
        "recover_durable_lane_assignment_v1",
        "persist_durable_lane_assignment_v1",
        "produce_single_selected_future_v1",
        "produce_from_ranking_state_root_v1",
        "run_single_selected_future_policy_v1",
        "persist_selection_bundle_atomic_v1",
        "_pick_top_eligible",
        "run_single_selected_future_runtime_binding_gate_v1",
        "mf_canonical_single_egress_authority_handoff_contract_v1",
        "mf_membership_selector_and_rotation_runtime_contract_v1",
        "master_v2",
        "double_play",
        "execution",
        "top_n_active_set",
    }
    assert FORBIDDEN_CALL_GRAPH_TARGETS == expected
    for forbidden in expected:
        assert forbidden not in source
    assert HOST_JOIN is False
    assert MF_SINGLE_EGRESS_REWIRED is False
    assert MF_PRODUCTIVE_JOIN is False
    assert FIVE_LANE_RUNTIME_CREATED is False
    assert FIVE_LANE_CONTINUOUS_HOST_JOIN is False


def test_builder_and_adapter_failure_propagates_without_partial_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")

    def _fail_second(topology, *, ranking_snapshot):
        occupied = topology.occupied_slots()
        assert len(occupied) >= 2
        first = occupied[0]
        first_pin = build_governed_cap23_pin_v1(
            canonical_instrument_id=str(first.canonical_instrument_id),
            ranking_snapshot=ranking_snapshot,
            lane_state_root=first.lane_state_root,
        )
        assert isinstance(first_pin, GovernedCap23InstrumentPinV1)
        raise IsolatedLaneTopologyError(FAILURE_PROVENANCE_MISMATCH, "forced_second_lane")

    monkeypatch.setattr(JOIN_BUILD_PATH, _fail_second)
    writer = _held_writer(tmp_path)
    try:
        with pytest.raises(IsolatedLaneTopologyError) as builder_exc:
            result = _join(ranking, [a, b], tmp_path, writer=writer)
            raise AssertionError(f"partial map returned:{result!r}")
        assert builder_exc.value.failure_code == FAILURE_PROVENANCE_MISMATCH
        assert builder_exc.value.detail == "forced_second_lane"
    finally:
        writer.release()

    monkeypatch.setattr(JOIN_BUILD_PATH, build_occupied_lane_pins_v1)
    ineligible = dict(ranking)
    ineligible["ranked_candidates"] = [
        dict(row, eligibility_status="INELIGIBLE")
        if str(row.get("canonical_instrument_id") or "") == a
        else dict(row)
        for row in ranking["ranked_candidates"]
    ]
    adapter_root = tmp_path / "adapter"
    adapter_writer = _held_writer(adapter_root)
    try:
        with pytest.raises(GovernedCap23PinAdapterError) as adapter_exc:
            result = _join(ineligible, [a], adapter_root, writer=adapter_writer)
            raise AssertionError(f"partial map returned:{result!r}")
        assert (
            adapter_exc.value.failure_code
            == SelectionFailureCodeV1.GOVERNED_PIN_CANDIDATE_INELIGIBLE.value
        )
    finally:
        adapter_writer.release()

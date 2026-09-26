"""CURRENT MF N=5 Ranking-domain occupied-lane Cap23 N=1 produce-join tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

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
    OWNER as TOPOLOGY_OWNER,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyError,
    lane_state_root_for,
)
from src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.constants_v1 import (
    OWNER as PIN_CONSUMER_OWNER,
)
from src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.consumer_v1 import (
    consume_occupied_lane_pins_v1,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP23_SELECTION_OWNER,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FAILURE_CAP23_SELECTION_MISSING,
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
    PIN_CONSUMER_OWNER as JOIN_PIN_CONSUMER_OWNER,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.produce_join_v1 import (
    RankingDomainOccupiedLaneCap23ProduceJoinError,
    produce_occupied_lane_cap23_n1_selections_v1,
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
    OWNER as CAP23_OWNER,
    SELECTION_FILENAME,
    STATE_NO_SELECTION,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)


REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
JOIN_SOURCE = Path(
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/produce_join_v1.py"
)
JOIN_CONSUME_PATH = (
    "src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1"
    ".produce_join_v1.consume_occupied_lane_pins_v1"
)
JOIN_RUN_PATH = (
    "src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1"
    ".produce_join_v1.run_single_selected_future_policy_v1"
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
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(uni),
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


def _join(
    ranking: dict,
    instruments: list[str],
    tmp_path: Path,
    *,
    writer,
    prior=None,
    observed_unix: float = OBSERVED_UNIX,
):
    bootstrap = prior is None
    membership = _membership(
        ranking,
        instruments,
        bootstrap=bootstrap,
        prior=None if prior is None else prior,
    )
    return produce_occupied_lane_cap23_n1_selections_v1(
        membership=membership,
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        writer=writer,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=observed_unix,
    )


def _selection_files(root: Path) -> list[Path]:
    return sorted(root.rglob(SELECTION_FILENAME))


def test_authority_signature_and_writer_bounds() -> None:
    assert OWNER == "ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1"
    assert LANE_MAPPING_OWNER == TOPOLOGY_OWNER
    assert JOIN_PIN_CONSUMER_OWNER == PIN_CONSUMER_OWNER
    assert CAP23_SELECTION_OWNER == CAP23_OWNER
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
    join_sig = inspect.signature(produce_occupied_lane_cap23_n1_selections_v1)
    consume_sig = inspect.signature(consume_occupied_lane_pins_v1)
    assert list(join_sig.parameters)[:4] == list(consume_sig.parameters)
    assert list(join_sig.parameters) == [
        "membership",
        "ranking_snapshot",
        "topology_state_root_base",
        "writer",
        "repository_sha",
        "producer_observed_at_unix",
    ]
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    assert "writer.acquire" not in source
    assert "writer.release" not in source
    assert "consume_occupied_lane_pins_v1" in source
    assert "run_single_selected_future_policy_v1" in source


def test_t1_empty_occupied_is_empty_map_without_cap23(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    fired: list[str] = []

    def _boom(*_args, **_kwargs):
        fired.append("cap23")
        raise AssertionError("Cap23 must not run for empty occupied topology")

    monkeypatch.setattr(JOIN_RUN_PATH, _boom)
    writer = _held_writer(tmp_path)
    try:
        result = _join(ranking, [], tmp_path, writer=writer)
    finally:
        writer.release()
    assert result == {}
    assert fired == []
    assert _selection_files(tmp_path) == []


def test_t2_one_occupied_isolated_cap23_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    calls: list[Path] = []
    real_run = run_single_selected_future_policy_v1

    def _spy(**kwargs):
        calls.append(Path(kwargs["state_root"]))
        assert kwargs["governed_pin"] is not None
        assert kwargs["load_previous_from_state"] is True
        assert kwargs["ranking_snapshot"] is ranking
        return real_run(**kwargs)

    monkeypatch.setattr(JOIN_RUN_PATH, _spy)
    writer = _held_writer(tmp_path)
    try:
        result = _join(ranking, [ada], tmp_path, writer=writer)
        expected_root = Path(
            lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1")
        )
    finally:
        writer.release()
    assert list(result) == ["LANE_1"]
    selection = result["LANE_1"]
    assert isinstance(selection, SingleSelectedFutureSelectionV1)
    assert selection.state == STATE_SELECTED_ACTIVE
    assert selection.instrument_id == ada
    assert selection.venue_native_id == "ADA-USDT-SWAP"
    assert selection.max_positions_effective == 1
    assert selection.selected_future_count == 1
    assert calls == [expected_root]
    loaded = load_and_validate_selection_v1(expected_root)
    assert loaded.ok is True
    assert loaded.selection is not None
    assert loaded.selection.to_dict() == selection.to_dict()
    assert _selection_files(tmp_path) == [expected_root / SELECTION_FILENAME]


def test_t3_five_occupied_isolated_n1_calls(tmp_path: Path) -> None:
    ranking = _five_ranking()
    natives = ["ADA-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    instruments = [_cid(ranking, native) for native in natives]
    writer = _held_writer(tmp_path)
    try:
        result = _join(ranking, instruments, tmp_path, writer=writer)
    finally:
        writer.release()
    assert list(result) == list(LANE_IDS)
    roots = [
        Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id=lane_id))
        for lane_id in LANE_IDS
    ]
    assert len(set(str(root) for root in roots)) == 5
    for lane_id, native, instrument_id, root in zip(LANE_IDS, natives, instruments, roots):
        selection = result[lane_id]
        assert isinstance(selection, SingleSelectedFutureSelectionV1)
        assert selection.instrument_id == instrument_id
        assert selection.venue_native_id == native
        loaded = load_and_validate_selection_v1(root)
        assert loaded.ok is True
        assert loaded.selection is not None
        assert loaded.selection.instrument_id == instrument_id
        assert (
            loaded.selection.integrity_digest != result[LANE_IDS[0]].integrity_digest
            or lane_id == "LANE_1"
        )


def test_t4_t5_t7_pin_identity_order_and_hysteresis(tmp_path: Path) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    sol = _cid(ranking, "SOL-USDT-SWAP")
    writer = _held_writer(tmp_path)
    try:
        first = _join(ranking, [ada], tmp_path, writer=writer)
        topology = recover_durable_lane_assignment_v1(
            topology_state_root_base=tmp_path,
            recovery_mode=RECOVERY_MODE_RESTART,
        )
        assert topology is not None
        second = _join(
            ranking,
            [sol],
            tmp_path,
            writer=writer,
            prior=topology.membership_instance_id,
            observed_unix=OBSERVED_UNIX + 60.0,
        )
        independent = produce_single_selected_future_v1(
            ranking_snapshot=ranking,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX + 60.0,
            previous_selection=first["LANE_1"],
            governed_pin=consume_occupied_lane_pins_v1(
                membership=_membership(
                    ranking,
                    [sol],
                    bootstrap=False,
                    prior=topology.membership_instance_id,
                ),
                ranking_snapshot=ranking,
                topology_state_root_base=tmp_path,
                writer=writer,
            )["LANE_1"],
            lane_state_root=lane_state_root_for(
                topology_state_root_base=tmp_path,
                lane_id="LANE_1",
            ),
        )
    finally:
        writer.release()
    assert list(first) == ["LANE_1"]
    assert first["LANE_1"].venue_native_id == "ADA-USDT-SWAP"
    assert list(second) == ["LANE_1"]
    assert second["LANE_1"].venue_native_id == "ADA-USDT-SWAP"
    assert SelectionFailureCodeV1.WITHIN_MIN_HOLDING_PERIOD.value in second["LANE_1"].reason_codes
    assert independent.selection.venue_native_id == "ADA-USDT-SWAP"
    assert independent.selection.instrument_id == second["LANE_1"].instrument_id


def test_t6_cross_lane_persistence_isolation(tmp_path: Path) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    eth = _cid(ranking, "ETH-USDT-SWAP")
    writer = _held_writer(tmp_path)
    try:
        result = _join(ranking, [ada, eth], tmp_path, writer=writer)
    finally:
        writer.release()
    assert list(result) == ["LANE_1", "LANE_2"]
    lane1 = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1"))
    lane2 = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_2"))
    loaded1 = load_and_validate_selection_v1(lane1)
    loaded2 = load_and_validate_selection_v1(lane2)
    assert loaded1.selection is not None
    assert loaded2.selection is not None
    assert loaded1.selection.instrument_id == ada
    assert loaded2.selection.instrument_id == eth
    assert loaded1.selection.integrity_digest != loaded2.selection.integrity_digest
    assert loaded2.selection.previous_instrument_id != ada
    empty3 = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_3"))
    assert not (empty3 / SELECTION_FILENAME).is_file()


def test_t8_no_selection_continues_and_missing_selection_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    eth = _cid(ranking, "ETH-USDT-SWAP")
    deny = produce_single_selected_future_v1(
        ranking_snapshot=None,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert deny.selection.state == STATE_NO_SELECTION
    real_run = run_single_selected_future_policy_v1
    calls: list[str] = []

    def _deny_first(**kwargs):
        lane = Path(kwargs["state_root"]).name
        calls.append(lane)
        if lane == "LANE_1":
            return {
                "ok": False,
                "hard_stop": True,
                "failure_codes": deny.failure_codes,
                "selection": deny.selection.to_dict(),
            }
        return real_run(**kwargs)

    monkeypatch.setattr(JOIN_RUN_PATH, _deny_first)
    writer = _held_writer(tmp_path)
    try:
        continued = _join(ranking, [ada, eth], tmp_path, writer=writer)
    finally:
        writer.release()
    assert list(continued) == ["LANE_1", "LANE_2"]
    assert continued["LANE_1"].state == STATE_NO_SELECTION
    assert continued["LANE_2"].venue_native_id == "ETH-USDT-SWAP"
    assert calls == ["LANE_1", "LANE_2"]

    missing_root = tmp_path / "missing"
    calls.clear()

    def _none_second(**kwargs):
        lane = Path(kwargs["state_root"]).name
        calls.append(lane)
        if lane == "LANE_2":
            return {
                "ok": False,
                "hard_stop": True,
                "failure_codes": (SelectionFailureCodeV1.DUPLICATE_SELECTION_WRITER.value,),
                "selection": None,
            }
        return real_run(**kwargs)

    monkeypatch.setattr(JOIN_RUN_PATH, _none_second)
    missing_writer = _held_writer(missing_root)
    try:
        with pytest.raises(RankingDomainOccupiedLaneCap23ProduceJoinError) as missing_exc:
            result = _join(ranking, [ada, eth], missing_root, writer=missing_writer)
            raise AssertionError(f"partial map returned:{result!r}")
        assert missing_exc.value.failure_code == FAILURE_CAP23_SELECTION_MISSING
        lane1 = Path(lane_state_root_for(topology_state_root_base=missing_root, lane_id="LANE_1"))
        loaded = load_and_validate_selection_v1(lane1)
        assert loaded.ok is True
        assert loaded.selection is not None
        assert loaded.selection.instrument_id == ada
        lane2 = Path(lane_state_root_for(topology_state_root_base=missing_root, lane_id="LANE_2"))
        assert not (lane2 / SELECTION_FILENAME).is_file()
    finally:
        missing_writer.release()
    assert calls == ["LANE_1", "LANE_2"]


def test_t8_pin_consume_exception_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")

    def _boom(**_kwargs):
        raise IsolatedLaneTopologyError("PIN_CONSUME_FORCED", "propagate")

    monkeypatch.setattr(JOIN_CONSUME_PATH, _boom)
    writer = _held_writer(tmp_path)
    try:
        with pytest.raises(IsolatedLaneTopologyError) as exc:
            result = _join(ranking, [ada], tmp_path, writer=writer)
            raise AssertionError(f"partial map returned:{result!r}")
        assert exc.value.failure_code == "PIN_CONSUME_FORCED"
    finally:
        writer.release()
    assert _selection_files(tmp_path) == []


def test_t9_t10_t11_t12_forbidden_surfaces_and_flags() -> None:
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    expected = {
        "apply_isolated_lane_topology_v1",
        "recover_durable_lane_assignment_v1",
        "persist_durable_lane_assignment_v1",
        "produce_single_selected_future_v1",
        "produce_from_ranking_state_root_v1",
        "persist_selection_bundle_atomic_v1",
        "_pick_top_eligible",
        "run_single_selected_future_runtime_binding_gate_v1",
        "BoundInstrumentV1",
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
    assert JOIN_CAP23_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert CAP23_SELECTION_OWNER == "ops.single_selected_future_policy_v1"
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert FIVE_LANE_RUNTIME_CREATED is False
    assert FIVE_LANE_CONTINUOUS_HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False

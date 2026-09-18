"""CURRENT MF N=5 recovered topology consumer-join tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.constants_v1 import (
    CHECKPOINT_FILENAME,
    COMMIT_MARKER_FILENAME,
    OWNER as PERSISTENCE_OWNER,
    RECOVERY_MODE_BOOTSTRAP,
    RECOVERY_MODE_RESTART,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    FAILURE_BOOTSTRAP_WITH_PRIOR,
    FAILURE_CROSS_UNIVERSE,
    FAILURE_MALFORMED,
    FAILURE_MISSING_RESTART,
    FAILURE_PARTIAL_WRITE,
    DurableLaneAssignmentPersistenceError,
    checkpoint_root_for,
    persist_durable_lane_assignment_v1,
    prior_durable_lane_assignment_commit_exists,
    recover_durable_lane_assignment_v1,
    write_manifest,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OWNER as TOPOLOGY_OWNER,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyError,
    IsolatedLaneTopologyV1,
    apply_isolated_lane_topology_v1,
)
from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CONSUMER_CAP23_SELECTION_AUTHORITY,
    CONSUMER_CAP24_BINDING_AUTHORITY,
    CONSUMER_EXECUTION_AUTHORITY,
    CONSUMER_MAPPING_AUTHORITY,
    CONSUMER_MEMBERSHIP_AUTHORITY,
    CONSUMER_PERSISTENCE_AUTHORITY,
    CONSUMER_RANKING_AUTHORITY,
    CONSUMER_TRADING_AUTHORITY,
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
    LANE_MAPPING_OWNER,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OWNER,
    PERSISTENCE_OWNER as CONSUMER_PERSISTENCE_OWNER,
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
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
)

REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
CONSUMER_SOURCE = Path("src/ops/current_mf_n5_recovered_topology_consumer_join_v1/consumer_v1.py")
MASTER_V2_SOURCE = Path("src/trading/master_v2/single_lane_confirmation_activation_v1.py")
TOPOLOGY_SOURCE = Path("src/ops/current_mf_n5_isolated_lane_instance_topology_v1/topology_v1.py")
PERSISTENCE_SOURCE = Path(
    "src/ops/current_mf_n5_durable_lane_assignment_persistence_v1/persistence_v1.py"
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


def _other_universe_ranking() -> dict:
    return _ranking(
        [
            _perp("BTC-USDT-SWAP", base="BTC"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("LINK-USDT-SWAP", base="LINK"),
            _perp("APT-USDT-SWAP", base="APT"),
        ],
        source_event="1700000001000",
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


def _consume(ranking: dict, instruments: list[str], tmp_path: Path, *, writer, prior=None):
    bootstrap = prior is None
    membership = _membership(
        ranking,
        instruments,
        bootstrap=bootstrap,
        prior=None if prior is None else prior.membership_instance_id,
    )
    return consume_recovered_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        writer=writer,
    )


def test_authority_bounds_and_forbidden_call_graph() -> None:
    assert OWNER == "ops.current_mf_n5_recovered_topology_consumer_join_v1"
    assert LANE_MAPPING_OWNER == TOPOLOGY_OWNER
    assert CONSUMER_PERSISTENCE_OWNER == PERSISTENCE_OWNER
    assert CONSUMER_RANKING_AUTHORITY is False
    assert CONSUMER_MEMBERSHIP_AUTHORITY is False
    assert CONSUMER_MAPPING_AUTHORITY is False
    assert CONSUMER_PERSISTENCE_AUTHORITY is False
    assert CONSUMER_CAP23_SELECTION_AUTHORITY is False
    assert CONSUMER_CAP24_BINDING_AUTHORITY is False
    assert CONSUMER_TRADING_AUTHORITY is False
    assert CONSUMER_EXECUTION_AUTHORITY is False
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
    sig = inspect.signature(consume_recovered_isolated_lane_topology_v1)
    assert list(sig.parameters) == [
        "membership",
        "ranking_snapshot",
        "topology_state_root_base",
        "writer",
    ]
    assert "prior_topology" not in sig.parameters
    assert "recovery_mode" not in sig.parameters
    source = CONSUMER_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    assert "writer.acquire" not in source
    assert "writer.release" not in source
    assert "apply_isolated_lane_topology_v1" in source
    assert MASTER_V2_SOURCE.is_file()
    assert TOPOLOGY_SOURCE.is_file()
    assert PERSISTENCE_SOURCE.is_file()


def test_bootstrap_prefix_fill_persists_and_recovers_equal(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    writer = _held_writer(tmp_path)
    try:
        topology = _consume(ranking, [a, b, c], tmp_path, writer=writer)
    finally:
        writer.release()
    assert topology.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", c: "LANE_3"}
    recovered = recover_durable_lane_assignment_v1(
        topology_state_root_base=tmp_path,
        recovery_mode=RECOVERY_MODE_RESTART,
    )
    assert recovered is not None
    assert recovered.to_dict() == topology.to_dict()


def test_restart_passes_exact_recovered_object_as_prior_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    writer = _held_writer(tmp_path)
    try:
        first = _consume(ranking, [a, b, c], tmp_path, writer=writer)
        recovered_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
        apply_holder: dict[str, IsolatedLaneTopologyV1 | None] = {}
        recover_mod = (
            "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
            ".recover_durable_lane_assignment_v1"
        )
        apply_mod = (
            "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
            ".apply_isolated_lane_topology_v1"
        )
        real_recover = recover_durable_lane_assignment_v1
        real_apply = apply_isolated_lane_topology_v1

        def _spy_recover(**kwargs):
            result = real_recover(**kwargs)
            recovered_holder["obj"] = result
            return result

        def _spy_apply(**kwargs):
            apply_holder["prior"] = kwargs.get("prior_topology")
            return real_apply(**kwargs)

        monkeypatch.setattr(recover_mod, _spy_recover)
        monkeypatch.setattr(apply_mod, _spy_apply)
        second = _consume(ranking, [a, b, c], tmp_path, writer=writer, prior=first)
    finally:
        writer.release()
    assert recovered_holder["obj"] is not None
    assert apply_holder["prior"] is recovered_holder["obj"]
    assert second.instrument_to_lane() == first.instrument_to_lane()


def test_same_membership_rank_reorder_preserves_lanes(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    writer = _held_writer(tmp_path)
    try:
        first = _consume(ranking, [a, b, c], tmp_path, writer=writer)
        replayed = _consume(ranking, [c, a, b], tmp_path, writer=writer, prior=first)
    finally:
        writer.release()
    assert (
        replayed.instrument_to_lane()
        == first.instrument_to_lane()
        == {
            a: "LANE_1",
            b: "LANE_2",
            c: "LANE_3",
        }
    )


def test_missing_corrupt_partial_restart_has_zero_bootstrap_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    apply_calls: list[str] = []
    real_apply = apply_isolated_lane_topology_v1

    def _spy_apply(**kwargs):
        apply_calls.append("apply")
        return real_apply(**kwargs)

    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".apply_isolated_lane_topology_v1",
        _spy_apply,
    )
    writer = _held_writer(tmp_path)
    try:
        membership = _membership(ranking, [a], bootstrap=False, prior="mca_" + "ab" * 8)
        with pytest.raises(DurableLaneAssignmentPersistenceError) as missing:
            consume_recovered_isolated_lane_topology_v1(
                membership=membership,
                ranking_snapshot=ranking,
                topology_state_root_base=tmp_path,
                writer=writer,
            )
        assert missing.value.failure_code == FAILURE_MISSING_RESTART
        assert apply_calls == []

        first = _consume(ranking, [a], tmp_path, writer=writer)
        apply_calls.clear()
        root = checkpoint_root_for(tmp_path)
        (root / CHECKPOINT_FILENAME).write_text("{", encoding="utf-8")
        write_manifest(root, (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME))
        restart_membership = _membership(
            ranking, [a], bootstrap=False, prior=first.membership_instance_id
        )
        with pytest.raises(DurableLaneAssignmentPersistenceError) as corrupt:
            consume_recovered_isolated_lane_topology_v1(
                membership=restart_membership,
                ranking_snapshot=ranking,
                topology_state_root_base=tmp_path,
                writer=writer,
            )
        assert corrupt.value.failure_code == FAILURE_MALFORMED
        assert apply_calls == []
        with pytest.raises(DurableLaneAssignmentPersistenceError) as bootstrap_exc:
            recover_durable_lane_assignment_v1(
                topology_state_root_base=tmp_path,
                recovery_mode=RECOVERY_MODE_BOOTSTRAP,
            )
        assert bootstrap_exc.value.failure_code == FAILURE_BOOTSTRAP_WITH_PRIOR
    finally:
        writer.release()

    ranking_b = _five_ranking()
    b = _cid(ranking_b, "ETH-USDT-SWAP")
    topology = apply_isolated_lane_topology_v1(
        membership=_membership(ranking_b, [b]),
        ranking_snapshot=ranking_b,
        topology_state_root_base=tmp_path / "partial",
    )
    partial_writer = _held_writer(tmp_path / "partial")
    try:
        with pytest.raises(DurableLaneAssignmentPersistenceError) as partial:
            persist_durable_lane_assignment_v1(
                topology=topology,
                writer=partial_writer,
                simulate_partial_write=True,
            )
        assert partial.value.failure_code == FAILURE_PARTIAL_WRITE
        assert prior_durable_lane_assignment_commit_exists(tmp_path / "partial") is True
        apply_calls.clear()
        monkeypatch.setattr(
            "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
            ".apply_isolated_lane_topology_v1",
            _spy_apply,
        )
        restart_membership = _membership(
            ranking_b, [b], bootstrap=False, prior=topology.membership_instance_id
        )
        with pytest.raises(DurableLaneAssignmentPersistenceError) as restart_partial:
            consume_recovered_isolated_lane_topology_v1(
                membership=restart_membership,
                ranking_snapshot=ranking_b,
                topology_state_root_base=tmp_path / "partial",
                writer=partial_writer,
            )
        assert restart_partial.value.failure_code == FAILURE_MISSING_RESTART
        assert apply_calls == []
    finally:
        partial_writer.release()


def test_bootstrap_versus_commit_presence_disagreement_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    apply_calls: list[str] = []

    def _boom(**_kwargs):
        apply_calls.append("apply")
        raise AssertionError("apply must not run on lifecycle disagreement")

    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".apply_isolated_lane_topology_v1",
        _boom,
    )
    writer = _held_writer(tmp_path)
    try:
        seeded = apply_isolated_lane_topology_v1(
            membership=_membership(ranking, [a]),
            ranking_snapshot=ranking,
            topology_state_root_base=tmp_path,
        )
        persist_durable_lane_assignment_v1(topology=seeded, writer=writer)
        bootstrap_membership = _membership(ranking, [a], bootstrap=True)
        with pytest.raises(DurableLaneAssignmentPersistenceError) as with_prior:
            consume_recovered_isolated_lane_topology_v1(
                membership=bootstrap_membership,
                ranking_snapshot=ranking,
                topology_state_root_base=tmp_path,
                writer=writer,
            )
        assert with_prior.value.failure_code == FAILURE_BOOTSTRAP_WITH_PRIOR
        assert apply_calls == []
    finally:
        writer.release()

    empty = tmp_path / "empty"
    empty.mkdir()
    writer_empty = _held_writer(empty)
    try:
        restart_membership = _membership(
            ranking, [a], bootstrap=False, prior=seeded.membership_instance_id
        )
        with pytest.raises(DurableLaneAssignmentPersistenceError) as missing:
            consume_recovered_isolated_lane_topology_v1(
                membership=restart_membership,
                ranking_snapshot=ranking,
                topology_state_root_base=empty,
                writer=writer_empty,
            )
        assert missing.value.failure_code == FAILURE_MISSING_RESTART
        assert apply_calls == []
    finally:
        writer_empty.release()


def test_cross_universe_fails_during_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    other = _other_universe_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    other_eth = _cid(other, "ETH-USDT-SWAP")
    apply_calls: list[str] = []

    def _boom(**_kwargs):
        apply_calls.append("apply")
        raise AssertionError("apply must not run on cross-universe recover")

    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".apply_isolated_lane_topology_v1",
        _boom,
    )
    writer = _held_writer(tmp_path)
    try:
        first = apply_isolated_lane_topology_v1(
            membership=_membership(ranking, [a]),
            ranking_snapshot=ranking,
            topology_state_root_base=tmp_path,
        )
        persist_durable_lane_assignment_v1(topology=first, writer=writer)
        other_membership = _membership(
            other, [other_eth], bootstrap=False, prior=first.membership_instance_id
        )
        with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
            consume_recovered_isolated_lane_topology_v1(
                membership=other_membership,
                ranking_snapshot=other,
                topology_state_root_base=tmp_path,
                writer=writer,
            )
        assert exc.value.failure_code == FAILURE_CROSS_UNIVERSE
        assert apply_calls == []
    finally:
        writer.release()


def test_same_universe_ranking_advance_omits_current_ranking_expected_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    recover_kwargs: list[dict] = []
    real_recover = recover_durable_lane_assignment_v1

    def _spy_recover(**kwargs):
        recover_kwargs.append(dict(kwargs))
        return real_recover(**kwargs)

    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".recover_durable_lane_assignment_v1",
        _spy_recover,
    )
    writer = _held_writer(tmp_path)
    try:
        first = _consume(ranking, [a, b], tmp_path, writer=writer)
        advanced = dict(ranking)
        advanced["ranking_snapshot_id"] = str(ranking["ranking_snapshot_id"]) + "-advance"
        advanced["integrity_digest"] = "cd" * 32
        assert advanced["universe_snapshot_id"] == ranking["universe_snapshot_id"]
        assert advanced["ranking_snapshot_id"] != ranking["ranking_snapshot_id"]
        recover_kwargs.clear()
        second = consume_recovered_isolated_lane_topology_v1(
            membership=_membership(
                advanced, [a, b], bootstrap=False, prior=first.membership_instance_id
            ),
            ranking_snapshot=advanced,
            topology_state_root_base=tmp_path,
            writer=writer,
        )
    finally:
        writer.release()
    assert len(recover_kwargs) == 1
    restart_call = recover_kwargs[0]
    assert restart_call["recovery_mode"] == RECOVERY_MODE_RESTART
    assert restart_call["expected_universe_snapshot_id"] == ranking["universe_snapshot_id"]
    assert "expected_ranking_snapshot_id" not in restart_call
    assert "expected_ranking_integrity_digest" not in restart_call
    assert second.instrument_to_lane() == first.instrument_to_lane()
    assert second.ranking_snapshot_id == advanced["ranking_snapshot_id"]
    assert second.ranking_integrity_digest == advanced["integrity_digest"]
    assert second.universe_snapshot_id == ranking["universe_snapshot_id"]


def test_forbidden_call_graph_excludes_selection_and_downstream_owners() -> None:
    source = CONSUMER_SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "produce_single_selected_future_v1",
        "_pick_top_eligible",
        "persist_selection_bundle_atomic_v1",
        "run_single_selected_future_runtime_binding_gate_v1",
        "master_v2",
        "double_play",
        "mf_canonical_single_egress_authority_handoff_contract_v1",
        "top_n_active_set",
        "build_occupied_lane_pins_v1",
    ):
        assert forbidden not in source


def test_persist_occurs_only_after_successful_apply_and_recover_does_not_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    order: list[str] = []
    apply_during_recover: list[int] = []
    real_recover = recover_durable_lane_assignment_v1
    real_apply = apply_isolated_lane_topology_v1
    real_persist = persist_durable_lane_assignment_v1
    apply_calls = {"n": 0}

    def _spy_recover(**kwargs):
        before = apply_calls["n"]
        order.append("recover")
        result = real_recover(**kwargs)
        apply_during_recover.append(apply_calls["n"] - before)
        return result

    def _spy_apply(**kwargs):
        apply_calls["n"] += 1
        order.append("apply")
        return real_apply(**kwargs)

    def _spy_persist(**kwargs):
        order.append("persist")
        return real_persist(**kwargs)

    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".recover_durable_lane_assignment_v1",
        _spy_recover,
    )
    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".apply_isolated_lane_topology_v1",
        _spy_apply,
    )
    monkeypatch.setattr(
        "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
        ".persist_durable_lane_assignment_v1",
        _spy_persist,
    )
    writer = _held_writer(tmp_path)
    try:
        _consume(ranking, [a], tmp_path, writer=writer)
        assert order == ["recover", "apply", "persist"]
        assert apply_during_recover == [0]

        order.clear()
        apply_during_recover.clear()
        apply_calls["n"] = 0

        def _fail_apply(**_kwargs):
            apply_calls["n"] += 1
            order.append("apply")
            raise IsolatedLaneTopologyError("LANE_CONSUMER_TEST_APPLY_FAIL", "forced")

        monkeypatch.setattr(
            "src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1"
            ".apply_isolated_lane_topology_v1",
            _fail_apply,
        )
        with pytest.raises(IsolatedLaneTopologyError) as exc:
            consume_recovered_isolated_lane_topology_v1(
                membership=_membership(ranking, [a], bootstrap=False, prior="mca_" + "cd" * 8),
                ranking_snapshot=ranking,
                topology_state_root_base=tmp_path,
                writer=writer,
            )
        assert exc.value.failure_code == "LANE_CONSUMER_TEST_APPLY_FAIL"
        assert order == ["recover", "apply"]
        assert "persist" not in order
        assert apply_during_recover == [0]
    finally:
        writer.release()

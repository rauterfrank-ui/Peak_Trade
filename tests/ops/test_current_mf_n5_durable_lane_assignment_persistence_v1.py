"""CURRENT MF N=5 durable lane-assignment persistence tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CHECKPOINT_FILENAME,
    COMMIT_MARKER_FILENAME,
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
    MULTI_UNIVERSE_MERGE,
    OWNER,
    PERSISTENCE_CAP23_SELECTION_AUTHORITY,
    PERSISTENCE_CAP24_BINDING_AUTHORITY,
    PERSISTENCE_EXECUTION_AUTHORITY,
    PERSISTENCE_LANE_MAPPING_AUTHORITY,
    PERSISTENCE_MEMBERSHIP_AUTHORITY,
    PERSISTENCE_RANKING_AUTHORITY,
    PERSISTENCE_TRADING_AUTHORITY,
    RECOVERY_MODE_BOOTSTRAP,
    RECOVERY_MODE_RESTART,
    SCHEMA_VERSION,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    FAILURE_BOOTSTRAP_WITH_PRIOR,
    FAILURE_CROSS_UNIVERSE,
    FAILURE_INTEGRITY,
    FAILURE_MALFORMED,
    FAILURE_MISSING_RESTART,
    FAILURE_PARTIAL_WRITE,
    FAILURE_PROVENANCE,
    FAILURE_UNSUPPORTED_SCHEMA,
    DurableLaneAssignmentPersistenceError,
    checkpoint_root_for,
    persist_durable_lane_assignment_v1,
    prior_durable_lane_assignment_commit_exists,
    recover_durable_lane_assignment_v1,
    topology_integrity_digest_v1,
    write_manifest,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_EMPTY,
    OCCUPANCY_OCCUPIED,
    OWNER as TOPOLOGY_OWNER,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    FAILURE_CORRUPT_PRIOR,
    FAILURE_DUPLICATE_INSTRUMENT,
    FAILURE_INVALID_LANE_ID,
    apply_isolated_lane_topology_v1,
    isolated_lane_topology_from_dict,
    lane_state_root_for,
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
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)


REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
PERSISTENCE_SOURCE = Path(
    "src/ops/current_mf_n5_durable_lane_assignment_persistence_v1/persistence_v1.py"
)
MASTER_V2_SOURCE = Path("src/trading/master_v2/single_lane_confirmation_activation_v1.py")


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


def _apply(ranking: dict, instruments: list[str], tmp_path: Path, *, prior=None):
    bootstrap = prior is None
    membership = _membership(
        ranking,
        instruments,
        bootstrap=bootstrap,
        prior=None if prior is None else prior.membership_instance_id,
    )
    return apply_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        prior_topology=prior,
    )


def _persist(topology, tmp_path: Path, **kwargs):
    writer = DurableLaneAssignmentSingleWriterV1(state_root=checkpoint_root_for(tmp_path))
    writer.acquire()
    try:
        return persist_durable_lane_assignment_v1(topology=topology, writer=writer, **kwargs)
    finally:
        writer.release()


def _recover(tmp_path: Path, *, mode: str = RECOVERY_MODE_RESTART, **kwargs):
    return recover_durable_lane_assignment_v1(
        topology_state_root_base=tmp_path, recovery_mode=mode, **kwargs
    )


def _seed(tmp_path: Path):
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    topology = _apply(ranking, [a, b, c], tmp_path)
    _persist(topology, tmp_path)
    return ranking, topology, a, b, c


def _write_raw_bundle(
    tmp_path: Path, topology_payload: dict, *, schema_version: str = SCHEMA_VERSION
) -> None:
    root = checkpoint_root_for(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    envelope = {
        "contract_id": "CURRENT_MF_N5_DURABLE_LANE_ASSIGNMENT_PERSISTENCE_CONTRACT_V1",
        "integrity_digest": topology_integrity_digest_v1(topology_payload),
        "lane_mapping_owner": LANE_MAPPING_OWNER,
        "owner": OWNER,
        "schema_version": schema_version,
        "topology": topology_payload,
    }
    marker = {
        "integrity_digest": envelope["integrity_digest"],
        "ranking_integrity_digest": topology_payload["ranking_integrity_digest"],
        "ranking_snapshot_id": topology_payload["ranking_snapshot_id"],
        "schema_version": schema_version,
        "topology_state_root_base": topology_payload["topology_state_root_base"],
        "universe_snapshot_id": topology_payload["universe_snapshot_id"],
    }
    (root / CHECKPOINT_FILENAME).write_text(
        json.dumps(envelope, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (root / COMMIT_MARKER_FILENAME).write_text(
        json.dumps(marker, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    write_manifest(root, (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME))


def test_authority_bounds_and_forbidden_call_graph() -> None:
    assert OWNER == "ops.current_mf_n5_durable_lane_assignment_persistence_v1"
    assert LANE_MAPPING_OWNER == TOPOLOGY_OWNER
    assert PERSISTENCE_RANKING_AUTHORITY is False
    assert PERSISTENCE_MEMBERSHIP_AUTHORITY is False
    assert PERSISTENCE_LANE_MAPPING_AUTHORITY is False
    assert PERSISTENCE_CAP23_SELECTION_AUTHORITY is False
    assert PERSISTENCE_CAP24_BINDING_AUTHORITY is False
    assert PERSISTENCE_TRADING_AUTHORITY is False
    assert PERSISTENCE_EXECUTION_AUTHORITY is False
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
    assert CAP23_CHANGE_REQUIRED is False
    assert CAP24_CHANGE_REQUIRED is False
    assert MASTER_V2_CHANGE_REQUIRED is False
    assert DOUBLE_PLAY_CHANGE_REQUIRED is False
    assert MAX_POSITIONS_EFFECTIVE == CAP23_MAX_POSITIONS == CAP24_MAX_POSITIONS == 1
    source = PERSISTENCE_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    assert MASTER_V2_SOURCE.is_file()


def test_exact_topology_round_trip_preserves_empty_and_occupied_lanes(tmp_path: Path) -> None:
    ranking, topology, a, b, c = _seed(tmp_path)
    recovered = _recover(
        tmp_path,
        expected_universe_snapshot_id=ranking["universe_snapshot_id"],
        expected_ranking_snapshot_id=ranking["ranking_snapshot_id"],
        expected_ranking_integrity_digest=ranking["integrity_digest"],
    )
    assert recovered is not None
    assert recovered.to_dict() == topology.to_dict()
    assert recovered.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", c: "LANE_3"}
    assert [slot.occupancy for slot in recovered.slots] == [
        OCCUPANCY_OCCUPIED,
        OCCUPANCY_OCCUPIED,
        OCCUPANCY_OCCUPIED,
        OCCUPANCY_EMPTY,
        OCCUPANCY_EMPTY,
    ]
    assert recovered.slots[3].canonical_instrument_id is None
    assert recovered.slots[4].canonical_instrument_id is None
    assert recovered.topology_state_root_base == topology.topology_state_root_base
    for lane_id in LANE_IDS:
        assert recovered.slots[int(lane_id[-1]) - 1].lane_state_root == lane_state_root_for(
            topology_state_root_base=tmp_path, lane_id=lane_id
        )


def test_pure_rank_reorder_cannot_alter_recovered_lane_identity(tmp_path: Path) -> None:
    ranking, topology, a, b, c = _seed(tmp_path)
    recovered = _recover(tmp_path)
    assert recovered is not None
    replayed = apply_isolated_lane_topology_v1(
        membership=_membership(
            ranking, [c, a, b], bootstrap=False, prior=recovered.membership_instance_id
        ),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        prior_topology=recovered,
    )
    assert replayed.instrument_to_lane() == topology.instrument_to_lane()
    _persist(replayed, tmp_path)
    again = _recover(tmp_path)
    assert again is not None
    assert again.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", c: "LANE_3"}


def test_universe_identity_preserved_and_wrong_universe_fails_closed(tmp_path: Path) -> None:
    ranking, topology, _a, _b, _c = _seed(tmp_path)
    recovered = _recover(tmp_path, expected_universe_snapshot_id=topology.universe_snapshot_id)
    assert recovered is not None
    assert recovered.universe_snapshot_id == ranking["universe_snapshot_id"]
    other = _other_universe_ranking()
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path, expected_universe_snapshot_id=str(other["universe_snapshot_id"]))
    assert exc.value.failure_code == FAILURE_CROSS_UNIVERSE


def test_provenance_mismatch_fails_closed(tmp_path: Path) -> None:
    _seed(tmp_path)
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path, expected_ranking_snapshot_id="other-ranking")
    assert exc.value.failure_code == FAILURE_PROVENANCE
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path, expected_ranking_integrity_digest="0" * 64)
    assert exc.value.failure_code == FAILURE_PROVENANCE


def test_duplicate_lane_and_instrument_and_over_max_fail_closed(tmp_path: Path) -> None:
    ranking, topology, a, b, c = _seed(tmp_path)
    payload = topology.to_dict()
    payload["slots"][1]["lane_id"] = "LANE_1"
    _write_raw_bundle(tmp_path, payload)
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path)
    assert exc.value.failure_code == FAILURE_INVALID_LANE_ID

    payload = topology.to_dict()
    payload["slots"][1]["canonical_instrument_id"] = a
    _write_raw_bundle(tmp_path, payload)
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path)
    assert exc.value.failure_code == FAILURE_DUPLICATE_INSTRUMENT

    extra = dict(payload["slots"][0])
    extra["lane_id"] = "LANE_6"
    extra["canonical_instrument_id"] = c
    payload = topology.to_dict()
    payload["slots"] = list(payload["slots"]) + [extra]
    _write_raw_bundle(tmp_path, payload)
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path)
    assert exc.value.failure_code == FAILURE_CORRUPT_PRIOR
    assert ranking["universe_snapshot_id"] == topology.universe_snapshot_id
    assert b != a


def test_malformed_unsupported_version_and_integrity_fail_closed(tmp_path: Path) -> None:
    ranking, topology, _a, _b, _c = _seed(tmp_path)
    root = checkpoint_root_for(tmp_path)
    (root / CHECKPOINT_FILENAME).write_text("{not-json", encoding="utf-8")
    write_manifest(root, (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME))
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path)
    assert exc.value.failure_code == FAILURE_MALFORMED

    _write_raw_bundle(tmp_path, topology.to_dict(), schema_version="durable_lane_assignment.v0")
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path)
    assert exc.value.failure_code == FAILURE_UNSUPPORTED_SCHEMA

    _persist(topology, tmp_path)
    raw = json.loads((root / CHECKPOINT_FILENAME).read_text(encoding="utf-8"))
    raw["integrity_digest"] = "0" * 64
    (root / CHECKPOINT_FILENAME).write_text(
        json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    write_manifest(root, (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME))
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path)
    assert exc.value.failure_code == FAILURE_INTEGRITY
    assert ranking["ranking_snapshot_id"] == topology.ranking_snapshot_id


def test_missing_restart_fails_closed_and_does_not_bootstrap(tmp_path: Path) -> None:
    assert prior_durable_lane_assignment_commit_exists(tmp_path) is False
    assert _recover(tmp_path, mode=RECOVERY_MODE_BOOTSTRAP) is None
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _recover(tmp_path, mode=RECOVERY_MODE_RESTART)
    assert exc.value.failure_code == FAILURE_MISSING_RESTART


def test_corrupt_restart_checkpoint_does_not_bootstrap(tmp_path: Path) -> None:
    _seed(tmp_path)
    root = checkpoint_root_for(tmp_path)
    (root / CHECKPOINT_FILENAME).write_text("{", encoding="utf-8")
    write_manifest(root, (CHECKPOINT_FILENAME, COMMIT_MARKER_FILENAME))
    with pytest.raises(DurableLaneAssignmentPersistenceError) as restart_exc:
        _recover(tmp_path, mode=RECOVERY_MODE_RESTART)
    assert restart_exc.value.failure_code == FAILURE_MALFORMED
    with pytest.raises(DurableLaneAssignmentPersistenceError) as bootstrap_exc:
        _recover(tmp_path, mode=RECOVERY_MODE_BOOTSTRAP)
    assert bootstrap_exc.value.failure_code == FAILURE_BOOTSTRAP_WITH_PRIOR


def test_recovery_does_not_run_topology_transition(tmp_path: Path, monkeypatch) -> None:
    ranking, topology, _a, _b, _c = _seed(tmp_path)

    def _boom(**_kwargs):
        raise AssertionError("apply_isolated_lane_topology_v1 must not run during recovery")

    monkeypatch.setattr(
        "src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1.apply_isolated_lane_topology_v1",
        _boom,
    )
    recovered = _recover(tmp_path)
    assert recovered is not None
    assert recovered.to_dict() == topology.to_dict()
    restored = isolated_lane_topology_from_dict(recovered.to_dict())
    assert restored.instrument_to_lane() == topology.instrument_to_lane()
    assert ranking["integrity_digest"] == topology.ranking_integrity_digest


def test_partial_write_fails_closed_and_does_not_bootstrap(tmp_path: Path) -> None:
    ranking = _five_ranking()
    topology = _apply(
        ranking,
        [
            _cid(ranking, "ADA-USDT-SWAP"),
            _cid(ranking, "ETH-USDT-SWAP"),
        ],
        tmp_path,
    )
    with pytest.raises(DurableLaneAssignmentPersistenceError) as exc:
        _persist(topology, tmp_path, simulate_partial_write=True)
    assert exc.value.failure_code == FAILURE_PARTIAL_WRITE
    assert prior_durable_lane_assignment_commit_exists(tmp_path) is True
    with pytest.raises(DurableLaneAssignmentPersistenceError) as restart_exc:
        _recover(tmp_path, mode=RECOVERY_MODE_RESTART)
    assert restart_exc.value.failure_code == FAILURE_MISSING_RESTART
    with pytest.raises(DurableLaneAssignmentPersistenceError) as bootstrap_exc:
        _recover(tmp_path, mode=RECOVERY_MODE_BOOTSTRAP)
    assert bootstrap_exc.value.failure_code == FAILURE_BOOTSTRAP_WITH_PRIOR


def test_checkpoint_replace_keeps_latest_governed_topology(tmp_path: Path) -> None:
    ranking, first, a, b, c = _seed(tmp_path)
    d = _cid(ranking, "LINK-USDT-SWAP")
    second = _apply(ranking, [a, b, d], tmp_path, prior=first)
    assert second.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", d: "LANE_3"}
    _persist(second, tmp_path)
    recovered = _recover(tmp_path)
    assert recovered is not None
    assert recovered.to_dict() == second.to_dict()
    assert recovered.instrument_to_lane() != first.instrument_to_lane()
    assert c not in recovered.instrument_to_lane()

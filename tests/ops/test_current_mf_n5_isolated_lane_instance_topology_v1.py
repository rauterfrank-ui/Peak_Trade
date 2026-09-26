"""CURRENT MF N=5 isolated lane-instance topology tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.constants_v1 import (
    ADAPTER_MAY_WRITE_CAP23_SELECTION,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    LANE_IDS,
    LANE_IDENTITY_ENCODES_RANK,
    LANE_TOPOLOGY_CAP23_SELECTION_AUTHORITY,
    LANE_TOPOLOGY_CAP24_BINDING_AUTHORITY,
    LANE_TOPOLOGY_EXECUTION_AUTHORITY,
    LANE_TOPOLOGY_MEMBERSHIP_AUTHORITY,
    LANE_TOPOLOGY_RANKING_AUTHORITY,
    LANE_TOPOLOGY_TRADING_AUTHORITY,
    MAX_LANE_COUNT,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_UNIVERSE_MERGE,
    OCCUPANCY_EMPTY,
    OCCUPANCY_OCCUPIED,
    PURE_RANK_REORDER_CAUSES_LANE_MOVE,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    FAILURE_CROSS_UNIVERSE,
    FAILURE_DUPLICATE_INSTRUMENT,
    FAILURE_EXTRA_RANKING,
    FAILURE_INSTRUMENT_NOT_IN_RANKING,
    FAILURE_PROVENANCE_MISMATCH,
    FAILURE_RESTART_WITHOUT_PRIOR,
    FAILURE_STATE_ROOT_MISMATCH,
    IsolatedLaneTopologyError,
    apply_isolated_lane_topology_v1,
    build_occupied_lane_pins_v1,
    isolated_lane_topology_from_dict,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    MembershipContextArtifactError,
    build_membership_context_artifact_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
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
TOPOLOGY_SOURCE = Path("src/ops/current_mf_n5_isolated_lane_instance_topology_v1/topology_v1.py")
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


def _ranking(rows: list[dict]) -> dict:
    mark_ids = [r["instId"] for r in rows]
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
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


def _membership(
    ranking: dict,
    instruments: list[str],
    *,
    bootstrap: bool = True,
    prior: str | None = None,
):
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


def _apply(ranking: dict, instruments: list[str], tmp_path: Path, *, prior=None, **kwargs):
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
        **kwargs,
    )


def test_authority_bounds_and_forbidden_call_graph() -> None:
    assert MAX_LANE_COUNT == 5
    assert LANE_IDS == ("LANE_1", "LANE_2", "LANE_3", "LANE_4", "LANE_5")
    assert LANE_IDENTITY_ENCODES_RANK is False
    assert PURE_RANK_REORDER_CAUSES_LANE_MOVE is False
    assert LANE_TOPOLOGY_RANKING_AUTHORITY is False
    assert LANE_TOPOLOGY_MEMBERSHIP_AUTHORITY is False
    assert LANE_TOPOLOGY_CAP23_SELECTION_AUTHORITY is False
    assert LANE_TOPOLOGY_CAP24_BINDING_AUTHORITY is False
    assert LANE_TOPOLOGY_TRADING_AUTHORITY is False
    assert LANE_TOPOLOGY_EXECUTION_AUTHORITY is False
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
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert HOST_JOIN is False
    assert MF_SINGLE_EGRESS_REWIRED is False
    assert MAX_POSITIONS_EFFECTIVE == CAP23_MAX_POSITIONS == CAP24_MAX_POSITIONS == 1
    assert ADAPTER_MAY_WRITE_CAP23_SELECTION is False
    source = TOPOLOGY_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    sig = inspect.signature(apply_isolated_lane_topology_v1)
    assert "SingleSelectedFutureSelectionV1" not in str(sig.return_annotation)
    pin_sig = inspect.signature(build_occupied_lane_pins_v1)
    assert "SingleSelectedFutureSelectionV1" not in str(pin_sig.return_annotation)
    assert MASTER_V2_SOURCE.is_file()


def test_case_a_initial_fill_no_padding(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    topology = _apply(ranking, [a, b, c], tmp_path)
    assert topology.occupied_count == 3
    assert len(topology.slots) == 5
    assert topology.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", c: "LANE_3"}
    assert [slot.occupancy for slot in topology.slots] == [
        OCCUPANCY_OCCUPIED,
        OCCUPANCY_OCCUPIED,
        OCCUPANCY_OCCUPIED,
        OCCUPANCY_EMPTY,
        OCCUPANCY_EMPTY,
    ]
    for slot in topology.empty_slots():
        assert slot.canonical_instrument_id is None


def test_case_b_pure_rank_reorder_retains_lanes(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    first = _apply(ranking, [a, b, c], tmp_path)
    reordered = _apply(ranking, [c, a, b], tmp_path, prior=first)
    assert reordered.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", c: "LANE_3"}
    assert reordered.occupied_count == 3


def test_case_c_one_exit_one_entry_reuses_released_lane(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c, d = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
        _cid(ranking, "LINK-USDT-SWAP"),
    )
    first = _apply(ranking, [a, b, c], tmp_path)
    after = _apply(ranking, [a, b, d], tmp_path, prior=first)
    assert after.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", d: "LANE_3"}
    assert "LANE_3" not in {
        slot.lane_id for slot in after.slots if slot.canonical_instrument_id == c
    }


def test_case_d_shrink_retains_and_releases(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c, d, e = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
        _cid(ranking, "LINK-USDT-SWAP"),
        _cid(ranking, "APT-USDT-SWAP"),
    )
    first = _apply(ranking, [a, b, c, d, e], tmp_path)
    after = _apply(ranking, [a, c, e], tmp_path, prior=first)
    assert after.instrument_to_lane() == {a: "LANE_1", c: "LANE_3", e: "LANE_5"}
    assert after.occupied_count == 3
    assert after.slots[1].occupancy == OCCUPANCY_EMPTY
    assert after.slots[3].occupancy == OCCUPANCY_EMPTY


def test_case_e_grow_fills_lowest_empty(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c, d, e = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
        _cid(ranking, "LINK-USDT-SWAP"),
        _cid(ranking, "APT-USDT-SWAP"),
    )
    first = _apply(ranking, [a, b], tmp_path)
    after = _apply(ranking, [a, b, c, d, e], tmp_path, prior=first)
    assert after.instrument_to_lane() == {
        a: "LANE_1",
        b: "LANE_2",
        c: "LANE_3",
        d: "LANE_4",
        e: "LANE_5",
    }
    assert after.occupied_count == 5


def test_case_f_duplicate_instrument_fails_closed(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    with pytest.raises(MembershipContextArtifactError) as exc:
        _membership(ranking, [a, a])
    assert exc.value.failure_code == "DUPLICATE_INSTRUMENT_ID"
    first = _apply(ranking, [a, _cid(ranking, "ETH-USDT-SWAP")], tmp_path)
    payload = first.to_dict()
    payload["slots"][1]["canonical_instrument_id"] = a
    payload["slots"][1]["occupancy"] = OCCUPANCY_OCCUPIED
    payload["slots"][1]["universe_snapshot_id"] = first.universe_snapshot_id
    payload["slots"][1]["ranking_snapshot_id"] = first.ranking_snapshot_id
    payload["slots"][1]["ranking_integrity_digest"] = first.ranking_integrity_digest
    with pytest.raises(IsolatedLaneTopologyError) as dup:
        isolated_lane_topology_from_dict(payload)
    assert dup.value.failure_code == FAILURE_DUPLICATE_INSTRUMENT


def test_case_g_cross_universe_fails_closed(tmp_path: Path) -> None:
    ranking_a = _five_ranking()
    ranking_b = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("LINK-USDT-SWAP", base="LINK"),
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ADA-USDT-SWAP", base="ADA"),
            _perp("DOGE-USDT-SWAP", base="DOGE"),
        ]
    )
    assert ranking_a["universe_snapshot_id"] != ranking_b["universe_snapshot_id"]
    a = _cid(ranking_a, "ADA-USDT-SWAP")
    membership_a = _membership(ranking_a, [a])
    with pytest.raises(IsolatedLaneTopologyError) as exc:
        apply_isolated_lane_topology_v1(
            membership=membership_a,
            ranking_snapshot=ranking_b,
            topology_state_root_base=tmp_path,
        )
    assert exc.value.failure_code == FAILURE_CROSS_UNIVERSE
    first = apply_isolated_lane_topology_v1(
        membership=membership_a,
        ranking_snapshot=ranking_a,
        topology_state_root_base=tmp_path,
    )
    b_eth = _cid(ranking_b, "ETH-USDT-SWAP")
    membership_b = _membership(ranking_b, [b_eth], bootstrap=False, prior=membership_a.instance_id)
    with pytest.raises(IsolatedLaneTopologyError) as prior_exc:
        apply_isolated_lane_topology_v1(
            membership=membership_b,
            ranking_snapshot=ranking_b,
            topology_state_root_base=tmp_path,
            prior_topology=first,
        )
    assert prior_exc.value.failure_code == FAILURE_CROSS_UNIVERSE


def test_case_h_restart_without_prior_fails_closed(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a, b, c = (
        _cid(ranking, "ADA-USDT-SWAP"),
        _cid(ranking, "ETH-USDT-SWAP"),
        _cid(ranking, "SOL-USDT-SWAP"),
    )
    first = _apply(ranking, [a, b, c], tmp_path)
    membership = _membership(
        ranking, [c, a, b], bootstrap=False, prior=first.membership_instance_id
    )
    with pytest.raises(IsolatedLaneTopologyError) as exc:
        apply_isolated_lane_topology_v1(
            membership=membership,
            ranking_snapshot=ranking,
            topology_state_root_base=tmp_path,
            prior_topology=None,
        )
    assert exc.value.failure_code == FAILURE_RESTART_WITHOUT_PRIOR
    restored = isolated_lane_topology_from_dict(first.to_dict())
    replayed = apply_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        prior_topology=restored,
    )
    assert replayed.instrument_to_lane() == {a: "LANE_1", b: "LANE_2", c: "LANE_3"}


def test_wrong_ranking_provenance_fails_closed(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    membership = _membership(ranking, [a])
    bad = dict(ranking)
    bad["ranking_snapshot_id"] = "foreign-ranking-snapshot"
    with pytest.raises(IsolatedLaneTopologyError) as exc:
        apply_isolated_lane_topology_v1(
            membership=membership,
            ranking_snapshot=bad,
            topology_state_root_base=tmp_path,
        )
    assert exc.value.failure_code == FAILURE_PROVENANCE_MISMATCH


def test_member_absent_from_ranking_fails_closed(tmp_path: Path) -> None:
    ranking = _five_ranking()
    a = _cid(ranking, "ADA-USDT-SWAP")
    membership = _membership(ranking, [a])
    stripped = dict(ranking)
    stripped["ranked_candidates"] = [
        row for row in ranking["ranked_candidates"] if row["canonical_instrument_id"] != a
    ]
    with pytest.raises(IsolatedLaneTopologyError) as exc:
        apply_isolated_lane_topology_v1(
            membership=membership,
            ranking_snapshot=stripped,
            topology_state_root_base=tmp_path,
        )
    assert exc.value.failure_code in {
        FAILURE_INSTRUMENT_NOT_IN_RANKING,
        FAILURE_PROVENANCE_MISMATCH,
    }


def test_extra_ranking_and_state_root_mismatch_fail_closed(tmp_path: Path) -> None:
    ranking = _five_ranking()
    other = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("LINK-USDT-SWAP", base="LINK"),
            _perp("SOL-USDT-SWAP", base="SOL"),
        ]
    )
    a = _cid(ranking, "ADA-USDT-SWAP")
    with pytest.raises(IsolatedLaneTopologyError) as extra:
        _apply(
            ranking,
            [a],
            tmp_path,
            replacement_ranking_snapshot=other,
        )
    assert extra.value.failure_code == FAILURE_EXTRA_RANKING
    first = _apply(ranking, [a], tmp_path)
    with pytest.raises(IsolatedLaneTopologyError) as mismatch:
        apply_isolated_lane_topology_v1(
            membership=_membership(
                ranking,
                [a, _cid(ranking, "ETH-USDT-SWAP")],
                bootstrap=False,
                prior=first.membership_instance_id,
            ),
            ranking_snapshot=ranking,
            topology_state_root_base=tmp_path / "other-base",
            prior_topology=first,
        )
    assert mismatch.value.failure_code == FAILURE_STATE_ROOT_MISMATCH


def test_occupied_lanes_consume_valid_6592_pins_without_fabricating_cap23(
    tmp_path: Path,
) -> None:
    ranking = _five_ranking()
    a, b = _cid(ranking, "ADA-USDT-SWAP"), _cid(ranking, "ETH-USDT-SWAP")
    topology = _apply(ranking, [a, b], tmp_path)
    pins = build_occupied_lane_pins_v1(topology, ranking_snapshot=ranking)
    assert set(pins) == {"LANE_1", "LANE_2"}
    for lane_id, pin in pins.items():
        slot = next(s for s in topology.slots if s.lane_id == lane_id)
        assert pin.canonical_instrument_id == slot.canonical_instrument_id
        assert pin.lane_state_root == slot.lane_state_root
        assert pin.universe_snapshot_id == ranking["universe_snapshot_id"]
        selected = produce_single_selected_future_v1(
            ranking_snapshot=ranking,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
            governed_pin=pin,
            lane_state_root=slot.lane_state_root,
        )
        assert selected.ok is True
        assert selected.selection.instrument_id == slot.canonical_instrument_id
        assert selected.selection.max_positions_effective == 1
        wrong = produce_single_selected_future_v1(
            ranking_snapshot=ranking,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
            governed_pin=pin,
            lane_state_root=tmp_path / "wrong-lane",
        )
        assert (
            SelectionFailureCodeV1.GOVERNED_PIN_LANE_STATE_ROOT_MISMATCH.value
            in wrong.failure_codes
        )


def test_unpinned_cap23_default_path_unchanged() -> None:
    ranking = _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA"),
        ]
    )
    unpinned = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    explicit_none = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        governed_pin=None,
        lane_state_root=None,
    )
    assert unpinned.ok is True
    assert unpinned.selection.to_dict() == explicit_none.selection.to_dict()
    assert unpinned.selection.max_positions_effective == 1

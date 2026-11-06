"""CURRENT MF N=5 Boundary occupied-lane Cap24 N=1 bind-join tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1 import (
    BoundaryOccupiedLaneCap24BindJoinError,
    bind_occupied_lane_cap24_n1_instruments_v1,
)
from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP23_SELECTION_OWNER,
    CAP24_BINDING_OWNER,
    CAP24_CHANGE_REQUIRED,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FAILURE_POLICY_FOR_OCCUPIED_LANE_WITHOUT_SUCCESSFUL_BIND,
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    HOST_JOIN,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    lane_state_root_for,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.produce_join_v1 import (
    produce_occupied_lane_cap23_n1_selections_v1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    GovernedUniverseSingleWriterV1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    build_membership_context_artifact_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    assert_handoff_invariants_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
    OWNER as CAP23_OWNER,
    STATE_NO_SELECTION,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    persist_selection_bundle_atomic_v1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import produce_single_selected_future_v1
from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
    SingleSelectedFutureSingleWriterV1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
    OWNER as CAP24_OWNER,
    RUNTIME_ACTIVATION_ALLOWED as CAP24_RUNTIME_ACTIVATION_ALLOWED,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
    RuntimeBindingEvidenceV1,
    RuntimeBindingGateResultV1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)


REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
JOIN_SOURCE = Path(
    "src/ops/current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1/bind_join_v1.py"
)
JOIN_GATE_PATH = (
    "src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1"
    ".bind_join_v1.run_single_selected_future_runtime_binding_gate_v1"
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


def _empty_portfolio(ts: float = OBSERVED_UNIX) -> PortfolioTruthSnapshotV1:
    return PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=ts,
        wall_time_unix=ts,
        source_id="analytical_execution_state",
    )


def _five_rows() -> list[dict]:
    return [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP"),
        _perp("ADA-USDT-SWAP", base="ADA"),
        _perp("LINK-USDT-SWAP", base="LINK"),
        _perp("APT-USDT-SWAP", base="APT"),
    ]


def _persist_universe_and_ranking(tmp: Path, rows: list[dict]) -> dict:
    mark_ids = [row["instId"] for row in rows]
    uni_root = tmp / "universe"
    rank_root = tmp / "ranking"
    recon_root = tmp / "recon"
    uni_root.mkdir()
    rank_root.mkdir()
    recon_root.mkdir()
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(
        state_root=uni_root, writer_identity="test_uni", session_id="s"
    )
    uni_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_universe_bundle_atomic_v1(
        state_root=uni_root,
        writer=uni_writer,
        snapshot=uni.snapshot,
        evidence={"ok": True, "capability_id": "CAPABILITY_2_1"},
    )
    uni_writer.release()
    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=uni.snapshot.to_dict(),
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(
            uni.snapshot.to_dict()
        ),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    rank_writer = ProductiveRankingSingleWriterV1(
        state_root=rank_root, writer_identity="test_rank", session_id="s"
    )
    rank_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_ranking_bundle_atomic_v1(
        state_root=rank_root,
        writer=rank_writer,
        snapshot=ranking.snapshot,
        evidence={"ok": True, "capability_id": "CAPABILITY_2_2"},
    )
    rank_writer.release()
    ranking_dict = ranking.snapshot.to_dict()
    return {
        "universe_root": uni_root,
        "ranking_root": rank_root,
        "recon_root": recon_root,
        "ranking": ranking_dict,
        "universe_snapshot_id": uni.snapshot.snapshot_id,
        "mark_price_by_native_id": {inst_id: "100.5" for inst_id in mark_ids},
    }


def _cid(ranking: dict, native: str) -> str:
    return str(
        next(c for c in ranking["ranked_candidates"] if c["venue_native_id"] == native)[
            "canonical_instrument_id"
        ]
    )


def _membership(ranking: dict, instruments: list[str]):
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
        bootstrap=True,
        prior_membership_reference=None,
    )


def _held_writer(tmp_path: Path) -> DurableLaneAssignmentSingleWriterV1:
    writer = DurableLaneAssignmentSingleWriterV1(state_root=checkpoint_root_for(tmp_path))
    writer.acquire()
    return writer


def _produce_selections(
    chain: dict, instruments: list[str], topology_root: Path
) -> dict[str, SingleSelectedFutureSelectionV1]:
    writer = _held_writer(topology_root)
    try:
        return produce_occupied_lane_cap23_n1_selections_v1(
            membership=_membership(chain["ranking"], instruments),
            ranking_snapshot=chain["ranking"],
            topology_state_root_base=topology_root,
            writer=writer,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
        )
    finally:
        writer.release()


def _bind(
    selections: dict[str, SingleSelectedFutureSelectionV1],
    topology_root: Path,
    chain: dict,
):
    return bind_occupied_lane_cap24_n1_instruments_v1(
        selections=selections,
        topology_state_root_base=topology_root,
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=_empty_portfolio(),
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        repository_sha=REPO_SHA,
        session_id="cap24-bind",
        now_unix=OBSERVED_UNIX,
    )


def _fail_gate(*, bound: BoundInstrumentV1 | None = None) -> RuntimeBindingGateResultV1:
    evidence = RuntimeBindingEvidenceV1(
        capability_id="CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1",
        schema_version="single_selected_future_runtime_binding.v1",
        producer_version="single_selected_future_runtime_binding.v1",
        owner="ops.single_selected_future_runtime_binding_v1",
        ok=False,
        alpha_enabled=False,
        new_alpha_allowed=False,
        exit_risk_safety_preserved=False,
        hard_stop=False,
        selection_state=STATE_NO_SELECTION,
        instrument_id="" if bound is None else bound.instrument_id,
        venue_native_id="" if bound is None else bound.venue_native_id,
        selection_id="" if bound is None else bound.selection_id,
        selection_integrity_digest="" if bound is None else bound.selection_integrity_digest,
        ranking_snapshot_id="" if bound is None else bound.ranking_snapshot_id,
        ranking_integrity_digest="" if bound is None else bound.ranking_integrity_digest,
        universe_snapshot_id="" if bound is None else bound.universe_snapshot_id,
        repository_sha=REPO_SHA,
        config_digest="",
        reconciliation_before_alpha=False,
        reconciliation_alpha_enabled=False,
        reason_codes=("NO_SELECTION",),
        failure_codes=("NO_SELECTION",),
        call_graph=(),
        bound=None if bound is None else bound.to_dict(),
    )
    return RuntimeBindingGateResultV1(
        ok=False,
        alpha_enabled=False,
        new_alpha_allowed=False,
        exit_risk_safety_preserved=False,
        hard_stop=False,
        selection_state=STATE_NO_SELECTION,
        bound=bound,
        evidence=evidence,
    )


def _persist_no_selection(lane_root: Path) -> SingleSelectedFutureSelectionV1:
    deny = produce_single_selected_future_v1(
        ranking_snapshot=None,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    selection = deny.selection
    if lane_root.exists():
        for child in lane_root.iterdir():
            if child.is_file():
                child.unlink()
    writer = SingleSelectedFutureSingleWriterV1(state_root=lane_root, session_id="deny")
    writer.acquire(now_unix=OBSERVED_UNIX)
    persist_selection_bundle_atomic_v1(
        state_root=lane_root,
        writer=writer,
        selection=selection,
        evidence={"ok": False, "capability_id": "CAPABILITY_2_3"},
    )
    writer.release()
    return selection


def test_authority_signature_and_flags() -> None:
    assert OWNER == "ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1"
    assert CAP23_SELECTION_OWNER == CAP23_OWNER
    assert CAP24_BINDING_OWNER == CAP24_OWNER
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_RUNTIME_ACTIVATION_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert PARALLEL_AUTHORITY_CREATED is False
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
    assert PREPARED_BOUND_CARDINALITY == "0..5"
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert FAILURE_POLICY_FOR_OCCUPIED_LANE_WITHOUT_SUCCESSFUL_BIND == "A_ABSENT_AND_CONTINUE"
    assert CAP24_RUNTIME_ACTIVATION_ALLOWED is False
    join_sig = inspect.signature(bind_occupied_lane_cap24_n1_instruments_v1)
    assert list(join_sig.parameters) == [
        "selections",
        "topology_state_root_base",
        "ranking_state_root",
        "universe_state_root",
        "reconciliation_state_root",
        "observed_portfolio",
        "mark_price_by_native_id",
        "repository_sha",
        "session_id",
        "now_unix",
    ]
    hints = inspect.get_annotations(bind_occupied_lane_cap24_n1_instruments_v1, eval_str=True)
    assert hints["return"] == dict[str, BoundInstrumentV1]
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in source
    assert "skip_reconciliation=False" in source
    assert "run_single_selected_future_runtime_binding_gate_v1" in source
    assert "assert_handoff_invariants_v1" in source
    assert "ensure_single_selected_future_runtime_binding_v1" not in source


def test_t1_empty_selections_is_empty_map_without_cap24(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    fired: list[str] = []

    def _boom(*_args, **_kwargs):
        fired.append("cap24")
        raise AssertionError("Cap24 must not run for empty selections")

    monkeypatch.setattr(JOIN_GATE_PATH, _boom)
    result = _bind({}, tmp_path, chain)
    assert result == {}
    assert fired == []


def test_t2_one_occupied_isolated_cap24_bind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    selections = _produce_selections(chain, [ada], tmp_path)
    calls: list[Path] = []
    real_gate = run_single_selected_future_runtime_binding_gate_v1

    def _spy(**kwargs):
        calls.append(Path(kwargs["selection_state_root"]))
        assert kwargs["ranking_state_root"] == chain["ranking_root"]
        assert kwargs["universe_state_root"] == chain["universe_root"]
        assert kwargs["reconciliation_state_root"] == chain["recon_root"]
        assert kwargs["skip_reconciliation"] is False
        return real_gate(**kwargs)

    monkeypatch.setattr(JOIN_GATE_PATH, _spy)
    result = _bind(selections, tmp_path, chain)
    expected_root = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1"))
    assert list(result) == ["LANE_1"]
    bound = result["LANE_1"]
    assert isinstance(bound, BoundInstrumentV1)
    assert bound.instrument_id == ada
    assert bound.venue_native_id == "ADA-USDT-SWAP"
    assert bound.max_positions_effective == 1
    assert bound.selected_future_count == 1
    assert calls == [expected_root]
    assert_handoff_invariants_v1(
        selections["LANE_1"],
        bound,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_universe_snapshot_id=bound.universe_snapshot_id,
        universe_snapshot_id=bound.universe_snapshot_id,
    )


def test_t3_five_occupied_sequential_isolated_n1_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    natives = ["ADA-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    instruments = [_cid(chain["ranking"], native) for native in natives]
    selections = _produce_selections(chain, instruments, tmp_path)
    calls: list[tuple[str, Path, Path, Path, Path]] = []
    real_gate = run_single_selected_future_runtime_binding_gate_v1

    def _spy(**kwargs):
        calls.append(
            (
                Path(kwargs["selection_state_root"]).name,
                Path(kwargs["selection_state_root"]),
                Path(kwargs["ranking_state_root"]),
                Path(kwargs["universe_state_root"]),
                Path(kwargs["reconciliation_state_root"]),
            )
        )
        assert kwargs["skip_reconciliation"] is False
        return real_gate(**kwargs)

    monkeypatch.setattr(JOIN_GATE_PATH, _spy)
    result = _bind(selections, tmp_path, chain)
    assert list(result) == list(LANE_IDS)
    roots = [
        Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id=lane_id))
        for lane_id in LANE_IDS
    ]
    assert [call[0] for call in calls] == list(LANE_IDS)
    assert [call[1] for call in calls] == roots
    assert len({str(root) for root in roots}) == 5
    assert {call[2] for call in calls} == {chain["ranking_root"]}
    assert {call[3] for call in calls} == {chain["universe_root"]}
    assert {call[4] for call in calls} == {chain["recon_root"]}
    for lane_id, native, instrument_id in zip(LANE_IDS, natives, instruments):
        bound = result[lane_id]
        assert isinstance(bound, BoundInstrumentV1)
        assert bound.instrument_id == instrument_id
        assert bound.venue_native_id == native
        assert bound.max_positions_effective == 1
        assert_handoff_invariants_v1(
            selections[lane_id],
            bound,
            ranking_snapshot_id=bound.ranking_snapshot_id,
            ranking_universe_snapshot_id=bound.universe_snapshot_id,
            universe_snapshot_id=bound.universe_snapshot_id,
        )


def test_t4_t5_pairwise_handoff_preserves_identity_no_reselect(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    selections = _produce_selections(chain, [ada], tmp_path)
    result = _bind(selections, tmp_path, chain)
    bound = result["LANE_1"]
    selection = selections["LANE_1"]
    assert bound.instrument_id == selection.instrument_id
    assert bound.venue_native_id == selection.venue_native_id
    assert bound.selection_id == selection.selection_id
    assert bound.ranking_snapshot_id == selection.ranking_snapshot_id
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    assert "run_single_selected_future_policy_v1" not in source
    assert "produce_productive_futures_ranking_v1" not in source
    assert "_pick_top_eligible" not in source


def test_t6_cross_lane_selection_root_isolation(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    eth = _cid(chain["ranking"], "ETH-USDT-SWAP")
    selections = _produce_selections(chain, [ada, eth], tmp_path)
    result = _bind(selections, tmp_path, chain)
    assert list(result) == ["LANE_1", "LANE_2"]
    assert result["LANE_1"].instrument_id == ada
    assert result["LANE_2"].instrument_id == eth
    assert (
        result["LANE_1"].selection_integrity_digest != result["LANE_2"].selection_integrity_digest
    )
    lane3 = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_3"))
    assert not (lane3 / "single_selected_future_selection_v1.json").is_file()


def test_t7_shared_reconciliation_and_skip_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    eth = _cid(chain["ranking"], "ETH-USDT-SWAP")
    selections = _produce_selections(chain, [ada, eth], tmp_path)
    recon_roots: list[Path] = []
    real_gate = run_single_selected_future_runtime_binding_gate_v1

    def _spy(**kwargs):
        recon_roots.append(Path(kwargs["reconciliation_state_root"]))
        assert kwargs["skip_reconciliation"] is False
        return real_gate(**kwargs)

    monkeypatch.setattr(JOIN_GATE_PATH, _spy)
    result = _bind(selections, tmp_path, chain)
    assert list(result) == ["LANE_1", "LANE_2"]
    assert recon_roots == [chain["recon_root"], chain["recon_root"]]


def test_t8_absent_and_continue_for_three_failure_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    eth = _cid(chain["ranking"], "ETH-USDT-SWAP")
    selections = _produce_selections(chain, [ada, eth], tmp_path)
    lane1 = Path(lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_1"))
    deny = _persist_no_selection(lane1)
    no_selection_map = {"LANE_1": deny, "LANE_2": selections["LANE_2"]}
    continued = _bind(no_selection_map, tmp_path, chain)
    assert list(continued) == ["LANE_2"]
    assert continued["LANE_2"].venue_native_id == "ETH-USDT-SWAP"
    assert "LANE_1" not in continued

    real_gate = run_single_selected_future_runtime_binding_gate_v1
    calls: list[str] = []

    def _none_first(**kwargs):
        lane = Path(kwargs["selection_state_root"]).name
        calls.append(lane)
        if lane == "LANE_1":
            return _fail_gate(bound=None)
        return real_gate(**kwargs)

    monkeypatch.setattr(JOIN_GATE_PATH, _none_first)
    none_result = _bind(selections, tmp_path, chain)
    assert list(none_result) == ["LANE_2"]
    assert none_result["LANE_2"].venue_native_id == "ETH-USDT-SWAP"
    assert calls == ["LANE_1", "LANE_2"]

    calls.clear()
    fail_bound = BoundInstrumentV1(
        instrument_id=selections["LANE_1"].instrument_id,
        venue_native_id=selections["LANE_1"].venue_native_id,
        ranking_snapshot_id=selections["LANE_1"].ranking_snapshot_id,
        ranking_integrity_digest=selections["LANE_1"].ranking_integrity_digest,
        universe_snapshot_id=chain["universe_snapshot_id"],
        selection_id=selections["LANE_1"].selection_id,
        selection_integrity_digest=selections["LANE_1"].integrity_digest,
        selection_state=selections["LANE_1"].state,
    )

    def _fail_path_bound(**kwargs):
        lane = Path(kwargs["selection_state_root"]).name
        calls.append(lane)
        if lane == "LANE_1":
            return _fail_gate(bound=fail_bound)
        return real_gate(**kwargs)

    monkeypatch.setattr(JOIN_GATE_PATH, _fail_path_bound)
    fail_path_result = _bind(selections, tmp_path, chain)
    assert list(fail_path_result) == ["LANE_2"]
    assert fail_path_result["LANE_2"].venue_native_id == "ETH-USDT-SWAP"
    assert "LANE_1" not in fail_path_result
    assert calls == ["LANE_1", "LANE_2"]


def test_t8_cap24_exception_propagates_no_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    eth = _cid(chain["ranking"], "ETH-USDT-SWAP")
    selections = _produce_selections(chain, [ada, eth], tmp_path)
    real_gate = run_single_selected_future_runtime_binding_gate_v1

    def _boom_second(**kwargs):
        lane = Path(kwargs["selection_state_root"]).name
        if lane == "LANE_2":
            raise RuntimeError("CAP24_FORCED")
        return real_gate(**kwargs)

    monkeypatch.setattr(JOIN_GATE_PATH, _boom_second)
    with pytest.raises(RuntimeError, match="CAP24_FORCED") as exc:
        result = _bind(selections, tmp_path, chain)
        raise AssertionError(f"partial map returned:{result!r}")
    assert "CAP24_FORCED" in str(exc.value)


def test_unknown_lane_id_fails_closed_before_cap24(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ada = _cid(chain["ranking"], "ADA-USDT-SWAP")
    selections = _produce_selections(chain, [ada], tmp_path)
    poisoned = dict(selections)
    poisoned["LANE_X"] = selections["LANE_1"]
    fired: list[str] = []

    def _boom(*_args, **_kwargs):
        fired.append("cap24")
        raise AssertionError("Cap24 must not run for unknown lane_id")

    monkeypatch.setattr(JOIN_GATE_PATH, _boom)
    with pytest.raises(BoundaryOccupiedLaneCap24BindJoinError) as exc:
        _bind(poisoned, tmp_path, chain)
    assert exc.value.failure_code == FAILURE_UNKNOWN_LANE_ID
    assert fired == []


def test_t9_t10_t11_t12_t13_t14_activation_and_protected_surfaces() -> None:
    source = JOIN_SOURCE.read_text(encoding="utf-8")
    assert "alpha_enabled" not in source
    assert "ensure_single_selected_future_runtime_binding_v1" not in source
    assert "run_current_productive_master_v2_runtime_cycle_v1" not in source
    assert "compose_core_live_execution_intent_v1" not in source
    assert "LiveExecutionPort" not in source
    assert "persist_binding_evidence_atomic_v1" not in source
    assert JOIN_RUNTIME_ACTIVATION_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert FIVE_LANE_RUNTIME_CREATED is False
    assert FIVE_LANE_CONTINUOUS_HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert PREPARED_BOUND_CARDINALITY == "0..5"
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    expected = {
        "produce_occupied_lane_cap23_n1_selections_v1",
        "run_single_selected_future_policy_v1",
        "produce_single_selected_future_v1",
        "produce_from_ranking_state_root_v1",
        "persist_selection_bundle_atomic_v1",
        "_pick_top_eligible",
        "ensure_single_selected_future_runtime_binding_v1",
        "persist_binding_evidence_atomic_v1",
        "run_current_productive_master_v2_runtime_cycle_v1",
        "compose_core_live_execution_intent_v1",
        "mf_canonical_single_egress_authority_handoff_contract_v1",
        "master_v2",
        "double_play",
        "execution",
        "top_n_active_set",
        "LiveExecutionPort",
    }
    assert FORBIDDEN_CALL_GRAPH_TARGETS == expected
    for forbidden in expected:
        assert forbidden not in source
    hints = inspect.get_annotations(bind_occupied_lane_cap24_n1_instruments_v1, eval_str=True)
    assert hints["return"] == dict[str, BoundInstrumentV1]

"""Scope-closure tests: D4 matrix, D5 topology, D6 MV2 bind, I11-I13, five-lane E2E."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    CURSOR_FILENAME,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.constants_v1 import (
    GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME,
    GOVERNED_CYCLE_LOCK_ROOT_DIRNAME,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.artifact_matrix_v1 import (
    LaneArtifactDisposition,
    lane_artifact_adjudication_matrix_v1,
    purge_lane_local_artifacts_for_release_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.reconciliation_admission_v1 import (
    build_master_v2_reconciliation_admission_for_lane_v1,
    build_per_lane_reconciliation_admission_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    apply_isolated_lane_topology_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.hard_facts_system_closure_v1.durable_kill_switch_mv2_binding_v1 import (
    resolve_durable_kill_switch_for_mv2_host_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
    ReleaseReasonV1,
    ReserveDispositionV1,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _bind
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.exit_policy_producer_binding_v1.host_binding_v1 import (
    HostExitPolicyBindingV1,
    evaluate_host_exit_policy_producers_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import SafetyMode, TradingGate
from tests.ops.test_current_mf_n5_instrument_runtime_identity_closure_v1 import (
    ORIGIN_SHA,
    C1_TS,
    _bound,
    _candles,
    _g17,
    _occupancy_absent,
    _pair,
)
from tests.ops.test_current_mf_n5_recovered_topology_consumer_join_v1 import (
    _cid,
    _five_ranking,
    _membership,
)

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lane_generation_v1 import (
    ensure_lane_generation_safe_v1,
)


def test_d4_artifact_matrix_required_rows() -> None:
    matrix = {row.artifact: row.disposition for row in lane_artifact_adjudication_matrix_v1()}
    for artifact in (
        "cap23_hysteresis",
        "cap24_binding",
        "mv2_cursor",
        "dynamic_scope",
        "side_state",
        "governed_cycle_lock",
        "governed_cycle_evidence",
        "reconciliation_lane_cache",
    ):
        assert artifact in matrix
    assert matrix["cap23_hysteresis"] == LaneArtifactDisposition.NOT_LANE_LOCAL
    assert matrix["mv2_cursor"] == LaneArtifactDisposition.IDENTITY_VALIDATED
    assert matrix["side_state"] == LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY


def test_d4_rekey_purges_lane_local_mutable(tmp_path: Path) -> None:
    root = tmp_path / "LANE_1"
    root.mkdir()
    (root / CURSOR_FILENAME).write_text("{}", encoding="utf-8")
    (root / "side_state_v1.json").write_text("{}", encoding="utf-8")
    (root / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME).mkdir()
    (root / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME / "lock.json").write_text("{}", encoding="utf-8")
    (root / GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME).mkdir()
    (root / GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME / "x.json").write_text("{}", encoding="utf-8")
    purge_lane_local_artifacts_for_release_v1(root)
    assert not (root / CURSOR_FILENAME).is_file()
    assert not (root / "side_state_v1.json").is_file()
    assert not (root / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME).exists()
    assert not (root / GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME).exists()


def test_d4_i5_i8_restart_manifest_and_purge(tmp_path: Path) -> None:
    root = tmp_path / "lane"
    root.mkdir()
    ident_a = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="VENUE-A")
    )
    ensure_lane_generation_safe_v1(lane_state_root=root, identity=ident_a)
    (root / CURSOR_FILENAME).write_text('{"instrument_id":"OLD"}', encoding="utf-8")
    ident_b = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1",
        bound=_bound(lane_id="LANE_1", native="VENUE-B"),
    )
    ensure_lane_generation_safe_v1(lane_state_root=root, identity=ident_b)
    manifest = json.loads((root / "lane_runtime_instrument_identity_manifest_v1.json").read_text())
    assert manifest["venue_native_id"] == "VENUE-B"
    assert not (root / CURSOR_FILENAME).is_file()


def test_d5_dropout_long_retains_lane(tmp_path: Path) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    eth = _cid(ranking, "ETH-USDT-SWAP")
    prior = apply_isolated_lane_topology_v1(
        membership=_membership(ranking, [ada, eth]),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
    )
    portfolio = PortfolioTruthSnapshotV1(
        positions=(PositionTruthV1.from_signed(instrument_id=ada, signed_quantity=Decimal("1")),)
    )
    dropped = apply_isolated_lane_topology_v1(
        membership=_membership(ranking, [eth], bootstrap=False, prior=prior.membership_instance_id),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        prior_topology=prior,
        open_position_custody_portfolio=portfolio,
    )
    assert ada in dropped.instrument_to_lane().keys()
    assert dropped.instrument_to_lane()[ada] == prior.instrument_to_lane()[ada]


def test_d5_dropout_short_retains_lane(tmp_path: Path) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    eth = _cid(ranking, "ETH-USDT-SWAP")
    prior = apply_isolated_lane_topology_v1(
        membership=_membership(ranking, [ada, eth]),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
    )
    portfolio = PortfolioTruthSnapshotV1(
        positions=(PositionTruthV1.from_signed(instrument_id=ada, signed_quantity=Decimal("-2")),)
    )
    dropped = apply_isolated_lane_topology_v1(
        membership=_membership(ranking, [eth], bootstrap=False, prior=prior.membership_instance_id),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        prior_topology=prior,
        open_position_custody_portfolio=portfolio,
    )
    assert ada in dropped.instrument_to_lane().keys()
    assert dropped.instrument_to_lane()[ada] == prior.instrument_to_lane()[ada]


def test_d5_dropout_flat_releases_lane(tmp_path: Path) -> None:
    ranking = _five_ranking()
    ada = _cid(ranking, "ADA-USDT-SWAP")
    eth = _cid(ranking, "ETH-USDT-SWAP")
    prior = apply_isolated_lane_topology_v1(
        membership=_membership(ranking, [ada, eth]),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
    )
    dropped = apply_isolated_lane_topology_v1(
        membership=_membership(ranking, [eth], bootstrap=False, prior=prior.membership_instance_id),
        ranking_snapshot=ranking,
        topology_state_root_base=tmp_path,
        prior_topology=prior,
        open_position_custody_portfolio=PortfolioTruthSnapshotV1(),
    )
    assert ada not in dropped.instrument_to_lane()


def test_d6_mv2_admission_instrument_bound() -> None:
    ident = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1", bound=_bound(lane_id="LANE_1")
    )
    per_lane = build_per_lane_reconciliation_admission_v1(
        identity=ident, portfolio=PortfolioTruthSnapshotV1()
    )
    admission = build_master_v2_reconciliation_admission_for_lane_v1(
        identity=ident,
        per_lane=per_lane,
        session_id="sess",
        repository_sha=ORIGIN_SHA,
        portfolio=PortfolioTruthSnapshotV1(),
    )
    admission.validate_for_productive_master_v2_entry_v1(
        instrument_id=ident.canonical_instrument_id
    )
    assert "LANE_1" in admission.reconciliation_classification


def test_i11_reservation_slot_lane_identity() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    obs = _bind(owner)
    r1 = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="dec-a",
        cycle_id="cyc-a",
        observation_id=obs,
        amount=Decimal("10"),
    )
    r2 = owner.try_reserve_v1(
        slot_id="LANE_2",
        decision_id="dec-b",
        cycle_id="cyc-b",
        observation_id=obs,
        amount=Decimal("10"),
    )
    assert r1.disposition == ReserveDispositionV1.ADMITTED
    assert r2.disposition == ReserveDispositionV1.ADMITTED
    assert r1.reservation is not None and r2.reservation is not None
    assert r1.reservation.reservation_id != r2.reservation.reservation_id
    owner.release_v1(str(r1.reservation.reservation_id), reason=ReleaseReasonV1.PLAN_FAILURE)
    owner.release_v1(str(r2.reservation.reservation_id), reason=ReleaseReasonV1.PLAN_FAILURE)


def test_i12_pre_external_evidence_lineage_per_lane(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1", native="VENUE-A")}
    mark = 100.0
    results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        pairs,
        origin_main_sha=ORIGIN_SHA,
        cycle_id_prefix="lineage",
        observed_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME) + 1.0,
        mark_px=mark,
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
        candles_payload=_candles(inst_id="VENUE-A", last_ts_ms=int(C1_TS * 1000), close=mark),
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id="VENUE-A", mark_px=mark, index_px=99.5
        ),
        g17_typed_vol_producers={"LANE_1": _g17("INST-LANE_1", "VENUE-A")},
    )
    record = results["LANE_1"]
    ledger = Path(record.evidence_root) / LEDGER_FILENAME
    assert ledger.is_file()
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload.get("native_id") == "VENUE-A"


def test_i13_kill_reachable_open_position_not_in_membership(tmp_path: Path) -> None:
    ks = tmp_path / "state.json"
    ks.write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    durable = resolve_durable_kill_switch_for_mv2_host_v1(kill_switch_state_path=str(ks))
    binding = HostExitPolicyBindingV1(instrument_id="orphan-inst")
    _bundle, _signals, safety_mode, trading_gate = evaluate_host_exit_policy_producers_v1(
        binding,
        mark_price=100.0,
        event_ts_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME),
        observation_digest="dig",
        has_open_position=True,
        existing_position_side="long",
        entry_price=99.0,
        entry_event_time=float(PREVIOUS_C1_VENUE_EVENT_TIME),
        entry_trading_epoch="epoch",
        killstate_active=durable.killstate_active,
        killstate_trigger=durable.killstate_trigger,
    )
    assert safety_mode == SafetyMode.BLOCKED
    assert trading_gate == TradingGate.BLOCKED


def test_five_lane_e2e_isolation(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id, native=f"VENUE-{lane_id}") for lane_id in LANE_IDS}
    mark = 100.0
    by_lane_candles = {
        lane_id: _candles(
            inst_id=f"VENUE-{lane_id}",
            last_ts_ms=int(C1_TS * 1000),
            close=mark + float(index),
        )
        for index, lane_id in enumerate(LANE_IDS)
    }
    by_lane_prov = {
        lane_id: build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=f"VENUE-{lane_id}",
            mark_px=mark + float(index),
            index_px=99.5 + float(index),
        )
        for index, lane_id in enumerate(LANE_IDS)
    }
    results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        pairs,
        origin_main_sha=ORIGIN_SHA,
        cycle_id_prefix="five-lane",
        observed_unix=float(PREVIOUS_C1_VENUE_EVENT_TIME) + 1.0,
        mark_px=mark,
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
        candles_payload_by_lane=by_lane_candles,
        canonical_price_provenance_by_lane=by_lane_prov,
        occupancy_payloads=_occupancy_absent(),
        g17_typed_vol_producers={
            lane_id: _g17(f"INST-{lane_id}", f"VENUE-{lane_id}") for lane_id in LANE_IDS
        },
    )
    assert set(results) == set(LANE_IDS)
    roots = {record.cursor_store_root for record in results.values()}
    assert len(roots) == 5
    natives = {record.native_id for record in results.values()}
    assert len(natives) == 5
    for lane_id, record in results.items():
        assert record.native_id == f"VENUE-{lane_id}"
        assert record.bound_instrument.instrument_id == f"INST-{lane_id}"

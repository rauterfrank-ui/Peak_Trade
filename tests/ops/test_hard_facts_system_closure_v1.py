"""Hard-facts system closure — authority, handoff, identity, kill-switch, treasury guards."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.hard_facts_system_closure_v1.cap22_productive_real_gate_v1 import (
    Cap22ProductiveRealGateError,
    assert_cap22_productive_real_ranking_v1,
)
from src.ops.hard_facts_system_closure_v1.durable_kill_switch_mv2_binding_v1 import (
    resolve_durable_kill_switch_for_mv2_host_v1,
)
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
    InstrumentSensitiveStateClass,
    StateCarryDisposition,
    adjudicate_instrument_sensitive_state_v1,
)
from src.ops.hard_facts_system_closure_v1.lane_health_membership_feedback_v1 import (
    LaneHealthClass,
    classify_lane_health_membership_feedback_v1,
)
from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    RotationPhase,
    evaluate_position_aware_rotation_v1,
)
from src.ops.hard_facts_system_closure_v1.productive_mf_n5_handoff_join_v1 import (
    HardFactsCap22MembershipHandoffRequestV1,
    execute_hard_facts_cap22_to_mf_n5_handoff_v1,
)
from src.ops.hard_facts_system_closure_v1.treasury_restart_guard_v1 import (
    evaluate_treasury_admission_guard_v1,
    reservation_cross_epoch_forbidden_v1,
    restart_silent_advance_forbidden_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    PRODUCER_VERSION,
    RANKING_POLICY_PROVENANCE,
    SNAPSHOT_STATE_VALID,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import SafetyMode, TradingGate
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    OBSERVED_UNIX,
    _five_rows,
    _held_writer,
    _persist_universe_and_ranking,
)


def test_authority_invariants() -> None:
    proof = prove_hard_facts_authority_invariants_v1()
    assert proof.ok is True
    assert proof.safety_flags["post_allowed"] is False
    assert proof.safety_flags["external_effect_authorized"] is False


def test_synthetic_ranking_rejected() -> None:
    snap = {
        "capability_id": CAPABILITY_ID,
        "producer_version": PRODUCER_VERSION,
        "snapshot_state": SNAPSHOT_STATE_VALID,
        "ranking_policy_provenance": "synthetic test fixture",
        "ranking_snapshot_id": "x",
        "integrity_digest": "abc",
    }
    with pytest.raises(Cap22ProductiveRealGateError):
        assert_cap22_productive_real_ranking_v1(snap)


def test_cap22_to_mf_n5_handoff_deterministic(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ranking = chain["ranking"]
    assert_cap22_productive_real_ranking_v1(ranking)
    writer = _held_writer(tmp_path / "topo")
    result = execute_hard_facts_cap22_to_mf_n5_handoff_v1(
        HardFactsCap22MembershipHandoffRequestV1(
            ranking_snapshot=ranking,
            membership_store_root=tmp_path / "mca",
            topology_state_root_base=tmp_path / "topo",
        ),
        lane_assignment_writer=writer,
    )
    assert result.membership.ordered_instrument_ids
    assert result.topology.slots


def test_same_lane_new_instrument_resets_confirmation_state() -> None:
    lane = "LANE_1"
    bound_a = BoundInstrumentV1(
        instrument_id="inst-a",
        venue_native_id="A-USDT-SWAP",
        ranking_snapshot_id="r1",
        ranking_integrity_digest="d1",
        universe_snapshot_id="u1",
        selection_id="s1",
        selection_integrity_digest="sd1",
        selection_state="SELECTED",
    )
    bound_b = BoundInstrumentV1(
        instrument_id="inst-b",
        venue_native_id="B-USDT-SWAP",
        ranking_snapshot_id="r2",
        ranking_integrity_digest="d2",
        universe_snapshot_id="u1",
        selection_id="s2",
        selection_integrity_digest="sd2",
        selection_state="SELECTED",
    )
    id_a = BoundInstrumentLaneIdentityV1.from_bound_instrument(lane_id=lane, bound=bound_a)
    id_b = BoundInstrumentLaneIdentityV1.from_bound_instrument(lane_id=lane, bound=bound_b)
    disp = adjudicate_instrument_sensitive_state_v1(
        state_class=InstrumentSensitiveStateClass.CONFIRMATION_CURSOR,
        prior_identity=id_a,
        current_identity=id_b,
    )
    assert disp == StateCarryDisposition.RESET


def test_same_lane_same_instrument_safe_carry_sidestate() -> None:
    lane = "LANE_1"
    bound = BoundInstrumentV1(
        instrument_id="inst-a",
        venue_native_id="A-USDT-SWAP",
        ranking_snapshot_id="r1",
        ranking_integrity_digest="d1",
        universe_snapshot_id="u1",
        selection_id="s1",
        selection_integrity_digest="sd1",
        selection_state="SELECTED",
    )
    identity = BoundInstrumentLaneIdentityV1.from_bound_instrument(lane_id=lane, bound=bound)
    disp = adjudicate_instrument_sensitive_state_v1(
        state_class=InstrumentSensitiveStateClass.SIDE_STATE,
        prior_identity=identity,
        current_identity=identity,
    )
    assert disp == StateCarryDisposition.SAFE_CARRY


def test_open_position_blocks_rotation_commit() -> None:
    rot = evaluate_position_aware_rotation_v1(
        phase=RotationPhase.COMMIT,
        venue_flat=False,
        reconciled=True,
        pending_external_custody=False,
        pending_pre_external_custody=False,
        lane_health_allows_replacement=True,
    )
    assert rot.allowed is False
    assert rot.retain_custody_for_open_position is True


def test_ordinary_hold_no_membership_churn() -> None:
    fb = classify_lane_health_membership_feedback_v1(
        health_class=LaneHealthClass.TRANSIENT_HOLD,
        venue_flat=True,
        reconciled=True,
        pending_custody_conflict=False,
    )
    assert fb.triggers_membership_churn is False


def test_global_halt_no_membership_churn() -> None:
    fb = classify_lane_health_membership_feedback_v1(
        health_class=LaneHealthClass.GLOBAL_HALT,
        venue_flat=True,
        reconciled=True,
        pending_custody_conflict=False,
    )
    assert fb.triggers_membership_churn is False


def test_lane_fatal_replacement_when_flat() -> None:
    fb = classify_lane_health_membership_feedback_v1(
        health_class=LaneHealthClass.LANE_LOCAL_FATAL,
        venue_flat=True,
        reconciled=True,
        pending_custody_conflict=False,
    )
    assert fb.may_commit_replacement is True


def test_durable_kill_switch_blocks_entry(tmp_path: Path) -> None:
    ks = tmp_path / "state.json"
    ks.write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    binding = resolve_durable_kill_switch_for_mv2_host_v1(kill_switch_state_path=str(ks))
    assert binding.killstate_active is True
    assert binding.blocks_new_entry is True


def test_kill_switch_mv2_trading_gate_blocked(tmp_path: Path) -> None:
    from src.ops.exit_policy_producer_binding_v1.host_binding_v1 import (
        HostExitPolicyBindingV1,
        evaluate_host_exit_policy_producers_v1,
    )

    ks = tmp_path / "state.json"
    ks.write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    durable = resolve_durable_kill_switch_for_mv2_host_v1(kill_switch_state_path=str(ks))
    binding = HostExitPolicyBindingV1(instrument_id="inst-x")
    _bundle, _signals, safety_mode, trading_gate = evaluate_host_exit_policy_producers_v1(
        binding,
        mark_price=100.0,
        event_ts_unix=float(OBSERVED_UNIX),
        observation_digest="dig",
        has_open_position=False,
        existing_position_side="none",
        entry_price=None,
        entry_event_time=None,
        entry_trading_epoch=None,
        killstate_active=durable.killstate_active,
        killstate_trigger=durable.killstate_trigger,
    )
    assert safety_mode == SafetyMode.BLOCKED
    assert trading_gate == TradingGate.BLOCKED


def test_treasury_stale_blocks_admission() -> None:
    guard = evaluate_treasury_admission_guard_v1(
        observation_trusted=True,
        reconciliation_pass=True,
        avail_eq_positive=True,
        numeric_fresh=False,
    )
    assert guard.admitted is False
    assert guard.stale_or_ambiguous is True


def test_reservation_cross_instrument_epoch_forbidden() -> None:
    lane = "LANE_1"
    bound = BoundInstrumentV1(
        instrument_id="inst-a",
        venue_native_id="A-USDT-SWAP",
        ranking_snapshot_id="r1",
        ranking_integrity_digest="d1",
        universe_snapshot_id="u1",
        selection_id="s1",
        selection_integrity_digest="sd1",
        selection_state="SELECTED",
    )
    current = BoundInstrumentLaneIdentityV1.from_bound_instrument(lane_id=lane, bound=bound)
    prior = {"instrument_epoch": "deadbeef", "lane_id": lane}
    assert reservation_cross_epoch_forbidden_v1(
        prior_material=prior,
        current=current,
        decision_id="d",
        cycle_id="c",
        observation_id="o",
    )


def test_restart_silent_confirmation_advance_forbidden() -> None:
    assert restart_silent_advance_forbidden_v1(
        prior_confirmation_epoch=3,
        restored_confirmation_epoch=5,
        identity_changed=False,
    )


def test_pre_external_post_flags_in_proof() -> None:
    proof = prove_hard_facts_authority_invariants_v1()
    assert proof.authority_matrix["pre_external_terminal"] is True
    assert proof.safety_flags["post_allowed"] is False


def test_productive_real_ranking_accepts_producer_snapshot(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows()[:2])
    assert_cap22_productive_real_ranking_v1(chain["ranking"])
    assert RANKING_POLICY_PROVENANCE in str(chain["ranking"].get("ranking_policy_provenance"))

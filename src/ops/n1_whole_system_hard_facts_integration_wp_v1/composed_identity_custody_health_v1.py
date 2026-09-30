"""RW-E4–E8: composed owners (no centralized case-switch)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from src.ops.hard_facts_system_closure_v1.constants_v1 import CASE_SWITCH_CANONICAL_OWNER
from src.ops.hard_facts_system_closure_v1.durable_kill_switch_mv2_binding_v1 import (
    DurableKillSwitchMv2BindingV1,
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
from src.ops.hard_facts_system_closure_v1.treasury_restart_guard_v1 import (
    reservation_cross_epoch_forbidden_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


@dataclass(frozen=True)
class ComposedSafetyChainProofV1:
    ok: bool
    instrument_epoch_safe: bool
    position_custody_safe: bool
    case_switch_owner_none: bool
    lane_health_membership_bound: bool
    durable_kill_switch_bound: bool


def prove_stale_instrument_identity_fail_closed_v1(
    *,
    lane_id: str,
    prior_bound: BoundInstrumentV1,
    current_bound: BoundInstrumentV1,
) -> bool:
    prior_id = BoundInstrumentLaneIdentityV1.from_bound_instrument(
        lane_id=lane_id, bound=prior_bound
    )
    current_id = BoundInstrumentLaneIdentityV1.from_bound_instrument(
        lane_id=lane_id, bound=current_bound
    )
    disp = adjudicate_instrument_sensitive_state_v1(
        state_class=InstrumentSensitiveStateClass.CONFIRMATION_CURSOR,
        prior_identity=prior_id,
        current_identity=current_id,
    )
    return disp is StateCarryDisposition.RESET


def prove_position_custody_blocks_replace_v1() -> bool:
    rot = evaluate_position_aware_rotation_v1(
        phase=RotationPhase.COMMIT,
        venue_flat=False,
        reconciled=True,
        pending_external_custody=False,
        pending_pre_external_custody=False,
        lane_health_allows_replacement=True,
    )
    return rot.allowed is False and rot.retain_custody_for_open_position is True


def prove_lane_health_membership_distinctions_v1() -> bool:
    hold = classify_lane_health_membership_feedback_v1(
        health_class=LaneHealthClass.TRANSIENT_HOLD,
        venue_flat=True,
        reconciled=True,
        pending_custody_conflict=False,
    )
    fatal = classify_lane_health_membership_feedback_v1(
        health_class=LaneHealthClass.LANE_LOCAL_FATAL,
        venue_flat=True,
        reconciled=True,
        pending_custody_conflict=False,
    )
    halt = classify_lane_health_membership_feedback_v1(
        health_class=LaneHealthClass.GLOBAL_HALT,
        venue_flat=True,
        reconciled=True,
        pending_custody_conflict=False,
    )
    return (
        hold.triggers_membership_churn is False
        and fatal.may_commit_replacement is True
        and halt.triggers_membership_churn is False
    )


def prove_kill_switch_blocks_entry_not_global_freeze_v1(
    binding: DurableKillSwitchMv2BindingV1,
) -> bool:
    if not binding.killstate_active:
        return binding.blocks_new_entry is False
    return binding.blocks_new_entry is True and binding.safety_exit_armed is True


def prove_composed_safety_chain_v1(
    *,
    kill_switch_state_path: Optional[str] = None,
) -> ComposedSafetyChainProofV1:
    ks = resolve_durable_kill_switch_for_mv2_host_v1(
        kill_switch_state_path=kill_switch_state_path,
        explicit_active=False,
    )
    epoch_ok = prove_stale_instrument_identity_fail_closed_v1(
        lane_id="LANE_1",
        prior_bound=_sample_bound("inst-a", "A-USDT-SWAP"),
        current_bound=_sample_bound("inst-b", "B-USDT-SWAP"),
    )
    custody_ok = prove_position_custody_blocks_replace_v1()
    lane_ok = prove_lane_health_membership_distinctions_v1()
    ks_ok = prove_kill_switch_blocks_entry_not_global_freeze_v1(ks)
    return ComposedSafetyChainProofV1(
        ok=epoch_ok and custody_ok and lane_ok and ks_ok,
        instrument_epoch_safe=epoch_ok,
        position_custody_safe=custody_ok,
        case_switch_owner_none=CASE_SWITCH_CANONICAL_OWNER == "NONE",
        lane_health_membership_bound=lane_ok,
        durable_kill_switch_bound=ks_ok,
    )


def reservation_epoch_mismatch_forbidden_v1(
    *,
    prior_material: Mapping[str, str],
    current: BoundInstrumentLaneIdentityV1,
) -> bool:
    return reservation_cross_epoch_forbidden_v1(
        prior_material=prior_material,
        current=current,
        decision_id="d",
        cycle_id="c",
        observation_id="o",
    )


def _sample_bound(iid: str, native: str) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=iid,
        venue_native_id=native,
        ranking_snapshot_id="r1",
        ranking_integrity_digest="d1",
        universe_snapshot_id="u1",
        selection_id="s1",
        selection_integrity_digest="sd1",
        selection_state="SELECTED",
    )

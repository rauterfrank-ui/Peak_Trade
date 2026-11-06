from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping, Optional

from research.multi_future_ghv_counterfactual_distance_lab_v2.constants_v2 import EXPERIMENT_ID
from research.multi_future_ghv_counterfactual_distance_lab_v2.symmetric_fork_v2 import (
    LastDistanceForkSnapshotV2,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

NOT_APPLICABLE = "NOT_APPLICABLE"


def _na(value: object, *, applicable: bool) -> object:
    return NOT_APPLICABLE if not applicable else value


def build_cycle_observation_v2(
    *,
    model_id: str,
    flight_id: str,
    lane_id: str,
    cycle_id: int,
    generalization_profile: str,
    future_profile_id: str,
    price_scale: float,
    p0: float,
    vol_level: str,
    regime_id: str,
    seed: int,
    fork: Optional[LastDistanceForkSnapshotV2],
    tick_size: str,
    price_precision: int,
    result: IntegratedOfflineReplayResultV1,
) -> Mapping[str, Any]:
    ev = result.evidence
    im = result.intermediate
    mark = float(im.market_context.mark_price) if im else 0.0
    vol = float(im.market_context.volatility_estimate) if im else 0.0
    sigma_p = vol * mark if mark > 0 else 0.0

    scope_events = NOT_APPLICABLE
    scope_before = NOT_APPLICABLE
    scope_after = NOT_APPLICABLE
    scope_anchor = NOT_APPLICABLE
    if im and im.scope_event is not None:
        scope_events = im.scope_event.event_type.value
    if im and im.runtime_scope_state_before is not None:
        scope_before = im.runtime_scope_state_before.now_tick
        scope_anchor = im.runtime_scope_state_before.anchor_price
    if im and im.runtime_scope_state_after is not None:
        scope_after = im.runtime_scope_state_after.now_tick

    conf_before = NOT_APPLICABLE
    conf_after = NOT_APPLICABLE
    conf_epoch = NOT_APPLICABLE
    conf_reset = NOT_APPLICABLE

    mv2_decision = NOT_APPLICABLE
    dp_decision = ev.decision_outcome
    if im and im.composition_result is not None:
        mv2_decision = im.composition_result.composition_status.value
    if im and im.entry_exit_decision is not None:
        dp_decision = im.entry_exit_decision.decision_outcome.value

    adverse_eff = fork.adverse_distance_effective if fork else NOT_APPLICABLE
    stop_raw = NOT_APPLICABLE
    stop_final = NOT_APPLICABLE
    stop_valid = NOT_APPLICABLE
    stop_fail = NOT_APPLICABLE
    if fork and isinstance(adverse_eff, (int, float)) and adverse_eff > 0 and mark > 0:
        side = str(ev.selected_side or "LONG")
        stop_raw = derive_protective_stop_price_from_adverse_exit_v0(
            selected_side=side,
            reference_price=Decimal(str(mark)),
            adverse_exit_distance=adverse_eff,
        )
        stop_final = stop_raw
        stop_valid = stop_raw is not None and stop_raw > 0
        stop_fail = NOT_APPLICABLE if stop_valid else "nonpositive_or_unresolved"

    enterish = ev.decision_outcome in ("enter_long", "enter_short")
    return {
        "EXPERIMENT_ID": EXPERIMENT_ID,
        "MODEL_ID": model_id,
        "FUTURE_PROFILE_ID": future_profile_id,
        "GENERALIZATION_PROFILE": generalization_profile,
        "PRICE_SCALE": price_scale,
        "P0": p0,
        "VOL_LEVEL": vol_level,
        "REGIME": regime_id,
        "SEED": seed,
        "FLIGHT_ID": flight_id,
        "LANE_ID": lane_id,
        "CYCLE_ID": cycle_id,
        "MARK_PRICE": mark,
        "INDEX_PRICE": im.market_context.index_price if im else NOT_APPLICABLE,
        "VOLATILITY_ESTIMATE": vol,
        "SIGMA": vol,
        "RAW_DYNAMIC_SCOPE_MAGNITUDE": fork.dynamic_scope_magnitude_input if fork else NOT_APPLICABLE,
        "UP_DISTANCE_RAW": fork.up_distance_raw if fork else NOT_APPLICABLE,
        "ADVERSE_DISTANCE_RAW": fork.adverse_distance_raw if fork else NOT_APPLICABLE,
        "REVERSAL_DISTANCE_RAW": fork.reversal_distance_raw if fork else NOT_APPLICABLE,
        "UP_DISTANCE_EFFECTIVE": fork.up_distance_effective if fork else NOT_APPLICABLE,
        "ADVERSE_DISTANCE_EFFECTIVE": fork.adverse_distance_effective if fork else NOT_APPLICABLE,
        "REVERSAL_DISTANCE_EFFECTIVE": fork.reversal_distance_effective if fork else NOT_APPLICABLE,
        "HARD_MAX_APPLIED": fork.hard_max_applied if fork else False,
        "HARD_MAX_VALUE": fork.hard_max_value if fork else NOT_APPLICABLE,
        "SCOPE_ANCHOR": scope_anchor,
        "SCOPE_STATE_BEFORE": scope_before,
        "SCOPE_EVENTS": scope_events,
        "SCOPE_STATE_AFTER": scope_after,
        "CONFIRMATION_STATE_BEFORE": conf_before,
        "CONFIRMATION_EPOCH": conf_epoch,
        "CONFIRMATION_RESET": conf_reset,
        "CONFIRMATION_STATE_AFTER": conf_after,
        "MV2_DECISION": mv2_decision,
        "MV2_REASON_CODE": NOT_APPLICABLE,
        "DOUBLE_PLAY_STATE": im.state_switch.next_side_state if im else NOT_APPLICABLE,
        "DOUBLE_PLAY_DECISION": dp_decision,
        "DECISION_OUTCOME": ev.decision_outcome,
        "DECISION_SIDE": ev.selected_side,
        "EXIT_DISPOSITION": _na(ev.decision_outcome, applicable=ev.decision_outcome.startswith("exit")),
        "PROTECTIVE_STOP_REFERENCE": mark,
        "PROTECTIVE_STOP_RAW": str(stop_raw) if stop_raw != NOT_APPLICABLE else NOT_APPLICABLE,
        "PROTECTIVE_STOP_FINALIZED": str(stop_final) if stop_final != NOT_APPLICABLE else NOT_APPLICABLE,
        "PROTECTIVE_STOP_VALID": stop_valid,
        "PROTECTIVE_STOP_FAIL_REASON": stop_fail,
        "TICK_SIZE": tick_size,
        "PRICE_PRECISION": price_precision,
        "REPLAY_PASS": result.replay_pass,
        "REPLAY_FAIL_REASON_CODES": tuple(result.fail_reasons),
        "29P_ATTEMPTED": True,
        "29P_PASS": result.replay_pass,
        "29P_FAIL_REASON_CODES": () if result.replay_pass else tuple(result.fail_reasons),
        "RISK_CONTEXT_RESOLVED": NOT_APPLICABLE,
        "RISK_PASS": NOT_APPLICABLE,
        "RISK_FAIL_REASON_CODES": NOT_APPLICABLE,
        "EXECUTION_ELIGIBLE": ev.execution_eligible,
        "EXECUTION_INELIGIBLE_REASON_CODES": NOT_APPLICABLE
        if ev.execution_eligible
        else ("execution_not_eligible",),
        "PRE_EXTERNAL_REACHED": ev.authority_effect == "NONE" and ev.order_effect == "NONE",
        "PRE_EXTERNAL_DISPOSITION": "OFFLINE_TERMINAL" if ev.order_effect == "NONE" else NOT_APPLICABLE,
        "FAIL_CLOSED": ev.decision_outcome == "blocked",
        "FAIL_CLOSED_REASON_CODES": tuple(ev.reason_codes) if ev.decision_outcome == "blocked" else (),
        "SEMANTIC_DIGEST": ev.semantic_digest,
        "NATURAL_ENTER": enterish,
    }

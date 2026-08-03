"""Observe one productive bridge cycle and emit stage telemetry (no authority)."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ACTIONABILITY_CALL_ORDER_V1,
    SCHEMA_VERSION,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.distance_v1 import (
    capture_distance_to_actionability_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    CycleTerminalRecordV1,
    ProductiveDecisionStageObservationV1,
    canonical_digest_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.stage_classifier_v1 import (
    confirmation_phase_from_carrier_v1,
    intent_bucket_from_intended_v1,
    is_distinct_accepted_v1,
    make_stage_observation_v1,
    market_state_from_features_v1,
    observation_class_from_result_v1,
    optional_attr,
    result_pass_like_v1,
    selected_side_norm_v1,
    volatility_presence_from_features_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.terminal_reason_v1 import (
    classify_terminal_outcome_v1,
    primary_reason_from_stages_v1,
)


def _as_map(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        try:
            return dict(value.to_dict())
        except Exception:  # noqa: BLE001
            return {}
    return value if isinstance(value, Mapping) else {}


def _obs_identity_str(obs: Any) -> str:
    if obs is None:
        return ""
    ident = getattr(obs, "observation_identity", None)
    if ident is None:
        return ""
    venue = getattr(ident, "venue", "")
    iid = getattr(ident, "canonical_instrument_id", "")
    et = getattr(ident, "venue_event_time", "")
    mark = getattr(ident, "mark_price", "")
    return f"{venue}:{iid}:{et}:{mark}"


def _obs_epoch(obs: Any, confirmation_binding: Any) -> int | None:
    state = None
    if obs is not None:
        state = getattr(obs, "state_after", None)
    if state is None and confirmation_binding is not None:
        state = getattr(confirmation_binding, "observation_acceptance_state", None)
    if state is None:
        return None
    epoch = getattr(state, "market_observation_epoch", None)
    if epoch is None:
        return None
    return int(getattr(epoch, "value", epoch))


def observe_productive_decision_cycle_v1(
    *,
    repository_sha: str,
    config_digest: str,
    runtime_session_id: str,
    decision_cycle_id: str,
    instrument_id: str,
    market_event_time: float | None,
    observation_acceptance_result: Any,
    observation_cycle_kind: str,
    confirmation_binding: Any,
    features: Any,
    replay: Any,
    intended: Any,
    fill: Mapping[str, Any] | None,
    exit_signals: Mapping[str, Any] | None,
    has_open_position: bool,
    position_state: str,
    scope_state: str,
    safety_result: str,
    risk_sizing_result: str,
    decision_cfg: Any = None,
    fail_closed: bool = False,
) -> tuple[tuple[ProductiveDecisionStageObservationV1, ...], CycleTerminalRecordV1]:
    """Build append-only stage observations for one already-decided productive cycle."""
    intended_map = _as_map(intended)
    intended_side = str(intended_map.get("intended_side") or "HOLD")
    decision_outcome = str(
        optional_attr(replay, "evidence", "decision_outcome", default="")
        or intended_map.get("decision_outcome")
        or ""
    )
    safety_blocked = bool(intended_map.get("safety_blocked")) or str(safety_result).upper() in {
        "BLOCKED_HOLD",
        "BLOCKED",
        "VETO",
        "EXIT_ONLY",
    }
    intermediate = optional_attr(replay, "intermediate", default=None)
    evidence = optional_attr(replay, "evidence", default=None)
    carrier_after = optional_attr(
        intermediate, "directional_confirmation_progress_after", default=None
    )
    if carrier_after is None and confirmation_binding is not None:
        carrier_after = getattr(confirmation_binding, "confirmation_side_carrier", None)
    confirmation_phase = confirmation_phase_from_carrier_v1(carrier_after)
    confirmation_session_id = ""
    if confirmation_binding is not None:
        confirmation_session_id = str(
            getattr(confirmation_binding, "confirmation_session_id", "") or ""
        )
    obs_identity = _obs_identity_str(observation_acceptance_result)
    obs_epoch = _obs_epoch(observation_acceptance_result, confirmation_binding)
    obs_class = observation_class_from_result_v1(observation_acceptance_result)
    kind = str(observation_cycle_kind or "").lower()
    distinct = is_distinct_accepted_v1(observation_acceptance_result)
    intent_bucket = intent_bucket_from_intended_v1(intended_map)
    entry_actionable = intent_bucket == "ENTRY"
    reduce_actionable = intent_bucket == "REDUCE"
    exit_actionable = intent_bucket == "EXIT"

    # Early terminal classification for short-circuit not_reached marking.
    early_missing = (
        kind in {"missing", "no_sample", "decision_cycle_only"}
        or obs_class == "missing"
        or observation_acceptance_result is None
        and kind in {"", "missing", "no_sample"}
    )
    early_duplicate = obs_class == "duplicate" or kind == "duplicate_sample"
    early_stale = obs_class in {"out_of_order", "invalid_event_time"} or "stale" in obs_class

    reached_until = len(ACTIONABILITY_CALL_ORDER_V1) - 1
    if early_missing:
        reached_until = 1  # public_market_observation
    elif early_duplicate or early_stale:
        reached_until = 3  # distinct_observation_acceptance
    elif not distinct:
        # Still evaluate features for diagnostics when host did, but mark blockers.
        reached_until = 4

    fmap = _as_map(features)
    features_ok = bool(fmap.get("ok", False)) and bool(fmap.get("warmup_complete", False))
    vol_state = volatility_presence_from_features_v1(features)
    market_state = market_state_from_features_v1(features)

    common = dict(
        repository_sha=repository_sha,
        config_digest=config_digest,
        runtime_session_id=runtime_session_id,
        decision_cycle_id=decision_cycle_id,
        instrument_id=instrument_id,
        market_event_time=market_event_time,
        observation_identity=obs_identity,
        observation_epoch=obs_epoch,
        confirmation_session_id=confirmation_session_id,
        intended_side=intended_side,
        position_state=str(position_state),
        scope_state=str(scope_state),
        confirmation_phase=confirmation_phase,
        entry_actionable=entry_actionable,
        reduce_actionable=reduce_actionable,
        exit_actionable=exit_actionable,
    )

    stages: list[ProductiveDecisionStageObservationV1] = []

    def add(**kwargs: Any) -> None:
        stages.append(make_stage_observation_v1(**common, **kwargs))

    # 0 instrument_selection
    add(
        stage="instrument_selection",
        input_state={"instrument_id": instrument_id},
        output_state={"instrument_id": instrument_id},
        evaluated=True,
        passed=bool(instrument_id),
        blocked=not bool(instrument_id),
        not_reached=False,
        not_applicable=False,
        decision="bound" if instrument_id else "missing",
        reason_code="INSTRUMENT_BOUND" if instrument_id else "INSTRUMENT_MISSING",
        reason_detail="",
        authority_symbol="ensure_single_selected_future_runtime_binding_v1",
        terminal_for_cycle=False,
        terminal_blocking_stage=not bool(instrument_id),
    )

    # 1 public_market_observation
    missing_obs = early_missing
    add(
        stage="public_market_observation",
        input_state={"kind": kind, "market_event_time": market_event_time},
        output_state={"observed": not missing_obs},
        evaluated=True,
        passed=not missing_obs,
        blocked=missing_obs,
        not_reached=False,
        not_applicable=False,
        decision="missing" if missing_obs else "observed",
        reason_code="MISSING_MARKET_TRUTH" if missing_obs else "MARKET_OBSERVATION_PRESENT",
        reason_detail=kind,
        authority_symbol="BridgeSessionStateV1.append_mid",
        terminal_for_cycle=missing_obs,
        terminal_blocking_stage=missing_obs,
    )

    # 2 observation_identity
    identity_ok = bool(obs_identity) and not missing_obs
    add(
        stage="observation_identity",
        input_state={"kind": kind},
        output_state={"observation_identity": obs_identity},
        evaluated=not missing_obs,
        passed=identity_ok,
        blocked=(not identity_ok) and not missing_obs,
        not_reached=missing_obs,
        not_applicable=False,
        decision="present" if identity_ok else "absent",
        reason_code="OBSERVATION_IDENTITY_PRESENT"
        if identity_ok
        else "OBSERVATION_IDENTITY_ABSENT",
        reason_detail="",
        authority_symbol="ObservationIdentityV1",
        terminal_for_cycle=False,
        terminal_blocking_stage=(not identity_ok) and not missing_obs,
    )

    # 3 distinct_observation_acceptance
    acc_blocked = (not distinct) and not missing_obs
    add(
        stage="distinct_observation_acceptance",
        input_state={"classification": obs_class, "kind": kind},
        output_state={
            "strategy_advance_allowed": bool(
                getattr(observation_acceptance_result, "strategy_advance_allowed", False)
            )
            if observation_acceptance_result is not None
            else False
        },
        evaluated=not missing_obs,
        passed=distinct,
        blocked=acc_blocked,
        not_reached=missing_obs,
        not_applicable=False,
        decision=obs_class if obs_class else ("missing" if missing_obs else "unknown"),
        reason_code=str(
            getattr(observation_acceptance_result, "reason_code", "")
            or obs_class
            or ("MISSING" if missing_obs else "UNKNOWN")
        ),
        reason_detail="",
        authority_symbol="evaluate_host_observation_acceptance_v1",
        terminal_for_cycle=acc_blocked,
        terminal_blocking_stage=acc_blocked,
    )

    # Helper: not_reached after acceptance short-circuit.
    def beyond_acceptance_not_reached() -> bool:
        return missing_obs or early_duplicate or early_stale

    # 4 features
    feat_nr = beyond_acceptance_not_reached()
    feat_blocked = (not features_ok) and not feat_nr
    add(
        stage="features",
        input_state={"warmup_complete": fmap.get("warmup_complete"), "ok": fmap.get("ok")},
        output_state={"regime_id": fmap.get("regime_id"), "mark_price": fmap.get("mark_price")},
        evaluated=not feat_nr,
        passed=features_ok and not feat_nr,
        blocked=feat_blocked,
        not_reached=feat_nr,
        not_applicable=False,
        decision="ready" if features_ok else "blocked",
        reason_code="FEATURES_READY" if features_ok else "FEATURES_NOT_READY",
        reason_detail="",
        authority_symbol="compute_feature_regime_from_mid_prices_v1",
        terminal_for_cycle=feat_blocked,
        terminal_blocking_stage=feat_blocked,
    )

    # 5 typed volatility presence
    vol_nr = feat_nr or not features_ok
    vol_present = vol_state == "present"
    add(
        stage="typed_volatility_presence",
        input_state={"volatility_estimate": fmap.get("volatility_estimate")},
        output_state={"presence": vol_state},
        evaluated=not vol_nr,
        passed=vol_present and not vol_nr,
        blocked=(not vol_present) and not vol_nr,
        not_reached=vol_nr,
        not_applicable=False,
        decision=vol_state,
        reason_code="VOLATILITY_PRESENT" if vol_present else "VOLATILITY_MISSING",
        reason_detail="",
        authority_symbol="CanonicalMarketContextV1.volatility_estimate",
        terminal_for_cycle=False,  # diagnostic presence; may not hard-block alpha
        terminal_blocking_stage=False,
    )

    # 6 market state / bull-bear
    mkt_nr = vol_nr
    mkt_unclassified = market_state == "unclassified"
    add(
        stage="market_state_bull_bear",
        input_state={"regime_id": fmap.get("regime_id")},
        output_state={"market_state": market_state},
        evaluated=not mkt_nr,
        passed=(not mkt_unclassified) and not mkt_nr,
        blocked=mkt_unclassified and not mkt_nr,
        not_reached=mkt_nr,
        not_applicable=False,
        decision=market_state,
        reason_code="MARKET_STATE_CLASSIFIED"
        if not mkt_unclassified
        else "MARKET_STATE_UNCLASSIFIED",
        reason_detail="",
        authority_symbol="DirectionalAssessmentV1",
        terminal_for_cycle=mkt_unclassified and not mkt_nr,
        terminal_blocking_stage=mkt_unclassified and not mkt_nr,
    )

    # 7 directional confirmation
    conf_nr = mkt_nr or mkt_unclassified
    conf_phase = confirmation_phase
    conf_blocked = conf_phase in {"observe", "invalid", "uninitialized"} and not conf_nr
    # candidate/confirmed are progress; observe is not yet actionable
    add(
        stage="directional_confirmation",
        input_state={"phase_before": conf_phase},
        output_state={"phase": conf_phase},
        evaluated=not conf_nr,
        passed=conf_phase in {"candidate", "confirmed"} and not conf_nr,
        blocked=conf_blocked and conf_phase in {"observe", "invalid", "uninitialized"},
        not_reached=conf_nr,
        not_applicable=False,
        decision=conf_phase,
        reason_code=f"CONFIRMATION_{conf_phase.upper()}",
        reason_detail="",
        authority_symbol="DirectionalConfirmationSideStateCarrierV1",
        terminal_for_cycle=conf_blocked and conf_phase in {"observe", "invalid", "uninitialized"},
        terminal_blocking_stage=conf_blocked
        and conf_phase in {"observe", "invalid", "uninitialized"}
        and intent_bucket == "NONE",
    )

    # 8 master_v2
    mv2_nr = conf_nr
    mv2_side = selected_side_norm_v1(optional_attr(evidence, "selected_side", default="hold"))
    # Prefer next_direction_state when selected_side empty.
    if mv2_side == "hold":
        mv2_side = selected_side_norm_v1(
            optional_attr(evidence, "next_direction_state", default="hold")
        )
    mv2_blocked = str(decision_outcome).lower() == "blocked" and not mv2_nr
    mv2_decision = (
        mv2_side if mv2_side in {"long", "short"} else ("blocked" if mv2_blocked else "hold")
    )
    add(
        stage="master_v2",
        input_state={"decision_outcome": decision_outcome},
        output_state={"selected_side": mv2_side, "decision_outcome": decision_outcome},
        evaluated=not mv2_nr,
        passed=mv2_decision in {"long", "short"} and not mv2_nr,
        blocked=mv2_blocked,
        not_reached=mv2_nr,
        not_applicable=False,
        decision=mv2_decision,
        reason_code=str((optional_attr(evidence, "reason_codes", default=()) or ("MASTER_V2",))[0]),
        reason_detail="",
        authority_symbol="run_integrated_offline_trading_logic_replay_v1",
        terminal_for_cycle=mv2_blocked,
        terminal_blocking_stage=mv2_blocked,
    )

    # 9 double_play
    dp_nr = mv2_nr
    entry_exit = optional_attr(intermediate, "entry_exit_decision", default=None)
    dp_outcome = str(
        getattr(getattr(entry_exit, "outcome", None), "value", getattr(entry_exit, "outcome", ""))
        or decision_outcome
        or "hold"
    ).lower()
    dp_side = selected_side_norm_v1(getattr(entry_exit, "selected_side", None) or mv2_side)
    if "enter_long" in dp_outcome or dp_outcome == "long":
        dp_decision = "long"
    elif "enter_short" in dp_outcome or dp_outcome == "short":
        dp_decision = "short"
    elif "block" in dp_outcome:
        dp_decision = "blocked"
    else:
        dp_decision = "hold" if dp_side == "hold" else dp_side
    dp_blocked = dp_decision == "blocked" and not dp_nr
    add(
        stage="double_play",
        input_state={"entry_exit_outcome": dp_outcome},
        output_state={"decision": dp_decision},
        evaluated=not dp_nr,
        passed=dp_decision in {"long", "short"} and not dp_nr,
        blocked=dp_blocked,
        not_reached=dp_nr,
        not_applicable=False,
        decision=dp_decision,
        reason_code="DOUBLE_PLAY_" + dp_decision.upper(),
        reason_detail="",
        authority_symbol="evaluate_double_play_entry_exit_policy_v0",
        terminal_for_cycle=dp_blocked,
        terminal_blocking_stage=dp_blocked,
    )

    # 10 dynamic_scope
    scope_nr = dp_nr or dp_decision not in {"long", "short", "hold"}
    # Scope is evaluated whenever intermediate has scope event and acceptance advanced.
    scope_event = optional_attr(intermediate, "scope_event", default=None)
    runtime_reinit = bool(optional_attr(intermediate, "runtime_scope_reinitialized", default=False))
    scope_before = optional_attr(intermediate, "runtime_scope_state_before", default=None)
    scope_after = optional_attr(intermediate, "runtime_scope_state_after", default=None)
    scope_created = scope_before is None and scope_after is not None
    scope_transition = scope_before is not None and scope_after is not None and not runtime_reinit
    if beyond_acceptance_not_reached() or intermediate is None:
        scope_nr = True
    scope_decision = (
        "not_reached"
        if scope_nr
        else ("created" if scope_created else ("transition" if scope_transition else "evaluated"))
    )
    scope_blocked = False
    if scope_event is not None:
        blocks = getattr(scope_event, "block_reasons", None) or getattr(scope_event, "blocks", None)
        if blocks:
            scope_blocked = True
    add(
        stage="dynamic_scope",
        input_state={"had_previous_scope": scope_before is not None},
        output_state={"decision": scope_decision, "reinitialized": runtime_reinit},
        evaluated=not scope_nr,
        passed=(not scope_nr) and not scope_blocked,
        blocked=scope_blocked and not scope_nr,
        not_reached=scope_nr,
        not_applicable=False,
        decision=scope_decision,
        reason_code="DYNAMIC_SCOPE_" + scope_decision.upper(),
        reason_detail="",
        authority_symbol="commit_host_dynamic_scope_after_replay_v1",
        terminal_for_cycle=scope_blocked and not scope_nr,
        terminal_blocking_stage=scope_blocked and not scope_nr,
    )

    def _side_pass(bull: Any, bear: Any) -> tuple[bool, bool, str]:
        bp = result_pass_like_v1(bull)
        ep = result_pass_like_v1(bear)
        if bp is True or ep is True:
            return True, False, "pass"
        if bp is False and ep is False:
            return False, True, "blocked"
        if bp is False or ep is False:
            # one side blocked, other unknown → treat as evaluated blocked if both known fail
            return False, True, "blocked"
        return False, False, "unevaluated"

    # 11 survival
    surv_nr = scope_nr and beyond_acceptance_not_reached()
    if intermediate is None or beyond_acceptance_not_reached():
        surv_nr = True
    else:
        surv_nr = False
    bull_s = optional_attr(intermediate, "bull_survival", default=None)
    bear_s = optional_attr(intermediate, "bear_survival", default=None)
    surv_pass, surv_block, surv_decision = _side_pass(bull_s, bear_s)
    if surv_nr:
        surv_pass, surv_block, surv_decision = False, False, "not_reached"
    add(
        stage="survival",
        input_state={},
        output_state={"decision": surv_decision},
        evaluated=not surv_nr,
        passed=surv_pass,
        blocked=surv_block,
        not_reached=surv_nr,
        not_applicable=False,
        decision=surv_decision,
        reason_code="SURVIVAL_" + surv_decision.upper(),
        reason_detail="",
        authority_symbol="evaluate_survival_assessment_v1",
        terminal_for_cycle=surv_block,
        terminal_blocking_stage=surv_block,
    )

    # 12 suitability
    suit_nr = surv_nr or surv_block
    bull_u = optional_attr(intermediate, "bull_suitability", default=None)
    bear_u = optional_attr(intermediate, "bear_suitability", default=None)
    if intermediate is None or beyond_acceptance_not_reached():
        suit_nr = True
    suit_pass, suit_block, suit_decision = _side_pass(bull_u, bear_u)
    if suit_nr:
        suit_pass, suit_block, suit_decision = False, False, "not_reached"
    add(
        stage="suitability",
        input_state={},
        output_state={"decision": suit_decision},
        evaluated=not suit_nr,
        passed=suit_pass,
        blocked=suit_block,
        not_reached=suit_nr,
        not_applicable=False,
        decision=suit_decision,
        reason_code="SUITABILITY_" + suit_decision.upper(),
        reason_detail="",
        authority_symbol="evaluate_suitability_binding_v1",
        terminal_for_cycle=suit_block,
        terminal_blocking_stage=suit_block,
    )

    # 13 composition
    comp = optional_attr(intermediate, "composition_result", default=None)
    comp_nr = suit_nr or suit_block or intermediate is None or beyond_acceptance_not_reached()
    selected = selected_side_norm_v1(getattr(comp, "selected_side", None) if comp else None)
    comp_blocked = False
    comp_pass = False
    if not comp_nr and comp is not None:
        outcome = str(
            getattr(getattr(comp, "outcome", None), "value", getattr(comp, "outcome", "")) or ""
        ).lower()
        if "block" in outcome or selected in {"", "hold", "neutral", "none"}:
            # hold/neutral is not necessarily a hard block; treat directional as pass
            if selected in {"long", "short"}:
                comp_pass = True
            elif "block" in outcome:
                comp_blocked = True
            else:
                comp_pass = False
                comp_blocked = False
        else:
            comp_pass = selected in {"long", "short"}
    comp_decision = (
        "not_reached"
        if comp_nr
        else ("blocked" if comp_blocked else (selected if selected else "hold"))
    )
    add(
        stage="composition",
        input_state={},
        output_state={"selected_side": selected},
        evaluated=not comp_nr,
        passed=comp_pass,
        blocked=comp_blocked,
        not_reached=comp_nr,
        not_applicable=False,
        decision=comp_decision,
        reason_code="COMPOSITION_" + comp_decision.upper(),
        reason_detail="",
        authority_symbol="DoublePlayCompositionMatrixV1",
        terminal_for_cycle=comp_blocked,
        terminal_blocking_stage=comp_blocked,
    )

    # 14 risk
    risk_nr = comp_nr or beyond_acceptance_not_reached()
    risk_text = str(risk_sizing_result or "").upper()
    risk_veto = any(x in risk_text for x in ("VETO", "BLOCK", "REJECT"))
    risk_pass = (not risk_veto) and not risk_nr and bool(risk_text)
    if not risk_text and not risk_nr:
        risk_pass = True  # NONE / empty treated as pass-through when evaluated
        risk_text = "NONE"
    add(
        stage="risk",
        input_state={"risk_sizing_result": risk_sizing_result},
        output_state={"result": risk_text},
        evaluated=not risk_nr,
        passed=risk_pass and not risk_veto,
        blocked=risk_veto and not risk_nr,
        not_reached=risk_nr,
        not_applicable=False,
        decision="veto" if risk_veto else "pass",
        reason_code=risk_text or "RISK_UNEVALUATED",
        reason_detail="",
        authority_symbol="CapitalRiskSizingDecisionV1",
        terminal_for_cycle=risk_veto and not risk_nr,
        terminal_blocking_stage=risk_veto and not risk_nr,
    )

    # 15 safety
    safety_nr = risk_nr or (risk_veto and intent_bucket == "NONE")
    if beyond_acceptance_not_reached():
        safety_nr = True
    safety_veto = safety_blocked
    add(
        stage="safety",
        input_state={"safety_result": safety_result},
        output_state={"safety_blocked": safety_blocked},
        evaluated=not safety_nr,
        passed=(not safety_veto) and not safety_nr,
        blocked=safety_veto and not safety_nr,
        not_reached=safety_nr,
        not_applicable=False,
        decision="veto" if safety_veto else "pass",
        reason_code=str(safety_result or "SAFETY"),
        reason_detail="",
        authority_symbol="safety_kernel",
        terminal_for_cycle=safety_veto and not safety_nr,
        terminal_blocking_stage=safety_veto and not safety_nr,
    )

    # 16 exit_policy
    signals = exit_signals or {}
    any_triggered = any(
        bool(_as_map(v).get("triggered")) for v in signals.values() if v is not None
    )
    exit_nr = beyond_acceptance_not_reached()
    exit_evaluated = has_open_position and not exit_nr
    add(
        stage="exit_policy",
        input_state={"has_open_position": has_open_position},
        output_state={"triggered": any_triggered},
        evaluated=exit_evaluated,
        passed=any_triggered if exit_evaluated else False,
        blocked=False,
        not_reached=(not has_open_position) or exit_nr,
        not_applicable=not has_open_position and not exit_nr,
        decision="triggered"
        if any_triggered
        else ("evaluated" if exit_evaluated else "not_applicable"),
        reason_code="EXIT_POLICY_TRIGGERED" if any_triggered else "EXIT_POLICY_QUIET",
        reason_detail="",
        authority_symbol="evaluate_host_exit_policy_producers_v1",
        terminal_for_cycle=False,
        terminal_blocking_stage=False,
    )

    # 17 canonical_intent
    intent_nr = beyond_acceptance_not_reached()
    intent_decision = (
        intent_bucket.lower()
        if intent_bucket != "NONE"
        else (
            "hold"
            if str(decision_outcome).lower() in {"hold", "observe", ""}
            else str(decision_outcome).lower()
        )
    )
    add(
        stage="canonical_intent",
        input_state={"decision_outcome": decision_outcome},
        output_state=dict(intended_map),
        evaluated=not intent_nr,
        passed=intent_bucket in {"ENTRY", "REDUCE", "EXIT"} and not intent_nr,
        blocked=False,
        not_reached=intent_nr,
        not_applicable=False,
        decision=intent_decision,
        reason_code=str(
            (intended_map.get("reason_codes") or ["CANONICAL_INTENT"])[0]
            if isinstance(intended_map.get("reason_codes"), (list, tuple))
            else intended_map.get("reason_codes") or "CANONICAL_INTENT"
        ),
        reason_detail="",
        authority_symbol="map_replay_result_to_intended_analytical_action_v1",
        terminal_for_cycle=intent_bucket == "NONE" and not intent_nr,
        terminal_blocking_stage=intent_bucket == "NONE" and not intent_nr,
    )

    # 18 simulated_execution
    exec_nr = intent_nr or intent_bucket == "NONE"
    fill_present = fill is not None and bool(fill)
    add(
        stage="simulated_execution",
        input_state={"intent_bucket": intent_bucket},
        output_state={"fill_present": fill_present},
        evaluated=not exec_nr,
        passed=fill_present and not exec_nr,
        blocked=False,
        not_reached=exec_nr,
        not_applicable=intent_bucket == "NONE",
        decision="filled" if fill_present else ("no_fill" if not exec_nr else "not_reached"),
        reason_code="SIMULATED_FILL" if fill_present else "NO_SIMULATED_FILL",
        reason_detail="",
        authority_symbol="apply_intended_action_via_canonical_accounting_v1",
        terminal_for_cycle=False,
        terminal_blocking_stage=False,
    )

    terminal_outcome = classify_terminal_outcome_v1(
        observation_acceptance_result=observation_acceptance_result,
        intended=intended_map,
        decision_outcome=decision_outcome,
        safety_blocked=safety_blocked,
        fail_closed=fail_closed,
    )
    # Refine NO_SAMPLE using cycle kind.
    if kind in {"missing", "no_sample", "decision_cycle_only"} and intent_bucket == "NONE":
        terminal_outcome = "NO_SAMPLE"

    primary, secondary, blocking_stage, blocking_index = primary_reason_from_stages_v1(
        stages, terminal_outcome=terminal_outcome
    )

    # Distance diagnostics from already-computed productive values only.
    epochs_required = None
    if decision_cfg is not None:
        epochs_required = getattr(decision_cfg, "confirmation_epochs", None)
    epochs_current = None
    if carrier_after is not None:
        for side_name in ("bull_confirmation_state", "bear_confirmation_state"):
            side = getattr(carrier_after, side_name, None)
            if side is None:
                continue
            cur = getattr(side, "epochs_observed", None)
            if cur is None:
                cur = getattr(side, "confirmation_epochs", None)
            if cur is not None:
                epochs_current = int(cur)
                break
    measure = None
    if fmap.get("momentum_features"):
        measure = (_as_map(fmap.get("momentum_features"))).get("roc")
    distance = capture_distance_to_actionability_v1(
        confirmation_epochs_required=None if epochs_required is None else int(epochs_required),
        confirmation_epochs_current=epochs_current,
        observe_threshold=0.001,
        candidate_threshold=0.005,
        confirm_threshold=0.01,
        actual_directional_measure=None if measure is None else float(measure),
        scope_boundary=None,
        current_price=None if fmap.get("mark_price") is None else float(fmap.get("mark_price")),
        composition_required_conditions=None,
        composition_satisfied_conditions=None,
        risk_headroom=None,
        safety_state=str(safety_result or "") or None,
    )

    terminal = CycleTerminalRecordV1(
        schema_version=SCHEMA_VERSION,
        repository_sha=repository_sha,
        config_digest=config_digest,
        runtime_session_id=runtime_session_id,
        decision_cycle_id=decision_cycle_id,
        instrument_id=instrument_id,
        market_event_time=market_event_time,
        terminal_outcome=terminal_outcome,
        primary_reason=primary,
        secondary_reasons=secondary,
        terminal_blocking_stage=blocking_stage,
        terminal_blocking_stage_index=blocking_index,
        entry_actionable=entry_actionable,
        reduce_actionable=reduce_actionable,
        exit_actionable=exit_actionable,
        intended_side=intended_side,
        decision_outcome=decision_outcome,
        distance_to_actionability=distance.to_dict(),
        stage_event_count=len(stages),
        event_digest="",
    )
    terminal.event_digest = canonical_digest_v1(
        {
            "stages": [s.to_dict() for s in stages],
            "terminal": {k: v for k, v in terminal.to_dict().items() if k != "event_digest"},
        }
    )
    return tuple(stages), terminal

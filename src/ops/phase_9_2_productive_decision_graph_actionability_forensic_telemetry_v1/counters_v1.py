"""Aggregate gate counters from stage observations + cycle terminals."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    GATE_COUNTER_KEYS,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    CycleTerminalRecordV1,
    ProductiveDecisionStageObservationV1,
    empty_counters_v1,
)


def _stage_map(
    stages: Sequence[ProductiveDecisionStageObservationV1],
) -> dict[str, ProductiveDecisionStageObservationV1]:
    return {s.stage: s for s in stages}


def increment_counters_for_cycle_v1(
    counters: dict[str, int],
    *,
    stages: Sequence[ProductiveDecisionStageObservationV1],
    terminal: CycleTerminalRecordV1,
    observation_kind: str = "",
) -> dict[str, int]:
    c = counters
    c["TOTAL_CYCLES"] += 1
    kind = str(observation_kind or "").lower()
    sm = _stage_map(stages)

    obs = sm.get("public_market_observation")
    if obs and not obs.not_reached:
        c["TOTAL_MARKET_OBSERVATIONS"] += 1

    acc = sm.get("distinct_observation_acceptance")
    if acc is not None:
        decision = acc.decision.lower()
        if decision == "distinct" and acc.passed:
            c["DISTINCT_OBSERVATIONS"] += 1
        elif decision == "duplicate" or terminal.terminal_outcome == "DUPLICATE_SAMPLE":
            c["DUPLICATE_OBSERVATIONS"] += 1
        elif decision == "missing" or terminal.terminal_outcome == "NO_SAMPLE" or "missing" in kind:
            c["MISSING_OBSERVATIONS"] += 1
        elif (
            decision in {"out_of_order", "stale", "invalid_event_time"}
            or terminal.terminal_outcome == "STALE_SAMPLE"
        ):
            c["STALE_OBSERVATIONS"] += 1

    feat = sm.get("features")
    if feat is not None and feat.evaluated:
        c["FEATURES_EVALUATED"] += 1
        if feat.blocked:
            c["FEATURES_BLOCKED"] += 1

    vol = sm.get("typed_volatility_presence")
    if vol is not None and vol.evaluated:
        if vol.passed:
            c["VOLATILITY_PRESENT"] += 1
        elif vol.blocked:
            c["VOLATILITY_MISSING"] += 1
        if "stale" in vol.reason_code.lower():
            c["VOLATILITY_STALE_DIAGNOSTIC"] += 1

    mkt = sm.get("market_state_bull_bear")
    if mkt is not None and mkt.evaluated:
        d = mkt.decision.lower()
        if d == "bull":
            c["BULL_STATE_COUNT"] += 1
        elif d == "bear":
            c["BEAR_STATE_COUNT"] += 1
        elif d == "unclassified":
            c["UNCLASSIFIED_MARKET_STATE_COUNT"] += 1
        # else: classified non-directional regime label (counted via funnel, not bull/bear)

    conf = sm.get("directional_confirmation")
    if conf is not None and conf.evaluated:
        phase = conf.confirmation_phase.lower()
        if phase == "observe":
            c["CONFIRMATION_OBSERVE_COUNT"] += 1
        elif phase == "candidate":
            c["CONFIRMATION_CANDIDATE_COUNT"] += 1
        elif phase == "confirmed":
            c["CONFIRMATION_CONFIRMED_COUNT"] += 1
        elif phase == "invalid":
            c["CONFIRMATION_INVALIDATED_COUNT"] += 1
        if "expir" in conf.reason_code.lower():
            c["CONFIRMATION_EXPIRED_COUNT"] += 1
        if conf.blocked:
            c["CONFIRMATION_BLOCKED_COUNT"] += 1

    mv2 = sm.get("master_v2")
    if mv2 is not None and mv2.evaluated:
        d = mv2.decision.lower()
        if d == "long":
            c["MASTER_V2_LONG_COUNT"] += 1
        elif d == "short":
            c["MASTER_V2_SHORT_COUNT"] += 1
        elif mv2.blocked:
            c["MASTER_V2_BLOCKED_COUNT"] += 1
        else:
            c["MASTER_V2_HOLD_COUNT"] += 1

    dp = sm.get("double_play")
    if dp is not None and dp.evaluated:
        d = dp.decision.lower()
        if d == "long":
            c["DOUBLE_PLAY_LONG_COUNT"] += 1
        elif d == "short":
            c["DOUBLE_PLAY_SHORT_COUNT"] += 1
        elif dp.blocked:
            c["DOUBLE_PLAY_BLOCKED_COUNT"] += 1
        else:
            c["DOUBLE_PLAY_HOLD_COUNT"] += 1

    scope = sm.get("dynamic_scope")
    if scope is None or scope.not_reached:
        c["DYNAMIC_SCOPE_NOT_REACHED_COUNT"] += 1
    elif scope.evaluated:
        c["DYNAMIC_SCOPE_EVALUATED_COUNT"] += 1
        if scope.decision == "created":
            c["DYNAMIC_SCOPE_CREATED_COUNT"] += 1
        if scope.decision == "transition":
            c["DYNAMIC_SCOPE_TRANSITION_COUNT"] += 1
        if scope.blocked:
            c["DYNAMIC_SCOPE_BLOCKED_COUNT"] += 1

    for stage_name, pass_key, block_key in (
        ("survival", "SURVIVAL_PASS_COUNT", "SURVIVAL_BLOCK_COUNT"),
        ("suitability", "SUITABILITY_PASS_COUNT", "SUITABILITY_BLOCK_COUNT"),
        ("composition", "COMPOSITION_PASS_COUNT", "COMPOSITION_BLOCK_COUNT"),
    ):
        st = sm.get(stage_name)
        if st is not None and st.evaluated:
            if st.passed:
                c[pass_key] += 1
            if st.blocked:
                c[block_key] += 1

    risk = sm.get("risk")
    if risk is not None and risk.evaluated:
        if risk.passed:
            c["RISK_PASS_COUNT"] += 1
        if risk.blocked:
            c["RISK_VETO_COUNT"] += 1

    safety = sm.get("safety")
    if safety is not None and safety.evaluated:
        if safety.passed:
            c["SAFETY_PASS_COUNT"] += 1
        if safety.blocked:
            c["SAFETY_VETO_COUNT"] += 1

    exit_st = sm.get("exit_policy")
    if exit_st is not None and exit_st.evaluated:
        c["EXIT_POLICY_EVALUATED_COUNT"] += 1
        if (
            exit_st.decision == "triggered"
            or exit_st.passed
            and "trigger" in exit_st.reason_code.lower()
        ):
            c["EXIT_POLICY_TRIGGERED_COUNT"] += 1
        if exit_st.blocked:
            c["EXIT_POLICY_BLOCKED_COUNT"] += 1

    outcome = terminal.terminal_outcome
    if outcome == "ENTRY_INTENT":
        c["ENTRY_INTENT_COUNT"] += 1
    elif outcome == "REDUCE_INTENT":
        c["REDUCE_INTENT_COUNT"] += 1
    elif outcome == "EXIT_INTENT":
        c["EXIT_INTENT_COUNT"] += 1
    elif outcome == "HOLD":
        c["HOLD_COUNT"] += 1
        c["NO_INTENT_COUNT"] += 1
    else:
        c["NO_INTENT_COUNT"] += 1
    return c


def new_gate_counters_v1() -> dict[str, int]:
    return empty_counters_v1(GATE_COUNTER_KEYS)


def counters_match_raw_events_v1(
    counters: Mapping[str, int],
    terminals: Sequence[CycleTerminalRecordV1],
) -> bool:
    if int(counters.get("TOTAL_CYCLES", -1)) != len(terminals):
        return False
    entry = sum(1 for t in terminals if t.terminal_outcome == "ENTRY_INTENT")
    reduce = sum(1 for t in terminals if t.terminal_outcome == "REDUCE_INTENT")
    exit_n = sum(1 for t in terminals if t.terminal_outcome == "EXIT_INTENT")
    hold = sum(1 for t in terminals if t.terminal_outcome == "HOLD")
    return (
        int(counters.get("ENTRY_INTENT_COUNT", 0)) == entry
        and int(counters.get("REDUCE_INTENT_COUNT", 0)) == reduce
        and int(counters.get("EXIT_INTENT_COUNT", 0)) == exit_n
        and int(counters.get("HOLD_COUNT", 0)) == hold
    )


def histogram_from_terminals_v1(
    terminals: Sequence[CycleTerminalRecordV1],
) -> dict[str, Any]:
    primary: dict[str, int] = {}
    secondary: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    for t in terminals:
        outcomes[t.terminal_outcome] = outcomes.get(t.terminal_outcome, 0) + 1
        if t.primary_reason:
            primary[t.primary_reason] = primary.get(t.primary_reason, 0) + 1
        for r in t.secondary_reasons:
            secondary[r] = secondary.get(r, 0) + 1
    return {
        "terminal_outcomes": outcomes,
        "primary_reasons": primary,
        "secondary_reasons": secondary,
    }

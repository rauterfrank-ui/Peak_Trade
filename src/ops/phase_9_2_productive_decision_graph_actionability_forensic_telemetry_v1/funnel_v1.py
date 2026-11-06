"""Entry/exit actionability funnels bound to productive stage outcomes."""

from __future__ import annotations

from typing import Mapping, Sequence

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ENTRY_FUNNEL_KEYS,
    EXIT_FUNNEL_KEYS,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    CycleTerminalRecordV1,
    ProductiveDecisionStageObservationV1,
    empty_counters_v1,
)


def new_entry_funnel_v1() -> dict[str, int]:
    return empty_counters_v1(ENTRY_FUNNEL_KEYS)


def new_exit_funnel_v1() -> dict[str, int]:
    return empty_counters_v1(EXIT_FUNNEL_KEYS)


def _sm(
    stages: Sequence[ProductiveDecisionStageObservationV1],
) -> dict[str, ProductiveDecisionStageObservationV1]:
    return {s.stage: s for s in stages}


def update_entry_funnel_v1(
    funnel: dict[str, int],
    *,
    stages: Sequence[ProductiveDecisionStageObservationV1],
    terminal: CycleTerminalRecordV1,
) -> dict[str, int]:
    sm = _sm(stages)
    acc = sm.get("distinct_observation_acceptance")
    if acc and acc.passed and acc.decision == "distinct":
        funnel["accepted_observation_count"] += 1
    else:
        return funnel

    feat = sm.get("features")
    if not (feat and feat.passed):
        return funnel
    funnel["features_ready_count"] += 1

    mkt = sm.get("market_state_bull_bear")
    if not (mkt and mkt.evaluated and mkt.decision != "unclassified"):
        return funnel
    funnel["market_state_classified_count"] += 1

    conf = sm.get("directional_confirmation")
    # Candidate funnel stage includes cycles that already progressed to confirmed.
    if conf and conf.confirmation_phase in {"candidate", "confirmed"}:
        funnel["confirmation_candidate_count"] += 1
    if not (conf and conf.confirmation_phase == "confirmed"):
        return funnel
    funnel["confirmation_confirmed_count"] += 1

    mv2 = sm.get("master_v2")
    if not (mv2 and mv2.decision in {"long", "short"}):
        return funnel
    funnel["master_v2_directional_count"] += 1

    dp = sm.get("double_play")
    if not (dp and dp.decision in {"long", "short"}):
        return funnel
    funnel["double_play_directional_count"] += 1

    scope = sm.get("dynamic_scope")
    if not (scope and scope.passed and not scope.not_reached):
        return funnel
    funnel["dynamic_scope_ready_count"] += 1

    for stage_name, key in (
        ("survival", "survival_pass_count"),
        ("suitability", "suitability_pass_count"),
        ("composition", "composition_pass_count"),
        ("risk", "risk_pass_count"),
        ("safety", "safety_pass_count"),
    ):
        st = sm.get(stage_name)
        if not (st and st.passed):
            return funnel
        funnel[key] += 1

    intent = sm.get("canonical_intent")
    if intent and intent.entry_actionable:
        funnel["entry_actionable_count"] += 1
    if terminal.terminal_outcome == "ENTRY_INTENT":
        funnel["entry_intent_count"] += 1
    return funnel


def update_exit_funnel_v1(
    funnel: dict[str, int],
    *,
    stages: Sequence[ProductiveDecisionStageObservationV1],
    terminal: CycleTerminalRecordV1,
    has_open_position: bool,
) -> dict[str, int]:
    if not has_open_position:
        return funnel
    funnel["open_position_cycles"] += 1
    sm = _sm(stages)
    exit_st = sm.get("exit_policy")
    if exit_st and exit_st.evaluated:
        funnel["exit_policy_evaluated_count"] += 1
        if exit_st.decision in {"triggered", "exit_triggered"} or exit_st.passed:
            if "trigger" in exit_st.reason_code.lower() or exit_st.decision == "triggered":
                funnel["exit_policy_triggered_count"] += 1
    risk = sm.get("risk")
    if risk and (
        risk.decision in {"reduce", "veto_reduce"} or "reduce" in risk.reason_code.lower()
    ):
        funnel["risk_reduce_count"] += 1
    safety = sm.get("safety")
    if safety and (safety.blocked or "exit" in safety.reason_code.lower()):
        funnel["safety_exit_count"] += 1
    if terminal.terminal_outcome == "REDUCE_INTENT":
        funnel["reduce_intent_count"] += 1
    if terminal.terminal_outcome == "EXIT_INTENT":
        funnel["exit_intent_count"] += 1
    return funnel


def funnel_counts_monotonic_v1(funnel: Mapping[str, int], keys: Sequence[str]) -> bool:
    prev = None
    for key in keys:
        val = int(funnel.get(key, 0))
        if prev is not None and val > prev:
            return False
        prev = val
    return True

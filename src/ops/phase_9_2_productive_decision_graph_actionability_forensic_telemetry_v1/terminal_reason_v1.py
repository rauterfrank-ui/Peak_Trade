"""Terminal outcome + primary reason classification (one primary per cycle)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ACTIONABILITY_CALL_ORDER_V1,
    PRIMARY_REASON_STAGE_INDEX,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    ProductiveDecisionStageObservationV1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.stage_classifier_v1 import (
    intent_bucket_from_intended_v1,
    observation_class_from_result_v1,
)


def _as_map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def classify_terminal_outcome_v1(
    *,
    observation_acceptance_result: Any,
    intended: Mapping[str, Any] | Any,
    decision_outcome: str,
    safety_blocked: bool,
    fail_closed: bool,
) -> str:
    if fail_closed:
        return "FAIL_CLOSED"
    obs_class = observation_class_from_result_v1(observation_acceptance_result)
    kind = str(getattr(observation_acceptance_result, "kind", "") or "").lower()
    if obs_class in {"missing"} or "missing" in kind or "no_sample" in kind:
        # Host may pass MISSING/NO_SAMPLE via cycle kind even with a result object.
        if obs_class == "missing":
            return "NO_SAMPLE"
    bucket = intent_bucket_from_intended_v1(intended)
    if bucket == "ENTRY":
        return "ENTRY_INTENT"
    if bucket == "REDUCE":
        return "REDUCE_INTENT"
    if bucket == "EXIT":
        return "EXIT_INTENT"
    if obs_class == "duplicate" or "duplicate" in kind:
        return "DUPLICATE_SAMPLE"
    if obs_class in {"out_of_order", "invalid_event_time"} or "stale" in obs_class:
        return "STALE_SAMPLE"
    if safety_blocked or str(decision_outcome).lower() == "blocked":
        return "BLOCKED"
    if str(decision_outcome).lower() in {"hold", "observe", ""}:
        return "HOLD"
    return "HOLD"


def primary_reason_from_stages_v1(
    stages: Sequence[ProductiveDecisionStageObservationV1],
    *,
    terminal_outcome: str,
) -> tuple[str | None, tuple[str, ...], str | None, int | None]:
    """Pick exactly one primary reason following call-order of first terminal blocker."""
    if terminal_outcome == "ENTRY_INTENT":
        return None, (), None, None
    if terminal_outcome == "REDUCE_INTENT":
        return None, (), None, None
    if terminal_outcome == "EXIT_INTENT":
        return None, (), None, None

    secondary: list[str] = []
    primary: str | None = None
    blocking_stage: str | None = None
    blocking_index: int | None = None

    reason_by_stage = {
        "public_market_observation": "BLOCKED_BY_MISSING_MARKET_TRUTH",
        "distinct_observation_acceptance": None,  # refined below
        "features": "BLOCKED_BY_FEATURES",
        "typed_volatility_presence": "BLOCKED_BY_VOLATILITY_PRESENCE",
        "market_state_bull_bear": "BLOCKED_BY_MARKET_STATE",
        "directional_confirmation": "BLOCKED_BY_CONFIRMATION",
        "master_v2": "BLOCKED_BY_MASTER_V2",
        "double_play": "BLOCKED_BY_DOUBLE_PLAY",
        "dynamic_scope": "BLOCKED_BY_DYNAMIC_SCOPE",
        "survival": "BLOCKED_BY_SURVIVAL",
        "suitability": "BLOCKED_BY_SUITABILITY",
        "composition": "BLOCKED_BY_COMPOSITION",
        "risk": "BLOCKED_BY_RISK",
        "safety": "BLOCKED_BY_SAFETY",
        "exit_policy": "BLOCKED_BY_EXIT_PRECEDENCE",
        "canonical_intent": "HOLD_BY_CANONICAL_DECISION",
    }

    ordered = sorted(stages, key=lambda s: s.stage_call_order_index)
    for stage in ordered:
        if not stage.terminal_blocking_stage and not stage.blocked:
            continue
        if stage.not_reached or stage.not_applicable:
            continue
        reason = reason_by_stage.get(stage.stage)
        if stage.stage == "distinct_observation_acceptance":
            code = stage.reason_code.lower()
            if "duplicate" in code or stage.decision == "duplicate":
                reason = "BLOCKED_BY_DUPLICATE_OBSERVATION"
            elif "stale" in code or "out_of_order" in code or "invalid_event_time" in code:
                reason = "BLOCKED_BY_STALE_OBSERVATION"
            elif "missing" in code or stage.decision == "missing":
                reason = "BLOCKED_BY_MISSING_MARKET_TRUTH"
            else:
                reason = "BLOCKED_BY_DUPLICATE_OBSERVATION"
        if stage.stage == "canonical_intent" and terminal_outcome == "HOLD":
            if stage.decision in {"hold", "observe", "none"}:
                reason = "HOLD_BY_CANONICAL_DECISION"
            else:
                reason = "NO_ACTIONABLE_CHANGE"
        if reason is None:
            continue
        if primary is None:
            primary = reason
            blocking_stage = stage.stage
            blocking_index = stage.stage_call_order_index
        elif reason != primary:
            secondary.append(reason)

    if terminal_outcome == "FAIL_CLOSED":
        primary = "FAIL_CLOSED_INTERNAL_ERROR"
        blocking_stage = ACTIONABILITY_CALL_ORDER_V1[0]
        blocking_index = 0
    elif terminal_outcome == "NO_SAMPLE":
        primary = "BLOCKED_BY_MISSING_MARKET_TRUTH"
        blocking_stage = "public_market_observation"
        blocking_index = PRIMARY_REASON_STAGE_INDEX[primary]
    elif terminal_outcome == "DUPLICATE_SAMPLE":
        primary = "BLOCKED_BY_DUPLICATE_OBSERVATION"
        blocking_stage = "distinct_observation_acceptance"
        blocking_index = PRIMARY_REASON_STAGE_INDEX[primary]
    elif terminal_outcome == "STALE_SAMPLE":
        primary = "BLOCKED_BY_STALE_OBSERVATION"
        blocking_stage = "distinct_observation_acceptance"
        blocking_index = PRIMARY_REASON_STAGE_INDEX[primary]
    elif primary is None and terminal_outcome in {"HOLD", "BLOCKED"}:
        primary = (
            "HOLD_BY_CANONICAL_DECISION" if terminal_outcome == "HOLD" else "NO_ACTIONABLE_CHANGE"
        )
        blocking_stage = "canonical_intent"
        blocking_index = PRIMARY_REASON_STAGE_INDEX[primary]

    # Deduplicate secondary while preserving order.
    seen = {primary} if primary else set()
    uniq_secondary: list[str] = []
    for r in secondary:
        if r in seen:
            continue
        seen.add(r)
        uniq_secondary.append(r)
    return primary, tuple(uniq_secondary), blocking_stage, blocking_index

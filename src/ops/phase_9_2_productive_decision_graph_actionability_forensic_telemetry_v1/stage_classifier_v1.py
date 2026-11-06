"""Stage classification helpers from productive cycle artifacts (observe-only)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ACTIONABILITY_CALL_ORDER_V1,
    SCHEMA_VERSION,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    ProductiveDecisionStageObservationV1,
    canonical_digest_v1,
    redact_detail_v1,
)


def _as_map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _bool(value: Any) -> bool:
    return bool(value)


def make_stage_observation_v1(
    *,
    repository_sha: str,
    config_digest: str,
    runtime_session_id: str,
    decision_cycle_id: str,
    instrument_id: str,
    market_event_time: float | None,
    observation_identity: str,
    observation_epoch: int | None,
    confirmation_session_id: str,
    stage: str,
    input_state: Mapping[str, Any] | None,
    output_state: Mapping[str, Any] | None,
    evaluated: bool,
    passed: bool,
    blocked: bool,
    not_reached: bool,
    not_applicable: bool,
    decision: str,
    reason_code: str,
    reason_detail: str,
    authority_symbol: str,
    intended_side: str,
    position_state: str,
    scope_state: str,
    confirmation_phase: str,
    entry_actionable: bool,
    reduce_actionable: bool,
    exit_actionable: bool,
    terminal_for_cycle: bool,
    terminal_blocking_stage: bool,
) -> ProductiveDecisionStageObservationV1:
    if stage not in ACTIONABILITY_CALL_ORDER_V1:
        raise ValueError(f"UNKNOWN_ACTIONABILITY_STAGE:{stage}")
    idx = ACTIONABILITY_CALL_ORDER_V1.index(stage)
    # Mutual exclusion: not_reached must never be reported as blocked.
    if not_reached:
        blocked = False
        passed = False
        evaluated = False
    if not_applicable:
        blocked = False
        not_reached = False
    return ProductiveDecisionStageObservationV1(
        schema_version=SCHEMA_VERSION,
        repository_sha=repository_sha,
        config_digest=config_digest,
        runtime_session_id=runtime_session_id,
        decision_cycle_id=decision_cycle_id,
        instrument_id=instrument_id,
        market_event_time=market_event_time,
        observation_identity=observation_identity,
        observation_epoch=observation_epoch,
        confirmation_session_id=confirmation_session_id,
        stage=stage,
        stage_call_order_index=idx,
        input_state_digest=canonical_digest_v1(dict(input_state or {})),
        output_state_digest=canonical_digest_v1(dict(output_state or {})),
        evaluated=evaluated,
        passed=passed,
        blocked=blocked,
        not_reached=not_reached,
        not_applicable=not_applicable,
        decision=decision,
        reason_code=reason_code,
        reason_detail_redacted=redact_detail_v1(reason_detail),
        authority_symbol=authority_symbol,
        intended_side=intended_side,
        position_state=position_state,
        scope_state=scope_state,
        confirmation_phase=confirmation_phase,
        entry_actionable=entry_actionable,
        reduce_actionable=reduce_actionable,
        exit_actionable=exit_actionable,
        terminal_for_cycle=terminal_for_cycle,
        terminal_blocking_stage=terminal_blocking_stage,
    )


def confirmation_phase_from_carrier_v1(carrier: Any) -> str:
    if carrier is None:
        return "uninitialized"
    bull = getattr(getattr(carrier, "bull_confirmation_state", None), "assessment_state", None)
    bear = getattr(getattr(carrier, "bear_confirmation_state", None), "assessment_state", None)
    values = []
    for state in (bull, bear):
        if state is None:
            continue
        values.append(_str(getattr(state, "value", state)).lower())
    for target in ("confirmed", "candidate", "observe", "invalid"):
        if target in values:
            return target
    return values[0] if values else "uninitialized"


def observation_class_from_result_v1(obs: Any) -> str:
    if obs is None:
        return "missing"
    classification = getattr(obs, "classification", None)
    if classification is None:
        return "missing"
    return _str(getattr(classification, "value", classification)).lower()


def is_distinct_accepted_v1(obs: Any) -> bool:
    return observation_class_from_result_v1(obs) == "distinct" and bool(
        getattr(obs, "strategy_advance_allowed", False)
    )


def volatility_presence_from_features_v1(features: Mapping[str, Any] | Any) -> str:
    fmap = features.to_dict() if hasattr(features, "to_dict") else _as_map(features)
    vol = fmap.get("volatility_estimate")
    if vol is None:
        return "missing"
    try:
        f = float(vol)
    except (TypeError, ValueError):
        return "missing"
    if f != f or f in (float("inf"), float("-inf")):
        return "missing"
    return "present"


def market_state_from_features_v1(features: Mapping[str, Any] | Any) -> str:
    fmap = features.to_dict() if hasattr(features, "to_dict") else _as_map(features)
    if not bool(fmap.get("ok", False)):
        return "unclassified"
    regime = _str(fmap.get("regime_id") or "").lower()
    if "bull" in regime or regime in {"up", "long", "trend_up"}:
        return "bull"
    if "bear" in regime or regime in {"down", "short", "trend_down"}:
        return "bear"
    if regime in {"", "unclassified", "unknown", "none"}:
        return "unclassified"
    # Classified but non-directional still counts as classified for funnel.
    return regime


def selected_side_norm_v1(value: Any) -> str:
    text = _str(value).lower()
    if "long" in text:
        return "long"
    if "short" in text:
        return "short"
    if "hold" in text or "neutral" in text or "none" in text or text == "":
        return "hold"
    return text


def intent_bucket_from_intended_v1(intended: Mapping[str, Any] | Any) -> str:
    imap = intended.to_dict() if hasattr(intended, "to_dict") else _as_map(intended)
    action = _str(imap.get("intent_action") or "").upper()
    outcome = _str(imap.get("decision_outcome") or "").lower()
    if action in {"ENTER_LONG", "ENTER_SHORT", "ENTRY_LONG", "ENTRY_SHORT"} or outcome in {
        "enter_long",
        "enter_short",
    }:
        return "ENTRY"
    if action in {"REDUCE", "REDUCE_LONG", "REDUCE_SHORT", "PARTIAL_REDUCE"} or outcome == "reduce":
        return "REDUCE"
    if action in {"EXIT", "EXIT_LONG", "EXIT_SHORT", "CLOSE", "FLAT"} or outcome == "exit":
        return "EXIT"
    return "NONE"


def optional_attr(obj: Any, *names: str, default: Any = None) -> Any:
    cur = obj
    for name in names:
        if cur is None:
            return default
        cur = getattr(cur, name, default)
    return cur


def result_pass_like_v1(result: Any) -> Optional[bool]:
    if result is None:
        return None
    if isinstance(result, bool):
        return result
    status = getattr(result, "status", None)
    if status is not None:
        text = _str(getattr(status, "value", status)).lower()
        if text in {"pass", "passed", "ok", "survive", "suitable", "eligible"}:
            return True
        if text in {"fail", "failed", "block", "blocked", "reject", "veto", "unsuitable"}:
            return False
    outcome = getattr(result, "outcome", None)
    if outcome is not None:
        text = _str(getattr(outcome, "value", outcome)).lower()
        if "pass" in text or "allow" in text or "ok" in text:
            return True
        if "block" in text or "veto" in text or "fail" in text or "reject" in text:
            return False
    ok = getattr(result, "ok", None)
    if isinstance(ok, bool):
        return ok
    passed = getattr(result, "passed", None)
    if isinstance(passed, bool):
        return passed
    return None

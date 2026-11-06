"""Deterministic, non-authoritative terminal outcome projection from ledger cycles.

Projection only. No decision, risk, safety, alpha, or execution authority.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1.constants_v1 import (
    ENTRY_INTENT_ACTIONS,
    EXIT_INTENT_ACTIONS,
    REDUCE_INTENT_ACTIONS,
    TERMINAL_OUTCOME_PRIORITY,
    TYPED_VOLATILITY_MISSING_REASON_CODES,
    WARMUP_REASON_CODES,
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def cycle_intended_action_v1(cycle: Mapping[str, Any]) -> Mapping[str, Any]:
    return _as_mapping(cycle.get("intended_action"))


def cycle_reason_codes_v1(cycle: Mapping[str, Any]) -> tuple[str, ...]:
    intended = cycle_intended_action_v1(cycle)
    raw = intended.get("reason_codes")
    if raw is None:
        raw = cycle.get("reason_codes")
    if not isinstance(raw, (list, tuple)):
        return ()
    return tuple(str(x) for x in raw)


def cycle_intent_action_v1(cycle: Mapping[str, Any]) -> str:
    intended = cycle_intended_action_v1(cycle)
    raw = intended.get("intent_action")
    if raw is None:
        raw = cycle.get("intent_action")
    text = str(raw or "NONE").strip().upper()
    return text if text and text != "NONE" else "NONE"


def cycle_intended_side_v1(cycle: Mapping[str, Any]) -> str:
    intended = cycle_intended_action_v1(cycle)
    raw = intended.get("intended_side")
    if raw is None:
        raw = cycle.get("intended_side")
    return str(raw or "").strip().upper()


def cycle_decision_outcome_v1(cycle: Mapping[str, Any]) -> str:
    intended = cycle_intended_action_v1(cycle)
    raw = cycle.get("decision_outcome")
    if raw is None:
        raw = intended.get("decision_outcome")
    return str(raw or "").strip().lower()


def cycle_quantity_source_v1(cycle: Mapping[str, Any]) -> str:
    intended = cycle_intended_action_v1(cycle)
    raw = intended.get("quantity_source")
    if raw is None:
        raw = cycle.get("quantity_source")
    return str(raw or "")


def cycle_fill_present_v1(cycle: Mapping[str, Any]) -> bool:
    fill = cycle.get("fill")
    if fill is None:
        return False
    if isinstance(fill, Mapping) and not fill:
        return False
    return True


def cycle_safety_evaluation_v1(cycle: Mapping[str, Any]) -> Mapping[str, Any]:
    return _as_mapping(cycle.get("safety_evaluation"))


def cycle_safety_result_v1(cycle: Mapping[str, Any]) -> str:
    evaluation = cycle_safety_evaluation_v1(cycle)
    raw = evaluation.get("safety_result")
    if raw is None:
        raw = cycle.get("safety_result")
    return str(raw or "")


def cycle_safety_veto_reason_v1(cycle: Mapping[str, Any]) -> str:
    evaluation = cycle_safety_evaluation_v1(cycle)
    return str(evaluation.get("veto_reason") or "")


def cycle_risk_sizing_result_v1(cycle: Mapping[str, Any]) -> str:
    return str(cycle.get("risk_sizing_result") or "")


def cycle_double_play_gate_v1(cycle: Mapping[str, Any]) -> Mapping[str, Any]:
    return _as_mapping(cycle.get("double_play_typed_volatility_presence_gate"))


def _explicit_terminal_classes_v1(cycle: Mapping[str, Any]) -> list[str] | None:
    """Optional ledger override used only for completeness negative fixtures."""
    multi = cycle.get("terminal_outcome_classes")
    if isinstance(multi, (list, tuple)):
        return [str(x) for x in multi if str(x).strip()]
    singular = cycle.get("terminal_outcome_class")
    if singular is not None and str(singular).strip():
        return [str(singular).strip()]
    return None


def matching_terminal_outcome_predicates_v1(cycle: Mapping[str, Any]) -> list[str]:
    """Return all predicate matches (unordered by priority).

    Used to detect MULTI_CLASSIFIED cycles when an explicit multi-class
    override is present. Normal productive cycles use exclusive projection.
    """
    explicit = _explicit_terminal_classes_v1(cycle)
    if explicit is not None:
        return list(explicit)

    reasons = set(cycle_reason_codes_v1(cycle))
    action = cycle_intent_action_v1(cycle)
    side = cycle_intended_side_v1(cycle)
    decision = cycle_decision_outcome_v1(cycle)
    fill = cycle_fill_present_v1(cycle)
    matches: list[str] = []

    if reasons & WARMUP_REASON_CODES:
        matches.append("SESSION_WARMUP")
    if reasons & TYPED_VOLATILITY_MISSING_REASON_CODES:
        matches.append("MISSING_VOLATILITY_OBSERVE_ONLY")
    if fill and action in ENTRY_INTENT_ACTIONS:
        matches.append("ENTRY_FILL")
    if fill and action in REDUCE_INTENT_ACTIONS:
        matches.append("REDUCE_FILL")
    if fill and action in EXIT_INTENT_ACTIONS:
        matches.append("EXIT_FILL")
    if fill and action not in ENTRY_INTENT_ACTIONS | REDUCE_INTENT_ACTIONS | EXIT_INTENT_ACTIONS:
        matches.append("SIMULATED_FILL_OTHER")
    if (not fill) and action in ENTRY_INTENT_ACTIONS:
        matches.append("ENTRY_INTENT_NO_FILL")
    if (not fill) and action in REDUCE_INTENT_ACTIONS:
        matches.append("REDUCE_INTENT_NO_FILL")
    if (not fill) and action in EXIT_INTENT_ACTIONS:
        matches.append("EXIT_INTENT_NO_FILL")
    if side == "HOLD" and action == "NONE":
        matches.append("HOLD_NO_ACTION")
    if decision in {"observe", "hold"}:
        matches.append("OBSERVE_OR_HOLD")
    if decision == "blocked":
        matches.append("BLOCKED_OTHER")
    return matches


def project_terminal_outcome_class_v1(cycle: Mapping[str, Any]) -> str | None:
    """Project exactly one terminal class via exclusive priority, or None."""
    explicit = _explicit_terminal_classes_v1(cycle)
    if explicit is not None:
        if len(explicit) == 1:
            return explicit[0]
        return None

    reasons = set(cycle_reason_codes_v1(cycle))
    action = cycle_intent_action_v1(cycle)
    side = cycle_intended_side_v1(cycle)
    decision = cycle_decision_outcome_v1(cycle)
    fill = cycle_fill_present_v1(cycle)

    if reasons & WARMUP_REASON_CODES:
        return "SESSION_WARMUP"
    if reasons & TYPED_VOLATILITY_MISSING_REASON_CODES:
        return "MISSING_VOLATILITY_OBSERVE_ONLY"
    if fill and action in ENTRY_INTENT_ACTIONS:
        return "ENTRY_FILL"
    if fill and action in REDUCE_INTENT_ACTIONS:
        return "REDUCE_FILL"
    if fill and action in EXIT_INTENT_ACTIONS:
        return "EXIT_FILL"
    if fill:
        return "SIMULATED_FILL_OTHER"
    if action in ENTRY_INTENT_ACTIONS:
        return "ENTRY_INTENT_NO_FILL"
    if action in REDUCE_INTENT_ACTIONS:
        return "REDUCE_INTENT_NO_FILL"
    if action in EXIT_INTENT_ACTIONS:
        return "EXIT_INTENT_NO_FILL"
    if side == "HOLD" and action == "NONE":
        return "HOLD_NO_ACTION"
    if decision in {"observe", "hold"}:
        return "OBSERVE_OR_HOLD"
    if decision == "blocked":
        return "BLOCKED_OTHER"
    _ = TERMINAL_OUTCOME_PRIORITY  # documented owner vocabulary
    return None


def classify_intent_bucket_v1(cycle: Mapping[str, Any]) -> str:
    action = cycle_intent_action_v1(cycle)
    if action in ENTRY_INTENT_ACTIONS:
        return "ENTRY"
    if action in REDUCE_INTENT_ACTIONS:
        return "REDUCE"
    if action in EXIT_INTENT_ACTIONS:
        return "EXIT"
    return "NONE"


def is_alpha_blocked_v1(cycle: Mapping[str, Any]) -> bool:
    gate = cycle_double_play_gate_v1(cycle)
    if "alpha_scope_entry_authority_allowed" in gate:
        return gate.get("alpha_scope_entry_authority_allowed") is False
    return False


def is_entry_blocked_v1(cycle: Mapping[str, Any]) -> bool:
    gate = cycle_double_play_gate_v1(cycle)
    if "eligibility_new_directional_exposure_allowed" in gate:
        return gate.get("eligibility_new_directional_exposure_allowed") is False
    if cycle.get("execution_eligible") is False:
        return True
    return False


def is_risk_veto_v1(cycle: Mapping[str, Any]) -> bool:
    sizing = cycle_risk_sizing_result_v1(cycle).upper()
    if "VETO" in sizing or sizing in {"BLOCKED", "REJECT", "REJECTED"}:
        return True
    evaluation = cycle_safety_evaluation_v1(cycle)
    signal = _as_mapping(evaluation.get("hard_risk_reduction_signal"))
    return bool(signal.get("triggered"))


def is_safety_veto_v1(cycle: Mapping[str, Any]) -> bool:
    intended = cycle_intended_action_v1(cycle)
    if intended.get("safety_blocked") is True:
        return True
    if cycle_safety_veto_reason_v1(cycle).strip():
        return True
    result = cycle_safety_result_v1(cycle).upper()
    return result in {"EXIT_ONLY", "BLOCKED", "VETO", "SAFETY_VETO"}

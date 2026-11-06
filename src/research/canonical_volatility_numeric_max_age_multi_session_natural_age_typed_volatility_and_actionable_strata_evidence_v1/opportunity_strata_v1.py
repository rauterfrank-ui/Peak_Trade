"""Actionable opportunity strata derived only from real decision-graph outputs."""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    OPPORTUNITY_STRATA_V1,
    OWNER,
    SCHEMA_OPPORTUNITY_STRATA,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    MultiSessionTypedVolEvidenceError,
    sha256_hex_canonical,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.actionable_strata_v1 import (
    project_actionable_alpha_strata_v1,
)


def derive_opportunity_stratum_v1(
    *,
    productive_cycle: Mapping[str, Any] | None = None,
    productive_record: Mapping[str, Any] | None = None,
    counterfactual_classification: str | None = None,
    age_only_blocker: bool = False,
) -> dict[str, Any]:
    """Map existing decision-graph strata to versioned opportunity enum."""
    strata = project_actionable_alpha_strata_v1(
        productive_cycle=productive_cycle,
        productive_record=productive_record,
    )
    side = strata.selected_side.lower()
    decision = strata.decision_outcome.lower()
    composition = strata.composition_outcome.lower()
    entry = bool(strata.entry_opportunity)

    stratum = "NO_ACTIONABLE_OPPORTUNITY"
    actionable = False
    if strata.exit_action_available and "open" in strata.position_state.lower():
        stratum = "OPEN_POSITION_EXIT_RELEVANT"
        actionable = True
    elif strata.risk_action_available and "open" in strata.position_state.lower():
        stratum = "OPEN_POSITION_REDUCE_RELEVANT"
        actionable = True
    elif age_only_blocker or counterfactual_classification == "ENTRY_PERMISSION_CHANGE":
        stratum = "ENTRY_BLOCKED_BY_AGE_ONLY"
        actionable = False
    elif strata.already_blocked_for_non_age_reason:
        stratum = "ENTRY_BLOCKED_BY_NON_AGE_REASON"
        actionable = False
    elif entry and side == "long":
        stratum = "LONG_ENTRY_ELIGIBLE"
        actionable = True
    elif entry and side == "short":
        stratum = "SHORT_ENTRY_ELIGIBLE"
        actionable = True
    elif "long" in composition and "selected" in composition:
        stratum = "LONG_COMPOSITION_SELECTED"
        actionable = True
    elif "short" in composition and "selected" in composition:
        stratum = "SHORT_COMPOSITION_SELECTED"
        actionable = True
    elif side == "long" and decision in {"armed", "entry", "selected"}:
        stratum = "LONG_ARMED" if decision == "armed" else "LONG_DIRECTIONAL_OPPORTUNITY"
        actionable = True
    elif side == "short" and decision in {"armed", "entry", "selected"}:
        stratum = "SHORT_ARMED" if decision == "armed" else "SHORT_DIRECTIONAL_OPPORTUNITY"
        actionable = True
    elif side == "long":
        stratum = "LONG_DIRECTIONAL_OPPORTUNITY"
        actionable = True
    elif side == "short":
        stratum = "SHORT_DIRECTIONAL_OPPORTUNITY"
        actionable = True

    if stratum not in OPPORTUNITY_STRATA_V1:
        raise MultiSessionTypedVolEvidenceError(f"unknown_opportunity_stratum:{stratum}")

    non_age_blockers = []
    if strata.already_blocked_for_non_age_reason:
        non_age_blockers.append("ALREADY_BLOCKED_NON_AGE")
    if strata.trading_permission_state and strata.trading_permission_state.upper() not in {
        "",
        "ALLOWED",
        "UNKNOWN",
    }:
        non_age_blockers.append(f"TRADING_PERMISSION:{strata.trading_permission_state}")

    payload = {
        "schema": SCHEMA_OPPORTUNITY_STRATA,
        "schema_version": "v1",
        "OPPORTUNITY_STRATUM": stratum,
        "STRATUM_OWNER": OWNER,
        "STRATUM_EVIDENCE": strata.to_dict(),
        "ACTIONABLE": bool(actionable),
        "FINAL_DECISION": decision,
        "ENTRY_ELIGIBILITY": bool(entry),
        "NON_AGE_BLOCKERS": non_age_blockers,
        "AGE_ONLY_BLOCKER": bool(age_only_blocker),
        "FILE_SYMBOL_REFERENCE": (
            "research.canonical_volatility_numeric_max_age_natural_age_progression_"
            "and_actionable_strata_evidence_plan_v1.actionable_strata_v1."
            "project_actionable_alpha_strata_v1"
        ),
        "SYNTHETIC_ACTIONABLE_OUTCOME": False,
    }
    payload["STRATUM_STATE_DIGEST"] = sha256_hex_canonical(
        {k: v for k, v in payload.items() if k != "STRATUM_STATE_DIGEST"}
    )
    return payload


def assert_long_short_mirror_support_v1() -> dict[str, bool]:
    longish = [s for s in OPPORTUNITY_STRATA_V1 if s.startswith("LONG_")]
    shortish = [s for s in OPPORTUNITY_STRATA_V1 if s.startswith("SHORT_")]
    long_suffixes = {s.removeprefix("LONG_") for s in longish}
    short_suffixes = {s.removeprefix("SHORT_") for s in shortish}
    return {
        "LONG_STRATA_SUPPORTED": bool(longish),
        "SHORT_STRATA_SUPPORTED": bool(shortish),
        "MIRROR_SUFFIXES_EQUAL": long_suffixes == short_suffixes,
        "ENTRY_ELIGIBLE_STRATA_SUPPORTED": (
            "LONG_ENTRY_ELIGIBLE" in OPPORTUNITY_STRATA_V1
            and "SHORT_ENTRY_ELIGIBLE" in OPPORTUNITY_STRATA_V1
        ),
    }

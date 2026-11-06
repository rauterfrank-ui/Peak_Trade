"""Extended counterfactual candidate-grid impact (diagnostic only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.actionable_strata_v1 import (
    ActionableAlphaStrataEvidenceV1,
    project_actionable_alpha_strata_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    ALPHA_ONLY_COUNTERFACTUAL_BLOCK,
    ENFORCEMENT_APPLIED,
    EXIT_COUNTERFACTUAL_BLOCK,
    NUMERIC_MAX_AGE_ENFORCING,
    NUMERIC_MAX_AGE_SELECTED,
    RECONCILIATION_COUNTERFACTUAL_BLOCK,
    RESEARCH_AGE_GRID_SECONDS,
    RISK_COUNTERFACTUAL_BLOCK,
    SAFETY_COUNTERFACTUAL_BLOCK,
    THRESHOLD_SELECTED,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.safety_observability_v1 import (
    project_safety_risk_exit_observability_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    CounterfactualAgeLabelV1,
    evaluate_counterfactual_max_age_threshold_diagnostic_v1,
)


@dataclass(frozen=True)
class CounterfactualCandidateImpactV1:
    candidate_max_age_seconds: int
    fresh_count: int
    stale_count: int
    not_evaluable_count: int
    alpha_allowed_by_age: int
    alpha_blocked_by_age: int
    already_blocked_for_other_reason: int
    incremental_age_only_block_count: int
    long_selected_affected: int
    short_selected_affected: int
    both_confirmed_affected: int
    entry_opportunity_affected: int
    hold_affected: int
    reduce_affected: int
    exit_affected: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "already_blocked_for_other_reason": self.already_blocked_for_other_reason,
            "alpha_allowed_by_age": self.alpha_allowed_by_age,
            "alpha_blocked_by_age": self.alpha_blocked_by_age,
            "both_confirmed_affected": self.both_confirmed_affected,
            "candidate_max_age_seconds": self.candidate_max_age_seconds,
            "entry_opportunity_affected": self.entry_opportunity_affected,
            "exit_affected": self.exit_affected,
            "fresh_count": self.fresh_count,
            "hold_affected": self.hold_affected,
            "incremental_age_only_block_count": self.incremental_age_only_block_count,
            "long_selected_affected": self.long_selected_affected,
            "not_evaluable_count": self.not_evaluable_count,
            "reduce_affected": self.reduce_affected,
            "short_selected_affected": self.short_selected_affected,
            "stale_count": self.stale_count,
        }


def _age_from_record(record: Mapping[str, Any]) -> Optional[float]:
    raw = record.get("age_seconds", record.get("estimate_age_seconds"))
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _strata_for_record(
    record: Mapping[str, Any],
    *,
    strata: ActionableAlphaStrataEvidenceV1 | Mapping[str, Any] | None,
) -> ActionableAlphaStrataEvidenceV1:
    if isinstance(strata, ActionableAlphaStrataEvidenceV1):
        return strata
    if strata is not None:
        return project_actionable_alpha_strata_v1(productive_record={**record, **dict(strata)})
    return project_actionable_alpha_strata_v1(productive_record=record)


def evaluate_counterfactual_candidate_impact_v1(
    records: Sequence[Mapping[str, Any]],
    *,
    candidate_grid_seconds: Sequence[int] = RESEARCH_AGE_GRID_SECONDS,
    strata_by_record_id: Mapping[str, ActionableAlphaStrataEvidenceV1 | Mapping[str, Any]]
    | None = None,
) -> dict[str, Any]:
    """Aggregate per-candidate counterfactual impact without selecting a threshold."""
    if tuple(int(x) for x in candidate_grid_seconds) != tuple(RESEARCH_AGE_GRID_SECONDS):
        raise ValueError("candidate_grid_must_match_preregistration")

    per_candidate: dict[int, dict[str, int]] = {
        int(c): {
            "fresh_count": 0,
            "stale_count": 0,
            "not_evaluable_count": 0,
            "alpha_allowed_by_age": 0,
            "alpha_blocked_by_age": 0,
            "already_blocked_for_other_reason": 0,
            "incremental_age_only_block_count": 0,
            "long_selected_affected": 0,
            "short_selected_affected": 0,
            "both_confirmed_affected": 0,
            "entry_opportunity_affected": 0,
            "hold_affected": 0,
            "reduce_affected": 0,
            "exit_affected": 0,
        }
        for c in candidate_grid_seconds
    }

    for record in records:
        age = _age_from_record(record)
        estimate_present = bool(record.get("estimate_present", age is not None))
        rid = str(record.get("evidence_record_id") or "")
        strata_src = None if strata_by_record_id is None else strata_by_record_id.get(rid)
        strata = _strata_for_record(record, strata=strata_src)
        already_other = bool(strata.already_blocked_for_non_age_reason)
        decision = strata.decision_outcome
        side = strata.selected_side

        for candidate in candidate_grid_seconds:
            bucket = per_candidate[int(candidate)]
            diagnostic = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
                computed_age_seconds=age if estimate_present else None,
                candidate_max_age_seconds_argument=float(candidate),
            )
            if diagnostic.enforcement_applied or diagnostic.alpha_decision_mutated:
                raise ValueError("counterfactual_mutated_authority")
            label = diagnostic.counterfactual_label
            if label == CounterfactualAgeLabelV1.WOULD_BE_FRESH_IF_THRESHOLD.value:
                bucket["fresh_count"] += 1
                bucket["alpha_allowed_by_age"] += 1
            elif label == CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value:
                bucket["stale_count"] += 1
                bucket["alpha_blocked_by_age"] += 1
                if already_other:
                    bucket["already_blocked_for_other_reason"] += 1
                else:
                    bucket["incremental_age_only_block_count"] += 1
                    if side == "long":
                        bucket["long_selected_affected"] += 1
                    elif side == "short":
                        bucket["short_selected_affected"] += 1
                    elif side in {"both", "both_confirmed"}:
                        bucket["both_confirmed_affected"] += 1
                    if strata.entry_opportunity or decision == "entry":
                        bucket["entry_opportunity_affected"] += 1
                    if decision == "hold":
                        bucket["hold_affected"] += 1
                    if decision == "reduce":
                        bucket["reduce_affected"] += 1
                    if decision == "exit":
                        bucket["exit_affected"] += 1
            else:
                bucket["not_evaluable_count"] += 1

            # Safety/risk/exit remain observationally available under stale.
            _ = project_safety_risk_exit_observability_v1(
                strata=strata,
                counterfactual_stale=(
                    label == CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value
                ),
            )

    impacts = [
        CounterfactualCandidateImpactV1(candidate_max_age_seconds=int(c), **per_candidate[int(c)])
        for c in candidate_grid_seconds
    ]
    fresh_rates = {i.candidate_max_age_seconds: i.fresh_count for i in impacts}
    discrimination = len(set(fresh_rates.values())) > 1 or any(i.stale_count > 0 for i in impacts)
    return {
        "authority_scope": "COUNTERFACTUAL_DIAGNOSTIC_ONLY",
        "alpha_only_counterfactual_block": ALPHA_ONLY_COUNTERFACTUAL_BLOCK,
        "exit_counterfactual_block": EXIT_COUNTERFACTUAL_BLOCK,
        "risk_counterfactual_block": RISK_COUNTERFACTUAL_BLOCK,
        "safety_counterfactual_block": SAFETY_COUNTERFACTUAL_BLOCK,
        "reconciliation_counterfactual_block": RECONCILIATION_COUNTERFACTUAL_BLOCK,
        "enforcement_applied": ENFORCEMENT_APPLIED,
        "threshold_selected": THRESHOLD_SELECTED,
        "numeric_max_age_selected": NUMERIC_MAX_AGE_SELECTED,
        "numeric_max_age_enforcing": NUMERIC_MAX_AGE_ENFORCING,
        "candidate_discrimination_observed": discrimination,
        "incremental_age_only_effect_observed": any(
            i.incremental_age_only_block_count > 0 for i in impacts
        ),
        "research_age_candidate_grid_seconds": list(candidate_grid_seconds),
        "record_count": len(records),
        "per_candidate": [i.to_dict() for i in impacts],
        "productive_threshold_recommendation": None,
    }

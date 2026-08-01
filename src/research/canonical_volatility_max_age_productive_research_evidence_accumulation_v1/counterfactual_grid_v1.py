"""Counterfactual age-grid diagnostics — never mutates Alpha/state/enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    ProductiveResearchEvidenceRecordV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    RESEARCH_AGE_CANDIDATE_GRID_SECONDS,
    build_productive_evidence_accumulation_preregistration_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    CounterfactualAgeLabelV1,
    evaluate_counterfactual_max_age_threshold_diagnostic_v1,
)

COUNTERFACTUAL_ONLY = True
ALPHA_MUTATION = False
STATE_MUTATION = False
ENFORCEMENT_APPLIED = False
THRESHOLD_SELECTED = False
EXIT_PATH_PRESERVATION_DEFAULT = True


@dataclass(frozen=True)
class CounterfactualAgeGridCellV1:
    candidate_max_age_seconds: int
    candidate_age_bucket: str
    counterfactual_label: str
    would_be_fresh: bool
    would_be_stale: bool
    entry_eligibility_counterfactual: str
    exit_path_preservation: bool
    enforcement_applied: bool
    alpha_decision_mutated: bool
    threshold_selected: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha_decision_mutated": self.alpha_decision_mutated,
            "candidate_age_bucket": self.candidate_age_bucket,
            "candidate_max_age_seconds": self.candidate_max_age_seconds,
            "counterfactual_label": self.counterfactual_label,
            "enforcement_applied": self.enforcement_applied,
            "entry_eligibility_counterfactual": self.entry_eligibility_counterfactual,
            "exit_path_preservation": self.exit_path_preservation,
            "threshold_selected": self.threshold_selected,
            "would_be_fresh": self.would_be_fresh,
            "would_be_stale": self.would_be_stale,
        }


def _entry_eligibility_v1(
    *,
    estimate_present: bool,
    counterfactual_eligible: bool,
    label: str,
) -> str:
    if not estimate_present:
        return "ENTRY_BLOCKED_UNKNOWN_OR_ABSENT"
    if not counterfactual_eligible:
        return "ENTRY_BLOCKED_UNTRUSTED_OR_INELIGIBLE"
    if label == CounterfactualAgeLabelV1.WOULD_BE_FRESH_IF_THRESHOLD.value:
        return "ENTRY_WOULD_BE_ALLOWED_IF_THRESHOLD"
    if label == CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value:
        return "ENTRY_WOULD_BE_BLOCKED_IF_THRESHOLD"
    if label == CounterfactualAgeLabelV1.AGE_UNAVAILABLE.value:
        return "ENTRY_BLOCKED_AGE_UNAVAILABLE"
    return "ENTRY_NOT_EVALUATED"


def evaluate_counterfactual_age_grid_for_record_v1(
    record: ProductiveResearchEvidenceRecordV1 | Mapping[str, Any],
    *,
    candidate_grid_seconds: Sequence[int] | None = None,
) -> tuple[CounterfactualAgeGridCellV1, ...]:
    """Diagnostic-only age grid. Never mutates productive decisions."""
    payload = (
        record.to_dict() if isinstance(record, ProductiveResearchEvidenceRecordV1) else dict(record)
    )
    grid = tuple(
        int(x)
        for x in (
            candidate_grid_seconds
            if candidate_grid_seconds is not None
            else RESEARCH_AGE_CANDIDATE_GRID_SECONDS
        )
    )
    if grid != RESEARCH_AGE_CANDIDATE_GRID_SECONDS:
        raise ProductiveEvidenceAccumulationError("counterfactual_grid_must_match_preregistration")

    age_seconds = payload.get("estimate_age_seconds")
    if age_seconds is None:
        age_seconds = payload.get("age_seconds")
    age_value: Optional[float]
    try:
        age_value = None if age_seconds is None else float(age_seconds)
    except (TypeError, ValueError) as exc:
        raise ProductiveEvidenceAccumulationError("counterfactual_age_not_numeric") from exc

    estimate_present = bool(payload.get("estimate_present"))
    counterfactual_eligible = bool(payload.get("counterfactual_eligible"))
    exit_preserved = bool(payload.get("exit_path_preservation", EXIT_PATH_PRESERVATION_DEFAULT))

    cells: list[CounterfactualAgeGridCellV1] = []
    for candidate in grid:
        diagnostic = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
            computed_age_seconds=age_value if estimate_present else None,
            candidate_max_age_seconds_argument=float(candidate),
        )
        if diagnostic.enforcement_applied or diagnostic.alpha_decision_mutated:
            raise ProductiveEvidenceAccumulationError("counterfactual_mutated_authority")
        label = diagnostic.counterfactual_label
        cells.append(
            CounterfactualAgeGridCellV1(
                candidate_max_age_seconds=int(candidate),
                candidate_age_bucket=f"AGE_LE_{int(candidate)}_S",
                counterfactual_label=label,
                would_be_fresh=label == CounterfactualAgeLabelV1.WOULD_BE_FRESH_IF_THRESHOLD.value,
                would_be_stale=label == CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value,
                entry_eligibility_counterfactual=_entry_eligibility_v1(
                    estimate_present=estimate_present,
                    counterfactual_eligible=counterfactual_eligible,
                    label=label,
                ),
                exit_path_preservation=exit_preserved,
                enforcement_applied=False,
                alpha_decision_mutated=False,
                threshold_selected=False,
            )
        )
    return tuple(cells)


def evaluate_counterfactual_age_grid_batch_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate counterfactual diagnostics without ranking a productive winner."""
    prereg = build_productive_evidence_accumulation_preregistration_v1()
    per_candidate: dict[str, dict[str, int]] = {
        f"CANDIDATE_{s}_S": {
            "fresh_count": 0,
            "stale_count": 0,
            "entry_allowed_count": 0,
            "entry_blocked_count": 0,
            "exit_preserved_count": 0,
            "observation_count": 0,
        }
        for s in prereg.research_age_candidate_grid_seconds
    }
    rows: list[dict[str, Any]] = []
    for record in records:
        cells = evaluate_counterfactual_age_grid_for_record_v1(record)
        payload = (
            record.to_dict()
            if isinstance(record, ProductiveResearchEvidenceRecordV1)
            else dict(record)
        )
        row = {
            "evidence_record_id": payload.get("evidence_record_id"),
            "session_id": payload.get("session_id"),
            "estimate_age_seconds": payload.get("estimate_age_seconds", payload.get("age_seconds")),
            "cells": [c.to_dict() for c in cells],
            "counterfactual_only": COUNTERFACTUAL_ONLY,
            "alpha_mutation": ALPHA_MUTATION,
            "state_mutation": STATE_MUTATION,
            "enforcement_applied": ENFORCEMENT_APPLIED,
            "threshold_selected": THRESHOLD_SELECTED,
        }
        rows.append(row)
        for cell in cells:
            key = f"CANDIDATE_{cell.candidate_max_age_seconds}_S"
            bucket = per_candidate[key]
            bucket["observation_count"] += 1
            if cell.would_be_fresh:
                bucket["fresh_count"] += 1
            if cell.would_be_stale:
                bucket["stale_count"] += 1
            if cell.entry_eligibility_counterfactual == "ENTRY_WOULD_BE_ALLOWED_IF_THRESHOLD":
                bucket["entry_allowed_count"] += 1
            else:
                bucket["entry_blocked_count"] += 1
            if cell.exit_path_preservation:
                bucket["exit_preserved_count"] += 1

    return {
        "authority_scope": "COUNTERFACTUAL_DIAGNOSTIC_ONLY",
        "counterfactual_only": COUNTERFACTUAL_ONLY,
        "alpha_mutation": ALPHA_MUTATION,
        "state_mutation": STATE_MUTATION,
        "enforcement_applied": ENFORCEMENT_APPLIED,
        "threshold_selected": THRESHOLD_SELECTED,
        "productive_preregistration_digest": prereg.productive_preregistration_digest,
        "research_age_candidate_grid_seconds": list(prereg.research_age_candidate_grid_seconds),
        "per_candidate": per_candidate,
        "record_count": len(rows),
        "rows": rows,
        "productive_threshold_recommendation": None,
        "ranking_with_productive_winner": False,
    }

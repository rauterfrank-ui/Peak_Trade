"""Counterfactual-only candidate evaluation (diagnostic, non-enforcing)."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    BASELINE_CANDIDATE_ID,
    MAX_COVERAGE_REDUCTION_VS_BASELINE,
    MAX_NEIGHBORHOOD_SENSITIVITY,
    MAX_STALE_REJECTION_RATE,
    MAX_WALK_FORWARD_INSTABILITY,
    MINIMUM_REGIME_COUNT,
    MINIMUM_SESSION_COUNT,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    ResearchEvidenceRecordV1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    CounterfactualAgeLabelV1,
    evaluate_counterfactual_max_age_threshold_diagnostic_v1,
)


def _distribution(values: Sequence[Optional[str]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for value in values:
        key = "MISSING" if value is None or not str(value).strip() else str(value)
        counter[key] += 1
    return dict(sorted(counter.items()))


def _age_distribution(ages: Sequence[Optional[float]]) -> dict[str, Any]:
    present = [float(a) for a in ages if a is not None]
    if not present:
        return {"count": 0, "min": None, "max": None, "mean": None, "p50": None}
    present_sorted = sorted(present)
    mid = len(present_sorted) // 2
    p50 = (
        present_sorted[mid]
        if len(present_sorted) % 2 == 1
        else 0.5 * (present_sorted[mid - 1] + present_sorted[mid])
    )
    return {
        "count": len(present_sorted),
        "min": present_sorted[0],
        "max": present_sorted[-1],
        "mean": sum(present_sorted) / len(present_sorted),
        "p50": p50,
    }


def _economic_diagnostics(
    records: Sequence[ResearchEvidenceRecordV1],
) -> Optional[dict[str, Any]]:
    metrics_rows = [dict(r.economic_metrics) for r in records if r.economic_metrics]
    if not metrics_rows:
        return None

    def _sum(key: str) -> Optional[float]:
        vals = []
        for row in metrics_rows:
            if key in row and row[key] is not None:
                try:
                    vals.append(float(row[key]))
                except (TypeError, ValueError):
                    continue
        if not vals:
            return None
        return float(sum(vals))

    out = {
        "trade_count": _sum("trade_count"),
        "exposure": _sum("exposure"),
        "turnover": _sum("turnover"),
        "gross_pnl": _sum("gross_pnl"),
        "net_pnl_after_fees_and_slippage": _sum("net_pnl_after_fees_and_slippage"),
        "sharpe": _sum("sharpe"),
        "sortino": _sum("sortino"),
        "profit_factor": _sum("profit_factor"),
        "max_drawdown": _sum("max_drawdown"),
        "average_holding_period": _sum("average_holding_period"),
        "long_short_asymmetry": _sum("long_short_asymmetry"),
        "diagnostic_only": True,
        "invented": False,
    }
    if all(v is None for k, v in out.items() if k not in {"diagnostic_only", "invented"}):
        return None
    return out


def evaluate_candidate_on_records_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_id: str,
    candidate_max_age_seconds: Optional[float],
    baseline_decision_outcomes: Optional[Mapping[str, Optional[str]]] = None,
) -> dict[str, Any]:
    """Evaluate one candidate or the unresolved baseline counterfactually."""
    n = len(records)
    sessions = {r.session_id for r in records}
    regimes = {r.regime_id for r in records}
    accepted = 0
    rejected_stale = 0
    missing_estimate = 0
    decision_changes = 0
    ages: list[Optional[float]] = []

    baseline_map = baseline_decision_outcomes or {}

    for record in records:
        ages.append(record.computed_age_seconds)
        if record.estimate_present is False or record.computed_age_seconds is None:
            missing_estimate += 1
            continue

        if candidate_max_age_seconds is None:
            # Baseline: unresolved / non-enforcing — no stale rejection.
            accepted += 1
            continue

        diagnostic = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
            computed_age_seconds=record.computed_age_seconds,
            candidate_max_age_seconds_argument=float(candidate_max_age_seconds),
        )
        if diagnostic.enforcement_applied or diagnostic.alpha_decision_mutated:
            raise RuntimeError("alpha_or_enforcement_leak_in_counterfactual")
        if (
            diagnostic.counterfactual_label
            == CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value
        ):
            rejected_stale += 1
            # Counterfactual decision change diagnostic vs baseline acceptance.
            if baseline_map.get(record.cycle_id) is not None:
                decision_changes += 1
        elif (
            diagnostic.counterfactual_label
            == CounterfactualAgeLabelV1.WOULD_BE_FRESH_IF_THRESHOLD.value
        ):
            accepted += 1
        else:
            missing_estimate += 1

    denom = max(n, 1)
    decision_coverage = accepted / denom
    result: dict[str, Any] = {
        "accepted_estimate_count": accepted,
        "age_distribution": _age_distribution(ages),
        "alpha_decision_mutated": False,
        "candidate_id": candidate_id,
        "candidate_max_age_seconds_argument": candidate_max_age_seconds,
        "counterfactual_decision_change_count": decision_changes,
        "decision_coverage": decision_coverage,
        "enforcement_applied": False,
        "evaluation_mode": "DIAGNOSTIC_COUNTERFACTUAL_NO_ENFORCEMENT",
        "evidence_count": n,
        "final_holdout_result": None,
        "missing_estimate_rate": missing_estimate / denom,
        "parameter_stability": None,
        "regime_count": len(regimes),
        "regime_distribution": _distribution([r.regime_id for r in records]),
        "rejected_as_stale_count": rejected_stale,
        "restart_status_distribution": _distribution([r.restart_status for r in records]),
        "reuse_status_distribution": _distribution([r.reuse_status for r in records]),
        "session_count": len(sessions),
        "stale_rejection_rate": rejected_stale / denom,
        "threshold_boundary_sensitivity": None,
        "walk_forward_stability": None,
    }
    econ = _economic_diagnostics(records)
    if econ is not None:
        result["economic_diagnostics"] = econ
    return result


def evaluate_all_candidates_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_max_age_seconds: Sequence[int],
) -> list[dict[str, Any]]:
    baseline_outcomes = {r.cycle_id: r.decision_outcome for r in records}
    results = [
        evaluate_candidate_on_records_v1(
            records,
            candidate_id=BASELINE_CANDIDATE_ID,
            candidate_max_age_seconds=None,
            baseline_decision_outcomes=baseline_outcomes,
        )
    ]
    for seconds in candidate_max_age_seconds:
        results.append(
            evaluate_candidate_on_records_v1(
                records,
                candidate_id=f"CANDIDATE_{int(seconds)}_S",
                candidate_max_age_seconds=float(seconds),
                baseline_decision_outcomes=baseline_outcomes,
            )
        )
    return results


def apply_rejection_criteria_v1(
    candidate_result: Mapping[str, Any],
    *,
    baseline_result: Mapping[str, Any],
    walk_forward_stability: Optional[float],
    neighborhood_sensitivity: Optional[float],
    holdout_degraded: bool,
    single_session_only: bool,
    single_regime_only: bool,
    leakage_or_digest_violation: bool,
    restart_ledger_nondeterminism: bool,
) -> dict[str, Any]:
    reasons: list[str] = []
    if int(candidate_result.get("session_count") or 0) < MINIMUM_SESSION_COUNT:
        reasons.append("INSUFFICIENT_SESSION_COVERAGE")
    if int(candidate_result.get("regime_count") or 0) < MINIMUM_REGIME_COUNT:
        reasons.append("INSUFFICIENT_REGIME_COVERAGE")
    if walk_forward_stability is not None and walk_forward_stability > MAX_WALK_FORWARD_INSTABILITY:
        reasons.append("UNSTABLE_WALK_FORWARD")
    if holdout_degraded:
        reasons.append("HOLDOUT_DEGRADATION")
    if (
        neighborhood_sensitivity is not None
        and neighborhood_sensitivity > MAX_NEIGHBORHOOD_SENSITIVITY
    ):
        reasons.append("HIGH_NEIGHBORHOOD_SENSITIVITY")
    baseline_coverage = float(baseline_result.get("decision_coverage") or 0.0)
    candidate_coverage = float(candidate_result.get("decision_coverage") or 0.0)
    if baseline_coverage > 0:
        reduction = (baseline_coverage - candidate_coverage) / baseline_coverage
        if reduction > MAX_COVERAGE_REDUCTION_VS_BASELINE:
            reasons.append("EXCESSIVE_COVERAGE_REDUCTION")
    if float(candidate_result.get("stale_rejection_rate") or 0.0) > MAX_STALE_REJECTION_RATE:
        reasons.append("EXCESSIVE_STALE_REJECTION")
    if single_session_only:
        reasons.append("BENEFIT_ONLY_IN_SINGLE_SESSION")
    if single_regime_only:
        reasons.append("BENEFIT_ONLY_IN_SINGLE_REGIME")
    if leakage_or_digest_violation:
        reasons.append("LEAKAGE_OR_DIGEST_VIOLATION")
    if restart_ledger_nondeterminism:
        reasons.append("RESTART_LEDGER_NONDETERMINISM")
    if int(candidate_result.get("evidence_count") or 0) < 1:
        reasons.append("INSUFFICIENT_STATISTICAL_POWER")

    return {
        "candidate_id": candidate_result.get("candidate_id"),
        "rejected": bool(reasons),
        "rejection_reasons": reasons,
        "alpha_decision_mutated": False,
        "enforcement_applied": False,
        "numeric_threshold_selected": False,
        "parameter_promoted": False,
    }

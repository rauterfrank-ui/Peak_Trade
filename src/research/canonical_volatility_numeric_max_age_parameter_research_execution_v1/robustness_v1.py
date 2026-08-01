"""Robustness / uncertainty analyses with time-structure-preserving resampling."""

from __future__ import annotations

import random
from typing import Any, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    BASELINE_CANDIDATE_ID,
    BOOTSTRAP_BLOCK_SECONDS,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    NEIGHBORHOOD_PERTURBATION_FACTORS,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evaluator_v1 import (
    evaluate_candidate_on_records_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    ResearchEvidenceRecordV1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.split_engine_v1 import (
    SplitAssignmentV1,
    access_final_holdout_v1,
    build_walk_forward_folds_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    SplitAndEmbargoContractV1,
)


def _coverage(records: Sequence[ResearchEvidenceRecordV1], seconds: Optional[float]) -> float:
    result = evaluate_candidate_on_records_v1(
        records,
        candidate_id="tmp",
        candidate_max_age_seconds=seconds,
    )
    return float(result["decision_coverage"])


def walk_forward_matrix_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    split_contract: SplitAndEmbargoContractV1,
    candidate_seconds: Sequence[int],
) -> dict[str, Any]:
    folds = build_walk_forward_folds_v1(records, split_contract=split_contract)
    fold_rows: list[dict[str, Any]] = []
    stabilities: list[float] = []
    for fold in folds:
        row: dict[str, Any] = {"fold_id": fold.fold_id, "candidates": {}}
        coverages: list[float] = []
        for seconds in candidate_seconds:
            cov = _coverage(fold.validation, float(seconds))
            row["candidates"][f"CANDIDATE_{seconds}_S"] = {
                "validation_decision_coverage": cov,
                "validation_count": len(fold.validation),
                "holdout_accessed": fold.holdout_accessed,
            }
            coverages.append(cov)
        if coverages:
            mean = sum(coverages) / len(coverages)
            var = sum((c - mean) ** 2 for c in coverages) / len(coverages)
            stability = var**0.5
            stabilities.append(stability)
            row["fold_coverage_stdev"] = stability
        fold_rows.append(row)
    overall = sum(stabilities) / len(stabilities) if stabilities else None
    return {
        "executed": True,
        "folds": fold_rows,
        "walk_forward_stability": overall,
        "holdout_untouched_during_walk_forward": all(not f.holdout_accessed for f in folds),
    }


def final_holdout_matrix_v1(
    sealed_split: SplitAssignmentV1,
    *,
    candidate_seconds: Sequence[int],
) -> dict[str, Any]:
    opened = access_final_holdout_v1(sealed_split)
    rows: dict[str, Any] = {}
    baseline = evaluate_candidate_on_records_v1(
        opened.holdout,
        candidate_id=BASELINE_CANDIDATE_ID,
        candidate_max_age_seconds=None,
    )
    rows[BASELINE_CANDIDATE_ID] = baseline
    for seconds in candidate_seconds:
        rows[f"CANDIDATE_{seconds}_S"] = evaluate_candidate_on_records_v1(
            opened.holdout,
            candidate_id=f"CANDIDATE_{seconds}_S",
            candidate_max_age_seconds=float(seconds),
        )
    return {
        "executed": True,
        "holdout_accessed": opened.holdout_accessed,
        "holdout_count": len(opened.holdout),
        "results": rows,
    }


def regime_session_matrices_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_seconds: Sequence[int],
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_regime: dict[str, list[ResearchEvidenceRecordV1]] = {}
    by_session: dict[str, list[ResearchEvidenceRecordV1]] = {}
    for record in records:
        by_regime.setdefault(record.regime_id, []).append(record)
        by_session.setdefault(record.session_id, []).append(record)

    def _slice_matrix(groups: dict[str, list[ResearchEvidenceRecordV1]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, rows in sorted(groups.items()):
            out[key] = {
                BASELINE_CANDIDATE_ID: evaluate_candidate_on_records_v1(
                    rows,
                    candidate_id=BASELINE_CANDIDATE_ID,
                    candidate_max_age_seconds=None,
                ),
            }
            for seconds in candidate_seconds:
                out[key][f"CANDIDATE_{seconds}_S"] = evaluate_candidate_on_records_v1(
                    rows,
                    candidate_id=f"CANDIDATE_{seconds}_S",
                    candidate_max_age_seconds=float(seconds),
                )
        return {"executed": True, "slices": out}

    return _slice_matrix(by_regime), _slice_matrix(by_session)


def neighborhood_perturbation_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_seconds: Sequence[int],
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for seconds in candidate_seconds:
        base = _coverage(records, float(seconds))
        perturbed = []
        for factor in NEIGHBORHOOD_PERTURBATION_FACTORS:
            perturbed.append(_coverage(records, float(seconds) * float(factor)))
        sensitivity = max(abs(p - base) for p in perturbed) if perturbed else 0.0
        rows[f"CANDIDATE_{seconds}_S"] = {
            "base_coverage": base,
            "perturbed_coverages": perturbed,
            "neighborhood_sensitivity": sensitivity,
            "factors": list(NEIGHBORHOOD_PERTURBATION_FACTORS),
        }
    return {"executed": True, "results": rows}


def _event_time_blocks(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    block_seconds: int,
) -> list[list[ResearchEvidenceRecordV1]]:
    ordered = sorted(
        records,
        key=lambda r: (float(r.event_time_epoch_seconds or 0.0), r.cycle_id),
    )
    if not ordered:
        return []
    blocks: list[list[ResearchEvidenceRecordV1]] = []
    current: list[ResearchEvidenceRecordV1] = []
    block_start = float(ordered[0].event_time_epoch_seconds or 0.0)
    for record in ordered:
        ts = float(record.event_time_epoch_seconds or 0.0)
        if current and (ts - block_start) >= float(block_seconds):
            blocks.append(current)
            current = [record]
            block_start = ts
        else:
            current.append(record)
    if current:
        blocks.append(current)
    return blocks


def block_bootstrap_confidence_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_seconds: Sequence[int],
    repetitions: int = BOOTSTRAP_REPETITIONS,
    block_seconds: int = BOOTSTRAP_BLOCK_SECONDS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    blocks = _event_time_blocks(records, block_seconds=block_seconds)
    if not blocks:
        return {
            "executed": False,
            "reason": "no_blocks",
            "method": "BLOCK_BOOTSTRAP_EVENT_TIME_PRESERVING",
            "seed": seed,
            "repetitions": repetitions,
        }
    rng = random.Random(seed)
    out: dict[str, Any] = {}
    for seconds in candidate_seconds:
        samples: list[float] = []
        for _ in range(repetitions):
            drawn: list[ResearchEvidenceRecordV1] = []
            for _b in range(len(blocks)):
                drawn.extend(rng.choice(blocks))
            samples.append(_coverage(drawn, float(seconds)))
        samples_sorted = sorted(samples)
        lo = samples_sorted[int(0.025 * (len(samples_sorted) - 1))]
        hi = samples_sorted[int(0.975 * (len(samples_sorted) - 1))]
        out[f"CANDIDATE_{seconds}_S"] = {
            "mean_coverage": sum(samples) / len(samples),
            "ci95_low": lo,
            "ci95_high": hi,
            "n": len(samples),
        }
    return {
        "executed": True,
        "method": "BLOCK_BOOTSTRAP_EVENT_TIME_PRESERVING",
        "seed": seed,
        "repetitions": repetitions,
        "block_seconds": block_seconds,
        "limitations": [
            "TEMPORAL_DEPENDENCE_PRESERVED_VIA_BLOCKS",
            "NOT_IID_RESAMPLE",
        ],
        "results": out,
    }


def stress_matrices_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    candidate_seconds: Sequence[int],
) -> dict[str, Any]:
    if not records:
        return {"executed": False, "reason": "no_records"}

    missing = [r for r in records if r.estimate_present is not False][: max(1, len(records) // 2)]
    duplicates = list(records) + list(records[: max(1, len(records) // 4)])
    out_of_order = list(reversed(records))
    stale_heavy = [
        r
        for r in records
        if r.computed_age_seconds is not None and float(r.computed_age_seconds) >= 300.0
    ] or list(records)

    def _pack(label: str, rows: Sequence[ResearchEvidenceRecordV1]) -> dict[str, Any]:
        return {
            label: {
                f"CANDIDATE_{seconds}_S": evaluate_candidate_on_records_v1(
                    rows,
                    candidate_id=f"CANDIDATE_{seconds}_S",
                    candidate_max_age_seconds=float(seconds),
                )
                for seconds in candidate_seconds
            }
        }

    return {
        "executed": True,
        "missing_sample_stress": _pack("subset", missing),
        "duplicate_sample_stress": _pack("with_duplicates", duplicates),
        "out_of_order_stress": _pack("reversed_event_order_diagnostic", out_of_order),
        "stale_data_stress": _pack("stale_heavy", stale_heavy),
        "note": "Stress views are diagnostic only; out-of-order does not authorize shuffled splits.",
    }


def monte_carlo_applicability_v1(
    records: Sequence[ResearchEvidenceRecordV1],
) -> dict[str, Any]:
    has_fill_sequence = any(
        r.economic_metrics is not None
        and isinstance(r.economic_metrics, dict)
        and r.economic_metrics.get("fill_sequence")
        for r in records
    )
    if not has_fill_sequence:
        return {
            "executed": False,
            "monte_carlo_not_applicable_reason": (
                "NO_REAL_FILL_SEQUENCE_IN_JOINABLE_ECONOMIC_EVIDENCE"
            ),
        }
    return {
        "executed": False,
        "monte_carlo_not_applicable_reason": (
            "FILL_SEQUENCE_PRESENT_BUT_TRADE_SEQUENCE_MONTE_CARLO_NOT_WIRED_IN_V1;"
            "FAIL_CLOSED_NO_IID_FALLBACK"
        ),
    }

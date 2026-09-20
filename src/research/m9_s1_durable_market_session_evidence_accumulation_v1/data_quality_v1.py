"""Raw session/data-quality metrics without invented good/bad thresholds."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    ResearchEvidenceRecordV1,
)


def _age_values(records: Sequence[ResearchEvidenceRecordV1]) -> list[float]:
    out: list[float] = []
    for record in records:
        if record.computed_age_seconds is not None:
            out.append(float(record.computed_age_seconds))
    return out


def summarize_data_quality_raw_v1(
    records: Sequence[ResearchEvidenceRecordV1],
    *,
    source_class_counts: Optional[Mapping[str, int]] = None,
) -> dict[str, Any]:
    n = len(records)
    sessions = {r.session_id for r in records}
    cycle_ids = [r.cycle_id for r in records]
    dup_cycles = [cid for cid, count in Counter(cycle_ids).items() if count > 1]

    missing_age = sum(1 for r in records if r.computed_age_seconds is None)
    missing_estimate = sum(
        1 for r in records if r.estimate_present is False or r.estimate_present is None
    )

    epochs = sorted(e for e in (r.event_time_epoch_seconds for r in records) if e is not None)
    inter_gap_seconds: list[float] = []
    for prev, cur in zip(epochs, epochs[1:]):
        inter_gap_seconds.append(float(cur) - float(prev))

    ages = _age_values(records)
    ages_sorted = sorted(ages)

    def _percentile(p: float) -> Optional[float]:
        if not ages_sorted:
            return None
        idx = int(round((len(ages_sorted) - 1) * p))
        return ages_sorted[max(0, min(len(ages_sorted) - 1, idx))]

    return {
        "observation_count": n,
        "session_count": len(sessions),
        "duplicate_cycle_id_count": len(dup_cycles),
        "duplicate_cycle_ids": dup_cycles[:50],
        "missing_computed_age_count": missing_age,
        "missing_estimate_count": missing_estimate,
        "inter_observation_gap_seconds": {
            "count": len(inter_gap_seconds),
            "min": min(inter_gap_seconds) if inter_gap_seconds else None,
            "max": max(inter_gap_seconds) if inter_gap_seconds else None,
            "mean": (
                sum(inter_gap_seconds) / len(inter_gap_seconds) if inter_gap_seconds else None
            ),
        },
        "age_distribution_seconds": {
            "count": len(ages_sorted),
            "min": ages_sorted[0] if ages_sorted else None,
            "p50": _percentile(0.5),
            "p90": _percentile(0.9),
            "p99": _percentile(0.99),
            "max": ages_sorted[-1] if ages_sorted else None,
        },
        "temporal_coverage": {
            "first_event_epoch_seconds": epochs[0] if epochs else None,
            "last_event_epoch_seconds": epochs[-1] if epochs else None,
        },
        "source_class_counts": dict(source_class_counts or {}),
        "unresolved_criteria": [],
    }

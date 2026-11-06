"""Read-only D26 adapter: F1 parameter research candidate results → candidate classification."""

from __future__ import annotations

from typing import Any, Mapping

from src.governance.platform_unified_native_vs_candidate_baseline_evidence_v1 import (
    classify_f1_parameter_research_candidate_result_v1,
)


def bind_f1_parameter_research_candidate_baseline_classification_v1(
    *,
    candidate_result: Mapping[str, Any],
    baseline_reference: Mapping[str, Any],
) -> Mapping[str, Any]:
    record = classify_f1_parameter_research_candidate_result_v1(
        candidate_result=candidate_result,
        baseline_reference=baseline_reference,
    )
    return record.to_dict()


__all__ = ["bind_f1_parameter_research_candidate_baseline_classification_v1"]

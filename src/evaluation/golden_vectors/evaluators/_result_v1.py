"""Shared evaluator result helpers."""

from __future__ import annotations

from typing import Any

from src.evaluation.golden_vectors.contracts.enums import (
    DomainVerdict,
    EvaluationDomain,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import (
    BoundaryResultV1,
    DomainEvaluationResultV1,
    InvariantResultV1,
    MetricResultV1,
)


def pass_result(
    *,
    domain: EvaluationDomain,
    metrics: list[MetricResultV1],
    invariants: list[InvariantResultV1],
    boundary_results: list[BoundaryResultV1],
    evidence_refs: list[str],
    semantic_digest_deltas: dict[str, Any] | None = None,
) -> DomainEvaluationResultV1:
    return DomainEvaluationResultV1(
        domain=domain,
        verdict=DomainVerdict.PASS,
        metrics=metrics,
        invariants=invariants,
        boundary_results=boundary_results,
        evidence_refs=evidence_refs,
        semantic_digest_deltas=semantic_digest_deltas,
    )


def fail_result(
    *,
    domain: EvaluationDomain,
    failure: FailureClassification,
    detail: str,
    metrics: list[MetricResultV1] | None = None,
    boundary_results: list[BoundaryResultV1] | None = None,
) -> DomainEvaluationResultV1:
    return DomainEvaluationResultV1(
        domain=domain,
        verdict=DomainVerdict.FAIL,
        metrics=metrics or [],
        invariants=[
            InvariantResultV1(invariant_id="evaluator.fail_closed", pass_=False, detail=detail)
        ],
        boundary_results=boundary_results or [],
        evidence_refs=[],
        failure_classification=failure,
    )


def reproof_for_failure(failure: FailureClassification) -> FanOutEvaluationClass:
    """BWP-3 / BWP-3-RU default fan-out."""
    return failure_fan_out(
        failure,
        domain_local_reproof=FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION,
    )


def failure_fan_out(
    failure: FailureClassification,
    *,
    domain_local_reproof: FanOutEvaluationClass,
) -> FanOutEvaluationClass:
    if failure is FailureClassification.NON_DETERMINISM:
        return FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    return domain_local_reproof

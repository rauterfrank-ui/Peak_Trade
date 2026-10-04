"""Fan-out reproof helpers per BWP (generic, no domain trading logic)."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.enums import (
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.evaluators._result_v1 import failure_fan_out

BWP3_REPROOF = FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
BWP456_REPROOF = FanOutEvaluationClass.LOCAL_EVALUATION


def bwp3_failure_fan_out(failure: FailureClassification) -> FanOutEvaluationClass:
    return failure_fan_out(failure, domain_local_reproof=BWP3_REPROOF)


def bwp456_failure_fan_out(failure: FailureClassification) -> FanOutEvaluationClass:
    return failure_fan_out(failure, domain_local_reproof=BWP456_REPROOF)

"""BWP-8 promotion adapter authority errors (fail-closed)."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.enums import (
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError


class GvefPromotionAuthorityError(GvefSchemaError):
    failure_classification: FailureClassification = FailureClassification.AUTHORITY_FAILURE
    reproof_class: FanOutEvaluationClass = FanOutEvaluationClass.LOCAL_EVALUATION

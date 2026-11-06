"""Corpus integrity errors (BWP-7)."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.enums import (
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError


class GvefCorpusDriftError(GvefSchemaError):
    failure_classification: FailureClassification = FailureClassification.CORPUS_DRIFT
    reproof_class: FanOutEvaluationClass = FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF

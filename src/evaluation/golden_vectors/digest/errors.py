"""GVEF protected semantic digest layer errors (BWP-0D, fail-closed)."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.enums import DigestVerdict, FanOutEvaluationClass
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError


class GvefProtectedDigestDriftError(GvefSchemaError):
    failure_classification: str = "PROTECTED_DIGEST_DRIFT"

    def __init__(
        self,
        message: str,
        *,
        verdict: DigestVerdict,
        reproof_class: FanOutEvaluationClass,
        domain: str | None = None,
    ) -> None:
        super().__init__(message)
        self.verdict = verdict
        self.reproof_class = reproof_class
        self.domain = domain

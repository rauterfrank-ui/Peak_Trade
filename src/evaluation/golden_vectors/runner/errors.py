"""Runner orchestration errors."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError


class GvefRunnerError(GvefSchemaError):
    """Fail-closed runner failure."""


class GvefNonDeterminismError(GvefRunnerError):
    failure_classification: str = "NON_DETERMINISM"
    reproof_class: str = "WHOLE_SYSTEM_REPROOF"

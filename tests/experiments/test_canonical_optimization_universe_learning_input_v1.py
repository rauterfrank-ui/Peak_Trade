"""Contract tests for optimization-universe learning input v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    OPTIMIZATION_CAN_DEFINE_OPTIMIZABLE_ENVELOPE,
    OPTIMIZATION_CAN_TRIGGER_SEARCH,
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    STATUS_REJECTED_INVALID_EVIDENCE,
    CanonicalOptimizationUniverseLearningInputError,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state


def test_authority_constants_fail_closed() -> None:
    assert OPTIMIZATION_PRODUCTIVE_AUTHORITY == "NONE"
    assert OPTIMIZATION_CAN_TRIGGER_SEARCH is False
    assert OPTIMIZATION_CAN_DEFINE_OPTIMIZABLE_ENVELOPE is False


def test_accepts_valid_learning_evidence(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    assert result["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
    assert result["optimizable_envelope_defined"] is False
    assert result["external_effect_authorized"] is False


def test_rejects_missing_evidence() -> None:
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=None)
    )
    assert result["status"] == STATUS_REJECTED_INVALID_EVIDENCE


def test_forbidden_productive_join() -> None:
    with pytest.raises(CanonicalOptimizationUniverseLearningInputError):
        validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(
                learning_evidence={},
                requested_productive_join=True,
            )
        )

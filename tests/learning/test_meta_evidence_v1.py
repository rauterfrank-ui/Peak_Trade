"""META_EVIDENCE_V1 contract tests."""

from __future__ import annotations

import pytest

from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    MetaEvidenceValidationError,
    SemanticRoutingClass,
    build_meta_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    MetaLearningEvidenceValidationError,
)


def test_learning_representation_requires_lineage_ref() -> None:
    malformed = {
        "schema_version": "meta_learning_evidence_v1",
        "domain": "peak_trade.learning.ddo.meta_learning_evidence.v1",
        "universe_class": "SELF_LEARNING_UNIVERSE",
        "evidence_class": "META_LEARNING_EVIDENCE",
        "meta_evidence_id": "0" * 64,
        "source_experiment_ids": [],
        "source_envelope_versions": {},
        "observed_regime_or_context_ref": "test",
        "optimization_family": "UNKNOWN_UNAVAILABLE",
        "search_method": {"method_token": "UNKNOWN_UNAVAILABLE"},
        "repeated_success_or_failure_pattern": "test",
        "oos_robustness_pattern": {},
        "cost_slippage_failure_pattern": "UNKNOWN_UNAVAILABLE",
        "predictive_evidence_features": "UNKNOWN_UNAVAILABLE",
        "uncertainty": "UNKNOWN_UNAVAILABLE",
        "support_count": 0,
        "provenance": {},
        "reproducibility_digest": "a" * 64,
        "meta_evidence_authority": "NONE",
        "source_optimization_experiment_evidence_record_id": "rec.test",
        "source_optimization_experiment_evidence_digest": "b" * 64,
    }
    with pytest.raises((MetaEvidenceValidationError, MetaLearningEvidenceValidationError)):
        build_meta_evidence_v1(
            meta_learning_evidence=malformed,
            semantic_routing_class=SemanticRoutingClass.LEARNING_REPRESENTATION.value,
        )

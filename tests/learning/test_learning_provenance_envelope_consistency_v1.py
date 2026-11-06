"""Reject contradictory declared evidence classes without reclassifying source data."""

from copy import deepcopy

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    STATUS_REJECTED_INVALID_EVIDENCE,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import export_learning_evidence_from_state_v1
from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import build_learning_evidence_record_v1
from src.learning.deterministic_decision_outcome_v0.optimization_provenance_eligibility_v1 import (
    assert_optimization_pool_compatible_v1,
    evaluate_optimization_provenance_eligibility_v1,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state


@pytest.fixture
def evidence(tmp_path):
    return dict(export_learning_evidence_from_state_v1(_learning_state(tmp_path)))


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"outcome_semantic_class": "INTERNAL_SIMULATED_OUTCOME", "evidence_pool_class": "INTERNAL_SIMULATED_OUTCOME"}, "OUTCOME_SEMANTIC_CLASS_MISMATCH"),
        ({"evidence_pool_class": "INTERNAL_SIMULATED_OUTCOME"}, "EVIDENCE_POOL_CLASS_MISMATCH"),
        ({"outcome_evidence_provenance_digest": "0" * 64}, "PROVENANCE_DIGEST_MISMATCH"),
    ],
)
def test_direct_gate_rejects_declared_envelope_contradictions(evidence, changes, reason):
    changed = deepcopy(evidence)
    changed.update(changes)
    result = evaluate_optimization_provenance_eligibility_v1(changed)
    assert result.admitted is False
    assert result.reason_code == reason


def _relabeled(evidence):
    changed = deepcopy(evidence)
    changed.pop("content_hash")
    changed["outcome_semantic_class"] = "INTERNAL_SIMULATED_OUTCOME"
    changed["evidence_pool_class"] = "INTERNAL_SIMULATED_OUTCOME"
    return changed


def test_record_builder_rejects_consistent_outer_labels_that_contradict_embedded_class(evidence):
    with pytest.raises(DdoValidationError, match="OUTCOME_SEMANTIC_CLASS_MISMATCH"):
        build_learning_evidence_record_v1(_relabeled(evidence))


def test_outer_optimization_intake_rejects_a_record_that_could_previously_be_rehashed(evidence):
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=_relabeled(evidence))
    )
    assert result["status"] == STATUS_REJECTED_INVALID_EVIDENCE


def test_pool_compatibility_does_not_silently_replace_wrong_declared_pool(evidence):
    wrong = deepcopy(evidence)
    wrong["evidence_pool_class"] = "INTERNAL_SIMULATED_OUTCOME"
    with pytest.raises(DdoValidationError, match="OPTIMIZATION_POOL_INELIGIBLE_EVIDENCE"):
        assert_optimization_pool_compatible_v1(evidence, wrong)


def test_existing_minimal_pair_check_without_repeated_digest_remains_valid(evidence):
    minimal = {
        key: evidence[key] for key in ("outcome_evidence_provenance", "outcome_semantic_class", "evidence_pool_class")
    }
    assert evaluate_optimization_provenance_eligibility_v1(minimal).admitted
    assert_optimization_pool_compatible_v1(minimal, minimal)


def test_unchanged_export_is_accepted_without_relabeling_or_mutation(evidence):
    before = deepcopy(evidence)
    assert evaluate_optimization_provenance_eligibility_v1(evidence).admitted
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    assert result["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
    assert evidence == before
    assert result["external_effect_authorized"] is False

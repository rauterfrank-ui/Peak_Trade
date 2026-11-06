"""Absent stability values cannot satisfy a measured sample-size policy."""

import pytest

from src.experiments.canonical_meta_learning_v1 import (
    build_canonical_meta_learning_v1,
    QUESTION_PARAMETER_INSTABILITY,
)
from tests.experiments.test_canonical_meta_learning_v1 import (
    _identity,
    _unit,
    _request,
    _question,
    _policy,
)


def _build(values, minimum=2):
    identities = tuple(_identity(seed=100 + i) for i in range(len(values)))
    units = tuple(
        _unit(identity, parameter_stability=value)
        for identity, value in zip(identities, values, strict=True)
    )
    return build_canonical_meta_learning_v1(
        _request(
            identities=identities,
            units=units,
            policy=_policy(min_sample_size_descriptive=minimum),
            failure_records=(),
            reality_gap_records=(),
        )
    )


@pytest.mark.parametrize("values", [(0.1, None), (0.1, None, None, None)])
def test_missing_measurements_do_not_enable_instability_findings_or_proposals(values):
    question = _question(_build(values), QUESTION_PARAMETER_INSTABILITY)
    assert question["evidence_status"] == "INSUFFICIENT_SAMPLE"
    assert question["sample_size"] == 1
    assert question["comparable_sample_size"] == len(values)
    assert question["missing_evidence_count"] == len(values) - 1
    assert question["findings"] == [] and question["research_proposals"] == []


def test_known_stable_measurement_counts_in_coverage():
    question = _question(_build((0.1, 0.9, None)), QUESTION_PARAMETER_INSTABILITY)
    assert question["evidence_status"] == "COMPUTED"
    assert question["sample_size"] == 2
    assert question["comparable_sample_size"] == 3
    assert question["findings"][0]["unstable_count"] == 1


def test_all_missing_keeps_explicit_absence():
    question = _question(_build((None, None)), QUESTION_PARAMETER_INSTABILITY)
    assert question["sample_size"] == 0
    assert question["evidence_status"] == "INSUFFICIENT_EVIDENCE"
    assert question["missing_evidence_count"] == 2

"""Knowledge availability is chronological, independent of UTC text precision."""

from dataclasses import replace

import pytest

from src.experiments.canonical_meta_learning_v1 import (
    MetaLearningValidationError,
    build_canonical_meta_learning_v1,
)
from tests.experiments.test_canonical_meta_learning_v1 import _identity, _request, _unit


def _at(evidence: str, analysis: str, later: str | None = None):
    unit = _unit(_identity(), evidence_created_at=evidence)
    unit = replace(
        unit,
        later_outcome=(replace(unit.later_outcome, observed_at=later) if later is not None else None),
    )
    return _request(
        units=(unit,), failure_records=(), reality_gap_records=(), created_at=analysis
    )


@pytest.mark.parametrize(
    ("evidence", "analysis"),
    [
        ("2026-08-18T14:00:00.100Z", "2026-08-18T14:00:00Z"),
        ("2026-08-18T14:00:00.000000001Z", "2026-08-18T14:00:00.00000000Z"),
        ("2026-08-18T14:00:00.000000002Z", "2026-08-18T14:00:00.000000001Z"),
    ],
)
def test_future_evidence_is_rejected_even_with_mixed_or_nanosecond_precision(evidence, analysis):
    with pytest.raises(MetaLearningValidationError, match="lookahead"):
        build_canonical_meta_learning_v1(_at(evidence, analysis))


@pytest.mark.parametrize(
    ("evidence", "observed", "analysis"),
    [
        (
            "2026-08-18T14:00:00.100Z",
            "2026-08-18T14:00:00Z",
            "2026-08-18T14:00:01Z",
        ),
        (
            "2026-08-18T14:00:00Z",
            "2026-08-18T14:00:01.000000001Z",
            "2026-08-18T14:00:01Z",
        ),
    ],
)
def test_later_outcome_must_be_between_evidence_and_analysis(evidence, observed, analysis):
    with pytest.raises(MetaLearningValidationError, match="later_outcome lookahead"):
        build_canonical_meta_learning_v1(_at(evidence, analysis, observed))


@pytest.mark.parametrize(
    ("evidence", "observed", "analysis"),
    [
        (
            "2026-08-18T14:00:00Z",
            "2026-08-18T14:00:00.100Z",
            "2026-08-18T14:00:01Z",
        ),
        (
            "2026-08-18T14:00:00.000000000Z",
            "2026-08-18T14:00:00.0Z",
            "2026-08-18T14:00:00Z",
        ),
        (
            "2026-08-18T14:00:00.000000001Z",
            "2026-08-18T14:00:00.000000002Z",
            "2026-08-18T14:00:00.000000003Z",
        ),
    ],
)
def test_valid_instants_and_same_instant_spellings_remain_accepted(evidence, observed, analysis):
    result = build_canonical_meta_learning_v1(_at(evidence, analysis, observed))
    assert result["created_at"] == analysis


@pytest.mark.parametrize(
    "timestamp",
    ["2026-02-30T14:00:00Z", "2026-13-01T14:00:00Z", "2026-08-18T14:00:65Z"],
)
def test_invalid_calendar_time_is_not_a_research_timestamp(timestamp):
    with pytest.raises(MetaLearningValidationError, match="valid UTC calendar"):
        build_canonical_meta_learning_v1(_at(timestamp, timestamp))

"""Unit tests for the derived-only adjudication contract (no bound corpus)."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_DIMENSIONS,
    ADJUDICATION_OUTCOMES,
    CANDIDATE_FAMILIES,
    EXPECTED_CANDIDATE_COUNT,
    EXPECTED_CANDIDATE_FAMILY_COUNT,
    EXPECTED_COMPETING_MEMBER_COUNT,
    EXPECTED_COMPETING_SET_COUNT,
    EXPECTED_ORIGINAL_AMBIGUOUS_BINDING_COUNT,
    EXPECTED_REFERENCED_OVERLAY_CLASS_FAMILY_COUNT,
    NON_IDENTITY_IDS,
    REASON_CODES,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_evaluator import (
    classify_candidate_family,
    load_candidate_projection,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_guards import AdjudicationGuardProgram
from scripts.ops.forensic_structure_schema_v1.adjudication_models import PresenceTagged
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue


def test_schema_vocabulary_is_dimension_specific() -> None:
    assert "OCCURRENCE_IDENTITY" in ADJUDICATION_DIMENSIONS
    assert "AUTHORITY" in ADJUDICATION_DIMENSIONS
    assert len(ADJUDICATION_DIMENSIONS) == 15
    assert "PROVEN_OCCURRENCE_IDENTITY" in ADJUDICATION_OUTCOMES
    assert "PROVEN" not in ADJUDICATION_OUTCOMES
    assert "OPEN" not in ADJUDICATION_OUTCOMES
    assert "CLOSED" not in ADJUDICATION_OUTCOMES
    assert "NI_APPLIES" in REASON_CODES
    assert "SIDECAR_CONSTRUCTED" in REASON_CODES
    assert len(CANDIDATE_FAMILIES) == EXPECTED_CANDIDATE_FAMILY_COUNT == 11
    assert EXPECTED_REFERENCED_OVERLAY_CLASS_FAMILY_COUNT == 11
    assert EXPECTED_CANDIDATE_COUNT == 244
    assert EXPECTED_COMPETING_SET_COUNT == 8
    assert EXPECTED_COMPETING_MEMBER_COUNT == 18
    assert EXPECTED_ORIGINAL_AMBIGUOUS_BINDING_COUNT == 6
    assert len(NON_IDENTITY_IDS) == 17


def test_presence_encodings_stay_distinct() -> None:
    absent = PresenceTagged.absent().to_canonical()
    null = PresenceTagged.null().to_canonical()
    unknown = PresenceTagged.present("UNKNOWN").to_canonical()
    false_value = PresenceTagged.present(False).to_canonical()
    assert absent != null
    assert absent != false_value
    assert unknown != false_value
    opt_absent = OptionalValue.absent().to_canonical()
    opt_null = OptionalValue.null().to_canonical()
    assert opt_absent != opt_null
    assert absent["presence"] == "absent"


def test_family_classifier_covers_known_tokens() -> None:
    competing = {
        "append_epoch-cf0b6e987ba84af5d14b810882453867",
        "Z2AR",
    }
    assert classify_candidate_family("SRC-000001", competing) == "T3_SRC_ALIAS"
    assert classify_candidate_family("REL-000001", competing) == "T4_REL_ALIAS"
    assert classify_candidate_family("wrapper_pair-abc", competing) == "OVERLAY_WRAPPER_PAIR"
    assert (
        classify_candidate_family("append_epoch-cf0b6e987ba84af5d14b810882453867", competing)
        == "OVERLAY_APPEND_EPOCH_REUSED"
    )
    assert (
        classify_candidate_family("append_epoch-d28acf7143588971ee415ac6bac9bbb4", competing)
        == "OVERLAY_APPEND_EPOCH_UNIQUE"
    )
    assert classify_candidate_family("occ-abc", competing) == "LAYER1_OCCURRENCE"
    assert classify_candidate_family("Z2AR", competing) == "DOC_Z2AR"
    assert classify_candidate_family("§22", competing) == "DOC_SECTION_22"
    with pytest.raises(TransformationContractViolation):
        classify_candidate_family("not-a-family", competing)


def test_present_locus_incomplete_fails_closed() -> None:
    guards = AdjudicationGuardProgram()
    with pytest.raises(TransformationContractViolation) as exc:
        guards.assert_present_locus_complete({"kind": "BYTE_RANGE_EXACT"}, "x")
    assert exc.value.rule == "LOCUS_INCOMPLETE"


def test_proven_outcome_fails_closed() -> None:
    guards = AdjudicationGuardProgram()
    with pytest.raises(TransformationContractViolation):
        guards.assert_outcome_not_proven("PROVEN_OCCURRENCE_IDENTITY", "x")
    with pytest.raises(TransformationContractViolation):
        guards.assert_outcome_not_proven("PROVEN", "x")
    with pytest.raises(TransformationContractViolation):
        guards.assert_no_proven_occurrence(count=1, detail="x")


def test_silent_ambiguous_normalization_fails_closed() -> None:
    guards = AdjudicationGuardProgram()
    with pytest.raises(TransformationContractViolation) as exc:
        guards.assert_silent_ambiguous_normalization(
            original_ambiguous_count=6,
            competing_member_count=18,
            ambiguous_outcomes=18,
        )
    assert exc.value.rule == "SILENT_AMBIGUOUS_NORMALIZATION"


def test_candidate_projection_loads_from_git_tracked_alignment() -> None:
    loaded = load_candidate_projection()
    assert len(loaded["candidates"]) == 244
    assert loaded["candidate_index_sha256"] == (
        "9eaded3909af1c5e89148b93650b08448a5b51eda359d2c51b8ea86f798c075e"
    )
    proven = [row for row in loaded["candidates"] if row["occurrence_binding_proven"]]
    assert proven == []
    states = {row["candidate_state"] for row in loaded["candidates"]}
    assert states == {"UNRESOLVED"}

"""Unit tests for alignment-index guards, schema, and non-identity model."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_GUARD_NAMES,
    ALIGNMENT_LAYER_ID,
    EXPECTED_ENDPOINT_RECORD_COUNT,
    EXPECTED_LAYER3_RELATION_COUNT,
    EXPECTED_T4_RECORD_COUNT,
    EXPECTED_VIEW_COUNT,
    NON_IDENTITY_STATEMENTS,
)
from scripts.ops.forensic_structure_schema_v1.alignment_guards import AlignmentGuardProgram
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guard_inventory import inventory_named_guards
from scripts.ops.forensic_structure_schema_v1.guards import (
    forbid_absent_to_no_parent_collapse,
    forbid_candidate_as_proven_occurrence,
    forbid_cross_residual_close_order,
    forbid_disposition_input_rewrite,
    forbid_documentary_parent_as_proven_parentage,
    forbid_duplicate_evidence_collapse,
    forbid_epoch_order_as_currentness,
    forbid_epoch_order_as_supersession,
    forbid_later_record_as_winner,
    forbid_mechanical_order_as_dependency,
    forbid_missing_binding_as_negative_fact,
    forbid_open_residual_status_transition,
    forbid_provenance_collapse,
    forbid_retained_input_rewrite,
    forbid_sidecar_mutation,
    forbid_source_mutation,
    forbid_t4_declared_equals_tsv_globally_unverified,
    forbid_unknown_to_false_collapse,
)
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue


def test_expected_corpus_constants() -> None:
    assert EXPECTED_T4_RECORD_COUNT == 7175
    assert EXPECTED_LAYER3_RELATION_COUNT == 122
    assert EXPECTED_ENDPOINT_RECORD_COUNT == 244
    assert EXPECTED_VIEW_COUNT == 12
    assert ALIGNMENT_LAYER_ID.endswith("BINDING_CANDIDATE_ALIGNMENT_INDEX_V1")


def test_non_identity_statements_are_first_class_and_unnormalized() -> None:
    statements = [f"{left} != {right}" for _id, left, right in NON_IDENTITY_STATEMENTS]
    assert "TSV_DIRECTIONALITY != SIDECAR_DECLARED_RELATION_TYPE" in statements
    assert "T4_CONTAINS != WRAPPER_CONTAINS" in statements
    assert "OPEN != CLOSED" in statements
    assert "OPEN != UNPROVEN" in statements
    assert "ABSENT != NO_PARENT" in statements
    assert "UNKNOWN != FALSE" in statements
    assert len(NON_IDENTITY_STATEMENTS) == 17
    assert len(set(statements)) == 17


def test_optional_value_does_not_collapse_absent_null_unknown() -> None:
    absent = OptionalValue.absent()
    null = OptionalValue.null()
    unknown = OptionalValue.present("UNKNOWN")
    false_value = OptionalValue.present(False)
    assert absent.to_canonical() != null.to_canonical()
    assert absent.to_canonical() != false_value.to_canonical()
    assert unknown.to_canonical() != false_value.to_canonical()
    assert absent.presence == "absent"
    assert null.presence == "null"


@pytest.mark.parametrize(
    "fn,args",
    [
        (forbid_missing_binding_as_negative_fact, ("x",)),
        (forbid_cross_residual_close_order, ("x",)),
        (forbid_t4_declared_equals_tsv_globally_unverified, ("x",)),
        (forbid_candidate_as_proven_occurrence, ("x",)),
        (forbid_documentary_parent_as_proven_parentage, ("x",)),
        (forbid_mechanical_order_as_dependency, ("x",)),
        (forbid_epoch_order_as_currentness, ("x",)),
        (forbid_epoch_order_as_supersession, ("x",)),
        (forbid_later_record_as_winner, ("x",)),
        (forbid_open_residual_status_transition, ("SW-R-002", "CLOSED")),
        (forbid_source_mutation, ("x",)),
        (forbid_sidecar_mutation, ("x",)),
        (forbid_retained_input_rewrite, ("x",)),
        (forbid_disposition_input_rewrite, ("x",)),
        (forbid_unknown_to_false_collapse, ("x",)),
        (forbid_absent_to_no_parent_collapse, ("x",)),
        (forbid_duplicate_evidence_collapse, ("x",)),
        (forbid_provenance_collapse, ("x",)),
    ],
)
def test_alignment_guards_fail_closed(fn, args) -> None:
    with pytest.raises(TransformationContractViolation):
        fn(*args)


def test_alignment_guard_program_rejects_promotions() -> None:
    program = AlignmentGuardProgram()
    with pytest.raises(TransformationContractViolation):
        program.assert_authority_none("CANONICAL")
    with pytest.raises(TransformationContractViolation):
        program.assert_output_not_canonical(True)
    with pytest.raises(TransformationContractViolation):
        program.assert_candidate_not_proven(proven=True, detail="x")
    with pytest.raises(TransformationContractViolation):
        program.assert_parentage_not_proven(proven=True, detail="x")
    with pytest.raises(TransformationContractViolation):
        program.assert_open_residuals({"SW-R-002": "CLOSED"})
    with pytest.raises(TransformationContractViolation):
        program.assert_close_order_false(close_order=True, detail="x")
    with pytest.raises(TransformationContractViolation):
        program.assert_tsv_declared_not_global_identity(True)
    with pytest.raises(TransformationContractViolation):
        program.assert_current_locator_not_historical(
            "/Users/frnkhrz/Desktop/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
        )


def test_alignment_guards_are_defined_and_called() -> None:
    inventory = inventory_named_guards(ALIGNMENT_GUARD_NAMES)
    missing = [name for name, row in inventory.items() if not row["DEFINED"] or not row["CALLED"]]
    assert missing == []


def test_historical_desktop_path_is_not_current_source_constant() -> None:
    from scripts.ops.forensic_structure_schema_v1.constants import BOUND_SOURCE_PATH

    assert "/Desktop/" not in BOUND_SOURCE_PATH
    assert "/Downloads/" not in BOUND_SOURCE_PATH
    assert BOUND_SOURCE_PATH.endswith(
        "/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
    )

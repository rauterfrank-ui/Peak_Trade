"""Adversarial unit tests for the alignment index (no bound corpus required)."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.alignment_guards import AlignmentGuardProgram
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import (
    forbid_authority_promotion,
    forbid_candidate_as_proven_occurrence,
    forbid_cross_residual_close_order,
    forbid_documentary_parent_as_proven_parentage,
    forbid_epoch_order_as_currentness,
    forbid_epoch_order_as_supersession,
    forbid_later_record_as_winner,
    forbid_mechanical_order_as_dependency,
    forbid_missing_binding_as_negative_fact,
    forbid_open_residual_status_transition,
    forbid_unknown_to_false_collapse,
)


def test_candidate_is_never_proven() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_candidate_as_proven_occurrence("endpoint")
    assert exc.value.rule == "SW-R-004"


def test_documentary_parent_is_not_proven_parentage() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_documentary_parent_as_proven_parentage("H1 proximity")
    assert exc.value.rule == "SW-R-009"


def test_cross_residual_prerequisites_are_not_close_order() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_cross_residual_close_order("SW-R-002 <-> SW-R-004")
    assert exc.value.rule == "ALIGNMENT_CROSS_RESIDUAL_CLOSE_ORDER"


def test_epoch_order_is_not_currentness_or_supersession() -> None:
    with pytest.raises(TransformationContractViolation):
        forbid_epoch_order_as_currentness("PREFIX_EPOCH_SUCCEEDS")
    with pytest.raises(TransformationContractViolation):
        forbid_epoch_order_as_supersession("PREFIX_EPOCH_SUCCEEDS")


def test_later_record_is_not_winner() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_later_record_as_winner("later occurrence")
    assert exc.value.rule == "C5"


def test_mechanical_order_is_not_dependency() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_mechanical_order_as_dependency("STRUCTURAL_ORDERED_BEFORE")
    assert exc.value.rule == "D1"


def test_unknown_and_missing_do_not_become_false() -> None:
    with pytest.raises(TransformationContractViolation):
        forbid_unknown_to_false_collapse("UNKNOWN")
    with pytest.raises(TransformationContractViolation):
        forbid_missing_binding_as_negative_fact("missing=false")


def test_open_does_not_become_closed_or_unproven() -> None:
    with pytest.raises(TransformationContractViolation):
        forbid_open_residual_status_transition("SW-R-002", "CLOSED")
    with pytest.raises(TransformationContractViolation):
        forbid_open_residual_status_transition("SW-R-004", "UNPROVEN")


def test_authority_promotion_and_historical_locator_fail_closed() -> None:
    with pytest.raises(TransformationContractViolation):
        forbid_authority_promotion("CANONICAL")
    program = AlignmentGuardProgram()
    with pytest.raises(TransformationContractViolation) as exc:
        program.assert_current_locator_not_historical(
            "/Users/frnkhrz/Downloads/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
        )
    assert exc.value.rule == "HISTORICAL_LOCATOR"


def test_prerequisite_edge_rejected_state_is_required() -> None:
    program = AlignmentGuardProgram()
    with pytest.raises(TransformationContractViolation):
        program.assert_cross_prerequisites_not_close_order(
            [
                {
                    "edge_id": "XRE-PREREQ-000",
                    "close_order": False,
                    "provenance_class": "PR_6063_CROSS_RESIDUAL_PREREQUISITES",
                    "epistemic_state": "proven",
                }
            ]
        )

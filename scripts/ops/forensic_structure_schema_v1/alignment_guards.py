"""Fail-closed guards for the binding-candidate alignment index.

Additive. Existing GuardProgram rules remain in force.
"""

from __future__ import annotations

from typing import Any, Iterable

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_AUTHORITY,
    ALIGNMENT_CROSS_RESIDUAL_PREREQUISITES,
    ALIGNMENT_MUST_REMAIN_OPEN,
    EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT,
    HISTORICAL_LOCATOR_SUBSTRINGS,
    OPEN_CLUSTER_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import (
    GuardProgram,
    forbid_absent_to_no_parent_collapse,
    forbid_authority_promotion,
    forbid_candidate_as_proven_occurrence,
    forbid_cross_residual_close_order,
    forbid_documentary_parent_as_proven_parentage,
    forbid_duplicate_evidence_collapse,
    forbid_epoch_order_as_currentness,
    forbid_epoch_order_as_supersession,
    forbid_later_record_as_winner,
    forbid_mechanical_order_as_dependency,
    forbid_missing_binding_as_negative_fact,
    forbid_open_residual_status_transition,
    forbid_provenance_collapse,
    forbid_t4_declared_equals_tsv_globally_unverified,
    forbid_unknown_to_false_collapse,
)


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


class AlignmentGuardProgram:
    """Always-on alignment denylist. Candidate is never proven."""

    def __init__(self) -> None:
        self.base = GuardProgram()

    def assert_authority_none(self, observed: str) -> None:
        if observed != ALIGNMENT_AUTHORITY:
            forbid_authority_promotion(observed)

    def assert_output_not_canonical(self, output_canonical: bool) -> None:
        if output_canonical is True:
            _fail("C9", "alignment index claimed canonical")

    def assert_candidate_not_proven(self, *, proven: bool, detail: str) -> None:
        if proven:
            forbid_candidate_as_proven_occurrence(detail)

    def assert_parentage_not_proven(self, *, proven: bool, detail: str) -> None:
        if proven:
            forbid_documentary_parent_as_proven_parentage(detail)

    def assert_open_residuals(self, residual_status: dict[str, str]) -> None:
        for residual_id in (*OPEN_CLUSTER_RESIDUAL_IDS, *ALIGNMENT_MUST_REMAIN_OPEN):
            observed = residual_status.get(residual_id)
            if observed != "OPEN":
                forbid_open_residual_status_transition(residual_id, str(observed))

    def assert_close_order_false(self, *, close_order: bool, detail: str) -> None:
        if close_order:
            forbid_cross_residual_close_order(detail)

    def assert_cross_prerequisites_not_close_order(self, edges: Iterable[dict[str, Any]]) -> None:
        for edge in edges:
            if edge.get("close_order") is True:
                forbid_cross_residual_close_order(str(edge.get("edge_id")))
            provenance = str(edge.get("provenance_class", ""))
            if provenance == "PR_6063_CROSS_RESIDUAL_PREREQUISITES":
                if edge.get("epistemic_state") != "rejected":
                    forbid_cross_residual_close_order(
                        f"{edge.get('edge_id')} prerequisite not rejected-as-close-order"
                    )

    def assert_no_t4_layer3_backfill(self, *, mapped_null_count: int, backfill_count: int) -> None:
        if backfill_count != 0:
            _fail(
                "SW-R-002",
                f"T4_TO_LAYER3_BACKFILL attempted on {backfill_count} records",
            )
        if mapped_null_count != EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT:
            _fail(
                "SW-R-002",
                f"T4 layer3_mapped_type NULL count {mapped_null_count} "
                f"!= {EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT}",
            )

    def assert_missing_binding_not_false(self, presence: str, detail: str) -> None:
        if presence in {"absent", "ABSENT", "UNKNOWN"} and detail.endswith("=false"):
            forbid_missing_binding_as_negative_fact(detail)

    def assert_unknown_not_false(self, value: Any, detail: str) -> None:
        if value is False and "UNKNOWN" in detail:
            forbid_unknown_to_false_collapse(detail)

    def assert_absent_not_no_parent(self, payload: dict[str, Any]) -> None:
        if payload.get("parents_field_state") == "ABSENT":
            for token in ("NO_PARENT", "no_parent", "ROOT", "CHILDLESS"):
                if token in payload and payload.get(token) not in {None, False, "absent"}:
                    forbid_absent_to_no_parent_collapse(f"{payload.get('view_id')} {token}")

    def assert_tsv_declared_not_global_identity(self, claimed_global_identity: bool) -> None:
        if claimed_global_identity:
            forbid_t4_declared_equals_tsv_globally_unverified("global identity claimed")

    def assert_mechanical_order_not_dependency(self, *, is_dependency: bool, detail: str) -> None:
        if is_dependency:
            forbid_mechanical_order_as_dependency(detail)

    def assert_epoch_not_currentness(self, *, promoted: bool, detail: str) -> None:
        if promoted:
            forbid_epoch_order_as_currentness(detail)

    def assert_epoch_not_supersession(self, *, promoted: bool, detail: str) -> None:
        if promoted:
            forbid_epoch_order_as_supersession(detail)

    def assert_later_not_winner(self, *, winner_selected: bool, detail: str) -> None:
        if winner_selected:
            forbid_later_record_as_winner(detail)

    def assert_no_duplicate_collapse(self, *, collapsed: bool, detail: str) -> None:
        if collapsed:
            forbid_duplicate_evidence_collapse(detail)

    def assert_provenance_preserved(self, left: str, right: str) -> None:
        if left != right and not left and not right:
            forbid_provenance_collapse("empty provenance pair")

    def assert_current_locator_not_historical(self, path: str) -> None:
        for token in HISTORICAL_LOCATOR_SUBSTRINGS:
            if token in path:
                _fail(
                    "HISTORICAL_LOCATOR",
                    f"historical Desktop/Downloads path used as current locator: {path}",
                )

    def assert_prerequisites_table_not_empty(self) -> None:
        if not ALIGNMENT_CROSS_RESIDUAL_PREREQUISITES:
            _fail("ALIGNMENT_CROSS_RESIDUAL_CLOSE_ORDER", "prerequisite table missing")

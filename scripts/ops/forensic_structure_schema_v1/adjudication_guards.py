"""Fail-closed guards for the derived-only adjudication contract."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_AUTHORITY,
    ADJUDICATION_MUST_REMAIN_OPEN,
    ADJUDICATION_OPEN_CLUSTER,
    ADJUDICATION_OUTCOMES,
    FORBIDDEN_NAKED_OUTCOMES,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import (
    forbid_authority_promotion,
    forbid_candidate_as_proven_occurrence,
    forbid_documentary_parent_as_proven_parentage,
    forbid_epoch_order_as_currentness,
    forbid_epoch_order_as_supersession,
    forbid_later_record_as_winner,
    forbid_open_residual_status_transition,
    forbid_sidecar_mutation,
    forbid_source_mutation,
)


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


class AdjudicationGuardProgram:
    """Always-on denylist. Structure does not create authority or identity."""

    def assert_authority_none(self, observed: str) -> None:
        if observed != ADJUDICATION_AUTHORITY:
            forbid_authority_promotion(observed)

    def assert_output_not_canonical(self, output_canonical: bool) -> None:
        if output_canonical is True:
            _fail("C9", "adjudication contract claimed canonical")

    def assert_no_proven_occurrence(self, *, count: int, detail: str) -> None:
        if count != 0:
            forbid_candidate_as_proven_occurrence(detail)

    def assert_outcome_not_proven(self, outcome: str, detail: str) -> None:
        if outcome == "PROVEN_OCCURRENCE_IDENTITY":
            forbid_candidate_as_proven_occurrence(detail)
        if outcome in FORBIDDEN_NAKED_OUTCOMES:
            _fail("NAKED_OUTCOME", f"naked outcome {outcome} forbidden: {detail}")
        if outcome not in ADJUDICATION_OUTCOMES:
            _fail("UNKNOWN_OUTCOME", f"unknown outcome {outcome}: {detail}")

    def assert_no_parentage(self, *, performed: bool, count: int, detail: str) -> None:
        if performed or count != 0:
            forbid_documentary_parent_as_proven_parentage(detail)

    def assert_no_currentness(self, *, performed: bool, detail: str) -> None:
        if performed:
            forbid_epoch_order_as_currentness(detail)

    def assert_no_supersession(self, *, performed: bool, detail: str) -> None:
        if performed:
            forbid_epoch_order_as_supersession(detail)

    def assert_no_winner(self, *, count: int, detail: str) -> None:
        if count != 0:
            forbid_later_record_as_winner(detail)

    def assert_no_residual_close(self, *, performed: bool, residual_status: dict[str, str]) -> None:
        if performed:
            _fail("STAGE_H", "residual close performed")
        for residual_id in (*ADJUDICATION_OPEN_CLUSTER, *ADJUDICATION_MUST_REMAIN_OPEN):
            observed = residual_status.get(residual_id)
            if observed != "OPEN":
                forbid_open_residual_status_transition(residual_id, str(observed))

    def assert_no_bind_from_alias(self, *, bound: bool, detail: str) -> None:
        if bound:
            _fail("NI-006", f"alias-only occurrence bind forbidden: {detail}")

    def assert_no_bind_from_sha(self, *, bound: bool, detail: str) -> None:
        if bound:
            _fail("CORPUS_SHA_NOT_OCCURRENCE_PROOF", f"sha-only bind forbidden: {detail}")

    def assert_no_bind_from_string_equality(self, *, bound: bool, detail: str) -> None:
        if bound:
            _fail("NI-004", f"string-equality occurrence bind forbidden: {detail}")

    def assert_no_bind_from_adjacency(self, *, bound: bool, detail: str) -> None:
        if bound:
            _fail("NI-011", f"adjacency bind/dependency forbidden: {detail}")

    def assert_present_locus_complete(self, locus: dict[str, Any], detail: str) -> None:
        required = ("kind", "byte_start", "byte_end", "layer1_occurrence_id")
        missing = [key for key in required if key not in locus or locus[key] in (None, "")]
        if missing:
            _fail("LOCUS_INCOMPLETE", f"PRESENT locus incomplete {missing}: {detail}")
        if not isinstance(locus["byte_start"], int) or not isinstance(locus["byte_end"], int):
            _fail("LOCUS_INCOMPLETE", f"PRESENT locus byte range not int: {detail}")

    def assert_source_unmutated(self, before: str, after: str) -> None:
        if before != after:
            forbid_source_mutation("source hash changed")

    def assert_sidecar_unmutated(self, before: str, after: str) -> None:
        if before != after:
            forbid_sidecar_mutation("sidecar hash changed")

    def assert_silent_ambiguous_normalization(
        self,
        *,
        original_ambiguous_count: int,
        competing_member_count: int,
        ambiguous_outcomes: int,
    ) -> None:
        if original_ambiguous_count != 6:
            _fail(
                "AMBIGUOUS_UNDERCOUNT",
                f"original AMBIGUOUS_BINDING count {original_ambiguous_count} != 6",
            )
        if competing_member_count != 18:
            _fail(
                "COMPETING_SET_DRIFT",
                f"competing member count {competing_member_count} != 18",
            )
        if ambiguous_outcomes != original_ambiguous_count:
            _fail(
                "SILENT_AMBIGUOUS_NORMALIZATION",
                "competing-set members silently reclassified as AMBIGUOUS_COMPETING",
            )

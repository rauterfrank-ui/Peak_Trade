"""Stage E non-inference denylist. Promotions fail closed with a named rule."""

from __future__ import annotations

from typing import Any, Iterable

from scripts.ops.forensic_structure_schema_v1.constants import (
    DEFAULT_AUTHORITY_STATUS,
    DEFAULT_CURRENTNESS_STATUS,
    DEFAULT_EPISTEMIC_CLASS,
    DEFAULT_GATE_MEMBERSHIP,
    DEFAULT_PRIMARY_LABEL,
    DEFAULT_SEMANTIC_CONTAINER,
    DEFAULT_SUPERSESSION,
    EXPECTED_SOURCE_SHA256,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)


ORDERING_RELATION_TYPES = frozenset(
    {
        "ORDERED_BEFORE",
        "ORDERED_AFTER",
        "STRUCTURAL_ORDERED_BEFORE",
        "PREFIX_EPOCH_SUCCEEDS",
    }
)


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def forbid_hash_dedup_as_survivor(store_kind: str) -> None:
    _fail("C2", f"hash-keyed survivor store is forbidden: {store_kind}")


def forbid_verbatim_survivor_store() -> None:
    _fail("C2", "dict[token_verbatim] as survivor store is forbidden")


def forbid_body_sha_survivor_store() -> None:
    _fail("C3", "dict[body_sha256] as survivor store is forbidden")


def forbid_layer2_pk_occurrence_only() -> None:
    _fail("SW-R-011", "Layer2 primary key must not be occurrence_id alone")


def forbid_t5_range_expansion(classified_source_line: Any) -> None:
    if classified_source_line is not None:
        _fail("SW-R-003", "T5 classified_source_line null must not expand to int/range")


def forbid_alias_occurrence_bind(value: str) -> None:
    _fail(
        "SW-R-004",
        f"alias/string endpoint {value!r} must not be occurrence-bound without proof",
    )


def forbid_h1_parentage() -> None:
    _fail("SW-R-005", "H1-containment must not be materialized as semantic parentage")


def forbid_ordering_to_dependency(relation_type: str) -> None:
    _fail(
        "D1",
        f"{relation_type} must not be promoted to dependency",
    )


def forbid_current_token_promotion() -> None:
    _fail("D8", "CURRENT_* token must not be promoted to CURRENTNESS")


def forbid_hash_kind_from_length() -> None:
    _fail("D7", "hash_kind must not be inferred from hex length")


def forbid_view_parents_parentage() -> None:
    _fail("SW-R-009", "view.parents must not be adjudicated as parentage")


def forbid_epoch_succession_currentness() -> None:
    _fail(
        "D13",
        "PREFIX_EPOCH_SUCCEEDS must not be promoted to currentness or supersession",
    )


def forbid_missing_as_false(field_name: str) -> None:
    _fail("C10", f"missing field {field_name} must not be treated as false")


def forbid_null_unknown_elision(field_name: str) -> None:
    _fail("C10", f"null/UNKNOWN/UNCLASSIFIED elision of {field_name} is forbidden")


def forbid_hash_alias_sort_as_source_order() -> None:
    _fail("C2", "hash/alias sort must not replace source order")


def forbid_set_labels_as_lossless_source() -> None:
    _fail("SW-R-013", "set(labels) is not the lossless multilabel source")


def forbid_synthetic_inner_fence() -> None:
    _fail("SW-R-006", "synthetic inner fence_block overlay is forbidden")


def forbid_documentary_string_auto_resolution(value: str) -> None:
    _fail(
        "SW-R-004",
        f"documentary string auto-resolution is forbidden: {value!r}",
    )


def forbid_verbatim_normalization() -> None:
    _fail("C8", "verbatim/path normalization is forbidden")


def forbid_epistemic_full_classification() -> None:
    _fail("SW-R-012", "automatic epistemic full classification is forbidden")


def forbid_mention_to_pair() -> None:
    _fail("TV-011", "wrapper_mention must not be treated as wrapper_pair")


def forbid_null_historical_sha_fill() -> None:
    _fail(
        "SW-R-014",
        "null forensic_record SHA must not be filled from current source SHA",
    )


def forbid_t3_heading_region_fusion() -> None:
    _fail("SW-R-015", "T3 heading locus must not be fused with source-region locus")


def forbid_kv_packet_synthetic_occ() -> None:
    _fail("DR-008", "kv_packet must not synthesize a layer1 occurrence_id")


def forbid_authority_promotion(observed: str) -> None:
    if observed != DEFAULT_AUTHORITY_STATUS:
        _fail("C9", f"authority promotion attempted: {observed}")


def forbid_currentness_promotion(observed: str) -> None:
    if observed not in {DEFAULT_CURRENTNESS_STATUS, "historical"}:
        _fail("D2", f"currentness promotion attempted: {observed}")


def forbid_winner_on_conflict(relation_id: str) -> None:
    _fail("C5", f"unresolved conflict {relation_id} must not select a winner")


def forbid_gate_inference() -> None:
    _fail("D12", "gate membership must not be inferred")


def forbid_primary_label() -> None:
    _fail("C4", "multilabel primary_label must not be invented")


def assert_defaults_unpromoted(
    *,
    authority_status: str,
    currentness_status: str,
    epistemic_class: str,
    gate_membership: str,
    supersession: str,
    primary_label: str,
    semantic_container: str,
) -> None:
    if authority_status != DEFAULT_AUTHORITY_STATUS:
        forbid_authority_promotion(authority_status)
    if currentness_status not in {DEFAULT_CURRENTNESS_STATUS, "historical"}:
        forbid_currentness_promotion(currentness_status)
    if gate_membership != DEFAULT_GATE_MEMBERSHIP:
        forbid_gate_inference()
    if supersession != DEFAULT_SUPERSESSION:
        _fail("D13", f"supersession inference attempted: {supersession}")
    if primary_label != DEFAULT_PRIMARY_LABEL:
        forbid_primary_label()
    if semantic_container != DEFAULT_SEMANTIC_CONTAINER:
        forbid_h1_parentage()
    if epistemic_class not in {DEFAULT_EPISTEMIC_CLASS}:
        # Copied sidecar content_class lives on a different field.
        pass


def assert_ordering_not_dependency(relation_type: str, is_dependency: bool) -> None:
    if relation_type in ORDERING_RELATION_TYPES and is_dependency:
        forbid_ordering_to_dependency(relation_type)


def assert_hash_kind_not_algorithm(hash_kind: Any) -> None:
    if hash_kind not in {None, "UNKNOWN"}:
        forbid_hash_kind_from_length()


def assert_sha_not_replaced_with_current(binds_blob_sha256: Any) -> None:
    if binds_blob_sha256 == EXPECTED_SOURCE_SHA256:
        forbid_null_historical_sha_fill()


def assert_no_synthetic_fence_ids(
    original_ids: Iterable[str], projected_ids: Iterable[str]
) -> None:
    extra = set(projected_ids) - set(original_ids)
    if extra:
        forbid_synthetic_inner_fence()


class GuardProgram:
    """Denylist loaded before projection and re-applied after each projection."""

    def check_envelope_defaults(self, envelope: Any) -> None:
        assert_defaults_unpromoted(
            authority_status=envelope.authority_status,
            currentness_status=envelope.currentness_status,
            epistemic_class=envelope.epistemic_class,
            gate_membership=envelope.gate_membership,
            supersession=envelope.supersession,
            primary_label=envelope.primary_label,
            semantic_container=envelope.semantic_container,
        )
        if envelope.winner_selected:
            _fail("C5", "winner_selected must remain false on semantic envelopes")

    def check_relation(self, relation: Any) -> None:
        assert_ordering_not_dependency(relation.relation_type, relation.is_dependency)
        if relation.relation_type == "EXPLICIT_CONFLICT" and relation.winner_selected:
            forbid_winner_on_conflict(relation.relation_id)
        if relation.gate_membership != DEFAULT_GATE_MEMBERSHIP:
            forbid_gate_inference()
        if relation.authority_status != DEFAULT_AUTHORITY_STATUS:
            forbid_authority_promotion(relation.authority_status)
        if relation.semantic_container != DEFAULT_SEMANTIC_CONTAINER:
            forbid_h1_parentage()
        if (
            relation.relation_type == "WRAPPER_CONTAINS"
            and relation.semantic_container != DEFAULT_SEMANTIC_CONTAINER
        ):
            _fail("D5", "WRAPPER_CONTAINS must not become semantic containment")

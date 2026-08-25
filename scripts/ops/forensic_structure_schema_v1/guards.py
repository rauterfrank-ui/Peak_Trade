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


def forbid_absent_view_parents_as_no_parent(view_id: str, token: str) -> None:
    _fail(
        "G2",
        f"{view_id} ABSENT view.parents must not be normalized to {token}",
    )


def forbid_t4_directionality_identity_with_layer3_relation_type(
    declared_relation_type: str, layer3_relation_type: str
) -> None:
    _fail(
        "G3",
        "T4 declared_relation_type/directionality must not be treated as identical "
        f"to Layer-3 relation_type: {declared_relation_type!r} == {layer3_relation_type!r}",
    )


def forbid_t4_contains_fusion_with_wrapper_contains(detail: str) -> None:
    _fail("G4", f"T4 CONTAINS must not be fused with WRAPPER_CONTAINS: {detail}")


def forbid_layer3_ordered_before_as_t4_src_target_pair(detail: str) -> None:
    _fail(
        "G5",
        "Layer-3 STRUCTURAL_ORDERED_BEFORE must not be reinterpreted as "
        f"T4 (source_src_id, target_ref): {detail}",
    )


def forbid_section_22_rewrite_as_source_identity(value: str) -> None:
    _fail(
        "G6",
        f"SECTION_22 -> {value!r} rewrite must not be treated as source identity",
    )


def forbid_sidecar_dependency_subject_as_source_identity(value: str) -> None:
    _fail(
        "G6",
        f"sidecar-constructed dependency from_id {value!r} is not source identity",
    )


def forbid_missing_binding_as_negative_fact(detail: str) -> None:
    _fail("ALIGNMENT_MISSING_BINDING", f"missing binding must not become a negative fact: {detail}")


def forbid_cross_residual_close_order(detail: str) -> None:
    _fail(
        "ALIGNMENT_CROSS_RESIDUAL_CLOSE_ORDER",
        f"CROSS_RESIDUAL_PREREQUISITES must not be treated as close-order: {detail}",
    )


def forbid_t4_declared_equals_tsv_globally_unverified(detail: str) -> None:
    _fail(
        "ALIGNMENT_T4_DECLARED_TSV_IDENTITY",
        "T4 declared_relation_type must not be globally identified with TSV "
        f"directionality: {detail}",
    )


def forbid_candidate_as_proven_occurrence(detail: str) -> None:
    _fail(
        "SW-R-004",
        f"binding candidate must not be treated as proven occurrence: {detail}",
    )


def forbid_documentary_parent_as_proven_parentage(detail: str) -> None:
    _fail(
        "SW-R-009",
        f"documentary parent hint must not be treated as proven parentage: {detail}",
    )


def forbid_mechanical_order_as_dependency(detail: str) -> None:
    _fail("D1", f"mechanical order must not be treated as dependency: {detail}")


def forbid_epoch_order_as_currentness(detail: str) -> None:
    _fail("D13", f"epoch order must not be treated as currentness: {detail}")


def forbid_epoch_order_as_supersession(detail: str) -> None:
    _fail("D13", f"epoch order must not be treated as supersession: {detail}")


def forbid_later_record_as_winner(detail: str) -> None:
    _fail("C5", f"later record must not be selected as winner: {detail}")


def forbid_open_residual_status_transition(residual_id: str, observed: str) -> None:
    _fail(
        "STAGE_H",
        f"open residual {residual_id} must not transition from OPEN to {observed}",
    )


def forbid_source_mutation(detail: str) -> None:
    _fail("SOURCE_MUTATION", f"source mutation is forbidden: {detail}")


def forbid_sidecar_mutation(detail: str) -> None:
    _fail("SIDECAR_MUTATION", f"sidecar mutation is forbidden: {detail}")


def forbid_retained_input_rewrite(detail: str) -> None:
    _fail("RETAINED_INPUT_REWRITE", f"A-L retained input rewrite is forbidden: {detail}")


def forbid_disposition_input_rewrite(detail: str) -> None:
    _fail(
        "DISPOSITION_INPUT_REWRITE",
        f"PR-6063 disposition input rewrite is forbidden: {detail}",
    )


def forbid_unknown_to_false_collapse(detail: str) -> None:
    _fail("C10", f"UNKNOWN must not collapse to false: {detail}")


def forbid_absent_to_no_parent_collapse(detail: str) -> None:
    _fail("G2", f"ABSENT must not collapse to NO_PARENT: {detail}")


def forbid_duplicate_evidence_collapse(detail: str) -> None:
    _fail("C2", f"duplicate evidence must not be collapsed: {detail}")


def forbid_provenance_collapse(detail: str) -> None:
    _fail("C2", f"provenance must not be collapsed: {detail}")


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
        if relation.relation_type == "PREFIX_EPOCH_SUCCEEDS":
            self.assert_epoch_succession_not_currentness(relation)
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
        self.assert_endpoint_not_occurrence_bound(relation.from_binding)
        self.assert_endpoint_not_occurrence_bound(relation.to_binding)

    def assert_epoch_succession_not_currentness(self, relation: Any) -> None:
        """Always invoked for PREFIX_EPOCH_SUCCEEDS. Promotions fail closed (G1)."""
        currentness = str(getattr(relation, "currentness_status", DEFAULT_CURRENTNESS_STATUS))
        supersession = str(getattr(relation, "supersession", DEFAULT_SUPERSESSION))
        authority = str(getattr(relation, "authority_status", DEFAULT_AUTHORITY_STATUS))
        rtype = str(relation.relation_type)
        promoted = (
            bool(relation.is_dependency)
            or bool(relation.winner_selected)
            or currentness not in {DEFAULT_CURRENTNESS_STATUS, "historical"}
            or supersession != DEFAULT_SUPERSESSION
            or authority != DEFAULT_AUTHORITY_STATUS
            or rtype in {"CURRENT", "SUPERSEDED", "WINNER", "CANONICAL_SUCCESSOR"}
            or currentness in {"CURRENT", "SUPERSEDED"}
            or supersession in {"SUPERSEDED", "CURRENT", "CANONICAL_SUCCESSOR"}
        )
        if promoted:
            forbid_epoch_succession_currentness()

    def assert_endpoint_not_occurrence_bound(self, binding: Any) -> None:
        """Always invoked. Alias/documentary strings stay occurrence-unbound (SW-R-004)."""
        kind = str(binding.kind)
        unresolved = bool(binding.unresolved_to_occurrence)
        if kind == "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY" and not unresolved:
            forbid_alias_occurrence_bind(str(binding.value))
        if kind == "DOCUMENTARY_STRING_ENDPOINT" and not unresolved:
            forbid_documentary_string_auto_resolution(str(binding.value))

    def assert_view_parents_not_parentage(self, view: dict[str, Any]) -> None:
        """Always invoked for retained views (SW-R-009 / G2)."""
        if view.get("parentage_adjudicated") is True:
            forbid_view_parents_parentage()
        if view.get("sw_r_009_status") not in {None, "OPEN"}:
            forbid_view_parents_parentage()
        status = view.get("parents_field_status")
        if status == "ABSENT":
            self.assert_absent_parents_not_normalized(view)

    def assert_absent_parents_not_normalized(self, view: dict[str, Any]) -> None:
        from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
            ABSENT_PARENT_FORBIDDEN_KEYS,
        )

        view_id = str(view.get("view_id", "<unknown>"))
        if view.get("parents") == {}:
            forbid_absent_view_parents_as_no_parent(view_id, "parents={}")
        for token in ABSENT_PARENT_FORBIDDEN_KEYS:
            if token in view and view.get(token) not in {None, "absent"}:
                forbid_absent_view_parents_as_no_parent(view_id, token)
            original = view.get("original_view")
            if isinstance(original, dict) and token in original:
                forbid_absent_view_parents_as_no_parent(view_id, f"original_view.{token}")

    def check_cluster_projection(self, relation: Any, state: Any) -> None:
        """G3–G6 projection guards. Additive; does not rewrite the relation."""
        rtype = str(relation.relation_type)
        overlay = None
        overlay_id = relation.sidecar_overlay_id
        if overlay_id.presence == "present":
            overlay = state.overlay_by_id.get(str(overlay_id.value))
        if rtype == "STRUCTURAL_ORDERED_BEFORE":
            self._check_g3_g5_ordered_before(relation, overlay, state)
        if rtype == "WRAPPER_CONTAINS":
            self._check_g4_wrapper_not_t4_contains(relation, overlay)
        if rtype == "EXPLICIT_CONFLICT":
            self._check_g6_section_22(relation)
        if rtype == "EXPLICIT_DEPENDENCY":
            self._check_g6_dependency_subject(relation)

    def _check_g3_g5_ordered_before(self, relation: Any, overlay: Any, state: Any) -> None:
        if overlay is None:
            _fail("G5", f"{relation.relation_id} missing t4 overlay for projection audit")
        declared = str(overlay.payload.get("declared_relation_type"))
        mapped = overlay.payload.get("layer3_mapped_type")
        if declared == str(relation.relation_type):
            forbid_t4_directionality_identity_with_layer3_relation_type(
                declared, str(relation.relation_type)
            )
        if "directionality" in overlay.payload:
            _fail(
                "G3",
                f"{overlay.overlay_id} unexpectedly carries source field name directionality",
            )
        if mapped != "STRUCTURAL_ORDERED_BEFORE":
            _fail("G3", f"{relation.relation_id} layer3_mapped_type is not derived mapping")
        subject = str(overlay.payload.get("subject"))
        from_id = str(relation.from_binding.value)
        to_id = str(relation.to_binding.value)
        if not from_id.startswith("REL-"):
            forbid_layer3_ordered_before_as_t4_src_target_pair(
                f"{relation.relation_id} from_id {from_id} is not T4_REL_ALIAS"
            )
        if to_id != subject:
            forbid_layer3_ordered_before_as_t4_src_target_pair(
                f"{relation.relation_id} to_id {to_id} != overlay.subject {subject}"
            )
        raw = _t4_raw_line(state, overlay)
        if raw is None:
            return
        fields = raw.split("|")
        if len(fields) != int(overlay.payload.get("field_count") or 0):
            _fail("G5", f"{overlay.overlay_id} TSV field_count drift")
        from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
            DERIVED_T4_TSV_INDEX,
        )

        directionality = fields[DERIVED_T4_TSV_INDEX["directionality"]]
        target_ref = fields[DERIVED_T4_TSV_INDEX["target_ref"]]
        subject_src = fields[DERIVED_T4_TSV_INDEX["subject_src"]]
        if directionality == str(relation.relation_type):
            forbid_t4_directionality_identity_with_layer3_relation_type(
                directionality, str(relation.relation_type)
            )
        if directionality != declared:
            _fail("G3", f"{overlay.overlay_id} derived directionality != declared_relation_type")
        if subject_src != to_id:
            forbid_layer3_ordered_before_as_t4_src_target_pair(
                f"{relation.relation_id} TSV subject {subject_src} != to_id {to_id}"
            )
        if to_id == target_ref:
            forbid_layer3_ordered_before_as_t4_src_target_pair(
                f"{relation.relation_id} to_id equals TSV target_ref {target_ref}"
            )

    def _check_g4_wrapper_not_t4_contains(self, relation: Any, overlay: Any) -> None:
        if overlay is not None and overlay.overlay_class == "t4_rel_row":
            forbid_t4_contains_fusion_with_wrapper_contains(
                f"{relation.relation_id} bound to t4 overlay {overlay.overlay_id}"
            )
        if str(relation.relation_type) == "CONTAINS":
            forbid_t4_contains_fusion_with_wrapper_contains(relation.relation_id)

    def _check_g6_section_22(self, relation: Any) -> None:
        from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
            SECTION_22_SIDECAR_ENDPOINT,
        )

        for binding in (relation.from_binding, relation.to_binding):
            if str(binding.value) == SECTION_22_SIDECAR_ENDPOINT:
                if binding.kind == "LAYER1_OCCURRENCE_REFERENCE":
                    forbid_section_22_rewrite_as_source_identity(str(binding.value))
                if not binding.unresolved_to_occurrence:
                    forbid_section_22_rewrite_as_source_identity(str(binding.value))

    def _check_g6_dependency_subject(self, relation: Any) -> None:
        from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
            SIDECAR_DEPENDENCY_SUBJECT,
        )

        value = str(relation.from_binding.value)
        if value == SIDECAR_DEPENDENCY_SUBJECT:
            if relation.from_binding.kind == "LAYER1_OCCURRENCE_REFERENCE":
                forbid_sidecar_dependency_subject_as_source_identity(value)
            if not relation.from_binding.unresolved_to_occurrence:
                forbid_sidecar_dependency_subject_as_source_identity(value)


def _t4_raw_line(state: Any, overlay: Any) -> str | None:
    start = overlay.payload.get("byte_start")
    end = overlay.payload.get("byte_end")
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    return state.source_bytes[start:end].decode("utf-8")

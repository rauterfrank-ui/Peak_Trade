"""Build the additive binding-candidate / alignment index.

Covers the full known alignment space: T4 overlays, Layer-3 relations,
endpoint candidates, views, cross-residual evidence, and non-identities.
Does not close residuals, bind occurrences, or adjudicate parentage.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_AUTHORITY,
    ALIGNMENT_CROSS_RESIDUAL_PREREQUISITES,
    ALIGNMENT_GENERATOR_ID,
    ALIGNMENT_LAYER_ID,
    ALIGNMENT_MUST_REMAIN_OPEN,
    ALIGNMENT_OUTPUT_ROLE,
    ALIGNMENT_TRANSFORMATION_VERSION,
    A_L_CATALOG_RELPATH,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    DISPOSITION_RELPATH,
    EXPECTED_A_L_DATASET_SHA256,
    EXPECTED_DATASET_CATALOG_SHA256,
    EXPECTED_DISPOSITION_LAYER_SHA256,
    EXPECTED_ENDPOINT_RECORD_COUNT,
    EXPECTED_LAYER3_RELATION_COUNT,
    EXPECTED_OCCURRENCE_BINDING_PROVEN_COUNT,
    EXPECTED_PROVEN_PARENTAGE_COUNT,
    EXPECTED_RELATION_ENVELOPES_SHA256,
    EXPECTED_T4_CONTAINS_COUNT,
    EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT,
    EXPECTED_T4_LAYER3_MAPPED_PRESENT_COUNT,
    EXPECTED_T4_RECORD_COUNT,
    EXPECTED_VIEW_COUNT,
    EXPECTED_WINNER_SELECTED_COUNT,
    NON_IDENTITY_STATEMENTS,
    OPEN_CLUSTER_RESIDUAL_IDS,
    POSSIBLE_CROSS_RESIDUAL_EDGES,
    PROVEN_CROSS_RESIDUAL_EDGES,
    REJECTED_CLOSE_ORDER_EDGES,
)
from scripts.ops.forensic_structure_schema_v1.alignment_guards import AlignmentGuardProgram
from scripts.ops.forensic_structure_schema_v1.alignment_models import (
    AlignmentIndex,
    CrossResidualEvidenceEdge,
    EndpointBindingCandidateRecord,
    Layer3RelationRecord,
    NonIdentityRecord,
    T4OverlayRecord,
    ViewRecord,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SOURCE_PATH,
    EXTERNAL_RETAINED_DATASET_DIR,
)
from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    DERIVED_T4_TSV_INDEX,
    DOCUMENTARY_PARENT_HINT_PAIRS,
    SECTION_22_SIDECAR_ENDPOINT,
    SIDECAR_DEPENDENCY_SUBJECT,
    VIEW_UNRESOLVED_BOUNDARIES_ID,
)
from scripts.ops.forensic_structure_schema_v1.disposition_layer import (
    build_disposition_layer,
    endpoint_disposition_classes,
    relation_disposition_classes,
    view_parent_disposition_classes,
)
from scripts.ops.forensic_structure_schema_v1.disposition_models import SourceLocus
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guard_inventory import inventory_named_guards
from scripts.ops.forensic_structure_schema_v1.guards import GuardProgram
from scripts.ops.forensic_structure_schema_v1.id_spaces import classify_alias
from scripts.ops.forensic_structure_schema_v1.minting import mint_transformation_local_id
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue
from scripts.ops.forensic_structure_schema_v1.navigation_views import project_navigation_views
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def collect_a_l_input_hashes(repo_root: Path | None = None) -> dict[str, str]:
    root = repo_root or _repo_root()
    catalog_dir = root / A_L_CATALOG_RELPATH
    hashes: dict[str, str] = {}
    for name in (
        "transformation_manifest.json",
        "dataset_catalog.json",
        "residual_register.json",
        "non_inference_audit.json",
        "navigation_views.json",
    ):
        path = catalog_dir / name
        if not path.is_file():
            _fail("RETAINED_INPUT_UNBOUND", f"missing A-L input {path}")
        hashes[f"repo:{A_L_CATALOG_RELPATH}/{name}"] = _sha256_file(path)
    catalog_sha = hashes[f"repo:{A_L_CATALOG_RELPATH}/dataset_catalog.json"]
    if catalog_sha != EXPECTED_DATASET_CATALOG_SHA256:
        _fail(
            "RETAINED_INPUT_UNBOUND",
            f"dataset_catalog sha {catalog_sha} != {EXPECTED_DATASET_CATALOG_SHA256}",
        )
    relation_blob = Path(EXTERNAL_RETAINED_DATASET_DIR) / "blobs" / "relation_envelopes.json"
    if not relation_blob.is_file():
        _fail("RETAINED_INPUT_UNBOUND", f"missing relation_envelopes blob {relation_blob}")
    relation_sha = _sha256_file(relation_blob)
    if relation_sha != EXPECTED_RELATION_ENVELOPES_SHA256:
        _fail(
            "RETAINED_INPUT_UNBOUND",
            f"relation_envelopes sha {relation_sha} != {EXPECTED_RELATION_ENVELOPES_SHA256}",
        )
    hashes["external:blobs/relation_envelopes.json"] = relation_sha
    hashes["expected_a_l_dataset_sha256"] = EXPECTED_A_L_DATASET_SHA256
    return hashes


def collect_disposition_input_hashes(repo_root: Path | None = None) -> dict[str, str]:
    root = repo_root or _repo_root()
    disp_dir = root / DISPOSITION_RELPATH
    hashes: dict[str, str] = {}
    for name in (
        "transformation_manifest.json",
        "disposition_layer.json",
        "relation_dispositions.json",
        "endpoint_dispositions.json",
        "view_parent_dispositions.json",
        "residual_status.json",
        "counts.json",
    ):
        path = disp_dir / name
        if not path.is_file():
            _fail("DISPOSITION_INPUT_UNBOUND", f"missing disposition input {path}")
        hashes[f"repo:{DISPOSITION_RELPATH}/{name}"] = _sha256_file(path)
    layer_sha = hashes[f"repo:{DISPOSITION_RELPATH}/disposition_layer.json"]
    if layer_sha != EXPECTED_DISPOSITION_LAYER_SHA256:
        _fail(
            "DISPOSITION_INPUT_UNBOUND",
            f"disposition_layer sha {layer_sha} != {EXPECTED_DISPOSITION_LAYER_SHA256}",
        )
    return hashes


def _parse_t4_fields(state: PipelineState, overlay: Any) -> list[str] | None:
    start = overlay.payload.get("byte_start")
    end = overlay.payload.get("byte_end")
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    raw = state.source_bytes[start:end].decode("utf-8")
    return raw.split("|")


def _tsv_optional(fields: list[str] | None, index: int) -> OptionalValue:
    if fields is None:
        return OptionalValue.absent()
    if index >= len(fields):
        return OptionalValue.absent()
    return OptionalValue.present(fields[index])


def _t4_record(state: PipelineState, overlay: Any) -> T4OverlayRecord:
    fields = _parse_t4_fields(state, overlay)
    payload = overlay.payload
    start = int(payload["byte_start"])
    end = int(payload["byte_end"])
    occ = str(payload["occurrence_id"])
    line = OptionalValue.from_mapping(payload, "line")
    locus = SourceLocus(
        kind="BYTE_RANGE_EXACT",
        byte_start=start,
        byte_end=end,
        line_start=int(line.value) if line.presence == "present" else None,
        line_end=int(line.value) if line.presence == "present" else None,
        layer1_occurrence_id=occ,
        raw_excerpt=OptionalValue.absent(),
    )
    mapped = OptionalValue.from_mapping(payload, "layer3_mapped_type")
    declared = OptionalValue.from_mapping(payload, "declared_relation_type")
    directionality = _tsv_optional(fields, DERIVED_T4_TSV_INDEX["directionality"])
    residuals = ["SW-R-002"]
    if mapped.presence == "present":
        residuals = ["SW-R-002", "SW-R-004"]
    if declared.presence == "present" and declared.value == "CONTAINS":
        residuals = ["SW-R-002", "DR-002"]
    flags = {
        "t4_family": payload.get("t4_family"),
        "overlay_class": overlay.overlay_class,
        "sidecar_index": overlay.sidecar_index,
        "tsv_declared_value_equal": (
            directionality.presence == "present"
            and declared.presence == "present"
            and directionality.value == declared.value
        ),
        "tsv_declared_identity": False,
        "layer3_identity": False,
        "contains_wrapper_identity": False,
    }
    return T4OverlayRecord(
        derived_record_id=mint_transformation_local_id(
            kind="align-t4",
            source_order=overlay.sidecar_index,
            sidecar_stable_suffix=overlay.overlay_id,
        ),
        overlay_id=overlay.overlay_id,
        source_order=overlay.sidecar_index,
        sidecar_index=overlay.sidecar_index,
        layer1_occurrence_id=occ,
        source_src_id=_tsv_optional(fields, DERIVED_T4_TSV_INDEX["subject_src"]),
        target_ref=_tsv_optional(fields, DERIVED_T4_TSV_INDEX["target_ref"]),
        tsv_directionality=directionality,
        sidecar_declared_relation_type=declared,
        layer3_mapped_type=mapped,
        byte_start=start,
        byte_end=end,
        line=line,
        t4_family=OptionalValue.from_mapping(payload, "t4_family"),
        overlay_kind=overlay.overlay_kind,
        field_count=OptionalValue.from_mapping(payload, "field_count"),
        content_hash_sha256=OptionalValue.from_mapping(payload, "content_hash_sha256"),
        source_identifier_alias=OptionalValue.from_mapping(payload, "source_identifier_alias"),
        sidecar_subject=OptionalValue.from_mapping(payload, "subject"),
        is_dependency=bool(payload.get("is_dependency")),
        t4_flags=flags,
        adjudication_status="BLOCKED_BY_RESIDUAL",
        provenance_type="FACT_FROM_SOURCE",
        epistemic_class="RAW_EVIDENCE",
        residual_ids=residuals,
        source_locus=locus,
        source_sha256=BOUND_SOURCE_SHA256,
        sidecar_sha256=BOUND_SIDECAR_SHA256,
        layer3_semantic_backfill_performed=False,
        occurrence_binding_proven=False,
    )


def _layer3_record(
    state: PipelineState,
    relation: Any,
    *,
    endpoint_ids: list[str],
    disposition_classes: list[str],
) -> Layer3RelationRecord:
    overlay_ref = OptionalValue.absent()
    if relation.sidecar_overlay_id.presence == "present":
        overlay_ref = OptionalValue.present(str(relation.sidecar_overlay_id.value))
    residuals = ["SW-R-002"]
    evidence = "STRUCTURAL_DERIVATION"
    if relation.relation_type == "WRAPPER_CONTAINS":
        residuals = ["SW-R-002", "DR-002"]
        evidence = "ENCODING"
    elif relation.relation_type == "STRUCTURAL_ORDERED_BEFORE":
        residuals = ["SW-R-002", "SW-R-004"]
        evidence = "ENDPOINT_COUPLING"
    elif relation.relation_type == "PREFIX_EPOCH_SUCCEEDS":
        residuals = ["SW-R-002"]
        evidence = "GUARD"
    elif relation.relation_type in {"EXPLICIT_DEPENDENCY", "EXPLICIT_CONFLICT"}:
        residuals = ["SW-R-002", "SW-R-004"]
        evidence = "EXPLICIT_TEXT_RELATION"
    projection = {
        "sidecar_overlay_id": overlay_ref.to_canonical(),
        "source_occurrence_id": relation.source_occurrence_id.to_canonical(),
        "from_binding": relation.from_binding.to_canonical(),
        "to_binding": relation.to_binding.to_canonical(),
        "layer3_not_t4_src_target_pair": relation.relation_type == "STRUCTURAL_ORDERED_BEFORE",
        "t4_contains_identity": False,
    }
    return Layer3RelationRecord(
        derived_record_id=mint_transformation_local_id(
            kind="align-rel",
            source_order=relation.source_order,
            sidecar_stable_suffix=relation.relation_id,
        ),
        relation_id=relation.relation_id,
        relation_type=relation.relation_type,
        from_id=str(relation.from_binding.value),
        to_id=str(relation.to_binding.value),
        source_order=relation.source_order,
        source_projection_references=projection,
        existing_disposition=list(disposition_classes),
        semantic_status="SEMANTIC_STATUS_UNKNOWN",
        endpoint_record_ids=list(endpoint_ids),
        residual_ids=residuals,
        provenance_type=relation.relation_provenance,
        evidence_class=evidence,
        epistemic_class="STRUCTURAL_DERIVATION",
        source_sha256=BOUND_SOURCE_SHA256,
        sidecar_sha256=BOUND_SIDECAR_SHA256,
        winner_selected=bool(relation.winner_selected),
        is_dependency=bool(relation.is_dependency),
        semantic_binding_performed=False,
    )


def _endpoint_record(
    state: PipelineState,
    relation: Any,
    side: str,
    *,
    disposition_classes: list[str],
) -> EndpointBindingCandidateRecord:
    binding = relation.from_binding if side == "from" else relation.to_binding
    raw = str(binding.value)
    sidecar_constructed = raw in {SECTION_22_SIDECAR_ENDPOINT, SIDECAR_DEPENDENCY_SUBJECT}
    loci: list[SourceLocus] = []
    locus_availability = "ABSENT"
    if sidecar_constructed:
        locus_availability = "ABSENT"
    elif relation.sidecar_overlay_id.presence == "present" and side == "from":
        overlay = state.overlay_by_id.get(str(relation.sidecar_overlay_id.value))
        if overlay is not None:
            start = overlay.payload.get("byte_start")
            end = overlay.payload.get("byte_end")
            if isinstance(start, int) and isinstance(end, int):
                occ = overlay.payload.get("occurrence_id")
                line = overlay.payload.get("line")
                loci.append(
                    SourceLocus(
                        kind="BYTE_RANGE_EXACT",
                        byte_start=start,
                        byte_end=end,
                        line_start=int(line) if isinstance(line, int) else None,
                        line_end=int(line) if isinstance(line, int) else None,
                        layer1_occurrence_id=str(occ) if isinstance(occ, str) else None,
                    )
                )
                locus_availability = "PRESENT"
    elif (
        relation.relation_type == "WRAPPER_CONTAINS"
        and side == "to"
        and binding.kind == "LAYER1_OCCURRENCE_REFERENCE"
    ):
        span = state.layer1_by_id.get(raw)
        if span is not None:
            loci.append(
                SourceLocus(
                    kind="BYTE_RANGE_EXACT",
                    byte_start=span.byte_start,
                    byte_end=span.byte_end,
                    line_start=span.line_start,
                    line_end=span.line_end,
                    layer1_occurrence_id=span.occurrence_id,
                )
            )
            locus_availability = "PRESENT"
    mapped_overlay = state.alias_to_overlay_id.get(raw)
    candidates: list[dict[str, Any]] = []
    if mapped_overlay is not None:
        candidates.append(
            {
                "candidate_kind": "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
                "overlay_id": mapped_overlay,
                "occurrence_binding_proven": False,
                "epistemic_class": "NAVIGATION_ONLY",
            }
        )
    alias_space = classify_alias(raw)
    reason = "CANDIDATE_NOT_AUTHORIZED_TO_PROVE_OCCURRENCE"
    if sidecar_constructed:
        reason = "SIDECAR_CONSTRUCTED_STRING_NO_SOURCE_LOCUS"
    return EndpointBindingCandidateRecord(
        derived_record_id=mint_transformation_local_id(
            kind=f"align-endpoint-{side}",
            source_order=relation.source_order,
            sidecar_stable_suffix=f"{relation.relation_id}-{raw}",
        ),
        endpoint_string=raw,
        endpoint_side=side,
        endpoint_class=binding.kind,
        relation_id=relation.relation_id,
        alias_navigation_references={
            "id_space": alias_space or binding.id_space,
            "binding_kind": binding.kind,
            "alias_map_overlay_id": (
                {"presence": "present", "value": mapped_overlay}
                if mapped_overlay is not None
                else {"presence": "absent"}
            ),
            "navigation_only": True,
        },
        possible_structural_candidates=candidates,
        source_locus_availability=locus_availability,
        source_loci=loci,
        candidate_state="UNRESOLVED",
        unresolved_to_occurrence=True,
        occurrence_binding_proven=False,
        provenance_type="NAVIGATION_ONLY",
        evidence_class="ENDPOINT_COUPLING",
        reason=reason,
        residual_ids=["SW-R-004", "DR-003"],
        existing_disposition=list(disposition_classes),
        source_sha256=BOUND_SOURCE_SHA256,
        sidecar_sha256=BOUND_SIDECAR_SHA256,
    )


def _parents_state(status: str) -> str:
    if status == "DOCUMENTARY_UNADJUDICATED":
        return "PRESENT"
    if status == "ABSENT":
        return "ABSENT"
    if status == "NULL":
        return "NULL"
    _fail("SW-R-009", f"unclassified parents_field_status {status}")
    raise AssertionError("unreachable")


def _view_record(state: PipelineState, view: dict[str, Any]) -> ViewRecord:
    view_id = str(view["view_id"])
    status = str(view["parents_field_status"])
    parents_state = _parents_state(status)
    hints = OptionalValue.absent()
    candidates = OptionalValue.absent()
    if parents_state == "PRESENT":
        pair_rows = [
            {
                "child_raw": child,
                "parent_raw": parent,
                "proven_parentage": False,
                "epistemic_class": "HYPOTHESIS",
                "candidate_state": "POSSIBLE",
            }
            for child, parent in DOCUMENTARY_PARENT_HINT_PAIRS
        ]
        hints = OptionalValue.present(pair_rows)
        candidates = OptionalValue.present(pair_rows)
    elif parents_state == "NULL":
        hints = OptionalValue.null()
        candidates = OptionalValue.null()
    dispositions = view_parent_disposition_classes(status)
    residuals = ["SW-R-009", "SW-R-005", "DR-006"]
    if view_id == VIEW_UNRESOLVED_BOUNDARIES_ID:
        residuals = ["SW-R-009", "SW-R-005", "SW-R-015", "DR-003", "DR-006"]
    return ViewRecord(
        derived_record_id=mint_transformation_local_id(
            kind="align-view",
            source_order=int(view["source_order"]),
            sidecar_stable_suffix=view_id,
        ),
        view_id=view_id,
        view_class="NAVIGATION_OR_ANALYSIS_ONLY",
        source_order=int(view["source_order"]),
        parents_field_state=parents_state,
        documentary_parent_hints=hints,
        candidate_parent_relationships=candidates,
        proven_parentage=False,
        residual_ids=residuals,
        existing_disposition=list(dispositions),
        provenance_type="NAVIGATION_ONLY",
        epistemic_class="UNKNOWN" if parents_state == "ABSENT" else "HYPOTHESIS",
        source_sha256=BOUND_SOURCE_SHA256,
        sidecar_sha256=BOUND_SIDECAR_SHA256,
    )


def _edge_from_tuple(
    row: tuple[str, str, str, str, str, str, str],
    *,
    source_order: int,
    provenance_class: str,
    close_order: bool = False,
) -> CrossResidualEvidenceEdge:
    edge_id, source_object, target_object, residual, evidence, state, edge_class = row
    return CrossResidualEvidenceEdge(
        derived_record_id=mint_transformation_local_id(
            kind="align-xres",
            source_order=source_order,
            sidecar_stable_suffix=edge_id,
        ),
        edge_id=edge_id,
        source_object=source_object,
        target_object=target_object,
        edge_class=edge_class,
        evidence_class=evidence,
        provenance_class=provenance_class,
        epistemic_state=state,
        close_order=close_order,
        residual_ids=[residual],
        source_order=source_order,
        source_sha256=BOUND_SOURCE_SHA256,
        sidecar_sha256=BOUND_SIDECAR_SHA256,
        note="close_order=false unless an explicit proof says otherwise",
    )


def _cross_residual_edges() -> list[CrossResidualEvidenceEdge]:
    edges: list[CrossResidualEvidenceEdge] = []
    order = 0
    for row in PROVEN_CROSS_RESIDUAL_EDGES:
        edges.append(
            _edge_from_tuple(
                row,
                source_order=order,
                provenance_class="STRUCTURAL_OR_GUARD_EVIDENCE",
            )
        )
        order += 1
    for row in POSSIBLE_CROSS_RESIDUAL_EDGES:
        edges.append(
            _edge_from_tuple(
                row,
                source_order=order,
                provenance_class="POSSIBLE_ONLY",
            )
        )
        order += 1
    for row in REJECTED_CLOSE_ORDER_EDGES:
        edges.append(
            _edge_from_tuple(
                row,
                source_order=order,
                provenance_class="OWNER_GO_REJECTED_CLOSE_ORDER",
            )
        )
        order += 1
    prereq_index = 0
    for source, targets in ALIGNMENT_CROSS_RESIDUAL_PREREQUISITES.items():
        for target in targets:
            edge_id = f"XRE-PREREQ-{prereq_index:03d}"
            edges.append(
                CrossResidualEvidenceEdge(
                    derived_record_id=mint_transformation_local_id(
                        kind="align-xres",
                        source_order=order,
                        sidecar_stable_suffix=edge_id,
                    ),
                    edge_id=edge_id,
                    source_object=source,
                    target_object=target,
                    edge_class="CROSS_RESIDUAL_PREREQUISITE_REFERENCE",
                    evidence_class="CROSS_RESIDUAL_PREREQUISITE_REFERENCE",
                    provenance_class="PR_6063_CROSS_RESIDUAL_PREREQUISITES",
                    epistemic_state="rejected",
                    close_order=False,
                    residual_ids=[source, target],
                    source_order=order,
                    source_sha256=BOUND_SOURCE_SHA256,
                    sidecar_sha256=BOUND_SIDECAR_SHA256,
                    note="PR #6063 CROSS_RESIDUAL_PREREQUISITES are not close-order",
                )
            )
            order += 1
            prereq_index += 1
    return edges


def _non_identity_records() -> list[NonIdentityRecord]:
    records: list[NonIdentityRecord] = []
    for index, (identity_id, left, right) in enumerate(NON_IDENTITY_STATEMENTS):
        records.append(
            NonIdentityRecord(
                derived_record_id=mint_transformation_local_id(
                    kind="align-nonid",
                    source_order=index,
                    sidecar_stable_suffix=identity_id,
                ),
                identity_id=identity_id,
                left_term=left,
                right_term=right,
                statement=f"{left} != {right}",
                source_order=index,
                epistemic_class="PRIOR_ADJUDICATION_REFERENCE",
                provenance_type="PRIOR_ADJUDICATION_REFERENCE",
                residual_ids=list(OPEN_CLUSTER_RESIDUAL_IDS),
                source_sha256=BOUND_SOURCE_SHA256,
                sidecar_sha256=BOUND_SIDECAR_SHA256,
                collapsed=False,
            )
        )
    return records


def build_alignment_index(
    state: PipelineState,
    *,
    repo_root: Path | None = None,
) -> AlignmentIndex:
    guards = AlignmentGuardProgram()
    guards.assert_current_locator_not_historical(BOUND_SOURCE_PATH)
    guards.assert_prerequisites_table_not_empty()
    if state.witness is None:
        _fail("ALIGNMENT_INDEX", "pipeline witness missing")
    if state.witness.source_sha256 != BOUND_SOURCE_SHA256:
        _fail("SOURCE_SHA_DRIFT", "alignment index refuses drifted source")
    if state.witness.sidecar_sha256 != BOUND_SIDECAR_SHA256:
        _fail("SIDECAR_SHA_DRIFT", "alignment index refuses drifted sidecar")
    if not state.output_eligible:
        _fail("ALIGNMENT_INDEX", "refusing index: transformer output_eligible is false")
    guards.assert_authority_none(state.witness.target_authority)
    guards.assert_current_locator_not_historical(str(state.source_path))
    guards.assert_current_locator_not_historical(str(state.sidecar_path))

    a_l_hashes = collect_a_l_input_hashes(repo_root)
    disposition_hashes = collect_disposition_input_hashes(repo_root)
    disposition = build_disposition_layer(state)
    base_guards = GuardProgram()

    t4_rows = list(state.overlays_by_class["t4_rel_row"])
    if len(t4_rows) != EXPECTED_T4_RECORD_COUNT:
        _fail("ALIGNMENT_INDEX", f"T4 count {len(t4_rows)} != {EXPECTED_T4_RECORD_COUNT}")
    t4_records = [_t4_record(state, overlay) for overlay in t4_rows]
    mapped_present = sum(1 for rec in t4_records if rec.layer3_mapped_type.presence == "present")
    mapped_null = sum(1 for rec in t4_records if rec.layer3_mapped_type.presence == "null")
    mapped_absent = sum(1 for rec in t4_records if rec.layer3_mapped_type.presence == "absent")
    t4_contains = sum(
        1
        for rec in t4_records
        if rec.sidecar_declared_relation_type.presence == "present"
        and rec.sidecar_declared_relation_type.value == "CONTAINS"
    )
    backfill = sum(1 for rec in t4_records if rec.layer3_semantic_backfill_performed)
    if mapped_present != EXPECTED_T4_LAYER3_MAPPED_PRESENT_COUNT:
        _fail("SW-R-002", f"mapped present {mapped_present} drifted")
    if mapped_absent != 0:
        _fail("DR-006", "layer3_mapped_type ABSENT would collapse NULL encoding")
    guards.assert_no_t4_layer3_backfill(mapped_null_count=mapped_null, backfill_count=backfill)
    if t4_contains != EXPECTED_T4_CONTAINS_COUNT:
        _fail("G4", f"T4 CONTAINS count {t4_contains} drifted")
    declared_equals_tsv_global = all(
        rec.t4_flags["tsv_declared_identity"] is True for rec in t4_records
    )
    guards.assert_tsv_declared_not_global_identity(declared_equals_tsv_global)
    for rec in t4_records:
        guards.assert_candidate_not_proven(
            proven=rec.occurrence_binding_proven, detail=rec.overlay_id
        )
        declared_value = (
            rec.sidecar_declared_relation_type.value
            if rec.sidecar_declared_relation_type.presence == "present"
            else None
        )
        mechanical = declared_value in {"ORDERED_BEFORE", "ORDERED_AFTER", "CONTAINS"}
        guards.assert_mechanical_order_not_dependency(
            is_dependency=bool(rec.is_dependency) and mechanical,
            detail=rec.overlay_id,
        )

    disposition_by_relation = {rec.source_object_id: rec for rec in disposition.relation_records}
    endpoint_records: list[EndpointBindingCandidateRecord] = []
    layer3_records: list[Layer3RelationRecord] = []
    for relation in state.relations:
        base_guards.check_relation(relation)
        base_guards.check_cluster_projection(relation, state)
        disp = disposition_by_relation[relation.relation_id]
        classes = list(
            disp.relation_dispositions or relation_disposition_classes(relation.relation_type)
        )
        from_disp = endpoint_disposition_classes(
            relation_type=relation.relation_type,
            binding_kind=relation.from_binding.kind,
            raw_value=str(relation.from_binding.value),
            unresolved_to_occurrence=relation.from_binding.unresolved_to_occurrence,
        )
        to_disp = endpoint_disposition_classes(
            relation_type=relation.relation_type,
            binding_kind=relation.to_binding.kind,
            raw_value=str(relation.to_binding.value),
            unresolved_to_occurrence=relation.to_binding.unresolved_to_occurrence,
        )
        from_rec = _endpoint_record(state, relation, "from", disposition_classes=from_disp)
        to_rec = _endpoint_record(state, relation, "to", disposition_classes=to_disp)
        guards.assert_candidate_not_proven(
            proven=from_rec.occurrence_binding_proven, detail=from_rec.derived_record_id
        )
        guards.assert_candidate_not_proven(
            proven=to_rec.occurrence_binding_proven, detail=to_rec.derived_record_id
        )
        if "OCCURRENCE_BINDING_PROVEN" in from_disp or "OCCURRENCE_BINDING_PROVEN" in to_disp:
            forbid_detail = f"{relation.relation_id} disposition proven"
            guards.assert_candidate_not_proven(proven=True, detail=forbid_detail)
        if relation.relation_type == "PREFIX_EPOCH_SUCCEEDS":
            guards.assert_epoch_not_currentness(promoted=False, detail=relation.relation_id)
            guards.assert_epoch_not_supersession(promoted=False, detail=relation.relation_id)
            guards.assert_later_not_winner(
                winner_selected=relation.winner_selected, detail=relation.relation_id
            )
        if relation.relation_type == "STRUCTURAL_ORDERED_BEFORE":
            guards.assert_mechanical_order_not_dependency(
                is_dependency=relation.is_dependency, detail=relation.relation_id
            )
        endpoint_ids = [from_rec.derived_record_id, to_rec.derived_record_id]
        layer3_records.append(
            _layer3_record(
                state,
                relation,
                endpoint_ids=endpoint_ids,
                disposition_classes=classes,
            )
        )
        endpoint_records.extend((from_rec, to_rec))

    if len(layer3_records) != EXPECTED_LAYER3_RELATION_COUNT:
        _fail("ALIGNMENT_INDEX", "layer3 count drifted")
    if len(endpoint_records) != EXPECTED_ENDPOINT_RECORD_COUNT:
        _fail("ALIGNMENT_INDEX", "endpoint count drifted")

    views = project_navigation_views(state.sidecar["layer4_derived_views"])
    view_records = [_view_record(state, view) for view in views]
    if len(view_records) != EXPECTED_VIEW_COUNT:
        _fail("ALIGNMENT_INDEX", "view count drifted")
    for rec in view_records:
        guards.assert_parentage_not_proven(proven=rec.proven_parentage, detail=rec.view_id)
        guards.assert_absent_not_no_parent(rec.to_canonical())
        if rec.parents_field_state == "ABSENT" and rec.epistemic_class == "FALSE":
            guards.assert_unknown_not_false(False, "UNKNOWN collapsed")

    edges = _cross_residual_edges()
    guards.assert_cross_prerequisites_not_close_order([e.to_canonical() for e in edges])
    for edge in edges:
        guards.assert_close_order_false(close_order=edge.close_order, detail=edge.edge_id)

    non_identities = _non_identity_records()
    if len(non_identities) != len(NON_IDENTITY_STATEMENTS):
        _fail("ALIGNMENT_INDEX", "non-identity count drifted")
    for rec in non_identities:
        guards.assert_no_duplicate_collapse(collapsed=rec.collapsed, detail=rec.identity_id)

    residual_status = {residual_id: "OPEN" for residual_id in ALIGNMENT_MUST_REMAIN_OPEN}
    residual_status.update({residual_id: "OPEN" for residual_id in OPEN_CLUSTER_RESIDUAL_IDS})
    for rec in state.residuals:
        if rec.residual_id in residual_status and rec.status != "OPEN":
            guards.assert_open_residuals({rec.residual_id: rec.status})
    guards.assert_open_residuals(residual_status)

    proven_occ = sum(1 for rec in endpoint_records if rec.occurrence_binding_proven)
    proven_parent = sum(1 for rec in view_records if rec.proven_parentage)
    winner = sum(1 for rec in layer3_records if rec.winner_selected)
    if proven_occ != EXPECTED_OCCURRENCE_BINDING_PROVEN_COUNT:
        guards.assert_candidate_not_proven(proven=True, detail="count")
    if proven_parent != EXPECTED_PROVEN_PARENTAGE_COUNT:
        guards.assert_parentage_not_proven(proven=True, detail="count")
    if winner != EXPECTED_WINNER_SELECTED_COUNT:
        guards.assert_later_not_winner(winner_selected=True, detail="count")

    hash_groups: dict[str, int] = {}
    for rec in t4_records:
        if rec.content_hash_sha256.presence == "present":
            key = str(rec.content_hash_sha256.value)
            hash_groups[key] = hash_groups.get(key, 0) + 1
    duplicate_hash_groups = sum(1 for count in hash_groups.values() if count > 1)

    inventory = inventory_named_guards()
    non_inference = {
        "SEMANTIC_BINDING_PERFORMED": False,
        "OCCURRENCE_BINDING_PROVEN_COUNT": proven_occ,
        "PROVEN_PARENTAGE_COUNT": proven_parent,
        "CURRENTNESS_ADJUDICATION_PERFORMED": False,
        "SUPERSESSION_ADJUDICATION_PERFORMED": False,
        "WINNER_SELECTED_COUNT": winner,
        "T4_TO_LAYER3_BACKFILL_COUNT": backfill,
        "CROSS_RESIDUAL_CLOSE_ORDER_COUNT": sum(1 for e in edges if e.close_order),
        "UNKNOWN_COLLAPSED_TO_FALSE": False,
        "ABSENT_COLLAPSED_TO_NO_PARENT": False,
        "OPEN_COLLAPSED_TO_CLOSED": False,
        "OPEN_COLLAPSED_TO_UNPROVEN": False,
        "TSV_DECLARED_GLOBAL_IDENTITY": False,
        "MISSING_BINDING_AS_NEGATIVE_FACT": False,
        "AUTHORITY_PROMOTION": False,
        "OUTPUT_CANONICAL": False,
        "EXISTING_GUARD_INVENTORY_UNWIRED_AFTER": sum(
            1 for row in inventory.values() if not row["CALLED"]
        ),
    }
    non_identity_audit = {
        "NON_IDENTITY_RECORD_COUNT": len(non_identities),
        "COLLAPSED_COUNT": sum(1 for rec in non_identities if rec.collapsed),
        "STATEMENTS": [rec.statement for rec in non_identities],
        "PRESERVED": True,
    }
    evidence_edge_report = {
        "CROSS_RESIDUAL_EDGE_COUNT": len(edges),
        "PROVEN_COUNT": sum(1 for e in edges if e.epistemic_state == "proven"),
        "POSSIBLE_COUNT": sum(1 for e in edges if e.epistemic_state == "possible"),
        "REJECTED_COUNT": sum(1 for e in edges if e.epistemic_state == "rejected"),
        "CLOSE_ORDER_TRUE_COUNT": sum(1 for e in edges if e.close_order),
        "MISSING_EVIDENCE_CLASS_COUNT": sum(1 for e in edges if not e.evidence_class),
    }
    counts = {
        "T4_RECORD_COUNT": len(t4_records),
        "LAYER3_RELATION_COUNT": len(layer3_records),
        "ENDPOINT_RECORD_COUNT": len(endpoint_records),
        "VIEW_COUNT": len(view_records),
        "CROSS_RESIDUAL_EDGE_COUNT": len(edges),
        "NON_IDENTITY_RECORD_COUNT": len(non_identities),
        "OCCURRENCE_BINDING_CANDIDATE_COUNT": len(endpoint_records),
        "OCCURRENCE_BINDING_PROVEN_COUNT": proven_occ,
        "PROVEN_PARENTAGE_COUNT": proven_parent,
        "WINNER_SELECTED_COUNT": winner,
        "T4_CONTAINS_COUNT": t4_contains,
        "T4_LAYER3_MAPPED_PRESENT_COUNT": mapped_present,
        "T4_LAYER3_MAPPED_NULL_COUNT": mapped_null,
        "T4_LAYER3_MAPPED_ABSENT_COUNT": mapped_absent,
        "T4_TO_LAYER3_BACKFILL_COUNT": backfill,
        "T4_DUPLICATE_CONTENT_HASH_GROUPS": duplicate_hash_groups,
        "SEMANTIC_BINDING_PERFORMED": False,
        "CURRENTNESS_ADJUDICATION_PERFORMED": False,
        "SUPERSESSION_ADJUDICATION_PERFORMED": False,
    }
    return AlignmentIndex(
        t4_records=t4_records,
        layer3_records=layer3_records,
        endpoint_records=endpoint_records,
        view_records=view_records,
        cross_residual_edges=edges,
        non_identity_records=non_identities,
        counts=counts,
        residual_status=residual_status,
        non_inference_audit=non_inference,
        non_identity_audit=non_identity_audit,
        evidence_edge_report=evidence_edge_report,
        generated_from_source_sha256=BOUND_SOURCE_SHA256,
        generated_from_sidecar_sha256=BOUND_SIDECAR_SHA256,
        a_l_input_hashes=a_l_hashes,
        disposition_input_hashes=disposition_hashes,
        layer_id=ALIGNMENT_LAYER_ID,
        generator_id=ALIGNMENT_GENERATOR_ID,
        output_role=ALIGNMENT_OUTPUT_ROLE,
        authority=ALIGNMENT_AUTHORITY,
        output_canonical=False,
        semantic_binding_performed=False,
        residual_close_performed=False,
        currentness_adjudication_performed=False,
        supersession_adjudication_performed=False,
        occurrence_binding_proven_count=proven_occ,
        proven_parentage_count=proven_parent,
        winner_selected_count=winner,
        transformation_version=ALIGNMENT_TRANSFORMATION_VERSION,
    )

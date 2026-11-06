"""Stage F — Semantic Envelope Projection. Incomplete positive semantics are legal."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    DEFAULT_EPISTEMIC_CLASS,
    DUAL_CLASS_OCCURRENCE_ID,
    EXPECTED_SOURCE_SHA256,
    OVERLAY_CLASS_ORDER,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.joins import byte_range_containing_span
from scripts.ops.forensic_structure_schema_v1.minting import mint_transformation_local_id
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue, SemanticEnvelope
from scripts.ops.forensic_structure_schema_v1.state import PipelineState

_CLASS_SOURCE_ORDER_BASE = {
    "append_epoch": 0,
    "fence_block": 100_000,
    "forensic_record": 200_000,
    "h1_span": 300_000,
    "kv_packet": 400_000,
    "t3_src_span": 500_000,
    "t4_rel_row": 600_000,
    "t5_cls_row": 700_000,
    "t5_multilabel": 800_000,
    "token_occurrence": 900_000,
    "wrapper_mention": 1_000_000,
    "wrapper_pair": 1_100_000,
    "layer2": 2_000_000,
}


def _int_optional(record: dict[str, Any], key: str) -> OptionalValue:
    return OptionalValue.from_mapping(record, key)


def _byte_bounds(payload: dict[str, Any], state: PipelineState) -> tuple[int, int]:
    if "byte_start" in payload and "byte_end" in payload:
        start = int(payload["byte_start"])
        end = int(payload["byte_end"])
        if start < 0 or end > len(state.source_bytes) or end < start:
            raise TransformationContractViolation(
                "C1",
                f"byte range [{start}, {end}) outside source blob",
            )
        return start, end
    raise TransformationContractViolation(
        "C1",
        "envelope requires byte bind or documentary relation; byte range absent",
    )


def _layer1_for_overlay(
    rec_class: str, payload: dict[str, Any], state: PipelineState
) -> OptionalValue:
    if rec_class == "token_occurrence":
        span = byte_range_containing_span(
            state.layer1_ordered,
            int(payload["byte_start"]),
            int(payload["byte_end"]),
            line=int(payload["line"]) if "line" in payload else None,
        )
        token_occ = str(payload["occurrence_id"])
        if token_occ == span.occurrence_id:
            raise TransformationContractViolation(
                "SW-R-008",
                "token occurrence_id copied into layer1_occurrence_id",
            )
        return OptionalValue.present(span.occurrence_id)
    for field_name in (
        "heading_occurrence_id",
        "open_occurrence_id",
        "begin_occurrence_id",
        "occurrence_id",
    ):
        if field_name in payload and payload[field_name] is not None:
            if rec_class == "token_occurrence":
                continue
            occ = str(payload[field_name])
            if occ not in state.layer1_by_id:
                raise TransformationContractViolation(
                    "LAYER1_OCCURRENCE_REFERENCE",
                    f"unknown layer1 id {occ}",
                )
            return OptionalValue.present(occ)
    if rec_class == "kv_packet":
        return OptionalValue.null()
    if rec_class in {"t5_multilabel", "append_epoch"}:
        return OptionalValue.null()
    if "byte_start" in payload and "byte_end" in payload:
        start = int(payload["byte_start"])
        end = int(payload["byte_end"])
        if end - start <= 0:
            return OptionalValue.null()
        try:
            span = byte_range_containing_span(state.layer1_ordered, start, min(end, start + 1))
            return OptionalValue.present(span.occurrence_id)
        except TransformationContractViolation:
            return OptionalValue.null()
    return OptionalValue.null()


def _residuals_for_class(rec_class: str, payload: dict[str, Any]) -> list[str]:
    residuals: list[str] = ["SW-R-001", "SW-R-012"]
    if rec_class == "t4_rel_row":
        residuals.append("SW-R-002")
    if rec_class == "t5_cls_row" and payload.get("classified_source_line") is None:
        residuals.append("SW-R-003")
    if rec_class == "h1_span":
        residuals.extend(
            ["SW-R-005", "SW-R-011"]
            if payload.get("heading_occurrence_id") == DUAL_CLASS_OCCURRENCE_ID
            else ["SW-R-005"]
        )
    if rec_class == "fence_block" and payload.get("inner_shorter_fence_like") is True:
        residuals.append("SW-R-006")
    if rec_class == "t5_multilabel":
        residuals.extend(["SW-R-007", "SW-R-013"])
    if rec_class == "token_occurrence":
        residuals.extend(["SW-R-008", "DR-001"])
    if rec_class == "append_epoch":
        residuals.append("SW-R-010")
    if rec_class == "t3_src_span":
        residuals.append("SW-R-015")
    if rec_class == "forensic_record" and payload.get("binds_blob_sha256") is None:
        residuals.append("SW-R-014")
    if rec_class == "kv_packet":
        residuals.append("DR-008")
    residuals.append("DR-006")
    residuals.append("DR-007")
    return sorted(set(residuals))


def _provenance_for_overlay(rec_class: str) -> str:
    if rec_class == "token_occurrence":
        return "FACT_FROM_SOURCE"
    if rec_class in {
        "t3_src_span",
        "t4_rel_row",
        "t5_cls_row",
        "forensic_record",
    }:
        return "PRIOR_ADJUDICATION_REFERENCE"
    return "STRUCTURAL_DERIVATION"


def run_stage_f(state: PipelineState) -> None:
    if state.guards is None:
        raise TransformationContractViolation("STAGE_F", "GuardProgram missing")
    envelopes: list[SemanticEnvelope] = []
    by_overlay: dict[str, list[SemanticEnvelope]] = {}
    by_tlid: dict[str, SemanticEnvelope] = {}

    class_iter = ("append_epoch",) + OVERLAY_CLASS_ORDER
    for rec_class in class_iter:
        for rec in state.overlays_by_class[rec_class]:
            payload = rec.payload
            if rec_class == "t5_multilabel":
                cls_aliases = payload.get("cls_aliases") or []
                first_cls = state.alias_to_overlay_id[str(cls_aliases[0])]
                first_payload = state.overlay_by_id[first_cls].payload
                start, end = _byte_bounds(first_payload, state)
            else:
                start, end = _byte_bounds(payload, state)
            source_order = _CLASS_SOURCE_ORDER_BASE[rec_class] + rec.sidecar_index
            tlid = mint_transformation_local_id(
                kind=rec_class,
                source_order=source_order,
                sidecar_stable_suffix=rec.overlay_id,
            )
            currentness = "CURRENTNESS_UNKNOWN"
            temporal = OptionalValue.from_mapping(payload, "temporal_status")
            if temporal.presence == "present" and temporal.value == "currentness_unknown":
                currentness = "CURRENTNESS_UNKNOWN"
            envelope = SemanticEnvelope(
                transformation_local_id=tlid,
                source_byte_start=start,
                source_byte_end=end,
                source_sha256=EXPECTED_SOURCE_SHA256,
                sidecar_overlay_id=OptionalValue.present(rec.overlay_id),
                layer1_occurrence_id=_layer1_for_overlay(rec_class, payload, state),
                token_occurrence_id=(
                    OptionalValue.present(str(payload["occurrence_id"]))
                    if rec_class == "token_occurrence"
                    else OptionalValue.null()
                ),
                provenance_type=_provenance_for_overlay(rec_class),
                unresolved_status=OptionalValue.from_mapping(payload, "unresolved"),
                source_order=source_order,
                content_class=str(
                    payload.get("content_class_mapped")
                    or payload.get("content_class")
                    or DEFAULT_EPISTEMIC_CLASS
                ),
                t5_label_verbatim=OptionalValue.from_mapping(payload, "t5_label_verbatim"),
                hash_kind=OptionalValue.from_mapping(payload, "hash_kind"),
                classified_source_line=OptionalValue.from_mapping(
                    payload, "classified_source_line"
                ),
                binds_blob_sha256=OptionalValue.from_mapping(payload, "binds_blob_sha256"),
                binds_blob_sha256_matches_current=OptionalValue.from_mapping(
                    payload, "binds_blob_sha256_matches_current"
                ),
                currentness_upgrade=OptionalValue.from_mapping(payload, "currentness_upgrade"),
                temporal_status=temporal,
                overlay_kind=rec.overlay_kind,
                overlay_class=rec_class,
                token_class=OptionalValue.from_mapping(payload, "token_class"),
                token_verbatim=OptionalValue.from_mapping(payload, "token_verbatim"),
                normalized=OptionalValue.from_mapping(payload, "normalized"),
                locator_role=OptionalValue.from_mapping(payload, "locator_role"),
                collapsed=OptionalValue.from_mapping(payload, "collapsed"),
                instance_vs_mention=OptionalValue.from_mapping(payload, "instance_vs_mention"),
                is_dependency=OptionalValue.from_mapping(payload, "is_dependency"),
                residuals=_residuals_for_class(rec_class, payload),
                currentness_status=currentness,
            )
            if rec_class == "token_occurrence":
                if envelope.hash_kind.presence == "present":
                    if envelope.hash_kind.value != "UNKNOWN":
                        raise TransformationContractViolation(
                            "D7",
                            f"{rec.overlay_id} hash_kind={envelope.hash_kind.value}",
                        )
                if envelope.currentness_upgrade.presence == "present":
                    if envelope.currentness_upgrade.value is not False:
                        raise TransformationContractViolation(
                            "D8",
                            f"{rec.overlay_id} currentness_upgrade is not false",
                        )
                if envelope.locator_role.presence == "present":
                    if envelope.locator_role.value != "HISTORICAL_STRING":
                        raise TransformationContractViolation(
                            "C7",
                            f"{rec.overlay_id} locator_role mutated",
                        )
            if rec_class == "h1_span":
                envelope.semantic_container = "NOT_ADJUDICATED"
                envelope.content_class = "UNCLASSIFIED"
            if rec_class == "t5_cls_row" and payload.get("authority_status") not in {
                None,
                "NONE",
            }:
                raise TransformationContractViolation(
                    "C9",
                    f"{rec.overlay_id} authority_status != NONE",
                )
            state.guards.check_envelope_defaults(envelope)
            envelopes.append(envelope)
            by_overlay.setdefault(rec.overlay_id, []).append(envelope)
            by_tlid[tlid] = envelope

    layer2_by_occ: dict[str, list[SemanticEnvelope]] = {}
    layer2_records = state.sidecar["layer2_classification"]["records"]
    for index, raw in enumerate(layer2_records):
        occ = str(raw["occurrence_id"])
        span = state.layer1_by_id[occ]
        overlay_ref = OptionalValue.from_mapping(raw, "overlay_ref")
        suffix = str(overlay_ref.value) if overlay_ref.presence == "present" else occ
        tlid = mint_transformation_local_id(
            kind="layer2",
            source_order=_CLASS_SOURCE_ORDER_BASE["layer2"] + index,
            sidecar_stable_suffix=suffix,
            layer2_record_index=index if occ == DUAL_CLASS_OCCURRENCE_ID else None,
        )
        temporal = OptionalValue.from_mapping(raw, "temporal_status")
        currentness = "CURRENTNESS_UNKNOWN"
        if temporal.presence == "present" and temporal.value == "historical":
            currentness = "historical"
        envelope = SemanticEnvelope(
            transformation_local_id=tlid,
            source_byte_start=span.byte_start,
            source_byte_end=span.byte_end,
            source_sha256=EXPECTED_SOURCE_SHA256,
            sidecar_overlay_id=overlay_ref,
            layer1_occurrence_id=OptionalValue.present(occ),
            token_occurrence_id=OptionalValue.null(),
            provenance_type=(
                "PRIOR_ADJUDICATION_REFERENCE"
                if raw.get("epistemic_basis") == "PRIOR_ADJUDICATION_REFERENCE"
                else (
                    "EXPLICIT_TEXT_RELATION"
                    if raw.get("epistemic_basis") == "EXPLICIT_TEXT"
                    else "STRUCTURAL_DERIVATION"
                    if raw.get("epistemic_basis") == "STRUCTURAL_INFERENCE"
                    else "UNKNOWN"
                )
            ),
            unresolved_status=OptionalValue.from_mapping(raw, "unresolved"),
            source_order=_CLASS_SOURCE_ORDER_BASE["layer2"] + index,
            content_class=str(raw.get("content_class") or DEFAULT_EPISTEMIC_CLASS),
            t5_label_verbatim=OptionalValue.from_mapping(raw, "t5_label_verbatim"),
            classified_source_line=_int_optional(raw, "classified_source_line"),
            binds_blob_sha256=OptionalValue.from_mapping(raw, "binds_blob_sha256"),
            temporal_status=temporal,
            overlay_class="layer2",
            residuals=["SW-R-011", "SW-R-012", "DR-006", "DR-007"]
            if occ == DUAL_CLASS_OCCURRENCE_ID
            else ["SW-R-012", "DR-006", "DR-007"],
            currentness_status=currentness,
        )
        if raw.get("authority_status") != "NONE":
            raise TransformationContractViolation(
                "C9",
                f"layer2[{index}] authority_status != NONE",
            )
        state.guards.check_envelope_defaults(envelope)
        envelopes.append(envelope)
        layer2_by_occ.setdefault(occ, []).append(envelope)
        by_tlid[tlid] = envelope
        if overlay_ref.presence == "present":
            by_overlay.setdefault(str(overlay_ref.value), []).append(envelope)

    dual = layer2_by_occ.get(DUAL_CLASS_OCCURRENCE_ID, [])
    if len(dual) != 2:
        raise TransformationContractViolation(
            "SW-R-011",
            f"dual-class envelopes {len(dual)} != 2",
        )
    if dual[0].transformation_local_id == dual[1].transformation_local_id:
        raise TransformationContractViolation(
            "SW-R-011",
            "dual-class envelopes collapsed to one transformation_local_id",
        )

    state.envelopes = envelopes
    state.envelope_by_overlay_id = by_overlay
    state.envelope_by_tlid = by_tlid
    state.layer2_envelopes_by_occurrence = layer2_by_occ
    state.stages_completed.append("F_SEMANTIC_ENVELOPE_PROJECTION")

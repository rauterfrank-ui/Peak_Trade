"""Stage D — Provenance Registry. Missing basis is UNKNOWN, never false/STRUCTURAL."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import DUAL_CLASS_OCCURRENCE_ID
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue, ProvenanceTag
from scripts.ops.forensic_structure_schema_v1.state import PipelineState

_BASIS_TO_PROVENANCE = {
    "FACT_FROM_SOURCE": "FACT_FROM_SOURCE",
    "STRUCTURAL_DERIVATION": "STRUCTURAL_DERIVATION",
    "STRUCTURAL_INFERENCE": "STRUCTURAL_DERIVATION",
    "PRIOR_ADJUDICATION_REFERENCE": "PRIOR_ADJUDICATION_REFERENCE",
    "EXPLICIT_TEXT": "EXPLICIT_TEXT_RELATION",
    "EXPLICIT_TEXT_RELATION": "EXPLICIT_TEXT_RELATION",
}


def _provenance_from_basis(basis: Any) -> str:
    if basis is None:
        return "UNKNOWN"
    mapped = _BASIS_TO_PROVENANCE.get(str(basis))
    if mapped is None:
        return "UNKNOWN"
    return mapped


def run_stage_d(state: PipelineState) -> None:
    tags: list[ProvenanceTag] = []
    layer2 = state.sidecar["layer2_classification"]["records"]
    dual_count = 0
    for index, raw in enumerate(layer2):
        occ = str(raw["occurrence_id"])
        if occ not in state.layer1_by_id:
            raise TransformationContractViolation(
                "LAYER1_OCCURRENCE_REFERENCE",
                f"layer2[{index}] occurrence_id {occ} not in LAYER1",
            )
        overlay_ref = raw.get("overlay_ref")
        if overlay_ref is not None and str(overlay_ref) not in state.overlay_by_id:
            raise TransformationContractViolation(
                "OVERLAY_REFERENCE",
                f"layer2[{index}] overlay_ref {overlay_ref} unknown",
            )
        if occ == DUAL_CLASS_OCCURRENCE_ID:
            dual_count += 1
        basis = OptionalValue.from_mapping(raw, "epistemic_basis")
        tags.append(
            ProvenanceTag(
                subject_kind="layer2_record",
                subject_id=f"layer2-{index}-{occ}",
                provenance_type=_provenance_from_basis(raw.get("epistemic_basis")),
                epistemic_basis=basis,
                sidecar_index=index,
            )
        )
    if dual_count != 2:
        raise TransformationContractViolation(
            "SW-R-011",
            f"dual-class occurrence must have 2 layer2 records, found {dual_count}",
        )

    overlay_with_layer2 = {
        str(raw["overlay_ref"]) for raw in layer2 if raw.get("overlay_ref") is not None
    }
    for overlay_id, rec in state.overlay_by_id.items():
        if overlay_id in overlay_with_layer2:
            continue
        payload = rec.payload
        basis_val = payload.get("epistemic_basis")
        if rec.overlay_class == "token_occurrence":
            ptype = "FACT_FROM_SOURCE"
        elif rec.overlay_class in {
            "fence_block",
            "h1_span",
            "kv_packet",
            "wrapper_mention",
            "wrapper_pair",
            "append_epoch",
            "t5_multilabel",
        }:
            ptype = "STRUCTURAL_DERIVATION"
        elif rec.overlay_class in {
            "t3_src_span",
            "t4_rel_row",
            "t5_cls_row",
            "forensic_record",
        }:
            ptype = "PRIOR_ADJUDICATION_REFERENCE"
        else:
            ptype = _provenance_from_basis(basis_val)
        tags.append(
            ProvenanceTag(
                subject_kind="overlay",
                subject_id=overlay_id,
                provenance_type=ptype,
                epistemic_basis=OptionalValue.from_mapping(payload, "epistemic_basis"),
                sidecar_index=rec.sidecar_index,
            )
        )

    state.provenance = tags
    state.stages_completed.append("D_PROVENANCE_REGISTRY")

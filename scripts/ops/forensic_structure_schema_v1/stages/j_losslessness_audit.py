"""Stage J — Losslessness Audit. Dedup must not 'improve' cardinalities."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import EXPECTED_LOSSLESSNESS
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import LosslessnessAudit
from scripts.ops.forensic_structure_schema_v1.stages.a_input_verification import sha256_hex
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def run_stage_j(state: PipelineState) -> None:
    source_after = sha256_hex(state.source_path.read_bytes())
    sidecar_after = sha256_hex(state.sidecar_path.read_bytes())
    source_mutated = source_after != state.source_sha256_before
    sidecar_mutated = sidecar_after != state.sidecar_sha256_before
    if source_mutated:
        raise TransformationContractViolation("SOURCE_MUTATION", "source bytes changed")
    if sidecar_mutated:
        raise TransformationContractViolation("SIDECAR_MUTATION", "sidecar bytes changed")

    layer1 = state.layer1_ordered
    gaps = 0
    overlaps = 0
    for index in range(len(layer1) - 1):
        left_end = layer1[index].byte_end
        right_start = layer1[index + 1].byte_start
        if left_end < right_start:
            gaps += 1
        elif left_end > right_start:
            overlaps += 1
    heading_outside = 0
    for rec in state.overlays_by_class["t3_src_span"]:
        heading = int(rec.payload["heading_line"])
        start = int(rec.payload["source_start_line"])
        end = int(rec.payload["source_end_line"])
        if not (start <= heading <= end):
            heading_outside += 1

    counts = {
        "LAYER1_COUNT": len(layer1),
        "LAYER1_GAPS": gaps,
        "LAYER1_OVERLAPS": overlaps,
        "LAYER1_BYTE_UNION_START": layer1[0].byte_start if layer1 else None,
        "LAYER1_BYTE_UNION_END": layer1[-1].byte_end if layer1 else None,
        "FENCE_BLOCK_COUNT": len(state.overlays_by_class["fence_block"]),
        "FENCE_UNIQUE_BODY_HASHES": len(
            {r.payload["body_sha256"] for r in state.overlays_by_class["fence_block"]}
        ),
        "FENCE_DUPLICATE_GROUPS": sum(
            1 for ids in state.body_sha_to_overlay_ids.values() if len(ids) > 1
        ),
        "T5_MULTILABEL_COUNT": len(state.overlays_by_class["t5_multilabel"]),
        "T5_MULTILABEL_COLLAPSED_TRUE_COUNT": sum(
            1
            for r in state.overlays_by_class["t5_multilabel"]
            if r.payload.get("collapsed") is True
        ),
        "T5_CLASSIFIED_SOURCE_LINE_NULL_COUNT": sum(
            1
            for r in state.overlays_by_class["t5_cls_row"]
            if r.payload.get("classified_source_line") is None
        ),
        "TOKEN_LAYER1_OCCURRENCE_ID_INTERSECTION_COUNT": len(
            state.token_occurrence_ids.intersection(state.layer1_by_id)
        ),
        "H1_SPAN_COUNT": len(state.overlays_by_class["h1_span"]),
        "H1_CONTINUATION_COUNT": sum(
            1
            for r in state.overlays_by_class["h1_span"]
            if r.payload.get("is_continuation_title") is True
        ),
        "T3_SRC_SPAN_COUNT": len(state.overlays_by_class["t3_src_span"]),
        "T3_HEADING_OUTSIDE_DECLARED_REGION_COUNT": heading_outside,
        "WRAPPER_MENTION_COUNT": len(state.overlays_by_class["wrapper_mention"]),
        "WRAPPER_PAIR_COUNT": len(state.overlays_by_class["wrapper_pair"]),
        "LAYER2_RECORD_COUNT": len(state.sidecar["layer2_classification"]["records"]),
        "LAYER2_UNIQUE_OCCURRENCE_IDS": len(
            {r["occurrence_id"] for r in state.sidecar["layer2_classification"]["records"]}
        ),
        "ENVELOPE_COUNT": len(state.envelopes),
        "RELATION_COUNT": len(state.relations),
        "RESIDUAL_COUNT": len(state.residuals),
        "HISTORICAL_LOCATOR_COUNT": sum(
            1
            for r in state.overlays_by_class["token_occurrence"]
            if r.payload.get("token_class") == "HISTORICAL_LOCATOR_STRING"
        ),
    }
    expected = EXPECTED_LOSSLESSNESS
    for key in (
        "LAYER1_COUNT",
        "LAYER1_GAPS",
        "LAYER1_OVERLAPS",
        "LAYER1_BYTE_UNION_START",
        "LAYER1_BYTE_UNION_END",
        "FENCE_BLOCK_COUNT",
        "FENCE_UNIQUE_BODY_HASHES",
        "FENCE_DUPLICATE_GROUPS",
        "T5_MULTILABEL_COUNT",
        "T5_MULTILABEL_COLLAPSED_TRUE_COUNT",
        "T5_CLASSIFIED_SOURCE_LINE_NULL_COUNT",
        "TOKEN_LAYER1_OCCURRENCE_ID_INTERSECTION_COUNT",
        "H1_SPAN_COUNT",
        "H1_CONTINUATION_COUNT",
        "T3_SRC_SPAN_COUNT",
        "T3_HEADING_OUTSIDE_DECLARED_REGION_COUNT",
        "WRAPPER_MENTION_COUNT",
        "WRAPPER_PAIR_COUNT",
        "LAYER2_RECORD_COUNT",
        "LAYER2_UNIQUE_OCCURRENCE_IDS",
    ):
        if counts[key] != expected[key]:
            raise TransformationContractViolation(
                "STAGE_J",
                f"losslessness {key} {counts[key]} != {expected[key]}",
            )
    if counts["HISTORICAL_LOCATOR_COUNT"] != 50:
        raise TransformationContractViolation(
            "C7",
            f"historical locator count {counts['HISTORICAL_LOCATOR_COUNT']} != 50",
        )
    if counts["RELATION_COUNT"] != expected["RELATION_COUNT"]:
        raise TransformationContractViolation(
            "STAGE_J",
            f"relation count {counts['RELATION_COUNT']} != {expected['RELATION_COUNT']}",
        )

    fence_ids = {r.overlay_id for r in state.overlays_by_class["fence_block"]}
    projected_fence = {
        e.sidecar_overlay_id.value
        for e in state.envelopes
        if e.overlay_class == "fence_block" and e.sidecar_overlay_id.presence == "present"
    }
    if fence_ids != projected_fence:
        raise TransformationContractViolation(
            "C3",
            "fence overlay ids were dropped or synthesized in envelopes",
        )
    if any(e.primary_label != "NONE" for e in state.envelopes):
        raise TransformationContractViolation("C4", "primary_label invented")

    state.source_sha256_after = source_after
    state.sidecar_sha256_after = sidecar_after
    state.losslessness_audit = LosslessnessAudit(
        passed=True,
        counts=counts,
        source_mutated=False,
        sidecar_mutated=False,
        source_sha256_before=state.source_sha256_before,
        source_sha256_after=source_after,
        sidecar_sha256_before=state.sidecar_sha256_before,
        sidecar_sha256_after=sidecar_after,
    )
    state.stages_completed.append("J_LOSSLESSNESS_AUDIT")

"""Stage I — Invariant Validation. Sidecar flags are re-checked, not re-derived as new facts."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import (
    DUAL_CLASS_OCCURRENCE_ID,
    EXPECTED_AUTHORITY,
    EXPECTED_LOSSLESSNESS,
    EXPECTED_SOURCE_BYTES,
    EXPECTED_SOURCE_SHA256,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import InvariantReport
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def run_stage_i(state: PipelineState) -> None:
    inv = dict(state.sidecar["invariants"])
    required_false = {
        "boundary_adjudication_performed": False,
        "canonicalization_performed": False,
        "pointer_adjudication_performed": False,
        "repo_z2cf_imported_as_target_resolution": False,
        "source_mutated": False,
    }
    required_true = {
        "duplicates_preserved": True,
        "h1_src_epoch_not_adjudicated_as_hierarchy": True,
        "multilabel_preserved": True,
        "pointer_conflict_preserved_unresolved": True,
        "structural_ordered_before_is_not_dependency": True,
        "unresolved_boundaries_preserved": True,
    }
    results: dict[str, bool] = {}
    for key, expected in required_false.items():
        ok = inv.get(key) is expected
        results[key] = ok
        if not ok:
            raise TransformationContractViolation(
                "STAGE_I",
                f"invariant {key}={inv.get(key)!r} expected {expected!r}",
            )
    for key, expected in required_true.items():
        ok = inv.get(key) is expected
        results[key] = ok
        if not ok:
            raise TransformationContractViolation(
                "STAGE_I",
                f"invariant {key}={inv.get(key)!r} expected {expected!r}",
            )
    if inv.get("sidecar_authority") != EXPECTED_AUTHORITY:
        raise TransformationContractViolation("C9", "invariants.sidecar_authority != NONE")
    if inv.get("target_authority") != EXPECTED_AUTHORITY:
        raise TransformationContractViolation("C9", "invariants.target_authority != NONE")
    results["sidecar_authority_none"] = True
    results["target_authority_none"] = True

    fences = state.overlays_by_class["fence_block"]
    unique_hashes = {r.payload["body_sha256"] for r in fences}
    dup_groups = sum(1 for ids in state.body_sha_to_overlay_ids.values() if len(ids) > 1)
    multilabel = state.overlays_by_class["t5_multilabel"]
    collapsed_true = sum(1 for r in multilabel if r.payload.get("collapsed") is True)
    t5_null = sum(
        1
        for r in state.overlays_by_class["t5_cls_row"]
        if r.payload.get("classified_source_line") is None
    )
    intersection = len(state.token_occurrence_ids.intersection(state.layer1_by_id))
    h1 = state.overlays_by_class["h1_span"]
    continuation = sum(1 for r in h1 if r.payload.get("is_continuation_title") is True)
    t3 = state.overlays_by_class["t3_src_span"]
    heading_outside = 0
    for rec in t3:
        heading = int(rec.payload["heading_line"])
        start = int(rec.payload["source_start_line"])
        end = int(rec.payload["source_end_line"])
        if not (start <= heading <= end):
            heading_outside += 1
    layer2 = state.sidecar["layer2_classification"]["records"]
    unique_occ = {r["occurrence_id"] for r in layer2}
    dual = [r for r in layer2 if r["occurrence_id"] == DUAL_CLASS_OCCURRENCE_ID]

    h1_sorted = sorted(h1, key=lambda r: int(r.payload["byte_start"]))
    if int(h1_sorted[0].payload["byte_start"]) != 0:
        raise TransformationContractViolation("SW-R-005", "h1 partition does not start at 0")
    prev = 0
    for rec in h1_sorted:
        start = int(rec.payload["byte_start"])
        end = int(rec.payload["byte_end"])
        if start != prev:
            raise TransformationContractViolation(
                "SW-R-005",
                f"h1 partition gap/overlap at {rec.overlay_id}",
            )
        prev = end
    if prev != EXPECTED_SOURCE_BYTES:
        raise TransformationContractViolation(
            "SW-R-005",
            f"h1 partition end {prev} != {EXPECTED_SOURCE_BYTES}",
        )

    measurements = {
        "layer1_count": len(state.layer1_ordered),
        "fence_block_count": len(fences),
        "fence_unique_body_hashes": len(unique_hashes),
        "fence_duplicate_groups": dup_groups,
        "t5_multilabel_count": len(multilabel),
        "t5_multilabel_collapsed_true_count": collapsed_true,
        "t5_classified_source_line_null_count": t5_null,
        "token_layer1_intersection": intersection,
        "h1_span_count": len(h1),
        "h1_continuation_count": continuation,
        "t3_src_span_count": len(t3),
        "t3_heading_outside_declared_region_count": heading_outside,
        "wrapper_mention_count": len(state.overlays_by_class["wrapper_mention"]),
        "wrapper_pair_count": len(state.overlays_by_class["wrapper_pair"]),
        "layer2_record_count": len(layer2),
        "layer2_unique_occurrence_ids": len(unique_occ),
        "dual_class_record_count": len(dual),
        "source_sha256": EXPECTED_SOURCE_SHA256,
    }
    expected = EXPECTED_LOSSLESSNESS
    checks = {
        "layer1_count": measurements["layer1_count"] == expected["LAYER1_COUNT"],
        "fence_block_count": measurements["fence_block_count"] == expected["FENCE_BLOCK_COUNT"],
        "fence_unique_body_hashes": measurements["fence_unique_body_hashes"]
        == expected["FENCE_UNIQUE_BODY_HASHES"],
        "fence_duplicate_groups": measurements["fence_duplicate_groups"]
        == expected["FENCE_DUPLICATE_GROUPS"],
        "t5_multilabel_collapsed_false": collapsed_true
        == expected["T5_MULTILABEL_COLLAPSED_TRUE_COUNT"],
        "t5_null_classified_source_line": t5_null
        == expected["T5_CLASSIFIED_SOURCE_LINE_NULL_COUNT"],
        "token_layer1_disjoint": intersection
        == expected["TOKEN_LAYER1_OCCURRENCE_ID_INTERSECTION_COUNT"],
        "h1_continuation": continuation == expected["H1_CONTINUATION_COUNT"],
        "t3_heading_outside": heading_outside
        == expected["T3_HEADING_OUTSIDE_DECLARED_REGION_COUNT"],
        "dual_class_preserved": len(dual) == 2,
        "authority_none_envelopes": all(e.authority_status == "NONE" for e in state.envelopes),
        "authority_none_relations": all(r.authority_status == "NONE" for r in state.relations),
        "semantic_container_not_adjudicated": all(
            e.semantic_container == "NOT_ADJUDICATED" for e in state.envelopes
        ),
        "adversarial_checks_true": all(
            v is True for v in state.sidecar["adversarial_checks"].values()
        ),
    }
    results.update(checks)
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        raise TransformationContractViolation(
            "STAGE_I",
            f"invariant re-measurement failed: {failed}",
        )

    for rec in state.overlays_by_class["t5_cls_row"]:
        mapped = rec.payload.get("content_class_mapped")
        verbatim = rec.payload.get("t5_label_verbatim")
        env = state.envelope_by_overlay_id[rec.overlay_id][0]
        if env.t5_label_verbatim.presence != "present":
            raise TransformationContractViolation("C8", "t5_label_verbatim dropped")
        if env.t5_label_verbatim.value != verbatim:
            raise TransformationContractViolation("C8", "t5_label_verbatim mutated")
        if mapped is not None and env.t5_label_verbatim.value == mapped:
            continue

    state.invariant_report = InvariantReport(
        results=results,
        measurements=measurements,
        passed=True,
    )
    state.stages_completed.append("I_INVARIANT_VALIDATION")

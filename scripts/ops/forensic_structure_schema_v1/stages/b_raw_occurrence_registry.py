"""Stage B — Raw Occurrence Registry. Primary key is occurrence_id, never content hash."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_LOSSLESSNESS,
    EXPECTED_SOURCE_BYTES,
    LAYER1_FIELD_ORDER,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import Layer1Occurrence
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def run_stage_b(state: PipelineState) -> None:
    raw = state.sidecar["layer1_raw_spans"]
    field_order = tuple(raw["field_order"])
    if field_order != LAYER1_FIELD_ORDER:
        raise TransformationContractViolation(
            "STAGE_B",
            f"layer1 field_order drift: {field_order}",
        )
    spans_raw = raw["spans"]
    expected_n = EXPECTED_LOSSLESSNESS["LAYER1_COUNT"]
    if len(spans_raw) != expected_n:
        raise TransformationContractViolation(
            "STAGE_B",
            f"layer1 count {len(spans_raw)} != {expected_n}",
        )

    ordered: list[Layer1Occurrence] = []
    by_id: dict[str, Layer1Occurrence] = {}
    prev_end = 0
    for index, tup in enumerate(spans_raw):
        if not isinstance(tup, list) or len(tup) != 8:
            raise TransformationContractViolation(
                "STAGE_B",
                f"layer1 tuple arity drift at index {index}",
            )
        occ = Layer1Occurrence(
            occurrence_id=str(tup[0]),
            source_sequence=int(tup[1]),
            byte_start=int(tup[2]),
            byte_end=int(tup[3]),
            line_start=int(tup[4]),
            line_end=int(tup[5]),
            content_hash_sha256=str(tup[6]),
            mechanical_type=str(tup[7]),
        )
        if occ.occurrence_id in by_id:
            raise TransformationContractViolation(
                "C2",
                f"duplicate layer1 occurrence_id {occ.occurrence_id}",
            )
        if occ.source_sequence != index + 1:
            raise TransformationContractViolation(
                "STAGE_B",
                f"source_sequence drift at {index}: {occ.source_sequence}",
            )
        if occ.byte_start != prev_end:
            raise TransformationContractViolation(
                "STAGE_B",
                f"layer1 gap/overlap at index {index}: prev_end={prev_end} "
                f"byte_start={occ.byte_start}",
            )
        if occ.byte_end < occ.byte_start:
            raise TransformationContractViolation(
                "STAGE_B",
                f"inverted byte range on {occ.occurrence_id}",
            )
        if occ.line_start != occ.line_end or occ.line_start != occ.source_sequence:
            raise TransformationContractViolation(
                "STAGE_B",
                f"layer1 single-line invariant failed on {occ.occurrence_id}",
            )
        by_id[occ.occurrence_id] = occ
        ordered.append(occ)
        prev_end = occ.byte_end

    if ordered[0].byte_start != 0 or prev_end != EXPECTED_SOURCE_BYTES:
        raise TransformationContractViolation(
            "STAGE_B",
            f"layer1 byte union is [{ordered[0].byte_start}, {prev_end}) "
            f"expected [0, {EXPECTED_SOURCE_BYTES})",
        )

    state.layer1_ordered = ordered
    state.layer1_by_id = by_id
    state.stages_completed.append("B_RAW_OCCURRENCE_REGISTRY")

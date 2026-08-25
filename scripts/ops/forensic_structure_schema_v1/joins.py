"""Closed join set. Line-equality and hash-equality are not joins."""

from __future__ import annotations

import bisect
from typing import Sequence

from scripts.ops.forensic_structure_schema_v1.constants import (
    CLOSED_JOIN_SET,
    ID_SPACE_NONE,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.id_spaces import (
    classify_alias,
    documentary_string_space,
    layer1_space,
)
from scripts.ops.forensic_structure_schema_v1.models import Binding, Layer1Occurrence


def assert_join_kind_closed(kind: str) -> None:
    if kind not in CLOSED_JOIN_SET:
        raise TransformationContractViolation(
            "UNAUTHORIZED_JOIN",
            f"join kind {kind!r} is not in the closed join set",
        )


def byte_range_containing_span(
    spans_by_start: Sequence[Layer1Occurrence],
    byte_start: int,
    byte_end: int,
    *,
    line: int | None = None,
) -> Layer1Occurrence:
    """BYTE_RANGE_EXACT: unique half-open containment in Layer-1 spans.

    ``line`` is a consistency check only (DR-003). It is not a join type.
    """
    if byte_end < byte_start:
        raise TransformationContractViolation(
            "C1",
            f"invalid byte range [{byte_start}, {byte_end})",
        )
    starts = [s.byte_start for s in spans_by_start]
    idx = bisect.bisect_right(starts, byte_start) - 1
    if idx < 0:
        raise TransformationContractViolation(
            "BYTE_RANGE_EXACT",
            f"no layer1 span contains [{byte_start}, {byte_end})",
        )
    span = spans_by_start[idx]
    if not (span.byte_start <= byte_start and byte_end <= span.byte_end):
        raise TransformationContractViolation(
            "BYTE_RANGE_EXACT",
            f"[{byte_start}, {byte_end}) is not contained in "
            f"[{span.byte_start}, {span.byte_end}) {span.occurrence_id}",
        )
    if line is not None and line != span.line_start:
        raise TransformationContractViolation(
            "DR-003",
            f"line {line} is not consistent with BYTE_RANGE_EXACT span "
            f"{span.occurrence_id} line_start={span.line_start}",
        )
    return span


def overlay_reference_binding(overlay_id: str, overlay_ids: set[str]) -> Binding:
    if overlay_id not in overlay_ids:
        raise TransformationContractViolation(
            "OVERLAY_REFERENCE",
            f"unknown overlay_id {overlay_id}",
        )
    from scripts.ops.forensic_structure_schema_v1.id_spaces import classify_overlay_id

    return Binding(
        kind="OVERLAY_REFERENCE",
        value=overlay_id,
        id_space=classify_overlay_id(overlay_id),
    )


def layer1_reference_binding(occurrence_id: str, layer1_ids: set[str]) -> Binding:
    if occurrence_id not in layer1_ids:
        raise TransformationContractViolation(
            "LAYER1_OCCURRENCE_REFERENCE",
            f"unknown layer1 occurrence_id {occurrence_id}",
        )
    return Binding(
        kind="LAYER1_OCCURRENCE_REFERENCE",
        value=occurrence_id,
        id_space=layer1_space(),
    )


def classify_endpoint(
    value: str,
    *,
    overlay_ids: set[str],
    layer1_ids: set[str],
    alias_maps: dict[str, str],
) -> Binding:
    """Map a layer-3/T4 endpoint to exactly one closed join kind.

    Alias maps are navigation-only. Documentary strings stay unresolved.
    Token occurrence ids are never accepted as LAYER1 references.
    """
    if value in overlay_ids:
        return overlay_reference_binding(value, overlay_ids)
    if value in layer1_ids:
        return layer1_reference_binding(value, layer1_ids)
    alias_space = classify_alias(value)
    if alias_space is not None:
        mapped = alias_maps.get(value)
        if mapped is None:
            return Binding(
                kind="DOCUMENTARY_STRING_ENDPOINT",
                value=value,
                id_space=alias_space,
                unresolved_to_occurrence=True,
            )
        return Binding(
            kind="EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
            value=value,
            id_space=alias_space,
            unresolved_to_occurrence=True,
        )
    return Binding(
        kind="DOCUMENTARY_STRING_ENDPOINT",
        value=value,
        id_space=documentary_string_space(),
        unresolved_to_occurrence=True,
    )


def unresolved_binding() -> Binding:
    return Binding(
        kind="UNRESOLVED",
        value="UNRESOLVED",
        id_space=ID_SPACE_NONE,
        unresolved_to_occurrence=True,
    )


def forbid_line_equality_join() -> None:
    raise TransformationContractViolation(
        "DR-003",
        "LINE_NUMBER_IS_NOT_A_JOIN_TYPE",
    )


def forbid_hash_equality_identity() -> None:
    raise TransformationContractViolation(
        "C2",
        "hash equality is not an identity proof",
    )

"""Closed identity spaces. Shared occ- prefix is not a join proof."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import (
    ID_SPACE_DOCUMENTARY_STRING,
    ID_SPACE_EPOCH,
    ID_SPACE_H1_ALIAS,
    ID_SPACE_LAYER1_OCCURRENCE,
    ID_SPACE_NONE,
    ID_SPACE_OVERLAY,
    ID_SPACE_RELATION,
    ID_SPACE_T3_SRC_ALIAS,
    ID_SPACE_T4_REL_ALIAS,
    ID_SPACE_T5_CLS_ALIAS,
    ID_SPACE_TOKEN_OCCURRENCE,
    ID_SPACE_TOKEN_OVERLAY,
    ID_SPACE_VIEW,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)


def classify_overlay_id(overlay_id: str) -> str:
    if overlay_id.startswith("token_occurrence-"):
        return ID_SPACE_TOKEN_OVERLAY
    if overlay_id.startswith(
        (
            "fence_block-",
            "forensic_record-",
            "h1_span-",
            "kv_packet-",
            "t3_src_span-",
            "t4_rel_row-",
            "t5_cls_row-",
            "t5_multilabel-",
            "wrapper_mention-",
            "wrapper_pair-",
            "append_epoch-",
        )
    ):
        return ID_SPACE_OVERLAY
    raise TransformationContractViolation(
        "ID_SPACE_UNKNOWN_OVERLAY_PREFIX",
        f"overlay_id not in a declared overlay space: {overlay_id}",
    )


def classify_alias(value: str) -> str | None:
    if value.startswith("SRC-"):
        return ID_SPACE_T3_SRC_ALIAS
    if value.startswith("REL-"):
        return ID_SPACE_T4_REL_ALIAS
    if value.startswith("CLS-"):
        return ID_SPACE_T5_CLS_ALIAS
    if value.startswith("H1-"):
        return ID_SPACE_H1_ALIAS
    return None


def classify_relation_id(relation_id: str) -> str:
    if relation_id.startswith("rel_"):
        return ID_SPACE_RELATION
    raise TransformationContractViolation(
        "ID_SPACE_UNKNOWN_RELATION_PREFIX",
        f"relation_id not in RELATION_ID_SPACE: {relation_id}",
    )


def classify_view_id(view_id: str) -> str:
    if view_id.startswith("view_"):
        return ID_SPACE_VIEW
    raise TransformationContractViolation(
        "ID_SPACE_UNKNOWN_VIEW_PREFIX",
        f"view_id not in VIEW_ID_SPACE: {view_id}",
    )


def epoch_id_space(_epoch_id: str) -> str:
    return ID_SPACE_EPOCH


def assert_token_layer1_disjoint(token_ids: set[str], layer1_ids: set[str]) -> None:
    overlap = token_ids.intersection(layer1_ids)
    if overlap:
        sample = sorted(overlap)[:5]
        raise TransformationContractViolation(
            "SW-R-008",
            f"TOKEN_OCCURRENCE_ID_SPACE intersected LAYER1_OCCURRENCE_ID_SPACE: {sample}",
        )


def forbid_equality_join_token_to_layer1(token_occurrence_id: str, layer1_ids: set[str]) -> None:
    """Equality join between the two occ-* spaces is forbidden even on miss."""
    if token_occurrence_id in layer1_ids:
        raise TransformationContractViolation(
            "SW-R-008",
            "equality join of token occurrence_id into LAYER1_OCCURRENCE_ID_SPACE: "
            f"{token_occurrence_id}",
        )


def documentary_string_space() -> str:
    return ID_SPACE_DOCUMENTARY_STRING


def none_space() -> str:
    return ID_SPACE_NONE


def layer1_space() -> str:
    return ID_SPACE_LAYER1_OCCURRENCE


def token_occurrence_space() -> str:
    return ID_SPACE_TOKEN_OCCURRENCE

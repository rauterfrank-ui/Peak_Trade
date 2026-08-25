"""Retain Layer-4 navigation/views without promoting parentage or authority."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_AUTHORITY,
    EXPECTED_LOSSLESSNESS,
    EXPECTED_NAVIGATION_VIEW_COUNT,
    VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.id_spaces import classify_view_id


def project_navigation_views(sidecar_views: list[Any]) -> list[dict[str, Any]]:
    """Copy sidecar views as NAVIGATION_OR_ANALYSIS_ONLY retained records."""
    if not isinstance(sidecar_views, list):
        raise TransformationContractViolation(
            "NAVIGATION_VIEW_RETENTION",
            "layer4_derived_views must be a list",
        )
    if len(sidecar_views) != EXPECTED_NAVIGATION_VIEW_COUNT:
        raise TransformationContractViolation(
            "NAVIGATION_VIEW_RETENTION",
            f"view count {len(sidecar_views)} != {EXPECTED_NAVIGATION_VIEW_COUNT}",
        )
    if len(sidecar_views) != EXPECTED_LOSSLESSNESS["VIEW_COUNT"]:
        raise TransformationContractViolation(
            "NAVIGATION_VIEW_RETENTION",
            "view count drifted from EXPECTED_LOSSLESSNESS.VIEW_COUNT",
        )
    retained: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(sidecar_views):
        if not isinstance(raw, dict):
            raise TransformationContractViolation(
                "NAVIGATION_VIEW_RETENTION",
                f"view at source_order {index} is not an object",
            )
        original = deepcopy(raw)
        view_id = str(original.get("view_id", ""))
        classify_view_id(view_id)
        if view_id in seen_ids:
            raise TransformationContractViolation(
                "NAVIGATION_VIEW_RETENTION",
                f"duplicate view_id {view_id}",
            )
        seen_ids.add(view_id)
        role = original.get("view_role")
        if role != VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY:
            raise TransformationContractViolation(
                "NAVIGATION_VIEW_RETENTION",
                f"{view_id} view_role {role!r} is not navigation-only",
            )
        for field_name in ("target_authority", "sidecar_authority"):
            if original.get(field_name) != EXPECTED_AUTHORITY:
                raise TransformationContractViolation(
                    "C9",
                    f"{view_id} {field_name}={original.get(field_name)!r}",
                )
        retained.append(
            {
                "view_id": view_id,
                "source_order": index,
                "view_role": VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY,
                "view_authority": EXPECTED_AUTHORITY,
                "target_authority": EXPECTED_AUTHORITY,
                "sidecar_authority": EXPECTED_AUTHORITY,
                "output_is_canonical": False,
                "output_is_authority_source": False,
                "does_not_alter_layer1_order": True,
                "does_not_alter_layer1_cardinality": True,
                "parentage_adjudicated": False,
                "sw_r_009_status": "OPEN",
                "parents_field_status": (
                    "DOCUMENTARY_UNADJUDICATED" if "parents" in original else "ABSENT"
                ),
                "original_view": original,
            }
        )
    return retained

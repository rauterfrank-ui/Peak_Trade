"""Navigation view retention tests. Views remain non-authoritative."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    DR_RESIDUAL_IDS,
    EXPECTED_LOSSLESSNESS,
    EXPECTED_NAVIGATION_VIEW_COUNT,
    SW_RESIDUAL_IDS,
    VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.navigation_views import (
    project_navigation_views,
)
from scripts.ops.forensic_structure_schema_v1.retained_output import (
    build_retained_dataset,
)


def _view(view_id: str, extra: dict | None = None) -> dict:
    payload = {
        "view_id": view_id,
        "view_role": VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY,
        "target_authority": "NONE",
        "sidecar_authority": "NONE",
        "member_ids": [],
        "member_kind": "demo",
        "does_not_replace_raw_spans": True,
    }
    if extra:
        payload.update(extra)
    return payload


def test_unit_view_retention_keeps_documentary_parents_unadjudicated() -> None:
    views = [_view(f"view_{i:02d}") for i in range(EXPECTED_NAVIGATION_VIEW_COUNT)]
    views[0]["parents"] = {"U16612": "SRC-000048"}
    retained = project_navigation_views(views)
    assert len(retained) == EXPECTED_NAVIGATION_VIEW_COUNT
    first = retained[0]
    assert first["view_role"] == VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY
    assert first["view_authority"] == "NONE"
    assert first["parentage_adjudicated"] is False
    assert first["sw_r_009_status"] == "OPEN"
    assert first["parents_field_status"] == "DOCUMENTARY_UNADJUDICATED"
    assert first["original_view"]["parents"] == {"U16612": "SRC-000048"}
    assert first["source_order"] == 0
    assert retained[1]["parents_field_status"] == "ABSENT"


def test_unit_view_count_and_role_drift_rejected() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        project_navigation_views([_view("view_only")])
    assert exc.value.rule == "NAVIGATION_VIEW_RETENTION"
    views = [_view(f"view_{i:02d}") for i in range(EXPECTED_NAVIGATION_VIEW_COUNT)]
    views[0]["view_role"] = "AUTHORITY"
    with pytest.raises(TransformationContractViolation) as exc:
        project_navigation_views(views)
    assert exc.value.rule == "NAVIGATION_VIEW_RETENTION"


@pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")
def test_bound_retained_views_are_navigation_only_and_do_not_alter_layer1() -> None:
    result = run_bound_transformer()
    layer1_before = [
        (occ.occurrence_id, occ.source_sequence, occ.byte_start, occ.byte_end)
        for occ in result.state.layer1_ordered
    ]
    dataset = build_retained_dataset(result.state)
    views = dataset["navigation_views"]
    assert len(views) == EXPECTED_NAVIGATION_VIEW_COUNT
    assert len(views) == EXPECTED_LOSSLESSNESS["VIEW_COUNT"]
    assert [v["view_id"] for v in views] == [
        v["view_id"] for v in result.state.sidecar["layer4_derived_views"]
    ]
    assert all(v["view_role"] == VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY for v in views)
    assert all(v["view_authority"] == "NONE" for v in views)
    assert all(v["output_is_canonical"] is False for v in views)
    assert all(v["output_is_authority_source"] is False for v in views)
    assert all(v["parentage_adjudicated"] is False for v in views)
    assert all(v["sw_r_009_status"] == "OPEN" for v in views)
    unresolved = next(v for v in views if v["view_id"] == "view_unresolved_boundaries")
    assert unresolved["parents_field_status"] == "DOCUMENTARY_UNADJUDICATED"
    assert unresolved["original_view"]["parents"] == {
        "U16612": "SRC-000048",
        "U25510": "SRC-000082",
        "U29481": "SRC-000087",
    }
    layer1_after = [
        (row["occurrence_id"], row["source_sequence"], row["byte_start"], row["byte_end"])
        for row in dataset["layer1_occurrences"]
    ]
    assert layer1_after == layer1_before
    assert len(dataset["layer1_occurrences"]) == EXPECTED_LOSSLESSNESS["LAYER1_COUNT"]
    residual = next(r for r in result.state.residuals if r.residual_id == "SW-R-009")
    assert residual.status == "OPEN"
    assert residual.auto_closed is False
    assert {r.residual_id for r in result.state.residuals if r.status == "OPEN"} == set(
        SW_RESIDUAL_IDS + DR_RESIDUAL_IDS
    )
    assert result.state.witness is not None
    assert result.state.witness.target_authority == "NONE"
    assert dataset["output_authority"] == "NONE"
    assert dataset["dataset_only_reconstruction_claim"] is False

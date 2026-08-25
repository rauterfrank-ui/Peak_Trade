"""Unit tests that do not require the bound forensic source/sidecar."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from scripts.ops.forensic_structure_schema_v1.constants import (
    CLOSED_JOIN_SET,
    DEFAULT_AUTHORITY_STATUS,
    DEFAULT_CURRENTNESS_STATUS,
    DEFAULT_GATE_MEMBERSHIP,
    DR_RESIDUAL_IDS,
    FORBIDDEN_IMPORT_PREFIXES,
    STAGE_ORDER,
    SW_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import (
    GuardProgram,
    forbid_body_sha_survivor_store,
    forbid_hash_kind_from_length,
    forbid_kv_packet_synthetic_occ,
    forbid_mention_to_pair,
    forbid_null_historical_sha_fill,
    forbid_set_labels_as_lossless_source,
    forbid_synthetic_inner_fence,
    forbid_t3_heading_region_fusion,
    forbid_t5_range_expansion,
    forbid_verbatim_survivor_store,
)
from scripts.ops.forensic_structure_schema_v1.id_spaces import (
    assert_token_layer1_disjoint,
    classify_overlay_id,
)
from scripts.ops.forensic_structure_schema_v1.joins import assert_join_kind_closed
from scripts.ops.forensic_structure_schema_v1.minting import mint_transformation_local_id
from scripts.ops.forensic_structure_schema_v1.models import (
    OptionalValue,
    RelationEnvelope,
    SemanticEnvelope,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes

PKG = Path("scripts/ops/forensic_structure_schema_v1")


def test_closed_join_set_has_exactly_six_kinds() -> None:
    assert CLOSED_JOIN_SET == (
        "BYTE_RANGE_EXACT",
        "OVERLAY_REFERENCE",
        "LAYER1_OCCURRENCE_REFERENCE",
        "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
        "DOCUMENTARY_STRING_ENDPOINT",
        "UNRESOLVED",
    )
    with pytest.raises(TransformationContractViolation) as exc:
        assert_join_kind_closed("LINE_EQUALITY")
    assert exc.value.rule == "UNAUTHORIZED_JOIN"


def test_token_layer1_disjointness_guard() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        assert_token_layer1_disjoint({"occ-aaa"}, {"occ-aaa"})
    assert exc.value.rule == "SW-R-008"


def test_minting_is_source_order_not_content_hash() -> None:
    a = mint_transformation_local_id(
        kind="fence_block",
        source_order=12,
        sidecar_stable_suffix="fence_block-aaa",
    )
    b = mint_transformation_local_id(
        kind="fence_block",
        source_order=12,
        sidecar_stable_suffix="fence_block-aaa",
    )
    assert a == b
    assert a == "tlid-fence_block-000012-fence_block-aaa"
    dual = mint_transformation_local_id(
        kind="layer2",
        source_order=90,
        sidecar_stable_suffix="h1_span-x",
        layer2_record_index=4047,
    )
    assert dual.endswith("-r4047")
    assert "sha256" not in dual


def test_optional_value_distinguishes_absent_null_present() -> None:
    absent = OptionalValue.absent().to_canonical()
    null = OptionalValue.null().to_canonical()
    present_false = OptionalValue.present(False).to_canonical()
    present_unknown = OptionalValue.present("UNKNOWN").to_canonical()
    present_none_enum = OptionalValue.present("NONE").to_canonical()
    assert absent == {"presence": "absent"}
    assert null == {"presence": "null", "value": None}
    assert present_false == {"presence": "present", "value": False}
    assert present_unknown != null
    assert present_none_enum != absent
    blob = dumps_canonical_bytes({"a": absent, "b": null, "c": present_false, "d": present_unknown})
    again = dumps_canonical_bytes(
        {"d": present_unknown, "c": present_false, "b": null, "a": absent}
    )
    assert blob == again


def test_named_non_inference_guards() -> None:
    cases = [
        (forbid_verbatim_survivor_store, "C2"),
        (forbid_body_sha_survivor_store, "C3"),
        (lambda: forbid_t5_range_expansion(320), "SW-R-003"),
        (forbid_hash_kind_from_length, "D7"),
        (forbid_set_labels_as_lossless_source, "SW-R-013"),
        (forbid_synthetic_inner_fence, "SW-R-006"),
        (forbid_mention_to_pair, "TV-011"),
        (forbid_null_historical_sha_fill, "SW-R-014"),
        (forbid_t3_heading_region_fusion, "SW-R-015"),
        (forbid_kv_packet_synthetic_occ, "DR-008"),
    ]
    for fn, rule in cases:
        with pytest.raises(TransformationContractViolation) as exc:
            fn()
        assert exc.value.rule == rule


def test_guard_program_rejects_winner_and_gate() -> None:
    guards = GuardProgram()
    env = SemanticEnvelope(
        transformation_local_id="tlid-x-000001-y",
        source_byte_start=0,
        source_byte_end=1,
        source_sha256="a" * 64,
        sidecar_overlay_id=OptionalValue.null(),
        layer1_occurrence_id=OptionalValue.null(),
        token_occurrence_id=OptionalValue.null(),
        provenance_type="UNKNOWN",
        winner_selected=True,
    )
    with pytest.raises(TransformationContractViolation) as exc:
        guards.check_envelope_defaults(env)
    assert exc.value.rule == "C5"

    rel = RelationEnvelope(
        transformation_local_id="tlid-relation-000000-rel_x",
        relation_id="rel_x",
        relation_type="STRUCTURAL_ORDERED_BEFORE",
        relation_provenance="PRIOR_ADJUDICATION_REFERENCE",
        from_binding=__import__(
            "scripts.ops.forensic_structure_schema_v1.models", fromlist=["Binding"]
        ).Binding(
            kind="EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
            value="REL-000001",
            id_space="T4_REL_ALIAS_SPACE",
            unresolved_to_occurrence=True,
        ),
        to_binding=__import__(
            "scripts.ops.forensic_structure_schema_v1.models", fromlist=["Binding"]
        ).Binding(
            kind="EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
            value="SRC-000001",
            id_space="T3_SRC_ALIAS_SPACE",
            unresolved_to_occurrence=True,
        ),
        relation_epistemic_basis="PRIOR_ADJUDICATION_REFERENCE",
        is_dependency=True,
        unresolved=OptionalValue.present(False),
        winner_selected=False,
        source_occurrence_id=OptionalValue.null(),
        sidecar_overlay_id=OptionalValue.null(),
        end_occurrence_id=OptionalValue.null(),
        gate_membership=DEFAULT_GATE_MEMBERSHIP,
    )
    with pytest.raises(TransformationContractViolation) as exc:
        guards.check_relation(rel)
    assert exc.value.rule == "D1"


def test_defaults_are_non_positive() -> None:
    assert DEFAULT_AUTHORITY_STATUS == "NONE"
    assert DEFAULT_CURRENTNESS_STATUS == "CURRENTNESS_UNKNOWN"
    assert DEFAULT_GATE_MEMBERSHIP == "UNKNOWN"


def test_residuals_are_enumerated_and_not_auto_closeable_by_constants() -> None:
    assert SW_RESIDUAL_IDS == tuple(f"SW-R-{i:03d}" for i in range(1, 16))
    assert DR_RESIDUAL_IDS == ("DR-001", "DR-002", "DR-003", "DR-006", "DR-007", "DR-008")


def test_stage_order_is_a_through_l_unmerged() -> None:
    assert STAGE_ORDER[0].startswith("A_")
    assert STAGE_ORDER[-1].startswith("L_")
    assert len(STAGE_ORDER) == 12


def test_overlay_id_spaces_partitioned() -> None:
    assert "TOKEN_OVERLAY" in classify_overlay_id("token_occurrence-abc")
    assert classify_overlay_id("fence_block-abc").endswith("PARTITIONED_BY_CLASS")
    with pytest.raises(TransformationContractViolation):
        classify_overlay_id("occ-not-an-overlay")


def test_package_has_no_trading_imports() -> None:
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in FORBIDDEN_IMPORT_PREFIXES:
                        assert not alias.name.startswith(prefix), path
            elif isinstance(node, ast.ImportFrom) and node.module:
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not node.module.startswith(prefix), path

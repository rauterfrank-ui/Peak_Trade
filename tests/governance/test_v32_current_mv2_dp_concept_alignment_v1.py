"""Tests for Concept v3/v3.2 CURRENT MV2+DP alignment (documentation binding only)."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.v32_current_mv2_dp_concept_alignment_v1 import (
    ALIGNMENT_ADDENDUM_SPEC,
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    OWNER_SYMBOLS,
    PDF_DELTA_INVENTORY_COUNT,
    WORKPACKAGE_ID,
    assert_concept_alignment_consistent_with_v32_lifecycle_v1,
    assert_current_owner_symbols_importable_v1,
    concept_alignment_binding_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_decision_config_and_specs_present() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["documentation_only"] is True
    assert decision["runtime_files_changed"] is False
    assert decision["p5_authority_cutover_authorized"] is False
    assert decision["pdf_stale_items_found"] == PDF_DELTA_INVENTORY_COUNT
    assert (REPO_ROOT / NORMATIVE_SPEC).is_file()
    assert (REPO_ROOT / ALIGNMENT_ADDENDUM_SPEC).is_file()


def test_owner_symbols_importable() -> None:
    assert_current_owner_symbols_importable_v1()
    assert len(OWNER_SYMBOLS) == 6


def test_alignment_consistent_with_v32_lifecycle_adjudication() -> None:
    assert_concept_alignment_consistent_with_v32_lifecycle_v1(repo_root=REPO_ROOT)
    binding = concept_alignment_binding_v1(repo_root=REPO_ROOT)
    assert binding["d26_implemented"] is True
    assert binding["d26_status"] == "PROVEN_CURRENT"
    assert binding["earliest_true_remaining_technical_gap"] is None
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False


def test_addendum_does_not_imply_layered_cutover() -> None:
    text = (REPO_ROOT / ALIGNMENT_ADDENDUM_SPEC).read_text(encoding="utf-8")
    assert "P5_AUTHORITY_CUTOVER_AUTHORIZED=false" in text
    assert "not layered-core cutover" in text.lower() or "not** layered-core cutover" in text


def test_normative_spec_points_to_d26_closure_spec() -> None:
    text = (REPO_ROOT / NORMATIVE_SPEC).read_text(encoding="utf-8")
    assert "V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1" in text
    d26_spec = REPO_ROOT / (
        "docs/ops/specs/V32_D26_PLATFORM_UNIFIED_NATIVE_VS_CANDIDATE_BASELINE_EVIDENCE_CLOSURE_V1.md"
    )
    assert d26_spec.is_file()

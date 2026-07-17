"""AUTH021/AUTH003 matrix sync with B-01/B-07 closeout (docs-only).

Static contract: ``authority_conflict_matrix_v1.md`` must reflect PR #5274
B-01/B-07 CLOSED truth. Does **not** create authority decisions, runtime
wiring, alias resolution outside boundary docs, or dashboard changes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = REPO_ROOT / "docs" / "governance" / "authority_conflict_matrix_v1.md"
PLAN = REPO_ROOT / "docs" / "analysis" / "missing_features_plan.md"
FEATURE_STATE_MAP = REPO_ROOT / "docs" / "governance" / "feature_state_map_v1.md"
DRIFT_PLAN = REPO_ROOT / "docs" / "governance" / "drift_cleanup_plan_v1.md"
B01_B07_EVIDENCE = (
    REPO_ROOT
    / "docs"
    / "product"
    / "evidence"
    / "drift_b01_b07_missing_features_plan_deferred_alignment_v0_20260717T033503Z"
)

PACKAGE_MARKER = "AUTH021_AUTH003_AUTHORITY_MATRIX_B01_B07_CLOSEOUT_SYNC_V0=true"

FORBIDDEN_DIRECT_AUTHORITY_LABELS: tuple[str, ...] = (
    "FEATURE_ENGINE_AUTHORITATIVE",
    "PLAN_AUTHORITATIVE",
    "RUNTIME_FEATURE_ENGINE_ENABLED",
    "DIRECT_AUTHORITY_MAPPING=true",
)

FORBIDDEN_BYPASS_PHRASES: tuple[str, ...] = (
    "BYPASS_AUTHORITY=true",
    "classic_engine_decision_authority_bypass",
    "LIVE_AUTHORIZED=true",
    "ORDERS=true",
)

FORBIDDEN_PROMOTION_PHRASES: tuple[str, ...] = (
    "Feature-Engine is READY",
    "Feature-Engine is ENABLED",
    "Feature-Engine is PASS",
    "Feature-Engine live-authorized",
)

# Canonical / boundary-only status tokens for this docs surface.
CANONICAL_MATRIX_STATES: frozenset[str] = frozenset(
    {
        "CLOSED",
        "DEFERRED",
        "STRUCTURAL",
        "NON-OPERATIONAL",
        "INTENTIONAL_POLICY_STATE",
    }
)

LEGACY_ALIAS_BOUNDARY_ONLY: frozenset[str] = frozenset(
    {
        "deferred",
        "DEFERRED",
        "Defer",
        "roadmap",
        "placeholder",
    }
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    rest = text[start + len(heading) :]
    nxt = rest.find("\n### ")
    return heading + (rest if nxt < 0 else rest[:nxt])


def test_package_marker_stable() -> None:
    assert PACKAGE_MARKER.startswith("AUTH021_AUTH003_")
    assert "B01_B07_CLOSEOUT_SYNC" in PACKAGE_MARKER


def test_auth021_matrix_closed_bound_to_b01_b07_evidence() -> None:
    matrix = _read(MATRIX)
    section = _section(matrix, "### AUTH-021 —")
    assert "**Status**" in section
    assert "CLOSED (2026-07-17)" in section
    assert "PR #5274" in section
    assert "B-01" in section and "B-07" in section
    assert "B-01 Operator-GO" not in section
    assert "721f28f52b81b01f01ec310eee0dbcdc75d10cce" in section
    assert "drift_b01_b07_missing_features_plan_deferred_alignment_v0_20260717T033503Z" in section
    assert B01_B07_EVIDENCE.is_dir()
    assert (B01_B07_EVIDENCE / "manifest.json").is_file()


def test_auth003_docs_layer_closed_residual_type_d_preserved() -> None:
    matrix = _read(MATRIX)
    section = _section(matrix, "### AUTH-003 —")
    assert "Status (docs layer)" in section
    assert "CLOSED (2026-07-17)" in section
    assert "PR #5274" in section
    assert "noch structural offen" not in section
    assert "Type D" in section or "**D**" in section
    assert "blocked" in section.lower() or "Product-Entscheid" in section
    # Must not claim full AUTH-003 authority resolution.
    assert "runtime enablement" in section.lower() or "Class C deferred" in section


def test_summary_matrix_marks_auth021_closed_and_auth003_docs_layer() -> None:
    matrix = _read(MATRIX)
    assert "AUTH-021" in matrix and "**CLOSED** (PR #5274 / B-01+B-07)" in matrix
    assert "docs layer B-01 CLOSED" in matrix
    assert "residual Type D remains" in matrix


def test_b01_b07_canonical_plan_still_deferred_fail_closed() -> None:
    plan = _read(PLAN)
    drift = _read(DRIFT_PLAN)
    assert "STRUCTURAL DOC DRIFT" in plan or "DEFERRED" in plan
    assert "NON-OPERATIONAL" in plan
    assert "feature_state_map_v1.md" in plan
    assert "**CLOSED (2026-07-17)**" in drift
    assert "B-01" in drift and "B-07" in drift
    fsm = _read(FEATURE_STATE_MAP)
    assert "Feature-Engine (central layer)" in fsm
    assert "Defer" in fsm


def test_no_direct_authority_mappings_introduced() -> None:
    matrix = _read(MATRIX)
    for label in FORBIDDEN_DIRECT_AUTHORITY_LABELS:
        assert label not in matrix, f"direct authority mapping label: {label!r}"


def test_no_bypass_paths_introduced() -> None:
    matrix = _read(MATRIX)
    for phrase in FORBIDDEN_BYPASS_PHRASES:
        assert phrase not in matrix, f"bypass phrase: {phrase!r}"


def test_no_feature_engine_promotion_or_runtime_activation() -> None:
    matrix = _read(MATRIX)
    for phrase in FORBIDDEN_PROMOTION_PHRASES:
        assert phrase not in matrix, f"promotion phrase: {phrase!r}"
    assert "LIVE_AUTHORIZED=true" not in matrix
    assert "ORDERS=true" not in matrix
    auth021 = _section(matrix, "### AUTH-021 —")
    assert "not operational wiring authority" in auth021.lower() or "NON-OPERATIONAL" in auth021


def test_unknown_marker_and_missing_features_fail_closed() -> None:
    known = CANONICAL_MATRIX_STATES | LEGACY_ALIAS_BOUNDARY_ONLY
    unknown = "TOTALLY_UNKNOWN_AUTHORITY_STATUS_XYZ"
    assert unknown not in known
    assert unknown not in _read(MATRIX)
    assert unknown not in _read(PLAN)
    with pytest.raises(AssertionError):
        assert unknown in known


def test_legacy_alias_boundary_only() -> None:
    """Legacy deferred synonyms remain documentation-boundary only."""
    plan = _read(PLAN)
    lower = plan.lower()
    assert "deferred" in lower or "defer" in lower
    for phrase in FORBIDDEN_PROMOTION_PHRASES:
        assert phrase not in plan


def test_stale_open_dependency_markers_removed() -> None:
    """The confirmed missing-link cluster must not remain open in the matrix."""
    matrix = _read(MATRIX)
    auth021 = _section(matrix, "### AUTH-021 —")
    auth003 = _section(matrix, "### AUTH-003 —")
    assert "Resolution Dependency** | B-01 Operator-GO" not in auth021
    assert "noch structural offen" not in auth003
    assert "CLOSED" in auth021 and "CLOSED" in auth003

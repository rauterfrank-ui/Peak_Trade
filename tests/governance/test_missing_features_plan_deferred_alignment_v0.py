"""DRIFT_B01/B07: missing_features_plan.md deferred + NON-OPERATIONAL DAG alignment.

Static docs↔governance contract. Reuses Class C / Validation Rule truth from
``docs/governance/feature_state_map_v1.md``. Does **not** create runtime Feature-
Engine wiring, authority decision logic, or dashboard changes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN = REPO_ROOT / "docs" / "analysis" / "missing_features_plan.md"
FEATURE_STATE_MAP = REPO_ROOT / "docs" / "governance" / "feature_state_map_v1.md"
FEATURES_INIT = REPO_ROOT / "src" / "features" / "__init__.py"
PIPELINE_PY = REPO_ROOT / "src" / "features" / "pipeline.py"

PACKAGE_MARKER = "DRIFT_B01_B07_MISSING_FEATURES_PLAN_DEFERRED_ALIGNMENT_V0=true"

# Canonical plan-state tokens for this docs surface (projection only).
CANONICAL_PLAN_STATES: frozenset[str] = frozenset(
    {
        "deferred",
        "DEFERRED",
        "STRUCTURAL DOC DRIFT",
        "NON-OPERATIONAL",
        "Non-operational",
        "Defer",
    }
)

# Boundary-only legacy aliases that may appear as synonyms of deferred.
LEGACY_DEFERRED_ALIASES_AT_BOUNDARY: frozenset[str] = frozenset(
    {
        "deferred",
        "DEFERRED",
        "Defer",
        "roadmap",
        "placeholder",
    }
)

# Forbidden promotions for this plan / Feature-Engine surface.
FORBIDDEN_PROMOTION_PHRASES: tuple[str, ...] = (
    "Feature-Engine is READY",
    "Feature-Engine is ENABLED",
    "Feature-Engine is PASS",
    "Feature-Engine live-authorized",
    "pipeline.py is operational",
    "LIVE_AUTHORIZED=true",
    "ORDERS=true",
)

FORBIDDEN_DIVERGENT_AUTHORITY_LABELS: tuple[str, ...] = (
    "FEATURE_ENGINE_AUTHORITATIVE",
    "PLAN_AUTHORITATIVE",
    "RUNTIME_FEATURE_ENGINE_ENABLED",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


def test_package_marker_stable() -> None:
    assert PACKAGE_MARKER.startswith("DRIFT_B01_B07_")
    assert "DEFERRED_ALIGNMENT" in PACKAGE_MARKER


def test_b01_deferred_banner_and_class_c_crosslink() -> None:
    text = _read(PLAN)
    assert "STRUCTURAL DOC DRIFT" in text or "STRUCTURAL DOC DRIFT / DEFERRED" in text
    assert "DEFERRED" in text or "deferred" in text
    assert "feature_state_map_v1.md" in text
    assert "Class C" in text
    assert "Defer" in text
    assert "not operational wiring authority" in text.lower() or "not operational wiring" in text
    # Must not silently claim operational readiness.
    assert "fail-closed" in text.lower() or "fail-closed" in text


def test_b01_src_features_framed_as_deferred_placeholder() -> None:
    text = _read(PLAN)
    assert "deferred placeholder" in text.lower() or "DEFERRED" in text
    assert "src/features" in text or "src&#47;features" in text
    assert FEATURES_INIT.is_file()
    assert not PIPELINE_PY.is_file(), "pipeline.py must remain absent (roadmap only)"


def test_b07_dag_non_operational_footnote() -> None:
    text = _read(PLAN)
    assert "NON-OPERATIONAL" in text
    assert "Validation Rule" in text or "Validation Rule" in _read(FEATURE_STATE_MAP)
    assert "NOT in Runtime Decision Core" in _read(FEATURE_STATE_MAP)
    assert "Feature-Engine" in text
    assert "deferred" in text.lower() or "DEFERRED" in text
    # DAG section must mark Feature-Engine edges as non-operational/deferred.
    assert "Class C" in text
    assert "roadmap" in text.lower() or "DEFERRED" in text


def test_feature_state_map_class_c_feature_engine_defer() -> None:
    text = _read(FEATURE_STATE_MAP)
    assert "Feature-Engine (central layer)" in text
    assert "Defer" in text
    assert "NON-OPERATIONAL" in text or "Non-operational" in text


def test_missing_features_fail_closed_no_ready_pass_enabled_promotion() -> None:
    text = _read(PLAN)
    for phrase in FORBIDDEN_PROMOTION_PHRASES:
        assert phrase not in text, f"forbidden promotion: {phrase!r}"


def test_no_divergent_direct_authority_mappings() -> None:
    text = _read(PLAN)
    for label in FORBIDDEN_DIVERGENT_AUTHORITY_LABELS:
        assert label not in text, f"divergent authority label: {label!r}"


def test_unknown_marker_rejected() -> None:
    known = CANONICAL_PLAN_STATES | LEGACY_DEFERRED_ALIASES_AT_BOUNDARY
    unknown = "TOTALLY_UNKNOWN_PLAN_STATUS_XYZ"
    assert unknown not in known
    assert unknown not in _read(PLAN)
    with pytest.raises(AssertionError):
        assert unknown in known


def test_legacy_alias_boundary_only_inventory() -> None:
    """Legacy deferred synonyms are documentation-boundary only (this plan file)."""
    text = _read(PLAN)
    lower = text.lower()
    assert "deferred" in lower or "defer" in lower
    for phrase in FORBIDDEN_PROMOTION_PHRASES:
        assert phrase not in text


def test_behavior_preserving_no_runtime_activation_claims() -> None:
    text = _read(PLAN)
    assert "does **not** authorize" in text
    assert "runtime activation" in text.lower() or "Runtime" in text or "runtime" in text
    assert "Kein Live-Trading freischalten" in text


def test_deterministic_required_markers_serializable() -> None:
    """Required markers are stable strings (audit-friendly)."""
    text = _read(PLAN)
    assert "feature_state_map_v1.md" in text
    assert "NON-OPERATIONAL" in text
    assert "Class C" in text
    assert ("DEFERRED" in text) or ("deferred" in text.lower())
    markers = {
        "feature_state_map": "feature_state_map_v1.md" in text,
        "non_operational": "NON-OPERATIONAL" in text,
        "class_c": "Class C" in text,
        "deferred": ("DEFERRED" in text) or ("deferred" in text.lower()),
    }
    assert all(markers.values()), markers

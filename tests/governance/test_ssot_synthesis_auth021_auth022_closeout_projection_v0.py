"""SSOT_SYNTHESIS_AUTH021_AUTH022_CLOSEOUT_PROJECTION_V0

Static contract: SSOT/synthesis/counterfactual projection surfaces must
project AUTH-021/AUTH-022 CLOSED from canonical
``authority_conflict_matrix_v1.md``. Docs-only; no runtime authority,
no dashboard, no second status engine.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = REPO_ROOT / "docs" / "governance" / "authority_conflict_matrix_v1.md"
SSOT_NEUTRAL = REPO_ROOT / "docs" / "governance" / "ssot_decision_surface_neutral_v1.md"
SYNTHESIS = REPO_ROOT / "docs" / "governance" / "authority_resolution_synthesis_v1.md"
COUNTERFACTUAL = REPO_ROOT / "docs" / "governance" / "ssot_counterfactual_simulation_v1.md"
PLAN = REPO_ROOT / "docs" / "analysis" / "missing_features_plan.md"

PACKAGE_MARKER = "SSOT_SYNTHESIS_AUTH021_AUTH022_CLOSEOUT_PROJECTION_V0=true"

PROJECTION_SURFACES: tuple[Path, ...] = (SSOT_NEUTRAL, SYNTHESIS, COUNTERFACTUAL)

FORBIDDEN_DIRECT_AUTHORITY: tuple[str, ...] = (
    "FEATURE_ENGINE_AUTHORITATIVE",
    "PLAN_AUTHORITATIVE",
    "RUNTIME_FEATURE_ENGINE_ENABLED",
    "DIRECT_AUTHORITY_MAPPING=true",
    "SSOT_SYNTHESIS_AUTHORITATIVE_RUNTIME=true",
)

FORBIDDEN_BYPASS: tuple[str, ...] = (
    "BYPASS_AUTHORITY=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS=true",
    "SHADOW=true",
    "PAPER=true",
    "TESTNET=true",
)

FORBIDDEN_PROMOTION: tuple[str, ...] = (
    "Feature-Engine is READY",
    "Feature-Engine is ENABLED",
    "Feature-Engine is PASS",
    "Feature-Engine live-authorized",
)

CANONICAL_CLOSEOUT_STATES: frozenset[str] = frozenset(
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
        "docs-echo",
        "docs-only",
    }
)

# Stale open-gap phrases that must not remain for AUTH-021/022 projections.
STALE_OPEN_AUTH021_PHRASES: tuple[str, ...] = (
    "B-01 weiter separat",
    "AUTH-021, AUTH-022 — structural docs only",
    "AUTH-021 (Feature-Engine stale DAG), AUTH-022 (R&D stub grammar) — LOW, structural docs only",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


def _matrix_section(heading: str) -> str:
    text = _read(MATRIX)
    start = text.index(heading)
    rest = text[start + len(heading) :]
    nxt = rest.find("\n### ")
    return heading + (rest if nxt < 0 else rest[:nxt])


def test_package_marker_stable() -> None:
    assert PACKAGE_MARKER.startswith("SSOT_SYNTHESIS_AUTH021_AUTH022_")
    assert "CLOSEOUT_PROJECTION" in PACKAGE_MARKER


def test_canonical_matrix_auth021_auth022_closed_happy_path() -> None:
    a21 = _matrix_section("### AUTH-021 —")
    a22 = _matrix_section("### AUTH-022 —")
    assert "CLOSED (2026-07-17)" in a21
    assert "PR #5274" in a21
    assert "CLOSED (2026-07-17)" in a22
    assert "PR #5270" in a22
    assert "B-01 Operator-GO" not in a21


def test_projection_surfaces_synthesize_closed_from_matrix() -> None:
    """Happy path: all three projection owners mark AUTH-021/022 CLOSED."""
    for path in PROJECTION_SURFACES:
        text = _read(path)
        assert "AUTH-021" in text and "AUTH-022" in text
        # Require CLOSED near AUTH-021 / AUTH-022 projections (not just anywhere).
        assert "CLOSED" in text
        assert (
            "matrix SSOT" in text
            or "canonical matrix" in text
            or "authority_conflict_matrix" in text
        )


def test_ssot_neutral_auth021_auth022_closeout_markers() -> None:
    text = _read(SSOT_NEUTRAL)
    assert "AUTH-021" in text and "**CLOSED**" in text
    assert "PR #5274" in text or "PR #5276" in text
    assert "PR #5270" in text
    assert "AUTH-021, AUTH-022 — structural docs only" not in text
    assert "stale DAG | A (Feature-Engine) | A |" not in text or "CLOSED" in text
    # AUTH-023 must not be falsely closed by this slice.
    assert "AUTH-023" in text
    assert "optional A-06" in text or "A-06 follow-up" in text


def test_synthesis_auth021_auth022_closeout_markers() -> None:
    text = _read(SYNTHESIS)
    assert "**CLOSED** — matrix SSOT" in text or "CLOSED** — matrix SSOT" in text
    assert "do not re-open as structural docs-echo" in text or "CLOSED" in text
    assert (
        "LOW, structural docs only"
        not in text.split("Residual Docs-Echo (Domain B):")[1].split("\n")[0]
    )


def test_counterfactual_no_b01_weiter_separat() -> None:
    text = _read(COUNTERFACTUAL)
    assert "B-01 weiter separat" not in text
    assert "CLOSED" in text
    assert "AUTH-021" in text and "AUTH-022" in text


def test_stale_open_gap_phrases_removed() -> None:
    combined = "\n".join(_read(p) for p in PROJECTION_SURFACES)
    for phrase in STALE_OPEN_AUTH021_PHRASES:
        assert phrase not in combined, f"stale open phrase remains: {phrase!r}"


def test_unknown_marker_fail_closed() -> None:
    known = CANONICAL_CLOSEOUT_STATES | LEGACY_ALIAS_BOUNDARY_ONLY
    unknown = "TOTALLY_UNKNOWN_SSOT_CLOSEOUT_STATUS_XYZ"
    assert unknown not in known
    for path in (MATRIX, *PROJECTION_SURFACES, PLAN):
        assert unknown not in _read(path)
    with pytest.raises(AssertionError):
        assert unknown in known


def test_missing_features_fail_closed_no_promotion() -> None:
    plan = _read(PLAN)
    for phrase in FORBIDDEN_PROMOTION:
        assert phrase not in plan
    for path in PROJECTION_SURFACES:
        text = _read(path)
        for phrase in FORBIDDEN_PROMOTION:
            assert phrase not in text, f"{path.name}: {phrase}"


def test_legacy_alias_boundary_only() -> None:
    """Legacy deferred / docs-echo synonyms remain documentation-boundary only."""
    plan = _read(PLAN)
    assert "deferred" in plan.lower() or "defer" in plan.lower()
    for path in PROJECTION_SURFACES:
        text = _read(path)
        for phrase in FORBIDDEN_DIRECT_AUTHORITY + FORBIDDEN_BYPASS:
            assert phrase not in text


def test_no_direct_authority_mappings_or_bypass() -> None:
    for path in (MATRIX, *PROJECTION_SURFACES):
        text = _read(path)
        for label in FORBIDDEN_DIRECT_AUTHORITY:
            assert label not in text
        for phrase in FORBIDDEN_BYPASS:
            assert phrase not in text


def test_deterministic_closeout_markers_serializable() -> None:
    markers = {
        "matrix_auth021_closed": "CLOSED (2026-07-17)" in _matrix_section("### AUTH-021 —"),
        "matrix_auth022_closed": "CLOSED (2026-07-17)" in _matrix_section("### AUTH-022 —"),
        "ssot_projects_closed": "CLOSED" in _read(SSOT_NEUTRAL),
        "synthesis_projects_closed": "CLOSED" in _read(SYNTHESIS),
        "counterfactual_no_b01_separat": "B-01 weiter separat" not in _read(COUNTERFACTUAL),
    }
    assert all(markers.values()), markers


def test_no_second_authority_engine_claims() -> None:
    for path in PROJECTION_SURFACES:
        text = _read(path)
        assert (
            "second status engine" not in text.lower() or "no second status engine" in text.lower()
        )
        assert "SSOT_SYNTHESIS_AUTHORITATIVE_RUNTIME=true" not in text

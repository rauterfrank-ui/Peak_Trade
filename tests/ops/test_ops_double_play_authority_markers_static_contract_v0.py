"""DRIFT_B03: Ops Double-Play runbooks must mirror Slice E authority markers.

Static docs↔code contract. Reuses frozen authority constants from
``trading.master_v2.evaluate_double_play_authority_boundary_v0`` — does **not**
create a second authority decision owner or change Double-Play algorithms.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER,
    EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_OWNER,
    LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE,
    MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED,
    OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
    ZERO_ORDER_RUNTIME_READY,
    classify_ops_evaluate_double_play_authority,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"
DOUBLE_PLAY_MD = RUNBOOKS / "double_play.md"
SPECIALISTS_MD = RUNBOOKS / "double_play_specialists.md"
AUTHORITY_MAP = REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"

PACKAGE_MARKER = "DRIFT_B03_OPS_DOUBLE_PLAY_AUTHORITY_MARKERS_V0=true"

# Canonical marker set projected into ops runbooks (docs-only consumers).
CANONICAL_OPS_AUTHORITY_MARKERS: frozenset[str] = frozenset(
    {
        OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
    }
)

# Phrases that reintroduce the B-03 docs drift (specialists falsely "missing").
BANNED_DRIFT_PHRASES: tuple[str, ...] = (
    "Next (not implemented here)",
    "Specialist interfaces + portfolio selector",
)

# Forbidden authority-grant language in these runbooks.
FORBIDDEN_AUTHORITY_GRANTS: tuple[str, ...] = (
    "live trading authorized",
    "orders authorized",
    "authoritative decision owner",
    "grants live",
    "unlocks execution",
    "ZERO_ORDER_RUNTIME_READY=true",
    "MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED=true",
)

# Direct drift: inventing a second ops authority label outside the boundary owner.
FORBIDDEN_DIVERGENT_AUTHORITY_LABELS: tuple[str, ...] = (
    "OPS_AUTHORITATIVE",
    "CANONICAL_AUTHORITATIVE",
    "LIVE_AUTHORITATIVE",
    "RUNTIME_AUTHORITATIVE",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", [DOUBLE_PLAY_MD, SPECIALISTS_MD])
def test_ops_runbooks_contain_legacy_non_authoritative_marker(path: Path) -> None:
    text = _read(path)
    assert OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY == "LEGACY_NON_AUTHORITATIVE"
    assert classify_ops_evaluate_double_play_authority() == OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY
    assert OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY in text
    assert "LEGACY_NON_AUTHORITATIVE" in text


@pytest.mark.parametrize("path", [DOUBLE_PLAY_MD, SPECIALISTS_MD])
def test_ops_runbooks_crosslink_slice_e_authority_map(path: Path) -> None:
    text = _read(path)
    assert "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md" in text
    assert "Slice E" in text
    assert AUTHORITY_MAP.is_file()
    map_text = _read(AUTHORITY_MAP)
    assert "Slice E authority boundary" in map_text
    assert OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY in map_text


@pytest.mark.parametrize("path", [DOUBLE_PLAY_MD, SPECIALISTS_MD])
def test_ops_runbooks_reference_boundary_and_canonical_offline_owners(path: Path) -> None:
    text = _read(path)
    assert "evaluate_double_play_authority_boundary_v0" in text
    assert "double_play_composition_matrix_v1" in text
    assert "annotation-only" in text.lower() or "non-authorizing" in text.lower()
    # Boundary owner module path fragment must appear (docs projection of SSOT).
    assert EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_OWNER.split(".")[-1] in text
    assert CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER.split(".")[-1] in text


def test_double_play_md_removes_false_not_implemented_specialist_claim() -> None:
    text = _read(DOUBLE_PLAY_MD)
    for phrase in BANNED_DRIFT_PHRASES:
        assert phrase not in text, f"stale drift phrase still present: {phrase!r}"
    assert "src/ops/double_play/specialists.py" in text or "specialists.py" in text


@pytest.mark.parametrize("path", [DOUBLE_PLAY_MD, SPECIALISTS_MD])
def test_ops_runbooks_fail_closed_no_authority_grants(path: Path) -> None:
    text = _read(path).lower()
    for phrase in FORBIDDEN_AUTHORITY_GRANTS:
        assert phrase.lower() not in text, f"forbidden grant language: {phrase!r}"
    # Frozen non-activation flags must remain false in code owner.
    assert MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED == "false"
    assert ZERO_ORDER_RUNTIME_READY == "false"
    assert LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE in (
        "LEGACY_NON_AUTHORITATIVE_ANNOTATION_ONLY",
        "PROJECTION_DIAGNOSTIC_ONLY",
    )


@pytest.mark.parametrize("path", [DOUBLE_PLAY_MD, SPECIALISTS_MD])
def test_ops_runbooks_no_divergent_direct_authority_mappings(path: Path) -> None:
    text = _read(path)
    for label in FORBIDDEN_DIVERGENT_AUTHORITY_LABELS:
        assert label not in text, f"divergent authority label: {label!r}"
    # Only the canonical ops marker from the boundary owner may appear as the
    # primary authority classification token for the ops evaluator.
    assert text.count(OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY) >= 1


def test_unknown_marker_projection_is_fail_closed() -> None:
    """Docs consumers must not invent markers; unknown tokens are rejected here."""
    known = CANONICAL_OPS_AUTHORITY_MARKERS
    unknown = "TOTALLY_UNKNOWN_AUTHORITY_MARKER_XYZ"
    assert unknown not in known
    for path in (DOUBLE_PLAY_MD, SPECIALISTS_MD):
        text = _read(path)
        assert unknown not in text
    with pytest.raises(AssertionError):
        assert unknown in known


def test_package_marker_stable() -> None:
    assert PACKAGE_MARKER.startswith("DRIFT_B03_")
    assert "AUTHORITY_MARKERS" in PACKAGE_MARKER

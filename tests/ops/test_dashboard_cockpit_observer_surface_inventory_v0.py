"""Offline characterization tests for Dashboard/Cockpit observer surfaces.

These tests pin the docs-only observer inventory posture as a read-only review
surface. They intentionally do not inspect dashboard runtime state, generated
artifacts, paper/live/testnet artifacts, or modify report/cockpit behavior.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OBSERVER_INVENTORY = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md"
)
OPERATOR_AUDIT_INDEX = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md"
)
SESSION_REVIEW_PACK = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md"
)
SYSTEM_DATAFLOW_AI = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md"
)
CI_SAFETY_GATE_POINTER = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md"
)


def read_plain(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def observer_text() -> str:
    return read_plain(OBSERVER_INVENTORY)


def combined_observer_reference_text() -> str:
    return "\n".join(
        read_plain(path)
        for path in [
            OBSERVER_INVENTORY,
            OPERATOR_AUDIT_INDEX,
            SESSION_REVIEW_PACK,
            SYSTEM_DATAFLOW_AI,
            CI_SAFETY_GATE_POINTER,
        ]
    )


def test_observer_inventory_file_exists_and_has_expected_title_and_frontmatter() -> None:
    assert OBSERVER_INVENTORY.exists()

    raw = OBSERVER_INVENTORY.read_text(encoding="utf-8")
    assert "# Master V2 Dashboard / Cockpit / Observer Surface Inventory V0" in raw
    assert "docs_token: DOCS_TOKEN_MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0" in raw
    assert "scope: docs-only" in raw


def test_observer_inventory_references_observer_report_concepts() -> None:
    text = observer_text().lower()

    expected_terms = [
        "dashboard",
        "cockpit",
        "observer",
        "report",
    ]

    for term in expected_terms:
        assert term in text


def test_observer_inventory_preserves_protected_authority_boundaries() -> None:
    text = combined_observer_reference_text().lower()

    expected_terms = [
        "master v2",
        "double play",
        "risk/killswitch",
        "execution/live gates",
    ]

    assert sum(term in text for term in expected_terms) >= 3


def test_observer_inventory_references_related_review_surfaces() -> None:
    """Cross-links: operator index cites session/CI; observer cites system dataflow."""
    text = combined_observer_reference_text()

    expected_anchors = [
        "DOCS_TOKEN_MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0",
        "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
        "MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md",
        "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md",
    ]

    for anchor in expected_anchors:
        assert anchor in text


def test_referenced_core_files_exist() -> None:
    for path in [
        OBSERVER_INVENTORY,
        OPERATOR_AUDIT_INDEX,
        SESSION_REVIEW_PACK,
        SYSTEM_DATAFLOW_AI,
        CI_SAFETY_GATE_POINTER,
    ]:
        assert path.exists(), path


def test_observer_inventory_has_read_only_non_authorizing_language() -> None:
    text = combined_observer_reference_text().lower()

    required_terms = [
        "non-authorizing",
        "read-only",
        "not order authority",
    ]

    assert any(term in text for term in required_terms)
    assert "not live authorization" in text or "not trading authority" in text


def test_observer_inventory_has_no_positive_authority_claims() -> None:
    """Negated editorial lines still contain substrings; block rare success phrases only."""
    text = combined_observer_reference_text().lower()

    forbidden_editorial_claims = [
        "live authorization granted",
        "strategies are cleared for live",
        "you may enable live trading",
        "trading is authorized",
        "go live now",
        "ready for live without gates",
    ]

    for claim in forbidden_editorial_claims:
        assert claim not in text


def test_dashboard_cockpit_is_observer_not_order_authority() -> None:
    text = combined_observer_reference_text().lower()

    assert "dashboard" in text
    assert "cockpit" in text
    assert "observer" in text
    assert "not order authority" in text or "does not place" in text
    assert "order authority" in text or "dashboard/cockpit authority" in text


def test_characterization_tests_do_not_read_generated_or_runtime_artifacts() -> None:
    this_file = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "execution_events" + "/sessions",
        "live_session" + "_registry",
        "paper" + "_" + "trading",
        "historical" + "_" + "run",
        "testnet" + "_" + "artifact",
        "src/trading/" + "master_v2",
        "src/ops/" + "double_play",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in this_file

"""Offline characterization tests for Paper/Testnet readiness gap-map surfaces.

These tests pin the docs-only gap map posture as a review and evidence surface.
They intentionally do not read generated outputs, paper/live/testnet artifacts,
or modify workflows, risk, execution, live, or report behavior.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GAP_MAP = REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md"

REQUIRED_TEXT_ANCHORS = [
    "MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0.md",
    "MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md",
    "MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md",
    "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
    "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
    "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md",
    "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md",
    "MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0.md",
    "RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md",
]

# Avoid false positives on negated phrasing in the spec (e.g. "not gate passage").
_BANNED_STANDALONE_CLAIMS = [
    "live authorization granted",
    "approved for live trading",
    "strategy is ready for live",
    "autonomous-ready for trading",
    "externally authorized for trading",
    "this map authorizes",
]


def gap_map_text() -> str:
    return GAP_MAP.read_text(encoding="utf-8")


def plain_text() -> str:
    text = gap_map_text()
    text = text.replace("&#47;", "/")
    text = re.sub(r"[`*]", "", text)
    return text


def test_gap_map_file_exists_and_has_expected_title_and_frontmatter() -> None:
    assert GAP_MAP.exists()

    text = gap_map_text()
    assert "# Master V2 Paper / Testnet Readiness Gap Map V0" in text
    assert "docs_token: DOCS_TOKEN_MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0" in text
    assert "scope: docs-only" in text
    assert "non-authorizing" in text


def test_gap_map_references_required_review_anchors() -> None:
    text = plain_text()

    for anchor in REQUIRED_TEXT_ANCHORS:
        assert anchor in text


def test_referenced_core_files_exist() -> None:
    expected_paths = [
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0.md",
        REPO_ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_gap_map_has_expected_table_headers() -> None:
    text = gap_map_text()

    assert "| Surface | Path | Type | Observes / supports | Consumer | Not used for |" in text
    assert "| **Surface** | **May** **(informational)** | **Must** **not**" in text


def test_gap_map_has_non_authorizing_language() -> None:
    text = plain_text().lower()

    required_phrases = [
        "non-authorizing",
        "not live authorization",
        "not approval",
        "not live enablement",
        "not order authority",
    ]

    for phrase in required_phrases:
        assert phrase in text

    # Executive summary: explicit negation list (phrasing may not use every
    # "not <noun> <noun>" pair as a single contiguous substring).
    assert "not imply" in text
    assert "strategy readiness" in text
    assert "autonomy readiness" in text
    assert "gate passage" in text


def test_gap_map_has_no_positive_authority_claims() -> None:
    text = plain_text().lower()

    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in text

    for needle in (
        "not live authorization",
        "not live enablement",
        "not imply",
    ):
        assert needle in text


def test_authority_boundaries_cover_expected_surfaces() -> None:
    text = plain_text().lower()

    expected_surfaces = [
        "paper run",
        "testnet run",
        "shadow run",
        "bounded pilot surface",
        "readiness summary",
        "ci/workflow result",
        "report/read-model",
        "session review pack",
    ]

    for surface in expected_surfaces:
        assert surface in text


def test_safe_followups_avoid_premature_artifact_and_gate_changes() -> None:
    text = plain_text().lower()

    assert "safe follow-up candidates" in text
    assert "avoid" in text and "premature" in text and "follow-ons" in text
    assert "reading" in text and "modifying" in text and "historical" in text
    assert "paper" in text and "test" in text and "artifacts" in text
    assert "changing" in text and "paper" in text and "testnet" in text
    assert "workflows" in text
    assert "changing" in text and "risk" in text and "killswitch" in text
    assert "changing" in text and "execution" in text and "live" in text and "gates" in text
    assert "binding" in text and "session" in text and "review" in text
    assert "pack" in text and "real" in text and "session" in text
    assert "mandate" in text


def test_characterization_source_avoids_synthetic_artifact_path_literals() -> None:
    """Forbid a few sensitive path shibboleths in this source; build with concat."""
    this_file = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "execution_events" + "/sessions",
        "live_session" + "_registry",
        "paper" + "_" + "trading",
        "historical" + "_" + "run",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in this_file

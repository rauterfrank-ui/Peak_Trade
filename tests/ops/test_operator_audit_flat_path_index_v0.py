"""Offline characterization tests for the Operator/Audit Flat Path Index.

These tests pin the docs-only flat path index posture as a navigation and
review surface. They intentionally do not read generated outputs, paper/live or
testnet artifacts, or modify workflows, risk, execution, live, or report
behavior.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FLAT_PATH_INDEX = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md"
)

REQUIRED_TEXT_ANCHORS = [
    "MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0.md",
    "MASTER_V2_OPERATOR_HANDOFF_SURFACE_MAP_V0.md",
    "MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md",
    "MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md",
    "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md",
    "MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md",
    "MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md",
    "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
    "RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md",
    "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
    "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md",
    "MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0.md",
    "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md",
    "MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md",
    "MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md",
    "MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md",
    "MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md",
    "MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md",
]

_BANNED_STANDALONE_CLAIMS = [
    "live authorization granted",
    "approved for live trading",
    "strategy is ready for live",
    "autonomous-ready for trading",
    "externally authorized for trading",
    "this index authorizes",
]


def flat_path_text() -> str:
    return FLAT_PATH_INDEX.read_text(encoding="utf-8")


def plain_text() -> str:
    text = flat_path_text()
    text = text.replace("&#47;", "/")
    text = re.sub(r"[`*]", "", text)
    return text


def test_flat_path_index_file_exists_and_has_expected_title_and_frontmatter() -> None:
    assert FLAT_PATH_INDEX.exists()

    text = flat_path_text()
    assert "# Master V2 Operator / Audit Flat Path Index V0" in text
    assert "docs_token: DOCS_TOKEN_MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0" in text
    assert "scope: docs-only" in text
    assert "non-authorizing" in text


def test_flat_path_index_references_required_review_anchors() -> None:
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
        / "MASTER_V2_VISUAL_LEARNING_EVIDENCE_REFERENCE_CHAIN_POINTER_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
        REPO_ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md",
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
        / "MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_flat_path_index_has_expected_table_headers() -> None:
    text = flat_path_text()

    assert (
        "| **Order** | **Open** **this** **file** | **Use** **when** | **Then** **open** | **Not** **used** **for** |"
        in text
    )
    assert "| **Question** | **Open** **first** | **Then** **open** |" in text
    assert "| **Surface** | **May** **(informational)** | **Must** **not**" in text


def test_flat_path_index_has_non_authorizing_language() -> None:
    text = plain_text().lower()

    required_phrases = [
        "non-authorizing",
        "not live authorization",
        "not runtime source of truth",
        "not trading authority",
        "not approve",
    ]

    for phrase in required_phrases:
        assert phrase in text

    assert "strategy readiness" in text
    assert "autonomy readiness" in text
    assert "not imply" in text or "not" in text


def test_flat_path_index_has_no_positive_authority_claims() -> None:
    text = plain_text().lower()

    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in text

    for needle in (
        "not live authorization",
        "no live enablement",
        "navigation aid only",
    ):
        assert needle in text


def test_authority_boundaries_cover_expected_surfaces() -> None:
    text = plain_text().lower()

    expected_surfaces = [
        "triage checklist",
        "handoff map",
        "evidence/registry index",
        "session review pack",
        "ci/safety pointer",
        "backtest inventory",
        "paper/testnet gap map",
        "strategy map",
        "ai/dataflow overview",
    ]

    for surface in expected_surfaces:
        assert surface in text


def test_flat_path_routes_cover_expected_domains() -> None:
    text = plain_text().lower()

    expected_routes = [
        "evidence / registry / provenance route",
        "session review pack route",
        "ci / safety gate route",
        "backtest / robustness route",
        "paper / testnet route",
        "strategy / learning / ai route",
    ]

    for route in expected_routes:
        assert route in text


def test_characterization_source_avoids_synthetic_artifact_path_literals() -> None:
    this_file = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "execution_events" + "/sessions",
        "live_session" + "_registry",
        "paper" + "_" + "trading",
        "historical" + "_" + "run",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in this_file

"""Offline characterization tests for Backtest Robustness inventory surfaces.

These tests pin the docs-only inventory posture as a review and evidence
surface. They intentionally do not read generated outputs, paper/live artifacts,
or modify backtest, strategy, risk, execution, or live behavior.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0.md"
)

REQUIRED_TEXT_ANCHORS = [
    "docs/BACKTEST_ENGINE.md",
    "src/risk_layer/var_backtest",
    "MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md",
    "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md",
    "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
    "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
]

# Phrases the inventory would not use as *affirmative* authority (avoid false
# positives on negated boilerplate like "not gate passage").
_BANNED_STANDALONE_CLAIMS = [
    "live authorization granted",
    "approved for live trading",
    "strategy is ready for live",
    "autonomous-ready for trading",
    "externally authorized for trading",
    "this inventory authorizes",
]


def inventory_text() -> str:
    return INVENTORY.read_text(encoding="utf-8")


def plain_text() -> str:
    text = inventory_text()
    text = text.replace("&#47;", "/")
    text = re.sub(r"[`*]", "", text)
    return text


def test_inventory_file_exists_and_has_expected_title_and_frontmatter() -> None:
    assert INVENTORY.exists()

    text = inventory_text()
    assert "# Master V2 Backtest Robustness / Statistical Validation Surface Inventory V0" in text
    assert (
        "docs_token: DOCS_TOKEN_MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0"
        in text
    )
    assert "scope: docs-only" in text
    assert "non-authorizing" in text


def test_inventory_references_required_backtest_validation_anchors() -> None:
    text = plain_text()

    for anchor in REQUIRED_TEXT_ANCHORS:
        assert anchor in text


def test_referenced_core_files_and_directories_exist() -> None:
    expected_paths = [
        REPO_ROOT / "docs" / "BACKTEST_ENGINE.md",
        REPO_ROOT / "src" / "risk_layer" / "var_backtest",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_inventory_has_expected_table_headers() -> None:
    text = inventory_text()

    assert "| Surface | Path | Type | Observes / validates | Consumer | Not used for |" in text
    assert "| Surface | **May** (informational) | **Must** **not**" in text


def test_inventory_has_non_authorizing_language() -> None:
    text = plain_text().lower()

    required_phrases = [
        "non-authorizing",
        "not live authorization",
        "not strategy readiness",
        "not autonomy readiness",
        "not external authority",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_inventory_has_no_positive_authority_claims() -> None:
    text = plain_text().lower()

    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in text

    # Executive summary: explicit negation chain for live/strategy/gate/authority
    text_full = text
    for needle in (
        "not strategy readiness",
        "not live readiness",
        "not gate passage",
    ):
        assert needle in text_full


def test_authority_boundaries_cover_expected_surfaces() -> None:
    text = plain_text().lower()

    # §11 + adjacent inventory coverage (phrasing matches doc, not a literal
    # "robustness result" row label).
    assert "backtest" in text and "result" in text
    assert "robustness" in text
    assert "statistical" in text and "validation" in text
    assert "metrics" in text
    assert "report" in text
    assert "strategy" in text
    assert "portfolio" in text
    assert "learning loop" in text
    assert "session review" in text
    # Registry / SRP are adjacent surfaces (§9); ensure ties remain doc-visible
    assert "registry" in text
    assert "evidence" in text


def test_safe_followups_avoid_premature_runtime_or_live_artifact_use() -> None:
    text = plain_text().lower()

    assert "safe follow-up candidates" in text
    assert "avoid" in text
    assert "premature" in text
    assert "follow-ons" in text
    assert "paper" in text and "live" in text and "artifacts" in text
    assert "changing" in text and "backtest" in text
    assert "governance" in text
    # Cross-section guardrails: risk / execution (must remain explicit in the doc)
    assert "killswitch" in text
    assert "execution" in text and "gates" in text


def test_characterization_tests_do_not_read_generated_or_paper_live_artifacts() -> None:
    """This test file must not open operator paths; fragments built so literals do not
    embed the exact combined strings (avoids a trivial self-false-positive).
    """
    this_file = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "execution_events" + "/sessions",
        "live_session" + "_registry",
        "paper" + "_" + "trading",
        "historical" + "_" + "run",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in this_file

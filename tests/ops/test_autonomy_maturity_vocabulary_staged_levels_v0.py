"""Offline characterization tests for autonomy maturity vocabulary surfaces.

These tests pin existing autonomy/staged-autonomy docs as review and vocabulary
surfaces only. They intentionally do not inspect runtime state, generated
artifacts, paper/live/testnet artifacts, or modify trading behavior.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VISUAL_REFERENCE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md"
)
SYSTEM_DATAFLOW_AI = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md"
)
LEARNING_LOOP_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md"
)
PAPER_TESTNET_GAP_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md"
)
CI_SAFETY_GATE_POINTER = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md"
)
SESSION_REVIEW_PACK = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md"
)
OPERATOR_AUDIT_INDEX = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md"
)


def read_plain(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def combined_autonomy_reference_text() -> str:
    return "\n".join(
        read_plain(path)
        for path in [
            VISUAL_REFERENCE,
            SYSTEM_DATAFLOW_AI,
            LEARNING_LOOP_MAP,
            PAPER_TESTNET_GAP_MAP,
            CI_SAFETY_GATE_POINTER,
            SESSION_REVIEW_PACK,
            OPERATOR_AUDIT_INDEX,
        ]
    )


def test_autonomy_reference_docs_exist() -> None:
    for path in [
        VISUAL_REFERENCE,
        SYSTEM_DATAFLOW_AI,
        LEARNING_LOOP_MAP,
        PAPER_TESTNET_GAP_MAP,
        CI_SAFETY_GATE_POINTER,
        SESSION_REVIEW_PACK,
        OPERATOR_AUDIT_INDEX,
    ]:
        assert path.exists(), path


def test_autonomy_surfaces_reference_future_target_not_current_authorization() -> None:
    text = combined_autonomy_reference_text().lower()

    assert "autonomy" in text or "autonomous" in text
    assert "future" in text or "target" in text
    assert "not autonomy readiness" in text or "not current autonomous execution" in text
    assert "not live authorization" in text


def test_autonomy_surfaces_reference_staged_progression_terms() -> None:
    text = combined_autonomy_reference_text().lower()

    expected_terms = [
        "research",
        "shadow",
        "paper",
        "testnet",
        "bounded pilot",
        "gated",
    ]

    assert sum(term in text for term in expected_terms) >= 4


def test_autonomy_surfaces_reference_protected_boundaries() -> None:
    text = combined_autonomy_reference_text().lower()

    expected_terms = [
        "master v2",
        "double play",
        "risk/killswitch",
        "execution/live gates",
        "operator",
        "external authority",
    ]

    assert sum(term in text for term in expected_terms) >= 4


def test_autonomy_surfaces_have_non_authorizing_language() -> None:
    text = combined_autonomy_reference_text().lower()

    required_terms = [
        "non-authorizing",
        "not live authorization",
        "not approval",
    ]

    assert any(term in text for term in required_terms)


def test_autonomy_docs_do_not_make_unqualified_positive_authority_claims() -> None:
    """Negated forms in real specs can still contain substrings; block rare editorials only."""
    text = combined_autonomy_reference_text().lower()

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


def test_autonomy_maturity_is_review_vocabulary_not_live_enablement() -> None:
    text = combined_autonomy_reference_text().lower()

    assert "review" in text or "vocabulary" in text or "classification" in text
    assert "no live enablement" in text or "not live enablement" in text


def test_ai_and_dashboard_authority_boundaries_are_preserved() -> None:
    text = combined_autonomy_reference_text().lower()

    assert "trading authority" in text
    assert "dashboard" in text or "cockpit" in text
    assert "not order authority" in text or "dashboard/cockpit authority" in text


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

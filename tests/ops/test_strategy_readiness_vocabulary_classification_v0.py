"""Offline characterization tests for strategy readiness vocabulary surfaces.

These tests pin existing strategy docs as review/classification surfaces only.
They intentionally do not inspect strategy runtime state, generated artifacts,
paper/live/testnet artifacts, or modify trading behavior.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_SURFACE_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md"
)
VISUAL_REFERENCE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_VISUAL_ARCHITECTURE_AND_STRATEGY_REFERENCE_V0.md"
)
BACKTEST_INVENTORY = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_BACKTEST_ROBUSTNESS_VALIDATION_SURFACE_INVENTORY_V0.md"
)
REGISTRY_EVIDENCE_INDEX = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md"
)
LEARNING_LOOP_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md"
)


def read_plain(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def strategy_text() -> str:
    return read_plain(STRATEGY_SURFACE_MAP)


def combined_strategy_reference_text() -> str:
    return "\n".join(
        [
            read_plain(STRATEGY_SURFACE_MAP),
            read_plain(VISUAL_REFERENCE),
            read_plain(BACKTEST_INVENTORY),
            read_plain(REGISTRY_EVIDENCE_INDEX),
            read_plain(LEARNING_LOOP_MAP),
        ]
    )


def test_strategy_surface_docs_exist() -> None:
    for path in [
        STRATEGY_SURFACE_MAP,
        VISUAL_REFERENCE,
        BACKTEST_INVENTORY,
        REGISTRY_EVIDENCE_INDEX,
        LEARNING_LOOP_MAP,
    ]:
        assert path.exists(), path


def test_strategy_surface_map_is_present_and_strategy_focused() -> None:
    text = strategy_text().lower()

    assert "strategy" in text
    assert "master v2" in text
    assert "double play" in text


def test_strategy_surfaces_are_classification_or_review_not_live_authority() -> None:
    text = combined_strategy_reference_text().lower()

    required_phrases = [
        "not live authorization",
        "not strategy readiness",
        "not strategy approval",
    ]

    assert any(phrase in text for phrase in required_phrases)
    assert "review" in text or "classification" in text


def test_strategy_surfaces_reference_learning_evidence_or_backtest_context() -> None:
    text = combined_strategy_reference_text().lower()

    expected_contexts = [
        "learning loop",
        "evidence",
        "registry",
        "backtest",
        "robustness",
    ]

    for context in expected_contexts:
        assert context in text


def test_strategy_readiness_docs_have_non_authorizing_language() -> None:
    text = combined_strategy_reference_text().lower()

    required_terms = [
        "non-authorizing",
        "not live authorization",
        "not approval",
    ]

    assert any(term in text for term in required_terms)


def test_strategy_docs_do_not_make_unqualified_positive_authority_claims() -> None:
    """Spec files often negate risky substrings; use rare editorial-only phrases as blockers."""
    text = combined_strategy_reference_text().lower()

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


def test_strategy_status_language_includes_research_or_candidate_posture() -> None:
    text = combined_strategy_reference_text().lower()

    assert any(
        phrase in text
        for phrase in [
            "candidate",
            "research",
            "r&d",
            "reference",
            "status",
            "surface",
        ]
    )


def test_master_v2_double_play_boundary_is_referenced() -> None:
    text = combined_strategy_reference_text().lower()

    assert "master v2" in text
    assert "double play" in text
    assert "bull" in text or "bear" in text


def test_characterization_tests_do_not_read_generated_or_runtime_artifacts() -> None:
    this_file = Path(__file__).read_text(encoding="utf-8")

    # Built via concatenation so this file does not embed literal full path fragments
    # (see tests/ops/test_operator_audit_flat_path_index_v0.py).
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

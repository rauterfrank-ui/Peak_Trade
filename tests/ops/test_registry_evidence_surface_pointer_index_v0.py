"""Offline characterization tests for Registry / Evidence pointer surfaces.

These tests intentionally do not read real session, paper, or live data, or
generated content under the repository ``out`` tree. They pin the docs-only
pointer/index posture as a navigation and review surface, not an authority
surface.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POINTER_INDEX = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0.md"
)

# Substrings that must appear in the pointer index (as authored; paths use &#47; or rel links).
REQUIRED_ANCHORS = [
    "../EVIDENCE_INDEX.md",
    "../../audit/EVIDENCE_INDEX.md",
    "../registry/",
    "../evidence/",
    "MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md",
    "MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md",
    "MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md",
    "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
    "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
    "RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md",
    "scripts/ops/verify_from_registry.sh",
    "scripts/report_live_sessions.py",
    "tests/ops/test_session_review_pack_report_contracts_v0.py",
    "tests/ops/test_session_review_pack_precedence_synthetic_v0.py",
    "tests/ci/test_required_checks_safety_gate_surfaces_v0.py",
]


def pointer_text() -> str:
    return POINTER_INDEX.read_text(encoding="utf-8")


def plain_text() -> str:
    """Strip markdown emphasis/backticks; keep underscores in filenames (EVIDENCE_INDEX)."""
    text = pointer_text()
    text = text.replace("&#47;", "/")
    text = text.replace("**", "")
    text = text.replace("`", "")
    return text


def test_pointer_index_file_exists_and_has_expected_title() -> None:
    assert POINTER_INDEX.is_file()

    text = pointer_text()
    assert "# Master V2 Registry / Evidence Surface Pointer Index V0" in text
    assert "docs_token: DOCS_TOKEN_MASTER_V2_REGISTRY_EVIDENCE_SURFACE_POINTER_INDEX_V0" in text


def test_pointer_index_references_required_registry_evidence_anchors() -> None:
    text = plain_text()

    for anchor in REQUIRED_ANCHORS:
        assert anchor in text, f"missing anchor: {anchor!r}"


def test_referenced_core_files_and_directories_exist() -> None:
    expected_paths = [
        REPO_ROOT / "docs" / "ops" / "EVIDENCE_INDEX.md",
        REPO_ROOT / "docs" / "audit" / "EVIDENCE_INDEX.md",
        REPO_ROOT / "docs" / "ops" / "registry",
        REPO_ROOT / "docs" / "ops" / "evidence",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_EVIDENCE_PACKET_AND_INDEX_NAVIGATION_MAP_V0.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md",
        REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
        REPO_ROOT
        / "docs"
        / "ops"
        / "specs"
        / "MASTER_V2_SESSION_REVIEW_PACK_EVIDENCE_PROVENANCE_PRECEDENCE_V0.md",
        REPO_ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_SESSION_REVIEW_PACK_INVOKE_V0.md",
        REPO_ROOT / "scripts" / "ops" / "verify_from_registry.sh",
        REPO_ROOT / "scripts" / "report_live_sessions.py",
        REPO_ROOT / "tests" / "ops" / "test_session_review_pack_report_contracts_v0.py",
        REPO_ROOT / "tests" / "ops" / "test_session_review_pack_precedence_synthetic_v0.py",
        REPO_ROOT / "tests" / "ci" / "test_required_checks_safety_gate_surfaces_v0.py",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_pointer_index_has_expected_table_headers() -> None:
    text = pointer_text()

    assert "| Surface | Path | Type | Read when | Consumer | Not used for |" in text
    assert (
        "| Candidate | Source class | Why useful | Risk | Required tests | Recommendation |" in text
    )


def test_pointer_index_has_non_authorizing_language() -> None:
    text = plain_text().lower()

    required_phrases = [
        "non-authorizing",
        "not live authorization",
        "not signoff",
        "not autonomy readiness",
        "not real data binding",  # Session Review Pack synthetic test row
    ]

    for phrase in required_phrases:
        assert phrase in text, f"missing non-authority phrase: {phrase!r}"


def test_pointer_index_has_no_positive_authority_claims() -> None:
    text = plain_text().lower()

    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "strategy ready",
        "autonomy ready",
        "autonomous-ready",
        "externally authorized",
        "trade approved",
        "approved for live",
    ]

    for claim in forbidden_claims:
        assert claim not in text


def test_safe_binding_section_does_not_make_real_binding_current_behavior() -> None:
    t = plain_text().lower()

    assert "read-only" in t and "non-authorizing" in t and "v0" in t
    assert "does not" in t and "bind" in t and "real" in t and "session" in t
    assert "do not" in t and "bind" in t and "real" in t
    assert "or live" in t  # spec: real * or live * (non-authorizing binding warning)


def test_authority_boundaries_cover_registry_evidence_session_pack_and_ai() -> None:
    t = plain_text().lower()

    for phrase in (
        "registry",
        "evidence index",
        "provenance",
        "readiness",
        "session",
        "review",
        "pack",
        "dashboard",
        "observer",
        "ai summary",
    ):
        assert phrase in t, f"expected {phrase!r} in authority table context"


def test_tests_do_not_read_out_ops_or_historical_run_artifacts() -> None:
    this_file = Path(__file__).read_text(encoding="utf-8")
    ops_out = "out" + "/" + "ops"
    ops_encoded = "out" + "&#47;" + "ops"
    for path_fragment in (ops_out, ops_encoded):
        assert path_fragment not in this_file

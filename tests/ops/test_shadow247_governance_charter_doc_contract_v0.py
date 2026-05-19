"""Contract tests for Shadow-247 Governance Charter v0 (read-only doc anchors, no runtime)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHARTER = REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
PREFLIGHT_NAME = "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"

# PR #3560: Status-and-scope clarification block (documentary 24h bounded tier only).
EVIDENCE_SEMANTICS_HEADING_V0 = (
    "**24h bounded Shadow dry-run candidate — evidence semantics (non-authorizing):**"
)

_FORBIDDEN_PROMOTION_PHRASES_V0: tuple[str, ...] = (
    "testnet approved",
    "live ready",
    "go-live approved",
    "broker ready",
    "order ready",
    "production trading validated",
    "execution authorized",
    "charter ready",
    "preflight unblocked",
)


def _evidence_semantics_paragraph_v0() -> str:
    """Return the #3560 evidence-semantics paragraph in Status and scope (read-only)."""
    text = _read()
    assert EVIDENCE_SEMANTICS_HEADING_V0 in text, (
        "missing 24h evidence semantics heading (PR #3560 regression?)"
    )
    start = text.index(EVIDENCE_SEMANTICS_HEADING_V0)
    end = text.find("\n\n---", start)
    assert end != -1, "expected evidence-semantics paragraph terminated by blank line + ---"
    return text[start:end]


EXPECTED_HEADINGS: tuple[str, ...] = (
    "## Status and scope",
    "## Boundary statements (non-negotiable semantics)",
    "## Activation ladder",
    "## Explicit next-state",
    "## Document control",
)


def _read() -> str:
    assert CHARTER.is_file(), f"missing canonical charter: {CHARTER}"
    return CHARTER.read_text(encoding="utf-8")


def test_shadow247_governance_charter_doc_exists_v0() -> None:
    assert CHARTER.is_file()


def test_shadow247_governance_charter_doc_has_stable_outline_v0() -> None:
    text = _read()
    for heading in EXPECTED_HEADINGS:
        assert heading in text, f"missing section heading {heading!r}"


def test_shadow247_governance_charter_doc_states_non_authorizing_posture_v0() -> None:
    text = _read()
    assert "`not_ready`" in text
    assert "**STOP_IDLE**" in text
    assert "**non-authorizing**" in text
    assert "planning only" in text
    assert "governance and activation-path **planning only**" in text


def test_shadow247_governance_charter_doc_forbids_runtime_authority_paths_v0() -> None:
    text = _read()
    lowered = text.lower()
    for phrase in (
        "testnet",
        "live",
        "broker",
        "exchange",
        "order submission",
        "daemon operation",
        "scheduler execution",
    ):
        assert phrase in lowered, f"expected boundary mention of {phrase!r}"
    assert "**It does not:**" in text
    assert "approve bounded Shadow smoke" in text


def test_shadow247_governance_charter_doc_forbids_runtime_authorization_payloads_v0() -> None:
    text = _read()
    assert '"activation_authorized": true' not in text
    assert '"activation_authorized":true' not in text


def test_shadow247_governance_charter_doc_links_preflight_not_parallel_owner_v0() -> None:
    text = _read()
    assert f"]({PREFLIGHT_NAME})" in text
    assert PREFLIGHT_NAME in text
    assert "**does not replace** the preflight contract" in text
    assert "do not fork parallel" in text


def test_shadow247_governance_charter_doc_rejects_duplicate_approval_surfaces_v0() -> None:
    text = _read()
    assert "**Docs ≠ Approval**" in text
    assert "**Evidence ≠ Approval**" in text
    assert "**Dashboard ≠ Approval**" in text
    assert "EVIDENCE_INDEX" not in text
    assert "HANDOFF" not in text


def test_shadow247_governance_charter_doc_does_not_name_notion_as_authority_v0() -> None:
    assert "notion" not in _read().lower()


def test_shadow247_governance_charter_doc_references_shadow247_bounded_test_anchors_v0() -> None:
    text = _read()
    assert "Shadow-247" in text
    assert "24h" in text
    assert "test_offline_crosslink_invariant_contract_v0.py" in text
    assert "test_shadow_247_futures_config_job_skeleton_v0.py" in text


def test_shadow247_governance_charter_doc_stage_zero_is_stop_idle_v0() -> None:
    text = _read()
    assert "### Stage 0 — STOP_IDLE / blocked (current)" in text
    assert "preflight **BLOCKED**" in text


def test_shadow247_governance_charter_doc_24h_evidence_semantics_regression_v0() -> None:
    """Regression anchor for PR #3560 — documentary bounded tier only; no gate lift."""
    p = _evidence_semantics_paragraph_v0()
    assert "**documentary machine-readable evidence** only" in p
    assert "**24h candidate tier**" in p
    assert "duration-capped local simulation" in p
    assert "dry-run only" in p
    assert PREFLIGHT_NAME in p
    assert "it **does not** satisfy the blocked" in p
    assert "status remains **BLOCKED**" in p
    assert "away from **`not_ready`**" in p
    for denial in (
        "**does not** authorize Testnet",
        "daemon operation",
        "scheduler execution",
    ):
        assert denial in p, f"missing denial fragment {denial!r}"
    assert "Canonical gate definitions remain in **this repository**" in p
    assert "notion" not in p.lower()


def test_shadow247_governance_charter_doc_forbidden_promotion_phrases_absent_v0() -> None:
    """No accidental approval / readiness wording in the charter document."""
    lowered = _read().lower()
    for phrase in _FORBIDDEN_PROMOTION_PHRASES_V0:
        assert phrase not in lowered, f"forbidden promotion phrase present: {phrase!r}"

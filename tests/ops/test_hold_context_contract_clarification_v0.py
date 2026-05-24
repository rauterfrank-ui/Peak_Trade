"""Static contract tests for hold_context conservative projection clarification v0."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
PREFLIGHT_REPORTER = REPO_ROOT / "scripts" / "ops" / "report_paper_shadow_247_preflight_status.py"

HOLD_CONTEXT_TOKENS = (
    "HOLD_CONTEXT_V0_CONSERVATIVE_PROJECTION=true",
    "ARCHIVE_OPERATOR_RECORD_TRACEABILITY_ONLY=true",
    "SCOPED_EXCEPTION_DOES_NOT_CLOSE_GLOBAL_HOLD=true",
    "PASS_BLOCKED_SAFE_DOES_NOT_CLEAR_HOLD=true",
)


def _hold_context_section() -> str:
    text = CANONICAL_OWNER.read_text(encoding="utf-8")
    start = text.index("## Unknown operator classification / HOLD context v0")
    end = text.index("## Operator decision record context v0 (optional)")
    return text[start:end]


def _operator_decision_section() -> str:
    text = CANONICAL_OWNER.read_text(encoding="utf-8")
    start = text.index("## Operator decision record context v0 (optional)")
    end = text.index("## 8. Revision")
    return text[start:end]


def test_hold_context_conservative_projection_subsection_exists() -> None:
    section = _hold_context_section()
    assert "Live projection (conservative by design)" in section
    for token in HOLD_CONTEXT_TOKENS:
        assert token in section


def test_hold_context_remains_unknown_projection_even_with_archive_records() -> None:
    section = _hold_context_section()
    collapsed = section.replace("**", "").replace("`", "")
    assert "unknown_hold_context.v0" in section
    assert "operator_classification=unknown" in section
    assert "do not mutate, override, or clear hold_context_v0" in collapsed
    assert "scoped_hold_with_exceptions" in section


def test_archive_operator_record_traceability_only() -> None:
    section = _operator_decision_section()
    collapsed = section.replace("**", "").replace("`", "")
    assert "traceability only" in collapsed
    assert "OPERATOR_HOLD_CLASSIFICATION_RECORD.txt" in section
    assert "does not change hold_context_v0" in collapsed


def test_scoped_exception_does_not_close_global_hold() -> None:
    hold = _hold_context_section().replace("**", "")
    op = _operator_decision_section().replace("**", "")
    assert "SCOPED_EXCEPTION_DOES_NOT_CLOSE_GLOBAL_HOLD=true" in hold
    assert "Global HOLD remains active" in hold
    assert "not global HOLD closure" in op


def test_pass_blocked_safe_does_not_clear_hold_cross_ref() -> None:
    section = _hold_context_section()
    collapsed = section.replace("**", "")
    assert "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE" in section
    assert "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE" in section
    assert "do not clear HOLD" in collapsed
    assert "GLB-015 §6.5" in section


def test_u3_cross_ref_non_duplicative() -> None:
    section = _hold_context_section()
    assert "§2a.1 U3 scoped preflight exception" in section


def test_reporter_hold_context_unchanged_with_scoped_hold_operator_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Archive scoped_hold operator record is traceability-only; hold_context stays conservative."""
    from tests.ops.test_report_paper_shadow_247_preflight_status_cli_v0 import (
        _assert_hold_context_v0,
        _materialize_minimal_preflight_repo,
    )

    for key in ("PT_INCIDENT_STOP", "PT_FORCE_NO_TRADE", "PT_ENABLED", "PT_ARMED"):
        monkeypatch.delenv(key, raising=False)
    _materialize_minimal_preflight_repo(tmp_path, include_scheduler_jobs=True)
    decision = tmp_path / "OPERATOR_HOLD_CLASSIFICATION_RECORD.txt"
    decision.write_text(
        "\n".join(
            [
                "OPERATOR_CLASSIFICATION=scoped_hold_with_exceptions",
                "CURRENT_STATE=HOLD_NO_PAPER_RUN",
                "GO_LIVE_NEXT_STEP=blocked",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops.report_paper_shadow_247_preflight_status import (
        build_paper_shadow_247_preflight_status,
    )

    payload = build_paper_shadow_247_preflight_status(
        tmp_path,
        operator_decision_record=decision,
    )
    ctx = payload["operator_decision_context_v0"]
    assert ctx["operator_classification"] == "scoped_hold_with_exceptions"
    assert ctx["non_authorizing"] is True
    assert ctx["permits_scheduler_runtime_paper_testnet_live"] is False
    _assert_hold_context_v0(payload)
    assert payload["status"] == "BLOCKED"
    assert payload["activation_authorized"] is False


def test_governance_outroot_clearance_doc_subsection_exists() -> None:
    text = (
        REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
    ).read_text(encoding="utf-8")
    assert "## Governance OUTROOT clearance evidence v0 (optional)" in text
    assert "governance_outroot_clearance_v0" in text
    assert "GOVERNANCE_OUTROOT_CLEARANCE_DOES_NOT_CLEAR_HOLD=true" in text


def test_docs_truth_map_records_hold_context_clarification_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "hold_context_v0 conservative projection" in text
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text

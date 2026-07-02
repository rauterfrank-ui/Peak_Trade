"""Contract tests for composite breakout confirmation vol-gated donchian v1 rejection closeout v0."""

from __future__ import annotations

import re
from pathlib import Path

from src.backtest import (
    step29m_composite_breakout_confirmation_vol_gated_donchian_v1_economic_evaluation_admissibility_contract_v1 as contract,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
CLOSEOUT_RECORD = (
    REPO_ROOT
    / "docs/governance/COMPOSITE_BREAKOUT_CONFIRMATION_VOL_GATED_DONCHIAN_V1_ARCHITECTURE_REJECTION_AND_RESEARCH_LINE_CLOSEOUT_V0.md"
)

FAILURE_DECOMPOSITION_EVIDENCE = Path(contract.FAILURE_DECOMPOSITION_EVIDENCE_REF)
OFFLINE_EVALUATION_EVIDENCE = Path(contract.OFFLINE_EVALUATION_EVIDENCE_REF)
ARCHITECTURE_RATIFICATION_EVIDENCE = Path(contract.ARCHITECTURE_RATIFICATION_EVIDENCE_REF)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(
        rf"\| `{re.escape(field)}` \| `([^`]*)`(?: <!--.*?-->)? \|",
        text,
    )
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _research_line_section(text: str) -> str:
    start = text.index(
        "#### RUNBOOK_RESEARCH_LINE — Composite Breakout Confirmation Vol-Gated Donchian v1"
    )
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_disposition_constants_match_ratified_closeout() -> None:
    assert contract.CANDIDATE_BINDING_ID == "composite_breakout_confirmation_vol_gated_donchian_v1"
    assert contract.ARCHITECTURE_HYPOTHESIS_FALSIFIED is True
    assert contract.ARCHITECTURE_REJECTED is True
    assert contract.RESEARCH_LINE_STATUS == "CLOSED_REJECTED"
    assert contract.ECONOMIC_VALIDITY_STATUS == "FAILED"
    assert contract.ECONOMIC_EVALUATION_VERDICT == "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL"
    assert contract.FINAL_RESEARCH_DISPOSITION == "REJECTED_CLOSED"
    assert contract.REJECTION_REASON == (
        "STRUCTURALLY_NEGATIVE_NET_EDGE_ACROSS_WALK_FORWARD_MONTE_CARLO_AND_STRESS"
    )
    assert contract.PROMOTION_ELIGIBLE is False
    assert contract.RETRY_ALLOWED is False
    assert contract.HOLDOUT_ALLOWED is False
    assert contract.PARAMETER_TUNING_ALLOWED is False
    assert contract.THRESHOLD_RELAXATION_ALLOWED is False


def test_research_line_closed_rejected_without_retry_or_promotion() -> None:
    section = _research_line_section(_read_registry())
    assert _field_value(section, "RESEARCH_LINE_STATUS") == "CLOSED_REJECTED"
    assert _field_value(section, "ARCHITECTURE_DISPOSITION") == "ARCHITECTURE_HYPOTHESIS_FALSIFIED"
    assert _field_value(section, "FINAL_RESEARCH_DISPOSITION") == "REJECTED_CLOSED"
    assert _field_value(section, "ECONOMIC_VALIDITY_STATUS") == "FAILED"
    assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
    assert _field_value(section, "RETRY_ALLOWED") == "false"
    assert _field_value(section, "HOLDOUT_ALLOWED") == "false"
    assert _field_value(section, "PARAMETER_TUNING_ALLOWED") == "false"
    assert _field_value(section, "THRESHOLD_RELAXATION_ALLOWED") == "false"
    assert _field_value(section, "DATASET_SUBSTITUTION_ALLOWED") == "false"
    assert _field_value(section, "PERIOD_SUBSTITUTION_ALLOWED") == "false"
    assert _field_value(section, "SHADOW_ELIGIBLE") == "false"
    assert _field_value(section, "PAPER_ELIGIBLE") == "false"
    assert _field_value(section, "TESTNET_ELIGIBLE") == "false"
    assert _field_value(section, "RUNTIME_ELIGIBLE") == "false"


def test_economic_evaluation_verdict_and_merge_commits_bound() -> None:
    section = _research_line_section(_read_registry())
    assert (
        _field_value(section, "ECONOMIC_EVALUATION_VERDICT")
        == "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL"
    )
    assert (
        _field_value(section, "FAILURE_DECOMPOSITION_VERDICT")
        == "ECONOMIC_VALIDITY_FAILURE_DECOMPOSITION_COMPLETE"
    )
    assert (
        _field_value(section, "ARCHITECTURE_BINDING_MERGE_COMMIT")
        == contract.ARCHITECTURE_BINDING_MERGE_COMMIT
    )
    assert (
        _field_value(section, "ECONOMIC_EVALUATION_MERGE_COMMIT")
        == contract.ECONOMIC_EVALUATION_MERGE_COMMIT
    )
    assert _field_value(section, "EVALUATION_ID") == "econ_evidence_eval_v1_d618bf84626619d6"


def test_no_pending_or_promising_status_language() -> None:
    section = _research_line_section(_read_registry())
    status = _field_value(section, "STATUS")
    assert status == "CLOSED_REJECTED"
    forbidden = ("PENDING", "PROMISING", "INCONCLUSIVE", "RETRYABLE", "BLOCKED")
    for token in forbidden:
        assert token not in status


def test_policy_convergence_no_new_candidate_hold() -> None:
    section = _research_line_section(_read_registry())
    assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
    assert _field_value(section, "EVALUATION_AUTHORIZED") == "false"
    assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
    assert _field_value(section, "RUNTIME_AUTHORIZED") == "false"
    assert _field_value(section, "STEP29N_PROMOTION_GATE_STATUS") == "FAIL_CLOSED_BLOCKED"
    assert _field_value(section, "STEP29R_RUNTIME_REWIRE_ADMISSIBLE") == "false"
    assert _field_value(section, "DOWNSTREAM_AUTHORITY_EFFECT") == "NONE"
    assert (
        _field_value(section, "NEXT_CANONICAL_STEP")
        == "NO_FURTHER_COMPOSITE_BREAKOUT_CONFIRMATION_VOL_GATED_DONCHIAN_V1_RESEARCH_ACTION_UNDER_NO_NEW_CANDIDATE_HOLD"
    )


def test_closeout_evidence_refs_bound() -> None:
    section = _research_line_section(_read_registry())
    assert str(FAILURE_DECOMPOSITION_EVIDENCE) in _field_value(
        section, "FAILURE_DECOMPOSITION_EVIDENCE_REF"
    )
    assert str(OFFLINE_EVALUATION_EVIDENCE) in _field_value(
        section, "OFFLINE_EVALUATION_EVIDENCE_REF"
    )
    assert str(ARCHITECTURE_RATIFICATION_EVIDENCE) in _field_value(
        section, "ARCHITECTURE_RATIFICATION_EVIDENCE_REF"
    )


def test_closeout_record_exists_and_matches_disposition() -> None:
    assert CLOSEOUT_RECORD.is_file(), f"missing: {CLOSEOUT_RECORD}"
    body = CLOSEOUT_RECORD.read_text(encoding="utf-8")
    assert "ARCHITECTURE_HYPOTHESIS_FALSIFIED" in body
    assert "CLOSED_REJECTED" in body
    assert "REJECTED_CLOSED" in body
    assert "NO_NEW_CANDIDATE_HOLD=ACTIVE" in body
    assert contract.CANDIDATE_BINDING_ID in body

"""Contract tests for STEP 29M fleet no-pass operator policy ratification closeout v0.

Verifies ratified NO_NEW_CANDIDATE_HOLD governance state without authorizing
promotion, runtime, economic evaluation, STEP29N reimplementation, or automatic
research continuation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
OPERATOR_DECISION_RECORD = (
    REPO_ROOT / "docs" / "governance" / "STEP29M_FLEET_NO_PASS_OPERATOR_POLICY_DECISION_V0.md"
)

CLOSEOUT_SLICE = (
    "step29m_fleet_no_pass_operator_policy_ratification_and_progress_registry_closeout_v0_slice"
)
PLANNING_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/bounded_step29m_no_pass_operator_policy_decision_preparation_read_only_v0_20260702T013118Z"
)
MA_CROSSOVER_EVAL_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic_evaluation/bounded_step29m_ma_crossover_v1_post_binding_fix_economic_evaluation_recovery_single_run_v0_20260702T012057Z"
)
MA_CROSSOVER_CLOSEOUT_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic_evaluation/bounded_step29m_ma_crossover_v1_economic_policy_fail_closeout_and_candidate_decision_read_only_v0_20260702T012719Z"
)


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


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_closeout_slice_registered_in_implemented_scope() -> None:
    text = _read_registry()
    scope = _field_value(text, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    assert CLOSEOUT_SLICE in scope.split(",")


def test_fleet_complete_no_pass_three_of_three_failed() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "STEP29M_FLEET_STATUS") == "COMPLETE_NO_PASS"
    assert _field_value(section, "STEP29M_RATIFIED_CANDIDATES_TOTAL") == "3"
    assert _field_value(section, "STEP29M_RATIFIED_CANDIDATES_PASSED") == "0"
    assert _field_value(section, "STEP29M_RATIFIED_CANDIDATES_FAILED") == "3"
    assert _field_value(section, "STEP29M_PENDING_CANDIDATES") == "0"
    assert _field_value(section, "STEP29M_PROMOTION_ELIGIBLE_CANDIDATES") == "0"
    assert _field_value(section, "COMPLETED_TECHNICALLY_VALID_EVALUATION_COUNT") == "3"
    assert _field_value(section, "ECONOMIC_POLICY_FAIL_COUNT") == "3"
    assert _field_value(section, "PROMOTION_ELIGIBLE_COUNT") == "0"


def test_ratified_no_new_candidate_hold() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "STEP29M_OPERATOR_POLICY_DECISION") == "NO_NEW_CANDIDATE_HOLD"
    assert _field_value(section, "STEP29M_OPERATOR_POLICY_RATIFIED") == "true"
    assert _field_value(section, "STEP29M_OPERATOR") == "Frank Rauter"
    assert (
        _field_value(section, "NEXT_CANONICAL_STEP")
        == "OPERATOR_POLICY_DECISION_REQUIRED_FOR_NEW_RESEARCH_SCOPE"
    )


def test_no_pending_candidates_or_automatic_continuation() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "POST_RATIFICATION_AUTHORIZED_PENDING_CANDIDATE_EXISTS") == "false"
    assert _field_value(section, "AUTHORIZED_PENDING_EVALUATION_COUNT") == "0"
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "NONE"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_STATUS") == "CLOSED_NO_PENDING_CANDIDATE"
    assert _field_value(section, "STEP29M_NEW_CANDIDATE_AUTHORIZED") == "false"
    assert (
        _field_value(section, "STEP29M_NEW_RESEARCH_SCOPE_REQUIRES_EXPLICIT_OPERATOR_RATIFICATION")
        == "true"
    )


def test_all_three_candidates_policy_fail_no_promotion() -> None:
    section = _step_29m_section(_read_registry())
    assert (
        _field_value(section, "MACD_V1_CONFIG_V3_STATUS")
        == "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert (
        _field_value(section, "BREAKOUT_DONCHIAN_V1_STATUS")
        == "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert (
        _field_value(section, "MA_CROSSOVER_V1_STATUS") == "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert _field_value(section, "MA_CROSSOVER_V1_ECONOMIC_EVALUATION_EXECUTED") == "true"
    assert _field_value(section, "MA_CROSSOVER_V1_PROMOTION_ELIGIBLE") == "false"


def test_hold_blocks_retry_tuning_and_further_evaluation() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "STEP29M_SAME_BINDING_RETRY_AUTHORIZED") == "false"
    assert _field_value(section, "STEP29M_PARAMETER_TUNING_AUTHORIZED") == "false"
    assert _field_value(section, "STEP29M_POLICY_THRESHOLD_RELAXATION_AUTHORIZED") == "false"
    assert _field_value(section, "STEP29M_FURTHER_ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_ALLOWED") == "false"
    assert _field_value(section, "ECONOMIC_REEVALUATION_ALLOWED") == "false"
    assert _field_value(section, "PARAMETER_TUNING_PERFORMED") == "false"


def test_no_promotion_runtime_or_profitability_authority() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "STEP29M_PROMOTION_AUTHORIZED") == "false"
    assert _field_value(section, "STEP29M_RUNTIME_AUTHORITY") == "false"
    assert _field_value(section, "STEP29M_PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_ALLOWED") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "STEP29N_AUTHORIZED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ALLOWED") == "false"


def test_step29n_already_complete_not_reimplemented() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(section, "STEP29N_ALREADY_COMPLETE") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29N_COMPLETE") == "true"
    assert "promotion_economic_gate_binding_v1_slice" in _field_value(
        text, "RUNBOOK_STEP_29N_IMPLEMENTED_SCOPE"
    )


def test_negative_decisions_remain_canonical() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEGATIVE_CANDIDATE_DECISIONS_REMAIN_CANONICAL") == "true"
    assert (
        _field_value(section, "NEGATIVE_CANDIDATE_DECISIONS_REMAIN_EVIDENCE_ADMISSIBLE") == "true"
    )
    assert _field_value(section, "HISTORICAL_FLEET_RESULTS_UNCHANGED") == "true"


def test_closeout_evidence_refs_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert str(PLANNING_EVIDENCE) in _field_value(
        section, "FLEET_NO_PASS_OPERATOR_POLICY_DECISION_EVIDENCE_REF"
    )
    assert str(MA_CROSSOVER_EVAL_EVIDENCE) in _field_value(
        section, "MA_CROSSOVER_V1_REAL_EVALUATION_EVIDENCE_REF"
    )
    assert str(MA_CROSSOVER_CLOSEOUT_EVIDENCE) in _field_value(
        section, "MA_CROSSOVER_V1_CANDIDATE_DECISION_EVIDENCE_REF"
    )


def test_operator_decision_record_exists() -> None:
    assert OPERATOR_DECISION_RECORD.is_file(), f"missing: {OPERATOR_DECISION_RECORD}"
    body = OPERATOR_DECISION_RECORD.read_text(encoding="utf-8")
    assert "NO_NEW_CANDIDATE_HOLD" in body
    assert "Frank Rauter" in body
    assert "COMPLETE_NO_PASS" in body

"""Contract tests for STEP 29M registered strategy evaluation fleet closeout v0.

Verifies fleet-complete registry truth without authorizing promotion, runtime,
profitability claims, or new strategy evaluation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

FLEET_SLICE = "step29m_registered_strategy_evaluation_fleet_closeout_v0_slice"
MACD_V3_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic/step29m_macd_v1_real_admissible_futures_economic_reevaluation_v3_after_risk_limits_rewire_single_rerun_v0_20260701T225645Z"
)
BREAKOUT_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic/step29m_breakout_donchian_v1_real_admissible_futures_economic_evaluation_v1_20260701T233425Z"
)
FLEET_ANALYSIS_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/bounded_breakout_donchian_step29m_economic_result_root_cause_and_strategy_ranking_read_only_v0_20260701T234245Z"
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


def test_fleet_slice_registered_in_implemented_scope() -> None:
    text = _read_registry()
    scope = _field_value(text, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    assert FLEET_SLICE in scope.split(",")


def test_registered_strategy_fleet_complete_no_economic_validity_pass() -> None:
    section = _step_29m_section(_read_registry())
    assert (
        _field_value(section, "STEP29M_REGISTERED_STRATEGY_FLEET_STATUS")
        == "EVALUATION_FLEET_COMPLETE_NO_ECONOMIC_VALIDITY_PASS"
    )
    assert _field_value(section, "REGISTERED_POLICY_RATIFIED_STRATEGY_COUNT") == "2"
    assert _field_value(section, "COMPLETED_TECHNICALLY_VALID_EVALUATION_COUNT") == "2"
    assert _field_value(section, "ECONOMIC_POLICY_PASS_COUNT") == "0"
    assert _field_value(section, "ECONOMIC_POLICY_FAIL_COUNT") == "2"
    assert _field_value(section, "PROMOTION_ELIGIBLE_COUNT") == "0"


def test_both_registered_candidates_technically_valid_policy_fails() -> None:
    section = _step_29m_section(_read_registry())
    assert (
        _field_value(section, "BREAKOUT_DONCHIAN_V1_STATUS")
        == "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert (
        _field_value(section, "MACD_V1_CONFIG_V3_STATUS")
        == "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert (
        _field_value(section, "PRIMARY_FLEET_FINDING")
        == "NO_ADMISSIBLE_REGISTERED_STRATEGY_ECONOMICALLY_VIABLE_OFFLINE"
    )


def test_evaluation_execution_complete_without_economic_validity_objective() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "EVALUATION_EXECUTION_COMPLETE") == "true"
    assert _field_value(section, "ECONOMIC_VALIDITY_OBJECTIVE_ACHIEVED") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"


def test_no_pending_next_evaluation_candidate() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "none"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_STATUS") == (
        "EVALUATION_FLEET_COMPLETE_NO_PENDING_CANDIDATE"
    )
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_PATH") == "none"
    assert _field_value(section, "LAST_EVALUATED_STRATEGY_ID") == "breakout_donchian"
    assert _field_value(section, "LAST_EVALUATED_CONFIG_VERSION") == "v1"


def test_fleet_evidence_refs_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert str(MACD_V3_EVIDENCE) in _field_value(
        section, "MACD_V1_CONFIG_V3_REAL_EVALUATION_EVIDENCE_REF"
    )
    assert str(BREAKOUT_EVIDENCE) in _field_value(
        section, "BREAKOUT_DONCHIAN_V1_REAL_EVALUATION_EVIDENCE_REF"
    )
    assert str(FLEET_ANALYSIS_EVIDENCE) in _field_value(
        section, "FLEET_ROOT_CAUSE_AND_RANKING_EVIDENCE_REF"
    )


def test_post_fleet_next_canonical_step_read_only_decision() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEXT_CANONICAL_STEP") == (
        "BOUNDED_STEP29M_POST_FLEET_NO_PASS_CANONICAL_DECISION_READ_ONLY_V0"
    )


def test_promotion_runtime_and_step29nr_blocked() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "PROMOTION_ALLOWED") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "STEP29N_AUTHORIZED") == "false"
    assert _field_value(section, "STEP29R_AUTHORIZED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ALLOWED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_ALLOWED") == "false"
    assert _field_value(section, "ECONOMIC_REEVALUATION_ALLOWED") == "false"

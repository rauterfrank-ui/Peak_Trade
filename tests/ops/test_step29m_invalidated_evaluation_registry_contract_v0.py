"""Registry contract for invalidated STEP 29M macd v1 real evaluation."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

ROOT_CAUSE_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning_or_validation/"
    "step29m_macd_zero_trade_post_signal_root_cause_and_strategy_ranking_read_only_v1_20260701T205720Z"
)
INVALIDATED_EVALUATION = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/step29m_macd_v1_real_admissible_futures_economic_evaluation_v1_20260701T161757Z"
)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file()
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_step_29m_macd_v1_evaluation_v2_complete_registry_truth() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "REAL_EVALUATION_ATTEMPTED") == "true"
    assert _field_value(section, "REAL_EVALUATION_PERFORMED") == "true"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "true"
    assert (
        _field_value(section, "REAL_EVALUATION_INPUT_STATUS")
        == "MACD_V1_EVALUATION_V2_COMPLETE"
    )
    assert _field_value(section, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "LAST_EVALUATED_CONFIG_VERSION") == "v2"
    assert _field_value(section, "RUNBOOK_STEP_29M_COMPLETE") == "true"


def test_step_29m_invalidated_evaluation_refs_present() -> None:
    section = _step_29m_section(_read_registry())
    assert ROOT_CAUSE_EVIDENCE in _field_value(section, "ROOT_CAUSE_EVIDENCE_REF")
    assert INVALIDATED_EVALUATION in _field_value(section, "INVALIDATED_EVALUATION_REF")
    assert _field_value(section, "INVALIDATED_EVALUATION_STATUS") == (
        "TECHNICALLY_REPRODUCIBLE_ECONOMICALLY_INVALIDATED"
    )
    assert _field_value(section, "INVALIDATION_REASON") == (
        "IMPLICIT_STOP_PCT_AND_OVERSIZE_REJECTION_BLOCKED_ALL_ENTRIES"
    )

"""Registry contract tests for STEP 29M operator input admissibility closure slice."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

OPERATOR_INPUT_SLICE = (
    "real_admissible_futures_economic_evaluation_operator_input_and_admissibility_closure_v0_slice"
)
STEP_29M_IMPLEMENTED_SCOPE = (
    "economic_viability_evidence_v1_offline_slice,"
    "economic_viability_evidence_v1_persistence_load_reproducibility_slice,"
    "economic_validity_policy_v1_contract_slice,"
    "funding_model_binding_v1_slice,"
    "parameter_sensitivity_evidence_binding_v1_slice,"
    "admissible_versioned_futures_dataset_binding_v1_slice,"
    "economic_validity_policy_threshold_values_v1_slice,"
    "real_admissible_futures_economic_evidence_evaluation_v1_offline_slice,"
    f"{OPERATOR_INPUT_SLICE}"
)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_operator_input_slice_registered_in_implemented_scope() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    global_scope = _field_value(text, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    section_scope = _field_value(section, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    assert global_scope == STEP_29M_IMPLEMENTED_SCOPE
    assert section_scope == STEP_29M_IMPLEMENTED_SCOPE
    assert OPERATOR_INPUT_SLICE in global_scope.split(",")


def test_step_29m_complete_remains_true() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29M_COMPLETE") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29M_COMPLETE") == "true"


def test_operator_input_contract_bound_without_real_evaluation() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "OPERATOR_INPUT_CONTRACT_V1_BOUND") == "true"
    assert _field_value(section, "OPERATOR_INPUT_CONTRACT_V1_BOUND") == "true"
    assert _field_value(text, "OPERATOR_INPUT_CONTRACT_COMPLETE") == "true"
    assert _field_value(section, "OPERATOR_INPUT_CONTRACT_COMPLETE") == "true"
    assert _field_value(text, "REAL_EVALUATION_PERFORMED") == "false"
    assert _field_value(section, "REAL_EVALUATION_PERFORMED") == "false"
    assert _field_value(text, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_PRESENT") == "false"
    assert _field_value(text, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "false"
    assert _field_value(text, "ECONOMIC_VALIDITY_RESULT") == "NOT_PROVEN"
    assert _field_value(text, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert _field_value(text, "CURRENT_PROMOTION_EVALUATION") == "INELIGIBLE"
    assert _field_value(text, "RUNTIME_REWIRE_IMPLEMENTATION_ALLOWED") == "false"


def test_real_evaluation_input_status_updated() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert (
        _field_value(text, "REAL_EVALUATION_INPUT_STATUS")
        == "OPERATOR_INPUT_CONTRACT_COMPLETE_AWAITING_DATASET_STAGING"
    )
    assert (
        _field_value(section, "REAL_EVALUATION_INPUT_STATUS")
        == "OPERATOR_INPUT_CONTRACT_COMPLETE_AWAITING_DATASET_STAGING"
    )
    assert _field_value(text, "OPERATOR_INPUT_REQUIRED_FOR_REAL_EVALUATION") == "true"


def test_canonical_operator_input_contract_owner_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert (
        _field_value(section, "CANONICAL_OPERATOR_INPUT_CONTRACT_OWNER")
        == "src/backtest/real_admissible_futures_economic_evaluation_operator_input_contract_v1.py"
    )


def test_no_step_29r_or_29s_started_by_this_slice() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(text, "STEP_29S_STARTED") == "false"

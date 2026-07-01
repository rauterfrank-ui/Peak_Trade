"""Contract tests for RUNBOOK STEP 29M progress registry closeout v0.

Verifies technical completion closeout semantics without authorizing runtime,
profitability claims, or STEP 29N implementation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29M_IMPLEMENTED_SCOPE = (
    "economic_viability_evidence_v1_offline_slice,"
    "economic_viability_evidence_v1_persistence_load_reproducibility_slice,"
    "economic_validity_policy_v1_contract_slice,"
    "funding_model_binding_v1_slice,"
    "parameter_sensitivity_evidence_binding_v1_slice,"
    "admissible_versioned_futures_dataset_binding_v1_slice,"
    "economic_validity_policy_threshold_values_v1_slice,"
    "real_admissible_futures_economic_evidence_evaluation_v1_offline_slice"
)
STEP_29M_SLICES = tuple(STEP_29M_IMPLEMENTED_SCOPE.split(","))


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


def test_progress_registry_is_canonical_single_ssot() -> None:
    text = _read_registry()
    assert text.count("STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY") == 1
    assert "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md" not in text.replace(
        "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1", ""
    )


def test_runbook_step_29m_complete_true() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29M_COMPLETE") == "true"


def test_progress_registry_closeout_performed_true() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"


def test_step_29n_not_started() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "STEP_29N_STARTED") == "false"


def test_next_required_contract_is_29n_in_section() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEXT_REQUIRED_CONTRACT") == "RUNBOOK_STEP_29N"


def test_economic_validity_not_proven() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_RESULT") == "NOT_PROVEN"


def test_profitability_claim_not_allowed() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"


def test_policy_and_admissibility_status_pass() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "POLICY_THRESHOLD_STATUS") == "PASS"
    assert _field_value(section, "DATA_ADMISSIBILITY_STATUS") == "PASS"


def test_all_registered_step_29m_slices_preserved() -> None:
    text = _read_registry()
    scope = _field_value(text, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    assert scope == STEP_29M_IMPLEMENTED_SCOPE
    for slice_name in STEP_29M_SLICES:
        assert slice_name in scope


def test_no_step_29n_implementation_markers() -> None:
    section = _step_29m_section(_read_registry())
    assert "RUNBOOK_STEP_29N_IMPLEMENTED" not in section
    assert "RUNBOOK_STEP_29N_COMPLETE" not in section
    assert _field_value(section, "STEP_29N_STARTED") == "false"


def test_no_promotion_eligibility_or_runtime_authority() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "PROMOTION_ELIGIBILITY_GRANTED") == "false"
    assert _field_value(section, "RUNTIME_AUTHORITY_GRANTED") == "false"
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "STEP_29M_COMPLETION_DOES_NOT_START_PROMOTION_GATE") == "true"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_technical_stack_complete_without_economic_pass() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "TECHNICAL_ECONOMIC_VIABILITY_EVIDENCE_STACK_COMPLETE") == "true"
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_REQUIRED") == "true"
    assert _field_value(section, "THRESHOLD_TUNING_ALLOWED") == "false"


def test_step_29m_section_status_complete_with_closeout() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "STATUS") == "COMPLETE"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "NEXT_REQUIRED_CONTRACT") == "RUNBOOK_STEP_29N"

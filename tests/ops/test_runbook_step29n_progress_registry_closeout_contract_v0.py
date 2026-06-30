"""Contract tests for RUNBOOK STEP 29N progress registry closeout v0.

Verifies technical completion closeout semantics without authorizing runtime,
profitability claims, promotion authority, or STEP 29O implementation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29N_IMPLEMENTED_SCOPE = "promotion_economic_gate_binding_v1_slice"


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29n_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1")
    end = text.index("#### RUNBOOK_STEP_29J (legacy heading)", start)
    return text[start:end]


def test_progress_registry_is_canonical_single_ssot() -> None:
    text = _read_registry()
    assert text.count("STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY") == 1


def test_runbook_step_29n_started_true() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29N_STARTED") == "true"
    assert _field_value(text, "STEP_29N_STARTED") == "true"


def test_runbook_step_29n_complete_true() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29N_COMPLETE") == "true"


def test_progress_registry_closeout_performed_true() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"


def test_step_29o_not_started() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "STEP_29O_STARTED") == "false"
    assert _field_value(section, "STEP_29O_STARTED") == "false"


def test_next_runbook_step_is_29o() -> None:
    text = _read_registry()
    assert _field_value(text, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29O"


def test_promotion_gate_binding_status_pass() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "PROMOTION_ECONOMIC_GATE_BINDING_STATUS") == "PASS"


def test_economic_validity_not_proven() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"


def test_profitability_claim_not_allowed() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"


def test_promotion_candidate_not_eligible() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_STATUS") == "INELIGIBLE"
    assert _field_value(section, "CURRENT_PROMOTION_EVALUATION") == "INELIGIBLE"


def test_no_deployment_runtime_activation_execution() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "DEPLOYMENT_ELIGIBLE") == "false"
    assert _field_value(text, "RUNTIME_ELIGIBLE") == "false"
    assert _field_value(text, "ACTIVATION_ALLOWED") == "false"
    assert _field_value(text, "EXECUTION_ALLOWED") == "false"
    assert _field_value(section, "DEPLOYMENT_ELIGIBLE") == "false"
    assert _field_value(section, "RUNTIME_ELIGIBLE") == "false"
    assert _field_value(section, "ACTIVATION_ALLOWED") == "false"
    assert _field_value(section, "EXECUTION_ALLOWED") == "false"


def test_step_29m_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29M_COMPLETE") == "true"


def test_implemented_scope_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29N_IMPLEMENTED_SCOPE") == STEP_29N_IMPLEMENTED_SCOPE
    section = _step_29n_section(text)
    assert _field_value(section, "RUNBOOK_STEP_29N_IMPLEMENTED_SCOPE") == STEP_29N_IMPLEMENTED_SCOPE


def test_no_step_29o_implementation_markers() -> None:
    section = _step_29n_section(_read_registry())
    assert "RUNBOOK_STEP_29O_IMPLEMENTED" not in section
    assert "RUNBOOK_STEP_29O_COMPLETE" not in section


def test_no_promotion_runtime_or_execution_authority() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "PROMOTION_ELIGIBILITY_GRANTED") == "false"
    assert _field_value(section, "PROMOTION_AUTHORITY_GRANTED") == "false"
    assert _field_value(section, "DEPLOYMENT_AUTHORITY_GRANTED") == "false"
    assert _field_value(section, "RUNTIME_AUTHORITY_GRANTED") == "false"
    assert _field_value(section, "EXECUTION_AUTHORITY_GRANTED") == "false"
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "STEP_29N_COMPLETION_DOES_NOT_START_STEP_29O") == "true"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_technical_stack_complete_without_promotion_pass() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "TECHNICAL_PROMOTION_GATE_STACK_COMPLETE") == "true"
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_REQUIRED") == "true"
    assert _field_value(section, "THRESHOLD_TUNING_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_technical_completion_not_equated_with_promotion_eligibility() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "RUNBOOK_STEP_29N_COMPLETE") == "true"
    assert _field_value(section, "TECHNICAL_PROMOTION_GATE_STACK_COMPLETE") == "true"
    assert _field_value(section, "CURRENT_PROMOTION_EVALUATION") == "INELIGIBLE"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_step_29n_section_status_complete_with_closeout() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "STATUS") == "COMPLETE"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "NEXT_REQUIRED_CONTRACT") == "RUNBOOK_STEP_29O"

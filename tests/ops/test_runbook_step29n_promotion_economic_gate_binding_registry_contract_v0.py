"""Contract tests for RUNBOOK STEP 29N promotion economic gate binding registry slice."""

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


def test_runbook_step_29n_started_true() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29N_STARTED") == "true"
    assert _field_value(text, "STEP_29N_STARTED") == "true"


def test_runbook_step_29n_implemented_scope() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29N_IMPLEMENTED_SCOPE") == STEP_29N_IMPLEMENTED_SCOPE


def test_promotion_gate_binding_status_pass() -> None:
    text = _read_registry()
    assert _field_value(text, "PROMOTION_ECONOMIC_GATE_BINDING_STATUS") == "PASS"


def test_promotion_candidate_not_eligible() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_no_deployment_runtime_activation_execution() -> None:
    text = _read_registry()
    assert _field_value(text, "DEPLOYMENT_ELIGIBLE") == "false"
    assert _field_value(text, "RUNTIME_ELIGIBLE") == "false"
    assert _field_value(text, "ACTIVATION_ALLOWED") == "false"
    assert _field_value(text, "EXECUTION_ALLOWED") == "false"


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


def test_step_29m_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29M_COMPLETE") == "true"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29n_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_candidate_eligibility_does_not_imply_authority() -> None:
    section = _step_29n_section(_read_registry())
    assert (
        _field_value(section, "PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_DEPLOYMENT") == "true"
    )
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_RUNTIME") == "true"
    assert (
        _field_value(section, "PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_ACTIVATION") == "true"
    )
    assert (
        _field_value(section, "PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_EXECUTION") == "true"
    )

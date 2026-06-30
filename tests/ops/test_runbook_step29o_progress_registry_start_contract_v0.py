"""Contract tests for RUNBOOK STEP 29O progress registry start v0.

Verifies registry-start-only semantics for Intent Compatibility Firewall without
authorizing runtime, orders, authority, fachliche implementation, or STEP 29P/29Q/29R.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29O_MINIMUM_SAFE_SLICE = "intent_compatibility_firewall_v1_offline_slice"
STEP_29O_CANONICAL_DEFINITION = "INTENT_COMPATIBILITY_FIREWALL"
NEXT_REQUIRED_CONTRACT = "RUNBOOK_STEP_29O_INTENT_COMPATIBILITY_FIREWALL_V1_IMPLEMENTATION"


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29o_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29O — Intent Compatibility Firewall v1")
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


def test_progress_registry_is_canonical_single_ssot() -> None:
    text = _read_registry()
    assert text.count("STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY") == 1


def test_exactly_one_step_29o_registry_start_section() -> None:
    text = _read_registry()
    assert text.count("#### RUNBOOK_STEP_29O — Intent Compatibility Firewall v1") == 1


def test_runbook_step_29o_started_true() -> None:
    text = _read_registry()
    section = _step_29o_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29O_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29O_STARTED") == "true"


def test_runbook_step_29o_implementation_not_started() -> None:
    text = _read_registry()
    section = _step_29o_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29O_IMPLEMENTATION_STARTED") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29O_IMPLEMENTATION_STARTED") == "false"


def test_runbook_step_29o_not_complete() -> None:
    text = _read_registry()
    section = _step_29o_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29O_COMPLETE") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29O_COMPLETE") == "false"


def test_progress_registry_closeout_not_performed_for_step_29o() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "false"


def test_runbook_step_29o_canonical_definition() -> None:
    section = _step_29o_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29O_CANONICAL_DEFINITION")
        == STEP_29O_CANONICAL_DEFINITION
    )


def test_runbook_step_29o_minimum_safe_slice() -> None:
    section = _step_29o_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29O_MINIMUM_SAFE_SLICE") == STEP_29O_MINIMUM_SAFE_SLICE
    )


def test_intent_compatibility_firewall_not_implemented() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "INTENT_COMPATIBILITY_FIREWALL_IMPLEMENTED") == "false"


def test_implicit_intent_conversion_not_allowed() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "IMPLICIT_INTENT_CONVERSION_ALLOWED") == "false"


def test_canonical_order_intent_not_defined() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "CANONICAL_ORDER_INTENT_DEFINED") == "false"


def test_capital_risk_sizing_mathematics_unchanged() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "CAPITAL_RISK_SIZING_MATHEMATICS_CHANGED") == "false"


def test_runtime_rewire_not_performed() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "RUNTIME_REWIRE_PERFORMED") == "false"


def test_next_required_contract_is_implementation_slice() -> None:
    text = _read_registry()
    section = _step_29o_section(text)
    assert _field_value(section, "NEXT_REQUIRED_CONTRACT") == NEXT_REQUIRED_CONTRACT


def test_next_runbook_step_remains_29o() -> None:
    text = _read_registry()
    section = _step_29o_section(text)
    assert _field_value(text, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29O"
    assert _field_value(section, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29O"


def test_no_runtime_order_risk_sizing_or_authority_effects() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "ORDER_EFFECT") == "false"
    assert _field_value(section, "RISK_SIZING_EFFECT") == "false"
    assert _field_value(section, "AUTHORITY_EFFECT") == "false"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_threshold_tuning_not_allowed() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "THRESHOLD_TUNING_ALLOWED") == "false"


def test_no_economic_validity_or_promotion_eligibility_claims() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_no_step_29p_29q_29r_start_markers() -> None:
    text = _read_registry()
    assert "RUNBOOK_STEP_29P_STARTED" not in text
    assert "RUNBOOK_STEP_29Q_STARTED" not in text
    assert "RUNBOOK_STEP_29R_STARTED" not in text
    assert "STEP_29P_STARTED" not in text
    assert "STEP_29Q_STARTED" not in text
    assert "STEP_29R_STARTED" not in text
    assert "#### RUNBOOK_STEP_29P" not in text
    assert "#### RUNBOOK_STEP_29Q" not in text
    assert "#### RUNBOOK_STEP_29R" not in text


def test_scope_classification_registry_start_only() -> None:
    section = _step_29o_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29O_SCOPE_CLASSIFICATION")
        == "PROGRESS_REGISTRY_START_ONLY"
    )
    assert _field_value(section, "RUNBOOK_STEP_29O_IMPLEMENTED_SCOPE") == "none"
    assert _field_value(section, "STATUS") == "IN_PROGRESS"


def test_step_29n_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29N_COMPLETE") == "true"


def test_no_runtime_deployment_adapter_or_order_authority() -> None:
    section = _step_29o_section(_read_registry())
    assert _field_value(section, "LIVE_AUTHORIZED") == "false"
    assert _field_value(section, "DEPLOYMENT_EFFECT") == "false"
    assert _field_value(section, "STEP_29O_DOES_NOT_CREATE_ORDERS") == "true"
    assert _field_value(section, "STEP_29O_DOES_NOT_GRANT_AUTHORITY") == "true"
    assert _field_value(section, "STEP_29O_DOES_NOT_CREATE_ADAPTER_COMPATIBILITY") == "true"

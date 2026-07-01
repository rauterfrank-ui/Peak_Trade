"""Contract tests for RUNBOOK STEP 29P progress registry closeout v0.

Verifies technical completion closeout semantics without authorizing runtime,
orders, authority, canonical order intent, or STEP 29Q/29R implementation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29P_IMPLEMENTED_SCOPE = "capital_risk_sizing_v1_offline_slice"


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29p_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29P — Capital Risk Sizing Mathematics v1")
    end = text.index("#### RUNBOOK_STEP_29Q — Canonical Order Intent v1", start)
    return re.sub(r"\s<!--.*?-->", "", text[start:end])


def test_progress_registry_is_canonical_single_ssot() -> None:
    text = _read_registry()
    assert text.count("STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY") == 1


def test_runbook_step_29p_started_true() -> None:
    text = _read_registry()
    section = _step_29p_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29P_STARTED") == "true"
    assert _field_value(text, "STEP_29P_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29P_STARTED") == "true"


def test_runbook_step_29p_implementation_started_true() -> None:
    text = _read_registry()
    section = _step_29p_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29P_IMPLEMENTATION_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29P_IMPLEMENTATION_STARTED") == "true"


def test_runbook_step_29p_complete_true() -> None:
    text = _read_registry()
    section = _step_29p_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29P_COMPLETE") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29P_COMPLETE") == "true"


def test_progress_registry_closeout_performed_true() -> None:
    text = _read_registry()
    section = _step_29p_section(text)
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"


def test_implemented_scope_bound() -> None:
    text = _read_registry()
    section = _step_29p_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29P_IMPLEMENTED_SCOPE") == STEP_29P_IMPLEMENTED_SCOPE
    assert _field_value(section, "RUNBOOK_STEP_29P_IMPLEMENTED_SCOPE") == STEP_29P_IMPLEMENTED_SCOPE


def test_capital_risk_sizing_mathematics_implemented_true() -> None:
    text = _read_registry()
    section = _step_29p_section(text)
    assert _field_value(text, "CAPITAL_RISK_SIZING_MATHEMATICS_IMPLEMENTED") == "true"
    assert _field_value(section, "CAPITAL_RISK_SIZING_MATHEMATICS_IMPLEMENTED") == "true"


def test_next_runbook_step_is_29q_in_29p_section() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29Q"


def test_next_required_contract_is_29q() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "NEXT_REQUIRED_CONTRACT") == "RUNBOOK_STEP_29Q"


def test_canonical_owner_ratified() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "CANONICAL_OWNER_STATUS") == "IMPLEMENTED"
    assert _field_value(section, "CANONICAL_OWNER_RATIFIED") == "true"


def test_quantity_chain_boundaries_declared() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "STEP_29P_QUANTITY_CHAIN") == (
        "canonical_trading_decision,scope_capital_envelope,pre_sizing_risk,"
        "canonical_position_sizing,post_sizing_risk,quantity_provenance"
    )


def test_no_runtime_order_risk_sizing_or_authority_effects() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "ORDER_EFFECT") == "false"
    assert _field_value(section, "RISK_SIZING_EFFECT") == "false"
    assert _field_value(section, "AUTHORITY_EFFECT") == "false"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_no_economic_validity_or_promotion_eligibility_claims() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_step_29q_not_started_in_29p_section_snapshot() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "STEP_29P_COMPLETION_DOES_NOT_START_STEP_29Q") == "true"
    assert "RUNBOOK_STEP_29Q_STARTED" not in section
    assert "RUNBOOK_STEP_29Q_COMPLETE" not in section


def test_no_step_29r_start_markers_in_29p_section_snapshot() -> None:
    section = _step_29p_section(_read_registry())
    assert "RUNBOOK_STEP_29R_STARTED" not in section
    assert "STEP_29R_STARTED" not in section
    assert "#### RUNBOOK_STEP_29R" not in section
    assert _field_value(section, "STEP_29P_EXCLUDES_RUNTIME_REWIRE_29R") == "true"


def test_canonical_order_intent_not_defined() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "CANONICAL_ORDER_INTENT_DEFINED") == "false"


def test_step_29o_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29O_COMPLETE") == "true"
    assert _field_value(text, "INTENT_COMPATIBILITY_FIREWALL_IMPLEMENTED") == "true"


def test_step_29p_section_status_complete_with_closeout() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "STATUS") == "COMPLETE"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "STEP_29P_COMPLETION_DOES_NOT_START_STEP_29Q") == "true"


def test_no_runtime_deployment_adapter_or_order_authority() -> None:
    section = _step_29p_section(_read_registry())
    assert _field_value(section, "LIVE_AUTHORIZED") == "false"
    assert _field_value(section, "DEPLOYMENT_EFFECT") == "false"
    assert _field_value(section, "STEP_29P_DOES_NOT_CREATE_ORDERS") == "true"
    assert _field_value(section, "STEP_29P_DOES_NOT_GRANT_AUTHORITY") == "true"
    assert _field_value(section, "STEP_29P_EXCLUDES_ADAPTER_COMPATIBILITY") == "true"
    assert _field_value(section, "STEP_29P_EXCLUDES_ORDER_SUBMISSION") == "true"

"""Contract tests for RUNBOOK STEP 29Q canonical order intent implementation v0.

Verifies implemented-scope semantics without authorizing runtime, orders, adapter
compatibility, transformation binding, registry closeout, or STEP 29R.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
CANONICAL_OWNER = REPO_ROOT / "src" / "governance" / "canonical_order_intent_v1.py"

STEP_29Q_IMPLEMENTED_SCOPE = "canonical_order_intent_v1_offline_slice"
STEP_29Q_CANONICAL_DEFINITION = "CANONICAL_ORDER_INTENT"
STEP_29Q_CANONICAL_OWNER = "src&#47;governance&#47;canonical_order_intent_v1.py"


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29q_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29Q — Canonical Order Intent v1")
    end = text.index("\n#### RUNBOOK_STEP_29R — Runtime Rewire", start)
    return re.sub(r"\s<!--.*?-->", "", text[start:end])


def test_canonical_owner_module_exists() -> None:
    assert CANONICAL_OWNER.is_file(), f"missing canonical owner: {CANONICAL_OWNER}"


def test_runbook_step_29q_implementation_started_true() -> None:
    text = _read_registry()
    section = _step_29q_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29Q_IMPLEMENTATION_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29Q_IMPLEMENTATION_STARTED") == "true"


def test_runbook_step_29q_implemented_scope_bound() -> None:
    text = _read_registry()
    section = _step_29q_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29Q_IMPLEMENTED_SCOPE") == STEP_29Q_IMPLEMENTED_SCOPE
    assert _field_value(section, "RUNBOOK_STEP_29Q_IMPLEMENTED_SCOPE") == STEP_29Q_IMPLEMENTED_SCOPE


def test_runbook_step_29q_implemented_true() -> None:
    text = _read_registry()
    section = _step_29q_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29Q_IMPLEMENTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29Q_IMPLEMENTED") == "true"


def test_canonical_order_intent_implemented_true() -> None:
    text = _read_registry()
    section = _step_29q_section(text)
    assert _field_value(text, "CANONICAL_ORDER_INTENT_IMPLEMENTED") == "true"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_IMPLEMENTED") == "true"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_DEFINED") == "true"


def test_canonical_owner_ratified() -> None:
    section = _step_29q_section(_read_registry())
    assert _field_value(section, "CANONICAL_OWNER") == STEP_29Q_CANONICAL_OWNER
    assert _field_value(section, "CANONICAL_OWNER_STATUS") == "IMPLEMENTED"
    assert _field_value(section, "CANONICAL_OWNER_RATIFIED") == "true"


def test_adapter_compatibility_and_transformation_not_proven_or_bound() -> None:
    text = _read_registry()
    section = _step_29q_section(text)
    assert _field_value(text, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "false"
    assert _field_value(section, "IMPLICIT_ADAPTER_COMPATIBILITY_ALLOWED") == "false"
    assert _field_value(section, "ADAPTER_TRANSFORMATION_IMPLEMENTED") == "false"


def test_scope_classification_offline_slice() -> None:
    section = _step_29q_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29Q_SCOPE_CLASSIFICATION")
        == "CANONICAL_ORDER_INTENT_V1_OFFLINE_SLICE"
    )
    assert (
        _field_value(section, "RUNBOOK_STEP_29Q_CANONICAL_DEFINITION")
        == STEP_29Q_CANONICAL_DEFINITION
    )


def test_no_runtime_order_or_authority_effects() -> None:
    section = _step_29q_section(_read_registry())
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "ORDER_EFFECT") == "false"
    assert _field_value(section, "AUTHORITY_EFFECT") == "false"
    assert _field_value(section, "ADAPTER_SUBMISSION_EFFECT") == "false"
    assert _field_value(section, "NETWORK_EFFECT") == "false"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29q_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_capital_risk_sizing_mathematics_not_changed() -> None:
    text = _read_registry()
    section = _step_29q_section(text)
    assert _field_value(text, "CAPITAL_RISK_SIZING_MATHEMATICS_CHANGED") == "false"
    assert _field_value(section, "CAPITAL_RISK_SIZING_MATHEMATICS_CHANGED") == "false"


def test_step_29q_section_does_not_start_step_29r() -> None:
    section = _step_29q_section(_read_registry())
    assert _field_value(section, "STEP_29Q_COMPLETION_DOES_NOT_START_STEP_29R") == "true"
    assert "RUNBOOK_STEP_29R_STARTED" not in section
    assert "#### RUNBOOK_STEP_29R" not in section


def test_step_29p_and_29o_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29P_COMPLETE") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29O_COMPLETE") == "true"


def test_implementation_does_not_claim_adapter_compatibility() -> None:
    section = _step_29q_section(_read_registry())
    assert _field_value(section, "STEP_29Q_DOES_NOT_CLAIM_ADAPTER_COMPATIBILITY") == "true"
    assert _field_value(section, "STEP_29Q_DOES_NOT_IMPLEMENT_ADAPTER_TRANSFORMATION") == "true"


def test_implementation_does_not_create_orders_or_grant_authority() -> None:
    section = _step_29q_section(_read_registry())
    assert _field_value(section, "STEP_29Q_DOES_NOT_CREATE_ORDERS") == "true"
    assert _field_value(section, "STEP_29Q_DOES_NOT_GRANT_AUTHORITY") == "true"
    assert _field_value(section, "LIVE_AUTHORIZED") == "false"

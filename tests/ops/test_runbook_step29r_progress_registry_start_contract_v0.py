"""Contract tests for RUNBOOK STEP 29R progress registry start v0.

Verifies registry-start-only semantics for Runtime Rewire without authorizing
runtime, orders, authority, fachliche implementation, adapter transformation,
pipeline activation, scheduler activation, or STEP 29S.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29R_MINIMUM_SAFE_SLICE = "runtime_rewire_v1_offline_slice"
STEP_29R_CANONICAL_DEFINITION = "RUNTIME_REWIRE"
RUNTIME_REWIRE_BLOCKERS = (
    "canonical_order_intent_adapter_compatibility_unproven;"
    "canonical_order_intent_transformation_unbound;"
    "economic_validity_offline_gate_not_pass;"
    "runtime_rewire_eligibility_unproven;"
    "runtime_rewire_activation_unbound"
)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29r_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29R — Runtime Rewire")
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return re.sub(r"\s<!--.*?-->", "", text[start:end])


def test_progress_registry_is_canonical_single_ssot() -> None:
    text = _read_registry()
    assert text.count("STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY") == 1


def test_exactly_one_step_29r_registry_start_section() -> None:
    text = _read_registry()
    assert text.count("#### RUNBOOK_STEP_29R — Runtime Rewire") == 1


def test_runbook_step_29r_started_true() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_STARTED") == "true"
    assert _field_value(text, "STEP_29R_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29R_STARTED") == "true"
    assert _field_value(section, "STEP_29R_STARTED") == "true"


def test_runbook_step_29r_implementation_not_started() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_IMPLEMENTATION_STARTED") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29R_IMPLEMENTATION_STARTED") == "false"


def test_runbook_step_29r_not_complete() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29R_COMPLETE") == "false"


def test_runbook_step_29r_implemented_scope_none() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_IMPLEMENTED_SCOPE") == "none"
    assert _field_value(section, "RUNBOOK_STEP_29R_IMPLEMENTED_SCOPE") == "none"


def test_progress_registry_closeout_not_performed_for_step_29r() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "false"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "false"


def test_runbook_step_29r_canonical_definition() -> None:
    section = _step_29r_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29R_CANONICAL_DEFINITION")
        == STEP_29R_CANONICAL_DEFINITION
    )


def test_runbook_step_29r_minimum_safe_slice() -> None:
    section = _step_29r_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29R_MINIMUM_SAFE_SLICE") == STEP_29R_MINIMUM_SAFE_SLICE
    )


def test_scope_classification_progress_registry_start_only() -> None:
    section = _step_29r_section(_read_registry())
    assert (
        _field_value(section, "RUNBOOK_STEP_29R_SCOPE_CLASSIFICATION")
        == "PROGRESS_REGISTRY_START_ONLY"
    )
    assert _field_value(section, "STATUS") == "IN_PROGRESS"
    assert _field_value(section, "STEP_29R_REGISTRY_START_ONLY") == "true"


def test_runtime_rewire_not_implemented() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNTIME_REWIRE_IMPLEMENTED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_IMPLEMENTED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_PERFORMED") == "false"


def test_runtime_rewire_eligibility_and_activation_not_proven_or_bound() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNTIME_REWIRE_ELIGIBILITY_PROVEN") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ELIGIBILITY_PROVEN") == "false"
    assert _field_value(text, "RUNTIME_REWIRE_ACTIVATION_BOUND") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ACTIVATION_BOUND") == "false"


def test_gate_truth_documented() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "TRADING_LOGIC_COMPLETION_GATE_PASS") == "true"
    assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert _field_value(section, "INTENT_COMPATIBILITY_FIREWALL_PASS") == "true"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_IMPLEMENTED") == "true"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "false"


def test_runtime_rewire_implementation_blockers_documented() -> None:
    section = _step_29r_section(_read_registry())
    assert (
        _field_value(section, "RUNTIME_REWIRE_IMPLEMENTATION_BLOCKERS") == RUNTIME_REWIRE_BLOCKERS
    )
    assert (
        _field_value(section, "REGISTRY_START_DOES_NOT_GRANT_IMPLEMENTATION_ELIGIBILITY") == "true"
    )


def test_registry_start_does_not_implement_runtime_paths() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "STEP_29R_DOES_NOT_IMPLEMENT_RUNTIME_REWIRE") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_GRANT_RUNTIME_ELIGIBILITY") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_IMPLEMENT_ADAPTER_TRANSFORMATION") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_SUBMIT_ADAPTERS") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_ACTIVATE_PIPELINE") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_ACTIVATE_SCHEDULER") == "true"


def test_no_runtime_order_network_credential_or_authority_effects() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "ORDER_EFFECT") == "false"
    assert _field_value(section, "AUTHORITY_EFFECT") == "false"
    assert _field_value(section, "ADAPTER_SUBMISSION_EFFECT") == "false"
    assert _field_value(section, "NETWORK_EFFECT") == "false"
    assert _field_value(section, "CREDENTIAL_EFFECT") == "false"


def test_no_shadow_paper_testnet_canary_or_live_authorization() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "LIVE_AUTHORIZED") == "false"
    assert _field_value(section, "SHADOW_AUTHORIZED") == "false"
    assert _field_value(section, "PAPER_AUTHORIZED") == "false"
    assert _field_value(section, "TESTNET_AUTHORIZED") == "false"
    assert _field_value(section, "CANARY_AUTHORIZED") == "false"
    assert _field_value(section, "STEP_29R_EXCLUDES_SHADOW_PAPER_TESTNET_CANARY_LIVE") == "true"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_no_economic_validity_or_promotion_eligibility_claims() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_no_step_29s_start_markers() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert "RUNBOOK_STEP_29S_STARTED" not in text
    assert "STEP_29S_STARTED" not in text
    assert "#### RUNBOOK_STEP_29S" not in text
    assert _field_value(section, "STEP_29R_EXCLUDES_STEP_29S") == "true"
    assert _field_value(section, "STEP_29R_COMPLETION_DOES_NOT_START_STEP_29S") == "true"


def test_next_runbook_step_is_29r() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29R"
    assert _field_value(section, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29R"


def test_next_required_contract_is_runtime_rewire_implementation() -> None:
    section = _step_29r_section(_read_registry())
    assert (
        _field_value(section, "NEXT_REQUIRED_CONTRACT")
        == "RUNBOOK_STEP_29R_RUNTIME_REWIRE_V1_IMPLEMENTATION"
    )


def test_step_29q_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29Q_COMPLETE") == "true"
    assert _field_value(text, "CANONICAL_ORDER_INTENT_IMPLEMENTED") == "true"


def test_step_29p_and_29o_complete_preserved() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNBOOK_STEP_29P_COMPLETE") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29O_COMPLETE") == "true"
    assert _field_value(text, "CAPITAL_RISK_SIZING_MATHEMATICS_IMPLEMENTED") == "true"
    assert _field_value(text, "INTENT_COMPATIBILITY_FIREWALL_IMPLEMENTED") == "true"


def test_no_runtime_deployment_adapter_or_order_authority() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "STEP_29R_DOES_NOT_SUBMIT_ORDERS") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_GRANT_AUTHORITY") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_PERFORM_NETWORK_IO") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_COMMUNICATE_VENUE") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_ACCESS_CREDENTIALS") == "true"


def test_canonical_owner_pending_no_runtime_implementation() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "CANONICAL_OWNER") == "none"
    assert _field_value(section, "CANONICAL_OWNER_STATUS") == "PROPOSED_PENDING_OWNER_SELECTION"
    assert _field_value(section, "CANONICAL_OWNER_RATIFIED") == "false"


def test_capital_risk_sizing_and_order_intent_semantics_not_changed() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "CAPITAL_RISK_SIZING_MATHEMATICS_CHANGED") == "false"
    assert _field_value(section, "CAPITAL_RISK_SIZING_MATHEMATICS_CHANGED") == "false"
    assert (
        _field_value(section, "STEP_29R_DOES_NOT_CHANGE_CANONICAL_ORDER_INTENT_SEMANTICS") == "true"
    )
    assert (
        _field_value(section, "STEP_29R_DOES_NOT_CHANGE_QUANTITY_RISK_SIZING_SEMANTICS") == "true"
    )

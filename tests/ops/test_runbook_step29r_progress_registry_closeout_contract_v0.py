"""Contract tests for RUNBOOK STEP 29R offline transformation progress registry closeout v0.

Verifies the bounded offline transformation slice closeout from PR #4721 without
marking STEP 29R complete, authorizing runtime rewire, claiming full adapter
compatibility, passing the economic validity gate, or starting STEP 29S.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29R_IMPLEMENTED_SCOPE = (
    "canonical_order_intent_v1_to_adapter_order_intent_v1_transformation_contract_offline_slice"
)
MERGE_COMMIT = "bbb500caa1997baee6ee6bca9656067ceca986f3"
RUNTIME_REWIRE_BLOCKERS = (
    "canonical_order_intent_adapter_compatibility_unproven;"
    "economic_validity_offline_gate_not_pass;"
    "runtime_rewire_eligibility_unproven;"
    "runtime_rewire_activation_unbound;"
    "runtime_rewire_v1_implementation_pending"
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


def _step_29n_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1")
    end = text.index("#### RUNBOOK_STEP_29J (legacy heading)", start)
    return text[start:end]


def _step_29q_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29Q — Canonical Order Intent v1")
    end = text.index("\n#### RUNBOOK_STEP_29R — Runtime Rewire", start)
    return re.sub(r"\s<!--.*?-->", "", text[start:end])


def test_progress_registry_is_canonical_single_ssot() -> None:
    text = _read_registry()
    assert text.count("STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY") == 1


def test_runbook_step_29r_started_true() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_STARTED") == "true"
    assert _field_value(text, "STEP_29R_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29R_STARTED") == "true"
    assert _field_value(section, "STEP_29R_STARTED") == "true"


def test_runbook_step_29r_implementation_started_true() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_IMPLEMENTATION_STARTED") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29R_IMPLEMENTATION_STARTED") == "true"


def test_implemented_scope_exact_offline_transformation_slice() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_IMPLEMENTED_SCOPE") == STEP_29R_IMPLEMENTED_SCOPE
    assert _field_value(section, "RUNBOOK_STEP_29R_IMPLEMENTED_SCOPE") == STEP_29R_IMPLEMENTED_SCOPE


def test_canonical_order_intent_transformation_bound_true() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "true"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "true"


def test_structural_adapter_compatibility_proven_true() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert (
        _field_value(text, "CANONICAL_ORDER_INTENT_STRUCTURAL_ADAPTER_COMPATIBILITY_PROVEN")
        == "true"
    )
    assert (
        _field_value(section, "CANONICAL_ORDER_INTENT_STRUCTURAL_ADAPTER_COMPATIBILITY_PROVEN")
        == "true"
    )


def test_full_adapter_compatibility_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"


def test_economic_validity_offline_gate_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"


def test_runtime_rewire_implementation_allowed_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNTIME_REWIRE_IMPLEMENTATION_ALLOWED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_IMPLEMENTATION_ALLOWED") == "false"


def test_runtime_rewire_implemented_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNTIME_REWIRE_IMPLEMENTED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_IMPLEMENTED") == "false"


def test_runtime_rewire_eligibility_proven_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNTIME_REWIRE_ELIGIBILITY_PROVEN") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ELIGIBILITY_PROVEN") == "false"


def test_runtime_rewire_activation_bound_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNTIME_REWIRE_ACTIVATION_BOUND") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ACTIVATION_BOUND") == "false"


def test_step_29r_complete_remains_false() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(text, "STEP_29R_COMPLETE") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(section, "STEP_29R_COMPLETE") == "false"


def test_status_remains_in_progress() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "STATUS") == "IN_PROGRESS"


def test_step_29s_not_started() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "STEP_29S_STARTED") == "false"
    assert _field_value(section, "STEP_29S_STARTED") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29S_STARTED") == "false"
    assert "#### RUNBOOK_STEP_29S" not in text


def test_progress_registry_closeout_performed_for_offline_slice() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"


def test_registry_closeout_does_not_imply_step_completion() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(section, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(section, "STATUS") == "IN_PROGRESS"


def test_registry_closeout_does_not_imply_runtime_eligibility() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(text, "RUNTIME_REWIRE_ELIGIBILITY_PROVEN") == "false"
    assert _field_value(text, "RUNTIME_REWIRE_ACTIVATION_BOUND") == "false"
    assert _field_value(text, "RUNTIME_REWIRE_IMPLEMENTATION_ALLOWED") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ELIGIBILITY_PROVEN") == "false"
    assert _field_value(section, "RUNTIME_REWIRE_ACTIVATION_BOUND") == "false"


def test_registry_closeout_does_not_imply_full_adapter_compatibility() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(text, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"
    assert _field_value(section, "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN") == "false"


def test_step_29n_history_preserved() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29N_COMPLETE") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29N_COMPLETE") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "STATUS") == "COMPLETE"


def test_global_closeout_not_permanently_bound_to_29n_section() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29R_STARTED") == "true"
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"


def test_transition_29q_to_29r_remains_valid() -> None:
    text = _read_registry()
    q_section = _step_29q_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29Q_COMPLETE") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29R_STARTED") == "true"
    assert _field_value(q_section, "NEXT_RUNBOOK_STEP") == "RUNBOOK_STEP_29R"
    assert _field_value(q_section, "STEP_29Q_COMPLETION_DOES_NOT_START_STEP_29R") == "true"


def test_no_29r_to_29s_transition_signal() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "STEP_29S_STARTED") == "false"
    assert _field_value(section, "STEP_29R_EXCLUDES_STEP_29S") == "true"
    assert _field_value(section, "STEP_29R_COMPLETION_DOES_NOT_START_STEP_29S") == "true"
    assert "RUNBOOK_STEP_29S" not in _field_value(section, "NEXT_REQUIRED_CONTRACT")


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    text = _read_registry()
    section = _step_29r_section(text)
    assert _field_value(text, "FUTURES_ONLY") == "true"
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_no_runtime_order_or_live_effects() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "ORDER_EFFECT") == "false"
    assert _field_value(section, "LIVE_AUTHORIZED") == "false"
    assert _field_value(section, "NETWORK_EFFECT") == "false"
    assert _field_value(section, "ADAPTER_SUBMISSION_EFFECT") == "false"


def test_gate_truth_documented() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "TRADING_LOGIC_COMPLETION_GATE_PASS") == "true"
    assert _field_value(section, "INTENT_COMPATIBILITY_FIREWALL_PASS") == "true"
    assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"


def test_runtime_rewire_blockers_exclude_transformation_unbound() -> None:
    section = _step_29r_section(_read_registry())
    blockers = _field_value(section, "RUNTIME_REWIRE_IMPLEMENTATION_BLOCKERS")
    assert blockers == RUNTIME_REWIRE_BLOCKERS
    assert "canonical_order_intent_transformation_unbound" not in blockers


def test_merged_pr_and_commit_bound() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "MERGED_PRS") == "#4721"
    assert _field_value(section, "MERGE_COMMITS") == MERGE_COMMIT


def test_offline_transformation_slice_implemented_not_runtime_rewire() -> None:
    section = _step_29r_section(_read_registry())
    assert _field_value(section, "STEP_29R_OFFLINE_TRANSFORMATION_SLICE_IMPLEMENTED") == "true"
    assert _field_value(section, "ADAPTER_TRANSFORMATION_IMPLEMENTED") == "true"
    assert _field_value(section, "STEP_29R_DOES_NOT_IMPLEMENT_RUNTIME_REWIRE") == "true"
    assert _field_value(section, "STEP_29R_REGISTRY_START_ONLY") == "false"

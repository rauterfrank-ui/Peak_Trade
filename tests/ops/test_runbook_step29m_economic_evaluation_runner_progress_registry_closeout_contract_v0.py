"""Contract tests for RUNBOOK STEP 29M economic evaluation runner progress registry closeout v0.

Verifies PR #4723 runner-slice registry closeout without claiming real evaluation,
economic validity pass, promotion eligibility, or runtime authority.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

RUNNER_SLICE = "real_admissible_futures_economic_evidence_evaluation_v1_offline_slice"
STEP_29M_IMPLEMENTED_SCOPE = (
    "economic_viability_evidence_v1_offline_slice,"
    "economic_viability_evidence_v1_persistence_load_reproducibility_slice,"
    "economic_validity_policy_v1_contract_slice,"
    "funding_model_binding_v1_slice,"
    "parameter_sensitivity_evidence_binding_v1_slice,"
    "admissible_versioned_futures_dataset_binding_v1_slice,"
    "economic_validity_policy_threshold_values_v1_slice,"
    f"{RUNNER_SLICE},"
    "real_admissible_futures_economic_evaluation_operator_input_and_admissibility_closure_v0_slice,"
    "real_okx_inst_eth_usdt_perp_economic_evaluation_v1_offline_slice"
)
MERGE_COMMIT = "aa1a8fd9d3444e5d5f3dbe2386d4114b2e48b0c9"
HISTORICAL_SLICES = tuple(
    slice_name for slice_name in STEP_29M_IMPLEMENTED_SCOPE.split(",") if slice_name != RUNNER_SLICE
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


def _step_29n_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1")
    end = text.index("#### RUNBOOK_STEP_29J (legacy heading)", start)
    return text[start:end]


def test_runbook_step_29m_complete_true() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29M_COMPLETE") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29M_COMPLETE") == "true"
    assert _field_value(section, "STATUS") == "COMPLETE"


def test_economic_gate_evaluator_bound_true() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "ECONOMIC_GATE_EVALUATOR_BOUND") == "true"
    assert _field_value(section, "ECONOMIC_GATE_EVALUATOR_BOUND") == "true"
    assert _field_value(section, "ECONOMIC_EVALUATION_RUNNER_V1_BOUND") == "true"


def test_runner_slice_registered_in_implemented_scope() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    global_scope = _field_value(text, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    section_scope = _field_value(section, "RUNBOOK_STEP_29M_IMPLEMENTED_SCOPE")
    assert global_scope == STEP_29M_IMPLEMENTED_SCOPE
    assert section_scope == STEP_29M_IMPLEMENTED_SCOPE
    assert RUNNER_SLICE in global_scope.split(",")
    for historical_slice in HISTORICAL_SLICES:
        assert historical_slice in global_scope


def test_real_evaluation_attempted_and_v2_performed() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "REAL_EVALUATION_ATTEMPTED") == "true"
    assert _field_value(section, "REAL_EVALUATION_ATTEMPTED") == "true"
    assert _field_value(text, "REAL_EVALUATION_PERFORMED") == "true"
    assert _field_value(section, "REAL_EVALUATION_PERFORMED") == "true"
    assert _field_value(text, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
    assert _field_value(section, "ECONOMIC_VALIDITY_RESULT") == "FAILED"


def test_real_admissible_futures_evidence_present_and_bound() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_PRESENT") == "true"
    assert _field_value(text, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "true"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_PRESENT") == "true"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "true"


def test_real_admissible_futures_evidence_required_true() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_REQUIRED") == "true"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_REQUIRED") == "true"


def test_economic_validity_failed_and_offline_gate_false() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
    assert _field_value(text, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(text, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
    assert _field_value(section, "ECONOMIC_VALIDITY_PROVEN") == "false"
    assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"


def test_current_promotion_evaluation_ineligible() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "CURRENT_PROMOTION_EVALUATION") == "INELIGIBLE"
    assert _field_value(section, "CURRENT_PROMOTION_EVALUATION") == "INELIGIBLE"
    assert _field_value(text, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"


def test_operator_input_not_required_after_macd_v1_v2_evaluation() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "OPERATOR_INPUT_REQUIRED_FOR_REAL_EVALUATION") == "false"
    assert _field_value(section, "OPERATOR_INPUT_REQUIRED_FOR_REAL_EVALUATION") == "false"
    assert _field_value(text, "REAL_EVALUATION_PERFORMED") == "true"
    assert _field_value(section, "REAL_EVALUATION_PERFORMED") == "true"
    assert _field_value(text, "REAL_EVALUATION_INPUT_STATUS") == "MACD_V1_EVALUATION_V2_COMPLETE"


def test_kraken_and_venue_fixtures_excluded_from_canonical_economic_path() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "KRAKEN_FIXTURE_LEAK_INTO_CANONICAL_ECONOMIC_PATH") == "false"
    assert _field_value(text, "VENUE_SPECIFIC_CANONICAL_ECONOMIC_PATH_ALLOWED") == "false"
    assert _field_value(section, "KRAKEN_FIXTURE_LEAK_INTO_CANONICAL_ECONOMIC_PATH") == "false"
    assert _field_value(section, "VENUE_SPECIFIC_CANONICAL_ECONOMIC_PATH_ALLOWED") == "false"


def test_runtime_rewire_and_step_29s_not_started() -> None:
    text = _read_registry()
    assert _field_value(text, "RUNTIME_REWIRE_IMPLEMENTATION_ALLOWED") == "false"
    assert _field_value(text, "RUNBOOK_STEP_29R_COMPLETE") == "false"
    assert _field_value(text, "STEP_29S_STARTED") == "false"


def test_progress_registry_closeout_performed_true() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"


def test_registry_closeout_does_not_imply_economic_pass_or_promotion() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(text, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
    assert _field_value(text, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert _field_value(text, "CURRENT_PROMOTION_EVALUATION") == "INELIGIBLE"
    assert _field_value(section, "PROMOTION_ELIGIBILITY_GRANTED") == "false"
    assert _field_value(section, "RUNTIME_AUTHORITY_GRANTED") == "false"


def test_step_29n_history_preserved() -> None:
    text = _read_registry()
    section = _step_29n_section(text)
    assert _field_value(text, "RUNBOOK_STEP_29N_COMPLETE") == "true"
    assert _field_value(section, "RUNBOOK_STEP_29N_COMPLETE") == "true"
    assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"
    assert _field_value(section, "STATUS") == "COMPLETE"


def test_global_closeout_not_permanently_bound_to_29m_section_snapshot() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(section, "STEP_29N_STARTED") == "false"
    assert _field_value(text, "STEP_29N_STARTED") == "true"
    assert _field_value(text, "RUNBOOK_STEP_29R_STARTED") == "true"


def test_no_runtime_order_network_or_live_effects() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "RUNTIME_EFFECT") == "false"
    assert _field_value(text, "ORDER_EFFECT") == "false"
    assert _field_value(text, "NETWORK_EFFECT") == "false"
    assert _field_value(text, "LIVE_AUTHORIZED") == "false"
    assert _field_value(section, "RUNTIME_EFFECT") == "false"
    assert _field_value(section, "ORDER_EFFECT") == "false"
    assert _field_value(section, "NETWORK_EFFECT") == "false"
    assert _field_value(section, "LIVE_AUTHORIZED") == "false"


def test_futures_only_and_bitcoin_direction_forbidden() -> None:
    text = _read_registry()
    section = _step_29m_section(text)
    assert _field_value(text, "FUTURES_ONLY") == "true"
    assert _field_value(section, "FUTURES_ONLY") == "true"
    assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"


def test_merged_pr_and_commit_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert "#4723" in section
    assert MERGE_COMMIT in section


def test_canonical_runner_owner_bound() -> None:
    section = _step_29m_section(_read_registry())
    assert (
        _field_value(section, "CANONICAL_RUNNER_OWNER")
        == "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
    )

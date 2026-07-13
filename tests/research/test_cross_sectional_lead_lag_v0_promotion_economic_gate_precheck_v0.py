"""Contract tests for lead-lag v0 promotion economic gate precheck v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN,
    load_versioned_hypothesis_binding_v0,
    run_promotion_economic_gate_precheck_dispatch_v0,
    validate_entry_point_go_token_v0,
)
from src.research.cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0 import (
    CANONICAL_PROMOTION_GATE_OWNER,
    OPERATOR_GO,
    NEGATIVE_PATH_CASES,
    build_lead_lag_promotion_gate_precheck_context_v0,
    evaluate_deterministic_double_execution_v0,
    evaluate_lead_lag_promotion_economic_gate_precheck_v0,
    evaluate_negative_path_matrix_v0,
    evaluate_promotion_gate_from_context_v0,
    materialize_promotion_gate_precheck_contract_v0,
    run_promotion_economic_gate_precheck_dispatch_v0 as run_precheck_dispatch,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / (
    "src/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


def _scan_forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(
                    alias.name.startswith(prefix) for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES
                ):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module.startswith(prefix) for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES):
                hits.append(node.module)
    return hits


def test_go_token_registered_in_entry_point_dispatch() -> None:
    ok, branch = validate_entry_point_go_token_v0(PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN)
    assert ok is True
    assert branch == "PROMOTION_ECONOMIC_GATE_PRECHECK_V0"


def test_precheck_contract_declares_canonical_promotion_gate_owner() -> None:
    contract = materialize_promotion_gate_precheck_contract_v0()
    assert contract["operator_go"] == OPERATOR_GO
    assert contract["canonical_promotion_gate_owner"] == CANONICAL_PROMOTION_GATE_OWNER
    assert contract["canonical_promotion_gate_owner"] == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER
    assert contract["reuse_decision"] == "REUSE_WITH_NARROW_ADAPTER"
    assert contract["economic_evaluation_executed"] is False
    assert contract["system_economic_evidence_admissible"] is False
    assert contract["authority_effect"] == "NONE"
    assert contract["runtime_effect"] == "NONE"


def test_slice_sources_exclude_runtime_imports() -> None:
    assert CONTRACT_MODULE.is_file()
    hits = _scan_forbidden_imports(CONTRACT_MODULE)
    assert hits == []


def test_config_json_matches_contract() -> None:
    config_path = (
        REPO_ROOT
        / "config/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.json"
    )
    assert config_path.is_file()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["operator_go"] == OPERATOR_GO
    assert config["canonical_promotion_gate_owner"] == CANONICAL_PROMOTION_GATE_OWNER


def test_baseline_precheck_executes_real_promotion_gate_fail_closed() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    result = evaluate_lead_lag_promotion_economic_gate_precheck_v0(
        versioned_binding=binding,
    )
    assert result.promotion_economic_gate_v1_real_owner_executed is True
    assert result.structural_gate_input_binding_pass is True
    assert result.eligible_for_promotion_candidate is False
    assert result.economic_validity_offline_gate_pass is False
    assert result.economic_evaluation_executed is False
    assert result.system_economic_evidence_admissible is False
    assert result.gate_result.authority_effect == gate.AUTHORITY_EFFECT_NONE
    assert result.gate_result.runtime_effect == gate.RUNTIME_EFFECT_NONE
    assert gate.REASON_ECONOMIC_EVIDENCE_INADMISSIBLE in result.gate_result.reason_codes


def test_gate_decision_field_and_order_parity() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    result = evaluate_lead_lag_promotion_economic_gate_precheck_v0(versioned_binding=binding)
    assert result.gate_decision_field_parity_pass is True
    assert result.gate_reason_code_parity_pass is True
    assert result.gate_decision_order_parity_pass is True
    assert list(result.gate_result.reason_codes) == sorted(result.gate_result.reason_codes)


def test_deterministic_double_execution() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    ok, payload = evaluate_deterministic_double_execution_v0(versioned_binding=binding)
    assert ok is True
    assert payload["first_evaluation_digest"] == payload["second_evaluation_digest"]


def test_negative_path_matrix_fail_closed() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    matrix = evaluate_negative_path_matrix_v0(versioned_binding=binding)
    assert matrix["negative_path_fail_closed_pass"] is True
    for case_name in NEGATIVE_PATH_CASES:
        assert matrix["cases"][case_name]["fail_closed"] is True


def test_legacy_confidence_only_bypass_blocked() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    ctx = build_lead_lag_promotion_gate_precheck_context_v0(
        versioned_binding=binding,
        overrides={"promotion_basis_confidence_only": True},
    )
    gate_result = evaluate_promotion_gate_from_context_v0(ctx)
    assert gate_result.eligible_for_promotion_candidate is False
    assert gate.REASON_CONFIDENCE_SCORE_ONLY in gate_result.reason_codes


def test_missing_economic_evidence_blocked() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    ctx = build_lead_lag_promotion_gate_precheck_context_v0(
        versioned_binding=binding,
        overrides={"economic_viability_evidence_ref": ""},
    )
    gate_result = evaluate_promotion_gate_from_context_v0(ctx)
    assert gate_result.eligible_for_promotion_candidate is False
    assert gate.REASON_ECONOMIC_EVIDENCE_MISSING in gate_result.reason_codes


def test_dispatch_wrapper_reports_precheck_complete() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    payload = run_precheck_dispatch(
        repo_root=REPO_ROOT,
        versioned_binding=binding,
        operator_go=OPERATOR_GO,
    )
    assert payload["promotion_economic_gate_precheck_complete"] is True
    assert payload["promotion_economic_gate_v1_real_owner_executed"] is True
    assert payload["structural_gate_input_binding_pass"] is True
    assert payload["negative_path_fail_closed_pass"] is True
    assert payload["legacy_confidence_only_bypass_reachable"] is False
    assert payload["economic_evaluation_executed"] is False
    assert payload["eligible_for_promotion_candidate"] is False
    assert payload["system_economic_evidence_admissible"] is False


def test_execution_owner_dispatch_wrapper() -> None:
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    requested_go = PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN
    payload = run_promotion_economic_gate_precheck_dispatch_v0(
        repo_root=REPO_ROOT,
        versioned_binding=binding,
        go_token=requested_go,
    )
    assert payload["dispatch_rc"] == 0
    assert payload["promotion_economic_gate_precheck_complete"] is True

"""Focused tests: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1 contract."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.pre_economic_zero_order_evidence_session_contract_v1 import (
    ACTIVATION_TOKEN_KEYS,
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    ECONOMIC_GATE_STILL_REQUIRED_FOR,
    MAX_DURATION_SECONDS,
    PACKAGE_MARKER,
    POLICY_SEQUENCE_AFTER,
    POLICY_SEQUENCE_BEFORE,
    REQUIRED_DECISION_LOGIC_BINDINGS,
    SAFETY_NON_GOALS,
    SESSION_CONTRACT_ID,
    PreEconomicZeroOrderEvidenceSessionOverridesV1,
    economic_gate_blocks_step,
    evaluate_pre_economic_zero_order_evidence_session_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src/ops/pre_economic_zero_order_evidence_session_contract_v1.py"
CLI = REPO_ROOT / "scripts/ops/run_pre_economic_zero_order_evidence_session_contract_v1.py"
CONTRACT_DOC = REPO_ROOT / "docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1.md"
RUNBOOK = REPO_ROOT / "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"
SHADOW_TOML = REPO_ROOT / "config/ops/shadow_preparation_readiness_gate_v0.toml"
SHADOW_CONTRACT = REPO_ROOT / "docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
STEP29U_ELIGIBILITY = (
    REPO_ROOT / "docs/ops/runbooks/STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0.md"
)


FORBIDDEN_IMPORT_PREFIXES = (
    "src.orders",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.webui",
)


def _all_bindings_true() -> dict[str, bool]:
    return {k: True for k in REQUIRED_DECISION_LOGIC_BINDINGS}


def test_package_and_schema_identity() -> None:
    assert PACKAGE_MARKER == "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1=true"
    assert CAPABILITY_ID == "GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1"
    assert SESSION_CONTRACT_ID == "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1"
    assert MAX_DURATION_SECONDS == 21600


def test_default_evaluation_is_blocked_without_operator_go() -> None:
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1()
    assert result.authority_effect == AUTHORITY_EFFECT_NONE
    assert result.activation_effect == "NONE"
    assert result.economic_gate_effect == "NONE"
    assert result.default_state == "BLOCKED"
    assert result.runtime_execution == "BLOCKED"
    assert result.orders_allowed is False
    assert result.broker_writes_allowed is False
    assert result.session_admissible is False
    assert result.six_hour_session_ready is False
    assert "EXPLICIT_OPERATOR_GO_ABSENT" in result.blockers
    assert result.economic_validity_offline_gate_pass_changed is False
    for key in ACTIVATION_TOKEN_KEYS:
        assert result.activation_tokens[key] is False


def test_cannot_set_economic_pass_or_activation_tokens() -> None:
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=True,
            decision_logic_bound=_all_bindings_true(),
            implementation_readiness_passed=True,
            economic_validity_offline_gate_pass=True,
        )
    )
    # Even if an override reports historical/current economic truth, this stage
    # must not claim it changed the gate and must not flip activation tokens.
    assert result.economic_validity_offline_gate_pass_changed is False
    assert result.economic_gate_effect == "NONE"
    for key in ACTIVATION_TOKEN_KEYS:
        assert result.activation_tokens[key] is False
    assert "NOT_ECONOMIC_PASS" in result.safety_non_goals
    assert "NOT_SHADOW_ACTIVATION" in result.safety_non_goals


def test_duration_over_21600_rejected() -> None:
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=True,
            requested_duration_seconds=21601,
            decision_logic_bound=_all_bindings_true(),
            implementation_readiness_passed=True,
        )
    )
    assert result.session_admissible is False
    assert "DURATION_EXCEEDS_MAX_21600" in result.blockers
    assert result.six_hour_session_ready is False


def test_orders_and_broker_writes_fail_closed() -> None:
    order_result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=True,
            order_intent_observed=True,
            decision_logic_bound=_all_bindings_true(),
            implementation_readiness_passed=True,
        )
    )
    assert "ORDER_INTENT_FORBIDDEN" in order_result.blockers
    assert order_result.session_admissible is False

    broker_result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=True,
            broker_write_observed=True,
            decision_logic_bound=_all_bindings_true(),
            implementation_readiness_passed=True,
        )
    )
    assert "BROKER_WRITE_FORBIDDEN" in broker_result.blockers
    assert broker_result.session_admissible is False


def test_missing_decision_logic_bindings_block_readiness() -> None:
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=True,
            decision_logic_bound={"DOUBLE_PLAY": True},
            implementation_readiness_passed=True,
        )
    )
    assert result.decision_logic_complete is False
    assert any(b.startswith("INCOMPLETE_DECISION_LOGIC_BINDING:") for b in result.blockers)
    assert result.six_hour_session_ready is False
    for required in REQUIRED_DECISION_LOGIC_BINDINGS:
        if required != "DOUBLE_PLAY":
            assert required in ",".join(result.blockers)


def test_economic_gate_still_required_for_29r_29t_29u_and_live_paths() -> None:
    for step in (
        "STEP_29R_RUNTIME_REWIRE",
        "STEP_29T_ZERO_ORDER_RUNTIME",
        "PROMOTION",
        "TESTNET",
        "LIVE",
    ):
        assert step in ECONOMIC_GATE_STILL_REQUIRED_FOR
        assert economic_gate_blocks_step(step, economic_validity_offline_gate_pass=False) is True
        assert economic_gate_blocks_step(step, economic_validity_offline_gate_pass=True) is False
    # Paper-Shadow observation readiness is not blocked by legacy offline gate alone.
    assert "STEP_29U_SHADOW" not in ECONOMIC_GATE_STILL_REQUIRED_FOR
    assert "PAPER" not in ECONOMIC_GATE_STILL_REQUIRED_FOR
    assert (
        economic_gate_blocks_step("STEP_29U_SHADOW", economic_validity_offline_gate_pass=False)
        is False
    )
    assert economic_gate_blocks_step("PAPER", economic_validity_offline_gate_pass=False) is False


def test_policy_sequence_inserts_pre_economic_stage() -> None:
    assert POLICY_SEQUENCE_BEFORE == (
        "INTEGRATED_OFFLINE_REPLAY",
        "ECONOMIC_VALIDITY_OFFLINE_GATE",
        "PROMOTION",
        "STEP_29R_RUNTIME_REWIRE",
        "STEP_29T_ZERO_ORDER_RUNTIME",
        "STEP_29U_SHADOW",
    )
    assert POLICY_SEQUENCE_AFTER == (
        "FULL_CANONICAL_SYSTEM_PARITY",
        "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS",
        "INTEGRATED_PAPER_SHADOW_OBSERVATION_READINESS_PASS",
        "OPERATOR_PAPER_SHADOW_OBSERVATION_GO",
        "INTEGRATED_PAPER_SHADOW_OBSERVATION",
        "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE",
        "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED",
        "ECONOMIC_VALIDITY_PASS",
        "PROMOTION",
        "TESTNET",
        "LIVE",
    )
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1()
    assert result.policy_sequence_after == POLICY_SEQUENCE_AFTER


def test_implementation_readiness_gap_keeps_six_hour_not_ready() -> None:
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=True,
            decision_logic_bound=_all_bindings_true(),
            implementation_readiness_passed=False,
            requested_duration_seconds=21600,
        )
    )
    assert "IMPLEMENTATION_READINESS_NOT_PASSED" in result.blockers
    assert result.six_hour_session_ready is False
    assert result.runtime_execution == "BLOCKED"


def test_shadow_and_live_safety_rules_remain_in_repo_surfaces() -> None:
    toml_text = SHADOW_TOML.read_text(encoding="utf-8")
    assert "economic_validity_offline_gate_pass = false" in toml_text
    assert 'ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"' in toml_text or (
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS" in toml_text
    )
    assert "shadow_activation_authorized = false" in toml_text
    assert "live_authorized = false" in toml_text
    assert "orders_authorized = false" in toml_text

    eligibility = STEP29U_ELIGIBILITY.read_text(encoding="utf-8")
    assert "ECONOMIC_VALIDITY_PROVEN" in eligibility
    assert "ACTIVATION_ELIGIBLE=false" in eligibility

    shadow_contract = SHADOW_CONTRACT.read_text(encoding="utf-8")
    assert "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false" in shadow_contract or (
        "ECONOMIC_READINESS" in shadow_contract
    )
    assert "SHADOW_ACTIVATION_AUTHORIZED=false" in shadow_contract


def test_runbook_and_contract_docs_ratify_stage() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE" in runbook
    assert "GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1" in runbook
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "MAX_DURATION_SECONDS=21600" in doc
    assert "AUTHORITY_EFFECT=NONE" in doc
    assert "NOT_SHADOW_ACTIVATION=true" in doc
    for goal in (
        "NOT_ECONOMIC_PASS",
        "NOT_LIVE_AUTHORIZATION",
        "NOT_ORDER_AUTHORITY",
    ):
        assert goal in SAFETY_NON_GOALS
        assert goal in doc


def test_no_forbidden_runtime_imports() -> None:
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for mod in imported:
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert not mod.startswith(prefix), mod


def test_cli_evaluate_only_exit_zero(tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    proc = subprocess.run(
        [sys.executable, str(CLI), "--json", "--output-path", str(out)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["session_admissible"] is False
    assert payload["six_hour_session_ready"] is False
    assert payload["orders_allowed"] is False
    assert payload["economic_validity_offline_gate_pass_changed"] is False

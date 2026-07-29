"""Runtime bridge pre-activation gate contract tests (offline only)."""

from __future__ import annotations

from dataclasses import replace

from trading.master_v2.runtime_bridge_pre_activation_gate_v0 import (
    CONTRACT_NAME,
    PACKAGE_MARKER,
    RuntimeBridgePreActivationGateInputV0,
    current_head_default_gate_input_v0,
    evaluate_runtime_bridge_pre_activation_gate_v0,
)


def _all_pass_input() -> RuntimeBridgePreActivationGateInputV0:
    return RuntimeBridgePreActivationGateInputV0(
        operator_go_token_status="PASS",
        full_canonical_chain_wired_status="PASS",
        backtest_runtime_decision_parity_status="PASS",
        system_economic_evidence_admissible_status="PASS",
        integrated_economic_evidence_bundle_verified_status="PASS",
        surface_p_status="PASS",
        canonical_order_intent_adapter_compatibility_status="PASS",
        runtime_rewire_eligibility_status="PASS",
        runtime_rewire_activation_contract_status="PASS",
        zero_order_pre_activation_evidence_status="PASS",
        legacy_entrypoint_guard_status="PASS_DEAUTHORIZED_UNTIL_CANONICAL_PATH",
        shadow_paper_testnet_canary_gate_status="SEPARATELY_GATED",
    )


def test_contract_constants_v0() -> None:
    assert CONTRACT_NAME == "RuntimeBridgePreActivationGateContractV0"
    assert PACKAGE_MARKER == "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_CONTRACT_V0=true"


def test_current_head_default_snapshot_evaluates_fail_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(current_head_default_gate_input_v0())
    assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert result.runtime_bridge_activation_admissible is False


def test_any_single_non_pass_gate_evaluates_fail_v0() -> None:
    base = _all_pass_input()
    for field in (
        "operator_go_token_status",
        "full_canonical_chain_wired_status",
        "backtest_runtime_decision_parity_status",
        "system_economic_evidence_admissible_status",
        "integrated_economic_evidence_bundle_verified_status",
        "surface_p_status",
        "canonical_order_intent_adapter_compatibility_status",
        "runtime_rewire_eligibility_status",
        "runtime_rewire_activation_contract_status",
        "zero_order_pre_activation_evidence_status",
    ):
        result = evaluate_runtime_bridge_pre_activation_gate_v0(replace(base, **{field: "FAIL"}))
        assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
        assert result.runtime_bridge_activation_admissible is False


def test_all_gates_pass_evaluates_pre_activation_readiness_pass_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(_all_pass_input())
    assert result.runtime_bridge_pre_activation_gate_status == "PASS"
    assert result.runtime_bridge_activation_admissible is True


def test_pass_output_keeps_authority_effect_none_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(_all_pass_input())
    assert result.authority_effect == "NONE"


def test_pass_output_keeps_runtime_effect_none_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(_all_pass_input())
    assert result.runtime_effect == "NONE"


def test_pass_output_keeps_order_effect_none_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(_all_pass_input())
    assert result.order_effect == "NONE"


def test_pass_output_keeps_execution_eligible_false_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(_all_pass_input())
    assert result.execution_eligible is False


def test_pass_output_keeps_adapter_compatible_false_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(_all_pass_input())
    assert result.adapter_compatible is False


def test_wrong_legacy_entrypoint_guard_status_fails_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(
        replace(_all_pass_input(), legacy_entrypoint_guard_status="FAIL")
    )
    assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert "legacy_entrypoint_guard_status!=FAIL" in result.blocking_reasons


def test_wrong_shadow_paper_testnet_canary_gate_status_fails_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(
        replace(_all_pass_input(), shadow_paper_testnet_canary_gate_status="FAIL")
    )
    assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert "shadow_paper_testnet_canary_gate_status!=FAIL" in result.blocking_reasons


def test_fail_populates_blocking_reasons_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(current_head_default_gate_input_v0())
    assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert len(result.blocking_reasons) > 0


def test_fail_populates_required_next_gates_v0() -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_v0(current_head_default_gate_input_v0())
    assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert len(result.required_next_gates) > 0

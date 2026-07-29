"""
Runtime Bridge Pre-Activation Gate Contract v0.

Fail-closed evaluator-only contract determining whether a later Runtime-Bridge
activation slice may be considered for separate Operator-GO review.

No runtime authority, no bridge activation, no orders, no IO, no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_LAYER_VERSION = "v0"
RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_OWNER = "trading.master_v2.runtime_bridge_pre_activation_gate_v0"
CONTRACT_NAME = "RuntimeBridgePreActivationGateContractV0"
PACKAGE_MARKER = "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_CONTRACT_V0=true"

GateStatus = Literal["PASS", "FAIL"]
LegacyEntrypointGuardStatus = Literal["PASS_DEAUTHORIZED_UNTIL_CANONICAL_PATH", "FAIL"]
ShadowPaperTestnetCanaryGateStatus = Literal["SEPARATELY_GATED", "FAIL"]
PreActivationGateStatus = Literal["PASS", "FAIL"]

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"

_GATE_FIELD_ORDER: Tuple[str, ...] = (
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
    "legacy_entrypoint_guard_status",
    "shadow_paper_testnet_canary_gate_status",
)

_REQUIRED_NEXT_GATE_BY_FIELD: dict[str, str] = {
    "operator_go_token_status": "OPERATOR_GO_SEPARATE_RUNTIME_BRIDGE_ACTIVATION",
    "full_canonical_chain_wired_status": "FULL_CANONICAL_CHAIN_WIRED_PASS",
    "backtest_runtime_decision_parity_status": "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
    "system_economic_evidence_admissible_status": "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE",
    "integrated_economic_evidence_bundle_verified_status": (
        "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED"
    ),
    "surface_p_status": "SURFACE_P_STATUS_PASS",
    "canonical_order_intent_adapter_compatibility_status": (
        "CANONICAL_ORDER_INTENT_ADAPTER_COMPATIBILITY_PROVEN"
    ),
    "runtime_rewire_eligibility_status": "RUNTIME_REWIRE_ELIGIBILITY_PROVEN",
    "runtime_rewire_activation_contract_status": "RUNTIME_REWIRE_ACTIVATION_BOUND_CONTRACT",
    "zero_order_pre_activation_evidence_status": "ZERO_ORDER_PRE_ACTIVATION_EVIDENCE",
    "legacy_entrypoint_guard_status": (
        "LEGACY_ENTRYPOINTS_REMAIN_DEAUTHORIZED_UNTIL_CANONICAL_PATH"
    ),
    "shadow_paper_testnet_canary_gate_status": "SHADOW_PAPER_TESTNET_CANARY_OPERATOR_GATES",
}


@dataclass(frozen=True)
class RuntimeBridgePreActivationGateInputV0:
    operator_go_token_status: GateStatus
    full_canonical_chain_wired_status: GateStatus
    backtest_runtime_decision_parity_status: GateStatus
    system_economic_evidence_admissible_status: GateStatus
    integrated_economic_evidence_bundle_verified_status: GateStatus
    surface_p_status: GateStatus
    canonical_order_intent_adapter_compatibility_status: GateStatus
    runtime_rewire_eligibility_status: GateStatus
    runtime_rewire_activation_contract_status: GateStatus
    zero_order_pre_activation_evidence_status: GateStatus
    legacy_entrypoint_guard_status: LegacyEntrypointGuardStatus
    shadow_paper_testnet_canary_gate_status: ShadowPaperTestnetCanaryGateStatus


@dataclass(frozen=True)
class RuntimeBridgePreActivationGateResultV0:
    runtime_bridge_pre_activation_gate_status: PreActivationGateStatus
    runtime_bridge_activation_admissible: bool
    blocking_reasons: Tuple[str, ...]
    required_next_gates: Tuple[str, ...]
    authority_effect: Literal["NONE"]
    runtime_effect: Literal["NONE"]
    order_effect: Literal["NONE"]
    execution_eligible: bool
    adapter_compatible: bool


def _gate_values(inp: RuntimeBridgePreActivationGateInputV0) -> dict[str, str]:
    return {field: getattr(inp, field) for field in _GATE_FIELD_ORDER}


def _is_gate_pass(field: str, value: str) -> bool:
    if field == "legacy_entrypoint_guard_status":
        return value == "PASS_DEAUTHORIZED_UNTIL_CANONICAL_PATH"
    if field == "shadow_paper_testnet_canary_gate_status":
        return value == "SEPARATELY_GATED"
    return value == "PASS"


def evaluate_runtime_bridge_pre_activation_gate_v0(
    inp: RuntimeBridgePreActivationGateInputV0,
) -> RuntimeBridgePreActivationGateResultV0:
    """Evaluate pre-activation gate inputs fail-closed; never grants runtime authority."""
    values = _gate_values(inp)
    blocking_reasons: list[str] = []
    required_next_gates: list[str] = []

    for field in _GATE_FIELD_ORDER:
        value = values[field]
        if not _is_gate_pass(field, value):
            blocking_reasons.append(f"{field}!={value}")
            required_next_gates.append(_REQUIRED_NEXT_GATE_BY_FIELD[field])

    gate_pass = not blocking_reasons
    return RuntimeBridgePreActivationGateResultV0(
        runtime_bridge_pre_activation_gate_status="PASS" if gate_pass else "FAIL",
        runtime_bridge_activation_admissible=gate_pass,
        blocking_reasons=tuple(blocking_reasons),
        required_next_gates=tuple(dict.fromkeys(required_next_gates)),
        authority_effect=_AUTHORITY_EFFECT_NONE,
        runtime_effect=_RUNTIME_EFFECT_NONE,
        order_effect=_ORDER_EFFECT_NONE,
        execution_eligible=False,
        adapter_compatible=False,
    )


def _bool_to_gate_status(value: bool) -> GateStatus:
    return "PASS" if value else "FAIL"


def current_head_default_gate_input_v0() -> RuntimeBridgePreActivationGateInputV0:
    """Reuse-first static snapshot aligned with gap assessment @ current main."""
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
    )
    from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
        CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
        SLICE_D_STATUS,
    )
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
    )

    final_flags = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")

    legacy_ok = (
        SLICE_D_STATUS == "LEGACY_RUNTIME_ENTRYPOINTS_DEAUTHORIZED"
        and CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"
    )

    return RuntimeBridgePreActivationGateInputV0(
        operator_go_token_status="FAIL",
        full_canonical_chain_wired_status=_bool_to_gate_status(
            final_flags.full_canonical_chain_wired
        ),
        backtest_runtime_decision_parity_status=_bool_to_gate_status(
            final_flags.backtest_runtime_decision_parity_pass
        ),
        system_economic_evidence_admissible_status=_bool_to_gate_status(
            final_flags.system_economic_evidence_admissible
        ),
        # System economic validity requires INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED.
        # Legacy ECONOMIC_VALIDITY_OFFLINE_GATE_PASS is sub-evidence only and is not
        # a Runtime-Bridge pre-activation hard gate after the reconciled ladder.
        integrated_economic_evidence_bundle_verified_status="FAIL",
        surface_p_status="PASS" if surface_p.parity_status == "PASS" else "FAIL",
        canonical_order_intent_adapter_compatibility_status="FAIL",
        runtime_rewire_eligibility_status="FAIL",
        runtime_rewire_activation_contract_status="PASS",
        zero_order_pre_activation_evidence_status="FAIL",
        legacy_entrypoint_guard_status=(
            "PASS_DEAUTHORIZED_UNTIL_CANONICAL_PATH" if legacy_ok else "FAIL"
        ),
        shadow_paper_testnet_canary_gate_status="SEPARATELY_GATED",
    )

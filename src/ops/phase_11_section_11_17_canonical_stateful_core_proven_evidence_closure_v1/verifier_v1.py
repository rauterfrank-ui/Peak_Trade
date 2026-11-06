"""Verifier for Phase 11 §11.17 CANONICAL_STATEFUL_CORE_PROVEN evidence closure."""

from __future__ import annotations

from typing import Any

from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.binding_v1 import (
    CanonicalStatefulCoreProvenBindingError,
    bind_canonical_stateful_core_proven_from_cap72_v1,
)
from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_ACCESS,
    FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN,
    LIVE_AUTONOMOUS_DEGRADATION_PROVEN,
    LIVE_AUTONOMOUS_RECOVERY_PROVEN,
    LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN,
    LIVE_EVIDENCE_VERIFIED,
    LIVE_KILL_SWITCH_PROVEN,
    LIVE_ORDER_LIFECYCLE_PROVEN,
    LIVE_PARTIAL_FILL_RECOVERY_PROVEN,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_RECONCILIATION_PROVEN,
    LIVE_RESTART_PROVEN,
    LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
    NETWORK_SESSION_STARTED,
    ORDER_SUBMIT_REACHABLE,
    OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION,
    OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE,
    CORE_LOGIC_PARITY_ACROSS_MODES,
    SIMULATED_LIFECYCLE_PROVEN,
    TESTNET_LIFECYCLE_PROVEN,
)


def verify_phase_11_section_11_17_canonical_stateful_core_proven_v1() -> dict[str, Any]:
    try:
        binding = bind_canonical_stateful_core_proven_from_cap72_v1()
    except CanonicalStatefulCoreProvenBindingError as exc:
        return {
            "ok": False,
            "VERIFIER_RESULT": "FAIL",
            "error": str(exc),
            "CAPABILITY_ID": CAPABILITY_ID,
        }

    residual_ok = all(
        [
            SIMULATED_LIFECYCLE_PROVEN is False,
            TESTNET_LIFECYCLE_PROVEN is False,
            LIVE_PRIVATE_READ_ONLY_PROVEN is False,
            LIVE_ORDER_LIFECYCLE_PROVEN is False,
            LIVE_RECONCILIATION_PROVEN is False,
            LIVE_RESTART_PROVEN is False,
            LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN is False,
            LIVE_PARTIAL_FILL_RECOVERY_PROVEN is False,
            LIVE_KILL_SWITCH_PROVEN is False,
            LIVE_AUTONOMOUS_DEGRADATION_PROVEN is False,
            LIVE_AUTONOMOUS_RECOVERY_PROVEN is False,
            LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN is False,
            LIVE_EVIDENCE_VERIFIED is False,
            OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION is True,
            OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE is True,
            CORE_LOGIC_PARITY_ACROSS_MODES is True,
            FULLY_AUTONOMOUS_LIVE_TRADING_READY is False,
            FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE is False,
            CAPABILITY_11_13_STARTED is False,
            NETWORK_SESSION_STARTED is False,
            CREDENTIAL_ACCESS is False,
            ORDER_SUBMIT_REACHABLE is False,
            CORE_LOGIC_CHANGE is False,
            ACTIVATION_STATE == "not_activated",
            binding.get("CANONICAL_STATEFUL_CORE_PROVEN") is True,
            binding.get("ok") is True,
            binding.get("FIXTURE_ONLY") is False,
        ]
    )
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "CANONICAL_STATEFUL_CORE_PROVEN": True,
        "SIMULATED_LIFECYCLE_PROVEN": False,
        "TESTNET_LIFECYCLE_PROVEN": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "LIVE_ORDER_LIFECYCLE_PROVEN": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "LIVE_RESTART_PROVEN": False,
        "LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN": False,
        "LIVE_PARTIAL_FILL_RECOVERY_PROVEN": False,
        "LIVE_KILL_SWITCH_PROVEN": False,
        "LIVE_AUTONOMOUS_DEGRADATION_PROVEN": False,
        "LIVE_AUTONOMOUS_RECOVERY_PROVEN": False,
        "LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN": False,
        "LIVE_EVIDENCE_VERIFIED": False,
        "OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION": True,
        "OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE": True,
        "CORE_LOGIC_PARITY_ACROSS_MODES": True,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
        "CAPABILITY_11_13_STARTED": False,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "NETWORK_SESSION_STARTED": False,
        "CREDENTIAL_ACCESS": False,
        "ORDER_SUBMIT_REACHABLE": False,
        "CORE_LOGIC_CHANGE": False,
        "CLOSURE_METHOD": binding.get("CLOSURE_METHOD"),
        "SOURCE_CAPABILITY_ID": binding.get("SOURCE_CAPABILITY_ID"),
        "EVIDENCE_REUSED": True,
        "REPROOF_EXECUTED": False,
        "FIXTURE_ONLY": False,
    }
    ok = residual_ok
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "binding": binding,
        "claims": claims,
    }

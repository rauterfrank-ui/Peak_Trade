"""Negative reachability and core-logic parity proofs for Cap 11.11."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
    construct_testnet_execution_port_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.live_bounded_order_lifecycle_continuity_contract_v1 import (
    LiveBoundedOrderLifecycleContinuityError,
    refuse_live_bounded_order_submit_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.live_bounded_single_future_continuity_contract_v1 import (
    LiveBoundedSingleFutureContinuityError,
    refuse_live_bounded_single_future_activation_v1,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1 as prove_cap_11_10_core_logic_parity_v1,
    prove_negative_reachability_v1 as prove_cap_11_10_negative_reachability_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_11_11_LIVE_AUTONOMOUS_RECOVERY_STARTED,
    CAPABILITY_11_11_STARTED,
    CAPABILITY_11_12_STARTED,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_11,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LIVE_AUTHORIZED,
    LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED,
    LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_ACTIVATED,
    LIVE_AUTONOMOUS_RECOVERY_ACTIVATED,
    LIVE_AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED,
    LIVE_AUTONOMOUS_RECOVERY_OBSERVED,
    LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED,
    LIVE_BOUNDED_MULTI_SESSION_ACTIVATED,
    LIVE_EXECUTION_REACHABLE,
    LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11,
    LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11,
    LIVE_RESTART_RECONSTRUCTED,
    NETWORK_SESSION_STARTED,
    PAPER_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11,
    PRIVATE_NETWORK_SESSION_STARTED,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    REAL_CAPITAL_MOVEMENT_REACHABLE,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_ADAPTER_ACTIVATED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_11,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.live_autonomous_degradation_contract_v1 import (
    LiveAutonomousDegradationError,
    refuse_cap_11_12_live_readiness_v1,
    refuse_live_autonomous_degradation_activation_v1,
    refuse_live_autonomous_degradation_proven_overclaim_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.live_autonomous_recovery_contract_v1 import (
    LiveAutonomousRecoveryError,
    refuse_live_autonomous_recovery_activation_v1,
    refuse_live_autonomous_recovery_credential_access_v1,
    refuse_live_autonomous_recovery_network_session_v1,
    refuse_live_autonomous_recovery_order_submit_v1,
    refuse_live_autonomous_recovery_proven_overclaim_v1,
)
from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.live_autonomous_recovery_evidence_ladder_contract_v1 import (
    LiveAutonomousRecoveryEvidenceLadderError,
    refuse_live_autonomous_recovery_evidence_activation_v1,
    refuse_live_end_to_end_and_beyond_claim_v1,
    refuse_live_restart_or_recovery_observed_overclaim_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_load_gate_v1 import (
    CredentialLoadGateError,
    CredentialLoadGateV1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_execution_adapter_v1 import (
    TestnetExecutionAdapterError,
    construct_testnet_execution_adapter_v1,
    refuse_testnet_network_session_start_v1,
    refuse_testnet_order_submit_v1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.live_private_readonly_port_v1 import (
    LivePrivateReadonlyPortError,
    construct_live_private_readonly_port_v1,
    refuse_live_private_readonly_network_session_v1,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.live_dry_run_order_plan_contract_v1 import (
    LiveDryRunOrderPlanError,
    refuse_live_dry_run_order_submit_v1,
)
from src.ops.capability_11_9_live_canary_order_execution_v1.live_canary_order_execution_contract_v1 import (
    LiveCanaryOrderExecutionError,
    refuse_live_canary_order_submit_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    refuse_real_execution_adapter_construction_v1,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent
_FORBIDDEN_CALL_ATTRS = frozenset(
    {
        "submit_order",
        "submit_orders",
        "place_order",
        "create_order",
        "cancel_order",
        "load_credentials",
        "load_exchange_credentials",
        "urlopen",
        "request",
    }
)


def _scan_package_for_forbidden_calls() -> list[str]:
    hits: list[str] = []
    for path in sorted(_PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            fname = ""
            if isinstance(func, ast.Name):
                fname = func.id
            elif isinstance(func, ast.Attribute):
                fname = func.attr
            if fname in _FORBIDDEN_CALL_ATTRS:
                hits.append(f"{path.name}:{fname}")
    return hits


def prove_negative_reachability_v1() -> dict[str, Any]:
    predecessor = prove_cap_11_10_negative_reachability_v1()

    testnet_port_blocked = False
    try:
        construct_testnet_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        testnet_port_blocked = True

    testnet_adapter_blocked = False
    try:
        construct_testnet_execution_adapter_v1()
    except TestnetExecutionAdapterError:
        testnet_adapter_blocked = True

    live_blocked = False
    try:
        construct_live_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        live_blocked = True

    real_blocked = False
    try:
        refuse_real_execution_adapter_construction_v1()
    except Exception:
        real_blocked = True

    live_private_port_blocked = False
    try:
        construct_live_private_readonly_port_v1()
    except LivePrivateReadonlyPortError:
        live_private_port_blocked = True

    live_private_session_blocked = False
    try:
        refuse_live_private_readonly_network_session_v1(session_id="session-reach-11-11")
    except LivePrivateReadonlyPortError:
        live_private_session_blocked = True

    submit_blocked = False
    try:
        refuse_testnet_order_submit_v1(client_order_id="pt-coid-reach-11-11")
    except TestnetExecutionAdapterError:
        submit_blocked = True

    session_blocked = False
    try:
        refuse_testnet_network_session_start_v1(session_id="session-reach-11-11")
    except TestnetExecutionAdapterError:
        session_blocked = True

    dry_run_submit_blocked = False
    try:
        refuse_live_dry_run_order_submit_v1(client_order_id="pt-coid-reach-11-11")
    except LiveDryRunOrderPlanError:
        dry_run_submit_blocked = True

    canary_submit_blocked = False
    try:
        refuse_live_canary_order_submit_v1(client_order_id="pt-coid-reach-11-11")
    except LiveCanaryOrderExecutionError:
        canary_submit_blocked = True

    bounded_activation_blocked = False
    try:
        refuse_live_bounded_single_future_activation_v1(claimed_action="activate_bounded")
    except LiveBoundedSingleFutureContinuityError:
        bounded_activation_blocked = True

    bounded_submit_blocked = False
    try:
        refuse_live_bounded_order_submit_v1(client_order_id="pt-coid-reach-11-11")
    except LiveBoundedOrderLifecycleContinuityError:
        bounded_submit_blocked = True

    degradation_activation_blocked = False
    try:
        refuse_live_autonomous_degradation_activation_v1(claimed_action="activate_degradation")
    except LiveAutonomousDegradationError:
        degradation_activation_blocked = True

    recovery_activation_blocked = False
    try:
        refuse_live_autonomous_recovery_activation_v1(claimed_action="activate_recovery")
    except LiveAutonomousRecoveryError:
        recovery_activation_blocked = True

    recovery_submit_blocked = False
    try:
        refuse_live_autonomous_recovery_order_submit_v1(client_order_id="pt-coid-reach-11-11")
    except LiveAutonomousRecoveryError:
        recovery_submit_blocked = True

    recovery_session_blocked = False
    try:
        refuse_live_autonomous_recovery_network_session_v1(session_id="live-recovery-reach-11-11")
    except LiveAutonomousRecoveryError:
        recovery_session_blocked = True

    recovery_credential_blocked = False
    try:
        refuse_live_autonomous_recovery_credential_access_v1(claimed_action="load_api_key")
    except LiveAutonomousRecoveryError:
        recovery_credential_blocked = True

    degradation_proven_blocked = False
    try:
        refuse_live_autonomous_degradation_proven_overclaim_v1(
            claimed_field="LIVE_AUTONOMOUS_DEGRADATION_PROVEN"
        )
    except LiveAutonomousDegradationError:
        degradation_proven_blocked = True

    recovery_proven_blocked = False
    try:
        refuse_live_autonomous_recovery_proven_overclaim_v1(
            claimed_field="LIVE_AUTONOMOUS_RECOVERY_PROVEN"
        )
    except LiveAutonomousRecoveryError:
        recovery_proven_blocked = True

    observed_overclaim_blocked = False
    try:
        refuse_live_restart_or_recovery_observed_overclaim_v1(
            field_name="LIVE_AUTONOMOUS_RECOVERY_OBSERVED"
        )
    except LiveAutonomousRecoveryEvidenceLadderError:
        observed_overclaim_blocked = True

    end_to_end_claim_blocked = False
    try:
        refuse_live_end_to_end_and_beyond_claim_v1(field_name="LIVE_END_TO_END_EVIDENCE_PROVEN")
    except LiveAutonomousRecoveryEvidenceLadderError:
        end_to_end_claim_blocked = True

    ladder_activation_blocked = False
    try:
        refuse_live_autonomous_recovery_evidence_activation_v1(claimed_action="activate_ladder")
    except LiveAutonomousRecoveryEvidenceLadderError:
        ladder_activation_blocked = True

    cap_11_12_blocked = False
    try:
        refuse_cap_11_12_live_readiness_v1(claimed_surface="FULLY_AUTONOMOUS_LIVE_TRADING_READY")
    except LiveAutonomousDegradationError:
        cap_11_12_blocked = True

    gate = CredentialLoadGateV1()
    for name in gate.prerequisites_satisfied:
        gate.mark_prerequisite(name, satisfied=True)
    credential_load_blocked = False
    try:
        gate.attempt_credential_load_v1()
    except CredentialLoadGateError:
        credential_load_blocked = True

    forbidden_hits = _scan_package_for_forbidden_calls()
    ok = all(
        [
            predecessor.get("ok") is True,
            testnet_port_blocked,
            testnet_adapter_blocked,
            live_blocked,
            real_blocked,
            live_private_port_blocked,
            live_private_session_blocked,
            submit_blocked,
            session_blocked,
            dry_run_submit_blocked,
            canary_submit_blocked,
            bounded_activation_blocked,
            bounded_submit_blocked,
            degradation_activation_blocked,
            recovery_activation_blocked,
            recovery_submit_blocked,
            recovery_session_blocked,
            recovery_credential_blocked,
            degradation_proven_blocked,
            recovery_proven_blocked,
            observed_overclaim_blocked,
            end_to_end_claim_blocked,
            ladder_activation_blocked,
            cap_11_12_blocked,
            credential_load_blocked,
            not forbidden_hits,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            PRIVATE_NETWORK_SESSION_STARTED is False,
            REAL_CAPITAL_MOVEMENT_REACHABLE is False,
            PRIVATE_READONLY_NETWORK_REACHABLE is False,
            TESTNET_EXECUTION_ADAPTER_ACTIVATED is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11 is False,
            TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_11 is False,
            LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11 is False,
            PAPER_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11 is False,
            LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11 is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            ACTIVATION_STATE == "not_activated",
            CREDENTIAL_PLAINTEXT_LOADED is False,
            CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_11 is False,
            CAPABILITY_11_11_STARTED is True,
            CAPABILITY_11_11_LIVE_AUTONOMOUS_RECOVERY_STARTED is True,
            LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED is False,
            LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_ACTIVATED is False,
            LIVE_AUTONOMOUS_RECOVERY_ACTIVATED is False,
            LIVE_AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED is False,
            LIVE_RESTART_RECONSTRUCTED is False,
            LIVE_AUTONOMOUS_RECOVERY_OBSERVED is False,
            LIVE_BOUNDED_MULTI_SESSION_ACTIVATED is False,
            LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED is False,
            CAPABILITY_11_12_STARTED is False,
            CORE_LOGIC_CHANGE is False,
        ]
    )
    return {
        "ok": ok,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "TESTNET_EXECUTION_REACHABLE": False,
        "LIVE_EXECUTION_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
        "PRIVATE_NETWORK_SESSION_STARTED": False,
        "REAL_CAPITAL_MOVEMENT_REACHABLE": False,
        "PRIVATE_READONLY_NETWORK_REACHABLE": False,
        "TESTNET_EXECUTION_ADAPTER_ACTIVATED": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11": False,
        "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_11": False,
        "LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11": False,
        "PAPER_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11": False,
        "LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11": False,
        "TESTNET_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_11": False,
        "CAPABILITY_11_11_STARTED": True,
        "CAPABILITY_11_11_LIVE_AUTONOMOUS_RECOVERY_STARTED": True,
        "LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED": False,
        "LIVE_AUTONOMOUS_RECOVERY_ACTIVATED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "CAPABILITY_11_12_STARTED": False,
        "testnet_port_construction_blocked": testnet_port_blocked,
        "testnet_adapter_construction_blocked": testnet_adapter_blocked,
        "live_construction_blocked": live_blocked,
        "real_adapter_construction_blocked": real_blocked,
        "live_private_readonly_port_construction_blocked": live_private_port_blocked,
        "live_private_network_session_blocked": live_private_session_blocked,
        "testnet_order_submit_blocked": submit_blocked,
        "network_session_start_blocked": session_blocked,
        "dry_run_order_submit_blocked": dry_run_submit_blocked,
        "canary_order_submit_blocked": canary_submit_blocked,
        "bounded_activation_blocked": bounded_activation_blocked,
        "bounded_order_submit_blocked": bounded_submit_blocked,
        "degradation_activation_blocked": degradation_activation_blocked,
        "recovery_activation_blocked": recovery_activation_blocked,
        "recovery_order_submit_blocked": recovery_submit_blocked,
        "recovery_network_session_blocked": recovery_session_blocked,
        "recovery_credential_access_blocked": recovery_credential_blocked,
        "degradation_proven_blocked": degradation_proven_blocked,
        "recovery_proven_blocked": recovery_proven_blocked,
        "observed_overclaim_blocked": observed_overclaim_blocked,
        "end_to_end_claim_blocked": end_to_end_claim_blocked,
        "ladder_activation_blocked": ladder_activation_blocked,
        "cap_11_12_surface_blocked": cap_11_12_blocked,
        "credential_load_blocked": credential_load_blocked,
        "forbidden_call_hits": forbidden_hits,
        "predecessor_negative_reachability_ok": predecessor.get("ok") is True,
        "CORE_LOGIC_CHANGE": False,
    }


def prove_core_logic_parity_v1() -> dict[str, Any]:
    predecessor = prove_cap_11_10_core_logic_parity_v1()
    ok = predecessor.get("ok") is True and CORE_LOGIC_CHANGE is False
    return {
        "ok": ok,
        "CORE_LOGIC_CHANGE": False,
        "CORE_LOGIC_PARITY_WITH_SIMULATED_EXECUTION_PORT": predecessor.get(
            "CORE_LOGIC_PARITY_WITH_SIMULATED_EXECUTION_PORT"
        ),
        "predecessor": predecessor,
        "master_v2_mutated": False,
        "double_play_mutated": False,
        "c1_c2_c3_mutated": False,
        "dynamic_scope_mutated": False,
        "risk_mutated": False,
        "safety_mutated": False,
        "exit_policy_mutated": False,
        "thresholds_mutated": False,
        "VOLATILITY_NUMERIC_MAX_AGE_ENFORCING": False,
        "NUMERIC_MAX_AGE_EFFECT": "DIAGNOSTIC_ONLY",
        "DASHBOARD_AUTHORITY_EFFECT": "NONE",
    }


CALL_GRAPH_BEFORE: dict[str, Any] = {
    "path": [
        "Canonical Stateful Trading Core",
        "Canonical Intent / Lifecycle Contracts (Cap 11.1)",
        "Credential / Authorization / Account-Identity Boundary (Cap 11.2)",
        "Private Read-Only Venue Integration Contracts (Cap 11.3)",
        "Testnet Execution Adapter and Lifecycle Closure Contracts (Cap 11.4)",
        "Testnet Restart / Recovery / Kill-Switch Closure Contracts (Cap 11.5)",
        "Long-Running Autonomous Testnet Evidence Contracts (Cap 11.6)",
        "Live Private Read-Only and Shadow Reconciliation Contracts (Cap 11.7)",
        "Live Dry-Run Order-Plan Parity Contracts (Cap 11.8)",
        "Live Canary Order Execution Contracts (Cap 11.9)",
        "Live Bounded Single-Future Continuity Contracts (Cap 11.10)",
        "Mode-Specific Execution Boundary (Simulated sole reachable)",
        "Accounting / Portfolio / Reconciliation / Evidence",
    ],
    "live_autonomous_degradation": "absent_as_phase11_capability",
    "live_autonomous_recovery": "absent_as_phase11_capability",
    "live_autonomous_recovery_evidence_ladder": "absent_as_phase11_capability",
    "private_network_session": "forbidden",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "path": [
        "Canonical Stateful Trading Core (unchanged)",
        "Canonical Intent / Lifecycle Contracts (Cap 11.1 retained)",
        "Credential / Authorization / Account-Identity Boundary (Cap 11.2 retained)",
        "Private Read-Only Venue Integration Contracts (Cap 11.3 retained)",
        "Testnet Execution Adapter and Lifecycle Closure Contracts (Cap 11.4 retained)",
        "Testnet Restart / Recovery / Kill-Switch Closure Contracts (Cap 11.5 retained)",
        "Long-Running Autonomous Testnet Evidence Contracts (Cap 11.6 retained)",
        "Live Private Read-Only and Shadow Reconciliation Contracts (Cap 11.7 retained)",
        "Live Dry-Run Order-Plan Parity Contracts (Cap 11.8 retained)",
        "Live Canary Order Execution Contracts (Cap 11.9 retained)",
        "Live Bounded Single-Future Continuity Contracts (Cap 11.10 retained)",
        "Live Autonomous Recovery and Degradation Evidence Contracts (Cap 11.11)",
        "LiveOperatingStateTransitionRecordV1 (fixture-only; activation forbidden)",
        "LiveAutonomousRecoveryRecordV1 (fixture-only; submit forbidden)",
        "LiveAutonomousRecoveryEvidenceLadderFieldRecordV1 (fixture-only; observed overclaim forbidden)",
        "Mode-Specific Execution Boundary (Simulated sole reachable)",
        "Accounting / Portfolio / Reconciliation / Evidence",
    ],
    "live_autonomous_degradation": "bound_fixture_only_not_activated",
    "live_autonomous_recovery": "bound_fixture_only_not_activated",
    "live_autonomous_recovery_evidence_ladder": "bound_fixture_only_not_observed",
    "private_network_session": "forbidden",
    "activation": "not_activated",
    "capability_11_12": "forbidden",
}

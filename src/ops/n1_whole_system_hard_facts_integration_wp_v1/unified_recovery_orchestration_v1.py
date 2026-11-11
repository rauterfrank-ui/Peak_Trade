"""RW-E19: auditable unified recovery ordering via existing runtime owners."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.n1_whole_system_hard_facts_integration_wp_v1.composed_identity_custody_health_v1 import (
    prove_composed_safety_chain_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.execution_lifecycle_chain_v1 import (
    prove_execution_lifecycle_chain_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.private_observation_chain_v1 import (
    prove_private_restart_recovery_order_v1,
    private_restart_reconciliation_trusted_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    PublicRestRecoveryError,
    bootstrap_rest_snapshot_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1
from src.ops.peak_trade_public_market_data_runtime_v1.event_sequence_persistence_v1 import (
    load_event_sequence_state_v1,
)


RECOVERY_STEP_ORDER: tuple[str, ...] = (
    "durable_local_state",
    "public_rest_baseline_gap_recovery",
    "private_rest_baseline",
    "canonical_reconciliation",
    "instrument_epoch_validation",
    "order_lifecycle_reconstruction",
    "reservation_reconstruction",
    "treasury_account_truth_reconstruction",
    "durable_kill_switch_state",
    "membership_custody_validation",
    "runtime_eligibility",
)


@dataclass
class UnifiedRecoveryOrchestrationResultV1:
    ok: bool
    steps_completed: list[str] = field(default_factory=list)
    fail_closed_reason: str = ""
    trace: list[dict[str, Any]] = field(default_factory=list)
    evidence_scope: str = "PUBLIC_PRIVATE_OBSERVATION_RECOVERY_AND_CONTRACT_CHECKS"
    runtime_owner_recovery_complete: bool = False
    contract_checks: dict[str, bool] = field(default_factory=dict)
    pending_runtime_steps: list[str] = field(default_factory=lambda: list(RECOVERY_STEP_ORDER[4:]))


def execute_unified_recovery_orchestration_v1(
    *,
    public_store_root: Path,
    private_store_root: Path,
    public_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    private_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    venue_native_id: str = "ETH-USDT-SWAP",
    public_instrument_ref: InstrumentRefV1 | None = None,
    kill_switch_state_path: Optional[str] = None,
    unresolved_venue_order: bool | None = None,
) -> UnifiedRecoveryOrchestrationResultV1:
    result = UnifiedRecoveryOrchestrationResultV1(ok=False)
    if unresolved_venue_order is True:
        result.fail_closed_reason = "UNRESOLVED_VENUE_ORDER_STATE"
        return result

    load_event_sequence_state_v1(public_store_root)
    result.steps_completed.append(RECOVERY_STEP_ORDER[0])
    result.trace.append({"step": RECOVERY_STEP_ORDER[0], "ok": True})

    try:
        bootstrap_rest_snapshot_v1(
            public_rest_fetch, venue_native_id, instrument_ref=public_instrument_ref
        )
    except PublicRestRecoveryError as exc:
        result.fail_closed_reason = str(exc)
        return result
    result.steps_completed.append(RECOVERY_STEP_ORDER[1])

    private_restart = prove_private_restart_recovery_order_v1(
        store_root=private_store_root,
        rest_fetch_json=private_rest_fetch,
    )
    result.steps_completed.append(RECOVERY_STEP_ORDER[2])
    if not private_restart.get("reconciliation"):
        result.fail_closed_reason = "PRIVATE_RECONCILIATION_INCOMPLETE"
        return result
    if not private_restart_reconciliation_trusted_v1(private_restart):
        result.fail_closed_reason = "PRIVATE_RECONCILIATION_UNTRUSTED"
        return result
    result.steps_completed.append(RECOVERY_STEP_ORDER[3])

    safety = prove_composed_safety_chain_v1(kill_switch_state_path=kill_switch_state_path)
    if not safety.instrument_epoch_safe:
        result.fail_closed_reason = "INSTRUMENT_EPOCH_UNSAFE"
        return result
    result.contract_checks["instrument_epoch_rule_sample"] = safety.instrument_epoch_safe

    exec_proof = prove_execution_lifecycle_chain_v1()
    if not exec_proof.order_lifecycle_contract:
        result.fail_closed_reason = "ORDER_LIFECYCLE_RECONSTRUCTION_FAIL"
        return result
    result.contract_checks["simulated_order_lifecycle"] = exec_proof.order_lifecycle_contract
    result.contract_checks["reservation_state_definitions"] = exec_proof.reservation_restart_safe
    result.contract_checks["treasury_guard_sample"] = exec_proof.treasury_feedback_closed

    if not safety.durable_kill_switch_bound:
        result.fail_closed_reason = "KILL_SWITCH_STATE_UNRESOLVED"
        return result
    result.contract_checks["kill_switch_blocking_rule"] = safety.durable_kill_switch_bound

    if not safety.position_custody_safe:
        result.fail_closed_reason = "MEMBERSHIP_CUSTODY_UNSAFE"
        return result
    result.contract_checks["position_custody_rule_sample"] = safety.position_custody_safe
    # These sample contracts do not reconstruct this account's orders, holds,
    # treasury, instrument generation or actual runtime eligibility.
    result.ok = len(result.steps_completed) == 4 and all(result.contract_checks.values())
    return result

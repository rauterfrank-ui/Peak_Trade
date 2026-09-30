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
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    bootstrap_rest_snapshot_v1,
)
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


def execute_unified_recovery_orchestration_v1(
    *,
    public_store_root: Path,
    private_store_root: Path,
    public_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    private_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    venue_native_id: str = "ETH-USDT-SWAP",
    kill_switch_state_path: Optional[str] = None,
    unresolved_venue_order: bool = False,
) -> UnifiedRecoveryOrchestrationResultV1:
    result = UnifiedRecoveryOrchestrationResultV1(ok=False)
    if unresolved_venue_order:
        result.fail_closed_reason = "UNRESOLVED_VENUE_ORDER_STATE"
        return result

    load_event_sequence_state_v1(public_store_root)
    result.steps_completed.append(RECOVERY_STEP_ORDER[0])
    result.trace.append({"step": RECOVERY_STEP_ORDER[0], "ok": True})

    bootstrap_rest_snapshot_v1(public_rest_fetch, venue_native_id)
    result.steps_completed.append(RECOVERY_STEP_ORDER[1])

    private_restart = prove_private_restart_recovery_order_v1(
        store_root=private_store_root,
        rest_fetch_json=private_rest_fetch,
    )
    result.steps_completed.append(RECOVERY_STEP_ORDER[2])
    if not private_restart.get("reconciliation"):
        result.fail_closed_reason = "PRIVATE_RECONCILIATION_INCOMPLETE"
        return result
    result.steps_completed.append(RECOVERY_STEP_ORDER[3])

    safety = prove_composed_safety_chain_v1(kill_switch_state_path=kill_switch_state_path)
    if not safety.instrument_epoch_safe:
        result.fail_closed_reason = "INSTRUMENT_EPOCH_UNSAFE"
        return result
    result.steps_completed.append(RECOVERY_STEP_ORDER[4])

    exec_proof = prove_execution_lifecycle_chain_v1()
    if not exec_proof.order_lifecycle_contract:
        result.fail_closed_reason = "ORDER_LIFECYCLE_RECONSTRUCTION_FAIL"
        return result
    result.steps_completed.extend(RECOVERY_STEP_ORDER[5:8])

    if not safety.durable_kill_switch_bound:
        result.fail_closed_reason = "KILL_SWITCH_STATE_UNRESOLVED"
        return result
    result.steps_completed.append(RECOVERY_STEP_ORDER[8])

    if not safety.position_custody_safe:
        result.fail_closed_reason = "MEMBERSHIP_CUSTODY_UNSAFE"
        return result
    result.steps_completed.append(RECOVERY_STEP_ORDER[9])
    result.steps_completed.append(RECOVERY_STEP_ORDER[10])
    result.ok = len(result.steps_completed) == len(RECOVERY_STEP_ORDER)
    return result

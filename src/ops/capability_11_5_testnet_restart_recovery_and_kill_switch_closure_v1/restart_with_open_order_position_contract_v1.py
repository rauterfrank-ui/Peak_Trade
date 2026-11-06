"""Restart with open order / open position contracts (§11.12.6) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    CONTRACT_VERSION,
    OWNER,
    RESTART_RECOVERY_PATHS,
    RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED,
    RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND,
    RESTART_WITH_OPEN_ORDER_POSITION_OWNER,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5,
    TESTNET_RESTART_PROVEN,
)


class RestartWithOpenOrderPositionError(RuntimeError):
    """Fail-closed restart-with-open-order/position violation."""

    __test__ = False


@dataclass(frozen=True)
class RestartRecoveryPathRecordV1:
    __test__ = False

    path_name: str
    pre_restart_state: str
    post_restart_state: str
    history: tuple[str, ...]
    terminal_state: str
    reconciliation_before_alpha: bool
    source: str = "FIXTURE_ONLY"
    exchange_submit_performed: bool = False
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = RESTART_WITH_OPEN_ORDER_POSITION_OWNER


def _advance_to_open(machine: OrderLifecycleStateMachineV1) -> None:
    for state in (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
    ):
        machine.transition(state)


def run_restart_recovery_fixture_path_v1(*, path_name: str) -> RestartRecoveryPathRecordV1:
    if path_name not in RESTART_RECOVERY_PATHS:
        raise RestartWithOpenOrderPositionError(f"UNKNOWN_RESTART_RECOVERY_PATH:{path_name}")

    machine = OrderLifecycleStateMachineV1(
        client_order_id=f"pt-coid-restart-{path_name}",
        intent_id=f"intent-restart-{path_name}",
        order_plan_id=f"plan-restart-{path_name}",
    )
    _advance_to_open(machine)
    pre_restart_state = machine.current_state

    # Fixture restart handoff: reconstruct from durable OPEN state without re-submit.
    reconstructed = OrderLifecycleStateMachineV1(
        current_state=pre_restart_state,
        client_order_id=machine.client_order_id,
        intent_id=machine.intent_id,
        order_plan_id=machine.order_plan_id,
        history=list(machine.history),
    )
    if reconstructed.current_state != "OPEN":
        raise RestartWithOpenOrderPositionError(
            f"RESTART_RECONSTRUCTION_FAILED:{path_name}:{reconstructed.current_state}"
        )

    # After restart: reconcile path continues without new submission.
    if path_name == "restart_with_open_order":
        for state in ("CANCEL_PENDING", "CANCELLED", "ACCOUNTED", "RECONCILED", "EVIDENCED"):
            reconstructed.transition(state)
    else:
        # restart_with_open_position: continue fill → account → reconcile → evidence
        for state in ("FILLED", "ACCOUNTED", "RECONCILED", "EVIDENCED"):
            reconstructed.transition(state)

    if reconstructed.current_state != "EVIDENCED":
        raise RestartWithOpenOrderPositionError(
            f"RESTART_RECOVERY_PATH_NOT_CLOSED:{path_name}:{reconstructed.current_state}"
        )

    return RestartRecoveryPathRecordV1(
        path_name=path_name,
        pre_restart_state=pre_restart_state,
        post_restart_state="OPEN",
        history=tuple(reconstructed.history),
        terminal_state=reconstructed.current_state,
        reconciliation_before_alpha=True,
    )


def refuse_restart_network_session_activation_v1(*, session_id: str) -> dict[str, Any]:
    raise RestartWithOpenOrderPositionError(
        f"RESTART_NETWORK_SESSION_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_5:{session_id}"
    )


def refuse_silent_reinitialization_v1(*, claimed_action: str) -> dict[str, Any]:
    raise RestartWithOpenOrderPositionError(
        f"SILENT_REINITIALIZATION_FORBIDDEN_IN_CAPABILITY_11_5:{claimed_action}"
    )


def prove_restart_with_open_order_position_contract_v1() -> dict[str, Any]:
    path_records: dict[str, RestartRecoveryPathRecordV1] = {}
    for path_name in RESTART_RECOVERY_PATHS:
        path_records[path_name] = run_restart_recovery_fixture_path_v1(path_name=path_name)

    unknown_path_blocked = False
    try:
        run_restart_recovery_fixture_path_v1(path_name="long_running_autonomous_campaign")
    except RestartWithOpenOrderPositionError as exc:
        unknown_path_blocked = "UNKNOWN_RESTART_RECOVERY_PATH" in str(exc)

    network_blocked = False
    try:
        refuse_restart_network_session_activation_v1(session_id="session-restart")
    except RestartWithOpenOrderPositionError as exc:
        network_blocked = "RESTART_NETWORK_SESSION_ACTIVATION_FORBIDDEN" in str(exc)

    silent_reset_blocked = False
    try:
        refuse_silent_reinitialization_v1(claimed_action="reset_to_zero")
    except RestartWithOpenOrderPositionError as exc:
        silent_reset_blocked = "SILENT_REINITIALIZATION_FORBIDDEN" in str(exc)

    illegal_from_open_blocked = False
    try:
        machine = OrderLifecycleStateMachineV1(current_state="OPEN", history=["OPEN"])
        machine.transition("INTENT_CREATED")
    except OrderLifecycleTransitionError as exc:
        illegal_from_open_blocked = exc.code == "ILLEGAL_LIFECYCLE_TRANSITION"

    all_closed = all(r.terminal_state == "EVIDENCED" for r in path_records.values())
    all_fixture = all(r.source == "FIXTURE_ONLY" for r in path_records.values())
    no_submit = all(r.exchange_submit_performed is False for r in path_records.values())
    all_recon = all(r.reconciliation_before_alpha is True for r in path_records.values())
    all_pre_open = all(r.pre_restart_state == "OPEN" for r in path_records.values())

    ok = all(
        [
            all_closed,
            all_fixture,
            no_submit,
            all_recon,
            all_pre_open,
            unknown_path_blocked,
            network_blocked,
            silent_reset_blocked,
            illegal_from_open_blocked,
            RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND is True,
            RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED is False,
            TESTNET_RESTART_PROVEN is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5 is False,
            all(name in path_records for name in RESTART_RECOVERY_PATHS),
        ]
    )
    return {
        "ok": ok,
        "RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND": True,
        "RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED": False,
        "TESTNET_RESTART_PROVEN": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5": False,
        "paths_closed": {name: rec.terminal_state for name, rec in path_records.items()},
        "pre_restart_states": {name: rec.pre_restart_state for name, rec in path_records.items()},
        "unknown_path_blocked": unknown_path_blocked,
        "network_session_activation_blocked": network_blocked,
        "silent_reinitialization_blocked": silent_reset_blocked,
        "illegal_from_open_blocked": illegal_from_open_blocked,
        "OWNER": OWNER,
    }

"""Unknown-submit and reconnect recovery contracts (§11.12.5) — fixture-only."""

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
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
    UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED,
    UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND,
    UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER,
    UNKNOWN_SUBMIT_RECOVERY_PATHS,
)


class UnknownSubmitReconnectRecoveryError(RuntimeError):
    """Fail-closed unknown-submit / reconnect recovery violation."""

    __test__ = False


@dataclass(frozen=True)
class UnknownSubmitRecoveryPathRecordV1:
    __test__ = False

    path_name: str
    history: tuple[str, ...]
    terminal_state: str
    exchange_query_completed: bool
    blind_retry_blocked: bool
    source: str = "FIXTURE_ONLY"
    exchange_submit_performed: bool = False
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER


def _advance_to_unknown(machine: OrderLifecycleStateMachineV1) -> None:
    for state in (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "UNKNOWN",
    ):
        machine.transition(state)


def run_unknown_submit_recovery_fixture_path_v1(
    *, path_name: str
) -> UnknownSubmitRecoveryPathRecordV1:
    if path_name not in UNKNOWN_SUBMIT_RECOVERY_PATHS:
        raise UnknownSubmitReconnectRecoveryError(
            f"UNKNOWN_SUBMIT_RECOVERY_PATH_FORBIDDEN:{path_name}"
        )

    machine = OrderLifecycleStateMachineV1(
        client_order_id=f"pt-coid-unknown-{path_name}",
        intent_id=f"intent-unknown-{path_name}",
        order_plan_id=f"plan-unknown-{path_name}",
    )
    _advance_to_unknown(machine)

    blind_retry_blocked = False
    try:
        machine.transition("ACKNOWLEDGED", exchange_query_completed=False)
    except OrderLifecycleTransitionError as exc:
        blind_retry_blocked = exc.code == "UNKNOWN_REQUIRES_EXCHANGE_QUERY_BEFORE_RETRY"

    if not blind_retry_blocked:
        raise UnknownSubmitReconnectRecoveryError("BLIND_RETRY_NOT_BLOCKED")

    # Fixture recovery: authoritative query completed, then resume lifecycle to EVIDENCED.
    machine.transition("ACKNOWLEDGED", exchange_query_completed=True)
    for state in (
        "OPEN",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ):
        machine.transition(state)

    if machine.current_state != "EVIDENCED":
        raise UnknownSubmitReconnectRecoveryError(
            f"UNKNOWN_SUBMIT_RECOVERY_PATH_NOT_CLOSED:{path_name}:{machine.current_state}"
        )

    return UnknownSubmitRecoveryPathRecordV1(
        path_name=path_name,
        history=tuple(machine.history),
        terminal_state=machine.current_state,
        exchange_query_completed=True,
        blind_retry_blocked=True,
    )


def refuse_unknown_submit_blind_retry_v1(*, client_order_id: str) -> dict[str, Any]:
    raise UnknownSubmitReconnectRecoveryError(
        f"UNKNOWN_SUBMIT_BLIND_RETRY_FORBIDDEN_IN_CAPABILITY_11_5:{client_order_id}"
    )


def refuse_unknown_submit_network_reconnect_activation_v1(*, session_id: str) -> dict[str, Any]:
    raise UnknownSubmitReconnectRecoveryError(
        f"UNKNOWN_SUBMIT_NETWORK_RECONNECT_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_5:{session_id}"
    )


def prove_unknown_submit_reconnect_recovery_contract_v1() -> dict[str, Any]:
    path_records: dict[str, UnknownSubmitRecoveryPathRecordV1] = {}
    for path_name in UNKNOWN_SUBMIT_RECOVERY_PATHS:
        path_records[path_name] = run_unknown_submit_recovery_fixture_path_v1(path_name=path_name)

    unknown_path_blocked = False
    try:
        run_unknown_submit_recovery_fixture_path_v1(path_name="long_running_autonomous_campaign")
    except UnknownSubmitReconnectRecoveryError as exc:
        unknown_path_blocked = "UNKNOWN_SUBMIT_RECOVERY_PATH_FORBIDDEN" in str(exc)

    blind_refuse_blocked = False
    try:
        refuse_unknown_submit_blind_retry_v1(client_order_id="pt-coid-blind")
    except UnknownSubmitReconnectRecoveryError as exc:
        blind_refuse_blocked = "UNKNOWN_SUBMIT_BLIND_RETRY_FORBIDDEN" in str(exc)

    reconnect_activation_blocked = False
    try:
        refuse_unknown_submit_network_reconnect_activation_v1(session_id="session-reconnect")
    except UnknownSubmitReconnectRecoveryError as exc:
        reconnect_activation_blocked = (
            "UNKNOWN_SUBMIT_NETWORK_RECONNECT_ACTIVATION_FORBIDDEN" in str(exc)
        )

    all_closed = all(r.terminal_state == "EVIDENCED" for r in path_records.values())
    all_fixture = all(r.source == "FIXTURE_ONLY" for r in path_records.values())
    no_submit = all(r.exchange_submit_performed is False for r in path_records.values())
    all_query = all(r.exchange_query_completed is True for r in path_records.values())
    all_blind_blocked = all(r.blind_retry_blocked is True for r in path_records.values())

    ok = all(
        [
            all_closed,
            all_fixture,
            no_submit,
            all_query,
            all_blind_blocked,
            unknown_path_blocked,
            blind_refuse_blocked,
            reconnect_activation_blocked,
            UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND is True,
            UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED is False,
            TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5 is False,
            all(name in path_records for name in UNKNOWN_SUBMIT_RECOVERY_PATHS),
        ]
    )
    return {
        "ok": ok,
        "UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND": True,
        "UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED": False,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5": False,
        "paths_closed": {name: rec.terminal_state for name, rec in path_records.items()},
        "path_histories": {name: list(rec.history) for name, rec in path_records.items()},
        "unknown_path_blocked": unknown_path_blocked,
        "blind_retry_refuse_blocked": blind_refuse_blocked,
        "reconnect_activation_blocked": reconnect_activation_blocked,
        "OWNER": OWNER,
    }

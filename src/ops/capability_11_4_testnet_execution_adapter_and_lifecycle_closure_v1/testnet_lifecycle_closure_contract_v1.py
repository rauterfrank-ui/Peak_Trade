"""Testnet lifecycle closure contracts (§11.12.3 / §11.12.4) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.constants_v1 import (
    CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED,
    CONTRACT_VERSION,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    OWNER,
    TESTNET_ENTRY_PARTIAL_FILL_CANCEL_EXIT_PATHS_BOUND,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_LIFECYCLE_CLOSURE_CONTRACT_BOUND,
    TESTNET_LIFECYCLE_CLOSURE_OWNER,
    TESTNET_LIFECYCLE_FIXTURE_ONLY,
    TESTNET_LIFECYCLE_PATHS,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
    UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED,
)


class TestnetLifecycleClosureError(RuntimeError):
    """Fail-closed Testnet lifecycle closure violation."""

    __test__ = False


@dataclass(frozen=True)
class TestnetLifecyclePathRecordV1:
    __test__ = False

    path_name: str
    history: tuple[str, ...]
    terminal_state: str
    source: str = "FIXTURE_ONLY"
    exchange_submit_performed: bool = False
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = TESTNET_LIFECYCLE_CLOSURE_OWNER


_PATH_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "single_controlled_order_lifecycle": (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ),
    "entry_lifecycle": (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ),
    "partial_fill_lifecycle": (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "PARTIALLY_FILLED",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ),
    "cancel_lifecycle": (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "CANCEL_PENDING",
        "CANCELLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ),
    "exit_lifecycle": (
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ),
}


def run_testnet_lifecycle_fixture_path_v1(*, path_name: str) -> TestnetLifecyclePathRecordV1:
    if path_name not in TESTNET_LIFECYCLE_PATHS:
        raise TestnetLifecycleClosureError(f"UNKNOWN_TESTNET_LIFECYCLE_PATH:{path_name}")
    transitions = _PATH_TRANSITIONS[path_name]
    machine = OrderLifecycleStateMachineV1(
        client_order_id=f"pt-coid-fixture-{path_name}",
        intent_id=f"intent-{path_name}",
        order_plan_id=f"plan-{path_name}",
    )
    for target in transitions:
        machine.transition(target)
    if machine.current_state != "EVIDENCED":
        raise TestnetLifecycleClosureError(
            f"TESTNET_LIFECYCLE_PATH_NOT_CLOSED:{path_name}:{machine.current_state}"
        )
    return TestnetLifecyclePathRecordV1(
        path_name=path_name,
        history=tuple(machine.history),
        terminal_state=machine.current_state,
    )


def refuse_cap_11_5_restart_recovery_kill_switch_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise TestnetLifecycleClosureError(
        f"CAPABILITY_11_5_SURFACE_FORBIDDEN_IN_CAPABILITY_11_4:{claimed_surface}"
    )


def prove_testnet_lifecycle_closure_contract_v1() -> dict[str, Any]:
    path_records: dict[str, TestnetLifecyclePathRecordV1] = {}
    for path_name in TESTNET_LIFECYCLE_PATHS:
        path_records[path_name] = run_testnet_lifecycle_fixture_path_v1(path_name=path_name)

    unknown_path_blocked = False
    try:
        run_testnet_lifecycle_fixture_path_v1(path_name="restart_with_open_order")
    except TestnetLifecycleClosureError as exc:
        unknown_path_blocked = "UNKNOWN_TESTNET_LIFECYCLE_PATH" in str(exc)

    cap_11_5_blocked = False
    try:
        refuse_cap_11_5_restart_recovery_kill_switch_v1(claimed_surface="kill_switch")
    except TestnetLifecycleClosureError as exc:
        cap_11_5_blocked = "CAPABILITY_11_5_SURFACE_FORBIDDEN" in str(exc)

    illegal_transition_blocked = False
    try:
        machine = OrderLifecycleStateMachineV1()
        machine.transition("FILLED")
    except OrderLifecycleTransitionError as exc:
        illegal_transition_blocked = exc.code == "ILLEGAL_LIFECYCLE_TRANSITION"

    all_closed = all(r.terminal_state == "EVIDENCED" for r in path_records.values())
    all_fixture = all(r.source == "FIXTURE_ONLY" for r in path_records.values())
    no_submit = all(r.exchange_submit_performed is False for r in path_records.values())

    ok = all(
        [
            all_closed,
            all_fixture,
            no_submit,
            unknown_path_blocked,
            cap_11_5_blocked,
            illegal_transition_blocked,
            TESTNET_LIFECYCLE_CLOSURE_CONTRACT_BOUND is True,
            TESTNET_LIFECYCLE_FIXTURE_ONLY is True,
            TESTNET_ENTRY_PARTIAL_FILL_CANCEL_EXIT_PATHS_BOUND is True,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4 is False,
            TESTNET_ORDER_LIFECYCLE_PROVEN is False,
            TESTNET_RESTART_PROVEN is False,
            TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            TESTNET_KILL_SWITCH_PROVEN is False,
            CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED is False,
            UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED is False,
            KILL_SWITCH_CONTRACT_ACTIVATED is False,
            all(name in path_records for name in TESTNET_LIFECYCLE_PATHS),
        ]
    )
    return {
        "ok": ok,
        "TESTNET_LIFECYCLE_CLOSURE_CONTRACT_BOUND": True,
        "TESTNET_LIFECYCLE_FIXTURE_ONLY": True,
        "TESTNET_ENTRY_PARTIAL_FILL_CANCEL_EXIT_PATHS_BOUND": True,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4": False,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": False,
        "TESTNET_RESTART_PROVEN": False,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "TESTNET_KILL_SWITCH_PROVEN": False,
        "CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED": False,
        "paths_closed": {name: rec.terminal_state for name, rec in path_records.items()},
        "path_histories": {name: list(rec.history) for name, rec in path_records.items()},
        "unknown_path_blocked": unknown_path_blocked,
        "cap_11_5_surface_blocked": cap_11_5_blocked,
        "illegal_transition_blocked": illegal_transition_blocked,
        "OWNER": OWNER,
    }

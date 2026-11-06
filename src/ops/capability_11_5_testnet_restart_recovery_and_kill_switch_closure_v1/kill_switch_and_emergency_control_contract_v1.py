"""Kill-switch and emergency control contracts (§11.12.7 / §11.9) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
    CONTRACT_VERSION,
    EMERGENCY_COMMANDS,
    EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
    KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND,
    KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER,
    KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME,
    KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    KILL_SWITCH_FAIL_CLOSED,
    KILL_SWITCH_PERSISTED,
    KILL_SWITCH_SURVIVES_RESTART,
    OWNER,
    OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5,
)


class KillSwitchEmergencyControlError(RuntimeError):
    """Fail-closed kill-switch / emergency control violation."""

    __test__ = False


@dataclass(frozen=True)
class KillSwitchFixtureRecordV1:
    __test__ = False

    command: str
    persisted: bool
    survives_restart: bool
    cleared_by_runtime: bool
    alpha_dependent: bool
    source: str = "FIXTURE_ONLY"
    exchange_submit_performed: bool = False
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER


def build_kill_switch_fixture_record_v1(*, command: str) -> KillSwitchFixtureRecordV1:
    if command not in EMERGENCY_COMMANDS:
        raise KillSwitchEmergencyControlError(f"UNKNOWN_EMERGENCY_COMMAND:{command}")
    return KillSwitchFixtureRecordV1(
        command=command,
        persisted=True,
        survives_restart=True,
        cleared_by_runtime=False,
        alpha_dependent=False,
    )


def refuse_runtime_kill_switch_clear_v1(*, actor: str) -> dict[str, Any]:
    raise KillSwitchEmergencyControlError(
        f"KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN_IN_CAPABILITY_11_5:{actor}"
    )


def refuse_kill_switch_side_effect_bypass_v1(*, claimed_side_effect: str) -> dict[str, Any]:
    raise KillSwitchEmergencyControlError(
        f"KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN_IN_CAPABILITY_11_5:{claimed_side_effect}"
    )


def refuse_emergency_command_risk_increase_v1(*, command: str) -> dict[str, Any]:
    raise KillSwitchEmergencyControlError(
        f"EMERGENCY_COMMAND_RISK_INCREASE_FORBIDDEN_IN_CAPABILITY_11_5:{command}"
    )


def prove_kill_switch_and_emergency_control_contract_v1() -> dict[str, Any]:
    records: dict[str, KillSwitchFixtureRecordV1] = {}
    for command in EMERGENCY_COMMANDS:
        records[command] = build_kill_switch_fixture_record_v1(command=command)

    unknown_command_blocked = False
    try:
        build_kill_switch_fixture_record_v1(command="ENABLE_LIVE_TRADING")
    except KillSwitchEmergencyControlError as exc:
        unknown_command_blocked = "UNKNOWN_EMERGENCY_COMMAND" in str(exc)

    clear_blocked = False
    try:
        refuse_runtime_kill_switch_clear_v1(actor="runtime_autonomy")
    except KillSwitchEmergencyControlError as exc:
        clear_blocked = "KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN" in str(exc)

    bypass_blocked = False
    try:
        refuse_kill_switch_side_effect_bypass_v1(claimed_side_effect="order_submit")
    except KillSwitchEmergencyControlError as exc:
        bypass_blocked = "KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN" in str(exc)

    risk_increase_blocked = False
    try:
        refuse_emergency_command_risk_increase_v1(command="PERSISTENT_KILL")
    except KillSwitchEmergencyControlError as exc:
        risk_increase_blocked = "EMERGENCY_COMMAND_RISK_INCREASE_FORBIDDEN" in str(exc)

    all_persisted = all(r.persisted is True for r in records.values())
    all_survive = all(r.survives_restart is True for r in records.values())
    none_cleared = all(r.cleared_by_runtime is False for r in records.values())
    none_alpha = all(r.alpha_dependent is False for r in records.values())
    all_fixture = all(r.source == "FIXTURE_ONLY" for r in records.values())
    no_submit = all(r.exchange_submit_performed is False for r in records.values())

    ok = all(
        [
            all_persisted,
            all_survive,
            none_cleared,
            none_alpha,
            all_fixture,
            no_submit,
            unknown_command_blocked,
            clear_blocked,
            bypass_blocked,
            risk_increase_blocked,
            KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND is True,
            KILL_SWITCH_CONTRACT_ACTIVATED is False,
            TESTNET_KILL_SWITCH_PROVEN is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5 is False,
            KILL_SWITCH_PERSISTED is True,
            KILL_SWITCH_FAIL_CLOSED is True,
            KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT is True,
            KILL_SWITCH_SURVIVES_RESTART is True,
            KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME is True,
            OWNER_AUTHORITY_REQUIRED_TO_CLEAR is True,
            CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA is True,
            EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA is True,
            all(name in records for name in EMERGENCY_COMMANDS),
        ]
    )
    return {
        "ok": ok,
        "KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND": True,
        "KILL_SWITCH_CONTRACT_ACTIVATED": False,
        "TESTNET_KILL_SWITCH_PROVEN": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5": False,
        "KILL_SWITCH_PERSISTED": True,
        "KILL_SWITCH_FAIL_CLOSED": True,
        "KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT": True,
        "KILL_SWITCH_SURVIVES_RESTART": True,
        "KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME": True,
        "OWNER_AUTHORITY_REQUIRED_TO_CLEAR": True,
        "CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA": True,
        "EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA": True,
        "commands_bound": sorted(records.keys()),
        "unknown_command_blocked": unknown_command_blocked,
        "runtime_clear_blocked": clear_blocked,
        "side_effect_bypass_blocked": bypass_blocked,
        "risk_increase_blocked": risk_increase_blocked,
        "OWNER": OWNER,
    }

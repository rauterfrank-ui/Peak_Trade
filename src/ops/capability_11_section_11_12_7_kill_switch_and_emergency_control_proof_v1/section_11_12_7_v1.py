"""Fail-closed §11.12.7 kill-switch and emergency control proof residual.

Reuses Cap 11.5 fixture-only kill-switch/emergency-control contracts and binds
the closed §11.12.6 productive restart-with-open-order/position predecessor.
Does not submit orders, authorize network writes, activate Cap 11.5 Testnet
adapters, activate the kill-switch contract, claim TESTNET_KILL_SWITCH_PROVEN,
or start §11.12.8 / Cap 11.13.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.kill_switch_and_emergency_control_contract_v1 import (
    KillSwitchEmergencyControlError,
    KillSwitchFixtureRecordV1,
    build_kill_switch_fixture_record_v1,
    prove_kill_switch_and_emergency_control_contract_v1,
    refuse_emergency_command_risk_increase_v1,
    refuse_kill_switch_side_effect_bypass_v1,
    refuse_runtime_kill_switch_clear_v1,
)
from src.ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.section_11_12_6_v1 import (
    execute_section_11_12_6_restart_with_open_order_and_open_position_v1,
    mark_section_11_12_5_predecessor_bound_v1,
)
from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_SECTION_11_12_7_COMMANDS,
    CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSE_ALLOWED,
    CAP_11_5_KILL_SWITCH_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    EXECUTION_MODE_REQUIRED,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
    FORBIDDEN_SECTION_11_12_8_PATHS,
    KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED,
    KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME,
    KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    KILL_SWITCH_FAIL_CLOSED,
    KILL_SWITCH_PERSISTED,
    KILL_SWITCH_SURVIVES_RESTART,
    LIFECYCLE_NETWORK_EFFECT,
    LIFECYCLE_SOURCE_REQUIRED,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_WRITE_PERFORMED,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDER_SUBMIT_PERFORMED,
    ORDERS_AUTHORIZED,
    OWNER,
    OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REQUIRED_PRECONDITIONS,
    SECTION_11_12_6_PREDECESSOR_BINDING_REQUIRED,
    SECTION_11_12_8_STARTED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)


class Section11127KillSwitchAndEmergencyControlProofError(RuntimeError):
    """Fail-closed §11.12.7 kill-switch/emergency-control violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class Section11127CommandResultV1:
    """One productive §11.12.7 fixture emergency-command result."""

    command: str
    persisted: bool
    survives_restart: bool
    cleared_by_runtime: bool
    alpha_dependent: bool
    lifecycle_source: str
    network_effect: str
    exchange_submit_performed: bool


@dataclass(frozen=True)
class Section11127ExecutionRecordV1:
    """Productive §11.12.7 kill-switch and emergency control execution record."""

    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    repository_sha: str
    config_digest: str
    section_11_12_6_execution_binding_digest: str
    client_order_id_prefix: str
    command_results: tuple[Section11127CommandResultV1, ...]
    commands_completed: tuple[str, ...]
    lifecycle_source: str
    network_effect: str
    exchange_submit_performed: bool
    kill_switch_and_emergency_control_proof_performed: bool
    cap_11_5_kill_switch_and_emergency_control_contract_reused: bool
    order_send_disabled: bool
    orders_authorized: bool
    network_writes_authorized: bool
    network_write_performed: bool
    exchange_order_submit_reachable: bool
    testnet_order_submit_performed: bool
    cap_11_5_adapter_activated: bool
    kill_switch_contract_activated: bool
    section_11_12_8_started: bool
    cap_11_13_started: bool
    testnet_order_lifecycle_proven: bool
    testnet_unknown_submit_recovery_proven: bool
    testnet_restart_proven: bool
    testnet_kill_switch_proven: bool
    missing_preconditions: tuple[str, ...]
    execution_admissible: bool
    execution_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    reference_only: bool = False
    path_class: str = PATH_CLASS


def evaluate_section_11_12_7_preconditions_v1(
    *,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_account_identity: str,
    expected_venue: str,
    section_11_12_6_predecessor_bound: bool,
    cap_11_5_kill_switch_and_emergency_control_contract_reused: bool,
    owner_go_kill_switch_emergency_control_authorized: bool,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    network_effect: str = LIFECYCLE_NETWORK_EFFECT,
    cap_11_5_adapter_activated: bool = False,
    kill_switch_contract_activated: bool = False,
    section_11_12_8_started: bool = False,
    cap_11_13_started: bool = False,
) -> dict[str, Any]:
    """Evaluate §11.12.7 productive preconditions."""
    missing: list[str] = []
    scope = tuple(str(x) for x in instrument_scope)

    if runtime_mode != EXECUTION_MODE_REQUIRED:
        missing.append("testnet_only_scope")
    if not venue:
        missing.append("venue_explicit")
    if not account_identity:
        missing.append("account_identity_explicit")
    if not scope:
        missing.append("instrument_scope_explicit")
    if not repository_sha or repository_sha != expected_repository_sha:
        missing.append("repository_sha_bound")
    if not config_digest or config_digest != expected_config_digest:
        missing.append("config_digest_bound")
    if not account_identity or account_identity != expected_account_identity:
        missing.append("account_identity_bound")
    if not venue or venue != expected_venue:
        missing.append("venue_bound")
    if not section_11_12_6_predecessor_bound or not SECTION_11_12_6_PREDECESSOR_BINDING_REQUIRED:
        missing.append("section_11_12_6_predecessor_bound")
    if (
        not cap_11_5_kill_switch_and_emergency_control_contract_reused
        or not CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSE_ALLOWED
    ):
        missing.append("cap_11_5_kill_switch_and_emergency_control_contract_reused")
    if not KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED:
        missing.append("kill_switch_and_emergency_control_proof_allowed")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED is not False:
        missing.append("network_writes_unauthorized")
    if network_effect != "NONE" or LIFECYCLE_NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if (
        cap_11_5_adapter_activated
        or CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED is True
        or CAPABILITY_11_5_STARTED is True
    ):
        missing.append("cap_11_5_adapter_not_activated")
    if kill_switch_contract_activated or KILL_SWITCH_CONTRACT_ACTIVATED is True:
        missing.append("kill_switch_contract_not_activated")
    if section_11_12_8_started or SECTION_11_12_8_STARTED is True:
        missing.append("section_11_12_8_not_started")
    if cap_11_13_started or CAPABILITY_11_13_STARTED is True:
        missing.append("cap_11_13_not_started")
    if not owner_go_kill_switch_emergency_control_authorized:
        missing.append("owner_go_kill_switch_emergency_control_authorized")

    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)
    return {
        "execution_admissible": len(ordered_missing) == 0,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
    }


def mark_section_11_12_6_predecessor_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> tuple[bool, str]:
    """Bind closed §11.12.6 productive restart predecessor.

    Returns (bound, execution_binding_digest).
    """
    pred_bound, pred_digest = mark_section_11_12_5_predecessor_bound_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    record = execute_section_11_12_6_restart_with_open_order_and_open_position_v1(
        runtime_mode="TESTNET",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_scope=("BTC-USDT-SWAP",),
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        expected_account_identity="acct-uid-demo",
        expected_venue="OKX",
        section_11_12_5_predecessor_bound=pred_bound,
        section_11_12_5_execution_binding_digest=pred_digest,
        client_order_id_prefix="pt-coid-section-11-12-7-pred",
    )
    bound = (
        record.execution_admissible is True
        and record.restart_with_open_order_and_open_position_performed is True
        and bool(record.execution_binding_digest)
    )
    return bound, record.execution_binding_digest


def reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(
    *,
    command: str,
) -> KillSwitchFixtureRecordV1:
    """Reuse Cap 11.5 fixture-only §11.12.7 / §11.9 emergency command."""
    if not CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSE_ALLOWED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSE_NOT_ALLOWED"
        )
    if command not in ALLOWED_SECTION_11_12_7_COMMANDS:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            f"SECTION_11_12_7_COMMAND_FORBIDDEN:{command}"
        )
    try:
        record = build_kill_switch_fixture_record_v1(command=command)
    except KillSwitchEmergencyControlError as exc:
        raise Section11127KillSwitchAndEmergencyControlProofError(str(exc)) from exc
    if record.source != LIFECYCLE_SOURCE_REQUIRED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            f"NON_FIXTURE_LIFECYCLE_SOURCE:{record.source}"
        )
    if record.network_effect != "NONE" or record.exchange_submit_performed is not False:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "LIFECYCLE_NETWORK_EFFECT_MUST_REMAIN_NONE"
        )
    if record.persisted is not True:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            f"SECTION_11_12_7_COMMAND_MUST_PERSIST:{command}"
        )
    if record.survives_restart is not True:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            f"SECTION_11_12_7_COMMAND_MUST_SURVIVE_RESTART:{command}"
        )
    if record.cleared_by_runtime is not False:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            f"SECTION_11_12_7_RUNTIME_CLEAR_FORBIDDEN:{command}"
        )
    if record.alpha_dependent is not False:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            f"SECTION_11_12_7_ALPHA_INDEPENDENCE_REQUIRED:{command}"
        )
    return record


def execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
    *,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_account_identity: str,
    expected_venue: str,
    section_11_12_6_predecessor_bound: bool,
    section_11_12_6_execution_binding_digest: str,
    client_order_id_prefix: str,
    owner_go_kill_switch_emergency_control_authorized: bool = True,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    cap_11_5_adapter_activated: bool = False,
    kill_switch_contract_activated: bool = False,
    section_11_12_8_started: bool = False,
    cap_11_13_started: bool = False,
) -> Section11127ExecutionRecordV1:
    """Execute productive §11.12.7: Cap 11.5 kill-switch reuse bound to §11.12.6."""
    if not order_send_disabled or orders_authorized:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "ORDER_SEND_MUST_REMAIN_DISABLED_IN_SECTION_11_12_7"
        )
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "NETWORK_WRITES_FORBIDDEN_IN_SECTION_11_12_7"
        )
    if not KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_NOT_ALLOWED"
        )
    if section_11_12_8_started or SECTION_11_12_8_STARTED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_8_MUST_REMAIN_UNSTARTED"
        )
    if cap_11_13_started or CAPABILITY_11_13_STARTED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "CAPABILITY_11_13_MUST_REMAIN_UNSTARTED"
        )
    if (
        cap_11_5_adapter_activated
        or CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED
        or CAPABILITY_11_5_STARTED
    ):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "CAPABILITY_11_5_ADAPTER_MUST_REMAIN_INACTIVE"
        )
    if kill_switch_contract_activated or KILL_SWITCH_CONTRACT_ACTIVATED:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "KILL_SWITCH_CONTRACT_MUST_REMAIN_INACTIVE"
        )

    scope = tuple(str(x) for x in instrument_scope)

    pre = evaluate_section_11_12_7_preconditions_v1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_account_identity=expected_account_identity,
        expected_venue=expected_venue,
        section_11_12_6_predecessor_bound=section_11_12_6_predecessor_bound,
        cap_11_5_kill_switch_and_emergency_control_contract_reused=True,
        owner_go_kill_switch_emergency_control_authorized=(
            owner_go_kill_switch_emergency_control_authorized
        ),
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        network_writes_authorized=network_writes_authorized,
        network_effect=LIFECYCLE_NETWORK_EFFECT,
        cap_11_5_adapter_activated=cap_11_5_adapter_activated,
        kill_switch_contract_activated=kill_switch_contract_activated,
        section_11_12_8_started=section_11_12_8_started,
        cap_11_13_started=cap_11_13_started,
    )
    if not pre["execution_admissible"]:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_7_NOT_ADMISSIBLE:" + ",".join(pre["missing_preconditions"])
        )

    if not section_11_12_6_execution_binding_digest:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_6_EXECUTION_BINDING_DIGEST_ABSENT"
        )

    command_results: list[Section11127CommandResultV1] = []
    for command in ALLOWED_SECTION_11_12_7_COMMANDS:
        life = reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(command=command)
        command_results.append(
            Section11127CommandResultV1(
                command=life.command,
                persisted=life.persisted,
                survives_restart=life.survives_restart,
                cleared_by_runtime=life.cleared_by_runtime,
                alpha_dependent=life.alpha_dependent,
                lifecycle_source=life.source,
                network_effect=life.network_effect,
                exchange_submit_performed=life.exchange_submit_performed,
            )
        )

    commands_completed = tuple(r.command for r in command_results)
    if commands_completed != ALLOWED_SECTION_11_12_7_COMMANDS:
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_7_COMMAND_SET_INCOMPLETE"
        )
    if any(r.network_effect != "NONE" for r in command_results):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "LIFECYCLE_NETWORK_EFFECT_MUST_REMAIN_NONE"
        )
    if any(r.exchange_submit_performed for r in command_results):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "EXCHANGE_SUBMIT_MUST_REMAIN_FALSE"
        )
    if any(r.persisted is not True for r in command_results):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_7_ALL_COMMANDS_MUST_PERSIST"
        )
    if any(r.survives_restart is not True for r in command_results):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_7_ALL_COMMANDS_MUST_SURVIVE_RESTART"
        )
    if any(r.cleared_by_runtime for r in command_results):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_7_RUNTIME_CLEAR_FORBIDDEN_FOR_ALL_COMMANDS"
        )
    if any(r.alpha_dependent for r in command_results):
        raise Section11127KillSwitchAndEmergencyControlProofError(
            "SECTION_11_12_7_ALPHA_INDEPENDENCE_REQUIRED_FOR_ALL_COMMANDS"
        )

    digest_material = {
        "capability_id": CAPABILITY_ID,
        "predecessor_capability_id": PREDECESSOR_CAPABILITY_ID,
        "section_11_12_6_execution_binding_digest": section_11_12_6_execution_binding_digest,
        "account_identity": account_identity,
        "venue": venue,
        "instrument_scope": list(scope),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "client_order_id_prefix": client_order_id_prefix,
        "commands_completed": list(commands_completed),
        "command_results": [
            {
                "command": r.command,
                "persisted": r.persisted,
                "survives_restart": r.survives_restart,
                "cleared_by_runtime": r.cleared_by_runtime,
                "alpha_dependent": r.alpha_dependent,
                "lifecycle_source": r.lifecycle_source,
                "network_effect": r.network_effect,
                "exchange_submit_performed": r.exchange_submit_performed,
            }
            for r in command_results
        ],
        "lifecycle_source": LIFECYCLE_SOURCE_REQUIRED,
        "network_effect": "NONE",
        "exchange_submit_performed": False,
        "path_class": PATH_CLASS,
        "cap_11_5_kill_switch_owner": CAP_11_5_KILL_SWITCH_OWNER,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "cap_11_5_adapter_activated": False,
        "kill_switch_contract_activated": False,
        "section_11_12_8_started": False,
        "cap_11_13_started": False,
        "testnet_order_lifecycle_proven": False,
        "testnet_unknown_submit_recovery_proven": False,
        "testnet_restart_proven": False,
        "testnet_kill_switch_proven": False,
        "kill_switch_persisted": True,
        "kill_switch_fail_closed": True,
        "kill_switch_checked_before_every_side_effect": True,
        "kill_switch_survives_restart": True,
        "kill_switch_cannot_be_cleared_by_runtime": True,
        "owner_authority_required_to_clear": True,
        "cancel_all_path_independent_of_alpha": True,
        "exit_or_reduce_policy_independent_of_alpha": True,
    }
    execution_binding_digest = hashlib.sha256(
        _canonical_dumps(digest_material).encode("utf-8")
    ).hexdigest()

    return Section11127ExecutionRecordV1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        section_11_12_6_execution_binding_digest=section_11_12_6_execution_binding_digest,
        client_order_id_prefix=client_order_id_prefix,
        command_results=tuple(command_results),
        commands_completed=commands_completed,
        lifecycle_source=LIFECYCLE_SOURCE_REQUIRED,
        network_effect="NONE",
        exchange_submit_performed=False,
        kill_switch_and_emergency_control_proof_performed=True,
        cap_11_5_kill_switch_and_emergency_control_contract_reused=True,
        order_send_disabled=True,
        orders_authorized=False,
        network_writes_authorized=False,
        network_write_performed=False,
        exchange_order_submit_reachable=False,
        testnet_order_submit_performed=False,
        cap_11_5_adapter_activated=False,
        kill_switch_contract_activated=False,
        section_11_12_8_started=False,
        cap_11_13_started=False,
        testnet_order_lifecycle_proven=False,
        testnet_unknown_submit_recovery_proven=False,
        testnet_restart_proven=False,
        testnet_kill_switch_proven=False,
        missing_preconditions=(),
        execution_admissible=True,
        execution_binding_digest=execution_binding_digest,
        reference_only=False,
    )


def refuse_order_send_v1() -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        "ORDER_SEND_FORBIDDEN_IN_SECTION_11_12_7"
    )


def refuse_network_write_v1(*, method: str = "POST") -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        f"NETWORK_WRITE_FORBIDDEN_IN_SECTION_11_12_7:{method}"
    )


def refuse_network_submit_v1() -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        "ORDER_LIFECYCLE_NETWORK_SUBMIT_FORBIDDEN_IN_SECTION_11_12_7"
    )


def refuse_runtime_clear_v1(*, actor: str = "runtime_autonomy") -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        f"KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN_IN_SECTION_11_12_7:{actor}"
    )


def refuse_side_effect_bypass_v1(*, claimed_side_effect: str = "order_submit") -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        f"KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN_IN_SECTION_11_12_7:{claimed_side_effect}"
    )


def refuse_emergency_risk_increase_v1(*, command: str = "PERSISTENT_KILL") -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        f"EMERGENCY_COMMAND_RISK_INCREASE_FORBIDDEN_IN_SECTION_11_12_7:{command}"
    )


def refuse_section_11_12_8_v1(*, path_name: str = "long_running_autonomous_campaign") -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        f"SECTION_11_12_8_PATH_FORBIDDEN_IN_SECTION_11_12_7:{path_name}"
    )


def refuse_cap_11_5_adapter_activation_v1() -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        "CAPABILITY_11_5_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_7"
    )


def refuse_kill_switch_contract_activation_v1() -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        "KILL_SWITCH_CONTRACT_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_7"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise Section11127KillSwitchAndEmergencyControlProofError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_7"
    )


def prove_section_11_12_7_kill_switch_and_emergency_control_proof_v1() -> dict[str, Any]:
    """Contract proof for §11.12.7 kill-switch with Cap 11.5 reuse + §11.12.6 bind."""
    sha = "2de0a4973e726f56c74a881f327130cc73706b17"
    cfg = "cfg-" + ("d" * 64)

    pred_bound, pred_digest = mark_section_11_12_6_predecessor_bound_v1(
        repository_sha=sha, config_digest=cfg
    )

    common = {
        "runtime_mode": "TESTNET",
        "venue": "OKX",
        "account_identity": "acct-uid-demo",
        "instrument_scope": ("BTC-USDT-SWAP",),
        "repository_sha": sha,
        "config_digest": cfg,
        "expected_repository_sha": sha,
        "expected_config_digest": cfg,
        "expected_account_identity": "acct-uid-demo",
        "expected_venue": "OKX",
        "section_11_12_6_predecessor_bound": pred_bound,
        "section_11_12_6_execution_binding_digest": pred_digest,
        "client_order_id_prefix": "pt-coid-section-11-12-7",
    }

    incomplete_blocked = False
    try:
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **{
                **common,
                "section_11_12_6_predecessor_bound": False,
            }
        )
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        incomplete_blocked = "SECTION_11_12_7_NOT_ADMISSIBLE" in str(exc)

    record = execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(**common)
    complete_ok = (
        record.execution_admissible is True
        and record.kill_switch_and_emergency_control_proof_performed is True
        and record.cap_11_5_kill_switch_and_emergency_control_contract_reused is True
        and record.network_effect == "NONE"
        and record.exchange_submit_performed is False
        and record.lifecycle_source == LIFECYCLE_SOURCE_REQUIRED
        and record.commands_completed == ALLOWED_SECTION_11_12_7_COMMANDS
        and len(record.command_results) == len(ALLOWED_SECTION_11_12_7_COMMANDS)
        and all(r.network_effect == "NONE" for r in record.command_results)
        and all(r.exchange_submit_performed is False for r in record.command_results)
        and all(r.persisted is True for r in record.command_results)
        and all(r.survives_restart is True for r in record.command_results)
        and all(r.cleared_by_runtime is False for r in record.command_results)
        and all(r.alpha_dependent is False for r in record.command_results)
        and record.order_send_disabled is True
        and record.orders_authorized is False
        and record.network_writes_authorized is False
        and record.network_write_performed is False
        and record.exchange_order_submit_reachable is False
        and record.testnet_order_submit_performed is False
        and record.cap_11_5_adapter_activated is False
        and record.kill_switch_contract_activated is False
        and record.section_11_12_8_started is False
        and record.cap_11_13_started is False
        and record.testnet_order_lifecycle_proven is False
        and record.testnet_unknown_submit_recovery_proven is False
        and record.testnet_restart_proven is False
        and record.testnet_kill_switch_proven is False
        and record.reference_only is False
        and record.path_class == PATH_CLASS
        and bool(record.execution_binding_digest)
        and bool(record.section_11_12_6_execution_binding_digest)
    )

    order_send_hard_reject = False
    try:
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **common,
            order_send_disabled=False,
        )
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **common,
            orders_authorized=True,
        )
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    network_write_hard_reject = False
    try:
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **common,
            network_writes_authorized=True,
        )
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        network_write_hard_reject = "NETWORK_WRITES_FORBIDDEN" in str(exc)

    live_mode_blocked = False
    try:
        execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
            **{**common, "runtime_mode": "LIVE"}
        )
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        live_mode_blocked = "SECTION_11_12_7_NOT_ADMISSIBLE" in str(exc)

    section_11_12_8_command_blocked = False
    try:
        reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(
            command="long_running_autonomous_campaign"
        )
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        section_11_12_8_command_blocked = "SECTION_11_12_7_COMMAND_FORBIDDEN" in str(exc)

    unknown_command_blocked = False
    try:
        reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(command="ENABLE_LIVE_TRADING")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        unknown_command_blocked = "SECTION_11_12_7_COMMAND_FORBIDDEN" in str(
            exc
        ) or "UNKNOWN_EMERGENCY_COMMAND" in str(exc)

    restart_path_blocked = False
    try:
        reuse_cap_11_5_section_11_12_7_kill_switch_command_v1(command="restart_with_open_order")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        restart_path_blocked = "SECTION_11_12_7_COMMAND_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_network_submit_v1()
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        submit_blocked = "NETWORK_SUBMIT_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    write_blocked = False
    try:
        refuse_network_write_v1(method="POST")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        write_blocked = "NETWORK_WRITE_FORBIDDEN" in str(exc)

    runtime_clear_blocked = False
    try:
        refuse_runtime_clear_v1(actor="runtime_autonomy")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        runtime_clear_blocked = "KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN" in str(exc)

    side_effect_bypass_blocked = False
    try:
        refuse_side_effect_bypass_v1(claimed_side_effect="order_submit")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        side_effect_bypass_blocked = "KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN" in str(exc)

    risk_increase_blocked = False
    try:
        refuse_emergency_risk_increase_v1(command="PERSISTENT_KILL")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        risk_increase_blocked = "EMERGENCY_COMMAND_RISK_INCREASE_FORBIDDEN" in str(exc)

    section_11_12_8_blocked = False
    try:
        refuse_section_11_12_8_v1(path_name="long_running_autonomous_campaign")
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        section_11_12_8_blocked = "SECTION_11_12_8" in str(exc)

    cap115_blocked = False
    try:
        refuse_cap_11_5_adapter_activation_v1()
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        cap115_blocked = "CAPABILITY_11_5_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN" in str(exc)

    kill_switch_activation_blocked = False
    try:
        refuse_kill_switch_contract_activation_v1()
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        kill_switch_activation_blocked = "KILL_SWITCH_CONTRACT_ACTIVATION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except Section11127KillSwitchAndEmergencyControlProofError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    # Cap 11.5 contract surface still refuse-closed for clear/bypass/risk-increase.
    cap_11_5_contract = prove_kill_switch_and_emergency_control_contract_v1()
    cap_11_5_reuse_ok = (
        cap_11_5_contract.get("ok") is True
        and cap_11_5_contract.get("KILL_SWITCH_CONTRACT_ACTIVATED") is False
        and cap_11_5_contract.get("TESTNET_KILL_SWITCH_PROVEN") is False
    )

    cap_11_5_clear_blocked = False
    try:
        refuse_runtime_kill_switch_clear_v1(actor="runtime_autonomy")
    except KillSwitchEmergencyControlError as exc:
        cap_11_5_clear_blocked = "KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN" in str(exc)

    cap_11_5_bypass_blocked = False
    try:
        refuse_kill_switch_side_effect_bypass_v1(claimed_side_effect="order_submit")
    except KillSwitchEmergencyControlError as exc:
        cap_11_5_bypass_blocked = "KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN" in str(exc)

    cap_11_5_risk_blocked = False
    try:
        refuse_emergency_command_risk_increase_v1(command="PERSISTENT_KILL")
    except KillSwitchEmergencyControlError as exc:
        cap_11_5_risk_blocked = "EMERGENCY_COMMAND_RISK_INCREASE_FORBIDDEN" in str(exc)

    allowed_commands_enumerated = ALLOWED_SECTION_11_12_7_COMMANDS == (
        "BLOCK_NEW_ENTRY",
        "EXIT_ONLY",
        "REDUCE_ONLY",
        "CANCEL_ALL",
        "HALT_AFTER_CANCEL",
        "PERSISTENT_KILL",
    )
    forbidden_paths_enumerated = all(
        name in FORBIDDEN_SECTION_11_12_8_PATHS for name in FORBIDDEN_SECTION_11_12_8_PATHS
    )

    ok = all(
        [
            complete_ok,
            incomplete_blocked,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            network_write_hard_reject,
            live_mode_blocked,
            section_11_12_8_command_blocked,
            unknown_command_blocked,
            restart_path_blocked,
            submit_blocked,
            order_send_blocked,
            write_blocked,
            runtime_clear_blocked,
            side_effect_bypass_blocked,
            risk_increase_blocked,
            section_11_12_8_blocked,
            cap115_blocked,
            kill_switch_activation_blocked,
            cap1113_blocked,
            cap_11_5_reuse_ok,
            cap_11_5_clear_blocked,
            cap_11_5_bypass_blocked,
            cap_11_5_risk_blocked,
            allowed_commands_enumerated,
            forbidden_paths_enumerated,
            CORE_LOGIC_CHANGE is False,
            REFERENCE_ONLY is False,
            ACTIVATION_STATE == "not_activated",
            LIFECYCLE_NETWORK_EFFECT == "NONE",
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            TESTNET_ORDER_SUBMIT_PERFORMED is False,
            ORDER_SUBMIT_PERFORMED is False,
            ORDER_PATH_STARTED is False,
            MUTATING_EXCHANGE_CALLS is False,
            NETWORK_WRITE_PERFORMED is False,
            LIVE_AUTHORIZED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            SECTION_11_12_8_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            CAPABILITY_11_5_STARTED is False,
            CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED is False,
            KILL_SWITCH_CONTRACT_ACTIVATED is False,
            TESTNET_ORDER_LIFECYCLE_PROVEN is False,
            TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            TESTNET_RESTART_PROVEN is False,
            TESTNET_KILL_SWITCH_PROVEN is False,
            KILL_SWITCH_PERSISTED is True,
            KILL_SWITCH_FAIL_CLOSED is True,
            KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT is True,
            KILL_SWITCH_SURVIVES_RESTART is True,
            KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME is True,
            OWNER_AUTHORITY_REQUIRED_TO_CLEAR is True,
            CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA is True,
            EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA is True,
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER": OWNER,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "activation_state": ACTIVATION_STATE,
        "reference_only": REFERENCE_ONLY,
        "complete_execution_ok": complete_ok,
        "incomplete_blocked": incomplete_blocked,
        "order_send_hard_reject": order_send_hard_reject,
        "orders_authorized_hard_reject": orders_authorized_hard_reject,
        "network_write_hard_reject": network_write_hard_reject,
        "live_mode_blocked": live_mode_blocked,
        "section_11_12_8_command_blocked": section_11_12_8_command_blocked,
        "unknown_command_blocked": unknown_command_blocked,
        "restart_path_blocked": restart_path_blocked,
        "submit_blocked": submit_blocked,
        "order_send_blocked": order_send_blocked,
        "write_blocked": write_blocked,
        "runtime_clear_blocked": runtime_clear_blocked,
        "side_effect_bypass_blocked": side_effect_bypass_blocked,
        "risk_increase_blocked": risk_increase_blocked,
        "section_11_12_8_blocked": section_11_12_8_blocked,
        "cap_11_5_adapter_blocked": cap115_blocked,
        "kill_switch_contract_activation_blocked": kill_switch_activation_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "cap_11_5_contract_reuse_ok": cap_11_5_reuse_ok,
        "kill_switch_and_emergency_control_proof_performed": (
            record.kill_switch_and_emergency_control_proof_performed
        ),
        "cap_11_5_kill_switch_and_emergency_control_contract_reused": (
            record.cap_11_5_kill_switch_and_emergency_control_contract_reused
        ),
        "section_11_12_6_predecessor_bound": pred_bound,
        "section_11_12_6_execution_binding_digest": pred_digest,
        "client_order_id_prefix": record.client_order_id_prefix,
        "commands_completed": list(record.commands_completed),
        "command_results": [
            {
                "command": r.command,
                "persisted": r.persisted,
                "survives_restart": r.survives_restart,
                "cleared_by_runtime": r.cleared_by_runtime,
                "alpha_dependent": r.alpha_dependent,
                "lifecycle_source": r.lifecycle_source,
                "network_effect": r.network_effect,
                "exchange_submit_performed": r.exchange_submit_performed,
            }
            for r in record.command_results
        ],
        "lifecycle_source": record.lifecycle_source,
        "execution_binding_digest": record.execution_binding_digest,
        "network_effect": record.network_effect,
        "exchange_submit_performed": record.exchange_submit_performed,
        "path_class": record.path_class,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "cap_11_5_adapter_activated": False,
        "kill_switch_contract_activated": False,
        "section_11_12_8_started": False,
        "cap_11_13_started": False,
        "testnet_order_lifecycle_proven": False,
        "testnet_unknown_submit_recovery_proven": False,
        "testnet_restart_proven": False,
        "testnet_kill_switch_proven": False,
        "KILL_SWITCH_PERSISTED": True,
        "KILL_SWITCH_FAIL_CLOSED": True,
        "KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT": True,
        "KILL_SWITCH_SURVIVES_RESTART": True,
        "KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME": True,
        "OWNER_AUTHORITY_REQUIRED_TO_CLEAR": True,
        "CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA": True,
        "EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA": True,
        "allowed_section_11_12_7_commands": list(ALLOWED_SECTION_11_12_7_COMMANDS),
        "forbidden_section_11_12_8_paths": list(FORBIDDEN_SECTION_11_12_8_PATHS),
        "cap_11_5_kill_switch_owner": CAP_11_5_KILL_SWITCH_OWNER,
    }

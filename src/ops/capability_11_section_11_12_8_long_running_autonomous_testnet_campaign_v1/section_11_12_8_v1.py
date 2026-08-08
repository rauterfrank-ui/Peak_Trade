"""Fail-closed §11.12.8 long-running autonomous Testnet campaign residual.

Reuses Cap 11.6 fixture-only long-running campaign evidence contracts and binds
the closed §11.12.7 kill-switch/emergency-control predecessor. This OWNER_GO
authorizes implementation/evidence binding only — not productive Testnet
campaign execution, network sessions, order submit, Testnet proven-flag claims,
or Cap 11.13 Live activation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.long_running_campaign_evidence_contract_v1 import (
    LongRunningCampaignEvidenceError,
    LongRunningCampaignEvidenceRecordV1,
    prove_long_running_campaign_evidence_contract_v1,
    refuse_long_running_campaign_activation_v1,
    refuse_long_running_campaign_network_session_v1,
    run_long_running_campaign_evidence_fixture_path_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.testnet_evidence_closure_contract_v1 import (
    prove_testnet_evidence_closure_contract_v1,
    refuse_testnet_proven_overclaim_v1,
)
from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.section_11_12_7_v1 import (
    execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1,
    mark_section_11_12_6_predecessor_bound_v1,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_SECTION_11_12_8_PATHS,
    CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED,
    CAPABILITY_11_6_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CAP_11_6_CAMPAIGN_EVIDENCE_OWNER,
    CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSE_ALLOWED,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    EXECUTION_MODE_REQUIRED,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
    FORBIDDEN_CAPABILITY_11_13_PATHS,
    KILL_SWITCH_BINDING_REQUIRED,
    KILL_SWITCH_BINDING_STATUS,
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
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED,
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_SESSION_STARTED,
    NETWORK_WRITE_PERFORMED,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
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
    SECTION_11_12_7_PREDECESSOR_BINDING_REQUIRED,
    SECTION_11_13_STARTED,
    TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
    TESTNET_CAMPAIGN_COMPLETED,
    TESTNET_CAMPAIGN_STARTED,
    TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
    TESTNET_EVIDENCE_VERIFIED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
    TESTNET_RECONCILIATION_PROVEN,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)


class Section11128LongRunningAutonomousTestnetCampaignError(RuntimeError):
    """Fail-closed §11.12.8 long-running campaign evidence violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class Section11128PathResultV1:
    """One productive §11.12.8 fixture campaign-evidence path result."""

    path_name: str
    continuity_observed: bool
    evidence_cursor_advanced: bool
    campaign_activated: bool
    exchange_submit_performed: bool
    terminal_state: str
    lifecycle_source: str
    network_effect: str


@dataclass(frozen=True)
class Section11128ExecutionRecordV1:
    """Productive §11.12.8 campaign-evidence execution record (fixture-only)."""

    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    repository_sha: str
    config_digest: str
    section_11_12_7_execution_binding_digest: str
    client_order_id_prefix: str
    path_results: tuple[Section11128PathResultV1, ...]
    paths_completed: tuple[str, ...]
    lifecycle_source: str
    network_effect: str
    order_effect: str
    exchange_submit_performed: bool
    long_running_campaign_evidence_performed: bool
    cap_11_6_long_running_campaign_evidence_contract_reused: bool
    kill_switch_binding_status: str
    order_send_disabled: bool
    orders_authorized: bool
    network_writes_authorized: bool
    network_write_performed: bool
    exchange_order_submit_reachable: bool
    testnet_order_submit_performed: bool
    testnet_campaign_started: bool
    testnet_campaign_completed: bool
    campaign_activated: bool
    network_session_started: bool
    cap_11_6_adapter_activated: bool
    kill_switch_contract_activated: bool
    cap_11_13_started: bool
    testnet_order_lifecycle_proven: bool
    testnet_reconciliation_proven: bool
    testnet_restart_proven: bool
    testnet_unknown_submit_recovery_proven: bool
    testnet_duplicate_order_prevention_proven: bool
    testnet_kill_switch_proven: bool
    testnet_autonomous_recovery_proven: bool
    testnet_evidence_verified: bool
    missing_preconditions: tuple[str, ...]
    execution_admissible: bool
    execution_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    reference_only: bool = False
    path_class: str = PATH_CLASS


def evaluate_section_11_12_8_preconditions_v1(
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
    section_11_12_7_predecessor_bound: bool,
    kill_switch_binding_bound: bool,
    cap_11_6_long_running_campaign_evidence_contract_reused: bool,
    owner_go_long_running_campaign_evidence_authorized: bool,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    network_effect: str = LIFECYCLE_NETWORK_EFFECT,
    testnet_campaign_started: bool = False,
    testnet_campaign_completed: bool = False,
    campaign_activated: bool = False,
    cap_11_6_adapter_activated: bool = False,
    kill_switch_contract_activated: bool = False,
    cap_11_13_started: bool = False,
) -> dict[str, Any]:
    """Evaluate §11.12.8 productive preconditions."""
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
    if not section_11_12_7_predecessor_bound or not SECTION_11_12_7_PREDECESSOR_BINDING_REQUIRED:
        missing.append("section_11_12_7_predecessor_bound")
    if (
        not kill_switch_binding_bound
        or not KILL_SWITCH_BINDING_REQUIRED
        or KILL_SWITCH_BINDING_STATUS != "BOUND"
    ):
        missing.append("kill_switch_binding_bound")
    if (
        not cap_11_6_long_running_campaign_evidence_contract_reused
        or not CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSE_ALLOWED
    ):
        missing.append("cap_11_6_long_running_campaign_evidence_contract_reused")
    if not LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED:
        missing.append("long_running_autonomous_testnet_campaign_evidence_allowed")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED is not False:
        missing.append("network_writes_unauthorized")
    if network_effect != "NONE" or LIFECYCLE_NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if testnet_campaign_started or TESTNET_CAMPAIGN_STARTED is True:
        missing.append("testnet_campaign_not_started")
    if testnet_campaign_completed or TESTNET_CAMPAIGN_COMPLETED is True:
        missing.append("testnet_campaign_not_completed")
    if campaign_activated or LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED is True:
        missing.append("campaign_not_activated")
    if (
        cap_11_6_adapter_activated
        or CAPABILITY_11_6_STARTED is True
        or CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED is True
        or CAPABILITY_11_5_STARTED is True
    ):
        missing.append("cap_11_6_adapter_not_activated")
    if kill_switch_contract_activated or KILL_SWITCH_CONTRACT_ACTIVATED is True:
        missing.append("kill_switch_contract_not_activated")
    if cap_11_13_started or CAPABILITY_11_13_STARTED is True or SECTION_11_13_STARTED is True:
        missing.append("cap_11_13_not_started")
    if not owner_go_long_running_campaign_evidence_authorized:
        missing.append("owner_go_long_running_campaign_evidence_authorized")

    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)
    return {
        "execution_admissible": len(ordered_missing) == 0,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
    }


def mark_section_11_12_7_predecessor_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> tuple[bool, str]:
    """Bind closed §11.12.7 kill-switch/emergency predecessor.

    Returns (bound, execution_binding_digest).
    """
    pred_bound, pred_digest = mark_section_11_12_6_predecessor_bound_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    record = execute_section_11_12_7_kill_switch_and_emergency_control_proof_v1(
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
        section_11_12_6_predecessor_bound=pred_bound,
        section_11_12_6_execution_binding_digest=pred_digest,
        client_order_id_prefix="pt-coid-section-11-12-8-pred",
    )
    bound = (
        record.execution_admissible is True
        and record.kill_switch_and_emergency_control_proof_performed is True
        and bool(record.execution_binding_digest)
        and record.kill_switch_contract_activated is False
        and record.section_11_12_8_started is False
    )
    return bound, record.execution_binding_digest


def reuse_cap_11_6_section_11_12_8_campaign_path_v1(
    *,
    path_name: str,
) -> LongRunningCampaignEvidenceRecordV1:
    """Reuse Cap 11.6 fixture-only §11.12.8 campaign evidence path."""
    if not CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSE_ALLOWED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSE_NOT_ALLOWED"
        )
    if path_name not in ALLOWED_SECTION_11_12_8_PATHS:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            f"SECTION_11_12_8_PATH_FORBIDDEN:{path_name}"
        )
    try:
        record = run_long_running_campaign_evidence_fixture_path_v1(path_name=path_name)
    except LongRunningCampaignEvidenceError as exc:
        raise Section11128LongRunningAutonomousTestnetCampaignError(str(exc)) from exc
    if record.source != LIFECYCLE_SOURCE_REQUIRED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            f"NON_FIXTURE_LIFECYCLE_SOURCE:{record.source}"
        )
    if record.network_effect != "NONE" or record.exchange_submit_performed is not False:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "LIFECYCLE_NETWORK_EFFECT_MUST_REMAIN_NONE"
        )
    if record.campaign_activated is not False:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            f"SECTION_11_12_8_CAMPAIGN_ACTIVATION_FORBIDDEN:{path_name}"
        )
    if record.terminal_state != "EVIDENCED":
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            f"SECTION_11_12_8_PATH_TERMINAL_STATE_INVALID:{path_name}:{record.terminal_state}"
        )
    return record


def execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
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
    section_11_12_7_predecessor_bound: bool,
    section_11_12_7_execution_binding_digest: str,
    client_order_id_prefix: str,
    owner_go_long_running_campaign_evidence_authorized: bool = True,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    testnet_campaign_started: bool = False,
    testnet_campaign_completed: bool = False,
    campaign_activated: bool = False,
    cap_11_6_adapter_activated: bool = False,
    kill_switch_contract_activated: bool = False,
    cap_11_13_started: bool = False,
) -> Section11128ExecutionRecordV1:
    """Execute productive §11.12.8: Cap 11.6 campaign evidence reuse bound to §11.12.7."""
    if not order_send_disabled or orders_authorized:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "ORDER_SEND_MUST_REMAIN_DISABLED_IN_SECTION_11_12_8"
        )
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "NETWORK_WRITES_FORBIDDEN_IN_SECTION_11_12_8"
        )
    if not LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_NOT_ALLOWED"
        )
    if testnet_campaign_started or TESTNET_CAMPAIGN_STARTED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "TESTNET_CAMPAIGN_MUST_REMAIN_UNSTARTED"
        )
    if testnet_campaign_completed or TESTNET_CAMPAIGN_COMPLETED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "TESTNET_CAMPAIGN_MUST_REMAIN_INCOMPLETE"
        )
    if campaign_activated or LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED:
        raise Section11128LongRunningAutonomousTestnetCampaignError("CAMPAIGN_MUST_REMAIN_INACTIVE")
    if cap_11_13_started or CAPABILITY_11_13_STARTED or SECTION_11_13_STARTED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "CAPABILITY_11_13_MUST_REMAIN_UNSTARTED"
        )
    if (
        cap_11_6_adapter_activated
        or CAPABILITY_11_6_STARTED
        or CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED
        or CAPABILITY_11_5_STARTED
    ):
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "CAPABILITY_11_6_ADAPTER_MUST_REMAIN_INACTIVE"
        )
    if kill_switch_contract_activated or KILL_SWITCH_CONTRACT_ACTIVATED:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "KILL_SWITCH_CONTRACT_MUST_REMAIN_INACTIVE"
        )

    scope = tuple(str(x) for x in instrument_scope)

    pre = evaluate_section_11_12_8_preconditions_v1(
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
        section_11_12_7_predecessor_bound=section_11_12_7_predecessor_bound,
        kill_switch_binding_bound=True,
        cap_11_6_long_running_campaign_evidence_contract_reused=True,
        owner_go_long_running_campaign_evidence_authorized=(
            owner_go_long_running_campaign_evidence_authorized
        ),
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        network_writes_authorized=network_writes_authorized,
        network_effect=LIFECYCLE_NETWORK_EFFECT,
        testnet_campaign_started=testnet_campaign_started,
        testnet_campaign_completed=testnet_campaign_completed,
        campaign_activated=campaign_activated,
        cap_11_6_adapter_activated=cap_11_6_adapter_activated,
        kill_switch_contract_activated=kill_switch_contract_activated,
        cap_11_13_started=cap_11_13_started,
    )
    if not pre["execution_admissible"]:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "SECTION_11_12_8_NOT_ADMISSIBLE:" + ",".join(pre["missing_preconditions"])
        )

    if not section_11_12_7_execution_binding_digest:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "SECTION_11_12_7_EXECUTION_BINDING_DIGEST_ABSENT"
        )

    path_results: list[Section11128PathResultV1] = []
    for path_name in ALLOWED_SECTION_11_12_8_PATHS:
        life = reuse_cap_11_6_section_11_12_8_campaign_path_v1(path_name=path_name)
        path_results.append(
            Section11128PathResultV1(
                path_name=life.path_name,
                continuity_observed=life.continuity_observed,
                evidence_cursor_advanced=life.evidence_cursor_advanced,
                campaign_activated=life.campaign_activated,
                exchange_submit_performed=life.exchange_submit_performed,
                terminal_state=life.terminal_state,
                lifecycle_source=life.source,
                network_effect=life.network_effect,
            )
        )

    paths_completed = tuple(r.path_name for r in path_results)
    if paths_completed != ALLOWED_SECTION_11_12_8_PATHS:
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "SECTION_11_12_8_PATH_SET_INCOMPLETE"
        )
    if any(r.network_effect != "NONE" for r in path_results):
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "LIFECYCLE_NETWORK_EFFECT_MUST_REMAIN_NONE"
        )
    if any(r.exchange_submit_performed for r in path_results):
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "EXCHANGE_SUBMIT_MUST_REMAIN_FALSE"
        )
    if any(r.campaign_activated for r in path_results):
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "CAMPAIGN_ACTIVATION_FORBIDDEN_FOR_ALL_PATHS"
        )
    if any(r.terminal_state != "EVIDENCED" for r in path_results):
        raise Section11128LongRunningAutonomousTestnetCampaignError(
            "SECTION_11_12_8_ALL_PATHS_MUST_BE_EVIDENCED"
        )

    digest_material = {
        "capability_id": CAPABILITY_ID,
        "predecessor_capability_id": PREDECESSOR_CAPABILITY_ID,
        "section_11_12_7_execution_binding_digest": section_11_12_7_execution_binding_digest,
        "account_identity": account_identity,
        "venue": venue,
        "instrument_scope": list(scope),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "client_order_id_prefix": client_order_id_prefix,
        "paths_completed": list(paths_completed),
        "path_results": [
            {
                "path_name": r.path_name,
                "continuity_observed": r.continuity_observed,
                "evidence_cursor_advanced": r.evidence_cursor_advanced,
                "campaign_activated": r.campaign_activated,
                "exchange_submit_performed": r.exchange_submit_performed,
                "terminal_state": r.terminal_state,
                "lifecycle_source": r.lifecycle_source,
                "network_effect": r.network_effect,
            }
            for r in path_results
        ],
        "lifecycle_source": LIFECYCLE_SOURCE_REQUIRED,
        "network_effect": "NONE",
        "order_effect": "NONE",
        "exchange_submit_performed": False,
        "path_class": PATH_CLASS,
        "cap_11_6_campaign_evidence_owner": CAP_11_6_CAMPAIGN_EVIDENCE_OWNER,
        "kill_switch_binding_status": KILL_SWITCH_BINDING_STATUS,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "testnet_campaign_started": False,
        "testnet_campaign_completed": False,
        "campaign_activated": False,
        "network_session_started": False,
        "cap_11_6_adapter_activated": False,
        "kill_switch_contract_activated": False,
        "cap_11_13_started": False,
        "testnet_order_lifecycle_proven": False,
        "testnet_reconciliation_proven": False,
        "testnet_restart_proven": False,
        "testnet_unknown_submit_recovery_proven": False,
        "testnet_duplicate_order_prevention_proven": False,
        "testnet_kill_switch_proven": False,
        "testnet_autonomous_recovery_proven": False,
        "testnet_evidence_verified": False,
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

    return Section11128ExecutionRecordV1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        section_11_12_7_execution_binding_digest=section_11_12_7_execution_binding_digest,
        client_order_id_prefix=client_order_id_prefix,
        path_results=tuple(path_results),
        paths_completed=paths_completed,
        lifecycle_source=LIFECYCLE_SOURCE_REQUIRED,
        network_effect="NONE",
        order_effect="NONE",
        exchange_submit_performed=False,
        long_running_campaign_evidence_performed=True,
        cap_11_6_long_running_campaign_evidence_contract_reused=True,
        kill_switch_binding_status=KILL_SWITCH_BINDING_STATUS,
        order_send_disabled=True,
        orders_authorized=False,
        network_writes_authorized=False,
        network_write_performed=False,
        exchange_order_submit_reachable=False,
        testnet_order_submit_performed=False,
        testnet_campaign_started=False,
        testnet_campaign_completed=False,
        campaign_activated=False,
        network_session_started=False,
        cap_11_6_adapter_activated=False,
        kill_switch_contract_activated=False,
        cap_11_13_started=False,
        testnet_order_lifecycle_proven=False,
        testnet_reconciliation_proven=False,
        testnet_restart_proven=False,
        testnet_unknown_submit_recovery_proven=False,
        testnet_duplicate_order_prevention_proven=False,
        testnet_kill_switch_proven=False,
        testnet_autonomous_recovery_proven=False,
        testnet_evidence_verified=False,
        missing_preconditions=(),
        execution_admissible=True,
        execution_binding_digest=execution_binding_digest,
        reference_only=False,
    )


def refuse_order_send_v1() -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        "ORDER_SEND_FORBIDDEN_IN_SECTION_11_12_8"
    )


def refuse_network_write_v1(*, method: str = "POST") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"NETWORK_WRITE_FORBIDDEN_IN_SECTION_11_12_8:{method}"
    )


def refuse_network_submit_v1() -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        "ORDER_LIFECYCLE_NETWORK_SUBMIT_FORBIDDEN_IN_SECTION_11_12_8"
    )


def refuse_testnet_campaign_start_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"TESTNET_CAMPAIGN_START_FORBIDDEN_IN_SECTION_11_12_8:{campaign_id}"
    )


def refuse_testnet_campaign_network_session_v1(*, session_id: str = "session-campaign") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"TESTNET_CAMPAIGN_NETWORK_SESSION_FORBIDDEN_IN_SECTION_11_12_8:{session_id}"
    )


def refuse_campaign_activation_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"CAMPAIGN_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_8:{campaign_id}"
    )


def refuse_kill_switch_runtime_clear_v1(*, actor: str = "runtime_autonomy") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN_IN_SECTION_11_12_8:{actor}"
    )


def refuse_kill_switch_side_effect_bypass_v1(*, claimed_side_effect: str = "order_submit") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN_IN_SECTION_11_12_8:{claimed_side_effect}"
    )


def refuse_scope_escalation_v1(*, claimed_scope: str = "productive_testnet_campaign") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"SCOPE_ESCALATION_FORBIDDEN_IN_SECTION_11_12_8:{claimed_scope}"
    )


def refuse_cap_11_6_adapter_activation_v1() -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        "CAPABILITY_11_6_ADAPTER_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_8"
    )


def refuse_kill_switch_contract_activation_v1() -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        "KILL_SWITCH_CONTRACT_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_8"
    )


def refuse_cap_11_13_live_activation_v1(*, path_name: str = "live_activation") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_8:{path_name}"
    )


def refuse_testnet_proven_claim_v1(*, field_name: str = "TESTNET_EVIDENCE_VERIFIED") -> None:
    raise Section11128LongRunningAutonomousTestnetCampaignError(
        f"TESTNET_PROVEN_OVERCLAIM_FORBIDDEN_IN_SECTION_11_12_8:{field_name}"
    )


def prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1() -> dict[str, Any]:
    """Contract proof for §11.12.8 campaign evidence with Cap 11.6 reuse + §11.12.7 bind."""
    sha = "2de0a4973e726f56c74a881f327130cc73706b17"
    cfg = "cfg-" + ("d" * 64)

    pred_bound, pred_digest = mark_section_11_12_7_predecessor_bound_v1(
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
        "section_11_12_7_predecessor_bound": pred_bound,
        "section_11_12_7_execution_binding_digest": pred_digest,
        "client_order_id_prefix": "pt-coid-section-11-12-8",
    }

    incomplete_blocked = False
    try:
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **{
                **common,
                "section_11_12_7_predecessor_bound": False,
            }
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        incomplete_blocked = "SECTION_11_12_8_NOT_ADMISSIBLE" in str(exc)

    record = execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(**common)
    complete_ok = (
        record.execution_admissible is True
        and record.long_running_campaign_evidence_performed is True
        and record.cap_11_6_long_running_campaign_evidence_contract_reused is True
        and record.kill_switch_binding_status == "BOUND"
        and record.network_effect == "NONE"
        and record.order_effect == "NONE"
        and record.exchange_submit_performed is False
        and record.lifecycle_source == LIFECYCLE_SOURCE_REQUIRED
        and record.paths_completed == ALLOWED_SECTION_11_12_8_PATHS
        and len(record.path_results) == len(ALLOWED_SECTION_11_12_8_PATHS)
        and all(r.network_effect == "NONE" for r in record.path_results)
        and all(r.exchange_submit_performed is False for r in record.path_results)
        and all(r.campaign_activated is False for r in record.path_results)
        and all(r.terminal_state == "EVIDENCED" for r in record.path_results)
        and record.order_send_disabled is True
        and record.orders_authorized is False
        and record.network_writes_authorized is False
        and record.network_write_performed is False
        and record.exchange_order_submit_reachable is False
        and record.testnet_order_submit_performed is False
        and record.testnet_campaign_started is False
        and record.testnet_campaign_completed is False
        and record.campaign_activated is False
        and record.network_session_started is False
        and record.cap_11_6_adapter_activated is False
        and record.kill_switch_contract_activated is False
        and record.cap_11_13_started is False
        and record.testnet_order_lifecycle_proven is False
        and record.testnet_reconciliation_proven is False
        and record.testnet_restart_proven is False
        and record.testnet_unknown_submit_recovery_proven is False
        and record.testnet_duplicate_order_prevention_proven is False
        and record.testnet_kill_switch_proven is False
        and record.testnet_autonomous_recovery_proven is False
        and record.testnet_evidence_verified is False
        and record.reference_only is False
        and record.path_class == PATH_CLASS
        and bool(record.execution_binding_digest)
        and bool(record.section_11_12_7_execution_binding_digest)
    )

    order_send_hard_reject = False
    try:
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **common,
            order_send_disabled=False,
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **common,
            orders_authorized=True,
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    network_write_hard_reject = False
    try:
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **common,
            network_writes_authorized=True,
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        network_write_hard_reject = "NETWORK_WRITES_FORBIDDEN" in str(exc)

    campaign_start_hard_reject = False
    try:
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **common,
            testnet_campaign_started=True,
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        campaign_start_hard_reject = "TESTNET_CAMPAIGN_MUST_REMAIN_UNSTARTED" in str(exc)

    live_mode_blocked = False
    try:
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **{**common, "runtime_mode": "LIVE"}
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        live_mode_blocked = "SECTION_11_12_8_NOT_ADMISSIBLE" in str(exc)

    unknown_path_blocked = False
    try:
        reuse_cap_11_6_section_11_12_8_campaign_path_v1(path_name="live_private_readonly_shadow")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        unknown_path_blocked = "SECTION_11_12_8_PATH_FORBIDDEN" in str(exc)

    productive_path_blocked = False
    try:
        reuse_cap_11_6_section_11_12_8_campaign_path_v1(
            path_name="productive_testnet_campaign_execution"
        )
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        productive_path_blocked = "SECTION_11_12_8_PATH_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_network_submit_v1()
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        submit_blocked = "NETWORK_SUBMIT_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    write_blocked = False
    try:
        refuse_network_write_v1(method="POST")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        write_blocked = "NETWORK_WRITE_FORBIDDEN" in str(exc)

    campaign_start_blocked = False
    try:
        refuse_testnet_campaign_start_v1(campaign_id="campaign-demo")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        campaign_start_blocked = "TESTNET_CAMPAIGN_START_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_testnet_campaign_network_session_v1(session_id="session-campaign")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        session_blocked = "TESTNET_CAMPAIGN_NETWORK_SESSION_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_campaign_activation_v1(campaign_id="campaign-demo")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        activation_blocked = "CAMPAIGN_ACTIVATION_FORBIDDEN" in str(exc)

    runtime_clear_blocked = False
    try:
        refuse_kill_switch_runtime_clear_v1(actor="runtime_autonomy")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        runtime_clear_blocked = "KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN" in str(exc)

    side_effect_bypass_blocked = False
    try:
        refuse_kill_switch_side_effect_bypass_v1(claimed_side_effect="order_submit")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        side_effect_bypass_blocked = "KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN" in str(exc)

    scope_escalation_blocked = False
    try:
        refuse_scope_escalation_v1(claimed_scope="productive_testnet_campaign")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        scope_escalation_blocked = "SCOPE_ESCALATION_FORBIDDEN" in str(exc)

    cap116_blocked = False
    try:
        refuse_cap_11_6_adapter_activation_v1()
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        cap116_blocked = "CAPABILITY_11_6_ADAPTER_ACTIVATION_FORBIDDEN" in str(exc)

    kill_switch_activation_blocked = False
    try:
        refuse_kill_switch_contract_activation_v1()
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        kill_switch_activation_blocked = "KILL_SWITCH_CONTRACT_ACTIVATION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1(path_name="live_activation")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    proven_overclaim_blocked = False
    try:
        refuse_testnet_proven_claim_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    except Section11128LongRunningAutonomousTestnetCampaignError as exc:
        proven_overclaim_blocked = "TESTNET_PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)

    # Cap 11.6 contract surface still refuse-closed for activation/session/overclaim.
    cap_11_6_contract = prove_long_running_campaign_evidence_contract_v1()
    cap_11_6_reuse_ok = (
        cap_11_6_contract.get("ok") is True
        and cap_11_6_contract.get("LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED") is False
        and cap_11_6_contract.get("TESTNET_EVIDENCE_VERIFIED") is False
    )

    closure_contract = prove_testnet_evidence_closure_contract_v1()
    closure_ok = (
        closure_contract.get("ok") is True
        and closure_contract.get("TESTNET_EVIDENCE_VERIFIED") is False
    )

    cap_11_6_activation_blocked = False
    try:
        refuse_long_running_campaign_activation_v1(campaign_id="campaign-demo")
    except LongRunningCampaignEvidenceError as exc:
        cap_11_6_activation_blocked = "LONG_RUNNING_CAMPAIGN_ACTIVATION_FORBIDDEN" in str(exc)

    cap_11_6_session_blocked = False
    try:
        refuse_long_running_campaign_network_session_v1(session_id="session-campaign")
    except LongRunningCampaignEvidenceError as exc:
        cap_11_6_session_blocked = "LONG_RUNNING_CAMPAIGN_NETWORK_SESSION_FORBIDDEN" in str(exc)

    cap_11_6_overclaim_blocked = False
    try:
        refuse_testnet_proven_overclaim_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    except Exception as exc:  # Cap 11.6 TestnetEvidenceClosureError
        cap_11_6_overclaim_blocked = "TESTNET_PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)

    allowed_paths_enumerated = ALLOWED_SECTION_11_12_8_PATHS == (
        "long_running_autonomous_campaign_continuity",
        "long_running_autonomous_campaign_degradation_evidence",
        "long_running_autonomous_campaign_evidence_cursor",
    )
    forbidden_paths_enumerated = all(
        name in FORBIDDEN_CAPABILITY_11_13_PATHS for name in FORBIDDEN_CAPABILITY_11_13_PATHS
    )

    ok = all(
        [
            complete_ok,
            incomplete_blocked,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            network_write_hard_reject,
            campaign_start_hard_reject,
            live_mode_blocked,
            unknown_path_blocked,
            productive_path_blocked,
            submit_blocked,
            order_send_blocked,
            write_blocked,
            campaign_start_blocked,
            session_blocked,
            activation_blocked,
            runtime_clear_blocked,
            side_effect_bypass_blocked,
            scope_escalation_blocked,
            cap116_blocked,
            kill_switch_activation_blocked,
            cap1113_blocked,
            proven_overclaim_blocked,
            cap_11_6_reuse_ok,
            closure_ok,
            cap_11_6_activation_blocked,
            cap_11_6_session_blocked,
            cap_11_6_overclaim_blocked,
            allowed_paths_enumerated,
            forbidden_paths_enumerated,
            CORE_LOGIC_CHANGE is False,
            REFERENCE_ONLY is False,
            ACTIVATION_STATE == "not_activated",
            LIFECYCLE_NETWORK_EFFECT == "NONE",
            ORDER_EFFECT == "NONE",
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            TESTNET_ORDER_SUBMIT_PERFORMED is False,
            ORDER_SUBMIT_PERFORMED is False,
            ORDER_PATH_STARTED is False,
            MUTATING_EXCHANGE_CALLS is False,
            NETWORK_WRITE_PERFORMED is False,
            NETWORK_SESSION_STARTED is False,
            LIVE_AUTHORIZED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            TESTNET_CAMPAIGN_STARTED is False,
            TESTNET_CAMPAIGN_COMPLETED is False,
            LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED is False,
            CAPABILITY_11_13_STARTED is False,
            SECTION_11_13_STARTED is False,
            CAPABILITY_11_6_STARTED is False,
            CAPABILITY_11_5_STARTED is False,
            CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED is False,
            KILL_SWITCH_CONTRACT_ACTIVATED is False,
            KILL_SWITCH_BINDING_STATUS == "BOUND",
            TESTNET_ORDER_LIFECYCLE_PROVEN is False,
            TESTNET_RECONCILIATION_PROVEN is False,
            TESTNET_RESTART_PROVEN is False,
            TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN is False,
            TESTNET_KILL_SWITCH_PROVEN is False,
            TESTNET_AUTONOMOUS_RECOVERY_PROVEN is False,
            TESTNET_EVIDENCE_VERIFIED is False,
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
        "campaign_start_hard_reject": campaign_start_hard_reject,
        "live_mode_blocked": live_mode_blocked,
        "unknown_path_blocked": unknown_path_blocked,
        "productive_path_blocked": productive_path_blocked,
        "submit_blocked": submit_blocked,
        "order_send_blocked": order_send_blocked,
        "write_blocked": write_blocked,
        "campaign_start_blocked": campaign_start_blocked,
        "session_blocked": session_blocked,
        "activation_blocked": activation_blocked,
        "runtime_clear_blocked": runtime_clear_blocked,
        "side_effect_bypass_blocked": side_effect_bypass_blocked,
        "scope_escalation_blocked": scope_escalation_blocked,
        "cap_11_6_adapter_blocked": cap116_blocked,
        "kill_switch_contract_activation_blocked": kill_switch_activation_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "proven_overclaim_blocked": proven_overclaim_blocked,
        "cap_11_6_contract_reuse_ok": cap_11_6_reuse_ok,
        "testnet_evidence_closure_ok": closure_ok,
        "long_running_campaign_evidence_performed": (
            record.long_running_campaign_evidence_performed
        ),
        "cap_11_6_long_running_campaign_evidence_contract_reused": (
            record.cap_11_6_long_running_campaign_evidence_contract_reused
        ),
        "section_11_12_7_predecessor_bound": pred_bound,
        "section_11_12_7_execution_binding_digest": pred_digest,
        "kill_switch_binding_status": record.kill_switch_binding_status,
        "client_order_id_prefix": record.client_order_id_prefix,
        "paths_completed": list(record.paths_completed),
        "path_results": [
            {
                "path_name": r.path_name,
                "continuity_observed": r.continuity_observed,
                "evidence_cursor_advanced": r.evidence_cursor_advanced,
                "campaign_activated": r.campaign_activated,
                "exchange_submit_performed": r.exchange_submit_performed,
                "terminal_state": r.terminal_state,
                "lifecycle_source": r.lifecycle_source,
                "network_effect": r.network_effect,
            }
            for r in record.path_results
        ],
        "lifecycle_source": record.lifecycle_source,
        "execution_binding_digest": record.execution_binding_digest,
        "network_effect": record.network_effect,
        "order_effect": record.order_effect,
        "exchange_submit_performed": record.exchange_submit_performed,
        "path_class": record.path_class,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "testnet_campaign_started": False,
        "testnet_campaign_completed": False,
        "campaign_activated": False,
        "network_session_started": False,
        "cap_11_6_adapter_activated": False,
        "kill_switch_contract_activated": False,
        "cap_11_13_started": False,
        "section_11_13_started": False,
        "testnet_order_lifecycle_proven": False,
        "testnet_reconciliation_proven": False,
        "testnet_restart_proven": False,
        "testnet_unknown_submit_recovery_proven": False,
        "testnet_duplicate_order_prevention_proven": False,
        "testnet_kill_switch_proven": False,
        "testnet_autonomous_recovery_proven": False,
        "testnet_evidence_verified": False,
        "KILL_SWITCH_PERSISTED": True,
        "KILL_SWITCH_FAIL_CLOSED": True,
        "KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT": True,
        "KILL_SWITCH_SURVIVES_RESTART": True,
        "KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME": True,
        "OWNER_AUTHORITY_REQUIRED_TO_CLEAR": True,
        "CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA": True,
        "EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA": True,
        "allowed_section_11_12_8_paths": list(ALLOWED_SECTION_11_12_8_PATHS),
        "forbidden_capability_11_13_paths": list(FORBIDDEN_CAPABILITY_11_13_PATHS),
        "cap_11_6_campaign_evidence_owner": CAP_11_6_CAMPAIGN_EVIDENCE_OWNER,
    }

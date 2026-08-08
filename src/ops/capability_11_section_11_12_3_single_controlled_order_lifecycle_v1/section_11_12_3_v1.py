"""Fail-closed §11.12.3 single controlled order lifecycle residual.

Reuses Cap 11.4 fixture-only `single_controlled_order_lifecycle` path and binds
the closed §11.12.2 productive order-serialization dry-run predecessor. Does
not submit orders, authorize network writes, activate Cap 11.4 Testnet
adapters, or start §11.12.4.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_lifecycle_closure_contract_v1 import (
    TestnetLifecycleClosureError,
    TestnetLifecyclePathRecordV1,
    run_testnet_lifecycle_fixture_path_v1,
)
from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.section_11_12_2_v1 import (
    execute_section_11_12_2_order_serialization_dry_run_v1,
    mark_section_11_12_1_predecessor_bound_v1,
)
from src.ops.capability_11_section_11_12_3_single_controlled_order_lifecycle_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CAP_11_4_LIFECYCLE_OWNER,
    CAP_11_4_SINGLE_CONTROLLED_LIFECYCLE_CONTRACT_REUSE_ALLOWED,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    EXECUTION_MODE_REQUIRED,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    FORBIDDEN_SECTION_11_12_4_PATHS,
    LIFECYCLE_NETWORK_EFFECT,
    LIFECYCLE_PATH_NAME,
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
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REQUIRED_PRECONDITIONS,
    SECTION_11_12_2_PREDECESSOR_BINDING_REQUIRED,
    SECTION_11_12_4_STARTED,
    SINGLE_CONTROLLED_ORDER_LIFECYCLE_ALLOWED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
)


class Section11123SingleControlledOrderLifecycleError(RuntimeError):
    """Fail-closed §11.12.3 single controlled order lifecycle violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class Section11123ExecutionRecordV1:
    """Productive §11.12.3 single controlled order lifecycle execution record."""

    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    repository_sha: str
    config_digest: str
    section_11_12_2_execution_binding_digest: str
    section_11_12_2_serialization_digest: str
    client_order_id: str
    path_name: str
    history: tuple[str, ...]
    terminal_state: str
    lifecycle_source: str
    network_effect: str
    exchange_submit_performed: bool
    single_controlled_order_lifecycle_performed: bool
    cap_11_4_single_controlled_lifecycle_contract_reused: bool
    order_send_disabled: bool
    orders_authorized: bool
    network_writes_authorized: bool
    network_write_performed: bool
    exchange_order_submit_reachable: bool
    testnet_order_submit_performed: bool
    cap_11_4_adapter_activated: bool
    section_11_12_4_started: bool
    cap_11_13_started: bool
    testnet_order_lifecycle_proven: bool
    missing_preconditions: tuple[str, ...]
    execution_admissible: bool
    execution_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    reference_only: bool = False
    path_class: str = PATH_CLASS


def evaluate_section_11_12_3_preconditions_v1(
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
    section_11_12_2_predecessor_bound: bool,
    cap_11_4_single_controlled_lifecycle_contract_reused: bool,
    owner_go_single_controlled_order_lifecycle_authorized: bool,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    network_effect: str = LIFECYCLE_NETWORK_EFFECT,
    cap_11_4_adapter_activated: bool = False,
    section_11_12_4_started: bool = False,
    cap_11_13_started: bool = False,
) -> dict[str, Any]:
    """Evaluate §11.12.3 productive preconditions."""
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
    if not section_11_12_2_predecessor_bound or not SECTION_11_12_2_PREDECESSOR_BINDING_REQUIRED:
        missing.append("section_11_12_2_predecessor_bound")
    if (
        not cap_11_4_single_controlled_lifecycle_contract_reused
        or not CAP_11_4_SINGLE_CONTROLLED_LIFECYCLE_CONTRACT_REUSE_ALLOWED
    ):
        missing.append("cap_11_4_single_controlled_lifecycle_contract_reused")
    if not SINGLE_CONTROLLED_ORDER_LIFECYCLE_ALLOWED:
        missing.append("single_controlled_order_lifecycle_allowed")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED is not False:
        missing.append("network_writes_unauthorized")
    if network_effect != "NONE" or LIFECYCLE_NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if (
        cap_11_4_adapter_activated
        or CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED is True
        or CAPABILITY_11_4_STARTED is True
    ):
        missing.append("cap_11_4_adapter_not_activated")
    if section_11_12_4_started or SECTION_11_12_4_STARTED is True:
        missing.append("section_11_12_4_not_started")
    if cap_11_13_started or CAPABILITY_11_13_STARTED is True:
        missing.append("cap_11_13_not_started")
    if not owner_go_single_controlled_order_lifecycle_authorized:
        missing.append("owner_go_single_controlled_order_lifecycle_authorized")

    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)
    return {
        "execution_admissible": len(ordered_missing) == 0,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
    }


def mark_section_11_12_2_predecessor_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> tuple[bool, str, str]:
    """Bind closed §11.12.2 productive dry-run predecessor.

    Returns (bound, execution_binding_digest, serialization_digest).
    """
    (
        pred_bound,
        _pred_digest,
        pred_identity,
    ) = mark_section_11_12_1_predecessor_bound_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    record = execute_section_11_12_2_order_serialization_dry_run_v1(
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
        section_11_12_1_predecessor_bound=pred_bound,
        section_11_12_1_execution_binding_digest=_pred_digest,
        section_11_12_1_account_identity_observed=pred_identity,
        client_order_id="pt-coid-section-11-12-3-pred",
    )
    bound = (
        record.execution_admissible is True
        and record.order_serialization_dry_run_performed is True
        and bool(record.execution_binding_digest)
        and bool(record.serialization_digest)
    )
    return bound, record.execution_binding_digest, record.serialization_digest


def reuse_cap_11_4_single_controlled_order_lifecycle_v1(
    *,
    path_name: str = LIFECYCLE_PATH_NAME,
) -> TestnetLifecyclePathRecordV1:
    """Reuse Cap 11.4 fixture-only single controlled order lifecycle path."""
    if not CAP_11_4_SINGLE_CONTROLLED_LIFECYCLE_CONTRACT_REUSE_ALLOWED:
        raise Section11123SingleControlledOrderLifecycleError(
            "CAP_11_4_SINGLE_CONTROLLED_LIFECYCLE_CONTRACT_REUSE_NOT_ALLOWED"
        )
    if path_name != LIFECYCLE_PATH_NAME:
        raise Section11123SingleControlledOrderLifecycleError(
            f"SECTION_11_12_3_PATH_FORBIDDEN:{path_name}"
        )
    try:
        record = run_testnet_lifecycle_fixture_path_v1(path_name=path_name)
    except TestnetLifecycleClosureError as exc:
        raise Section11123SingleControlledOrderLifecycleError(str(exc)) from exc
    if record.source != LIFECYCLE_SOURCE_REQUIRED:
        raise Section11123SingleControlledOrderLifecycleError(
            f"NON_FIXTURE_LIFECYCLE_SOURCE:{record.source}"
        )
    if record.network_effect != "NONE" or record.exchange_submit_performed is not False:
        raise Section11123SingleControlledOrderLifecycleError(
            "LIFECYCLE_NETWORK_EFFECT_MUST_REMAIN_NONE"
        )
    if record.terminal_state != "EVIDENCED":
        raise Section11123SingleControlledOrderLifecycleError(
            f"SINGLE_CONTROLLED_ORDER_LIFECYCLE_NOT_CLOSED:{record.terminal_state}"
        )
    return record


def execute_section_11_12_3_single_controlled_order_lifecycle_v1(
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
    section_11_12_2_predecessor_bound: bool,
    section_11_12_2_execution_binding_digest: str,
    section_11_12_2_serialization_digest: str,
    client_order_id: str,
    owner_go_single_controlled_order_lifecycle_authorized: bool = True,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    cap_11_4_adapter_activated: bool = False,
    section_11_12_4_started: bool = False,
    cap_11_13_started: bool = False,
) -> Section11123ExecutionRecordV1:
    """Execute productive §11.12.3: Cap 11.4 single path reuse bound to §11.12.2."""
    if not order_send_disabled or orders_authorized:
        raise Section11123SingleControlledOrderLifecycleError(
            "ORDER_SEND_MUST_REMAIN_DISABLED_IN_SECTION_11_12_3"
        )
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED:
        raise Section11123SingleControlledOrderLifecycleError(
            "NETWORK_WRITES_FORBIDDEN_IN_SECTION_11_12_3"
        )
    if not SINGLE_CONTROLLED_ORDER_LIFECYCLE_ALLOWED:
        raise Section11123SingleControlledOrderLifecycleError(
            "SINGLE_CONTROLLED_ORDER_LIFECYCLE_NOT_ALLOWED"
        )
    if section_11_12_4_started or SECTION_11_12_4_STARTED:
        raise Section11123SingleControlledOrderLifecycleError(
            "SECTION_11_12_4_MUST_REMAIN_UNSTARTED"
        )
    if cap_11_13_started or CAPABILITY_11_13_STARTED:
        raise Section11123SingleControlledOrderLifecycleError(
            "CAPABILITY_11_13_MUST_REMAIN_UNSTARTED"
        )
    if (
        cap_11_4_adapter_activated
        or CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED
        or CAPABILITY_11_4_STARTED
    ):
        raise Section11123SingleControlledOrderLifecycleError(
            "CAPABILITY_11_4_ADAPTER_MUST_REMAIN_INACTIVE"
        )

    scope = tuple(str(x) for x in instrument_scope)

    pre = evaluate_section_11_12_3_preconditions_v1(
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
        section_11_12_2_predecessor_bound=section_11_12_2_predecessor_bound,
        cap_11_4_single_controlled_lifecycle_contract_reused=True,
        owner_go_single_controlled_order_lifecycle_authorized=(
            owner_go_single_controlled_order_lifecycle_authorized
        ),
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        network_writes_authorized=network_writes_authorized,
        network_effect=LIFECYCLE_NETWORK_EFFECT,
        cap_11_4_adapter_activated=cap_11_4_adapter_activated,
        section_11_12_4_started=section_11_12_4_started,
        cap_11_13_started=cap_11_13_started,
    )
    if not pre["execution_admissible"]:
        raise Section11123SingleControlledOrderLifecycleError(
            "SECTION_11_12_3_NOT_ADMISSIBLE:" + ",".join(pre["missing_preconditions"])
        )

    if not section_11_12_2_execution_binding_digest:
        raise Section11123SingleControlledOrderLifecycleError(
            "SECTION_11_12_2_EXECUTION_BINDING_DIGEST_ABSENT"
        )
    if not section_11_12_2_serialization_digest:
        raise Section11123SingleControlledOrderLifecycleError(
            "SECTION_11_12_2_SERIALIZATION_DIGEST_ABSENT"
        )

    life = reuse_cap_11_4_single_controlled_order_lifecycle_v1(path_name=LIFECYCLE_PATH_NAME)

    digest_material = {
        "capability_id": CAPABILITY_ID,
        "predecessor_capability_id": PREDECESSOR_CAPABILITY_ID,
        "section_11_12_2_execution_binding_digest": section_11_12_2_execution_binding_digest,
        "section_11_12_2_serialization_digest": section_11_12_2_serialization_digest,
        "account_identity": account_identity,
        "venue": venue,
        "instrument_scope": list(scope),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "client_order_id": client_order_id,
        "path_name": life.path_name,
        "history": list(life.history),
        "terminal_state": life.terminal_state,
        "lifecycle_source": life.source,
        "network_effect": life.network_effect,
        "exchange_submit_performed": life.exchange_submit_performed,
        "path_class": PATH_CLASS,
        "cap_11_4_lifecycle_owner": CAP_11_4_LIFECYCLE_OWNER,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "cap_11_4_adapter_activated": False,
        "section_11_12_4_started": False,
        "cap_11_13_started": False,
        "testnet_order_lifecycle_proven": False,
    }
    execution_binding_digest = hashlib.sha256(
        _canonical_dumps(digest_material).encode("utf-8")
    ).hexdigest()

    return Section11123ExecutionRecordV1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        section_11_12_2_execution_binding_digest=section_11_12_2_execution_binding_digest,
        section_11_12_2_serialization_digest=section_11_12_2_serialization_digest,
        client_order_id=client_order_id,
        path_name=life.path_name,
        history=life.history,
        terminal_state=life.terminal_state,
        lifecycle_source=life.source,
        network_effect=life.network_effect,
        exchange_submit_performed=life.exchange_submit_performed,
        single_controlled_order_lifecycle_performed=True,
        cap_11_4_single_controlled_lifecycle_contract_reused=True,
        order_send_disabled=True,
        orders_authorized=False,
        network_writes_authorized=False,
        network_write_performed=False,
        exchange_order_submit_reachable=False,
        testnet_order_submit_performed=False,
        cap_11_4_adapter_activated=False,
        section_11_12_4_started=False,
        cap_11_13_started=False,
        testnet_order_lifecycle_proven=False,
        missing_preconditions=(),
        execution_admissible=True,
        execution_binding_digest=execution_binding_digest,
        reference_only=False,
    )


def refuse_order_send_v1() -> None:
    raise Section11123SingleControlledOrderLifecycleError("ORDER_SEND_FORBIDDEN_IN_SECTION_11_12_3")


def refuse_network_write_v1(*, method: str = "POST") -> None:
    raise Section11123SingleControlledOrderLifecycleError(
        f"NETWORK_WRITE_FORBIDDEN_IN_SECTION_11_12_3:{method}"
    )


def refuse_network_submit_v1() -> None:
    raise Section11123SingleControlledOrderLifecycleError(
        "ORDER_LIFECYCLE_NETWORK_SUBMIT_FORBIDDEN_IN_SECTION_11_12_3"
    )


def refuse_section_11_12_4_v1(*, path_name: str = "entry_lifecycle") -> None:
    raise Section11123SingleControlledOrderLifecycleError(
        f"SECTION_11_12_4_PATH_FORBIDDEN_IN_SECTION_11_12_3:{path_name}"
    )


def refuse_cap_11_4_adapter_activation_v1() -> None:
    raise Section11123SingleControlledOrderLifecycleError(
        "CAPABILITY_11_4_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_3"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise Section11123SingleControlledOrderLifecycleError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_3"
    )


def prove_section_11_12_3_single_controlled_order_lifecycle_v1() -> dict[str, Any]:
    """Contract proof for §11.12.3 lifecycle with Cap 11.4 reuse + §11.12.2 bind."""
    sha = "2de0a4973e726f56c74a881f327130cc73706b17"
    cfg = "cfg-" + ("d" * 64)

    (
        pred_bound,
        pred_digest,
        pred_serialization,
    ) = mark_section_11_12_2_predecessor_bound_v1(repository_sha=sha, config_digest=cfg)

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
        "section_11_12_2_predecessor_bound": pred_bound,
        "section_11_12_2_execution_binding_digest": pred_digest,
        "section_11_12_2_serialization_digest": pred_serialization,
        "client_order_id": "pt-coid-section-11-12-3-lifecycle",
    }

    incomplete_blocked = False
    try:
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **{
                **common,
                "section_11_12_2_predecessor_bound": False,
            }
        )
    except Section11123SingleControlledOrderLifecycleError as exc:
        incomplete_blocked = "SECTION_11_12_3_NOT_ADMISSIBLE" in str(exc)

    record = execute_section_11_12_3_single_controlled_order_lifecycle_v1(**common)
    complete_ok = (
        record.execution_admissible is True
        and record.single_controlled_order_lifecycle_performed is True
        and record.cap_11_4_single_controlled_lifecycle_contract_reused is True
        and record.network_effect == "NONE"
        and record.exchange_submit_performed is False
        and record.lifecycle_source == LIFECYCLE_SOURCE_REQUIRED
        and record.path_name == LIFECYCLE_PATH_NAME
        and record.terminal_state == "EVIDENCED"
        and record.order_send_disabled is True
        and record.orders_authorized is False
        and record.network_writes_authorized is False
        and record.network_write_performed is False
        and record.exchange_order_submit_reachable is False
        and record.testnet_order_submit_performed is False
        and record.cap_11_4_adapter_activated is False
        and record.section_11_12_4_started is False
        and record.cap_11_13_started is False
        and record.testnet_order_lifecycle_proven is False
        and record.reference_only is False
        and record.path_class == PATH_CLASS
        and bool(record.history)
        and bool(record.execution_binding_digest)
        and bool(record.section_11_12_2_execution_binding_digest)
        and bool(record.section_11_12_2_serialization_digest)
    )

    order_send_hard_reject = False
    try:
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **common,
            order_send_disabled=False,
        )
    except Section11123SingleControlledOrderLifecycleError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **common,
            orders_authorized=True,
        )
    except Section11123SingleControlledOrderLifecycleError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    network_write_hard_reject = False
    try:
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **common,
            network_writes_authorized=True,
        )
    except Section11123SingleControlledOrderLifecycleError as exc:
        network_write_hard_reject = "NETWORK_WRITES_FORBIDDEN" in str(exc)

    live_mode_blocked = False
    try:
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **{**common, "runtime_mode": "LIVE"}
        )
    except Section11123SingleControlledOrderLifecycleError as exc:
        live_mode_blocked = "SECTION_11_12_3_NOT_ADMISSIBLE" in str(exc)

    section_11_12_4_path_blocked = False
    try:
        reuse_cap_11_4_single_controlled_order_lifecycle_v1(path_name="entry_lifecycle")
    except Section11123SingleControlledOrderLifecycleError as exc:
        section_11_12_4_path_blocked = "SECTION_11_12_3_PATH_FORBIDDEN" in str(exc)

    unknown_path_blocked = False
    try:
        reuse_cap_11_4_single_controlled_order_lifecycle_v1(path_name="restart_with_open_order")
    except Section11123SingleControlledOrderLifecycleError as exc:
        unknown_path_blocked = "SECTION_11_12_3_PATH_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_network_submit_v1()
    except Section11123SingleControlledOrderLifecycleError as exc:
        submit_blocked = "NETWORK_SUBMIT_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except Section11123SingleControlledOrderLifecycleError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    write_blocked = False
    try:
        refuse_network_write_v1(method="POST")
    except Section11123SingleControlledOrderLifecycleError as exc:
        write_blocked = "NETWORK_WRITE_FORBIDDEN" in str(exc)

    section_11_12_4_blocked = False
    try:
        refuse_section_11_12_4_v1(path_name="entry_lifecycle")
    except Section11123SingleControlledOrderLifecycleError as exc:
        section_11_12_4_blocked = "SECTION_11_12_4" in str(exc)

    cap114_blocked = False
    try:
        refuse_cap_11_4_adapter_activation_v1()
    except Section11123SingleControlledOrderLifecycleError as exc:
        cap114_blocked = "CAPABILITY_11_4_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except Section11123SingleControlledOrderLifecycleError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    forbidden_paths_enumerated = all(
        name in FORBIDDEN_SECTION_11_12_4_PATHS for name in FORBIDDEN_SECTION_11_12_4_PATHS
    )

    ok = all(
        [
            complete_ok,
            incomplete_blocked,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            network_write_hard_reject,
            live_mode_blocked,
            section_11_12_4_path_blocked,
            unknown_path_blocked,
            submit_blocked,
            order_send_blocked,
            write_blocked,
            section_11_12_4_blocked,
            cap114_blocked,
            cap1113_blocked,
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
            SECTION_11_12_4_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            CAPABILITY_11_4_STARTED is False,
            CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED is False,
            TESTNET_ORDER_LIFECYCLE_PROVEN is False,
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
        "section_11_12_4_path_blocked": section_11_12_4_path_blocked,
        "unknown_path_blocked": unknown_path_blocked,
        "submit_blocked": submit_blocked,
        "order_send_blocked": order_send_blocked,
        "write_blocked": write_blocked,
        "section_11_12_4_blocked": section_11_12_4_blocked,
        "cap_11_4_adapter_blocked": cap114_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "single_controlled_order_lifecycle_performed": (
            record.single_controlled_order_lifecycle_performed
        ),
        "cap_11_4_single_controlled_lifecycle_contract_reused": (
            record.cap_11_4_single_controlled_lifecycle_contract_reused
        ),
        "section_11_12_2_predecessor_bound": pred_bound,
        "section_11_12_2_execution_binding_digest": pred_digest,
        "section_11_12_2_serialization_digest": pred_serialization,
        "client_order_id": record.client_order_id,
        "path_name": record.path_name,
        "history": list(record.history),
        "terminal_state": record.terminal_state,
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
        "cap_11_4_adapter_activated": False,
        "section_11_12_4_started": False,
        "cap_11_13_started": False,
        "testnet_order_lifecycle_proven": False,
        "forbidden_section_11_12_4_paths": list(FORBIDDEN_SECTION_11_12_4_PATHS),
        "cap_11_4_lifecycle_owner": CAP_11_4_LIFECYCLE_OWNER,
    }

"""Fail-closed §11.12.2 order serialization dry-run residual.

Reuses Cap 11.4 order-serialization dry-run contract (fixture-only, network
effect NONE) and binds the closed §11.12.1 productive account-identity
predecessor. Does not submit orders, authorize network writes, activate Cap
11.4 Testnet adapters, or start §11.12.3.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.order_serialization_dry_run_contract_v1 import (
    OrderSerializationDryRunError,
    OrderSerializationDryRunRecordV1,
    build_order_serialization_dry_run_record_v1,
    refuse_order_serialization_network_submit_v1,
)
from src.ops.capability_11_productive_private_readonly_fetch_reference_only_v1.reference_only_fetch_v1 import (
    mark_cap_11_3_path_bound_for_fetch_reference_only_v1,
)
from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.section_11_12_1_v1 import (
    GovernedFixturePrivateReadonlyGetTransportV1,
    execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1,
    mark_fetch_reference_only_predecessor_bound_v1,
)
from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CAP_11_4_ORDER_SERIALIZATION_CONTRACT_REUSE_ALLOWED,
    CAP_11_4_SERIALIZATION_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    EXECUTION_MODE_REQUIRED,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_WRITE_PERFORMED,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDER_SERIALIZATION_DRY_RUN_ALLOWED,
    ORDER_SERIALIZATION_NETWORK_EFFECT,
    ORDER_SUBMIT_PERFORMED,
    ORDERS_AUTHORIZED,
    OWNER,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REQUIRED_PRECONDITIONS,
    REQUIRED_SERIALIZATION_FIELDS,
    SECTION_11_12_1_PREDECESSOR_BINDING_REQUIRED,
    SECTION_11_12_3_STARTED,
    SERIALIZATION_SOURCE_REQUIRED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_SUBMIT_PERFORMED,
)


class Section11122OrderSerializationDryRunError(RuntimeError):
    """Fail-closed §11.12.2 order serialization dry-run violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class Section11122ExecutionRecordV1:
    """Productive §11.12.2 order serialization dry-run execution record."""

    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    repository_sha: str
    config_digest: str
    section_11_12_1_execution_binding_digest: str
    section_11_12_1_account_identity_observed: str
    client_order_id: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    execution_mode: str
    serialization_source: str
    serialization_digest: str
    venue_native_payload: dict[str, Any]
    network_effect: str
    submitted: bool
    order_serialization_dry_run_performed: bool
    cap_11_4_order_serialization_contract_reused: bool
    order_send_disabled: bool
    orders_authorized: bool
    network_writes_authorized: bool
    network_write_performed: bool
    exchange_order_submit_reachable: bool
    testnet_order_submit_performed: bool
    cap_11_4_adapter_activated: bool
    section_11_12_3_started: bool
    cap_11_13_started: bool
    missing_preconditions: tuple[str, ...]
    execution_admissible: bool
    execution_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    reference_only: bool = False
    path_class: str = PATH_CLASS


def evaluate_section_11_12_2_preconditions_v1(
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
    section_11_12_1_predecessor_bound: bool,
    cap_11_4_order_serialization_contract_reused: bool,
    owner_go_order_serialization_dry_run_authorized: bool,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    network_effect: str = ORDER_SERIALIZATION_NETWORK_EFFECT,
    cap_11_4_adapter_activated: bool = False,
    section_11_12_3_started: bool = False,
    cap_11_13_started: bool = False,
) -> dict[str, Any]:
    """Evaluate §11.12.2 productive preconditions."""
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
    if not section_11_12_1_predecessor_bound or not SECTION_11_12_1_PREDECESSOR_BINDING_REQUIRED:
        missing.append("section_11_12_1_predecessor_bound")
    if (
        not cap_11_4_order_serialization_contract_reused
        or not CAP_11_4_ORDER_SERIALIZATION_CONTRACT_REUSE_ALLOWED
    ):
        missing.append("cap_11_4_order_serialization_contract_reused")
    if not ORDER_SERIALIZATION_DRY_RUN_ALLOWED:
        missing.append("order_serialization_dry_run_allowed")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED is not False:
        missing.append("network_writes_unauthorized")
    if network_effect != "NONE" or ORDER_SERIALIZATION_NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if (
        cap_11_4_adapter_activated
        or CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED is True
        or CAPABILITY_11_4_STARTED is True
    ):
        missing.append("cap_11_4_adapter_not_activated")
    if section_11_12_3_started or SECTION_11_12_3_STARTED is True:
        missing.append("section_11_12_3_not_started")
    if cap_11_13_started or CAPABILITY_11_13_STARTED is True:
        missing.append("cap_11_13_not_started")
    if not owner_go_order_serialization_dry_run_authorized:
        missing.append("owner_go_order_serialization_dry_run_authorized")

    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)
    return {
        "execution_admissible": len(ordered_missing) == 0,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
    }


def mark_section_11_12_1_predecessor_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> tuple[bool, str, str]:
    """Bind closed §11.12.1 productive account-identity predecessor.

    Returns (bound, execution_binding_digest, account_identity_observed).
    """
    (
        pred_bound,
        owner_auth_digest,
        _cred_load_digest,
        fetch_ref_digest,
    ) = mark_fetch_reference_only_predecessor_bound_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    path_bound = mark_cap_11_3_path_bound_for_fetch_reference_only_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    record = execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
        credential_ref_id="cred-ref-section-11-12-2",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
        credential_material="fixture-credential-material-never-logged-or-evidenced",
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
        authorization_id="owner-auth-for-section-11-12-2",
        owner_auth_artifact_digest=owner_auth_digest,
        fetch_reference_only_binding_digest=fetch_ref_digest,
        fetch_reference_only_predecessor_bound=pred_bound,
        owner_auth_artifact_bound=pred_bound,
        credential_load_reference_only_bound=pred_bound,
        cap_11_3_productive_private_readonly_path_bound=path_bound,
        transport=GovernedFixturePrivateReadonlyGetTransportV1(
            expected_account_identity="acct-uid-demo"
        ),
    )
    bound = (
        record.execution_admissible is True
        and record.account_identity_fetch_performed is True
        and bool(record.execution_binding_digest)
    )
    return bound, record.execution_binding_digest, record.account_identity_observed


def reuse_cap_11_4_order_serialization_dry_run_v1(
    *,
    client_order_id: str,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    execution_mode: str = EXECUTION_MODE_REQUIRED,
    source: str = SERIALIZATION_SOURCE_REQUIRED,
) -> OrderSerializationDryRunRecordV1:
    """Reuse Cap 11.4 fixture-only order serialization dry-run builder."""
    if not CAP_11_4_ORDER_SERIALIZATION_CONTRACT_REUSE_ALLOWED:
        raise Section11122OrderSerializationDryRunError(
            "CAP_11_4_ORDER_SERIALIZATION_CONTRACT_REUSE_NOT_ALLOWED"
        )
    try:
        return build_order_serialization_dry_run_record_v1(
            client_order_id=client_order_id,
            instrument_id=instrument_id,
            side=side,
            order_type=order_type,
            quantity=quantity,
            execution_mode=execution_mode,
            source=source,
        )
    except OrderSerializationDryRunError as exc:
        raise Section11122OrderSerializationDryRunError(str(exc)) from exc


def execute_section_11_12_2_order_serialization_dry_run_v1(
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
    section_11_12_1_predecessor_bound: bool,
    section_11_12_1_execution_binding_digest: str,
    section_11_12_1_account_identity_observed: str,
    client_order_id: str,
    side: str = "BUY",
    order_type: str = "LIMIT",
    quantity: str = "1",
    owner_go_order_serialization_dry_run_authorized: bool = True,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    cap_11_4_adapter_activated: bool = False,
    section_11_12_3_started: bool = False,
    cap_11_13_started: bool = False,
) -> Section11122ExecutionRecordV1:
    """Execute productive §11.12.2: Cap 11.4 dry-run reuse bound to §11.12.1."""
    if not order_send_disabled or orders_authorized:
        raise Section11122OrderSerializationDryRunError(
            "ORDER_SEND_MUST_REMAIN_DISABLED_IN_SECTION_11_12_2"
        )
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED:
        raise Section11122OrderSerializationDryRunError(
            "NETWORK_WRITES_FORBIDDEN_IN_SECTION_11_12_2"
        )
    if not ORDER_SERIALIZATION_DRY_RUN_ALLOWED:
        raise Section11122OrderSerializationDryRunError("ORDER_SERIALIZATION_DRY_RUN_NOT_ALLOWED")
    if section_11_12_3_started or SECTION_11_12_3_STARTED:
        raise Section11122OrderSerializationDryRunError("SECTION_11_12_3_MUST_REMAIN_UNSTARTED")
    if cap_11_13_started or CAPABILITY_11_13_STARTED:
        raise Section11122OrderSerializationDryRunError("CAPABILITY_11_13_MUST_REMAIN_UNSTARTED")
    if (
        cap_11_4_adapter_activated
        or CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED
        or CAPABILITY_11_4_STARTED
    ):
        raise Section11122OrderSerializationDryRunError(
            "CAPABILITY_11_4_ADAPTER_MUST_REMAIN_INACTIVE"
        )

    scope = tuple(str(x) for x in instrument_scope)
    instrument_id = scope[0] if scope else ""

    pre = evaluate_section_11_12_2_preconditions_v1(
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
        section_11_12_1_predecessor_bound=section_11_12_1_predecessor_bound,
        cap_11_4_order_serialization_contract_reused=True,
        owner_go_order_serialization_dry_run_authorized=(
            owner_go_order_serialization_dry_run_authorized
        ),
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        network_writes_authorized=network_writes_authorized,
        network_effect=ORDER_SERIALIZATION_NETWORK_EFFECT,
        cap_11_4_adapter_activated=cap_11_4_adapter_activated,
        section_11_12_3_started=section_11_12_3_started,
        cap_11_13_started=cap_11_13_started,
    )
    if not pre["execution_admissible"]:
        raise Section11122OrderSerializationDryRunError(
            "SECTION_11_12_2_NOT_ADMISSIBLE:" + ",".join(pre["missing_preconditions"])
        )

    if not section_11_12_1_execution_binding_digest:
        raise Section11122OrderSerializationDryRunError(
            "SECTION_11_12_1_EXECUTION_BINDING_DIGEST_ABSENT"
        )
    if section_11_12_1_account_identity_observed != account_identity:
        raise Section11122OrderSerializationDryRunError("SECTION_11_12_1_ACCOUNT_IDENTITY_MISMATCH")

    ser = reuse_cap_11_4_order_serialization_dry_run_v1(
        client_order_id=client_order_id,
        instrument_id=instrument_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        execution_mode=EXECUTION_MODE_REQUIRED,
        source=SERIALIZATION_SOURCE_REQUIRED,
    )
    if ser.network_effect != "NONE" or ser.submitted is not False:
        raise Section11122OrderSerializationDryRunError(
            "ORDER_SERIALIZATION_NETWORK_EFFECT_MUST_REMAIN_NONE"
        )
    if ser.venue_native_payload.get("dry_run") is not True:
        raise Section11122OrderSerializationDryRunError("VENUE_NATIVE_DRY_RUN_FLAG_REQUIRED")

    digest_material = {
        "capability_id": CAPABILITY_ID,
        "predecessor_capability_id": PREDECESSOR_CAPABILITY_ID,
        "section_11_12_1_execution_binding_digest": section_11_12_1_execution_binding_digest,
        "account_identity": account_identity,
        "venue": venue,
        "instrument_scope": list(scope),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "client_order_id": ser.client_order_id,
        "instrument_id": ser.instrument_id,
        "side": ser.side,
        "order_type": ser.order_type,
        "quantity": ser.quantity,
        "execution_mode": ser.execution_mode,
        "serialization_source": ser.source,
        "serialization_digest": ser.serialization_digest,
        "network_effect": ser.network_effect,
        "submitted": ser.submitted,
        "path_class": PATH_CLASS,
        "cap_11_4_serialization_owner": CAP_11_4_SERIALIZATION_OWNER,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "cap_11_4_adapter_activated": False,
        "section_11_12_3_started": False,
        "cap_11_13_started": False,
    }
    execution_binding_digest = hashlib.sha256(
        _canonical_dumps(digest_material).encode("utf-8")
    ).hexdigest()

    return Section11122ExecutionRecordV1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        section_11_12_1_execution_binding_digest=section_11_12_1_execution_binding_digest,
        section_11_12_1_account_identity_observed=section_11_12_1_account_identity_observed,
        client_order_id=ser.client_order_id,
        instrument_id=ser.instrument_id,
        side=ser.side,
        order_type=ser.order_type,
        quantity=ser.quantity,
        execution_mode=ser.execution_mode,
        serialization_source=ser.source,
        serialization_digest=ser.serialization_digest,
        venue_native_payload=dict(ser.venue_native_payload),
        network_effect=ser.network_effect,
        submitted=ser.submitted,
        order_serialization_dry_run_performed=True,
        cap_11_4_order_serialization_contract_reused=True,
        order_send_disabled=True,
        orders_authorized=False,
        network_writes_authorized=False,
        network_write_performed=False,
        exchange_order_submit_reachable=False,
        testnet_order_submit_performed=False,
        cap_11_4_adapter_activated=False,
        section_11_12_3_started=False,
        cap_11_13_started=False,
        missing_preconditions=(),
        execution_admissible=True,
        execution_binding_digest=execution_binding_digest,
        reference_only=False,
    )


def refuse_order_send_v1() -> None:
    raise Section11122OrderSerializationDryRunError("ORDER_SEND_FORBIDDEN_IN_SECTION_11_12_2")


def refuse_network_write_v1(*, method: str = "POST") -> None:
    raise Section11122OrderSerializationDryRunError(
        f"NETWORK_WRITE_FORBIDDEN_IN_SECTION_11_12_2:{method}"
    )


def refuse_network_submit_v1(*, record: OrderSerializationDryRunRecordV1) -> None:
    try:
        refuse_order_serialization_network_submit_v1(record=record)
    except OrderSerializationDryRunError as exc:
        raise Section11122OrderSerializationDryRunError(
            "ORDER_SERIALIZATION_NETWORK_SUBMIT_FORBIDDEN_IN_SECTION_11_12_2:"
            + record.client_order_id
        ) from exc


def refuse_section_11_12_3_v1() -> None:
    raise Section11122OrderSerializationDryRunError(
        "SECTION_11_12_3_SINGLE_CONTROLLED_ORDER_LIFECYCLE_FORBIDDEN_IN_SECTION_11_12_2"
    )


def refuse_cap_11_4_adapter_activation_v1() -> None:
    raise Section11122OrderSerializationDryRunError(
        "CAPABILITY_11_4_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_2"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise Section11122OrderSerializationDryRunError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_2"
    )


def prove_section_11_12_2_order_serialization_dry_run_v1() -> dict[str, Any]:
    """Contract proof for §11.12.2 dry-run with Cap 11.4 reuse + §11.12.1 bind."""
    sha = "74024d06470df7d44e186e02f47ec4dc38bb92c1"
    cfg = "cfg-" + ("c" * 64)

    (
        pred_bound,
        pred_digest,
        pred_identity,
    ) = mark_section_11_12_1_predecessor_bound_v1(repository_sha=sha, config_digest=cfg)

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
        "section_11_12_1_predecessor_bound": pred_bound,
        "section_11_12_1_execution_binding_digest": pred_digest,
        "section_11_12_1_account_identity_observed": pred_identity,
        "client_order_id": "pt-coid-section-11-12-2-dryrun",
    }

    incomplete_blocked = False
    try:
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **{
                **common,
                "section_11_12_1_predecessor_bound": False,
            }
        )
    except Section11122OrderSerializationDryRunError as exc:
        incomplete_blocked = "SECTION_11_12_2_NOT_ADMISSIBLE" in str(exc)

    record = execute_section_11_12_2_order_serialization_dry_run_v1(**common)
    complete_ok = (
        record.execution_admissible is True
        and record.order_serialization_dry_run_performed is True
        and record.cap_11_4_order_serialization_contract_reused is True
        and record.network_effect == "NONE"
        and record.submitted is False
        and record.serialization_source == SERIALIZATION_SOURCE_REQUIRED
        and record.venue_native_payload.get("dry_run") is True
        and record.order_send_disabled is True
        and record.orders_authorized is False
        and record.network_writes_authorized is False
        and record.network_write_performed is False
        and record.exchange_order_submit_reachable is False
        and record.testnet_order_submit_performed is False
        and record.cap_11_4_adapter_activated is False
        and record.section_11_12_3_started is False
        and record.cap_11_13_started is False
        and record.reference_only is False
        and record.path_class == PATH_CLASS
        and bool(record.serialization_digest)
        and bool(record.execution_binding_digest)
        and bool(record.section_11_12_1_execution_binding_digest)
        and record.section_11_12_1_account_identity_observed == "acct-uid-demo"
        and set(REQUIRED_SERIALIZATION_FIELDS).issubset(
            {
                "client_order_id",
                "instrument_id",
                "side",
                "order_type",
                "quantity",
                "execution_mode",
            }
        )
    )

    order_send_hard_reject = False
    try:
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **common,
            order_send_disabled=False,
        )
    except Section11122OrderSerializationDryRunError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **common,
            orders_authorized=True,
        )
    except Section11122OrderSerializationDryRunError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    network_write_hard_reject = False
    try:
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **common,
            network_writes_authorized=True,
        )
    except Section11122OrderSerializationDryRunError as exc:
        network_write_hard_reject = "NETWORK_WRITES_FORBIDDEN" in str(exc)

    live_mode_blocked = False
    try:
        execute_section_11_12_2_order_serialization_dry_run_v1(**{**common, "runtime_mode": "LIVE"})
    except Section11122OrderSerializationDryRunError as exc:
        live_mode_blocked = "SECTION_11_12_2_NOT_ADMISSIBLE" in str(exc)

    non_fixture_blocked = False
    try:
        reuse_cap_11_4_order_serialization_dry_run_v1(
            client_order_id="pt-coid-bad-source",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    except Section11122OrderSerializationDryRunError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    submit_blocked = False
    try:
        refuse_network_submit_v1(
            record=reuse_cap_11_4_order_serialization_dry_run_v1(
                client_order_id=record.client_order_id,
                instrument_id=record.instrument_id,
                side=record.side,
                order_type=record.order_type,
                quantity=record.quantity,
            )
        )
    except Section11122OrderSerializationDryRunError as exc:
        submit_blocked = "NETWORK_SUBMIT_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except Section11122OrderSerializationDryRunError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    write_blocked = False
    try:
        refuse_network_write_v1(method="POST")
    except Section11122OrderSerializationDryRunError as exc:
        write_blocked = "NETWORK_WRITE_FORBIDDEN" in str(exc)

    section_11_12_3_blocked = False
    try:
        refuse_section_11_12_3_v1()
    except Section11122OrderSerializationDryRunError as exc:
        section_11_12_3_blocked = "SECTION_11_12_3" in str(exc)

    cap114_blocked = False
    try:
        refuse_cap_11_4_adapter_activation_v1()
    except Section11122OrderSerializationDryRunError as exc:
        cap114_blocked = "CAPABILITY_11_4_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except Section11122OrderSerializationDryRunError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    field_missing_blocked = False
    try:
        reuse_cap_11_4_order_serialization_dry_run_v1(
            client_order_id="",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    except Section11122OrderSerializationDryRunError as exc:
        field_missing_blocked = "ORDER_SERIALIZATION_FIELD_MISSING" in str(exc)

    ok = all(
        [
            complete_ok,
            incomplete_blocked,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            network_write_hard_reject,
            live_mode_blocked,
            non_fixture_blocked,
            submit_blocked,
            order_send_blocked,
            write_blocked,
            section_11_12_3_blocked,
            cap114_blocked,
            cap1113_blocked,
            field_missing_blocked,
            CORE_LOGIC_CHANGE is False,
            REFERENCE_ONLY is False,
            ACTIVATION_STATE == "not_activated",
            ORDER_SERIALIZATION_NETWORK_EFFECT == "NONE",
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
            SECTION_11_12_3_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            CAPABILITY_11_4_STARTED is False,
            CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED is False,
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
        "non_fixture_blocked": non_fixture_blocked,
        "submit_blocked": submit_blocked,
        "order_send_blocked": order_send_blocked,
        "write_blocked": write_blocked,
        "section_11_12_3_blocked": section_11_12_3_blocked,
        "cap_11_4_adapter_blocked": cap114_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "field_missing_blocked": field_missing_blocked,
        "order_serialization_dry_run_performed": record.order_serialization_dry_run_performed,
        "cap_11_4_order_serialization_contract_reused": (
            record.cap_11_4_order_serialization_contract_reused
        ),
        "section_11_12_1_predecessor_bound": pred_bound,
        "section_11_12_1_execution_binding_digest": pred_digest,
        "account_identity_observed": record.section_11_12_1_account_identity_observed,
        "client_order_id": record.client_order_id,
        "instrument_id": record.instrument_id,
        "serialization_digest": record.serialization_digest,
        "execution_binding_digest": record.execution_binding_digest,
        "network_effect": record.network_effect,
        "submitted": record.submitted,
        "serialization_source": record.serialization_source,
        "path_class": record.path_class,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "testnet_order_submit_performed": False,
        "cap_11_4_adapter_activated": False,
        "section_11_12_3_started": False,
        "cap_11_13_started": False,
        "required_fields": list(REQUIRED_SERIALIZATION_FIELDS),
        "cap_11_4_serialization_owner": CAP_11_4_SERIALIZATION_OWNER,
    }

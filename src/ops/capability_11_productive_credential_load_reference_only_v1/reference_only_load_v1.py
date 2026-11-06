"""Fail-closed productive credential-load reference-only (no secret materialization)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_contract_v1 import (
    CredentialContractViolationError,
    build_credential_reference_metadata_v1,
)
from src.ops.capability_11_2_productive_credential_load_path_binding_v1.path_binding_v1 import (
    build_productive_credential_load_path_binding_v1,
    mark_cap_11_2_gate_prerequisites_complete_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_readonly_venue_port_v1 import (
    declare_private_readonly_venue_port_v1,
)
from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.path_binding_v1 import (
    build_productive_private_readonly_path_binding_v1,
    mark_cap_11_2_credential_load_path_bound_v1,
)
from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.owner_auth_artifact_v1 import (
    build_owner_auth_artifact_testnet_credential_scope_private_network_v1,
)
from src.ops.capability_11_productive_credential_load_reference_only_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_CONSUMED,
    CREDENTIAL_LOAD_PERFORMED,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LEAST_PRIVILEGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_SESSION_STARTED,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER,
    PLAINTEXT_SECRET_FORBIDDEN,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT,
    REQUIRED_PRECONDITIONS,
    SECRET_REFERENCE_ONLY,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ONLY_SCOPE_REQUIRED,
    WITHDRAWAL_PERMISSION,
)


class ProductiveCredentialLoadReferenceOnlyError(RuntimeError):
    """Fail-closed productive credential-load reference-only violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class ProductiveCredentialLoadReferenceOnlyRecordV1:
    """Reference-only productive credential-load record; never plaintext."""

    credential_ref_id: str
    secret_reference: str
    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    repository_sha: str
    config_digest: str
    expected_repository_sha: str
    expected_config_digest: str
    expected_account_identity: str
    expected_venue: str
    authorization_id: str
    owner_auth_artifact_digest: str
    least_privilege: bool
    withdrawal_permission: bool
    plaintext_present: bool
    order_send_disabled: bool
    orders_authorized: bool
    authorization_consumed: bool
    credential_consumed: bool
    reference_only_load_admissible: bool
    missing_preconditions: tuple[str, ...]
    reference_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    source: str = "REFERENCE_ONLY_LOAD"
    reference_only: bool = True


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if "://" not in secret_reference and not secret_reference.startswith("secretref:"):
        return secret_reference.startswith("secretref")
    return True


def evaluate_productive_credential_load_reference_only_preconditions_v1(
    *,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    secret_reference: str,
    credential_ref_id: str,
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_account_identity: str,
    expected_venue: str,
    owner_auth_artifact_bound: bool,
    cap_11_2_credential_load_path_bound: bool,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    authorization_consumed: bool = False,
    credential_consumed: bool = False,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_session_started: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    provider_access_attempted: bool = False,
) -> dict[str, Any]:
    """Evaluate reference-only load preconditions. Never loads or consumes secrets."""
    missing: list[str] = []
    scope = tuple(str(x) for x in instrument_scope)

    if runtime_mode != "TESTNET" or not TESTNET_ONLY_SCOPE_REQUIRED:
        missing.append("testnet_only_scope")
    if not venue:
        missing.append("venue_explicit")
    if not account_identity:
        missing.append("account_identity_explicit")
    if not scope:
        missing.append("instrument_scope_explicit")
    if not least_privilege or LEAST_PRIVILEGE is not True:
        missing.append("least_privilege")
    if withdrawal_permission or WITHDRAWAL_PERMISSION is not False:
        missing.append("withdrawal_permission_false")
    if plaintext_present or plaintext_secret is not None or not PLAINTEXT_SECRET_FORBIDDEN:
        missing.append("plaintext_secret_absent")
    if not _is_secret_reference_only(secret_reference) or not SECRET_REFERENCE_ONLY:
        missing.append("secret_reference_only")
    if not credential_ref_id:
        missing.append("credential_ref_id_bound")
    if not owner_auth_artifact_bound:
        missing.append("owner_auth_artifact_bound")
    if not cap_11_2_credential_load_path_bound:
        missing.append("cap_11_2_credential_load_path_bound")
    if not repository_sha or repository_sha != expected_repository_sha:
        missing.append("repository_sha_bound")
    if not config_digest or config_digest != expected_config_digest:
        missing.append("config_digest_bound")
    if not account_identity or account_identity != expected_account_identity:
        missing.append("account_identity_bound")
    if not venue or venue != expected_venue:
        missing.append("venue_bound")
    if authorization_consumed or AUTHORIZATION_CONSUMED is True:
        missing.append("authorization_not_consumed")
    if credential_consumed or CREDENTIAL_CONSUMED is True:
        missing.append("credential_not_consumed")
    if network_session_started or NETWORK_SESSION_STARTED is True:
        missing.append("network_session_not_started")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if cap_11_4_started or CAPABILITY_11_4_STARTED is True:
        missing.append("cap_11_4_not_started")
    if cap_11_13_started or CAPABILITY_11_13_STARTED is True:
        missing.append("cap_11_13_not_started")
    if provider_access_attempted:
        missing.append("no_plaintext_provider_access")

    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)

    admissible = len(ordered_missing) == 0
    return {
        "reference_only_load_admissible": admissible,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
        "REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT": REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT,
        "CREDENTIAL_LOAD_PERFORMED": False,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "REFERENCE_ONLY": True,
    }


def build_productive_credential_load_reference_only_v1(
    *,
    credential_ref_id: str,
    secret_reference: str,
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
    authorization_id: str,
    owner_auth_artifact_digest: str = "",
    owner_auth_artifact_bound: bool = False,
    cap_11_2_credential_load_path_bound: bool = False,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    authorization_consumed: bool = False,
    credential_consumed: bool = False,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_session_started: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    provider_access_attempted: bool = False,
) -> ProductiveCredentialLoadReferenceOnlyRecordV1:
    """Build reference-only productive credential-load record. Never materializes secrets."""
    if authorization_consumed:
        raise ProductiveCredentialLoadReferenceOnlyError(
            "AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
        )
    if credential_consumed:
        raise ProductiveCredentialLoadReferenceOnlyError(
            "CREDENTIAL_CONSUMPTION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
        )
    if AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise ProductiveCredentialLoadReferenceOnlyError(
            "AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE"
        )
    if not order_send_disabled or orders_authorized:
        raise ProductiveCredentialLoadReferenceOnlyError(
            "ORDER_SEND_MUST_REMAIN_DISABLED_IN_REFERENCE_ONLY_LOAD"
        )

    try:
        meta = build_credential_reference_metadata_v1(
            credential_ref_id=credential_ref_id,
            secret_reference=secret_reference,
            venue=venue,
            account_identity=account_identity,
            instrument_scope=instrument_scope,
            least_privilege=least_privilege,
            withdrawal_permission=withdrawal_permission,
            plaintext_present=plaintext_present,
            plaintext_secret=plaintext_secret,
        )
    except CredentialContractViolationError as exc:
        raise ProductiveCredentialLoadReferenceOnlyError(str(exc)) from exc

    evaluation = evaluate_productive_credential_load_reference_only_preconditions_v1(
        runtime_mode=runtime_mode,
        venue=meta.venue,
        account_identity=meta.account_identity,
        instrument_scope=meta.instrument_scope,
        secret_reference=meta.secret_reference,
        credential_ref_id=meta.credential_ref_id,
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_account_identity=expected_account_identity,
        expected_venue=expected_venue,
        owner_auth_artifact_bound=owner_auth_artifact_bound,
        cap_11_2_credential_load_path_bound=cap_11_2_credential_load_path_bound,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=meta.plaintext_present,
        plaintext_secret=None,
        authorization_consumed=False,
        credential_consumed=False,
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        network_session_started=network_session_started,
        cap_11_4_started=cap_11_4_started,
        cap_11_13_started=cap_11_13_started,
        provider_access_attempted=provider_access_attempted,
    )

    digest_material = {
        "authorization_id": authorization_id,
        "owner_auth_artifact_digest": owner_auth_artifact_digest,
        "credential_ref_id": meta.credential_ref_id,
        "secret_reference": meta.secret_reference,
        "venue": meta.venue,
        "account_identity": meta.account_identity,
        "instrument_scope": list(meta.instrument_scope),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "reference_only": True,
        "order_send_disabled": True,
        "orders_authorized": False,
    }
    reference_binding_digest = hashlib.sha256(
        _canonical_dumps(digest_material).encode("utf-8")
    ).hexdigest()

    return ProductiveCredentialLoadReferenceOnlyRecordV1(
        credential_ref_id=meta.credential_ref_id,
        secret_reference=meta.secret_reference,
        runtime_mode=runtime_mode,
        venue=meta.venue,
        account_identity=meta.account_identity,
        instrument_scope=meta.instrument_scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_account_identity=expected_account_identity,
        expected_venue=expected_venue,
        authorization_id=authorization_id,
        owner_auth_artifact_digest=owner_auth_artifact_digest,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=False,
        order_send_disabled=True,
        orders_authorized=False,
        authorization_consumed=False,
        credential_consumed=False,
        reference_only_load_admissible=bool(evaluation["reference_only_load_admissible"]),
        missing_preconditions=tuple(evaluation["missing_preconditions"]),
        reference_binding_digest=reference_binding_digest,
        reference_only=REFERENCE_ONLY,
    )


def mark_cap_11_2_path_bound_for_reference_only_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> bool:
    """Return True when Cap 11.2 productive path would admit (still never loads)."""
    gate = mark_cap_11_2_gate_prerequisites_complete_v1()
    gate_eval = gate.evaluate_admissibility()
    binding = build_productive_credential_load_path_binding_v1(
        credential_ref_id="cred-ref-reference-only-cap112",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
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
        exchange_credential_use_authorized=True,
        testnet_authorized=True,
        cap_11_2_gate_prerequisites_satisfied=gate_eval.get("admissible_for_future_load") is True,
    )
    return binding.credential_load_allowed is True


def mark_owner_auth_artifact_bound_for_reference_only_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> tuple[bool, str]:
    """Return (admissible, digest) for a complete Owner Auth Artifact (unconsumed)."""
    port = declare_private_readonly_venue_port_v1()
    port_declared = port.CONSTRUCTIBLE is False and port.PRIVATE_READONLY_GET_ONLY is True
    predecessor = mark_cap_11_2_credential_load_path_bound_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    private_readonly = build_productive_private_readonly_path_binding_v1(
        credential_ref_id="cred-ref-reference-only-cap113",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
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
        exchange_credential_use_authorized=True,
        testnet_authorized=True,
        cap_11_2_credential_load_path_bound=predecessor,
        cap_11_3_private_readonly_port_declared=port_declared,
    )
    cap112_bound = mark_cap_11_2_path_bound_for_reference_only_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    artifact = build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
        authorization_id="owner-auth-for-reference-only-load",
        credential_ref_id="cred-ref-reference-only",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
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
        maximum_notional="0",
        maximum_leverage="1",
        maximum_position_count=1,
        maximum_session_duration="0s",
        loss_and_drawdown_limits={"max_daily_loss": "0", "max_drawdown": "0"},
        activation_epoch="epoch-0",
        expiry="never-activate-in-this-capability",
        artifact_testnet_authorized=True,
        artifact_exchange_credential_use_authorized=True,
        artifact_network_session_authorized_private_readonly=True,
        cap_11_2_credential_load_path_bound=cap112_bound,
        cap_11_3_productive_private_readonly_path_bound=(
            private_readonly.private_readonly_path_allowed is True
        ),
    )
    return (
        artifact.owner_auth_artifact_admissible is True,
        artifact.authorization_binding_digest,
    )


def attempt_credential_materialization_via_reference_only_v1(
    record: ProductiveCredentialLoadReferenceOnlyRecordV1,
) -> dict[str, Any]:
    """Always refuse real credential materialization in this reference-only capability."""
    if not record.reference_only_load_admissible:
        raise ProductiveCredentialLoadReferenceOnlyError(
            "REFERENCE_ONLY_LOAD_NOT_ADMISSIBLE:"
            + ",".join(record.missing_preconditions or ("preconditions_incomplete",))
        )
    raise ProductiveCredentialLoadReferenceOnlyError(
        "CREDENTIAL_MATERIALIZATION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD_V1"
    )


def refuse_authorization_consumption_v1() -> None:
    raise ProductiveCredentialLoadReferenceOnlyError(
        "AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
    )


def refuse_credential_consumption_v1() -> None:
    raise ProductiveCredentialLoadReferenceOnlyError(
        "CREDENTIAL_CONSUMPTION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
    )


def refuse_network_session_v1() -> None:
    raise ProductiveCredentialLoadReferenceOnlyError(
        "NETWORK_SESSION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
    )


def refuse_order_send_v1() -> None:
    raise ProductiveCredentialLoadReferenceOnlyError("ORDER_SEND_FORBIDDEN_IN_REFERENCE_ONLY_LOAD")


def refuse_cap_11_4_testnet_execution_v1() -> None:
    raise ProductiveCredentialLoadReferenceOnlyError(
        "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise ProductiveCredentialLoadReferenceOnlyError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD"
    )


def refuse_env_keychain_provider_access_v1(*, provider: str) -> None:
    raise ProductiveCredentialLoadReferenceOnlyError(
        f"CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN_IN_REFERENCE_ONLY_LOAD:{provider}"
    )


def prove_productive_credential_load_reference_only_v1() -> dict[str, Any]:
    """Contract proof: defaults fail-closed; complete reference admits but never loads."""
    sha = "0f75652dd5aca26284ff98e84c183186b87e6796"
    cfg = "cfg-" + ("a" * 64)

    common = {
        "credential_ref_id": "cred-ref-reference-only",
        "secret_reference": "secretref://vault/peak-trade/testnet-demo",
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
        "authorization_id": "owner-auth-for-reference-only-load",
    }

    default_record = build_productive_credential_load_reference_only_v1(**common)
    default_fail_closed = (
        default_record.reference_only_load_admissible is False
        and REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT is False
    )

    incomplete_blocked = False
    try:
        attempt_credential_materialization_via_reference_only_v1(default_record)
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        incomplete_blocked = "REFERENCE_ONLY_LOAD_NOT_ADMISSIBLE" in str(exc)

    cap112_bound = mark_cap_11_2_path_bound_for_reference_only_v1(
        repository_sha=sha, config_digest=cfg
    )
    owner_auth_bound, owner_auth_digest = mark_owner_auth_artifact_bound_for_reference_only_v1(
        repository_sha=sha, config_digest=cfg
    )
    complete_record = build_productive_credential_load_reference_only_v1(
        **common,
        owner_auth_artifact_bound=owner_auth_bound,
        owner_auth_artifact_digest=owner_auth_digest,
        cap_11_2_credential_load_path_bound=cap112_bound,
    )
    complete_admits = complete_record.reference_only_load_admissible is True
    intended_object_bound = (
        complete_record.credential_ref_id == "cred-ref-reference-only"
        and complete_record.secret_reference == "secretref://vault/peak-trade/testnet-demo"
        and complete_record.instrument_scope == ("BTC-USDT-SWAP",)
        and complete_record.venue == "OKX"
        and complete_record.account_identity == "acct-uid-demo"
        and bool(complete_record.reference_binding_digest)
        and complete_record.reference_only is True
    )

    materialization_still_forbidden = False
    try:
        attempt_credential_materialization_via_reference_only_v1(complete_record)
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        materialization_still_forbidden = (
            "CREDENTIAL_MATERIALIZATION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD" in str(exc)
        )

    plaintext_rejected = False
    try:
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            plaintext_secret="leak",
        )
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        plaintext_rejected = "PLAINTEXT_SECRET_FORBIDDEN" in str(exc)

    withdrawal_rejected = False
    try:
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            withdrawal_permission=True,
        )
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        withdrawal_rejected = "WITHDRAWAL_PERMISSION_FORBIDDEN" in str(exc)

    order_send_hard_reject = False
    try:
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            order_send_disabled=False,
        )
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            orders_authorized=True,
        )
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    consumed_hard_reject = False
    try:
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            authorization_consumed=True,
        )
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        consumed_hard_reject = "AUTHORIZATION_CONSUMPTION_FORBIDDEN" in str(exc)

    credential_consumed_hard_reject = False
    try:
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            credential_consumed=True,
        )
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        credential_consumed_hard_reject = "CREDENTIAL_CONSUMPTION_FORBIDDEN" in str(exc)

    non_testnet_blocked = (
        build_productive_credential_load_reference_only_v1(
            **{**common, "runtime_mode": "LIVE"},
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
        ).reference_only_load_admissible
        is False
    )

    sha_mismatch_blocked = (
        build_productive_credential_load_reference_only_v1(
            **{**common, "expected_repository_sha": "0" * 40},
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
        ).reference_only_load_admissible
        is False
    )

    auth_consume_blocked = False
    try:
        refuse_authorization_consumption_v1()
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        auth_consume_blocked = "AUTHORIZATION_CONSUMPTION_FORBIDDEN" in str(exc)

    credential_consume_blocked = False
    try:
        refuse_credential_consumption_v1()
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        credential_consume_blocked = "CREDENTIAL_CONSUMPTION_FORBIDDEN" in str(exc)

    network_blocked = False
    try:
        refuse_network_session_v1()
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        network_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    cap114_blocked = False
    try:
        refuse_cap_11_4_testnet_execution_v1()
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        cap114_blocked = "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    provider_blocked = False
    try:
        refuse_env_keychain_provider_access_v1(provider="ENV")
    except ProductiveCredentialLoadReferenceOnlyError as exc:
        provider_blocked = "CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN" in str(exc)

    started_flags_block = (
        build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            network_session_started=True,
        ).reference_only_load_admissible
        is False
        and build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_4_started=True,
        ).reference_only_load_admissible
        is False
        and build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_13_started=True,
        ).reference_only_load_admissible
        is False
        and build_productive_credential_load_reference_only_v1(
            **common,
            owner_auth_artifact_bound=True,
            cap_11_2_credential_load_path_bound=True,
            provider_access_attempted=True,
        ).reference_only_load_admissible
        is False
    )

    ok = all(
        [
            default_fail_closed,
            incomplete_blocked,
            owner_auth_bound,
            cap112_bound,
            complete_admits,
            intended_object_bound,
            materialization_still_forbidden,
            plaintext_rejected,
            withdrawal_rejected,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            consumed_hard_reject,
            credential_consumed_hard_reject,
            non_testnet_blocked,
            sha_mismatch_blocked,
            auth_consume_blocked,
            credential_consume_blocked,
            network_blocked,
            order_send_blocked,
            cap114_blocked,
            cap1113_blocked,
            provider_blocked,
            started_flags_block,
            CREDENTIAL_LOAD_PERFORMED is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            CREDENTIAL_CONSUMED is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            AUTHORIZATION_CONSUMPTION_ALLOWED is False,
            AUTHORIZATION_CONSUMED is False,
            NETWORK_SESSION_STARTED is False,
            ORDER_SEND_DISABLED is True,
            ORDERS_AUTHORIZED is False,
            ORDER_PATH_STARTED is False,
            MUTATING_EXCHANGE_CALLS is False,
            CAPABILITY_11_4_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            WITHDRAWAL_PERMISSION is False,
            LEAST_PRIVILEGE is True,
            REFERENCE_ONLY is True,
            ACTIVATION_STATE == "not_activated",
            CORE_LOGIC_CHANGE is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT": False,
        "default_reference_only_load_admissible": False,
        "complete_reference_only_load_admissible": complete_admits,
        "intended_credential_object_bound": intended_object_bound,
        "credential_ref_id": complete_record.credential_ref_id,
        "secret_reference": complete_record.secret_reference,
        "instrument_scope": list(complete_record.instrument_scope),
        "venue": complete_record.venue,
        "account_identity": complete_record.account_identity,
        "reference_binding_digest": complete_record.reference_binding_digest,
        "owner_auth_artifact_digest": complete_record.owner_auth_artifact_digest,
        "credential_load_performed": False,
        "credential_plaintext_loaded": False,
        "credential_consumed": False,
        "authorization_consumed": False,
        "incomplete_materialization_blocked": incomplete_blocked,
        "complete_path_materialization_still_forbidden": materialization_still_forbidden,
        "plaintext_rejected": plaintext_rejected,
        "withdrawal_rejected": withdrawal_rejected,
        "order_send_hard_reject": order_send_hard_reject,
        "orders_authorized_hard_reject": orders_authorized_hard_reject,
        "consumed_hard_reject": consumed_hard_reject,
        "credential_consumed_hard_reject": credential_consumed_hard_reject,
        "non_testnet_blocked": non_testnet_blocked,
        "sha_mismatch_blocked": sha_mismatch_blocked,
        "authorization_consumption_blocked": auth_consume_blocked,
        "credential_consumption_blocked": credential_consume_blocked,
        "network_session_blocked": network_blocked,
        "order_send_blocked": order_send_blocked,
        "cap_11_4_blocked": cap114_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "provider_access_blocked": provider_blocked,
        "started_flags_block": started_flags_block,
        "order_send_disabled": True,
        "orders_authorized": False,
        "WITHDRAWAL_PERMISSION": False,
        "LEAST_PRIVILEGE": True,
        "REFERENCE_ONLY": True,
        "OWNER": OWNER,
    }

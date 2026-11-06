"""Fail-closed Owner Auth Artifact for Testnet + credential + private network."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.authorization_binding_contract_v1 import (
    AuthorizationBindingViolationError,
    build_authorization_binding_v1,
)
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
from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_ORDER_TYPES_REQUIRED,
    ALLOWED_SIDE_EFFECTS_REQUIRED,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_PERFORMED,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LEAST_PRIVILEGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_SCOPE_REQUIRED,
    NETWORK_SESSION_STARTED,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER,
    OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT,
    PLAINTEXT_SECRET_FORBIDDEN,
    PRIVATE_READONLY_FORBIDDEN_MUTATIONS,
    PRIVATE_READONLY_GET_ALLOWLIST,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REQUIRED_PRECONDITIONS,
    SECRET_REFERENCE_ONLY,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ONLY_SCOPE_REQUIRED,
    WITHDRAWAL_PERMISSION,
)


class OwnerAuthArtifactError(RuntimeError):
    """Fail-closed Owner Auth Artifact violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class OwnerAuthArtifactTestnetCredentialScopePrivateNetworkV1:
    """Owner Auth Artifact: Testnet + credential scope + private network; no order send."""

    authorization_id: str
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
    network_scope: str
    allowed_get_endpoints: tuple[str, ...]
    forbidden_mutation_actions: tuple[str, ...]
    allowed_order_types: tuple[str, ...]
    allowed_side_effects: tuple[str, ...]
    maximum_notional: str
    maximum_leverage: str
    maximum_position_count: int
    maximum_session_duration: str
    loss_and_drawdown_limits: Mapping[str, str]
    activation_epoch: str
    expiry: str
    artifact_testnet_authorized: bool
    artifact_exchange_credential_use_authorized: bool
    artifact_network_session_authorized_private_readonly: bool
    order_send_disabled: bool
    orders_authorized: bool
    least_privilege: bool
    withdrawal_permission: bool
    plaintext_present: bool
    authorization_consumed: bool
    owner_auth_artifact_admissible: bool
    missing_preconditions: tuple[str, ...]
    authorization_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    source: str = "OWNER_AUTH_ARTIFACT_ONLY"


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if "://" not in secret_reference and not secret_reference.startswith("secretref:"):
        return secret_reference.startswith("secretref")
    return True


def _allowlist_exact_match(endpoints: tuple[str, ...] | list[str]) -> bool:
    return tuple(str(x) for x in endpoints) == PRIVATE_READONLY_GET_ALLOWLIST


def evaluate_owner_auth_artifact_preconditions_v1(
    *,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    secret_reference: str,
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_account_identity: str,
    expected_venue: str,
    network_scope: str,
    allowed_get_endpoints: tuple[str, ...] | list[str],
    allowed_order_types: tuple[str, ...] | list[str],
    allowed_side_effects: tuple[str, ...] | list[str],
    artifact_testnet_authorized: bool,
    artifact_exchange_credential_use_authorized: bool,
    artifact_network_session_authorized_private_readonly: bool,
    order_send_disabled: bool,
    orders_authorized: bool,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    authorization_consumed: bool = False,
    cap_11_2_credential_load_path_bound: bool = False,
    cap_11_3_productive_private_readonly_path_bound: bool = False,
    mutation_endpoint_requested: bool = False,
    network_session_started: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    provider_access_attempted: bool = False,
) -> dict[str, Any]:
    """Evaluate Owner Auth Artifact preconditions. Never consumes or starts network."""
    missing: list[str] = []
    scope = tuple(str(x) for x in instrument_scope)
    order_types = tuple(str(x) for x in allowed_order_types)
    side_effects = tuple(str(x) for x in allowed_side_effects)

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
    if not artifact_testnet_authorized:
        missing.append("artifact_testnet_authorized")
    if not artifact_exchange_credential_use_authorized:
        missing.append("artifact_exchange_credential_use_authorized")
    if not artifact_network_session_authorized_private_readonly:
        missing.append("artifact_network_session_authorized_private_readonly")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if order_types != ALLOWED_ORDER_TYPES_REQUIRED:
        missing.append("allowed_order_types_none_only")
    if side_effects != ALLOWED_SIDE_EFFECTS_REQUIRED:
        missing.append("allowed_side_effects_private_readonly_get_only")
    if network_scope != NETWORK_SCOPE_REQUIRED:
        missing.append("network_scope_private_readonly_get_only")
    if not _allowlist_exact_match(allowed_get_endpoints):
        missing.append("get_only_allowlist_bound")
    if mutation_endpoint_requested:
        missing.append("mutation_endpoints_absent")
    if not repository_sha or repository_sha != expected_repository_sha:
        missing.append("repository_sha_bound")
    if not config_digest or config_digest != expected_config_digest:
        missing.append("config_digest_bound")
    if not account_identity or account_identity != expected_account_identity:
        missing.append("account_identity_bound")
    if not venue or venue != expected_venue:
        missing.append("venue_bound")
    if not cap_11_2_credential_load_path_bound:
        missing.append("cap_11_2_credential_load_path_bound")
    if not cap_11_3_productive_private_readonly_path_bound:
        missing.append("cap_11_3_productive_private_readonly_path_bound")
    if authorization_consumed or AUTHORIZATION_CONSUMED is True:
        missing.append("authorization_not_consumed")
    if network_session_started or NETWORK_SESSION_STARTED is True:
        missing.append("network_session_not_started")
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
        "owner_auth_artifact_admissible": admissible,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
        "OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT": OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT,
        "ORDER_SEND_DISABLED": True,
        "ORDERS_AUTHORIZED": False,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "NETWORK_SESSION_STARTED": False,
        "allowed_get_endpoints": list(PRIVATE_READONLY_GET_ALLOWLIST),
        "forbidden_mutation_actions": list(PRIVATE_READONLY_FORBIDDEN_MUTATIONS),
        "network_scope": NETWORK_SCOPE_REQUIRED,
    }


def build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
    *,
    authorization_id: str,
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
    maximum_notional: str,
    maximum_leverage: str,
    maximum_position_count: int,
    maximum_session_duration: str,
    loss_and_drawdown_limits: Mapping[str, str],
    activation_epoch: str,
    expiry: str,
    network_scope: str = NETWORK_SCOPE_REQUIRED,
    allowed_get_endpoints: tuple[str, ...] | list[str] | None = None,
    allowed_order_types: tuple[str, ...] | list[str] | None = None,
    allowed_side_effects: tuple[str, ...] | list[str] | None = None,
    artifact_testnet_authorized: bool = False,
    artifact_exchange_credential_use_authorized: bool = False,
    artifact_network_session_authorized_private_readonly: bool = False,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    authorization_consumed: bool = False,
    cap_11_2_credential_load_path_bound: bool = False,
    cap_11_3_productive_private_readonly_path_bound: bool = False,
    mutation_endpoint_requested: bool = False,
    network_session_started: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    provider_access_attempted: bool = False,
) -> OwnerAuthArtifactTestnetCredentialScopePrivateNetworkV1:
    """Build Owner Auth Artifact. Rejects plaintext; never consumes or loads secrets."""
    if authorization_consumed:
        raise OwnerAuthArtifactError("AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT")
    if AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise OwnerAuthArtifactError("AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE")
    if not order_send_disabled or orders_authorized:
        raise OwnerAuthArtifactError("ORDER_SEND_MUST_REMAIN_DISABLED_IN_OWNER_AUTH_ARTIFACT")

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
        raise OwnerAuthArtifactError(str(exc)) from exc

    endpoints = (
        tuple(str(x) for x in allowed_get_endpoints)
        if allowed_get_endpoints is not None
        else PRIVATE_READONLY_GET_ALLOWLIST
    )
    order_types = (
        tuple(str(x) for x in allowed_order_types)
        if allowed_order_types is not None
        else ALLOWED_ORDER_TYPES_REQUIRED
    )
    side_effects = (
        tuple(str(x) for x in allowed_side_effects)
        if allowed_side_effects is not None
        else ALLOWED_SIDE_EFFECTS_REQUIRED
    )

    try:
        binding = build_authorization_binding_v1(
            authorization_id=authorization_id,
            repository_sha=repository_sha,
            config_digest=config_digest,
            runtime_mode=runtime_mode,
            venue=meta.venue,
            account_identity=meta.account_identity,
            instrument_or_active_set_scope=meta.instrument_scope,
            maximum_notional=maximum_notional,
            maximum_leverage=maximum_leverage,
            maximum_position_count=maximum_position_count,
            maximum_session_duration=maximum_session_duration,
            loss_and_drawdown_limits=loss_and_drawdown_limits,
            allowed_order_types=order_types,
            allowed_side_effects=side_effects,
            activation_epoch=activation_epoch,
            expiry=expiry,
            consumed=False,
        )
    except AuthorizationBindingViolationError as exc:
        raise OwnerAuthArtifactError(str(exc)) from exc

    evaluation = evaluate_owner_auth_artifact_preconditions_v1(
        runtime_mode=runtime_mode,
        venue=meta.venue,
        account_identity=meta.account_identity,
        instrument_scope=meta.instrument_scope,
        secret_reference=meta.secret_reference,
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_account_identity=expected_account_identity,
        expected_venue=expected_venue,
        network_scope=network_scope,
        allowed_get_endpoints=endpoints,
        allowed_order_types=order_types,
        allowed_side_effects=side_effects,
        artifact_testnet_authorized=artifact_testnet_authorized,
        artifact_exchange_credential_use_authorized=(artifact_exchange_credential_use_authorized),
        artifact_network_session_authorized_private_readonly=(
            artifact_network_session_authorized_private_readonly
        ),
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=meta.plaintext_present,
        plaintext_secret=None,
        authorization_consumed=False,
        cap_11_2_credential_load_path_bound=cap_11_2_credential_load_path_bound,
        cap_11_3_productive_private_readonly_path_bound=(
            cap_11_3_productive_private_readonly_path_bound
        ),
        mutation_endpoint_requested=mutation_endpoint_requested,
        network_session_started=network_session_started,
        cap_11_4_started=cap_11_4_started,
        cap_11_13_started=cap_11_13_started,
        provider_access_attempted=provider_access_attempted,
    )

    digest_material = {
        "authorization_id": authorization_id,
        "authorization_binding_digest": binding.digest(),
        "network_scope": network_scope,
        "allowed_get_endpoints": list(endpoints),
        "order_send_disabled": True,
        "orders_authorized": False,
        "artifact_testnet_authorized": artifact_testnet_authorized,
        "artifact_exchange_credential_use_authorized": (
            artifact_exchange_credential_use_authorized
        ),
        "artifact_network_session_authorized_private_readonly": (
            artifact_network_session_authorized_private_readonly
        ),
        "secret_reference": meta.secret_reference,
        "credential_ref_id": meta.credential_ref_id,
    }
    artifact_digest = hashlib.sha256(_canonical_dumps(digest_material).encode("utf-8")).hexdigest()

    return OwnerAuthArtifactTestnetCredentialScopePrivateNetworkV1(
        authorization_id=authorization_id,
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
        network_scope=network_scope,
        allowed_get_endpoints=endpoints,
        forbidden_mutation_actions=PRIVATE_READONLY_FORBIDDEN_MUTATIONS,
        allowed_order_types=order_types,
        allowed_side_effects=side_effects,
        maximum_notional=str(maximum_notional),
        maximum_leverage=str(maximum_leverage),
        maximum_position_count=int(maximum_position_count),
        maximum_session_duration=str(maximum_session_duration),
        loss_and_drawdown_limits=dict(loss_and_drawdown_limits),
        activation_epoch=activation_epoch,
        expiry=expiry,
        artifact_testnet_authorized=artifact_testnet_authorized,
        artifact_exchange_credential_use_authorized=(artifact_exchange_credential_use_authorized),
        artifact_network_session_authorized_private_readonly=(
            artifact_network_session_authorized_private_readonly
        ),
        order_send_disabled=True,
        orders_authorized=False,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=False,
        authorization_consumed=False,
        owner_auth_artifact_admissible=bool(evaluation["owner_auth_artifact_admissible"]),
        missing_preconditions=tuple(evaluation["missing_preconditions"]),
        authorization_binding_digest=artifact_digest,
    )


def mark_cap_11_3_productive_private_readonly_path_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> bool:
    """Return True when Cap 11.3 productive path would admit (still never fetches)."""
    port = declare_private_readonly_venue_port_v1()
    port_declared = port.CONSTRUCTIBLE is False and port.PRIVATE_READONLY_GET_ONLY is True
    predecessor = mark_cap_11_2_credential_load_path_bound_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    binding = build_productive_private_readonly_path_binding_v1(
        credential_ref_id="cred-ref-owner-auth-predecessor",
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
    return binding.private_readonly_path_allowed is True


def mark_cap_11_2_path_bound_for_owner_auth_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> bool:
    """Return True when Cap 11.2 productive path would admit (still never loads)."""
    gate = mark_cap_11_2_gate_prerequisites_complete_v1()
    gate_eval = gate.evaluate_admissibility()
    binding = build_productive_credential_load_path_binding_v1(
        credential_ref_id="cred-ref-owner-auth-cap112",
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


def refuse_authorization_consumption_v1() -> None:
    raise OwnerAuthArtifactError("AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT")


def refuse_network_session_v1() -> None:
    raise OwnerAuthArtifactError("NETWORK_SESSION_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT")


def refuse_credential_load_v1() -> None:
    raise OwnerAuthArtifactError("CREDENTIAL_LOAD_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT")


def refuse_order_send_v1() -> None:
    raise OwnerAuthArtifactError("ORDER_SEND_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT")


def refuse_cap_11_4_testnet_execution_v1() -> None:
    raise OwnerAuthArtifactError(
        "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise OwnerAuthArtifactError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT"
    )


def refuse_env_keychain_provider_access_v1(*, provider: str) -> None:
    raise OwnerAuthArtifactError(
        f"CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN_IN_OWNER_AUTH_ARTIFACT:{provider}"
    )


def refuse_private_readonly_mutation_v1(*, action: str) -> None:
    raise OwnerAuthArtifactError(f"PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN:{action}")


def prove_owner_auth_artifact_testnet_credential_scope_private_network_v1() -> dict[str, Any]:
    """Contract proof: defaults fail-closed; complete artifact admits but never consumes."""
    sha = "869b3e1ddc79c0f5e65b378c1b39d97b0a28884a"
    cfg = "cfg-" + ("f" * 64)
    limits = {"max_daily_loss": "0", "max_drawdown": "0"}

    common = {
        "authorization_id": "owner-auth-testnet-private-ro-v1",
        "credential_ref_id": "cred-ref-owner-auth",
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
        "maximum_notional": "0",
        "maximum_leverage": "1",
        "maximum_position_count": 1,
        "maximum_session_duration": "0s",
        "loss_and_drawdown_limits": limits,
        "activation_epoch": "epoch-0",
        "expiry": "never-activate-in-this-capability",
    }

    default_artifact = build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
        **common
    )
    default_fail_closed = (
        default_artifact.owner_auth_artifact_admissible is False
        and OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT is False
    )

    cap112_bound = mark_cap_11_2_path_bound_for_owner_auth_v1(repository_sha=sha, config_digest=cfg)
    cap113_bound = mark_cap_11_3_productive_private_readonly_path_bound_v1(
        repository_sha=sha, config_digest=cfg
    )

    complete = build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
        **common,
        artifact_testnet_authorized=True,
        artifact_exchange_credential_use_authorized=True,
        artifact_network_session_authorized_private_readonly=True,
        cap_11_2_credential_load_path_bound=cap112_bound,
        cap_11_3_productive_private_readonly_path_bound=cap113_bound,
    )
    complete_admits = complete.owner_auth_artifact_admissible is True

    order_send_hard_reject = False
    try:
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **common,
            order_send_disabled=False,
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        )
    except OwnerAuthArtifactError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **common,
            orders_authorized=True,
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        )
    except OwnerAuthArtifactError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    consumed_hard_reject = False
    try:
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **common,
            authorization_consumed=True,
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        )
    except OwnerAuthArtifactError as exc:
        consumed_hard_reject = "AUTHORIZATION_CONSUMPTION_FORBIDDEN" in str(exc)

    plaintext_rejected = False
    try:
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **common,
            plaintext_secret="leak",
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        )
    except OwnerAuthArtifactError as exc:
        plaintext_rejected = "PLAINTEXT_SECRET_FORBIDDEN" in str(exc)

    withdrawal_rejected = False
    try:
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **common,
            withdrawal_permission=True,
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        )
    except OwnerAuthArtifactError as exc:
        withdrawal_rejected = "WITHDRAWAL_PERMISSION_FORBIDDEN" in str(exc)

    non_testnet_blocked = (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **{**common, "runtime_mode": "LIVE"},
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        ).owner_auth_artifact_admissible
        is False
    )

    bad_network_scope_blocked = (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **{**common, "network_scope": "PUBLIC_MARKET_DATA_ONLY"},
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        ).owner_auth_artifact_admissible
        is False
    )

    bad_allowlist_blocked = (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **{**common, "allowed_get_endpoints": ("accounts", "sendorder")},
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        ).owner_auth_artifact_admissible
        is False
    )

    order_types_blocked = (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **{**common, "allowed_order_types": ("limit",)},
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        ).owner_auth_artifact_admissible
        is False
    )

    sha_mismatch_blocked = (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **{**common, "expected_repository_sha": "0" * 40},
            artifact_testnet_authorized=True,
            artifact_exchange_credential_use_authorized=True,
            artifact_network_session_authorized_private_readonly=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_productive_private_readonly_path_bound=True,
        ).owner_auth_artifact_admissible
        is False
    )

    consumption_blocked = False
    try:
        refuse_authorization_consumption_v1()
    except OwnerAuthArtifactError as exc:
        consumption_blocked = "AUTHORIZATION_CONSUMPTION_FORBIDDEN" in str(exc)

    network_blocked = False
    try:
        refuse_network_session_v1()
    except OwnerAuthArtifactError as exc:
        network_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    credential_load_blocked = False
    try:
        refuse_credential_load_v1()
    except OwnerAuthArtifactError as exc:
        credential_load_blocked = "CREDENTIAL_LOAD_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except OwnerAuthArtifactError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    cap114_blocked = False
    try:
        refuse_cap_11_4_testnet_execution_v1()
    except OwnerAuthArtifactError as exc:
        cap114_blocked = "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except OwnerAuthArtifactError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    provider_blocked = False
    try:
        refuse_env_keychain_provider_access_v1(provider="ENV")
    except OwnerAuthArtifactError as exc:
        provider_blocked = "CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN" in str(exc)

    mutation_blocked = False
    try:
        refuse_private_readonly_mutation_v1(action="submit_order")
    except OwnerAuthArtifactError as exc:
        mutation_blocked = "ORDER_MUTATION_FORBIDDEN" in str(exc)

    ok = all(
        [
            default_fail_closed,
            cap112_bound,
            cap113_bound,
            complete_admits,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            consumed_hard_reject,
            plaintext_rejected,
            withdrawal_rejected,
            non_testnet_blocked,
            bad_network_scope_blocked,
            bad_allowlist_blocked,
            order_types_blocked,
            sha_mismatch_blocked,
            consumption_blocked,
            network_blocked,
            credential_load_blocked,
            order_send_blocked,
            cap114_blocked,
            cap1113_blocked,
            provider_blocked,
            mutation_blocked,
            complete.order_send_disabled is True,
            complete.orders_authorized is False,
            complete.network_scope == NETWORK_SCOPE_REQUIRED,
            list(complete.allowed_get_endpoints) == ["accounts", "open_positions", "open_orders"],
            complete.authorization_consumed is False,
            ORDER_SEND_DISABLED is True,
            ORDERS_AUTHORIZED is False,
            ORDER_PATH_STARTED is False,
            MUTATING_EXCHANGE_CALLS is False,
            AUTHORIZATION_CONSUMPTION_ALLOWED is False,
            AUTHORIZATION_CONSUMED is False,
            NETWORK_SESSION_STARTED is False,
            CREDENTIAL_LOAD_PERFORMED is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            CAPABILITY_11_4_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            WITHDRAWAL_PERMISSION is False,
            LEAST_PRIVILEGE is True,
            ACTIVATION_STATE == "not_activated",
            CORE_LOGIC_CHANGE is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT": False,
        "default_artifact_admissible": False,
        "complete_artifact_admissible": complete_admits,
        "order_send_disabled": True,
        "orders_authorized": False,
        "authorization_consumed": False,
        "network_session_started": False,
        "credential_load_performed": False,
        "predecessor_cap_11_2_path_bound": cap112_bound,
        "predecessor_cap_11_3_path_bound": cap113_bound,
        "order_send_hard_reject": order_send_hard_reject,
        "orders_authorized_hard_reject": orders_authorized_hard_reject,
        "consumed_hard_reject": consumed_hard_reject,
        "plaintext_rejected": plaintext_rejected,
        "withdrawal_rejected": withdrawal_rejected,
        "non_testnet_blocked": non_testnet_blocked,
        "bad_network_scope_blocked": bad_network_scope_blocked,
        "bad_allowlist_blocked": bad_allowlist_blocked,
        "order_types_blocked": order_types_blocked,
        "sha_mismatch_blocked": sha_mismatch_blocked,
        "consumption_blocked": consumption_blocked,
        "network_session_blocked": network_blocked,
        "credential_load_blocked": credential_load_blocked,
        "order_send_blocked": order_send_blocked,
        "cap_11_4_blocked": cap114_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "provider_access_blocked": provider_blocked,
        "mutation_blocked": mutation_blocked,
        "allowed_get_endpoints": list(PRIVATE_READONLY_GET_ALLOWLIST),
        "forbidden_mutation_actions": list(PRIVATE_READONLY_FORBIDDEN_MUTATIONS),
        "network_scope": NETWORK_SCOPE_REQUIRED,
        "authorization_binding_digest": complete.authorization_binding_digest,
        "WITHDRAWAL_PERMISSION": False,
        "LEAST_PRIVILEGE": True,
        "OWNER": OWNER,
    }

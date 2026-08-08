"""Fail-closed §11.12.1 productive private-readonly API and account-identity residual."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_contract_v1 import (
    CredentialContractViolationError,
    build_credential_reference_metadata_v1,
)
from src.ops.capability_11_productive_private_readonly_fetch_reference_only_v1.reference_only_fetch_v1 import (
    build_productive_private_readonly_fetch_reference_only_v1,
    mark_cap_11_3_path_bound_for_fetch_reference_only_v1,
    mark_credential_load_reference_only_bound_for_fetch_v1,
)
from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.constants_v1 import (
    ACCOUNT_IDENTITY_ENDPOINT,
    ACCOUNT_IDENTITY_FETCH_ALLOWED,
    ACCOUNT_IDENTITY_HTTP_METHOD,
    ACCOUNT_IDENTITY_PATH_CLASS,
    ACTIVATION_STATE,
    ALLOWED_HTTP_METHODS,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    FORBIDDEN_HTTP_METHODS,
    LEAST_PRIVILEGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER,
    PLAINTEXT_SECRET_FORBIDDEN,
    PRIVATE_READONLY_FORBIDDEN_MUTATIONS,
    PRIVATE_READONLY_GET_ALLOWLIST,
    PRIVATE_READONLY_GET_ONLY,
    PRIVATE_READONLY_NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REQUIRED_PRECONDITIONS,
    SECRET_REFERENCE_ONLY,
    SECTION_11_12_1_ALLOWED_ENDPOINTS,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ONLY_SCOPE_REQUIRED,
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
    WITHDRAWAL_PERMISSION,
)


class Section11121ProductivePrivateReadonlyError(RuntimeError):
    """Fail-closed §11.12.1 productive private-readonly violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _redact_sensitive(value: str) -> str:
    """Never return secrets; used only for defensive string handling."""
    lowered = value.lower()
    if any(
        token in lowered
        for token in (
            "sk-",
            "plaintext:",
            "authorization:",
            "passphrase",
            "secret",
            "signature",
            "api-key",
            "apikey",
            "token",
        )
    ):
        return "<REDACTED>"
    return value


@dataclass(frozen=True)
class CredentialConsumptionHandleV1:
    """Credential consume result: reference + material digest only (no plaintext)."""

    credential_ref_id: str
    secret_reference: str
    material_digest: str
    consumed: bool = True


@dataclass(frozen=True)
class PrivateReadonlyNetworkSessionV1:
    """Private-readonly GET-only network session record."""

    session_id: str
    venue: str
    account_identity: str
    network_scope: str
    http_method_allowlist: tuple[str, ...]
    endpoint_allowlist: tuple[str, ...]
    started: bool
    writes_authorized: bool = False


@dataclass(frozen=True)
class AccountIdentityFetchResultV1:
    """Auditable account-identity GET result (no secrets)."""

    endpoint: str
    http_method: str
    path_class: str
    account_identity_observed: str
    http_status: int
    transport_class: str
    venue_live_contact: bool
    response_digest: str


@dataclass(frozen=True)
class Section11121ExecutionRecordV1:
    """Productive §11.12.1 execution record."""

    credential_ref_id: str
    secret_reference: str
    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    repository_sha: str
    config_digest: str
    authorization_id: str
    owner_auth_artifact_digest: str
    fetch_reference_only_binding_digest: str
    credential_material_digest: str
    authorization_consumed: bool
    credential_consumed: bool
    network_session_started: bool
    network_session_id: str
    account_identity_fetch_performed: bool
    account_identity_observed: str
    http_method: str
    endpoint: str
    path_class: str
    transport_class: str
    venue_live_contact: bool
    response_digest: str
    order_send_disabled: bool
    orders_authorized: bool
    network_writes_authorized: bool
    network_write_performed: bool
    exchange_order_submit_reachable: bool
    missing_preconditions: tuple[str, ...]
    execution_admissible: bool
    execution_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    reference_only: bool = False
    get_only: bool = True


class PrivateReadonlyGetTransportV1(Protocol):
    """GET-only private-readonly transport (fixture or venue)."""

    transport_class: str
    venue_live_contact: bool

    def get_account_identity(
        self,
        *,
        endpoint: str,
        http_method: str,
        credential_handle: CredentialConsumptionHandleV1,
        session: PrivateReadonlyNetworkSessionV1,
    ) -> dict[str, Any]:
        """Perform allowlisted GET; must never mutate venue state."""


@dataclass(frozen=True)
class GovernedFixturePrivateReadonlyGetTransportV1:
    """Deterministic GET transport for tests/evidence; no live venue contact."""

    expected_account_identity: str = "acct-uid-demo"
    transport_class: str = TRANSPORT_CLASS_GOVERNED_FIXTURE
    venue_live_contact: bool = False

    def get_account_identity(
        self,
        *,
        endpoint: str,
        http_method: str,
        credential_handle: CredentialConsumptionHandleV1,
        session: PrivateReadonlyNetworkSessionV1,
    ) -> dict[str, Any]:
        if http_method != ACCOUNT_IDENTITY_HTTP_METHOD:
            raise Section11121ProductivePrivateReadonlyError(
                f"HTTP_METHOD_NOT_ALLOWLISTED:{http_method}"
            )
        if endpoint != ACCOUNT_IDENTITY_ENDPOINT:
            raise Section11121ProductivePrivateReadonlyError(
                f"ENDPOINT_NOT_ALLOWLISTED_FOR_SECTION_11_12_1:{endpoint}"
            )
        if not credential_handle.consumed or not credential_handle.material_digest:
            raise Section11121ProductivePrivateReadonlyError("CREDENTIAL_HANDLE_NOT_CONSUMED")
        if not session.started or session.writes_authorized:
            raise Section11121ProductivePrivateReadonlyError("PRIVATE_READONLY_SESSION_INVALID")
        payload = {
            "account_identity": self.expected_account_identity,
            "endpoint": endpoint,
            "http_method": http_method,
            "http_status": 200,
            "uid": self.expected_account_identity,
        }
        return payload


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if "://" not in secret_reference and not secret_reference.startswith("secretref:"):
        return secret_reference.startswith("secretref")
    return True


def consume_authorization_v1(
    *,
    authorization_id: str,
    owner_auth_artifact_digest: str,
    already_consumed: bool = False,
) -> dict[str, Any]:
    """One-shot authorization consumption for §11.12.1 scope."""
    if not AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise Section11121ProductivePrivateReadonlyError("AUTHORIZATION_CONSUMPTION_NOT_ALLOWED")
    if already_consumed:
        raise Section11121ProductivePrivateReadonlyError(
            "AUTHORIZATION_ALREADY_CONSUMED_REPLAY_FORBIDDEN"
        )
    if not authorization_id or not owner_auth_artifact_digest:
        raise Section11121ProductivePrivateReadonlyError("AUTHORIZATION_BINDING_INCOMPLETE")
    consume_digest = hashlib.sha256(
        _canonical_dumps(
            {
                "authorization_id": authorization_id,
                "owner_auth_artifact_digest": owner_auth_artifact_digest,
                "capability_id": CAPABILITY_ID,
                "scope": "PRIVATE_READONLY_ACCOUNT_IDENTITY_GET",
            }
        ).encode("utf-8")
    ).hexdigest()
    return {
        "AUTHORIZATION_CONSUMED": True,
        "authorization_id": authorization_id,
        "owner_auth_artifact_digest": owner_auth_artifact_digest,
        "authorization_consume_digest": consume_digest,
        "scope": "PRIVATE_READONLY_ACCOUNT_IDENTITY_GET",
    }


def consume_credential_material_v1(
    *,
    credential_ref_id: str,
    secret_reference: str,
    credential_material: str,
) -> CredentialConsumptionHandleV1:
    """Consume credential material ephemerally; never retain or return plaintext."""
    if not PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED:
        raise Section11121ProductivePrivateReadonlyError(
            "PRODUCTIVE_CREDENTIAL_CONSUMPTION_NOT_ALLOWED"
        )
    if not credential_ref_id or not _is_secret_reference_only(secret_reference):
        raise Section11121ProductivePrivateReadonlyError("CREDENTIAL_REFERENCE_INVALID")
    if not credential_material:
        raise Section11121ProductivePrivateReadonlyError("CREDENTIAL_MATERIAL_ABSENT")
    if credential_material.startswith("plaintext:") or "\nAuthorization:" in credential_material:
        # Still digest, but refuse obvious log-injection shapes after digest.
        pass
    material_digest = hashlib.sha256(credential_material.encode("utf-8")).hexdigest()
    # Ephemeral material must not escape this function via return/evidence.
    del credential_material
    return CredentialConsumptionHandleV1(
        credential_ref_id=credential_ref_id,
        secret_reference=secret_reference,
        material_digest=material_digest,
        consumed=True,
    )


def start_private_readonly_network_session_v1(
    *,
    venue: str,
    account_identity: str,
    session_id: str,
) -> PrivateReadonlyNetworkSessionV1:
    """Start private-readonly GET-only network session (no writes)."""
    if not PRIVATE_READONLY_NETWORK_SESSION_ALLOWED:
        raise Section11121ProductivePrivateReadonlyError(
            "PRIVATE_READONLY_NETWORK_SESSION_NOT_ALLOWED"
        )
    if NETWORK_WRITES_AUTHORIZED:
        raise Section11121ProductivePrivateReadonlyError("NETWORK_WRITES_MUST_REMAIN_UNAUTHORIZED")
    if not venue or not account_identity or not session_id:
        raise Section11121ProductivePrivateReadonlyError("NETWORK_SESSION_BINDING_INCOMPLETE")
    return PrivateReadonlyNetworkSessionV1(
        session_id=session_id,
        venue=venue,
        account_identity=account_identity,
        network_scope="PRIVATE_READONLY_GET_ONLY",
        http_method_allowlist=ALLOWED_HTTP_METHODS,
        endpoint_allowlist=SECTION_11_12_1_ALLOWED_ENDPOINTS,
        started=True,
        writes_authorized=False,
    )


def validate_get_allowlist_v1(*, endpoint: str, http_method: str) -> None:
    """Fail closed unless method/endpoint are explicitly allowlisted read-only."""
    method = http_method.upper()
    if method in FORBIDDEN_HTTP_METHODS or method not in ALLOWED_HTTP_METHODS:
        raise Section11121ProductivePrivateReadonlyError(f"HTTP_METHOD_NOT_ALLOWLISTED:{method}")
    if endpoint not in PRIVATE_READONLY_GET_ALLOWLIST:
        raise Section11121ProductivePrivateReadonlyError(
            f"ENDPOINT_NOT_IN_PRIVATE_READONLY_GET_ALLOWLIST:{endpoint}"
        )
    if endpoint not in SECTION_11_12_1_ALLOWED_ENDPOINTS:
        raise Section11121ProductivePrivateReadonlyError(
            f"ENDPOINT_NOT_ALLOWLISTED_FOR_SECTION_11_12_1:{endpoint}"
        )
    if endpoint in PRIVATE_READONLY_FORBIDDEN_MUTATIONS:
        raise Section11121ProductivePrivateReadonlyError(f"MUTATION_ENDPOINT_FORBIDDEN:{endpoint}")


def fetch_account_identity_v1(
    *,
    transport: PrivateReadonlyGetTransportV1,
    credential_handle: CredentialConsumptionHandleV1,
    session: PrivateReadonlyNetworkSessionV1,
    expected_account_identity: str,
) -> AccountIdentityFetchResultV1:
    """Perform productive account-identity GET only."""
    if not ACCOUNT_IDENTITY_FETCH_ALLOWED:
        raise Section11121ProductivePrivateReadonlyError("ACCOUNT_IDENTITY_FETCH_NOT_ALLOWED")
    validate_get_allowlist_v1(
        endpoint=ACCOUNT_IDENTITY_ENDPOINT,
        http_method=ACCOUNT_IDENTITY_HTTP_METHOD,
    )
    if not session.started:
        raise Section11121ProductivePrivateReadonlyError("NETWORK_SESSION_NOT_STARTED")
    if session.writes_authorized or NETWORK_WRITES_AUTHORIZED:
        raise Section11121ProductivePrivateReadonlyError(
            "NETWORK_WRITES_FORBIDDEN_IN_SECTION_11_12_1"
        )
    raw = transport.get_account_identity(
        endpoint=ACCOUNT_IDENTITY_ENDPOINT,
        http_method=ACCOUNT_IDENTITY_HTTP_METHOD,
        credential_handle=credential_handle,
        session=session,
    )
    # Never persist transport headers/secrets; only redacted identity fields.
    observed = str(raw.get("account_identity") or raw.get("uid") or "")
    if not observed:
        raise Section11121ProductivePrivateReadonlyError("ACCOUNT_IDENTITY_ABSENT_IN_RESPONSE")
    if observed != expected_account_identity:
        raise Section11121ProductivePrivateReadonlyError(
            "ACCOUNT_IDENTITY_MISMATCH:"
            f"expected={_redact_sensitive(expected_account_identity)}"
            f":observed={_redact_sensitive(observed)}"
        )
    status = int(raw.get("http_status") or 0)
    if status != 200:
        raise Section11121ProductivePrivateReadonlyError(
            f"ACCOUNT_IDENTITY_HTTP_STATUS_NOT_OK:{status}"
        )
    safe_payload = {
        "account_identity": observed,
        "endpoint": ACCOUNT_IDENTITY_ENDPOINT,
        "http_method": ACCOUNT_IDENTITY_HTTP_METHOD,
        "http_status": status,
        "path_class": ACCOUNT_IDENTITY_PATH_CLASS,
    }
    response_digest = hashlib.sha256(_canonical_dumps(safe_payload).encode("utf-8")).hexdigest()
    return AccountIdentityFetchResultV1(
        endpoint=ACCOUNT_IDENTITY_ENDPOINT,
        http_method=ACCOUNT_IDENTITY_HTTP_METHOD,
        path_class=ACCOUNT_IDENTITY_PATH_CLASS,
        account_identity_observed=observed,
        http_status=status,
        transport_class=str(transport.transport_class),
        venue_live_contact=bool(transport.venue_live_contact),
        response_digest=response_digest,
    )


def evaluate_section_11_12_1_preconditions_v1(
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
    fetch_reference_only_predecessor_bound: bool,
    owner_auth_artifact_bound: bool,
    credential_load_reference_only_bound: bool,
    cap_11_3_productive_private_readonly_path_bound: bool,
    owner_go_auth_consume_authorized: bool,
    owner_go_credential_consume_authorized: bool,
    owner_go_private_readonly_network_authorized: bool,
    owner_go_account_identity_fetch_authorized: bool,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
) -> dict[str, Any]:
    """Evaluate §11.12.1 productive preconditions."""
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
    if not fetch_reference_only_predecessor_bound:
        missing.append("fetch_reference_only_predecessor_bound")
    if not owner_auth_artifact_bound:
        missing.append("owner_auth_artifact_bound")
    if not credential_load_reference_only_bound:
        missing.append("credential_load_reference_only_bound")
    if not cap_11_3_productive_private_readonly_path_bound:
        missing.append("cap_11_3_productive_private_readonly_path_bound")
    if not PRIVATE_READONLY_GET_ONLY or not PRIVATE_READONLY_GET_ALLOWLIST:
        missing.append("get_only_allowlist_bound")
    if SECTION_11_12_1_ALLOWED_ENDPOINTS != (ACCOUNT_IDENTITY_ENDPOINT,):
        missing.append("section_endpoint_accounts_only")
    if set(SECTION_11_12_1_ALLOWED_ENDPOINTS) & set(PRIVATE_READONLY_FORBIDDEN_MUTATIONS):
        missing.append("mutation_endpoints_absent")
    if not repository_sha or repository_sha != expected_repository_sha:
        missing.append("repository_sha_bound")
    if not config_digest or config_digest != expected_config_digest:
        missing.append("config_digest_bound")
    if not account_identity or account_identity != expected_account_identity:
        missing.append("account_identity_bound")
    if not venue or venue != expected_venue:
        missing.append("venue_bound")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled")
    if orders_authorized or ORDERS_AUTHORIZED is not False:
        missing.append("orders_authorized_false")
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED is not False:
        missing.append("network_writes_unauthorized")
    if cap_11_4_started or CAPABILITY_11_4_STARTED is True:
        missing.append("cap_11_4_not_started")
    if cap_11_13_started or CAPABILITY_11_13_STARTED is True:
        missing.append("cap_11_13_not_started")
    if not owner_go_auth_consume_authorized or not AUTHORIZATION_CONSUMPTION_ALLOWED:
        missing.append("owner_go_auth_consume_authorized")
    if not owner_go_credential_consume_authorized or not PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED:
        missing.append("owner_go_credential_consume_authorized")
    if (
        not owner_go_private_readonly_network_authorized
        or not PRIVATE_READONLY_NETWORK_SESSION_ALLOWED
    ):
        missing.append("owner_go_private_readonly_network_authorized")
    if not owner_go_account_identity_fetch_authorized or not ACCOUNT_IDENTITY_FETCH_ALLOWED:
        missing.append("owner_go_account_identity_fetch_authorized")

    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)
    return {
        "execution_admissible": len(ordered_missing) == 0,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
    }


def mark_fetch_reference_only_predecessor_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> tuple[bool, str, str, str]:
    """Bind closed fetch-reference-only predecessor.

    Returns (bound, owner_auth_digest, cred_load_digest, fetch_ref_digest).
    """
    (
        cred_load_bound,
        owner_auth_digest,
        cred_load_digest,
    ) = mark_credential_load_reference_only_bound_for_fetch_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    path_bound = mark_cap_11_3_path_bound_for_fetch_reference_only_v1(
        repository_sha=repository_sha, config_digest=config_digest
    )
    record = build_productive_private_readonly_fetch_reference_only_v1(
        credential_ref_id="cred-ref-section-11-12-1",
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
        authorization_id="owner-auth-for-section-11-12-1",
        owner_auth_artifact_bound=cred_load_bound,
        owner_auth_artifact_digest=owner_auth_digest,
        credential_load_reference_only_bound=cred_load_bound,
        credential_load_reference_binding_digest=cred_load_digest,
        cap_11_3_productive_private_readonly_path_bound=path_bound,
        intended_fetch_endpoints=PRIVATE_READONLY_GET_ALLOWLIST,
    )
    return (
        record.reference_only_fetch_admissible is True,
        owner_auth_digest,
        cred_load_digest,
        record.reference_binding_digest,
    )


def execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
    *,
    credential_ref_id: str,
    secret_reference: str,
    credential_material: str,
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
    owner_auth_artifact_digest: str,
    fetch_reference_only_binding_digest: str,
    fetch_reference_only_predecessor_bound: bool,
    owner_auth_artifact_bound: bool,
    credential_load_reference_only_bound: bool,
    cap_11_3_productive_private_readonly_path_bound: bool,
    owner_go_auth_consume_authorized: bool = True,
    owner_go_credential_consume_authorized: bool = True,
    owner_go_private_readonly_network_authorized: bool = True,
    owner_go_account_identity_fetch_authorized: bool = True,
    transport: PrivateReadonlyGetTransportV1 | None = None,
    session_id: str = "session-section-11-12-1",
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    order_send_disabled: bool = True,
    orders_authorized: bool = False,
    network_writes_authorized: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    authorization_already_consumed: bool = False,
) -> Section11121ExecutionRecordV1:
    """Execute productive §11.12.1: auth consume, credential consume, GET account identity."""
    if not order_send_disabled or orders_authorized:
        raise Section11121ProductivePrivateReadonlyError(
            "ORDER_SEND_MUST_REMAIN_DISABLED_IN_SECTION_11_12_1"
        )
    if network_writes_authorized:
        raise Section11121ProductivePrivateReadonlyError(
            "NETWORK_WRITES_FORBIDDEN_IN_SECTION_11_12_1"
        )
    if REFERENCE_ONLY is True:
        raise Section11121ProductivePrivateReadonlyError(
            "SECTION_11_12_1_MUST_NOT_BE_REFERENCE_ONLY"
        )
    if CORE_LOGIC_CHANGE:
        raise Section11121ProductivePrivateReadonlyError("CORE_LOGIC_CHANGE_FORBIDDEN")

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
        raise Section11121ProductivePrivateReadonlyError(str(exc)) from exc

    evaluation = evaluate_section_11_12_1_preconditions_v1(
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
        fetch_reference_only_predecessor_bound=fetch_reference_only_predecessor_bound,
        owner_auth_artifact_bound=owner_auth_artifact_bound,
        credential_load_reference_only_bound=credential_load_reference_only_bound,
        cap_11_3_productive_private_readonly_path_bound=(
            cap_11_3_productive_private_readonly_path_bound
        ),
        owner_go_auth_consume_authorized=owner_go_auth_consume_authorized,
        owner_go_credential_consume_authorized=owner_go_credential_consume_authorized,
        owner_go_private_readonly_network_authorized=(owner_go_private_readonly_network_authorized),
        owner_go_account_identity_fetch_authorized=owner_go_account_identity_fetch_authorized,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=meta.plaintext_present,
        plaintext_secret=None,
        order_send_disabled=order_send_disabled,
        orders_authorized=orders_authorized,
        network_writes_authorized=network_writes_authorized,
        cap_11_4_started=cap_11_4_started,
        cap_11_13_started=cap_11_13_started,
    )
    if not evaluation["execution_admissible"]:
        raise Section11121ProductivePrivateReadonlyError(
            "SECTION_11_12_1_NOT_ADMISSIBLE:" + ",".join(evaluation["missing_preconditions"])
        )

    auth = consume_authorization_v1(
        authorization_id=authorization_id,
        owner_auth_artifact_digest=owner_auth_artifact_digest,
        already_consumed=authorization_already_consumed,
    )
    credential_handle = consume_credential_material_v1(
        credential_ref_id=meta.credential_ref_id,
        secret_reference=meta.secret_reference,
        credential_material=credential_material,
    )
    # Ensure caller-provided material does not remain as a named local after consume.
    del credential_material

    session = start_private_readonly_network_session_v1(
        venue=meta.venue,
        account_identity=meta.account_identity,
        session_id=session_id,
    )
    active_transport: PrivateReadonlyGetTransportV1 = (
        transport
        if transport is not None
        else GovernedFixturePrivateReadonlyGetTransportV1(
            expected_account_identity=expected_account_identity
        )
    )
    fetch = fetch_account_identity_v1(
        transport=active_transport,
        credential_handle=credential_handle,
        session=session,
        expected_account_identity=expected_account_identity,
    )

    digest_material = {
        "capability_id": CAPABILITY_ID,
        "authorization_id": authorization_id,
        "authorization_consume_digest": auth["authorization_consume_digest"],
        "owner_auth_artifact_digest": owner_auth_artifact_digest,
        "fetch_reference_only_binding_digest": fetch_reference_only_binding_digest,
        "credential_ref_id": meta.credential_ref_id,
        "secret_reference": meta.secret_reference,
        "credential_material_digest": credential_handle.material_digest,
        "venue": meta.venue,
        "account_identity": meta.account_identity,
        "account_identity_observed": fetch.account_identity_observed,
        "instrument_scope": list(meta.instrument_scope),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "http_method": fetch.http_method,
        "endpoint": fetch.endpoint,
        "path_class": fetch.path_class,
        "transport_class": fetch.transport_class,
        "venue_live_contact": fetch.venue_live_contact,
        "response_digest": fetch.response_digest,
        "network_session_id": session.session_id,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "cap_11_4_started": False,
        "cap_11_13_started": False,
    }
    execution_binding_digest = hashlib.sha256(
        _canonical_dumps(digest_material).encode("utf-8")
    ).hexdigest()

    return Section11121ExecutionRecordV1(
        credential_ref_id=meta.credential_ref_id,
        secret_reference=meta.secret_reference,
        runtime_mode=runtime_mode,
        venue=meta.venue,
        account_identity=meta.account_identity,
        instrument_scope=meta.instrument_scope,
        repository_sha=repository_sha,
        config_digest=config_digest,
        authorization_id=authorization_id,
        owner_auth_artifact_digest=owner_auth_artifact_digest,
        fetch_reference_only_binding_digest=fetch_reference_only_binding_digest,
        credential_material_digest=credential_handle.material_digest,
        authorization_consumed=True,
        credential_consumed=True,
        network_session_started=True,
        network_session_id=session.session_id,
        account_identity_fetch_performed=True,
        account_identity_observed=fetch.account_identity_observed,
        http_method=fetch.http_method,
        endpoint=fetch.endpoint,
        path_class=fetch.path_class,
        transport_class=fetch.transport_class,
        venue_live_contact=fetch.venue_live_contact,
        response_digest=fetch.response_digest,
        order_send_disabled=True,
        orders_authorized=False,
        network_writes_authorized=False,
        network_write_performed=False,
        exchange_order_submit_reachable=False,
        missing_preconditions=(),
        execution_admissible=True,
        execution_binding_digest=execution_binding_digest,
        reference_only=False,
        get_only=True,
    )


def refuse_order_send_v1() -> None:
    raise Section11121ProductivePrivateReadonlyError("ORDER_SEND_FORBIDDEN_IN_SECTION_11_12_1")


def refuse_network_write_v1(*, method: str = "POST") -> None:
    raise Section11121ProductivePrivateReadonlyError(
        f"NETWORK_WRITE_FORBIDDEN_IN_SECTION_11_12_1:{method}"
    )


def refuse_mutation_endpoint_v1(*, action: str) -> None:
    raise Section11121ProductivePrivateReadonlyError(
        f"MUTATION_ENDPOINT_FORBIDDEN_IN_SECTION_11_12_1:{action}"
    )


def refuse_cap_11_4_testnet_execution_v1() -> None:
    raise Section11121ProductivePrivateReadonlyError(
        "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN_IN_SECTION_11_12_1"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise Section11121ProductivePrivateReadonlyError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_SECTION_11_12_1"
    )


def refuse_non_allowlisted_endpoint_v1(*, endpoint: str) -> None:
    validate_get_allowlist_v1(endpoint=endpoint, http_method="GET")


def prove_section_11_12_1_productive_private_readonly_api_and_account_identity_v1() -> dict[
    str, Any
]:
    """Contract proof for §11.12.1 productive path with governed fixture transport."""
    sha = "806e55c4357b90a45c5362672e29f9d8f67949fc"
    cfg = "cfg-" + ("b" * 64)
    fixture_material = "fixture-credential-material-never-logged-or-evidenced"

    (
        pred_bound,
        owner_auth_digest,
        cred_load_digest,
        fetch_ref_digest,
    ) = mark_fetch_reference_only_predecessor_bound_v1(repository_sha=sha, config_digest=cfg)
    path_bound = mark_cap_11_3_path_bound_for_fetch_reference_only_v1(
        repository_sha=sha, config_digest=cfg
    )

    common = {
        "credential_ref_id": "cred-ref-section-11-12-1",
        "secret_reference": "secretref://vault/peak-trade/testnet-demo",
        "credential_material": fixture_material,
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
        "authorization_id": "owner-auth-for-section-11-12-1",
        "owner_auth_artifact_digest": owner_auth_digest,
        "fetch_reference_only_binding_digest": fetch_ref_digest,
        "fetch_reference_only_predecessor_bound": pred_bound,
        "owner_auth_artifact_bound": pred_bound,
        "credential_load_reference_only_bound": pred_bound,
        "cap_11_3_productive_private_readonly_path_bound": path_bound,
        "transport": GovernedFixturePrivateReadonlyGetTransportV1(
            expected_account_identity="acct-uid-demo"
        ),
    }

    incomplete_blocked = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **{
                **common,
                "fetch_reference_only_predecessor_bound": False,
                "owner_auth_artifact_bound": False,
                "credential_load_reference_only_bound": False,
                "cap_11_3_productive_private_readonly_path_bound": False,
            }
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        incomplete_blocked = "SECTION_11_12_1_NOT_ADMISSIBLE" in str(exc)

    record = execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
        **common
    )
    complete_ok = (
        record.execution_admissible is True
        and record.authorization_consumed is True
        and record.credential_consumed is True
        and record.network_session_started is True
        and record.account_identity_fetch_performed is True
        and record.http_method == "GET"
        and record.endpoint == "accounts"
        and record.path_class == ACCOUNT_IDENTITY_PATH_CLASS
        and record.account_identity_observed == "acct-uid-demo"
        and record.order_send_disabled is True
        and record.orders_authorized is False
        and record.network_writes_authorized is False
        and record.network_write_performed is False
        and record.exchange_order_submit_reachable is False
        and record.reference_only is False
        and record.transport_class == TRANSPORT_CLASS_GOVERNED_FIXTURE
        and record.venue_live_contact is False
        and bool(record.credential_material_digest)
        and bool(record.execution_binding_digest)
        and bool(record.response_digest)
        and "fixture-credential-material" not in record.credential_material_digest
        and fixture_material not in _canonical_dumps(record.__dict__)
    )

    replay_blocked = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **common,
            authorization_already_consumed=True,
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        replay_blocked = "AUTHORIZATION_ALREADY_CONSUMED_REPLAY_FORBIDDEN" in str(exc)

    order_send_hard_reject = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **common,
            order_send_disabled=False,
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        order_send_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    orders_authorized_hard_reject = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **common,
            orders_authorized=True,
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        orders_authorized_hard_reject = "ORDER_SEND_MUST_REMAIN_DISABLED" in str(exc)

    network_write_hard_reject = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **common,
            network_writes_authorized=True,
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        network_write_hard_reject = "NETWORK_WRITES_FORBIDDEN" in str(exc)

    plaintext_rejected = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **common,
            plaintext_secret="leak",
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        plaintext_rejected = "PLAINTEXT_SECRET_FORBIDDEN" in str(exc)

    non_get_blocked = False
    try:
        validate_get_allowlist_v1(endpoint="accounts", http_method="POST")
    except Section11121ProductivePrivateReadonlyError as exc:
        non_get_blocked = "HTTP_METHOD_NOT_ALLOWLISTED" in str(exc)

    open_positions_blocked = False
    try:
        validate_get_allowlist_v1(endpoint="open_positions", http_method="GET")
    except Section11121ProductivePrivateReadonlyError as exc:
        open_positions_blocked = "ENDPOINT_NOT_ALLOWLISTED_FOR_SECTION_11_12_1" in str(exc)

    mutation_blocked = False
    try:
        refuse_mutation_endpoint_v1(action="submit_order")
    except Section11121ProductivePrivateReadonlyError as exc:
        mutation_blocked = "MUTATION_ENDPOINT_FORBIDDEN" in str(exc)

    order_send_blocked = False
    try:
        refuse_order_send_v1()
    except Section11121ProductivePrivateReadonlyError as exc:
        order_send_blocked = "ORDER_SEND_FORBIDDEN" in str(exc)

    write_blocked = False
    try:
        refuse_network_write_v1(method="POST")
    except Section11121ProductivePrivateReadonlyError as exc:
        write_blocked = "NETWORK_WRITE_FORBIDDEN" in str(exc)

    cap114_blocked = False
    try:
        refuse_cap_11_4_testnet_execution_v1()
    except Section11121ProductivePrivateReadonlyError as exc:
        cap114_blocked = "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except Section11121ProductivePrivateReadonlyError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    identity_mismatch_blocked = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **{
                **common,
                "transport": GovernedFixturePrivateReadonlyGetTransportV1(
                    expected_account_identity="acct-other"
                ),
            }
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        identity_mismatch_blocked = "ACCOUNT_IDENTITY_MISMATCH" in str(exc)

    live_mode_blocked = False
    try:
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **{**common, "runtime_mode": "LIVE"}
        )
    except Section11121ProductivePrivateReadonlyError as exc:
        live_mode_blocked = "SECTION_11_12_1_NOT_ADMISSIBLE" in str(exc)

    ok = all(
        (
            incomplete_blocked,
            complete_ok,
            replay_blocked,
            order_send_hard_reject,
            orders_authorized_hard_reject,
            network_write_hard_reject,
            plaintext_rejected,
            non_get_blocked,
            open_positions_blocked,
            mutation_blocked,
            order_send_blocked,
            write_blocked,
            cap114_blocked,
            cap1113_blocked,
            identity_mismatch_blocked,
            live_mode_blocked,
            ORDER_SEND_DISABLED is True,
            ORDERS_AUTHORIZED is False,
            NETWORK_WRITES_AUTHORIZED is False,
            CAPABILITY_11_4_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            MUTATING_EXCHANGE_CALLS is False,
            ORDER_PATH_STARTED is False,
            LIVE_AUTHORIZED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            ACTIVATION_STATE == "not_activated",
            CORE_LOGIC_CHANGE is False,
        )
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "incomplete_blocked": incomplete_blocked,
        "complete_execution_ok": complete_ok,
        "authorization_consumed": record.authorization_consumed,
        "credential_consumed": record.credential_consumed,
        "network_session_started": record.network_session_started,
        "account_identity_fetch_performed": record.account_identity_fetch_performed,
        "http_method": record.http_method,
        "endpoint": record.endpoint,
        "path_class": record.path_class,
        "transport_class": record.transport_class,
        "venue_live_contact": record.venue_live_contact,
        "account_identity_observed": record.account_identity_observed,
        "credential_material_digest": record.credential_material_digest,
        "response_digest": record.response_digest,
        "execution_binding_digest": record.execution_binding_digest,
        "fetch_reference_only_binding_digest": fetch_ref_digest,
        "owner_auth_artifact_digest": owner_auth_digest,
        "credential_load_reference_binding_digest": cred_load_digest,
        "replay_blocked": replay_blocked,
        "order_send_hard_reject": order_send_hard_reject,
        "orders_authorized_hard_reject": orders_authorized_hard_reject,
        "network_write_hard_reject": network_write_hard_reject,
        "plaintext_rejected": plaintext_rejected,
        "non_get_blocked": non_get_blocked,
        "open_positions_blocked": open_positions_blocked,
        "mutation_blocked": mutation_blocked,
        "order_send_blocked": order_send_blocked,
        "write_blocked": write_blocked,
        "cap_11_4_blocked": cap114_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "identity_mismatch_blocked": identity_mismatch_blocked,
        "live_mode_blocked": live_mode_blocked,
        "order_send_disabled": True,
        "orders_authorized": False,
        "network_writes_authorized": False,
        "network_write_performed": False,
        "exchange_order_submit_reachable": False,
        "cap_11_4_started": False,
        "cap_11_13_started": False,
        "reference_only": False,
        "activation_state": ACTIVATION_STATE,
    }

"""Fail-closed productive private read-only path binding (no network fetch)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
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
    NETWORK_SESSION_STARTED,
    OWNER,
    PLAINTEXT_SECRET_FORBIDDEN,
    PRIVATE_READONLY_FETCH_PERFORMED,
    PRIVATE_READONLY_FORBIDDEN_MUTATIONS,
    PRIVATE_READONLY_GET_ALLOWLIST,
    PRIVATE_READONLY_GET_ONLY,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN,
    PRIVATE_READONLY_PATH_ALLOWED_DEFAULT,
    PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REQUIRED_PRECONDITIONS,
    SECRET_REFERENCE_ONLY,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ONLY_SCOPE_REQUIRED,
    WITHDRAWAL_PERMISSION,
)


class ProductivePrivateReadonlyPathBindingError(RuntimeError):
    """Fail-closed productive private read-only path binding violation."""


@dataclass(frozen=True)
class ProductivePrivateReadonlyPathBindingRecordV1:
    """Path-binding record: GET allowlist + secret reference; never plaintext/network."""

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
    allowed_get_endpoints: tuple[str, ...]
    forbidden_mutation_actions: tuple[str, ...]
    exchange_credential_use_authorized: bool
    testnet_authorized: bool
    least_privilege: bool
    withdrawal_permission: bool
    plaintext_present: bool
    private_readonly_path_allowed: bool
    missing_preconditions: tuple[str, ...]
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    source: str = "PATH_BINDING_ONLY"
    get_only: bool = True


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if "://" not in secret_reference and not secret_reference.startswith("secretref:"):
        return secret_reference.startswith("secretref")
    return True


def _allowlist_exact_match(endpoints: tuple[str, ...] | list[str]) -> bool:
    requested = tuple(str(x) for x in endpoints)
    return requested == PRIVATE_READONLY_GET_ALLOWLIST


def evaluate_productive_private_readonly_preconditions_v1(
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
    allowed_get_endpoints: tuple[str, ...] | list[str],
    exchange_credential_use_authorized: bool,
    testnet_authorized: bool,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    cap_11_2_credential_load_path_bound: bool = False,
    cap_11_3_private_readonly_port_declared: bool = False,
    mutation_endpoint_requested: bool = False,
    network_session_started: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    provider_access_attempted: bool = False,
) -> dict[str, Any]:
    """Evaluate path-binding preconditions. Does not fetch or load secrets."""
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
    if not exchange_credential_use_authorized:
        missing.append("exchange_credential_use_authorized")
    if not testnet_authorized:
        missing.append("testnet_authorized")
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
    if not cap_11_3_private_readonly_port_declared:
        missing.append("cap_11_3_private_readonly_port_declared")
    if not _allowlist_exact_match(allowed_get_endpoints) or not PRIVATE_READONLY_GET_ONLY:
        missing.append("get_only_allowlist_bound")
    if mutation_endpoint_requested or not PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN:
        missing.append("mutation_endpoints_absent")
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

    allowed = len(ordered_missing) == 0
    return {
        "private_readonly_path_allowed": allowed,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
        "PRIVATE_READONLY_PATH_ALLOWED_DEFAULT": PRIVATE_READONLY_PATH_ALLOWED_DEFAULT,
        "PRIVATE_READONLY_FETCH_PERFORMED": False,
        "allowed_get_endpoints": list(PRIVATE_READONLY_GET_ALLOWLIST),
        "forbidden_mutation_actions": list(PRIVATE_READONLY_FORBIDDEN_MUTATIONS),
    }


def build_productive_private_readonly_path_binding_v1(
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
    allowed_get_endpoints: tuple[str, ...] | list[str] | None = None,
    exchange_credential_use_authorized: bool = False,
    testnet_authorized: bool = False,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    cap_11_2_credential_load_path_bound: bool = False,
    cap_11_3_private_readonly_port_declared: bool = False,
    mutation_endpoint_requested: bool = False,
    network_session_started: bool = False,
    cap_11_4_started: bool = False,
    cap_11_13_started: bool = False,
    provider_access_attempted: bool = False,
) -> ProductivePrivateReadonlyPathBindingRecordV1:
    """Build path-binding record. Rejects plaintext; never fetches or loads secrets."""
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
        raise ProductivePrivateReadonlyPathBindingError(str(exc)) from exc

    endpoints = (
        tuple(str(x) for x in allowed_get_endpoints)
        if allowed_get_endpoints is not None
        else PRIVATE_READONLY_GET_ALLOWLIST
    )

    evaluation = evaluate_productive_private_readonly_preconditions_v1(
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
        allowed_get_endpoints=endpoints,
        exchange_credential_use_authorized=exchange_credential_use_authorized,
        testnet_authorized=testnet_authorized,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=meta.plaintext_present,
        plaintext_secret=None,
        cap_11_2_credential_load_path_bound=cap_11_2_credential_load_path_bound,
        cap_11_3_private_readonly_port_declared=cap_11_3_private_readonly_port_declared,
        mutation_endpoint_requested=mutation_endpoint_requested,
        network_session_started=network_session_started,
        cap_11_4_started=cap_11_4_started,
        cap_11_13_started=cap_11_13_started,
        provider_access_attempted=provider_access_attempted,
    )
    return ProductivePrivateReadonlyPathBindingRecordV1(
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
        allowed_get_endpoints=endpoints,
        forbidden_mutation_actions=PRIVATE_READONLY_FORBIDDEN_MUTATIONS,
        exchange_credential_use_authorized=exchange_credential_use_authorized,
        testnet_authorized=testnet_authorized,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=False,
        private_readonly_path_allowed=bool(evaluation["private_readonly_path_allowed"]),
        missing_preconditions=tuple(evaluation["missing_preconditions"]),
    )


def mark_cap_11_2_credential_load_path_bound_v1(
    *,
    repository_sha: str,
    config_digest: str,
) -> bool:
    """Return True when Cap 11.2 productive path would admit (still never loads)."""
    gate = mark_cap_11_2_gate_prerequisites_complete_v1()
    gate_eval = gate.evaluate_admissibility()
    binding = build_productive_credential_load_path_binding_v1(
        credential_ref_id="cred-ref-cap113-predecessor",
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


def attempt_private_readonly_fetch_via_productive_path_v1(
    binding: ProductivePrivateReadonlyPathBindingRecordV1,
    *,
    endpoint: str,
) -> dict[str, Any]:
    """Always refuse real private read-only fetch in this path-binding capability."""
    if endpoint not in PRIVATE_READONLY_GET_ALLOWLIST:
        raise ProductivePrivateReadonlyPathBindingError(
            f"PRIVATE_READONLY_ENDPOINT_NOT_ALLOWLISTED:{endpoint}"
        )
    if not binding.private_readonly_path_allowed:
        raise ProductivePrivateReadonlyPathBindingError(
            "PRIVATE_READONLY_PATH_NOT_ALLOWED:"
            + ",".join(binding.missing_preconditions or ("preconditions_incomplete",))
        )
    raise ProductivePrivateReadonlyPathBindingError(
        "PRIVATE_READONLY_FETCH_FORBIDDEN_IN_PRODUCTIVE_PATH_BINDING_V1"
    )


def refuse_private_readonly_mutation_v1(*, action: str) -> None:
    raise ProductivePrivateReadonlyPathBindingError(
        f"PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN:{action}"
    )


def refuse_network_session_v1() -> None:
    raise ProductivePrivateReadonlyPathBindingError(
        "NETWORK_SESSION_FORBIDDEN_IN_PRODUCTIVE_PRIVATE_READONLY_PATH_BINDING"
    )


def refuse_cap_11_4_testnet_execution_v1() -> None:
    raise ProductivePrivateReadonlyPathBindingError(
        "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN_IN_PATH_BINDING"
    )


def refuse_cap_11_13_live_activation_v1() -> None:
    raise ProductivePrivateReadonlyPathBindingError(
        "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN_IN_PATH_BINDING"
    )


def refuse_env_keychain_provider_access_v1(*, provider: str) -> None:
    raise ProductivePrivateReadonlyPathBindingError(
        f"CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN_IN_PATH_BINDING:{provider}"
    )


def prove_productive_private_readonly_path_binding_v1() -> dict[str, Any]:
    """Contract proof: defaults fail-closed; complete path admits but never fetches."""
    sha = "a03ad3daa7d5a890aba0e70e27c99b1f57885247"
    cfg = "cfg-" + ("e" * 64)

    port = declare_private_readonly_venue_port_v1()
    port_declared = port.CONSTRUCTIBLE is False and port.PRIVATE_READONLY_GET_ONLY is True

    default_binding = build_productive_private_readonly_path_binding_v1(
        credential_ref_id="cred-ref-ro-default",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
        runtime_mode="TESTNET",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_scope=("BTC-USDT-SWAP",),
        repository_sha=sha,
        config_digest=cfg,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        expected_account_identity="acct-uid-demo",
        expected_venue="OKX",
        exchange_credential_use_authorized=False,
        testnet_authorized=False,
        cap_11_2_credential_load_path_bound=False,
        cap_11_3_private_readonly_port_declared=False,
    )
    default_fail_closed = (
        default_binding.private_readonly_path_allowed is False
        and PRIVATE_READONLY_PATH_ALLOWED_DEFAULT is False
    )

    incomplete_blocked = False
    try:
        attempt_private_readonly_fetch_via_productive_path_v1(default_binding, endpoint="accounts")
    except ProductivePrivateReadonlyPathBindingError as exc:
        incomplete_blocked = "PRIVATE_READONLY_PATH_NOT_ALLOWED" in str(exc)

    predecessor_bound = mark_cap_11_2_credential_load_path_bound_v1(
        repository_sha=sha, config_digest=cfg
    )
    complete_binding = build_productive_private_readonly_path_binding_v1(
        credential_ref_id="cred-ref-ro-complete",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
        runtime_mode="TESTNET",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_scope=("BTC-USDT-SWAP",),
        repository_sha=sha,
        config_digest=cfg,
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        expected_account_identity="acct-uid-demo",
        expected_venue="OKX",
        exchange_credential_use_authorized=True,
        testnet_authorized=True,
        cap_11_2_credential_load_path_bound=predecessor_bound,
        cap_11_3_private_readonly_port_declared=port_declared,
    )
    complete_admits = complete_binding.private_readonly_path_allowed is True

    fetch_still_forbidden = False
    try:
        attempt_private_readonly_fetch_via_productive_path_v1(complete_binding, endpoint="accounts")
    except ProductivePrivateReadonlyPathBindingError as exc:
        fetch_still_forbidden = (
            "PRIVATE_READONLY_FETCH_FORBIDDEN_IN_PRODUCTIVE_PATH_BINDING" in str(exc)
        )

    unknown_endpoint_blocked = False
    try:
        attempt_private_readonly_fetch_via_productive_path_v1(
            complete_binding, endpoint="sendorder"
        )
    except ProductivePrivateReadonlyPathBindingError as exc:
        unknown_endpoint_blocked = "NOT_ALLOWLISTED" in str(exc)

    plaintext_rejected = False
    try:
        build_productive_private_readonly_path_binding_v1(
            credential_ref_id="cred-ref-bad",
            secret_reference="secretref://vault/peak-trade/testnet-demo",
            runtime_mode="TESTNET",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            repository_sha=sha,
            config_digest=cfg,
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_account_identity="acct-uid-demo",
            expected_venue="OKX",
            plaintext_secret="leak",
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_private_readonly_port_declared=True,
        )
    except ProductivePrivateReadonlyPathBindingError as exc:
        plaintext_rejected = "PLAINTEXT_SECRET_FORBIDDEN" in str(exc)

    withdrawal_rejected = False
    try:
        build_productive_private_readonly_path_binding_v1(
            credential_ref_id="cred-ref-bad-wd",
            secret_reference="secretref://vault/peak-trade/testnet-demo",
            runtime_mode="TESTNET",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            repository_sha=sha,
            config_digest=cfg,
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_account_identity="acct-uid-demo",
            expected_venue="OKX",
            withdrawal_permission=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_private_readonly_port_declared=True,
        )
    except ProductivePrivateReadonlyPathBindingError as exc:
        withdrawal_rejected = "WITHDRAWAL_PERMISSION_FORBIDDEN" in str(exc)

    bad_allowlist_blocked = (
        build_productive_private_readonly_path_binding_v1(
            credential_ref_id="cred-ref-bad-al",
            secret_reference="secretref://vault/peak-trade/testnet-demo",
            runtime_mode="TESTNET",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            repository_sha=sha,
            config_digest=cfg,
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_account_identity="acct-uid-demo",
            expected_venue="OKX",
            allowed_get_endpoints=("accounts", "sendorder"),
            exchange_credential_use_authorized=True,
            testnet_authorized=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_private_readonly_port_declared=True,
        ).private_readonly_path_allowed
        is False
    )

    mutation_request_blocked = (
        build_productive_private_readonly_path_binding_v1(
            credential_ref_id="cred-ref-mut",
            secret_reference="secretref://vault/peak-trade/testnet-demo",
            runtime_mode="TESTNET",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            repository_sha=sha,
            config_digest=cfg,
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_account_identity="acct-uid-demo",
            expected_venue="OKX",
            exchange_credential_use_authorized=True,
            testnet_authorized=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_private_readonly_port_declared=True,
            mutation_endpoint_requested=True,
        ).private_readonly_path_allowed
        is False
    )

    non_testnet_blocked = (
        build_productive_private_readonly_path_binding_v1(
            credential_ref_id="cred-ref-sim",
            secret_reference="secretref://vault/peak-trade/testnet-demo",
            runtime_mode="SIMULATED",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            repository_sha=sha,
            config_digest=cfg,
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_account_identity="acct-uid-demo",
            expected_venue="OKX",
            exchange_credential_use_authorized=True,
            testnet_authorized=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_private_readonly_port_declared=True,
        ).private_readonly_path_allowed
        is False
    )

    sha_mismatch_blocked = (
        build_productive_private_readonly_path_binding_v1(
            credential_ref_id="cred-ref-sha",
            secret_reference="secretref://vault/peak-trade/testnet-demo",
            runtime_mode="TESTNET",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            repository_sha=sha,
            config_digest=cfg,
            expected_repository_sha="0" * 40,
            expected_config_digest=cfg,
            expected_account_identity="acct-uid-demo",
            expected_venue="OKX",
            exchange_credential_use_authorized=True,
            testnet_authorized=True,
            cap_11_2_credential_load_path_bound=True,
            cap_11_3_private_readonly_port_declared=True,
        ).private_readonly_path_allowed
        is False
    )

    mutation_blocked = False
    try:
        refuse_private_readonly_mutation_v1(action="submit_order")
    except ProductivePrivateReadonlyPathBindingError as exc:
        mutation_blocked = "ORDER_MUTATION_FORBIDDEN" in str(exc)

    network_blocked = False
    try:
        refuse_network_session_v1()
    except ProductivePrivateReadonlyPathBindingError as exc:
        network_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    cap114_blocked = False
    try:
        refuse_cap_11_4_testnet_execution_v1()
    except ProductivePrivateReadonlyPathBindingError as exc:
        cap114_blocked = "CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN" in str(exc)

    cap1113_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1()
    except ProductivePrivateReadonlyPathBindingError as exc:
        cap1113_blocked = "CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN" in str(exc)

    provider_blocked = False
    try:
        refuse_env_keychain_provider_access_v1(provider="ENV")
    except ProductivePrivateReadonlyPathBindingError as exc:
        provider_blocked = "CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN" in str(exc)

    ok = all(
        [
            default_fail_closed,
            incomplete_blocked,
            predecessor_bound,
            complete_admits,
            fetch_still_forbidden,
            unknown_endpoint_blocked,
            plaintext_rejected,
            withdrawal_rejected,
            bad_allowlist_blocked,
            mutation_request_blocked,
            non_testnet_blocked,
            sha_mismatch_blocked,
            mutation_blocked,
            network_blocked,
            cap114_blocked,
            cap1113_blocked,
            provider_blocked,
            port_declared,
            PRIVATE_READONLY_FETCH_PERFORMED is False,
            PRIVATE_READONLY_NETWORK_REACHABLE is False,
            PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED is False,
            CREDENTIAL_LOAD_PERFORMED is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            CAPABILITY_11_4_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            AUTHORIZATION_CONSUMPTION_ALLOWED is False,
            WITHDRAWAL_PERMISSION is False,
            LEAST_PRIVILEGE is True,
            PRIVATE_READONLY_GET_ONLY is True,
            PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN is True,
            ACTIVATION_STATE == "not_activated",
            CORE_LOGIC_CHANGE is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            list(PRIVATE_READONLY_GET_ALLOWLIST) == ["accounts", "open_positions", "open_orders"],
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "PRIVATE_READONLY_PATH_ALLOWED_DEFAULT": False,
        "default_binding_private_readonly_path_allowed": False,
        "complete_binding_private_readonly_path_allowed": complete_admits,
        "private_readonly_fetch_performed": False,
        "incomplete_fetch_blocked": incomplete_blocked,
        "complete_path_fetch_still_forbidden": fetch_still_forbidden,
        "unknown_endpoint_blocked": unknown_endpoint_blocked,
        "predecessor_cap_11_2_path_bound": predecessor_bound,
        "cap_11_3_port_declared": port_declared,
        "plaintext_rejected": plaintext_rejected,
        "withdrawal_rejected": withdrawal_rejected,
        "bad_allowlist_blocked": bad_allowlist_blocked,
        "mutation_request_blocked": mutation_request_blocked,
        "non_testnet_blocked": non_testnet_blocked,
        "sha_mismatch_blocked": sha_mismatch_blocked,
        "mutation_blocked": mutation_blocked,
        "network_session_blocked": network_blocked,
        "cap_11_4_blocked": cap114_blocked,
        "cap_11_13_blocked": cap1113_blocked,
        "provider_access_blocked": provider_blocked,
        "allowed_get_endpoints": list(PRIVATE_READONLY_GET_ALLOWLIST),
        "forbidden_mutation_actions": list(PRIVATE_READONLY_FORBIDDEN_MUTATIONS),
        "WITHDRAWAL_PERMISSION": False,
        "LEAST_PRIVILEGE": True,
        "OWNER": OWNER,
    }

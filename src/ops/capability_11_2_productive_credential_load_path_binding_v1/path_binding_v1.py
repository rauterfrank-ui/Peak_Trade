"""Fail-closed productive credential-load path binding (no secret materialization)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    CREDENTIAL_LOAD_PREREQUISITES,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_contract_v1 import (
    CredentialContractViolationError,
    build_credential_reference_metadata_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_load_gate_v1 import (
    CredentialLoadGateError,
    CredentialLoadGateV1,
)
from src.ops.capability_11_2_productive_credential_load_path_binding_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_11_3_PRIVATE_READONLY_STARTED,
    CAPABILITY_11_3_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_ALLOWED_DEFAULT,
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
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REQUIRED_PRECONDITIONS,
    SECRET_REFERENCE_ONLY,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ONLY_SCOPE_REQUIRED,
    WITHDRAWAL_PERMISSION,
)


class ProductiveCredentialLoadPathBindingError(RuntimeError):
    """Fail-closed productive credential-load path binding violation."""


@dataclass(frozen=True)
class ProductiveCredentialLoadPathBindingRecordV1:
    """Path-binding record: secret reference + scope only; never plaintext."""

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
    exchange_credential_use_authorized: bool
    testnet_authorized: bool
    least_privilege: bool
    withdrawal_permission: bool
    plaintext_present: bool
    credential_load_allowed: bool
    missing_preconditions: tuple[str, ...]
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    source: str = "PATH_BINDING_ONLY"


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if "://" not in secret_reference and not secret_reference.startswith("secretref:"):
        # Allow vault-style refs and secretref:// forms only.
        return secret_reference.startswith("secretref")
    return True


def evaluate_productive_credential_load_preconditions_v1(
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
    exchange_credential_use_authorized: bool,
    testnet_authorized: bool,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    cap_11_2_gate_prerequisites_satisfied: bool = False,
    cap_11_3_started: bool = False,
    network_session_started: bool = False,
    provider_access_attempted: bool = False,
) -> dict[str, Any]:
    """Evaluate path-binding preconditions. Does not load secrets."""
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
    if not cap_11_2_gate_prerequisites_satisfied:
        missing.append("cap_11_2_load_gate_prerequisites")
    if cap_11_3_started or CAPABILITY_11_3_STARTED is True:
        missing.append("cap_11_3_not_started")
    if network_session_started or NETWORK_SESSION_STARTED is True:
        missing.append("network_session_not_started")
    if provider_access_attempted:
        missing.append("no_plaintext_provider_access")

    # Preserve deterministic ordering against required precondition names.
    ordered_missing = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    # Include any unexpected missing labels last.
    for name in missing:
        if name not in ordered_missing:
            ordered_missing = (*ordered_missing, name)

    allowed = len(ordered_missing) == 0
    return {
        "credential_load_allowed": allowed,
        "missing_preconditions": list(ordered_missing),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
        "CREDENTIAL_LOAD_ALLOWED_DEFAULT": CREDENTIAL_LOAD_ALLOWED_DEFAULT,
        "CREDENTIAL_LOAD_PERFORMED": False,
    }


def build_productive_credential_load_path_binding_v1(
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
    exchange_credential_use_authorized: bool = False,
    testnet_authorized: bool = False,
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
    cap_11_2_gate_prerequisites_satisfied: bool = False,
    cap_11_3_started: bool = False,
    network_session_started: bool = False,
    provider_access_attempted: bool = False,
) -> ProductiveCredentialLoadPathBindingRecordV1:
    """Build path-binding record. Rejects plaintext; never loads secrets."""
    # Reuse Cap 11.2 reference-metadata contract for secret-reference safety.
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
        raise ProductiveCredentialLoadPathBindingError(str(exc)) from exc

    evaluation = evaluate_productive_credential_load_preconditions_v1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=meta.instrument_scope,
        secret_reference=meta.secret_reference,
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_account_identity=expected_account_identity,
        expected_venue=expected_venue,
        exchange_credential_use_authorized=exchange_credential_use_authorized,
        testnet_authorized=testnet_authorized,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=meta.plaintext_present,
        plaintext_secret=None,
        cap_11_2_gate_prerequisites_satisfied=cap_11_2_gate_prerequisites_satisfied,
        cap_11_3_started=cap_11_3_started,
        network_session_started=network_session_started,
        provider_access_attempted=provider_access_attempted,
    )
    return ProductiveCredentialLoadPathBindingRecordV1(
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
        exchange_credential_use_authorized=exchange_credential_use_authorized,
        testnet_authorized=testnet_authorized,
        least_privilege=meta.least_privilege,
        withdrawal_permission=meta.withdrawal_permission,
        plaintext_present=False,
        credential_load_allowed=bool(evaluation["credential_load_allowed"]),
        missing_preconditions=tuple(evaluation["missing_preconditions"]),
    )


def mark_cap_11_2_gate_prerequisites_complete_v1() -> CredentialLoadGateV1:
    """Return a Cap 11.2 gate with all ordered prerequisites marked (still no load)."""
    gate = CredentialLoadGateV1()
    for name in CREDENTIAL_LOAD_PREREQUISITES:
        gate.mark_prerequisite(name, satisfied=True)
    return gate


def attempt_credential_load_via_productive_path_v1(
    binding: ProductiveCredentialLoadPathBindingRecordV1,
) -> dict[str, Any]:
    """Always refuse real credential load in this path-binding capability."""
    if not binding.credential_load_allowed:
        raise ProductiveCredentialLoadPathBindingError(
            "CREDENTIAL_LOAD_NOT_ALLOWED:"
            + ",".join(binding.missing_preconditions or ("preconditions_incomplete",))
        )
    # Even when path is admissible, this capability never materializes secrets.
    raise ProductiveCredentialLoadPathBindingError(
        "CREDENTIAL_LOAD_FORBIDDEN_IN_PRODUCTIVE_PATH_BINDING_V1"
    )


def refuse_cap_11_3_private_readonly_construction_v1() -> None:
    raise ProductiveCredentialLoadPathBindingError(
        "CAPABILITY_11_3_PRIVATE_READONLY_CONSTRUCTION_FORBIDDEN_IN_PATH_BINDING"
    )


def refuse_network_session_v1() -> None:
    raise ProductiveCredentialLoadPathBindingError(
        "NETWORK_SESSION_FORBIDDEN_IN_PRODUCTIVE_CREDENTIAL_LOAD_PATH_BINDING"
    )


def refuse_env_keychain_provider_access_v1(*, provider: str) -> None:
    raise ProductiveCredentialLoadPathBindingError(
        f"CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN_IN_PATH_BINDING:{provider}"
    )


def prove_productive_credential_load_path_binding_v1() -> dict[str, Any]:
    """Contract proof: defaults fail-closed; complete path admits but never loads."""
    sha = "5e4b71268a5cbb969a97b1522750b53cfb01c556"
    cfg = "cfg-" + ("d" * 64)

    default_binding = build_productive_credential_load_path_binding_v1(
        credential_ref_id="cred-ref-path-default",
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
        # Defaults: no explicit auth → fail-closed.
        exchange_credential_use_authorized=False,
        testnet_authorized=False,
        cap_11_2_gate_prerequisites_satisfied=False,
    )
    default_fail_closed = (
        default_binding.credential_load_allowed is False
        and CREDENTIAL_LOAD_ALLOWED_DEFAULT is False
    )

    incomplete_blocked = False
    try:
        attempt_credential_load_via_productive_path_v1(default_binding)
    except ProductiveCredentialLoadPathBindingError as exc:
        incomplete_blocked = "CREDENTIAL_LOAD_NOT_ALLOWED" in str(exc)

    gate = mark_cap_11_2_gate_prerequisites_complete_v1()
    gate_eval = gate.evaluate_admissibility()
    complete_binding = build_productive_credential_load_path_binding_v1(
        credential_ref_id="cred-ref-path-complete",
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
        cap_11_2_gate_prerequisites_satisfied=gate_eval.get("admissible_for_future_load") is True,
    )
    complete_admits = complete_binding.credential_load_allowed is True

    load_still_forbidden = False
    try:
        attempt_credential_load_via_productive_path_v1(complete_binding)
    except ProductiveCredentialLoadPathBindingError as exc:
        load_still_forbidden = "CREDENTIAL_LOAD_FORBIDDEN_IN_PRODUCTIVE_PATH_BINDING" in str(exc)

    # Cap 11.2 gate itself still refuses load.
    predecessor_gate_blocks = False
    try:
        gate.attempt_credential_load_v1()
    except CredentialLoadGateError as exc:
        predecessor_gate_blocks = "CREDENTIAL_LOAD_FORBIDDEN_IN_CAPABILITY_11_2" in str(exc)

    plaintext_rejected = False
    try:
        build_productive_credential_load_path_binding_v1(
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
        )
    except ProductiveCredentialLoadPathBindingError as exc:
        plaintext_rejected = "PLAINTEXT_SECRET_FORBIDDEN" in str(exc)

    withdrawal_rejected = False
    try:
        build_productive_credential_load_path_binding_v1(
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
        )
    except ProductiveCredentialLoadPathBindingError as exc:
        withdrawal_rejected = "WITHDRAWAL_PERMISSION_FORBIDDEN" in str(exc)

    non_testnet_blocked = (
        build_productive_credential_load_path_binding_v1(
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
            cap_11_2_gate_prerequisites_satisfied=True,
        ).credential_load_allowed
        is False
    )

    sha_mismatch_blocked = (
        build_productive_credential_load_path_binding_v1(
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
            cap_11_2_gate_prerequisites_satisfied=True,
        ).credential_load_allowed
        is False
    )

    cap113_blocked = False
    try:
        refuse_cap_11_3_private_readonly_construction_v1()
    except ProductiveCredentialLoadPathBindingError as exc:
        cap113_blocked = "CAPABILITY_11_3_PRIVATE_READONLY_CONSTRUCTION_FORBIDDEN" in str(exc)

    network_blocked = False
    try:
        refuse_network_session_v1()
    except ProductiveCredentialLoadPathBindingError as exc:
        network_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    provider_blocked = False
    try:
        refuse_env_keychain_provider_access_v1(provider="ENV")
    except ProductiveCredentialLoadPathBindingError as exc:
        provider_blocked = "CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN" in str(exc)

    ok = all(
        [
            default_fail_closed,
            incomplete_blocked,
            complete_admits,
            load_still_forbidden,
            predecessor_gate_blocks,
            plaintext_rejected,
            withdrawal_rejected,
            non_testnet_blocked,
            sha_mismatch_blocked,
            cap113_blocked,
            network_blocked,
            provider_blocked,
            CREDENTIAL_LOAD_PERFORMED is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            CAPABILITY_11_3_STARTED is False,
            CAPABILITY_11_3_PRIVATE_READONLY_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            AUTHORIZATION_CONSUMPTION_ALLOWED is False,
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
        "CREDENTIAL_LOAD_ALLOWED_DEFAULT": False,
        "default_binding_credential_load_allowed": False,
        "complete_binding_credential_load_allowed": complete_admits,
        "credential_load_performed": False,
        "incomplete_load_blocked": incomplete_blocked,
        "complete_path_load_still_forbidden": load_still_forbidden,
        "predecessor_cap_11_2_gate_blocks_load": predecessor_gate_blocks,
        "plaintext_rejected": plaintext_rejected,
        "withdrawal_rejected": withdrawal_rejected,
        "non_testnet_blocked": non_testnet_blocked,
        "sha_mismatch_blocked": sha_mismatch_blocked,
        "cap_11_3_construction_blocked": cap113_blocked,
        "network_session_blocked": network_blocked,
        "provider_access_blocked": provider_blocked,
        "WITHDRAWAL_PERMISSION": False,
        "LEAST_PRIVILEGE": True,
        "OWNER": OWNER,
    }

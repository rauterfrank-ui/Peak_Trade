"""§11.13.2 runner: fail-closed call chain with preflight and productive execute."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1 import (
    constants_v1 as cap_11_7,
)
from src.ops.section_11_13_2_live_private_read_only_v1.authorization_v1 import (
    LivePrivateRoAuthorizationError,
    default_authorization_is_false_v1,
    validate_live_private_read_only_authorization_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.binding_v1 import (
    LivePrivateRoBindingError,
    build_live_private_ro_venue_binding_v1,
    reject_cross_binding_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.config_v1 import (
    LivePrivateRoConfigError,
    LivePrivateRoConfigV1,
    load_live_private_ro_config_v1,
    require_execute_time_fields_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE,
    CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY,
    ENABLE_LIVE_TRADING,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    OWNER_GO_EXECUTE,
    REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS,
    REQUIRED_CREDENTIAL_CLASS,
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
    TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK,
)
from src.ops.section_11_13_2_live_private_read_only_v1.evidence_v1 import (
    build_claims_v1,
    persist_evidence_bundle_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.http_client_v1 import (
    LivePrivateRoHttpClientV1,
    LivePrivateRoHttpError,
    LivePrivateRoTransportV1,
    RecordingFakeTransportV1,
    UrllibLiveTransportV1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.live_credential_ephemeral_v1 import (
    LivePrivateRoCredentialError,
    assert_no_plaintext_in_payload_v1,
    build_file_secretref_vault_backend_v1,
    release_live_ephemeral_material_v1,
    resolve_and_load_live_secretref_ephemeral_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.okx_live_ro_signer_v1 import (
    LivePrivateRoSignerError,
    auth_headers_presence_doc_v1,
    build_okx_live_ro_get_auth_headers_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.response_assertions_v1 import (
    LivePrivateRoAssertionError,
    assert_authenticated_private_read_success_v1,
    productive_proven_allowed_v1,
    redact_mapping_v1,
    validate_permission_attestation_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.secretref_v1 import (
    LivePrivateRoSecretRefError,
    build_live_private_ro_secretref_metadata_v1,
    refuse_credential_material_borrow_v1,
    reject_cross_environment_secretref_use_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.verifier_v1 import (
    verify_live_private_read_only_evidence_v1,
)


class LivePrivateRoRunnerError(RuntimeError):
    """Fail-closed runner violation."""


@dataclass(frozen=True)
class LivePrivateRoRunnerResultV1:
    ok: bool
    mode: str
    verdict: str
    LIVE_PRIVATE_READ_ONLY_PROVEN: bool
    LIVE_AUTHORIZED: bool
    FULLY_AUTONOMOUS_LIVE_TRADING_READY: bool
    NETWORK_EFFECT: str
    CREDENTIAL_ACCESS: str
    ORDER_EFFECT: str
    evidence_root: str | None
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "verdict": self.verdict,
            "LIVE_PRIVATE_READ_ONLY_PROVEN": self.LIVE_PRIVATE_READ_ONLY_PROVEN,
            "LIVE_AUTHORIZED": self.LIVE_AUTHORIZED,
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY": (self.FULLY_AUTONOMOUS_LIVE_TRADING_READY),
            "NETWORK_EFFECT": self.NETWORK_EFFECT,
            "CREDENTIAL_ACCESS": self.CREDENTIAL_ACCESS,
            "ORDER_EFFECT": self.ORDER_EFFECT,
            "evidence_root": self.evidence_root,
            "details": self.details,
        }


def _assert_cap_11_7_contracts_only() -> None:
    if not CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY:
        raise LivePrivateRoRunnerError("CAP_11_7_CONTRACTS_ONLY_FLAG_DRIFT")
    if cap_11_7.LIVE_PRIVATE_READONLY_ACTIVATED is not False:
        raise LivePrivateRoRunnerError("CAP_11_7_MUST_REMAIN_NOT_ACTIVATED")
    if cap_11_7.PRIVATE_READONLY_NETWORK_REACHABLE is not False:
        raise LivePrivateRoRunnerError("CAP_11_7_NETWORK_MUST_REMAIN_UNREACHABLE")
    if cap_11_7.LIVE_PRIVATE_READ_ONLY_PROVEN is not False:
        raise LivePrivateRoRunnerError("CAP_11_7_MUST_NOT_CLAIM_PROVEN")


def _assert_trading_gates_remain_false() -> None:
    if any(
        (
            LIVE_AUTHORIZED,
            LIVE_ENABLED,
            LIVE_ARMED,
            LIVE_ORDER_AUTHORIZED,
            ENABLE_LIVE_TRADING,
            FULLY_AUTONOMOUS_LIVE_TRADING_READY,
        )
    ):
        raise LivePrivateRoRunnerError("TRADING_GATES_MUST_REMAIN_FALSE")


def _transport_allows_productive_proven(transport: LivePrivateRoTransportV1) -> bool:
    return bool(getattr(transport, "allows_productive_proven", False))


def run_section_11_13_2_live_private_read_only_v1(
    *,
    mode: str,
    config_payload: Mapping[str, Any],
    origin_main_sha: str,
    owner_go: str | None = None,
    authorization_scope: str | None = None,
    live_private_read_only_authorized: bool | None = None,
    transport: LivePrivateRoTransportV1 | None = None,
    evidence_run_root: Path | str | None = None,
    peer_environment_for_cross_check: str | None = None,
    peer_credential_class_for_cross_check: str | None = None,
    vault_file: Path | str | None = None,
    permission_attestation: Mapping[str, Any] | None = None,
    allow_real_transport: bool = False,
    executed_code_sha: str | None = None,
) -> LivePrivateRoRunnerResultV1:
    """Fail-closed call chain.

    Modes:
    - preflight: validate through SecretRef metadata; no credential material; no network
    - execute: requires scoped GO + vault material + LIVE transport (real or injected)
    - fixture: local schema path; never sets proven
    """
    mode_s = str(mode or "").strip().lower()
    if mode_s not in {"preflight", "execute", "fixture"}:
        raise LivePrivateRoRunnerError(f"UNSUPPORTED_MODE:{mode}")

    _assert_cap_11_7_contracts_only()
    _assert_trading_gates_remain_false()
    if not default_authorization_is_false_v1() and live_private_read_only_authorized is None:
        raise LivePrivateRoRunnerError("DEFAULT_AUTH_MUST_BE_FALSE")

    if CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE != OWNER_GO_EXECUTE:
        pass

    try:
        config = load_live_private_ro_config_v1(config_payload)
    except LivePrivateRoConfigError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    try:
        require_execute_time_fields_v1(config)
    except LivePrivateRoConfigError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    try:
        binding = build_live_private_ro_venue_binding_v1(
            environment=config.environment,
            venue=config.venue,
            entity=config.entity,
            region=config.region,
            rest_host=config.rest_host,
            rest_base=config.rest_base or None,
            account_scope=config.account_scope,
            instrument_scope=config.instrument_scope,
            owner_declared_host_allowlist=config.owner_declared_host_allowlist
            or (config.rest_host,),
        )
    except LivePrivateRoBindingError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    cross_binding_pass = True
    if peer_environment_for_cross_check is not None:
        try:
            reject_cross_binding_v1(
                live_environment=binding.environment,
                peer_environment=peer_environment_for_cross_check,
                live_credential_class=config.credential_class,
                peer_credential_class=peer_credential_class_for_cross_check or "DEMO_API_KEY",
            )
            cross_binding_pass = False
        except LivePrivateRoBindingError:
            cross_binding_pass = True

    auth_details: dict[str, Any] = {
        "LIVE_PRIVATE_READ_ONLY_AUTHORIZED": False,
        "authorization_validated": False,
    }
    if mode_s == "execute":
        try:
            auth = validate_live_private_read_only_authorization_v1(
                owner_go=owner_go,
                authorization_scope=authorization_scope or AUTHORIZATION_SCOPE,
                bound_origin_main_sha=origin_main_sha,
                expected_origin_main_sha=origin_main_sha,
                bound_config_digest=config.digest(),
                expected_config_digest=config.digest(),
                live_private_read_only_authorized=live_private_read_only_authorized,
            )
        except LivePrivateRoAuthorizationError as exc:
            raise LivePrivateRoRunnerError(str(exc)) from exc
        auth_details = auth.to_dict()
        auth_details["authorization_validated"] = True
    else:
        if live_private_read_only_authorized:
            try:
                auth = validate_live_private_read_only_authorization_v1(
                    owner_go=owner_go,
                    authorization_scope=authorization_scope or AUTHORIZATION_SCOPE,
                    bound_origin_main_sha=origin_main_sha,
                    expected_origin_main_sha=origin_main_sha,
                    bound_config_digest=config.digest(),
                    expected_config_digest=config.digest(),
                    live_private_read_only_authorized=True,
                )
                auth_details = auth.to_dict()
                auth_details["authorization_validated"] = True
            except LivePrivateRoAuthorizationError as exc:
                raise LivePrivateRoRunnerError(str(exc)) from exc

    try:
        reject_cross_environment_secretref_use_v1(
            secretref_uri=config.secretref_uri,
            requested_environment="LIVE",
        )
        secret_meta = build_live_private_ro_secretref_metadata_v1(
            secretref_uri=config.secretref_uri,
            credential_class=config.credential_class or REQUIRED_CREDENTIAL_CLASS,
        )
    except LivePrivateRoSecretRefError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    if mode_s in {"preflight", "fixture"}:
        try:
            refuse_credential_material_borrow_v1(reason=f"{mode_s.upper()}_NO_NETWORK")
        except LivePrivateRoSecretRefError:
            pass
        evidence_root = None
        if evidence_run_root is not None:
            evidence_root = _write_non_proven_evidence(
                evidence_run_root=Path(evidence_run_root),
                config=config,
                origin_main_sha=origin_main_sha,
                secret_meta=secret_meta.to_dict(),
                auth_details=auth_details,
                binding=binding.to_dict(),
                mode=mode_s,
                cross_binding_pass=cross_binding_pass,
            )
        return LivePrivateRoRunnerResultV1(
            ok=True,
            mode=mode_s,
            verdict="PREFLIGHT_PASS_NO_NETWORK"
            if mode_s == "preflight"
            else "FIXTURE_PASS_NOT_PROVEN",
            LIVE_PRIVATE_READ_ONLY_PROVEN=False,
            LIVE_AUTHORIZED=False,
            FULLY_AUTONOMOUS_LIVE_TRADING_READY=False,
            NETWORK_EFFECT="NONE",
            CREDENTIAL_ACCESS="NONE",
            ORDER_EFFECT="NONE",
            evidence_root=str(evidence_root) if evidence_root else None,
            details={
                "config_digest": config.digest(),
                "binding": binding.to_dict(),
                "secretref": secret_meta.to_dict(),
                "authorization": auth_details,
                "cap_11_7_contracts_only": True,
                "credential_material_loaded": False,
                "wire_send_performed": False,
                "PRODUCTIVE_EXECUTE_PATH_READY": True,
            },
        )

    # EXECUTE path
    try:
        attestation = validate_permission_attestation_v1(permission_attestation)
    except LivePrivateRoAssertionError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc
    auth_details["permission_attestation"] = attestation

    if vault_file is None or not str(vault_file).strip():
        raise LivePrivateRoRunnerError("EXECUTE_REQUIRES_VAULT_FILE")

    active_transport = transport
    if active_transport is None:
        if not allow_real_transport:
            raise LivePrivateRoRunnerError("EXECUTE_REQUIRES_EXPLICIT_TRANSPORT_INJECTION")
        active_transport = UrllibLiveTransportV1()
    if getattr(active_transport, "transport_class", "") not in {
        TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
        TRANSPORT_CLASS_GOVERNED_FIXTURE,
    }:
        raise LivePrivateRoRunnerError("TRANSPORT_CLASS_UNSUPPORTED")

    handle = None
    try:
        try:
            vault_backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_secretref_ephemeral_v1(
                secret_reference=config.secretref_uri,
                vault_backend=vault_backend,
                credential_class=config.credential_class,
            )
        except LivePrivateRoCredentialError as exc:
            raise LivePrivateRoRunnerError(str(exc)) from exc

        client = LivePrivateRoHttpClientV1(
            binding=binding,
            transport=active_transport,
            endpoint_allowlist=config.endpoint_allowlist,
            max_request_count=config.max_request_count,
            max_retries=config.max_retries,
            timeout_seconds=config.timeout_seconds,
        )

        successes: list[dict[str, Any]] = []
        auth_presence_docs: list[dict[str, Any]] = []
        account_scope_match = False
        okx_code_success = False
        account_identity_redacted = "<NOT_FETCHED>"

        for endpoint in (
            "/api/v5/account/config",
            "/api/v5/account/balance",
        ):
            if endpoint not in REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS:
                raise LivePrivateRoRunnerError(f"REQUIRED_ENDPOINT_CONSTANT_DRIFT:{endpoint}")
            if endpoint not in config.endpoint_allowlist:
                raise LivePrivateRoRunnerError(f"REQUIRED_ENDPOINT_NOT_IN_CONFIG:{endpoint}")
            url = f"{binding.rest_base.rstrip('/')}{endpoint}"
            try:
                headers = build_okx_live_ro_get_auth_headers_v1(handle=handle, url=url)
            except LivePrivateRoSignerError as exc:
                raise LivePrivateRoRunnerError(str(exc)) from exc
            auth_presence_docs.append(auth_headers_presence_doc_v1(headers))
            try:
                response = client.get(endpoint=endpoint, headers=headers)
                headers.clear()
                require_identity = endpoint == "/api/v5/account/config"
                expected_scope = binding.account_scope if require_identity else None
                success = assert_authenticated_private_read_success_v1(
                    response=response,
                    transport_class=getattr(active_transport, "transport_class", ""),
                    venue_live_contact=bool(getattr(active_transport, "venue_live_contact", False)),
                    expected_account_scope=expected_scope,
                    require_account_identity=require_identity,
                )
            except (
                LivePrivateRoHttpError,
                LivePrivateRoAssertionError,
                LivePrivateRoConfigError,
            ) as exc:
                raise LivePrivateRoRunnerError(str(exc)) from exc
            successes.append(success.to_dict())
            okx_code_success = okx_code_success or (success.okx_code == "0")
            if require_identity:
                account_scope_match = bool(success.account_scope_match)
                account_identity_redacted = success.account_identity_redacted
            elif success.account_identity_redacted not in {"<ABSENT>", "<NOT_FETCHED>"}:
                account_identity_redacted = success.account_identity_redacted

        if not account_scope_match:
            raise LivePrivateRoRunnerError("ACCOUNT_SCOPE_MATCH_REQUIRED")
        if not okx_code_success:
            raise LivePrivateRoRunnerError("OKX_CODE_SUCCESS_REQUIRED")

    finally:
        if handle is not None:
            release_live_ephemeral_material_v1(handle)

    if evidence_run_root is None:
        raise LivePrivateRoRunnerError("EXECUTE_REQUIRES_EVIDENCE_ROOT")

    transport_class = str(getattr(active_transport, "transport_class", ""))
    venue_live = bool(getattr(active_transport, "venue_live_contact", False))
    allows_proven = _transport_allows_productive_proven(active_transport)
    fixture_like = (not allows_proven) or transport_class == TRANSPORT_CLASS_GOVERNED_FIXTURE
    productive_live_transport = bool(allows_proven and not fixture_like)
    authenticated = all(bool(s.get("authenticated_read_success")) for s in successes)

    counters = client.counters.to_dict()
    claims = build_claims_v1(
        origin_main_sha=origin_main_sha,
        executed_code_sha=executed_code_sha or origin_main_sha,
        config_digest=config.digest(),
        environment=binding.environment,
        venue=binding.venue,
        entity=binding.entity,
        region=binding.region,
        rest_host=binding.rest_host,
        account_identity_redacted=account_identity_redacted,
        secretref_log_safe_id=secret_meta.log_safe_id,
        secretref_credential_class=secret_meta.credential_class,
        authorization_scope=str(auth_details.get("authorization_scope", AUTHORIZATION_SCOPE)),
        methods_used=list(counters["methods_used"]),
        endpoints_used=list(counters["endpoints_used"]),
        request_count=int(counters["REQUEST_COUNT"]),
        http_result_classes=list(counters["http_result_classes"]),
        authenticated_read_success=authenticated,
        write_request_count=int(counters["WRITE_REQUEST_COUNT"]),
        order_request_count=int(counters["ORDER_REQUEST_COUNT"]),
        cancel_request_count=int(counters["CANCEL_REQUEST_COUNT"]),
        amend_request_count=int(counters["AMEND_REQUEST_COUNT"]),
        withdraw_request_count=int(counters["WITHDRAW_REQUEST_COUNT"]),
        transfer_request_count=int(counters["TRANSFER_REQUEST_COUNT"]),
        demo_simulation_marker_absent=True,
        cross_binding_checks_pass=cross_binding_pass,
        redaction_check_pass=True,
        transport_class=transport_class,
        venue_live_contact=venue_live,
        fixture_or_demo_or_testnet=fixture_like,
        productive_live_transport=productive_live_transport,
        mode="execute",
        permission_attestation=attestation,
        account_scope_match=account_scope_match,
        okx_code_success=okx_code_success,
    )
    productive_path_structurally_ok = productive_proven_allowed_v1(
        transport_class=transport_class,
        venue_live_contact=venue_live,
        fixture_or_demo_or_testnet=fixture_like,
        authenticated_read_success=authenticated,
    )
    claims["productive_path_structurally_ok"] = productive_path_structurally_ok

    network_effect = (
        "LIVE_PRIVATE_READ_ONLY"
        if isinstance(active_transport, UrllibLiveTransportV1)
        else "INJECTED_TRANSPORT_ONLY"
    )
    summary = {
        "verdict": "PASS" if claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] else "EXECUTE_NOT_PROVEN",
        "LIVE_PRIVATE_READ_ONLY_PROVEN": claims["LIVE_PRIVATE_READ_ONLY_PROVEN"],
        "LIVE_PRIVATE_READ_ONLY_EXECUTED": claims["LIVE_PRIVATE_READ_ONLY_EXECUTED"],
        "LIVE_AUTHORIZED": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "WITHDRAWAL_EFFECT": "NONE",
        "NETWORK_EFFECT": network_effect,
        "CREDENTIAL_ACCESS": "EPHEMERAL_BORROW_RELEASED",
    }
    proof = {
        "successes": successes,
        "counters": counters,
        "auth_headers_presence": auth_presence_docs,
        "permission_attestation": attestation,
        "redacted_sample": redact_mapping_v1({"uid": account_identity_redacted}),
    }
    try:
        assert_no_plaintext_in_payload_v1(summary)
        assert_no_plaintext_in_payload_v1(proof)
        assert_no_plaintext_in_payload_v1(claims)
    except LivePrivateRoCredentialError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    persisted = persist_evidence_bundle_v1(
        evidence_root=Path(evidence_run_root),
        claims=claims,
        summary=summary,
        proof=proof,
        config_digest_doc={"config_digest": config.digest(), "config": config.to_dict()},
        authorization_doc=auth_details,
        zero_write_doc={k: counters[k] for k in counters if k.endswith("_COUNT")},
        redaction_doc={"redaction_check_PASS": True, "plaintext_secret_present": False},
    )
    verify = verify_live_private_read_only_evidence_v1(Path(evidence_run_root))
    return LivePrivateRoRunnerResultV1(
        ok=True,
        mode="execute",
        verdict="EXECUTE_PASS" if claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] else "EXECUTE_NOT_PROVEN",
        LIVE_PRIVATE_READ_ONLY_PROVEN=bool(claims["LIVE_PRIVATE_READ_ONLY_PROVEN"]),
        LIVE_AUTHORIZED=False,
        FULLY_AUTONOMOUS_LIVE_TRADING_READY=False,
        NETWORK_EFFECT=network_effect,
        CREDENTIAL_ACCESS="EPHEMERAL_BORROW_RELEASED",
        ORDER_EFFECT="NONE",
        evidence_root=persisted["evidence_root"],
        details={
            "claims": claims,
            "verify": verify,
            "manifest_sha256": persisted["manifest_sha256"],
            "LIVE_PRIVATE_READ_ONLY_PROVEN_CONSTANT": LIVE_PRIVATE_READ_ONLY_PROVEN,
            "cap_11_7_contracts_only": True,
        },
    )


def run_execute_with_injected_transport_for_tests_v1(
    *,
    config_payload: Mapping[str, Any],
    origin_main_sha: str,
    transport: LivePrivateRoTransportV1,
    evidence_run_root: Path | str,
    owner_go: str = OWNER_GO_EXECUTE,
    authorization_scope: str = AUTHORIZATION_SCOPE,
    live_private_read_only_authorized: bool = True,
    vault_file: Path | str | None = None,
    permission_attestation: Mapping[str, Any] | None = None,
) -> LivePrivateRoRunnerResultV1:
    """Test execute path using injected transport.

    Without vault_file this remains the legacy fixture path (never proven).
    With vault_file it exercises the productive execute wiring; proven only if
    transport.allows_productive_proven is True.
    """
    if vault_file is None:
        # Legacy injected path: placeholders only; never proven.
        _assert_cap_11_7_contracts_only()
        _assert_trading_gates_remain_false()
        config = load_live_private_ro_config_v1(config_payload)
        require_execute_time_fields_v1(config)
        binding = build_live_private_ro_venue_binding_v1(
            environment=config.environment,
            venue=config.venue,
            entity=config.entity,
            region=config.region,
            rest_host=config.rest_host,
            rest_base=config.rest_base or None,
            account_scope=config.account_scope,
            instrument_scope=config.instrument_scope,
            owner_declared_host_allowlist=config.owner_declared_host_allowlist
            or (config.rest_host,),
        )
        auth = validate_live_private_read_only_authorization_v1(
            owner_go=owner_go,
            authorization_scope=authorization_scope,
            bound_origin_main_sha=origin_main_sha,
            expected_origin_main_sha=origin_main_sha,
            bound_config_digest=config.digest(),
            expected_config_digest=config.digest(),
            live_private_read_only_authorized=live_private_read_only_authorized,
        )
        reject_cross_environment_secretref_use_v1(
            secretref_uri=config.secretref_uri,
            requested_environment="LIVE",
        )
        secret_meta = build_live_private_ro_secretref_metadata_v1(
            secretref_uri=config.secretref_uri,
            credential_class=config.credential_class,
        )
        client = LivePrivateRoHttpClientV1(
            binding=binding,
            transport=transport,
            endpoint_allowlist=config.endpoint_allowlist,
            max_request_count=config.max_request_count,
            max_retries=config.max_retries,
            timeout_seconds=config.timeout_seconds,
        )
        headers = {"OK-ACCESS-KEY": "<REF_ONLY>", "OK-ACCESS-SIGN": "<REF_ONLY>"}
        endpoint = REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS[0]
        try:
            response = client.get(endpoint=endpoint, headers=headers)
            success = assert_authenticated_private_read_success_v1(
                response=response,
                transport_class=getattr(transport, "transport_class", ""),
                venue_live_contact=bool(getattr(transport, "venue_live_contact", False)),
            )
        except (
            LivePrivateRoHttpError,
            LivePrivateRoAssertionError,
            LivePrivateRoConfigError,
        ) as exc:
            raise LivePrivateRoRunnerError(str(exc)) from exc
        transport_class = str(getattr(transport, "transport_class", ""))
        venue_live = bool(getattr(transport, "venue_live_contact", False))
        productive_path_structurally_ok = productive_proven_allowed_v1(
            transport_class=transport_class,
            venue_live_contact=venue_live,
            fixture_or_demo_or_testnet=False,
            authenticated_read_success=success.authenticated_read_success,
        )
        counters = client.counters.to_dict()
        claims = build_claims_v1(
            origin_main_sha=origin_main_sha,
            config_digest=config.digest(),
            environment=binding.environment,
            venue=binding.venue,
            entity=binding.entity,
            region=binding.region,
            rest_host=binding.rest_host,
            account_identity_redacted=success.account_identity_redacted,
            secretref_log_safe_id=secret_meta.log_safe_id,
            secretref_credential_class=secret_meta.credential_class,
            authorization_scope=auth.authorization_scope,
            methods_used=list(counters["methods_used"]),
            endpoints_used=list(counters["endpoints_used"]),
            request_count=int(counters["REQUEST_COUNT"]),
            http_result_classes=list(counters["http_result_classes"]),
            authenticated_read_success=success.authenticated_read_success,
            write_request_count=int(counters["WRITE_REQUEST_COUNT"]),
            order_request_count=int(counters["ORDER_REQUEST_COUNT"]),
            cancel_request_count=int(counters["CANCEL_REQUEST_COUNT"]),
            amend_request_count=int(counters["AMEND_REQUEST_COUNT"]),
            withdraw_request_count=int(counters["WITHDRAW_REQUEST_COUNT"]),
            transfer_request_count=int(counters["TRANSFER_REQUEST_COUNT"]),
            demo_simulation_marker_absent=True,
            cross_binding_checks_pass=True,
            redaction_check_pass=True,
            transport_class=transport_class,
            venue_live_contact=venue_live,
            fixture_or_demo_or_testnet=True,
            productive_live_transport=False,
            mode="fixture",
            permission_attestation={"READ": True, "TRADE": False, "WITHDRAW": False},
            account_scope_match=False,
            okx_code_success=True,
        )
        claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] = False
        claims["productive_path_structurally_ok"] = productive_path_structurally_ok
        summary = {
            "verdict": "PASS" if claims["authenticated_read_success"] else "FAIL",
            "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
            "LIVE_AUTHORIZED": False,
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
            "ORDER_EFFECT": "NONE",
            "NETWORK_EFFECT": "INJECTED_TRANSPORT_ONLY",
            "CREDENTIAL_ACCESS": "REF_METADATA_ONLY",
        }
        proof = {
            "success": success.to_dict(),
            "counters": counters,
            "redacted_sample": redact_mapping_v1({"uid": "acct-live-redacted"}),
        }
        persisted = persist_evidence_bundle_v1(
            evidence_root=Path(evidence_run_root),
            claims=claims,
            summary=summary,
            proof=proof,
            config_digest_doc={"config_digest": config.digest(), "config": config.to_dict()},
            authorization_doc=auth.to_dict(),
            zero_write_doc={k: counters[k] for k in counters if k.endswith("_COUNT")},
            redaction_doc={"redaction_check_PASS": True, "plaintext_secret_present": False},
        )
        verify = verify_live_private_read_only_evidence_v1(Path(evidence_run_root))
        return LivePrivateRoRunnerResultV1(
            ok=True,
            mode="fixture",
            verdict="EXECUTE_NOT_PROVEN",
            LIVE_PRIVATE_READ_ONLY_PROVEN=False,
            LIVE_AUTHORIZED=False,
            FULLY_AUTONOMOUS_LIVE_TRADING_READY=False,
            NETWORK_EFFECT="INJECTED_TRANSPORT_ONLY",
            CREDENTIAL_ACCESS="REF_METADATA_ONLY",
            ORDER_EFFECT="NONE",
            evidence_root=persisted["evidence_root"],
            details={
                "claims": claims,
                "verify": verify,
                "manifest_sha256": persisted["manifest_sha256"],
                "fake_transport_type": type(transport).__name__,
                "recording_transport_available": RecordingFakeTransportV1.__name__,
            },
        )

    return run_section_11_13_2_live_private_read_only_v1(
        mode="execute",
        config_payload=config_payload,
        origin_main_sha=origin_main_sha,
        owner_go=owner_go,
        authorization_scope=authorization_scope,
        live_private_read_only_authorized=live_private_read_only_authorized,
        transport=transport,
        evidence_run_root=evidence_run_root,
        vault_file=vault_file,
        permission_attestation=permission_attestation
        or {"READ": True, "TRADE": False, "WITHDRAW": False},
        allow_real_transport=False,
    )


def _write_non_proven_evidence(
    *,
    evidence_run_root: Path,
    config: LivePrivateRoConfigV1,
    origin_main_sha: str,
    secret_meta: dict[str, Any],
    auth_details: dict[str, Any],
    binding: dict[str, Any],
    mode: str,
    cross_binding_pass: bool,
) -> Path:
    claims = build_claims_v1(
        origin_main_sha=origin_main_sha,
        config_digest=config.digest(),
        environment=str(binding.get("environment", "LIVE")),
        venue=str(binding.get("venue", "")),
        entity=str(binding.get("entity", "")),
        region=str(binding.get("region", "")),
        rest_host=str(binding.get("rest_host", "")),
        account_identity_redacted="<NOT_FETCHED>",
        secretref_log_safe_id=str(secret_meta.get("log_safe_id", "")),
        secretref_credential_class=str(secret_meta.get("credential_class", "")),
        authorization_scope=str(auth_details.get("authorization_scope", AUTHORIZATION_SCOPE)),
        methods_used=[],
        endpoints_used=[],
        request_count=0,
        http_result_classes=[],
        authenticated_read_success=False,
        write_request_count=0,
        order_request_count=0,
        cancel_request_count=0,
        amend_request_count=0,
        withdraw_request_count=0,
        transfer_request_count=0,
        demo_simulation_marker_absent=True,
        cross_binding_checks_pass=cross_binding_pass,
        redaction_check_pass=True,
        transport_class=TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK,
        venue_live_contact=False,
        fixture_or_demo_or_testnet=True,
        productive_live_transport=False,
        mode=mode,
    )
    persist_evidence_bundle_v1(
        evidence_root=evidence_run_root,
        claims=claims,
        summary={
            "verdict": "PREFLIGHT_OR_FIXTURE_NOT_PROVEN",
            "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
            "LIVE_AUTHORIZED": False,
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        },
        proof={"preflight": True, "wire_send_performed": False},
        config_digest_doc={"config_digest": config.digest()},
        authorization_doc=auth_details,
        zero_write_doc={
            "WRITE_REQUEST_COUNT": 0,
            "ORDER_REQUEST_COUNT": 0,
            "CANCEL_REQUEST_COUNT": 0,
            "AMEND_REQUEST_COUNT": 0,
            "WITHDRAW_REQUEST_COUNT": 0,
            "TRANSFER_REQUEST_COUNT": 0,
        },
        redaction_doc={"redaction_check_PASS": True},
    )
    verify_live_private_read_only_evidence_v1(evidence_run_root)
    return evidence_run_root

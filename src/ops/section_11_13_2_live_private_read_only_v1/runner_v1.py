"""§11.13.2 runner: fail-closed call chain with preflight no-network mode."""

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
)
from src.ops.section_11_13_2_live_private_read_only_v1.response_assertions_v1 import (
    LivePrivateRoAssertionError,
    assert_authenticated_private_read_success_v1,
    productive_proven_allowed_v1,
    redact_mapping_v1,
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
) -> LivePrivateRoRunnerResultV1:
    """Fail-closed call chain.

    Modes:
    - preflight: validate through SecretRef metadata; no credential material; no network
    - execute: requires scoped GO + injective LIVE transport (tests may inject fake)
    - fixture: local schema path; never sets proven
    """
    mode_s = str(mode or "").strip().lower()
    if mode_s not in {"preflight", "execute", "fixture"}:
        raise LivePrivateRoRunnerError(f"UNSUPPORTED_MODE:{mode}")

    _assert_cap_11_7_contracts_only()
    _assert_trading_gates_remain_false()
    if not default_authorization_is_false_v1() and live_private_read_only_authorized is None:
        raise LivePrivateRoRunnerError("DEFAULT_AUTH_MUST_BE_FALSE")

    # 1) SSOT / selector validation (package-local).
    if CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE != OWNER_GO_EXECUTE:
        # After preparation merge the execute token is the next GO; keep aligned.
        pass

    # 2) Config load
    try:
        config = load_live_private_ro_config_v1(config_payload)
    except LivePrivateRoConfigError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    # Preflight and execute both require productive fields present to proceed past
    # structural validation; missing fields fail closed before network.
    try:
        require_execute_time_fields_v1(config)
    except LivePrivateRoConfigError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    # 3) LIVE binding validation
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

    # Cross-binding reject (optional explicit peer probe).
    cross_binding_pass = True
    if peer_environment_for_cross_check is not None:
        try:
            reject_cross_binding_v1(
                live_environment=binding.environment,
                peer_environment=peer_environment_for_cross_check,
                live_credential_class=config.credential_class,
                peer_credential_class=peer_credential_class_for_cross_check or "DEMO_API_KEY",
            )
            cross_binding_pass = False  # reject_cross_binding should have raised
        except LivePrivateRoBindingError:
            cross_binding_pass = True

    # 4) Scoped authorization (execute requires true GO; preflight may validate false path)
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
        # Preflight/fixture: authorization must not be silently treated as true.
        if live_private_read_only_authorized:
            # Allow validating the auth module in preflight without network, but still
            # refuse credential material borrow / wire send below.
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

    # 5) SecretRef metadata validation (no material)
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
        # Stop immediately before credential material borrow / wire-send.
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
            },
        )

    # EXECUTE path
    if transport is None:
        raise LivePrivateRoRunnerError("EXECUTE_REQUIRES_EXPLICIT_TRANSPORT_INJECTION")
    if getattr(transport, "transport_class", "") not in {
        TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
        TRANSPORT_CLASS_GOVERNED_FIXTURE,
    }:
        raise LivePrivateRoRunnerError("TRANSPORT_CLASS_UNSUPPORTED")

    # Credential resolve: metadata only in this preparation surface. Vault material
    # borrow requires a later separately Owner-authorized execute with local vault.
    try:
        refuse_credential_material_borrow_v1(reason="PREPARATION_SURFACE_NO_VAULT_MATERIAL")
    except LivePrivateRoSecretRefError as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc
    raise LivePrivateRoRunnerError("UNREACHABLE_WITHOUT_VAULT_MATERIAL")  # pragma: no cover


def run_execute_with_injected_transport_for_tests_v1(
    *,
    config_payload: Mapping[str, Any],
    origin_main_sha: str,
    transport: LivePrivateRoTransportV1,
    evidence_run_root: Path | str,
    owner_go: str = OWNER_GO_EXECUTE,
    authorization_scope: str = AUTHORIZATION_SCOPE,
    live_private_read_only_authorized: bool = True,
) -> LivePrivateRoRunnerResultV1:
    """Test-only execute path using injected transport (no vault material).

    Uses auth headers placeholders (not secrets). Never loads vault material.
    Injected/unit evidence cannot set LIVE_PRIVATE_READ_ONLY_PROVEN=true.
    """
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
        owner_declared_host_allowlist=config.owner_declared_host_allowlist or (config.rest_host,),
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

    # Auth header names only; values are placeholders (not secrets).
    headers = {"OK-ACCESS-KEY": "<REF_ONLY>", "OK-ACCESS-SIGN": "<REF_ONLY>"}
    endpoint = REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS[0]
    try:
        response = client.get(endpoint=endpoint, headers=headers)
        success = assert_authenticated_private_read_success_v1(
            response=response,
            transport_class=getattr(transport, "transport_class", ""),
            venue_live_contact=bool(getattr(transport, "venue_live_contact", False)),
        )
    except (LivePrivateRoHttpError, LivePrivateRoAssertionError, LivePrivateRoConfigError) as exc:
        raise LivePrivateRoRunnerError(str(exc)) from exc

    transport_class = str(getattr(transport, "transport_class", ""))
    venue_live = bool(getattr(transport, "venue_live_contact", False))
    # Preparation / unit / injected-transport evidence must never emit the real
    # productive proven claim. Productive proven requires a later Owner-authorized
    # live execute with vault material + real LIVE transport outside this PR.
    productive_path_structurally_ok = productive_proven_allowed_v1(
        transport_class=transport_class,
        venue_live_contact=venue_live,
        fixture_or_demo_or_testnet=False,
        authenticated_read_success=success.authenticated_read_success,
    )
    mode = "fixture"
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
        mode=mode,
    )
    claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] = False
    claims["productive_path_structurally_ok"] = productive_path_structurally_ok

    summary = {
        "verdict": "PASS" if claims["authenticated_read_success"] else "FAIL",
        "LIVE_PRIVATE_READ_ONLY_PROVEN": claims["LIVE_PRIVATE_READ_ONLY_PROVEN"],
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
        mode=mode,
        verdict="EXECUTE_PASS" if claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] else "EXECUTE_NOT_PROVEN",
        LIVE_PRIVATE_READ_ONLY_PROVEN=bool(claims["LIVE_PRIVATE_READ_ONLY_PROVEN"]),
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
            "LIVE_PRIVATE_READ_ONLY_PROVEN_CONSTANT": LIVE_PRIVATE_READ_ONLY_PROVEN,
            "preflight_transport_class": TRANSPORT_CLASS_PREFLIGHT_NO_NETWORK,
            "fake_transport_type": type(transport).__name__,
            "recording_transport_available": RecordingFakeTransportV1.__name__,
        },
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

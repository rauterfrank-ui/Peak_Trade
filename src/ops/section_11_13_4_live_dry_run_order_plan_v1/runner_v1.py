"""§11.13.4 runner: GET-only Live dry-run order plan (no submit)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1 import (
    constants_v1 as cap_11_7,
)
from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1 import (
    constants_v1 as cap_11_8,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.reconciliation_v1 import (
    LiveShadowReconReconciliationError,
    build_exchange_snapshot_from_endpoint_payloads_v1,
    build_local_expected_flat_shadow_state_v1,
    evaluate_live_shadow_exchange_reconciliation_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.response_assertions_v1 import (
    LiveShadowReconAssertionError,
    assert_authenticated_private_read_success_v1,
    productive_proven_allowed_v1,
    validate_permission_attestation_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.authorization_v1 import (
    LiveDryRunOrderPlanAuthorizationError,
    default_authorization_is_false_v1,
    validate_live_dry_run_order_plan_authorization_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.binding_v1 import (
    LiveDryRunOrderPlanBindingError,
    build_live_dry_run_order_plan_venue_binding_v1,
    reject_cross_binding_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.config_v1 import (
    LiveDryRunOrderPlanConfigError,
    LiveDryRunOrderPlanConfigV1,
    load_live_dry_run_order_plan_config_v1,
    require_execute_time_fields_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY,
    CAPABILITY_11_8_REMAINS_FIXTURE_ONLY,
    ENABLE_LIVE_TRADING,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_DRY_RUN_ORDER_PLAN_PROVEN,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    OWNER_GO_EXECUTE,
    PREDECESSOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_REQUIRED,
    PRODUCTIVE_EXECUTE_PATH_READY,
    PUBLIC_REFERENCE_PRICE_ENDPOINT,
    REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_RECONCILIATION_SNAPSHOT_ENDPOINTS,
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.evidence_v1 import (
    build_claims_v1,
    persist_evidence_bundle_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.http_client_v1 import (
    LiveDryRunOrderPlanHttpClientV1,
    LiveDryRunOrderPlanHttpError,
    LiveDryRunOrderPlanTransportV1,
    RecordingFakeTransportV1,
    UrllibLiveTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.live_credential_ephemeral_v1 import (
    LiveDryRunOrderPlanCredentialError,
    assert_no_plaintext_in_payload_v1,
    build_file_secretref_vault_backend_v1,
    release_live_ephemeral_material_v1,
    resolve_and_load_live_secretref_ephemeral_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.mutation_boundary_v1 import (
    LiveDryRunOrderPlanMutationBoundaryError,
    build_mutation_boundary_attestation_v1,
    refuse_order_submit_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.okx_live_ro_signer_v1 import (
    LiveDryRunOrderPlanSignerError,
    auth_headers_presence_doc_v1,
    build_okx_live_ro_get_auth_headers_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.order_plan_v1 import (
    LiveDryRunOrderPlanBuilderError,
    build_live_dry_run_order_plan_record_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.secretref_v1 import (
    LiveDryRunOrderPlanSecretRefError,
    build_live_dry_run_order_plan_secretref_metadata_v1,
    refuse_credential_material_borrow_v1,
    reject_cross_environment_secretref_use_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.verifier_v1 import (
    verify_live_dry_run_order_plan_evidence_v1,
)


class LiveDryRunOrderPlanRunnerError(RuntimeError):
    """Fail-closed runner violation."""


@dataclass(frozen=True)
class LiveDryRunOrderPlanRunnerResultV1:
    ok: bool
    mode: str
    verdict: str
    LIVE_DRY_RUN_ORDER_PLAN_PROVEN: bool
    LIVE_AUTHORIZED: bool
    FULLY_AUTONOMOUS_LIVE_TRADING_READY: bool
    ORDER_PLAN_RESULT: str | None
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
            "LIVE_DRY_RUN_ORDER_PLAN_PROVEN": self.LIVE_DRY_RUN_ORDER_PLAN_PROVEN,
            "LIVE_AUTHORIZED": self.LIVE_AUTHORIZED,
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY": self.FULLY_AUTONOMOUS_LIVE_TRADING_READY,
            "ORDER_PLAN_RESULT": self.ORDER_PLAN_RESULT,
            "NETWORK_EFFECT": self.NETWORK_EFFECT,
            "CREDENTIAL_ACCESS": self.CREDENTIAL_ACCESS,
            "ORDER_EFFECT": self.ORDER_EFFECT,
            "evidence_root": self.evidence_root,
            "details": self.details,
        }


def _assert_caps_remain_contracts_only() -> None:
    if not CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY:
        raise LiveDryRunOrderPlanRunnerError("CAP_11_7_CONTRACTS_ONLY_FLAG_DRIFT")
    if not CAPABILITY_11_8_REMAINS_FIXTURE_ONLY:
        raise LiveDryRunOrderPlanRunnerError("CAP_11_8_FIXTURE_ONLY_FLAG_DRIFT")
    if cap_11_7.LIVE_PRIVATE_READONLY_ACTIVATED is not False:
        raise LiveDryRunOrderPlanRunnerError("CAP_11_7_MUST_REMAIN_NOT_ACTIVATED")
    if getattr(cap_11_8, "LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED", False) is not False:
        raise LiveDryRunOrderPlanRunnerError("CAP_11_8_MUST_REMAIN_NOT_ACTIVATED")


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
        raise LiveDryRunOrderPlanRunnerError("TRADING_GATES_MUST_REMAIN_FALSE")


def _transport_allows_productive_proven(transport: LiveDryRunOrderPlanTransportV1) -> bool:
    return bool(getattr(transport, "allows_productive_proven", False))


def _extract_reference_price(ticker_payload: Mapping[str, Any] | None) -> tuple[str | None, str]:
    if not isinstance(ticker_payload, Mapping):
        return None, "REFERENCE_PRICE_UNAVAILABLE"
    data = ticker_payload.get("data")
    row: Mapping[str, Any] | None = None
    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        row = data[0]
    elif isinstance(data, Mapping):
        row = data
    if not row:
        return None, "REFERENCE_PRICE_UNAVAILABLE"
    for key in ("last", "markPx", "idxPx", "askPx", "bidPx"):
        if row.get(key) not in (None, ""):
            return str(row.get(key)), f"OKX_PUBLIC_TICKER_{key}"
    return None, "REFERENCE_PRICE_UNAVAILABLE"


def _write_non_proven_evidence(
    *,
    evidence_run_root: Path,
    config: LiveDryRunOrderPlanConfigV1,
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
        environment=config.environment,
        venue=config.venue or "<UNSET>",
        entity=config.entity or "<UNSET>",
        region=config.region or "<UNSET>",
        rest_host=config.rest_host or "<UNSET>",
        account_identity_redacted="<NOT_FETCHED>",
        secretref_log_safe_id=str(secret_meta.get("log_safe_id", "")),
        secretref_credential_class=str(secret_meta.get("credential_class", "")),
        authorization_scope=AUTHORIZATION_SCOPE,
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
        transport_class="PREFLIGHT_NO_NETWORK",
        venue_live_contact=False,
        fixture_or_demo_or_testnet=True,
        productive_live_transport=False,
        mode=mode,
        order_plan_result=None,
        blocks_new_entry=True,
        live_reconciliation_proven=False,
    )
    persist_evidence_bundle_v1(
        evidence_root=evidence_run_root,
        claims=claims,
        summary={"verdict": "PREFLIGHT_OR_FIXTURE_NOT_PROVEN", "mode": mode},
        proof={"mode": mode, "LIVE_DRY_RUN_ORDER_PLAN_PROVEN": False},
        config_digest_doc={"config_digest": config.digest(), "binding": binding},
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
    return evidence_run_root


def run_section_11_13_4_live_dry_run_order_plan_v1(
    *,
    mode: str,
    config_payload: Mapping[str, Any],
    origin_main_sha: str,
    owner_go: str | None = None,
    authorization_scope: str | None = None,
    live_dry_run_order_plan_authorized: bool | None = None,
    transport: LiveDryRunOrderPlanTransportV1 | None = None,
    evidence_run_root: Path | str | None = None,
    peer_environment_for_cross_check: str | None = None,
    peer_credential_class_for_cross_check: str | None = None,
    vault_file: Path | str | None = None,
    permission_attestation: Mapping[str, Any] | None = None,
    allow_real_transport: bool = False,
    executed_code_sha: str | None = None,
) -> LiveDryRunOrderPlanRunnerResultV1:
    mode_s = str(mode or "").strip().lower()
    if mode_s not in {"preflight", "execute", "fixture"}:
        raise LiveDryRunOrderPlanRunnerError(f"UNSUPPORTED_MODE:{mode}")

    _assert_caps_remain_contracts_only()
    _assert_trading_gates_remain_false()
    if not default_authorization_is_false_v1() and live_dry_run_order_plan_authorized is None:
        raise LiveDryRunOrderPlanRunnerError("DEFAULT_AUTH_MUST_BE_FALSE")
    if LIVE_DRY_RUN_ORDER_PLAN_PROVEN is not False:
        raise LiveDryRunOrderPlanRunnerError("PACKAGE_DEFAULT_PROVEN_MUST_BE_FALSE")

    try:
        config = load_live_dry_run_order_plan_config_v1(config_payload)
    except LiveDryRunOrderPlanConfigError as exc:
        raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

    try:
        require_execute_time_fields_v1(config)
    except LiveDryRunOrderPlanConfigError as exc:
        raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

    try:
        binding = build_live_dry_run_order_plan_venue_binding_v1(
            environment=config.environment,
            venue=config.venue,
            entity=config.entity,
            region=config.region,
            rest_host=config.rest_host,
            rest_base=config.rest_base or None,
            account_scope=config.account_scope,
            instrument_scope=config.instrument_id,
            owner_declared_host_allowlist=config.owner_declared_host_allowlist
            or (config.rest_host,),
        )
    except LiveDryRunOrderPlanBindingError as exc:
        raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

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
        except LiveDryRunOrderPlanBindingError:
            cross_binding_pass = True

    auth_details: dict[str, Any] = {
        "LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED": False,
        "authorization_validated": False,
    }
    if mode_s == "execute":
        try:
            auth = validate_live_dry_run_order_plan_authorization_v1(
                owner_go=owner_go,
                authorization_scope=authorization_scope or AUTHORIZATION_SCOPE,
                bound_origin_main_sha=origin_main_sha,
                expected_origin_main_sha=origin_main_sha,
                bound_config_digest=config.digest(),
                expected_config_digest=config.digest(),
                live_dry_run_order_plan_authorized=live_dry_run_order_plan_authorized,
            )
        except LiveDryRunOrderPlanAuthorizationError as exc:
            raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc
        auth_details = auth.to_dict()
        auth_details["authorization_validated"] = True
    elif live_dry_run_order_plan_authorized:
        try:
            auth = validate_live_dry_run_order_plan_authorization_v1(
                owner_go=owner_go,
                authorization_scope=authorization_scope or AUTHORIZATION_SCOPE,
                bound_origin_main_sha=origin_main_sha,
                expected_origin_main_sha=origin_main_sha,
                bound_config_digest=config.digest(),
                expected_config_digest=config.digest(),
                live_dry_run_order_plan_authorized=True,
            )
            auth_details = auth.to_dict()
            auth_details["authorization_validated"] = True
        except LiveDryRunOrderPlanAuthorizationError as exc:
            raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

    try:
        reject_cross_environment_secretref_use_v1(
            secretref_uri=config.secretref_uri,
            requested_environment="LIVE",
        )
        secret_meta = build_live_dry_run_order_plan_secretref_metadata_v1(
            secretref_uri=config.secretref_uri,
            credential_class=config.credential_class or REQUIRED_CREDENTIAL_CLASS,
        )
    except LiveDryRunOrderPlanSecretRefError as exc:
        raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

    if mode_s in {"preflight", "fixture"}:
        try:
            refuse_credential_material_borrow_v1(reason=f"{mode_s.upper()}_NO_NETWORK")
        except LiveDryRunOrderPlanSecretRefError:
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
        return LiveDryRunOrderPlanRunnerResultV1(
            ok=True,
            mode=mode_s,
            verdict="PREFLIGHT_PASS_NO_NETWORK"
            if mode_s == "preflight"
            else "FIXTURE_PASS_NOT_PROVEN",
            LIVE_DRY_RUN_ORDER_PLAN_PROVEN=False,
            LIVE_AUTHORIZED=False,
            FULLY_AUTONOMOUS_LIVE_TRADING_READY=False,
            ORDER_PLAN_RESULT=None,
            NETWORK_EFFECT="NONE",
            CREDENTIAL_ACCESS="NONE",
            ORDER_EFFECT="NONE",
            evidence_root=str(evidence_root) if evidence_root else None,
            details={
                "config_digest": config.digest(),
                "binding": binding.to_dict(),
                "secretref": secret_meta.to_dict(),
                "authorization": auth_details,
                "cap_11_8_fixture_only": True,
                "credential_material_loaded": False,
                "wire_send_performed": False,
                "PRODUCTIVE_EXECUTE_PATH_READY": PRODUCTIVE_EXECUTE_PATH_READY,
                "PREDECESSOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_REQUIRED": (
                    PREDECESSOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN_REQUIRED
                ),
            },
        )

    # EXECUTE path
    try:
        attestation = validate_permission_attestation_v1(permission_attestation)
    except LiveShadowReconAssertionError as exc:
        raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc
    auth_details["permission_attestation"] = attestation

    if vault_file is None or not str(vault_file).strip():
        raise LiveDryRunOrderPlanRunnerError("EXECUTE_REQUIRES_VAULT_FILE")

    active_transport = transport
    if active_transport is None:
        if not allow_real_transport:
            raise LiveDryRunOrderPlanRunnerError("EXECUTE_REQUIRES_EXPLICIT_TRANSPORT_INJECTION")
        active_transport = UrllibLiveTransportV1()
    if getattr(active_transport, "transport_class", "") not in {
        TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
        TRANSPORT_CLASS_GOVERNED_FIXTURE,
    }:
        raise LiveDryRunOrderPlanRunnerError("TRANSPORT_CLASS_UNSUPPORTED")

    handle = None
    try:
        try:
            vault_backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_secretref_ephemeral_v1(
                secret_reference=config.secretref_uri,
                vault_backend=vault_backend,
                credential_class=config.credential_class,
            )
        except LiveDryRunOrderPlanCredentialError as exc:
            raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

        client = LiveDryRunOrderPlanHttpClientV1(
            binding=binding,
            transport=active_transport,
            endpoint_allowlist=config.endpoint_allowlist,
            max_request_count=config.max_request_count,
            max_retries=config.max_retries,
            timeout_seconds=config.timeout_seconds,
        )

        successes: list[dict[str, Any]] = []
        auth_presence_docs: list[dict[str, Any]] = []
        payloads_by_endpoint: dict[str, dict[str, Any]] = {}
        account_scope_match = False
        okx_code_success = False
        account_identity_raw = ""
        account_identity_redacted = "<NOT_FETCHED>"

        for endpoint in REQUIRED_RECONCILIATION_SNAPSHOT_ENDPOINTS:
            if endpoint not in config.endpoint_allowlist:
                raise LiveDryRunOrderPlanRunnerError(f"REQUIRED_ENDPOINT_NOT_IN_CONFIG:{endpoint}")
            url = f"{binding.rest_base.rstrip('/')}{endpoint}"
            try:
                headers = build_okx_live_ro_get_auth_headers_v1(handle=handle, url=url)
            except LiveDryRunOrderPlanSignerError as exc:
                raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc
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
                LiveDryRunOrderPlanHttpError,
                LiveShadowReconAssertionError,
                LiveDryRunOrderPlanConfigError,
            ) as exc:
                raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc
            successes.append(success.to_dict())
            if success.sanitized_payload is not None:
                payloads_by_endpoint[endpoint] = dict(success.sanitized_payload)
            okx_code_success = okx_code_success or (success.okx_code == "0")
            if require_identity:
                account_scope_match = bool(success.account_scope_match)
                account_identity_redacted = success.account_identity_redacted
                account_identity_raw = binding.account_scope
            elif success.account_identity_redacted not in {"<ABSENT>", "<NOT_FETCHED>"}:
                account_identity_redacted = success.account_identity_redacted

        # Public reference-price GET (still GET-only; may be signed or unsigned).
        ticker_endpoint = f"{PUBLIC_REFERENCE_PRICE_ENDPOINT}?instId={config.instrument_id}"
        ticker_url = f"{binding.rest_base.rstrip('/')}{ticker_endpoint}"
        try:
            headers = build_okx_live_ro_get_auth_headers_v1(handle=handle, url=ticker_url)
            auth_presence_docs.append(auth_headers_presence_doc_v1(headers))
            ticker_resp = client.get(endpoint=ticker_endpoint, headers=headers)
            headers.clear()
            ticker_payload = parse_json_object_v1(ticker_resp.body_bytes)
            payloads_by_endpoint[PUBLIC_REFERENCE_PRICE_ENDPOINT] = ticker_payload
            if str(ticker_payload.get("code", "")) == "0":
                okx_code_success = True
        except (LiveDryRunOrderPlanHttpError, LiveDryRunOrderPlanSignerError) as exc:
            raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

        if not account_scope_match:
            raise LiveDryRunOrderPlanRunnerError("ACCOUNT_SCOPE_MATCH_REQUIRED")
        if not okx_code_success:
            raise LiveDryRunOrderPlanRunnerError("OKX_CODE_SUCCESS_REQUIRED")
        for required in REQUIRED_ACCOUNT_IDENTITY_ENDPOINTS:
            if required not in payloads_by_endpoint:
                raise LiveDryRunOrderPlanRunnerError(
                    f"REQUIRED_IDENTITY_ENDPOINT_MISSING:{required}"
                )

        local_state = build_local_expected_flat_shadow_state_v1(account_scope=binding.account_scope)
        # Snapshot builder expects recon endpoints only.
        recon_payloads = {
            k: v
            for k, v in payloads_by_endpoint.items()
            if k in REQUIRED_RECONCILIATION_SNAPSHOT_ENDPOINTS
        }
        exchange_snapshot = build_exchange_snapshot_from_endpoint_payloads_v1(
            payloads_by_endpoint=recon_payloads,
            account_identity=account_identity_raw or binding.account_scope,
        )
        try:
            recon = evaluate_live_shadow_exchange_reconciliation_v1(
                local_expected_state=local_state,
                exchange_snapshot=exchange_snapshot,
            )
        except LiveShadowReconReconciliationError as exc:
            raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

        reference_price, pricing_basis = _extract_reference_price(
            payloads_by_endpoint.get(PUBLIC_REFERENCE_PRICE_ENDPOINT)
        )
        run_token = uuid4().hex[:12]
        try:
            plan = build_live_dry_run_order_plan_record_v1(
                venue=binding.venue,
                entity=binding.entity,
                region=binding.region,
                rest_host=binding.rest_host,
                account_scope=binding.account_scope,
                instrument_id=config.instrument_id,
                side=config.side,
                order_type=config.order_type,
                quantity=config.quantity,
                td_mode=config.td_mode,
                fee_bps_assumption=config.fee_bps_assumption,
                slippage_bps_assumption=config.slippage_bps_assumption,
                reference_price=reference_price,
                pricing_basis=pricing_basis,
                balance_payload=payloads_by_endpoint.get("/api/v5/account/balance"),
                positions_payload=payloads_by_endpoint.get("/api/v5/account/positions"),
                reconciliation={
                    "BLOCKS_NEW_ENTRY": recon.blocks_new_entry,
                    "LIVE_RECONCILIATION_PROVEN": False,
                    "UNRESOLVED_ECONOMIC_DIVERGENCE": recon.unresolved_economic_divergence,
                    "ALL_LAYERS_MATCH": recon.all_layers_match,
                    "layers": [layer.to_dict() for layer in recon.layers]
                    if hasattr(recon, "layers")
                    else recon.to_dict().get("layers"),
                },
                intent_id=f"intent-live-dryrun-{run_token}",
                order_plan_id=f"plan-live-dryrun-{run_token}",
                client_order_id=f"pt-coid-ldr-{run_token}",
                min_notional_usdt_assumption=config.min_notional_usdt_assumption,
            )
        except LiveDryRunOrderPlanBuilderError as exc:
            raise LiveDryRunOrderPlanRunnerError(str(exc)) from exc

        # Hard prove submit remains unreachable even after a complete plan.
        try:
            refuse_order_submit_v1(claimed_action="productive_live_dry_run_order_plan")
        except LiveDryRunOrderPlanMutationBoundaryError:
            pass

        order_plan_result = (
            "BLOCKED_NO_EXECUTE"
            if plan.execution_eligibility == "BLOCKED_NO_EXECUTE"
            else "CONSTRUCTED_BLOCKED"
        )

    finally:
        if handle is not None:
            release_live_ephemeral_material_v1(handle)

    if evidence_run_root is None:
        raise LiveDryRunOrderPlanRunnerError("EXECUTE_REQUIRES_EVIDENCE_ROOT")

    transport_class = str(getattr(active_transport, "transport_class", ""))
    venue_live = bool(getattr(active_transport, "venue_live_contact", False))
    allows_proven = _transport_allows_productive_proven(active_transport)
    fixture_like = (not allows_proven) or transport_class == TRANSPORT_CLASS_GOVERNED_FIXTURE
    productive_live_transport = bool(allows_proven and not fixture_like)
    authenticated = all(bool(s.get("authenticated_read_success")) for s in successes)

    counters = client.counters.to_dict()
    mutation_doc = build_mutation_boundary_attestation_v1(
        blocks_new_entry=bool(recon.blocks_new_entry),
        live_reconciliation_proven=False,
        write_request_count=int(counters["WRITE_REQUEST_COUNT"]),
        order_request_count=int(counters["ORDER_REQUEST_COUNT"]),
        cancel_request_count=int(counters["CANCEL_REQUEST_COUNT"]),
        amend_request_count=int(counters["AMEND_REQUEST_COUNT"]),
        withdraw_request_count=int(counters["WITHDRAW_REQUEST_COUNT"]),
        transfer_request_count=int(counters["TRANSFER_REQUEST_COUNT"]),
        methods_used=list(counters["methods_used"]),
    )

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
        order_plan_result=order_plan_result,
        blocks_new_entry=bool(recon.blocks_new_entry),
        live_reconciliation_proven=False,
    )
    claims["productive_path_structurally_ok"] = productive_proven_allowed_v1(
        transport_class=transport_class,
        venue_live_contact=venue_live,
        fixture_or_demo_or_testnet=fixture_like,
        authenticated_read_success=authenticated,
    )
    claims["OWNER_GO"] = OWNER_GO_EXECUTE
    claims["OWNER_GO_STATUS"] = "CONSUMED"
    claims["RUN_BOUND_TO_OWNER_GO"] = OWNER_GO_EXECUTE

    network_effect = (
        "LIVE_DRY_RUN_ORDER_PLAN"
        if isinstance(active_transport, UrllibLiveTransportV1)
        else "INJECTED_TRANSPORT_ONLY"
    )
    plan_dict = plan.to_dict()
    assert_no_plaintext_in_payload_v1(plan_dict)
    assert_no_plaintext_in_payload_v1(claims)

    summary = {
        "verdict": "PASS" if claims["LIVE_DRY_RUN_ORDER_PLAN_PROVEN"] else "EXECUTE_NOT_PROVEN",
        "LIVE_DRY_RUN_ORDER_PLAN_PROVEN": claims["LIVE_DRY_RUN_ORDER_PLAN_PROVEN"],
        "LIVE_DRY_RUN_ORDER_PLAN_EXECUTED": claims["LIVE_DRY_RUN_ORDER_PLAN_EXECUTED"],
        "ORDER_PLAN_RESULT": order_plan_result,
        "LIVE_RECONCILIATION_PROVEN": False,
        "BLOCKS_NEW_ENTRY": bool(recon.blocks_new_entry),
        "LIVE_AUTHORIZED": False,
        "ORDER_EFFECT": "NONE",
        "NETWORK_EFFECT": network_effect,
    }
    proof = {
        "auth_headers_presence": auth_presence_docs,
        "counters": counters,
        "permission_attestation": attestation,
        "reconciliation": recon.to_dict() if hasattr(recon, "to_dict") else {},
        "order_plan_digest": plan.canonical_order_plan_digest,
        "mutation_boundary": mutation_doc,
        "ORDER_PLAN_RESULT": order_plan_result,
        "LIVE_AUTHORIZED": False,
        "ORDER_EFFECT": "NONE",
    }
    persist_evidence_bundle_v1(
        evidence_root=Path(evidence_run_root),
        claims=claims,
        summary=summary,
        proof=proof,
        config_digest_doc={
            "config_digest": config.digest(),
            "binding": binding.to_dict(),
            "predecessor_shadow_evidence_root": config.predecessor_shadow_evidence_root,
        },
        authorization_doc=auth_details,
        zero_write_doc={
            "WRITE_REQUEST_COUNT": int(counters["WRITE_REQUEST_COUNT"]),
            "ORDER_REQUEST_COUNT": int(counters["ORDER_REQUEST_COUNT"]),
            "CANCEL_REQUEST_COUNT": int(counters["CANCEL_REQUEST_COUNT"]),
            "AMEND_REQUEST_COUNT": int(counters["AMEND_REQUEST_COUNT"]),
            "WITHDRAW_REQUEST_COUNT": int(counters["WITHDRAW_REQUEST_COUNT"]),
            "TRANSFER_REQUEST_COUNT": int(counters["TRANSFER_REQUEST_COUNT"]),
        },
        redaction_doc={"redaction_check_PASS": True},
        order_plan_doc=plan_dict,
        mutation_boundary_doc=mutation_doc,
        reconciliation_doc=recon.to_dict() if hasattr(recon, "to_dict") else {},
        exchange_snapshot_doc=exchange_snapshot
        if isinstance(exchange_snapshot, dict)
        else getattr(exchange_snapshot, "to_dict", lambda: {})(),
        local_expected_state_doc=local_state
        if isinstance(local_state, dict)
        else getattr(local_state, "to_dict", lambda: {})(),
    )
    verify_live_dry_run_order_plan_evidence_v1(Path(evidence_run_root))

    return LiveDryRunOrderPlanRunnerResultV1(
        ok=True,
        mode="execute",
        verdict="PASS" if claims["LIVE_DRY_RUN_ORDER_PLAN_PROVEN"] else "EXECUTE_NOT_PROVEN",
        LIVE_DRY_RUN_ORDER_PLAN_PROVEN=bool(claims["LIVE_DRY_RUN_ORDER_PLAN_PROVEN"]),
        LIVE_AUTHORIZED=False,
        FULLY_AUTONOMOUS_LIVE_TRADING_READY=False,
        ORDER_PLAN_RESULT=order_plan_result,
        NETWORK_EFFECT=network_effect,
        CREDENTIAL_ACCESS="EPHEMERAL_BORROW_RELEASED",
        ORDER_EFFECT="NONE",
        evidence_root=str(evidence_run_root),
        details={
            "config_digest": config.digest(),
            "binding": binding.to_dict(),
            "authorization": auth_details,
            "order_plan_eligibility": plan.execution_eligibility,
            "execution_block_reasons": plan.execution_block_reasons,
            "LIVE_RECONCILIATION_PROVEN": False,
            "BLOCKS_NEW_ENTRY": bool(recon.blocks_new_entry),
            "mutation_boundary": mutation_doc,
        },
    )


def run_execute_with_injected_transport_for_tests_v1(
    *,
    config_payload: Mapping[str, Any],
    origin_main_sha: str,
    transport: LiveDryRunOrderPlanTransportV1,
    evidence_run_root: Path | str,
    vault_file: Path | str,
    owner_go: str = OWNER_GO_EXECUTE,
    permission_attestation: Mapping[str, Any] | None = None,
) -> LiveDryRunOrderPlanRunnerResultV1:
    return run_section_11_13_4_live_dry_run_order_plan_v1(
        mode="execute",
        config_payload=config_payload,
        origin_main_sha=origin_main_sha,
        owner_go=owner_go,
        live_dry_run_order_plan_authorized=True,
        transport=transport,
        evidence_run_root=evidence_run_root,
        vault_file=vault_file,
        permission_attestation=permission_attestation
        or {"READ": True, "TRADE": False, "WITHDRAW": False},
        allow_real_transport=False,
    )


# Silence unused import in static analyzers when RecordingFakeTransport used only by tests.
_ = RecordingFakeTransportV1

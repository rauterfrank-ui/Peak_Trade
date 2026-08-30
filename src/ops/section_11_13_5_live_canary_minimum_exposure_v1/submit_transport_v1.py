"""Bounded §11.13.5 canary submit-transport orchestrator (exactly one entry POST)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from src.ops.pre_submit_open_position_cap_v1 import (
    PreSubmitOpenPositionCapErrorV1,
    assert_pre_submit_open_position_cap_allows_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    LiveCanaryConfigV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    BLOCKS_NEW_ENTRY,
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    CANARY_SUBMIT_TRANSPORT_SCOPE,
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_SUBMIT,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    GET_ENDPOINTS_PRIVATE,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_RECONCILIATION_PROVEN,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    SUBMIT_UNLOCKED,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
    USER_AGENT_CANARY,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryHttpResponseV1,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    build_canary_submit_adjudication_evidence_v1,
    extract_canary_http_response_evidence_v1,
    extract_canary_venue_native_request_evidence_v1,
    parse_json_object_v1,
    signed_wire_body_evidence_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.incident_classification_v1 import (
    attach_canary_post_401_classification_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryEphemeralCredentialHandleV1,
    LiveCanaryVaultBackendPortV1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
    serialize_signed_post_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_EXPECTED_MGN_MODE,
    LiveCanaryLeverageObservationError,
    account_leverage_info_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    LiveCanaryMarginModeObservationError,
    account_positions_query_path_v1,
    require_canonical_execution_td_mode_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    LiveCanaryPosModeObservationError,
    account_config_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    LiveCanaryMaxAvailableObservationError,
    account_max_size_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    LiveCanaryPriceBandObservationError,
    public_price_limit_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
    extract_instrument_constraints_v1,
    extract_reference_price_v1,
    quantize_limit_price_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPreSubmitStateError,
    classify_unknown_submit_from_exchange_v1,
    evaluate_pre_submit_exchange_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
    refuse_submit_unless_gates_pass_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    LiveCanaryVenueContractCountError,
    assert_identity_sz_after_contract_sizing_v1,
)


class LiveCanarySubmitTransportError(RuntimeError):
    """Fail-closed canary submit-transport violation."""


def _assert_standing_safety() -> None:
    if not CANARY_SUBMIT_TRANSPORT_IMPLEMENTED:
        raise LiveCanarySubmitTransportError("CANARY_SUBMIT_TRANSPORT_NOT_IMPLEMENTED")
    if CANARY_SUBMIT_TRANSPORT_SCOPE != "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_ONLY":
        raise LiveCanarySubmitTransportError("CANARY_SUBMIT_TRANSPORT_SCOPE_DRIFT")
    if GENERAL_LIVE_SUBMIT_UNLOCKED or SUBMIT_UNLOCKED:
        raise LiveCanarySubmitTransportError("GENERAL_LIVE_SUBMIT_UNLOCK_FORBIDDEN")
    if LIVE_AUTHORIZED:
        raise LiveCanarySubmitTransportError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED:
        raise LiveCanarySubmitTransportError("STANDING_EXECUTED_FLAG_MUST_REMAIN_FALSE")


def _pre_sizing_gates(
    *,
    cfg: LiveCanaryConfigV1,
    owner_go: str | None,
    owner_go_consumed: bool,
    live_canary_authorized: bool,
    origin_main_sha: str,
    live_enabled: bool,
    live_armed: bool,
    confirm_token: str | None,
    permission_attestation: Mapping[str, Any] | None,
    live_canary_cybersecurity_gate: str,
) -> None:
    gate = evaluate_canary_submit_gates_v1(
        owner_go=owner_go,
        owner_go_consumed=owner_go_consumed,
        authorization_scope=AUTHORIZATION_SCOPE if owner_go else None,
        bound_origin_main_sha=origin_main_sha,
        expected_origin_main_sha=origin_main_sha,
        live_canary_authorized=live_canary_authorized,
        live_enabled=live_enabled,
        live_armed=live_armed,
        confirm_token=confirm_token,
        blocks_new_entry=BLOCKS_NEW_ENTRY,
        unresolved_economic_divergence=UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
        live_reconciliation_proven=LIVE_RECONCILIATION_PROVEN,
        permission_attestation=permission_attestation,
        environment=str(cfg.payload.get("environment") or "LIVE"),
        fixture_or_demo_or_testnet=False,
        max_notional=None,
        min_executable_notional=None,
        order_count=1,
        position_count=0,
        exposure_above_minimum_bound=False,
        live_canary_cybersecurity_gate=live_canary_cybersecurity_gate,
        rest_host=str(cfg.payload.get("rest_host") or ""),
        secretref_uri=str(cfg.payload.get("secretref_uri") or ""),
        require_notional_bounds=False,
    )
    refuse_submit_unless_gates_pass_v1(gate)


def _entry_submit_returned_payload_v1(
    *,
    response: LiveCanaryHttpResponseV1,
    plan: Any,
    submit_gate: Any,
    client: LiveCanaryHttpClientV1,
    signed_wire: Mapping[str, Any],
    http_evidence: Mapping[str, Any],
    venue_native_request: Mapping[str, Any],
) -> dict[str, Any]:
    status = int(http_evidence.get("http_status") or response.status_code)
    redirectish = bool(http_evidence.get("redirect_status")) or (300 <= status < 400)
    parsed_ok = bool(http_evidence.get("json_parse_ok"))
    code = str(http_evidence.get("okx_code") or "")
    ok = (
        parsed_ok
        and code == "0"
        and status == 200
        and not redirectish
        and not response.redirect_followed
    )
    if response.redirect_followed:
        canary_result = "ENTRY_SUBMIT_POST_REDIRECT_FOLLOWED_FORBIDDEN"
    elif redirectish:
        canary_result = "ENTRY_SUBMIT_POST_REDIRECT_FAIL_CLOSED"
    else:
        canary_result = "ENTRY_SUBMIT_TRANSPORT_RETURNED"
    adjudication = build_canary_submit_adjudication_evidence_v1(
        http_evidence=http_evidence,
        venue_native_request=venue_native_request,
    )
    payload = {
        "ok": ok,
        "mode": "execute",
        "CANARY_RESULT": canary_result,
        "CANARY_EXECUTED": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_AUTHORIZED": False,
        "SESSION_ENTRY_SUBMITTED": True,
        "ORDER_COUNT_SUBMITTED": int(client.counters.entry_submit_count),
        "DUPLICATE_SUBMIT": False,
        "UNKNOWN_SUBMIT": False,
        "BLIND_RETRY": False,
        "plan": plan.to_dict(),
        "submit_gate": submit_gate.to_dict(),
        "counters": client.counters.to_dict(),
        "http_status": status,
        "http_error_evidence": dict(http_evidence),
        "venue_native_request_evidence": dict(venue_native_request),
        "submit_adjudication_evidence": adjudication,
        "signed_wire_body_evidence": dict(signed_wire),
        "SIGNED_BODY_EQUALS_WIRE_BODY": bool(signed_wire.get("SIGNED_BODY_EQUALS_WIRE_BODY")),
        "OWNER_GO_CONSUMED": False,
        "GENERAL_LIVE_SUBMIT_UNLOCKED": False,
        "SUBMIT_UNLOCKED": False,
        "CANARY_SUBMIT_TRANSPORT_SCOPE": CANARY_SUBMIT_TRANSPORT_SCOPE,
        "RETRY_SAFE_NOW": False,
    }
    return attach_canary_post_401_classification_v1(
        payload,
        http_evidence=http_evidence,
        http_status=status,
    )


def _signed_get(
    *,
    client: LiveCanaryHttpClientV1,
    handle: LiveCanaryEphemeralCredentialHandleV1 | None,
    endpoint: str,
) -> dict[str, Any]:
    path = endpoint.split("?", 1)[0]
    headers = {"User-Agent": USER_AGENT_CANARY}
    if path in GET_ENDPOINTS_PRIVATE:
        if handle is None:
            raise LiveCanarySubmitTransportError("PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE")
        url = f"{client.rest_base.rstrip('/')}{endpoint}"
        headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
    response = client.get(endpoint=endpoint, headers=headers)
    if headers is not None:
        headers.clear()
    return parse_json_object_v1(response.body_bytes)


def run_canary_submit_transport_v1(
    *,
    cfg: LiveCanaryConfigV1,
    origin_main_sha: str,
    owner_go: str | None,
    live_canary_authorized: bool,
    live_enabled: bool,
    live_armed: bool,
    confirm_token: str | None,
    owner_go_consumed: bool,
    permission_attestation: Mapping[str, Any] | None,
    transport: LiveCanaryTransportV1 | None,
    allow_productive_wire_send: bool = False,
    live_canary_cybersecurity_gate: str = "PASS",
    vault_backend: LiveCanaryVaultBackendPortV1 | None = None,
    credential_handle: LiveCanaryEphemeralCredentialHandleV1 | None = None,
) -> dict[str, Any]:
    """Gated canary execute path. Standing LIVE_AUTHORIZED remains false."""
    _assert_standing_safety()
    if str(owner_go or "") == OWNER_GO_AUTHORING:
        raise LiveCanarySubmitTransportError("AUTHORING_GO_CANNOT_EXECUTE_CANARY")
    if str(owner_go or "") != OWNER_GO_EXECUTE:
        raise LiveCanarySubmitTransportError("OWNER_GO_MISMATCH_FOR_TRANSPORT")
    if owner_go_consumed:
        raise LiveCanarySubmitTransportError("OWNER_GO_CONSUMED")

    _pre_sizing_gates(
        cfg=cfg,
        owner_go=owner_go,
        owner_go_consumed=owner_go_consumed,
        live_canary_authorized=live_canary_authorized,
        origin_main_sha=origin_main_sha,
        live_enabled=live_enabled,
        live_armed=live_armed,
        confirm_token=confirm_token,
        permission_attestation=permission_attestation,
        live_canary_cybersecurity_gate=live_canary_cybersecurity_gate,
    )

    if transport is None and not allow_productive_wire_send:
        raise LiveCanarySubmitTransportError("CANARY_SUBMIT_TRANSPORT_NO_WIRE_BACKEND")
    if transport is None:
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)

    rest_host = str(cfg.payload.get("rest_host") or "")
    rest_base = str(cfg.payload.get("rest_base") or "")
    if rest_host != REUSED_BINDING_REST_HOST:
        raise LiveCanarySubmitTransportError("REST_HOST_NOT_PRODUCTION_EEA")
    client = LiveCanaryHttpClientV1(rest_base=rest_base, rest_host=rest_host, transport=transport)

    handle = credential_handle
    created_handle = False
    try:
        if handle is None:
            if vault_backend is None:
                raise LiveCanarySubmitTransportError("VAULT_BACKEND_OR_HANDLE_REQUIRED")
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=str(cfg.payload.get("secretref_uri") or REQUIRED_SECRETREF_URI),
                vault_backend=vault_backend,
                credential_class=str(
                    cfg.payload.get("credential_class") or REQUIRED_CREDENTIAL_CLASS
                ),
            )
            created_handle = True

        instrument_id = str(cfg.payload.get("instrument_id") or DEFAULT_INSTRUMENT_ID)
        try:
            assert_live_canary_instrument_binding_v1(
                instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
            )
        except LiveCanaryInstrumentBindingError as exc:
            raise LiveCanarySubmitTransportError(f"INSTRUMENT_BINDING_FAIL_CLOSED:{exc}") from exc
        inst_ep = public_instruments_query_path_v1(
            instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
        )
        tick_ep = f"/api/v5/market/ticker?instId={instrument_id}"
        pretrade_decision_id = str(uuid4())
        observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        try:
            inst_headers = {"User-Agent": USER_AGENT_CANARY}
            inst_response = client.get(endpoint=inst_ep, headers=inst_headers)
            inst_headers.clear()
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"MAX_SIZE_FRESH_GET_FAILED:{exc}") from exc
        if int(inst_response.status_code) != 200:
            raise LiveCanarySubmitTransportError(
                f"MAX_SIZE_FRESH_GET_HTTP:{inst_response.status_code}"
            )
        try:
            instruments = parse_json_object_v1(inst_response.body_bytes)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"MAX_SIZE_FRESH_GET_BODY:{exc}") from exc
        ticker = _signed_get(client=client, handle=handle, endpoint=tick_ep)
        side = str(cfg.payload.get("side") or "BUY")
        td_mode = str(cfg.payload.get("td_mode") or "cross")
        try:
            require_canonical_execution_td_mode_v1(td_mode)
        except LiveCanaryMarginModeObservationError as exc:
            raise LiveCanarySubmitTransportError(f"MARGIN_MODE_GATE:{exc}") from exc
        try:
            constraints = extract_instrument_constraints_v1(
                instruments_payload=instruments, instrument_id=instrument_id
            )
            reference = extract_reference_price_v1(ticker_payload=ticker)
            limit_px = quantize_limit_price_v1(
                reference_price=reference, tick_sz=constraints["tickSz"]
            )
        except LiveCanaryOrderPlanError as exc:
            raise LiveCanarySubmitTransportError(
                f"ORDER_PLAN_FAIL_CLOSED_BEFORE_POST:{exc}"
            ) from exc
        try:
            price_band_ep = public_price_limit_query_path_v1(instrument_id=instrument_id)
        except LiveCanaryPriceBandObservationError as exc:
            raise LiveCanarySubmitTransportError(f"PRICE_BAND_GATE:{exc}") from exc
        try:
            price_band_headers = {"User-Agent": USER_AGENT_CANARY}
            price_band_response = client.get(endpoint=price_band_ep, headers=price_band_headers)
            price_band_headers.clear()
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"PRICE_BAND_FRESH_GET_FAILED:{exc}") from exc
        if int(price_band_response.status_code) != 200:
            raise LiveCanarySubmitTransportError(
                f"PRICE_BAND_FRESH_GET_HTTP:{price_band_response.status_code}"
            )
        try:
            price_band_payload = parse_json_object_v1(price_band_response.body_bytes)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"PRICE_BAND_FRESH_GET_BODY:{exc}") from exc
        try:
            max_avail_ep = account_max_size_query_path_v1(
                instrument_id=instrument_id,
                td_mode=td_mode,
                px=limit_px,
                order_type=DEFAULT_ORDER_TYPE,
            )
        except LiveCanaryMaxAvailableObservationError as exc:
            raise LiveCanarySubmitTransportError(f"MAX_AVAILABLE_GATE:{exc}") from exc
        max_avail_headers = {"User-Agent": USER_AGENT_CANARY}
        try:
            max_avail_url = f"{client.rest_base.rstrip('/')}{max_avail_ep}"
            max_avail_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=max_avail_url, method="GET"
            )
            max_avail_response = client.get(endpoint=max_avail_ep, headers=max_avail_headers)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"MAX_AVAILABLE_FRESH_GET_FAILED:{exc}") from exc
        finally:
            max_avail_headers.clear()
        if int(max_avail_response.status_code) != 200:
            raise LiveCanarySubmitTransportError(
                f"MAX_AVAILABLE_FRESH_GET_HTTP:{max_avail_response.status_code}"
            )
        try:
            max_available_payload = parse_json_object_v1(max_avail_response.body_bytes)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"MAX_AVAILABLE_FRESH_GET_BODY:{exc}") from exc
        try:
            leverage_ep = account_leverage_info_query_path_v1(
                instrument_id=instrument_id,
                mgn_mode=LEVERAGE_EXPECTED_MGN_MODE,
            )
        except LiveCanaryLeverageObservationError as exc:
            raise LiveCanarySubmitTransportError(f"LEVERAGE_GATE:{exc}") from exc
        leverage_headers = {"User-Agent": USER_AGENT_CANARY}
        try:
            leverage_url = f"{client.rest_base.rstrip('/')}{leverage_ep}"
            leverage_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=leverage_url, method="GET"
            )
            leverage_response = client.get(endpoint=leverage_ep, headers=leverage_headers)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"LEVERAGE_FRESH_GET_FAILED:{exc}") from exc
        finally:
            leverage_headers.clear()
        if int(leverage_response.status_code) != 200:
            raise LiveCanarySubmitTransportError(
                f"LEVERAGE_FRESH_GET_HTTP:{leverage_response.status_code}"
            )
        try:
            leverage_payload = parse_json_object_v1(leverage_response.body_bytes)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"LEVERAGE_FRESH_GET_BODY:{exc}") from exc
        pos_mode_ep = account_config_query_path_v1()
        pos_mode_headers = {"User-Agent": USER_AGENT_CANARY}
        try:
            pos_mode_url = f"{client.rest_base.rstrip('/')}{pos_mode_ep}"
            pos_mode_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=pos_mode_url, method="GET"
            )
            pos_mode_response = client.get(endpoint=pos_mode_ep, headers=pos_mode_headers)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"POS_MODE_FRESH_GET_FAILED:{exc}") from exc
        except LiveCanaryPosModeObservationError as exc:
            raise LiveCanarySubmitTransportError(f"POS_MODE_GATE:{exc}") from exc
        finally:
            pos_mode_headers.clear()
        if int(pos_mode_response.status_code) != 200:
            raise LiveCanarySubmitTransportError(
                f"POS_MODE_FRESH_GET_HTTP:{pos_mode_response.status_code}"
            )
        try:
            pos_mode_payload = parse_json_object_v1(pos_mode_response.body_bytes)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"POS_MODE_FRESH_GET_BODY:{exc}") from exc
        margin_mode_ep = account_positions_query_path_v1()
        try:
            positions = _signed_get(client=client, handle=handle, endpoint=margin_mode_ep)
        except LiveCanaryHttpError as exc:
            raise LiveCanarySubmitTransportError(f"MARGIN_MODE_FRESH_GET_FAILED:{exc}") from exc
        try:
            plan = build_minimum_valid_canary_order_plan_v1(
                instruments_payload=instruments,
                ticker_payload=ticker,
                owner_go=str(owner_go),
                origin_main_sha=origin_main_sha,
                pretrade_decision_id=pretrade_decision_id,
                instrument_id=instrument_id,
                side=side,
                td_mode=td_mode,
                max_size_http_status=int(inst_response.status_code),
                max_size_endpoint=inst_ep,
                max_size_observed_at_utc=observed_at,
                max_size_get_performed=True,
                max_size_auth_header_sent=False,
                max_size_historical_reuse=False,
                max_available_payload=max_available_payload,
                max_available_http_status=int(max_avail_response.status_code),
                max_available_endpoint=max_avail_ep,
                max_available_observed_at_utc=observed_at,
                max_available_get_performed=True,
                max_available_auth_header_sent=True,
                max_available_historical_reuse=False,
                max_available_px_sent=limit_px,
                price_band_payload=price_band_payload,
                price_band_http_status=int(price_band_response.status_code),
                price_band_endpoint=price_band_ep,
                price_band_observed_at_utc=observed_at,
                price_band_get_performed=True,
                price_band_auth_header_sent=False,
                price_band_historical_reuse=False,
                leverage_payload=leverage_payload,
                leverage_http_status=int(leverage_response.status_code),
                leverage_endpoint=leverage_ep,
                leverage_observed_at_utc=observed_at,
                leverage_get_performed=True,
                leverage_auth_header_sent=True,
                leverage_historical_reuse=False,
                leverage_mgn_mode=LEVERAGE_EXPECTED_MGN_MODE,
                pos_mode_payload=pos_mode_payload,
                pos_mode_http_status=int(pos_mode_response.status_code),
                pos_mode_endpoint=pos_mode_ep,
                pos_mode_observed_at_utc=observed_at,
                pos_mode_get_performed=True,
                pos_mode_auth_header_sent=True,
                pos_mode_historical_reuse=False,
                margin_mode_payload=positions,
                margin_mode_http_status=200,
                margin_mode_endpoint=margin_mode_ep,
                margin_mode_observed_at_utc=observed_at,
                margin_mode_get_performed=True,
                margin_mode_auth_header_sent=True,
                margin_mode_historical_reuse=False,
            )
        except LiveCanaryOrderPlanError as exc:
            raise LiveCanarySubmitTransportError(
                f"ORDER_PLAN_FAIL_CLOSED_BEFORE_POST:{exc}"
            ) from exc
        try:
            assert_identity_sz_after_contract_sizing_v1(
                quantity=plan.quantity,
                sz=str(plan.venue_native_payload.get("sz") or ""),
                quantity_domain=plan.quantity_domain,
            )
        except LiveCanaryVenueContractCountError as exc:
            raise LiveCanarySubmitTransportError(
                f"ORDER_PLAN_SZ_IDENTITY_FAIL_CLOSED_BEFORE_POST:{exc}"
            ) from exc

        pending = _signed_get(client=client, handle=handle, endpoint="/api/v5/trade/orders-pending")
        try:
            pre_state = evaluate_pre_submit_exchange_state_v1(
                positions_payload=positions,
                pending_orders_payload=pending,
                instrument_id=plan.instrument_id,
            )
        except LiveCanaryPreSubmitStateError as exc:
            raise LiveCanarySubmitTransportError(f"PRE_SUBMIT_STATE_BLOCK:{exc}") from exc

        # Account-wide second-open-instrument cap on the already fetched
        # GET /api/v5/account/positions payload. Does not replace
        # same-instrument OPEN_POSITION_PRESENT / OPEN_ORDER_PRESENT.
        try:
            assert_pre_submit_open_position_cap_allows_v1(
                target_instrument_id=plan.instrument_id,
                positions_payload=positions,
            )
        except PreSubmitOpenPositionCapErrorV1 as exc:
            raise LiveCanarySubmitTransportError(
                f"ACCOUNT_WIDE_OPEN_POSITION_CAP:{exc.reason_code}"
            ) from exc

        submit_gate = evaluate_canary_submit_gates_v1(
            owner_go=owner_go,
            owner_go_consumed=owner_go_consumed,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=origin_main_sha,
            expected_origin_main_sha=origin_main_sha,
            live_canary_authorized=live_canary_authorized,
            live_enabled=live_enabled,
            live_armed=live_armed,
            confirm_token=confirm_token,
            blocks_new_entry=BLOCKS_NEW_ENTRY,
            unresolved_economic_divergence=UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
            live_reconciliation_proven=LIVE_RECONCILIATION_PROVEN,
            permission_attestation=permission_attestation,
            environment=str(cfg.payload.get("environment") or "LIVE"),
            fixture_or_demo_or_testnet=False,
            max_notional=plan.max_notional,
            min_executable_notional=plan.min_executable_notional,
            order_count=1,
            # LEGACY/NON-AUTHORITATIVE: hardcoded 0 feeds POSITION_COUNT_LIMIT
            # only. Account-wide second-open-instrument admission is
            # assert_pre_submit_open_position_cap_allows_v1 on the GET payload.
            position_count=0,
            exposure_above_minimum_bound=False,
            live_canary_cybersecurity_gate=live_canary_cybersecurity_gate,
            rest_host=rest_host,
            secretref_uri=str(cfg.payload.get("secretref_uri") or ""),
            open_order_count=int(pre_state["open_order_count"]),
            open_position_count=int(pre_state["open_position_count"]),
            require_notional_bounds=True,
            recovery_state_clear=bool(pre_state["recovery_state_clear"]),
        )
        refuse_submit_unless_gates_pass_v1(submit_gate)

        body_text = serialize_signed_post_body_v1(plan.venue_native_payload)
        venue_native_request = extract_canary_venue_native_request_evidence_v1(body_text=body_text)
        url = f"{client.rest_base.rstrip('/')}{ENDPOINT_SUBMIT}"
        headers = build_okx_live_canary_auth_headers_v1(
            handle=handle,
            url=url,
            method="POST",
            body=body_text,
        )
        permit = CanaryEntrySubmitPermitV1(
            owner_go=str(owner_go),
            clordid=plan.clordid,
            permit_id=uuid4().hex,
        )
        try:
            response = client.post_entry_order(permit=permit, body_text=body_text, headers=headers)
        except LiveCanaryHttpError as exc:
            headers.clear()
            if "UNKNOWN_SUBMIT" in str(exc) or "DUPLICATE" in str(exc):
                pending_after = _signed_get(
                    client=client,
                    handle=handle,
                    endpoint="/api/v5/trade/orders-pending",
                )
                history_after = None
                try:
                    history_after = _signed_get(
                        client=client,
                        handle=handle,
                        endpoint=ENDPOINT_ORDERS_HISTORY,
                    )
                except LiveCanaryHttpError:
                    history_after = None
                recovery = classify_unknown_submit_from_exchange_v1(
                    pending_orders_payload=pending_after,
                    history_payload=history_after,
                    clordid=plan.clordid,
                )
                return {
                    "ok": False,
                    "mode": "execute",
                    "CANARY_RESULT": recovery,
                    "CANARY_EXECUTED": False,
                    "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
                    "LIVE_AUTHORIZED": False,
                    "ORDER_COUNT_SUBMITTED": int(client.counters.entry_submit_count),
                    "DUPLICATE_SUBMIT": "DUPLICATE" in str(exc),
                    "UNKNOWN_SUBMIT": True,
                    "BLIND_RETRY": False,
                    "plan": plan.to_dict(),
                    "counters": client.counters.to_dict(),
                    "venue_native_request_evidence": dict(venue_native_request),
                    "submit_adjudication_evidence": build_canary_submit_adjudication_evidence_v1(
                        http_evidence={
                            "http_status": None,
                            "okx_code": None,
                            "okx_msg": None,
                            "okx_data_count": None,
                            "okx_data": [],
                        },
                        venue_native_request=venue_native_request,
                    ),
                    "OWNER_GO_CONSUMED": False,
                    "error": str(exc),
                }
            raise LiveCanarySubmitTransportError(str(exc)) from exc
        headers.clear()
        signed_wire = signed_wire_body_evidence_v1(
            signed_body_text=body_text,
            wire_body_bytes=body_text.encode("utf-8"),
        )
        if response.wire_body_sha256:
            signed_wire["wire_body_sha256_12"] = response.wire_body_sha256[:12]
            signed_wire["wire_body_byte_len"] = int(response.wire_body_byte_len)
            signed_wire["SIGNED_BODY_EQUALS_WIRE_BODY"] = signed_wire[
                "signed_body_sha256_12"
            ] == response.wire_body_sha256[:12] and signed_wire["signed_body_byte_len"] == int(
                response.wire_body_byte_len
            )
        http_evidence = extract_canary_http_response_evidence_v1(
            status_code=response.status_code,
            body_bytes=response.body_bytes,
            headers=response.response_headers_safe,
            redirect_followed=response.redirect_followed,
            redirect_status=response.redirect_status,
            redirect_location=response.redirect_location,
        )
        return _entry_submit_returned_payload_v1(
            response=response,
            plan=plan,
            submit_gate=submit_gate,
            client=client,
            signed_wire=signed_wire,
            http_evidence=http_evidence,
            venue_native_request=venue_native_request,
        )
    finally:
        if created_handle and handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

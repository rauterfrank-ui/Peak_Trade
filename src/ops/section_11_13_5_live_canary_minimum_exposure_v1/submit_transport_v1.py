"""Bounded §11.13.5 canary submit-transport orchestrator (exactly one entry POST)."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    LiveCanaryConfigV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    BLOCKS_NEW_ENTRY,
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    CANARY_SUBMIT_TRANSPORT_SCOPE,
    DEFAULT_INSTRUMENT_ID,
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
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
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

        inst_ep = f"/api/v5/public/instruments?instType=SWAP&instId={DEFAULT_INSTRUMENT_ID}"
        tick_ep = f"/api/v5/market/ticker?instId={DEFAULT_INSTRUMENT_ID}"
        instruments = _signed_get(client=client, handle=handle, endpoint=inst_ep)
        ticker = _signed_get(client=client, handle=handle, endpoint=tick_ep)
        try:
            plan = build_minimum_valid_canary_order_plan_v1(
                instruments_payload=instruments,
                ticker_payload=ticker,
                owner_go=str(owner_go),
                origin_main_sha=origin_main_sha,
                instrument_id=str(cfg.payload.get("instrument_id") or DEFAULT_INSTRUMENT_ID),
                side=str(cfg.payload.get("side") or "BUY"),
                td_mode=str(cfg.payload.get("td_mode") or "cross"),
            )
        except LiveCanaryOrderPlanError as exc:
            raise LiveCanarySubmitTransportError(
                f"ORDER_PLAN_FAIL_CLOSED_BEFORE_POST:{exc}"
            ) from exc

        positions = _signed_get(client=client, handle=handle, endpoint="/api/v5/account/positions")
        pending = _signed_get(client=client, handle=handle, endpoint="/api/v5/trade/orders-pending")
        try:
            pre_state = evaluate_pre_submit_exchange_state_v1(
                positions_payload=positions,
                pending_orders_payload=pending,
                instrument_id=plan.instrument_id,
            )
        except LiveCanaryPreSubmitStateError as exc:
            raise LiveCanarySubmitTransportError(f"PRE_SUBMIT_STATE_BLOCK:{exc}") from exc

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
                    "OWNER_GO_CONSUMED": False,
                    "error": str(exc),
                }
            raise LiveCanarySubmitTransportError(str(exc)) from exc
        headers.clear()
        parsed = parse_json_object_v1(response.body_bytes)
        return {
            "ok": str(parsed.get("code") or "") == "0",
            "mode": "execute",
            "CANARY_RESULT": "ENTRY_SUBMIT_TRANSPORT_RETURNED",
            "CANARY_EXECUTED": False,
            "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
            "LIVE_AUTHORIZED": False,
            "SESSION_ENTRY_SUBMITTED": True,
            "ORDER_COUNT_SUBMITTED": int(client.counters.entry_submit_count),
            "DUPLICATE_SUBMIT": False,
            "UNKNOWN_SUBMIT": False,
            "plan": plan.to_dict(),
            "submit_gate": submit_gate.to_dict(),
            "counters": client.counters.to_dict(),
            "http_status": response.status_code,
            "OWNER_GO_CONSUMED": False,
            "GENERAL_LIVE_SUBMIT_UNLOCKED": False,
            "SUBMIT_UNLOCKED": False,
            "CANARY_SUBMIT_TRANSPORT_SCOPE": CANARY_SUBMIT_TRANSPORT_SCOPE,
        }
    finally:
        if created_handle and handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

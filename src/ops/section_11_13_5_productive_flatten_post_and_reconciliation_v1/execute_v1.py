"""Execute fresh reads, one flatten POST if gates pass, then reconciliation."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    classify_http_okx_result_v1,
    classify_position_observation_v1,
    observation_identity_v1,
    secretref_identity_without_values_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.runtime_permit_v1 import (
    PRICE_BINDING_ROLE,
    evaluate_runtime_permit_issuance_v1,
    runtime_permit_audit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
    RecordingAuthenticatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_gated_submit_v1 import (
    submit_productive_flatten_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    evaluate_canary_flatten_post_action_proof_contract_v1,
    flatten_post_action_submit_evidence_from_submit_result_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
    default_local_monotonic_ms_v1,
    evaluate_position_observation_freshness_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    observe_target_position_flatten_candidate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
    sanitize_positions_payload_v1,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.execute_v1 import (
    sanitize_okx_message_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CANONICAL_TICK_SZ,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_E_HTTP_OR_OKX_ERROR,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT_FILLS,
    ENDPOINT_FLATTEN_POST,
    ENDPOINT_PENDING,
    ENDPOINT_POSITIONS,
    ENDPOINT_TICKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    FRESHNESS_POLICY_MAX_AGE_MS,
    MAX_GET_COUNT,
    MAX_POST_COUNT,
    OWNER_GO,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.contract_v1 import (
    ProductiveFlattenPostContractError,
    assert_live_authorized_cannot_substitute_v1,
    assert_no_retry_v1,
    assert_standing_live_flags_remain_false_v1,
)


class ProductiveFlattenPostExecuteError(RuntimeError):
    """Fail-closed productive flatten execute violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wall_ms_v1() -> int:
    return int(time.time() * 1000)


def _header_presence_v1(headers: Mapping[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PASSPHRASE_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any("simul" in str(k).lower() for k in headers),
    }


def _fixture_offline_hmac_headers_v1() -> dict[str, str]:
    return {
        "OK-ACCESS-KEY": "fixture-offline-key",
        "OK-ACCESS-SIGN": "fixture-offline-sign",
        "OK-ACCESS-TIMESTAMP": "2026-09-04T00:00:00.000Z",
        "OK-ACCESS-PASSPHRASE": "fixture-offline-pass",
        "User-Agent": USER_AGENT_CANARY,
    }


def _redact_order_id_v1(raw: str | None) -> str | None:
    text = str(raw or "").strip()
    if not text:
        return None
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"redacted:{digest}"


def _sanitize_envelope_v1(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    try:
        dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        cloned = json.loads(dumped)
    except (TypeError, ValueError):
        return {"code": str(payload.get("code") or ""), "data": [], "msg": ""}
    if not isinstance(cloned, dict):
        return {"code": "", "data": [], "msg": ""}
    cloned["msg"] = sanitize_okx_message_v1(str(cloned.get("msg") or "")[:200])
    return cloned


def _exchange_observation_v1(
    *,
    endpoint: str,
    method: str,
    request_class: str,
    http_status: int | None,
    payload: Mapping[str, Any] | None,
    body_bytes: bytes,
    get_error: str | None,
    request_time: str,
    response_time: str,
    received_ms: int | None,
    hmac_used: bool,
) -> dict[str, Any]:
    venue_code = str((payload or {}).get("code") or "") if payload else None
    venue_msg = sanitize_okx_message_v1(
        str((payload or {}).get("msg") or "")[:200] if payload else None
    )
    data = (payload or {}).get("data") if payload else None
    body_sha256 = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None
    result_class = classify_http_okx_result_v1(
        http_status=http_status,
        venue_code=venue_code,
        get_error=get_error,
    )
    identity = observation_identity_v1(
        body_sha256=body_sha256,
        received_ms=received_ms,
        endpoint=endpoint,
    )
    return {
        "UTC_TIMESTAMP": request_time,
        "REQUEST_TIME_UTC": request_time,
        "RESPONSE_TIME_UTC": response_time,
        "ENDPOINT": endpoint,
        "METHOD": method,
        "REQUEST_CLASSIFICATION": request_class,
        "HTTP_STATUS": http_status,
        "VENUE_CODE": venue_code,
        "VENUE_MSG": venue_msg,
        "RESULT_CLASS": result_class,
        "BODY_SHA256": body_sha256,
        "BODY_BYTES": len(body_bytes),
        "OBSERVATION_IDENTITY": identity,
        "LOCAL_RESPONSE_RECEIVED_AT": received_ms,
        "HMAC_USED": hmac_used,
        "GET_ERROR": get_error,
        "DATA_ROW_COUNT": len(data) if isinstance(data, list) else None,
        "REDACTED_PAYLOAD": _sanitize_envelope_v1(payload)
        if endpoint != ENDPOINT_POSITIONS
        else sanitize_positions_payload_v1(payload),
        "SECRET_VALUES_INCLUDED": False,
        "SUCCESS": result_class == "HTTP_200_OKX_0" and get_error is None,
    }


def _signed_get_v1(
    *,
    client: LiveCanaryHttpClientV1,
    handle: Any | None,
    endpoint: str,
    request_class: str,
    hmac_required: bool,
) -> dict[str, Any]:
    request_time = _utc_now_iso_v1()
    auth_headers: dict[str, str] = {"User-Agent": USER_AGENT_CANARY}
    get_error: str | None = None
    http_status: int | None = None
    body_bytes = b""
    received_ms: int | None = None
    payload: dict[str, Any] | None = None
    try:
        url = f"{REUSED_REST_BASE}{endpoint}"
        parsed = urlparse(url)
        if parsed.hostname != AUTHORIZED_HOST:
            raise ProductiveFlattenPostExecuteError("HOST_MISMATCH")
        if hmac_required:
            if handle is None:
                raise ProductiveFlattenPostExecuteError("CREDENTIAL_HANDLE_REQUIRED")
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
            presence = _header_presence_v1(auth_headers)
            if not (
                presence["AUTH_KEY_HEADER_PRESENT"]
                and presence["AUTH_SIGN_HEADER_PRESENT"]
                and presence["AUTH_TIMESTAMP_HEADER_PRESENT"]
                and presence["AUTH_PASSPHRASE_HEADER_PRESENT"]
            ):
                raise ProductiveFlattenPostExecuteError("HMAC_HEADERS_MISSING")
            if presence["SIMULATION_HEADER_PRESENT"]:
                raise ProductiveFlattenPostExecuteError("SIMULATION_HEADER_FORBIDDEN")
        response = client.get(endpoint=endpoint, headers=auth_headers)
        received_ms = default_local_monotonic_ms_v1()
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        if response.method != "GET":
            raise ProductiveFlattenPostExecuteError("NON_GET_RESPONSE")
        if response.redirect_followed:
            raise ProductiveFlattenPostExecuteError("REDIRECT_FOLLOWED")
    except LiveCanaryHttpError as exc:
        get_error = str(exc)
        received_ms = default_local_monotonic_ms_v1()
    finally:
        auth_headers.clear()
    if body_bytes:
        try:
            payload = parse_json_object_v1(body_bytes)
        except LiveCanaryHttpError as exc:
            get_error = str(exc) if get_error is None else get_error
            payload = None
    return _exchange_observation_v1(
        endpoint=endpoint,
        method="GET",
        request_class=request_class,
        http_status=http_status,
        payload=payload,
        body_bytes=body_bytes,
        get_error=get_error,
        request_time=request_time,
        response_time=_utc_now_iso_v1(),
        received_ms=received_ms,
        hmac_used=hmac_required,
    )


def _ticker_price_input_v1(
    *,
    ticker_obs: Mapping[str, Any],
    flatten_side: str,
    signed_pos: str,
) -> FlattenPriceInputV1 | None:
    payload = ticker_obs.get("REDACTED_PAYLOAD") or {}
    data = payload.get("data") if isinstance(payload, Mapping) else None
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        return None
    row = data[0]
    bid = str(row.get("bidPx") or "").strip()
    ask = str(row.get("askPx") or "").strip()
    quote_ts = str(row.get("ts") or "").strip()
    if not bid or not ask or not quote_ts:
        return None
    return FlattenPriceInputV1(
        flatten_side=flatten_side,
        observed_signed_pos=signed_pos,
        bid=bid,
        ask=ask,
        quote_timestamp_ms=quote_ts,
        evaluation_timestamp_ms=str(_wall_ms_v1()),
        tick_sz=CANONICAL_TICK_SZ,
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def execute_productive_flatten_post_and_reconciliation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    get_transport: LiveCanaryTransportV1 | None = None,
    post_transport: Any | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Fresh reads, one-shot flatten POST if all gates pass, then recon GETs."""
    from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.assemble_v1 import (
        assemble_productive_flatten_post_and_reconciliation_v1,
    )

    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise ProductiveFlattenPostExecuteError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise ProductiveFlattenPostExecuteError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_live_authorized_cannot_substitute_v1(live_authorized_claim=False)
    assert_standing_live_flags_remain_false_v1(
        live_authorized=LIVE_AUTHORIZED,
        live_enabled=LIVE_ENABLED,
        live_armed=LIVE_ARMED,
        dedicated_flatten_live_wire_enabled=DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    )
    assert_no_retry_v1(retry_used=False)

    productive = get_transport is None
    secretref_identity: dict[str, Any] | None = None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise ProductiveFlattenPostExecuteError("VAULT_FILE_REQUIRED")
        secretref_identity = secretref_identity_without_values_v1(vault_file=vault_file)
        get_transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if get_transport is None:
        raise ProductiveFlattenPostExecuteError("GET_TRANSPORT_REQUIRED")
    if isinstance(get_transport, AuthenticatedGatedProductiveFlattenTransportV1):
        raise ProductiveFlattenPostExecuteError("FLATTEN_POST_TRANSPORT_FORBIDDEN_ON_GET_PATH")

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=get_transport,
        max_request_count=MAX_GET_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    handle = None
    observations: dict[str, Any] = {}
    post_attempted = False
    post_used = False
    post_result = "NOT_ATTEMPTED"
    order_id_redacted: str | None = None
    retry_used = False
    permit_consumed = False
    submit_result = None
    gate_receipt = None
    runtime_permit_audit: dict[str, Any] = {}
    post_action_verdict: dict[str, Any] | None = None
    fail_closed_reason: str | None = None
    observation: dict[str, Any] = {
        "POSITION_OBSERVATION_CLASS": CASE_E_HTTP_OR_OKX_ERROR,
        "POSITION_RESPONSE_OBSERVED": False,
        "TARGET_INSTRUMENT_ROW_OBSERVED": False,
        "POSITION_STATE_OBSERVED": False,
        "TARGET_POSITION_ZERO_PROVEN": False,
        "TARGET_POSITION_NONZERO_PROVEN": False,
    }
    freshness = None
    obs_class = CASE_E_HTTP_OR_OKX_ERROR
    epoch_monotonic_ms = default_local_monotonic_ms_v1()

    def relative_monotonic_ms_v1() -> int:
        return default_local_monotonic_ms_v1() - epoch_monotonic_ms

    try:
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REUSED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REUSED_CREDENTIAL_CLASS,
            )
        hmac_private = handle is not None
        ticker_ep = f"{ENDPOINT_TICKER}?instId={TARGET_INSTRUMENT_ID}"
        observations["GET_TICKER"] = _signed_get_v1(
            client=client,
            handle=handle,
            endpoint=ticker_ep,
            request_class="PUBLIC_GET_TICKER_LIMIT_PRICE",
            hmac_required=False,
        )
        observations["GET_ORDERS_PENDING_PRE"] = _signed_get_v1(
            client=client,
            handle=handle,
            endpoint=ENDPOINT_PENDING,
            request_class="PRIVATE_GET_ORDERS_PENDING_PRE_WIRE",
            hmac_required=hmac_private,
        )
        observations["GET_ACCOUNT_POSITIONS_PRE"] = _signed_get_v1(
            client=client,
            handle=handle,
            endpoint=ENDPOINT_POSITIONS,
            request_class="PRIVATE_GET_ACCOUNT_POSITIONS_PRE_WIRE",
            hmac_required=hmac_private,
        )
        pre_pos = observations["GET_ACCOUNT_POSITIONS_PRE"]
        pre_pending = observations["GET_ORDERS_PENDING_PRE"]
        pre_payload = pre_pos.get("REDACTED_PAYLOAD")
        window = None
        if pre_pos.get("RESULT_CLASS") == "HTTP_200_OKX_0" and isinstance(pre_payload, Mapping):
            window = adjudicate_prerequisite_08_window_v1(
                positions_payload=pre_payload,
                instrument_id=TARGET_INSTRUMENT_ID,
                body_sha256=str(pre_pos.get("BODY_SHA256") or ""),
            )
        observation = classify_position_observation_v1(
            result_class=str(pre_pos.get("RESULT_CLASS") or ""),
            payload=pre_payload if isinstance(pre_payload, Mapping) else None,
            window=window,
        )
        freshness_evidence = None
        received_ms = pre_pos.get("LOCAL_RESPONSE_RECEIVED_AT")
        relative_received_ms = None
        if received_ms is not None:
            relative_received_ms = int(received_ms) - epoch_monotonic_ms
            freshness_evidence = PositionObservationFreshnessEvidenceV1(
                response_received_monotonic_ms=relative_received_ms,
                decision_id="PRODUCTIVE_FLATTEN_PRE_WIRE",
                evidence_kind=PRE_SEND_EVIDENCE_KIND,
                observation_get_identity=str(pre_pos.get("OBSERVATION_IDENTITY") or ""),
            )
        issuance_ms = relative_monotonic_ms_v1()
        freshness = evaluate_position_observation_freshness_v1(
            evidence=freshness_evidence,
            evaluation_monotonic_ms=issuance_ms,
            current_decision_id="PRODUCTIVE_FLATTEN_PRE_WIRE",
        )
        size_binding = None
        if window is not None:
            raw = window.get("TARGET_POSITION_QTY_RAW")
            if raw is not None and str(raw).strip():
                size_binding = str(raw).strip()
        permit, permit_reasons = evaluate_runtime_permit_issuance_v1(
            origin_main_sha=bound_sha,
            instrument_id=TARGET_INSTRUMENT_ID,
            observation_class=str(observation["POSITION_OBSERVATION_CLASS"]),
            observation_identity=str(pre_pos.get("OBSERVATION_IDENTITY") or ""),
            observation_body_sha256=str(pre_pos.get("BODY_SHA256") or ""),
            size_binding=size_binding,
            freshness_allowed=bool(freshness.allowed),
            freshness_reject_reason=freshness.reject_reason or None,
            issuance_monotonic_ms=issuance_ms,
            response_received_monotonic_ms=relative_received_ms,
            result_class=str(pre_pos.get("RESULT_CLASS") or ""),
            authentication_failure=(
                str(pre_pos.get("GET_ERROR") or "")
                if pre_pos.get("RESULT_CLASS") == "HTTP_401_OKX_50110"
                else None
            ),
            transport_error=(
                str(pre_pos.get("GET_ERROR") or "")
                if pre_pos.get("RESULT_CLASS") == "TRANSPORT_OR_CLIENT_FAIL"
                else None
            ),
            unsigned_flatten_transport_used=False,
            live_authorized_claim=False,
            post_performed_claim=False,
            flatten_execute_authorized_claim=False,
            historical_reuse_claim=False,
            price_binding_claimed=PRICE_BINDING_ROLE,
            implementation_owner_go=OWNER_GO,
            expected_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )
        runtime_permit_audit = runtime_permit_audit_v1(permit=permit, deny_reasons=permit_reasons)
        obs_class = str(observation["POSITION_OBSERVATION_CLASS"])
        if obs_class == CASE_B_TARGET_ZERO:
            fail_closed_reason = "POSITION_ALREADY_ZERO_NO_POST"
        elif obs_class != CASE_A_TARGET_NONZERO:
            fail_closed_reason = f"POSITION_OBSERVATION_NOT_FLATTENABLE:{obs_class}"
        elif permit is None:
            fail_closed_reason = "PERMIT_ISSUANCE_DENIED:" + ",".join(permit_reasons)
        elif not pre_pending.get("SUCCESS"):
            fail_closed_reason = "PENDING_ORDERS_GET_FAILED"
        elif not observations["GET_TICKER"].get("SUCCESS"):
            fail_closed_reason = "TICKER_GET_FAILED"
        else:
            pending_payload = pre_pending.get("REDACTED_PAYLOAD")
            if not isinstance(pending_payload, Mapping):
                fail_closed_reason = "PENDING_ORDERS_PAYLOAD_INVALID"
            else:
                observed = observe_target_position_flatten_candidate_v1(
                    positions_payload=pre_payload if isinstance(pre_payload, Mapping) else {},
                    instrument_id=TARGET_INSTRUMENT_ID,
                )
                signed_pos = format(observed.signed_pos, "f")
                flatten_side = observed.candidate_flatten_side
                price_input = _ticker_price_input_v1(
                    ticker_obs=observations["GET_TICKER"],
                    flatten_side=flatten_side,
                    signed_pos=signed_pos,
                )
                if price_input is None:
                    fail_closed_reason = "LIMIT_PRICE_INPUT_MISSING"
                else:
                    flatten_confirm = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
                    gate_input = FlattenPreSendGateInputV1(
                        live_authorized=False,
                        live_enabled=True,
                        live_armed=True,
                        flatten_live_wire_enabled=True,
                        allow_productive_wire_send=True,
                        flatten_execute_token=flatten_confirm,
                        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
                        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
                        positions_payload=pre_payload if isinstance(pre_payload, Mapping) else {},
                        pending_orders_payload=pending_payload,
                        price_input=price_input,
                        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
                        origin_main_sha=bound_sha,
                        flatten_execute_bound_origin_main_sha=bound_sha,
                        instrument_id=TARGET_INSTRUMENT_ID,
                        one_shot_no_retry=True,
                        duplicate_post_protection=True,
                        flatten_pre_send_decision_id="PRODUCTIVE_FLATTEN_PRE_WIRE",
                        position_observation_freshness_evidence=freshness_evidence,
                        monotonic_ms_clock=relative_monotonic_ms_v1,
                        bounded_activation_permit=permit.p16_permit_v1(),
                    )
                    if post_transport is None:
                        post_transport = AuthenticatedGatedProductiveFlattenTransportV1(
                            network_session_authorized=True
                        )
                    post_attempted = True
                    header_builder = None
                    extra_headers: dict[str, str] | None = None
                    if (
                        productive
                        and handle is not None
                        and not isinstance(
                            post_transport, RecordingAuthenticatedProductiveFlattenTransportV1
                        )
                        and not isinstance(post_transport, RecordingFakeCanaryTransportV1)
                    ):
                        credential_handle = handle

                        def _sign_approved_body(receipt: Any) -> dict[str, str]:
                            headers = build_okx_live_canary_auth_headers_v1(
                                handle=credential_handle,
                                url=str(receipt.approved_url),
                                method="POST",
                                body=str(receipt.approved_body_text or ""),
                                extra_headers={"User-Agent": USER_AGENT_CANARY},
                            )
                            headers["User-Agent"] = USER_AGENT_CANARY
                            return headers

                        header_builder = _sign_approved_body
                    elif isinstance(
                        post_transport, RecordingAuthenticatedProductiveFlattenTransportV1
                    ):
                        extra_headers = _fixture_offline_hmac_headers_v1()
                    submit_result = submit_productive_flatten_v1(
                        gate_input=gate_input,
                        transport=post_transport,
                        extra_headers=extra_headers,
                        header_builder=header_builder,
                    )
                    if extra_headers is not None:
                        extra_headers.clear()
                    gate_receipt = submit_result.receipt
                    permit_consumed = bool(submit_result.allowed)
                    if not submit_result.allowed:
                        fail_closed_reason = "PRE_SEND_GATE_DENIED:" + ",".join(
                            submit_result.reasons
                        )
                        post_attempted = False
                    if submit_result is not None:
                        post_used = bool(submit_result.send_attempted)
                        if submit_result.send_completed and submit_result.venue_acceptance_proven:
                            post_result = "POST_ACCEPTED"
                        elif submit_result.send_completed:
                            post_result = "POST_SENT"
                        elif submit_result.send_attempted:
                            post_result = "POST_ATTEMPTED_NOT_COMPLETED:" + ",".join(
                                submit_result.reasons
                            )
                        else:
                            post_result = "POST_NOT_SENT:" + ",".join(submit_result.reasons)
                        response = submit_result.response
                        if response is not None:
                            try:
                                body = json.loads(response.body_bytes.decode("utf-8"))
                            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                                body = None
                            if isinstance(body, dict):
                                data = body.get("data")
                                if isinstance(data, list) and data and isinstance(data[0], dict):
                                    order_id_redacted = _redact_order_id_v1(
                                        str(data[0].get("ordId") or "")
                                    )
                                observations["POST_TRADE_ORDER"] = _exchange_observation_v1(
                                    endpoint=ENDPOINT_FLATTEN_POST,
                                    method="POST",
                                    request_class="PRODUCTIVE_FLATTEN_POST",
                                    http_status=int(response.status_code),
                                    payload=body if isinstance(body, dict) else None,
                                    body_bytes=bytes(response.body_bytes or b""),
                                    get_error=None,
                                    request_time=_utc_now_iso_v1(),
                                    response_time=_utc_now_iso_v1(),
                                    received_ms=default_local_monotonic_ms_v1(),
                                    hmac_used=hmac_private,
                                )
    except ProductiveFlattenPostContractError as exc:
        fail_closed_reason = str(exc)
    except ProductiveFlattenPostExecuteError as exc:
        fail_closed_reason = str(exc)
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
            handle = None

    recon_attempted = False
    if post_used and fail_closed_reason is None:
        recon_attempted = True
        hmac_recon = productive
        recon_handle = None
        try:
            if productive:
                backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
                recon_handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                    secret_reference=REUSED_SECRETREF_URI,
                    vault_backend=backend,
                    credential_class=REUSED_CREDENTIAL_CLASS,
                )
            observations["GET_ACCOUNT_POSITIONS_POST"] = _signed_get_v1(
                client=client,
                handle=recon_handle,
                endpoint=ENDPOINT_POSITIONS,
                request_class="PRIVATE_GET_ACCOUNT_POSITIONS_POST_ACTION",
                hmac_required=hmac_recon,
            )
            observations["GET_ORDERS_PENDING_POST"] = _signed_get_v1(
                client=client,
                handle=recon_handle,
                endpoint=ENDPOINT_PENDING,
                request_class="PRIVATE_GET_ORDERS_PENDING_POST_ACTION",
                hmac_required=hmac_recon,
            )
            observations["GET_TRADE_FILLS"] = _signed_get_v1(
                client=client,
                handle=recon_handle,
                endpoint=f"{ENDPOINT_FILLS}?instId={TARGET_INSTRUMENT_ID}",
                request_class="PRIVATE_GET_TRADE_FILLS_POST_ACTION",
                hmac_required=hmac_recon,
            )
        finally:
            if recon_handle is not None:
                release_live_canary_ephemeral_material_v1(recon_handle)

        post_pos = observations.get("GET_ACCOUNT_POSITIONS_POST") or {}
        post_pending = observations.get("GET_ORDERS_PENDING_POST") or {}
        pre_payload = (observations.get("GET_ACCOUNT_POSITIONS_PRE") or {}).get("REDACTED_PAYLOAD")
        post_payload = post_pos.get("REDACTED_PAYLOAD")
        pending_payload = post_pending.get("REDACTED_PAYLOAD")
        if (
            submit_result is not None
            and isinstance(pre_payload, Mapping)
            and isinstance(post_payload, Mapping)
            and isinstance(pending_payload, Mapping)
        ):
            submit_evidence = flatten_post_action_submit_evidence_from_submit_result_v1(
                submit_result,
                post_readback_after_submit=True,
            )
            submit_evidence = type(submit_evidence)(
                **{
                    **submit_evidence.__dict__,
                    "pre_send_get_identity": str(
                        (observations.get("GET_ACCOUNT_POSITIONS_PRE") or {}).get(
                            "OBSERVATION_IDENTITY"
                        )
                        or ""
                    ),
                    "post_readback_get_identity": str(post_pos.get("OBSERVATION_IDENTITY") or ""),
                }
            )
            verdict = evaluate_canary_flatten_post_action_proof_contract_v1(
                pre_positions_payload=pre_payload,
                post_positions_payload=post_payload,
                post_pending_orders_payload=pending_payload,
                instrument_id=TARGET_INSTRUMENT_ID,
                pre_pending_orders_payload=(
                    (observations.get("GET_ORDERS_PENDING_PRE") or {}).get("REDACTED_PAYLOAD")
                    if isinstance(
                        (observations.get("GET_ORDERS_PENDING_PRE") or {}).get("REDACTED_PAYLOAD"),
                        Mapping,
                    )
                    else None
                ),
                submit_evidence=submit_evidence,
            )
            post_action_verdict = verdict.to_dict()

    counters = client.counters.to_dict()
    write_count = int(counters.get("WRITE_REQUEST_COUNT", 0) or 0)
    if write_count != 0:
        raise ProductiveFlattenPostExecuteError("GET_CLIENT_WRITE_DETECTED")
    post_count = 1 if post_used else 0
    if post_count > MAX_POST_COUNT:
        raise ProductiveFlattenPostExecuteError("POST_COUNT_EXCEEDED")

    post_pos_obs = observations.get("GET_ACCOUNT_POSITIONS_POST") or {}
    post_window = None
    post_payload = post_pos_obs.get("REDACTED_PAYLOAD")
    if post_pos_obs.get("RESULT_CLASS") == "HTTP_200_OKX_0" and isinstance(post_payload, Mapping):
        post_window = adjudicate_prerequisite_08_window_v1(
            positions_payload=post_payload,
            instrument_id=TARGET_INSTRUMENT_ID,
            body_sha256=str(post_pos_obs.get("BODY_SHA256") or ""),
        )
    post_observation = classify_position_observation_v1(
        result_class=str(post_pos_obs.get("RESULT_CLASS") or ""),
        payload=post_payload if isinstance(post_payload, Mapping) else None,
        window=post_window,
    )
    target_zero = bool(
        (post_action_verdict or {}).get("post_pos_zero")
        and (post_action_verdict or {}).get("offline_contract_satisfied")
    )
    live_flatten_proven = bool(
        post_used
        and submit_result is not None
        and submit_result.venue_acceptance_proven
        and target_zero
        and (post_action_verdict or {}).get("causal_submit_bound") is True
        and (post_action_verdict or {}).get("pending_empty") is True
        and (post_action_verdict or {}).get("no_flip") is True
    )
    runtime_facts = {
        "OWNER_GO": owned,
        "OWNER_GO_CONSUMED": True,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "HOST": REUSED_REST_HOST,
        "SECRET_VALUES_INCLUDED": False,
        "SECRETREF_IDENTITY": secretref_identity,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "RETRY_USED": retry_used,
        "RETRY_AUTHORITY_PROVEN": False,
        "GET_PERFORMED_THIS_PERSIST": True,
        "PRIVATE_AUTH_USED": productive,
        "PRIVATE_GET_USED": True,
        "POSITION_GET_USED": True,
        "PUBLIC_GET_USED": True,
        "POST_PERFORMED": post_used,
        "POST_ATTEMPTED": post_attempted,
        "POST_USED": post_used,
        "POST_RESULT": post_result,
        "POST_COUNT": post_count,
        "ORDER_SUBMIT_USED": post_used,
        "ORDER_ID_REDACTED": order_id_redacted,
        "PERMIT_AUDIT": runtime_permit_audit,
        "PERMIT_CONSUMED": permit_consumed,
        "PERMIT_VALIDATION_RESULT": (
            "PASS" if runtime_permit_audit.get("issued") else "FAIL_CLOSED"
        ),
        "OBSERVATION": observation,
        "POST_OBSERVATION": post_observation,
        "FRESHNESS": freshness.to_dict() if freshness is not None else {},
        "PRE_WIRE_POSITION_FRESHNESS": bool(freshness.allowed) if freshness is not None else False,
        "OBSERVATIONS": observations,
        "GATE_RECEIPT": None if gate_receipt is None else gate_receipt.to_dict(),
        "SUBMIT_RESULT": None if submit_result is None else submit_result.to_dict(),
        "POST_ACTION_VERDICT": post_action_verdict,
        "RECONCILIATION_ATTEMPTED": recon_attempted,
        "FAIL_CLOSED_REASON": fail_closed_reason,
        "TARGET_POSITION_ZERO_PROVEN": target_zero,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": live_flatten_proven,
        "NETWORK_SESSION_INSTANCE_AUTHORIZED": bool(
            post_transport is not None
            and bool(getattr(post_transport, "network_session_authorized", False))
        ),
        "FLATTEN_EXECUTE_INVOCATION_USED": post_attempted,
        "COUNTERS": counters,
        "GET_REQUEST_COUNT": int(counters.get("GET_REQUEST_COUNT", 0) or 0),
        "WRITE_REQUEST_COUNT": write_count,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "STANDING_LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "STANDING_LIVE_ENABLED": LIVE_ENABLED,
        "STANDING_LIVE_ARMED": LIVE_ARMED,
        "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED": (
            DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED
        ),
        "FRESHNESS_POLICY_MAX_AGE_MS": FRESHNESS_POLICY_MAX_AGE_MS,
        "CANONICAL_TICK_SZ": CANONICAL_TICK_SZ,
        "CANONICAL_OWNER_GO_TOKEN_FOUND": True,
        "CANONICAL_OWNER_GO_TOKEN": FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        "PRE_WIRE_POSITION_RESULT": obs_class,
    }
    assembled = assemble_productive_flatten_post_and_reconciliation_v1(
        origin_main_sha=bound_sha,
        runtime_facts=runtime_facts,
        evidence_root=evidence_root if persist else None,
        persist=persist,
    )
    assembled["runtime_facts"] = runtime_facts
    assembled["RUNTIME_PERMIT"] = runtime_permit_audit
    return assembled


def recovery_read_only_reobservation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    vault_file: Path | str | None,
    evidence_pack: Path,
    get_transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Bounded post-POST read-only recovery. Never POSTs. Never retries submit."""
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
        write_json_v1,
        write_manifest_v1,
    )
    from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.persist_v1 import (
        assert_no_secrets_in_payload_v1,
    )

    if str(owner_go or "").strip() != OWNER_GO:
        raise ProductiveFlattenPostExecuteError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise ProductiveFlattenPostExecuteError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_no_retry_v1(retry_used=False)
    productive = get_transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise ProductiveFlattenPostExecuteError("VAULT_FILE_REQUIRED")
        get_transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if get_transport is None:
        raise ProductiveFlattenPostExecuteError("GET_TRANSPORT_REQUIRED")
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=get_transport,
        max_request_count=3,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    handle = None
    if productive:
        backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REUSED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REUSED_CREDENTIAL_CLASS,
        )
    observations: dict[str, Any] = {}
    try:
        observations["GET_ACCOUNT_POSITIONS_RECOVERY"] = _signed_get_v1(
            client=client,
            handle=handle,
            endpoint=ENDPOINT_POSITIONS,
            request_class="PRIVATE_GET_ACCOUNT_POSITIONS_RECOVERY_READ_ONLY",
            hmac_required=handle is not None,
        )
        observations["GET_ORDERS_PENDING_RECOVERY"] = _signed_get_v1(
            client=client,
            handle=handle,
            endpoint=ENDPOINT_PENDING,
            request_class="PRIVATE_GET_ORDERS_PENDING_RECOVERY_READ_ONLY",
            hmac_required=handle is not None,
        )
        observations["GET_TRADE_FILLS_RECOVERY"] = _signed_get_v1(
            client=client,
            handle=handle,
            endpoint=f"{ENDPOINT_FILLS}?instId={TARGET_INSTRUMENT_ID}",
            request_class="PRIVATE_GET_TRADE_FILLS_RECOVERY_READ_ONLY",
            hmac_required=handle is not None,
        )
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    counters = client.counters.to_dict()
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise ProductiveFlattenPostExecuteError("GET_CLIENT_WRITE_DETECTED")
    pos = observations["GET_ACCOUNT_POSITIONS_RECOVERY"]
    payload = pos.get("REDACTED_PAYLOAD")
    window = None
    if pos.get("RESULT_CLASS") == "HTTP_200_OKX_0" and isinstance(payload, dict):
        window = adjudicate_prerequisite_08_window_v1(
            positions_payload=payload,
            instrument_id=TARGET_INSTRUMENT_ID,
            body_sha256=str(pos.get("BODY_SHA256") or ""),
        )
    observation = classify_position_observation_v1(
        result_class=str(pos.get("RESULT_CLASS") or ""),
        payload=payload if isinstance(payload, dict) else None,
        window=window,
    )
    pending = observations["GET_ORDERS_PENDING_RECOVERY"]
    pending_payload = pending.get("REDACTED_PAYLOAD") or {}
    pending_data = pending_payload.get("data") if isinstance(pending_payload, dict) else None
    pending_count = len(pending_data) if isinstance(pending_data, list) else None
    fills_payload = observations["GET_TRADE_FILLS_RECOVERY"].get("REDACTED_PAYLOAD") or {}
    fills_data = fills_payload.get("data") if isinstance(fills_payload, dict) else None
    flatten_fill_bound = False
    flatten_fill_sz = None
    flatten_fill_side = None
    if isinstance(fills_data, list):
        for row in fills_data:
            if not isinstance(row, dict):
                continue
            if str(row.get("clOrdId") or "") == "ptokxeprod508b7b41508b7b4101":
                flatten_fill_bound = True
                flatten_fill_sz = str(row.get("fillSz") or "")
                flatten_fill_side = str(row.get("side") or "")
                break
    document = {
        "DOCUMENT_CLASS": "PRODUCTIVE_FLATTEN_RECOVERY_READ_ONLY_REOBSERVATION_V1",
        "DOCUMENT_ROLE": "SANITIZED_RAW_RUNTIME_EVIDENCE_NOT_SSOT",
        "AUTHORITY": "NONE",
        "OWNER_GO": OWNER_GO,
        "BOUND_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "POST_USED": False,
        "RETRY_USED": False,
        "RETRY_AUTHORITY_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "FUNDING_USED": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "SECRET_VALUES_INCLUDED": False,
        "OBSERVATION": observation,
        "PENDING_ROW_COUNT": pending_count,
        "FLATTEN_FILL_BOUND_TO_THIS_CLORDID": flatten_fill_bound,
        "FLATTEN_FILL_SZ": flatten_fill_sz,
        "FLATTEN_FILL_SIDE": flatten_fill_side,
        "ORDER_FILLED_FOR_THIS_CLORDID": flatten_fill_bound and flatten_fill_sz == "1",
        "TARGET_POSITION_ZERO_PROVEN": False,
        "EMPTY_DATA_IS_ZERO": False,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": False,
        "OBSERVATIONS": observations,
        "COUNTERS": counters,
        "WRITE_REQUEST_COUNT": 0,
    }
    assert_no_secrets_in_payload_v1(document)
    recovery_root = Path(evidence_pack).parent / f"{Path(evidence_pack).name}_recovery_read_only"
    recovery_root.mkdir(parents=True, exist_ok=False)
    write_json_v1(recovery_root / "RECOVERY_RECON.sanitized.json", document)
    write_manifest_v1(recovery_root, ("RECOVERY_RECON.sanitized.json",))
    verified = verify_manifest_v1(recovery_root)
    return {
        "EVIDENCE_PACK": str(recovery_root),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "OBSERVATION": observation,
        "PENDING_ROW_COUNT": pending_count,
        "FLATTEN_FILL_BOUND_TO_THIS_CLORDID": flatten_fill_bound,
        "ORDER_FILLED_FOR_THIS_CLORDID": flatten_fill_bound and flatten_fill_sz == "1",
        "TARGET_POSITION_ZERO_PROVEN": False,
        "LIVE_FLATTEN_PROVABILITY_PROVEN": False,
        "POST_USED": False,
        "RETRY_USED": False,
    }

"""Execute the bounded Z2DP read-only create-readiness GET package.

GET only. Reuses LiveCanaryHttpClientV1 and the live-canary signer/SecretRef.
No POST, transfer, order, leverage SET, position-mode SET, or capital movement.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import uuid4

from src.ops.pre_submit_open_position_cap_v1 import (
    evaluate_pre_submit_open_position_cap_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_mode_observation_v1 import (
    acquire_fresh_account_mode_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAIL_EQ_STATUS_OBSERVED,
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    LiveCanaryAvailableMarginObservationError,
    account_balance_query_path_v1,
    acquire_fresh_available_margin_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.category_c_open_algo_pending_observer_v1 import (
    observe_category_c_open_algo_pending_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    USER_AGENT_CANARY,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.instrument_state_observation_v1 import (
    acquire_fresh_instrument_state_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_EXPECTED_MGN_MODE,
    LiveCanaryLeverageObservationError,
    account_leverage_info_query_path_v1,
    acquire_fresh_leverage_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    LiveCanaryMaxAvailableObservationError,
    account_max_size_query_path_v1,
    acquire_fresh_max_available_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    acquire_fresh_max_size_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    extract_instrument_constraints_v1,
    extract_reference_price_v1,
    quantize_limit_price_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    account_config_query_path_v1,
    acquire_fresh_pos_mode_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    classify_target_position_state_v1,
    open_order_instruments_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    acquire_fresh_price_band_observation_from_payload_v1,
    public_price_limit_query_path_v1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.adjudicate_v1 import (
    adjudicate_create_readiness_v1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT_ORDERS_PENDING,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    FORBIDDEN_HTTP_METHODS,
    FUNDING_GET_REQUIRED,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    TARGET_INSTRUMENT_ID,
    TARGET_ORDER_TYPE,
    TARGET_TD_MODE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.persist_v1 import (
    persist_z2dp_create_readiness_evidence_v1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.redaction_v1 import (
    account_binding_fingerprint_v1,
    query_parameters_v1,
    sanitize_account_config_row_v1,
)


class Z2DPCreateReadinessGetError(RuntimeError):
    """Fail-closed Z2DP GET-package violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _header_presence_v1(headers: Mapping[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PASSPHRASE_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any("simul" in str(k).lower() for k in headers),
        "SIGNED_METHOD": "GET",
    }


def _endpoint_path_v1(endpoint: str) -> str:
    return str(endpoint or "").split("?", 1)[0]


def _assert_get_only_client(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DPCreateReadinessGetError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DPCreateReadinessGetError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DPCreateReadinessGetError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise Z2DPCreateReadinessGetError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise Z2DPCreateReadinessGetError("FLATTEN_SUBMIT_DETECTED")
    methods = list(client.counters.methods_used)
    if any(method != "GET" for method in methods):
        raise Z2DPCreateReadinessGetError("NON_GET_METHOD_DETECTED")
    for endpoint in client.counters.endpoints_used:
        path = _endpoint_path_v1(str(endpoint))
        if path in FORBIDDEN_ENDPOINTS:
            raise Z2DPCreateReadinessGetError(f"FORBIDDEN_ENDPOINT_USED:{path}")
    return counters


def execute_fresh_create_readiness_evidence_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform the allowlisted authenticated/public GET package and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise Z2DPCreateReadinessGetError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Z2DPCreateReadinessGetError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise Z2DPCreateReadinessGetError("HOST_MISMATCH")
    if FUNDING_GET_REQUIRED:
        raise Z2DPCreateReadinessGetError("FUNDING_GET_REQUIRED_DRIFT")

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise Z2DPCreateReadinessGetError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise Z2DPCreateReadinessGetError("PRODUCTIVE_WIRE_DISABLED")

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    handle = None
    records: list[dict[str, Any]] = []
    observations: dict[str, Any] = {
        "ACCOUNT_IDENTITY_OBSERVED": False,
        "ACCOUNT_UID": "",
        "ACCOUNT_CONFIG_OK": False,
        "POS_MODE_RAW": "",
        "POSITIONS_OK": False,
        "TARGET_POSITION_STATE": "",
        "OPEN_POSITION_CAP": {},
        "LEVERAGE_OK": False,
        "AVAILABLE_MARGIN_OK": False,
        "AVAIL_EQ_STATUS": "",
        "AVAIL_EQ_RAW": "",
        "MAX_AVAILABLE_OK": False,
        "MAX_BUY_RAW": "",
        "MAX_SELL_RAW": "",
        "MAX_SIZE_OK": False,
        "INSTRUMENT_STATE_OK": False,
        "PRICE_BAND_OK": False,
        "TICKER_OK": False,
        "PENDING_ORDINARY_OK": False,
        "PENDING_ORDINARY_COUNT": None,
        "CATEGORY_C_OK": False,
        "CATEGORY_C_OUTCOME": "",
    }
    parsed_surfaces: dict[str, Any] = {}
    pretrade_decision_id = str(uuid4())
    package_started = _utc_now_iso_v1()
    account_fingerprint = account_binding_fingerprint_v1("")

    def _record(
        *,
        endpoint: str,
        signed: bool,
        http_status: int | None,
        body_bytes: bytes,
        payload: Mapping[str, Any] | None,
        error: str | None,
        parser_result: str,
        redirect_followed: bool,
        header_presence: Mapping[str, Any],
        timestamp: str,
    ) -> dict[str, Any]:
        venue_code = None
        venue_msg = None
        data_row_count = None
        if payload is not None:
            venue_code = str(payload.get("code") or "")
            venue_msg = str(payload.get("msg") or "")[:200]
            data = payload.get("data")
            data_row_count = len(data) if isinstance(data, list) else None
        item = {
            "REQUEST_TIME_UTC": timestamp,
            "METHOD": "GET",
            "HOST": REUSED_REST_HOST,
            "ENDPOINT": _endpoint_path_v1(endpoint),
            "QUERY_PARAMETERS": query_parameters_v1(endpoint),
            "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS if signed else "PUBLIC_UNAUTHENTICATED",
            "SECRETREF_URI": REUSED_SECRETREF_URI if signed else None,
            "ACCOUNT_BINDING_FINGERPRINT": account_fingerprint,
            "HTTP_STATUS": http_status,
            "OKX_CODE": venue_code,
            "OKX_MESSAGE": venue_msg,
            "BODY_BYTES": len(body_bytes),
            "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
            "DATA_ROW_COUNT": data_row_count,
            "PARSER_RESULT": parser_result,
            "GET_ERROR": error,
            "REDIRECT_FOLLOWED": redirect_followed,
            "AUTH_HEADER_PRESENCE": dict(header_presence),
            "OWNER_GO": owned,
            "THIS_SLICE": THIS_SLICE,
            "SECRET_VALUES_INCLUDED": False,
        }
        records.append(item)
        return item

    def _issue_get(*, endpoint: str, signed: bool) -> dict[str, Any]:
        path = _endpoint_path_v1(endpoint)
        if path in FORBIDDEN_ENDPOINTS:
            raise Z2DPCreateReadinessGetError(f"FORBIDDEN_ENDPOINT:{path}")
        url = f"{REUSED_REST_BASE}{endpoint}"
        parsed = urlparse(url)
        if parsed.hostname != AUTHORIZED_HOST:
            raise Z2DPCreateReadinessGetError("HOST_MISMATCH")
        timestamp = _utc_now_iso_v1()
        headers: dict[str, str] = {"User-Agent": USER_AGENT_CANARY}
        header_presence = _header_presence_v1(headers)
        http_status: int | None = None
        body_bytes = b""
        payload: dict[str, Any] | None = None
        error: str | None = None
        parser_result = "NOT_PARSED"
        redirect_followed = False
        try:
            if signed and handle is not None:
                headers = build_okx_live_canary_auth_headers_v1(
                    handle=handle, url=url, method="GET"
                )
                headers["User-Agent"] = USER_AGENT_CANARY
                header_presence = _header_presence_v1(headers)
            elif signed and productive:
                raise Z2DPCreateReadinessGetError("PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE")
            response = client.get(endpoint=endpoint, headers=headers)
            http_status = int(response.status_code)
            body_bytes = bytes(response.body_bytes)
            redirect_followed = bool(response.redirect_followed)
            if response.method != "GET":
                raise Z2DPCreateReadinessGetError("NON_GET_RESPONSE")
            if redirect_followed:
                error = "REDIRECT_FOLLOWED"
                parser_result = "REDIRECT_FAIL_CLOSED"
            elif body_bytes:
                try:
                    payload = parse_json_object_v1(body_bytes)
                    parser_result = "JSON_OBJECT"
                except LiveCanaryHttpError as exc:
                    error = str(exc)
                    parser_result = "PARSE_FAIL"
        except LiveCanaryHttpError as exc:
            error = str(exc)
            parser_result = "HTTP_ERROR"
        except Z2DPCreateReadinessGetError:
            raise
        finally:
            headers.clear()
        record = _record(
            endpoint=endpoint,
            signed=signed,
            http_status=http_status,
            body_bytes=body_bytes,
            payload=payload,
            error=error,
            parser_result=parser_result,
            redirect_followed=redirect_followed,
            header_presence=header_presence,
            timestamp=timestamp,
        )
        return {
            "record": record,
            "payload": payload,
            "http_status": http_status,
            "body_bytes": body_bytes,
            "error": error,
            "endpoint": endpoint,
        }

    try:
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REUSED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REUSED_CREDENTIAL_CLASS,
            )

        instruments_ep = public_instruments_query_path_v1(instrument_id=TARGET_INSTRUMENT_ID)
        instruments_get = _issue_get(endpoint=instruments_ep, signed=False)
        ticker_ep = f"/api/v5/market/ticker?instId={TARGET_INSTRUMENT_ID}"
        ticker_get = _issue_get(endpoint=ticker_ep, signed=False)
        price_band_ep = public_price_limit_query_path_v1(instrument_id=TARGET_INSTRUMENT_ID)
        price_band_get = _issue_get(endpoint=price_band_ep, signed=False)
        config_ep = account_config_query_path_v1()
        config_get = _issue_get(endpoint=config_ep, signed=True)
        positions_ep = "/api/v5/account/positions"
        positions_get = _issue_get(endpoint=positions_ep, signed=True)
        leverage_ep = account_leverage_info_query_path_v1(
            instrument_id=TARGET_INSTRUMENT_ID,
            mgn_mode=LEVERAGE_EXPECTED_MGN_MODE,
        )
        leverage_get = _issue_get(endpoint=leverage_ep, signed=True)
        balance_ep = account_balance_query_path_v1()
        balance_get = _issue_get(endpoint=balance_ep, signed=True)

        observed_at = _utc_now_iso_v1()
        limit_px = ""
        constraints: dict[str, str] = {}
        if instruments_get["payload"] is not None:
            try:
                constraints = extract_instrument_constraints_v1(
                    instruments_payload=instruments_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                )
                inst_obs = acquire_fresh_instrument_state_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    instruments_payload=instruments_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    observed_at_utc=observed_at,
                    endpoint=instruments_ep,
                    http_status=int(instruments_get["http_status"] or 0),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=False,
                    body_sha256=str(instruments_get["record"].get("BODY_SHA256") or ""),
                )
                observations["INSTRUMENT_STATE_OK"] = str(inst_obs.state_raw or "") == "live"
                parsed_surfaces["INSTRUMENT_STATE"] = {
                    "state": inst_obs.state_raw,
                    "endpoint": instruments_ep,
                }
                max_size_obs = acquire_fresh_max_size_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    instruments_payload=instruments_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    observed_at_utc=observed_at,
                    endpoint=instruments_ep,
                    http_status=int(instruments_get["http_status"] or 0),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=False,
                    body_sha256=str(instruments_get["record"].get("BODY_SHA256") or ""),
                )
                observations["MAX_SIZE_OK"] = True
                parsed_surfaces["MAX_SIZE"] = {
                    "maxLmtSz": max_size_obs.max_lmt_sz_raw,
                    "maxMktSz": max_size_obs.max_mkt_sz_raw,
                    "minSz": constraints.get("minSz"),
                    "lotSz": constraints.get("lotSz"),
                    "tickSz": constraints.get("tickSz"),
                }
            except (LiveCanaryOrderPlanError, Exception) as exc:
                parsed_surfaces["INSTRUMENT_PARSE_ERROR"] = str(exc)[:200]

        if ticker_get["payload"] is not None:
            try:
                reference = extract_reference_price_v1(ticker_payload=ticker_get["payload"])
                observations["TICKER_OK"] = True
                parsed_surfaces["TICKER"] = {
                    "last": reference,
                    "source": "extract_reference_price_v1",
                }
                tick_sz = constraints.get("tickSz")
                if tick_sz:
                    limit_px = quantize_limit_price_v1(reference_price=reference, tick_sz=tick_sz)
                    parsed_surfaces["TICKER"]["limit_px_for_max_size_query"] = limit_px
                    parsed_surfaces["TICKER"]["px_authority"] = (
                        "TICKER_LAST_QUANTIZED_TO_TICKSZ_FOR_MAX_SIZE_QUERY_ONLY"
                    )
            except (LiveCanaryOrderPlanError, Exception) as exc:
                parsed_surfaces["TICKER_PARSE_ERROR"] = str(exc)[:200]

        if price_band_get["payload"] is not None and price_band_get["http_status"]:
            try:
                band = acquire_fresh_price_band_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    payload=price_band_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    observed_at_utc=observed_at,
                    endpoint=price_band_ep,
                    http_status=int(price_band_get["http_status"]),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=False,
                    body_sha256=str(price_band_get["record"].get("BODY_SHA256") or ""),
                    order_type=TARGET_ORDER_TYPE,
                )
                observations["PRICE_BAND_OK"] = True
                parsed_surfaces["PRICE_BAND"] = {
                    "buyLmt": band.buy_lmt_raw,
                    "sellLmt": band.sell_lmt_raw,
                    "enabled": band.enabled_raw,
                }
            except Exception as exc:
                parsed_surfaces["PRICE_BAND_PARSE_ERROR"] = str(exc)[:200]

        if config_get["payload"] is not None and config_get["http_status"]:
            try:
                pos_obs = acquire_fresh_pos_mode_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    payload=config_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    observed_at_utc=observed_at,
                    endpoint=config_ep,
                    http_status=int(config_get["http_status"]),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=True,
                    body_sha256=str(config_get["record"].get("BODY_SHA256") or ""),
                )
                observations["POS_MODE_RAW"] = pos_obs.pos_mode_raw
                observations["ACCOUNT_CONFIG_OK"] = True
                data = config_get["payload"].get("data")
                row = (
                    data[0]
                    if isinstance(data, list) and data and isinstance(data[0], Mapping)
                    else {}
                )
                sanitized = sanitize_account_config_row_v1(row if isinstance(row, Mapping) else {})
                parsed_surfaces["ACCOUNT_CONFIG"] = sanitized
                acct_obs = acquire_fresh_account_mode_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    payload=config_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    observed_at_utc=observed_at,
                    endpoint=config_ep,
                    http_status=int(config_get["http_status"]),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=True,
                    body_sha256=str(config_get["record"].get("BODY_SHA256") or ""),
                )
                observations["ACCOUNT_UID"] = acct_obs.uid_raw
                observations["ACCOUNT_IDENTITY_OBSERVED"] = True
                account_fingerprint = account_binding_fingerprint_v1(acct_obs.uid_raw)
                parsed_surfaces["ACCOUNT_MODE"] = {
                    "acctLv": acct_obs.acct_lv_raw,
                    "uid_fingerprint": account_fingerprint,
                    "uid_bound_match": acct_obs.uid_raw == observations["ACCOUNT_UID"],
                }
            except Exception as exc:
                parsed_surfaces["ACCOUNT_CONFIG_PARSE_ERROR"] = str(exc)[:200]

        if positions_get["payload"] is not None:
            try:
                classified = classify_target_position_state_v1(
                    positions_payload=positions_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                )
                observations["TARGET_POSITION_STATE"] = classified.state
                observations["POSITIONS_OK"] = True
                cap = evaluate_pre_submit_open_position_cap_v1(
                    target_instrument_id=TARGET_INSTRUMENT_ID,
                    positions_payload=positions_get["payload"],
                )
                observations["OPEN_POSITION_CAP"] = {
                    "admitted": cap.admitted,
                    "reason_code": cap.reason_code,
                    "open_instrument_ids": list(cap.open_instrument_ids),
                }
                parsed_surfaces["POSITIONS"] = {
                    **classified.to_dict(),
                    "OPEN_POSITION_CAP": observations["OPEN_POSITION_CAP"],
                    "EMPTY_DATA_IS_NOT_ZERO": True,
                    "EMPTY_DATA_IS_NOT_PREREQUISITE_08_ZERO": True,
                }
            except Exception as exc:
                parsed_surfaces["POSITIONS_PARSE_ERROR"] = str(exc)[:200]

        if leverage_get["payload"] is not None and leverage_get["http_status"]:
            try:
                lev = acquire_fresh_leverage_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    payload=leverage_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    mgn_mode=LEVERAGE_EXPECTED_MGN_MODE,
                    observed_at_utc=observed_at,
                    endpoint=leverage_ep,
                    http_status=int(leverage_get["http_status"]),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=True,
                    body_sha256=str(leverage_get["record"].get("BODY_SHA256") or ""),
                )
                observations["LEVERAGE_OK"] = True
                parsed_surfaces["LEVERAGE"] = {
                    "lever": lev.lever_raw,
                    "mgnMode": lev.mgn_mode_raw,
                    "posSide": lev.pos_side_raw,
                    "POSSIDE_NET_IS_NOT_POS_MODE": True,
                    "POSSIDE_IS_NOT_SUBMIT_BODY_PROOF": True,
                }
            except (LiveCanaryLeverageObservationError, Exception) as exc:
                parsed_surfaces["LEVERAGE_PARSE_ERROR"] = str(exc)[:200]

        if balance_get["payload"] is not None and balance_get["http_status"]:
            try:
                margin = acquire_fresh_available_margin_observation_from_payload_v1(
                    pretrade_decision_id=pretrade_decision_id,
                    payload=balance_get["payload"],
                    instrument_id=TARGET_INSTRUMENT_ID,
                    planned_td_mode=TARGET_TD_MODE,
                    observed_at_utc=observed_at,
                    endpoint=balance_ep,
                    http_status=int(balance_get["http_status"]),
                    get_performed=True,
                    rest_host=REUSED_REST_HOST,
                    auth_header_sent=True,
                    body_sha256=str(balance_get["record"].get("BODY_SHA256") or ""),
                )
                observations["AVAIL_EQ_STATUS"] = margin.avail_eq_status
                observations["AVAIL_EQ_RAW"] = margin.avail_eq_raw
                observations["AVAILABLE_MARGIN_OK"] = (
                    margin.avail_eq_status == AVAIL_EQ_STATUS_OBSERVED
                )
                parsed_surfaces["AVAILABLE_MARGIN"] = {
                    "domain": AVAILABLE_MARGIN_OUTPUT_DOMAIN,
                    "selected_ccy": margin.selected_ccy,
                    "avail_eq_status": margin.avail_eq_status,
                    "avail_eq_raw": margin.avail_eq_raw,
                    "account_avail_eq_is_not_authority": True,
                }
            except (LiveCanaryAvailableMarginObservationError, Exception) as exc:
                parsed_surfaces["AVAILABLE_MARGIN_PARSE_ERROR"] = str(exc)[:200]

        max_avail_get: dict[str, Any] | None = None
        if limit_px:
            try:
                max_avail_ep = account_max_size_query_path_v1(
                    instrument_id=TARGET_INSTRUMENT_ID,
                    td_mode=TARGET_TD_MODE,
                    px=limit_px,
                    order_type=TARGET_ORDER_TYPE,
                )
                max_avail_get = _issue_get(endpoint=max_avail_ep, signed=True)
                if max_avail_get["payload"] is not None and max_avail_get["http_status"]:
                    max_obs = acquire_fresh_max_available_observation_from_payload_v1(
                        pretrade_decision_id=pretrade_decision_id,
                        payload=max_avail_get["payload"],
                        instrument_id=TARGET_INSTRUMENT_ID,
                        td_mode=TARGET_TD_MODE,
                        px_sent=limit_px,
                        observed_at_utc=observed_at,
                        endpoint=max_avail_ep,
                        http_status=int(max_avail_get["http_status"]),
                        get_performed=True,
                        rest_host=REUSED_REST_HOST,
                        auth_header_sent=True,
                        body_sha256=str(max_avail_get["record"].get("BODY_SHA256") or ""),
                        order_type=TARGET_ORDER_TYPE,
                    )
                    observations["MAX_AVAILABLE_OK"] = True
                    observations["MAX_BUY_RAW"] = max_obs.max_buy_raw
                    observations["MAX_SELL_RAW"] = max_obs.max_sell_raw
                    parsed_surfaces["MAX_AVAILABLE"] = {
                        "maxBuy": max_obs.max_buy_raw,
                        "maxSell": max_obs.max_sell_raw,
                        "px_sent": limit_px,
                        "NOT_STEP_29P_QUANTITY": True,
                    }
            except (LiveCanaryMaxAvailableObservationError, Exception) as exc:
                parsed_surfaces["MAX_AVAILABLE_PARSE_ERROR"] = str(exc)[:200]
        else:
            parsed_surfaces["MAX_AVAILABLE_SKIPPED"] = "LIMIT_PX_UNAVAILABLE_NO_PRICE_SYNTHESIS"

        pending_get = _issue_get(endpoint=ENDPOINT_ORDERS_PENDING, signed=True)
        if pending_get["payload"] is not None:
            try:
                pending_inst = open_order_instruments_v1(pending_get["payload"])
                observations["PENDING_ORDINARY_OK"] = True
                observations["PENDING_ORDINARY_COUNT"] = len(pending_inst)
                parsed_surfaces["PENDING_ORDINARY"] = {
                    "count": len(pending_inst),
                    "target_instrument_pending": TARGET_INSTRUMENT_ID in pending_inst,
                }
            except Exception as exc:
                parsed_surfaces["PENDING_ORDINARY_PARSE_ERROR"] = str(exc)[:200]

        def _algo_header_factory(url: str) -> dict[str, str]:
            if handle is None:
                return {"User-Agent": USER_AGENT_CANARY}
            headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
            headers["User-Agent"] = USER_AGENT_CANARY
            return headers

        algo_started = len(records)
        try:
            algo_obs = observe_category_c_open_algo_pending_v1(
                client=client,
                instrument_id=TARGET_INSTRUMENT_ID,
                header_factory=_algo_header_factory,
                max_requests=3,
                max_pages_per_variant=1,
            )
            observations["CATEGORY_C_OK"] = algo_obs.outcome.value in {
                "TARGET_CATEGORY_C_NOT_OBSERVED",
                "TARGET_CATEGORY_C_OBSERVED",
            }
            observations["CATEGORY_C_OUTCOME"] = algo_obs.outcome.value
            parsed_surfaces["PENDING_ALGO"] = {
                "outcome": algo_obs.outcome.value,
                "request_count": algo_obs.request_count,
                "target_row_count": len(algo_obs.target_rows),
                "fail_closed_reason": algo_obs.fail_closed_reason,
            }
            for endpoint in algo_obs.endpoints_requested:
                already = any(
                    item.get("ENDPOINT") == _endpoint_path_v1(endpoint)
                    and item.get("QUERY_PARAMETERS") == query_parameters_v1(endpoint)
                    for item in records[algo_started:]
                )
                if already:
                    continue
                records.append(
                    {
                        "REQUEST_TIME_UTC": _utc_now_iso_v1(),
                        "METHOD": "GET",
                        "HOST": REUSED_REST_HOST,
                        "ENDPOINT": _endpoint_path_v1(endpoint),
                        "QUERY_PARAMETERS": query_parameters_v1(endpoint),
                        "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS,
                        "SECRETREF_URI": REUSED_SECRETREF_URI,
                        "ACCOUNT_BINDING_FINGERPRINT": account_fingerprint,
                        "HTTP_STATUS": None,
                        "OKX_CODE": None,
                        "PARSER_RESULT": "CATEGORY_C_OBSERVER",
                        "OWNER_GO": owned,
                        "THIS_SLICE": THIS_SLICE,
                        "SECRET_VALUES_INCLUDED": False,
                    }
                )
        except Exception as exc:
            parsed_surfaces["PENDING_ALGO_PARSE_ERROR"] = str(exc)[:200]
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

    for method in FORBIDDEN_HTTP_METHODS:
        if method in list(client.counters.methods_used):
            raise Z2DPCreateReadinessGetError(f"FORBIDDEN_METHOD:{method}")
    counters = _assert_get_only_client(client)
    for item in records:
        item["ACCOUNT_BINDING_FINGERPRINT"] = account_fingerprint

    adjudication = adjudicate_create_readiness_v1(observations=observations)
    package_finished = _utc_now_iso_v1()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    public_get_count = sum(
        1 for item in records if item.get("CREDENTIAL_CLASS") == "PUBLIC_UNAUTHENTICATED"
    )
    private_get_count = sum(
        1 for item in records if item.get("CREDENTIAL_CLASS") == REUSED_CREDENTIAL_CLASS
    )
    snapshot = {
        "DOCUMENT_CLASS": "Z2DP_POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "PRETRADE_DECISION_ID": pretrade_decision_id,
        "PACKAGE_STARTED_UTC": package_started,
        "PACKAGE_FINISHED_UTC": package_finished,
        "HOST": REUSED_REST_HOST,
        "METHOD_ALLOWLIST": ["GET"],
        "REQUESTS": records,
        "PARSED_SURFACES": parsed_surfaces,
        "COUNTERS": counters,
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT"),
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT"),
        "PUBLIC_GET_COUNT": public_get_count,
        "PRIVATE_GET_COUNT": private_get_count,
        "FUNDING_GET_PERFORMED": False,
        "POSITIONS_GET_PERFORMED": any(
            item.get("ENDPOINT") == "/api/v5/account/positions" for item in records
        ),
        "POST_PERFORMED": False,
        "ORDER_PERFORMED": False,
        "POSITION_CREATION_PERFORMED": False,
        "EXECUTION_PERFORMED": False,
        "LIVE_ARMING_PERFORMED": False,
        "SECRET_VALUES_INCLUDED": False,
        "LIVE_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY": (
            CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY
        ),
    }
    summary = {
        "DOCUMENT_CLASS": "Z2DP_POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT"),
        "PUBLIC_GET_COUNT": public_get_count,
        "PRIVATE_GET_COUNT": private_get_count,
        "FUNDING_GET_PERFORMED": False,
        "POSITIONS_GET_PERFORMED": snapshot["POSITIONS_GET_PERFORMED"],
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT"),
        **{
            k: adjudication[k]
            for k in (
                "CREATE_ACCOUNT_IDENTITY_READY",
                "POSITION_MODE_SUBMIT_BODY_SEMANTICS",
                "POSITION_MODE_FAIL_CLOSED",
                "POSITION_MODE_READY",
                "PRETRADE_GATES_READY",
                "FUNDING_EXPOSURE_READY",
                "VENUE_NONZERO_CAPACITY",
                "CURRENT_ROUTE_C_QUANTITY_ADMISSIBILITY",
                "PREREQUISITE_08_CLOSED",
                "CREATE_READINESS_AFTER_FRESH_EVIDENCE",
                "CURRENT_PRODUCTIVE_WIRE_REACHABLE",
                "CREATE_PATH_CURRENTLY_AUTHORIZED",
            )
            if k in adjudication
        },
        "SECRET_VALUES_INCLUDED": False,
        "LIVE_AUTHORIZED": False,
        "SUBMIT_UNLOCKED": False,
        "EXECUTION_READY": False,
    }
    verified = persist_z2dp_create_readiness_evidence_v1(
        pack=pack,
        origin_main_sha=bound_sha,
        snapshot=snapshot,
        summary=summary,
        adjudication=adjudication,
    )
    result = {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "summary": summary,
        "adjudication": adjudication,
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT"),
        "NONZERO_HARD_STOP": observations.get("TARGET_POSITION_STATE")
        == TARGET_POSITION_NONZERO_PROVEN,
    }
    if observations.get("TARGET_POSITION_STATE") == TARGET_POSITION_NONZERO_PROVEN:
        raise Z2DPCreateReadinessGetError(f"NONZERO_TARGET_POSITION_HARD_STOP:{pack}")
    return result

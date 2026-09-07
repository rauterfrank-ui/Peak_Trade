"""GET-only pretrade orchestrator bound to a recorded current origin/main SHA.

Does not consume Owner-GO. Does not POST. Does not import submit transport.
"""

from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.bound_testnet_http_client_v1 import (
    assert_okx_access_timestamp_iso_ms_v1,
    format_okx_access_timestamp_iso_ms_v1,
    sign_okx_request_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_mode_observation_v1 import (
    ACCOUNT_MODE_REQUIRED_VALUE as CANARY_ACCOUNT_MODE_REQUIRED,
    acquire_fresh_account_mode_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    acquire_fresh_available_margin_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
    REQUIRED_SECRETREF_URI,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.instrument_state_observation_v1 import (
    acquire_fresh_instrument_state_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    account_leverage_info_query_path_v1,
    acquire_fresh_leverage_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryCredentialError,
    assert_no_plaintext_in_payload_v1,
    borrow_live_canary_ephemeral_material_for_session_auth_v1,
    build_file_secretref_vault_backend_v1,
    parse_okx_live_canary_material_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    POSITION_MGN_MODE_STATUS_NOT_OBSERVED,
    acquire_fresh_margin_mode_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    account_max_size_query_path_v1,
    acquire_fresh_max_available_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    extract_instrument_constraints_v1,
    extract_reference_price_v1,
    quantize_limit_price_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_REQUIRED_VALUE as CANARY_POS_MODE_REQUIRED,
    account_config_query_path_v1,
    acquire_fresh_pos_mode_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    acquire_fresh_price_band_observation_from_payload_v1,
    public_price_limit_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    SUI_OPERATIVE_ORDER_SZ_UNIT,
    canary_venue_contract_count_v1,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.constants_v1 import (
    ACCOUNT_MODE_REQUIRED_VALUE,
    ADJUDICATION_FILENAME,
    CENSUS_FILENAME,
    CLAIMS_FILENAME,
    ENDPOINT_PATH_ALLOWLIST,
    EXISTING_SURFACE_CENSUS,
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    GET_LOG_FILENAME,
    INSTRUMENT_STATE_REQUIRED,
    LEVERAGE_EXPECTED_MGN_MODE,
    LINEAGE_FILENAME,
    MAX_SUBMIT_ATTEMPTS,
    MAX_SUCCESSFUL_SUBMITS,
    OBSOLETE_FROZEN_ORIGIN_MAIN_SHA,
    ORDER_QTY,
    ORDER_QTY_UNIT,
    ORDER_TYPE,
    PATH_ACCOUNT_BALANCE,
    PATH_ACCOUNT_POSITIONS,
    PATH_MARKET_TICKER,
    PLANNED_TD_MODE,
    POS_MODE_REQUIRED_VALUE,
    PRIVATE_ENDPOINT_PATHS,
    PUBLIC_ENDPOINT_PATHS,
    REST_SCHEME_HOST,
    SCHEMA_VERSION,
    SIDE,
    SOURCE_EVIDENCE_CURRENT,
    SUMMARY_FILENAME,
    THIS_SLICE,
    USER_AGENT,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.http_get_only_v1 import (
    GetOnlyHttpClientV1,
    GetOnlyHttpError,
    GetOnlyTransportV1,
    UrllibGetOnlyTransportV1,
    endpoint_path_v1,
    parse_json_object_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)


class GetOnlyPretradeError(RuntimeError):
    """Fail-closed GET-only pretrade violation."""


HeaderProvider = Callable[[str], Mapping[str, str]]


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def assert_standing_live_flags_remain_false_v1() -> dict[str, bool]:
    flags = {
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": bool(
            SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED
        ),
        "POST_ALLOWED": bool(POST_ALLOWED),
    }
    if any(flags.values()):
        raised = ",".join(name for name, value in flags.items() if value)
        raise GetOnlyPretradeError(f"STANDING_LIVE_FLAG_MUST_REMAIN_FALSE:{raised}")
    return flags


def assert_origin_main_sha_is_recorded_not_obsolete_gate_v1(origin_main_sha: str) -> str:
    sha = str(origin_main_sha or "").strip().lower()
    if not sha or len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise GetOnlyPretradeError("ORIGIN_MAIN_SHA_REQUIRED")
    return sha


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _secret_needles() -> tuple[str, ...]:
    return (
        "api_secret",
        "api_key",
        "passphrase",
        "ok-access-sign",
        "ok-access-key",
        "ok-access-passphrase",
        "authorization: bearer",
        "plaintext:",
    )


def assert_no_secrets_in_mapping_v1(payload: Mapping[str, Any]) -> None:
    blob = str(payload).lower()
    for needle in _secret_needles():
        if needle in blob and needle in {"authorization: bearer", "plaintext:"}:
            raise GetOnlyPretradeError(f"SECRET_LEAK_DETECTED:{needle}")
    assert_no_plaintext_in_payload_v1(payload)


def build_get_only_auth_headers_v1(
    *,
    handle: Any,
    url: str,
    method: str = "GET",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    method_u = str(method or "").strip().upper()
    if method_u != "GET":
        raise GetOnlyPretradeError(f"GET_ONLY_SIGNER_METHOD_FORBIDDEN:{method_u or '<empty>'}")
    if extra_headers:
        for key in extra_headers:
            if str(key).strip().lower() in FORBIDDEN_DEMO_SIMULATION_HEADERS:
                raise GetOnlyPretradeError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key}")
    material: str | None = None
    creds: dict[str, str] | None = None
    try:
        material = borrow_live_canary_ephemeral_material_for_session_auth_v1(handle)
        creds = parse_okx_live_canary_material_v1(material)
        timestamp = assert_okx_access_timestamp_iso_ms_v1(format_okx_access_timestamp_iso_ms_v1())
        parsed = urlparse(url)
        request_path = parsed.path or ""
        if parsed.query:
            request_path = f"{request_path}?{parsed.query}"
        sign = sign_okx_request_v1(
            secret=creds["api_secret"],
            timestamp=timestamp,
            method="GET",
            request_path=request_path,
            body="",
        )
        headers = {
            "OK-ACCESS-KEY": creds["api_key"],
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": creds["passphrase"],
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        if extra_headers:
            headers.update({str(k): str(v) for k, v in extra_headers.items()})
        return headers
    finally:
        creds = None
        material = None


def _status_from_exception(exc: Exception) -> str:
    text = str(exc)
    if "INDETERMINATE_TIMEOUT" in text or isinstance(exc, TimeoutError):
        return "INDETERMINATE_TIMEOUT"
    if "HTTP_401" in text or "HTTP_403" in text or "AUTH" in text:
        return "AUTH_ERROR"
    return "FAIL_CLOSED"


def _predicate(
    *,
    status: str,
    extracted: Mapping[str, Any] | None,
    reason: str,
    observed_at_utc: str,
    endpoint: str,
    http_status: int | None,
    venue_code: str,
    body_sha256: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "extracted": dict(extracted or {}),
        "reason": reason,
        "observed_at_utc": observed_at_utc,
        "endpoint": endpoint,
        "http_status": http_status,
        "venue_code": venue_code,
        "body_sha256": body_sha256,
        "freshness_policy": "CURRENT_GET_ONLY_NO_HISTORICAL_SUBSTITUTION",
        "freshness_status": "CURRENT" if status in {"PASS", "NOT_OBSERVED"} else status,
        "historical_reuse": False,
    }


@dataclass
class _GetAttempt:
    endpoint: str
    observed_at_utc: str
    http_status: int | None
    venue_code: str
    body_sha256: str
    payload: dict[str, Any] | None
    error: str
    timeout: bool
    auth_header_sent: bool


def _one_get(
    *,
    client: GetOnlyHttpClientV1,
    endpoint: str,
    headers: Mapping[str, str] | None,
) -> _GetAttempt:
    observed = utc_now_iso_v1()
    path = endpoint_path_v1(endpoint)
    auth_sent = path in PRIVATE_ENDPOINT_PATHS
    try:
        response = client.get(endpoint=endpoint, headers=headers)
    except GetOnlyHttpError as exc:
        timeout = "INDETERMINATE_TIMEOUT" in str(exc)
        return _GetAttempt(
            endpoint=endpoint,
            observed_at_utc=observed,
            http_status=None,
            venue_code="",
            body_sha256="",
            payload=None,
            error=str(exc),
            timeout=timeout,
            auth_header_sent=auth_sent,
        )
    digest = hashlib.sha256(response.body_bytes).hexdigest()
    try:
        payload = parse_json_object_v1(response.body_bytes)
        venue_code = str(payload.get("code") or "")
        error = ""
    except GetOnlyHttpError as exc:
        payload = None
        venue_code = ""
        error = str(exc)
    return _GetAttempt(
        endpoint=endpoint,
        observed_at_utc=observed,
        http_status=int(response.status_code),
        venue_code=venue_code,
        body_sha256=digest,
        payload=payload,
        error=error,
        timeout=False,
        auth_header_sent=auth_sent,
    )


def _headers_for_endpoint(
    *,
    endpoint: str,
    rest_base: str,
    header_provider: HeaderProvider | None,
) -> Mapping[str, str] | None:
    path = endpoint_path_v1(endpoint)
    if path in PUBLIC_ENDPOINT_PATHS:
        return {"User-Agent": USER_AGENT}
    if header_provider is None:
        raise GetOnlyPretradeError(f"PRIVATE_HEADER_PROVIDER_REQUIRED:{path}")
    url = f"{rest_base.rstrip('/')}{endpoint}"
    return header_provider(url)


def extract_pre_existing_position_v1(
    *,
    payload: Mapping[str, Any],
    instrument_id: str,
) -> dict[str, str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return {"status": "MALFORMED", "pos": "", "posSide": "", "row_count": "invalid"}
    rows = [
        item
        for item in data
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id
    ]
    if not rows:
        return {
            "status": "NO_TARGET_ROW",
            "pos": "",
            "posSide": "",
            "row_count": str(len(data)),
        }
    if len(rows) != 1:
        return {
            "status": "AMBIGUOUS_TARGET_ROWS",
            "pos": "",
            "posSide": "",
            "row_count": str(len(rows)),
        }
    row = rows[0]
    if "pos" not in row or row.get("pos") is None:
        return {"status": "POS_FIELD_MISSING", "pos": "", "posSide": "", "row_count": "1"}
    return {
        "status": "OBSERVED",
        "pos": str(row.get("pos")).strip(),
        "posSide": str(row.get("posSide") or "").strip(),
        "row_count": "1",
    }


def _limit_px_within_band(*, px: str, buy_lmt: str, side: str) -> tuple[bool, str]:
    try:
        price = Decimal(px)
        buy = Decimal(buy_lmt)
    except (InvalidOperation, TypeError):
        return False, "PRICE_OR_BAND_UNPARSEABLE"
    if str(side).upper() != "BUY":
        return False, f"UNSUPPORTED_SIDE:{side}"
    if price <= 0:
        return False, "LIMIT_PRICE_NON_POSITIVE"
    if price > buy:
        return False, "LIMIT_PRICE_ABOVE_BUY_LMT"
    return True, "WITHIN_BUY_LMT"


def run_get_only_pretrade_readiness_v1(
    *,
    origin_main_sha: str,
    transport: GetOnlyTransportV1,
    header_provider: HeaderProvider | None = None,
    origin_main_tree: str = "",
    rest_host: str = REUSED_BINDING_REST_HOST,
    rest_base: str = REST_SCHEME_HOST,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    persist_root: Path | str | None = None,
    historical_reuse: bool = False,
) -> dict[str, Any]:
    """Execute the GET-only pretrade conjunction. No Owner-GO parameter exists."""
    if historical_reuse:
        raise GetOnlyPretradeError("HISTORICAL_EVIDENCE_MUST_NOT_BE_CURRENT")
    recorded_sha = assert_origin_main_sha_is_recorded_not_obsolete_gate_v1(origin_main_sha)
    if rest_host != REUSED_BINDING_REST_HOST:
        raise GetOnlyPretradeError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    flags = assert_standing_live_flags_remain_false_v1()
    decision = f"{SOURCE_EVIDENCE_CURRENT}:{recorded_sha[:12]}"
    client = GetOnlyHttpClientV1(transport=transport, rest_base=rest_base)
    gets: list[dict[str, Any]] = []
    predicates: dict[str, dict[str, Any]] = {}

    def record_get(attempt: _GetAttempt, name: str) -> None:
        gets.append(
            {
                "name": name,
                "endpoint": attempt.endpoint,
                "observed_at_utc": attempt.observed_at_utc,
                "http_status": attempt.http_status,
                "venue_code": attempt.venue_code,
                "body_sha256": attempt.body_sha256,
                "auth_header_sent": attempt.auth_header_sent,
                "timeout": attempt.timeout,
                "error": attempt.error,
                "method": "GET",
            }
        )

    instruments_ep = public_instruments_query_path_v1(instrument_id=instrument_id)
    ticker_ep = f"{PATH_MARKET_TICKER}?instId={instrument_id}"
    price_band_ep = public_price_limit_query_path_v1(instrument_id=instrument_id)
    config_ep = account_config_query_path_v1()
    balance_ep = PATH_ACCOUNT_BALANCE
    positions_ep = PATH_ACCOUNT_POSITIONS
    leverage_ep = account_leverage_info_query_path_v1(
        instrument_id=instrument_id,
        mgn_mode=LEVERAGE_EXPECTED_MGN_MODE,
    )

    inst_attempt = _one_get(
        client=client,
        endpoint=instruments_ep,
        headers=_headers_for_endpoint(
            endpoint=instruments_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(inst_attempt, "INSTRUMENT_STATE")
    tick_sz = ""
    ct_val = ""
    ref_px = ""
    limit_px = ""
    buy_lmt = ""
    sell_lmt = ""

    if inst_attempt.timeout:
        predicates["INSTRUMENT_STATE_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=inst_attempt.error,
            observed_at_utc=inst_attempt.observed_at_utc,
            endpoint=instruments_ep,
            http_status=inst_attempt.http_status,
            venue_code="",
            body_sha256="",
        )
    elif inst_attempt.payload is None or inst_attempt.http_status != 200:
        predicates["INSTRUMENT_STATE_CURRENT"] = _predicate(
            status="FAIL_CLOSED" if inst_attempt.error else "INDETERMINATE",
            extracted=None,
            reason=inst_attempt.error or f"HTTP_{inst_attempt.http_status}",
            observed_at_utc=inst_attempt.observed_at_utc,
            endpoint=instruments_ep,
            http_status=inst_attempt.http_status,
            venue_code=inst_attempt.venue_code,
            body_sha256=inst_attempt.body_sha256,
        )
    else:
        try:
            inst_obs = acquire_fresh_instrument_state_observation_from_payload_v1(
                pretrade_decision_id=decision,
                instruments_payload=inst_attempt.payload,
                instrument_id=instrument_id,
                observed_at_utc=inst_attempt.observed_at_utc,
                endpoint=instruments_ep,
                http_status=int(inst_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=False,
                historical_reuse=False,
                body_sha256=inst_attempt.body_sha256,
                request_started_at_utc=inst_attempt.observed_at_utc,
                request_finished_at_utc=inst_attempt.observed_at_utc,
            )
            constraints = extract_instrument_constraints_v1(
                instruments_payload=inst_attempt.payload,
                instrument_id=instrument_id,
            )
            tick_sz = str(constraints.get("tickSz") or "")
            ct_val = str(constraints.get("ctVal") or "")
            state = inst_obs.state_raw
            ok = state == INSTRUMENT_STATE_REQUIRED
            predicates["INSTRUMENT_STATE_CURRENT"] = _predicate(
                status="PASS" if ok else "FAIL_CLOSED",
                extracted={
                    "state": state,
                    "tickSz": tick_sz,
                    "ctVal": ct_val,
                    "instType": inst_obs.inst_type_raw,
                    "ruleType": inst_obs.rule_type_raw,
                },
                reason="" if ok else f"INSTRUMENT_STATE_NOT_LIVE:{state}",
                observed_at_utc=inst_attempt.observed_at_utc,
                endpoint=instruments_ep,
                http_status=inst_attempt.http_status,
                venue_code=inst_attempt.venue_code,
                body_sha256=inst_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001 — observation fail-closed
            predicates["INSTRUMENT_STATE_CURRENT"] = _predicate(
                status=_status_from_exception(exc),
                extracted=None,
                reason=str(exc),
                observed_at_utc=inst_attempt.observed_at_utc,
                endpoint=instruments_ep,
                http_status=inst_attempt.http_status,
                venue_code=inst_attempt.venue_code,
                body_sha256=inst_attempt.body_sha256,
            )

    ticker_attempt = _one_get(
        client=client,
        endpoint=ticker_ep,
        headers=_headers_for_endpoint(
            endpoint=ticker_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(ticker_attempt, "PRICE_SOURCE")
    if ticker_attempt.timeout:
        predicates["PRICE_SOURCE_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=ticker_attempt.error,
            observed_at_utc=ticker_attempt.observed_at_utc,
            endpoint=ticker_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )
    elif ticker_attempt.payload is None or ticker_attempt.http_status != 200:
        predicates["PRICE_SOURCE_CURRENT"] = _predicate(
            status="FAIL_CLOSED" if ticker_attempt.error else "INDETERMINATE",
            extracted=None,
            reason=ticker_attempt.error or f"HTTP_{ticker_attempt.http_status}",
            observed_at_utc=ticker_attempt.observed_at_utc,
            endpoint=ticker_ep,
            http_status=ticker_attempt.http_status,
            venue_code=ticker_attempt.venue_code,
            body_sha256=ticker_attempt.body_sha256,
        )
    else:
        try:
            ref_px = extract_reference_price_v1(ticker_payload=ticker_attempt.payload)
            predicates["PRICE_SOURCE_CURRENT"] = _predicate(
                status="PASS",
                extracted={
                    "source": "GET /api/v5/market/ticker last|askPx",
                    "reference_price": ref_px,
                },
                reason="",
                observed_at_utc=ticker_attempt.observed_at_utc,
                endpoint=ticker_ep,
                http_status=ticker_attempt.http_status,
                venue_code=ticker_attempt.venue_code,
                body_sha256=ticker_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001
            predicates["PRICE_SOURCE_CURRENT"] = _predicate(
                status=_status_from_exception(exc),
                extracted=None,
                reason=str(exc),
                observed_at_utc=ticker_attempt.observed_at_utc,
                endpoint=ticker_ep,
                http_status=ticker_attempt.http_status,
                venue_code=ticker_attempt.venue_code,
                body_sha256=ticker_attempt.body_sha256,
            )

    if predicates.get("PRICE_SOURCE_CURRENT", {}).get("status") == "PASS" and tick_sz and ref_px:
        try:
            limit_px = quantize_limit_price_v1(reference_price=ref_px, tick_sz=tick_sz)
        except Exception as exc:  # noqa: BLE001
            predicates["EXACT_PRICE_SEMANTICS_BOUND"] = _predicate(
                status="FAIL_CLOSED",
                extracted={"reference_price": ref_px, "tickSz": tick_sz},
                reason=str(exc),
                observed_at_utc=utc_now_iso_v1(),
                endpoint=ticker_ep,
                http_status=ticker_attempt.http_status,
                venue_code=ticker_attempt.venue_code,
                body_sha256=ticker_attempt.body_sha256,
            )

    band_attempt = _one_get(
        client=client,
        endpoint=price_band_ep,
        headers=_headers_for_endpoint(
            endpoint=price_band_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(band_attempt, "PRICE_BAND")
    if band_attempt.timeout:
        predicates["PRICE_BAND_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=band_attempt.error,
            observed_at_utc=band_attempt.observed_at_utc,
            endpoint=price_band_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )
    elif band_attempt.payload is None or band_attempt.http_status != 200:
        predicates["PRICE_BAND_CURRENT"] = _predicate(
            status="FAIL_CLOSED" if band_attempt.error else "INDETERMINATE",
            extracted=None,
            reason=band_attempt.error or f"HTTP_{band_attempt.http_status}",
            observed_at_utc=band_attempt.observed_at_utc,
            endpoint=price_band_ep,
            http_status=band_attempt.http_status,
            venue_code=band_attempt.venue_code,
            body_sha256=band_attempt.body_sha256,
        )
    else:
        try:
            band_obs = acquire_fresh_price_band_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=band_attempt.payload,
                instrument_id=instrument_id,
                observed_at_utc=band_attempt.observed_at_utc,
                endpoint=price_band_ep,
                http_status=int(band_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=False,
                historical_reuse=False,
                body_sha256=band_attempt.body_sha256,
            )
            buy_lmt = band_obs.buy_lmt_raw
            sell_lmt = band_obs.sell_lmt_raw
            predicates["PRICE_BAND_CURRENT"] = _predicate(
                status="PASS",
                extracted={"buyLmt": buy_lmt, "sellLmt": sell_lmt, "enabled": band_obs.enabled_raw},
                reason="",
                observed_at_utc=band_attempt.observed_at_utc,
                endpoint=price_band_ep,
                http_status=band_attempt.http_status,
                venue_code=band_attempt.venue_code,
                body_sha256=band_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001
            predicates["PRICE_BAND_CURRENT"] = _predicate(
                status=_status_from_exception(exc),
                extracted=None,
                reason=str(exc),
                observed_at_utc=band_attempt.observed_at_utc,
                endpoint=price_band_ep,
                http_status=band_attempt.http_status,
                venue_code=band_attempt.venue_code,
                body_sha256=band_attempt.body_sha256,
            )

    price_policy = (
        "LIMIT px = quantize_limit_price_v1(extract_reference_price_v1("
        "GET /api/v5/market/ticker last|askPx), tickSz from GET "
        "/api/v5/public/instruments) ROUND_DOWN; BUY requires px <= buyLmt from "
        "GET /api/v5/public/price-limit; then GET /api/v5/account/max-size?px="
    )
    if limit_px and buy_lmt:
        within, within_reason = _limit_px_within_band(px=limit_px, buy_lmt=buy_lmt, side=SIDE)
        predicates["EXACT_PRICE_SEMANTICS_BOUND"] = _predicate(
            status="PASS" if within else "FAIL_CLOSED",
            extracted={
                "PRICE_OR_PRICE_POLICY": price_policy,
                "EXECUTION_LIMIT_PRICE": limit_px,
                "reference_price": ref_px,
                "tickSz": tick_sz,
                "buyLmt": buy_lmt,
                "band_check": within_reason,
            },
            reason="" if within else within_reason,
            observed_at_utc=utc_now_iso_v1(),
            endpoint=price_band_ep,
            http_status=band_attempt.http_status,
            venue_code=band_attempt.venue_code,
            body_sha256=band_attempt.body_sha256,
        )
    elif "EXACT_PRICE_SEMANTICS_BOUND" not in predicates:
        predicates["EXACT_PRICE_SEMANTICS_BOUND"] = _predicate(
            status="INDETERMINATE",
            extracted={"PRICE_OR_PRICE_POLICY": price_policy, "EXECUTION_LIMIT_PRICE": limit_px},
            reason="LIMIT_PX_OR_BAND_NOT_CURRENT",
            observed_at_utc=utc_now_iso_v1(),
            endpoint=price_band_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )

    config_attempt = _one_get(
        client=client,
        endpoint=config_ep,
        headers=_headers_for_endpoint(
            endpoint=config_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(config_attempt, "ACCOUNT_CONFIG")
    session_auth_ok = (
        config_attempt.http_status == 200
        and config_attempt.venue_code == "0"
        and not config_attempt.timeout
        and config_attempt.auth_header_sent
    )
    if config_attempt.timeout:
        auth_status = "INDETERMINATE_TIMEOUT"
        net_status = "INDETERMINATE_TIMEOUT"
    elif config_attempt.http_status in {401, 403}:
        auth_status = "AUTH_ERROR"
        net_status = "PASS"
    elif config_attempt.http_status is None:
        auth_status = "INDETERMINATE"
        net_status = "FAIL_CLOSED" if config_attempt.error else "INDETERMINATE"
    elif session_auth_ok:
        auth_status = "PASS"
        net_status = "PASS"
    else:
        auth_status = "FAIL_CLOSED"
        net_status = "PASS" if config_attempt.http_status is not None else "INDETERMINATE"
    predicates["SESSION_AUTH_CURRENT"] = _predicate(
        status=auth_status,
        extracted={"auth_header_sent": config_attempt.auth_header_sent},
        reason=config_attempt.error,
        observed_at_utc=config_attempt.observed_at_utc,
        endpoint=config_ep,
        http_status=config_attempt.http_status,
        venue_code=config_attempt.venue_code,
        body_sha256=config_attempt.body_sha256,
    )
    predicates["NETWORK_EGRESS_COMPATIBILITY_CURRENT"] = _predicate(
        status=net_status,
        extracted={"rest_host": rest_host, "rest_base": rest_base},
        reason=config_attempt.error,
        observed_at_utc=config_attempt.observed_at_utc,
        endpoint=config_ep,
        http_status=config_attempt.http_status,
        venue_code=config_attempt.venue_code,
        body_sha256=config_attempt.body_sha256,
    )
    if config_attempt.timeout:
        predicates["ACCOUNT_MODE_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=config_attempt.error,
            observed_at_utc=config_attempt.observed_at_utc,
            endpoint=config_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )
        predicates["POSITION_MODE_CURRENT"] = predicates["ACCOUNT_MODE_CURRENT"]
    elif config_attempt.payload is None or config_attempt.http_status != 200:
        st = "AUTH_ERROR" if config_attempt.http_status in {401, 403} else "FAIL_CLOSED"
        predicates["ACCOUNT_MODE_CURRENT"] = _predicate(
            status=st,
            extracted=None,
            reason=config_attempt.error or f"HTTP_{config_attempt.http_status}",
            observed_at_utc=config_attempt.observed_at_utc,
            endpoint=config_ep,
            http_status=config_attempt.http_status,
            venue_code=config_attempt.venue_code,
            body_sha256=config_attempt.body_sha256,
        )
        predicates["POSITION_MODE_CURRENT"] = predicates["ACCOUNT_MODE_CURRENT"]
    else:
        try:
            acct_obs = acquire_fresh_account_mode_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=config_attempt.payload,
                instrument_id=instrument_id,
                observed_at_utc=config_attempt.observed_at_utc,
                endpoint=config_ep,
                http_status=int(config_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=True,
                historical_reuse=False,
                body_sha256=config_attempt.body_sha256,
                source_evidence=SOURCE_EVIDENCE_CURRENT,
            )
            pos_obs = acquire_fresh_pos_mode_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=config_attempt.payload,
                instrument_id=instrument_id,
                observed_at_utc=config_attempt.observed_at_utc,
                endpoint=config_ep,
                http_status=int(config_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=True,
                historical_reuse=False,
                body_sha256=config_attempt.body_sha256,
            )
            acct_ok = acct_obs.acct_lv_raw == ACCOUNT_MODE_REQUIRED_VALUE
            pos_ok = pos_obs.pos_mode_raw == POS_MODE_REQUIRED_VALUE
            uid_match = acct_obs.uid_raw == REUSED_BINDING_ACCOUNT_SCOPE
            predicates["ACCOUNT_MODE_CURRENT"] = _predicate(
                status="PASS" if acct_ok else "FAIL_CLOSED",
                extracted={
                    "acctLv": acct_obs.acct_lv_raw,
                    "uid_sha256": _sha256_hex(acct_obs.uid_raw),
                    "uid_matches_intended_account_scope": uid_match,
                    "required": CANARY_ACCOUNT_MODE_REQUIRED,
                },
                reason="" if acct_ok else f"ACCTLV_MISMATCH:{acct_obs.acct_lv_raw}",
                observed_at_utc=config_attempt.observed_at_utc,
                endpoint=config_ep,
                http_status=config_attempt.http_status,
                venue_code=config_attempt.venue_code,
                body_sha256=config_attempt.body_sha256,
            )
            predicates["POSITION_MODE_CURRENT"] = _predicate(
                status="PASS" if pos_ok else "FAIL_CLOSED",
                extracted={
                    "posMode": pos_obs.pos_mode_raw,
                    "required": CANARY_POS_MODE_REQUIRED,
                },
                reason="" if pos_ok else f"POSMODE_MISMATCH:{pos_obs.pos_mode_raw}",
                observed_at_utc=config_attempt.observed_at_utc,
                endpoint=config_ep,
                http_status=config_attempt.http_status,
                venue_code=config_attempt.venue_code,
                body_sha256=config_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001
            st = _status_from_exception(exc)
            predicates["ACCOUNT_MODE_CURRENT"] = _predicate(
                status=st,
                extracted=None,
                reason=str(exc),
                observed_at_utc=config_attempt.observed_at_utc,
                endpoint=config_ep,
                http_status=config_attempt.http_status,
                venue_code=config_attempt.venue_code,
                body_sha256=config_attempt.body_sha256,
            )
            predicates["POSITION_MODE_CURRENT"] = predicates["ACCOUNT_MODE_CURRENT"]

    balance_attempt = _one_get(
        client=client,
        endpoint=balance_ep,
        headers=_headers_for_endpoint(
            endpoint=balance_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(balance_attempt, "AVAILABLE_MARGIN")
    if balance_attempt.timeout:
        predicates["AVAILABLE_MARGIN_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=balance_attempt.error,
            observed_at_utc=balance_attempt.observed_at_utc,
            endpoint=balance_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )
    elif balance_attempt.payload is None or balance_attempt.http_status != 200:
        st = "AUTH_ERROR" if balance_attempt.http_status in {401, 403} else "FAIL_CLOSED"
        predicates["AVAILABLE_MARGIN_CURRENT"] = _predicate(
            status=st,
            extracted=None,
            reason=balance_attempt.error or f"HTTP_{balance_attempt.http_status}",
            observed_at_utc=balance_attempt.observed_at_utc,
            endpoint=balance_ep,
            http_status=balance_attempt.http_status,
            venue_code=balance_attempt.venue_code,
            body_sha256=balance_attempt.body_sha256,
        )
    else:
        try:
            margin_obs = acquire_fresh_available_margin_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=balance_attempt.payload,
                instrument_id=instrument_id,
                planned_td_mode=PLANNED_TD_MODE,
                observed_at_utc=balance_attempt.observed_at_utc,
                endpoint=balance_ep,
                http_status=int(balance_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=True,
                historical_reuse=False,
                body_sha256=balance_attempt.body_sha256,
            )
            predicates["AVAILABLE_MARGIN_CURRENT"] = _predicate(
                status="PASS",
                extracted={
                    "selected_ccy": margin_obs.selected_ccy,
                    "availEq": margin_obs.avail_eq_raw,
                    "avail_eq_status": margin_obs.avail_eq_status,
                },
                reason="",
                observed_at_utc=balance_attempt.observed_at_utc,
                endpoint=balance_ep,
                http_status=balance_attempt.http_status,
                venue_code=balance_attempt.venue_code,
                body_sha256=balance_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001
            predicates["AVAILABLE_MARGIN_CURRENT"] = _predicate(
                status=_status_from_exception(exc),
                extracted=None,
                reason=str(exc),
                observed_at_utc=balance_attempt.observed_at_utc,
                endpoint=balance_ep,
                http_status=balance_attempt.http_status,
                venue_code=balance_attempt.venue_code,
                body_sha256=balance_attempt.body_sha256,
            )

    pos_attempt = _one_get(
        client=client,
        endpoint=positions_ep,
        headers=_headers_for_endpoint(
            endpoint=positions_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(pos_attempt, "POSITIONS")
    if pos_attempt.timeout:
        predicates["MARGIN_MODE_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=pos_attempt.error,
            observed_at_utc=pos_attempt.observed_at_utc,
            endpoint=positions_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )
        predicates["EXPECTED_PRE_EXISTING_POSITION"] = predicates["MARGIN_MODE_CURRENT"]
    elif pos_attempt.payload is None or pos_attempt.http_status != 200:
        st = "AUTH_ERROR" if pos_attempt.http_status in {401, 403} else "FAIL_CLOSED"
        predicates["MARGIN_MODE_CURRENT"] = _predicate(
            status=st,
            extracted=None,
            reason=pos_attempt.error or f"HTTP_{pos_attempt.http_status}",
            observed_at_utc=pos_attempt.observed_at_utc,
            endpoint=positions_ep,
            http_status=pos_attempt.http_status,
            venue_code=pos_attempt.venue_code,
            body_sha256=pos_attempt.body_sha256,
        )
        predicates["EXPECTED_PRE_EXISTING_POSITION"] = predicates["MARGIN_MODE_CURRENT"]
    else:
        try:
            mgn_obs = acquire_fresh_margin_mode_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=pos_attempt.payload,
                instrument_id=instrument_id,
                planned_td_mode=PLANNED_TD_MODE,
                observed_at_utc=pos_attempt.observed_at_utc,
                endpoint=positions_ep,
                http_status=int(pos_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=True,
                historical_reuse=False,
                body_sha256=pos_attempt.body_sha256,
            )
            pos_ex = extract_pre_existing_position_v1(
                payload=pos_attempt.payload,
                instrument_id=instrument_id,
            )
            if mgn_obs.position_mgn_mode_status == POSITION_MGN_MODE_STATUS_NOT_OBSERVED:
                mgn_status = "NOT_OBSERVED"
                mgn_reason = "NO_TARGET_POSITION_ROW_CURRENT_GET"
            elif mgn_obs.position_mgn_mode_raw == PLANNED_TD_MODE:
                mgn_status = "PASS"
                mgn_reason = ""
            else:
                mgn_status = "FAIL_CLOSED"
                mgn_reason = f"MGNMODE_MISMATCH:{mgn_obs.position_mgn_mode_raw}"
            predicates["MARGIN_MODE_CURRENT"] = _predicate(
                status=mgn_status,
                extracted={
                    "mgnMode": mgn_obs.position_mgn_mode_raw,
                    "position_mgn_mode_status": mgn_obs.position_mgn_mode_status,
                    "planned_td_mode": PLANNED_TD_MODE,
                },
                reason=mgn_reason,
                observed_at_utc=pos_attempt.observed_at_utc,
                endpoint=positions_ep,
                http_status=pos_attempt.http_status,
                venue_code=pos_attempt.venue_code,
                body_sha256=pos_attempt.body_sha256,
            )
            pos_status = (
                "PASS" if pos_ex["status"] in {"OBSERVED", "NO_TARGET_ROW"} else "FAIL_CLOSED"
            )
            if pos_ex["status"] == "NO_TARGET_ROW":
                pos_status = "NOT_OBSERVED"
            predicates["EXPECTED_PRE_EXISTING_POSITION"] = _predicate(
                status=pos_status,
                extracted=pos_ex,
                reason="" if pos_status in {"PASS", "NOT_OBSERVED"} else pos_ex["status"],
                observed_at_utc=pos_attempt.observed_at_utc,
                endpoint=positions_ep,
                http_status=pos_attempt.http_status,
                venue_code=pos_attempt.venue_code,
                body_sha256=pos_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001
            predicates["MARGIN_MODE_CURRENT"] = _predicate(
                status=_status_from_exception(exc),
                extracted=None,
                reason=str(exc),
                observed_at_utc=pos_attempt.observed_at_utc,
                endpoint=positions_ep,
                http_status=pos_attempt.http_status,
                venue_code=pos_attempt.venue_code,
                body_sha256=pos_attempt.body_sha256,
            )
            predicates["EXPECTED_PRE_EXISTING_POSITION"] = predicates["MARGIN_MODE_CURRENT"]

    lev_attempt = _one_get(
        client=client,
        endpoint=leverage_ep,
        headers=_headers_for_endpoint(
            endpoint=leverage_ep, rest_base=rest_base, header_provider=header_provider
        ),
    )
    record_get(lev_attempt, "LEVERAGE")
    if lev_attempt.timeout:
        predicates["LEVERAGE_CURRENT"] = _predicate(
            status="INDETERMINATE_TIMEOUT",
            extracted=None,
            reason=lev_attempt.error,
            observed_at_utc=lev_attempt.observed_at_utc,
            endpoint=leverage_ep,
            http_status=None,
            venue_code="",
            body_sha256="",
        )
    elif lev_attempt.payload is None or lev_attempt.http_status != 200:
        st = "AUTH_ERROR" if lev_attempt.http_status in {401, 403} else "FAIL_CLOSED"
        predicates["LEVERAGE_CURRENT"] = _predicate(
            status=st,
            extracted=None,
            reason=lev_attempt.error or f"HTTP_{lev_attempt.http_status}",
            observed_at_utc=lev_attempt.observed_at_utc,
            endpoint=leverage_ep,
            http_status=lev_attempt.http_status,
            venue_code=lev_attempt.venue_code,
            body_sha256=lev_attempt.body_sha256,
        )
    else:
        try:
            lev_obs = acquire_fresh_leverage_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=lev_attempt.payload,
                instrument_id=instrument_id,
                mgn_mode=LEVERAGE_EXPECTED_MGN_MODE,
                observed_at_utc=lev_attempt.observed_at_utc,
                endpoint=leverage_ep,
                http_status=int(lev_attempt.http_status or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=True,
                historical_reuse=False,
                body_sha256=lev_attempt.body_sha256,
            )
            predicates["LEVERAGE_CURRENT"] = _predicate(
                status="PASS" if lev_obs.lever_raw else "FAIL_CLOSED",
                extracted={
                    "lever": lev_obs.lever_raw,
                    "mgnMode": lev_obs.mgn_mode_raw,
                    "posSide": lev_obs.pos_side_raw,
                },
                reason="" if lev_obs.lever_raw else "LEVER_EMPTY",
                observed_at_utc=lev_attempt.observed_at_utc,
                endpoint=leverage_ep,
                http_status=lev_attempt.http_status,
                venue_code=lev_attempt.venue_code,
                body_sha256=lev_attempt.body_sha256,
            )
        except Exception as exc:  # noqa: BLE001
            predicates["LEVERAGE_CURRENT"] = _predicate(
                status=_status_from_exception(exc),
                extracted=None,
                reason=str(exc),
                observed_at_utc=lev_attempt.observed_at_utc,
                endpoint=leverage_ep,
                http_status=lev_attempt.http_status,
                venue_code=lev_attempt.venue_code,
                body_sha256=lev_attempt.body_sha256,
            )

    max_ep = ""
    if limit_px:
        try:
            max_ep = account_max_size_query_path_v1(
                instrument_id=instrument_id,
                td_mode=PLANNED_TD_MODE,
                px=limit_px,
                order_type=ORDER_TYPE,
            )
        except Exception as exc:  # noqa: BLE001
            predicates["MAX_AVAILABLE_MAX_SIZE_CURRENT"] = _predicate(
                status="FAIL_CLOSED",
                extracted={"px": limit_px},
                reason=str(exc),
                observed_at_utc=utc_now_iso_v1(),
                endpoint="",
                http_status=None,
                venue_code="",
                body_sha256="",
            )
    if max_ep:
        max_attempt = _one_get(
            client=client,
            endpoint=max_ep,
            headers=_headers_for_endpoint(
                endpoint=max_ep, rest_base=rest_base, header_provider=header_provider
            ),
        )
        record_get(max_attempt, "MAX_SIZE")
        if max_attempt.timeout:
            predicates["MAX_AVAILABLE_MAX_SIZE_CURRENT"] = _predicate(
                status="INDETERMINATE_TIMEOUT",
                extracted=None,
                reason=max_attempt.error,
                observed_at_utc=max_attempt.observed_at_utc,
                endpoint=max_ep,
                http_status=None,
                venue_code="",
                body_sha256="",
            )
        elif max_attempt.payload is None or max_attempt.http_status != 200:
            st = "AUTH_ERROR" if max_attempt.http_status in {401, 403} else "FAIL_CLOSED"
            predicates["MAX_AVAILABLE_MAX_SIZE_CURRENT"] = _predicate(
                status=st,
                extracted=None,
                reason=max_attempt.error or f"HTTP_{max_attempt.http_status}",
                observed_at_utc=max_attempt.observed_at_utc,
                endpoint=max_ep,
                http_status=max_attempt.http_status,
                venue_code=max_attempt.venue_code,
                body_sha256=max_attempt.body_sha256,
            )
        else:
            try:
                max_obs = acquire_fresh_max_available_observation_from_payload_v1(
                    pretrade_decision_id=decision,
                    payload=max_attempt.payload,
                    instrument_id=instrument_id,
                    td_mode=PLANNED_TD_MODE,
                    px_sent=limit_px,
                    order_type=ORDER_TYPE,
                    observed_at_utc=max_attempt.observed_at_utc,
                    endpoint=max_ep,
                    http_status=int(max_attempt.http_status or 0),
                    get_performed=True,
                    rest_host=rest_host,
                    auth_header_sent=True,
                    historical_reuse=False,
                    body_sha256=max_attempt.body_sha256,
                )
                predicates["MAX_AVAILABLE_MAX_SIZE_CURRENT"] = _predicate(
                    status="PASS",
                    extracted={
                        "maxBuy": max_obs.max_buy_raw,
                        "maxSell": max_obs.max_sell_raw,
                        "px_sent": limit_px,
                    },
                    reason="",
                    observed_at_utc=max_attempt.observed_at_utc,
                    endpoint=max_ep,
                    http_status=max_attempt.http_status,
                    venue_code=max_attempt.venue_code,
                    body_sha256=max_attempt.body_sha256,
                )
            except Exception as exc:  # noqa: BLE001
                predicates["MAX_AVAILABLE_MAX_SIZE_CURRENT"] = _predicate(
                    status=_status_from_exception(exc),
                    extracted=None,
                    reason=str(exc),
                    observed_at_utc=max_attempt.observed_at_utc,
                    endpoint=max_ep,
                    http_status=max_attempt.http_status,
                    venue_code=max_attempt.venue_code,
                    body_sha256=max_attempt.body_sha256,
                )
    elif "MAX_AVAILABLE_MAX_SIZE_CURRENT" not in predicates:
        predicates["MAX_AVAILABLE_MAX_SIZE_CURRENT"] = _predicate(
            status="INDETERMINATE",
            extracted=None,
            reason="MAX_SIZE_REQUIRES_CURRENT_LIMIT_PX",
            observed_at_utc=utc_now_iso_v1(),
            endpoint="",
            http_status=None,
            venue_code="",
            body_sha256="",
        )

    derived_notional = "UNKNOWN"
    if limit_px and ct_val:
        try:
            derived_notional = format(
                Decimal(canary_venue_contract_count_v1()) * Decimal(ct_val) * Decimal(limit_px),
                "f",
            )
        except (InvalidOperation, TypeError):
            derived_notional = "UNKNOWN"

    required_pass = (
        "SESSION_AUTH_CURRENT",
        "NETWORK_EGRESS_COMPATIBILITY_CURRENT",
        "ACCOUNT_MODE_CURRENT",
        "POSITION_MODE_CURRENT",
        "LEVERAGE_CURRENT",
        "INSTRUMENT_STATE_CURRENT",
        "AVAILABLE_MARGIN_CURRENT",
        "MAX_AVAILABLE_MAX_SIZE_CURRENT",
        "PRICE_BAND_CURRENT",
        "PRICE_SOURCE_CURRENT",
        "EXACT_PRICE_SEMANTICS_BOUND",
    )
    # MARGIN_MODE_CURRENT and EXPECTED_PRE_EXISTING_POSITION may be NOT_OBSERVED
    # on a current empty positions GET; that is current evidence, not PASS.
    all_required = all(predicates.get(name, {}).get("status") == "PASS" for name in required_pass)
    missing: list[str] = [
        name for name in required_pass if predicates.get(name, {}).get("status") != "PASS"
    ]
    if predicates.get("MARGIN_MODE_CURRENT", {}).get("status") not in {"PASS", "NOT_OBSERVED"}:
        missing.append("MARGIN_MODE_CURRENT")
        all_required = False
    if predicates.get("EXPECTED_PRE_EXISTING_POSITION", {}).get("status") not in {
        "PASS",
        "NOT_OBSERVED",
    }:
        missing.append("EXPECTED_PRE_EXISTING_POSITION")
        all_required = False
    missing.extend(["EXPECTED_FEES", "SLIPPAGE_BOUND"])
    envelope_complete = all_required and derived_notional != "UNKNOWN"
    # Standing fee/slippage policy is not bound as CURRENT; keep envelope incomplete.
    envelope_complete = False
    technical_ready = False

    get_success = sum(
        1 for item in gets if item["http_status"] == 200 and item["venue_code"] == "0"
    )
    get_timeout = sum(1 for item in gets if item["timeout"])
    get_failure = len(gets) - get_success - get_timeout

    result: dict[str, Any] = {
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO_CONSUMED": False,
        "OWNER_GO_PARAMETER_PRESENT": "owner_go"
        in inspect.signature(run_get_only_pretrade_readiness_v1).parameters,
        "OBSOLETE_SHA_GATE_USED": False,
        "OBSOLETE_FROZEN_ORIGIN_MAIN_SHA": OBSOLETE_FROZEN_ORIGIN_MAIN_SHA,
        "RECORDED_ORIGIN_MAIN_SHA": recorded_sha,
        "RECORDED_ORIGIN_MAIN_TREE": str(origin_main_tree or ""),
        "GET_ONLY_ENDPOINT_ALLOWLIST": list(ENDPOINT_PATH_ALLOWLIST),
        "GET_ONLY_SURFACE_POST_REACHABLE": False,
        "GET_ONLY_SURFACE_SUBMIT_REACHABLE": False,
        "STANDING_FLAGS": flags,
        "PRIVATE_GET_EXECUTED": any(
            endpoint_path_v1(item["endpoint"]) in PRIVATE_ENDPOINT_PATHS for item in gets
        ),
        "GET_ENDPOINT_COUNT": len(gets),
        "GET_SUCCESS_COUNT": get_success,
        "GET_FAILURE_COUNT": get_failure,
        "GET_TIMEOUT_COUNT": get_timeout,
        "GETS": gets,
        "PREDICATES": predicates,
        "EXISTING_SURFACE_CENSUS": [dict(row) for row in EXISTING_SURFACE_CENSUS],
        "PRICE_OR_PRICE_POLICY": price_policy,
        "EXECUTION_LIMIT_PRICE": limit_px or "UNKNOWN",
        "EXPECTED_MAX_NOTIONAL": derived_notional,
        "EXPECTED_FEES": "UNKNOWN",
        "SLIPPAGE_BOUND": "UNKNOWN",
        "EXACT_VENUE_BOUND": True,
        "EXACT_ACCOUNT_CONTEXT_BOUND": predicates.get("ACCOUNT_MODE_CURRENT", {}).get("status")
        == "PASS",
        "EXACT_INSTRUMENT_BOUND": True,
        "EXACT_SIDE_BOUND": True,
        "EXACT_SIZE_BOUND": True,
        "EXACT_SIZE_UNIT_BOUND": True,
        "EXACT_ORDER_TYPE_BOUND": True,
        "EXACT_PRICE_SEMANTICS_BOUND": predicates.get("EXACT_PRICE_SEMANTICS_BOUND", {}).get(
            "status"
        )
        == "PASS",
        "ORDER_QTY": ORDER_QTY,
        "ORDER_QTY_SOURCE": "SUI_OPERATIVE_ORDER_SZ",
        "ORDER_QTY_UNIT": ORDER_QTY_UNIT,
        "VENUE_CONTRACT_COUNT": canary_venue_contract_count_v1(),
        "VENUE_CONTRACT_COUNT_UNIT": SUI_OPERATIVE_ORDER_SZ_UNIT,
        "SIDE": SIDE,
        "ORDER_TYPE": ORDER_TYPE,
        "INSTRUMENT_ID": instrument_id,
        "REST_HOST": rest_host,
        "ACCOUNT_SCOPE_INTENDED": REUSED_BINDING_ACCOUNT_SCOPE,
        "MAX_SUBMIT_ATTEMPTS": MAX_SUBMIT_ATTEMPTS,
        "MAX_SUCCESSFUL_SUBMITS": MAX_SUCCESSFUL_SUBMITS,
        "RETRY_AFTER_AMBIGUOUS_WIRE_RESULT": False,
        "RETRY_AFTER_TIMEOUT": False,
        "RETRY_AFTER_UNKNOWN_VENUE_RESULT": False,
        "ALL_REQUIRED_PRETRADE_PREDICATES": all_required,
        "MISSING_EXECUTION_ENVELOPE_FIELDS": missing,
        "EXACT_EXECUTION_ENVELOPE_COMPLETE": envelope_complete,
        "TECHNICAL_EXECUTION_READY": technical_ready,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "MUTATING_EXECUTION_ALLOWED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "COUNTERS": client.counters.to_dict(),
    }
    assert_no_secrets_in_mapping_v1(result)
    if persist_root is not None:
        persist_get_only_pretrade_evidence_v1(root=Path(persist_root), result=result)
    return result


def persist_get_only_pretrade_evidence_v1(
    *, root: Path, result: Mapping[str, Any]
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    predicates = dict(result.get("PREDICATES") or {})
    summary = {
        "THIS_SLICE": result.get("THIS_SLICE"),
        "RECORDED_ORIGIN_MAIN_SHA": result.get("RECORDED_ORIGIN_MAIN_SHA"),
        "GET_ENDPOINT_COUNT": result.get("GET_ENDPOINT_COUNT"),
        "GET_SUCCESS_COUNT": result.get("GET_SUCCESS_COUNT"),
        "GET_FAILURE_COUNT": result.get("GET_FAILURE_COUNT"),
        "GET_TIMEOUT_COUNT": result.get("GET_TIMEOUT_COUNT"),
        "TECHNICAL_EXECUTION_READY": result.get("TECHNICAL_EXECUTION_READY"),
        "EXACT_EXECUTION_ENVELOPE_COMPLETE": result.get("EXACT_EXECUTION_ENVELOPE_COMPLETE"),
        "MISSING_EXECUTION_ENVELOPE_FIELDS": result.get("MISSING_EXECUTION_ENVELOPE_FIELDS"),
        "EXECUTION_LIMIT_PRICE": result.get("EXECUTION_LIMIT_PRICE"),
        "PRICE_OR_PRICE_POLICY": result.get("PRICE_OR_PRICE_POLICY"),
        "EXPECTED_MAX_NOTIONAL": result.get("EXPECTED_MAX_NOTIONAL"),
        "EXPECTED_FEES": result.get("EXPECTED_FEES"),
        "SLIPPAGE_BOUND": result.get("SLIPPAGE_BOUND"),
        "OWNER_EXECUTION_AUTHORIZED": False,
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "PREDICATE_STATUS": {
            name: (predicates.get(name) or {}).get("status") for name in sorted(predicates)
        },
    }
    claims = {
        "GET_ONLY": True,
        "POST_PERFORMED": False,
        "OWNER_GO_CONSUMED": False,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "TECHNICAL_EXECUTION_READY": result.get("TECHNICAL_EXECUTION_READY"),
    }
    files = (
        SUMMARY_FILENAME,
        CLAIMS_FILENAME,
        ADJUDICATION_FILENAME,
        CENSUS_FILENAME,
        GET_LOG_FILENAME,
        LINEAGE_FILENAME,
    )
    write_json_v1(root / SUMMARY_FILENAME, summary)
    write_json_v1(root / CLAIMS_FILENAME, claims)
    write_json_v1(root / ADJUDICATION_FILENAME, dict(result.get("PREDICATES") or {}))
    write_json_v1(
        root / CENSUS_FILENAME, {"EXISTING_SURFACE_CENSUS": result.get("EXISTING_SURFACE_CENSUS")}
    )
    write_json_v1(root / GET_LOG_FILENAME, {"GETS": result.get("GETS")})
    write_json_v1(
        root / LINEAGE_FILENAME,
        {
            "RECORDED_ORIGIN_MAIN_SHA": result.get("RECORDED_ORIGIN_MAIN_SHA"),
            "RECORDED_ORIGIN_MAIN_TREE": result.get("RECORDED_ORIGIN_MAIN_TREE"),
            "OBSOLETE_SHA_GATE_USED": False,
        },
    )
    write_manifest_v1(root, files)
    verify = verify_manifest_v1(root)
    if int(verify.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise GetOnlyPretradeError(f"MANIFEST_VERIFY_FAILED:{verify}")
    return verify


def execute_current_origin_main_bound_get_only_pretrade_v1(
    *,
    vault_file: Path | str,
    origin_main_sha: str,
    origin_main_tree: str = "",
    persist_root: Path | str | None = None,
    secret_reference: str = REQUIRED_SECRETREF_URI,
    transport: GetOnlyTransportV1 | None = None,
) -> dict[str, Any]:
    """Productive GET-only execute. No Owner-GO. No POST."""
    handle = None
    try:
        vault = build_file_secretref_vault_backend_v1(vault_file=vault_file)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=secret_reference,
            vault_backend=vault,
        )

        def header_provider(url: str) -> Mapping[str, str]:
            return build_get_only_auth_headers_v1(handle=handle, url=url, method="GET")

        return run_get_only_pretrade_readiness_v1(
            origin_main_sha=origin_main_sha,
            origin_main_tree=origin_main_tree,
            transport=transport or UrllibGetOnlyTransportV1(),
            header_provider=header_provider,
            persist_root=persist_root,
        )
    except LiveCanaryCredentialError as exc:
        raise GetOnlyPretradeError(f"CREDENTIAL_RESOLVE_FAILED:{exc}") from exc
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

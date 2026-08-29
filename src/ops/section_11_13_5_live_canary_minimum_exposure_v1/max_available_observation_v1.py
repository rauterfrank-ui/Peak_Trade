"""Decision-bound fresh MAX_AVAILABLE observation for §11.13.5 pretrade.

Owner-adjudicated operative source is authenticated GET /api/v5/account/max-size.
Historical max-avail-size / BTC windows are not an operative cache. No TTL.
No POST. No trading.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode, urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_UNIT,
)

MAX_AVAILABLE_ENDPOINT_PATH = "/api/v5/account/max-size"
MAX_AVAILABLE_UNIT = "contracts"
MAX_AVAILABLE_COMPARISON_DOMAIN = "VENUE_CONTRACT_COUNT"
MAX_AVAILABLE_PX_SOURCE = "ORDER_PLAN_LIMIT_PX"
MAX_AVAILABLE_LEVERAGE_REQUEST_POLICY = "OMIT"
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF = True
ACCOUNT_MODE = "UNPROVEN"
ACCOUNT_MODE_PROOF_STATUS = "UNPROVEN"
MARGIN_MODE = "UNPROVEN"
OBSERVATION_CLASS_SUCCESS_NUMERIC = "SUCCESS_NUMERIC"
OBSERVATION_CLASS_UNSUPPORTED_ACCOUNT_MODE = "UNSUPPORTED_ACCOUNT_MODE"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
MAX_RAW_DIGIT_LEN = 40
_SCIENTIFIC_NOTATION = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+")
HISTORICAL_Z2V_PACK = "section_11_13_5_z2v_negative_account_runtime_probe_v1"
HISTORICAL_S_MAX_AVAIL_PACK = "section_11_13_5_operational_funding_get_evidence_v1"
HISTORICAL_SUPERSEDED_MAX_AVAIL_SIZE_PATH = "/api/v5/account/max-avail-size"
HISTORICAL_BTC_INSTRUMENT_ID = "BTC-USD_UM_XPERP-310404"


class LiveCanaryMaxAvailableObservationError(RuntimeError):
    """Fail-closed fresh MAX_AVAILABLE observation violation."""


@dataclass(frozen=True)
class FreshMaxAvailableObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    instrument_id: str
    td_mode: str
    px_sent: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    max_buy_raw: str
    max_sell_raw: str
    quantity_domain: str
    max_available_unit: str
    historical_reuse: bool
    body_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pretrade_decision_id": self.pretrade_decision_id,
            "observed_at_utc": self.observed_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "instrument_id": self.instrument_id,
            "td_mode": self.td_mode,
            "px_sent": self.px_sent,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "max_buy_raw": self.max_buy_raw,
            "max_sell_raw": self.max_sell_raw,
            "quantity_domain": self.quantity_domain,
            "max_available_unit": self.max_available_unit,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
        }


@dataclass(frozen=True)
class ValidatedFreshMaxAvailableObservationV1:
    raw: FreshMaxAvailableObservationV1
    max_buy: Decimal
    max_sell: Decimal
    comparison_domain: str


def account_max_size_query_path_v1(
    *,
    instrument_id: str,
    td_mode: str,
    px: str | None = None,
    order_type: str = "LIMIT",
) -> str:
    inst = str(instrument_id or "").strip()
    mode = str(td_mode or "").strip()
    selected_type = str(order_type or "").strip().upper()
    if not inst:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_INSTID_REQUIRED")
    if not mode:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_TDMODE_REQUIRED")
    params: list[tuple[str, str]] = [("instId", inst), ("tdMode", mode)]
    px_text = str(px or "").strip()
    if selected_type == "LIMIT":
        if not px_text:
            raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_LIMIT_PX_REQUIRED")
        params.append(("px", px_text))
    elif selected_type == "MARKET":
        if px_text:
            raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_MARKET_PX_FORBIDDEN")
    else:
        raise LiveCanaryMaxAvailableObservationError(
            f"UNSUPPORTED_ORDER_TYPE_FOR_MAX_AVAILABLE:{selected_type}"
        )
    return f"{MAX_AVAILABLE_ENDPOINT_PATH}?{urlencode(params)}"


def classify_max_available_observation_class_v1(
    *,
    get_performed: bool,
    http_status: int,
    payload: Mapping[str, Any] | None,
) -> str:
    if not get_performed:
        return OBSERVATION_CLASS_NOT_PERFORMED
    status = int(http_status)
    if status in {401, 403}:
        return OBSERVATION_CLASS_AUTH_ERROR
    if status != 200:
        return OBSERVATION_CLASS_NETWORK_ERROR
    if not isinstance(payload, Mapping):
        return OBSERVATION_CLASS_MALFORMED
    code = str(payload.get("code") or "").strip()
    if code != "0":
        msg = str(payload.get("msg") or "").lower()
        if "not supported" in msg and (
            "portfolio" in msg or "account mode" in msg or "account-mode" in msg
        ):
            return OBSERVATION_CLASS_UNSUPPORTED_ACCOUNT_MODE
        return OBSERVATION_CLASS_VENUE_ERROR
    return OBSERVATION_CLASS_SUCCESS_NUMERIC


def account_mode_support_for_max_size_cross_derivatives_v1(*, observation_class: str) -> str:
    if observation_class == OBSERVATION_CLASS_SUCCESS_NUMERIC:
        return "PROVEN_SUPPORTED"
    if observation_class == OBSERVATION_CLASS_UNSUPPORTED_ACCOUNT_MODE:
        return "PROVEN_UNSUPPORTED"
    return "UNPROVEN"


def _raise_for_observation_class(observation_class: str) -> None:
    if observation_class == OBSERVATION_CLASS_SUCCESS_NUMERIC:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "MAX_AVAILABLE_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "MAX_AVAILABLE_NETWORK_ERROR",
        OBSERVATION_CLASS_UNSUPPORTED_ACCOUNT_MODE: "MAX_AVAILABLE_BLOCKED_BY_ACCOUNT_MODE_SUPPORT",
        OBSERVATION_CLASS_VENUE_ERROR: "MAX_AVAILABLE_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "MAX_AVAILABLE_MALFORMED",
    }
    raise LiveCanaryMaxAvailableObservationError(
        mapping.get(observation_class, f"MAX_AVAILABLE_FAIL_CLOSED:{observation_class}")
    )


def select_max_available_field_for_side_v1(*, side: str) -> str:
    selected = str(side or "").strip().upper()
    if selected == "BUY":
        return "maxBuy"
    if selected == "SELL":
        return "maxSell"
    raise LiveCanaryMaxAvailableObservationError(f"UNSUPPORTED_SIDE_FOR_MAX_AVAILABLE:{selected}")


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryMaxAvailableObservationError("HISTORICAL_MAX_AVAILABLE_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    if HISTORICAL_Z2V_PACK in decision or HISTORICAL_Z2V_PACK in ep:
        raise LiveCanaryMaxAvailableObservationError("HISTORICAL_Z2V_WINDOW_REUSE_FORBIDDEN")
    if HISTORICAL_S_MAX_AVAIL_PACK in decision or HISTORICAL_S_MAX_AVAIL_PACK in ep:
        raise LiveCanaryMaxAvailableObservationError(
            "HISTORICAL_MAX_AVAIL_SIZE_PACK_REUSE_FORBIDDEN"
        )
    if HISTORICAL_SUPERSEDED_MAX_AVAIL_SIZE_PATH in ep:
        raise LiveCanaryMaxAvailableObservationError("SUPERSEDED_MAX_AVAIL_SIZE_ENDPOINT_FORBIDDEN")
    if "leverage=" in ep:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_LEVERAGE_QUERY_FORBIDDEN")
    if HISTORICAL_BTC_INSTRUMENT_ID in ep or instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryMaxAvailableObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")


def _require_non_negative_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_FIELD_NULL:{field}")
    text = str(raw).strip()
    if not text:
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_FIELD_MISSING:{field}")
    lowered = text.lower()
    if lowered in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_FIELD_NON_NUMERIC:{field}")
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_FIELD_OUT_OF_DOMAIN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryMaxAvailableObservationError(
            f"MAX_AVAILABLE_FIELD_NON_NUMERIC:{field}"
        ) from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_FIELD_NON_NUMERIC:{field}")
    if value < 0:
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_FIELD_NEGATIVE:{field}")
    return value


def _target_row(
    *,
    payload: Mapping[str, Any],
    instrument_id: str,
) -> Mapping[str, Any]:
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryMaxAvailableObservationError(str(exc)) from exc
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryMaxAvailableObservationError(
            f"MAX_AVAILABLE_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_DATA_MISSING")
    row = None
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            row = item
            break
    if row is None:
        if len(data) == 1 and isinstance(data[0], Mapping) and not str(data[0].get("instId") or ""):
            raise LiveCanaryMaxAvailableObservationError(f"INSTRUMENT_MISMATCH:{instrument_id}")
        raise LiveCanaryMaxAvailableObservationError(f"INSTRUMENT_MISMATCH:{instrument_id}")
    return row


def acquire_fresh_max_available_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    td_mode: str,
    px_sent: str = "",
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    order_type: str = "LIMIT",
) -> FreshMaxAvailableObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryMaxAvailableObservationError("PRETRADE_DECISION_ID_REQUIRED")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
    )
    observation_class = classify_max_available_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    if not auth_header_sent:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_AUTH_HEADER_REQUIRED")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryMaxAvailableObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != MAX_AVAILABLE_ENDPOINT_PATH:
        raise LiveCanaryMaxAvailableObservationError(f"MAX_AVAILABLE_ENDPOINT_MISMATCH:{endpoint}")
    selected_type = str(order_type or "").strip().upper()
    has_px = "px=" in str(endpoint or "")
    if selected_type == "LIMIT":
        if not has_px or not str(px_sent or "").strip():
            raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_LIMIT_PX_REQUIRED")
    elif selected_type == "MARKET":
        if has_px or str(px_sent or "").strip():
            raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_MARKET_PX_FORBIDDEN")
    else:
        raise LiveCanaryMaxAvailableObservationError(
            f"UNSUPPORTED_ORDER_TYPE_FOR_MAX_AVAILABLE:{selected_type}"
        )
    row = _target_row(payload=payload, instrument_id=instrument_id)
    if "maxBuy" not in row:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_FIELD_MISSING:maxBuy")
    if "maxSell" not in row:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_FIELD_MISSING:maxSell")
    buy_raw = row.get("maxBuy")
    sell_raw = row.get("maxSell")
    if buy_raw is None:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_FIELD_NULL:maxBuy")
    if sell_raw is None:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_FIELD_NULL:maxSell")
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshMaxAvailableObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        instrument_id=instrument_id,
        td_mode=str(td_mode or "").strip(),
        px_sent=str(px_sent or "").strip(),
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=True,
        max_buy_raw=str(buy_raw).strip(),
        max_sell_raw=str(sell_raw).strip(),
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        max_available_unit=MAX_AVAILABLE_UNIT,
        historical_reuse=False,
        body_sha256=digest,
    )


def validate_fresh_max_available_observation_v1(
    observation: FreshMaxAvailableObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    quantity_domain: str,
) -> ValidatedFreshMaxAvailableObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryMaxAvailableObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.instrument_id != instrument_id:
        raise LiveCanaryMaxAvailableObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(quantity_domain) != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryMaxAvailableObservationError("QUANTITY_DOMAIN_INCOMPATIBLE")
    if observation.quantity_domain != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryMaxAvailableObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.max_available_unit != MAX_AVAILABLE_UNIT:
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_UNIT_INCOMPATIBLE")
    if observation.max_available_unit != ORDER_PLAN_QTY_UNIT:
        raise LiveCanaryMaxAvailableObservationError("DOMAIN_COMPATIBILITY_UNPROVEN")
    max_buy = _require_non_negative_decimal(observation.max_buy_raw, field="maxBuy")
    max_sell = _require_non_negative_decimal(observation.max_sell_raw, field="maxSell")
    return ValidatedFreshMaxAvailableObservationV1(
        raw=observation,
        max_buy=max_buy,
        max_sell=max_sell,
        comparison_domain=MAX_AVAILABLE_COMPARISON_DOMAIN,
    )


PRODUCTION_REST_BASE = "https://eea.okx.com"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1"
FORBIDDEN_HEADER_NAME_MARKERS = (
    "authorization",
    "ok-access",
    "cookie",
    "api-key",
    "secret",
    "sign",
)
SAFE_HEADER_ALLOWLIST = frozenset({"content-type", "date", "server"})


def persist_authorized_fresh_max_available_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
    vault_file: Path | str,
    td_mode: str = "cross",
    side: str = "BUY",
) -> dict[str, Any]:
    """Perform one authenticated account/max-size GET and persist forensic evidence.

    Public instruments+ticker GETs exist only to bind LIMIT px. No POST.
    The pack is not an operative cache.
    """
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        DEFAULT_INST_TYPE,
        DEFAULT_ORDER_TYPE,
        REQUIRED_CREDENTIAL_CLASS,
        REQUIRED_SECRETREF_URI,
        USER_AGENT_CANARY,
        public_instruments_query_path_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
        LiveCanaryHttpClientV1,
        LiveCanaryHttpError,
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
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
        extract_instrument_constraints_v1,
        extract_reference_price_v1,
        quantize_limit_price_v1,
    )

    owned = str(owner_go or "").strip()
    if owned != OWNER_GO_THIS_SLICE:
        raise LiveCanaryMaxAvailableObservationError("OWNER_GO_MISMATCH")
    client = LiveCanaryHttpClientV1(
        rest_base=PRODUCTION_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=UrllibLiveCanaryTransportV1(wire_send_enabled=True),
        max_retries=0,
        timeout_seconds=10.0,
    )
    public_headers = {"User-Agent": USER_AGENT_CANARY}
    inst_ep = public_instruments_query_path_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID, inst_type=DEFAULT_INST_TYPE
    )
    tick_ep = f"/api/v5/market/ticker?instId={DEFAULT_INSTRUMENT_ID}"
    try:
        inst_response = client.get(endpoint=inst_ep, headers=public_headers)
        ticker_response = client.get(endpoint=tick_ep, headers=public_headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryMaxAvailableObservationError(
            f"MAX_AVAILABLE_LIMIT_PX_PUBLIC_GET_FAILED:{exc}"
        ) from exc
    finally:
        public_headers.clear()
    instruments = parse_json_object_v1(inst_response.body_bytes)
    ticker = parse_json_object_v1(ticker_response.body_bytes)
    constraints = extract_instrument_constraints_v1(
        instruments_payload=instruments, instrument_id=DEFAULT_INSTRUMENT_ID
    )
    reference = extract_reference_price_v1(ticker_payload=ticker)
    limit_px = quantize_limit_price_v1(reference_price=reference, tick_sz=constraints["tickSz"])
    if not str(limit_px).strip():
        raise LiveCanaryMaxAvailableObservationError("MAX_AVAILABLE_LIMIT_PX_REQUIRED")
    endpoint = account_max_size_query_path_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID,
        td_mode=td_mode,
        px=limit_px,
        order_type=DEFAULT_ORDER_TYPE,
    )
    backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
    handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
        credential_class=REQUIRED_CREDENTIAL_CLASS,
    )
    auth_headers: dict[str, str] = {}
    request_time = utc_now_iso_v1()
    try:
        url = f"{PRODUCTION_REST_BASE}{endpoint}"
        parsed = urlparse(url)
        signed_target = f"{parsed.path}?{parsed.query}" if parsed.query else parsed.path
        if signed_target != endpoint:
            raise LiveCanaryMaxAvailableObservationError(
                f"SIGNED_REQUEST_TARGET_MISMATCH:{signed_target}"
            )
        auth_headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
        response = client.get(endpoint=endpoint, headers=auth_headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryMaxAvailableObservationError(
            f"MAX_AVAILABLE_FRESH_GET_FAILED:{exc}"
        ) from exc
    finally:
        auth_headers.clear()
        release_live_canary_ephemeral_material_v1(handle)
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_max_available_observation_class_v1(
        get_performed=True,
        http_status=int(response.status_code),
        payload=payload,
    )
    support = account_mode_support_for_max_size_cross_derivatives_v1(
        observation_class=observation_class
    )
    if observation_class != OBSERVATION_CLASS_SUCCESS_NUMERIC:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pack = Path(evidence_root) / run_id
        pack.mkdir(parents=True, exist_ok=False)
        forensic = {
            "DOCUMENT_CLASS": "MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
            "ENDPOINT": endpoint,
            "GET_REQUEST_COUNT_AUTHENTICATED": 1,
            "HOST": REUSED_BINDING_REST_HOST,
            "HTTP_STATUS": int(response.status_code),
            "MAX_AVAIL_SIZE_FALLBACK_USED": False,
            "METHOD": "GET",
            "OBSERVATION_CLASS": observation_class,
            "OKX_CODE": str(payload.get("code") or ""),
            "OKX_MSG": str(payload.get("msg") or ""),
            "OWNER_GO": owned,
            "POST_COUNT": 0,
            "PX_SENT": limit_px,
            "SECRET_VALUES_INCLUDED": False,
            "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "ZERO_NORMALIZATION_PERFORMED": False,
            "ACCOUNT_MODE_SUPPORT_FOR_MAX_SIZE_CROSS_DERIVATIVES": support,
            "payload": payload,
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        _raise_for_observation_class(observation_class)
    observation = acquire_fresh_max_available_observation_from_payload_v1(
        pretrade_decision_id=pretrade_decision_id,
        payload=payload,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        td_mode=td_mode,
        px_sent=limit_px,
        observed_at_utc=response_time,
        endpoint=endpoint,
        http_status=int(response.status_code),
        get_performed=True,
        auth_header_sent=True,
        body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
        order_type=DEFAULT_ORDER_TYPE,
    )
    validated = validate_fresh_max_available_observation_v1(
        observation,
        pretrade_decision_id=pretrade_decision_id,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
    )
    field = select_max_available_field_for_side_v1(side=side)
    selected = validated.max_buy if field == "maxBuy" else validated.max_sell
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    pack.mkdir(parents=True, exist_ok=False)

    def _safe_headers(headers: Mapping[str, str]) -> dict[str, str]:
        out: dict[str, str] = {}
        for key, value in dict(headers).items():
            lowered = str(key).strip().lower()
            if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
                continue
            if lowered in SAFE_HEADER_ALLOWLIST:
                out[str(key)] = str(value)
        return out

    snapshot = {
        "AUTHENTICATION_REQUIREMENT": "AUTHENTICATED_PRIVATE_GET",
        "AUTH_HEADER_SENT": True,
        "AUTH_REQUIRED": True,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "EVIDENCE_READ_ONLY": True,
        "GET_REQUEST_COUNT_AUTHENTICATED": 1,
        "PUBLIC_GET_COUNT_FOR_LIMIT_PX": 2,
        "HOST": REUSED_BINDING_REST_HOST,
        "METHOD": "GET",
        "NO_POST": True,
        "OWNER_GO": owned,
        "POST_COUNT": 0,
        "SECRET_VALUES_INCLUDED": False,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "TARGET_TDMODE": td_mode,
        "TARGET_SIDE": side,
        "TARGET_VENUE": "OKX_EEA",
        "PX_SENT": limit_px,
        "PX_SOURCE": MAX_AVAILABLE_PX_SOURCE,
        "LEVERAGE_REQUEST_POLICY": MAX_AVAILABLE_LEVERAGE_REQUEST_POLICY,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "MAX_AVAIL_SIZE_FALLBACK_USED": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "observation": observation.to_dict(),
        "validated": {
            "max_buy": format(validated.max_buy, "f"),
            "max_sell": format(validated.max_sell, "f"),
            "selected_field": field,
            "selected_value": format(selected, "f"),
            "comparison_domain": validated.comparison_domain,
            "observation_class": observation_class,
            "account_mode": ACCOUNT_MODE,
            "account_mode_proof_status": ACCOUNT_MODE_PROOF_STATUS,
            "account_mode_support_for_max_size_cross_derivatives": support,
        },
        "http_evidence": {
            "SECRET_VALUES_INCLUDED": False,
            "body_byte_len": len(response.body_bytes),
            "body_sha256": hashlib.sha256(response.body_bytes).hexdigest(),
            "http_status": response.status_code,
            "json_parse_ok": True,
            "okx_code": str(payload.get("code") or ""),
            "okx_msg": str(payload.get("msg") or ""),
            "response_headers_safe": _safe_headers(response.response_headers_safe),
        },
        "payload": payload,
        "request_event_time": request_time,
        "response_event_time": response_time,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
    }
    summary = {
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "DOCUMENT_CLASS": "MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "GET_REQUEST_COUNT_AUTHENTICATED": 1,
        "HOST": REUSED_BINDING_REST_HOST,
        "HTTP_STATUS": response.status_code,
        "LIVE_AUTHORIZED": False,
        "METHOD": "GET",
        "OKX_CODE": observation.venue_code,
        "OWNER_GO": owned,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "POST_COUNT": 0,
        "PRETRADE_DECISION_ID": pretrade_decision_id,
        "RESPONSE_BODY_SHA256": hashlib.sha256(response.body_bytes).hexdigest(),
        "RUN_ID": run_id,
        "SECRET_VALUES_INCLUDED": False,
        "SELECTED_FIELD": field,
        "SELECTED_VALUE": format(selected, "f"),
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "OBSERVATION_CLASS": observation_class,
        "ACCOUNT_MODE_SUPPORT_FOR_MAX_SIZE_CROSS_DERIVATIVES": support,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "NETWORK_POST_PERFORMED": False,
        "MAX_AVAIL_SIZE_FALLBACK_USED": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "TRADING_PERFORMED": False,
    }
    redaction = {
        "AUTH_HEADER_PERSISTED": False,
        "COOKIE_PERSISTED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
    zero_write = {
        "DELETE_COUNT": 0,
        "FUNDING_EXECUTED": False,
        "GET_COUNT_AUTHENTICATED": 1,
        "ORDER_EXECUTED": False,
        "PATCH_COUNT": 0,
        "POST_COUNT": 0,
        "PUT_COUNT": 0,
        "RETRY_EXECUTED": False,
        "SET_LEVERAGE_EXECUTED": False,
    }
    persistence = {"ok": True, "OPERATIVE_CACHE": False, "pack": str(pack)}
    files = {
        "GET_SNAPSHOT.sanitized.json": snapshot,
        "SUMMARY.json": summary,
        "claims.json": claims,
        "redaction_check.json": redaction,
        "zero_write_assertions.json": zero_write,
        "PERSISTENCE_RESULT.json": persistence,
    }
    digest_lines: list[str] = []
    for name, body in files.items():
        encoded = json.dumps(body, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / name).write_bytes(encoded)
        digest_lines.append(f"{hashlib.sha256(encoded).hexdigest()}  {name}")
    (pack / "MANIFEST.sha256").write_text("\n".join(digest_lines) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "run_id": run_id,
        "pack": str(pack),
        "observation": observation.to_dict(),
        "http_status": response.status_code,
        "venue_code": observation.venue_code,
        "observed_at_utc": observation.observed_at_utc,
        "endpoint": endpoint,
        "selected_field": field,
        "selected_value": format(selected, "f"),
        "observation_class": observation_class,
        "account_mode_support_for_max_size_cross_derivatives": support,
        "px_sent": limit_px,
    }

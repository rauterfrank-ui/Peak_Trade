"""Decision-bound fresh PRICE_BAND observation for §11.13.5 pretrade.

Owner-adjudicated operative source is unsigned GET /api/v5/public/price-limit.
Percent fields, markPx, last, bid/ask, tickSz, and historical BTC/testnet
51006 packs are not an operative cache. No TTL. No POST. No trading.
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
from urllib.parse import urlencode

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)

PRICE_BAND_ENDPOINT_PATH = ENDPOINT_PUBLIC_PRICE_LIMIT
PRICE_BAND_OUTPUT_DOMAIN = "VENUE_LIMIT_PRICE"
PRICE_BAND_COMPARISON_DOMAIN = "VENUE_LIMIT_PRICE"
PRICE_BAND_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
PRICE_BAND_TS_AGE_BOUND = "UNBOUND"
PRICE_BAND_AUTH_CLASS = "PUBLIC_UNSIGNED_GET"
OBSERVATION_CLASS_SUCCESS_NUMERIC = "SUCCESS_NUMERIC"
OBSERVATION_CLASS_PRICE_LIMIT_NOT_ACTIVE = "PRICE_LIMIT_NOT_ACTIVE"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
MAX_RAW_DIGIT_LEN = 40
_SCIENTIFIC_NOTATION = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+")
HISTORICAL_BTC_INSTRUMENT_ID = "BTC-USD_UM_XPERP-310404"
HISTORICAL_TESTNET_51006_PACK = "section_11_12_testnet_restart_proven_v1"
FORBIDDEN_RECONSTRUCTION_MARKERS = (
    "markPx",
    "mark-price",
    "maxPxLmtPct",
    "floatPxLmtPct",
    "initPxLmtPct",
)
FORBIDDEN_HEADER_NAME_MARKERS = (
    "authorization",
    "ok-access",
    "cookie",
    "api-key",
    "secret",
    "sign",
)
SAFE_HEADER_ALLOWLIST = frozenset({"content-type", "date", "server"})
PRODUCTION_REST_BASE = "https://eea.okx.com"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"


class LiveCanaryPriceBandObservationError(RuntimeError):
    """Fail-closed fresh PRICE_BAND observation violation."""


@dataclass(frozen=True)
class FreshPriceBandObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    instrument_id: str
    inst_type_raw: str
    enabled_raw: str
    ts_raw: str
    buy_lmt_raw: str
    sell_lmt_raw: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    price_domain: str
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
            "inst_type_raw": self.inst_type_raw,
            "enabled_raw": self.enabled_raw,
            "ts_raw": self.ts_raw,
            "buy_lmt_raw": self.buy_lmt_raw,
            "sell_lmt_raw": self.sell_lmt_raw,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "price_domain": self.price_domain,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
        }


@dataclass(frozen=True)
class ValidatedFreshPriceBandObservationV1:
    raw: FreshPriceBandObservationV1
    buy_lmt: Decimal
    sell_lmt: Decimal
    comparison_domain: str
    enabled: bool


def public_price_limit_query_path_v1(*, instrument_id: str) -> str:
    inst = str(instrument_id or "").strip()
    if not inst:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_INSTID_REQUIRED")
    return f"{PRICE_BAND_ENDPOINT_PATH}?{urlencode({'instId': inst})}"


def normalize_enabled_raw_v1(raw: Any) -> str:
    if raw is True:
        return "true"
    if raw is False:
        return "false"
    text = str(raw).strip().lower()
    if text == "true":
        return "true"
    if text == "false":
        return "false"
    raise LiveCanaryPriceBandObservationError("PRICE_BAND_ENABLED_UNPARSEABLE")


def classify_price_band_observation_class_v1(
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
        return OBSERVATION_CLASS_VENUE_ERROR
    data = payload.get("data")
    if not isinstance(data, list):
        return OBSERVATION_CLASS_MALFORMED
    return OBSERVATION_CLASS_SUCCESS_NUMERIC


def _raise_for_observation_class(observation_class: str) -> None:
    if observation_class == OBSERVATION_CLASS_SUCCESS_NUMERIC:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "PRICE_BAND_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "PRICE_BAND_NETWORK_ERROR",
        OBSERVATION_CLASS_VENUE_ERROR: "PRICE_BAND_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "PRICE_BAND_MALFORMED",
        OBSERVATION_CLASS_PRICE_LIMIT_NOT_ACTIVE: "PRICE_BAND_NOT_ACTIVE",
    }
    raise LiveCanaryPriceBandObservationError(
        mapping.get(observation_class, f"PRICE_BAND_FAIL_CLOSED:{observation_class}")
    )


def select_price_band_field_for_side_v1(*, side: str) -> str:
    selected = str(side or "").strip().upper()
    if selected == "BUY":
        return "buyLmt"
    if selected == "SELL":
        return "sellLmt"
    raise LiveCanaryPriceBandObservationError(f"UNSUPPORTED_SIDE_FOR_PRICE_BAND:{selected}")


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryPriceBandObservationError("HISTORICAL_PRICE_BAND_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    if HISTORICAL_TESTNET_51006_PACK in decision or HISTORICAL_TESTNET_51006_PACK in ep:
        raise LiveCanaryPriceBandObservationError("HISTORICAL_TESTNET_51006_PACK_REUSE_FORBIDDEN")
    if HISTORICAL_BTC_INSTRUMENT_ID in ep or instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryPriceBandObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    for marker in FORBIDDEN_RECONSTRUCTION_MARKERS:
        if marker in ep:
            raise LiveCanaryPriceBandObservationError(
                f"PRICE_BAND_RECONSTRUCTION_SOURCE_FORBIDDEN:{marker}"
            )


def _require_non_negative_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_NULL:{field}")
    text = str(raw).strip()
    if not text:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_MISSING:{field}")
    lowered = text.lower()
    if lowered in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_NON_NUMERIC:{field}")
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_OUT_OF_DOMAIN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_NON_NUMERIC:{field}") from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_NON_NUMERIC:{field}")
    if value < 0:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FIELD_NEGATIVE:{field}")
    return value


def _target_row(
    *,
    payload: Mapping[str, Any],
    instrument_id: str,
) -> Mapping[str, Any]:
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryPriceBandObservationError(str(exc)) from exc
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryPriceBandObservationError(
            f"PRICE_BAND_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_DATA_MISSING")
    matches: list[Mapping[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            matches.append(item)
    if len(matches) > 1:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_AMBIGUOUS_TARGET_ROW")
    if not matches:
        raise LiveCanaryPriceBandObservationError(f"INSTRUMENT_MISMATCH:{instrument_id}")
    return matches[0]


def acquire_fresh_price_band_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = False,
    historical_reuse: bool = False,
    body_sha256: str = "",
    order_type: str = "LIMIT",
) -> FreshPriceBandObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryPriceBandObservationError("PRETRADE_DECISION_ID_REQUIRED")
    selected_type = str(order_type or "").strip().upper()
    if selected_type != "LIMIT":
        raise LiveCanaryPriceBandObservationError(
            f"UNSUPPORTED_ORDER_TYPE_FOR_PRICE_BAND:{selected_type}"
        )
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
    )
    observation_class = classify_price_band_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    if auth_header_sent:
        raise LiveCanaryPriceBandObservationError("PUBLIC_PRICE_LIMIT_AUTH_HEADER_FORBIDDEN")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryPriceBandObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != PRICE_BAND_ENDPOINT_PATH:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_ENDPOINT_MISMATCH:{endpoint}")
    row = _target_row(payload=payload, instrument_id=instrument_id)
    if "enabled" not in row:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_MISSING:enabled")
    if "buyLmt" not in row:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_MISSING:buyLmt")
    if "sellLmt" not in row:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_MISSING:sellLmt")
    if "ts" not in row:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_MISSING:ts")
    if "instType" not in row:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_MISSING:instType")
    enabled_raw = normalize_enabled_raw_v1(row.get("enabled"))
    if enabled_raw == "false":
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_NOT_ACTIVE")
    inst_type = str(row.get("instType") or "").strip().upper()
    if inst_type != DEFAULT_INST_TYPE:
        raise LiveCanaryPriceBandObservationError(f"INST_TYPE_BINDING_MISMATCH:{inst_type}")
    buy_raw = row.get("buyLmt")
    sell_raw = row.get("sellLmt")
    if buy_raw is None:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_NULL:buyLmt")
    if sell_raw is None:
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_NULL:sellLmt")
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshPriceBandObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        instrument_id=instrument_id,
        inst_type_raw=inst_type,
        enabled_raw=enabled_raw,
        ts_raw=str(row.get("ts") if row.get("ts") is not None else "").strip(),
        buy_lmt_raw=str(buy_raw).strip(),
        sell_lmt_raw=str(sell_raw).strip(),
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=False,
        price_domain=PRICE_BAND_OUTPUT_DOMAIN,
        historical_reuse=False,
        body_sha256=digest,
    )


def validate_fresh_price_band_observation_v1(
    observation: FreshPriceBandObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    price_domain: str,
) -> ValidatedFreshPriceBandObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryPriceBandObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.instrument_id != instrument_id:
        raise LiveCanaryPriceBandObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(price_domain) != PRICE_BAND_OUTPUT_DOMAIN:
        raise LiveCanaryPriceBandObservationError("PRICE_DOMAIN_INCOMPATIBLE")
    if observation.price_domain != PRICE_BAND_OUTPUT_DOMAIN:
        raise LiveCanaryPriceBandObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.enabled_raw != "true":
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_NOT_ACTIVE")
    if not str(observation.ts_raw or "").strip():
        raise LiveCanaryPriceBandObservationError("PRICE_BAND_FIELD_MISSING:ts")
    buy_lmt = _require_non_negative_decimal(observation.buy_lmt_raw, field="buyLmt")
    sell_lmt = _require_non_negative_decimal(observation.sell_lmt_raw, field="sellLmt")
    return ValidatedFreshPriceBandObservationV1(
        raw=observation,
        buy_lmt=buy_lmt,
        sell_lmt=sell_lmt,
        comparison_domain=PRICE_BAND_COMPARISON_DOMAIN,
        enabled=True,
    )


def _safe_headers(headers: Mapping[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in dict(headers).items():
        lowered = str(key).strip().lower()
        if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
            continue
        if lowered in SAFE_HEADER_ALLOWLIST:
            out[str(key)] = str(value)
    return out


def persist_authorized_fresh_price_band_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
) -> dict[str, Any]:
    """Perform one unsigned public/price-limit GET and persist forensic evidence.

    The pack is not an operative cache. No POST. No credentials.
    """
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
        LiveCanaryHttpClientV1,
        LiveCanaryHttpError,
        UrllibLiveCanaryTransportV1,
        parse_json_object_v1,
    )

    owned = str(owner_go or "").strip()
    if owned != OWNER_GO_THIS_SLICE:
        raise LiveCanaryPriceBandObservationError("OWNER_GO_MISMATCH")
    endpoint = public_price_limit_query_path_v1(instrument_id=DEFAULT_INSTRUMENT_ID)
    client = LiveCanaryHttpClientV1(
        rest_base=PRODUCTION_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=UrllibLiveCanaryTransportV1(wire_send_enabled=True),
        max_retries=0,
        timeout_seconds=10.0,
    )
    headers = {"User-Agent": USER_AGENT_CANARY}
    request_time = utc_now_iso_v1()
    try:
        for key in list(headers):
            lowered = str(key).strip().lower()
            if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
                raise LiveCanaryPriceBandObservationError(
                    "PUBLIC_PRICE_LIMIT_AUTH_HEADER_FORBIDDEN"
                )
        response = client.get(endpoint=endpoint, headers=headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryPriceBandObservationError(f"PRICE_BAND_FRESH_GET_FAILED:{exc}") from exc
    finally:
        headers.clear()
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_price_band_observation_class_v1(
        get_performed=True,
        http_status=int(response.status_code),
        payload=payload,
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    pack.mkdir(parents=True, exist_ok=False)
    row: Mapping[str, Any] = {}
    data = payload.get("data") if isinstance(payload, Mapping) else None
    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        for item in data:
            if isinstance(item, Mapping) and str(item.get("instId") or "") == DEFAULT_INSTRUMENT_ID:
                row = item
                break
        if not row and isinstance(data[0], Mapping):
            row = data[0]
    raw_fields = {
        "HTTP_STATUS": int(response.status_code),
        "VENUE_CODE": str(payload.get("code") or ""),
        "VENUE_MSG": str(payload.get("msg") or ""),
        "instType": row.get("instType") if "instType" in row else None,
        "instId": row.get("instId") if "instId" in row else None,
        "buyLmt_raw": row.get("buyLmt") if "buyLmt" in row else None,
        "sellLmt_raw": row.get("sellLmt") if "sellLmt" in row else None,
        "ts_raw": row.get("ts") if "ts" in row else None,
        "enabled_raw": row.get("enabled") if "enabled" in row else None,
    }
    if observation_class != OBSERVATION_CLASS_SUCCESS_NUMERIC:
        forensic = {
            "DOCUMENT_CLASS": "PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
            "ENDPOINT": endpoint,
            "GET_REQUEST_COUNT_PUBLIC": 1,
            "HOST": REUSED_BINDING_REST_HOST,
            "METHOD": "GET",
            "OBSERVATION_CLASS": observation_class,
            "OWNER_GO": owned,
            "POST_COUNT": 0,
            "AUTH_HEADER_SENT": False,
            "AUTH_REQUIRED": False,
            "SECRET_VALUES_INCLUDED": False,
            "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "ZERO_NORMALIZATION_PERFORMED": False,
            "PERCENT_FIELD_RECONSTRUCTION_USED": False,
            "raw_fields": raw_fields,
            "payload": payload,
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        _raise_for_observation_class(observation_class)
    try:
        observation = acquire_fresh_price_band_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            observed_at_utc=response_time,
            endpoint=endpoint,
            http_status=int(response.status_code),
            get_performed=True,
            auth_header_sent=False,
            body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
        )
        validated = validate_fresh_price_band_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            price_domain=PRICE_BAND_OUTPUT_DOMAIN,
        )
        observation_class = OBSERVATION_CLASS_SUCCESS_NUMERIC
    except LiveCanaryPriceBandObservationError as exc:
        if str(exc) == "PRICE_BAND_NOT_ACTIVE":
            observation_class = OBSERVATION_CLASS_PRICE_LIMIT_NOT_ACTIVE
        else:
            observation_class = OBSERVATION_CLASS_MALFORMED
        forensic = {
            "DOCUMENT_CLASS": "PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
            "ENDPOINT": endpoint,
            "GET_REQUEST_COUNT_PUBLIC": 1,
            "HOST": REUSED_BINDING_REST_HOST,
            "METHOD": "GET",
            "OBSERVATION_CLASS": observation_class,
            "OWNER_GO": owned,
            "POST_COUNT": 0,
            "AUTH_HEADER_SENT": False,
            "AUTH_REQUIRED": False,
            "SECRET_VALUES_INCLUDED": False,
            "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "ZERO_NORMALIZATION_PERFORMED": False,
            "PERCENT_FIELD_RECONSTRUCTION_USED": False,
            "FAIL_CLOSED_REASON": str(exc),
            "raw_fields": raw_fields,
            "payload": payload,
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        raise
    snapshot = {
        "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
        "AUTH_HEADER_SENT": False,
        "AUTH_REQUIRED": False,
        "AUTH_CLASS": PRICE_BAND_AUTH_CLASS,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "EVIDENCE_READ_ONLY": True,
        "GET_REQUEST_COUNT_PUBLIC": 1,
        "GET_REQUEST_COUNT_AUTHENTICATED": 0,
        "HOST": REUSED_BINDING_REST_HOST,
        "METHOD": "GET",
        "NO_POST": True,
        "OWNER_GO": owned,
        "POST_COUNT": 0,
        "SECRET_VALUES_INCLUDED": False,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "TARGET_VENUE": "OKX_EEA",
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "PERCENT_FIELD_RECONSTRUCTION_USED": False,
        "MARKPX_SUBSTITUTION_USED": False,
        "FRESHNESS_POLICY": PRICE_BAND_FRESHNESS_POLICY,
        "TS_AGE_BOUND": PRICE_BAND_TS_AGE_BOUND,
        "observation": observation.to_dict(),
        "validated": {
            "buy_lmt": format(validated.buy_lmt, "f"),
            "sell_lmt": format(validated.sell_lmt, "f"),
            "comparison_domain": validated.comparison_domain,
            "enabled": True,
            "observation_class": observation_class,
        },
        "raw_fields": raw_fields,
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
        "DOCUMENT_CLASS": "PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "GET_REQUEST_COUNT_PUBLIC": 1,
        "GET_REQUEST_COUNT_AUTHENTICATED": 0,
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
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "OBSERVATION_CLASS": observation_class,
        "BUY_LMT_RAW": observation.buy_lmt_raw,
        "SELL_LMT_RAW": observation.sell_lmt_raw,
        "ENABLED_RAW": observation.enabled_raw,
        "TS_RAW": observation.ts_raw,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "NETWORK_POST_PERFORMED": False,
        "NETWORK_AUTHENTICATED_GET_PERFORMED": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "PERCENT_FIELD_RECONSTRUCTION_USED": False,
        "MARKPX_SUBSTITUTION_USED": False,
        "TRADING_PERFORMED": False,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
    }
    redaction = {
        "AUTH_HEADER_PERSISTED": False,
        "COOKIE_PERSISTED": False,
        "SECRET_VALUES_INCLUDED": False,
    }
    zero_write = {
        "DELETE_COUNT": 0,
        "FUNDING_EXECUTED": False,
        "GET_COUNT_PUBLIC": 1,
        "GET_COUNT_AUTHENTICATED": 0,
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
        "observation_class": observation_class,
        "buy_lmt": format(validated.buy_lmt, "f"),
        "sell_lmt": format(validated.sell_lmt, "f"),
        "enabled_raw": observation.enabled_raw,
        "ts_raw": observation.ts_raw,
    }

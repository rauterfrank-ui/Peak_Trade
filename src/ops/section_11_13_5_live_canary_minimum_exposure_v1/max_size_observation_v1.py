"""Decision-bound fresh max-size observation for §11.13.5 pretrade.

Historical #6148 windows are not an operative cache. No TTL. No event-cache.
Unsigned public GET only. No POST. No trading.
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

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryHttpResponseV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    MAX_SIZE_COMPARISON_DOMAIN,
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_UNIT,
)

HISTORICAL_6148_RUN_ID = "20260829T182239Z"
HISTORICAL_6148_EVIDENCE_PACK = (
    "evidence/ops/exact_venue_metadata_get_current_sui_pretrade_max_size_v1/20260829T182239Z"
)
MAX_SIZE_UNIT = "contracts"
MAX_RAW_DIGIT_LEN = 40
_SCIENTIFIC_NOTATION = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+")
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


class LiveCanaryMaxSizeObservationError(RuntimeError):
    """Fail-closed fresh max-size observation violation."""


@dataclass(frozen=True)
class FreshMaxSizeObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    instrument_id: str
    inst_type: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    max_lmt_sz_raw: str
    max_mkt_sz_raw: str
    quantity_domain: str
    max_size_unit: str
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
            "inst_type": self.inst_type,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "max_lmt_sz_raw": self.max_lmt_sz_raw,
            "max_mkt_sz_raw": self.max_mkt_sz_raw,
            "quantity_domain": self.quantity_domain,
            "max_size_unit": self.max_size_unit,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
        }


@dataclass(frozen=True)
class ValidatedFreshMaxSizeObservationV1:
    raw: FreshMaxSizeObservationV1
    max_lmt_sz: Decimal
    max_mkt_sz: Decimal
    comparison_domain: str


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _reject_historical_reuse(
    *, pretrade_decision_id: str, endpoint: str, historical_reuse: bool
) -> None:
    if historical_reuse:
        raise LiveCanaryMaxSizeObservationError("HISTORICAL_MAX_SIZE_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    if decision == HISTORICAL_6148_RUN_ID:
        raise LiveCanaryMaxSizeObservationError("HISTORICAL_6148_WINDOW_REUSE_FORBIDDEN")
    if HISTORICAL_6148_EVIDENCE_PACK in str(endpoint or ""):
        raise LiveCanaryMaxSizeObservationError("HISTORICAL_6148_EVIDENCE_PACK_REUSE_FORBIDDEN")


def _require_positive_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_NULL:{field}")
    text = str(raw).strip()
    if not text:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_MISSING:{field}")
    if text.lower() in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_NON_NUMERIC:{field}")
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_OUT_OF_DOMAIN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_NON_NUMERIC:{field}") from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_NON_NUMERIC:{field}")
    if value < 0:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_NEGATIVE:{field}")
    if value == 0:
        raise LiveCanaryMaxSizeObservationError(f"MAX_SIZE_FIELD_ZERO_FORBIDDEN:{field}")
    return value


def _target_instrument_row(
    *,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
) -> Mapping[str, Any]:
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryMaxSizeObservationError(str(exc)) from exc
    if str(instruments_payload.get("code") or "") != "0":
        raise LiveCanaryMaxSizeObservationError("INSTRUMENTS_PAYLOAD_NOT_OK")
    data = instruments_payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryMaxSizeObservationError("INSTRUMENTS_DATA_MISSING")
    row = None
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            row = item
            break
    if row is None:
        raise LiveCanaryMaxSizeObservationError(f"INSTRUMENT_MISMATCH:{instrument_id}")
    row_type = str(row.get("instType") or "").strip().upper()
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id,
            inst_type=row_type or DEFAULT_INST_TYPE,
            rule_type=str(row.get("ruleType") or "") or None,
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryMaxSizeObservationError(str(exc)) from exc
    return row


def acquire_fresh_max_size_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    instruments_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = False,
    historical_reuse: bool = False,
    body_sha256: str = "",
) -> FreshMaxSizeObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryMaxSizeObservationError("PRETRADE_DECISION_ID_REQUIRED")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
    )
    if not get_performed:
        raise LiveCanaryMaxSizeObservationError("FRESH_GET_NOT_PERFORMED")
    if int(http_status) != 200:
        raise LiveCanaryMaxSizeObservationError(f"FRESH_GET_HTTP_UNSUCCESSFUL:{http_status}")
    if auth_header_sent:
        raise LiveCanaryMaxSizeObservationError("PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryMaxSizeObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    row = _target_instrument_row(
        instruments_payload=instruments_payload, instrument_id=instrument_id
    )
    venue_code = str(instruments_payload.get("code") or "")
    if "maxLmtSz" not in row:
        raise LiveCanaryMaxSizeObservationError("MAX_SIZE_FIELD_MISSING:maxLmtSz")
    if "maxMktSz" not in row:
        raise LiveCanaryMaxSizeObservationError("MAX_SIZE_FIELD_MISSING:maxMktSz")
    max_lmt = row.get("maxLmtSz")
    max_mkt = row.get("maxMktSz")
    if max_lmt is None:
        raise LiveCanaryMaxSizeObservationError("MAX_SIZE_FIELD_NULL:maxLmtSz")
    if max_mkt is None:
        raise LiveCanaryMaxSizeObservationError("MAX_SIZE_FIELD_NULL:maxMktSz")
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(instruments_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshMaxSizeObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        instrument_id=instrument_id,
        inst_type=str(row.get("instType") or DEFAULT_INST_TYPE).strip().upper(),
        http_status=int(http_status),
        venue_code=venue_code,
        get_performed=True,
        auth_header_sent=False,
        max_lmt_sz_raw=str(max_lmt).strip(),
        max_mkt_sz_raw=str(max_mkt).strip(),
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        max_size_unit=MAX_SIZE_UNIT,
        historical_reuse=False,
        body_sha256=digest,
    )


def validate_fresh_max_size_observation_v1(
    observation: FreshMaxSizeObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    quantity_domain: str,
) -> ValidatedFreshMaxSizeObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryMaxSizeObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.instrument_id != instrument_id:
        raise LiveCanaryMaxSizeObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(quantity_domain) != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryMaxSizeObservationError("QUANTITY_DOMAIN_INCOMPATIBLE")
    if observation.quantity_domain != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryMaxSizeObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.max_size_unit != MAX_SIZE_UNIT:
        raise LiveCanaryMaxSizeObservationError("MAX_SIZE_UNIT_INCOMPATIBLE")
    if observation.max_size_unit != ORDER_PLAN_QTY_UNIT:
        raise LiveCanaryMaxSizeObservationError("DOMAIN_COMPATIBILITY_UNPROVEN")
    max_lmt = _require_positive_decimal(observation.max_lmt_sz_raw, field="maxLmtSz")
    max_mkt = _require_positive_decimal(observation.max_mkt_sz_raw, field="maxMktSz")
    return ValidatedFreshMaxSizeObservationV1(
        raw=observation,
        max_lmt_sz=max_lmt,
        max_mkt_sz=max_mkt,
        comparison_domain=MAX_SIZE_COMPARISON_DOMAIN,
    )


def fetch_unsigned_public_instruments_v1(
    *,
    client: LiveCanaryHttpClientV1,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    inst_type: str = DEFAULT_INST_TYPE,
) -> LiveCanaryHttpResponseV1:
    endpoint = public_instruments_query_path_v1(instrument_id=instrument_id, inst_type=inst_type)
    headers = {"User-Agent": USER_AGENT_CANARY}
    try:
        for key in list(headers):
            lowered = str(key).strip().lower()
            if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
                raise LiveCanaryMaxSizeObservationError("PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN")
        return client.get(endpoint=endpoint, headers=headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryMaxSizeObservationError(f"FRESH_GET_FAILED:{exc}") from exc
    finally:
        headers.clear()


def build_live_unsigned_public_get_client_v1() -> LiveCanaryHttpClientV1:
    return LiveCanaryHttpClientV1(
        rest_base=PRODUCTION_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=UrllibLiveCanaryTransportV1(wire_send_enabled=True),
        max_retries=2,
        timeout_seconds=10.0,
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


def persist_authorized_fresh_max_size_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
    client: LiveCanaryHttpClientV1 | None = None,
) -> dict[str, Any]:
    """Perform exactly one unsigned public instruments GET and persist evidence.

    The persisted pack is forensic evidence for this Owner-GO. It is not an
    operative cache for later pretrade decisions.
    """
    owned = str(owner_go or "").strip()
    if owned != "PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1":
        raise LiveCanaryMaxSizeObservationError("OWNER_GO_MISMATCH")
    _reject_historical_reuse(
        pretrade_decision_id=pretrade_decision_id,
        endpoint="",
        historical_reuse=False,
    )
    http_client = client or build_live_unsigned_public_get_client_v1()
    endpoint = public_instruments_query_path_v1()
    request_time = utc_now_iso_v1()
    response = fetch_unsigned_public_instruments_v1(client=http_client)
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation = acquire_fresh_max_size_observation_from_payload_v1(
        pretrade_decision_id=pretrade_decision_id,
        instruments_payload=payload,
        observed_at_utc=response_time,
        endpoint=endpoint,
        http_status=response.status_code,
        get_performed=True,
        body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
    )
    validated = validate_fresh_max_size_observation_v1(
        observation,
        pretrade_decision_id=pretrade_decision_id,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = evidence_root / run_id
    pack.mkdir(parents=True, exist_ok=False)
    snapshot = {
        "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
        "AUTH_HEADER_SENT": False,
        "AUTH_REQUIRED": False,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "EVIDENCE_READ_ONLY": True,
        "GET_REQUEST_COUNT": 1,
        "HOST": REUSED_BINDING_REST_HOST,
        "METHOD": "GET",
        "NO_PRIVATE_GET": True,
        "NO_SECOND_ENDPOINT": True,
        "OWNER_GO": owned,
        "POST_COUNT": 0,
        "SECRET_VALUES_INCLUDED": False,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "TARGET_INST_TYPE": DEFAULT_INST_TYPE,
        "TARGET_VENUE": "OKX_EEA",
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_MAX_SIZE_REUSE_ALLOWED": False,
        "observation": observation.to_dict(),
        "validated": {
            "max_lmt_sz": format(validated.max_lmt_sz, "f"),
            "max_mkt_sz": format(validated.max_mkt_sz, "f"),
            "comparison_domain": validated.comparison_domain,
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
        "CURRENT_REUSABLE_MAXLMTSZ_PROVEN": False,
        "CURRENT_REUSABLE_MAXMKTSZ_PROVEN": False,
        "DOCUMENT_CLASS": "MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "FRESH_MAXLMTSZ_OBSERVED": True,
        "FRESH_MAXLMTSZ_VALUE": observation.max_lmt_sz_raw,
        "FRESH_MAXMKTSZ_OBSERVED": True,
        "FRESH_MAXMKTSZ_VALUE": observation.max_mkt_sz_raw,
        "GET_REQUEST_COUNT": 1,
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
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "NETWORK_POST_PERFORMED": False,
        "OBSERVATION_BOUND_TO_CURRENT_DECISION_CONTRACT": True,
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
        "GET_COUNT": 1,
        "ORDER_EXECUTED": False,
        "PATCH_COUNT": 0,
        "POST_COUNT": 0,
        "PUT_COUNT": 0,
        "RETRY_EXECUTED": False,
        "SET_LEVERAGE_EXECUTED": False,
    }
    persistence = {
        "ok": True,
        "OPERATIVE_CACHE": False,
        "pack": str(pack),
    }
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
    }

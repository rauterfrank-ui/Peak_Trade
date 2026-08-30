"""Decision-bound fresh INSTRUMENT_STATE observation for §11.13.5 pretrade.

Owner-adjudicated operative source is unsigned GET /api/v5/public/instruments
exact-row field `state`. Admissible order-attempt value is the exact
documented enum `live`. Historical BTC rows, the Z2BY identity rebind,
Aug-27 SUI observations, ruleType, instType, expTime, ticker, and mark
price are not this edge. No TTL. No venue-row timestamp. No POST.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_RULE_TYPE,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
    public_instruments_query_path_v1,
)

INSTRUMENT_STATE_ENDPOINT_PATH = "/api/v5/public/instruments"
INSTRUMENT_STATE_OUTPUT_DOMAIN = "VENUE_INSTRUMENT_STATE"
INSTRUMENT_STATE_COMPARISON_DOMAIN = "VENUE_INSTRUMENT_STATE"
INSTRUMENT_STATE_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
INSTRUMENT_STATE_TS_AGE_BOUND = "UNBOUND"
INSTRUMENT_STATE_AUTH_CLASS = "PUBLIC_UNSIGNED_GET"
INSTRUMENT_STATE_SEMANTIC_CLASS = "ORDER_ATTEMPT_ELIGIBILITY_REQUIRES_STATE_LIVE"
INSTRUMENT_STATE_RAW_FIELD = "state"
INSTRUMENT_STATE_ADMISSIBLE_RAW = "live"
INSTRUMENT_STATE_SEMANTIC_LIVE = "LIVE"
INSTRUMENT_STATE_KNOWN_NEGATIVE_RAW = frozenset({"suspend", "preopen", "test"})
INSTRUMENT_STATE_QUERY = f"instType={DEFAULT_INST_TYPE}&instId={DEFAULT_INSTRUMENT_ID}"
GET_VENUE_TS_STATUS = "ABSENT_NOT_IN_INSTRUMENTS_ROW"
OBSERVATION_CLASS_SUCCESS_LIVE = "SUCCESS_LIVE"
OBSERVATION_CLASS_NOT_OBSERVED = "NOT_OBSERVED"
OBSERVATION_CLASS_NOT_ADMISSIBLE = "NOT_ADMISSIBLE"
OBSERVATION_CLASS_UNKNOWN_ENUM = "UNKNOWN_ENUM"
OBSERVATION_CLASS_CONFLICTED = "CONFLICTED"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
HISTORICAL_BTC_INSTRUMENT_ID = "BTC-USD_UM_XPERP-310404"
HISTORICAL_SUI_STATE_PACK = (
    "evidence/ops/section_11_13_5_z2cg_same_pack_public_unauthenticated_get_v1"
)
HISTORICAL_Z2AR_STATE_MARKER = "GET_1_STATE=live"
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
OWNER_GO_THIS_SLICE = "PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1"


class LiveCanaryInstrumentStateObservationError(RuntimeError):
    """Fail-closed fresh INSTRUMENT_STATE observation violation."""


@dataclass(frozen=True)
class FreshInstrumentStateObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    request_started_at_utc: str
    request_finished_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    instrument_id: str
    inst_type_raw: str
    rule_type_raw: str
    state_raw: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    instrument_state_domain: str
    historical_reuse: bool
    target_row_count: int
    body_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pretrade_decision_id": self.pretrade_decision_id,
            "observed_at_utc": self.observed_at_utc,
            "request_started_at_utc": self.request_started_at_utc,
            "request_finished_at_utc": self.request_finished_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "instrument_id": self.instrument_id,
            "inst_type_raw": self.inst_type_raw,
            "rule_type_raw": self.rule_type_raw,
            "state_raw": self.state_raw,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "instrument_state_domain": self.instrument_state_domain,
            "historical_reuse": self.historical_reuse,
            "target_row_count": self.target_row_count,
            "body_sha256": self.body_sha256,
        }


@dataclass(frozen=True)
class ValidatedFreshInstrumentStateObservationV1:
    raw: FreshInstrumentStateObservationV1
    state_raw: str
    semantic_value: str
    comparison_domain: str
    consumer_precondition_satisfied: bool


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _reject_historical_reuse(
    *, pretrade_decision_id: str, endpoint: str, historical_reuse: bool
) -> None:
    if historical_reuse:
        raise LiveCanaryInstrumentStateObservationError(
            "HISTORICAL_INSTRUMENT_STATE_REUSE_FORBIDDEN"
        )
    if HISTORICAL_SUI_STATE_PACK in str(endpoint or ""):
        raise LiveCanaryInstrumentStateObservationError("HISTORICAL_SUI_STATE_PACK_REUSE_FORBIDDEN")
    if HISTORICAL_Z2AR_STATE_MARKER in str(pretrade_decision_id or ""):
        raise LiveCanaryInstrumentStateObservationError("HISTORICAL_Z2AR_STATE_REUSE_FORBIDDEN")


def _require_public_instruments_endpoint(endpoint: str) -> None:
    text = str(endpoint or "").strip()
    if not text.startswith(INSTRUMENT_STATE_ENDPOINT_PATH):
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_ENDPOINT_FORBIDDEN")
    expected = public_instruments_query_path_v1()
    if text != expected and not text.startswith(f"{INSTRUMENT_STATE_ENDPOINT_PATH}?"):
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_ENDPOINT_FORBIDDEN")
    if text != expected:
        raise LiveCanaryInstrumentStateObservationError(f"INSTRUMENT_STATE_QUERY_MISMATCH:{text}")


def _exact_target_rows(
    *,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
) -> list[Mapping[str, Any]]:
    data = instruments_payload.get("data")
    if not isinstance(data, list):
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENTS_DATA_MISSING")
    matches: list[Mapping[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            matches.append(item)
    return matches


def acquire_fresh_instrument_state_observation_from_payload_v1(
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
    request_started_at_utc: str = "",
    request_finished_at_utc: str = "",
) -> FreshInstrumentStateObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryInstrumentStateObservationError("PRETRADE_DECISION_ID_REQUIRED")
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryInstrumentStateObservationError(str(exc)) from exc
    if instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryInstrumentStateObservationError("HISTORICAL_BTC_INSTRUMENT")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
    )
    if not get_performed:
        raise LiveCanaryInstrumentStateObservationError("FRESH_GET_NOT_PERFORMED")
    if int(http_status) != 200:
        raise LiveCanaryInstrumentStateObservationError(
            f"FRESH_GET_HTTP_UNSUCCESSFUL:{http_status}"
        )
    if auth_header_sent:
        raise LiveCanaryInstrumentStateObservationError("PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryInstrumentStateObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    _require_public_instruments_endpoint(endpoint)
    if not isinstance(instruments_payload, Mapping):
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENTS_PAYLOAD_NOT_OBJECT")
    venue_code = str(instruments_payload.get("code") or "")
    if venue_code != "0":
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_VENUE_CODE_UNSUCCESSFUL:{venue_code or 'EMPTY'}"
        )
    matches = _exact_target_rows(
        instruments_payload=instruments_payload, instrument_id=instrument_id
    )
    if not matches:
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_NOT_OBSERVED:{instrument_id}"
        )
    if len(matches) > 1:
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_DUPLICATE_TARGET_ROWS:{len(matches)}"
        )
    row = matches[0]
    if "state" not in row:
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_FIELD_MISSING:state")
    if row.get("state") is None:
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_FIELD_NULL:state")
    state_raw = str(row.get("state")).strip() if row.get("state") is not None else ""
    if isinstance(row.get("state"), str):
        state_raw = str(row.get("state"))
    else:
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_FIELD_WRONG_TYPE:state")
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(instruments_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        digest = hashlib.sha256(encoded).hexdigest()
    finished = str(request_finished_at_utc or observed_at_utc or "").strip() or utc_now_iso_v1()
    started = str(request_started_at_utc or "").strip() or finished
    return FreshInstrumentStateObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or finished,
        request_started_at_utc=started,
        request_finished_at_utc=finished,
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        instrument_id=instrument_id,
        inst_type_raw=str(row.get("instType") or "").strip(),
        rule_type_raw=str(row.get("ruleType") or "").strip(),
        state_raw=state_raw,
        http_status=int(http_status),
        venue_code=venue_code,
        get_performed=True,
        auth_header_sent=False,
        instrument_state_domain=INSTRUMENT_STATE_OUTPUT_DOMAIN,
        historical_reuse=False,
        target_row_count=1,
        body_sha256=digest,
    )


def validate_fresh_instrument_state_observation_v1(
    observation: FreshInstrumentStateObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    instrument_state_domain: str,
) -> ValidatedFreshInstrumentStateObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryInstrumentStateObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.instrument_id != instrument_id:
        raise LiveCanaryInstrumentStateObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(instrument_state_domain) != INSTRUMENT_STATE_OUTPUT_DOMAIN:
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_DOMAIN_INCOMPATIBLE")
    if observation.instrument_state_domain != INSTRUMENT_STATE_OUTPUT_DOMAIN:
        raise LiveCanaryInstrumentStateObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    raw = observation.state_raw
    if raw.strip() == "":
        raise LiveCanaryInstrumentStateObservationError("INSTRUMENT_STATE_FIELD_EMPTY:state")
    if raw != INSTRUMENT_STATE_ADMISSIBLE_RAW:
        if raw in INSTRUMENT_STATE_KNOWN_NEGATIVE_RAW:
            raise LiveCanaryInstrumentStateObservationError(
                f"INSTRUMENT_STATE_NOT_ADMISSIBLE:{raw}"
            )
        raise LiveCanaryInstrumentStateObservationError(f"INSTRUMENT_STATE_UNKNOWN_ENUM:{raw}")
    row_type = str(observation.inst_type_raw or "").strip().upper()
    if row_type and row_type != DEFAULT_INST_TYPE:
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_GEOMETRY_INST_TYPE_MISMATCH:{row_type}"
        )
    rule = str(observation.rule_type_raw or "").strip()
    if rule and rule != DEFAULT_RULE_TYPE:
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_GEOMETRY_RULE_TYPE_MISMATCH:{rule}"
        )
    return ValidatedFreshInstrumentStateObservationV1(
        raw=observation,
        state_raw=raw,
        semantic_value=INSTRUMENT_STATE_SEMANTIC_LIVE,
        comparison_domain=INSTRUMENT_STATE_COMPARISON_DOMAIN,
        consumer_precondition_satisfied=True,
    )


def classify_instrument_state_observation_class_v1(
    *,
    get_performed: bool,
    http_status: int,
    payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> str:
    if not get_performed:
        return OBSERVATION_CLASS_NOT_PERFORMED
    if int(http_status) != 200:
        return OBSERVATION_CLASS_VENUE_ERROR
    if not isinstance(payload, Mapping):
        return OBSERVATION_CLASS_MALFORMED
    if str(payload.get("code") or "") != "0":
        return OBSERVATION_CLASS_VENUE_ERROR
    data = payload.get("data")
    if not isinstance(data, list):
        return OBSERVATION_CLASS_MALFORMED
    matches = [
        item
        for item in data
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id
    ]
    if not matches:
        return OBSERVATION_CLASS_NOT_OBSERVED
    if len(matches) > 1:
        return OBSERVATION_CLASS_CONFLICTED
    row = matches[0]
    if "state" not in row or row.get("state") is None:
        return OBSERVATION_CLASS_NOT_OBSERVED
    if not isinstance(row.get("state"), str):
        return OBSERVATION_CLASS_MALFORMED
    raw = str(row.get("state") or "")
    if raw == "":
        return OBSERVATION_CLASS_NOT_OBSERVED
    if raw == INSTRUMENT_STATE_ADMISSIBLE_RAW:
        return OBSERVATION_CLASS_SUCCESS_LIVE
    if raw in INSTRUMENT_STATE_KNOWN_NEGATIVE_RAW:
        return OBSERVATION_CLASS_NOT_ADMISSIBLE
    return OBSERVATION_CLASS_UNKNOWN_ENUM


def _safe_headers(headers: Mapping[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in dict(headers).items():
        lowered = str(key).strip().lower()
        if any(marker in lowered for marker in FORBIDDEN_HEADER_NAME_MARKERS):
            continue
        if lowered in SAFE_HEADER_ALLOWLIST:
            out[str(key)] = str(value)
    return out


def persist_authorized_fresh_instrument_state_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
) -> dict[str, Any]:
    """Perform one unsigned public/instruments GET and persist forensic evidence.

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
        raise LiveCanaryInstrumentStateObservationError("OWNER_GO_MISMATCH")
    endpoint = public_instruments_query_path_v1()
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
                raise LiveCanaryInstrumentStateObservationError(
                    "PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN"
                )
        response = client.get(endpoint=endpoint, headers=headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_FRESH_GET_FAILED:{exc}"
        ) from exc
    finally:
        headers.clear()
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_instrument_state_observation_class_v1(
        get_performed=True,
        http_status=int(response.status_code),
        payload=payload,
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    pack.mkdir(parents=True, exist_ok=False)
    row: Mapping[str, Any] = {}
    data = payload.get("data") if isinstance(payload, Mapping) else None
    matches: list[Mapping[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, Mapping) and str(item.get("instId") or "") == DEFAULT_INSTRUMENT_ID:
                matches.append(item)
        if len(matches) == 1:
            row = matches[0]
    raw_fields = {
        "HTTP_STATUS": int(response.status_code),
        "VENUE_CODE": str(payload.get("code") or ""),
        "VENUE_MSG": str(payload.get("msg") or ""),
        "TARGET_ROW_COUNT": len(matches),
        "instId": row.get("instId") if "instId" in row else None,
        "instType": row.get("instType") if "instType" in row else None,
        "ruleType": row.get("ruleType") if "ruleType" in row else None,
        "state_raw": row.get("state") if "state" in row else None,
        "expTime": row.get("expTime") if "expTime" in row else None,
        "GET_VENUE_TS": GET_VENUE_TS_STATUS,
    }

    def _write_fail(reason: str, obs_class: str) -> None:
        forensic = {
            "DOCUMENT_CLASS": "INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1",
            "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
            "ENDPOINT": endpoint,
            "GET_REQUEST_COUNT_PUBLIC": 1,
            "HOST": REUSED_BINDING_REST_HOST,
            "METHOD": "GET",
            "OBSERVATION_CLASS": obs_class,
            "OWNER_GO": owned,
            "POST_COUNT": 0,
            "AUTH_HEADER_SENT": False,
            "AUTH_REQUIRED": False,
            "SECRET_VALUES_INCLUDED": False,
            "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
            "FAIL_CLOSED_REASON": reason,
            "GET_VENUE_TS": GET_VENUE_TS_STATUS,
            "raw_fields": raw_fields,
            "payload": payload,
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )

    if observation_class != OBSERVATION_CLASS_SUCCESS_LIVE:
        _write_fail(observation_class, observation_class)
        raise LiveCanaryInstrumentStateObservationError(
            f"INSTRUMENT_STATE_OBSERVATION_CLASS:{observation_class}"
        )
    try:
        observation = acquire_fresh_instrument_state_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            instruments_payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            observed_at_utc=response_time,
            endpoint=endpoint,
            http_status=int(response.status_code),
            get_performed=True,
            auth_header_sent=False,
            body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
            request_started_at_utc=request_time,
            request_finished_at_utc=response_time,
        )
        validated = validate_fresh_instrument_state_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            instrument_state_domain=INSTRUMENT_STATE_OUTPUT_DOMAIN,
        )
        observation_class = OBSERVATION_CLASS_SUCCESS_LIVE
    except LiveCanaryInstrumentStateObservationError as exc:
        obs_class = classify_instrument_state_observation_class_v1(
            get_performed=True,
            http_status=int(response.status_code),
            payload=payload,
        )
        _write_fail(str(exc), obs_class)
        raise
    snapshot = {
        "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
        "AUTH_HEADER_SENT": False,
        "AUTH_REQUIRED": False,
        "AUTH_CLASS": INSTRUMENT_STATE_AUTH_CLASS,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "EVIDENCE_READ_ONLY": True,
        "GET_REQUEST_COUNT_PUBLIC": 1,
        "GET_REQUEST_COUNT_AUTHENTICATED": 0,
        "GET_VENUE_TS": GET_VENUE_TS_STATUS,
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
        "INSTRUMENT_STATE_IS_NOT_LIVE_AUTHORIZATION": True,
        "RULE_TYPE_XPERP_IS_NOT_INSTRUMENT_STATE_AUTHORITY": True,
        "INST_TYPE_FUTURES_IS_NOT_INSTRUMENT_STATE_AUTHORITY": True,
        "EXP_TIME_IS_NOT_INSTRUMENT_STATE_AUTHORITY": True,
        "TICKER_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY": True,
        "MARK_PRICE_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY": True,
        "HISTORICAL_BTC_CURRENT_CLAIMS_ARE_NOT_CURRENT_AUTHORITY": True,
        "HISTORICAL_SUI_STATE_OBSERVATION_IS_NOT_AUTOMATIC_CURRENT_STATE": True,
        "UNKNOWN_STATE_IS_NOT_LIVE": True,
        "NOT_OBSERVED_IS_NOT_LIVE": True,
        "CANONICAL_REBIND_IS_NOT_CURRENT_STATE_PROOF": True,
        "FRESHNESS_POLICY": INSTRUMENT_STATE_FRESHNESS_POLICY,
        "TS_AGE_BOUND": INSTRUMENT_STATE_TS_AGE_BOUND,
        "observation": observation.to_dict(),
        "validated": {
            "state_raw": validated.state_raw,
            "semantic_value": validated.semantic_value,
            "comparison_domain": validated.comparison_domain,
            "consumer_precondition_satisfied": True,
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
        "DOCUMENT_CLASS": "INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "GET_REQUEST_COUNT_PUBLIC": 1,
        "GET_REQUEST_COUNT_AUTHENTICATED": 0,
        "GET_VENUE_TS": GET_VENUE_TS_STATUS,
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
        "STATE_RAW": observation.state_raw,
        "SEMANTIC_VALUE": validated.semantic_value,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "NETWORK_POST_PERFORMED": False,
        "NETWORK_AUTHENTICATED_GET_PERFORMED": False,
        "INSTRUMENT_STATE_IS_NOT_LIVE_AUTHORIZATION": True,
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
        "request_started_at_utc": observation.request_started_at_utc,
        "request_finished_at_utc": observation.request_finished_at_utc,
        "endpoint": endpoint,
        "observation_class": observation_class,
        "state_raw": observation.state_raw,
        "semantic_value": validated.semantic_value,
        "get_venue_ts": GET_VENUE_TS_STATUS,
    }

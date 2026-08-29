"""Decision-bound fresh POS_MODE observation for §11.13.5 pretrade.

Owner-adjudicated operative source is authenticated GET /api/v5/account/config.
The raw response field is posMode. This is account-global configuration, not
per-instrument, not posSide, not acctLv, not tdMode, not mgnMode, and not a TTL
cache. No POST. No set-position-mode. Venue tokens are not rewritten to posSide
``net``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_CONFIG,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)

POS_MODE_ENDPOINT_PATH = ENDPOINT_ACCOUNT_CONFIG
POS_MODE_OUTPUT_DOMAIN = "ACCOUNT_POS_MODE"
POS_MODE_COMPARISON_DOMAIN = "ACCOUNT_POS_MODE"
POS_MODE_FRESHNESS_POLICY = "CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION"
POS_MODE_TS_AGE_BOUND = "UNBOUND"
POS_MODE_NO_TS_FIELD = True
POS_MODE_AUTH_CLASS = "AUTHENTICATED_PRIVATE_GET"
POS_MODE_VENUE_SCOPE = "ACCOUNT_GLOBAL"
POS_MODE_CONSUMER_SCOPE = "CURRENT_SUI_PRETRADE_CONSUMER"
POS_MODE_REQUEST_GRAMMAR = "NONE"
POS_MODE_RESPONSE_FIELD = "posMode"
POS_MODE_VENUE_ALLOWED_VALUES = frozenset({"net_mode", "long_short_mode"})
POS_MODE_REQUIRED_VALUE = "net_mode"
POS_MODE_SEMANTIC_CLASS = "NET_POSITION_MODE"
POS_SIDE_TOKEN_NET = "net"
ACCTLV_IS_NOT_POS_MODE = True
POSSIDE_NET_IS_NOT_POS_MODE = True
TDMODE_CROSS_IS_NOT_POS_MODE = True
MGNMODE_CROSS_IS_NOT_POS_MODE = True
MAX_POSITIONS_IS_NOT_POS_MODE = True
SINGLE_SELECTED_FUTURE_IS_NOT_POS_MODE = True
ACCOUNT_MODE = "UNPROVEN"
ACCOUNT_MODE_PROOF_STATUS = "UNPROVEN"
OBSERVATION_CLASS_SUCCESS_TOKEN = "SUCCESS_TOKEN"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
HISTORICAL_BTC_PACK = "section_11_13_5_post_k_cross_imr_leverage_get_bind_v1"
HISTORICAL_BTC_INSTRUMENT_ID = HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID
FORBIDDEN_SOURCE_MARKERS = (
    "set-position-mode",
    "leverage-info",
    "max-avail-size",
    "account/max-size",
    "account/positions",
    "public/instruments",
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
OWNER_GO_THIS_SLICE = "PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"
UNBOUND_ACCOUNT_CONFIG_FIELDS_NOTE = (
    "Observed on the same GET. OBSERVED != CANONICALLY_BOUND. Not POS_MODE proof."
)


class LiveCanaryPosModeObservationError(RuntimeError):
    """Fail-closed fresh POS_MODE observation violation."""


@dataclass(frozen=True)
class FreshPosModeObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    consumer_instrument_id: str
    pos_mode_raw: str
    acct_lv_raw: str
    venue_scope: str
    consumer_scope: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    pos_mode_domain: str
    historical_reuse: bool
    body_sha256: str
    row_count: int
    unbound_account_config_fields: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pretrade_decision_id": self.pretrade_decision_id,
            "observed_at_utc": self.observed_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "consumer_instrument_id": self.consumer_instrument_id,
            "pos_mode_raw": self.pos_mode_raw,
            "acct_lv_raw": self.acct_lv_raw,
            "venue_scope": self.venue_scope,
            "consumer_scope": self.consumer_scope,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "pos_mode_domain": self.pos_mode_domain,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
            "row_count": self.row_count,
            "unbound_account_config_fields": dict(self.unbound_account_config_fields),
        }


@dataclass(frozen=True)
class ValidatedFreshPosModeObservationV1:
    raw: FreshPosModeObservationV1
    pos_mode: str
    comparison_domain: str
    semantic_class: str
    venue_scope: str
    consumer_scope: str


def account_config_query_path_v1() -> str:
    return POS_MODE_ENDPOINT_PATH


def classify_pos_mode_observation_class_v1(
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
    return OBSERVATION_CLASS_SUCCESS_TOKEN


def _raise_for_observation_class(observation_class: str) -> None:
    if observation_class == OBSERVATION_CLASS_SUCCESS_TOKEN:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "POS_MODE_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "POS_MODE_NETWORK_ERROR",
        OBSERVATION_CLASS_VENUE_ERROR: "POS_MODE_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "POS_MODE_MALFORMED",
    }
    raise LiveCanaryPosModeObservationError(
        mapping.get(observation_class, f"POS_MODE_FAIL_CLOSED:{observation_class}")
    )


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryPosModeObservationError("HISTORICAL_POS_MODE_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    if HISTORICAL_BTC_PACK in decision or HISTORICAL_BTC_PACK in ep:
        raise LiveCanaryPosModeObservationError("HISTORICAL_BTC_POS_MODE_PACK_REUSE_FORBIDDEN")
    if HISTORICAL_BTC_INSTRUMENT_ID in ep or instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryPosModeObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    if HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID in ep or "-SWAP" in instrument_id:
        raise LiveCanaryPosModeObservationError("SWAP_POS_MODE_SUBSTITUTION_FORBIDDEN")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in ep:
            raise LiveCanaryPosModeObservationError(
                f"POS_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN:{marker}"
            )


def _query_pairs(endpoint: str) -> dict[str, str]:
    query = str(endpoint or "").split("?", 1)
    if len(query) != 2:
        return {}
    return {str(k): str(v) for k, v in parse_qsl(query[1], keep_blank_values=True)}


def _config_object(*, payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], int]:
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryPosModeObservationError(
            f"POS_MODE_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryPosModeObservationError("POS_MODE_DATA_MISSING")
    objects = [item for item in data if isinstance(item, Mapping)]
    if not objects:
        raise LiveCanaryPosModeObservationError("POS_MODE_CONFIG_OBJECT_MISSING")
    if len(objects) != 1:
        raise LiveCanaryPosModeObservationError("POS_MODE_AMBIGUOUS_CONFIG_OBJECT")
    return objects[0], len(objects)


def _unbound_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key == POS_MODE_RESPONSE_FIELD:
            continue
        out[str(key)] = value
    return out


def acquire_fresh_pos_mode_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
) -> FreshPosModeObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryPosModeObservationError("PRETRADE_DECISION_ID_REQUIRED")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
    )
    observation_class = classify_pos_mode_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    if not auth_header_sent:
        raise LiveCanaryPosModeObservationError("POS_MODE_AUTH_HEADER_REQUIRED")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryPosModeObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != POS_MODE_ENDPOINT_PATH:
        raise LiveCanaryPosModeObservationError(f"POS_MODE_ENDPOINT_MISMATCH:{endpoint}")
    query = _query_pairs(endpoint)
    if query:
        raise LiveCanaryPosModeObservationError("POS_MODE_QUERY_FORBIDDEN")
    row, row_count = _config_object(payload=payload)
    if POS_MODE_RESPONSE_FIELD not in row:
        raise LiveCanaryPosModeObservationError("POS_MODE_FIELD_MISSING:posMode")
    raw_value = row.get(POS_MODE_RESPONSE_FIELD)
    if raw_value is None:
        raise LiveCanaryPosModeObservationError("POS_MODE_FIELD_NULL:posMode")
    pos_mode_raw = str(raw_value).strip()
    if not pos_mode_raw:
        raise LiveCanaryPosModeObservationError("POS_MODE_FIELD_MISSING:posMode")
    if pos_mode_raw == POS_SIDE_TOKEN_NET:
        raise LiveCanaryPosModeObservationError("POS_MODE_POSSIDE_TOKEN_REJECTED:net")
    if pos_mode_raw not in POS_MODE_VENUE_ALLOWED_VALUES:
        raise LiveCanaryPosModeObservationError(f"POS_MODE_UNKNOWN_TOKEN:{pos_mode_raw}")
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    acct_lv_raw = str(row.get("acctLv") or "")
    return FreshPosModeObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        consumer_instrument_id=instrument_id,
        pos_mode_raw=pos_mode_raw,
        acct_lv_raw=acct_lv_raw,
        venue_scope=POS_MODE_VENUE_SCOPE,
        consumer_scope=POS_MODE_CONSUMER_SCOPE,
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=True,
        pos_mode_domain=POS_MODE_OUTPUT_DOMAIN,
        historical_reuse=False,
        body_sha256=digest,
        row_count=int(row_count),
        unbound_account_config_fields=_unbound_fields(row),
    )


def validate_fresh_pos_mode_observation_v1(
    observation: FreshPosModeObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    pos_mode_domain: str,
) -> ValidatedFreshPosModeObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryPosModeObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.consumer_instrument_id != instrument_id:
        raise LiveCanaryPosModeObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(pos_mode_domain) != POS_MODE_OUTPUT_DOMAIN:
        raise LiveCanaryPosModeObservationError("POS_MODE_DOMAIN_INCOMPATIBLE")
    if observation.pos_mode_domain != POS_MODE_OUTPUT_DOMAIN:
        raise LiveCanaryPosModeObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.venue_scope != POS_MODE_VENUE_SCOPE:
        raise LiveCanaryPosModeObservationError("POS_MODE_VENUE_SCOPE_MISMATCH")
    if observation.consumer_scope != POS_MODE_CONSUMER_SCOPE:
        raise LiveCanaryPosModeObservationError("POS_MODE_CONSUMER_SCOPE_MISMATCH")
    if observation.row_count != 1:
        raise LiveCanaryPosModeObservationError("POS_MODE_AMBIGUOUS_CONFIG_OBJECT")
    if observation.pos_mode_raw != POS_MODE_REQUIRED_VALUE:
        raise LiveCanaryPosModeObservationError(
            f"POS_MODE_REQUIRED_VALUE_MISMATCH:{observation.pos_mode_raw}"
        )
    return ValidatedFreshPosModeObservationV1(
        raw=observation,
        pos_mode=observation.pos_mode_raw,
        comparison_domain=POS_MODE_COMPARISON_DOMAIN,
        semantic_class=POS_MODE_SEMANTIC_CLASS,
        venue_scope=observation.venue_scope,
        consumer_scope=observation.consumer_scope,
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


def persist_authorized_fresh_pos_mode_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
    vault_file: Path | str,
) -> dict[str, Any]:
    """Perform one authenticated account/config GET and persist forensic evidence.

    No POST. No set-position-mode. The pack is not an operative cache.
    """
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REQUIRED_CREDENTIAL_CLASS,
        REQUIRED_SECRETREF_URI,
        USER_AGENT_CANARY,
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

    owned = str(owner_go or "").strip()
    if owned != OWNER_GO_THIS_SLICE:
        raise LiveCanaryPosModeObservationError("OWNER_GO_MISMATCH")
    endpoint = account_config_query_path_v1()
    client = LiveCanaryHttpClientV1(
        rest_base=PRODUCTION_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=UrllibLiveCanaryTransportV1(wire_send_enabled=True),
        max_retries=0,
        timeout_seconds=10.0,
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
        signed_target = parsed.path
        if signed_target != endpoint:
            raise LiveCanaryPosModeObservationError(
                f"SIGNED_REQUEST_TARGET_MISMATCH:{signed_target}"
            )
        auth_headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
        auth_headers["User-Agent"] = USER_AGENT_CANARY
        response = client.get(endpoint=endpoint, headers=auth_headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryPosModeObservationError(f"POS_MODE_FRESH_GET_FAILED:{exc}") from exc
    finally:
        auth_headers.clear()
        release_live_canary_ephemeral_material_v1(handle)
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_pos_mode_observation_class_v1(
        get_performed=True,
        http_status=int(response.status_code),
        payload=payload,
    )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    pack.mkdir(parents=True, exist_ok=False)
    data = payload.get("data") if isinstance(payload, Mapping) else None
    raw_rows: list[dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, Mapping):
                raw_rows.append(dict(item))
    raw_fields = {
        "HTTP_STATUS": int(response.status_code),
        "VENUE_CODE": str(payload.get("code") or ""),
        "VENUE_MSG": str(payload.get("msg") or ""),
        "POS_MODE_RESPONSE_FIELD": POS_MODE_RESPONSE_FIELD,
        "VENUE_SCOPE": POS_MODE_VENUE_SCOPE,
        "CONSUMER_SCOPE": POS_MODE_CONSUMER_SCOPE,
        "UNBOUND_ACCOUNT_CONFIG_FIELDS_NOTE": UNBOUND_ACCOUNT_CONFIG_FIELDS_NOTE,
        "raw_rows": raw_rows,
    }
    common_fail = {
        "DOCUMENT_CLASS": "POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "GET_REQUEST_COUNT_AUTHENTICATED": 1,
        "HOST": REUSED_BINDING_REST_HOST,
        "METHOD": "GET",
        "OWNER_GO": owned,
        "POST_COUNT": 0,
        "AUTH_HEADER_SENT": True,
        "AUTH_REQUIRED": True,
        "SECRET_VALUES_INCLUDED": False,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "DEFAULT_POS_MODE_USED": False,
        "HISTORICAL_POS_MODE_REUSED": False,
        "LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF": False,
        "SET_POSITION_MODE_EXECUTED": False,
        "raw_fields": raw_fields,
        "payload": payload,
    }
    if observation_class != OBSERVATION_CLASS_SUCCESS_TOKEN:
        forensic = {**common_fail, "OBSERVATION_CLASS": observation_class}
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        _raise_for_observation_class(observation_class)
    try:
        observation = acquire_fresh_pos_mode_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            observed_at_utc=response_time,
            endpoint=endpoint,
            http_status=int(response.status_code),
            get_performed=True,
            auth_header_sent=True,
            body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
        )
        validated = validate_fresh_pos_mode_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            pos_mode_domain=POS_MODE_OUTPUT_DOMAIN,
        )
        observation_class = OBSERVATION_CLASS_SUCCESS_TOKEN
    except LiveCanaryPosModeObservationError as exc:
        forensic = {
            **common_fail,
            "OBSERVATION_CLASS": OBSERVATION_CLASS_MALFORMED,
            "FAIL_CLOSED_REASON": str(exc),
        }
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        raise
    snapshot = {
        "AUTHENTICATION_REQUIREMENT": "AUTHENTICATED_PRIVATE_GET",
        "AUTH_HEADER_SENT": True,
        "AUTH_REQUIRED": True,
        "AUTH_CLASS": POS_MODE_AUTH_CLASS,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_OPERATIVE_CACHE",
        "ENDPOINT": endpoint,
        "EVIDENCE_READ_ONLY": True,
        "GET_REQUEST_COUNT_AUTHENTICATED": 1,
        "GET_REQUEST_COUNT_PUBLIC": 0,
        "HOST": REUSED_BINDING_REST_HOST,
        "METHOD": "GET",
        "NO_POST": True,
        "OWNER_GO": owned,
        "POST_COUNT": 0,
        "SECRET_VALUES_INCLUDED": False,
        "SECRETREF_URI": REQUIRED_SECRETREF_URI,
        "CREDENTIAL_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "TARGET_VENUE": "OKX_EEA",
        "POS_MODE_VENUE_SCOPE": POS_MODE_VENUE_SCOPE,
        "POS_MODE_CONSUMER_SCOPE": POS_MODE_CONSUMER_SCOPE,
        "POS_MODE_REQUEST_GRAMMAR": POS_MODE_REQUEST_GRAMMAR,
        "POS_MODE_RESPONSE_FIELD": POS_MODE_RESPONSE_FIELD,
        "ACCTLV_IS_NOT_POS_MODE": ACCTLV_IS_NOT_POS_MODE,
        "POSSIDE_NET_IS_NOT_POS_MODE": POSSIDE_NET_IS_NOT_POS_MODE,
        "TDMODE_CROSS_IS_NOT_POS_MODE": TDMODE_CROSS_IS_NOT_POS_MODE,
        "MGNMODE_CROSS_IS_NOT_POS_MODE": MGNMODE_CROSS_IS_NOT_POS_MODE,
        "ACCOUNT_MODE": ACCOUNT_MODE,
        "ACCOUNT_MODE_PROOF_STATUS": ACCOUNT_MODE_PROOF_STATUS,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "HISTORICAL_POS_MODE_REUSED": False,
        "DEFAULT_POS_MODE_USED": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "SET_POSITION_MODE_EXECUTED": False,
        "LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF": False,
        "FRESHNESS_POLICY": POS_MODE_FRESHNESS_POLICY,
        "TS_AGE_BOUND": POS_MODE_TS_AGE_BOUND,
        "NO_TS_FIELD": POS_MODE_NO_TS_FIELD,
        "observation": observation.to_dict(),
        "validated": {
            "pos_mode": validated.pos_mode,
            "comparison_domain": validated.comparison_domain,
            "semantic_class": validated.semantic_class,
            "venue_scope": validated.venue_scope,
            "consumer_scope": validated.consumer_scope,
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
        "DOCUMENT_CLASS": "POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "TARGET_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "OBSERVATION_CLASS": observation_class,
        "POS_MODE_RAW": observation.pos_mode_raw,
        "ACCT_LV_RAW": observation.acct_lv_raw,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "HISTORICAL_POS_MODE_REUSED": False,
        "NETWORK_POST_PERFORMED": False,
        "NETWORK_AUTHENTICATED_GET_PERFORMED": True,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "DEFAULT_POS_MODE_USED": False,
        "TRADING_PERFORMED": False,
        "SET_POSITION_MODE_EXECUTED": False,
        "ACCOUNT_MODE_MUTATION_PERFORMED": False,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF": False,
        "TDMODE_CROSS_REUSED_AS_POS_MODE_PROOF": False,
        "MGNMODE_CROSS_REUSED_AS_POS_MODE_PROOF": False,
        "ACCTLV_USED_AS_POS_MODE_PROOF": False,
        "POS_SIDE_INFERENCE_USED_AS_AUTHORITY": False,
    }
    redaction = {
        "AUTH_HEADER_PERSISTED": False,
        "COOKIE_PERSISTED": False,
        "SECRET_VALUES_INCLUDED": False,
        "SECRETREF_URI_PERSISTED": True,
        "SECRET_MATERIAL_PERSISTED": False,
    }
    zero_write = {
        "DELETE_COUNT": 0,
        "FUNDING_EXECUTED": False,
        "GET_COUNT_PUBLIC": 0,
        "GET_COUNT_AUTHENTICATED": 1,
        "ORDER_EXECUTED": False,
        "PATCH_COUNT": 0,
        "POST_COUNT": 0,
        "PUT_COUNT": 0,
        "RETRY_EXECUTED": False,
        "SET_POSITION_MODE_EXECUTED": False,
        "ACCOUNT_MODE_MUTATION_PERFORMED": False,
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
        "pos_mode": validated.pos_mode,
        "semantic_class": validated.semantic_class,
        "acct_lv_raw": observation.acct_lv_raw,
        "venue_scope": validated.venue_scope,
        "consumer_scope": validated.consumer_scope,
    }

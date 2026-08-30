"""Decision-bound MARGIN_MODE observation for §11.13.5 pretrade.

OKX does not expose a global account-level cross/isolated setting analogous
to posMode. Cross and isolated positions may coexist. Margin mode for a trade
is chosen per order via tdMode. Position rows may carry mgnMode. Empty
positions data is not a margin mode and is not zero.

This owner binds the current single-selected-future execution tdMode. It does
not bind ACCOUNT_MODE, POS_MODE, LEVERAGE, or AVAILABLE_MARGIN. No POST. No
set-isolated-mode. No set-leverage. acctLv and posMode are not sources.
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
    DEFAULT_TD_MODE,
    ENDPOINT_ACCOUNT_POSITIONS,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)

MARGIN_MODE_ENDPOINT_PATH = ENDPOINT_ACCOUNT_POSITIONS
MARGIN_MODE_OUTPUT_DOMAIN = "ORDER_TDMODE"
MARGIN_MODE_COMPARISON_DOMAIN = "ORDER_TDMODE"
MARGIN_MODE_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
MARGIN_MODE_TS_AGE_BOUND = "UNBOUND"
MARGIN_MODE_NO_TS_FIELD = True
MARGIN_MODE_AUTH_CLASS = "AUTHENTICATED_PRIVATE_GET"
MARGIN_MODE_VENUE_SCOPE = "CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION"
MARGIN_MODE_CONSUMER_SCOPE = "CURRENT_SUI_PRETRADE_CONSUMER"
MARGIN_MODE_REQUEST_GRAMMAR = "NONE"
MARGIN_MODE_POSITION_RESPONSE_FIELD = "mgnMode"
MARGIN_MODE_ORDER_FIELD = "tdMode"
MARGIN_MODE_VENUE_ALLOWED_VALUES = frozenset({"cross", "isolated"})
MARGIN_MODE_REQUIRED_ORDER_TD_MODE = DEFAULT_TD_MODE
MARGIN_MODE_SEMANTIC_CLASS_ORDER_TDMODE_CROSS = "CURRENT_SINGLE_SELECTED_FUTURE_ORDER_TDMODE_CROSS"
MARGIN_MODE_SEMANTIC_CLASS_POSITION_MATCH = (
    "CURRENT_SINGLE_SELECTED_FUTURE_POSITION_MGNMODE_MATCHES_ORDER_TDMODE"
)
POSITION_MGN_MODE_STATUS_NOT_OBSERVED = "NOT_OBSERVED"
POSITION_MGN_MODE_STATUS_OBSERVED = "OBSERVED"
EMPTY_DATA_IS_NOT_ZERO = True
ABSENT_OR_NOT_RETURNED_IS_NOT_ZERO = True
MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS = False
ACCTLV_IS_NOT_MARGIN_MODE = True
POSMODE_IS_NOT_MARGIN_MODE = True
CTISOMODE_IS_NOT_MARGIN_MODE = True
MGNISOMODE_IS_NOT_MARGIN_MODE = True
LEVERAGE_MGNMODE_IS_NOT_MARGIN_MODE_AUTHORITY = True
DEFAULT_TDMODE_IS_NOT_ACCOUNT_MODE_PROOF = True
ACCOUNT_MODE = "UNPROVEN"
ACCOUNT_MODE_PROOF_STATUS = "UNPROVEN"
OBSERVATION_CLASS_SUCCESS_TOKEN = "SUCCESS_TOKEN"
OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED = "SUCCESS_NOT_OBSERVED"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
HISTORICAL_BTC_PACK = "section_11_13_5_post_k_cross_imr_leverage_get_bind_v1"
HISTORICAL_BTC_INSTRUMENT_ID = HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID
FORBIDDEN_SOURCE_MARKERS = (
    "account/config",
    "set-isolated-mode",
    "set-leverage",
    "set-position-mode",
    "leverage-info",
    "max-avail-size",
    "account/max-size",
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
OWNER_GO_THIS_SLICE = "PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"


class LiveCanaryMarginModeObservationError(RuntimeError):
    """Fail-closed fresh MARGIN_MODE observation violation."""


@dataclass(frozen=True)
class FreshMarginModeObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    consumer_instrument_id: str
    planned_td_mode: str
    position_mgn_mode_raw: str
    position_mgn_mode_status: str
    target_row_count: int
    total_row_count: int
    venue_scope: str
    consumer_scope: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    margin_mode_domain: str
    historical_reuse: bool
    body_sha256: str
    other_instrument_mgn_modes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pretrade_decision_id": self.pretrade_decision_id,
            "observed_at_utc": self.observed_at_utc,
            "venue": self.venue,
            "rest_host": self.rest_host,
            "method": self.method,
            "endpoint": self.endpoint,
            "consumer_instrument_id": self.consumer_instrument_id,
            "planned_td_mode": self.planned_td_mode,
            "position_mgn_mode_raw": self.position_mgn_mode_raw,
            "position_mgn_mode_status": self.position_mgn_mode_status,
            "target_row_count": self.target_row_count,
            "total_row_count": self.total_row_count,
            "venue_scope": self.venue_scope,
            "consumer_scope": self.consumer_scope,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "margin_mode_domain": self.margin_mode_domain,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
            "other_instrument_mgn_modes": list(self.other_instrument_mgn_modes),
            "EMPTY_DATA_IS_NOT_ZERO": EMPTY_DATA_IS_NOT_ZERO,
            "MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS": (
                MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS
            ),
        }


@dataclass(frozen=True)
class ValidatedFreshMarginModeObservationV1:
    raw: FreshMarginModeObservationV1
    order_td_mode: str
    position_mgn_mode_raw: str
    position_mgn_mode_status: str
    comparison_domain: str
    semantic_class: str
    venue_scope: str
    consumer_scope: str


def account_positions_query_path_v1() -> str:
    return MARGIN_MODE_ENDPOINT_PATH


def require_canonical_execution_td_mode_v1(td_mode: str) -> str:
    raw = str(td_mode or "").strip()
    if not raw:
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_TDMODE_MISSING")
    if raw not in MARGIN_MODE_VENUE_ALLOWED_VALUES:
        raise LiveCanaryMarginModeObservationError(f"MARGIN_MODE_UNKNOWN_TDMODE:{raw}")
    if raw != MARGIN_MODE_REQUIRED_ORDER_TD_MODE:
        raise LiveCanaryMarginModeObservationError(
            f"MARGIN_MODE_REQUIRED_ORDER_TDMODE_MISMATCH:{raw}"
        )
    return raw


def classify_margin_mode_observation_class_v1(
    *,
    get_performed: bool,
    http_status: int,
    payload: Mapping[str, Any] | None,
    target_row_count: int | None = None,
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
    if target_row_count == 0 or (target_row_count is None and not data):
        return OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED
    if target_row_count == 0:
        return OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED
    return OBSERVATION_CLASS_SUCCESS_TOKEN


def _raise_for_observation_class(observation_class: str) -> None:
    if observation_class in {
        OBSERVATION_CLASS_SUCCESS_TOKEN,
        OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED,
    }:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "MARGIN_MODE_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "MARGIN_MODE_NETWORK_ERROR",
        OBSERVATION_CLASS_VENUE_ERROR: "MARGIN_MODE_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "MARGIN_MODE_MALFORMED",
    }
    raise LiveCanaryMarginModeObservationError(
        mapping.get(observation_class, f"MARGIN_MODE_FAIL_CLOSED:{observation_class}")
    )


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryMarginModeObservationError("HISTORICAL_MARGIN_MODE_REUSE_FORBIDDEN")
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    if HISTORICAL_BTC_PACK in decision or HISTORICAL_BTC_PACK in ep:
        raise LiveCanaryMarginModeObservationError(
            "HISTORICAL_BTC_MARGIN_MODE_PACK_REUSE_FORBIDDEN"
        )
    if HISTORICAL_BTC_INSTRUMENT_ID in ep or instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryMarginModeObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    if HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID in ep or "-SWAP" in instrument_id:
        raise LiveCanaryMarginModeObservationError("SWAP_MARGIN_MODE_SUBSTITUTION_FORBIDDEN")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in ep:
            raise LiveCanaryMarginModeObservationError(
                f"MARGIN_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN:{marker}"
            )


def _query_pairs(endpoint: str) -> dict[str, str]:
    query = str(endpoint or "").split("?", 1)
    if len(query) != 2:
        return {}
    return {str(k): str(v) for k, v in parse_qsl(query[1], keep_blank_values=True)}


def _select_target_rows(
    *,
    payload: Mapping[str, Any],
    instrument_id: str,
) -> tuple[list[Mapping[str, Any]], int, tuple[str, ...]]:
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryMarginModeObservationError(
            f"MARGIN_MODE_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list):
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_DATA_MISSING")
    rows = [item for item in data if isinstance(item, Mapping)]
    target = [item for item in rows if str(item.get("instId") or "").strip() == instrument_id]
    other_modes: list[str] = []
    for item in rows:
        if str(item.get("instId") or "").strip() == instrument_id:
            continue
        mode = item.get(MARGIN_MODE_POSITION_RESPONSE_FIELD)
        if mode is not None and str(mode).strip():
            other_modes.append(str(mode).strip())
    return target, len(rows), tuple(other_modes)


def acquire_fresh_margin_mode_observation_from_payload_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    planned_td_mode: str,
    observed_at_utc: str,
    endpoint: str,
    http_status: int,
    get_performed: bool,
    rest_host: str = REUSED_BINDING_REST_HOST,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
) -> FreshMarginModeObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryMarginModeObservationError("PRETRADE_DECISION_ID_REQUIRED")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
    )
    planned = require_canonical_execution_td_mode_v1(planned_td_mode)
    if not auth_header_sent:
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_AUTH_HEADER_REQUIRED")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryMarginModeObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != MARGIN_MODE_ENDPOINT_PATH:
        raise LiveCanaryMarginModeObservationError(f"MARGIN_MODE_ENDPOINT_MISMATCH:{endpoint}")
    query = _query_pairs(endpoint)
    if query:
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_QUERY_FORBIDDEN")
    observation_class = classify_margin_mode_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    target_rows, total_row_count, other_modes = _select_target_rows(
        payload=payload, instrument_id=instrument_id
    )
    if not target_rows:
        position_mgn_mode_raw = ""
        position_mgn_mode_status = POSITION_MGN_MODE_STATUS_NOT_OBSERVED
    else:
        modes: list[str] = []
        for row in target_rows:
            if MARGIN_MODE_POSITION_RESPONSE_FIELD not in row:
                raise LiveCanaryMarginModeObservationError("MARGIN_MODE_FIELD_MISSING:mgnMode")
            raw_value = row.get(MARGIN_MODE_POSITION_RESPONSE_FIELD)
            if raw_value is None:
                raise LiveCanaryMarginModeObservationError("MARGIN_MODE_FIELD_NULL:mgnMode")
            mode = str(raw_value).strip()
            if not mode:
                raise LiveCanaryMarginModeObservationError("MARGIN_MODE_FIELD_MISSING:mgnMode")
            if mode not in MARGIN_MODE_VENUE_ALLOWED_VALUES:
                raise LiveCanaryMarginModeObservationError(f"MARGIN_MODE_UNKNOWN_TOKEN:{mode}")
            modes.append(mode)
        unique = set(modes)
        if len(unique) != 1:
            raise LiveCanaryMarginModeObservationError(
                f"MARGIN_MODE_AMBIGUOUS_TARGET_MGNMODE:{','.join(sorted(unique))}"
            )
        position_mgn_mode_raw = modes[0]
        position_mgn_mode_status = POSITION_MGN_MODE_STATUS_OBSERVED
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshMarginModeObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        consumer_instrument_id=instrument_id,
        planned_td_mode=planned,
        position_mgn_mode_raw=position_mgn_mode_raw,
        position_mgn_mode_status=position_mgn_mode_status,
        target_row_count=len(target_rows),
        total_row_count=int(total_row_count),
        venue_scope=MARGIN_MODE_VENUE_SCOPE,
        consumer_scope=MARGIN_MODE_CONSUMER_SCOPE,
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=True,
        margin_mode_domain=MARGIN_MODE_OUTPUT_DOMAIN,
        historical_reuse=False,
        body_sha256=digest,
        other_instrument_mgn_modes=other_modes,
    )


def validate_fresh_margin_mode_observation_v1(
    observation: FreshMarginModeObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    margin_mode_domain: str,
    planned_td_mode: str,
) -> ValidatedFreshMarginModeObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryMarginModeObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.consumer_instrument_id != instrument_id:
        raise LiveCanaryMarginModeObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(margin_mode_domain) != MARGIN_MODE_OUTPUT_DOMAIN:
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_DOMAIN_INCOMPATIBLE")
    if observation.margin_mode_domain != MARGIN_MODE_OUTPUT_DOMAIN:
        raise LiveCanaryMarginModeObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.venue_scope != MARGIN_MODE_VENUE_SCOPE:
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_VENUE_SCOPE_MISMATCH")
    if observation.consumer_scope != MARGIN_MODE_CONSUMER_SCOPE:
        raise LiveCanaryMarginModeObservationError("MARGIN_MODE_CONSUMER_SCOPE_MISMATCH")
    planned = require_canonical_execution_td_mode_v1(planned_td_mode)
    if observation.planned_td_mode != planned:
        raise LiveCanaryMarginModeObservationError("OBSERVATION_TDMODE_MISMATCH")
    if observation.position_mgn_mode_status == POSITION_MGN_MODE_STATUS_NOT_OBSERVED:
        if observation.position_mgn_mode_raw:
            raise LiveCanaryMarginModeObservationError("EMPTY_POSITIONS_NORMALIZED_FORBIDDEN")
        semantic = MARGIN_MODE_SEMANTIC_CLASS_ORDER_TDMODE_CROSS
    elif observation.position_mgn_mode_status == POSITION_MGN_MODE_STATUS_OBSERVED:
        if observation.position_mgn_mode_raw != planned:
            raise LiveCanaryMarginModeObservationError(
                "MARGIN_MODE_SCOPED_CONFLICT:"
                f"order_tdMode={planned}:position_mgnMode={observation.position_mgn_mode_raw}"
            )
        semantic = MARGIN_MODE_SEMANTIC_CLASS_POSITION_MATCH
    else:
        raise LiveCanaryMarginModeObservationError(
            f"MARGIN_MODE_UNKNOWN_POSITION_STATUS:{observation.position_mgn_mode_status}"
        )
    return ValidatedFreshMarginModeObservationV1(
        raw=observation,
        order_td_mode=planned,
        position_mgn_mode_raw=observation.position_mgn_mode_raw,
        position_mgn_mode_status=observation.position_mgn_mode_status,
        comparison_domain=MARGIN_MODE_COMPARISON_DOMAIN,
        semantic_class=semantic,
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


def persist_authorized_fresh_margin_mode_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
    vault_file: Path | str,
    planned_td_mode: str = MARGIN_MODE_REQUIRED_ORDER_TD_MODE,
) -> dict[str, Any]:
    """Perform one authenticated unfiltered positions GET and persist forensic evidence.

    No POST. No margin-mode mutation. Empty data is not a margin mode.
    The pack is not an operative cache.
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
        raise LiveCanaryMarginModeObservationError("OWNER_GO_MISMATCH")
    planned = require_canonical_execution_td_mode_v1(planned_td_mode)
    endpoint = account_positions_query_path_v1()
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
            raise LiveCanaryMarginModeObservationError(
                f"SIGNED_REQUEST_TARGET_MISMATCH:{signed_target}"
            )
        auth_headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
        auth_headers["User-Agent"] = USER_AGENT_CANARY
        response = client.get(endpoint=endpoint, headers=auth_headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryMarginModeObservationError(f"MARGIN_MODE_FRESH_GET_FAILED:{exc}") from exc
    finally:
        auth_headers.clear()
        release_live_canary_ephemeral_material_v1(handle)
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_margin_mode_observation_class_v1(
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
        "MARGIN_MODE_POSITION_RESPONSE_FIELD": MARGIN_MODE_POSITION_RESPONSE_FIELD,
        "MARGIN_MODE_ORDER_FIELD": MARGIN_MODE_ORDER_FIELD,
        "VENUE_SCOPE": MARGIN_MODE_VENUE_SCOPE,
        "CONSUMER_SCOPE": MARGIN_MODE_CONSUMER_SCOPE,
        "EMPTY_DATA_IS_NOT_ZERO": EMPTY_DATA_IS_NOT_ZERO,
        "raw_rows": raw_rows,
    }
    common_fail = {
        "DOCUMENT_CLASS": "MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "raw_fields": raw_fields,
        "payload": payload,
    }
    if observation_class not in {
        OBSERVATION_CLASS_SUCCESS_TOKEN,
        OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED,
    }:
        forensic = {**common_fail, "OBSERVATION_CLASS": observation_class}
        encoded = json.dumps(forensic, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (pack / "GET_SNAPSHOT.sanitized.json").write_bytes(encoded)
        (pack / "MANIFEST.sha256").write_text(
            f"{hashlib.sha256(encoded).hexdigest()}  GET_SNAPSHOT.sanitized.json\n",
            encoding="utf-8",
        )
        _raise_for_observation_class(observation_class)
    try:
        observation = acquire_fresh_margin_mode_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            planned_td_mode=planned,
            observed_at_utc=response_time,
            endpoint=endpoint,
            http_status=int(response.status_code),
            get_performed=True,
            auth_header_sent=True,
            body_sha256=hashlib.sha256(response.body_bytes).hexdigest(),
        )
        validated = validate_fresh_margin_mode_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            margin_mode_domain=MARGIN_MODE_OUTPUT_DOMAIN,
            planned_td_mode=planned,
        )
        if observation.position_mgn_mode_status == POSITION_MGN_MODE_STATUS_NOT_OBSERVED:
            observation_class = OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED
        else:
            observation_class = OBSERVATION_CLASS_SUCCESS_TOKEN
    except LiveCanaryMarginModeObservationError as exc:
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
        "AUTH_CLASS": MARGIN_MODE_AUTH_CLASS,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "MARGIN_MODE_VENUE_SCOPE": MARGIN_MODE_VENUE_SCOPE,
        "MARGIN_MODE_CONSUMER_SCOPE": MARGIN_MODE_CONSUMER_SCOPE,
        "MARGIN_MODE_REQUEST_GRAMMAR": MARGIN_MODE_REQUEST_GRAMMAR,
        "MARGIN_MODE_POSITION_RESPONSE_FIELD": MARGIN_MODE_POSITION_RESPONSE_FIELD,
        "MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS": MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS,
        "ACCTLV_IS_NOT_MARGIN_MODE": ACCTLV_IS_NOT_MARGIN_MODE,
        "POSMODE_IS_NOT_MARGIN_MODE": POSMODE_IS_NOT_MARGIN_MODE,
        "ACCOUNT_MODE": ACCOUNT_MODE,
        "ACCOUNT_MODE_PROOF_STATUS": ACCOUNT_MODE_PROOF_STATUS,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "LEVERAGE_MGNMODE_IS_NOT_MARGIN_MODE_AUTHORITY": (
            LEVERAGE_MGNMODE_IS_NOT_MARGIN_MODE_AUTHORITY
        ),
        "ZERO_NORMALIZATION_PERFORMED": False,
        "FRESHNESS_POLICY": MARGIN_MODE_FRESHNESS_POLICY,
        "TS_AGE_BOUND": MARGIN_MODE_TS_AGE_BOUND,
        "NO_TS_FIELD": MARGIN_MODE_NO_TS_FIELD,
        "observation": observation.to_dict(),
        "validated": {
            "order_td_mode": validated.order_td_mode,
            "position_mgn_mode_raw": validated.position_mgn_mode_raw,
            "position_mgn_mode_status": validated.position_mgn_mode_status,
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
        "DOCUMENT_CLASS": "MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "ORDER_TD_MODE": observation.planned_td_mode,
        "POSITION_MGN_MODE_RAW": observation.position_mgn_mode_raw or "NOT_OBSERVED",
        "POSITION_MGN_MODE_STATUS": observation.position_mgn_mode_status,
        "TARGET_ROW_COUNT": observation.target_row_count,
        "TOTAL_ROW_COUNT": observation.total_row_count,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "NETWORK_POST_PERFORMED": False,
        "NETWORK_AUTHENTICATED_GET_PERFORMED": True,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY": False,
        "TRADING_PERFORMED": False,
        "MARGIN_MODE_MUTATION_PERFORMED": False,
        "ACCOUNT_MODE_MUTATION_PERFORMED": False,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS": False,
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
        "MARGIN_MODE_MUTATION_PERFORMED": False,
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
        "order_td_mode": validated.order_td_mode,
        "position_mgn_mode_raw": validated.position_mgn_mode_raw,
        "position_mgn_mode_status": validated.position_mgn_mode_status,
        "semantic_class": validated.semantic_class,
        "venue_scope": validated.venue_scope,
        "consumer_scope": validated.consumer_scope,
    }

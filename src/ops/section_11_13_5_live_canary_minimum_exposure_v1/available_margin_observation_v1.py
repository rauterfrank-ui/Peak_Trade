"""Decision-bound AVAILABLE_MARGIN observation for §11.13.5 pretrade.

AVAILABLE_MARGIN is currency-scoped cross-margin free margin, not a global
account scalar, not MAX_AVAILABLE, not max-avail-size, and not availBal.
First-Party OKX free margin for cross futures is details[].availEq.
Account-level availEq is a different USD-denominated account-equity field.
USD is not USDC. Empty details are not zero. No POST. No trading.
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
from urllib.parse import parse_qsl, urlparse

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_TD_MODE,
    ENDPOINT_ACCOUNT_BALANCE,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
    SETTLEMENT_ACCOUNT_TRUTH,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    require_canonical_execution_td_mode_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    utc_now_iso_v1,
)

AVAILABLE_MARGIN_ENDPOINT_PATH = ENDPOINT_ACCOUNT_BALANCE
AVAILABLE_MARGIN_OUTPUT_DOMAIN = "CURRENCY_SCOPED_AVAILABLE_EQUITY"
AVAILABLE_MARGIN_COMPARISON_DOMAIN = "CURRENCY_SCOPED_AVAILABLE_EQUITY"
AVAILABLE_MARGIN_UNIT = "CURRENCY_NATIVE"
AVAILABLE_MARGIN_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
AVAILABLE_MARGIN_TS_AGE_BOUND = "UNBOUND"
AVAILABLE_MARGIN_VENUE_U_TIME_FIELD = "uTime"
AVAILABLE_MARGIN_AUTH_CLASS = "AUTHENTICATED_PRIVATE_GET"
AVAILABLE_MARGIN_VENUE_SCOPE = "CURRENCY_SCOPED_SETTLEMENT_ACCOUNT_TRUTH"
AVAILABLE_MARGIN_CONSUMER_SCOPE = "CURRENT_SUI_PRETRADE_CONSUMER"
AVAILABLE_MARGIN_REQUEST_GRAMMAR = "NONE"
AVAILABLE_MARGIN_RESPONSE_FIELD = "details.availEq"
AVAILABLE_MARGIN_ACCOUNT_LEVEL_FIELD = "availEq"
AVAILABLE_MARGIN_REQUIRED_CCY = SETTLEMENT_ACCOUNT_TRUTH
AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY = "USD"
AVAILABLE_MARGIN_REQUIRED_TD_MODE = DEFAULT_TD_MODE
AVAILABLE_MARGIN_SEMANTIC_CLASS = "CURRENCY_SCOPED_CROSS_MARGIN_FREE_MARGIN_DETAILS_AVAILEQ"
AVAIL_EQ_STATUS_NOT_OBSERVED = "NOT_OBSERVED"
AVAIL_EQ_STATUS_OBSERVED = "OBSERVED"
EMPTY_DATA_IS_NOT_ZERO = True
ABSENT_OR_NOT_RETURNED_IS_NOT_ZERO = True
USD_USDC_EQUIVALENCE_ASSUMED = False
ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY = True
AVAIL_BAL_IS_NOT_AUTHORITY = True
MAX_AVAILABLE_IS_NOT_AVAILABLE_MARGIN = True
MAX_SIZE_IS_NOT_AVAILABLE_MARGIN = True
POS_MODE_IS_NOT_AVAILABLE_MARGIN = True
MARGIN_MODE_IS_NOT_NUMERIC_AVAILABLE_MARGIN = True
LEVERAGE_IS_NOT_AVAILABLE_MARGIN_AUTHORITY = True
ACCOUNT_MODE = "UNPROVEN"
ACCOUNT_MODE_PROOF_STATUS = "UNPROVEN"
OBSERVATION_CLASS_SUCCESS_NUMERIC = "SUCCESS_NUMERIC"
OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED = "SUCCESS_NOT_OBSERVED"
OBSERVATION_CLASS_VENUE_ERROR = "VENUE_ERROR"
OBSERVATION_CLASS_AUTH_ERROR = "AUTH_ERROR"
OBSERVATION_CLASS_NETWORK_ERROR = "NETWORK_ERROR"
OBSERVATION_CLASS_MALFORMED = "MALFORMED"
OBSERVATION_CLASS_NOT_PERFORMED = "NOT_PERFORMED"
HISTORICAL_BTC_PACK = "section_11_13_5_post_k_cross_imr_leverage_get_bind_v1"
HISTORICAL_BTC_INSTRUMENT_ID = HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID
MAX_RAW_DIGIT_LEN = 64
_SCIENTIFIC_NOTATION = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")
FORBIDDEN_SOURCE_MARKERS = (
    "max-avail-size",
    "account/max-size",
    "set-isolated-mode",
    "set-leverage",
    "set-position-mode",
    "leverage-info",
    "account/config",
    "account/positions",
    "public/instruments",
    "public/price-limit",
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
OWNER_GO_THIS_SLICE = "PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"


class LiveCanaryAvailableMarginObservationError(RuntimeError):
    """Fail-closed fresh AVAILABLE_MARGIN observation violation."""


@dataclass(frozen=True)
class FreshAvailableMarginObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    consumer_instrument_id: str
    planned_td_mode: str
    required_ccy: str
    instrument_settle_ccy: str
    selected_ccy: str
    avail_eq_raw: str
    avail_eq_status: str
    account_avail_eq_raw: str
    selected_avail_bal_raw: str
    venue_u_time_raw: str
    detail_u_time_raw: str
    detail_row_count: int
    other_detail_ccys: tuple[str, ...]
    venue_scope: str
    consumer_scope: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    available_margin_domain: str
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
            "consumer_instrument_id": self.consumer_instrument_id,
            "planned_td_mode": self.planned_td_mode,
            "required_ccy": self.required_ccy,
            "instrument_settle_ccy": self.instrument_settle_ccy,
            "selected_ccy": self.selected_ccy,
            "avail_eq_raw": self.avail_eq_raw,
            "avail_eq_status": self.avail_eq_status,
            "account_avail_eq_raw": self.account_avail_eq_raw,
            "selected_avail_bal_raw": self.selected_avail_bal_raw,
            "venue_u_time_raw": self.venue_u_time_raw,
            "detail_u_time_raw": self.detail_u_time_raw,
            "detail_row_count": self.detail_row_count,
            "other_detail_ccys": list(self.other_detail_ccys),
            "venue_scope": self.venue_scope,
            "consumer_scope": self.consumer_scope,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "available_margin_domain": self.available_margin_domain,
            "historical_reuse": self.historical_reuse,
            "body_sha256": self.body_sha256,
            "EMPTY_DATA_IS_NOT_ZERO": EMPTY_DATA_IS_NOT_ZERO,
            "USD_USDC_EQUIVALENCE_ASSUMED": USD_USDC_EQUIVALENCE_ASSUMED,
            "ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY": ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY,
            "AVAIL_BAL_IS_NOT_AUTHORITY": AVAIL_BAL_IS_NOT_AUTHORITY,
        }


@dataclass(frozen=True)
class ValidatedFreshAvailableMarginObservationV1:
    raw: FreshAvailableMarginObservationV1
    selected_ccy: str
    avail_eq: Decimal
    avail_eq_raw: str
    comparison_domain: str
    semantic_class: str
    unit: str
    venue_scope: str
    consumer_scope: str
    planned_td_mode: str


def account_balance_query_path_v1() -> str:
    return AVAILABLE_MARGIN_ENDPOINT_PATH


def classify_available_margin_observation_class_v1(
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
    if observation_class in {
        OBSERVATION_CLASS_SUCCESS_NUMERIC,
        OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED,
    }:
        return
    mapping = {
        OBSERVATION_CLASS_NOT_PERFORMED: "FRESH_GET_NOT_PERFORMED",
        OBSERVATION_CLASS_AUTH_ERROR: "AVAILABLE_MARGIN_AUTH_ERROR",
        OBSERVATION_CLASS_NETWORK_ERROR: "AVAILABLE_MARGIN_NETWORK_ERROR",
        OBSERVATION_CLASS_VENUE_ERROR: "AVAILABLE_MARGIN_VENUE_CODE_UNSUCCESSFUL",
        OBSERVATION_CLASS_MALFORMED: "AVAILABLE_MARGIN_MALFORMED",
    }
    raise LiveCanaryAvailableMarginObservationError(
        mapping.get(observation_class, f"AVAILABLE_MARGIN_FAIL_CLOSED:{observation_class}")
    )


def _reject_historical_reuse(
    *,
    pretrade_decision_id: str,
    endpoint: str,
    historical_reuse: bool,
    instrument_id: str,
) -> None:
    if historical_reuse:
        raise LiveCanaryAvailableMarginObservationError(
            "HISTORICAL_AVAILABLE_MARGIN_REUSE_FORBIDDEN"
        )
    decision = str(pretrade_decision_id or "").strip()
    ep = str(endpoint or "")
    if HISTORICAL_BTC_PACK in decision or HISTORICAL_BTC_PACK in ep:
        raise LiveCanaryAvailableMarginObservationError(
            "HISTORICAL_BTC_AVAILABLE_MARGIN_PACK_REUSE_FORBIDDEN"
        )
    if HISTORICAL_BTC_INSTRUMENT_ID in ep or instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryAvailableMarginObservationError("HISTORICAL_BTC_INSTRUMENT_FORBIDDEN")
    if HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID in ep or "-SWAP" in instrument_id:
        raise LiveCanaryAvailableMarginObservationError(
            "SWAP_AVAILABLE_MARGIN_SUBSTITUTION_FORBIDDEN"
        )
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in ep:
            raise LiveCanaryAvailableMarginObservationError(
                f"AVAILABLE_MARGIN_RECONSTRUCTION_SOURCE_FORBIDDEN:{marker}"
            )


def _query_pairs(endpoint: str) -> dict[str, str]:
    query = str(endpoint or "").split("?", 1)
    if len(query) != 2:
        return {}
    return {str(k): str(v) for k, v in parse_qsl(query[1], keep_blank_values=True)}


def _require_non_negative_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise LiveCanaryAvailableMarginObservationError(f"AVAILABLE_MARGIN_FIELD_NULL:{field}")
    text = str(raw).strip()
    if not text:
        raise LiveCanaryAvailableMarginObservationError(f"AVAILABLE_MARGIN_FIELD_EMPTY:{field}")
    lowered = text.lower()
    if lowered in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_FIELD_NON_NUMERIC:{field}"
        )
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_FIELD_OUT_OF_DOMAIN:{field}"
        )
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_FIELD_NON_NUMERIC:{field}"
        ) from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_FIELD_NON_NUMERIC:{field}"
        )
    if value < 0:
        raise LiveCanaryAvailableMarginObservationError(f"AVAILABLE_MARGIN_FIELD_NEGATIVE:{field}")
    return value


def _account_row(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_VENUE_CODE_UNSUCCESSFUL:{payload.get('code')}"
        )
    data = payload.get("data")
    if not isinstance(data, list):
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_DATA_MISSING")
    if not data:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_DATA_EMPTY")
    if len(data) != 1:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_AMBIGUOUS_ACCOUNT_ROW")
    row = data[0]
    if not isinstance(row, Mapping):
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_ACCOUNT_ROW_MALFORMED")
    return row


def _select_usdc_detail(
    account_row: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, int, tuple[str, ...]]:
    details = account_row.get("details")
    if details is None:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_DETAILS_MISSING")
    if not isinstance(details, list):
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_DETAILS_MALFORMED")
    rows = [item for item in details if isinstance(item, Mapping)]
    if len(rows) != len(details):
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_DETAILS_ROW_MALFORMED")
    matches: list[Mapping[str, Any]] = []
    other: list[str] = []
    for item in rows:
        ccy = str(item.get("ccy") or "").strip()
        if not ccy:
            raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_DETAIL_CCY_MISSING")
        if ccy == AVAILABLE_MARGIN_REQUIRED_CCY:
            matches.append(item)
        else:
            other.append(ccy)
    if len(matches) > 1:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_USDC_ROW_AMBIGUOUS")
    selected = matches[0] if matches else None
    return selected, len(rows), tuple(other)


def acquire_fresh_available_margin_observation_from_payload_v1(
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
) -> FreshAvailableMarginObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryAvailableMarginObservationError("PRETRADE_DECISION_ID_REQUIRED")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
        instrument_id=instrument_id,
    )
    planned = require_canonical_execution_td_mode_v1(planned_td_mode)
    if not auth_header_sent:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_AUTH_HEADER_REQUIRED")
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryAvailableMarginObservationError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    path = str(endpoint or "").split("?", 1)[0]
    if path != AVAILABLE_MARGIN_ENDPOINT_PATH:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_ENDPOINT_MISMATCH:{endpoint}"
        )
    query = _query_pairs(endpoint)
    if query:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_QUERY_FORBIDDEN")
    observation_class = classify_available_margin_observation_class_v1(
        get_performed=get_performed,
        http_status=http_status,
        payload=payload,
    )
    _raise_for_observation_class(observation_class)
    account_row = _account_row(payload)
    selected, detail_count, other_ccys = _select_usdc_detail(account_row)
    if AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY in other_ccys:
        if AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY == AVAILABLE_MARGIN_REQUIRED_CCY:
            raise LiveCanaryAvailableMarginObservationError("USD_USDC_EQUIVALENCE_ASSUMED")
    account_avail_eq_raw = (
        "" if account_row.get("availEq") is None else str(account_row.get("availEq"))
    )
    venue_u_time_raw = "" if account_row.get("uTime") is None else str(account_row.get("uTime"))
    if selected is None:
        status = AVAIL_EQ_STATUS_NOT_OBSERVED
        selected_ccy = ""
        avail_eq_raw = ""
        selected_avail_bal_raw = ""
        detail_u_time_raw = ""
    else:
        selected_ccy = str(selected.get("ccy") or "").strip()
        if selected_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
            raise LiveCanaryAvailableMarginObservationError(
                f"AVAILABLE_MARGIN_CCY_MISMATCH:{selected_ccy}"
            )
        if selected_ccy == AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY:
            raise LiveCanaryAvailableMarginObservationError("USD_USDC_EQUIVALENCE_ASSUMED")
        if "availEq" not in selected:
            raise LiveCanaryAvailableMarginObservationError(
                "AVAILABLE_MARGIN_FIELD_MISSING:details.availEq"
            )
        avail_eq_raw = "" if selected.get("availEq") is None else str(selected.get("availEq"))
        if not str(avail_eq_raw).strip():
            raise LiveCanaryAvailableMarginObservationError(
                "AVAILABLE_MARGIN_FIELD_EMPTY:details.availEq"
            )
        _require_non_negative_decimal(avail_eq_raw, field="details.availEq")
        status = AVAIL_EQ_STATUS_OBSERVED
        selected_avail_bal_raw = (
            "" if selected.get("availBal") is None else str(selected.get("availBal"))
        )
        detail_u_time_raw = "" if selected.get("uTime") is None else str(selected.get("uTime"))
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshAvailableMarginObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        consumer_instrument_id=instrument_id,
        planned_td_mode=planned,
        required_ccy=AVAILABLE_MARGIN_REQUIRED_CCY,
        instrument_settle_ccy=AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY,
        selected_ccy=selected_ccy,
        avail_eq_raw=avail_eq_raw,
        avail_eq_status=status,
        account_avail_eq_raw=account_avail_eq_raw,
        selected_avail_bal_raw=selected_avail_bal_raw,
        venue_u_time_raw=venue_u_time_raw,
        detail_u_time_raw=detail_u_time_raw,
        detail_row_count=int(detail_count),
        other_detail_ccys=other_ccys,
        venue_scope=AVAILABLE_MARGIN_VENUE_SCOPE,
        consumer_scope=AVAILABLE_MARGIN_CONSUMER_SCOPE,
        http_status=int(http_status),
        venue_code=str(payload.get("code") or ""),
        get_performed=True,
        auth_header_sent=True,
        available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
        historical_reuse=False,
        body_sha256=digest,
    )


def validate_fresh_available_margin_observation_v1(
    observation: FreshAvailableMarginObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    available_margin_domain: str,
    planned_td_mode: str,
) -> ValidatedFreshAvailableMarginObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryAvailableMarginObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.consumer_instrument_id != instrument_id:
        raise LiveCanaryAvailableMarginObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if observation.available_margin_domain != available_margin_domain:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE:{available_margin_domain}"
        )
    if available_margin_domain != AVAILABLE_MARGIN_OUTPUT_DOMAIN:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE:{available_margin_domain}"
        )
    planned = require_canonical_execution_td_mode_v1(planned_td_mode)
    if observation.planned_td_mode != planned:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_TDMODE_MISMATCH")
    if observation.required_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_REQUIRED_CCY_DRIFT")
    if observation.instrument_settle_ccy != AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY:
        raise LiveCanaryAvailableMarginObservationError("AVAILABLE_MARGIN_SETTLE_CCY_DRIFT")
    if observation.avail_eq_status != AVAIL_EQ_STATUS_OBSERVED:
        raise LiveCanaryAvailableMarginObservationError(
            "AVAILABLE_MARGIN_USDC_AVAILEQ_NOT_OBSERVED"
        )
    if observation.selected_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_CCY_MISMATCH:{observation.selected_ccy}"
        )
    if observation.selected_ccy == AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY:
        raise LiveCanaryAvailableMarginObservationError("USD_USDC_EQUIVALENCE_ASSUMED")
    avail_eq = _require_non_negative_decimal(observation.avail_eq_raw, field="details.availEq")
    return ValidatedFreshAvailableMarginObservationV1(
        raw=observation,
        selected_ccy=observation.selected_ccy,
        avail_eq=avail_eq,
        avail_eq_raw=observation.avail_eq_raw,
        comparison_domain=AVAILABLE_MARGIN_COMPARISON_DOMAIN,
        semantic_class=AVAILABLE_MARGIN_SEMANTIC_CLASS,
        unit=AVAILABLE_MARGIN_UNIT,
        venue_scope=observation.venue_scope,
        consumer_scope=observation.consumer_scope,
        planned_td_mode=observation.planned_td_mode,
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


def persist_authorized_fresh_available_margin_observation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    evidence_root: Path,
    vault_file: Path | str,
    planned_td_mode: str = AVAILABLE_MARGIN_REQUIRED_TD_MODE,
) -> dict[str, Any]:
    """Perform one authenticated unfiltered balance GET and persist forensic evidence.

    No POST. No trading. Empty details are not zero. The pack is not an
    operative cache.
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
        raise LiveCanaryAvailableMarginObservationError("OWNER_GO_MISMATCH")
    planned = require_canonical_execution_td_mode_v1(planned_td_mode)
    endpoint = account_balance_query_path_v1()
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
            raise LiveCanaryAvailableMarginObservationError(
                f"SIGNED_REQUEST_TARGET_MISMATCH:{signed_target}"
            )
        auth_headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
        auth_headers["User-Agent"] = USER_AGENT_CANARY
        response = client.get(endpoint=endpoint, headers=auth_headers)
    except LiveCanaryHttpError as exc:
        raise LiveCanaryAvailableMarginObservationError(
            f"AVAILABLE_MARGIN_FRESH_GET_FAILED:{exc}"
        ) from exc
    finally:
        auth_headers.clear()
        release_live_canary_ephemeral_material_v1(handle)
    response_time = utc_now_iso_v1()
    payload = parse_json_object_v1(response.body_bytes)
    observation_class = classify_available_margin_observation_class_v1(
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
        "AVAILABLE_MARGIN_RESPONSE_FIELD": AVAILABLE_MARGIN_RESPONSE_FIELD,
        "AVAILABLE_MARGIN_ACCOUNT_LEVEL_FIELD": AVAILABLE_MARGIN_ACCOUNT_LEVEL_FIELD,
        "AVAILABLE_MARGIN_REQUIRED_CCY": AVAILABLE_MARGIN_REQUIRED_CCY,
        "AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY": AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY,
        "VENUE_SCOPE": AVAILABLE_MARGIN_VENUE_SCOPE,
        "CONSUMER_SCOPE": AVAILABLE_MARGIN_CONSUMER_SCOPE,
        "EMPTY_DATA_IS_NOT_ZERO": EMPTY_DATA_IS_NOT_ZERO,
        "USD_USDC_EQUIVALENCE_ASSUMED": USD_USDC_EQUIVALENCE_ASSUMED,
        "raw_rows": raw_rows,
    }
    common_fail = {
        "DOCUMENT_CLASS": "AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "USD_USDC_EQUIVALENCE_ASSUMED": False,
        "MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "raw_fields": raw_fields,
        "payload": payload,
    }
    if observation_class not in {
        OBSERVATION_CLASS_SUCCESS_NUMERIC,
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
        observation = acquire_fresh_available_margin_observation_from_payload_v1(
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
        if observation.avail_eq_status == AVAIL_EQ_STATUS_NOT_OBSERVED:
            observation_class = OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED
            validated = None
        else:
            validated = validate_fresh_available_margin_observation_v1(
                observation,
                pretrade_decision_id=pretrade_decision_id,
                instrument_id=DEFAULT_INSTRUMENT_ID,
                available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
                planned_td_mode=planned,
            )
            observation_class = OBSERVATION_CLASS_SUCCESS_NUMERIC
    except LiveCanaryAvailableMarginObservationError as exc:
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
        "AUTH_CLASS": AVAILABLE_MARGIN_AUTH_CLASS,
        "COOKIE_HEADER_SENT": False,
        "DOCUMENT_CLASS": "AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "AVAILABLE_MARGIN_VENUE_SCOPE": AVAILABLE_MARGIN_VENUE_SCOPE,
        "AVAILABLE_MARGIN_CONSUMER_SCOPE": AVAILABLE_MARGIN_CONSUMER_SCOPE,
        "AVAILABLE_MARGIN_REQUEST_GRAMMAR": AVAILABLE_MARGIN_REQUEST_GRAMMAR,
        "AVAILABLE_MARGIN_RESPONSE_FIELD": AVAILABLE_MARGIN_RESPONSE_FIELD,
        "AVAILABLE_MARGIN_REQUIRED_CCY": AVAILABLE_MARGIN_REQUIRED_CCY,
        "AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY": AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY,
        "ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY": ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY,
        "AVAIL_BAL_IS_NOT_AUTHORITY": AVAIL_BAL_IS_NOT_AUTHORITY,
        "USD_USDC_EQUIVALENCE_ASSUMED": USD_USDC_EQUIVALENCE_ASSUMED,
        "ACCOUNT_MODE": ACCOUNT_MODE,
        "ACCOUNT_MODE_PROOF_STATUS": ACCOUNT_MODE_PROOF_STATUS,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "POS_MODE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "MARGIN_MODE_USED_AS_NUMERIC_AVAILABLE_MARGIN_AUTHORITY": False,
        "LEVERAGE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY": False,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "FRESHNESS_POLICY": AVAILABLE_MARGIN_FRESHNESS_POLICY,
        "TS_AGE_BOUND": AVAILABLE_MARGIN_TS_AGE_BOUND,
        "VENUE_U_TIME_FIELD": AVAILABLE_MARGIN_VENUE_U_TIME_FIELD,
        "observation": observation.to_dict(),
        "validated": None
        if validated is None
        else {
            "selected_ccy": validated.selected_ccy,
            "avail_eq_raw": validated.avail_eq_raw,
            "avail_eq": str(validated.avail_eq),
            "comparison_domain": validated.comparison_domain,
            "semantic_class": validated.semantic_class,
            "unit": validated.unit,
            "venue_scope": validated.venue_scope,
            "consumer_scope": validated.consumer_scope,
            "planned_td_mode": validated.planned_td_mode,
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
        "DOCUMENT_CLASS": "AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1",
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
        "SELECTED_CCY": observation.selected_ccy or "NOT_OBSERVED",
        "AVAIL_EQ_RAW": observation.avail_eq_raw or "NOT_OBSERVED",
        "AVAIL_EQ_STATUS": observation.avail_eq_status,
        "ACCOUNT_AVAIL_EQ_RAW": observation.account_avail_eq_raw,
        "DETAIL_ROW_COUNT": observation.detail_row_count,
        "PLANNED_TD_MODE": observation.planned_td_mode,
        "ok": True,
    }
    claims = {
        "FRESH_GET_PERFORMED": True,
        "HISTORICAL_REUSE_PATH_EXISTS": False,
        "NETWORK_POST_PERFORMED": False,
        "NETWORK_AUTHENTICATED_GET_PERFORMED": True,
        "ZERO_NORMALIZATION_PERFORMED": False,
        "USD_USDC_EQUIVALENCE_ASSUMED": False,
        "MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "POS_MODE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "MARGIN_MODE_USED_AS_NUMERIC_AVAILABLE_MARGIN_AUTHORITY": False,
        "LEVERAGE_USED_AS_AVAILABLE_MARGIN_AUTHORITY": False,
        "EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY": False,
        "TRADING_PERFORMED": False,
        "ACCOUNT_MODE_MUTATION_PERFORMED": False,
        "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE": False,
        "ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY": True,
        "AVAIL_BAL_IS_NOT_AUTHORITY": True,
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
        "selected_ccy": observation.selected_ccy,
        "avail_eq_raw": observation.avail_eq_raw,
        "avail_eq_status": observation.avail_eq_status,
        "planned_td_mode": observation.planned_td_mode,
        "semantic_class": AVAILABLE_MARGIN_SEMANTIC_CLASS
        if observation_class == OBSERVATION_CLASS_SUCCESS_NUMERIC
        else AVAIL_EQ_STATUS_NOT_OBSERVED,
        "venue_scope": observation.venue_scope,
        "consumer_scope": observation.consumer_scope,
    }

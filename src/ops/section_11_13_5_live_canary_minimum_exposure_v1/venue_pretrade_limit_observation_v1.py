"""Decision-bound venue-pretrade limit observation for §11.13.5.

Owner-adjudicated source is the same unsigned GET /api/v5/public/instruments
exact-row already used for MAX_SIZE and INSTRUMENT_STATE. Required LIMIT-entry
fields are minSz, lotSz, tickSz, and maxLmtSz. maxMktSz is observed as a
MARKET peer and is not a LIMIT substitute. ctVal/ctMult are unit context only.
No new GET. No POST. No TTL. No operative cache.
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
    DEFAULT_RULE_TYPE,
    REUSED_BINDING_REST_HOST,
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_UNIT,
)

VENUE_PRETRADE_LIMIT_ENDPOINT_PATH = "/api/v5/public/instruments"
VENUE_PRETRADE_LIMIT_OUTPUT_DOMAIN = "VENUE_PRETRADE_LIMITS"
VENUE_PRETRADE_LIMIT_SIZE_UNIT = "contracts"
VENUE_PRETRADE_LIMIT_PRICE_UNIT = "venue_price_increment"
VENUE_PRETRADE_LIMIT_FRESHNESS_POLICY = "FRESH_GET_PER_PRETRADE_DECISION"
VENUE_PRETRADE_LIMIT_TS_AGE_BOUND = "UNBOUND"
VENUE_PRETRADE_LIMIT_AUTH_CLASS = "PUBLIC_UNSIGNED_GET"
GET_VENUE_TS_STATUS = "ABSENT_NOT_IN_INSTRUMENTS_ROW"
MAX_RAW_DIGIT_LEN = 40
_SCIENTIFIC_NOTATION = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+")
HISTORICAL_BTC_INSTRUMENT_ID = "BTC-USD_UM_XPERP-310404"
HISTORICAL_Z2AR_MARKER = "GET_1_MAX_LMT_SZ"
COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE = (
    "evidence/ops/instrument_state_forensic_binding_and_closure_v1"
    "/20260830T044522Z/GET_SNAPSHOT.sanitized.json"
)
COMMITTED_BODY_SHA256 = "038f2bf82f18f2d42ed26dca281cc7733e4ef7d07206fd0b19637189ec3e4cd2"
COMMITTED_OBSERVED_AT_UTC = "2026-08-30T04:45:22.376551Z"
COMMITTED_MIN_SZ_RAW = "1"
COMMITTED_LOT_SZ_RAW = "1"
COMMITTED_TICK_SZ_RAW = "0.0001"
COMMITTED_MAX_LMT_SZ_RAW = "100000000"
COMMITTED_MAX_MKT_SZ_RAW = "100000"
COMMITTED_CT_VAL_RAW = "1"
COMMITTED_CT_MULT_RAW = "1"
COMMITTED_CT_VAL_CCY_RAW = "SUI"


class LiveCanaryVenuePretradeLimitObservationError(RuntimeError):
    """Fail-closed venue-pretrade limit observation violation."""


@dataclass(frozen=True)
class FreshVenuePretradeLimitObservationV1:
    pretrade_decision_id: str
    observed_at_utc: str
    venue: str
    rest_host: str
    method: str
    endpoint: str
    instrument_id: str
    inst_type_raw: str
    rule_type_raw: str
    min_sz_raw: str
    lot_sz_raw: str
    tick_sz_raw: str
    max_lmt_sz_raw: str
    max_mkt_sz_raw: str | None
    ct_val_raw: str
    ct_mult_raw: str
    ct_val_ccy_raw: str
    http_status: int
    venue_code: str
    get_performed: bool
    auth_header_sent: bool
    quantity_domain: str
    size_unit: str
    price_unit: str
    historical_reuse: bool
    target_row_count: int
    body_sha256: str
    source_evidence: str

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
            "rule_type_raw": self.rule_type_raw,
            "min_sz_raw": self.min_sz_raw,
            "lot_sz_raw": self.lot_sz_raw,
            "tick_sz_raw": self.tick_sz_raw,
            "max_lmt_sz_raw": self.max_lmt_sz_raw,
            "max_mkt_sz_raw": self.max_mkt_sz_raw,
            "ct_val_raw": self.ct_val_raw,
            "ct_mult_raw": self.ct_mult_raw,
            "ct_val_ccy_raw": self.ct_val_ccy_raw,
            "http_status": self.http_status,
            "venue_code": self.venue_code,
            "get_performed": self.get_performed,
            "auth_header_sent": self.auth_header_sent,
            "quantity_domain": self.quantity_domain,
            "size_unit": self.size_unit,
            "price_unit": self.price_unit,
            "historical_reuse": self.historical_reuse,
            "target_row_count": self.target_row_count,
            "body_sha256": self.body_sha256,
            "source_evidence": self.source_evidence,
        }


@dataclass(frozen=True)
class ValidatedFreshVenuePretradeLimitObservationV1:
    raw: FreshVenuePretradeLimitObservationV1
    min_sz: Decimal
    lot_sz: Decimal
    tick_sz: Decimal
    max_lmt_sz: Decimal
    ct_val: Decimal
    ct_mult: Decimal | None
    comparison_domain: str
    conversion_performed: bool


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _reject_historical_reuse(
    *, pretrade_decision_id: str, endpoint: str, historical_reuse: bool
) -> None:
    if historical_reuse:
        raise LiveCanaryVenuePretradeLimitObservationError(
            "HISTORICAL_VENUE_PRETRADE_LIMIT_REUSE_FORBIDDEN"
        )
    if HISTORICAL_Z2AR_MARKER in str(pretrade_decision_id or ""):
        raise LiveCanaryVenuePretradeLimitObservationError("HISTORICAL_Z2AR_LIMIT_REUSE_FORBIDDEN")
    if "z2bd" in str(endpoint or "").lower() or "z2bf" in str(endpoint or "").lower():
        raise LiveCanaryVenuePretradeLimitObservationError(
            "HISTORICAL_Z2BD_Z2BF_PACK_REUSE_FORBIDDEN"
        )


def _require_public_instruments_endpoint(endpoint: str) -> None:
    text = str(endpoint or "").strip()
    expected = public_instruments_query_path_v1()
    if text != expected:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_ENDPOINT_FORBIDDEN:{text or 'EMPTY'}"
        )


def _require_raw_string_field(row: Mapping[str, Any], *, field: str) -> str:
    if field not in row:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_MISSING:{field}"
        )
    value = row.get(field)
    if value is None:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_NULL:{field}"
        )
    if not isinstance(value, str):
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_WRONG_TYPE:{field}"
        )
    if value == "":
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_EMPTY:{field}"
        )
    if value.strip() == "":
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_EMPTY:{field}"
        )
    if value != value.strip():
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_UNSTRIPPED:{field}"
        )
    return value


def _require_positive_decimal(raw: str, *, field: str) -> Decimal:
    text = str(raw)
    if text.lower() in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_NON_FINITE:{field}"
        )
    if _SCIENTIFIC_NOTATION.fullmatch(text) or len(text) > MAX_RAW_DIGIT_LEN:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_OUT_OF_DOMAIN:{field}"
        )
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_NON_NUMERIC:{field}"
        ) from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_NON_FINITE:{field}"
        )
    if value < 0:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_NEGATIVE:{field}"
        )
    if value == 0:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_FIELD_ZERO_FORBIDDEN:{field}"
        )
    return value


def _exact_target_rows(
    *,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(instruments_payload, Mapping):
        raise LiveCanaryVenuePretradeLimitObservationError("INSTRUMENTS_PAYLOAD_NOT_OBJECT")
    data = instruments_payload.get("data")
    if not isinstance(data, list):
        raise LiveCanaryVenuePretradeLimitObservationError("INSTRUMENTS_DATA_MISSING")
    matches: list[Mapping[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            matches.append(item)
    return matches


def acquire_fresh_venue_pretrade_limit_observation_from_payload_v1(
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
    source_evidence: str = "",
) -> FreshVenuePretradeLimitObservationV1:
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise LiveCanaryVenuePretradeLimitObservationError("PRETRADE_DECISION_ID_REQUIRED")
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryVenuePretradeLimitObservationError(str(exc)) from exc
    if instrument_id == HISTORICAL_BTC_INSTRUMENT_ID:
        raise LiveCanaryVenuePretradeLimitObservationError("HISTORICAL_BTC_INSTRUMENT")
    _reject_historical_reuse(
        pretrade_decision_id=decision,
        endpoint=endpoint,
        historical_reuse=historical_reuse,
    )
    if not get_performed:
        raise LiveCanaryVenuePretradeLimitObservationError("FRESH_GET_NOT_PERFORMED")
    if int(http_status) != 200:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"FRESH_GET_HTTP_UNSUCCESSFUL:{http_status}"
        )
    if auth_header_sent:
        raise LiveCanaryVenuePretradeLimitObservationError(
            "PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN"
        )
    if str(rest_host or "") != REUSED_BINDING_REST_HOST:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}"
        )
    _require_public_instruments_endpoint(endpoint)
    venue_code = str(instruments_payload.get("code") or "")
    if venue_code != "0":
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_VENUE_CODE_UNSUCCESSFUL:{venue_code or 'EMPTY'}"
        )
    matches = _exact_target_rows(
        instruments_payload=instruments_payload, instrument_id=instrument_id
    )
    if not matches:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_NOT_OBSERVED:{instrument_id}"
        )
    if len(matches) > 1:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_DUPLICATE_TARGET_ROWS:{len(matches)}"
        )
    row = matches[0]
    min_sz_raw = _require_raw_string_field(row, field="minSz")
    lot_sz_raw = _require_raw_string_field(row, field="lotSz")
    tick_sz_raw = _require_raw_string_field(row, field="tickSz")
    max_lmt_sz_raw = _require_raw_string_field(row, field="maxLmtSz")
    ct_val_raw = _require_raw_string_field(row, field="ctVal")
    if "ctMult" not in row:
        ct_mult_raw = ""
    else:
        ct_mult_raw = _require_raw_string_field(row, field="ctMult")
    ct_val_ccy_raw = ""
    if "ctValCcy" in row and row.get("ctValCcy") is not None:
        if not isinstance(row.get("ctValCcy"), str):
            raise LiveCanaryVenuePretradeLimitObservationError(
                "VENUE_PRETRADE_LIMIT_FIELD_WRONG_TYPE:ctValCcy"
            )
        ct_val_ccy_raw = str(row.get("ctValCcy") or "")
    max_mkt_sz_raw: str | None
    if "maxMktSz" not in row:
        max_mkt_sz_raw = None
    elif row.get("maxMktSz") is None:
        raise LiveCanaryVenuePretradeLimitObservationError(
            "VENUE_PRETRADE_LIMIT_FIELD_NULL:maxMktSz"
        )
    elif not isinstance(row.get("maxMktSz"), str):
        raise LiveCanaryVenuePretradeLimitObservationError(
            "VENUE_PRETRADE_LIMIT_FIELD_WRONG_TYPE:maxMktSz"
        )
    else:
        max_mkt_sz_raw = str(row.get("maxMktSz"))
        if max_mkt_sz_raw == "":
            raise LiveCanaryVenuePretradeLimitObservationError(
                "VENUE_PRETRADE_LIMIT_FIELD_EMPTY:maxMktSz"
            )
    digest = str(body_sha256 or "").strip()
    if not digest:
        encoded = json.dumps(instruments_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        digest = hashlib.sha256(encoded).hexdigest()
    return FreshVenuePretradeLimitObservationV1(
        pretrade_decision_id=decision,
        observed_at_utc=str(observed_at_utc or "").strip() or utc_now_iso_v1(),
        venue="OKX_EEA",
        rest_host=REUSED_BINDING_REST_HOST,
        method="GET",
        endpoint=str(endpoint or "").strip(),
        instrument_id=instrument_id,
        inst_type_raw=str(row.get("instType") or "").strip(),
        rule_type_raw=str(row.get("ruleType") or "").strip(),
        min_sz_raw=min_sz_raw,
        lot_sz_raw=lot_sz_raw,
        tick_sz_raw=tick_sz_raw,
        max_lmt_sz_raw=max_lmt_sz_raw,
        max_mkt_sz_raw=max_mkt_sz_raw,
        ct_val_raw=ct_val_raw,
        ct_mult_raw=ct_mult_raw,
        ct_val_ccy_raw=ct_val_ccy_raw,
        http_status=int(http_status),
        venue_code=venue_code,
        get_performed=True,
        auth_header_sent=False,
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        size_unit=VENUE_PRETRADE_LIMIT_SIZE_UNIT,
        price_unit=VENUE_PRETRADE_LIMIT_PRICE_UNIT,
        historical_reuse=False,
        target_row_count=1,
        body_sha256=digest,
        source_evidence=str(source_evidence or ""),
    )


def validate_fresh_venue_pretrade_limit_observation_v1(
    observation: FreshVenuePretradeLimitObservationV1,
    *,
    pretrade_decision_id: str,
    instrument_id: str,
    quantity_domain: str,
) -> ValidatedFreshVenuePretradeLimitObservationV1:
    if observation.pretrade_decision_id != str(pretrade_decision_id).strip():
        raise LiveCanaryVenuePretradeLimitObservationError("OBSERVATION_DECISION_ID_MISMATCH")
    if observation.instrument_id != instrument_id:
        raise LiveCanaryVenuePretradeLimitObservationError("OBSERVATION_INSTRUMENT_MISMATCH")
    if str(quantity_domain) != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryVenuePretradeLimitObservationError("QUANTITY_DOMAIN_INCOMPATIBLE")
    if observation.quantity_domain != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryVenuePretradeLimitObservationError("OBSERVATION_DOMAIN_INCOMPATIBLE")
    if observation.size_unit != VENUE_PRETRADE_LIMIT_SIZE_UNIT:
        raise LiveCanaryVenuePretradeLimitObservationError("SIZE_UNIT_INCOMPATIBLE")
    if observation.size_unit != ORDER_PLAN_QTY_UNIT:
        raise LiveCanaryVenuePretradeLimitObservationError("SIZE_UNIT_NOT_CONTRACTS")
    if observation.price_unit != VENUE_PRETRADE_LIMIT_PRICE_UNIT:
        raise LiveCanaryVenuePretradeLimitObservationError("PRICE_UNIT_INCOMPATIBLE")
    row_type = str(observation.inst_type_raw or "").strip().upper()
    if row_type and row_type != DEFAULT_INST_TYPE:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_GEOMETRY_INST_TYPE_MISMATCH:{row_type}"
        )
    rule = str(observation.rule_type_raw or "").strip()
    if rule and rule != DEFAULT_RULE_TYPE:
        raise LiveCanaryVenuePretradeLimitObservationError(
            f"VENUE_PRETRADE_LIMIT_GEOMETRY_RULE_TYPE_MISMATCH:{rule}"
        )
    min_sz = _require_positive_decimal(observation.min_sz_raw, field="minSz")
    lot_sz = _require_positive_decimal(observation.lot_sz_raw, field="lotSz")
    tick_sz = _require_positive_decimal(observation.tick_sz_raw, field="tickSz")
    max_lmt_sz = _require_positive_decimal(observation.max_lmt_sz_raw, field="maxLmtSz")
    ct_val = _require_positive_decimal(observation.ct_val_raw, field="ctVal")
    ct_mult: Decimal | None
    if observation.ct_mult_raw == "":
        ct_mult = None
    else:
        ct_mult = _require_positive_decimal(observation.ct_mult_raw, field="ctMult")
    if min_sz != min_sz.to_integral_value():
        raise LiveCanaryVenuePretradeLimitObservationError("INTEGER_CONTRACT_REQUIRED:minSz")
    if lot_sz != lot_sz.to_integral_value():
        raise LiveCanaryVenuePretradeLimitObservationError("INTEGER_CONTRACT_REQUIRED:lotSz")
    if max_lmt_sz != max_lmt_sz.to_integral_value():
        raise LiveCanaryVenuePretradeLimitObservationError("INTEGER_CONTRACT_REQUIRED:maxLmtSz")
    if min_sz > max_lmt_sz:
        raise LiveCanaryVenuePretradeLimitObservationError("VENUE_PRETRADE_LIMIT_MIN_MAX_INVERSION")
    if observation.max_mkt_sz_raw is not None:
        _require_positive_decimal(observation.max_mkt_sz_raw, field="maxMktSz")
    return ValidatedFreshVenuePretradeLimitObservationV1(
        raw=observation,
        min_sz=min_sz,
        lot_sz=lot_sz,
        tick_sz=tick_sz,
        max_lmt_sz=max_lmt_sz,
        ct_val=ct_val,
        ct_mult=ct_mult,
        comparison_domain=ORDER_PLAN_QTY_DOMAIN,
        conversion_performed=False,
    )


def bind_venue_pretrade_limits_from_committed_instrument_state_pack_v1(
    *,
    repo_root: Path,
    pretrade_decision_id: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> ValidatedFreshVenuePretradeLimitObservationV1:
    """Bind LIMIT gates from the committed PR #6160 instruments pack. No network."""
    snapshot_path = repo_root / COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE
    if not snapshot_path.is_file():
        raise LiveCanaryVenuePretradeLimitObservationError(
            "COMMITTED_INSTRUMENT_STATE_PACK_MISSING"
        )
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, Mapping):
        raise LiveCanaryVenuePretradeLimitObservationError(
            "COMMITTED_INSTRUMENT_STATE_PACK_MALFORMED"
        )
    payload = snapshot.get("payload")
    if not isinstance(payload, Mapping):
        raise LiveCanaryVenuePretradeLimitObservationError(
            "COMMITTED_INSTRUMENT_STATE_PAYLOAD_MISSING"
        )
    http_evidence = snapshot.get("http_evidence")
    body_sha256 = ""
    if isinstance(http_evidence, Mapping):
        body_sha256 = str(http_evidence.get("body_sha256") or "")
    if body_sha256 != COMMITTED_BODY_SHA256:
        raise LiveCanaryVenuePretradeLimitObservationError(
            "COMMITTED_INSTRUMENT_STATE_BODY_SHA256_MISMATCH"
        )
    host = str(snapshot.get("HOST") or REUSED_BINDING_REST_HOST)
    endpoint = str(snapshot.get("ENDPOINT") or public_instruments_query_path_v1())
    observed_at = str(snapshot.get("response_event_time") or COMMITTED_OBSERVED_AT_UTC)
    observation = acquire_fresh_venue_pretrade_limit_observation_from_payload_v1(
        pretrade_decision_id=pretrade_decision_id,
        instruments_payload=payload,
        instrument_id=instrument_id,
        observed_at_utc=observed_at,
        endpoint=endpoint,
        http_status=200,
        get_performed=True,
        rest_host=host,
        auth_header_sent=False,
        historical_reuse=False,
        body_sha256=body_sha256,
        source_evidence=COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE,
    )
    return validate_fresh_venue_pretrade_limit_observation_v1(
        observation,
        pretrade_decision_id=pretrade_decision_id,
        instrument_id=instrument_id,
        quantity_domain=ORDER_PLAN_QTY_DOMAIN,
    )

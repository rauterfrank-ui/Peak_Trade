"""Productive venue-pretrade LIMIT gates for §11.13.5 order-plan.

Validates a proposed LIMIT order against venue-native minSz, lotSz, tickSz,
and maxLmtSz. Does not clamp, round, or rewrite the proposal. MARKET maxMktSz
is not a LIMIT substitute. Iceberg/TWAP/trigger/stop caps are out of scope for
canary LIMIT entry. Internal order-count and position-count caps are not venue
limits. No network I/O. No trading I/O.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ORDER_PLAN_QTY_DOMAIN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_pretrade_limit_observation_v1 import (
    COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE,
    GET_VENUE_TS_STATUS,
    VENUE_PRETRADE_LIMIT_AUTH_CLASS,
    VENUE_PRETRADE_LIMIT_FRESHNESS_POLICY,
    VENUE_PRETRADE_LIMIT_OUTPUT_DOMAIN,
    VENUE_PRETRADE_LIMIT_PRICE_UNIT,
    VENUE_PRETRADE_LIMIT_SIZE_UNIT,
    VENUE_PRETRADE_LIMIT_TS_AGE_BOUND,
    LiveCanaryVenuePretradeLimitObservationError,
    acquire_fresh_venue_pretrade_limit_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_venue_pretrade_limit_observation_v1,
)

VENUE_PRETRADE_LIMIT_GATES_CONSUMER_BOUND = True
VENUE_PRETRADE_LIMIT_GATES_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
REQUIRED_GATE_COUNT = 4
REQUIRED_GATES = ("MIN_SIZE", "LOT_SIZE", "TICK_SIZE", "MAX_LIMIT_SIZE")
CANARY_ENTRY_ORDER_TYPE = "LIMIT"
MAX_MKT_SZ_IS_NOT_LIMIT_MAX = True
MAX_ICEBERG_SZ_IS_NOT_LIMIT_MAX = True
MAX_TWAP_SZ_IS_NOT_LIMIT_MAX = True
MAX_TRIGGER_SZ_IS_NOT_LIMIT_MAX = True
MAX_STOP_SZ_IS_NOT_LIMIT_MAX = True
MAX_LMT_AMT_IS_NOT_MAX_LMT_SZ = True
INTERNAL_ORDER_COUNT_LIMIT_IS_NOT_VENUE_LIMIT = True
AVAILABLE_MARGIN_IS_NOT_VENUE_PRETRADE_LIMIT = True
LEVERAGE_IS_NOT_VENUE_PRETRADE_LIMIT = True
ACCOUNT_MODE_IS_NOT_VENUE_PRETRADE_LIMIT = True
INSTRUMENT_STATE_IS_NOT_VENUE_PRETRADE_LIMIT = True
NO_SILENT_CLAMPING = True
NO_IMPLICIT_ROUNDING = True
NO_ABSENT_MAX_EQUALS_INFINITE = True
NO_ABSENT_MIN_EQUALS_ZERO = True
CTVAL_CONVERSION_PERFORMED = False
CTMULT_CONVERSION_PERFORMED = False


class LiveCanaryVenuePretradeLimitGatesConsumerError(RuntimeError):
    """Fail-closed productive venue-pretrade limit-gate violation."""


def _require_proposed_decimal(raw: Any, *, field: str) -> Decimal:
    if raw is None:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_NULL:{field}"
        )
    if not isinstance(raw, str):
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_WRONG_TYPE:{field}"
        )
    text = raw
    if text.strip() == "":
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_EMPTY:{field}"
        )
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_NON_NUMERIC:{field}"
        ) from exc
    if value.is_nan() or value.is_infinite():
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_NON_FINITE:{field}"
        )
    if value < 0:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_NEGATIVE:{field}"
        )
    if value == 0:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_PROPOSED_ZERO_FORBIDDEN:{field}"
        )
    return value


def _require_exact_multiple(*, value: Decimal, increment: Decimal, field: str) -> None:
    remainder = value % increment
    if remainder != 0:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_NOT_EXACT_MULTIPLE:{field}"
        )


def apply_fresh_venue_pretrade_limit_gates_v1(
    *,
    pretrade_decision_id: str,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
    order_type: str,
    venue_contract_count: str,
    planned_limit_px: str,
    quantity_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = False,
    historical_reuse: bool = False,
    body_sha256: str = "",
    source_evidence: str = "",
) -> Mapping[str, Any]:
    """Bind a decision-scoped observation and fail-closed validate LIMIT limits."""
    ord_type = str(order_type or "").strip().upper()
    if ord_type != CANARY_ENTRY_ORDER_TYPE:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            f"VENUE_PRETRADE_LIMIT_ORDER_TYPE_NOT_LIMIT:{ord_type or 'EMPTY'}"
        )
    try:
        observation = acquire_fresh_venue_pretrade_limit_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            instruments_payload=instruments_payload,
            instrument_id=instrument_id,
            observed_at_utc=observed_at_utc or utc_now_iso_v1(),
            endpoint=endpoint,
            http_status=http_status,
            get_performed=get_performed,
            rest_host=rest_host or REUSED_BINDING_REST_HOST,
            auth_header_sent=auth_header_sent,
            historical_reuse=historical_reuse,
            body_sha256=body_sha256,
            source_evidence=source_evidence,
        )
        validated = validate_fresh_venue_pretrade_limit_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            quantity_domain=quantity_domain,
        )
    except LiveCanaryVenuePretradeLimitObservationError as exc:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(str(exc)) from exc
    count = _require_proposed_decimal(venue_contract_count, field="venue_contract_count")
    planned_px = _require_proposed_decimal(planned_limit_px, field="planned_limit_px")
    if count < validated.min_sz:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            "VENUE_PRETRADE_LIMIT_SIZE_BELOW_MIN_SZ"
        )
    _require_exact_multiple(value=count, increment=validated.lot_sz, field="lotSz")
    if count > validated.max_lmt_sz:
        raise LiveCanaryVenuePretradeLimitGatesConsumerError(
            "VENUE_PRETRADE_LIMIT_SIZE_ABOVE_MAX_LMT_SZ"
        )
    _require_exact_multiple(value=planned_px, increment=validated.tick_sz, field="tickSz")
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "instrument_id": observation.instrument_id,
        "order_type": ord_type,
        "required_gate_count": REQUIRED_GATE_COUNT,
        "required_gates": list(REQUIRED_GATES),
        "gates": {
            "MIN_SIZE": {
                "ok": True,
                "raw_field": "minSz",
                "raw_value": observation.min_sz_raw,
                "raw_unit": VENUE_PRETRADE_LIMIT_SIZE_UNIT,
                "order_type_scope": CANARY_ENTRY_ORDER_TYPE,
                "bound_status": "PROVEN",
            },
            "LOT_SIZE": {
                "ok": True,
                "raw_field": "lotSz",
                "raw_value": observation.lot_sz_raw,
                "raw_unit": VENUE_PRETRADE_LIMIT_SIZE_UNIT,
                "order_type_scope": CANARY_ENTRY_ORDER_TYPE,
                "bound_status": "PROVEN",
            },
            "TICK_SIZE": {
                "ok": True,
                "raw_field": "tickSz",
                "raw_value": observation.tick_sz_raw,
                "raw_unit": VENUE_PRETRADE_LIMIT_PRICE_UNIT,
                "order_type_scope": CANARY_ENTRY_ORDER_TYPE,
                "bound_status": "PROVEN",
            },
            "MAX_LIMIT_SIZE": {
                "ok": True,
                "raw_field": "maxLmtSz",
                "raw_value": observation.max_lmt_sz_raw,
                "raw_unit": VENUE_PRETRADE_LIMIT_SIZE_UNIT,
                "order_type_scope": CANARY_ENTRY_ORDER_TYPE,
                "bound_status": "PROVEN",
            },
        },
        "min_sz_raw": observation.min_sz_raw,
        "lot_sz_raw": observation.lot_sz_raw,
        "tick_sz_raw": observation.tick_sz_raw,
        "max_lmt_sz_raw": observation.max_lmt_sz_raw,
        "max_mkt_sz_raw": observation.max_mkt_sz_raw,
        "ct_val_raw": observation.ct_val_raw,
        "ct_mult_raw": observation.ct_mult_raw,
        "venue_contract_count": str(venue_contract_count),
        "planned_limit_px": str(planned_limit_px),
        "quantity_domain": observation.quantity_domain,
        "comparison_domain": validated.comparison_domain,
        "conversion_performed": False,
        "max_mkt_sz_applied": False,
        "historical_reuse": False,
        "get_performed": True,
        "target_row_count": observation.target_row_count,
        "instrument_bound": True,
        "environment_bound": True,
        "provenance_bound": True,
        "account_identity_bound_if_required": "N/A",
        "all_required_metadata_edges_bound": True,
        "freshness_policy": VENUE_PRETRADE_LIMIT_FRESHNESS_POLICY,
        "ts_age_bound": VENUE_PRETRADE_LIMIT_TS_AGE_BOUND,
        "get_venue_ts": GET_VENUE_TS_STATUS,
        "auth_class": VENUE_PRETRADE_LIMIT_AUTH_CLASS,
        "output_domain": VENUE_PRETRADE_LIMIT_OUTPUT_DOMAIN,
        "source_evidence": observation.source_evidence
        or COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE,
        "max_mkt_sz_is_not_limit_max": True,
        "max_iceberg_sz_is_not_limit_max": True,
        "max_lmt_amt_is_not_max_lmt_sz": True,
        "no_silent_clamping": True,
        "no_implicit_rounding": True,
        "ctval_conversion_performed": False,
        "ctmult_conversion_performed": False,
    }

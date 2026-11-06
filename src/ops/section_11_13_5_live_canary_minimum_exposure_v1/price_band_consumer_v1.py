"""Productive pretrade PRICE_BAND consumer for §11.13.5 order-plan.

BUY uses only fresh buyLmt (planned LIMIT px <= buyLmt).
SELL uses only fresh sellLmt (planned LIMIT px >= sellLmt).
Does not cache. Does not reconstruct from percent fields, mark price, last,
or bid/ask. Does not mix VENUE_CONTRACT_COUNT with VENUE_LIMIT_PRICE.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    OBSERVATION_CLASS_SUCCESS_NUMERIC,
    PRICE_BAND_FRESHNESS_POLICY,
    PRICE_BAND_OUTPUT_DOMAIN,
    PRICE_BAND_TS_AGE_BOUND,
    LiveCanaryPriceBandObservationError,
    acquire_fresh_price_band_observation_from_payload_v1,
    select_price_band_field_for_side_v1,
    utc_now_iso_v1,
    validate_fresh_price_band_observation_v1,
)

PRICE_BAND_CONSUMER_BOUND = True
PRICE_BAND_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
ZERO_NORMALIZATION_PERFORMED = False
PERCENT_FIELD_RECONSTRUCTION_USED = False
MARKPX_SUBSTITUTION_USED = False
ENABLED_FALSE_POLICY = "FAIL_CLOSED_NOT_ACTIVE"


class LiveCanaryPriceBandConsumerError(RuntimeError):
    """Fail-closed productive PRICE_BAND consumer violation."""


def _planned_limit_px(raw: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryPriceBandConsumerError("INVALID_DECIMAL:planned_limit_px") from exc
    if value <= 0:
        raise LiveCanaryPriceBandConsumerError("NON_POSITIVE:planned_limit_px")
    return value


def apply_fresh_price_band_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    side: str,
    planned_limit_px: str,
    price_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = False,
    historical_reuse: bool = False,
    body_sha256: str = "",
    order_type: str = "LIMIT",
) -> Mapping[str, Any]:
    """Bind a decision-scoped observation and compare planned LIMIT px."""
    try:
        observation = acquire_fresh_price_band_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=instrument_id,
            observed_at_utc=observed_at_utc or utc_now_iso_v1(),
            endpoint=endpoint,
            http_status=http_status,
            get_performed=get_performed,
            rest_host=rest_host or REUSED_BINDING_REST_HOST,
            auth_header_sent=auth_header_sent,
            historical_reuse=historical_reuse,
            body_sha256=body_sha256,
            order_type=order_type,
        )
        validated = validate_fresh_price_band_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            price_domain=price_domain,
        )
        field = select_price_band_field_for_side_v1(side=side)
        limit = validated.buy_lmt if field == "buyLmt" else validated.sell_lmt
        px = _planned_limit_px(planned_limit_px)
        selected_side = str(side).strip().upper()
        if selected_side == "BUY" and px > limit:
            raise LiveCanaryPriceBandConsumerError("PLANNED_LIMIT_PX_EXCEEDS_BUYLMT")
        if selected_side == "SELL" and px < limit:
            raise LiveCanaryPriceBandConsumerError("PLANNED_LIMIT_PX_BELOW_SELLLMT")
    except LiveCanaryPriceBandObservationError as exc:
        raise LiveCanaryPriceBandConsumerError(str(exc)) from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "side": selected_side,
        "price_band_field": field,
        "buy_lmt": observation.buy_lmt_raw,
        "sell_lmt": observation.sell_lmt_raw,
        "selected_value": format(limit, "f"),
        "planned_limit_px": format(px, "f"),
        "comparison_domain": validated.comparison_domain,
        "price_domain": observation.price_domain,
        "enabled": True,
        "ts_raw": observation.ts_raw,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": OBSERVATION_CLASS_SUCCESS_NUMERIC,
        "freshness_policy": PRICE_BAND_FRESHNESS_POLICY,
        "ts_age_bound": PRICE_BAND_TS_AGE_BOUND,
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "percent_field_reconstruction_used": PERCENT_FIELD_RECONSTRUCTION_USED,
        "markpx_substitution_used": MARKPX_SUBSTITUTION_USED,
        "enabled_false_policy": ENABLED_FALSE_POLICY,
        "output_domain": PRICE_BAND_OUTPUT_DOMAIN,
        "quantity_domain_mixed": False,
    }

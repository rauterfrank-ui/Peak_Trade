"""Productive pretrade MAX_AVAILABLE consumer for §11.13.5 order-plan.

BUY uses only fresh maxBuy. SELL uses only fresh maxSell.
LIMIT and MARKET share the side selector. Does not cache. Does not read
historical max-avail-size or BTC packs. Does not replace MAX_SIZE.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    ACCOUNT_MODE,
    ACCOUNT_MODE_PROOF_STATUS,
    DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
    MAX_AVAILABLE_LEVERAGE_REQUEST_POLICY,
    MAX_AVAILABLE_PX_SOURCE,
    OBSERVATION_CLASS_SUCCESS_NUMERIC,
    LiveCanaryMaxAvailableObservationError,
    account_mode_support_for_max_size_cross_derivatives_v1,
    acquire_fresh_max_available_observation_from_payload_v1,
    classify_max_available_observation_class_v1,
    select_max_available_field_for_side_v1,
    utc_now_iso_v1,
    validate_fresh_max_available_observation_v1,
)

MAX_AVAILABLE_CONSUMER_BOUND = True
MAX_AVAILABLE_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
AVAILABLE_MARGIN_BINDING_STATUS = "UNBOUND"
ZERO_NORMALIZATION_PERFORMED = False
MAX_AVAIL_SIZE_FALLBACK_USED = False
AVAILABLE_MARGIN_CLOSED_BY_THIS_SLICE = False


class LiveCanaryMaxAvailableConsumerError(RuntimeError):
    """Fail-closed productive MAX_AVAILABLE consumer violation."""


def _planned_count(raw: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryMaxAvailableConsumerError("INVALID_DECIMAL:venue_contract_count") from exc
    if value <= 0:
        raise LiveCanaryMaxAvailableConsumerError("NON_POSITIVE:venue_contract_count")
    return value


def apply_fresh_max_available_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    side: str,
    td_mode: str,
    venue_contract_count: str,
    quantity_domain: str,
    http_status: int,
    endpoint: str,
    px_sent: str = "",
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    order_type: str = "LIMIT",
) -> Mapping[str, Any]:
    """Bind a decision-scoped observation and compare typed contract count."""
    try:
        observation_class = classify_max_available_observation_class_v1(
            get_performed=get_performed,
            http_status=http_status,
            payload=payload if isinstance(payload, Mapping) else None,
        )
        support = account_mode_support_for_max_size_cross_derivatives_v1(
            observation_class=observation_class
        )
        observation = acquire_fresh_max_available_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=instrument_id,
            td_mode=td_mode,
            px_sent=px_sent,
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
        validated = validate_fresh_max_available_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            quantity_domain=quantity_domain,
        )
        field = select_max_available_field_for_side_v1(side=side)
        limit = validated.max_buy if field == "maxBuy" else validated.max_sell
        count = _planned_count(venue_contract_count)
        if count > limit:
            raise LiveCanaryMaxAvailableConsumerError(
                f"VENUE_CONTRACT_COUNT_EXCEEDS_{field.upper()}"
            )
    except LiveCanaryMaxAvailableObservationError as exc:
        raise LiveCanaryMaxAvailableConsumerError(str(exc)) from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "side": str(side).strip().upper(),
        "max_available_field": field,
        "max_buy": observation.max_buy_raw,
        "max_sell": observation.max_sell_raw,
        "selected_value": format(limit, "f"),
        "comparison_domain": validated.comparison_domain,
        "quantity_domain": observation.quantity_domain,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": OBSERVATION_CLASS_SUCCESS_NUMERIC,
        "account_mode": ACCOUNT_MODE,
        "account_mode_proof_status": ACCOUNT_MODE_PROOF_STATUS,
        "account_mode_support_for_max_size_cross_derivatives": support,
        "default_tdmode_cross_is_not_account_mode_proof": (
            DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF
        ),
        "px_source": MAX_AVAILABLE_PX_SOURCE,
        "leverage_request_policy": MAX_AVAILABLE_LEVERAGE_REQUEST_POLICY,
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "max_avail_size_fallback_used": MAX_AVAIL_SIZE_FALLBACK_USED,
        "available_margin_binding_status": AVAILABLE_MARGIN_BINDING_STATUS,
        "available_margin_closed_by_this_slice": AVAILABLE_MARGIN_CLOSED_BY_THIS_SLICE,
    }

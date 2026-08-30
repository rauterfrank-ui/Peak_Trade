"""Productive pretrade AVAILABLE_MARGIN consumer for §11.13.5 order-plan.

Binds currency-scoped cross-margin free margin from a decision-scoped
authenticated unfiltered GET /api/v5/account/balance. Authority is
details[ccy=USDC].availEq. Account-level availEq, availBal, max-size,
max-avail-size, POS_MODE, MARGIN_MODE, and LEVERAGE are not this edge.
USD is not USDC. Empty details are not zero. Missing USDC availEq fails
closed. No trading mutation.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY,
    AVAIL_BAL_IS_NOT_AUTHORITY,
    AVAILABLE_MARGIN_FRESHNESS_POLICY,
    AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY,
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_REQUIRED_TD_MODE,
    AVAILABLE_MARGIN_TS_AGE_BOUND,
    AVAILABLE_MARGIN_UNIT,
    AVAILABLE_MARGIN_VENUE_SCOPE,
    AVAILABLE_MARGIN_CONSUMER_SCOPE,
    AVAIL_EQ_STATUS_NOT_OBSERVED,
    EMPTY_DATA_IS_NOT_ZERO,
    LEVERAGE_IS_NOT_AVAILABLE_MARGIN_AUTHORITY,
    MARGIN_MODE_IS_NOT_NUMERIC_AVAILABLE_MARGIN,
    MAX_AVAILABLE_IS_NOT_AVAILABLE_MARGIN,
    MAX_SIZE_IS_NOT_AVAILABLE_MARGIN,
    OBSERVATION_CLASS_SUCCESS_NUMERIC,
    POS_MODE_IS_NOT_AVAILABLE_MARGIN,
    USD_USDC_EQUIVALENCE_ASSUMED,
    LiveCanaryAvailableMarginObservationError,
    acquire_fresh_available_margin_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_available_margin_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    LiveCanaryMarginModeObservationError,
)

AVAILABLE_MARGIN_CONSUMER_BOUND = True
AVAILABLE_MARGIN_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
ZERO_NORMALIZATION_PERFORMED = False
EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY = False
USD_USDC_EQUIVALENCE_ASSUMED_CONSUMER = False
MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY = False
POS_MODE_USED_AS_AVAILABLE_MARGIN_AUTHORITY = False
MARGIN_MODE_USED_AS_NUMERIC_AVAILABLE_MARGIN_AUTHORITY = False
LEVERAGE_USED_AS_AVAILABLE_MARGIN_AUTHORITY = False
AVAILABLE_MARGIN_BINDING_STATUS = "PROVEN"


class LiveCanaryAvailableMarginConsumerError(RuntimeError):
    """Fail-closed productive AVAILABLE_MARGIN consumer violation."""


def apply_fresh_available_margin_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    available_margin_domain: str,
    planned_td_mode: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
) -> Mapping[str, Any]:
    """Bind a decision-scoped USDC details.availEq observation."""
    try:
        observation = acquire_fresh_available_margin_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=instrument_id,
            planned_td_mode=planned_td_mode,
            observed_at_utc=observed_at_utc or utc_now_iso_v1(),
            endpoint=endpoint,
            http_status=http_status,
            get_performed=get_performed,
            rest_host=rest_host or REUSED_BINDING_REST_HOST,
            auth_header_sent=auth_header_sent,
            historical_reuse=historical_reuse,
            body_sha256=body_sha256,
        )
        validated = validate_fresh_available_margin_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            available_margin_domain=available_margin_domain,
            planned_td_mode=planned_td_mode,
        )
    except LiveCanaryAvailableMarginObservationError as exc:
        raise LiveCanaryAvailableMarginConsumerError(str(exc)) from exc
    except LiveCanaryMarginModeObservationError as exc:
        raise LiveCanaryAvailableMarginConsumerError(f"AVAILABLE_MARGIN_TD_MODE:{exc}") from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "selected_ccy": validated.selected_ccy,
        "avail_eq_raw": validated.avail_eq_raw,
        "avail_eq": str(validated.avail_eq),
        "avail_eq_status": observation.avail_eq_status,
        "account_avail_eq_raw": observation.account_avail_eq_raw,
        "selected_avail_bal_raw": observation.selected_avail_bal_raw,
        "required_ccy": AVAILABLE_MARGIN_REQUIRED_CCY,
        "instrument_settle_ccy": AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY,
        "planned_td_mode": validated.planned_td_mode,
        "semantic_class": validated.semantic_class,
        "unit": validated.unit,
        "venue_scope": validated.venue_scope,
        "consumer_scope": validated.consumer_scope,
        "comparison_domain": validated.comparison_domain,
        "available_margin_domain": observation.available_margin_domain,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": OBSERVATION_CLASS_SUCCESS_NUMERIC,
        "freshness_policy": AVAILABLE_MARGIN_FRESHNESS_POLICY,
        "ts_age_bound": AVAILABLE_MARGIN_TS_AGE_BOUND,
        "venue_u_time_raw": observation.venue_u_time_raw,
        "detail_u_time_raw": observation.detail_u_time_raw,
        "detail_row_count": observation.detail_row_count,
        "other_detail_ccys": list(observation.other_detail_ccys),
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "empty_response_used_as_zero_authority": EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY,
        "empty_data_is_not_zero": EMPTY_DATA_IS_NOT_ZERO,
        "usd_usdc_equivalence_assumed": USD_USDC_EQUIVALENCE_ASSUMED,
        "account_avail_eq_is_not_authority": ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY,
        "avail_bal_is_not_authority": AVAIL_BAL_IS_NOT_AUTHORITY,
        "max_available_is_not_available_margin": MAX_AVAILABLE_IS_NOT_AVAILABLE_MARGIN,
        "max_size_is_not_available_margin": MAX_SIZE_IS_NOT_AVAILABLE_MARGIN,
        "pos_mode_is_not_available_margin": POS_MODE_IS_NOT_AVAILABLE_MARGIN,
        "margin_mode_is_not_numeric_available_margin": (
            MARGIN_MODE_IS_NOT_NUMERIC_AVAILABLE_MARGIN
        ),
        "leverage_is_not_available_margin_authority": (LEVERAGE_IS_NOT_AVAILABLE_MARGIN_AUTHORITY),
        "max_size_used_as_available_margin_authority": (
            MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY
        ),
        "pos_mode_used_as_available_margin_authority": (
            POS_MODE_USED_AS_AVAILABLE_MARGIN_AUTHORITY
        ),
        "margin_mode_used_as_numeric_available_margin_authority": (
            MARGIN_MODE_USED_AS_NUMERIC_AVAILABLE_MARGIN_AUTHORITY
        ),
        "leverage_used_as_available_margin_authority": (
            LEVERAGE_USED_AS_AVAILABLE_MARGIN_AUTHORITY
        ),
        "required_order_td_mode": AVAILABLE_MARGIN_REQUIRED_TD_MODE,
        "output_domain": AVAILABLE_MARGIN_OUTPUT_DOMAIN,
        "venue_scope_constant": AVAILABLE_MARGIN_VENUE_SCOPE,
        "consumer_scope_constant": AVAILABLE_MARGIN_CONSUMER_SCOPE,
        "quantity_domain_mixed": False,
        "price_domain_mixed": False,
        "not_observed_status": AVAIL_EQ_STATUS_NOT_OBSERVED,
        "usd_usdc_equivalence_assumed_consumer": USD_USDC_EQUIVALENCE_ASSUMED_CONSUMER,
        "available_margin_binding_status": AVAILABLE_MARGIN_BINDING_STATUS,
    }

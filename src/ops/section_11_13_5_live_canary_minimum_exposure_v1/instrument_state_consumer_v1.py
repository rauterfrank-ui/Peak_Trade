"""Productive pretrade INSTRUMENT_STATE consumer for §11.13.5 order-plan.

Order-attempt eligibility requires exact fresh `state=live` on the current
canonical instrument row. This is not live authorization. ruleType, instType,
expTime, ticker, and mark price are not this edge.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.instrument_state_observation_v1 import (
    GET_VENUE_TS_STATUS,
    INSTRUMENT_STATE_FRESHNESS_POLICY,
    INSTRUMENT_STATE_OUTPUT_DOMAIN,
    INSTRUMENT_STATE_SEMANTIC_CLASS,
    INSTRUMENT_STATE_TS_AGE_BOUND,
    OBSERVATION_CLASS_SUCCESS_LIVE,
    LiveCanaryInstrumentStateObservationError,
    acquire_fresh_instrument_state_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_instrument_state_observation_v1,
)

INSTRUMENT_STATE_CONSUMER_BOUND = True
INSTRUMENT_STATE_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
INSTRUMENT_STATE_IS_NOT_LIVE_AUTHORIZATION = True
RULE_TYPE_XPERP_IS_NOT_INSTRUMENT_STATE_AUTHORITY = True
INST_TYPE_FUTURES_IS_NOT_INSTRUMENT_STATE_AUTHORITY = True
EXP_TIME_IS_NOT_INSTRUMENT_STATE_AUTHORITY = True
TICKER_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY = True
MARK_PRICE_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY = True
UNKNOWN_STATE_IS_NOT_LIVE = True
NOT_OBSERVED_IS_NOT_LIVE = True
CANONICAL_REBIND_IS_NOT_CURRENT_STATE_PROOF = True


class LiveCanaryInstrumentStateConsumerError(RuntimeError):
    """Fail-closed productive INSTRUMENT_STATE consumer violation."""


def apply_fresh_instrument_state_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
    instrument_state_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = False,
    historical_reuse: bool = False,
    body_sha256: str = "",
    request_started_at_utc: str = "",
    request_finished_at_utc: str = "",
) -> Mapping[str, Any]:
    """Bind a decision-scoped observation and require exact state=live."""
    try:
        observation = acquire_fresh_instrument_state_observation_from_payload_v1(
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
            request_started_at_utc=request_started_at_utc,
            request_finished_at_utc=request_finished_at_utc,
        )
        validated = validate_fresh_instrument_state_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            instrument_state_domain=instrument_state_domain,
        )
    except LiveCanaryInstrumentStateObservationError as exc:
        raise LiveCanaryInstrumentStateConsumerError(str(exc)) from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "instrument_id": observation.instrument_id,
        "state_raw": observation.state_raw,
        "semantic_value": validated.semantic_value,
        "consumer_precondition_satisfied": True,
        "comparison_domain": validated.comparison_domain,
        "instrument_state_domain": observation.instrument_state_domain,
        "inst_type_raw": observation.inst_type_raw,
        "rule_type_raw": observation.rule_type_raw,
        "historical_reuse": False,
        "get_performed": True,
        "target_row_count": observation.target_row_count,
        "observation_class": OBSERVATION_CLASS_SUCCESS_LIVE,
        "freshness_policy": INSTRUMENT_STATE_FRESHNESS_POLICY,
        "ts_age_bound": INSTRUMENT_STATE_TS_AGE_BOUND,
        "get_venue_ts": GET_VENUE_TS_STATUS,
        "semantic_class": INSTRUMENT_STATE_SEMANTIC_CLASS,
        "output_domain": INSTRUMENT_STATE_OUTPUT_DOMAIN,
        "instrument_state_is_not_live_authorization": True,
        "rule_type_xperp_is_not_instrument_state_authority": True,
        "inst_type_futures_is_not_instrument_state_authority": True,
    }

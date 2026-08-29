"""Productive pretrade max-size consumer for §11.13.5 order-plan.

LIMIT uses only fresh maxLmtSz. MARKET uses only fresh maxMktSz.
Does not cache. Does not read historical #6148 packs.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    LiveCanaryMaxSizeObservationError,
    acquire_fresh_max_size_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_max_size_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    LiveCanaryVenueContractCountError,
    compare_venue_contract_count_to_max_size_v1,
    select_max_size_field_for_order_type_v1,
)

MAX_SIZE_CONSUMER_BOUND = True
LIMIT_MAX_SIZE_GATE_BOUND = True
MARKET_MAX_SIZE_GATE_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False


class LiveCanaryMaxSizeConsumerError(RuntimeError):
    """Fail-closed productive max-size consumer violation."""


def apply_fresh_max_size_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    instruments_payload: Mapping[str, Any],
    instrument_id: str,
    order_type: str,
    venue_contract_count: str,
    quantity_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = False,
    historical_reuse: bool = False,
    body_sha256: str = "",
) -> Mapping[str, Any]:
    """Bind a decision-scoped observation and compare typed contract count."""
    try:
        observation = acquire_fresh_max_size_observation_from_payload_v1(
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
        )
        validated = validate_fresh_max_size_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            quantity_domain=quantity_domain,
        )
        field = select_max_size_field_for_order_type_v1(order_type=order_type)
        compared = compare_venue_contract_count_to_max_size_v1(
            venue_contract_count=venue_contract_count,
            order_type=order_type,
            max_lmt_sz=format(validated.max_lmt_sz, "f"),
            max_mkt_sz=format(validated.max_mkt_sz, "f"),
        )
    except LiveCanaryMaxSizeObservationError as exc:
        raise LiveCanaryMaxSizeConsumerError(str(exc)) from exc
    except LiveCanaryVenueContractCountError as exc:
        raise LiveCanaryMaxSizeConsumerError(str(exc)) from exc
    if compared.get("max_size_field") != field:
        raise LiveCanaryMaxSizeConsumerError("MAX_SIZE_FIELD_SELECTION_DRIFT")
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "order_type": str(order_type).strip().upper(),
        "max_size_field": field,
        "max_lmt_sz": observation.max_lmt_sz_raw,
        "max_mkt_sz": observation.max_mkt_sz_raw,
        "comparison_domain": validated.comparison_domain,
        "quantity_domain": observation.quantity_domain,
        "historical_reuse": False,
        "get_performed": True,
    }

"""Productive pretrade POS_MODE consumer for §11.13.5 order-plan.

Binds current account position mode from a decision-scoped authenticated
GET /api/v5/account/config. Does not cache. Does not substitute posSide=net,
tdMode=cross, mgnMode=cross, acctLv, MAX_POSITIONS, Single-Selected-Future,
or historical BTC posMode. Venue token net_mode is not rewritten to posSide
net. No set-position-mode.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    ACCTLV_IS_NOT_POS_MODE,
    MGNMODE_CROSS_IS_NOT_POS_MODE,
    MAX_POSITIONS_IS_NOT_POS_MODE,
    OBSERVATION_CLASS_SUCCESS_TOKEN,
    POS_MODE_FRESHNESS_POLICY,
    POS_MODE_OUTPUT_DOMAIN,
    POS_MODE_REQUIRED_VALUE,
    POS_MODE_SEMANTIC_CLASS,
    POS_MODE_TS_AGE_BOUND,
    POS_MODE_VENUE_ALLOWED_VALUES,
    POS_MODE_VENUE_SCOPE,
    POS_MODE_CONSUMER_SCOPE,
    POSSIDE_NET_IS_NOT_POS_MODE,
    SINGLE_SELECTED_FUTURE_IS_NOT_POS_MODE,
    TDMODE_CROSS_IS_NOT_POS_MODE,
    LiveCanaryPosModeObservationError,
    acquire_fresh_pos_mode_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_pos_mode_observation_v1,
)

POS_MODE_CONSUMER_BOUND = True
POS_MODE_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
ZERO_NORMALIZATION_PERFORMED = False
DEFAULT_POS_MODE_USED = False
HISTORICAL_POS_MODE_REUSED = False
LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF = False
TDMODE_CROSS_REUSED_AS_POS_MODE_PROOF = False
MGNMODE_CROSS_REUSED_AS_POS_MODE_PROOF = False
SET_POSITION_MODE_EXECUTED = False


class LiveCanaryPosModeConsumerError(RuntimeError):
    """Fail-closed productive POS_MODE consumer violation."""


def apply_fresh_pos_mode_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    pos_mode_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    td_mode: str | None = None,
    mgn_mode: str | None = None,
    pos_side: str | None = None,
    max_positions: int | None = None,
    single_selected_future: bool | None = None,
) -> Mapping[str, Any]:
    """Bind a decision-scoped current account posMode observation."""
    if td_mode is not None:
        _ = str(td_mode)
    if mgn_mode is not None:
        _ = str(mgn_mode)
    if pos_side is not None:
        _ = str(pos_side)
    if max_positions is not None:
        _ = int(max_positions)
    if single_selected_future is not None:
        _ = bool(single_selected_future)
    try:
        observation = acquire_fresh_pos_mode_observation_from_payload_v1(
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
        )
        validated = validate_fresh_pos_mode_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            pos_mode_domain=pos_mode_domain,
        )
    except LiveCanaryPosModeObservationError as exc:
        raise LiveCanaryPosModeConsumerError(str(exc)) from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "pos_mode": validated.pos_mode,
        "pos_mode_raw": observation.pos_mode_raw,
        "semantic_class": validated.semantic_class,
        "acct_lv_raw": observation.acct_lv_raw,
        "acct_lv_bound": False,
        "venue_scope": validated.venue_scope,
        "consumer_scope": validated.consumer_scope,
        "comparison_domain": validated.comparison_domain,
        "pos_mode_domain": observation.pos_mode_domain,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": OBSERVATION_CLASS_SUCCESS_TOKEN,
        "freshness_policy": POS_MODE_FRESHNESS_POLICY,
        "ts_age_bound": POS_MODE_TS_AGE_BOUND,
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "default_pos_mode_used": DEFAULT_POS_MODE_USED,
        "historical_pos_mode_reused": HISTORICAL_POS_MODE_REUSED,
        "leverage_posside_net_reused_as_pos_mode_proof": (
            LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF
        ),
        "tdmode_cross_reused_as_pos_mode_proof": TDMODE_CROSS_REUSED_AS_POS_MODE_PROOF,
        "mgnmode_cross_reused_as_pos_mode_proof": MGNMODE_CROSS_REUSED_AS_POS_MODE_PROOF,
        "acctlv_is_not_pos_mode": ACCTLV_IS_NOT_POS_MODE,
        "posside_net_is_not_pos_mode": POSSIDE_NET_IS_NOT_POS_MODE,
        "tdmode_cross_is_not_pos_mode": TDMODE_CROSS_IS_NOT_POS_MODE,
        "mgnmode_cross_is_not_pos_mode": MGNMODE_CROSS_IS_NOT_POS_MODE,
        "max_positions_is_not_pos_mode": MAX_POSITIONS_IS_NOT_POS_MODE,
        "single_selected_future_is_not_pos_mode": SINGLE_SELECTED_FUTURE_IS_NOT_POS_MODE,
        "required_value": POS_MODE_REQUIRED_VALUE,
        "allowed_venue_values": sorted(POS_MODE_VENUE_ALLOWED_VALUES),
        "output_domain": POS_MODE_OUTPUT_DOMAIN,
        "semantic_class_constant": POS_MODE_SEMANTIC_CLASS,
        "venue_scope_constant": POS_MODE_VENUE_SCOPE,
        "consumer_scope_constant": POS_MODE_CONSUMER_SCOPE,
        "quantity_domain_mixed": False,
        "price_domain_mixed": False,
        "set_position_mode_executed": SET_POSITION_MODE_EXECUTED,
        "unbound_account_config_fields": dict(observation.unbound_account_config_fields),
    }

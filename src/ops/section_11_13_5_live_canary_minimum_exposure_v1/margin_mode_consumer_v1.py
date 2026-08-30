"""Productive pretrade MARGIN_MODE consumer for §11.13.5 order-plan.

Binds current single-selected-future execution tdMode. Requires a
decision-scoped authenticated unfiltered GET /api/v5/account/positions as a
conflict check. Empty data is not a margin mode and is not zero. Does not
use account/config, acctLv, posMode, ctIsoMode, mgnIsoMode, or leverage-info
as MARGIN_MODE authority. Isolated planned tdMode fails closed. Observed
target-row mgnMode that disagrees with planned tdMode is a scoped conflict.
No set-isolated-mode.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    ACCTLV_IS_NOT_MARGIN_MODE,
    CTISOMODE_IS_NOT_MARGIN_MODE,
    DEFAULT_TDMODE_IS_NOT_ACCOUNT_MODE_PROOF,
    EMPTY_DATA_IS_NOT_ZERO,
    LEVERAGE_MGNMODE_IS_NOT_MARGIN_MODE_AUTHORITY,
    MARGIN_MODE_FRESHNESS_POLICY,
    MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS,
    MARGIN_MODE_OUTPUT_DOMAIN,
    MARGIN_MODE_REQUIRED_ORDER_TD_MODE,
    MARGIN_MODE_TS_AGE_BOUND,
    MARGIN_MODE_VENUE_ALLOWED_VALUES,
    MARGIN_MODE_VENUE_SCOPE,
    MARGIN_MODE_CONSUMER_SCOPE,
    MGNISOMODE_IS_NOT_MARGIN_MODE,
    OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED,
    OBSERVATION_CLASS_SUCCESS_TOKEN,
    POSMODE_IS_NOT_MARGIN_MODE,
    POSITION_MGN_MODE_STATUS_NOT_OBSERVED,
    LiveCanaryMarginModeObservationError,
    acquire_fresh_margin_mode_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_margin_mode_observation_v1,
)

MARGIN_MODE_CONSUMER_BOUND = True
MARGIN_MODE_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
ZERO_NORMALIZATION_PERFORMED = False
EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY = False
ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY = False
ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY = False
POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY = False
LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY = False
MARGIN_MODE_MUTATION_PERFORMED = False


class LiveCanaryMarginModeConsumerError(RuntimeError):
    """Fail-closed productive MARGIN_MODE consumer violation."""


def apply_fresh_margin_mode_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    margin_mode_domain: str,
    planned_td_mode: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    leverage_mgn_mode: str | None = None,
    acct_lv: str | None = None,
    pos_mode: str | None = None,
) -> Mapping[str, Any]:
    """Bind a decision-scoped current-future execution tdMode observation."""
    if leverage_mgn_mode is not None:
        supporting = str(leverage_mgn_mode).strip()
        if supporting and supporting != MARGIN_MODE_REQUIRED_ORDER_TD_MODE:
            raise LiveCanaryMarginModeConsumerError(
                f"MARGIN_MODE_LEVERAGE_SCOPE_CONFLICT:{supporting}"
            )
    if acct_lv is not None:
        _ = str(acct_lv)
    if pos_mode is not None:
        _ = str(pos_mode)
    try:
        observation = acquire_fresh_margin_mode_observation_from_payload_v1(
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
        validated = validate_fresh_margin_mode_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            margin_mode_domain=margin_mode_domain,
            planned_td_mode=planned_td_mode,
        )
    except LiveCanaryMarginModeObservationError as exc:
        raise LiveCanaryMarginModeConsumerError(str(exc)) from exc
    observation_class = (
        OBSERVATION_CLASS_SUCCESS_NOT_OBSERVED
        if validated.position_mgn_mode_status == POSITION_MGN_MODE_STATUS_NOT_OBSERVED
        else OBSERVATION_CLASS_SUCCESS_TOKEN
    )
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "order_td_mode": validated.order_td_mode,
        "position_mgn_mode_raw": observation.position_mgn_mode_raw,
        "position_mgn_mode_status": validated.position_mgn_mode_status,
        "semantic_class": validated.semantic_class,
        "venue_scope": validated.venue_scope,
        "consumer_scope": validated.consumer_scope,
        "comparison_domain": validated.comparison_domain,
        "margin_mode_domain": observation.margin_mode_domain,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": observation_class,
        "freshness_policy": MARGIN_MODE_FRESHNESS_POLICY,
        "ts_age_bound": MARGIN_MODE_TS_AGE_BOUND,
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "empty_positions_used_as_margin_mode_authority": (
            EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY
        ),
        "account_config_used_as_margin_mode_authority": (
            ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY
        ),
        "acct_lv_used_as_margin_mode_authority": ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY,
        "pos_mode_used_as_margin_mode_authority": POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY,
        "leverage_used_as_margin_mode_authority": LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY,
        "acctlv_is_not_margin_mode": ACCTLV_IS_NOT_MARGIN_MODE,
        "posmode_is_not_margin_mode": POSMODE_IS_NOT_MARGIN_MODE,
        "ctisomode_is_not_margin_mode": CTISOMODE_IS_NOT_MARGIN_MODE,
        "mgnisomode_is_not_margin_mode": MGNISOMODE_IS_NOT_MARGIN_MODE,
        "leverage_mgnmode_is_not_margin_mode_authority": (
            LEVERAGE_MGNMODE_IS_NOT_MARGIN_MODE_AUTHORITY
        ),
        "default_tdmode_is_not_account_mode_proof": DEFAULT_TDMODE_IS_NOT_ACCOUNT_MODE_PROOF,
        "empty_data_is_not_zero": EMPTY_DATA_IS_NOT_ZERO,
        "margin_mode_global_account_setting_exists": (MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS),
        "required_order_td_mode": MARGIN_MODE_REQUIRED_ORDER_TD_MODE,
        "allowed_venue_values": sorted(MARGIN_MODE_VENUE_ALLOWED_VALUES),
        "output_domain": MARGIN_MODE_OUTPUT_DOMAIN,
        "venue_scope_constant": MARGIN_MODE_VENUE_SCOPE,
        "consumer_scope_constant": MARGIN_MODE_CONSUMER_SCOPE,
        "quantity_domain_mixed": False,
        "price_domain_mixed": False,
        "margin_mode_mutation_performed": MARGIN_MODE_MUTATION_PERFORMED,
        "target_row_count": observation.target_row_count,
        "total_row_count": observation.total_row_count,
        "other_instrument_mgn_modes": list(observation.other_instrument_mgn_modes),
    }

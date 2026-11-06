"""Productive pretrade LEVERAGE consumer for §11.13.5 order-plan.

Binds current configured set-account leverage from a decision-scoped
authenticated GET /api/v5/account/leverage-info. Does not cache. Does not
substitute BTC lever=3, public max leverage, IMR/MMR, or position lever.
mgnMode is not tdMode and is not account-mode proof.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_EXPECTED_MGN_MODE,
    LEVERAGE_EXPECTED_POS_SIDE,
    LEVERAGE_FRESHNESS_POLICY,
    LEVERAGE_OUTPUT_DOMAIN,
    LEVERAGE_REQUEST_INSTID_ROLE,
    LEVERAGE_SCOPE,
    LEVERAGE_TS_AGE_BOUND,
    MGNMODE_IS_NOT_ACCOUNT_MODE,
    MGNMODE_IS_NOT_TDMODE,
    OBSERVATION_CLASS_SUCCESS_NUMERIC,
    TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
    LiveCanaryLeverageObservationError,
    acquire_fresh_leverage_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_leverage_observation_v1,
)

LEVERAGE_CONSUMER_BOUND = True
LEVERAGE_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
ZERO_NORMALIZATION_PERFORMED = False
DEFAULT_LEVERAGE_USED = False
MAX_LEVERAGE_SUBSTITUTION_USED = False
IMR_MMR_RECONSTRUCTION_USED = False
HISTORICAL_BTC_LEVERAGE_REUSED = False


class LiveCanaryLeverageConsumerError(RuntimeError):
    """Fail-closed productive LEVERAGE consumer violation."""


def apply_fresh_leverage_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    mgn_mode: str,
    leverage_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    expected_inst_family: str = DEFAULT_INST_FAMILY,
    td_mode: str | None = None,
) -> Mapping[str, Any]:
    """Bind a decision-scoped current configured leverage observation."""
    if td_mode is not None:
        # Presence of tdMode on the order path is independent. It is not mgnMode
        # and is not accepted as account-mode proof.
        _ = str(td_mode)
    try:
        observation = acquire_fresh_leverage_observation_from_payload_v1(
            pretrade_decision_id=pretrade_decision_id,
            payload=payload,
            instrument_id=instrument_id,
            mgn_mode=mgn_mode,
            observed_at_utc=observed_at_utc or utc_now_iso_v1(),
            endpoint=endpoint,
            http_status=http_status,
            get_performed=get_performed,
            rest_host=rest_host or REUSED_BINDING_REST_HOST,
            auth_header_sent=auth_header_sent,
            historical_reuse=historical_reuse,
            body_sha256=body_sha256,
            expected_inst_family=expected_inst_family,
        )
        validated = validate_fresh_leverage_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            leverage_domain=leverage_domain,
            mgn_mode=mgn_mode,
            expected_inst_family=expected_inst_family,
        )
    except LiveCanaryLeverageObservationError as exc:
        raise LiveCanaryLeverageConsumerError(str(exc)) from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "lever": format(validated.lever, "f"),
        "lever_raw": observation.lever_raw,
        "mgn_mode": validated.mgn_mode,
        "pos_side": validated.pos_side,
        "inst_id": observation.inst_id_raw,
        "ccy_raw": observation.ccy_raw,
        "inst_family": validated.inst_family,
        "leverage_scope": LEVERAGE_SCOPE,
        "request_instid_role": LEVERAGE_REQUEST_INSTID_ROLE,
        "comparison_domain": validated.comparison_domain,
        "leverage_domain": observation.leverage_domain,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": OBSERVATION_CLASS_SUCCESS_NUMERIC,
        "freshness_policy": LEVERAGE_FRESHNESS_POLICY,
        "ts_age_bound": LEVERAGE_TS_AGE_BOUND,
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "default_leverage_used": DEFAULT_LEVERAGE_USED,
        "max_leverage_substitution_used": MAX_LEVERAGE_SUBSTITUTION_USED,
        "imr_mmr_reconstruction_used": IMR_MMR_RECONSTRUCTION_USED,
        "historical_btc_leverage_reused": HISTORICAL_BTC_LEVERAGE_REUSED,
        "mgnmode_is_not_tdmode": MGNMODE_IS_NOT_TDMODE,
        "mgnmode_is_not_account_mode": MGNMODE_IS_NOT_ACCOUNT_MODE,
        "tdmode_cross_is_not_account_mode_proof": TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
        "expected_mgn_mode": LEVERAGE_EXPECTED_MGN_MODE,
        "expected_pos_side": LEVERAGE_EXPECTED_POS_SIDE,
        "output_domain": LEVERAGE_OUTPUT_DOMAIN,
        "quantity_domain_mixed": False,
        "price_domain_mixed": False,
    }

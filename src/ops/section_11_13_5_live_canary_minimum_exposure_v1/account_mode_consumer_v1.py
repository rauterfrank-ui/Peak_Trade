"""Productive pretrade ACCOUNT_MODE consumer for §11.13.5 order-plan.

Binds current account mode from a decision-scoped authenticated
GET /api/v5/account/config field acctLv. Reuses the POS_MODE GET payload.
Does not cache. Does not substitute posMode, tdMode, mgnMode, leverage,
settleCcy, instrument state, or historical GATE_20 status. Raw venue token
``2`` is not rewritten. No set-account-level.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_mode_observation_v1 import (
    ACCOUNT_IDENTITY_IS_NOT_ACCOUNT_MODE,
    ACCOUNT_MODE_FRESHNESS_POLICY,
    ACCOUNT_MODE_KNOWN_NEGATIVE_RAW,
    ACCOUNT_MODE_OUTPUT_DOMAIN,
    ACCOUNT_MODE_REQUIRED_VALUE,
    ACCOUNT_MODE_SEMANTIC_CLASS,
    ACCOUNT_MODE_TS_AGE_BOUND,
    ACCOUNT_MODE_VENUE_ALLOWED_VALUES,
    ACCOUNT_MODE_VENUE_SCOPE,
    ACCOUNT_MODE_CONSUMER_SCOPE,
    AVAILABLE_MARGIN_IS_NOT_ACCOUNT_MODE,
    COMMITTED_POS_MODE_SNAPSHOT_RELATIVE,
    DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
    INSTRUMENT_STATE_IS_NOT_ACCOUNT_MODE,
    LEVERAGE_IS_NOT_ACCOUNT_MODE,
    MGNMODE_CROSS_IS_NOT_ACCOUNT_MODE,
    OBSERVATION_CLASS_SUCCESS_TOKEN,
    POS_MODE_IS_NOT_ACCOUNT_MODE,
    SETTLE_CCY_IS_NOT_ACCOUNT_MODE,
    TDMODE_CROSS_IS_NOT_ACCOUNT_MODE,
    LiveCanaryAccountModeObservationError,
    acquire_fresh_account_mode_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_account_mode_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
)

ACCOUNT_MODE_CONSUMER_BOUND = True
ACCOUNT_MODE_FAIL_CLOSED_BOUND = True
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION = True
HISTORICAL_REUSE_PATH_EXISTS = False
ZERO_NORMALIZATION_PERFORMED = False
DEFAULT_ACCOUNT_MODE_USED = False
HISTORICAL_ACCOUNT_MODE_REUSED = False
POS_MODE_REUSED_AS_ACCOUNT_MODE_PROOF = False
TDMODE_CROSS_REUSED_AS_ACCOUNT_MODE_PROOF = False
MGNMODE_CROSS_REUSED_AS_ACCOUNT_MODE_PROOF = False
SET_ACCOUNT_LEVEL_EXECUTED = False
ACCOUNT_MODE_MUTATION_PERFORMED = False


class LiveCanaryAccountModeConsumerError(RuntimeError):
    """Fail-closed productive ACCOUNT_MODE consumer violation."""


def apply_fresh_account_mode_pretrade_gate_v1(
    *,
    pretrade_decision_id: str,
    payload: Mapping[str, Any],
    instrument_id: str,
    account_mode_domain: str,
    http_status: int,
    endpoint: str,
    observed_at_utc: str | None = None,
    get_performed: bool = True,
    rest_host: str | None = None,
    auth_header_sent: bool = True,
    historical_reuse: bool = False,
    body_sha256: str = "",
    source_evidence: str = COMMITTED_POS_MODE_SNAPSHOT_RELATIVE,
    td_mode: str | None = None,
    mgn_mode: str | None = None,
    pos_mode: str | None = None,
) -> Mapping[str, Any]:
    """Bind a decision-scoped current account acctLv observation."""
    if td_mode is not None:
        _ = str(td_mode)
    if mgn_mode is not None:
        _ = str(mgn_mode)
    if pos_mode is not None:
        _ = str(pos_mode)
    try:
        observation = acquire_fresh_account_mode_observation_from_payload_v1(
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
            source_evidence=source_evidence,
        )
        validated = validate_fresh_account_mode_observation_v1(
            observation,
            pretrade_decision_id=pretrade_decision_id,
            instrument_id=instrument_id,
            account_mode_domain=account_mode_domain,
        )
    except LiveCanaryAccountModeObservationError as exc:
        raise LiveCanaryAccountModeConsumerError(str(exc)) from exc
    return {
        "ok": True,
        "pretrade_decision_id": observation.pretrade_decision_id,
        "acct_lv": validated.acct_lv,
        "acct_lv_raw": observation.acct_lv_raw,
        "semantic_class": validated.semantic_class,
        "uid_raw": observation.uid_raw,
        "pos_mode_raw_contextual": observation.pos_mode_raw_contextual,
        "pos_mode_bound": False,
        "account_identity_bound": validated.account_identity_bound,
        "environment_bound": validated.environment_bound,
        "provenance_bound": validated.provenance_bound,
        "all_required_metadata_edges_bound": True,
        "venue_scope": validated.venue_scope,
        "consumer_scope": validated.consumer_scope,
        "comparison_domain": validated.comparison_domain,
        "account_mode_domain": observation.account_mode_domain,
        "historical_reuse": False,
        "get_performed": True,
        "observation_class": OBSERVATION_CLASS_SUCCESS_TOKEN,
        "freshness_policy": ACCOUNT_MODE_FRESHNESS_POLICY,
        "ts_age_bound": ACCOUNT_MODE_TS_AGE_BOUND,
        "zero_normalization_performed": ZERO_NORMALIZATION_PERFORMED,
        "default_account_mode_used": DEFAULT_ACCOUNT_MODE_USED,
        "historical_account_mode_reused": HISTORICAL_ACCOUNT_MODE_REUSED,
        "pos_mode_reused_as_account_mode_proof": POS_MODE_REUSED_AS_ACCOUNT_MODE_PROOF,
        "tdmode_cross_reused_as_account_mode_proof": TDMODE_CROSS_REUSED_AS_ACCOUNT_MODE_PROOF,
        "mgnmode_cross_reused_as_account_mode_proof": MGNMODE_CROSS_REUSED_AS_ACCOUNT_MODE_PROOF,
        "pos_mode_is_not_account_mode": POS_MODE_IS_NOT_ACCOUNT_MODE,
        "tdmode_cross_is_not_account_mode": TDMODE_CROSS_IS_NOT_ACCOUNT_MODE,
        "mgnmode_cross_is_not_account_mode": MGNMODE_CROSS_IS_NOT_ACCOUNT_MODE,
        "leverage_is_not_account_mode": LEVERAGE_IS_NOT_ACCOUNT_MODE,
        "settle_ccy_is_not_account_mode": SETTLE_CCY_IS_NOT_ACCOUNT_MODE,
        "instrument_state_is_not_account_mode": INSTRUMENT_STATE_IS_NOT_ACCOUNT_MODE,
        "available_margin_is_not_account_mode": AVAILABLE_MARGIN_IS_NOT_ACCOUNT_MODE,
        "account_identity_is_not_account_mode": ACCOUNT_IDENTITY_IS_NOT_ACCOUNT_MODE,
        "default_tdmode_cross_is_not_account_mode_proof": (
            DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF
        ),
        "required_value": ACCOUNT_MODE_REQUIRED_VALUE,
        "allowed_venue_values": sorted(ACCOUNT_MODE_VENUE_ALLOWED_VALUES),
        "known_negative_raw": sorted(ACCOUNT_MODE_KNOWN_NEGATIVE_RAW),
        "output_domain": ACCOUNT_MODE_OUTPUT_DOMAIN,
        "semantic_class_constant": ACCOUNT_MODE_SEMANTIC_CLASS,
        "venue_scope_constant": ACCOUNT_MODE_VENUE_SCOPE,
        "consumer_scope_constant": ACCOUNT_MODE_CONSUMER_SCOPE,
        "source_evidence": observation.source_evidence,
        "set_account_level_executed": SET_ACCOUNT_LEVEL_EXECUTED,
        "account_mode_mutation_performed": ACCOUNT_MODE_MUTATION_PERFORMED,
    }

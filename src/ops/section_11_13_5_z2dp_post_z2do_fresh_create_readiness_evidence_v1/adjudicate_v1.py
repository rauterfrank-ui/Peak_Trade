"""Adjudicate the Z2DP fresh create-readiness observation package.

Does not choose a trade quantity. Does not manufacture posSide. Does not close
Prerequisite 08 unless the canonical classifier proves a matching NONZERO row.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_FAIL_CLOSED as ROUTE_C_POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS as ROUTE_C_POSITION_MODE_SUBMIT_BODY_SEMANTICS,
)
from src.ops.pre_submit_open_position_cap_v1 import (
    REASON_ALLOW_NO_OPEN_POSITION,
    REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN,
    REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT,
    evaluate_pre_submit_open_position_cap_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAIL_EQ_STATUS_OBSERVED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    POSITION_COUNT_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_REQUIRED_VALUE,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.constants_v1 import (
    BOUND_ACCOUNT_SCOPE,
    CREATE_READINESS_BLOCKED_EXPOSURE,
    CREATE_READINESS_BLOCKED_FUNDING,
    CREATE_READINESS_BLOCKED_IDENTITY,
    CREATE_READINESS_BLOCKED_MULTIPLE,
    CREATE_READINESS_BLOCKED_POSITION_MODE,
    CREATE_READINESS_BLOCKED_PRETRADE,
    CREATE_READINESS_NOT_DETERMINABLE,
    CREATE_READINESS_READY,
    FRESHNESS_NOT_APPLICABLE,
    FRESHNESS_SENDTIME_REFRESH_REQUIRED,
    FRESHNESS_SENDTIME_REUSABLE,
    FRESHNESS_UNPROVEN,
    FUNDING_GET_NOT_REQUIRED_REASON,
    FUNDING_GET_REQUIRED,
    POSITION_MODE_SEMANTICS_UNPROVEN,
    QTY_BLOCKED_CAPACITY,
    QTY_BLOCKED_FUNDING,
    QTY_POTENTIALLY_ADMISSIBLE,
    QTY_UNPROVEN,
    TARGET_INSTRUMENT_ID,
    VENUE_CAPACITY_POSITIVE,
    VENUE_CAPACITY_UNPROVEN,
    VENUE_CAPACITY_ZERO,
)


def _decimal_or_none(raw: Any) -> Decimal | None:
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        return None


def adjudicate_position_mode_submit_body_semantics_v1(
    *,
    pos_mode_raw: str | None,
) -> dict[str, Any]:
    """Account posMode is not submit-body posSide proof.

    Repository-authoritative Route-C contract remains UNPROVEN. Canary
    omit-on-net-mode is not transferred. No first-party OKX submit-body
    artifact in this GO's evidence set proves omit vs emit vs other.
    """
    del pos_mode_raw
    if ROUTE_C_POSITION_MODE_SUBMIT_BODY_SEMANTICS != POSITION_MODE_SEMANTICS_UNPROVEN:
        return {
            "POSITION_MODE_SUBMIT_BODY_SEMANTICS": ROUTE_C_POSITION_MODE_SUBMIT_BODY_SEMANTICS,
            "POSITION_MODE_FAIL_CLOSED": True,
            "POSITION_MODE_READY": False,
            "POSITION_MODE_REASON": "ROUTE_C_SEMANTICS_DRIFT",
        }
    if not ROUTE_C_POSITION_MODE_FAIL_CLOSED:
        return {
            "POSITION_MODE_SUBMIT_BODY_SEMANTICS": POSITION_MODE_SEMANTICS_UNPROVEN,
            "POSITION_MODE_FAIL_CLOSED": True,
            "POSITION_MODE_READY": False,
            "POSITION_MODE_REASON": "POSITION_MODE_FAIL_CLOSED_REQUIRED",
        }
    return {
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS": POSITION_MODE_SEMANTICS_UNPROVEN,
        "POSITION_MODE_FAIL_CLOSED": True,
        "POSITION_MODE_READY": False,
        "POSITION_MODE_REASON": (
            "NO_REPOSITORY_FIRST_PARTY_OKX_SUBMIT_BODY_CONTRACT_FOR_NET_MODE_POSSIDE"
        ),
    }


def adjudicate_create_readiness_v1(*, observations: Mapping[str, Any]) -> dict[str, Any]:
    identity_uid = str(observations.get("ACCOUNT_UID") or "").strip()
    identity_match = identity_uid == BOUND_ACCOUNT_SCOPE
    identity_ready = bool(observations.get("ACCOUNT_IDENTITY_OBSERVED")) and identity_match

    pos_mode = adjudicate_position_mode_submit_body_semantics_v1(
        pos_mode_raw=str(observations.get("POS_MODE_RAW") or "") or None
    )
    pos_mode_observed = str(observations.get("POS_MODE_RAW") or "").strip()
    pos_mode_matches_required = pos_mode_observed == POS_MODE_REQUIRED_VALUE

    classifier_state = str(observations.get("TARGET_POSITION_STATE") or "")
    prerequisite_08_closed = classifier_state == TARGET_POSITION_NONZERO_PROVEN

    cap = observations.get("OPEN_POSITION_CAP") or {}
    cap_reason = str(cap.get("reason_code") or "")
    cap_admitted = bool(cap.get("admitted"))
    existing_exposure_blocked = (
        classifier_state == TARGET_POSITION_NONZERO_PROVEN
        or cap_reason == REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT
        or cap_reason == REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN
    )
    existing_exposure_clear = (
        classifier_state in {TARGET_POSITION_NOT_OBSERVED, TARGET_POSITION_ZERO_PROVEN}
        and cap_admitted
        and cap_reason == REASON_ALLOW_NO_OPEN_POSITION
    )

    pending_count = observations.get("PENDING_ORDINARY_COUNT")
    algo_outcome = str(observations.get("CATEGORY_C_OUTCOME") or "")
    pending_blocking = (
        isinstance(pending_count, int) and pending_count > 0
    ) or algo_outcome == "TARGET_CATEGORY_C_OBSERVED"

    max_buy = _decimal_or_none(observations.get("MAX_BUY_RAW"))
    max_sell = _decimal_or_none(observations.get("MAX_SELL_RAW"))
    if max_buy is None or max_sell is None:
        venue_capacity = VENUE_CAPACITY_UNPROVEN
    elif max_buy > 0 or max_sell > 0:
        venue_capacity = VENUE_CAPACITY_POSITIVE
    else:
        venue_capacity = VENUE_CAPACITY_ZERO

    avail_status = str(observations.get("AVAIL_EQ_STATUS") or "")
    avail_eq = _decimal_or_none(observations.get("AVAIL_EQ_RAW"))
    funding_observed_positive = (
        avail_status == AVAIL_EQ_STATUS_OBSERVED and avail_eq is not None and avail_eq > 0
    )
    funding_observed_zero = (
        avail_status == AVAIL_EQ_STATUS_OBSERVED and avail_eq is not None and avail_eq == 0
    )

    if venue_capacity == VENUE_CAPACITY_ZERO:
        qty = QTY_BLOCKED_CAPACITY
    elif funding_observed_zero:
        qty = QTY_BLOCKED_FUNDING
    elif venue_capacity == VENUE_CAPACITY_POSITIVE and funding_observed_positive:
        qty = QTY_POTENTIALLY_ADMISSIBLE
    else:
        qty = QTY_UNPROVEN

    required_gate_ok = {
        "INSTRUMENT_STATE": bool(observations.get("INSTRUMENT_STATE_OK")),
        "PRICE_BAND": bool(observations.get("PRICE_BAND_OK")),
        "TICKER": bool(observations.get("TICKER_OK")),
        "LEVERAGE": bool(observations.get("LEVERAGE_OK")),
        "MAX_SIZE": bool(observations.get("MAX_SIZE_OK")),
        "MAX_AVAILABLE": bool(observations.get("MAX_AVAILABLE_OK")),
        "AVAILABLE_MARGIN": bool(observations.get("AVAILABLE_MARGIN_OK")),
        "POS_MODE_OBSERVED": pos_mode_matches_required,
        "ACCOUNT_CONFIG": bool(observations.get("ACCOUNT_CONFIG_OK")),
        "POSITIONS": bool(observations.get("POSITIONS_OK")),
        "PENDING_ORDINARY": bool(observations.get("PENDING_ORDINARY_OK")),
        "CATEGORY_C": bool(observations.get("CATEGORY_C_OK")),
    }
    pretrade_observations_ok = all(required_gate_ok.values())
    pretrade_gates_ready = pretrade_observations_ok and not pending_blocking

    funding_exposure_ready = (
        funding_observed_positive
        and existing_exposure_clear
        and not pending_blocking
        and venue_capacity == VENUE_CAPACITY_POSITIVE
    )

    gaps: list[str] = []
    if not identity_ready:
        gaps.append("ACCOUNT_IDENTITY")
    if not pos_mode["POSITION_MODE_READY"]:
        gaps.append("POSITION_MODE")
    if not pretrade_observations_ok:
        gaps.append("PRETRADE_GATES")
    if qty in {QTY_BLOCKED_CAPACITY, QTY_BLOCKED_FUNDING, QTY_UNPROVEN}:
        gaps.append("FUNDING_OR_CAPACITY")
    if existing_exposure_blocked or pending_blocking:
        gaps.append("EXISTING_EXPOSURE")

    unique_gaps = list(dict.fromkeys(gaps))
    if not unique_gaps:
        verdict = CREATE_READINESS_READY
    elif len(unique_gaps) > 1:
        verdict = CREATE_READINESS_BLOCKED_MULTIPLE
    elif unique_gaps[0] == "POSITION_MODE":
        verdict = CREATE_READINESS_BLOCKED_POSITION_MODE
    elif unique_gaps[0] == "FUNDING_OR_CAPACITY":
        verdict = CREATE_READINESS_BLOCKED_FUNDING
    elif unique_gaps[0] == "EXISTING_EXPOSURE":
        verdict = CREATE_READINESS_BLOCKED_EXPOSURE
    elif unique_gaps[0] == "ACCOUNT_IDENTITY":
        verdict = CREATE_READINESS_BLOCKED_IDENTITY
    elif unique_gaps[0] == "PRETRADE_GATES":
        verdict = CREATE_READINESS_BLOCKED_PRETRADE
    else:
        verdict = CREATE_READINESS_NOT_DETERMINABLE

    freshness: dict[str, str] = {
        "CREATE_ACCOUNT_IDENTITY": (
            FRESHNESS_SENDTIME_REUSABLE if identity_ready else FRESHNESS_UNPROVEN
        ),
        "POS_MODE": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED if pos_mode_matches_required else FRESHNESS_UNPROVEN
        ),
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS": FRESHNESS_UNPROVEN,
        "ACCOUNT_MODE_ACCTLV": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("ACCOUNT_CONFIG_OK")
            else FRESHNESS_UNPROVEN
        ),
        "POSITIONS": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("POSITIONS_OK")
            else FRESHNESS_UNPROVEN
        ),
        "LEVERAGE": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("LEVERAGE_OK")
            else FRESHNESS_UNPROVEN
        ),
        "AVAILABLE_MARGIN": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("AVAILABLE_MARGIN_OK")
            else FRESHNESS_UNPROVEN
        ),
        "MAX_AVAILABLE": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("MAX_AVAILABLE_OK")
            else FRESHNESS_UNPROVEN
        ),
        "MAX_SIZE": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("MAX_SIZE_OK")
            else FRESHNESS_UNPROVEN
        ),
        "INSTRUMENT_METADATA": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("INSTRUMENT_STATE_OK")
            else FRESHNESS_UNPROVEN
        ),
        "PRICE_BAND": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("PRICE_BAND_OK")
            else FRESHNESS_UNPROVEN
        ),
        "TICKER": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("TICKER_OK")
            else FRESHNESS_UNPROVEN
        ),
        "PENDING_ORDINARY": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("PENDING_ORDINARY_OK")
            else FRESHNESS_UNPROVEN
        ),
        "PENDING_ALGO": (
            FRESHNESS_SENDTIME_REFRESH_REQUIRED
            if observations.get("CATEGORY_C_OK")
            else FRESHNESS_UNPROVEN
        ),
        "FUNDING_ACCOUNT": FRESHNESS_NOT_APPLICABLE,
    }

    return {
        "CREATE_ACCOUNT_IDENTITY_READY": identity_ready,
        "ACCOUNT_UID_BOUND_MATCH": identity_match,
        "POS_MODE_RAW": pos_mode_observed,
        "POS_MODE_MATCHES_REQUIRED_NET_MODE": pos_mode_matches_required,
        **pos_mode,
        "PRETRADE_GATES_READY": pretrade_gates_ready,
        "PRETRADE_GATE_DETAIL": required_gate_ok,
        "FUNDING_EXPOSURE_READY": funding_exposure_ready,
        "FUNDING_GET_REQUIRED": FUNDING_GET_REQUIRED,
        "FUNDING_GET_NOT_REQUIRED_REASON": FUNDING_GET_NOT_REQUIRED_REASON,
        "VENUE_NONZERO_CAPACITY": venue_capacity,
        "CURRENT_ROUTE_C_QUANTITY_ADMISSIBILITY": qty,
        "PREREQUISITE_08_CLOSED": prerequisite_08_closed,
        "TARGET_POSITION_STATE": classifier_state,
        "OPEN_POSITION_CAP_REASON": cap_reason,
        "EXISTING_EXPOSURE_CLEAR": existing_exposure_clear,
        "EXISTING_EXPOSURE_BLOCKED": existing_exposure_blocked,
        "PENDING_BLOCKING": pending_blocking,
        "MAX_POSITIONS_EFFECTIVE": POSITION_COUNT_LIMIT,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CREATE_READINESS_AFTER_FRESH_EVIDENCE": verdict,
        "CREATE_READINESS_GAPS": unique_gaps,
        "FRESHNESS_MATRIX": freshness,
        "CURRENT_PRODUCTIVE_WIRE_REACHABLE": False,
        "CREATE_PATH_CURRENTLY_AUTHORIZED": False,
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE": True,
        "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE": False,
    }

"""Adjudicate post-Z2DR maximum-safe-leverage read-only runtime evidence."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_FAIL_CLOSED as ROUTE_C_POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS as ROUTE_C_POSITION_MODE_SUBMIT_BODY_SEMANTICS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAIL_EQ_STATUS_OBSERVED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_REQUIRED_VALUE,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.constants_v1 import (
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    OBSERVATION_AUTH_FAILED,
    OBSERVATION_NOT_EXECUTED,
    OBSERVATION_NOT_OBSERVED,
    OBSERVATION_NOT_PROVEN,
    OBSERVATION_OBSERVED,
    OBSERVATION_PROVEN,
    OBSERVATION_SATISFIED,
    OBSERVATION_UNSATISFIED,
    TARGET_INSTRUMENT_ID,
    Z2DR_G_POSMODE_RESULT_CLASS,
    Z2DR_G_POSMODE_STATUS,
    Z2DR_G_POSMODE_STATUS_CLOSED_AS,
)


def _decimal_or_none(raw: Any) -> Decimal | None:
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _endpoint_auth_failed(records: Mapping[str, Any], path: str) -> bool:
    for item in records.get("REQUESTS") or []:
        if str(item.get("ENDPOINT") or "") != path:
            continue
        if str(item.get("PARSER_RESULT") or "") == "AUTH_FAILED":
            return True
        http_status = item.get("HTTP_STATUS")
        if http_status in {401, 403}:
            return True
        okx_code = str(item.get("OKX_CODE") or "")
        if okx_code == "50110":
            return True
    return False


def _endpoint_executed(records: Mapping[str, Any], path: str) -> bool:
    return any(str(item.get("ENDPOINT") or "") == path for item in records.get("REQUESTS") or [])


def adjudicate_runtime_read_only_evidence_v1(
    *,
    observations: Mapping[str, Any],
    snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map fresh GET observations to Z2DR blocker DAG without semantic overclaim."""
    records = snapshot or {}
    auth_balance_failed = _endpoint_auth_failed(records, "/api/v5/account/balance")
    auth_positions_failed = _endpoint_auth_failed(records, "/api/v5/account/positions")
    auth_config_failed = _endpoint_auth_failed(records, "/api/v5/account/config")
    auth_max_size_failed = _endpoint_auth_failed(records, "/api/v5/account/max-size")
    auth_leverage_failed = _endpoint_auth_failed(records, "/api/v5/account/leverage-info")

    classifier_state = str(observations.get("TARGET_POSITION_STATE") or "")
    if auth_positions_failed:
        p08_status = OBSERVATION_AUTH_FAILED
        p08_proven = False
        target_position_observation = OBSERVATION_AUTH_FAILED
    elif classifier_state == TARGET_POSITION_NONZERO_PROVEN:
        p08_status = OBSERVATION_PROVEN
        p08_proven = True
        target_position_observation = TARGET_POSITION_NONZERO_PROVEN
    elif classifier_state in {TARGET_POSITION_NOT_OBSERVED, TARGET_POSITION_ZERO_PROVEN, ""}:
        p08_status = OBSERVATION_NOT_PROVEN
        p08_proven = False
        target_position_observation = classifier_state or OBSERVATION_NOT_OBSERVED
    else:
        p08_status = OBSERVATION_NOT_OBSERVED
        p08_proven = False
        target_position_observation = classifier_state or OBSERVATION_NOT_OBSERVED

    avail_status = str(observations.get("AVAIL_EQ_STATUS") or "")
    avail_eq = _decimal_or_none(observations.get("AVAIL_EQ_RAW"))
    if auth_balance_failed:
        available_margin_current = OBSERVATION_AUTH_FAILED
    elif avail_status == AVAIL_EQ_STATUS_OBSERVED and avail_eq is not None:
        available_margin_current = OBSERVATION_OBSERVED
    elif _endpoint_executed(records, "/api/v5/account/balance"):
        available_margin_current = OBSERVATION_NOT_OBSERVED
    else:
        available_margin_current = OBSERVATION_NOT_EXECUTED

    max_buy = _decimal_or_none(observations.get("MAX_BUY_RAW"))
    max_sell = _decimal_or_none(observations.get("MAX_SELL_RAW"))
    if auth_max_size_failed:
        max_available_current = OBSERVATION_AUTH_FAILED
    elif max_buy is not None and max_sell is not None:
        max_available_current = OBSERVATION_OBSERVED
    elif parsed_skipped := observations.get("MAX_AVAILABLE_SKIPPED"):
        max_available_current = (
            OBSERVATION_NOT_EXECUTED if parsed_skipped else OBSERVATION_NOT_OBSERVED
        )
    else:
        max_available_current = OBSERVATION_NOT_OBSERVED

    pos_mode_raw = str(observations.get("POS_MODE_RAW") or "").strip()
    if auth_config_failed:
        position_mode_current = OBSERVATION_AUTH_FAILED
    elif pos_mode_raw:
        position_mode_current = OBSERVATION_OBSERVED
    elif _endpoint_executed(records, "/api/v5/account/config"):
        position_mode_current = OBSERVATION_NOT_OBSERVED
    else:
        position_mode_current = OBSERVATION_NOT_EXECUTED

    if auth_leverage_failed:
        leverage_current = OBSERVATION_AUTH_FAILED
    elif observations.get("LEVERAGE_OK"):
        leverage_current = OBSERVATION_OBSERVED
    elif _endpoint_executed(records, "/api/v5/account/leverage-info"):
        leverage_current = OBSERVATION_NOT_OBSERVED
    else:
        leverage_current = OBSERVATION_NOT_EXECUTED

    margin_mode_current = (
        leverage_current
        if observations.get("LEVERAGE_OK")
        else (OBSERVATION_AUTH_FAILED if auth_leverage_failed else OBSERVATION_NOT_OBSERVED)
    )

    if auth_config_failed:
        account_mode_current = OBSERVATION_AUTH_FAILED
    elif observations.get("ACCOUNT_CONFIG_OK"):
        account_mode_current = OBSERVATION_OBSERVED
    else:
        account_mode_current = OBSERVATION_NOT_OBSERVED

    if observations.get("INSTRUMENT_STATE_OK"):
        instrument_state_current = OBSERVATION_OBSERVED
    elif _endpoint_executed(records, "/api/v5/public/instruments"):
        instrument_state_current = OBSERVATION_NOT_OBSERVED
    else:
        instrument_state_current = OBSERVATION_NOT_EXECUTED

    if observations.get("PRICE_BAND_OK"):
        price_limit_current = OBSERVATION_OBSERVED
    elif _endpoint_executed(records, "/api/v5/public/price-limit"):
        price_limit_current = OBSERVATION_NOT_OBSERVED
    else:
        price_limit_current = OBSERVATION_NOT_EXECUTED

    pos_mode_matches = pos_mode_raw == POS_MODE_REQUIRED_VALUE
    venue_capacity_zero = (
        max_buy is not None and max_sell is not None and max_buy == 0 and max_sell == 0
    )
    venue_capacity_positive = (
        max_buy is not None and max_sell is not None and (max_buy > 0 or max_sell > 0)
    )
    funding_positive = (
        avail_status == AVAIL_EQ_STATUS_OBSERVED and avail_eq is not None and avail_eq > 0
    )

    blocker_updates: dict[str, dict[str, Any]] = {
        "G-POSMODE": {
            "prior_status": "CLOSED_FAIL_CLOSED",
            "current_status": "CLOSED_FAIL_CLOSED",
            "runtime_get_closable": False,
            "note": Z2DR_G_POSMODE_RESULT_CLASS,
        },
        "G-POSITION-MODE-READY": {
            "prior_status": "OPEN",
            "current_status": "OPEN",
            "runtime_get_closable": False,
        },
        "G-PRETRADE-AVAILEQ": {
            "prior_status": "OPEN",
            "current_status": (
                "SATISFIED"
                if funding_positive
                else "OPEN"
                if not auth_balance_failed
                else "AUTH_FAILED"
            ),
            "runtime_get_closable": True,
            "fresh_observation": available_margin_current,
        },
        "G-CAPACITY": {
            "prior_status": "OPEN",
            "current_status": (
                "SATISFIED"
                if venue_capacity_positive
                else "OPEN_ZERO"
                if venue_capacity_zero
                else "OPEN"
                if not auth_max_size_failed
                else "AUTH_FAILED"
            ),
            "runtime_get_closable": True,
            "fresh_observation": max_available_current,
        },
        "G-P08": {
            "prior_status": "OPEN",
            "current_status": "SATISFIED" if p08_proven else "OPEN",
            "runtime_get_closable": True,
            "fresh_observation": p08_status,
        },
        "G-FUNDING-EXPOSURE": {
            "prior_status": "OPEN",
            "current_status": (
                "SATISFIED" if funding_positive and venue_capacity_positive else "OPEN"
            ),
            "runtime_get_closable": True,
        },
        "G-WIRE": {
            "prior_status": "OPEN",
            "current_status": "OPEN",
            "runtime_get_closable": False,
            "mutation_required": True,
        },
        "G-CREATE-AUTH": {
            "prior_status": "OPEN",
            "current_status": "OPEN",
            "runtime_get_closable": False,
            "mutation_required": True,
        },
        "G-EXEC-PERMIT": {
            "prior_status": "OPEN",
            "current_status": "OPEN",
            "runtime_get_closable": False,
            "mutation_required": True,
        },
    }

    read_only_closable_remaining = [
        gap_id
        for gap_id, row in blocker_updates.items()
        if row.get("runtime_get_closable")
        and row.get("current_status") in {"OPEN", "OPEN_ZERO", "AUTH_FAILED", "NOT_OBSERVED"}
    ]
    read_only_closable_after = len(read_only_closable_remaining)
    all_planned_gets_executed = bool(records.get("REQUESTS"))
    max_safe_remaining = 0 if all_planned_gets_executed else read_only_closable_after
    mutation_required_open = sum(
        1
        for row in blocker_updates.values()
        if row.get("mutation_required") and row.get("current_status") == "OPEN"
    )
    offline_closed = sum(
        1
        for row in blocker_updates.values()
        if str(row.get("current_status") or "").startswith("CLOSED")
    )
    create_path_blocker_count = sum(
        1
        for row in blocker_updates.values()
        if row.get("current_status") not in {"SATISFIED", "CLOSED_FAIL_CLOSED"}
    )

    return {
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN": p08_proven,
        "EXECUTION_PREREQUISITE_08_STATUS": (
            "PASS_TARGET_POSITION_NONZERO_OBSERVED_THIS_WINDOW"
            if p08_proven
            else "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"
        ),
        "TARGET_POSITION_OBSERVATION": target_position_observation,
        "AVAILABLE_MARGIN_CURRENT": available_margin_current,
        "MAX_AVAILABLE_CURRENT": max_available_current,
        "POSITION_MODE_CURRENT": position_mode_current,
        "POS_MODE_RAW": pos_mode_raw,
        "POS_MODE_MATCHES_REQUIRED_NET_MODE": pos_mode_matches,
        "LEVERAGE_CURRENT": leverage_current,
        "MARGIN_MODE_CURRENT": margin_mode_current,
        "ACCOUNT_MODE_CURRENT": account_mode_current,
        "INSTRUMENT_STATE_CURRENT": instrument_state_current,
        "PRICE_LIMIT_CURRENT": price_limit_current,
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS": ROUTE_C_POSITION_MODE_SUBMIT_BODY_SEMANTICS,
        "POSITION_MODE_FAIL_CLOSED": ROUTE_C_POSITION_MODE_FAIL_CLOSED,
        "POSITION_MODE_READY": False,
        "GET_POSMODE_IS_NOT_SUBMIT_BODY_PROOF": True,
        "G_POSMODE_STATUS": Z2DR_G_POSMODE_STATUS,
        "G_POSMODE_STATUS_CLOSED_AS": Z2DR_G_POSMODE_STATUS_CLOSED_AS,
        "G_POSMODE_RESULT_CLASS": Z2DR_G_POSMODE_RESULT_CLASS,
        "PREREQUISITE_08_CLOSED": p08_proven,
        "BLOCKER_UPDATES": blocker_updates,
        "CREATE_PATH_BLOCKER_COUNT": create_path_blocker_count,
        "READ_ONLY_CLOSABLE_BLOCKER_COUNT_AFTER_GETS": read_only_closable_after,
        "REMAINING_MUTATION_REQUIRED_BLOCKER_COUNT": mutation_required_open + 2,
        "MAX_SAFE_READ_ONLY_RUNTIME_BUNDLE_REMAINING": max_safe_remaining,
        "OFFLINE_CLOSED_BLOCKER_COUNT": offline_closed,
        "EARLIEST_UNRESOLVED_DEPENDENCY": (
            "EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC"
            if p08_proven
            else CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY
        ),
        "CREATE_PATH_CURRENTLY_AUTHORIZED": False,
        "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE": False,
        "CURRENT_PRODUCTIVE_WIRE_REACHABLE": False,
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE": True,
        "FUNDING_EXPOSURE_SATISFIED": blocker_updates["G-FUNDING-EXPOSURE"]["current_status"]
        == "SATISFIED",
        "VENUE_CAPACITY_ZERO": venue_capacity_zero,
        "VENUE_CAPACITY_POSITIVE": venue_capacity_positive,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "EMPTY_DATA_IS_NOT_ZERO": True,
        "EMPTY_DATA_IS_NOT_PREREQUISITE_08_ZERO": True,
    }

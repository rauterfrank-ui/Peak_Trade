"""CURRENT occupancy classify and C1-gate tokens.

Relocation of non-credential classify/gate semantics. Not a credential
owner. Does not load vault material, sign venue requests, or borrow
ephemeral secrets.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
)

V5_OWNER_GO = (
    "OWNER_GO_CONDITION_GATED_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_C1_BOUNDARY_1789527780_V1"
)
PREVIOUS_C1_VENUE_EVENT_TIME = 1789527780.0
C1_GATE_NATIVE_ID = "0G-USDT-SWAP"
C1_GATE_BAR = "1m"
POST_NEXT_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
NON_EXECUTABLE_NEXT_OWNER_GO = (
    "SEPARATE_OWNER_GO_FOR_NEXT_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_FROM_PERSISTED_CURSOR"
)
OCCUPANCY_NEXT_OWNER_GO = "SEPARATE_OWNER_GO_FOR_CURRENT_OCCUPANCY_DISPOSITION_AFTER_FRESH_REPROOF"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


def _token(value: bool) -> str:
    return TRUE_TOKEN if value is True else FALSE_TOKEN


def _newest_finalized_1m_identity_v1(payload: Any) -> dict[str, Any]:
    closes, last_ts = extract_finalized_candle_closes_v1(payload)
    newest: dict[str, Any] = {
        "finalized_close_count": len(closes),
        "newest_finalized_venue_event_time": last_ts,
        "confirm": "1" if last_ts is not None else "",
        "close": closes[-1] if closes else None,
    }
    if not isinstance(payload, Mapping):
        return newest
    rows = payload.get("data")
    if not isinstance(rows, list) or last_ts is None:
        return newest
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 9:
            continue
        if str(row[8] or "").strip() != "1":
            continue
        try:
            ts = float(row[0]) / 1000.0
        except (TypeError, ValueError):
            continue
        if ts == float(last_ts):
            newest["ts_ms"] = row[0]
            newest["close"] = row[4]
            newest["confirm"] = "1"
            break
    return newest


def _evaluate_c1_gate_v1(
    *,
    payload: Any,
    http_status: int = 0,
    error_class: str = "",
    get_performed: bool = False,
    body_sha256: str = "",
) -> dict[str, str]:
    identity = _newest_finalized_1m_identity_v1(payload)
    last_ts = identity.get("newest_finalized_venue_event_time")
    satisfied = last_ts is not None and float(last_ts) > float(PREVIOUS_C1_VENUE_EVENT_TIME)
    return {
        "CONDITION_GATE": "SATISFIED" if satisfied else "NOT_YET_SATISFIED",
        "PREVIOUS_C1_VENUE_EVENT_TIME": str(PREVIOUS_C1_VENUE_EVENT_TIME),
        "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME": "" if last_ts is None else str(last_ts),
        "NEW_C1_EVIDENCE_AVAILABLE": _token(satisfied),
        "C1_GATE_NATIVE_ID": C1_GATE_NATIVE_ID,
        "C1_GATE_BAR": C1_GATE_BAR,
        "CONFIRM": str(identity.get("confirm") or ""),
        "CLOSE": str(identity.get("close") or ""),
        "TS_MS": str(identity.get("ts_ms") or ""),
        "FINALIZED_CLOSE_COUNT": str(identity.get("finalized_close_count") or 0),
        "GET_PERFORMED": _token(get_performed),
        "HTTP_STATUS": str(http_status),
        "ERROR_CLASS": error_class,
        "BODY_SHA256": body_sha256,
        "AUTH_HEADER_SENT": FALSE_TOKEN,
        "POST_COUNT": "0",
        "SELECTION_FORCED": FALSE_TOKEN,
    }


def _data_rows(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _open_nonzero_position_rows(payload: Any) -> list[Mapping[str, Any]]:
    open_rows: list[Mapping[str, Any]] = []
    for row in _data_rows(payload):
        text = str(row.get("pos") or "").strip()
        if not text:
            continue
        try:
            if Decimal(text) == 0:
                continue
        except Exception:
            continue
        open_rows.append(row)
    return open_rows


def _classify_occupancy_v1(
    *,
    positions_payload: Any,
    pending_payload: Any,
    config_payload: Any,
    positions_error: str,
    pending_error: str,
    config_error: str,
) -> dict[str, str]:
    config_rows = _data_rows(config_payload)
    config_row = config_rows[0] if config_rows else {}
    facts = {
        "POSITIONS_GET_ERROR": positions_error,
        "PENDING_GET_ERROR": pending_error,
        "CONFIG_GET_ERROR": config_error,
        "POSITIONS_CODE": str(positions_payload.get("code") or "")
        if isinstance(positions_payload, Mapping)
        else "",
        "PENDING_CODE": str(pending_payload.get("code") or "")
        if isinstance(pending_payload, Mapping)
        else "",
        "CONFIG_CODE": str(config_payload.get("code") or "")
        if isinstance(config_payload, Mapping)
        else "",
        "POSITION_ROW_COUNT": str(len(_data_rows(positions_payload))),
        "OPEN_POSITION_COUNT": "0",
        "PENDING_ROW_COUNT": str(len(_data_rows(pending_payload))),
        "OCCUPANCY_STATUS": "UNKNOWN",
        "PENDING_ORDERS_STATUS": "UNKNOWN",
        "CONFIG_ACCTLV": str(config_row.get("acctLv") or ""),
        "CONFIG_POS_MODE": str(config_row.get("posMode") or ""),
        "OPEN_POSITION_INST_IDS": "",
        "PENDING_INST_IDS": "",
        "OCCUPANCY_ABSENT": FALSE_TOKEN,
    }
    if positions_error or not isinstance(positions_payload, Mapping):
        facts["OCCUPANCY_STATUS"] = f"POSITIONS_GET_FAIL_CLOSED:{positions_error or 'MISSING'}"
        return facts
    if pending_error or not isinstance(pending_payload, Mapping):
        facts["PENDING_ORDERS_STATUS"] = f"PENDING_GET_FAIL_CLOSED:{pending_error or 'MISSING'}"
        facts["OCCUPANCY_STATUS"] = facts["PENDING_ORDERS_STATUS"]
        return facts
    if config_error or not isinstance(config_payload, Mapping):
        facts["OCCUPANCY_STATUS"] = f"CONFIG_GET_FAIL_CLOSED:{config_error or 'MISSING'}"
        return facts
    open_rows = _open_nonzero_position_rows(positions_payload)
    pending_rows = _data_rows(pending_payload)
    facts["OPEN_POSITION_COUNT"] = str(len(open_rows))
    facts["OPEN_POSITION_INST_IDS"] = ",".join(
        str(row.get("instId") or "") for row in open_rows if str(row.get("instId") or "")
    )
    facts["PENDING_INST_IDS"] = ",".join(
        str(row.get("instId") or "") for row in pending_rows if str(row.get("instId") or "")
    )
    if open_rows:
        facts["OCCUPANCY_STATUS"] = "OCCUPANCY_PRESENT"
        facts["OCCUPANCY_ABSENT"] = FALSE_TOKEN
    else:
        facts["OCCUPANCY_STATUS"] = "OCCUPANCY_ABSENT"
        facts["OCCUPANCY_ABSENT"] = TRUE_TOKEN
    facts["PENDING_ORDERS_STATUS"] = "PENDING_ORDERS_PRESENT" if pending_rows else "NONE_OBSERVED"
    return facts

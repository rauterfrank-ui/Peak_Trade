"""Pre-submit exchange-state guards for §11.13.5 (open orders/positions/recovery)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)


class LiveCanaryPreSubmitStateError(RuntimeError):
    """Fail-closed pre-submit exchange-state violation."""


def _rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_PAYLOAD_NOT_OK")
    data = payload.get("data")
    if data is None:
        return []
    if not isinstance(data, list):
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_DATA_NOT_LIST")
    return [row for row in data if isinstance(row, Mapping)]


def _pos_size(row: Mapping[str, Any]) -> Decimal:
    raw = row.get("pos") or row.get("posSize") or "0"
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryPreSubmitStateError("POSITION_SIZE_UNPARSEABLE") from exc


def evaluate_pre_submit_exchange_state_v1(
    *,
    positions_payload: Mapping[str, Any],
    pending_orders_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> dict[str, Any]:
    positions = _rows(positions_payload)
    pending = _rows(pending_orders_payload)
    open_positions = [
        row
        for row in positions
        if str(row.get("instId") or "") == instrument_id and _pos_size(row) != 0
    ]
    open_orders = [
        row for row in pending if str(row.get("instId") or row.get("instID") or "") == instrument_id
    ]
    blockers: list[str] = []
    if open_positions:
        blockers.append("OPEN_POSITION_PRESENT")
    if open_orders:
        blockers.append("OPEN_ORDER_PRESENT")
    if blockers:
        raise LiveCanaryPreSubmitStateError(",".join(blockers))
    return {
        "ok": True,
        "open_position_count": 0,
        "open_order_count": 0,
        "instrument_id": instrument_id,
        "recovery_state_clear": True,
    }


def classify_unknown_submit_from_exchange_v1(
    *,
    pending_orders_payload: Mapping[str, Any],
    history_payload: Mapping[str, Any] | None,
    clordid: str,
) -> str:
    """Exchange truth after ambiguous POST. Never implies a second submit."""
    pending = _rows(pending_orders_payload)
    if any(str(row.get("clOrdId") or "") == clordid for row in pending):
        return "UNKNOWN_SUBMIT_RESOLVED_PENDING"
    if history_payload is not None:
        history = _rows(history_payload)
        if any(str(row.get("clOrdId") or "") == clordid for row in history):
            return "UNKNOWN_SUBMIT_RESOLVED_HISTORY"
    return "UNKNOWN_SUBMIT_UNRESOLVED_HALT"

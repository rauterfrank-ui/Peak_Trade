"""Final exchange reconcile/cleanup hook for productive §11.12.8 campaign path.

Offline/fixture-capable. Does not invent exchange truth. Successful seal
requires explicit proven final open-order/position counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


class ActualStartFinalReconcileError(RuntimeError):
    """Fail-closed final reconcile/cleanup violation."""


TransportGetFn = Callable[[str], Mapping[str, Any]]
CancelFn = Callable[[str], Mapping[str, Any]]


@dataclass
class FinalExchangeReconcileCleanupRecordV1:
    ok: bool = False
    pending_orders_read: bool = False
    positions_read: bool = False
    cancel_attempt_count: int = 0
    cancel_ack_count: int = 0
    final_open_order_count: int | None = None
    final_open_position_count: int | None = None
    unresolved: bool = False
    reason: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "pending_orders_read": self.pending_orders_read,
            "positions_read": self.positions_read,
            "cancel_attempt_count": self.cancel_attempt_count,
            "cancel_ack_count": self.cancel_ack_count,
            "FINAL_OPEN_ORDER_COUNT": self.final_open_order_count,
            "FINAL_OPEN_POSITION_COUNT": self.final_open_position_count,
            "unresolved": self.unresolved,
            "reason": self.reason,
            "events": list(self.events),
        }


def exchange_payload_from_transport_result_v1(
    result: Mapping[str, Any],
    *,
    allow_empty_without_wire: bool = False,
) -> dict[str, Any]:
    """Normalize transport/client results into an exchange JSON object with data[]."""
    body = result.get("response_body")
    if isinstance(body, dict):
        return dict(body)
    if "data" in result:
        return dict(result)
    if allow_empty_without_wire and not bool(result.get("wire_sent")):
        return {"data": []}
    raise ActualStartFinalReconcileError("EXCHANGE_PAYLOAD_UNPROVEN")


def _extract_pending_ids(payload: Mapping[str, Any]) -> list[str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        oid = str(row.get("ordId") or row.get("clOrdId") or "").strip()
        if oid:
            out.append(oid)
    return out


def _count_open_positions(payload: Mapping[str, Any]) -> int:
    data = payload.get("data")
    if not isinstance(data, list):
        return 0
    count = 0
    for row in data:
        if not isinstance(row, dict):
            continue
        try:
            if float(row.get("pos") or 0) != 0.0:
                count += 1
        except (TypeError, ValueError):
            # Ambiguous position payload => unresolved at caller.
            raise ActualStartFinalReconcileError("POSITION_PAYLOAD_UNPARSEABLE")
    return count


def run_final_exchange_reconcile_cleanup_v1(
    *,
    ephemeral_campaign_write_gate_pass: bool,
    get_pending_orders: TransportGetFn,
    get_positions: TransportGetFn,
    cancel_order: CancelFn | None = None,
    campaign_client_order_ids: tuple[str, ...] | list[str] | None = None,
    require_zero_open: bool = True,
) -> FinalExchangeReconcileCleanupRecordV1:
    """Read pending/positions, cancel campaign opens when authorized, bind finals."""
    record = FinalExchangeReconcileCleanupRecordV1()
    if not ephemeral_campaign_write_gate_pass and cancel_order is not None:
        # Read-only reconcile still allowed; mutation cancel requires gate.
        cancel_order = None

    try:
        pending = dict(get_pending_orders("/api/v5/trade/orders-pending"))
        record.pending_orders_read = True
        record.events.append({"event": "pending_orders_read", "ok": True})
    except Exception as exc:  # noqa: BLE001
        record.unresolved = True
        record.reason = f"PENDING_ORDERS_READ_FAILED:{type(exc).__name__}"
        raise ActualStartFinalReconcileError(record.reason) from exc

    pending_ids = _extract_pending_ids(pending)
    campaign_ids = {str(x) for x in (campaign_client_order_ids or ()) if str(x)}
    if campaign_ids:
        targets = [oid for oid in pending_ids if oid in campaign_ids]
        if not targets:
            targets = list(pending_ids)
    else:
        targets = list(pending_ids)

    if targets and cancel_order is None and require_zero_open:
        record.unresolved = True
        record.reason = "OPEN_ORDERS_PRESENT_WITHOUT_CANCEL_AUTHORITY"
        raise ActualStartFinalReconcileError(record.reason)

    for oid in targets:
        if cancel_order is None:
            break
        if not ephemeral_campaign_write_gate_pass:
            record.unresolved = True
            record.reason = "CANCEL_REQUIRES_EPHEMERAL_WRITE_GATE_PASS"
            raise ActualStartFinalReconcileError(record.reason)
        record.cancel_attempt_count += 1
        try:
            cancel_result = dict(cancel_order(oid))
        except Exception as exc:  # noqa: BLE001
            record.unresolved = True
            record.reason = f"CANCEL_FAILED:{oid}:{type(exc).__name__}"
            raise ActualStartFinalReconcileError(record.reason) from exc
        if bool(cancel_result.get("ok") or cancel_result.get("order_acknowledged")):
            record.cancel_ack_count += 1
        elif cancel_result.get("exchange_rejected"):
            record.events.append({"event": "cancel_rejected", "order_id": oid})
        else:
            record.unresolved = True
            record.reason = f"CANCEL_STATE_UNPROVEN:{oid}"
            raise ActualStartFinalReconcileError(record.reason)
        record.events.append({"event": "cancel_attempt", "order_id": oid})

    # Re-read pending after cancels.
    try:
        pending_after = dict(get_pending_orders("/api/v5/trade/orders-pending"))
        final_orders = len(_extract_pending_ids(pending_after))
        record.final_open_order_count = final_orders
    except Exception as exc:  # noqa: BLE001
        record.unresolved = True
        record.reason = f"PENDING_ORDERS_REREAD_FAILED:{type(exc).__name__}"
        raise ActualStartFinalReconcileError(record.reason) from exc

    try:
        positions = dict(get_positions("/api/v5/account/positions"))
        record.positions_read = True
        record.final_open_position_count = _count_open_positions(positions)
        record.events.append({"event": "positions_read", "ok": True})
    except ActualStartFinalReconcileError:
        raise
    except Exception as exc:  # noqa: BLE001
        record.unresolved = True
        record.reason = f"POSITIONS_READ_FAILED:{type(exc).__name__}"
        raise ActualStartFinalReconcileError(record.reason) from exc

    if record.final_open_order_count is None or record.final_open_position_count is None:
        record.unresolved = True
        record.reason = "FINAL_OPEN_STATE_NOT_BOUND"
        raise ActualStartFinalReconcileError(record.reason)

    if require_zero_open and (
        record.final_open_order_count != 0 or record.final_open_position_count != 0
    ):
        record.unresolved = True
        record.reason = (
            "FINAL_OPEN_STATE_NONZERO:"
            f"orders={record.final_open_order_count}:positions={record.final_open_position_count}"
        )
        raise ActualStartFinalReconcileError(record.reason)

    record.ok = True
    record.reason = "FINAL_EXCHANGE_RECONCILE_CLEANUP_PASS"
    return record


def assert_seal_allowed_after_final_reconcile_v1(
    *,
    reconcile: FinalExchangeReconcileCleanupRecordV1 | Mapping[str, Any] | None,
) -> None:
    if reconcile is None:
        raise ActualStartFinalReconcileError("FINAL_RECONCILE_REQUIRED_BEFORE_SEAL")
    payload = reconcile.to_dict() if hasattr(reconcile, "to_dict") else dict(reconcile)
    if not bool(payload.get("ok")):
        raise ActualStartFinalReconcileError("FINAL_RECONCILE_NOT_OK_SEAL_FORBIDDEN")
    if payload.get("FINAL_OPEN_ORDER_COUNT") is None:
        raise ActualStartFinalReconcileError("FINAL_OPEN_ORDER_COUNT_REQUIRED_FOR_SEAL")
    if payload.get("FINAL_OPEN_POSITION_COUNT") is None:
        raise ActualStartFinalReconcileError("FINAL_OPEN_POSITION_COUNT_REQUIRED_FOR_SEAL")
    if bool(payload.get("unresolved")):
        raise ActualStartFinalReconcileError("FINAL_RECONCILE_UNRESOLVED_SEAL_FORBIDDEN")

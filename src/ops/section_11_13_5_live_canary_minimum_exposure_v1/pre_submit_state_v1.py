"""Pre-submit exchange-state guards for §11.13.5 (open orders/positions/recovery)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)


class LiveCanaryPreSubmitStateError(RuntimeError):
    """Fail-closed pre-submit exchange-state violation."""


class LiveCanaryPositionObservationError(RuntimeError):
    """Fail-closed observed-position flatten-candidate violation."""


TARGET_POSITION_NOT_OBSERVED = "TARGET_POSITION_NOT_OBSERVED"
TARGET_POSITION_ZERO_PROVEN = "TARGET_POSITION_ZERO_PROVEN"
TARGET_POSITION_NONZERO_PROVEN = "TARGET_POSITION_NONZERO_PROVEN"
TARGET_POSITION_UNKNOWN = "UNKNOWN"

EMPTY_DATA_IS_NOT_ZERO = True
ABSENT_TARGET_ROW_IS_NOT_ZERO = True
ABSENT_TARGET_ROW_IS_NOT_FLAT = True
HTTP_OK_DOES_NOT_PROVE_COMPLETENESS = True
QUERY_COMPLETENESS_PROVEN_DEFAULT = False


@dataclass(frozen=True)
class ObservedTargetPositionFlattenCandidateV1:
    """Offline observation only. Not productive flatten authorization."""

    instrument_id: str
    signed_pos: Decimal
    candidate_flatten_qty: Decimal
    candidate_flatten_side: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "signed_pos": format(self.signed_pos, "f"),
            "candidate_flatten_qty": format(self.candidate_flatten_qty, "f"),
            "candidate_flatten_side": self.candidate_flatten_side,
        }


@dataclass(frozen=True)
class TargetPositionStateClassificationV1:
    """Fail-closed target-position predicate. Never promotes empty or absent to zero."""

    instrument_id: str
    state: str
    signed_pos: str | None
    reason: str
    query_completeness_proven: bool = False
    empty_data_is_zero: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "state": self.state,
            "signed_pos": self.signed_pos,
            "reason": self.reason,
            "query_completeness_proven": self.query_completeness_proven,
            "empty_data_is_zero": self.empty_data_is_zero,
            "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": HTTP_OK_DOES_NOT_PROVE_COMPLETENESS,
        }


def _rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Valid code==0 list envelope. data=None / missing data is not empty."""
    if not isinstance(payload, Mapping):
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_PAYLOAD_NOT_MAPPING")
    if "code" not in payload:
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_CODE_MISSING")
    if str(payload.get("code") or "") != "0":
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_PAYLOAD_NOT_OK")
    if "data" not in payload:
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_DATA_MISSING")
    data = payload["data"]
    if data is None:
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_DATA_NONE")
    if not isinstance(data, list):
        raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_DATA_NOT_LIST")
    rows: list[Mapping[str, Any]] = []
    for row in data:
        if not isinstance(row, Mapping):
            raise LiveCanaryPreSubmitStateError("EXCHANGE_STATE_ROW_NOT_MAPPING")
        rows.append(row)
    return rows


def _pos_size(row: Mapping[str, Any]) -> Decimal:
    raw = row.get("pos") or row.get("posSize") or "0"
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryPreSubmitStateError("POSITION_SIZE_UNPARSEABLE") from exc


def _signed_observed_pos(row: Mapping[str, Any]) -> Decimal:
    if "pos" in row and row["pos"] is not None:
        raw = row["pos"]
    elif "posSize" in row and row["posSize"] is not None:
        raw = row["posSize"]
    else:
        raise LiveCanaryPositionObservationError("POSITION_SIZE_MISSING")
    text = str(raw).strip()
    if not text:
        raise LiveCanaryPositionObservationError("POSITION_SIZE_MISSING")
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryPositionObservationError("POSITION_SIZE_UNPARSEABLE") from exc


def signed_nonzero_positions_by_instrument_v1(
    positions_payload: Mapping[str, Any],
) -> dict[str, Decimal]:
    """Map instId → signed pos for every nonzero row. Ambiguous instIds fail closed."""
    rows = _rows(positions_payload)
    out: dict[str, Decimal] = {}
    seen: dict[str, int] = {}
    for row in rows:
        inst = str(row.get("instId") or "").strip()
        if not inst:
            raise LiveCanaryPositionObservationError("POSITION_INSTID_MISSING")
        seen[inst] = seen.get(inst, 0) + 1
        signed = _signed_observed_pos(row)
        if signed == 0:
            continue
        out[inst] = signed
    for inst, count in seen.items():
        if count != 1:
            raise LiveCanaryPositionObservationError("AMBIGUOUS_TARGET_POSITION_ROWS")
    return out


def open_order_instruments_v1(pending_orders_payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Return instIds of open orders. Malformed pending payloads fail closed."""
    rows = _rows(pending_orders_payload)
    instruments: list[str] = []
    for row in rows:
        inst = str(row.get("instId") or row.get("instID") or "").strip()
        if not inst:
            raise LiveCanaryPreSubmitStateError("OPEN_ORDER_INSTID_MISSING")
        instruments.append(inst)
    return tuple(instruments)


def classify_target_position_state_v1(
    *,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> TargetPositionStateClassificationV1:
    """Classify target position as not-observed, explicit zero, nonzero, or unknown.

    Empty data[] is not zero. data=None / missing data is not empty. A successful
    envelope is not completeness. This classifier never authorizes flatten or live.
    """
    target = str(instrument_id or "").strip()
    if not target:
        return TargetPositionStateClassificationV1(
            instrument_id="",
            state=TARGET_POSITION_UNKNOWN,
            signed_pos=None,
            reason="TARGET_INSTRUMENT_REQUIRED",
        )
    if positions_payload is None:
        return TargetPositionStateClassificationV1(
            instrument_id=target,
            state=TARGET_POSITION_UNKNOWN,
            signed_pos=None,
            reason="POSITIONS_PAYLOAD_MISSING",
        )
    try:
        rows = _rows(positions_payload)
    except LiveCanaryPreSubmitStateError as exc:
        return TargetPositionStateClassificationV1(
            instrument_id=target,
            state=TARGET_POSITION_UNKNOWN,
            signed_pos=None,
            reason=str(exc),
        )
    matching = [row for row in rows if str(row.get("instId") or "").strip() == target]
    if not matching:
        return TargetPositionStateClassificationV1(
            instrument_id=target,
            state=TARGET_POSITION_NOT_OBSERVED,
            signed_pos=None,
            reason="TARGET_INSTRUMENT_NOT_OBSERVED",
        )
    if len(matching) != 1:
        return TargetPositionStateClassificationV1(
            instrument_id=target,
            state=TARGET_POSITION_UNKNOWN,
            signed_pos=None,
            reason="AMBIGUOUS_TARGET_POSITION_ROWS",
        )
    try:
        signed = _signed_observed_pos(matching[0])
    except LiveCanaryPositionObservationError as exc:
        return TargetPositionStateClassificationV1(
            instrument_id=target,
            state=TARGET_POSITION_UNKNOWN,
            signed_pos=None,
            reason=str(exc),
        )
    if signed == 0:
        return TargetPositionStateClassificationV1(
            instrument_id=target,
            state=TARGET_POSITION_ZERO_PROVEN,
            signed_pos=format(signed, "f"),
            reason="ZERO_POSITION_NO_FLATTEN_ORDER",
        )
    return TargetPositionStateClassificationV1(
        instrument_id=target,
        state=TARGET_POSITION_NONZERO_PROVEN,
        signed_pos=format(signed, "f"),
        reason="TARGET_POSITION_NONZERO_PROVEN",
    )


def observe_target_position_flatten_candidate_v1(
    *,
    positions_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> ObservedTargetPositionFlattenCandidateV1:
    """Derive flatten qty/side from a unique observed nonzero target position.

    Submitted Entry quantity is not an input and cannot be authority.
    Empty data[] is TARGET_INSTRUMENT_NOT_OBSERVED, not zero. data=None is
    UNKNOWN, not not-observed. This result is not productive flatten
    authorization.
    """
    classified = classify_target_position_state_v1(
        positions_payload=positions_payload,
        instrument_id=instrument_id,
    )
    if classified.state == TARGET_POSITION_NOT_OBSERVED:
        raise LiveCanaryPositionObservationError("TARGET_INSTRUMENT_NOT_OBSERVED")
    if classified.state == TARGET_POSITION_ZERO_PROVEN:
        raise LiveCanaryPositionObservationError("ZERO_POSITION_NO_FLATTEN_ORDER")
    if classified.state != TARGET_POSITION_NONZERO_PROVEN or classified.signed_pos is None:
        raise LiveCanaryPositionObservationError(classified.reason)
    signed = Decimal(classified.signed_pos)
    abs_qty = abs(signed)
    side = "SELL" if signed > 0 else "BUY"
    return ObservedTargetPositionFlattenCandidateV1(
        instrument_id=classified.instrument_id,
        signed_pos=signed,
        candidate_flatten_qty=abs_qty,
        candidate_flatten_side=side,
    )


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

"""Pure pre-submit admission: would this intent open a second instrument?

Offline, side-effect-free. No network, no exchange client, no config load.
Does not implement sizing, direction, reduceOnly, or hedge/posSide policy.
Does not reuse LiveRiskLimits.check_orders batch-symbol counting or
MAX_POSITIONS_EFFECTIVE selection policy.

Proven OKX net/signed semantics: envelope code=="0", data list, pos/posSize.
Uniqueness of a nonzero instId must be proven; otherwise fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

REASON_ALLOW_NO_OPEN_POSITION = "ALLOW_NO_OPEN_POSITION"
REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN = "ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN"
REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT = "DENY_OTHER_OPEN_INSTRUMENT_PRESENT"
REASON_DENY_AMBIGUOUS_POSITION_ROWS = "DENY_AMBIGUOUS_POSITION_ROWS"
REASON_DENY_INVALID_POSITION_PAYLOAD = "DENY_INVALID_POSITION_PAYLOAD"
REASON_DENY_POSITION_STATE_UNAVAILABLE = "DENY_POSITION_STATE_UNAVAILABLE"

_ALLOW_REASONS = frozenset(
    {
        REASON_ALLOW_NO_OPEN_POSITION,
        REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN,
    }
)


class PreSubmitOpenPositionCapErrorV1(RuntimeError):
    """Fail-closed second-open-instrument admission denial."""

    def __init__(self, reason_code: str, message: str | None = None) -> None:
        self.reason_code = str(reason_code)
        super().__init__(message or self.reason_code)


@dataclass(frozen=True)
class PreSubmitOpenPositionCapDecisionV1:
    admitted: bool
    reason_code: str
    open_instrument_ids: tuple[str, ...]


def _deny(reason_code: str) -> PreSubmitOpenPositionCapDecisionV1:
    return PreSubmitOpenPositionCapDecisionV1(
        admitted=False,
        reason_code=reason_code,
        open_instrument_ids=(),
    )


def _parse_signed_pos(row: Mapping[str, Any]) -> Decimal | None:
    raw = row.get("pos")
    if raw is None:
        raw = row.get("posSize")
    if raw is None or str(raw).strip() == "":
        raw = "0"
    try:
        return Decimal(str(raw).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def evaluate_pre_submit_open_position_cap_v1(
    *,
    target_instrument_id: str,
    positions_payload: Any,
) -> PreSubmitOpenPositionCapDecisionV1:
    """Decide whether a new intent could create a second open instrument.

    A) no nonzero instrument → ALLOW_NO_OPEN_POSITION
    B) only target already open → ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN
       (add/reduce/close/flip remain host rules; this cap invents none)
    C) a different instrument already open → DENY_OTHER_OPEN_INSTRUMENT_PRESENT
    D) ambiguous rows → DENY_AMBIGUOUS_POSITION_ROWS
    E) missing/unproven payload → DENY_POSITION_STATE_UNAVAILABLE
       or DENY_INVALID_POSITION_PAYLOAD
    """
    if positions_payload is None:
        return _deny(REASON_DENY_POSITION_STATE_UNAVAILABLE)
    if not isinstance(positions_payload, Mapping):
        return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)

    target = str(target_instrument_id or "").strip()
    if not target:
        return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)

    if "code" not in positions_payload:
        return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)
    # Proven OKX envelope uses code == "0". Integer 0 is accepted via str().
    if str(positions_payload.get("code")) != "0":
        return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)

    data = positions_payload.get("data")
    if data is None:
        data = []
    if not isinstance(data, list):
        return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)

    sizes_by_inst: dict[str, list[Decimal]] = {}
    for row in data:
        if not isinstance(row, Mapping):
            return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)
        signed = _parse_signed_pos(row)
        if signed is None:
            return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)
        inst = str(row.get("instId") or "").strip()
        if not inst:
            if signed != 0:
                return _deny(REASON_DENY_INVALID_POSITION_PAYLOAD)
            continue
        sizes_by_inst.setdefault(inst, []).append(signed)

    open_ids: list[str] = []
    for inst, sizes in sizes_by_inst.items():
        nonzero = [size for size in sizes if size != 0]
        if len(nonzero) > 1:
            return _deny(REASON_DENY_AMBIGUOUS_POSITION_ROWS)
        if len(sizes) > 1 and nonzero:
            return _deny(REASON_DENY_AMBIGUOUS_POSITION_ROWS)
        if nonzero:
            open_ids.append(inst)

    open_tuple = tuple(open_ids)
    if not open_tuple:
        return PreSubmitOpenPositionCapDecisionV1(
            admitted=True,
            reason_code=REASON_ALLOW_NO_OPEN_POSITION,
            open_instrument_ids=open_tuple,
        )
    others = tuple(inst for inst in open_tuple if inst != target)
    if others:
        return PreSubmitOpenPositionCapDecisionV1(
            admitted=False,
            reason_code=REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT,
            open_instrument_ids=open_tuple,
        )
    return PreSubmitOpenPositionCapDecisionV1(
        admitted=True,
        reason_code=REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN,
        open_instrument_ids=open_tuple,
    )


def assert_pre_submit_open_position_cap_allows_v1(
    *,
    target_instrument_id: str,
    positions_payload: Any,
) -> PreSubmitOpenPositionCapDecisionV1:
    """Raise typed fail-closed error unless the cap admits the intent."""
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=target_instrument_id,
        positions_payload=positions_payload,
    )
    if not decision.admitted or decision.reason_code not in _ALLOW_REASONS:
        raise PreSubmitOpenPositionCapErrorV1(decision.reason_code)
    return decision

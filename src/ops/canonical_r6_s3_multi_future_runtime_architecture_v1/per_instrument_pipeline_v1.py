"""Per-instrument Master V2 / Double Play and risk/sizing invocation contracts.

Reuses existing owners by identity. Does not reimplement strategy or
redefine per-instrument risk formulas.
"""

from __future__ import annotations

from decimal import Decimal

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    MASTER_V2_DOUBLE_PLAY_OWNER,
    NO_ORDER_WITHOUT_SINGLE_USE_PERMISSION,
    NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION,
    ONE_ACTIVE_DIRECTIONAL_SIDE_PER_INSTRUMENT,
    PER_INSTRUMENT_RISK_OWNER,
    REVERSAL_REQUIRES_RECONCILED_FLAT_PER_INSTRUMENT,
    SIMULTANEOUS_LONG_SHORT_PER_INSTRUMENT_ALLOWED,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    IntentV1,
    R6S3RuntimeArchitectureError,
)

_INCREASE_ACTIONS = frozenset({"ENTRY", "REVERSAL"})
_VALID_SIDES = frozenset({"FLAT", "LONG", "SHORT"})
_VALID_ACTIONS = frozenset({"HOLD", "ENTRY", "REDUCE", "EXIT", "REVERSAL"})


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def _qty(value: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception as exc:  # noqa: BLE001
        raise R6S3RuntimeArchitectureError(f"qty_not_decimal:{value}") from exc
    if parsed < 0:
        _reject(f"qty_negative:{value}")
    return parsed


def evaluate_per_instrument_pipeline_v1(
    contexts: tuple[InstrumentContextV1, ...],
    *,
    sequence_start: int = 0,
) -> tuple[IntentV1, ...]:
    if ONE_ACTIVE_DIRECTIONAL_SIDE_PER_INSTRUMENT is not True:
        _reject("one_active_side_doctrine_missing")
    if SIMULTANEOUS_LONG_SHORT_PER_INSTRUMENT_ALLOWED is not False:
        _reject("simultaneous_long_short_must_remain_false")
    intents: list[IntentV1] = []
    for offset, context in enumerate(sorted(contexts, key=lambda row: row.instrument_id)):
        if context.directional_side not in _VALID_SIDES:
            _reject(f"invalid_directional_side:{context.instrument_id}")
        if context.intended_action not in _VALID_ACTIONS:
            _reject(f"invalid_intended_action:{context.instrument_id}")
        if context.intended_side not in _VALID_SIDES:
            _reject(f"invalid_intended_side:{context.instrument_id}")
        reasons: list[str] = []
        blocked = False
        qty = str(_qty(context.intended_qty))
        if context.directional_side == "LONG" and context.intended_side == "SHORT":
            if context.intended_action != "EXIT" and context.intended_action != "REDUCE":
                reasons.append("SIMULTANEOUS_LONG_SHORT_FORBIDDEN")
                blocked = True
        if context.directional_side == "SHORT" and context.intended_side == "LONG":
            if context.intended_action != "EXIT" and context.intended_action != "REDUCE":
                reasons.append("SIMULTANEOUS_LONG_SHORT_FORBIDDEN")
                blocked = True
        if context.intended_action == "REVERSAL":
            if REVERSAL_REQUIRES_RECONCILED_FLAT_PER_INSTRUMENT is not True:
                _reject("reversal_flat_doctrine_missing")
            if context.directional_side != "FLAT" or context.reconciliation_status != "RECONCILED":
                reasons.append("REVERSAL_REQUIRES_RECONCILED_FLAT")
                blocked = True
        if context.intended_action in _INCREASE_ACTIONS:
            if NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION is not True:
                _reject("unresolved_recon_increase_doctrine_missing")
            if context.reconciliation_status in {"UNRESOLVED", "UNKNOWN"}:
                reasons.append("NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION")
                blocked = True
            if NO_ORDER_WITHOUT_SINGLE_USE_PERMISSION is not True:
                _reject("single_use_permission_doctrine_missing")
            if context.single_use_permission is not True:
                reasons.append("NO_ORDER_WITHOUT_SINGLE_USE_PERMISSION")
                blocked = True
        if context.stale:
            reasons.append("STALE_INSTRUMENT_FAIL_CLOSED")
            blocked = True
        if context.kill_switch_tripped:
            reasons.append("INSTRUMENT_KILL_SWITCH")
            blocked = True
        # Invocation contract only — existing owners remain the engines.
        _ = MASTER_V2_DOUBLE_PLAY_OWNER
        _ = PER_INSTRUMENT_RISK_OWNER
        intents.append(
            IntentV1(
                instrument_id=context.instrument_id,
                action=context.intended_action,
                side=context.intended_side,
                qty="0" if blocked else qty,
                blocked=blocked,
                block_reasons=tuple(reasons),
                sequence=sequence_start + offset,
                source_stage="per_instrument",
            )
        )
    return tuple(intents)

"""Global safety after portfolio risk. Can only restrict or block."""

from __future__ import annotations

from decimal import Decimal

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    GLOBAL_SAFETY_CAN_ONLY_RESTRICT_OR_BLOCK,
    SAFETY_OWNER,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    IntentV1,
    R6S3RuntimeArchitectureError,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def apply_global_safety_v1(
    intents: tuple[IntentV1, ...],
    *,
    global_kill_switch: bool,
) -> tuple[IntentV1, ...]:
    if GLOBAL_SAFETY_CAN_ONLY_RESTRICT_OR_BLOCK is not True:
        _reject("safety_restrict_only_doctrine_missing")
    _ = SAFETY_OWNER
    out: list[IntentV1] = []
    for intent in intents:
        current = intent
        if global_kill_switch:
            current = current.restrict(
                qty="0",
                reason="GLOBAL_KILL_SWITCH",
                block=True,
                source_stage="global_safety",
            )
        if current.action in {"ENTRY", "REVERSAL"} and not current.blocked:
            # Safety may not unblock a previously blocked intent.
            current = IntentV1(
                instrument_id=current.instrument_id,
                action=current.action,
                side=current.side,
                qty=current.qty,
                blocked=current.blocked,
                block_reasons=current.block_reasons,
                sequence=current.sequence,
                source_stage="global_safety",
            )
        if intent.blocked and not current.blocked:
            _reject("safety_unblocked_prior_intent")
        if (not intent.blocked) and current.blocked is False:
            if Decimal(str(current.qty)) > Decimal(str(intent.qty)):
                _reject("safety_increased_qty")
        out.append(current)
    return tuple(sorted(out, key=lambda row: (row.instrument_id, row.sequence)))

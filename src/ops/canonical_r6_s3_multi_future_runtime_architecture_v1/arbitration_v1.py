"""Deterministic cross-instrument intent arbitration.

Identical input yields identical order. No dict/set/random dependence.
Conflicts fail closed.
"""

from __future__ import annotations

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    ACTION_PRIORITY,
    DETERMINISTIC_INTENT_ARBITRATION,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    IntentV1,
    R6S3RuntimeArchitectureError,
)

_PRIORITY = dict(ACTION_PRIORITY)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def _sort_key(intent: IntentV1) -> tuple[str, int, int, str]:
    priority = _PRIORITY.get(intent.action)
    if priority is None:
        _reject(f"unknown_action_for_arbitration:{intent.action}")
    return (intent.instrument_id, int(priority), int(intent.sequence), intent.side)


def arbitrate_intents_v1(intents: tuple[IntentV1, ...]) -> tuple[IntentV1, ...]:
    if DETERMINISTIC_INTENT_ARBITRATION is not True:
        _reject("arbitration_doctrine_missing")
    ordered = tuple(sorted(intents, key=_sort_key))
    seen_open: dict[str, IntentV1] = {}
    out: list[IntentV1] = []
    for intent in ordered:
        prior = seen_open.get(intent.instrument_id)
        if prior is not None and prior.action != "HOLD" and intent.action != "HOLD":
            if prior.action != intent.action or prior.side != intent.side:
                _reject(
                    "arbitration_conflict_fail_closed:"
                    f"{intent.instrument_id}:{prior.action}/{intent.action}"
                )
        if intent.side == "LONG" and prior is not None and prior.side == "SHORT":
            _reject(f"arbitration_long_short_conflict:{intent.instrument_id}")
        if intent.side == "SHORT" and prior is not None and prior.side == "LONG":
            _reject(f"arbitration_long_short_conflict:{intent.instrument_id}")
        seen_open[intent.instrument_id] = intent
        out.append(
            IntentV1(
                instrument_id=intent.instrument_id,
                action=intent.action,
                side=intent.side,
                qty=intent.qty,
                blocked=intent.blocked,
                block_reasons=intent.block_reasons,
                sequence=intent.sequence,
                source_stage="arbitration",
            )
        )
    return tuple(out)

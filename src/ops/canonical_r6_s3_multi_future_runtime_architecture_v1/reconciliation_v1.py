"""Per-instrument reconciliation. Unresolved increase is blocked locally."""

from __future__ import annotations

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION,
    PER_INSTRUMENT_RECONCILIATION,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    IntentV1,
    R6S3RuntimeArchitectureError,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def apply_per_instrument_reconciliation_v1(
    intents: tuple[IntentV1, ...],
    contexts: tuple[InstrumentContextV1, ...],
) -> tuple[IntentV1, ...]:
    if PER_INSTRUMENT_RECONCILIATION is not True:
        _reject("per_instrument_recon_doctrine_missing")
    if NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION is not True:
        _reject("unresolved_increase_doctrine_missing")
    by_id = {context.instrument_id: context for context in contexts}
    if len(by_id) != len(contexts):
        _reject("recon_context_duplicate")
    out: list[IntentV1] = []
    for intent in intents:
        context = by_id.get(intent.instrument_id)
        if context is None:
            current = intent.restrict(
                qty="0",
                reason="MISSING_INSTRUMENT_RECON_CONTEXT",
                block=True,
                source_stage="reconciliation",
            )
            out.append(current)
            continue
        current = intent
        unresolved = context.reconciliation_status in {"UNRESOLVED", "UNKNOWN"}
        if unresolved and intent.action in {"ENTRY", "REVERSAL"}:
            current = intent.restrict(
                qty="0",
                reason="NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION",
                block=True,
                source_stage="reconciliation",
            )
        out.append(current)
    return tuple(sorted(out, key=lambda row: (row.instrument_id, row.sequence)))

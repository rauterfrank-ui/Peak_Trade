"""Per-instrument isolated runtime context. No shared mutable state."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    R6S3RuntimeArchitectureError,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def isolate_instrument_contexts_v1(
    contexts: tuple[InstrumentContextV1, ...],
) -> Mapping[str, InstrumentContextV1]:
    isolated: dict[str, InstrumentContextV1] = {}
    for context in contexts:
        instrument_id = str(context.instrument_id or "").strip()
        if not instrument_id:
            _reject("instrument_id_missing")
        if instrument_id in isolated:
            _reject(f"duplicate_instrument_context:{instrument_id}")
        isolated[instrument_id] = InstrumentContextV1(
            instrument_id=instrument_id,
            directional_side=context.directional_side,
            position_qty=context.position_qty,
            reconciliation_status=context.reconciliation_status,
            intended_action=context.intended_action,
            intended_side=context.intended_side,
            intended_qty=context.intended_qty,
            single_use_permission=bool(context.single_use_permission),
            isolated_state=dict(context.isolated_state),
            kill_switch_tripped=bool(context.kill_switch_tripped),
            stale=bool(context.stale),
        )
    ordered = {key: isolated[key] for key in sorted(isolated)}
    return MappingProxyType(ordered)


def mutate_isolated_state_copy_v1(
    contexts: Mapping[str, InstrumentContextV1],
    instrument_id: str,
    patch: Mapping[str, Any],
) -> Mapping[str, InstrumentContextV1]:
    if instrument_id not in contexts:
        _reject(f"unknown_instrument_for_isolation_patch:{instrument_id}")
    updated: dict[str, InstrumentContextV1] = {}
    for key in sorted(contexts):
        current = contexts[key]
        if key != instrument_id:
            updated[key] = InstrumentContextV1(**current.to_mapping())
            continue
        state = dict(current.isolated_state)
        state.update(dict(patch))
        payload = dict(current.to_mapping())
        payload["isolated_state"] = state
        updated[key] = InstrumentContextV1(**payload)
    return MappingProxyType(updated)

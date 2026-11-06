"""Restart/recovery contract. Unknown remains fail-closed. Restart cannot authorize."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    R6S3RuntimeArchitectureError,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def snapshot_contexts_v1(
    contexts: tuple[InstrumentContextV1, ...],
) -> Mapping[str, Mapping[str, Any]]:
    payload = {
        context.instrument_id: dict(context.to_mapping())
        for context in sorted(contexts, key=lambda row: row.instrument_id)
    }
    return MappingProxyType(payload)


def reconstruct_contexts_v1(
    snapshot: Mapping[str, Any] | None,
    *,
    authorized_after_restart: bool,
) -> tuple[InstrumentContextV1, ...]:
    if authorized_after_restart is True:
        _reject("restart_cannot_create_authorization")
    if snapshot is None:
        _reject("restart_snapshot_missing_fail_closed")
    if not isinstance(snapshot, Mapping):
        _reject("restart_snapshot_not_mapping")
    reconstructed: list[InstrumentContextV1] = []
    for instrument_id in sorted(snapshot):
        row = snapshot[instrument_id]
        if not isinstance(row, Mapping):
            _reject(f"restart_row_not_mapping:{instrument_id}")
        status = str(row.get("reconciliation_status", "UNKNOWN"))
        if status == "UNKNOWN":
            reconstructed.append(
                InstrumentContextV1(
                    instrument_id=str(row.get("instrument_id") or instrument_id),
                    directional_side=str(row.get("directional_side") or "FLAT"),
                    position_qty=str(row.get("position_qty") or "0"),
                    reconciliation_status="UNKNOWN",
                    intended_action="HOLD",
                    intended_side="FLAT",
                    intended_qty="0",
                    single_use_permission=False,
                    isolated_state=dict(row.get("isolated_state") or {}),
                    kill_switch_tripped=bool(row.get("kill_switch_tripped", False)),
                    stale=True,
                )
            )
            continue
        reconstructed.append(
            InstrumentContextV1(
                instrument_id=str(row.get("instrument_id") or instrument_id),
                directional_side=str(row.get("directional_side") or "FLAT"),
                position_qty=str(row.get("position_qty") or "0"),
                reconciliation_status=status,
                intended_action=str(row.get("intended_action") or "HOLD"),
                intended_side=str(row.get("intended_side") or "FLAT"),
                intended_qty=str(row.get("intended_qty") or "0"),
                single_use_permission=bool(row.get("single_use_permission", False)),
                isolated_state=dict(row.get("isolated_state") or {}),
                kill_switch_tripped=bool(row.get("kill_switch_tripped", False)),
                stale=bool(row.get("stale", False)),
            )
        )
    return tuple(reconstructed)

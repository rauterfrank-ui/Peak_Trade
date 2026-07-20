"""Resume state machine for acquisition partitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.longer_chronological_pit_acquisition_v1 import STATE_SCHEMA_VERSION
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    ArchiveRootError,
    archive_layout,
    assert_path_under_archive,
)

STATES = (
    "PLANNED",
    "DISCOVERED",
    "ACQUIRING",
    "ACQUIRED",
    "CHECKSUM_VERIFIED",
    "NORMALIZED",
    "QUALIFIED",
    "QUARANTINED",
    "FAILED",
)

_ALLOWED: dict[str, frozenset[str]] = {
    "PLANNED": frozenset({"DISCOVERED", "FAILED", "QUARANTINED"}),
    "DISCOVERED": frozenset({"ACQUIRING", "FAILED", "QUARANTINED"}),
    "ACQUIRING": frozenset({"ACQUIRED", "FAILED", "QUARANTINED"}),
    "ACQUIRED": frozenset({"CHECKSUM_VERIFIED", "FAILED", "QUARANTINED"}),
    "CHECKSUM_VERIFIED": frozenset({"NORMALIZED", "FAILED", "QUARANTINED"}),
    "NORMALIZED": frozenset({"QUALIFIED", "FAILED", "QUARANTINED"}),
    "QUALIFIED": frozenset(),
    "QUARANTINED": frozenset(),
    "FAILED": frozenset({"PLANNED"}),  # explicit replan only
}


class StateTransitionError(ValueError):
    """Illegal resume-state transition."""


def assert_transition(current: str, new: str) -> None:
    if current not in _ALLOWED:
        raise StateTransitionError(f"UNKNOWN_STATE:{current}")
    if new not in STATES:
        raise StateTransitionError(f"UNKNOWN_TARGET_STATE:{new}")
    if new not in _ALLOWED[current]:
        raise StateTransitionError(f"ILLEGAL_TRANSITION:{current}->{new}")


def new_state_store() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "partitions": {},
    }


def get_status(store: Mapping[str, Any], partition_id: str) -> str | None:
    row = (store.get("partitions") or {}).get(partition_id)
    if not row:
        return None
    return str(row.get("status"))


def transition(
    store: dict[str, Any],
    partition_id: str,
    new_status: str,
    *,
    detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    parts = store.setdefault("partitions", {})
    cur_row = parts.get(partition_id) or {"status": "PLANNED"}
    current = str(cur_row.get("status") or "PLANNED")
    if partition_id not in parts and new_status == "PLANNED":
        parts[partition_id] = {"status": "PLANNED", **(detail or {})}
        return store
    assert_transition(current, new_status)
    updated = {**cur_row, **(detail or {}), "status": new_status}
    parts[partition_id] = updated
    return store


def should_skip_verified(store: Mapping[str, Any], partition_id: str) -> bool:
    status = get_status(store, partition_id)
    return status in {"CHECKSUM_VERIFIED", "NORMALIZED", "QUALIFIED"}


def write_state_atomic(store: Mapping[str, Any], *, archive_root: Path) -> Path:
    layout = archive_layout(archive_root)
    layout["state"].mkdir(parents=True, exist_ok=True)
    target = assert_path_under_archive(layout["state"] / "resume_state.json", archive_root)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


def load_state(archive_root: Path) -> dict[str, Any]:
    layout = archive_layout(archive_root)
    path = layout["state"] / "resume_state.json"
    if not path.exists():
        return new_state_store()
    assert_path_under_archive(path, archive_root)
    return json.loads(path.read_text(encoding="utf-8"))


def write_immutable_partition_bytes(
    *,
    archive_root: Path,
    relative_path: str,
    payload: bytes,
) -> Path:
    """Atomic create-only write; refuse overwrite of existing immutable artifact."""
    layout = archive_layout(archive_root)
    target = assert_path_under_archive(layout["base"] / relative_path, archive_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ArchiveRootError("IMMUTABLE_PARTITION_EXISTS_NO_OVERWRITE")
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(payload)
    tmp.replace(target)
    return target

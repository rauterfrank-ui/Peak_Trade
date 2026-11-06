"""Append-only pending outcome store with derived index."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    EVENTS_LEDGER_BASENAME,
    INDEX_BASENAME,
    OPEN_STATUSES,
    SCHEMA_VERSION,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.types_v1 import (
    NaturalEnterPendingOutcomeRecordV1,
)


class NaturalEnterPendingOutcomeStoreError(RuntimeError):
    """Fail-closed pending outcome persistence error."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def lane_pending_lane_dir_v1(lane_state_root: Path) -> Path:
    return Path(lane_state_root) / "LANE_1"


def _events_path(lane_dir: Path) -> Path:
    return lane_dir / EVENTS_LEDGER_BASENAME


def _index_path(lane_dir: Path) -> Path:
    return lane_dir / INDEX_BASENAME


def _atomic_write_json_v1(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def append_pending_outcome_event_v1(
    lane_state_root: Path,
    *,
    event_type: str,
    record: NaturalEnterPendingOutcomeRecordV1,
    detail: Mapping[str, Any] | None = None,
) -> None:
    lane_dir = lane_pending_lane_dir_v1(lane_state_root)
    lane_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": str(event_type),
        "event_time_utc": _utc_now_iso_v1(),
        "pending_outcome_id": record.pending_outcome_id,
        "decision_event_ref": record.decision_event_ref,
        "record": record.to_index_dict_v1(),
        "detail": dict(detail or {}),
    }
    events = _events_path(lane_dir)
    with events.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def upsert_pending_outcome_index_v1(
    lane_state_root: Path,
    record: NaturalEnterPendingOutcomeRecordV1,
) -> None:
    lane_dir = lane_pending_lane_dir_v1(lane_state_root)
    index_path = _index_path(lane_dir)
    index: dict[str, Any]
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"schema_version": SCHEMA_VERSION, "records_by_decision_event_ref": {}}
    by_ref = index.setdefault("records_by_decision_event_ref", {})
    existing = by_ref.get(record.decision_event_ref)
    if isinstance(existing, dict):
        prior_status = str(existing.get("status") or "")
        if prior_status == "CLOSED" and record.status != "CLOSED":
            raise NaturalEnterPendingOutcomeStoreError("CLOSED_PENDING_OUTCOME_IMMUTABLE")
    by_ref[record.decision_event_ref] = record.to_index_dict_v1()
    index["updated_at_utc"] = _utc_now_iso_v1()
    _atomic_write_json_v1(index_path, index)


def load_pending_outcome_by_decision_ref_v1(
    lane_state_root: Path,
    decision_event_ref: str,
) -> NaturalEnterPendingOutcomeRecordV1 | None:
    lane_dir = lane_pending_lane_dir_v1(lane_state_root)
    index_path = _index_path(lane_dir)
    if not index_path.is_file():
        return None
    index = json.loads(index_path.read_text(encoding="utf-8"))
    by_ref = index.get("records_by_decision_event_ref") or {}
    raw = by_ref.get(decision_event_ref)
    if not isinstance(raw, dict):
        return None
    return NaturalEnterPendingOutcomeRecordV1.from_index_dict_v1(raw)


def list_open_pending_outcomes_v1(
    lane_state_root: Path,
) -> tuple[NaturalEnterPendingOutcomeRecordV1, ...]:
    lane_dir = lane_pending_lane_dir_v1(lane_state_root)
    index_path = _index_path(lane_dir)
    if not index_path.is_file():
        return ()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    by_ref = index.get("records_by_decision_event_ref") or {}
    out: list[NaturalEnterPendingOutcomeRecordV1] = []
    for raw in by_ref.values():
        if not isinstance(raw, dict):
            continue
        rec = NaturalEnterPendingOutcomeRecordV1.from_index_dict_v1(raw)
        if rec.status in OPEN_STATUSES:
            out.append(rec)
    return tuple(sorted(out, key=lambda r: r.created_at_utc))


def pending_outcome_has_closed_outcome_in_ddo_ledger_v1(
    ddo_ledger_path: Path,
    decision_event_ref: str,
) -> bool:
    if not ddo_ledger_path.is_file():
        return False
    needle = str(decision_event_ref)
    for line in ddo_ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if needle not in line:
            continue
        if "out.nbars." in line and "decision_event_ref" in line:
            try:
                envelope = json.loads(line)
                payload = envelope.get("payload") or envelope.get("record") or envelope
                if isinstance(payload, dict) and payload.get("decision_event_ref") == needle:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def persist_record_v1(
    lane_state_root: Path,
    *,
    event_type: str,
    record: NaturalEnterPendingOutcomeRecordV1,
    detail: Mapping[str, Any] | None = None,
) -> None:
    upsert_pending_outcome_index_v1(lane_state_root, record)
    append_pending_outcome_event_v1(
        lane_state_root,
        event_type=event_type,
        record=record,
        detail=detail,
    )


def replace_record_v1(
    record: NaturalEnterPendingOutcomeRecordV1,
    **updates: Any,
) -> NaturalEnterPendingOutcomeRecordV1:
    data = record.to_index_dict_v1()
    data.update(updates)
    data["updated_at_utc"] = _utc_now_iso_v1()
    if "finalized_bar_identities" in updates and isinstance(
        updates["finalized_bar_identities"], Sequence
    ):
        data["finalized_bar_identities"] = list(updates["finalized_bar_identities"])
    return NaturalEnterPendingOutcomeRecordV1.from_index_dict_v1(data)

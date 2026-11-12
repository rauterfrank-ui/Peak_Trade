"""Persist the occupied-lane mark with the original Core episode snapshot."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_text,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    SNAPSHOT_FILENAME,
    SNAPSHOT_SCHEMA_NAME,
    NakedLayeredCoreDurableStateError,
    NakedLayeredCoreEpisodeV1,
    _canonical_json,
    _snapshot_digest,
    atomic_persist_episode_v1,
    episode_from_snapshot_v1,
    episode_to_snapshot_v1,
    restore_episode_from_store_v1,
)


def _occupied_scope_mark_snapshot_v1(text: str) -> dict[str, Any] | None:
    try:
        body = json.loads(text)
    except ValueError:
        # The legacy reader verifies the manifest before decoding the snapshot.
        return None
    if isinstance(body, dict) and body.get("schema_name") == SNAPSHOT_SCHEMA_NAME:
        return None
    if not isinstance(body, dict) or set(body) != {"snapshot", "mark", "digest"}:
        raise NakedLayeredCoreDurableStateError("OCCUPIED_MARK_SNAPSHOT_INVALID")
    expected = _snapshot_digest({"snapshot": body["snapshot"], "mark": body["mark"]})
    mark = body["mark"]
    if body["digest"] != expected:
        raise NakedLayeredCoreDurableStateError("OCCUPIED_MARK_SNAPSHOT_DIGEST_MISMATCH")
    if (
        not isinstance(mark, dict)
        or type(mark.get("event_unix")) not in (int, float)
        or not math.isfinite(mark["event_unix"])
        or mark["event_unix"] <= 0
        or not isinstance(mark.get("prices"), list)
        or not mark["prices"]
        or any(
            type(p) not in (int, float) or not math.isfinite(p) or p <= 0 for p in mark["prices"]
        )
        or not isinstance(mark.get("position_episode_id"), str)
        or not mark["position_episode_id"]
        or "pending_close_episode_id" not in mark
        or mark["pending_close_episode_id"] not in (None, mark["position_episode_id"])
    ):
        raise NakedLayeredCoreDurableStateError("OCCUPIED_MARK_SNAPSHOT_INVALID")
    return body


def read_occupied_scope_mark_snapshot_v1(store_root: Path) -> dict[str, Any] | None:
    try:
        text = (store_root / SNAPSHOT_FILENAME).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise NakedLayeredCoreDurableStateError("OCCUPIED_MARK_SNAPSHOT_UNREADABLE") from exc
    return _occupied_scope_mark_snapshot_v1(text)


def require_new_occupied_scope_mark_v1(
    store_root: Path, *, event_unix: float, price: float, episode_id: str
) -> list[float]:
    record = read_occupied_scope_mark_snapshot_v1(store_root)
    if record is None:
        return [price]
    mark = record["mark"]
    if event_unix < mark["event_unix"]:
        raise NakedLayeredCoreDurableStateError("OCCUPIED_SCOPE_MARK_OUT_OF_ORDER")
    if event_unix == mark["event_unix"] and price in mark["prices"]:
        raise NakedLayeredCoreDurableStateError("OCCUPIED_SCOPE_MARK_DUPLICATE")
    if mark["pending_close_episode_id"] == episode_id:
        raise NakedLayeredCoreDurableStateError("OCCUPIED_SCOPE_CLOSE_ALREADY_PLANNED")
    return [*mark["prices"], price] if event_unix == mark["event_unix"] else [price]


def persist_layered_core_episode_v1(
    store_root: Path,
    episode: NakedLayeredCoreEpisodeV1,
    *,
    occupied_mark: Mapping[str, Any] | None = None,
) -> str:
    prior = read_occupied_scope_mark_snapshot_v1(store_root)
    if occupied_mark is None and prior is None:
        return atomic_persist_episode_v1(store_root, episode)

    store_root.mkdir(parents=True, exist_ok=True)
    snapshot = episode_to_snapshot_v1(episode)
    mark = dict(occupied_mark) if occupied_mark is not None else prior["mark"]
    record = {"snapshot": snapshot, "mark": mark}
    record["digest"] = _snapshot_digest(record)
    atomic_write_text(path=store_root / SNAPSHOT_FILENAME, text=_canonical_json(record))
    return hashlib.sha256(_canonical_json(snapshot).encode("utf-8")).hexdigest()


def restore_layered_core_episode_v1(
    store_root: Path, *, expected_instrument_id: str | None = None
) -> NakedLayeredCoreEpisodeV1:
    occupied = read_occupied_scope_mark_snapshot_v1(store_root)
    if occupied is None:
        return restore_episode_from_store_v1(
            store_root, expected_instrument_id=expected_instrument_id
        )
    return episode_from_snapshot_v1(
        occupied["snapshot"], expected_instrument_id=expected_instrument_id
    )

"""Verified same-episode fill progress through the existing Exit state writer."""

from copy import deepcopy
from decimal import Decimal
import math
from pathlib import Path
import re

from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    build_current_cursor_publication_v1,
    require_current_cursor_continuity_v1,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    SCHEMA as SOURCE_SCHEMA,
    _archive_verified_source_v1,
    _load_source,
    _ref,
    _verify,
    require_economic_history_extension_v1,
    latest_economic_event_time_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)

SCHEMA = "simulated_accounting_episode_progress.v1"
FUNDING_SCHEMA = "simulated_accounting_episode_progress.v2"


def _same_accounting_domain(previous, current):
    if any(
        previous["accounting_checkpoint"][key] != current["accounting_checkpoint"][key]
        for key in ("contract", "initial_equity", "writer_identity")
    ):
        raise ValueError("SIMULATED_ENTRY_PROGRESS_ACCOUNTING_DOMAIN_CHANGED")


def _source(ref, identity):
    if not isinstance(ref, str):
        raise ValueError("SIMULATED_ENTRY_PROGRESS_SOURCE_REQUIRED")
    parts = ref.split(":", 2)
    if len(parts) != 3 or parts[0] != SOURCE_SCHEMA or not re.fullmatch("[0-9a-f]{64}", parts[1]):
        raise ValueError("SIMULATED_ENTRY_PROGRESS_SOURCE_REQUIRED")
    path = Path(parts[2])
    if not path.is_absolute() or str(path.resolve()) != parts[2]:
        raise ValueError("SIMULATED_ENTRY_PROGRESS_SOURCE_PATH_INVALID")
    digest, anchors, payload = _load_source(path, identity, include_payload=True)
    if digest != parts[1]:
        raise ValueError("SIMULATED_ENTRY_PROGRESS_SOURCE_DIGEST_MISMATCH")
    return payload, anchors


def verify_simulated_accounting_progress_v1(episode):
    record = episode.binding.simulated_accounting_progress
    funding_mode = isinstance(record, dict) and record.get("schema") == FUNDING_SCHEMA
    time_key = "latest_economic_event_time" if funding_mode else "latest_fill_event_time"
    required = {
        "schema",
        "initial_source_ref",
        "previous_source_ref",
        "current_source_ref",
        "applied_fill_count",
        time_key,
    }
    if funding_mode:
        required.add("applied_funding_count")
    if (
        not isinstance(record, dict)
        or set(record) != required
        or record["schema"] not in {SCHEMA, FUNDING_SCHEMA}
        or record["initial_source_ref"] != episode.entry_source_ref
        or type(record["applied_fill_count"]) is not int
        or type(record[time_key]) not in (int, float)
        or not math.isfinite(record[time_key])
        or record[time_key] <= 0
        or funding_mode
        and type(record["applied_funding_count"]) is not int
    ):
        raise ValueError("SIMULATED_ENTRY_PROGRESS_RECORD_INVALID")
    initial, original_anchors = _source(episode.entry_source_ref, episode.identity)
    previous, _ = _source(record["previous_source_ref"], episode.identity)
    current, anchors = _source(record["current_source_ref"], episode.identity)
    _same_accounting_domain(initial, previous)
    _same_accounting_domain(previous, current)
    old, now = previous["fills"], current["fills"]
    before, after = require_economic_history_extension_v1(previous, current)
    require_economic_history_extension_v1(initial, previous)
    latest = latest_economic_event_time_v1(current) if funding_mode else now[-1]["event_time_unix"]
    if (
        len(old) < len(initial["fills"])
        or len(before) >= len(after)
        or now[: len(old)] != old
        or now[: len(initial["fills"])] != initial["fills"]
        or len(now) != record["applied_fill_count"]
        or any(row["event_time_unix"] is None for row in now[len(initial["fills"]) :])
        or latest != record[time_key]
        or funding_mode
        and record["applied_funding_count"]
        != len(current["accounting_checkpoint"]["funding_events"])
        or not funding_mode
        and bool(current["accounting_checkpoint"]["funding_events"])
        or anchors["entry_event_time"] != original_anchors["entry_event_time"]
        or any(
            getattr(episode.binding, k) != anchors[k]
            for k in ("entry_price", "entry_event_time", "entry_trading_epoch")
        )
    ):
        raise ValueError("SIMULATED_ENTRY_PROGRESS_LINEAGE_OR_ANCHOR_MISMATCH")
    return {
        "payload": current,
        "anchors": anchors,
        "quantity": Decimal(current["accounting_checkpoint"]["position"]["qty"]),
        "latest_fill_event_time": now[-1]["event_time_unix"],
        "latest_economic_event_time": latest,
    }


def require_simulated_accounting_quantity_v1(*, episode, observation):
    if episode.binding.simulated_accounting_progress is None:
        if not isinstance(episode.entry_source_ref, str) or not episode.entry_source_ref.startswith(
            SOURCE_SCHEMA + ":"
        ):
            return
        payload, _ = _source(episode.entry_source_ref, episode.identity)
        quantity = Decimal(payload["accounting_checkpoint"]["position"]["qty"])
        reason = "SIMULATED_ENTRY_INITIAL_POSITION_QUANTITY_MISMATCH"
    else:
        quantity = verify_simulated_accounting_progress_v1(episode)["quantity"]
        reason = "SIMULATED_ENTRY_PROGRESS_POSITION_QUANTITY_MISMATCH"
    if (
        observation is None
        or observation.quantity != quantity
        or observation.lane_id != episode.identity.lane_id
        or observation.canonical_instrument_id != episode.identity.instrument_id
        or observation.venue_native_id != episode.identity.venue_native_id
    ):
        raise ValueError(reason)


def advance_position_episode_from_simulated_accounting_v1(
    *,
    episode,
    session,
    fills,
    source_archive_root,
    cursor_store_root,
    expected_scope,
    writer_session_id,
):
    if expected_scope != episode.identity.account_scope:
        raise ValueError("POSITION_EPISODE_ACCOUNT_SCOPE_MISMATCH")
    if not episode.binding.state_root or episode.binding.alpha_blocked:
        raise ValueError("POSITION_EPISODE_EXIT_BINDING_BLOCKED")
    state = load_exit_policy_state_v1(
        Path(episode.binding.state_root),
        expected_repository_sha=episode.binding.repository_sha,
        expected_config_digest=episode.binding.config_digest,
        expected_instrument_id=episode.identity.instrument_id,
    )
    if state.to_dict() != episode.binding.to_canonical_state().to_dict():
        raise ValueError("SIMULATED_ENTRY_PROGRESS_STALE_HANDLE")
    if episode.binding.simulated_accounting_progress is None:
        old_ref = episode.entry_source_ref
        old_payload, old_anchors = _source(old_ref, episode.identity)
        if any(
            getattr(episode.binding, k) != old_anchors[k]
            for k in ("entry_price", "entry_event_time", "entry_trading_epoch")
        ):
            raise ValueError("SIMULATED_ENTRY_PROGRESS_INITIAL_ANCHOR_MISMATCH")
    else:
        old_payload = verify_simulated_accounting_progress_v1(episode)["payload"]
        old_ref = episode.binding.simulated_accounting_progress["current_source_ref"]
    payload, anchors = _verify(identity=episode.identity, session=session, fills=fills)
    _same_accounting_domain(old_payload, payload)
    old, now = old_payload["fills"], payload["fills"]
    if len(now) < len(old) or now[: len(old)] != old:
        raise ValueError("SIMULATED_ENTRY_PROGRESS_HISTORY_REWRITE")
    before, after = require_economic_history_extension_v1(old_payload, payload)
    if len(after) == len(before):
        return {"status": "ALREADY_APPLIED", "commit_sequence": episode.binding.commit_sequence}
    if any(row["event_time_unix"] is None for row in now[len(old) :]):
        raise ValueError("SIMULATED_ENTRY_PROGRESS_NEW_FILL_TIME_REQUIRED")
    if anchors["entry_event_time"] != episode.binding.entry_event_time:
        raise ValueError("SIMULATED_ENTRY_PROGRESS_OPEN_TIME_CHANGED")
    root = Path(cursor_store_root)
    if not root.is_absolute():
        raise ValueError("POSITION_EPISODE_CURSOR_ROOT_REQUIRED")
    incoming = load_current_productive_sidestate_confirmation_cursor_v1(root)
    restored = restore_current_productive_sidestate_confirmation_cursor_v1(
        incoming,
        expected_instrument_id=episode.identity.instrument_id,
        expected_venue_native_id=episode.identity.venue_native_id,
        venue_flat=False,
    )
    if restored.disposition.value != "restored" or restored.cursor.existing_scope is None:
        raise ValueError("SIMULATED_ENTRY_PROGRESS_OCCUPIED_CURSOR_REQUIRED")
    require_current_cursor_continuity_v1(episode=episode, incoming=incoming, store_root=root)
    path, digest = _archive_verified_source_v1(
        payload=payload,
        anchors=anchors,
        identity=episode.identity,
        source_archive_root=source_archive_root,
    )
    evaluated = deepcopy(episode.binding)
    evaluated.entry_price = anchors["entry_price"]
    evaluated.simulated_accounting_progress = {
        "schema": SCHEMA,
        "initial_source_ref": episode.entry_source_ref,
        "previous_source_ref": old_ref,
        "current_source_ref": _ref(path, digest),
        "applied_fill_count": len(now),
        "latest_fill_event_time": now[-1]["event_time_unix"],
    }
    if payload["accounting_checkpoint"]["funding_events"]:
        record = evaluated.simulated_accounting_progress
        record.update(
            schema=FUNDING_SCHEMA,
            applied_funding_count=len(payload["accounting_checkpoint"]["funding_events"]),
            latest_economic_event_time=latest_economic_event_time_v1(payload),
        )
        record.pop("latest_fill_event_time")
    # Identity publication for this state-only update: the actual cursor stays unchanged.
    evaluated.current_cursor_publication = build_current_cursor_publication_v1(
        episode=episode,
        incoming=restored.cursor,
        outgoing=restored.cursor,
        store_root=root,
    )
    receipt = episode._persist_checked_generation_v1(evaluated, writer_session_id=writer_session_id)
    return {"status": "APPLIED", "commit_sequence": receipt["commit_sequence"]}

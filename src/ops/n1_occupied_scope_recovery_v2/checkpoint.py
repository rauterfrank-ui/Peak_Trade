"""Bind an occupied WAIT to its original Core state and durable capital hold."""

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    PRICE_BOUND_SCHEMA,
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
    restore_layered_core_episode_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    digest as budget_digest,
    read_budget_revision_read_only_v1,
    require_budget_head_read_only_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.execution_v1 import (
    read_persisted_execution_reconciliation_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    SNAPSHOT_FILENAME,
)


def _scope_and_hold_v1(*, cursor_root, budget_root, account, revision, native_id):
    if cursor_root.resolve() != cursor_root or budget_root.resolve() != budget_root:
        raise ValueError("OCCUPIED_WAIT_ORIGINAL_ROOT_REQUIRED")
    sequence, digest = revision
    state = read_budget_revision_read_only_v1(
        budget_root,
        account_identity=account,
        sequence=sequence,
        expected_digest=digest,
    )["state"]
    slot = cursor_root.name
    (reservation,) = [
        row for row in state["reservations"] if row["state"] in {"RESERVED", "COMMITTED"}
    ]
    bound = state["lane_bindings"][slot]["bound"]
    if (
        slot != reservation["slot_id"]
        or set(state["lane_bindings"]) != {slot}
        or reservation["state"] != "COMMITTED"
        or bound["venue_native_id"] != native_id
    ):
        raise ValueError("OCCUPIED_WAIT_ORIGINAL_RESERVATION_REQUIRED")
    rid = reservation["reservation_id"]
    link = state["execution_links"][rid]
    result = link["reconciliation"]
    if (
        link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
        or result["matched"] is not True
        or result["reservation_released"] is not False
        or result["decision"]["reconciliation_complete"] is not True
        or result["decision"]["exposure_retained"] is not True
    ):
        raise ValueError("OCCUPIED_WAIT_ORIGINAL_POSITION_REQUIRED")
    scope_path = cursor_root / SNAPSHOT_FILENAME
    if scope_path.resolve() != scope_path:
        raise ValueError("OCCUPIED_WAIT_ORIGINAL_SCOPE_REQUIRED")
    scope_sha = sha256(scope_path.read_bytes()).hexdigest()
    scope = read_occupied_scope_mark_snapshot_v1(cursor_root)
    core = restore_layered_core_episode_v1(
        cursor_root,
        expected_instrument_id=bound["instrument_id"],
    )
    if (
        scope is None
        or core.scope is None
        or not core.scope.valid
        or sha256(scope_path.read_bytes()).hexdigest() != scope_sha
    ):
        raise ValueError("OCCUPIED_WAIT_ORIGINAL_SCOPE_REQUIRED")
    position_id = result.get("identity_digest")
    latest_booking = state.get("live_net_reversal_bookings", {}).get(rid, [])
    if latest_booking:
        position_id = latest_booking[-1]["envelope_digest"]
    if scope is not None:
        mark = scope["mark"]
        if (
            mark["pending_close_episode_id"] is not None
            or mark["position_episode_id"] != position_id
        ):
            raise ValueError("OCCUPIED_WAIT_OPEN_EXECUTION_UNPROVEN")
        cursor = parse_current_productive_sidestate_confirmation_cursor_v1(
            load_current_productive_sidestate_confirmation_cursor_v1(cursor_root)
        )
        read_current_core_entry_assessment_frame_v1(cursor)
        frame = cursor.entry_assessment_frame
        if (
            (cursor.instrument_id, cursor.venue_native_id) != (bound["instrument_id"], native_id)
            or cursor.runtime_scope_state is None
            or cursor.runtime_scope_state.current_hysteresis_band != core.scope.d_t
            or frame["schema"] != PRICE_BOUND_SCHEMA
        ):
            raise ValueError("OCCUPIED_WAIT_SCOPE_CURSOR_MISMATCH")
        source = frame["scope_price_source"]
        mark_clock = json.loads(source["mark_clock_json"])
        market = json.loads(frame["market_context"]["canonical"])
        event_time = datetime.fromisoformat(market["market_event_time"].replace("Z", "+00:00"))
        if (
            mark_clock["payload_sha256"] != mark["mark_payload_sha256"]
            or market["mark_price"] != mark["prices"][-1]
            or event_time.utcoffset() is None
            or event_time.timestamp() != mark["event_unix"]
        ):
            raise ValueError("OCCUPIED_WAIT_SCOPE_CURSOR_MISMATCH")
        if mark.get("pending_reversal_episode_id"):
            attempt_root = (
                budget_root.parent / "position-episodes" / position_id / "net-reversal-submit"
            )
            if attempt_root.exists() or attempt_root.is_symlink():
                raise ValueError("OCCUPIED_WAIT_EXTERNAL_ATTEMPT_PRESENT")
    return {
        "scope_sha256": scope_sha,
        "scope_snapshot_id": core.snapshot_id,
        "position_episode_id": position_id,
        "reservation_id": rid,
        "reserve_amount": reservation["amount"],
        "bound": bound,
        "execution_identity_sha256": budget_digest(link["identity"]),
        "net_reversal_booking_digest": latest_booking[-1]["booking_digest"]
        if latest_booking
        else None,
    }


def occupied_wait_checkpoint_v1(*, host, cursor_root: Path, native_id: str):
    """Capture only an owned, reconciled position at a completed WAIT."""
    budget_root = host.root / "owner"
    (reservation_id,) = host.owner.execution_links_v1(active_only=True)
    sequence, digest, _ = read_persisted_execution_reconciliation_v1(
        host.owner,
        reservation_id,
    )
    revision = (sequence, digest)
    proof = _scope_and_hold_v1(
        cursor_root=cursor_root,
        budget_root=budget_root,
        account=host.account,
        revision=revision,
        native_id=native_id,
    )
    require_budget_head_read_only_v1(
        budget_root,
        account_identity=host.account,
        expected_digest=revision[1],
    )
    return {"budget_revision": list(revision), "position": proof}


def verify_occupied_wait_checkpoint_v1(
    checkpoint,
    *,
    cursor_root: Path,
    budget_root: Path,
    native_id: str,
    account: str,
    admitted_host=None,
):
    revision = checkpoint["budget_revision"]
    if admitted_host is None:
        require_budget_head_read_only_v1(
            budget_root,
            account_identity=account,
            expected_digest=revision[1],
        )
    else:
        if admitted_host.root / "owner" != budget_root or admitted_host.account != account:
            raise ValueError("OCCUPIED_WAIT_ORIGINAL_HOST_REQUIRED")
        # Startup may append fresh GET reconciliation after the controller has
        # checked the original head. It must still describe the original hold.
        sequence, digest, _ = read_persisted_execution_reconciliation_v1(
            admitted_host.owner,
            checkpoint["position"]["reservation_id"],
        )
        latest = (sequence, digest)
        if latest[0] < revision[0] or checkpoint["position"] != _scope_and_hold_v1(
            cursor_root=cursor_root,
            budget_root=budget_root,
            account=account,
            revision=latest,
            native_id=native_id,
        ):
            return False
    return checkpoint["position"] == _scope_and_hold_v1(
        cursor_root=cursor_root,
        budget_root=budget_root,
        account=account,
        revision=revision,
        native_id=native_id,
    )

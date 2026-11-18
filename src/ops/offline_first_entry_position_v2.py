"""Hand a confirmed offline V2 first fill to the occupied C1 cursor."""

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    build_current_cursor_publication_v1,
    recover_current_cursor_publication_v1,
    require_current_cursor_continuity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.offline_first_entry_budget_v2 import OfflineFirstEntryBudgetOwnerV2


def bind_offline_first_entry_position_v2(
    *,
    owner,
    reservation_id,
    episode,
    cursor_root: Path,
    g17_producer,
    writer_session_id,
):
    """Retain the original simulated opening fill and transition to the C1 clock."""
    if not isinstance(owner, OfflineFirstEntryBudgetOwnerV2):
        raise ValueError("FIRST_ENTRY_V2_SIMULATED_OWNER_REQUIRED")
    return publish_confirmed_first_entry_c1_v2(
        episode=episode,
        cursor_root=cursor_root,
        g17_producer=g17_producer,
        writer_session_id=writer_session_id,
        retain_opening=lambda: owner.retain_opening_fill_v2(
            reservation_id=reservation_id, episode=episode
        ),
    )


def publish_confirmed_first_entry_c1_v2(
    *, episode, cursor_root: Path, g17_producer, writer_session_id, retain_opening
):
    """Retain the opening source and publish the finalized C1 clock for the occupied lane.

    Flat confirmation counts distinct Marks. Once the original episode is
    occupied, the V1 governor compares finalized C1 candle opens. The bound
    G17 window supplies that candle; the Mark clock remains in its own evidence.
    """
    raw = load_current_productive_sidestate_confirmation_cursor_v1(cursor_root)
    cursor = parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    identity = episode.identity
    if (cursor.instrument_id, cursor.venue_native_id) != (
        identity.instrument_id,
        identity.venue_native_id,
    ):
        raise ValueError("FIRST_ENTRY_V2_OCCUPIED_CURSOR_INSTRUMENT_MISMATCH")
    cap61 = cursor.cap61_confirmation_state
    observation = cap61.observation_acceptance_state
    last = observation.last_accepted_observation_identity
    port = g17_producer.output_port_v1()
    (latest,) = g17_producer.history.trailing_window_records_v1(count=1)
    c1_open = latest.event_time.unix_seconds
    if (
        port.estimate is None
        or port.as_of_event_time.timestamp() != c1_open
        or (latest.canonical_instrument_id, latest.venue_instrument_id)
        != (identity.instrument_id, identity.venue_native_id)
        or last is None
    ):
        raise ValueError("FIRST_ENTRY_V2_FINALIZED_C1_SOURCE_REQUIRED")

    # After an interruption, the Exit owner may already have committed the
    # exact new cursor. Finish its retained CAS publication before advancing.
    published = episode.binding.current_cursor_publication
    if published is not None:
        outgoing = published["outgoing_payload"]
        if outgoing["entry_assessment_frame"] is None:
            expected = outgoing["cap61_confirmation_state"]["observation_acceptance_state"]
            expected_identity = expected["last_accepted_observation_identity"]
            if (
                expected_identity["venue_event_time"] != c1_open
                or expected_identity["mark_price"] != latest.mark_price
            ):
                raise ValueError("FIRST_ENTRY_V2_RETAINED_C1_SOURCE_MISMATCH")
            opening_digest = retain_opening()
            result = recover_current_cursor_publication_v1(
                episode=episode,
                store_root=cursor_root,
                expected_scope=identity.account_scope,
                writer_session_id=writer_session_id,
            )
            return {**result, "opening_digest": opening_digest, "c1_open_unix": c1_open}

    require_current_cursor_continuity_v1(episode=episode, incoming=raw, store_root=cursor_root)
    frame = read_current_core_entry_assessment_frame_v1(cursor)
    market = json.loads(cursor.entry_assessment_frame["market_context"]["canonical"])
    mark_event = datetime.fromisoformat(market["market_event_time"]).timestamp()
    volatility = market["canonical_volatility_estimate"]
    if (
        volatility["source_digest"] != port.estimate.source_digest
        or datetime.fromisoformat(volatility["as_of_event_time"]).timestamp() != c1_open
        or last.venue_event_time > mark_event
        or frame["entry"]["decision_outcome"] not in {"enter_" + identity.position_side, "hold"}
    ):
        raise ValueError("FIRST_ENTRY_V2_C1_MARK_LINEAGE_MISMATCH")
    if last.venue_event_time == c1_open and last.mark_price == latest.mark_price:
        return {
            "status": "ALREADY_BOUND",
            "opening_digest": retain_opening(),
            "c1_open_unix": c1_open,
        }
    if c1_open + port.estimate.bar_interval_seconds > min(
        last.venue_event_time, episode.binding.entry_event_time
    ):
        raise ValueError("FIRST_ENTRY_V2_C1_MARK_LINEAGE_MISMATCH")

    normalized = replace(
        cursor,
        cap61_confirmation_state=replace(
            cap61,
            observation_acceptance_state=replace(
                observation,
                last_accepted_observation_identity=replace(
                    last,
                    venue_event_time=c1_open,
                    mark_price=latest.mark_price,
                ),
                last_accepted_transport=None,
            ),
        ),
        # The old assessment remains valid in the original cursor and its
        # evidence. It belongs to the old confirmation-state digest.
        entry_assessment_frame=None,
    )
    opening_digest = retain_opening()
    publication = build_current_cursor_publication_v1(
        episode=episode,
        incoming=raw,
        outgoing=normalized,
        store_root=cursor_root,
    )
    episode.commit_evaluated_v1(
        replace(episode.binding, current_cursor_publication=publication),
        writer_session_id=writer_session_id,
    )
    result = recover_current_cursor_publication_v1(
        episode=episode,
        store_root=cursor_root,
        expected_scope=identity.account_scope,
        writer_session_id=writer_session_id,
    )
    return {**result, "opening_digest": opening_digest, "c1_open_unix": c1_open}

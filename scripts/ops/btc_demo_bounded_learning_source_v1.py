"""Read the bounded host's original confirmed entry, without opening its writers."""

from datetime import datetime, timezone
import json
from pathlib import Path

from src.ops.execution_reconciliation_proof_store_v1 import find_authenticated_entry_sources_v1
from src.ops.exit_policy_producer_binding_v1.authenticated_execution_entry_source_v1 import (
    _entry_anchors_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import IDENTITY_FILENAME
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    read_budget_revision_read_only_v1,
)


def read_bounded_btc_entry_measurement_v1(root: Path):
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("BTC_BOUNDED_LEARNING_ORIGINAL_ROOT_REQUIRED")
    packet = json.loads((root / "original-entry-g17-c1.json").read_bytes())
    if packet["record_digest"] != canonical_digest_v1(
        {k: v for k, v in packet.items() if k != "record_digest"}
    ):
        raise ValueError("BTC_BOUNDED_LEARNING_ORIGINAL_PACKET_CHANGED")
    raw = packet["original_cursor"]
    origin = packet["core_cursor_source"]
    if current_productive_cursor_digest_v1(raw) != origin["source_cursor_digest"]:
        raise ValueError("BTC_BOUNDED_LEARNING_ORIGINAL_CURSOR_CHANGED")
    cursor = parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    frame = read_current_core_entry_assessment_frame_v1(cursor)
    market = json.loads(raw["entry_assessment_frame"]["market_context"]["canonical"])
    lane = root / "testnet-state/LANE_3"
    budget = root / "testnet-state/budget-owner"
    candidates = []
    for path in (budget / "position-episodes").glob("*/" + IDENTITY_FILENAME):
        episode = json.loads(path.read_bytes())
        identity = episode["identity"]
        if (
            identity["lane_id"],
            identity["instrument_id"],
            identity["venue_native_id"],
            identity["account_scope"]["execution_environment"],
        ) != ("LANE_3", cursor.instrument_id, cursor.venue_native_id, "TESTNET"):
            continue
        if episode["content_digest"] != canonical_digest_v1(
            {k: v for k, v in episode.items() if k != "content_digest"}
        ):
            raise ValueError("BTC_BOUNDED_LEARNING_EPISODE_CHANGED")
        for source in find_authenticated_entry_sources_v1(
            root=lane / "authenticated-execution-proofs",
            budget_owner_root=budget / "owner",
            account=identity["account_scope"]["account_identity"],
            reservation_id=packet["reservation_id"],
            episode_id=identity["episode_id"],
        ):
            if source.identity.canonical_decision_id != frame["parent"]["decision_id"]:
                continue
            side = identity["position_side"]
            price, filled_ms, anchors = _entry_anchors_v1(source, side=side)
            expected = "authenticated_execution_entry.v1:" + canonical_digest_v1(
                {"attempt": identity["episode_id"], "anchors": anchors}
            )
            revision = read_budget_revision_read_only_v1(
                budget / "owner",
                account_identity=source.identity.account_identity,
                sequence=source.proof.revision_ref[0],
                expected_digest=source.proof.revision_ref[1],
            )
            state = revision["state"]
            link = state["execution_links"][packet["reservation_id"]]
            registration = state["bounded_demo_session_control"]["registration"]
            if (
                episode["entry_source_ref"] != expected
                or link["plan_origin"]["core_cursor_source"] != origin
                or origin["decision_id"] != source.identity.canonical_decision_id
                or source.identity.execution_environment != "TESTNET"
                or source.identity.decision_outcome.upper() != "ENTER_" + side.upper()
                or source.identity.slot_id != "LANE_3"
                or source.identity.instrument_id != cursor.instrument_id
                or source.identity.native_id != cursor.venue_native_id
                or registration["session_id"] != source.proof.session_id
            ):
                raise ValueError("BTC_BOUNDED_LEARNING_OWNER_DECISION_MISMATCH")
            exit_state = load_exit_policy_state_v1(
                path.parent,
                expected_repository_sha="",
                expected_config_digest="",
                expected_instrument_id=cursor.instrument_id,
            )
            if (exit_state.entry_price, exit_state.entry_event_time) != (
                float(price),
                filled_ms / 1000,
            ):
                raise ValueError("BTC_BOUNDED_LEARNING_ORIGINAL_ANCHOR_MISMATCH")
            candidates.append(
                (
                    source.proof.revision_ref[0],
                    source,
                    link,
                    registration,
                    price,
                    filled_ms,
                    exit_state,
                )
            )
    if not candidates:
        raise ValueError("BTC_BOUNDED_LEARNING_CONFIRMED_ORIGINAL_ENTRY_REQUIRED")
    # Later matching observations do not move the original learning identity.
    _, source, link, registration, price, filled_ms, exit_state = min(
        candidates, key=lambda row: row[0]
    )
    attempt = source.identity
    created = link["envelope"]["creation_epoch"]
    confirmed = (
        max(read.acquired_at for read in source.proof.gets)
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    original = dict(
        canonical_decision_id=attempt.canonical_decision_id,
        policy_decision_id=frame["entry"]["policy_decision_id"],
        policy_input_digest=frame["entry"]["input_digest"],
        composition_result_ref=frame["entry"]["composition_result_ref"],
        trading_epoch=frame["entry"]["trading_epoch"],
        decision_time=market["decision_time"],
        exit_config_digest=exit_state.config_digest,
    )
    if datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp() > filled_ms / 1000:
        raise ValueError("BTC_BOUNDED_LEARNING_FILL_BEFORE_ENVELOPE")
    body = dict(
        schema="btc_demo_bounded_confirmed_entry_measurement.v1",
        authority="NONE",
        execution_environment="TESTNET",
        venue=attempt.venue,
        lane_id="LANE_3",
        session_id=registration["session_id"],
        account_identity=attempt.account_identity,
        episode_id=attempt.identity_digest(),
        instrument_id=attempt.instrument_id,
        venue_native_id=attempt.native_id,
        decision_id=attempt.canonical_decision_id,
        decision_outcome=attempt.decision_outcome,
        cycle_id=attempt.cycle_id,
        envelope_created_utc=created,
        confirmed_at_utc=confirmed,
        repository_sha=exit_state.repository_sha,
        config_digest=original["exit_config_digest"],
        source_proof=dict(
            revision_ref=list(source.proof.revision_ref),
            snapshot_digest=source.proof.snapshot_digest,
            original_cursor_digest=origin["source_cursor_digest"],
        ),
        opening_fill=dict(
            first_fill_time_ms=filled_ms,
            filled_quantity=source.reconciliation["decision"]["cumulative_filled_qty"],
            price=str(price),
            decision_source=original,
        ),
    )
    return {**body, "source_digest": canonical_digest_v1(body)}

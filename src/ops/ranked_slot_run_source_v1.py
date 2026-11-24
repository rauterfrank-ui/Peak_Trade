"""Read an immutable N5 assignment and its published Cap21–23 originals for a prepared run."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import re

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    RECOVERY_MODE_RESTART,
    load_completed_selection_publication_v1,
    load_pending_selection_publication_v1,
    recover_durable_lane_assignment_v1,
    topology_integrity_digest_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import GovernedUniverseInstrumentV1
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    FIXED_RANK_ASSIGNMENT_POLICY,
    SHADOW_SLOT4_SUCCESSOR_POLICY,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1


@dataclass(frozen=True)
class RankedRunSlotV1:
    lane_id: str
    selection: SingleSelectedFutureSelectionV1
    instrument: GovernedUniverseInstrumentV1
    universe_id: str
    transition_id: str
    selection_root: Path | None = None
    predecessor: dict | None = None

    def reference(self):
        s = self.selection
        return dict(
            lane_id=self.lane_id,
            canonical_instrument_id=s.instrument_id,
            venue_native_id=s.venue_native_id,
            selected_rank=s.selected_rank,
            selection_id=s.selection_id,
            selection_digest=s.integrity_digest,
            universe_snapshot_id=self.universe_id,
            ranking_snapshot_id=s.ranking_snapshot_id,
            ranking_digest=s.ranking_integrity_digest,
            transition_id=self.transition_id,
            **(
                {"slot4_successor": {"predecessor": self.predecessor, "selection": s.to_dict()}}
                if self.predecessor is not None
                else {}
            ),
        )

    def require_current_v1(self, now):
        if not (
            datetime.fromisoformat(self.selection.valid_from.replace("Z", "+00:00")).timestamp()
            <= now
            <= datetime.fromisoformat(self.selection.valid_until.replace("Z", "+00:00")).timestamp()
        ):
            raise ValueError("RANKED_SLOT_CAP23_OUTSIDE_SELECTION_WINDOW")

    def require_binding_v1(self, bound):
        s = self.selection
        if (
            bound.instrument_id,
            bound.venue_native_id,
            bound.selection_id,
            bound.selection_integrity_digest,
            bound.ranking_snapshot_id,
            bound.ranking_integrity_digest,
            bound.universe_snapshot_id,
            bound.selection_state,
        ) != (
            s.instrument_id,
            s.venue_native_id,
            s.selection_id,
            s.integrity_digest,
            s.ranking_snapshot_id,
            s.ranking_integrity_digest,
            self.universe_id,
            s.state,
        ):
            raise ValueError("RANKED_SLOT_CAP24_ORIGINAL_REQUIRED")


def read_ranked_run_slot_v1(config):
    return _read_ranked_run_slot_v1(config, fixed_original_only=False)


def _read_ranked_run_slot_v1(config, *, fixed_original_only):
    lane = config["lane"]
    if lane not in ("LANE_1", "LANE_2", "LANE_4", "LANE_5") or config["authority"] != "NONE":
        raise ValueError("RANKED_SLOT_SCOPE_INVALID")
    source = config["n5_source"]
    topology, ranking, universe = (
        Path(source[k]) for k in ("topology_root", "ranking_root", "universe_root")
    )
    revision = source["repository_sha"]
    receipt = load_completed_selection_publication_v1(topology)
    policy = receipt["topology"]["initial_assignment_policy"] if receipt else None
    successor = policy == SHADOW_SLOT4_SUCCESSOR_POLICY
    if successor and fixed_original_only:
        raise ValueError("SHADOW_SLOT4_FIXED_PREDECESSOR_REQUIRED")
    recovered = recover_durable_lane_assignment_v1(
        topology_state_root_base=topology, recovery_mode=RECOVERY_MODE_RESTART
    )
    if (
        policy not in (FIXED_RANK_ASSIGNMENT_POLICY, SHADOW_SLOT4_SUCCESSOR_POLICY)
        or not recovered
        or receipt["transition_id"] != source["transition_id"]
        or receipt["topology_digest"] != topology_integrity_digest_v1(recovered.to_dict())
    ):
        raise ValueError("RANKED_SLOT_PUBLICATION_MISMATCH")
    slot = next((s for s in recovered.occupied_slots() if s.lane_id == lane), None)
    if slot is None:
        raise ValueError("RANKED_SLOT_NOT_OCCUPIED")
    selected = load_and_validate_selection_v1(
        Path(slot.lane_state_root), expected_repository_sha=revision
    )
    ranked = load_and_validate_ranking_snapshot_v1(ranking, expected_repository_sha=revision)
    governed = load_and_validate_universe_snapshot_v1(universe, expected_repository_sha=revision)
    if not (selected.ok and ranked.ok and governed.ok):
        raise ValueError("RANKED_SLOT_SOURCE_INTEGRITY_FAILURE")
    s, r, u = selected.selection, ranked.snapshot, governed.snapshot
    predecessor = None
    if successor:
        from src.ops.ranked_shadow_slot4_successor_v1 import validate_successor_source_v1

        predecessor = validate_successor_source_v1(config, receipt, s, r, u)
    identity = (config["canonical_instrument_id"], config["native_instrument_id"])
    rows = [
        i
        for i in u.instruments
        if (i.canonical_instrument_id, i.venue_native_inst_id) == identity and i.eligibility
    ]
    ranks = [
        c.rank
        for c in r.ranked_candidates
        if (c.canonical_instrument_id, c.venue_native_id) == identity
        and c.eligibility_status == "ELIGIBLE"
    ]
    if (
        s.state != "SELECTED_ACTIVE"
        or (s.instrument_id, s.venue_native_id) != identity
        or slot.canonical_instrument_id != s.instrument_id
        or ranks != [s.selected_rank]
        or (not successor and ranks != [int(lane.split("_")[1])])
        or len(rows) != 1
        or (s.selection_id, s.integrity_digest)
        != (source["selection_id"], source["selection_digest"])
        or receipt["selection_digests"].get(lane) != s.integrity_digest
        or (r.ranking_snapshot_id, r.integrity_digest)
        != (s.ranking_snapshot_id, s.ranking_integrity_digest)
        or (slot.ranking_snapshot_id, slot.ranking_integrity_digest)
        != (r.ranking_snapshot_id, r.integrity_digest)
        or slot.universe_snapshot_id != u.snapshot_id
        or r.universe_snapshot_id != u.snapshot_id
        or (r.universe_source_digest, r.universe_payload_digest)
        != (u.source_digest, u.payload_digest)
        or receipt != load_completed_selection_publication_v1(topology)
        or load_pending_selection_publication_v1(topology)
    ):
        raise ValueError("RANKED_SLOT_ORIGINAL_REFERENCE_MISMATCH")
    if not fixed_original_only and not successor and lane == "LANE_4":
        from src.ops.ranked_shadow_slot4_successor_v1 import successor_root_v1

        child = successor_root_v1(topology)
        if load_pending_selection_publication_v1(child) or load_completed_selection_publication_v1(
            child
        ):
            raise ValueError("SHADOW_SLOT4_PREDECESSOR_SUPERSEDED")
    return RankedRunSlotV1(
        lane,
        s,
        rows[0],
        u.snapshot_id,
        receipt["transition_id"],
        Path(slot.lane_state_root),
        predecessor,
    )


def read_ranked_shadow_profile_v1(path, instrument, session_id):
    if not isinstance(path, Path):
        raise ValueError("I17_RANKED_SWAP_N5_SOURCE_REQUIRED")
    config = json.loads(path.read_bytes())
    if (
        config.get("surface"),
        config.get("session_id"),
        config["lane"],
        config["native_instrument_id"],
        config["canonical_instrument_id"],
    ) != ("SHADOW", session_id, instrument.lane_id, instrument.native_id, instrument.canonical_id):
        raise ValueError("I17_RANKED_SWAP_SESSION_SCOPE_MISMATCH")
    return read_ranked_run_slot_v1(config)


def read_ranked_paper_slot_v1(config):
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import XperpPaperSlotV1

    assignment = read_ranked_run_slot_v1(config)
    row = assignment.instrument
    if (
        config["surface"],
        row.instrument_type,
        row.contract_type,
        row.quote_currency,
        row.settlement_currency,
    ) != ("PAPER_EXCHANGE", "FUTURES", "linear_dated_future", "USD", "USD"):
        raise ValueError("RANKED_PAPER_REQUIRES_USD_XPERP")
    slot = XperpPaperSlotV1(
        assignment.lane_id, row.base_currency, row.venue_native_inst_id.rsplit("-", 1)[-1]
    )
    if (slot.native_id, slot.instrument_id) != (
        row.venue_native_inst_id,
        row.canonical_instrument_id,
    ):
        raise ValueError("RANKED_PAPER_XPERP_IDENTITY_MISMATCH")
    return assignment, slot


def read_paper_entry_admission_v1(config, original):
    """Verify a later Cap23 selection against the immutable slot and its own Cap21/22."""
    return _read_ranked_entry_admission_v1(
        config, original, field="paper_entry_admission", surface="PAPER_EXCHANGE"
    )


def read_shadow_entry_admission_v1(config, original):
    return _read_ranked_entry_admission_v1(
        config, original, field="shadow_entry_admission", surface="SHADOW"
    )


def _read_ranked_entry_admission_v1(config, original, *, field, surface):
    source = config.get(field)
    if source is None:
        return original

    from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
        build_governed_cap23_pin_v1,
    )
    from src.ops.single_selected_future_policy_v1.selection_v1 import (
        produce_single_selected_future_v1,
    )

    prior = original.selection
    lane_root = Path(source["selection_root"])
    if (
        config["surface"] != surface
        or source["occupancy"] != original.reference()
        or lane_root.name != original.lane_id
        or lane_root.parent.name != config["session_id"]
        or lane_root != lane_root.resolve()
    ):
        raise ValueError(f"{field.upper()}_SCOPE_MISMATCH")
    revision = prior.repository_sha
    loaded = load_and_validate_selection_v1(lane_root, expected_repository_sha=revision)
    ranked = load_and_validate_ranking_snapshot_v1(
        Path(source["ranking_root"]), expected_repository_sha=revision
    )
    governed = load_and_validate_universe_snapshot_v1(
        Path(source["universe_root"]), expected_repository_sha=revision
    )
    if not (loaded.ok and ranked.ok and governed.ok):
        raise ValueError(f"{field.upper()}_ORIGINALS_REQUIRED")
    s, rank, universe = loaded.selection, ranked.snapshot, governed.snapshot
    rows = [
        row
        for row in universe.instruments
        if row.canonical_instrument_id == prior.instrument_id
        and row.venue_native_inst_id == prior.venue_native_id
        and row.eligibility
    ]
    if (
        len(rows) != 1
        or s.integrity_digest != source["selection_digest"]
        or s.state != "SELECTED_ACTIVE"
        or s.previous_selection_id != prior.selection_id
        or s.selected_at_event_time != prior.selected_at_event_time
        or s.config_digest != prior.config_digest
        or s.ranking_snapshot_id == prior.ranking_snapshot_id
        or (rank.universe_snapshot_id, rank.universe_source_digest, rank.universe_payload_digest)
        != (universe.snapshot_id, universe.source_digest, universe.payload_digest)
        or datetime.fromisoformat(rank.event_time.replace("Z", "+00:00"))
        <= datetime.fromisoformat(prior.ranking_event_time.replace("Z", "+00:00"))
    ):
        raise ValueError(f"{field.upper()}_LINEAGE_MISMATCH")
    pin = build_governed_cap23_pin_v1(
        canonical_instrument_id=prior.instrument_id,
        ranking_snapshot=rank.to_dict(),
        lane_state_root=lane_root,
    )
    replay = produce_single_selected_future_v1(
        ranking_snapshot=rank.to_dict(),
        repository_sha=revision,
        expected_ranking_repository_sha=revision,
        producer_observed_at_unix=datetime.fromisoformat(
            s.selected_at_wall_time.replace("Z", "+00:00")
        ).timestamp(),
        previous_selection=prior,
        governed_pin=pin,
        lane_state_root=lane_root,
    )
    if (
        not replay.ok
        or replay.hard_stop
        or replay.selection != s
        or pin.resolved_venue_native_id != prior.venue_native_id
    ):
        raise ValueError(f"{field.upper()}_POLICY_MISMATCH")
    return RankedRunSlotV1(
        original.lane_id, s, rows[0], universe.snapshot_id, original.transition_id, lane_root
    )


def read_recorded_paper_slot_v1(profile):
    """Recover the sealed entry identity without consulting a later ranking."""
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import XperpPaperSlotV1

    config = profile["ranked_config"]
    original = profile["n5_assignment"]
    bound = profile["instrument_binding"]
    lane = config["lane"]
    native = config["native_instrument_id"]
    match = re.fullmatch(r"([A-Z0-9]+)-USD_UM_XPERP-([0-9]{6})", native)
    if lane not in ("LANE_1", "LANE_2", "LANE_4", "LANE_5") or match is None:
        raise ValueError("RANKED_PAPER_ARCHIVE_IDENTITY_MISMATCH")
    slot = XperpPaperSlotV1(lane, *match.groups())
    source = config["n5_source"]
    admission = config.get("paper_entry_admission")
    entry = profile.get("paper_entry_admission")
    if (entry is None) != (admission is None):
        raise ValueError("RANKED_PAPER_ENTRY_ARCHIVE_INCOMPLETE")
    expected = dict(
        lane_id=lane,
        selected_rank=int(lane.split("_")[1]) if entry is None else entry["selected_rank"],
        canonical_instrument_id=slot.instrument_id,
        venue_native_id=slot.native_id,
        selection_id=bound["selection_id"],
        selection_digest=bound["selection_integrity_digest"],
        ranking_snapshot_id=bound["ranking_snapshot_id"],
        ranking_digest=bound["ranking_integrity_digest"],
        universe_snapshot_id=bound["universe_snapshot_id"],
        transition_id=source["transition_id"],
    )
    if (
        (original if entry is None else entry) != expected
        or (
            entry is not None
            and (
                original != admission["occupancy"]
                or original["lane_id"] != lane
                or original["selected_rank"] != int(lane.split("_")[1])
                or original["canonical_instrument_id"] != slot.instrument_id
                or original["venue_native_id"] != native
                or original["transition_id"] != source["transition_id"]
                or entry["selected_rank"] < 1
                or entry["selection_digest"] != admission["selection_digest"]
            )
        )
        or config["surface"] != "PAPER_EXCHANGE"
        or config["authority"] != "NONE"
        or config["canonical_instrument_id"] != slot.instrument_id
        or bound["instrument_id"] != slot.instrument_id
        or bound["venue_native_id"] != native
        or bound["selection_state"] != "SELECTED_ACTIVE"
        or original["selection_digest"] != source["selection_digest"]
        or original["selection_id"] != source["selection_id"]
        or not all(expected.values())
        or profile["binding"]["lane_id"] != lane
    ):
        raise ValueError("RANKED_PAPER_ARCHIVE_IDENTITY_MISMATCH")
    return slot

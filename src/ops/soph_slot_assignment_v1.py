"""Read SOPH's committed N5 lane selection without acquiring a writer or reranking."""

from dataclasses import dataclass
from pathlib import Path

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    RECOVERY_MODE_RESTART,
    load_completed_selection_publication_v1,
    load_pending_selection_publication_v1,
    recover_durable_lane_assignment_v1,
    topology_integrity_digest_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from src.ops.single_selected_future_policy_v1.persistence_v1 import load_and_validate_selection_v1


@dataclass(frozen=True)
class SophSlotAssignmentV1:
    selection: SingleSelectedFutureSelectionV1
    ranking: ProductiveFuturesRankingSnapshotV1
    universe: GovernedFuturesUniverseSnapshotV1
    lane_id: str

    def require_matching_binding(self, bound):
        from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
            assert_handoff_invariants_v1,
        )

        assert_handoff_invariants_v1(
            self.selection,
            bound,
            ranking_snapshot_id=self.ranking.ranking_snapshot_id,
            ranking_universe_snapshot_id=self.ranking.universe_snapshot_id,
            universe_snapshot_id=self.universe.snapshot_id,
        )
        if (
            bound.selection_integrity_digest != self.selection.integrity_digest
            or bound.ranking_integrity_digest != self.ranking.integrity_digest
        ):
            raise ValueError("SOPH_SLOT_CAP24_REFERENCE_MISMATCH")

    def card_reference(self):
        return dict(
            lane_id=self.lane_id,
            instrument_id=self.selection.instrument_id,
            venue_native_id=self.selection.venue_native_id,
            selected_rank=self.selection.selected_rank,
            selection_id=self.selection.selection_id,
            selection_integrity_digest=self.selection.integrity_digest,
            ranking_snapshot_id=self.ranking.ranking_snapshot_id,
            ranking_integrity_digest=self.ranking.integrity_digest,
            universe_snapshot_id=self.universe.snapshot_id,
            universe_source_digest=self.universe.source_digest,
            universe_payload_digest=self.universe.payload_digest,
            selection_state=self.selection.state,
            valid_from=self.selection.valid_from,
            valid_until=self.selection.valid_until,
            repository_sha=self.selection.repository_sha,
        )


@dataclass(frozen=True)
class SophSlotSourcesV1:
    topology_root: Path
    ranking_root: Path
    universe_root: Path

    def inspect(self, repository_sha: str) -> SophSlotAssignmentV1:
        if not repository_sha:
            raise ValueError("SOPH_SLOT_REPOSITORY_REQUIRED")
        receipt = load_completed_selection_publication_v1(self.topology_root)
        topology = recover_durable_lane_assignment_v1(
            topology_state_root_base=self.topology_root, recovery_mode=RECOVERY_MODE_RESTART
        )
        if receipt is None or topology is None:
            raise ValueError("SOPH_SLOT_COMPLETED_PUBLICATION_REQUIRED")
        if receipt.get("topology_digest") != topology_integrity_digest_v1(topology.to_dict()):
            raise ValueError("SOPH_SLOT_COMPLETED_PUBLICATION_REQUIRED")
        slot = next((s for s in topology.occupied_slots() if s.lane_id == SOPH_I17.lane_id), None)
        if slot is None or slot.canonical_instrument_id != SOPH_I17.canonical_id:
            raise ValueError("SOPH_SLOT_ORIGINAL_LANE_MISMATCH")
        selected = load_and_validate_selection_v1(
            Path(slot.lane_state_root), expected_repository_sha=repository_sha
        )
        ranked = load_and_validate_ranking_snapshot_v1(
            self.ranking_root, expected_repository_sha=repository_sha
        )
        governed = load_and_validate_universe_snapshot_v1(
            self.universe_root, expected_repository_sha=repository_sha
        )
        if not (selected.ok and ranked.ok and governed.ok):
            raise ValueError("SOPH_SLOT_SELECTION_RANKING_UNIVERSE_SOURCE_INVALID")
        selection, ranking, universe = selected.selection, ranked.snapshot, governed.snapshot
        # A retained slot can refer to an older ranking than the overall topology.
        ranking_ref = (ranking.ranking_snapshot_id, ranking.integrity_digest)
        instrument = (slot.canonical_instrument_id, SOPH_I17.native_id)
        ranks = [
            r.rank
            for r in ranking.ranked_candidates
            if (r.canonical_instrument_id, r.venue_native_id) == instrument
        ]
        universe_rows = [
            i
            for i in universe.instruments
            if (i.canonical_instrument_id, i.venue_native_inst_id) == instrument
        ]
        lane_digests = receipt.get("selection_digests")
        if (
            not isinstance(lane_digests, dict)
            or lane_digests.get(slot.lane_id) != selection.integrity_digest
            or (selection.instrument_id, selection.venue_native_id) != instrument
            or (slot.ranking_snapshot_id, slot.ranking_integrity_digest) != ranking_ref
            or (selection.ranking_snapshot_id, selection.ranking_integrity_digest) != ranking_ref
            or slot.universe_snapshot_id != universe.snapshot_id
            or ranking.universe_snapshot_id != universe.snapshot_id
            or ranking.universe_payload_digest != universe.payload_digest
            or ranking.universe_source_digest != universe.source_digest
            or ranks != [selection.selected_rank]
            or len(universe_rows) != 1
        ):
            raise ValueError("SOPH_SLOT_ORIGINAL_REFERENCE_MISMATCH")
        if (
            load_completed_selection_publication_v1(self.topology_root) != receipt
            or load_pending_selection_publication_v1(self.topology_root) is not None
        ):
            raise ValueError("SOPH_SLOT_PUBLICATION_CHANGED")
        return SophSlotAssignmentV1(selection, ranking, universe, slot.lane_id)

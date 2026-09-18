"""Map governed MF membership identity onto isolated Single-Future lane slots.

Owns only membership-identity → lane-instance-identity. Does not rank, select,
bind, trade, persist Cap23, or join a productive host.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Optional, Sequence

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.adapter_v1 import (
    build_governed_cap23_pin_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    CONTRACT_ID,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    ENTRY_POLICY,
    EXIT_POLICY,
    FIVE_LANE_RUNTIME_CREATED,
    FREE_LANE_ASSIGNMENT_POLICY,
    INITIAL_ASSIGNMENT_POLICY,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    LANE_CARDINALITY_MODE,
    LANE_IDS,
    LANE_IDENTITY_ENCODES_RANK,
    LANE_MAPPING_OWNER,
    LANE_TOPOLOGY_CAP23_SELECTION_AUTHORITY,
    LANE_TOPOLOGY_CAP24_BINDING_AUTHORITY,
    LANE_TOPOLOGY_EXECUTION_AUTHORITY,
    LANE_TOPOLOGY_MEMBERSHIP_AUTHORITY,
    LANE_TOPOLOGY_RANKING_AUTHORITY,
    LANE_TOPOLOGY_TRADING_AUTHORITY,
    MAX_LANE_COUNT,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MULTI_UNIVERSE_MERGE,
    NO_PADDING,
    OCCUPANCY_EMPTY,
    OCCUPANCY_OCCUPIED,
    ONE_INSTRUMENT_PER_LANE,
    ONE_LANE_PER_INSTRUMENT,
    OWNER,
    PURE_RANK_REORDER_CAUSES_LANE_MOVE,
    RESTART_RECONSTRUCTION_POLICY,
    RETAINED_MEMBER_POLICY,
    SCHEMA_VERSION,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    MembershipContextArtifactV1,
    validate_membership_context_artifact_v1,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import (
    GovernedCap23InstrumentPinV1,
    lane_state_root_key,
)

FAILURE_CARDINALITY_EXCEEDS_MAX = "LANE_CARDINALITY_EXCEEDS_MAX"
FAILURE_DUPLICATE_INSTRUMENT = "LANE_DUPLICATE_INSTRUMENT"
FAILURE_CROSS_UNIVERSE = "LANE_CROSS_UNIVERSE_FORBIDDEN"
FAILURE_PROVENANCE_MISMATCH = "LANE_PROVENANCE_MISMATCH"
FAILURE_STATE_ROOT_MISMATCH = "LANE_STATE_ROOT_MISMATCH"
FAILURE_RESTART_WITHOUT_PRIOR = "LANE_RESTART_WITHOUT_PRIOR_FORBIDDEN"
FAILURE_INSTRUMENT_NOT_IN_RANKING = "LANE_INSTRUMENT_NOT_IN_RANKING"
FAILURE_CORRUPT_PRIOR = "LANE_CORRUPT_PRIOR"
FAILURE_PADDING_FORBIDDEN = "LANE_PADDING_FORBIDDEN"
FAILURE_EXTRA_RANKING = "LANE_CROSS_UNIVERSE_FORBIDDEN"
FAILURE_INVALID_LANE_ID = "LANE_IDENTITY_INVALID"


class IsolatedLaneTopologyError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise IsolatedLaneTopologyError(code, detail)


def lane_state_root_for(*, topology_state_root_base: Path | str, lane_id: str) -> str:
    if lane_id not in LANE_IDS:
        _fail(FAILURE_INVALID_LANE_ID, lane_id)
    return lane_state_root_key(Path(topology_state_root_base) / lane_id)


def _require_snapshot_field(snapshot: Mapping[str, Any], key: str) -> str:
    value = str(snapshot.get(key) or "").strip()
    if not value:
        _fail(FAILURE_PROVENANCE_MISMATCH, key)
    return value


def _instrument_rows(
    ranking_snapshot: Mapping[str, Any], instrument_id: str
) -> list[Mapping[str, Any]]:
    ranked = list(ranking_snapshot.get("ranked_candidates") or [])
    return [
        row
        for row in ranked
        if isinstance(row, Mapping)
        and str(row.get("canonical_instrument_id") or "").strip() == instrument_id
    ]


def _validate_member_in_same_universe_ranking(
    *,
    instrument_id: str,
    ranking_snapshot: Mapping[str, Any],
) -> None:
    matches = _instrument_rows(ranking_snapshot, instrument_id)
    if not matches:
        _fail(FAILURE_INSTRUMENT_NOT_IN_RANKING, instrument_id)
    natives = {str(row.get("venue_native_id") or "").strip() for row in matches}
    if len(matches) != 1 or len(natives) != 1 or not next(iter(natives)):
        _fail(FAILURE_DUPLICATE_INSTRUMENT, instrument_id)


def _empty_slot(*, lane_id: str, topology_state_root_base: Path | str) -> "IsolatedLaneSlotV1":
    return IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=OCCUPANCY_EMPTY,
        canonical_instrument_id=None,
        lane_state_root=lane_state_root_for(
            topology_state_root_base=topology_state_root_base, lane_id=lane_id
        ),
        universe_snapshot_id=None,
        ranking_snapshot_id=None,
        ranking_integrity_digest=None,
    )


def _occupied_slot(
    *,
    lane_id: str,
    instrument_id: str,
    topology_state_root_base: Path | str,
    universe_snapshot_id: str,
    ranking_snapshot_id: str,
    ranking_integrity_digest: str,
) -> "IsolatedLaneSlotV1":
    return IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=instrument_id,
        lane_state_root=lane_state_root_for(
            topology_state_root_base=topology_state_root_base, lane_id=lane_id
        ),
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
    )


@dataclass(frozen=True)
class IsolatedLaneSlotV1:
    lane_id: str
    occupancy: str
    canonical_instrument_id: Optional[str]
    lane_state_root: str
    universe_snapshot_id: Optional[str]
    ranking_snapshot_id: Optional[str]
    ranking_integrity_digest: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "lane_id": self.lane_id,
            "lane_state_root": self.lane_state_root,
            "occupancy": self.occupancy,
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "universe_snapshot_id": self.universe_snapshot_id,
        }


@dataclass(frozen=True)
class IsolatedLaneTopologyV1:
    schema_version: str
    owner: str
    contract_id: str
    topology_state_root_base: str
    membership_instance_id: str
    universe_snapshot_id: str
    ranking_snapshot_id: str
    ranking_integrity_digest: str
    slots: tuple[IsolatedLaneSlotV1, ...]
    occupied_count: int
    occupied_instrument_ids: tuple[str, ...]
    lane_identity_encodes_rank: bool
    no_padding: bool
    one_instrument_per_lane: bool
    one_lane_per_instrument: bool
    pure_rank_reorder_causes_lane_move: bool
    mf_productive_join: bool
    five_lane_runtime_created: bool
    max_positions_effective: int
    initial_assignment_policy: str
    retained_member_policy: str
    exit_policy: str
    entry_policy: str
    free_lane_assignment_policy: str
    restart_reconstruction_policy: str

    def occupied_slots(self) -> tuple[IsolatedLaneSlotV1, ...]:
        return tuple(slot for slot in self.slots if slot.occupancy == OCCUPANCY_OCCUPIED)

    def empty_slots(self) -> tuple[IsolatedLaneSlotV1, ...]:
        return tuple(slot for slot in self.slots if slot.occupancy == OCCUPANCY_EMPTY)

    def instrument_to_lane(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for slot in self.occupied_slots():
            instrument_id = str(slot.canonical_instrument_id or "").strip()
            mapping[instrument_id] = slot.lane_id
        return mapping

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "entry_policy": self.entry_policy,
            "exit_policy": self.exit_policy,
            "five_lane_runtime_created": bool(self.five_lane_runtime_created),
            "free_lane_assignment_policy": self.free_lane_assignment_policy,
            "initial_assignment_policy": self.initial_assignment_policy,
            "lane_identity_encodes_rank": bool(self.lane_identity_encodes_rank),
            "max_positions_effective": int(self.max_positions_effective),
            "membership_instance_id": self.membership_instance_id,
            "mf_productive_join": bool(self.mf_productive_join),
            "no_padding": bool(self.no_padding),
            "occupied_count": int(self.occupied_count),
            "occupied_instrument_ids": list(self.occupied_instrument_ids),
            "one_instrument_per_lane": bool(self.one_instrument_per_lane),
            "one_lane_per_instrument": bool(self.one_lane_per_instrument),
            "owner": self.owner,
            "pure_rank_reorder_causes_lane_move": bool(self.pure_rank_reorder_causes_lane_move),
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "restart_reconstruction_policy": self.restart_reconstruction_policy,
            "retained_member_policy": self.retained_member_policy,
            "schema_version": self.schema_version,
            "slots": [slot.to_dict() for slot in self.slots],
            "topology_state_root_base": self.topology_state_root_base,
            "universe_snapshot_id": self.universe_snapshot_id,
        }


def _validate_slots(
    slots: Sequence[IsolatedLaneSlotV1],
    *,
    topology_state_root_base: Path | str,
    universe_snapshot_id: str,
    ranking_snapshot_id: str,
    ranking_integrity_digest: str,
) -> tuple[IsolatedLaneSlotV1, ...]:
    if len(slots) != MAX_LANE_COUNT:
        _fail(FAILURE_CORRUPT_PRIOR, f"slot_count={len(slots)}")
    expected_ids = list(LANE_IDS)
    actual_ids = [slot.lane_id for slot in slots]
    if actual_ids != expected_ids:
        _fail(FAILURE_INVALID_LANE_ID, ",".join(actual_ids))
    occupied_ids: list[str] = []
    seen_instruments: set[str] = set()
    for slot in slots:
        expected_root = lane_state_root_for(
            topology_state_root_base=topology_state_root_base, lane_id=slot.lane_id
        )
        if lane_state_root_key(slot.lane_state_root) != expected_root:
            _fail(FAILURE_STATE_ROOT_MISMATCH, slot.lane_id)
        if slot.occupancy == OCCUPANCY_EMPTY:
            if (
                slot.canonical_instrument_id is not None
                or slot.universe_snapshot_id is not None
                or slot.ranking_snapshot_id is not None
                or slot.ranking_integrity_digest is not None
            ):
                _fail(FAILURE_PADDING_FORBIDDEN, slot.lane_id)
            continue
        if slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_CORRUPT_PRIOR, slot.occupancy)
        instrument_id = str(slot.canonical_instrument_id or "").strip()
        if not instrument_id:
            _fail(FAILURE_CORRUPT_PRIOR, f"empty_instrument:{slot.lane_id}")
        if instrument_id in seen_instruments:
            _fail(FAILURE_DUPLICATE_INSTRUMENT, instrument_id)
        seen_instruments.add(instrument_id)
        occupied_ids.append(instrument_id)
        if slot.universe_snapshot_id != universe_snapshot_id:
            _fail(FAILURE_CROSS_UNIVERSE, slot.lane_id)
        if (
            slot.ranking_snapshot_id != ranking_snapshot_id
            or slot.ranking_integrity_digest != ranking_integrity_digest
        ):
            _fail(FAILURE_PROVENANCE_MISMATCH, slot.lane_id)
    if len(occupied_ids) > MAX_LANE_COUNT:
        _fail(FAILURE_CARDINALITY_EXCEEDS_MAX, str(len(occupied_ids)))
    return tuple(slots)


def _finish_topology(
    *,
    membership: MembershipContextArtifactV1,
    topology_state_root_base: Path | str,
    universe_snapshot_id: str,
    ranking_snapshot_id: str,
    ranking_integrity_digest: str,
    slots: Sequence[IsolatedLaneSlotV1],
) -> IsolatedLaneTopologyV1:
    validated = _validate_slots(
        slots,
        topology_state_root_base=topology_state_root_base,
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
    )
    occupied = tuple(
        str(slot.canonical_instrument_id)
        for slot in validated
        if slot.occupancy == OCCUPANCY_OCCUPIED
    )
    return IsolatedLaneTopologyV1(
        schema_version=SCHEMA_VERSION,
        owner=OWNER,
        contract_id=CONTRACT_ID,
        topology_state_root_base=lane_state_root_key(topology_state_root_base),
        membership_instance_id=membership.instance_id,
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
        slots=validated,
        occupied_count=len(occupied),
        occupied_instrument_ids=occupied,
        lane_identity_encodes_rank=LANE_IDENTITY_ENCODES_RANK,
        no_padding=NO_PADDING,
        one_instrument_per_lane=ONE_INSTRUMENT_PER_LANE,
        one_lane_per_instrument=ONE_LANE_PER_INSTRUMENT,
        pure_rank_reorder_causes_lane_move=PURE_RANK_REORDER_CAUSES_LANE_MOVE,
        mf_productive_join=MF_PRODUCTIVE_JOIN,
        five_lane_runtime_created=FIVE_LANE_RUNTIME_CREATED,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
        initial_assignment_policy=INITIAL_ASSIGNMENT_POLICY,
        retained_member_policy=RETAINED_MEMBER_POLICY,
        exit_policy=EXIT_POLICY,
        entry_policy=ENTRY_POLICY,
        free_lane_assignment_policy=FREE_LANE_ASSIGNMENT_POLICY,
        restart_reconstruction_policy=RESTART_RECONSTRUCTION_POLICY,
    )


def isolated_lane_topology_from_dict(payload: Mapping[str, Any]) -> IsolatedLaneTopologyV1:
    if not isinstance(payload, Mapping):
        _fail(FAILURE_CORRUPT_PRIOR, "not_object")
    slots_raw = payload.get("slots") or []
    if not isinstance(slots_raw, list):
        _fail(FAILURE_CORRUPT_PRIOR, "slots")
    slots: list[IsolatedLaneSlotV1] = []
    for raw in slots_raw:
        if not isinstance(raw, Mapping):
            _fail(FAILURE_CORRUPT_PRIOR, "slot")
        instrument_raw = raw.get("canonical_instrument_id")
        slots.append(
            IsolatedLaneSlotV1(
                lane_id=str(raw.get("lane_id") or ""),
                occupancy=str(raw.get("occupancy") or ""),
                canonical_instrument_id=(
                    None if instrument_raw is None else str(instrument_raw).strip() or None
                ),
                lane_state_root=str(raw.get("lane_state_root") or ""),
                universe_snapshot_id=(
                    None
                    if raw.get("universe_snapshot_id") is None
                    else str(raw.get("universe_snapshot_id") or "").strip() or None
                ),
                ranking_snapshot_id=(
                    None
                    if raw.get("ranking_snapshot_id") is None
                    else str(raw.get("ranking_snapshot_id") or "").strip() or None
                ),
                ranking_integrity_digest=(
                    None
                    if raw.get("ranking_integrity_digest") is None
                    else str(raw.get("ranking_integrity_digest") or "").strip() or None
                ),
            )
        )
    membership_instance_id = str(payload.get("membership_instance_id") or "").strip()
    universe_snapshot_id = str(payload.get("universe_snapshot_id") or "").strip()
    ranking_snapshot_id = str(payload.get("ranking_snapshot_id") or "").strip()
    ranking_integrity_digest = str(payload.get("ranking_integrity_digest") or "").strip()
    base = str(payload.get("topology_state_root_base") or "").strip()
    if not membership_instance_id or not universe_snapshot_id or not ranking_snapshot_id:
        _fail(FAILURE_CORRUPT_PRIOR, "identity")
    if not ranking_integrity_digest or not base:
        _fail(FAILURE_CORRUPT_PRIOR, "identity")
    validated = _validate_slots(
        slots,
        topology_state_root_base=base,
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
    )
    occupied = tuple(
        str(slot.canonical_instrument_id)
        for slot in validated
        if slot.occupancy == OCCUPANCY_OCCUPIED
    )
    return IsolatedLaneTopologyV1(
        schema_version=str(payload.get("schema_version") or SCHEMA_VERSION),
        owner=str(payload.get("owner") or OWNER),
        contract_id=str(payload.get("contract_id") or CONTRACT_ID),
        topology_state_root_base=lane_state_root_key(base),
        membership_instance_id=membership_instance_id,
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
        slots=validated,
        occupied_count=len(occupied),
        occupied_instrument_ids=occupied,
        lane_identity_encodes_rank=bool(payload.get("lane_identity_encodes_rank", False)),
        no_padding=bool(payload.get("no_padding", True)),
        one_instrument_per_lane=bool(payload.get("one_instrument_per_lane", True)),
        one_lane_per_instrument=bool(payload.get("one_lane_per_instrument", True)),
        pure_rank_reorder_causes_lane_move=bool(
            payload.get("pure_rank_reorder_causes_lane_move", False)
        ),
        mf_productive_join=bool(payload.get("mf_productive_join", False)),
        five_lane_runtime_created=bool(payload.get("five_lane_runtime_created", False)),
        max_positions_effective=int(
            payload.get("max_positions_effective") or MAX_POSITIONS_EFFECTIVE
        ),
        initial_assignment_policy=str(
            payload.get("initial_assignment_policy") or INITIAL_ASSIGNMENT_POLICY
        ),
        retained_member_policy=str(payload.get("retained_member_policy") or RETAINED_MEMBER_POLICY),
        exit_policy=str(payload.get("exit_policy") or EXIT_POLICY),
        entry_policy=str(payload.get("entry_policy") or ENTRY_POLICY),
        free_lane_assignment_policy=str(
            payload.get("free_lane_assignment_policy") or FREE_LANE_ASSIGNMENT_POLICY
        ),
        restart_reconstruction_policy=str(
            payload.get("restart_reconstruction_policy") or RESTART_RECONSTRUCTION_POLICY
        ),
    )


def apply_isolated_lane_topology_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    prior_topology: IsolatedLaneTopologyV1 | None = None,
    replacement_ranking_snapshot: Mapping[str, Any] | None = None,
    fallback_ranking_snapshot: Mapping[str, Any] | None = None,
    underfill_ranking_snapshot: Mapping[str, Any] | None = None,
) -> IsolatedLaneTopologyV1:
    """Assign governed members to opaque LANE_1..LANE_5 slots.

    Rank order is not lane identity. Missing prior topology on a non-bootstrap
    membership fails closed; this function does not invent restart persistence.
    """
    if (
        LANE_TOPOLOGY_RANKING_AUTHORITY
        or LANE_TOPOLOGY_MEMBERSHIP_AUTHORITY
        or LANE_TOPOLOGY_CAP23_SELECTION_AUTHORITY
        or LANE_TOPOLOGY_CAP24_BINDING_AUTHORITY
        or LANE_TOPOLOGY_TRADING_AUTHORITY
        or LANE_TOPOLOGY_EXECUTION_AUTHORITY
    ):
        _fail("LANE_AUTHORITY_CLAIM_FORBIDDEN", OWNER)
    if (
        CROSS_UNIVERSE_SELECTION
        or CROSS_UNIVERSE_PIN
        or CROSS_UNIVERSE_REPLACEMENT
        or CROSS_UNIVERSE_FALLBACK
        or CROSS_UNIVERSE_CANDIDATE_BORROWING
        or CROSS_UNIVERSE_RERANKING
        or MULTI_UNIVERSE_MERGE
        or INSTRUMENT_ID_ALONE_SUFFICIENT
    ):
        _fail(FAILURE_CROSS_UNIVERSE, "constant_violation")
    if (
        replacement_ranking_snapshot is not None
        or fallback_ranking_snapshot is not None
        or underfill_ranking_snapshot is not None
    ):
        _fail(FAILURE_EXTRA_RANKING, "extra_ranking")
    if not isinstance(ranking_snapshot, Mapping):
        _fail(FAILURE_PROVENANCE_MISMATCH, "ranking_snapshot")
    if LANE_CARDINALITY_MODE != "AT_MOST_N" or not UNIVERSE_ISOLATION_ENFORCED:
        _fail(FAILURE_CORRUPT_PRIOR, "cardinality_mode")

    decided = validate_membership_context_artifact_v1(membership)
    current_ids = list(decided.ordered_instrument_ids)
    if len(current_ids) > MAX_LANE_COUNT:
        _fail(FAILURE_CARDINALITY_EXCEEDS_MAX, str(len(current_ids)))
    if len(set(current_ids)) != len(current_ids):
        _fail(FAILURE_DUPLICATE_INSTRUMENT, ",".join(current_ids))

    universe_snapshot_id = _require_snapshot_field(ranking_snapshot, "universe_snapshot_id")
    ranking_snapshot_id = _require_snapshot_field(ranking_snapshot, "ranking_snapshot_id")
    ranking_integrity_digest = _require_snapshot_field(ranking_snapshot, "integrity_digest")
    provenance = decided.cap22_provenance
    if provenance.universe_snapshot_id != universe_snapshot_id:
        _fail(FAILURE_CROSS_UNIVERSE, "universe_snapshot_id")
    if provenance.ranking_snapshot_id != ranking_snapshot_id:
        _fail(FAILURE_PROVENANCE_MISMATCH, "ranking_snapshot_id")
    if provenance.ranking_integrity_digest != ranking_integrity_digest:
        _fail(FAILURE_PROVENANCE_MISMATCH, "integrity_digest")

    for instrument_id in current_ids:
        _validate_member_in_same_universe_ranking(
            instrument_id=instrument_id, ranking_snapshot=ranking_snapshot
        )

    base = Path(topology_state_root_base)
    assignment: dict[str, str] = {}

    if prior_topology is None:
        if not decided.bootstrap:
            _fail(FAILURE_RESTART_WITHOUT_PRIOR, decided.instance_id)
        for lane_id, instrument_id in zip(LANE_IDS, current_ids):
            assignment[instrument_id] = lane_id
    else:
        if prior_topology.universe_snapshot_id != universe_snapshot_id:
            _fail(FAILURE_CROSS_UNIVERSE, "prior_universe")
        if lane_state_root_key(prior_topology.topology_state_root_base) != lane_state_root_key(
            base
        ):
            _fail(FAILURE_STATE_ROOT_MISMATCH, "topology_state_root_base")
        _validate_slots(
            prior_topology.slots,
            topology_state_root_base=prior_topology.topology_state_root_base,
            universe_snapshot_id=prior_topology.universe_snapshot_id,
            ranking_snapshot_id=prior_topology.ranking_snapshot_id,
            ranking_integrity_digest=prior_topology.ranking_integrity_digest,
        )
        prior_map = prior_topology.instrument_to_lane()
        prior_set = set(prior_map)
        current_set = set(current_ids)
        retained = [item for item in current_ids if item in prior_set]
        entered = [item for item in current_ids if item not in prior_set]
        for instrument_id in retained:
            assignment[instrument_id] = prior_map[instrument_id]
        occupied_after_retain = {assignment[item] for item in retained}
        empty_lane_ids = [lane_id for lane_id in LANE_IDS if lane_id not in occupied_after_retain]
        if len(entered) > len(empty_lane_ids):
            _fail(FAILURE_CARDINALITY_EXCEEDS_MAX, str(len(entered)))
        for instrument_id, lane_id in zip(entered, empty_lane_ids):
            assignment[instrument_id] = lane_id

    slots: list[IsolatedLaneSlotV1] = []
    lane_to_instrument = {lane_id: instrument_id for instrument_id, lane_id in assignment.items()}
    if len(lane_to_instrument) != len(assignment):
        _fail(FAILURE_DUPLICATE_INSTRUMENT, "lane_collision")
    for lane_id in LANE_IDS:
        instrument_id = lane_to_instrument.get(lane_id)
        if instrument_id is None:
            slots.append(_empty_slot(lane_id=lane_id, topology_state_root_base=base))
            continue
        slots.append(
            _occupied_slot(
                lane_id=lane_id,
                instrument_id=instrument_id,
                topology_state_root_base=base,
                universe_snapshot_id=universe_snapshot_id,
                ranking_snapshot_id=ranking_snapshot_id,
                ranking_integrity_digest=ranking_integrity_digest,
            )
        )
    return _finish_topology(
        membership=decided,
        topology_state_root_base=base,
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
        slots=slots,
    )


def build_occupied_lane_pins_v1(
    topology: IsolatedLaneTopologyV1,
    *,
    ranking_snapshot: Mapping[str, Any],
) -> dict[str, GovernedCap23InstrumentPinV1]:
    """Build existing #6592 pins for occupied lanes. Does not write Cap23."""
    if not isinstance(ranking_snapshot, Mapping):
        _fail(FAILURE_PROVENANCE_MISMATCH, "ranking_snapshot")
    universe_snapshot_id = _require_snapshot_field(ranking_snapshot, "universe_snapshot_id")
    ranking_snapshot_id = _require_snapshot_field(ranking_snapshot, "ranking_snapshot_id")
    ranking_integrity_digest = _require_snapshot_field(ranking_snapshot, "integrity_digest")
    if universe_snapshot_id != topology.universe_snapshot_id:
        _fail(FAILURE_CROSS_UNIVERSE, "pin_universe")
    if (
        ranking_snapshot_id != topology.ranking_snapshot_id
        or ranking_integrity_digest != topology.ranking_integrity_digest
    ):
        _fail(FAILURE_PROVENANCE_MISMATCH, "pin_ranking")
    pins: dict[str, GovernedCap23InstrumentPinV1] = {}
    for slot in topology.occupied_slots():
        instrument_id = str(slot.canonical_instrument_id or "").strip()
        pin = build_governed_cap23_pin_v1(
            canonical_instrument_id=instrument_id,
            ranking_snapshot=ranking_snapshot,
            lane_state_root=slot.lane_state_root,
        )
        if pin.lane_state_root != slot.lane_state_root:
            _fail(FAILURE_STATE_ROOT_MISMATCH, slot.lane_id)
        pins[slot.lane_id] = pin
    return pins

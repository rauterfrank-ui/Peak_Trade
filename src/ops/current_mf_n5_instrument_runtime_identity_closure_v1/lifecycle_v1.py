"""Position-aware membership / topology lifecycle pins (D5)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.ops.hard_facts_system_closure_v1.position_aware_rotation_v1 import (
    PositionAwareRotationDecisionV1,
    RotationPhase,
    evaluate_position_aware_rotation_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    MembershipContextArtifactV1,
    build_membership_context_artifact_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)


class LaneLifecycleMode(str, Enum):
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    EXIT_ONLY = "EXIT_ONLY"
    RELEASE_PENDING = "RELEASE_PENDING"
    FLAT_RELEASED = "FLAT_RELEASED"


@dataclass(frozen=True)
class OpenPositionCustodyPinV1:
    instrument_id: str
    lane_id: str | None
    mode: LaneLifecycleMode
    retain_in_membership: bool


def open_position_instrument_ids_v1(
    portfolio: PortfolioTruthSnapshotV1 | None,
) -> frozenset[str]:
    if portfolio is None:
        return frozenset()
    open_ids: set[str] = set()
    for pos in portfolio.positions:
        if str(pos.side or "").upper() in {"LONG", "SHORT"}:
            open_ids.add(str(pos.instrument_id))
        elif pos.signed_quantity != 0:
            open_ids.add(str(pos.instrument_id))
    return frozenset(open_ids)


def pin_open_positions_in_membership_v1(
    membership: MembershipContextArtifactV1,
    *,
    portfolio: PortfolioTruthSnapshotV1 | None,
    instrument_to_lane: dict[str, str] | None = None,
) -> MembershipContextArtifactV1:
    """Ranking may drop members; open positions stay in membership for custody."""
    open_ids = open_position_instrument_ids_v1(portfolio)
    if not open_ids:
        return membership
    ordered = list(membership.ordered_instrument_ids)
    changed = False
    for inst in sorted(open_ids):
        if inst not in ordered:
            ordered.append(inst)
            changed = True
    if not changed:
        return membership
    prior_ref = None if membership.bootstrap else membership.instance_id
    return build_membership_context_artifact_v1(
        ordered_instrument_ids=tuple(ordered),
        cap22_provenance=membership.cap22_provenance,
        bootstrap=membership.bootstrap,
        prior_membership_reference=prior_ref,
    )


def evaluate_lane_lifecycle_for_instrument_v1(
    *,
    instrument_id: str,
    in_current_membership: bool,
    venue_flat: bool,
    reconciled: bool,
) -> OpenPositionCustodyPinV1:
    if venue_flat and reconciled:
        mode = (
            LaneLifecycleMode.FLAT_RELEASED
            if not in_current_membership
            else LaneLifecycleMode.ACTIVE
        )
        return OpenPositionCustodyPinV1(
            instrument_id=instrument_id,
            lane_id=None,
            mode=mode,
            retain_in_membership=False,
        )
    if not venue_flat:
        mode = (
            LaneLifecycleMode.DRAINING if not in_current_membership else LaneLifecycleMode.EXIT_ONLY
        )
        return OpenPositionCustodyPinV1(
            instrument_id=instrument_id,
            lane_id=None,
            mode=mode,
            retain_in_membership=True,
        )
    return OpenPositionCustodyPinV1(
        instrument_id=instrument_id,
        lane_id=None,
        mode=LaneLifecycleMode.RELEASE_PENDING,
        retain_in_membership=True,
    )


def rotation_decision_for_lane_v1(
    *,
    venue_flat: bool,
    reconciled: bool,
    lane_health_allows_replacement: bool,
    phase: RotationPhase = RotationPhase.COMMIT,
) -> PositionAwareRotationDecisionV1:
    return evaluate_position_aware_rotation_v1(
        phase=phase,
        venue_flat=venue_flat,
        reconciled=reconciled,
        pending_external_custody=False,
        pending_pre_external_custody=False,
        lane_health_allows_replacement=lane_health_allows_replacement,
    )

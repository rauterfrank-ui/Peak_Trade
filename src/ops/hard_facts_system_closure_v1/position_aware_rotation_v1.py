"""Membership proposal vs replacement commit under open-position custody rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RotationPhase(str, Enum):
    PROPOSAL = "proposal"
    COMMIT = "commit"


@dataclass(frozen=True)
class PositionAwareRotationDecisionV1:
    phase: RotationPhase
    allowed: bool
    reason_code: str
    retain_custody_for_open_position: bool


def evaluate_position_aware_rotation_v1(
    *,
    phase: RotationPhase,
    venue_flat: bool,
    reconciled: bool,
    pending_external_custody: bool,
    pending_pre_external_custody: bool,
    lane_health_allows_replacement: bool,
) -> PositionAwareRotationDecisionV1:
    custody_conflict = pending_external_custody or pending_pre_external_custody
    if not venue_flat:
        return PositionAwareRotationDecisionV1(
            phase=phase,
            allowed=False,
            reason_code="OPEN_POSITION_CUSTODY_RETAINED",
            retain_custody_for_open_position=True,
        )
    if not reconciled:
        return PositionAwareRotationDecisionV1(
            phase=phase,
            allowed=False,
            reason_code="NOT_RECONCILED",
            retain_custody_for_open_position=False,
        )
    if custody_conflict:
        return PositionAwareRotationDecisionV1(
            phase=phase,
            allowed=False,
            reason_code="PENDING_CUSTODY_CONFLICT",
            retain_custody_for_open_position=False,
        )
    if phase == RotationPhase.PROPOSAL:
        return PositionAwareRotationDecisionV1(
            phase=phase,
            allowed=lane_health_allows_replacement,
            reason_code="PROPOSAL_OK" if lane_health_allows_replacement else "PROPOSAL_VETO",
            retain_custody_for_open_position=False,
        )
    return PositionAwareRotationDecisionV1(
        phase=phase,
        allowed=lane_health_allows_replacement,
        reason_code="COMMIT_OK" if lane_health_allows_replacement else "COMMIT_VETO",
        retain_custody_for_open_position=False,
    )

"""Lane health → membership / replacement qualification (veto-only, not ranking owner)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LaneHealthClass(str, Enum):
    TRANSIENT_HOLD = "transient_hold"
    ENTRY_VETO = "entry_veto"
    DEGRADED_DATA = "degraded_data"
    QUARANTINE = "quarantine"
    LANE_LOCAL_FATAL = "lane_local_fatal"
    INSTRUMENT_FATAL = "instrument_fatal"
    GLOBAL_HALT = "global_halt"


@dataclass(frozen=True)
class LaneHealthMembershipFeedbackV1:
    health_class: LaneHealthClass
    may_propose_membership_replacement: bool
    may_commit_replacement: bool
    blocks_entry_only: bool
    triggers_membership_churn: bool
    reason_code: str


def classify_lane_health_membership_feedback_v1(
    *,
    health_class: LaneHealthClass,
    venue_flat: bool,
    reconciled: bool,
    pending_custody_conflict: bool,
) -> LaneHealthMembershipFeedbackV1:
    if health_class == LaneHealthClass.GLOBAL_HALT:
        return LaneHealthMembershipFeedbackV1(
            health_class=health_class,
            may_propose_membership_replacement=False,
            may_commit_replacement=False,
            blocks_entry_only=True,
            triggers_membership_churn=False,
            reason_code="GLOBAL_HALT_NO_MEMBERSHIP_CHURN",
        )
    if health_class in {LaneHealthClass.TRANSIENT_HOLD, LaneHealthClass.ENTRY_VETO}:
        return LaneHealthMembershipFeedbackV1(
            health_class=health_class,
            may_propose_membership_replacement=False,
            may_commit_replacement=False,
            blocks_entry_only=True,
            triggers_membership_churn=False,
            reason_code="ORDINARY_HOLD_NO_EVICTION",
        )
    if health_class == LaneHealthClass.DEGRADED_DATA:
        return LaneHealthMembershipFeedbackV1(
            health_class=health_class,
            may_propose_membership_replacement=False,
            may_commit_replacement=False,
            blocks_entry_only=True,
            triggers_membership_churn=False,
            reason_code="DEGRADED_DATA_VETO_ENTRY",
        )
    if health_class == LaneHealthClass.QUARANTINE:
        return LaneHealthMembershipFeedbackV1(
            health_class=health_class,
            may_propose_membership_replacement=False,
            may_commit_replacement=False,
            blocks_entry_only=True,
            triggers_membership_churn=False,
            reason_code="QUARANTINE_RECOVER_SAME_INSTRUMENT",
        )
    replacement_ok = venue_flat and reconciled and not pending_custody_conflict
    if health_class == LaneHealthClass.LANE_LOCAL_FATAL:
        return LaneHealthMembershipFeedbackV1(
            health_class=health_class,
            may_propose_membership_replacement=replacement_ok,
            may_commit_replacement=replacement_ok,
            blocks_entry_only=not replacement_ok,
            triggers_membership_churn=replacement_ok,
            reason_code="LANE_FATAL_REPLACEMENT_WHEN_FLAT",
        )
    if health_class == LaneHealthClass.INSTRUMENT_FATAL:
        return LaneHealthMembershipFeedbackV1(
            health_class=health_class,
            may_propose_membership_replacement=replacement_ok,
            may_commit_replacement=replacement_ok,
            blocks_entry_only=True,
            triggers_membership_churn=replacement_ok,
            reason_code="INSTRUMENT_FATAL_REPLACE_WHEN_FLAT",
        )
    return LaneHealthMembershipFeedbackV1(
        health_class=health_class,
        may_propose_membership_replacement=False,
        may_commit_replacement=False,
        blocks_entry_only=True,
        triggers_membership_churn=False,
        reason_code="UNKNOWN_HEALTH_FAIL_CLOSED",
    )

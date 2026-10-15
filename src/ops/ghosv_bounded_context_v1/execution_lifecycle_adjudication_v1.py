"""GHOSV Execution lifecycle adjudication (read-only semantics, AUTHORITY=NONE)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import TRAFFIC_GREEN, TRAFFIC_YELLOW
from src.ops.ghosv_bounded_context_v1.execution_offline_consistency_guard_v1 import (
    ConsistencyGuardResultV1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvEvidenceKind, GhosvEvidenceRecordV1

LIFECYCLE_ADJUDICATION_CONTRACT = "ghosv_execution_lifecycle_adjudication.v1"

_G004_SUBMIT_OUTCOMES_CONFIRMING_POST = frozenset(
    {
        "SUBMITTED",
        "TRANSPORT_ACK",
    }
)


def venue_post_outcome_from_attempt_payload_v1(payload: Mapping[str, Any]) -> bool | None:
    """Map EXECUTION_ATTEMPT payload to confirmed venue POST (True/False) or unknown (None)."""
    if "post_occurred" in payload:
        occurred = payload.get("post_occurred")
        if occurred is True:
            return True
        if occurred is False:
            return False
        return None
    if payload.get("post_count_known") is True:
        raw = payload.get("post_count")
        if isinstance(raw, int):
            return raw > 0
        return None
    return None


def g004_confirms_venue_submission_v1(record: GhosvEvidenceRecordV1) -> bool:
    """Persisted G004 disposition implies a post attempt was submitted (not a fill)."""
    if record.kind != GhosvEvidenceKind.RECONCILIATION_GATE.value:
        return False
    payload = record.payload if isinstance(record.payload, dict) else {}
    if payload.get("g004_witness") is not True:
        return False
    local_submit = str(payload.get("local_submit_outcome") or "").strip().upper()
    return local_submit in _G004_SUBMIT_OUTCOMES_CONFIRMING_POST


def adjudicate_confirmed_venue_post_submission_v1(
    records: Sequence[GhosvEvidenceRecordV1],
) -> tuple[bool, bool]:
    """Return (confirmed_venue_post_submission, conflicting_post_witnesses)."""
    outcomes: list[bool] = []
    for record in records:
        if record.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value:
            payload = record.payload if isinstance(record.payload, dict) else {}
            outcome = venue_post_outcome_from_attempt_payload_v1(payload)
            if outcome is not None:
                outcomes.append(outcome)
        elif g004_confirms_venue_submission_v1(record):
            outcomes.append(True)
    if not outcomes:
        return False, False
    if any(outcomes) and not all(outcomes):
        return False, True
    return bool(outcomes[0]), False


def apply_post_witness_conflict_traffic_guard_v1(
    traffic: str,
    post_witness_conflict: bool,
) -> str:
    """Confirmed contradictory POST witnesses must not yield overall GREEN."""
    if post_witness_conflict and traffic == TRAFFIC_GREEN:
        return TRAFFIC_YELLOW
    return traffic


def execution_lifecycle_completeness_v1(
    *,
    records_kinds: set[str],
    guard: ConsistencyGuardResultV1,
    post_submission_witnessed: bool,
    pre_external_witnessed: bool,
    post_witness_conflict: bool,
) -> str:
    if guard.evidence_consistency == "FAIL" or post_witness_conflict:
        return "INCONSISTENT_SOURCES"
    has_ack = GhosvEvidenceKind.ORDER_ACK.value in records_kinds
    has_fill = bool(
        records_kinds
        & {
            GhosvEvidenceKind.FILL.value,
            GhosvEvidenceKind.FULL_FILL.value,
            GhosvEvidenceKind.PARTIAL_FILL.value,
        }
    )
    if has_fill:
        return "FILL_WITNESSED"
    if has_ack:
        return "VENUE_ACK_WITNESSED"
    if post_submission_witnessed:
        return "POST_SUBMISSION_WITNESSED"
    if pre_external_witnessed:
        return "PRE_EXTERNAL_ONLY"
    if records_kinds:
        return "PARTIAL_WITNESSED"
    return "UNKNOWN"


__all__ = [
    "LIFECYCLE_ADJUDICATION_CONTRACT",
    "adjudicate_confirmed_venue_post_submission_v1",
    "apply_post_witness_conflict_traffic_guard_v1",
    "execution_lifecycle_completeness_v1",
    "g004_confirms_venue_submission_v1",
    "venue_post_outcome_from_attempt_payload_v1",
]

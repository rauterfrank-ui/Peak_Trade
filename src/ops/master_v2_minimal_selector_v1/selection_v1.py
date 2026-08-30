"""Exactly-one Master V2 selection (explicit control-plane trigger only).

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false

eligible_count == 0 → NO_SELECTION
eligible_count == 1 → SELECT that candidate
eligible_count > 1 → NO_SELECTION

No ranking, score, sort-to-select, fallback, cadence, or hot-path rescan.
Candidate list order must not change the decision.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.governed_futures_universe_producer_v1.discovery_v1 import (
    discover_okx_eea_instruments_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import compute_source_digest_v1
from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    CALL_GRAPH,
    CAP22_ROLE,
    CAP22_SELECTION_AUTHORITY,
    CAPABILITY_ID,
    HISTORICAL_CLAIM,
    OWNER_SELECTOR_POLICY_VERSION,
    POLICY_ID,
    PRODUCER_VERSION,
    REASON_NO_SELECTION_INCOMPLETE_SOURCE,
    REASON_NO_SELECTION_MULTIPLE_ELIGIBLE,
    REASON_NO_SELECTION_OVERRIDE_REJECTED,
    REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE,
    REASON_NO_SELECTION_ZERO_ELIGIBLE,
    REASON_SELECTED_EXACTLY_ONE,
    SCHEMA_VERSION,
    STATUS_NO_SELECTION,
    STATUS_SELECTED,
    VENUE,
    VENUE_DISCOVERY,
)
from src.ops.master_v2_minimal_selector_v1.models_v1 import (
    MasterV2SelectionDecisionV1,
    StructuralEligibilityRowV1,
    authority_block,
    compute_policy_digest_v1,
    empty_no_selection,
)
from src.ops.master_v2_minimal_selector_v1.structural_eligibility_v1 import (
    classify_census_rows_v1,
    is_okx_eea_venue_v1,
)


def _eligible_native_ids(rows: Sequence[StructuralEligibilityRowV1]) -> tuple[str, ...]:
    ids = [row.venue_native_inst_id for row in rows if row.eligible and row.venue_native_inst_id]
    return tuple(sorted(set(ids)))


def _finish(
    *,
    reason: str,
    source_snapshot_digest: str,
    source_event_time: str,
    classified_rows: Sequence[StructuralEligibilityRowV1] = (),
    selected_native_instrument_id: Optional[str] = None,
) -> MasterV2SelectionDecisionV1:
    eligible_ids = _eligible_native_ids(classified_rows)
    eligible_count = len(eligible_ids)
    if reason == REASON_SELECTED_EXACTLY_ONE:
        status = STATUS_SELECTED
        selected = selected_native_instrument_id
    else:
        status = STATUS_NO_SELECTION
        selected = None
    return MasterV2SelectionDecisionV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        producer_version=PRODUCER_VERSION,
        policy_version=OWNER_SELECTOR_POLICY_VERSION,
        policy_id=POLICY_ID,
        historical_claim=HISTORICAL_CLAIM,
        venue=VENUE,
        source_snapshot_digest=source_snapshot_digest,
        source_event_time=source_event_time,
        decision_status=status,
        eligible_count=eligible_count,
        selected_native_instrument_id=selected,
        decision_reason=reason,
        policy_digest=compute_policy_digest_v1(),
        identity_digest="",
        eligible_native_instrument_ids=eligible_ids,
        ranking_input_ignored=True,
        cap22_role=CAP22_ROLE,
        cap22_selection_authority=CAP22_SELECTION_AUTHORITY,
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        classified_rows=tuple(classified_rows),
    ).with_identity_digest()


def decide_master_v2_minimal_selection_v1(
    *,
    source_payload: Mapping[str, Any] | None,
    mark_price_payload: Mapping[str, Any] | Sequence[str] | None = None,
    source_event_time: str | None = None,
    venue: str = VENUE,
    source_kind: str | None = "okx_eea_public_instruments",
    ranking_snapshot: Mapping[str, Any] | None = None,
    dashboard_payload: Mapping[str, Any] | None = None,
    allowlist_payload: Mapping[str, Any] | None = None,
    manual_override_payload: Mapping[str, Any] | None = None,
    default_instrument: str | None = None,
    fallback_instrument: str | None = None,
) -> MasterV2SelectionDecisionV1:
    """Pure selection decision. Ranking and fallback arguments are ignored.

    ``ranking_snapshot`` is accepted only so callers can prove it cannot change
    the decision. ``default_instrument`` / ``fallback_instrument`` are never used.
    """
    _ = ranking_snapshot
    _ = default_instrument
    _ = fallback_instrument

    if dashboard_payload is not None or allowlist_payload is not None:
        return empty_no_selection(reason=REASON_NO_SELECTION_OVERRIDE_REJECTED)
    if manual_override_payload is not None:
        return empty_no_selection(reason=REASON_NO_SELECTION_OVERRIDE_REJECTED)

    if not is_okx_eea_venue_v1(venue):
        return empty_no_selection(reason=REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE)

    if source_payload is None:
        return empty_no_selection(reason=REASON_NO_SELECTION_INCOMPLETE_SOURCE)

    discovery = discover_okx_eea_instruments_v1(
        source_payload=source_payload,
        mark_price_payload=mark_price_payload,
        source_event_time=source_event_time,
        venue=VENUE_DISCOVERY,
        source_kind=source_kind,
    )
    if not discovery.ok:
        return empty_no_selection(
            reason=REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE,
            source_event_time=str(discovery.source_event_time or ""),
        )

    event_time = str(discovery.source_event_time or "").strip()
    if not event_time:
        return empty_no_selection(reason=REASON_NO_SELECTION_INCOMPLETE_SOURCE)

    source_digest = compute_source_digest_v1(
        instruments=discovery.instruments,
        mark_price_supported_ids=sorted(discovery.mark_price_supported_ids),
        source_event_time=event_time,
        venue=discovery.venue,
    )

    rows, has_duplicates = classify_census_rows_v1(
        discovery.instruments,
        venue=VENUE,
        mark_price_supported_ids=discovery.mark_price_supported_ids,
    )
    if has_duplicates:
        return _finish(
            reason=REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE,
            source_snapshot_digest=source_digest,
            source_event_time=event_time,
            classified_rows=rows,
        )

    eligible_ids = _eligible_native_ids(rows)
    if len(eligible_ids) == 0:
        return _finish(
            reason=REASON_NO_SELECTION_ZERO_ELIGIBLE,
            source_snapshot_digest=source_digest,
            source_event_time=event_time,
            classified_rows=rows,
        )
    if len(eligible_ids) > 1:
        return _finish(
            reason=REASON_NO_SELECTION_MULTIPLE_ELIGIBLE,
            source_snapshot_digest=source_digest,
            source_event_time=event_time,
            classified_rows=rows,
        )

    selected = eligible_ids[0]
    return _finish(
        reason=REASON_SELECTED_EXACTLY_ONE,
        source_snapshot_digest=source_digest,
        source_event_time=event_time,
        classified_rows=rows,
        selected_native_instrument_id=selected,
    )


def trigger_master_v2_minimal_selection_v1(
    **kwargs: Any,
) -> MasterV2SelectionDecisionV1:
    """Explicit control-plane trigger. No scheduler, cadence, or background refresh."""
    return decide_master_v2_minimal_selection_v1(**kwargs)

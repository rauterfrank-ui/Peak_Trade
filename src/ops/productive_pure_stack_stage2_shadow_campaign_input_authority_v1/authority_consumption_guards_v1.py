"""PIT / provenance / stale-incomplete fail-closed guards for Surface B consumption.

PUBLIC_MARKET_FINALIZED_BARS / PT1M may be consumed only with explicit provenance,
finalized bars, and point-in-time (no-lookahead) coverage. No productive numeric
max-age thresholds are applied or authorized here.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
    assert_source_not_forbidden,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
    ObservationPackProvenanceV1,
    ObservationPackV1,
    ProducedFinalizedBarV1,
)

REQUIRED_PROVENANCE_FIELDS: tuple[str, ...] = (
    "dataset_id",
    "source_id",
    "venue",
    "instrument_id",
    "timeframe",
    "event_time_range",
    "ingestion_timestamp",
    "finalization_timestamp",
    "repository_sha",
    "config_digest",
    "producer_version",
    "raw_source_digest",
    "correction_revision_policy",
)


def assert_provenance_complete_v1(provenance: ObservationPackProvenanceV1) -> None:
    """Fail closed when any ratified provenance field is missing or semantically wrong."""
    assert_forbidden_effects_remain_false()
    payload = provenance.to_dict()
    for field in REQUIRED_PROVENANCE_FIELDS:
        if field not in payload:
            raise InputAuthorityErrorV1(f"PROVENANCE_INCOMPLETE:{field}")
        value = payload[field]
        if value is None:
            raise InputAuthorityErrorV1(f"PROVENANCE_INCOMPLETE:{field}")
        if field == "event_time_range":
            if not isinstance(value, Mapping):
                raise InputAuthorityErrorV1("PROVENANCE_EVENT_TIME_RANGE_INVALID")
            start = value.get("start_epoch_s")
            end = value.get("end_epoch_s_exclusive")
            if not isinstance(start, int) or not isinstance(end, int):
                raise InputAuthorityErrorV1("PROVENANCE_EVENT_TIME_RANGE_INVALID")
            if end <= start:
                raise InputAuthorityErrorV1("PROVENANCE_EVENT_TIME_RANGE_EMPTY")
            continue
        if not isinstance(value, str) or not value.strip():
            raise InputAuthorityErrorV1(f"PROVENANCE_INCOMPLETE:{field}")
    if provenance.timeframe != C.BAR_INTERVAL:
        raise InputAuthorityErrorV1("PROVENANCE_TIMEFRAME_MUST_BE_PT1M")
    if provenance.source_id != C.SOURCE_ID:
        raise InputAuthorityErrorV1("PROVENANCE_SOURCE_ID_MISMATCH")
    if len(provenance.repository_sha) != 40:
        raise InputAuthorityErrorV1("PROVENANCE_REPOSITORY_SHA_INVALID")
    assert_source_not_forbidden(provenance.source_id)


def assert_finalized_pt1m_only_v1(bars: Sequence[ProducedFinalizedBarV1]) -> None:
    """Fail closed unless every bar is finalized PT1M under Surface-B source identity."""
    assert_forbidden_effects_remain_false()
    if not bars:
        raise InputAuthorityErrorV1("OBSERVATION_BARS_REQUIRED")
    prev: Optional[int] = None
    for bar in bars:
        if not bar.finalized:
            raise InputAuthorityErrorV1("NON_FINALIZED_BAR_FORBIDDEN")
        if bar.source_id != C.SOURCE_ID:
            raise InputAuthorityErrorV1("SOURCE_ID_MISMATCH")
        if int(bar.event_time_epoch_s) % C.PT1M_SECONDS != 0:
            raise InputAuthorityErrorV1("EVENT_TIME_NOT_PT1M_ALIGNED")
        if prev is not None:
            if int(bar.event_time_epoch_s) <= prev:
                raise InputAuthorityErrorV1("BARS_NOT_STRICTLY_INCREASING")
            if int(bar.event_time_epoch_s) - prev != C.PT1M_SECONDS:
                raise InputAuthorityErrorV1("PT1M_GAP_INCOMPLETE")
        prev = int(bar.event_time_epoch_s)


def assert_pit_no_lookahead_v1(
    *,
    bars: Sequence[ProducedFinalizedBarV1],
    as_of_event_time_epoch_s: int,
) -> None:
    """Point-in-time: only fully closed PT1M buckets at or before as_of may be used."""
    assert_forbidden_effects_remain_false()
    if as_of_event_time_epoch_s < 0:
        raise InputAuthorityErrorV1("AS_OF_EVENT_TIME_INVALID")
    for bar in bars:
        # Bucket closes at event_time + PT1M; using the bar before close is lookahead.
        bucket_close = int(bar.event_time_epoch_s) + C.PT1M_SECONDS
        if int(bar.event_time_epoch_s) > int(as_of_event_time_epoch_s):
            raise InputAuthorityErrorV1("LOOKAHEAD_BAR_AFTER_AS_OF")
        if bucket_close > int(as_of_event_time_epoch_s):
            raise InputAuthorityErrorV1("LOOKAHEAD_OPEN_BUCKET_AT_AS_OF")


def assert_coverage_not_stale_or_incomplete_v1(
    *,
    pack: ObservationPackV1,
    as_of_event_time_epoch_s: int,
    productive_max_age_seconds: Optional[int] = None,
) -> None:
    """Structural stale/incomplete fail-closed without productive numeric max-age.

    - Reject any attempt to supply a productive max-age Owner magnitude.
    - Require contiguous finalized PT1M coverage whose exclusive end equals as_of
      (pack tip must land exactly on as_of; otherwise coverage is incomplete/stale).
    """
    assert_forbidden_effects_remain_false()
    if productive_max_age_seconds is not None:
        raise InputAuthorityErrorV1("PRODUCTIVE_MAX_AGE_MUST_REMAIN_UNSET")
    assert_provenance_complete_v1(pack.provenance)
    assert_finalized_pt1m_only_v1(pack.bars)
    assert_pit_no_lookahead_v1(bars=pack.bars, as_of_event_time_epoch_s=as_of_event_time_epoch_s)
    tip = pack.provenance.event_time_range.end_epoch_s_exclusive
    if tip < int(as_of_event_time_epoch_s):
        raise InputAuthorityErrorV1("STALE_INCOMPLETE_COVERAGE_BEFORE_AS_OF")
    if tip > int(as_of_event_time_epoch_s):
        # Pack claims future-exclusive coverage beyond as_of → not PIT-safe.
        raise InputAuthorityErrorV1("STALE_OR_FUTURE_COVERAGE_BEYOND_AS_OF")
    if pack.bars[-1].event_time_epoch_s + C.PT1M_SECONDS != int(as_of_event_time_epoch_s):
        raise InputAuthorityErrorV1("STALE_INCOMPLETE_TIP_MISMATCH")


def assert_surface_b_authority_consumable_v1(
    *,
    pack: ObservationPackV1,
    as_of_event_time_epoch_s: int,
    productive_max_age_seconds: Optional[int] = None,
) -> dict[str, Any]:
    """Single entry: provenance + finalized PT1M + PIT + structural coverage."""
    boundary = assert_forbidden_effects_remain_false()
    if C.DASHBOARD_AUTHORITY_EFFECT != "NONE":
        raise InputAuthorityErrorV1("DASHBOARD_AUTHORITY_FORBIDDEN")
    if C.PRODUCTIVE_NUMERIC_VALUES_SET != 0:
        raise InputAuthorityErrorV1("PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO")
    assert_coverage_not_stale_or_incomplete_v1(
        pack=pack,
        as_of_event_time_epoch_s=as_of_event_time_epoch_s,
        productive_max_age_seconds=productive_max_age_seconds,
    )
    return {
        **dict(boundary),
        "observation_family": C.OBSERVATION_FAMILY,
        "bar_interval": C.BAR_INTERVAL,
        "pit_no_lookahead": True,
        "provenance_complete": True,
        "finalized_pt1m_only": True,
        "shadow_campaign_startable": C.SHADOW_CAMPAIGN_STARTABLE,
    }

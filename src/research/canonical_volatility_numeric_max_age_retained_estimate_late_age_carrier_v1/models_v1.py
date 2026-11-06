"""Models and errors for the R1 retained-estimate lifecycle carrier."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    VolatilityEstimateLifecycleState,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.constants_v1 import (
    SCHEMA_VERSION,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CanonicalVolatilityEstimateV1,
    validate_canonical_volatility_estimate_v1,
)


class RetainedEstimateLateAgeCarrierError(ValueError):
    """Fail-closed retained-estimate carrier / late-age hold error."""


def _parse_aware_utc(value: Any, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip()
        if not text:
            raise RetainedEstimateLateAgeCarrierError(f"{field_name}_required")
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise RetainedEstimateLateAgeCarrierError(f"{field_name}_must_be_timezone_aware")
    return dt.astimezone(timezone.utc)


def estimate_id_from_source_digest_v1(source_digest: str) -> str:
    digest = str(source_digest or "").strip()
    if not digest:
        raise RetainedEstimateLateAgeCarrierError("source_digest_required")
    return f"est_{digest[:24]}"


def reconstruct_canonical_volatility_estimate_v1(
    payload: Mapping[str, Any],
) -> CanonicalVolatilityEstimateV1:
    """Rebuild typed estimate from durable carrier payload (SSOT for lifecycle)."""
    if not isinstance(payload, Mapping):
        raise RetainedEstimateLateAgeCarrierError("estimate_payload_not_object")
    oldest_raw = payload.get("oldest_observation_event_time")
    oldest = None if oldest_raw in (None, "") else _parse_aware_utc(oldest_raw, field_name="oldest")
    estimate = CanonicalVolatilityEstimateV1(
        value=float(payload["value"]),
        unit=str(payload["unit"]),
        bar_interval_seconds=int(payload["bar_interval_seconds"]),
        lookback_bars=int(payload["lookback_bars"]),
        horizon_seconds=int(payload["horizon_seconds"]),
        annualized=bool(payload["annualized"]),
        estimator=str(payload["estimator"]),
        observation_count=int(payload["observation_count"]),
        as_of_event_time=_parse_aware_utc(payload.get("as_of_event_time"), field_name="as_of"),
        fallback_used=bool(payload["fallback_used"]),
        source_digest=str(payload["source_digest"]),
        contract_version=str(payload["contract_version"]),
        estimator_version=str(payload.get("estimator_version") or ""),
        minimum_observation_count=int(payload["minimum_observation_count"]),
        bar_duration=str(payload.get("bar_duration") or ""),
        oldest_observation_event_time=oldest,
        config_digest=str(payload.get("config_digest") or ""),
        fallback_identity=str(payload.get("fallback_identity") or ""),
        provenance=str(payload.get("provenance") or ""),
        data_quality=str(payload.get("data_quality") or ""),
    )
    return validate_canonical_volatility_estimate_v1(estimate)


def lifecycle_state_from_mapping_v1(
    payload: Mapping[str, Any],
) -> VolatilityEstimateLifecycleState:
    if not isinstance(payload, Mapping):
        raise RetainedEstimateLateAgeCarrierError("lifecycle_state_not_object")
    estimate = reconstruct_canonical_volatility_estimate_v1(
        payload.get("estimate") if isinstance(payload.get("estimate"), Mapping) else {}
    )
    state = VolatilityEstimateLifecycleState(
        estimate=estimate,
        produced_at_market_event_time=str(payload.get("produced_at_market_event_time") or ""),
        last_recompute_reason=str(payload.get("last_recompute_reason") or ""),
        reuse_count=int(payload.get("reuse_count") or 0),
        distinct_observations_since_recompute=int(
            payload.get("distinct_observations_since_recompute") or 0
        ),
        source_window_start_event_time=str(payload.get("source_window_start_event_time") or ""),
        source_window_end_event_time=str(payload.get("source_window_end_event_time") or ""),
        source_digest=str(payload.get("source_digest") or ""),
    )
    if state.source_digest != estimate.source_digest:
        raise RetainedEstimateLateAgeCarrierError("lifecycle_source_digest_mismatch")
    return state


@dataclass(frozen=True)
class RetainedEstimateLifecycleCarrierV1:
    """Immutable write-once carrier binding a retained estimate across S01→S02."""

    schema_version: str
    campaign_id: str
    early_session_id: str
    late_session_id: str
    repository_sha: str
    preregistration_digest: str
    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    estimate_id: str
    as_of_event_time: str
    source_digest: str
    lifecycle_state: VolatilityEstimateLifecycleState
    research_age_grid_seconds: tuple[int, ...]
    minimum_distinct_observations_per_age_bucket: int
    age_bucket_observation_counts: Mapping[str, int]
    written_at_utc: str
    artifact_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_bucket_observation_counts": {
                str(k): int(v) for k, v in sorted(self.age_bucket_observation_counts.items())
            },
            "artifact_digest": self.artifact_digest,
            "as_of_event_time": self.as_of_event_time,
            "campaign_id": self.campaign_id,
            "canonical_instrument_id": self.canonical_instrument_id,
            "early_session_id": self.early_session_id,
            "estimate_id": self.estimate_id,
            "late_session_id": self.late_session_id,
            "lifecycle_state": self.lifecycle_state.to_dict(),
            "minimum_distinct_observations_per_age_bucket": (
                self.minimum_distinct_observations_per_age_bucket
            ),
            "preregistration_digest": self.preregistration_digest,
            "repository_sha": self.repository_sha,
            "research_age_grid_seconds": list(self.research_age_grid_seconds),
            "schema_version": self.schema_version,
            "source_digest": self.source_digest,
            "venue": self.venue,
            "venue_instrument_id": self.venue_instrument_id,
            "written_at_utc": self.written_at_utc,
        }


def require_nonempty_str(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RetainedEstimateLateAgeCarrierError(f"{field}_required")
    return text


def require_int_tuple(values: Sequence[Any], *, field: str) -> tuple[int, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise RetainedEstimateLateAgeCarrierError(f"{field}_list_required")
    out = tuple(int(x) for x in values)
    if not out:
        raise RetainedEstimateLateAgeCarrierError(f"{field}_empty")
    if len(out) != len(set(out)):
        raise RetainedEstimateLateAgeCarrierError(f"{field}_not_unique")
    return out


def parse_retained_estimate_lifecycle_carrier_v1(
    payload: Mapping[str, Any],
) -> RetainedEstimateLifecycleCarrierV1:
    if not isinstance(payload, Mapping):
        raise RetainedEstimateLateAgeCarrierError("carrier_payload_not_object")
    required = {
        "schema_version",
        "campaign_id",
        "early_session_id",
        "late_session_id",
        "repository_sha",
        "preregistration_digest",
        "venue",
        "canonical_instrument_id",
        "venue_instrument_id",
        "estimate_id",
        "as_of_event_time",
        "source_digest",
        "lifecycle_state",
        "research_age_grid_seconds",
        "minimum_distinct_observations_per_age_bucket",
        "age_bucket_observation_counts",
        "written_at_utc",
        "artifact_digest",
    }
    missing = sorted(required - set(payload.keys()))
    if missing:
        raise RetainedEstimateLateAgeCarrierError("carrier_field_missing:" + ",".join(missing))
    unknown = sorted(set(payload.keys()) - required)
    if unknown:
        raise RetainedEstimateLateAgeCarrierError("carrier_unknown_field:" + ",".join(unknown))
    if str(payload.get("schema_version")) != SCHEMA_VERSION:
        raise RetainedEstimateLateAgeCarrierError("carrier_schema_mismatch")

    lifecycle = lifecycle_state_from_mapping_v1(
        payload["lifecycle_state"] if isinstance(payload.get("lifecycle_state"), Mapping) else {}
    )
    estimate_id = require_nonempty_str(payload.get("estimate_id"), field="estimate_id")
    source_digest = require_nonempty_str(payload.get("source_digest"), field="source_digest")
    as_of = require_nonempty_str(payload.get("as_of_event_time"), field="as_of_event_time")
    expected_id = estimate_id_from_source_digest_v1(lifecycle.estimate.source_digest)
    if estimate_id != expected_id:
        raise RetainedEstimateLateAgeCarrierError("carrier_estimate_id_mismatch")
    if source_digest != lifecycle.estimate.source_digest:
        raise RetainedEstimateLateAgeCarrierError("carrier_source_digest_mismatch")
    lifecycle_as_of = lifecycle.estimate.as_of_event_time.astimezone(timezone.utc).isoformat()
    if as_of != lifecycle_as_of:
        raise RetainedEstimateLateAgeCarrierError("carrier_as_of_mismatch")

    grid = require_int_tuple(
        payload.get("research_age_grid_seconds") or (),
        field="research_age_grid_seconds",
    )
    min_obs = int(payload.get("minimum_distinct_observations_per_age_bucket") or 0)
    if min_obs < 1:
        raise RetainedEstimateLateAgeCarrierError(
            "minimum_distinct_observations_per_age_bucket_invalid"
        )

    return RetainedEstimateLifecycleCarrierV1(
        schema_version=SCHEMA_VERSION,
        campaign_id=require_nonempty_str(payload.get("campaign_id"), field="campaign_id"),
        early_session_id=require_nonempty_str(
            payload.get("early_session_id"), field="early_session_id"
        ),
        late_session_id=require_nonempty_str(
            payload.get("late_session_id"), field="late_session_id"
        ),
        repository_sha=require_nonempty_str(payload.get("repository_sha"), field="repository_sha"),
        preregistration_digest=require_nonempty_str(
            payload.get("preregistration_digest"), field="preregistration_digest"
        ),
        venue=require_nonempty_str(payload.get("venue"), field="venue"),
        canonical_instrument_id=require_nonempty_str(
            payload.get("canonical_instrument_id"), field="canonical_instrument_id"
        ),
        venue_instrument_id=require_nonempty_str(
            payload.get("venue_instrument_id"), field="venue_instrument_id"
        ),
        estimate_id=estimate_id,
        as_of_event_time=as_of,
        source_digest=source_digest,
        lifecycle_state=lifecycle,
        research_age_grid_seconds=grid,
        minimum_distinct_observations_per_age_bucket=min_obs,
        age_bucket_observation_counts=_parse_age_bucket_counts(
            payload.get("age_bucket_observation_counts"),
            grid=grid,
        ),
        written_at_utc=require_nonempty_str(payload.get("written_at_utc"), field="written_at_utc"),
        artifact_digest=require_nonempty_str(
            payload.get("artifact_digest"), field="artifact_digest"
        ),
    )


def _parse_age_bucket_counts(raw: Any, *, grid: tuple[int, ...]) -> dict[str, int]:
    if not isinstance(raw, Mapping):
        raise RetainedEstimateLateAgeCarrierError("age_bucket_observation_counts_not_object")
    expected = {str(g) for g in grid}
    unknown = sorted(set(str(k) for k in raw.keys()) - expected)
    if unknown:
        raise RetainedEstimateLateAgeCarrierError(
            "age_bucket_observation_counts_unknown_slot:" + ",".join(unknown)
        )
    out: dict[str, int] = {}
    for g in grid:
        key = str(g)
        value = int(raw.get(key, 0) or 0)
        if value < 0:
            raise RetainedEstimateLateAgeCarrierError("age_bucket_observation_count_negative")
        out[key] = value
    return out

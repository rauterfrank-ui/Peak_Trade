"""Write-once atomic retained-estimate lifecycle carrier I/O."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    VolatilityEstimateLifecycleState,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.constants_v1 import (
    SCHEMA_VERSION,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.digest_v1 import (
    carrier_content_digest_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.hold_v1 import (
    empty_age_bucket_observation_counts_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.models_v1 import (
    RetainedEstimateLateAgeCarrierError,
    RetainedEstimateLifecycleCarrierV1,
    estimate_id_from_source_digest_v1,
    parse_retained_estimate_lifecycle_carrier_v1,
    require_int_tuple,
    require_nonempty_str,
)


def _atomic_write_text(*, destination: Path, body: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd: int | None = None
    tmp_name: str | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            prefix=destination.name + ".",
            dir=str(destination.parent),
        )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = None
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, destination)
        tmp_name = None
    except OSError as exc:
        raise RetainedEstimateLateAgeCarrierError(f"carrier_atomic_write_failed:{exc}") from exc
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if tmp_name is not None and os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def build_retained_estimate_lifecycle_carrier_payload_v1(
    *,
    campaign_id: str,
    early_session_id: str,
    late_session_id: str,
    repository_sha: str,
    preregistration_digest: str,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    lifecycle_state: VolatilityEstimateLifecycleState,
    research_age_grid_seconds: Sequence[int],
    minimum_distinct_observations_per_age_bucket: int,
    age_bucket_observation_counts: Mapping[str, int] | None = None,
    written_at_utc: str | None = None,
) -> dict[str, Any]:
    grid = require_int_tuple(research_age_grid_seconds, field="research_age_grid_seconds")
    counts = (
        dict(age_bucket_observation_counts)
        if age_bucket_observation_counts is not None
        else empty_age_bucket_observation_counts_v1(grid)
    )
    for g in grid:
        counts.setdefault(str(int(g)), 0)
    estimate = lifecycle_state.estimate
    as_of = estimate.as_of_event_time.astimezone(timezone.utc).isoformat()
    source_digest = str(estimate.source_digest)
    provisional: dict[str, Any] = {
        "age_bucket_observation_counts": {str(k): int(v) for k, v in sorted(counts.items())},
        "as_of_event_time": as_of,
        "campaign_id": require_nonempty_str(campaign_id, field="campaign_id"),
        "canonical_instrument_id": require_nonempty_str(
            canonical_instrument_id, field="canonical_instrument_id"
        ),
        "early_session_id": require_nonempty_str(early_session_id, field="early_session_id"),
        "estimate_id": estimate_id_from_source_digest_v1(source_digest),
        "late_session_id": require_nonempty_str(late_session_id, field="late_session_id"),
        "lifecycle_state": lifecycle_state.to_dict(),
        "minimum_distinct_observations_per_age_bucket": int(
            minimum_distinct_observations_per_age_bucket
        ),
        "preregistration_digest": require_nonempty_str(
            preregistration_digest, field="preregistration_digest"
        ),
        "repository_sha": require_nonempty_str(repository_sha, field="repository_sha"),
        "research_age_grid_seconds": list(grid),
        "schema_version": SCHEMA_VERSION,
        "source_digest": source_digest,
        "venue": require_nonempty_str(venue, field="venue"),
        "venue_instrument_id": require_nonempty_str(
            venue_instrument_id, field="venue_instrument_id"
        ),
        "written_at_utc": (
            written_at_utc if written_at_utc is not None else datetime.now(timezone.utc).isoformat()
        ),
    }
    provisional["artifact_digest"] = carrier_content_digest_v1(provisional)
    return provisional


def write_retained_estimate_lifecycle_carrier_once_v1(
    *,
    path: Path,
    payload: Mapping[str, Any],
) -> RetainedEstimateLifecycleCarrierV1:
    """Atomic write-once finalize. Existing path => fail closed."""
    destination = Path(path)
    if destination.exists():
        raise RetainedEstimateLateAgeCarrierError("duplicate_carrier_write")
    parsed = parse_retained_estimate_lifecycle_carrier_v1(payload)
    body = json.dumps(parsed.to_dict(), sort_keys=True, separators=(",", ":"), default=str)
    recomputed = carrier_content_digest_v1(parsed.to_dict())
    if recomputed != parsed.artifact_digest:
        raise RetainedEstimateLateAgeCarrierError("carrier_digest_mismatch_before_write")
    _atomic_write_text(destination=destination, body=body + "\n")
    if not destination.is_file() or destination.stat().st_size <= 0:
        raise RetainedEstimateLateAgeCarrierError("carrier_partial_or_non_atomic")
    return load_retained_estimate_lifecycle_carrier_v1(path=destination)


def load_retained_estimate_lifecycle_carrier_v1(
    *,
    path: Path,
) -> RetainedEstimateLifecycleCarrierV1:
    carrier_path = Path(path)
    if not carrier_path.is_file() or carrier_path.stat().st_size <= 0:
        raise RetainedEstimateLateAgeCarrierError("carrier_missing_or_empty")
    try:
        raw = json.loads(carrier_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RetainedEstimateLateAgeCarrierError("carrier_malformed_json") from exc
    if not isinstance(raw, Mapping):
        raise RetainedEstimateLateAgeCarrierError("carrier_payload_not_object")
    parsed = parse_retained_estimate_lifecycle_carrier_v1(raw)
    if parsed.artifact_digest != carrier_content_digest_v1(parsed.to_dict()):
        raise RetainedEstimateLateAgeCarrierError("carrier_digest_mismatch")
    return parsed


def verify_retained_estimate_lifecycle_carrier_binding_v1(
    carrier: RetainedEstimateLifecycleCarrierV1,
    *,
    campaign_id: str,
    early_session_id: str,
    late_session_id: str,
    repository_sha: str,
    preregistration_digest: str,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    research_age_grid_seconds: Sequence[int] | None = None,
) -> RetainedEstimateLifecycleCarrierV1:
    if carrier.campaign_id != campaign_id:
        raise RetainedEstimateLateAgeCarrierError("carrier_campaign_mismatch")
    if carrier.early_session_id != early_session_id:
        raise RetainedEstimateLateAgeCarrierError("carrier_early_session_mismatch")
    if carrier.late_session_id != late_session_id:
        raise RetainedEstimateLateAgeCarrierError("carrier_late_session_mismatch")
    if carrier.repository_sha != repository_sha:
        raise RetainedEstimateLateAgeCarrierError("carrier_repository_sha_mismatch")
    if carrier.preregistration_digest != preregistration_digest:
        raise RetainedEstimateLateAgeCarrierError("carrier_preregistration_digest_mismatch")
    if carrier.venue != venue:
        raise RetainedEstimateLateAgeCarrierError("carrier_venue_mismatch")
    if carrier.canonical_instrument_id != canonical_instrument_id:
        raise RetainedEstimateLateAgeCarrierError("carrier_canonical_instrument_mismatch")
    if carrier.venue_instrument_id != venue_instrument_id:
        raise RetainedEstimateLateAgeCarrierError("carrier_venue_instrument_mismatch")
    if research_age_grid_seconds is not None:
        expected = require_int_tuple(research_age_grid_seconds, field="research_age_grid_seconds")
        if carrier.research_age_grid_seconds != expected:
            raise RetainedEstimateLateAgeCarrierError("carrier_research_age_grid_mismatch")
    return carrier

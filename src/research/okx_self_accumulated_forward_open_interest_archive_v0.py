"""OKX self-accumulated forward open-interest archive v0.

Append-only, fail-closed forward observation archive for cross_sectional_open_interest_delta_rank/v0.
Reuses existing OI normalization and instrument eligibility owners. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    RESEARCH_SCOPE,
    is_historical_backfill_allowed,
    is_self_accumulated_archive_allowed,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
    OI_OBSERVATION_CADENCE,
    SOURCE_ENDPOINT,
    SOURCE_SCHEMA_VERSION,
    STALE_THRESHOLD_BARS,
)
from src.research.missing_open_interest_policy_v0 import (
    MISSING_REASON_LOOKAHEAD_REJECTED,
    resolve_open_interest_or_missing_v0,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
    parse_okx_open_interest_history_row_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    OkxLifecycleSourceErrorCode,
    evaluate_okx_instrument_eligibility_v1,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

PACKAGE_MARKER = "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_V0=true"
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_archive.v0"
CONFIRM_GO = "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_V0"
CONFIG_REL_PATH = "config/research/okx_self_accumulated_forward_open_interest_archive_v0.json"

ARCHIVE_KIND = "okx_self_accumulated_forward_open_interest_archive"
ARCHIVE_SCHEMA_VERSION = "okx_self_accumulated_forward_open_interest_observation.v0"
COLLECTION_MODE_FORWARD_ONLY = "FORWARD_ONLY"
COLLECTION_MODE_BACKFILL = "BACKFILL"
BAR_INTERVAL_MS = 3_600_000
VENUE = "OKX"
INSTRUMENT_TYPE = "linear_usdt_perpetual_swap"
OPEN_INTEREST_UNIT = "okx_native_contract_count"
OVERLAP_VALIDATION_STATUS_NOT_EXECUTED = "NOT_EXECUTED"


class ArchiveAppendVerdict(str, Enum):
    APPENDED = "APPENDED"
    DUPLICATE_SKIPPED = "DUPLICATE_SKIPPED"
    CONFLICT_REJECTED = "CONFLICT_REJECTED"
    INELIGIBLE_INSTRUMENT = "INELIGIBLE_INSTRUMENT"
    BACKFILL_REJECTED = "BACKFILL_REJECTED"
    LOOKAHEAD_REJECTED = "LOOKAHEAD_REJECTED"
    ARCHIVE_NOT_ALLOWED = "ARCHIVE_NOT_ALLOWED"
    INVALID_OBSERVATION = "INVALID_OBSERVATION"


class GapStalenessStatus(str, Enum):
    OK = "OK"
    GAP = "GAP"
    STALE = "STALE"
    MISSING = "MISSING"


@dataclass(frozen=True)
class ForwardOpenInterestObservationV0:
    instrument_id: str
    native_instrument_id: str
    venue_timestamp_ms: int
    venue_timestamp_utc: str
    collected_at_ms: int
    collected_at_utc: str
    open_interest_raw: str
    open_interest_unit: str
    bar_interval: str
    source_schema_version: str
    source_endpoint: str
    source_record_key: str
    collection_mode: str
    observation_digest: str


@dataclass(frozen=True)
class ArchiveAppendResultV0:
    verdict: ArchiveAppendVerdict
    observation: ForwardOpenInterestObservationV0 | None
    conflict_existing_digest: str | None = None
    reason_code: str | None = None


@dataclass
class InstrumentArchiveStateV0:
    instrument_id: str
    native_instrument_id: str
    observations: list[ForwardOpenInterestObservationV0] = field(default_factory=list)
    index_by_venue_ms: dict[int, ForwardOpenInterestObservationV0] = field(default_factory=dict)

    def latest_venue_timestamp_ms(self) -> int | None:
        if not self.observations:
            return None
        return max(o.venue_timestamp_ms for o in self.observations)


@dataclass(frozen=True)
class GapStalenessAssessmentV0:
    instrument_id: str
    venue_timestamp_utc: str
    status: GapStalenessStatus
    prior_venue_timestamp_utc: str | None
    gap_hours: int | None
    staleness_hours: int | None
    collected_at_utc: str | None


@dataclass(frozen=True)
class OverlapValidationReadinessV0:
    status: str
    archive_observation_count: int
    earliest_venue_timestamp_utc: str | None
    latest_venue_timestamp_utc: str | None
    overlap_validation_executable: bool
    overlap_validation_blocked_reason: str | None


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_observation_digest_v0(obs: Mapping[str, Any]) -> str:
    body = {k: v for k, v in obs.items() if k != "observation_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return compute_sha256_digest(
        {
            "module": "okx_self_accumulated_forward_open_interest_archive_v0",
            "module_version": MODULE_VERSION,
            "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
            "bar_interval": BAR_INTERVAL,
            "collection_mode_forward_only": COLLECTION_MODE_FORWARD_ONLY,
            "source_schema_version": SOURCE_SCHEMA_VERSION,
            "source_endpoint": SOURCE_ENDPOINT,
        }
    )


def build_archive_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "archive_kind": ARCHIVE_KIND,
        "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "venue": VENUE,
        "instrument_type": INSTRUMENT_TYPE,
        "source_endpoint": SOURCE_ENDPOINT,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "open_interest_unit": OPEN_INTEREST_UNIT,
        "bar_interval": BAR_INTERVAL,
        "oi_observation_cadence": OI_OBSERVATION_CADENCE,
        "collection_mode": COLLECTION_MODE_FORWARD_ONLY,
        "historical_backfill_allowed": False,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "bitcoin_present": False,
        "no_interpolation": True,
        "no_synthetic_historical": True,
        "append_only": True,
        "conflict_overwrite_allowed": False,
        "overlap_validation_status": OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
        "implementation_digest": compute_implementation_digest_v0(),
    }


def assert_archive_preconditions_v0() -> None:
    if not is_self_accumulated_archive_allowed():
        raise ValueError("SELF_ACCUMULATED_ARCHIVE_NOT_ALLOWED")
    if is_historical_backfill_allowed():
        raise ValueError("HISTORICAL_BACKFILL_MUST_REMAIN_BLOCKED")


def validate_instrument_for_forward_archive_v0(
    inst: Mapping[str, Any],
) -> tuple[bool, str | None, str | None]:
    """Futures-only, non-Bitcoin eligibility gate. Returns (eligible, instrument_id, reason)."""
    result = evaluate_okx_instrument_eligibility_v1(inst)
    if not result.eligible:
        codes = result.error_codes
        if OkxLifecycleSourceErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value in codes:
            return False, None, OkxLifecycleSourceErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value
        return False, None, codes[0] if codes else "INELIGIBLE_INSTRUMENT"
    return True, result.instrument_id, None


def normalize_forward_open_interest_observation_v0(
    row: Sequence[Any],
    *,
    instrument_id: str,
    native_instrument_id: str,
    collected_at_utc: str,
    collection_mode: str = COLLECTION_MODE_FORWARD_ONLY,
) -> ForwardOpenInterestObservationV0 | None:
    """Normalize one forward-observed OI row with venue and collection provenance."""
    if collection_mode != COLLECTION_MODE_FORWARD_ONLY:
        return None
    parsed = parse_okx_open_interest_history_row_v0(
        row,
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
    )
    if parsed is None:
        return None
    oi_value = resolve_open_interest_or_missing_v0(raw_value=parsed.open_interest_raw)
    if oi_value is None:
        return None
    collected_at_ms = _parse_utc_ms(collected_at_utc)
    if parsed.observation_time_ms > collected_at_ms:
        return None
    payload = {
        "instrument_id": instrument_id,
        "native_instrument_id": native_instrument_id,
        "venue_timestamp_ms": parsed.observation_time_ms,
        "venue_timestamp_utc": parsed.observation_time_utc,
        "collected_at_ms": collected_at_ms,
        "collected_at_utc": collected_at_utc,
        "open_interest_raw": oi_value,
        "open_interest_unit": OPEN_INTEREST_UNIT,
        "bar_interval": BAR_INTERVAL,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_endpoint": SOURCE_ENDPOINT,
        "source_record_key": parsed.source_record_key,
        "collection_mode": collection_mode,
    }
    digest = compute_observation_digest_v0(payload)
    return ForwardOpenInterestObservationV0(observation_digest=digest, **payload)


def observation_from_normalized_v0(
    normalized: NormalizedOpenInterestObservationV0,
    *,
    collected_at_utc: str,
    collection_mode: str = COLLECTION_MODE_FORWARD_ONLY,
) -> ForwardOpenInterestObservationV0 | None:
    oi_value = resolve_open_interest_or_missing_v0(raw_value=normalized.open_interest_raw)
    if oi_value is None:
        return None
    collected_at_ms = _parse_utc_ms(collected_at_utc)
    if normalized.observation_time_ms > collected_at_ms:
        return None
    payload = {
        "instrument_id": normalized.instrument_id,
        "native_instrument_id": normalized.native_instrument_id,
        "venue_timestamp_ms": normalized.observation_time_ms,
        "venue_timestamp_utc": normalized.observation_time_utc,
        "collected_at_ms": collected_at_ms,
        "collected_at_utc": collected_at_utc,
        "open_interest_raw": oi_value,
        "open_interest_unit": OPEN_INTEREST_UNIT,
        "bar_interval": BAR_INTERVAL,
        "source_schema_version": normalized.source_schema_version,
        "source_endpoint": SOURCE_ENDPOINT,
        "source_record_key": normalized.source_record_key,
        "collection_mode": collection_mode,
    }
    digest = compute_observation_digest_v0(payload)
    return ForwardOpenInterestObservationV0(observation_digest=digest, **payload)


def _is_backfill_attempt_v0(
    obs: ForwardOpenInterestObservationV0,
    *,
    latest_venue_ms: int | None,
) -> bool:
    if obs.collection_mode == COLLECTION_MODE_BACKFILL:
        return True
    if latest_venue_ms is None:
        return False
    if obs.venue_timestamp_ms < latest_venue_ms:
        return True
    return False


def append_forward_observation_v0(
    state: InstrumentArchiveStateV0,
    obs: ForwardOpenInterestObservationV0,
    *,
    preconditions_checked: bool = False,
) -> ArchiveAppendResultV0:
    """Idempotent append with conflict rejection. Append-only; no overwrite."""
    if not preconditions_checked:
        try:
            assert_archive_preconditions_v0()
        except ValueError:
            return ArchiveAppendResultV0(
                verdict=ArchiveAppendVerdict.ARCHIVE_NOT_ALLOWED,
                observation=None,
                reason_code="SELF_ACCUMULATED_ARCHIVE_NOT_ALLOWED",
            )

    if obs.instrument_id != state.instrument_id:
        return ArchiveAppendResultV0(
            verdict=ArchiveAppendVerdict.INVALID_OBSERVATION,
            observation=None,
            reason_code="INSTRUMENT_ID_MISMATCH",
        )

    if obs.collected_at_ms < obs.venue_timestamp_ms:
        return ArchiveAppendResultV0(
            verdict=ArchiveAppendVerdict.LOOKAHEAD_REJECTED,
            observation=None,
            reason_code=MISSING_REASON_LOOKAHEAD_REJECTED,
        )

    latest = state.latest_venue_timestamp_ms()
    if _is_backfill_attempt_v0(obs, latest_venue_ms=latest):
        return ArchiveAppendResultV0(
            verdict=ArchiveAppendVerdict.BACKFILL_REJECTED,
            observation=None,
            reason_code="HISTORICAL_BACKFILL_NOT_ALLOWED",
        )

    existing = state.index_by_venue_ms.get(obs.venue_timestamp_ms)
    if existing is not None:
        if (
            existing.open_interest_raw == obs.open_interest_raw
            and existing.observation_digest == obs.observation_digest
        ):
            return ArchiveAppendResultV0(
                verdict=ArchiveAppendVerdict.DUPLICATE_SKIPPED,
                observation=existing,
                reason_code="IDEMPOTENT_DUPLICATE",
            )
        return ArchiveAppendResultV0(
            verdict=ArchiveAppendVerdict.CONFLICT_REJECTED,
            observation=None,
            conflict_existing_digest=existing.observation_digest,
            reason_code="CONFLICTING_OBSERVATION_NO_OVERWRITE",
        )

    state.observations.append(obs)
    state.index_by_venue_ms[obs.venue_timestamp_ms] = obs
    state.observations.sort(key=lambda o: o.venue_timestamp_ms)
    return ArchiveAppendResultV0(
        verdict=ArchiveAppendVerdict.APPENDED,
        observation=obs,
    )


def assess_gap_and_staleness_v0(
    obs: ForwardOpenInterestObservationV0,
    *,
    prior: ForwardOpenInterestObservationV0 | None,
    stale_threshold_bars: int = STALE_THRESHOLD_BARS,
) -> GapStalenessAssessmentV0:
    if prior is None:
        return GapStalenessAssessmentV0(
            instrument_id=obs.instrument_id,
            venue_timestamp_utc=obs.venue_timestamp_utc,
            status=GapStalenessStatus.OK,
            prior_venue_timestamp_utc=None,
            gap_hours=None,
            staleness_hours=None,
            collected_at_utc=obs.collected_at_utc,
        )

    delta_ms = obs.venue_timestamp_ms - prior.venue_timestamp_ms
    gap_hours = delta_ms // BAR_INTERVAL_MS
    collection_lag_ms = obs.collected_at_ms - obs.venue_timestamp_ms
    staleness_hours = collection_lag_ms // BAR_INTERVAL_MS

    if delta_ms > BAR_INTERVAL_MS:
        status = GapStalenessStatus.GAP
    elif staleness_hours > stale_threshold_bars:
        status = GapStalenessStatus.STALE
    else:
        status = GapStalenessStatus.OK

    return GapStalenessAssessmentV0(
        instrument_id=obs.instrument_id,
        venue_timestamp_utc=obs.venue_timestamp_utc,
        status=status,
        prior_venue_timestamp_utc=prior.venue_timestamp_utc,
        gap_hours=gap_hours if delta_ms > BAR_INTERVAL_MS else 0,
        staleness_hours=staleness_hours,
        collected_at_utc=obs.collected_at_utc,
    )


def build_overlap_validation_readiness_v0(
    states: Sequence[InstrumentArchiveStateV0],
) -> OverlapValidationReadinessV0:
    all_obs: list[ForwardOpenInterestObservationV0] = []
    for state in states:
        all_obs.extend(state.observations)
    if not all_obs:
        return OverlapValidationReadinessV0(
            status=OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
            archive_observation_count=0,
            earliest_venue_timestamp_utc=None,
            latest_venue_timestamp_utc=None,
            overlap_validation_executable=False,
            overlap_validation_blocked_reason="ARCHIVE_EMPTY",
        )
    earliest_ms = min(o.venue_timestamp_ms for o in all_obs)
    latest_ms = max(o.venue_timestamp_ms for o in all_obs)
    return OverlapValidationReadinessV0(
        status=OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
        archive_observation_count=len(all_obs),
        earliest_venue_timestamp_utc=_format_utc_ms(earliest_ms),
        latest_venue_timestamp_utc=_format_utc_ms(latest_ms),
        overlap_validation_executable=True,
        overlap_validation_blocked_reason=None,
    )


def serialize_observation_v0(obs: ForwardOpenInterestObservationV0) -> dict[str, Any]:
    return {
        "instrument_id": obs.instrument_id,
        "native_instrument_id": obs.native_instrument_id,
        "venue_timestamp_ms": obs.venue_timestamp_ms,
        "venue_timestamp_utc": obs.venue_timestamp_utc,
        "collected_at_ms": obs.collected_at_ms,
        "collected_at_utc": obs.collected_at_utc,
        "open_interest_raw": obs.open_interest_raw,
        "open_interest_unit": obs.open_interest_unit,
        "bar_interval": obs.bar_interval,
        "source_schema_version": obs.source_schema_version,
        "source_endpoint": obs.source_endpoint,
        "source_record_key": obs.source_record_key,
        "collection_mode": obs.collection_mode,
        "observation_digest": obs.observation_digest,
    }


def persist_archive_snapshot_v0(
    states: Sequence[InstrumentArchiveStateV0],
    *,
    output_dir: Path,
) -> dict[str, Any]:
    """Write append-only JSONL snapshot and manifest metadata. Offline/test harness only."""
    assert_archive_preconditions_v0()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = build_archive_config_v0()
    rows: list[dict[str, Any]] = []
    for state in states:
        for obs in state.observations:
            rows.append(serialize_observation_v0(obs))
    rows.sort(key=lambda r: (r["instrument_id"], r["venue_timestamp_ms"]))
    archive_digest = compute_sha256_digest({"rows": rows})
    jsonl_path = output_dir / "observations.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(serialize_canonical_json(row) + "\n")
    manifest = {
        "archive_kind": ARCHIVE_KIND,
        "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
        "module_version": MODULE_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "observation_count": len(rows),
        "instrument_count": len(states),
        "archive_digest": archive_digest,
        "config_digest": compute_sha256_digest(config),
        "implementation_digest": compute_implementation_digest_v0(),
        "append_only": True,
        "overlap_validation_status": OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
        "historical_backfill_allowed": False,
        "futures_only": True,
        "bitcoin_present": False,
    }
    manifest_path = output_dir / "archive_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def write_manifest_sha256_v0(bundle_dir: Path) -> None:
    entries: list[str] = []
    for path in sorted(bundle_dir.iterdir()):
        if path.name == "MANIFEST.sha256":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  {path.name}")
    (bundle_dir / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")

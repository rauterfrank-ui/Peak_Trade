"""Cross-sectional research data digest and period split materialization v0.

Deterministic, fail-closed materialization of versioned dataset envelopes and
chronological train/validation/out-of-sample splits for the final research fleet.
Research-only; no economic evaluation, no runtime or order effect.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.pit_futures_universe_manifest_v1 import (
    PointInTimeFuturesUniverseManifestV1,
    compute_sha256_digest,
    is_valid_digest,
    is_valid_rfc3339_utc,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    ProductionManifestMaterializationEnvelopeV1,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    BAR_GRANULARITY,
    PANEL_DATASET_VERSION,
    TIMESTAMP_SEMANTICS,
    TIMEZONE,
    InstrumentPanelSeriesV1,
    PanelBarV1,
    PanelValidationErrorCode,
    compute_panel_digest,
    compute_series_digest,
    validate_panel_series_v1,
)

PACKAGE_MARKER = (
    "PIT_FUTURES_CROSS_SECTIONAL_RESEARCH_DATA_DIGEST_PERIOD_SPLIT_MATERIALIZATION_V0=true"
)

MATERIALIZATION_VERSION = (
    "pit_futures_cross_sectional_research_data_digest_period_split_materialization.v0"
)
POLICY_CONFIG_REL_PATH = (
    "config/research/pit_cross_sectional_research_data_digest_period_split_policy_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = "research_dataset_envelope_canonical_json_v1"

DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
DATASET_SCHEMA_VERSION = "pit_cross_sectional_research_dataset_envelope.v0"
INGESTION_CONTRACT_VERSION = "okx_public_pt1h_panel_ingest.v1"
PERIOD_BINDING_ID = "pit_cross_sectional_research_chronological_holdout_v1"
SPLIT_POLICY_ID = "pit_cross_sectional_research_chronological_holdout_v1"

FORBIDDEN_INSTRUMENT_TOKENS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)

REASON_MISSING_PANEL_MANIFEST = "MISSING_PANEL_MANIFEST"
REASON_MISSING_PANEL_BARS = "MISSING_PANEL_BARS"
REASON_MISSING_SOURCE_REGISTRATION = "MISSING_SOURCE_REGISTRATION"
REASON_PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
REASON_UNIVERSE_MANIFEST_DIGEST_MISMATCH = "UNIVERSE_MANIFEST_DIGEST_MISMATCH"
REASON_INSUFFICIENT_SPLIT_HISTORY = "INSUFFICIENT_SPLIT_HISTORY"
REASON_PERIOD_OVERLAP = "PERIOD_OVERLAP"
REASON_LOOKAHEAD_BOUNDARY = "LOOKAHEAD_BOUNDARY"
REASON_MISSING_EMBARGO = "MISSING_EMBARGO"
REASON_MISSING_PURGE = "MISSING_PURGE"
REASON_SPLIT_OUTSIDE_COVERAGE = "SPLIT_OUTSIDE_COVERAGE"
REASON_POLICY_CONFIG_INVALID = "POLICY_CONFIG_INVALID"
REASON_DATA_QUALITY_FAIL = "DATA_QUALITY_FAIL"


class MaterializationStatus(str, Enum):
    MATERIALIZED = "MATERIALIZED"
    BLOCKED = "BLOCKED"


class DataQualityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CrossSectionalDatasetEnvelopeV0:
    dataset_id: str
    dataset_version: str
    dataset_schema_version: str
    venue_id: str
    market_type: str
    settlement_currency: str
    bar_interval: str
    instrument_ids: tuple[str, ...]
    instrument_count: int
    universe_manifest_ref: str
    universe_manifest_digest: str
    source_registration_ref: str
    source_registration_digest: str
    ingestion_contract_version: str
    data_start_time: str
    data_end_time: str
    row_count_total: int
    row_count_by_instrument: dict[str, int]
    finalized_bar_count_by_instrument: dict[str, int]
    missing_bar_summary: dict[str, int]
    duplicate_bar_summary: dict[str, int]
    out_of_order_summary: dict[str, int]
    timestamp_semantics: str
    timezone: str
    data_quality_status: str
    canonical_serialization_version: str
    data_digest: str
    config_digest: str
    implementation_digest: str
    materialization_status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class CrossSectionalPeriodSplitV0:
    period_binding_id: str
    period_binding_version: str
    split_policy_id: str
    split_policy_version: str
    dataset_id: str
    dataset_version: str
    data_digest: str
    training_start: str
    training_end: str
    validation_start: str
    validation_end: str
    out_of_sample_start: str
    out_of_sample_end: str
    embargo_duration: str
    purge_duration: str
    split_timezone: str
    boundary_semantics: str
    minimum_required_rows: int
    minimum_required_rows_by_instrument: dict[str, dict[str, int]]
    candidate_applicability: tuple[str, ...]
    period_digest: str
    config_digest: str
    implementation_digest: str
    status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ResearchDataDigestPeriodSplitMaterializationResultV0:
    dataset_envelope: CrossSectionalDatasetEnvelopeV0 | None
    period_split: CrossSectionalPeriodSplitV0 | None
    success: bool
    error_codes: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "materialization_version": MATERIALIZATION_VERSION,
            "module": "pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0",
        }
    )


def compute_policy_config_digest_v0(repo_root: Path | None = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[2]
    payload = json.loads((root / POLICY_CONFIG_REL_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(REASON_POLICY_CONFIG_INVALID)
    return _stable_digest(payload)


def load_split_policy_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / POLICY_CONFIG_REL_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(REASON_POLICY_CONFIG_INVALID)
    return payload


def _parse_duration_iso8601(value: str) -> timedelta:
    match = re.fullmatch(r"PT(\d+)H", value.strip())
    if not match:
        raise ValueError(REASON_POLICY_CONFIG_INVALID + ":duration")
    return timedelta(hours=int(match.group(1)))


def _parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _build_semantic_row_payload(
    series_list: Sequence[InstrumentPanelSeriesV1],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for series in sorted(series_list, key=lambda item: item.instrument_id):
        for bar in series.bars:
            rows.append(
                {
                    "close": bar.close,
                    "high": bar.high,
                    "instrument_id": bar.instrument_id,
                    "is_final": bar.is_final,
                    "low": bar.low,
                    "open": bar.open,
                    "timestamp_utc": bar.timestamp_utc,
                    "volume": bar.volume,
                }
            )
    rows.sort(key=lambda item: (item["instrument_id"], item["timestamp_utc"]))
    return rows


def compute_semantic_data_digest_v0(
    *,
    series_list: Sequence[InstrumentPanelSeriesV1],
    universe_manifest_digest: str,
    source_registration_digest: str,
    dataset_id: str,
    dataset_version: str,
    dataset_schema_version: str,
) -> str:
    payload = {
        "dataset_id": dataset_id,
        "dataset_schema_version": dataset_schema_version,
        "dataset_version": dataset_version,
        "instrument_ids": sorted(series.instrument_id for series in series_list),
        "rows": _build_semantic_row_payload(series_list),
        "source_registration_digest": source_registration_digest.strip().lower(),
        "universe_manifest_digest": universe_manifest_digest.strip().lower(),
    }
    return compute_sha256_digest(payload)


def _count_bars_in_range(
    series: InstrumentPanelSeriesV1,
    *,
    start_inclusive: str,
    end_inclusive: str,
) -> int:
    return sum(1 for bar in series.bars if start_inclusive <= bar.timestamp_utc <= end_inclusive)


def _panel_time_bounds(
    series_list: Sequence[InstrumentPanelSeriesV1],
) -> tuple[str, str]:
    if not series_list or not series_list[0].bars:
        raise ValueError(REASON_MISSING_PANEL_BARS)
    timestamps = [bar.timestamp_utc for bar in series_list[0].bars]
    return timestamps[0], timestamps[-1]


def _validate_split_policy_against_panel(
    policy: Mapping[str, Any],
    series_list: Sequence[InstrumentPanelSeriesV1],
) -> list[str]:
    reasons: list[str] = []
    required = (
        "training_start",
        "training_end",
        "validation_start",
        "validation_end",
        "out_of_sample_start",
        "out_of_sample_end",
        "embargo_duration",
        "purge_duration",
        "minimum_required_rows",
    )
    for field in required:
        if field not in policy:
            reasons.append(f"{REASON_POLICY_CONFIG_INVALID}:{field}")

    ts_fields = (
        "training_start",
        "training_end",
        "validation_start",
        "validation_end",
        "out_of_sample_start",
        "out_of_sample_end",
    )
    for field in ts_fields:
        raw = policy.get(field)
        if not isinstance(raw, str) or not is_valid_rfc3339_utc(raw):
            reasons.append(f"{REASON_POLICY_CONFIG_INVALID}:{field}")
            continue

    if reasons:
        return reasons

    training_start = str(policy["training_start"])
    training_end = str(policy["training_end"])
    validation_start = str(policy["validation_start"])
    validation_end = str(policy["validation_end"])
    oos_start = str(policy["out_of_sample_start"])
    oos_end = str(policy["out_of_sample_end"])

    if not (
        training_start <= training_end < validation_start <= validation_end < oos_start <= oos_end
    ):
        reasons.append(REASON_PERIOD_OVERLAP)

    try:
        embargo = _parse_duration_iso8601(str(policy["embargo_duration"]))
        purge = _parse_duration_iso8601(str(policy["purge_duration"]))
    except ValueError:
        reasons.append(REASON_MISSING_EMBARGO)
        embargo = purge = timedelta(0)

    if _parse_ts(training_end) + embargo > _parse_ts(validation_start):
        reasons.append(REASON_MISSING_EMBARGO)
    if _parse_ts(validation_end) + purge > _parse_ts(oos_start):
        reasons.append(REASON_MISSING_PURGE)

    panel_start, panel_end = _panel_time_bounds(series_list)
    for label, start, end in (
        ("training", training_start, training_end),
        ("validation", validation_start, validation_end),
        ("out_of_sample", oos_start, oos_end),
    ):
        if start < panel_start or end > panel_end:
            reasons.append(f"{REASON_SPLIT_OUTSIDE_COVERAGE}:{label}")

    min_rows = int(policy["minimum_required_rows"])
    split_ranges = (
        ("training", training_start, training_end),
        ("validation", validation_start, validation_end),
        ("out_of_sample", oos_start, oos_end),
    )
    for series in series_list:
        for label, start, end in split_ranges:
            count = _count_bars_in_range(series, start_inclusive=start, end_inclusive=end)
            if count < min_rows:
                reasons.append(
                    f"{REASON_INSUFFICIENT_SPLIT_HISTORY}:{series.instrument_id}:{label}:{count}"
                )

    return reasons


def compute_period_digest_v0(
    *,
    policy: Mapping[str, Any],
    data_digest: str,
    dataset_id: str,
    dataset_version: str,
) -> str:
    payload = {
        "boundary_semantics": str(policy["boundary_semantics"]),
        "data_digest": data_digest,
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "embargo_duration": str(policy["embargo_duration"]),
        "out_of_sample_end": str(policy["out_of_sample_end"]),
        "out_of_sample_start": str(policy["out_of_sample_start"]),
        "period_binding_id": str(policy["period_binding_id"]),
        "period_binding_version": str(policy["period_binding_version"]),
        "purge_duration": str(policy["purge_duration"]),
        "split_policy_id": str(policy["split_policy_id"]),
        "split_policy_version": str(policy["split_policy_version"]),
        "split_timezone": str(policy["split_timezone"]),
        "training_end": str(policy["training_end"]),
        "training_start": str(policy["training_start"]),
        "validation_end": str(policy["validation_end"]),
        "validation_start": str(policy["validation_start"]),
    }
    return compute_sha256_digest(payload)


def _blocked_dataset_envelope(
    *,
    reason_codes: Sequence[str],
    universe_manifest_ref: str = "",
    universe_manifest_digest: str = "",
    source_registration_ref: str = "",
    source_registration_digest: str = "",
    config_digest: str = "",
) -> CrossSectionalDatasetEnvelopeV0:
    zero_digest = "0" * 64
    return CrossSectionalDatasetEnvelopeV0(
        dataset_id=DATASET_ID,
        dataset_version=PANEL_DATASET_VERSION,
        dataset_schema_version=DATASET_SCHEMA_VERSION,
        venue_id="okx",
        market_type="futures",
        settlement_currency="USDT",
        bar_interval=BAR_GRANULARITY,
        instrument_ids=(),
        instrument_count=0,
        universe_manifest_ref=universe_manifest_ref,
        universe_manifest_digest=universe_manifest_digest,
        source_registration_ref=source_registration_ref,
        source_registration_digest=source_registration_digest,
        ingestion_contract_version=INGESTION_CONTRACT_VERSION,
        data_start_time="",
        data_end_time="",
        row_count_total=0,
        row_count_by_instrument={},
        finalized_bar_count_by_instrument={},
        missing_bar_summary={},
        duplicate_bar_summary={},
        out_of_order_summary={},
        timestamp_semantics=TIMESTAMP_SEMANTICS,
        timezone=TIMEZONE,
        data_quality_status=DataQualityStatus.FAIL.value,
        canonical_serialization_version=CANONICAL_SERIALIZATION_VERSION,
        data_digest=zero_digest,
        config_digest=config_digest,
        implementation_digest=compute_implementation_digest_v0(),
        materialization_status=MaterializationStatus.BLOCKED.value,
        reason_codes=tuple(sorted(set(reason_codes))),
    )


def materialize_cross_sectional_research_data_digest_and_period_split_v0(
    *,
    repo_root: Path,
    production_manifest: PointInTimeFuturesUniverseManifestV1,
    production_envelope: ProductionManifestMaterializationEnvelopeV1,
    panel_series: Sequence[InstrumentPanelSeriesV1] | None,
    source_registration_ref: str,
    source_registration_digest: str,
    split_policy: Mapping[str, Any] | None = None,
) -> ResearchDataDigestPeriodSplitMaterializationResultV0:
    config_digest = compute_policy_config_digest_v0(repo_root)
    policy = dict(split_policy or load_split_policy_v0(repo_root))
    universe_ref = production_envelope.manifest_reference or ""
    universe_digest = production_manifest.manifest_digest

    if production_envelope.manifest_digest != universe_digest:
        blocked = _blocked_dataset_envelope(
            reason_codes=(REASON_UNIVERSE_MANIFEST_DIGEST_MISMATCH,),
            universe_manifest_ref=universe_ref,
            universe_manifest_digest=universe_digest,
            config_digest=config_digest,
        )
        return ResearchDataDigestPeriodSplitMaterializationResultV0(
            dataset_envelope=blocked,
            period_split=None,
            success=False,
            error_codes=blocked.reason_codes,
        )

    if panel_series is None or len(panel_series) == 0:
        blocked = _blocked_dataset_envelope(
            reason_codes=(REASON_MISSING_PANEL_BARS,),
            universe_manifest_ref=universe_ref,
            universe_manifest_digest=universe_digest,
            source_registration_ref=source_registration_ref,
            source_registration_digest=source_registration_digest,
            config_digest=config_digest,
        )
        return ResearchDataDigestPeriodSplitMaterializationResultV0(
            dataset_envelope=blocked,
            period_split=None,
            success=False,
            error_codes=blocked.reason_codes,
        )

    if not is_valid_digest(source_registration_digest.strip().lower()):
        blocked = _blocked_dataset_envelope(
            reason_codes=(REASON_MISSING_SOURCE_REGISTRATION,),
            universe_manifest_ref=universe_ref,
            universe_manifest_digest=universe_digest,
            source_registration_ref=source_registration_ref,
            config_digest=config_digest,
        )
        return ResearchDataDigestPeriodSplitMaterializationResultV0(
            dataset_envelope=blocked,
            period_split=None,
            success=False,
            error_codes=blocked.reason_codes,
        )

    for series in panel_series:
        if _contains_forbidden_token(series.instrument_id):
            blocked = _blocked_dataset_envelope(
                reason_codes=(PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value,),
                universe_manifest_ref=universe_ref,
                universe_manifest_digest=universe_digest,
                source_registration_ref=source_registration_ref,
                source_registration_digest=source_registration_digest,
                config_digest=config_digest,
            )
            return ResearchDataDigestPeriodSplitMaterializationResultV0(
                dataset_envelope=blocked,
                period_split=None,
                success=False,
                error_codes=blocked.reason_codes,
            )

    panel_validation = validate_panel_series_v1(
        panel_series,
        min_instruments=5,
        generation_cutoff_utc=production_envelope.period_end_utc,
    )
    if not panel_validation.valid:
        blocked = _blocked_dataset_envelope(
            reason_codes=(REASON_PANEL_VALIDATION_FAILED, *panel_validation.error_codes),
            universe_manifest_ref=universe_ref,
            universe_manifest_digest=universe_digest,
            source_registration_ref=source_registration_ref,
            source_registration_digest=source_registration_digest,
            config_digest=config_digest,
        )
        return ResearchDataDigestPeriodSplitMaterializationResultV0(
            dataset_envelope=blocked,
            period_split=None,
            success=False,
            error_codes=blocked.reason_codes,
        )

    split_reasons = _validate_split_policy_against_panel(policy, panel_series)
    if split_reasons:
        data_start, data_end = _panel_time_bounds(panel_series)
        blocked = CrossSectionalDatasetEnvelopeV0(
            dataset_id=str(policy.get("dataset_id", DATASET_ID)),
            dataset_version=str(policy.get("dataset_version", PANEL_DATASET_VERSION)),
            dataset_schema_version=str(
                policy.get("dataset_schema_version", DATASET_SCHEMA_VERSION)
            ),
            venue_id=str(policy.get("venue_id", "okx")),
            market_type=str(policy.get("market_type", "futures")),
            settlement_currency=str(policy.get("settlement_currency", "USDT")),
            bar_interval=BAR_GRANULARITY,
            instrument_ids=tuple(sorted(s.instrument_id for s in panel_series)),
            instrument_count=len(panel_series),
            universe_manifest_ref=universe_ref,
            universe_manifest_digest=universe_digest,
            source_registration_ref=source_registration_ref,
            source_registration_digest=source_registration_digest.strip().lower(),
            ingestion_contract_version=INGESTION_CONTRACT_VERSION,
            data_start_time=data_start,
            data_end_time=data_end,
            row_count_total=sum(len(s.bars) for s in panel_series),
            row_count_by_instrument={s.instrument_id: len(s.bars) for s in panel_series},
            finalized_bar_count_by_instrument={
                s.instrument_id: sum(1 for b in s.bars if b.is_final) for s in panel_series
            },
            missing_bar_summary={},
            duplicate_bar_summary={},
            out_of_order_summary={},
            timestamp_semantics=TIMESTAMP_SEMANTICS,
            timezone=TIMEZONE,
            data_quality_status=DataQualityStatus.FAIL.value,
            canonical_serialization_version=CANONICAL_SERIALIZATION_VERSION,
            data_digest="0" * 64,
            config_digest=config_digest,
            implementation_digest=compute_implementation_digest_v0(),
            materialization_status=MaterializationStatus.BLOCKED.value,
            reason_codes=tuple(sorted(set(split_reasons))),
        )
        return ResearchDataDigestPeriodSplitMaterializationResultV0(
            dataset_envelope=blocked,
            period_split=None,
            success=False,
            error_codes=blocked.reason_codes,
        )

    data_start, data_end = _panel_time_bounds(panel_series)
    data_digest = compute_semantic_data_digest_v0(
        series_list=panel_series,
        universe_manifest_digest=universe_digest,
        source_registration_digest=source_registration_digest,
        dataset_id=str(policy.get("dataset_id", DATASET_ID)),
        dataset_version=str(policy.get("dataset_version", PANEL_DATASET_VERSION)),
        dataset_schema_version=str(policy.get("dataset_schema_version", DATASET_SCHEMA_VERSION)),
    )

    row_count_by_instrument = {series.instrument_id: len(series.bars) for series in panel_series}
    finalized_counts = {
        series.instrument_id: sum(1 for bar in series.bars if bar.is_final)
        for series in panel_series
    }

    dataset_envelope = CrossSectionalDatasetEnvelopeV0(
        dataset_id=str(policy.get("dataset_id", DATASET_ID)),
        dataset_version=str(policy.get("dataset_version", PANEL_DATASET_VERSION)),
        dataset_schema_version=str(policy.get("dataset_schema_version", DATASET_SCHEMA_VERSION)),
        venue_id=str(policy.get("venue_id", "okx")),
        market_type=str(policy.get("market_type", "futures")),
        settlement_currency=str(policy.get("settlement_currency", "USDT")),
        bar_interval=BAR_GRANULARITY,
        instrument_ids=tuple(sorted(s.instrument_id for s in panel_series)),
        instrument_count=len(panel_series),
        universe_manifest_ref=universe_ref,
        universe_manifest_digest=universe_digest,
        source_registration_ref=source_registration_ref,
        source_registration_digest=source_registration_digest.strip().lower(),
        ingestion_contract_version=INGESTION_CONTRACT_VERSION,
        data_start_time=data_start,
        data_end_time=data_end,
        row_count_total=sum(row_count_by_instrument.values()),
        row_count_by_instrument=row_count_by_instrument,
        finalized_bar_count_by_instrument=finalized_counts,
        missing_bar_summary={},
        duplicate_bar_summary={},
        out_of_order_summary={},
        timestamp_semantics=TIMESTAMP_SEMANTICS,
        timezone=TIMEZONE,
        data_quality_status=DataQualityStatus.PASS.value,
        canonical_serialization_version=CANONICAL_SERIALIZATION_VERSION,
        data_digest=data_digest,
        config_digest=config_digest,
        implementation_digest=compute_implementation_digest_v0(),
        materialization_status=MaterializationStatus.MATERIALIZED.value,
        reason_codes=(),
    )

    split_ranges = (
        ("training", str(policy["training_start"]), str(policy["training_end"])),
        ("validation", str(policy["validation_start"]), str(policy["validation_end"])),
        ("out_of_sample", str(policy["out_of_sample_start"]), str(policy["out_of_sample_end"])),
    )
    min_rows_by_instrument: dict[str, dict[str, int]] = {}
    for series in panel_series:
        min_rows_by_instrument[series.instrument_id] = {
            label: _count_bars_in_range(series, start_inclusive=start, end_inclusive=end)
            for label, start, end in split_ranges
        }

    period_digest = compute_period_digest_v0(
        policy=policy,
        data_digest=data_digest,
        dataset_id=dataset_envelope.dataset_id,
        dataset_version=dataset_envelope.dataset_version,
    )

    period_split = CrossSectionalPeriodSplitV0(
        period_binding_id=str(policy["period_binding_id"]),
        period_binding_version=str(policy["period_binding_version"]),
        split_policy_id=str(policy["split_policy_id"]),
        split_policy_version=str(policy["split_policy_version"]),
        dataset_id=dataset_envelope.dataset_id,
        dataset_version=dataset_envelope.dataset_version,
        data_digest=data_digest,
        training_start=str(policy["training_start"]),
        training_end=str(policy["training_end"]),
        validation_start=str(policy["validation_start"]),
        validation_end=str(policy["validation_end"]),
        out_of_sample_start=str(policy["out_of_sample_start"]),
        out_of_sample_end=str(policy["out_of_sample_end"]),
        embargo_duration=str(policy["embargo_duration"]),
        purge_duration=str(policy["purge_duration"]),
        split_timezone=str(policy["split_timezone"]),
        boundary_semantics=str(policy["boundary_semantics"]),
        minimum_required_rows=int(policy["minimum_required_rows"]),
        minimum_required_rows_by_instrument=min_rows_by_instrument,
        candidate_applicability=("trend_following", "bollinger_bands", "momentum_1h"),
        period_digest=period_digest,
        config_digest=config_digest,
        implementation_digest=compute_implementation_digest_v0(),
        status=MaterializationStatus.MATERIALIZED.value,
        reason_codes=(),
    )

    return ResearchDataDigestPeriodSplitMaterializationResultV0(
        dataset_envelope=dataset_envelope,
        period_split=period_split,
        success=True,
        error_codes=(),
    )


def dataset_envelope_to_dict(envelope: CrossSectionalDatasetEnvelopeV0) -> dict[str, Any]:
    return {
        "bar_interval": envelope.bar_interval,
        "canonical_serialization_version": envelope.canonical_serialization_version,
        "config_digest": envelope.config_digest,
        "data_digest": envelope.data_digest,
        "data_end_time": envelope.data_end_time,
        "data_quality_status": envelope.data_quality_status,
        "data_start_time": envelope.data_start_time,
        "dataset_id": envelope.dataset_id,
        "dataset_schema_version": envelope.dataset_schema_version,
        "dataset_version": envelope.dataset_version,
        "duplicate_bar_summary": envelope.duplicate_bar_summary,
        "finalized_bar_count_by_instrument": envelope.finalized_bar_count_by_instrument,
        "implementation_digest": envelope.implementation_digest,
        "ingestion_contract_version": envelope.ingestion_contract_version,
        "instrument_count": envelope.instrument_count,
        "instrument_ids": list(envelope.instrument_ids),
        "market_type": envelope.market_type,
        "materialization_status": envelope.materialization_status,
        "missing_bar_summary": envelope.missing_bar_summary,
        "out_of_order_summary": envelope.out_of_order_summary,
        "reason_codes": list(envelope.reason_codes),
        "row_count_by_instrument": envelope.row_count_by_instrument,
        "row_count_total": envelope.row_count_total,
        "settlement_currency": envelope.settlement_currency,
        "source_registration_digest": envelope.source_registration_digest,
        "source_registration_ref": envelope.source_registration_ref,
        "timestamp_semantics": envelope.timestamp_semantics,
        "timezone": envelope.timezone,
        "universe_manifest_digest": envelope.universe_manifest_digest,
        "universe_manifest_ref": envelope.universe_manifest_ref,
        "venue_id": envelope.venue_id,
    }


def period_split_to_dict(split: CrossSectionalPeriodSplitV0) -> dict[str, Any]:
    return {
        "boundary_semantics": split.boundary_semantics,
        "candidate_applicability": list(split.candidate_applicability),
        "config_digest": split.config_digest,
        "data_digest": split.data_digest,
        "dataset_id": split.dataset_id,
        "dataset_version": split.dataset_version,
        "embargo_duration": split.embargo_duration,
        "implementation_digest": split.implementation_digest,
        "minimum_required_rows": split.minimum_required_rows,
        "minimum_required_rows_by_instrument": split.minimum_required_rows_by_instrument,
        "out_of_sample_end": split.out_of_sample_end,
        "out_of_sample_start": split.out_of_sample_start,
        "period_binding_id": split.period_binding_id,
        "period_binding_version": split.period_binding_version,
        "period_digest": split.period_digest,
        "purge_duration": split.purge_duration,
        "reason_codes": list(split.reason_codes),
        "split_policy_id": split.split_policy_id,
        "split_policy_version": split.split_policy_version,
        "split_timezone": split.split_timezone,
        "status": split.status,
        "training_end": split.training_end,
        "training_start": split.training_start,
        "validation_end": split.validation_end,
        "validation_start": split.validation_start,
    }


def load_panel_series_from_staging(
    staging_root: Path,
) -> tuple[tuple[InstrumentPanelSeriesV1, ...], str]:
    panel_dir = staging_root / "panel"
    manifest_path = panel_dir / "panel_dataset_manifest.json"
    bars_path = panel_dir / "normalized_panel_bars.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(REASON_MISSING_PANEL_MANIFEST)
    if not bars_path.is_file():
        raise FileNotFoundError(REASON_MISSING_PANEL_BARS)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = json.loads(bars_path.read_text(encoding="utf-8"))
    grouped: dict[str, list[PanelBarV1]] = {}
    for row in rows:
        bar = PanelBarV1(
            instrument_id=str(row["instrument_id"]),
            timestamp_utc=str(row["timestamp_utc"]),
            open=str(row["open"]),
            high=str(row["high"]),
            low=str(row["low"]),
            close=str(row["close"]),
            volume=str(row["volume"]),
            is_final=bool(row["is_final"]),
        )
        grouped.setdefault(bar.instrument_id, []).append(bar)
    series_list: list[InstrumentPanelSeriesV1] = []
    native_by_id = dict(
        zip(manifest["instrument_ids"], manifest["native_instrument_ids"], strict=True)
    )
    for instrument_id in sorted(grouped):
        bars = tuple(sorted(grouped[instrument_id], key=lambda item: item.timestamp_utc))
        interim = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=native_by_id.get(instrument_id, instrument_id),
            bars=bars,
            series_digest="0" * 64,
        )
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=interim.instrument_id,
                native_instrument_id=interim.native_instrument_id,
                bars=interim.bars,
                series_digest=compute_series_digest(interim),
            )
        )
    panel_ref = (
        f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{manifest['panel_id']}:"
        f"sha256:{manifest['manifest_digest']}"
    )
    return tuple(series_list), panel_ref


__all__ = [
    "CANONICAL_SERIALIZATION_VERSION",
    "DATASET_ID",
    "DATASET_SCHEMA_VERSION",
    "INGESTION_CONTRACT_VERSION",
    "MATERIALIZATION_VERSION",
    "PERIOD_BINDING_ID",
    "POLICY_CONFIG_REL_PATH",
    "SPLIT_POLICY_ID",
    "CrossSectionalDatasetEnvelopeV0",
    "CrossSectionalPeriodSplitV0",
    "DataQualityStatus",
    "MaterializationStatus",
    "ResearchDataDigestPeriodSplitMaterializationResultV0",
    "compute_implementation_digest_v0",
    "compute_period_digest_v0",
    "compute_policy_config_digest_v0",
    "compute_semantic_data_digest_v0",
    "dataset_envelope_to_dict",
    "load_panel_series_from_staging",
    "load_split_policy_v0",
    "materialize_cross_sectional_research_data_digest_and_period_split_v0",
    "period_split_to_dict",
]

"""Read-only registry consumer binding for pit_futures_universe_manifest_generator_v1 — Slice D.

Research-only, non-authorizing. Pure offline binding: no I/O, no network, no clock.
Consumes an explicit validated registry snapshot; never writes, repairs, or reconstructs registry data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    SCHEMA_VERSION,
    InstrumentLifecycleIntervalV1,
    RegistrySnapshotV1,
    format_registry_reference_v1,
    query_lifecycle_at_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)
from src.research.pit_futures_universe_manifest_generator_v1 import (
    GENERATOR_VERSION,
    INPUT_CONTRACT_VERSION,
    GeneratorEpochInputV1,
    PitFuturesUniverseManifestGeneratorInputV1,
    PitFuturesUniverseManifestGeneratorResultV1,
    RawInstrumentRecordV1,
    generate_pit_futures_universe_manifest_v1,
)
from src.research.pit_futures_universe_manifest_v1 import (
    PointInTimeFuturesUniverseManifestV1,
    compute_sha256_digest,
    is_valid_digest,
    is_valid_rfc3339_utc,
)

PACKAGE_MARKER = "PIT_FUTURES_UNIVERSE_MANIFEST_GENERATOR_REGISTRY_CONSUMER_BINDING_V1=true"
BINDING_VERSION = "pit_futures_universe_manifest_generator_registry_consumer_binding.v1"
BINDING_INPUT_CONTRACT_VERSION = (
    "pit_futures_universe_manifest_generator_registry_consumer_binding_input.v1"
)
BINDING_MODULE_NAME = "pit_futures_universe_manifest_generator_registry_consumer_binding_v1"

_SUPPORTED_REGISTRY_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})
_CURRENT_STATE_FALLBACK_MARKERS = frozenset(
    {"current_state", "use_current_state", "fallback_to_current", "now()", "latest"}
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")


class RegistryBindingErrorCode(str, Enum):
    INVALID_BINDING_INPUT = "INVALID_BINDING_INPUT"
    MISSING_REGISTRY = "MISSING_REGISTRY"
    CORRUPT_REGISTRY = "CORRUPT_REGISTRY"
    REGISTRY_DIGEST_MISMATCH = "REGISTRY_DIGEST_MISMATCH"
    REGISTRY_VERSION_MISMATCH = "REGISTRY_VERSION_MISMATCH"
    UNSUPPORTED_REGISTRY_VERSION = "UNSUPPORTED_REGISTRY_VERSION"
    UNKNOWN_HISTORICAL_MEMBERSHIP = "UNKNOWN_HISTORICAL_MEMBERSHIP"
    AMBIGUOUS_INSTRUMENT_LIFECYCLE = "AMBIGUOUS_INSTRUMENT_LIFECYCLE"
    MISSING_SUPPLEMENTARY_MARKET_DATA = "MISSING_SUPPLEMENTARY_MARKET_DATA"
    CURRENT_STATE_FALLBACK_BLOCKED = "CURRENT_STATE_FALLBACK_BLOCKED"
    GENERATOR_FAILED = "GENERATOR_FAILED"


@dataclass(frozen=True)
class SupplementaryInstrumentMarketDataV1:
    instrument_id: str
    source_ref: str
    record_digest: str
    market_type: str
    history_bars_available: int
    required_history_bars: int
    data_availability_status: str


@dataclass(frozen=True)
class RegistryBoundEpochInputV1:
    score_epoch: int
    finalized_bar_close: str
    historical_as_of_time: str


@dataclass(frozen=True)
class PitFuturesUniverseManifestGeneratorRegistryBindingInputV1:
    binding_input_contract_version: str
    binding_version: str
    registry_artifact_id: str
    bound_registry_schema_version: str
    bound_registry_snapshot_version: int
    bound_registry_snapshot_digest: str
    registry_snapshot: RegistrySnapshotV1 | None
    input_contract_version: str
    artifact_id: str
    venue_id: str
    universe_id: str
    hypothesis_id: str
    universe_policy_id: str
    universe_policy_version: str
    inclusion_policy_version: str
    exclusion_policy_version: str
    generator_version: str
    generated_at: str
    bar_interval: str
    minimum_history_bars: int
    minimum_required_member_count: int
    venue_scope: tuple[str, ...]
    source_snapshot_refs: tuple[str, ...]
    source_digests: tuple[str, ...]
    period_binding_ref: str
    config_digest: str
    implementation_digest: str
    supplementary_market_data: tuple[SupplementaryInstrumentMarketDataV1, ...]
    epochs: tuple[RegistryBoundEpochInputV1, ...]


@dataclass(frozen=True)
class RegistryBindingProvenanceV1:
    registry_schema_version: str
    registry_schema_name: str
    registry_artifact_id: str
    registry_snapshot_version: int
    registry_content_digest: str
    registry_reference: str
    registry_policy_version: str
    historical_as_of_times: tuple[str, ...]
    generator_config_digest: str
    generator_implementation_digest: str
    binding_version: str
    binding_implementation_digest: str
    output_manifest_digest: str | None


@dataclass(frozen=True)
class PitFuturesUniverseManifestGeneratorRegistryBindingResultV1:
    success: bool
    manifest: PointInTimeFuturesUniverseManifestV1 | None
    manifest_reference: str | None
    generator_result: PitFuturesUniverseManifestGeneratorResultV1 | None
    provenance: RegistryBindingProvenanceV1 | None
    error_codes: tuple[str, ...]
    generator_error_codes: tuple[str, ...] = ()
    validator_reason_codes: tuple[str, ...] = ()


def _add(errors: list[str], code: RegistryBindingErrorCode) -> None:
    value = code.value
    if value not in errors:
        errors.append(value)


def _validate_source_ref(value: str, errors: list[str]) -> bool:
    if not value.strip():
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
        return False
    if _ABSOLUTE_PATH_PATTERN.search(value):
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
        return False
    lowered = value.strip().lower()
    for marker in _CURRENT_STATE_FALLBACK_MARKERS:
        if marker in lowered:
            _add(errors, RegistryBindingErrorCode.CURRENT_STATE_FALLBACK_BLOCKED)
            return False
    return True


def _compute_binding_implementation_digest_payload() -> dict[str, str]:
    return {
        "binding_version": BINDING_VERSION,
        "module": BINDING_MODULE_NAME,
    }


def compute_binding_implementation_digest() -> str:
    return compute_sha256_digest(_compute_binding_implementation_digest_payload())


def _active_intervals(snapshot: RegistrySnapshotV1) -> dict[str, InstrumentLifecycleIntervalV1]:
    grouped: dict[str, list[InstrumentLifecycleIntervalV1]] = {}
    for interval in snapshot.intervals:
        if interval.superseded_by_version is not None:
            continue
        grouped.setdefault(interval.instrument_id, []).append(interval)

    resolved: dict[str, InstrumentLifecycleIntervalV1] = {}
    for instrument_id, intervals in grouped.items():
        if len(intervals) > 1:
            return {"__AMBIGUOUS__": intervals[0]}
        resolved[instrument_id] = intervals[0]
    return resolved


def _interval_to_raw_record(
    interval: InstrumentLifecycleIntervalV1,
    supplementary: SupplementaryInstrumentMarketDataV1,
) -> RawInstrumentRecordV1:
    return RawInstrumentRecordV1(
        source_ref=supplementary.source_ref.strip(),
        record_digest=supplementary.record_digest.strip().lower(),
        venue_id=interval.venue_id.strip().lower(),
        market_type=supplementary.market_type.strip().lower(),
        contract_type=interval.contract_type.strip().lower(),
        base_asset=interval.base_asset.strip().upper(),
        quote_asset=interval.quote_asset.strip().upper(),
        settlement_asset=interval.settlement_asset.strip().upper(),
        venue_symbol=(interval.venue_symbol or "").strip(),
        native_instrument_id=interval.native_instrument_id,
        contract_expiry=interval.contract_expiry,
        listing_time=interval.listing_time,
        delisting_time=interval.delisting_time,
        eligible_from=interval.eligible_from,
        eligible_until=interval.eligible_until,
        expiry_time=interval.expiry_time,
        history_bars_available=supplementary.history_bars_available,
        required_history_bars=supplementary.required_history_bars,
        data_availability_status=supplementary.data_availability_status.strip().upper(),
    )


def _validate_binding_input(
    inp: PitFuturesUniverseManifestGeneratorRegistryBindingInputV1,
) -> list[str]:
    errors: list[str] = []

    if inp.binding_input_contract_version != BINDING_INPUT_CONTRACT_VERSION:
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
    if inp.binding_version != BINDING_VERSION:
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
    if inp.input_contract_version != INPUT_CONTRACT_VERSION:
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
    if inp.generator_version != GENERATOR_VERSION:
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)

    if not inp.registry_artifact_id.strip():
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
    if inp.bound_registry_schema_version not in _SUPPORTED_REGISTRY_SCHEMA_VERSIONS:
        _add(errors, RegistryBindingErrorCode.UNSUPPORTED_REGISTRY_VERSION)
    if not is_valid_digest(inp.bound_registry_snapshot_digest.strip().lower()):
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
    if inp.bound_registry_snapshot_version < 1:
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)

    if inp.registry_snapshot is None:
        _add(errors, RegistryBindingErrorCode.MISSING_REGISTRY)
        return sorted(errors)

    snapshot = inp.registry_snapshot
    if snapshot.schema_version != inp.bound_registry_schema_version:
        _add(errors, RegistryBindingErrorCode.UNSUPPORTED_REGISTRY_VERSION)
    if snapshot.registry_snapshot_version != inp.bound_registry_snapshot_version:
        _add(errors, RegistryBindingErrorCode.REGISTRY_VERSION_MISMATCH)
    if snapshot.registry_snapshot_digest != inp.bound_registry_snapshot_digest.strip().lower():
        _add(errors, RegistryBindingErrorCode.REGISTRY_DIGEST_MISMATCH)

    for ref in inp.source_snapshot_refs:
        _validate_source_ref(ref, errors)
    _validate_source_ref(inp.period_binding_ref, errors)

    if not inp.epochs:
        _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)

    for epoch in inp.epochs:
        if not is_valid_rfc3339_utc(epoch.finalized_bar_close):
            _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
        if not is_valid_rfc3339_utc(epoch.historical_as_of_time):
            _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)
        if epoch.finalized_bar_close != epoch.historical_as_of_time:
            _add(errors, RegistryBindingErrorCode.INVALID_BINDING_INPUT)

    if not errors and snapshot is not None:
        validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot)
        if validation.verdict != ValidationVerdict.ACCEPTED:
            _add(errors, RegistryBindingErrorCode.CORRUPT_REGISTRY)

    return sorted(errors)


def _resolve_epoch_records(
    *,
    snapshot: RegistrySnapshotV1,
    supplementary_by_id: dict[str, SupplementaryInstrumentMarketDataV1],
    active_by_id: dict[str, InstrumentLifecycleIntervalV1],
    query_instant: str,
    errors: list[str],
) -> tuple[RawInstrumentRecordV1, ...]:
    records: list[RawInstrumentRecordV1] = []

    for instrument_id in sorted(active_by_id):
        interval = active_by_id[instrument_id]
        query = query_lifecycle_at_snapshot_v1(
            snapshot,
            instrument_id=instrument_id,
            query_instant=query_instant,
        )
        if query.error_codes:
            if RegistryBindingErrorCode.UNKNOWN_HISTORICAL_MEMBERSHIP.value not in errors:
                _add(errors, RegistryBindingErrorCode.UNKNOWN_HISTORICAL_MEMBERSHIP)
            continue

        supplementary = supplementary_by_id.get(instrument_id)
        if supplementary is None:
            _add(errors, RegistryBindingErrorCode.MISSING_SUPPLEMENTARY_MARKET_DATA)
            continue

        records.append(_interval_to_raw_record(interval, supplementary))

    return tuple(records)


def generate_pit_futures_universe_manifest_from_registry_binding_v1(
    binding_input: PitFuturesUniverseManifestGeneratorRegistryBindingInputV1,
) -> PitFuturesUniverseManifestGeneratorRegistryBindingResultV1:
    """Bind an explicit validated registry snapshot to the offline manifest generator."""
    errors = _validate_binding_input(binding_input)
    if errors:
        return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
            False,
            None,
            None,
            None,
            None,
            tuple(errors),
        )

    assert binding_input.registry_snapshot is not None
    snapshot = binding_input.registry_snapshot

    active_by_id = _active_intervals(snapshot)
    if "__AMBIGUOUS__" in active_by_id:
        return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
            False,
            None,
            None,
            None,
            None,
            (RegistryBindingErrorCode.AMBIGUOUS_INSTRUMENT_LIFECYCLE.value,),
        )

    supplementary_by_id: dict[str, SupplementaryInstrumentMarketDataV1] = {}
    for item in binding_input.supplementary_market_data:
        key = item.instrument_id.strip()
        if key in supplementary_by_id:
            return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
                False,
                None,
                None,
                None,
                None,
                (RegistryBindingErrorCode.INVALID_BINDING_INPUT.value,),
            )
        supplementary_by_id[key] = item

    for instrument_id in sorted(supplementary_by_id):
        if instrument_id not in active_by_id:
            return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
                False,
                None,
                None,
                None,
                None,
                (RegistryBindingErrorCode.UNKNOWN_HISTORICAL_MEMBERSHIP.value,),
            )

    registry_reference = format_registry_reference_v1(
        artifact_id=binding_input.registry_artifact_id.strip(),
        registry_snapshot_digest=snapshot.registry_snapshot_digest,
    )
    merged_refs = tuple(
        sorted({registry_reference, *(ref.strip() for ref in binding_input.source_snapshot_refs)})
    )
    merged_digests = tuple(
        digest.strip().lower()
        for digest in (
            snapshot.registry_snapshot_digest,
            *binding_input.source_digests,
        )
    )

    generator_epochs: list[GeneratorEpochInputV1] = []
    for epoch in sorted(binding_input.epochs, key=lambda item: item.score_epoch):
        epoch_errors: list[str] = []
        raw_records = _resolve_epoch_records(
            snapshot=snapshot,
            supplementary_by_id=supplementary_by_id,
            active_by_id=active_by_id,
            query_instant=epoch.historical_as_of_time,
            errors=epoch_errors,
        )
        if epoch_errors:
            return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
                False,
                None,
                None,
                None,
                None,
                tuple(sorted(set(epoch_errors))),
            )
        generator_epochs.append(
            GeneratorEpochInputV1(
                score_epoch=epoch.score_epoch,
                finalized_bar_close=epoch.finalized_bar_close,
                raw_instrument_records=raw_records,
            )
        )

    generator_input = PitFuturesUniverseManifestGeneratorInputV1(
        input_contract_version=binding_input.input_contract_version,
        artifact_id=binding_input.artifact_id.strip(),
        venue_id=binding_input.venue_id.strip().lower(),
        universe_id=binding_input.universe_id.strip(),
        hypothesis_id=binding_input.hypothesis_id.strip(),
        universe_policy_id=binding_input.universe_policy_id.strip(),
        universe_policy_version=binding_input.universe_policy_version.strip(),
        inclusion_policy_version=binding_input.inclusion_policy_version.strip(),
        exclusion_policy_version=binding_input.exclusion_policy_version.strip(),
        generator_version=binding_input.generator_version,
        generated_at=binding_input.generated_at,
        bar_interval=binding_input.bar_interval.strip(),
        minimum_history_bars=binding_input.minimum_history_bars,
        minimum_required_member_count=binding_input.minimum_required_member_count,
        venue_scope=binding_input.venue_scope,
        source_snapshot_refs=merged_refs,
        source_digests=merged_digests,
        period_binding_ref=binding_input.period_binding_ref.strip(),
        config_digest=binding_input.config_digest.strip().lower(),
        implementation_digest=binding_input.implementation_digest.strip().lower(),
        epochs=tuple(generator_epochs),
    )

    generator_result = generate_pit_futures_universe_manifest_v1(generator_input)
    if not generator_result.success or generator_result.manifest is None:
        return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
            False,
            None,
            None,
            generator_result,
            None,
            (RegistryBindingErrorCode.GENERATOR_FAILED.value,),
            generator_result.error_codes,
            generator_result.validator_reason_codes,
        )

    provenance = RegistryBindingProvenanceV1(
        registry_schema_version=snapshot.schema_version,
        registry_schema_name=snapshot.schema_name,
        registry_artifact_id=binding_input.registry_artifact_id.strip(),
        registry_snapshot_version=snapshot.registry_snapshot_version,
        registry_content_digest=snapshot.registry_snapshot_digest,
        registry_reference=registry_reference,
        registry_policy_version=snapshot.policy_version,
        historical_as_of_times=tuple(
            epoch.historical_as_of_time
            for epoch in sorted(binding_input.epochs, key=lambda item: item.score_epoch)
        ),
        generator_config_digest=generator_input.config_digest,
        generator_implementation_digest=generator_input.implementation_digest,
        binding_version=BINDING_VERSION,
        binding_implementation_digest=compute_binding_implementation_digest(),
        output_manifest_digest=generator_result.manifest.manifest_digest,
    )

    return PitFuturesUniverseManifestGeneratorRegistryBindingResultV1(
        True,
        generator_result.manifest,
        generator_result.manifest_reference,
        generator_result,
        provenance,
        (),
        generator_result.error_codes,
        generator_result.validator_reason_codes,
    )


__all__ = [
    "BINDING_INPUT_CONTRACT_VERSION",
    "BINDING_VERSION",
    "RegistryBindingErrorCode",
    "RegistryBindingProvenanceV1",
    "RegistryBoundEpochInputV1",
    "PitFuturesUniverseManifestGeneratorRegistryBindingInputV1",
    "PitFuturesUniverseManifestGeneratorRegistryBindingResultV1",
    "SupplementaryInstrumentMarketDataV1",
    "compute_binding_implementation_digest",
    "generate_pit_futures_universe_manifest_from_registry_binding_v1",
]

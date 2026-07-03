"""Generic offline generator for point-in-time futures universe manifest v1.

Research-only, non-authorizing. Side-effect-free core: no I/O, no network, no clock.
Consumes explicit lifecycle records; does not fetch historical registry data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
    InstrumentIdCanonicalizationInputV1,
    canonicalize_instrument_id_v1,
)
from src.research.pit_futures_universe_manifest_v1 import (
    MARKET_TYPE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SCORE_EPOCH_SEMANTICS,
    ContractType,
    DataAvailabilityStatus,
    EligibilityStatus,
    MembershipStatus,
    PointInTimeFuturesUniverseEpochV1,
    PointInTimeFuturesUniverseExclusionV1,
    PointInTimeFuturesUniverseManifestV1,
    PointInTimeFuturesUniverseMemberV1,
    attach_computed_digests,
    compute_sha256_digest,
    default_manifest_policy_constants,
    format_pit_universe_manifest_reference_v1,
    is_valid_digest,
    is_valid_rfc3339_utc,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)

PACKAGE_MARKER = "PIT_FUTURES_UNIVERSE_MANIFEST_GENERATOR_V1=true"
GENERATOR_VERSION = "pit_futures_universe_manifest_generator.v1"
INPUT_CONTRACT_VERSION = "pit_futures_universe_manifest_generator_input.v1"
GENERATOR_MODULE_NAME = "pit_futures_universe_manifest_generator_v1"

_PERPETUAL_TYPES = frozenset(
    {ContractType.LINEAR_PERPETUAL.value, ContractType.INVERSE_PERPETUAL.value}
)
_DATED_TYPES = frozenset(
    {ContractType.LINEAR_DATED_FUTURE.value, ContractType.INVERSE_DATED_FUTURE.value}
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")
_ARTIFACT_ID_PATTERN = re.compile(r"^[a-z0-9_\-]{1,128}$")
_VENUE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class GeneratorErrorCode(str, Enum):
    INVALID_INPUT_CONTRACT = "INVALID_INPUT_CONTRACT"
    UNKNOWN_VENUE = "UNKNOWN_VENUE"
    NON_FUTURES_INSTRUMENT = "NON_FUTURES_INSTRUMENT"
    BITCOIN_INSTRUMENT_BLOCKED = "BITCOIN_INSTRUMENT_BLOCKED"
    SPOT_INSTRUMENT_BLOCKED = "SPOT_INSTRUMENT_BLOCKED"
    SYNTHETIC_SPOT_BLOCKED = "SYNTHETIC_SPOT_BLOCKED"
    INVALID_CANONICAL_INSTRUMENT_ID = "INVALID_CANONICAL_INSTRUMENT_ID"
    MISSING_LISTING_TIME = "MISSING_LISTING_TIME"
    MISSING_EXPIRY_OR_PERPETUAL_CLASSIFICATION = "MISSING_EXPIRY_OR_PERPETUAL_CLASSIFICATION"
    INVALID_LIFECYCLE_INTERVAL = "INVALID_LIFECYCLE_INTERVAL"
    AMBIGUOUS_LIFECYCLE_STATE = "AMBIGUOUS_LIFECYCLE_STATE"
    DUPLICATE_CANONICAL_INSTRUMENT_ID = "DUPLICATE_CANONICAL_INSTRUMENT_ID"
    CONFLICTING_SOURCE_RECORDS = "CONFLICTING_SOURCE_RECORDS"
    SOURCE_DIGEST_MISMATCH = "SOURCE_DIGEST_MISMATCH"
    EMPTY_EPOCH = "EMPTY_EPOCH"
    INVALID_EPOCH_ORDER = "INVALID_EPOCH_ORDER"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"


@dataclass(frozen=True)
class RawInstrumentRecordV1:
    source_ref: str
    record_digest: str
    venue_id: str
    market_type: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    venue_symbol: str
    native_instrument_id: str | None
    contract_expiry: str | None
    listing_time: str | None
    delisting_time: str | None
    eligible_from: str | None
    eligible_until: str | None
    expiry_time: str | None
    history_bars_available: int
    required_history_bars: int
    data_availability_status: str


@dataclass(frozen=True)
class GeneratorEpochInputV1:
    score_epoch: int
    finalized_bar_close: str
    raw_instrument_records: tuple[RawInstrumentRecordV1, ...]


@dataclass(frozen=True)
class PitFuturesUniverseManifestGeneratorInputV1:
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
    epochs: tuple[GeneratorEpochInputV1, ...]


@dataclass(frozen=True)
class PitFuturesUniverseManifestGeneratorResultV1:
    success: bool
    manifest: PointInTimeFuturesUniverseManifestV1 | None
    manifest_reference: str | None
    error_codes: tuple[str, ...]
    validator_reason_codes: tuple[str, ...] = ()


def _add(errors: list[str], code: GeneratorErrorCode) -> None:
    value = code.value
    if value not in errors:
        errors.append(value)


def _parse_utc_instant(value: str) -> tuple[int, int] | None:
    if not is_valid_rfc3339_utc(value):
        return None
    date_part, time_part = value.split("T", 1)
    year, month, day = (int(part) for part in date_part.split("-"))
    hour = int(time_part[0:2])
    minute = int(time_part[3:5])
    second = int(time_part[6:8])
    return (year * 10_000 + month * 100 + day, hour * 10_000 + minute * 100 + second)


def _validate_source_ref(value: str, errors: list[str]) -> bool:
    if not value.strip():
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
        return False
    if _ABSOLUTE_PATH_PATTERN.search(value):
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
        return False
    return True


def _compute_config_digest_payload(
    inp: PitFuturesUniverseManifestGeneratorInputV1,
) -> dict[str, Any]:
    return {
        "artifact_id": inp.artifact_id.strip(),
        "bar_interval": inp.bar_interval.strip(),
        "exclusion_policy_version": inp.exclusion_policy_version.strip(),
        "hypothesis_id": inp.hypothesis_id.strip(),
        "inclusion_policy_version": inp.inclusion_policy_version.strip(),
        "minimum_history_bars": inp.minimum_history_bars,
        "minimum_required_member_count": inp.minimum_required_member_count,
        "period_binding_ref": inp.period_binding_ref.strip(),
        "universe_id": inp.universe_id.strip(),
        "universe_policy_id": inp.universe_policy_id.strip(),
        "universe_policy_version": inp.universe_policy_version.strip(),
        "venue_id": inp.venue_id.strip().lower(),
        "venue_scope": sorted({item.strip().lower() for item in inp.venue_scope if item.strip()}),
    }


def _compute_implementation_digest_payload() -> dict[str, str]:
    return {
        "generator_version": GENERATOR_VERSION,
        "module": GENERATOR_MODULE_NAME,
    }


def _compute_source_data_digest_payload(
    inp: PitFuturesUniverseManifestGeneratorInputV1,
) -> dict[str, Any]:
    return {
        "source_digests": list(inp.source_digests),
        "source_snapshot_refs": list(inp.source_snapshot_refs),
    }


def _compute_epoch_input_digest(
    *,
    score_epoch: int,
    source_snapshot_refs: tuple[str, ...],
    record_digests: tuple[str, ...],
) -> str:
    return compute_sha256_digest(
        {
            "record_digests": list(record_digests),
            "score_epoch": score_epoch,
            "source_snapshot_refs": list(source_snapshot_refs),
        }
    )


def _record_semantic_key(record: RawInstrumentRecordV1) -> tuple[Any, ...]:
    return (
        record.source_ref.strip(),
        record.venue_id.strip().lower(),
        record.market_type.strip().lower(),
        record.contract_type.strip().lower(),
        record.base_asset.strip().upper(),
        record.quote_asset.strip().upper(),
        record.settlement_asset.strip().upper(),
        record.venue_symbol.strip(),
        record.native_instrument_id,
        record.contract_expiry,
        record.listing_time,
        record.delisting_time,
        record.eligible_from,
        record.eligible_until,
        record.expiry_time,
        record.history_bars_available,
        record.required_history_bars,
        record.data_availability_status.strip().upper(),
    )


def _classify_market_input_errors(record: RawInstrumentRecordV1, errors: list[str]) -> bool:
    market_type = record.market_type.strip().lower()
    if market_type == "spot":
        _add(errors, GeneratorErrorCode.SPOT_INSTRUMENT_BLOCKED)
        return True
    if market_type in {"synthetic_spot", "synthetic-spot"}:
        _add(errors, GeneratorErrorCode.SYNTHETIC_SPOT_BLOCKED)
        return True
    if market_type not in {"futures", "futures_panel", "future", "perpetual"}:
        _add(errors, GeneratorErrorCode.NON_FUTURES_INSTRUMENT)
        return True
    contract_type = record.contract_type.strip().lower()
    if contract_type not in {item.value for item in ContractType}:
        _add(errors, GeneratorErrorCode.NON_FUTURES_INSTRUMENT)
        return True
    return False


def _validate_record_contract(
    record: RawInstrumentRecordV1,
    *,
    venue_scope: frozenset[str],
    minimum_history_bars: int,
    errors: list[str],
) -> None:
    venue_id = record.venue_id.strip().lower()
    if not venue_id or not _VENUE_ID_PATTERN.fullmatch(venue_id):
        _add(errors, GeneratorErrorCode.UNKNOWN_VENUE)
    elif venue_id not in venue_scope:
        _add(errors, GeneratorErrorCode.UNKNOWN_VENUE)

    if not _validate_source_ref(record.source_ref, errors):
        return
    if not is_valid_digest(record.record_digest.strip().lower()):
        _add(errors, GeneratorErrorCode.SOURCE_DIGEST_MISMATCH)

    if _classify_market_input_errors(record, errors):
        return

    if record.listing_time is None:
        _add(errors, GeneratorErrorCode.MISSING_LISTING_TIME)
    elif not is_valid_rfc3339_utc(record.listing_time):
        _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)

    if record.eligible_from is None:
        _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)
    elif not is_valid_rfc3339_utc(record.eligible_from):
        _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)

    if record.delisting_time is not None and not is_valid_rfc3339_utc(record.delisting_time):
        _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)
    if record.eligible_until is not None and not is_valid_rfc3339_utc(record.eligible_until):
        _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)
    if record.expiry_time is not None and not is_valid_rfc3339_utc(record.expiry_time):
        _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)

    contract_type = record.contract_type.strip().lower()
    if contract_type in _DATED_TYPES:
        if record.expiry_time is None and (
            record.contract_expiry is None or not record.contract_expiry.strip()
        ):
            _add(errors, GeneratorErrorCode.MISSING_EXPIRY_OR_PERPETUAL_CLASSIFICATION)

    if record.required_history_bars != minimum_history_bars:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    if record.history_bars_available < 0:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    try:
        DataAvailabilityStatus(record.data_availability_status.strip().upper())
    except ValueError:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    if record.listing_time and record.delisting_time:
        lt = _parse_utc_instant(record.listing_time)
        dt = _parse_utc_instant(record.delisting_time)
        if lt is not None and dt is not None and lt >= dt:
            _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)

    if record.eligible_from and record.eligible_until:
        ef = _parse_utc_instant(record.eligible_from)
        eu = _parse_utc_instant(record.eligible_until)
        if ef is not None and eu is not None and ef >= eu:
            _add(errors, GeneratorErrorCode.INVALID_LIFECYCLE_INTERVAL)


def _canonicalize_record(
    record: RawInstrumentRecordV1,
    errors: list[str],
) -> str | None:
    if _classify_market_input_errors(record, errors):
        return None
    result = canonicalize_instrument_id_v1(
        InstrumentIdCanonicalizationInputV1(
            venue_id=record.venue_id.strip().lower(),
            market_type=record.market_type.strip().lower(),
            contract_type=record.contract_type.strip().lower(),
            base_asset=record.base_asset.strip(),
            quote_asset=record.quote_asset.strip(),
            settlement_asset=record.settlement_asset.strip(),
            venue_symbol=record.venue_symbol.strip(),
            native_instrument_id=record.native_instrument_id,
            contract_expiry=record.contract_expiry,
        )
    )
    if not result.success or result.instrument_id is None:
        for code in result.error_codes:
            if code == "BITCOIN_DIRECTION_DISALLOWED":
                _add(errors, GeneratorErrorCode.BITCOIN_INSTRUMENT_BLOCKED)
            elif code == "SPOT_MARKET":
                _add(errors, GeneratorErrorCode.SPOT_INSTRUMENT_BLOCKED)
            elif code == "SYNTHETIC_SPOT_MARKET":
                _add(errors, GeneratorErrorCode.SYNTHETIC_SPOT_BLOCKED)
            elif code == "NON_FUTURES_MARKET":
                _add(errors, GeneratorErrorCode.NON_FUTURES_INSTRUMENT)
            else:
                _add(errors, GeneratorErrorCode.INVALID_CANONICAL_INSTRUMENT_ID)
        return None
    return result.instrument_id


def _determine_exclusion_reason_codes(
    record: RawInstrumentRecordV1,
    *,
    finalized_bar_close: str,
    minimum_history_bars: int,
) -> tuple[str, ...]:
    reasons: list[str] = []
    close = _parse_utc_instant(finalized_bar_close)
    if close is None:
        return ("UNFINALIZED_EPOCH",)

    listing = record.listing_time
    if listing is None:
        return ("INVALID_INSTRUMENT_ID",)
    listing_instant = _parse_utc_instant(listing)
    if listing_instant is None or listing_instant > close:
        reasons.append("NOT_LISTED_AT_SCORE_EPOCH")

    if record.delisting_time is not None:
        delist = _parse_utc_instant(record.delisting_time)
        if delist is not None and delist <= close:
            reasons.append("DELISTED_AT_SCORE_EPOCH")

    eligible_from = record.eligible_from
    if eligible_from is None:
        reasons.append("INVALID_INSTRUMENT_ID")
    else:
        ef = _parse_utc_instant(eligible_from)
        if ef is None or ef > close:
            reasons.append("NOT_LISTED_AT_SCORE_EPOCH")

    if record.eligible_until is not None:
        eu = _parse_utc_instant(record.eligible_until)
        if eu is not None and eu <= close:
            reasons.append("DELISTED_AT_SCORE_EPOCH")

    contract_type = record.contract_type.strip().lower()
    if contract_type in _DATED_TYPES and record.expiry_time is not None:
        expiry = _parse_utc_instant(record.expiry_time)
        if expiry is not None and expiry <= close:
            reasons.append("DELISTED_AT_SCORE_EPOCH")

    if record.history_bars_available < minimum_history_bars:
        reasons.append("INSUFFICIENT_HISTORY")

    status = record.data_availability_status.strip().upper()
    if status == DataAvailabilityStatus.UNAVAILABLE.value:
        reasons.append("DATA_UNAVAILABLE_AT_SCORE_EPOCH")
    elif status == DataAvailabilityStatus.HALTED.value:
        reasons.append("TRADING_HALT_AT_SCORE_EPOCH")
    elif status == DataAvailabilityStatus.STALE.value:
        reasons.append("STALE_DATA_AT_SCORE_EPOCH")

    return tuple(sorted(set(reasons)))


def _is_eligible_at_epoch(record: RawInstrumentRecordV1, *, finalized_bar_close: str) -> bool:
    return not _determine_exclusion_reason_codes(
        record,
        finalized_bar_close=finalized_bar_close,
        minimum_history_bars=record.required_history_bars,
    )


def _build_member(
    record: RawInstrumentRecordV1,
    *,
    instrument_id: str,
) -> PointInTimeFuturesUniverseMemberV1:
    return PointInTimeFuturesUniverseMemberV1(
        instrument_id=instrument_id,
        venue_id=record.venue_id.strip().lower(),
        venue_symbol=record.venue_symbol.strip(),
        contract_type=record.contract_type.strip().lower(),
        base_asset=record.base_asset.strip().upper(),
        quote_asset=record.quote_asset.strip().upper(),
        settlement_asset=record.settlement_asset.strip().upper(),
        listing_time=record.listing_time,
        delisting_time=record.delisting_time,
        eligible_from=str(record.eligible_from),
        eligible_until=record.eligible_until,
        history_bars_available=record.history_bars_available,
        required_history_bars=record.required_history_bars,
        data_availability_status=record.data_availability_status.strip().upper(),
        eligibility_status=EligibilityStatus.ELIGIBLE.value,
        reason_codes=(),
        source_ref=record.source_ref.strip(),
        member_digest="0" * 64,
    )


def _validate_input_contract(inp: PitFuturesUniverseManifestGeneratorInputV1) -> list[str]:
    errors: list[str] = []

    if inp.input_contract_version != INPUT_CONTRACT_VERSION:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
    if inp.generator_version != GENERATOR_VERSION:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    artifact_id = inp.artifact_id.strip()
    if not artifact_id or not _ARTIFACT_ID_PATTERN.fullmatch(artifact_id):
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    venue_id = inp.venue_id.strip().lower()
    if not venue_id or not _VENUE_ID_PATTERN.fullmatch(venue_id):
        _add(errors, GeneratorErrorCode.UNKNOWN_VENUE)

    for field_name, value in (
        ("universe_id", inp.universe_id),
        ("hypothesis_id", inp.hypothesis_id),
        ("universe_policy_id", inp.universe_policy_id),
        ("universe_policy_version", inp.universe_policy_version),
        ("inclusion_policy_version", inp.inclusion_policy_version),
        ("exclusion_policy_version", inp.exclusion_policy_version),
        ("bar_interval", inp.bar_interval),
    ):
        if not isinstance(value, str) or not value.strip():
            _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    if not is_valid_rfc3339_utc(inp.generated_at):
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
    if inp.minimum_history_bars <= 0:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
    if inp.minimum_required_member_count < 5:
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    normalized_scope = tuple(
        sorted({item.strip().lower() for item in inp.venue_scope if item.strip()})
    )
    if not normalized_scope:
        _add(errors, GeneratorErrorCode.UNKNOWN_VENUE)
    for item in normalized_scope:
        if not _VENUE_ID_PATTERN.fullmatch(item):
            _add(errors, GeneratorErrorCode.UNKNOWN_VENUE)

    normalized_refs = tuple(
        sorted({item.strip() for item in inp.source_snapshot_refs if item.strip()})
    )
    normalized_digests = tuple(d.strip().lower() for d in inp.source_digests)
    if len(normalized_refs) != len(normalized_digests):
        _add(errors, GeneratorErrorCode.SOURCE_DIGEST_MISMATCH)
    for digest in normalized_digests:
        if not is_valid_digest(digest):
            _add(errors, GeneratorErrorCode.SOURCE_DIGEST_MISMATCH)
    for ref in normalized_refs:
        _validate_source_ref(ref, errors)

    if not _validate_source_ref(inp.period_binding_ref, errors):
        pass

    if not is_valid_digest(inp.config_digest.strip().lower()):
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
    if not is_valid_digest(inp.implementation_digest.strip().lower()):
        _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)

    if not errors:
        expected_config = compute_sha256_digest(_compute_config_digest_payload(inp))
        if expected_config != inp.config_digest.strip().lower():
            _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
        expected_impl = compute_sha256_digest(_compute_implementation_digest_payload())
        if expected_impl != inp.implementation_digest.strip().lower():
            _add(errors, GeneratorErrorCode.INVALID_INPUT_CONTRACT)
        if len(normalized_refs) != len(inp.source_snapshot_refs) or len(normalized_digests) != len(
            inp.source_digests
        ):
            _add(errors, GeneratorErrorCode.SOURCE_DIGEST_MISMATCH)

    if not inp.epochs:
        _add(errors, GeneratorErrorCode.EMPTY_EPOCH)
        return sorted(errors)

    sorted_epochs = sorted(inp.epochs, key=lambda item: item.score_epoch)

    previous_score: int | None = None
    previous_close: tuple[int, int] | None = None
    venue_scope_set = frozenset(normalized_scope) if normalized_scope else frozenset()

    for epoch in sorted_epochs:
        if previous_score is not None and epoch.score_epoch != previous_score + 1:
            _add(errors, GeneratorErrorCode.INVALID_EPOCH_ORDER)
        if previous_score is not None and epoch.score_epoch <= previous_score:
            _add(errors, GeneratorErrorCode.INVALID_EPOCH_ORDER)
        previous_score = epoch.score_epoch

        close = _parse_utc_instant(epoch.finalized_bar_close)
        if close is None:
            _add(errors, GeneratorErrorCode.INVALID_EPOCH_ORDER)
        elif previous_close is not None and close <= previous_close:
            _add(errors, GeneratorErrorCode.INVALID_EPOCH_ORDER)
        previous_close = close

        if not epoch.raw_instrument_records:
            _add(errors, GeneratorErrorCode.EMPTY_EPOCH)
            continue

        canonical_groups: dict[str, list[RawInstrumentRecordV1]] = {}
        for record in epoch.raw_instrument_records:
            _validate_record_contract(
                record,
                venue_scope=venue_scope_set,
                minimum_history_bars=inp.minimum_history_bars,
                errors=errors,
            )
            instrument_id = _canonicalize_record(record, errors)
            if instrument_id is None:
                continue
            canonical_groups.setdefault(instrument_id, []).append(record)

        for records in canonical_groups.values():
            if len(records) <= 1:
                continue
            semantic_keys = {_record_semantic_key(item) for item in records}
            digests = {item.record_digest.strip().lower() for item in records}
            if len(semantic_keys) > 1:
                _add(errors, GeneratorErrorCode.CONFLICTING_SOURCE_RECORDS)
            elif len(digests) > 1:
                _add(errors, GeneratorErrorCode.CONFLICTING_SOURCE_RECORDS)

    return sorted(errors)


def _resolve_epoch_records(
    records: Sequence[RawInstrumentRecordV1],
    errors: list[str],
) -> dict[str, RawInstrumentRecordV1]:
    resolved: dict[str, RawInstrumentRecordV1] = {}
    canonical_groups: dict[str, list[RawInstrumentRecordV1]] = {}
    for record in records:
        instrument_id = _canonicalize_record(record, errors)
        if instrument_id is None:
            continue
        canonical_groups.setdefault(instrument_id, []).append(record)

    for instrument_id, grouped in canonical_groups.items():
        semantic_keys = {_record_semantic_key(item) for item in grouped}
        digests = {item.record_digest.strip().lower() for item in grouped}
        if len(grouped) > 1 and (len(semantic_keys) > 1 or len(digests) > 1):
            _add(errors, GeneratorErrorCode.CONFLICTING_SOURCE_RECORDS)
            continue
        resolved[instrument_id] = grouped[0]
    return resolved


def generate_pit_futures_universe_manifest_v1(
    generator_input: PitFuturesUniverseManifestGeneratorInputV1 | Mapping[str, Any],
) -> PitFuturesUniverseManifestGeneratorResultV1:
    """Deterministically generate a PIT futures universe manifest from explicit inputs."""
    if isinstance(generator_input, Mapping):
        raise TypeError(
            "Mapping input is not supported; pass PitFuturesUniverseManifestGeneratorInputV1"
        )

    errors = _validate_input_contract(generator_input)
    if errors:
        return PitFuturesUniverseManifestGeneratorResultV1(False, None, None, tuple(errors))

    inp = generator_input
    normalized_scope = tuple(sorted({item.strip().lower() for item in inp.venue_scope}))
    normalized_refs = tuple(sorted({item.strip() for item in inp.source_snapshot_refs}))
    sorted_epochs = tuple(sorted(inp.epochs, key=lambda item: item.score_epoch))

    built_epochs: list[PointInTimeFuturesUniverseEpochV1] = []
    for epoch in sorted_epochs:
        epoch_errors: list[str] = []
        resolved = _resolve_epoch_records(epoch.raw_instrument_records, epoch_errors)
        if epoch_errors:
            return PitFuturesUniverseManifestGeneratorResultV1(
                False, None, None, tuple(sorted(set(epoch_errors)))
            )

        members: list[PointInTimeFuturesUniverseMemberV1] = []
        exclusions: list[PointInTimeFuturesUniverseExclusionV1] = []

        for instrument_id in sorted(resolved):
            record = resolved[instrument_id]
            if _is_eligible_at_epoch(record, finalized_bar_close=epoch.finalized_bar_close):
                members.append(_build_member(record, instrument_id=instrument_id))
            else:
                reason_codes = _determine_exclusion_reason_codes(
                    record,
                    finalized_bar_close=epoch.finalized_bar_close,
                    minimum_history_bars=inp.minimum_history_bars,
                )
                exclusions.append(
                    PointInTimeFuturesUniverseExclusionV1(
                        instrument_id=instrument_id,
                        reason_codes=reason_codes,
                        source_ref=record.source_ref.strip(),
                        excluded_at_epoch=epoch.score_epoch,
                    )
                )

        eligible_count = len(members)
        membership_status = (
            MembershipStatus.FINALIZED.value
            if eligible_count >= inp.minimum_required_member_count
            else MembershipStatus.INSUFFICIENT_PANEL.value
        )

        record_digests = tuple(
            sorted(resolved[item].record_digest.strip().lower() for item in sorted(resolved))
        )
        built_epochs.append(
            PointInTimeFuturesUniverseEpochV1(
                score_epoch=epoch.score_epoch,
                finalized_bar_close=epoch.finalized_bar_close,
                eligible_member_count=eligible_count,
                minimum_required_member_count=inp.minimum_required_member_count,
                membership_status=membership_status,
                members=tuple(members),
                excluded_members=tuple(exclusions),
                epoch_input_digest=_compute_epoch_input_digest(
                    score_epoch=epoch.score_epoch,
                    source_snapshot_refs=normalized_refs,
                    record_digests=record_digests,
                ),
                epoch_membership_digest="0" * 64,
            )
        )

    policy = default_manifest_policy_constants()
    manifest = PointInTimeFuturesUniverseManifestV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        manifest_id=inp.artifact_id.strip(),
        hypothesis_id=inp.hypothesis_id.strip(),
        universe_policy_id=inp.universe_policy_id.strip(),
        universe_policy_version=inp.universe_policy_version.strip(),
        venue_scope=normalized_scope,
        market_type=MARKET_TYPE,
        generated_at=inp.generated_at,
        score_epoch_semantics=SCORE_EPOCH_SEMANTICS,
        bar_interval=inp.bar_interval.strip(),
        minimum_history_bars=inp.minimum_history_bars,
        futures_only=policy["futures_only"],
        bitcoin_direction_allowed=policy["bitcoin_direction_allowed"],
        spot_allowed=policy["spot_allowed"],
        synthetic_spot_allowed=policy["synthetic_spot_allowed"],
        non_authorizing=policy["non_authorizing"],
        research_binding_only=policy["research_binding_only"],
        instrument_id_canonicalization_version=INSTRUMENT_ID_CANONICALIZATION_VERSION,
        source_dataset_refs=normalized_refs,
        period_binding_ref=inp.period_binding_ref.strip(),
        implementation_digest=inp.implementation_digest.strip().lower(),
        config_digest=inp.config_digest.strip().lower(),
        source_data_digest=compute_sha256_digest(_compute_source_data_digest_payload(inp)),
        membership_digest="0" * 64,
        manifest_digest="0" * 64,
        epochs=tuple(built_epochs),
    )
    manifest = attach_computed_digests(manifest)

    validation = validate_pit_futures_universe_manifest_v1(manifest)
    if validation.verdict != ValidationVerdict.ACCEPTED:
        return PitFuturesUniverseManifestGeneratorResultV1(
            False,
            None,
            None,
            (GeneratorErrorCode.OUTPUT_VALIDATION_FAILED.value,),
            validation.reason_codes,
        )

    reference = format_pit_universe_manifest_reference_v1(
        artifact_id=inp.artifact_id.strip(),
        manifest_digest=manifest.manifest_digest,
    )
    return PitFuturesUniverseManifestGeneratorResultV1(
        True,
        manifest,
        reference,
        (),
    )


def compute_generator_config_digest(inp: PitFuturesUniverseManifestGeneratorInputV1) -> str:
    """Expose config digest helper for tests and offline input construction."""
    return compute_sha256_digest(_compute_config_digest_payload(inp))


def compute_generator_implementation_digest() -> str:
    """Expose implementation digest helper for tests and offline input construction."""
    return compute_sha256_digest(_compute_implementation_digest_payload())

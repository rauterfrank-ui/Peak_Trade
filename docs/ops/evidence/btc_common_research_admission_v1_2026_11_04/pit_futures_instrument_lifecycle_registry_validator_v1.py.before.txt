"""Fail-closed offline validator for pit_futures_instrument_lifecycle_registry snapshots v1.

Binary ACCEPTED/REJECTED only. No network, no file I/O, no runtime authority.
Reuses LifecycleRegistryErrorCode from registry owner — no parallel error enum.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from src.research.instrument_id_canonicalization_v1 import validate_instrument_id_format_v1
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    REGISTRY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOURCE_PRIORITY_POLICY_VERSION,
    CONFLICT_RESOLUTION_POLICY_VERSION,
    InstrumentLifecycleIntervalV1,
    LifecycleRegistryErrorCode,
    ObservationKind,
    QueryState,
    RegistrySnapshotV1,
    SourceTrustLevel,
    _PERPETUAL_TYPES,
    _DATED_TYPES,
    _FUTURES_MARKET_TYPES,
    _REGISTERED_SOURCES_V0,
    _cross_sequence_intervals_overlap_v1,
    attach_snapshot_digest,
    compute_interval_digest,
    compute_registry_snapshot_digest,
    intervals_overlap_v1,
    parse_utc_instant,
    query_lifecycle_state_at_instant_v1,
    validate_observation_transition_v1,
)
from src.research.pit_futures_universe_manifest_v1 import (
    ContractType,
    is_valid_digest,
    is_valid_rfc3339_utc,
)

PACKAGE_MARKER = "PIT_FUTURES_INSTRUMENT_LIFECYCLE_REGISTRY_VALIDATOR_V1=true"

_FORBIDDEN_BASE_ASSETS = frozenset({"BTC", "XBT", "WBTC", "TBTC", "RBTC", "BTCB"})
_FORBIDDEN_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "wbtc"})
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")
_CURRENT_STATE_FALLBACK_MARKERS = frozenset(
    {"current_state", "use_current_state", "fallback_to_current", "now()"}
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class LifecycleRegistryValidationIssueV1:
    error_code: str
    instrument_id: str | None
    record_ref: str | None
    field_path: str


@dataclass(frozen=True)
class LifecycleRegistryValidationResultV1:
    verdict: ValidationVerdict
    valid: bool
    issues: tuple[LifecycleRegistryValidationIssueV1, ...]
    error_codes: tuple[str, ...]


def _issue_sort_key(issue: LifecycleRegistryValidationIssueV1) -> tuple[str, str, str, str]:
    return (
        issue.error_code,
        issue.instrument_id or "",
        issue.field_path,
        issue.record_ref or "",
    )


def _add_issue(
    issues: list[LifecycleRegistryValidationIssueV1],
    code: LifecycleRegistryErrorCode,
    *,
    instrument_id: str | None = None,
    record_ref: str | None = None,
    field_path: str = "",
) -> None:
    candidate = LifecycleRegistryValidationIssueV1(
        error_code=code.value,
        instrument_id=instrument_id,
        record_ref=record_ref,
        field_path=field_path,
    )
    if candidate not in issues:
        issues.append(candidate)


def _is_sorted(values: Sequence[str]) -> bool:
    return list(values) == sorted(values)


def _validate_source_ref(
    value: str | None,
    issues: list[LifecycleRegistryValidationIssueV1],
    *,
    field_path: str,
    instrument_id: str | None = None,
    record_ref: str | None = None,
) -> None:
    if value is None or not value.strip():
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_SOURCE_REFERENCE,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=field_path,
        )
        return
    if _ABSOLUTE_PATH_PATTERN.search(value):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_SOURCE_REFERENCE,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=field_path,
        )


def _is_bitcoin_instrument(
    interval: InstrumentLifecycleIntervalV1,
) -> bool:
    if interval.base_asset.upper() in _FORBIDDEN_BASE_ASSETS:
        return True
    instrument_id = interval.instrument_id.lower()
    venue_symbol = (interval.venue_symbol or "").lower()
    for token in _FORBIDDEN_SUBSTRINGS:
        if re.search(rf"(?<![a-z0-9]){token}(?![a-z0-9])", instrument_id):
            return True
        if venue_symbol and re.search(rf"(?<![a-z0-9]){token}(?![a-z0-9])", venue_symbol):
            return True
    return False


def _validate_timestamp_field(
    value: str | None,
    issues: list[LifecycleRegistryValidationIssueV1],
    *,
    field_path: str,
    instrument_id: str | None = None,
    record_ref: str | None = None,
    required: bool = False,
) -> None:
    if value is None:
        if required:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=field_path,
            )
        return
    if not is_valid_rfc3339_utc(value):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_TIMESTAMP,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=field_path,
        )
        return
    if parse_utc_instant(value) is None:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.AMBIGUOUS_EFFECTIVE_TIME,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=field_path,
        )


def _validate_interval(
    interval: InstrumentLifecycleIntervalV1,
    issues: list[LifecycleRegistryValidationIssueV1],
    *,
    path_prefix: str,
) -> None:
    instrument_id = interval.instrument_id
    record_ref = interval.record_digest

    if not validate_instrument_id_format_v1(instrument_id):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_INSTRUMENT_TYPE,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.instrument_id",
        )

    if interval.venue_id != instrument_id.split(":", 1)[0]:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_VENUE_ID,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.venue_id",
        )

    contract_type = interval.contract_type.strip().lower()
    if contract_type not in {item.value for item in ContractType}:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_CONTRACT_TYPE,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.contract_type",
        )
    elif contract_type not in _PERPETUAL_TYPES | _DATED_TYPES:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.NON_FUTURES_INSTRUMENT,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.contract_type",
        )

    if _is_bitcoin_instrument(interval):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.BITCOIN_DIRECTION_PROHIBITED,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.base_asset",
        )

    if contract_type in _PERPETUAL_TYPES:
        if interval.expiry_time is not None or interval.contract_expiry is not None:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.INVALID_INSTRUMENT_TYPE,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=f"{path_prefix}.expiry_time",
            )
    elif contract_type in _DATED_TYPES:
        if interval.expiry_time is None or interval.contract_expiry is None:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.MISSING_EXPIRY_FOR_DATED_FUTURE,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=f"{path_prefix}.expiry_time",
            )

    _validate_timestamp_field(
        interval.listing_time,
        issues,
        field_path=f"{path_prefix}.listing_time",
        instrument_id=instrument_id,
        record_ref=record_ref,
        required=True,
    )
    _validate_timestamp_field(
        interval.eligible_from,
        issues,
        field_path=f"{path_prefix}.eligible_from",
        instrument_id=instrument_id,
        record_ref=record_ref,
        required=True,
    )
    _validate_timestamp_field(
        interval.delisting_time,
        issues,
        field_path=f"{path_prefix}.delisting_time",
        instrument_id=instrument_id,
        record_ref=record_ref,
    )
    _validate_timestamp_field(
        interval.eligible_until,
        issues,
        field_path=f"{path_prefix}.eligible_until",
        instrument_id=instrument_id,
        record_ref=record_ref,
    )
    _validate_timestamp_field(
        interval.expiry_time,
        issues,
        field_path=f"{path_prefix}.expiry_time",
        instrument_id=instrument_id,
        record_ref=record_ref,
    )

    listing = parse_utc_instant(interval.listing_time)
    eligible_from = parse_utc_instant(interval.eligible_from)
    if listing is not None and eligible_from is not None and eligible_from < listing:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.INVALID_TRANSITION,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.eligible_from",
        )

    if not is_valid_digest(interval.record_digest):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.DIGEST_MISMATCH,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.record_digest",
        )
    else:
        expected = compute_interval_digest(interval)
        if expected != interval.record_digest:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.DIGEST_MISMATCH,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=f"{path_prefix}.record_digest",
            )

    if interval.registry_record_version < 1:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.POLICY_MISMATCH,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.registry_record_version",
        )

    if not _is_sorted(list(interval.source_snapshot_refs)):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.OUT_OF_ORDER_EVENT,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.source_snapshot_refs",
        )
    for ref in interval.source_snapshot_refs:
        _validate_source_ref(
            ref,
            issues,
            field_path=f"{path_prefix}.source_snapshot_refs",
            instrument_id=instrument_id,
            record_ref=record_ref,
        )

    if not _is_sorted(list(interval.source_digests)):
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.OUT_OF_ORDER_EVENT,
            instrument_id=instrument_id,
            record_ref=record_ref,
            field_path=f"{path_prefix}.source_digests",
        )
    for digest in interval.source_digests:
        if not is_valid_digest(digest):
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.DIGEST_MISMATCH,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=f"{path_prefix}.source_digests",
            )

    if interval.correction_provenance_ref is not None:
        _validate_source_ref(
            interval.correction_provenance_ref,
            issues,
            field_path=f"{path_prefix}.correction_provenance_ref",
            instrument_id=instrument_id,
            record_ref=record_ref,
        )

    pending_start: str | None = None
    for index, sub in enumerate(interval.suspension_sub_intervals):
        sub_path = f"{path_prefix}.suspension_sub_intervals[{index}]"
        _validate_timestamp_field(
            sub.suspension_start,
            issues,
            field_path=f"{sub_path}.suspension_start",
            instrument_id=instrument_id,
            record_ref=record_ref,
            required=True,
        )
        _validate_timestamp_field(
            sub.suspension_end,
            issues,
            field_path=f"{sub_path}.suspension_end",
            instrument_id=instrument_id,
            record_ref=record_ref,
            required=True,
        )
        start = parse_utc_instant(sub.suspension_start)
        end = parse_utc_instant(sub.suspension_end)
        if start is not None and end is not None and start >= end:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.INVALID_TRANSITION,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=sub_path,
            )
        if pending_start is not None:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.INVALID_TRANSITION,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=sub_path,
            )
        pending_start = sub.suspension_end

    for marker in _CURRENT_STATE_FALLBACK_MARKERS:
        if marker in interval.instrument_id.lower():
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE,
                instrument_id=instrument_id,
                record_ref=record_ref,
                field_path=f"{path_prefix}.instrument_id",
            )


def validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(
    snapshot: RegistrySnapshotV1,
) -> LifecycleRegistryValidationResultV1:
    issues: list[LifecycleRegistryValidationIssueV1] = []

    if snapshot.schema_name != SCHEMA_NAME:
        _add_issue(
            issues, LifecycleRegistryErrorCode.INVALID_INPUT_CONTRACT, field_path="schema_name"
        )
    if snapshot.schema_version != SCHEMA_VERSION:
        _add_issue(
            issues, LifecycleRegistryErrorCode.INVALID_INPUT_CONTRACT, field_path="schema_version"
        )
    if snapshot.policy_version != REGISTRY_VERSION:
        _add_issue(issues, LifecycleRegistryErrorCode.POLICY_MISMATCH, field_path="policy_version")
    if snapshot.source_priority_policy_version != SOURCE_PRIORITY_POLICY_VERSION:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.POLICY_MISMATCH,
            field_path="source_priority_policy_version",
        )
    if snapshot.conflict_resolution_policy_version != CONFLICT_RESOLUTION_POLICY_VERSION:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.POLICY_MISMATCH,
            field_path="conflict_resolution_policy_version",
        )

    if snapshot.registry_snapshot_version < 1:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.POLICY_MISMATCH,
            field_path="registry_snapshot_version",
        )

    _validate_timestamp_field(
        snapshot.generated_at,
        issues,
        field_path="generated_at",
        required=True,
    )

    for digest_field in ("config_digest", "implementation_digest", "registry_snapshot_digest"):
        if not is_valid_digest(getattr(snapshot, digest_field)):
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.DIGEST_MISMATCH,
                field_path=digest_field,
            )

    if not snapshot.venue_scope or not _is_sorted(list(snapshot.venue_scope)):
        _add_issue(issues, LifecycleRegistryErrorCode.OUT_OF_ORDER_EVENT, field_path="venue_scope")

    expected_snapshot_digest = compute_registry_snapshot_digest(snapshot)
    if expected_snapshot_digest != snapshot.registry_snapshot_digest:
        _add_issue(
            issues,
            LifecycleRegistryErrorCode.DIGEST_MISMATCH,
            field_path="registry_snapshot_digest",
        )

    sorted_intervals = sorted(
        snapshot.intervals, key=lambda item: (item.instrument_id, item.interval_sequence)
    )
    if list(snapshot.intervals) != sorted_intervals:
        _add_issue(issues, LifecycleRegistryErrorCode.OUT_OF_ORDER_EVENT, field_path="intervals")

    active_by_instrument: dict[str, list[InstrumentLifecycleIntervalV1]] = {}
    seen_keys: set[tuple[str, int]] = set()

    for index, interval in enumerate(sorted_intervals):
        path_prefix = f"intervals[{index}]"
        key = (interval.instrument_id, interval.interval_sequence)
        if key in seen_keys:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.DUPLICATE_CANONICAL_INSTRUMENT_ID,
                instrument_id=interval.instrument_id,
                record_ref=interval.record_digest,
                field_path=f"{path_prefix}.interval_sequence",
            )
        seen_keys.add(key)

        if interval.venue_id not in snapshot.venue_scope:
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.INVALID_VENUE_ID,
                instrument_id=interval.instrument_id,
                record_ref=interval.record_digest,
                field_path=f"{path_prefix}.venue_id",
            )

        _validate_interval(interval, issues, path_prefix=path_prefix)

        if interval.superseded_by_version is None:
            active_by_instrument.setdefault(interval.instrument_id, []).append(interval)

    for instrument_id, intervals in active_by_instrument.items():
        if len(intervals) > 1:
            for left in intervals:
                for right in intervals:
                    if left is right:
                        continue
                    if _cross_sequence_intervals_overlap_v1(left, right):
                        _add_issue(
                            issues,
                            LifecycleRegistryErrorCode.OVERLAPPING_LIFECYCLE_INTERVALS,
                            instrument_id=instrument_id,
                            field_path="eligible_from",
                        )
        active = [item for item in intervals if item.superseded_by_version is None]
        if len(active) > 1:
            for left in active:
                for right in active:
                    if left is right:
                        continue
                    if intervals_overlap_v1(left, right) or _cross_sequence_intervals_overlap_v1(
                        left, right
                    ):
                        _add_issue(
                            issues,
                            LifecycleRegistryErrorCode.OVERLAPPING_LIFECYCLE_INTERVALS,
                            instrument_id=instrument_id,
                            field_path="eligible_from",
                        )

    for index, interval in enumerate(sorted_intervals):
        if interval.superseded_by_version is not None:
            if interval.superseded_by_version <= snapshot.registry_snapshot_version:
                continue
            _add_issue(
                issues,
                LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE,
                instrument_id=interval.instrument_id,
                record_ref=interval.record_digest,
                field_path=f"intervals[{index}].superseded_by_version",
            )

    sorted_issues = tuple(sorted(issues, key=_issue_sort_key))
    error_codes = tuple(sorted({issue.error_code for issue in sorted_issues}))

    if sorted_issues:
        return LifecycleRegistryValidationResultV1(
            ValidationVerdict.REJECTED,
            False,
            sorted_issues,
            error_codes,
        )

    return LifecycleRegistryValidationResultV1(
        ValidationVerdict.ACCEPTED,
        True,
        (),
        (),
    )


def validate_registry_snapshot_is_immutable_v1(
    snapshot: RegistrySnapshotV1,
) -> bool:
    """Verify attach_snapshot_digest is idempotent — canonical immutability check."""
    reattached = attach_snapshot_digest(snapshot)
    return reattached.registry_snapshot_digest == snapshot.registry_snapshot_digest


__all__ = [
    "LifecycleRegistryValidationIssueV1",
    "LifecycleRegistryValidationResultV1",
    "ValidationVerdict",
    "validate_pit_futures_instrument_lifecycle_registry_snapshot_v1",
    "validate_registry_snapshot_is_immutable_v1",
]

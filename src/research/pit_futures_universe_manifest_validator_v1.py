"""Fail-closed offline validator for point-in_time_futures_universe_manifest v1.

Binary ACCEPTED/REJECTED only. No network, no file I/O, no runtime authority.
Collects all validation errors deterministically (sorted unique codes).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
    validate_instrument_id_format_v1,
)
from src.research.pit_futures_universe_manifest_v1 import (
    EXCLUSION_REASON_CODES,
    MARKET_TYPE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SCORE_EPOCH_SEMANTICS,
    ContractType,
    DataAvailabilityStatus,
    EligibilityStatus,
    MembershipStatus,
    PointInTimeFuturesUniverseManifestV1,
    compute_epoch_membership_digest,
    compute_manifest_digest,
    compute_member_digest,
    compute_membership_digest,
    is_valid_digest,
    is_valid_rfc3339_utc,
    manifest_from_dict,
)

PACKAGE_MARKER = "PIT_FUTURES_UNIVERSE_MANIFEST_VALIDATOR_V1=true"

_FORBIDDEN_BASE_ASSETS = frozenset({"BTC", "XBT", "WBTC", "TBTC", "RBTC", "BTCB"})
_FORBIDDEN_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "wbtc"})
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ValidatorErrorCode(str, Enum):
    INVALID_SCHEMA_VERSION = "INVALID_SCHEMA_VERSION"
    INVALID_SCHEMA_NAME = "INVALID_SCHEMA_NAME"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DIGEST_FORMAT = "INVALID_DIGEST_FORMAT"
    MANIFEST_DIGEST_MISMATCH = "MANIFEST_DIGEST_MISMATCH"
    MEMBERSHIP_DIGEST_MISMATCH = "MEMBERSHIP_DIGEST_MISMATCH"
    EPOCH_MEMBERSHIP_DIGEST_MISMATCH = "EPOCH_MEMBERSHIP_DIGEST_MISMATCH"
    MEMBER_DIGEST_MISMATCH = "MEMBER_DIGEST_MISMATCH"
    SOURCE_DATA_DIGEST_MISMATCH = "SOURCE_DATA_DIGEST_MISMATCH"
    CONFIG_DIGEST_MISMATCH = "CONFIG_DIGEST_MISMATCH"
    IMPLEMENTATION_DIGEST_MISMATCH = "IMPLEMENTATION_DIGEST_MISMATCH"
    EMPTY_EPOCHS = "EMPTY_EPOCHS"
    DUPLICATE_SCORE_EPOCH = "DUPLICATE_SCORE_EPOCH"
    OUT_OF_ORDER_EPOCHS = "OUT_OF_ORDER_EPOCHS"
    MISSING_EPOCH_IN_SEQUENCE = "MISSING_EPOCH_IN_SEQUENCE"
    UNFINALIZED_EPOCH = "UNFINALIZED_EPOCH"
    INSUFFICIENT_PANEL = "INSUFFICIENT_PANEL"
    EMPTY_MEMBERSHIP = "EMPTY_MEMBERSHIP"
    UNSORTED_MEMBERSHIP = "UNSORTED_MEMBERSHIP"
    DUPLICATE_INSTRUMENT_ID = "DUPLICATE_INSTRUMENT_ID"
    BITCOIN_MEMBER_REJECTED = "BITCOIN_MEMBER_REJECTED"
    SPOT_MEMBER_REJECTED = "SPOT_MEMBER_REJECTED"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    INVALID_INSTRUMENT_ID = "INVALID_INSTRUMENT_ID"
    UNKNOWN_INSTRUMENT_CANONICALIZATION_VERSION = "UNKNOWN_INSTRUMENT_CANONICALIZATION_VERSION"
    POLICY_FLAG_VIOLATION = "POLICY_FLAG_VIOLATION"
    UNKNOWN_REASON_CODE = "UNKNOWN_REASON_CODE"
    ELIGIBLE_WITH_REASON_CODES = "ELIGIBLE_WITH_REASON_CODES"
    INELIGIBLE_WITHOUT_REASON_CODES = "INELIGIBLE_WITHOUT_REASON_CODES"
    LISTING_BOUNDARY_VIOLATION = "LISTING_BOUNDARY_VIOLATION"
    DELISTING_BOUNDARY_VIOLATION = "DELISTING_BOUNDARY_VIOLATION"
    MEMBER_DATA_UNAVAILABLE = "MEMBER_DATA_UNAVAILABLE"
    INVALID_SOURCE_REFERENCE = "INVALID_SOURCE_REFERENCE"
    ABSOLUTE_HOST_PATH_FORBIDDEN = "ABSOLUTE_HOST_PATH_FORBIDDEN"


@dataclass(frozen=True)
class PitFuturesUniverseManifestValidationResultV1:
    verdict: ValidationVerdict
    valid: bool
    reason_codes: tuple[str, ...]


def _add(reasons: list[str], code: str) -> None:
    if code not in reasons:
        reasons.append(code)


def _require_field(data: Mapping[str, Any], key: str, reasons: list[str]) -> Any | None:
    if key not in data:
        _add(reasons, f"{ValidatorErrorCode.MISSING_REQUIRED_FIELD.value}:{key}")
        return None
    return data[key]


def _is_sorted(values: Sequence[str]) -> bool:
    return list(values) == sorted(values)


def _parse_utc_instant(value: str) -> tuple[int, int] | None:
    if not is_valid_rfc3339_utc(value):
        return None
    date_part, time_part = value.split("T", 1)
    year, month, day = (int(part) for part in date_part.split("-"))
    hour = int(time_part[0:2])
    minute = int(time_part[3:5])
    second = int(time_part[6:8])
    return (year * 10_000 + month * 100 + day, hour * 10_000 + minute * 100 + second)


def _is_bitcoin_member(member: Mapping[str, Any]) -> bool:
    base_asset = str(member.get("base_asset", "")).upper()
    if base_asset in _FORBIDDEN_BASE_ASSETS:
        return True
    instrument_id = str(member.get("instrument_id", "")).lower()
    venue_symbol = str(member.get("venue_symbol", "")).lower()
    for token in _FORBIDDEN_SUBSTRINGS:
        if re.search(rf"(?<![a-z0-9]){token}(?![a-z0-9])", instrument_id):
            return True
        if re.search(rf"(?<![a-z0-9]){token}(?![a-z0-9])", venue_symbol):
            return True
    return False


def _is_spot_like_member(member: Mapping[str, Any]) -> bool:
    contract_type = str(member.get("contract_type", "")).lower()
    if contract_type in {"spot", "synthetic_spot", "synthetic-spot"}:
        return True
    if contract_type not in {item.value for item in ContractType}:
        return True
    return False


def _validate_source_ref(value: Any, reasons: list[str], *, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _add(reasons, f"{ValidatorErrorCode.INVALID_SOURCE_REFERENCE.value}:{path}")
        return
    if _ABSOLUTE_PATH_PATTERN.search(value):
        _add(reasons, ValidatorErrorCode.ABSOLUTE_HOST_PATH_FORBIDDEN.value)


def _validate_member_at_epoch(
    member: Mapping[str, Any],
    *,
    epoch: Mapping[str, Any],
    reasons: list[str],
    path: str,
) -> None:
    finalized_bar_close = str(epoch.get("finalized_bar_close", ""))
    instrument_id = str(member.get("instrument_id", ""))
    eligibility = str(member.get("eligibility_status", ""))

    if not validate_instrument_id_format_v1(instrument_id):
        _add(reasons, ValidatorErrorCode.INVALID_INSTRUMENT_ID.value)

    if eligibility == EligibilityStatus.ELIGIBLE.value:
        if member.get("reason_codes"):
            _add(reasons, ValidatorErrorCode.ELIGIBLE_WITH_REASON_CODES.value)
        if _is_bitcoin_member(member):
            _add(reasons, ValidatorErrorCode.BITCOIN_MEMBER_REJECTED.value)
        if _is_spot_like_member(member):
            _add(reasons, ValidatorErrorCode.SPOT_MEMBER_REJECTED.value)
        history_available = member.get("history_bars_available")
        required_history = member.get("required_history_bars")
        if isinstance(history_available, int) and isinstance(required_history, int):
            if history_available < required_history:
                _add(reasons, ValidatorErrorCode.INSUFFICIENT_HISTORY.value)
        listing_time = member.get("listing_time")
        if listing_time is None:
            _add(reasons, ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value)
        elif isinstance(listing_time, str):
            if _parse_utc_instant(listing_time) is None:
                _add(reasons, ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value)
            elif _parse_utc_instant(listing_time) > _parse_utc_instant(finalized_bar_close):
                _add(reasons, ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value)
        delisting_time = member.get("delisting_time")
        if isinstance(delisting_time, str):
            if _parse_utc_instant(delisting_time) is not None:
                if _parse_utc_instant(delisting_time) <= _parse_utc_instant(finalized_bar_close):
                    _add(reasons, ValidatorErrorCode.DELISTING_BOUNDARY_VIOLATION.value)
        eligible_from = member.get("eligible_from")
        if isinstance(eligible_from, str):
            if _parse_utc_instant(eligible_from) is None:
                _add(reasons, ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value)
            elif _parse_utc_instant(eligible_from) > _parse_utc_instant(finalized_bar_close):
                _add(reasons, ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value)
        eligible_until = member.get("eligible_until")
        if isinstance(eligible_until, str):
            if _parse_utc_instant(eligible_until) is not None:
                if _parse_utc_instant(eligible_until) <= _parse_utc_instant(finalized_bar_close):
                    _add(reasons, ValidatorErrorCode.LISTING_BOUNDARY_VIOLATION.value)
        data_status = str(member.get("data_availability_status", ""))
        if data_status in {
            DataAvailabilityStatus.UNAVAILABLE.value,
            DataAvailabilityStatus.HALTED.value,
        }:
            _add(reasons, ValidatorErrorCode.MEMBER_DATA_UNAVAILABLE.value)
    elif eligibility == EligibilityStatus.INELIGIBLE.value:
        reason_codes = member.get("reason_codes", [])
        if not reason_codes:
            _add(reasons, ValidatorErrorCode.INELIGIBLE_WITHOUT_REASON_CODES.value)
    else:
        _add(
            reasons, f"{ValidatorErrorCode.MISSING_REQUIRED_FIELD.value}:{path}.eligibility_status"
        )

    reason_codes = member.get("reason_codes", [])
    if isinstance(reason_codes, list):
        if not _is_sorted([str(code) for code in reason_codes]):
            _add(reasons, ValidatorErrorCode.UNSORTED_MEMBERSHIP.value)
        for code in reason_codes:
            if str(code) not in EXCLUSION_REASON_CODES:
                _add(reasons, ValidatorErrorCode.UNKNOWN_REASON_CODE.value)

    _validate_source_ref(member.get("source_ref"), reasons, path=f"{path}.source_ref")


def validate_pit_futures_universe_manifest_v1(
    payload: PointInTimeFuturesUniverseManifestV1 | Mapping[str, Any],
) -> PitFuturesUniverseManifestValidationResultV1:
    reasons: list[str] = []

    if isinstance(payload, PointInTimeFuturesUniverseManifestV1):
        manifest = payload
        data = None
    else:
        data = dict(payload)
        try:
            manifest = manifest_from_dict(data)
        except (KeyError, TypeError, ValueError):
            for key in (
                "schema_name",
                "schema_version",
                "manifest_id",
                "epochs",
                "membership_digest",
                "manifest_digest",
            ):
                _require_field(data, key, reasons)
            return PitFuturesUniverseManifestValidationResultV1(
                ValidationVerdict.REJECTED,
                False,
                tuple(sorted(reasons)),
            )

    if manifest.schema_name != SCHEMA_NAME:
        _add(reasons, ValidatorErrorCode.INVALID_SCHEMA_NAME.value)
    if manifest.schema_version != SCHEMA_VERSION:
        _add(reasons, ValidatorErrorCode.INVALID_SCHEMA_VERSION.value)

    if manifest.instrument_id_canonicalization_version != INSTRUMENT_ID_CANONICALIZATION_VERSION:
        _add(reasons, ValidatorErrorCode.UNKNOWN_INSTRUMENT_CANONICALIZATION_VERSION.value)

    policy_checks = {
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "non_authorizing": True,
        "research_binding_only": True,
        "score_epoch_semantics": SCORE_EPOCH_SEMANTICS,
        "market_type": MARKET_TYPE,
    }
    for key, expected in policy_checks.items():
        if getattr(manifest, key) != expected:
            _add(reasons, ValidatorErrorCode.POLICY_FLAG_VIOLATION.value)

    if manifest.minimum_history_bars <= 0:
        _add(reasons, ValidatorErrorCode.POLICY_FLAG_VIOLATION.value)

    for digest_field in (
        "implementation_digest",
        "config_digest",
        "source_data_digest",
        "membership_digest",
        "manifest_digest",
    ):
        if not is_valid_digest(getattr(manifest, digest_field)):
            _add(reasons, ValidatorErrorCode.INVALID_DIGEST_FORMAT.value)

    if not manifest.venue_scope or not _is_sorted(list(manifest.venue_scope)):
        _add(reasons, ValidatorErrorCode.UNSORTED_MEMBERSHIP.value)
    if not manifest.source_dataset_refs or not _is_sorted(list(manifest.source_dataset_refs)):
        _add(reasons, ValidatorErrorCode.UNSORTED_MEMBERSHIP.value)

    _validate_source_ref(manifest.period_binding_ref, reasons, path="period_binding_ref")
    for ref in manifest.source_dataset_refs:
        _validate_source_ref(ref, reasons, path="source_dataset_refs")

    if not manifest.epochs:
        _add(reasons, ValidatorErrorCode.EMPTY_EPOCHS.value)
        return PitFuturesUniverseManifestValidationResultV1(
            ValidationVerdict.REJECTED,
            False,
            tuple(sorted(reasons)),
        )

    seen_epochs: set[int] = set()
    previous_score_epoch: int | None = None
    previous_close: tuple[int, int] | None = None

    for epoch in manifest.epochs:
        epoch_path = f"epochs[{epoch.score_epoch}]"
        if epoch.score_epoch in seen_epochs:
            _add(reasons, ValidatorErrorCode.DUPLICATE_SCORE_EPOCH.value)
        seen_epochs.add(epoch.score_epoch)

        close_instant = _parse_utc_instant(epoch.finalized_bar_close)
        if close_instant is None:
            _add(reasons, ValidatorErrorCode.UNFINALIZED_EPOCH.value)
        elif previous_close is not None and close_instant <= previous_close:
            _add(reasons, ValidatorErrorCode.OUT_OF_ORDER_EPOCHS.value)
        previous_close = close_instant

        if previous_score_epoch is not None and epoch.score_epoch <= previous_score_epoch:
            _add(reasons, ValidatorErrorCode.OUT_OF_ORDER_EPOCHS.value)
        previous_score_epoch = epoch.score_epoch

        if epoch.membership_status == MembershipStatus.UNFINALIZED.value:
            _add(reasons, ValidatorErrorCode.UNFINALIZED_EPOCH.value)

        if epoch.minimum_required_member_count < 5:
            _add(reasons, ValidatorErrorCode.INSUFFICIENT_PANEL.value)

        eligible_count = sum(
            1
            for member in epoch.members
            if member.eligibility_status == EligibilityStatus.ELIGIBLE.value
        )
        if eligible_count != epoch.eligible_member_count:
            _add(reasons, ValidatorErrorCode.INSUFFICIENT_PANEL.value)

        if (
            epoch.membership_status == MembershipStatus.FINALIZED.value
            and eligible_count < epoch.minimum_required_member_count
        ):
            _add(reasons, ValidatorErrorCode.INSUFFICIENT_PANEL.value)

        if not epoch.members and not epoch.excluded_members:
            _add(reasons, ValidatorErrorCode.EMPTY_MEMBERSHIP.value)

        member_ids = [member.instrument_id for member in epoch.members]
        if member_ids != sorted(member_ids):
            _add(reasons, ValidatorErrorCode.UNSORTED_MEMBERSHIP.value)

        excluded_ids = [item.instrument_id for item in epoch.excluded_members]
        if excluded_ids != sorted(excluded_ids):
            _add(reasons, ValidatorErrorCode.UNSORTED_MEMBERSHIP.value)

        all_ids = member_ids + excluded_ids
        if len(all_ids) != len(set(all_ids)):
            _add(reasons, ValidatorErrorCode.DUPLICATE_INSTRUMENT_ID.value)

        for index, member in enumerate(epoch.members):
            member_dict = {
                "instrument_id": member.instrument_id,
                "venue_id": member.venue_id,
                "venue_symbol": member.venue_symbol,
                "contract_type": member.contract_type,
                "base_asset": member.base_asset,
                "quote_asset": member.quote_asset,
                "settlement_asset": member.settlement_asset,
                "listing_time": member.listing_time,
                "delisting_time": member.delisting_time,
                "eligible_from": member.eligible_from,
                "eligible_until": member.eligible_until,
                "history_bars_available": member.history_bars_available,
                "required_history_bars": member.required_history_bars,
                "data_availability_status": member.data_availability_status,
                "eligibility_status": member.eligibility_status,
                "reason_codes": list(member.reason_codes),
                "source_ref": member.source_ref,
                "member_digest": member.member_digest,
            }
            _validate_member_at_epoch(
                member_dict,
                epoch={"finalized_bar_close": epoch.finalized_bar_close},
                reasons=reasons,
                path=f"{epoch_path}.members[{index}]",
            )
            if not is_valid_digest(member.member_digest):
                _add(reasons, ValidatorErrorCode.INVALID_DIGEST_FORMAT.value)
            else:
                expected = compute_member_digest(member)
                if expected != member.member_digest:
                    _add(reasons, ValidatorErrorCode.MEMBER_DIGEST_MISMATCH.value)

        if not is_valid_digest(epoch.epoch_membership_digest):
            _add(reasons, ValidatorErrorCode.INVALID_DIGEST_FORMAT.value)
        else:
            expected_epoch_digest = compute_epoch_membership_digest(epoch)
            if expected_epoch_digest != epoch.epoch_membership_digest:
                _add(reasons, ValidatorErrorCode.EPOCH_MEMBERSHIP_DIGEST_MISMATCH.value)

    if seen_epochs:
        expected_sequence = set(range(min(seen_epochs), max(seen_epochs) + 1))
        if seen_epochs != expected_sequence:
            _add(reasons, ValidatorErrorCode.MISSING_EPOCH_IN_SEQUENCE.value)

    expected_membership_digest = compute_membership_digest(manifest)
    if expected_membership_digest != manifest.membership_digest:
        _add(reasons, ValidatorErrorCode.MEMBERSHIP_DIGEST_MISMATCH.value)

    expected_manifest_digest = compute_manifest_digest(manifest)
    if expected_manifest_digest != manifest.manifest_digest:
        _add(reasons, ValidatorErrorCode.MANIFEST_DIGEST_MISMATCH.value)

    if reasons:
        return PitFuturesUniverseManifestValidationResultV1(
            ValidationVerdict.REJECTED,
            False,
            tuple(sorted(reasons)),
        )

    return PitFuturesUniverseManifestValidationResultV1(
        ValidationVerdict.ACCEPTED,
        True,
        (),
    )

"""Point-in-time futures universe manifest v1 schema, serialization, and digests.

Research-only, non-authorizing contracts. No generator, no runtime authority.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Mapping, Sequence

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)

PACKAGE_MARKER = "PIT_FUTURES_UNIVERSE_MANIFEST_V1=true"
SCHEMA_NAME = "point_in_time_futures_universe_manifest"
SCHEMA_VERSION = "v1"
SCORE_EPOCH_SEMANTICS = "finalized_bar_close"
MARKET_TYPE = "futures_panel"
REFERENCE_PREFIX = "pit_universe_manifest_v1"

_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_ID_PATTERN = re.compile(r"^[a-z0-9_\-]{1,128}$")
_RFC3339_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


class ContractType(str, Enum):
    LINEAR_PERPETUAL = "linear_perpetual"
    INVERSE_PERPETUAL = "inverse_perpetual"
    LINEAR_DATED_FUTURE = "linear_dated_future"
    INVERSE_DATED_FUTURE = "inverse_dated_future"


class MembershipStatus(str, Enum):
    FINALIZED = "FINALIZED"
    UNFINALIZED = "UNFINALIZED"
    INSUFFICIENT_PANEL = "INSUFFICIENT_PANEL"
    DATA_GAP = "DATA_GAP"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class DataAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    HALTED = "HALTED"


EXCLUSION_REASON_CODES: frozenset[str] = frozenset(
    {
        "NON_FUTURES_MARKET",
        "SPOT_MARKET",
        "SYNTHETIC_SPOT_MARKET",
        "BITCOIN_DIRECTION_DISALLOWED",
        "INSUFFICIENT_HISTORY",
        "NOT_LISTED_AT_SCORE_EPOCH",
        "DELISTED_AT_SCORE_EPOCH",
        "DATA_UNAVAILABLE_AT_SCORE_EPOCH",
        "UNFINALIZED_EPOCH",
        "INVALID_INSTRUMENT_ID",
        "AMBIGUOUS_INSTRUMENT_ID",
        "UNTRUSTED_SOURCE",
        "DUPLICATE_CANONICAL_INSTRUMENT",
        "POLICY_EXCLUDED",
        "TRADING_HALT_AT_SCORE_EPOCH",
        "STALE_DATA_AT_SCORE_EPOCH",
    }
)


@dataclass(frozen=True)
class PointInTimeFuturesUniverseExclusionV1:
    instrument_id: str
    reason_codes: tuple[str, ...]
    source_ref: str
    excluded_at_epoch: int


@dataclass(frozen=True)
class PointInTimeFuturesUniverseMemberV1:
    instrument_id: str
    venue_id: str
    venue_symbol: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    listing_time: str | None
    delisting_time: str | None
    eligible_from: str
    eligible_until: str | None
    history_bars_available: int
    required_history_bars: int
    data_availability_status: str
    eligibility_status: str
    reason_codes: tuple[str, ...]
    source_ref: str
    member_digest: str


@dataclass(frozen=True)
class PointInTimeFuturesUniverseEpochV1:
    score_epoch: int
    finalized_bar_close: str
    eligible_member_count: int
    minimum_required_member_count: int
    membership_status: str
    members: tuple[PointInTimeFuturesUniverseMemberV1, ...]
    excluded_members: tuple[PointInTimeFuturesUniverseExclusionV1, ...]
    epoch_input_digest: str
    epoch_membership_digest: str


@dataclass(frozen=True)
class PointInTimeFuturesUniverseManifestV1:
    schema_name: str
    schema_version: str
    manifest_id: str
    hypothesis_id: str
    universe_policy_id: str
    universe_policy_version: str
    venue_scope: tuple[str, ...]
    market_type: str
    generated_at: str
    score_epoch_semantics: str
    bar_interval: str
    minimum_history_bars: int
    futures_only: bool
    bitcoin_direction_allowed: bool
    spot_allowed: bool
    synthetic_spot_allowed: bool
    non_authorizing: bool
    research_binding_only: bool
    instrument_id_canonicalization_version: str
    source_dataset_refs: tuple[str, ...]
    period_binding_ref: str
    implementation_digest: str
    config_digest: str
    source_data_digest: str
    membership_digest: str
    manifest_digest: str
    epochs: tuple[PointInTimeFuturesUniverseEpochV1, ...]


def is_valid_digest(value: str) -> bool:
    return isinstance(value, str) and _DIGEST_PATTERN.fullmatch(value) is not None


def is_valid_rfc3339_utc(value: str) -> bool:
    return isinstance(value, str) and _RFC3339_UTC_PATTERN.fullmatch(value) is not None


def _omit_nulls(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


def _member_to_dict(
    member: PointInTimeFuturesUniverseMemberV1, *, include_digest: bool
) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
    }
    if include_digest:
        payload["member_digest"] = member.member_digest
    return _omit_nulls(payload)


def _exclusion_to_dict(exclusion: PointInTimeFuturesUniverseExclusionV1) -> dict[str, Any]:
    return {
        "instrument_id": exclusion.instrument_id,
        "reason_codes": list(exclusion.reason_codes),
        "source_ref": exclusion.source_ref,
        "excluded_at_epoch": exclusion.excluded_at_epoch,
    }


def _epoch_to_dict(
    epoch: PointInTimeFuturesUniverseEpochV1, *, include_digests: bool
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "score_epoch": epoch.score_epoch,
        "finalized_bar_close": epoch.finalized_bar_close,
        "eligible_member_count": epoch.eligible_member_count,
        "minimum_required_member_count": epoch.minimum_required_member_count,
        "membership_status": epoch.membership_status,
        "members": [
            _member_to_dict(member, include_digest=include_digests) for member in epoch.members
        ],
        "excluded_members": [_exclusion_to_dict(item) for item in epoch.excluded_members],
    }
    if include_digests:
        payload["epoch_input_digest"] = epoch.epoch_input_digest
        payload["epoch_membership_digest"] = epoch.epoch_membership_digest
    return payload


def manifest_to_dict(
    manifest: PointInTimeFuturesUniverseManifestV1,
    *,
    include_manifest_digest: bool = True,
    include_computed_digests: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": manifest.schema_name,
        "schema_version": manifest.schema_version,
        "manifest_id": manifest.manifest_id,
        "hypothesis_id": manifest.hypothesis_id,
        "universe_policy_id": manifest.universe_policy_id,
        "universe_policy_version": manifest.universe_policy_version,
        "venue_scope": list(manifest.venue_scope),
        "market_type": manifest.market_type,
        "generated_at": manifest.generated_at,
        "score_epoch_semantics": manifest.score_epoch_semantics,
        "bar_interval": manifest.bar_interval,
        "minimum_history_bars": manifest.minimum_history_bars,
        "futures_only": manifest.futures_only,
        "bitcoin_direction_allowed": manifest.bitcoin_direction_allowed,
        "spot_allowed": manifest.spot_allowed,
        "synthetic_spot_allowed": manifest.synthetic_spot_allowed,
        "non_authorizing": manifest.non_authorizing,
        "research_binding_only": manifest.research_binding_only,
        "instrument_id_canonicalization_version": manifest.instrument_id_canonicalization_version,
        "source_dataset_refs": list(manifest.source_dataset_refs),
        "period_binding_ref": manifest.period_binding_ref,
        "implementation_digest": manifest.implementation_digest,
        "config_digest": manifest.config_digest,
        "source_data_digest": manifest.source_data_digest,
        "membership_digest": manifest.membership_digest,
        "epochs": [
            _epoch_to_dict(epoch, include_digests=include_computed_digests)
            for epoch in manifest.epochs
        ],
    }
    if include_manifest_digest:
        payload["manifest_digest"] = manifest.manifest_digest
    return payload


def compute_sha256_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(dumps_canonical(dict(payload)).encode("utf-8")).hexdigest()


def compute_member_digest(member: PointInTimeFuturesUniverseMemberV1) -> str:
    # member_digest excludes its own field.
    return compute_sha256_digest(_member_to_dict(member, include_digest=False))


def compute_epoch_membership_digest(epoch: PointInTimeFuturesUniverseEpochV1) -> str:
    # epoch_membership_digest excludes epoch_input_digest and epoch_membership_digest.
    payload = {
        "score_epoch": epoch.score_epoch,
        "finalized_bar_close": epoch.finalized_bar_close,
        "members": [_member_to_dict(member, include_digest=False) for member in epoch.members],
        "excluded_members": [_exclusion_to_dict(item) for item in epoch.excluded_members],
    }
    return compute_sha256_digest(payload)


def compute_membership_digest(manifest: PointInTimeFuturesUniverseManifestV1) -> str:
    # membership_digest excludes generated_at, implementation/config/source_data/membership/manifest digests,
    # and per-entity computed digests.
    payload = {
        "epochs": [
            {
                "score_epoch": epoch.score_epoch,
                "finalized_bar_close": epoch.finalized_bar_close,
                "eligible_member_count": epoch.eligible_member_count,
                "minimum_required_member_count": epoch.minimum_required_member_count,
                "membership_status": epoch.membership_status,
                "members": [
                    _member_to_dict(member, include_digest=False) for member in epoch.members
                ],
                "excluded_members": [_exclusion_to_dict(item) for item in epoch.excluded_members],
            }
            for epoch in manifest.epochs
        ]
    }
    return compute_sha256_digest(payload)


def compute_manifest_digest(manifest: PointInTimeFuturesUniverseManifestV1) -> str:
    # manifest_digest excludes manifest_digest itself; includes membership_digest value.
    payload = manifest_to_dict(
        manifest, include_manifest_digest=False, include_computed_digests=True
    )
    return compute_sha256_digest(payload)


def attach_computed_digests(
    manifest: PointInTimeFuturesUniverseManifestV1,
) -> PointInTimeFuturesUniverseManifestV1:
    epochs: list[PointInTimeFuturesUniverseEpochV1] = []
    for epoch in manifest.epochs:
        members = tuple(
            replace(member, member_digest=compute_member_digest(member)) for member in epoch.members
        )
        updated_epoch = replace(
            epoch,
            members=members,
            epoch_membership_digest="",
        )
        epoch_membership_digest = compute_epoch_membership_digest(updated_epoch)
        epochs.append(replace(updated_epoch, epoch_membership_digest=epoch_membership_digest))

    interim = replace(
        manifest,
        epochs=tuple(epochs),
        membership_digest="",
        manifest_digest="",
    )
    membership_digest = compute_membership_digest(interim)
    interim_with_membership = replace(interim, membership_digest=membership_digest)
    manifest_digest = compute_manifest_digest(interim_with_membership)
    return replace(interim_with_membership, manifest_digest=manifest_digest)


def _parse_member(data: Mapping[str, Any]) -> PointInTimeFuturesUniverseMemberV1:
    return PointInTimeFuturesUniverseMemberV1(
        instrument_id=str(data["instrument_id"]),
        venue_id=str(data["venue_id"]),
        venue_symbol=str(data["venue_symbol"]),
        contract_type=str(data["contract_type"]),
        base_asset=str(data["base_asset"]),
        quote_asset=str(data["quote_asset"]),
        settlement_asset=str(data["settlement_asset"]),
        listing_time=data.get("listing_time"),
        delisting_time=data.get("delisting_time"),
        eligible_from=str(data["eligible_from"]),
        eligible_until=data.get("eligible_until"),
        history_bars_available=int(data["history_bars_available"]),
        required_history_bars=int(data["required_history_bars"]),
        data_availability_status=str(data["data_availability_status"]),
        eligibility_status=str(data["eligibility_status"]),
        reason_codes=tuple(str(code) for code in data.get("reason_codes", ())),
        source_ref=str(data["source_ref"]),
        member_digest=str(data["member_digest"]),
    )


def _parse_exclusion(data: Mapping[str, Any]) -> PointInTimeFuturesUniverseExclusionV1:
    return PointInTimeFuturesUniverseExclusionV1(
        instrument_id=str(data["instrument_id"]),
        reason_codes=tuple(str(code) for code in data["reason_codes"]),
        source_ref=str(data["source_ref"]),
        excluded_at_epoch=int(data["excluded_at_epoch"]),
    )


def _parse_epoch(data: Mapping[str, Any]) -> PointInTimeFuturesUniverseEpochV1:
    return PointInTimeFuturesUniverseEpochV1(
        score_epoch=int(data["score_epoch"]),
        finalized_bar_close=str(data["finalized_bar_close"]),
        eligible_member_count=int(data["eligible_member_count"]),
        minimum_required_member_count=int(data["minimum_required_member_count"]),
        membership_status=str(data["membership_status"]),
        members=tuple(_parse_member(item) for item in data.get("members", ())),
        excluded_members=tuple(_parse_exclusion(item) for item in data.get("excluded_members", ())),
        epoch_input_digest=str(data["epoch_input_digest"]),
        epoch_membership_digest=str(data["epoch_membership_digest"]),
    )


def manifest_from_dict(data: Mapping[str, Any]) -> PointInTimeFuturesUniverseManifestV1:
    return PointInTimeFuturesUniverseManifestV1(
        schema_name=str(data["schema_name"]),
        schema_version=str(data["schema_version"]),
        manifest_id=str(data["manifest_id"]),
        hypothesis_id=str(data["hypothesis_id"]),
        universe_policy_id=str(data["universe_policy_id"]),
        universe_policy_version=str(data["universe_policy_version"]),
        venue_scope=tuple(str(item) for item in data["venue_scope"]),
        market_type=str(data["market_type"]),
        generated_at=str(data["generated_at"]),
        score_epoch_semantics=str(data["score_epoch_semantics"]),
        bar_interval=str(data["bar_interval"]),
        minimum_history_bars=int(data["minimum_history_bars"]),
        futures_only=bool(data["futures_only"]),
        bitcoin_direction_allowed=bool(data["bitcoin_direction_allowed"]),
        spot_allowed=bool(data["spot_allowed"]),
        synthetic_spot_allowed=bool(data["synthetic_spot_allowed"]),
        non_authorizing=bool(data["non_authorizing"]),
        research_binding_only=bool(data["research_binding_only"]),
        instrument_id_canonicalization_version=str(data["instrument_id_canonicalization_version"]),
        source_dataset_refs=tuple(str(item) for item in data["source_dataset_refs"]),
        period_binding_ref=str(data["period_binding_ref"]),
        implementation_digest=str(data["implementation_digest"]),
        config_digest=str(data["config_digest"]),
        source_data_digest=str(data["source_data_digest"]),
        membership_digest=str(data["membership_digest"]),
        manifest_digest=str(data["manifest_digest"]),
        epochs=tuple(_parse_epoch(item) for item in data["epochs"]),
    )


@dataclass(frozen=True)
class PitUniverseManifestReferenceV1:
    schema_prefix: str
    artifact_id: str
    digest_algorithm: str
    manifest_digest: str


@dataclass(frozen=True)
class PitUniverseManifestReferenceParseResultV1:
    success: bool
    reference: PitUniverseManifestReferenceV1 | None
    error_codes: tuple[str, ...]


class ManifestReferenceErrorCode(str, Enum):
    INVALID_REFERENCE_FORMAT = "INVALID_REFERENCE_FORMAT"
    EMPTY_ARTIFACT_ID = "EMPTY_ARTIFACT_ID"
    INVALID_DIGEST_ALGORITHM = "INVALID_DIGEST_ALGORITHM"
    INVALID_DIGEST_FORMAT = "INVALID_DIGEST_FORMAT"
    ABSOLUTE_HOST_PATH_FORBIDDEN = "ABSOLUTE_HOST_PATH_FORBIDDEN"
    TRAVERSAL_FORBIDDEN = "TRAVERSAL_FORBIDDEN"
    WHITESPACE_FORBIDDEN = "WHITESPACE_FORBIDDEN"


def format_pit_universe_manifest_reference_v1(
    *,
    artifact_id: str,
    manifest_digest: str,
) -> str:
    parsed = parse_pit_universe_manifest_reference_v1(
        f"{REFERENCE_PREFIX}:{artifact_id}:sha256:{manifest_digest}"
    )
    if not parsed.success or parsed.reference is None:
        raise ValueError(parsed.error_codes)
    return f"{REFERENCE_PREFIX}:{artifact_id.strip()}:sha256:{manifest_digest.strip().lower()}"


def parse_pit_universe_manifest_reference_v1(
    token: str,
) -> PitUniverseManifestReferenceParseResultV1:
    errors: list[str] = []
    if not isinstance(token, str) or not token:
        return PitUniverseManifestReferenceParseResultV1(
            False, None, (ManifestReferenceErrorCode.INVALID_REFERENCE_FORMAT.value,)
        )
    if token != token.strip() or any(ch.isspace() for ch in token):
        return PitUniverseManifestReferenceParseResultV1(
            False, None, (ManifestReferenceErrorCode.WHITESPACE_FORBIDDEN.value,)
        )
    if token.startswith("/") or token.startswith("\\") or "://" in token:
        return PitUniverseManifestReferenceParseResultV1(
            False, None, (ManifestReferenceErrorCode.ABSOLUTE_HOST_PATH_FORBIDDEN.value,)
        )
    if ".." in token.split(":"):
        return PitUniverseManifestReferenceParseResultV1(
            False, None, (ManifestReferenceErrorCode.TRAVERSAL_FORBIDDEN.value,)
        )

    parts = token.split(":")
    if len(parts) != 4:
        errors.append(ManifestReferenceErrorCode.INVALID_REFERENCE_FORMAT.value)
        return PitUniverseManifestReferenceParseResultV1(False, None, tuple(errors))

    schema_prefix, artifact_id, digest_algorithm, manifest_digest = parts
    if ".." in artifact_id or "/" in artifact_id or "\\" in artifact_id:
        return PitUniverseManifestReferenceParseResultV1(
            False, None, (ManifestReferenceErrorCode.TRAVERSAL_FORBIDDEN.value,)
        )
    if schema_prefix != REFERENCE_PREFIX:
        errors.append(ManifestReferenceErrorCode.INVALID_REFERENCE_FORMAT.value)
    if not artifact_id:
        errors.append(ManifestReferenceErrorCode.EMPTY_ARTIFACT_ID.value)
    elif not _ARTIFACT_ID_PATTERN.fullmatch(artifact_id):
        errors.append(ManifestReferenceErrorCode.INVALID_REFERENCE_FORMAT.value)
    if digest_algorithm != "sha256":
        errors.append(ManifestReferenceErrorCode.INVALID_DIGEST_ALGORITHM.value)
    if not is_valid_digest(manifest_digest):
        errors.append(ManifestReferenceErrorCode.INVALID_DIGEST_FORMAT.value)

    if errors:
        return PitUniverseManifestReferenceParseResultV1(False, None, tuple(sorted(set(errors))))

    return PitUniverseManifestReferenceParseResultV1(
        True,
        PitUniverseManifestReferenceV1(
            schema_prefix=schema_prefix,
            artifact_id=artifact_id,
            digest_algorithm=digest_algorithm,
            manifest_digest=manifest_digest,
        ),
        (),
    )


def default_manifest_policy_constants() -> dict[str, Any]:
    return {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "market_type": MARKET_TYPE,
        "score_epoch_semantics": SCORE_EPOCH_SEMANTICS,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "non_authorizing": True,
        "research_binding_only": True,
        "instrument_id_canonicalization_version": INSTRUMENT_ID_CANONICALIZATION_VERSION,
    }

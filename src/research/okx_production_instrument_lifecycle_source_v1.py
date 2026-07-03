"""OKX production instrument lifecycle source v1 — pure core for PIT registry assembly.

Research-only, non-authorizing. No network, no I/O, no runtime authority.
Converts OKX public instrument metadata snapshots into lifecycle source observations
for `okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.instrument_id_canonicalization_v1 import (
    InstrumentIdCanonicalizationInputV1,
    canonicalize_instrument_id_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1,
    ObservationKind,
    SourceObservationRecordV1,
    SourceTrustLevel,
    compute_observation_digest,
)
from src.research.pit_futures_universe_manifest_v1 import ContractType, compute_sha256_digest

PACKAGE_MARKER = "OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_SOURCE_V1=true"
SOURCE_ID = OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1
SOURCE_PRIORITY = 10
VENUE_ID = "okx"
VENUE_TIMEZONE = "UTC"
MARKET_TYPE = "futures"
CONTRACT_TYPE = ContractType.LINEAR_PERPETUAL.value
UNIVERSE_POLICY_ID = "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe"
UNIVERSE_POLICY_VERSION = "v1"
MIN_ELIGIBLE_INSTRUMENT_COUNT = 5

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})
_FORBIDDEN_BASE_ASSETS = frozenset({"BTC", "XBT", "WBTC", "TBTC", "RBTC", "BTCB"})
_INST_ID_PATTERN = re.compile(r"^[A-Z0-9]+-USDT-SWAP$")


class OkxLifecycleSourceErrorCode(str, Enum):
    INVALID_INSTRUMENT_RECORD = "INVALID_INSTRUMENT_RECORD"
    NON_LINEAR_USDT_SWAP = "NON_LINEAR_USDT_SWAP"
    BITCOIN_INSTRUMENT_BLOCKED = "BITCOIN_INSTRUMENT_BLOCKED"
    SPOT_OR_INVERSE_BLOCKED = "SPOT_OR_INVERSE_BLOCKED"
    MISSING_LIST_TIME = "MISSING_LIST_TIME"
    INVALID_LIST_TIME = "INVALID_LIST_TIME"
    NON_LIVE_STATE_BLOCKED = "NON_LIVE_STATE_BLOCKED"
    UNKNOWN_LIFECYCLE_FIELD = "UNKNOWN_LIFECYCLE_FIELD"
    CANONICALIZATION_FAILED = "CANONICALIZATION_FAILED"
    INSUFFICIENT_ELIGIBLE_INSTRUMENTS = "INSUFFICIENT_ELIGIBLE_INSTRUMENTS"


@dataclass(frozen=True)
class OkxInstrumentMetadataV1:
    inst_id: str
    inst_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    state: str
    list_time_utc: str
    exp_time: str
    ct_type: str
    raw_record_digest: str


@dataclass(frozen=True)
class OkxInstrumentEligibilityResultV1:
    eligible: bool
    instrument_id: str | None
    metadata: OkxInstrumentMetadataV1 | None
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class OkxLifecycleSourceSnapshotV1:
    source_id: str
    retrieval_timestamp_utc: str
    raw_snapshot_digest: str
    source_snapshot_ref: str
    eligible_instruments: tuple[OkxInstrumentMetadataV1, ...]
    excluded_count: int
    exclusion_reason_counts: dict[str, int]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ms_to_rfc3339_utc(value: str) -> str | None:
    raw = str(value or "").strip()
    if not raw or not raw.isdigit():
        return None
    ms = int(raw)
    if ms <= 0:
        return None
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_base_asset(inst: Mapping[str, Any], inst_id: str) -> str:
    base = str(inst.get("baseCcy") or "").strip().upper()
    if base:
        return base
    parts = inst_id.split("-")
    if len(parts) >= 1:
        return parts[0].upper()
    return ""


def is_forbidden_okx_instrument_token(*values: str | None) -> bool:
    combined = " ".join(v for v in values if v).lower()
    return any(token in combined for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def is_okx_linear_usdt_perpetual(inst: Mapping[str, Any]) -> bool:
    inst_id = str(inst.get("instId", "")).strip()
    inst_type = str(inst.get("instType", "")).strip().upper()
    settle = str(inst.get("settleCcy", "")).strip().upper()
    ct_type = str(inst.get("ctType", "linear")).strip().lower()
    exp = str(inst.get("expTime") or inst.get("expiry") or "").strip()
    if inst_type != "SWAP":
        return False
    if settle != "USDT":
        return False
    if ct_type and ct_type != "linear":
        return False
    if exp not in ("", "0", "None", "null"):
        return False
    if not _INST_ID_PATTERN.fullmatch(inst_id):
        return False
    return True


def evaluate_okx_instrument_eligibility_v1(
    inst: Mapping[str, Any],
    *,
    raw_record_digest: str | None = None,
) -> OkxInstrumentEligibilityResultV1:
    """Fail-closed eligibility for one OKX public instrument record."""
    errors: list[str] = []
    inst_id = str(inst.get("instId", "")).strip()
    if not inst_id:
        return OkxInstrumentEligibilityResultV1(
            False, None, None, (OkxLifecycleSourceErrorCode.INVALID_INSTRUMENT_RECORD.value,)
        )

    if not is_okx_linear_usdt_perpetual(inst):
        errors.append(OkxLifecycleSourceErrorCode.NON_LINEAR_USDT_SWAP.value)

    base_asset = _extract_base_asset(inst, inst_id)
    if base_asset in _FORBIDDEN_BASE_ASSETS or is_forbidden_okx_instrument_token(
        inst_id, base_asset, str(inst.get("uly", ""))
    ):
        errors.append(OkxLifecycleSourceErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value)

    state = str(inst.get("state", "")).strip().lower()
    if state != "live":
        errors.append(OkxLifecycleSourceErrorCode.NON_LIVE_STATE_BLOCKED.value)

    list_time_raw = str(inst.get("listTime", "")).strip()
    if not list_time_raw:
        errors.append(OkxLifecycleSourceErrorCode.MISSING_LIST_TIME.value)
    list_time_utc = _ms_to_rfc3339_utc(list_time_raw)
    if list_time_raw and list_time_utc is None:
        errors.append(OkxLifecycleSourceErrorCode.INVALID_LIST_TIME.value)

    if errors:
        return OkxInstrumentEligibilityResultV1(False, None, None, tuple(sorted(set(errors))))

    canon = canonicalize_instrument_id_v1(
        InstrumentIdCanonicalizationInputV1(
            venue_id=VENUE_ID,
            market_type=MARKET_TYPE,
            contract_type=CONTRACT_TYPE,
            base_asset=base_asset,
            quote_asset="USDT",
            settlement_asset="USDT",
            venue_symbol=inst_id,
        )
    )
    if not canon.success or canon.instrument_id is None:
        return OkxInstrumentEligibilityResultV1(
            False,
            None,
            None,
            (OkxLifecycleSourceErrorCode.CANONICALIZATION_FAILED.value,),
        )

    digest = raw_record_digest or _stable_digest(dict(inst))
    metadata = OkxInstrumentMetadataV1(
        inst_id=inst_id,
        inst_type=str(inst.get("instType", "")),
        base_asset=base_asset,
        quote_asset="USDT",
        settlement_asset="USDT",
        state=state,
        list_time_utc=list_time_utc or "",
        exp_time=str(inst.get("expTime") or ""),
        ct_type=str(inst.get("ctType") or "linear"),
        raw_record_digest=digest,
    )
    return OkxInstrumentEligibilityResultV1(True, canon.instrument_id, metadata, ())


def select_eligible_okx_instruments_v1(
    instruments: Sequence[Mapping[str, Any]],
    *,
    min_count: int = MIN_ELIGIBLE_INSTRUMENT_COUNT,
) -> tuple[tuple[OkxInstrumentMetadataV1, ...], dict[str, int]]:
    eligible: list[tuple[str, OkxInstrumentMetadataV1]] = []
    exclusion_counts: dict[str, int] = {}
    for inst in instruments:
        digest = _stable_digest(dict(inst))
        result = evaluate_okx_instrument_eligibility_v1(inst, raw_record_digest=digest)
        if result.eligible and result.metadata is not None and result.instrument_id is not None:
            eligible.append((result.instrument_id, result.metadata))
            continue
        for code in result.error_codes:
            exclusion_counts[code] = exclusion_counts.get(code, 0) + 1
    selected = tuple(meta for _, meta in sorted(eligible, key=lambda item: item[0]))
    if len(selected) < min_count:
        exclusion_counts[OkxLifecycleSourceErrorCode.INSUFFICIENT_ELIGIBLE_INSTRUMENTS.value] = (
            min_count - len(selected)
        )
    return selected, exclusion_counts


def compute_raw_instruments_snapshot_digest(instruments: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {
            "instId": str(item.get("instId", "")),
            "instType": str(item.get("instType", "")),
            "settleCcy": str(item.get("settleCcy", "")),
            "state": str(item.get("state", "")),
            "listTime": str(item.get("listTime", "")),
            "expTime": str(item.get("expTime", "")),
            "ctType": str(item.get("ctType", "")),
        }
        for item in sorted(instruments, key=lambda row: str(row.get("instId", "")))
    ]
    return compute_sha256_digest({"instruments": payload, "source_id": SOURCE_ID})


def build_okx_lifecycle_source_snapshot_v1(
    instruments: Sequence[Mapping[str, Any]],
    *,
    retrieval_timestamp_utc: str,
    source_snapshot_ref: str,
) -> OkxLifecycleSourceSnapshotV1:
    raw_digest = compute_raw_instruments_snapshot_digest(instruments)
    eligible, exclusion_counts = select_eligible_okx_instruments_v1(instruments)
    return OkxLifecycleSourceSnapshotV1(
        source_id=SOURCE_ID,
        retrieval_timestamp_utc=retrieval_timestamp_utc,
        raw_snapshot_digest=raw_digest,
        source_snapshot_ref=source_snapshot_ref,
        eligible_instruments=eligible,
        excluded_count=len(instruments) - len(eligible),
        exclusion_reason_counts=exclusion_counts,
    )


def _build_observation_record(
    metadata: OkxInstrumentMetadataV1,
    *,
    observation_kind: str,
    source_snapshot_ref: str,
    source_snapshot_digest: str,
    source_observed_at: str,
    source_effective_at: str,
    listing_time: str | None = None,
    eligible_from: str | None = None,
) -> SourceObservationRecordV1:
    interim = SourceObservationRecordV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        source_id=SOURCE_ID,
        source_trust_level=SourceTrustLevel.TRUSTED.value,
        source_priority=SOURCE_PRIORITY,
        source_snapshot_ref=source_snapshot_ref,
        source_snapshot_digest=source_snapshot_digest,
        source_observed_at=source_observed_at,
        source_effective_at=source_effective_at,
        venue_id=VENUE_ID,
        venue_timezone=VENUE_TIMEZONE,
        market_type=MARKET_TYPE,
        contract_type=CONTRACT_TYPE,
        base_asset=metadata.base_asset,
        quote_asset=metadata.quote_asset,
        settlement_asset=metadata.settlement_asset,
        observation_kind=observation_kind,
        observation_digest="0" * 64,
        venue_symbol=metadata.inst_id,
        native_instrument_id=None,
        listing_time=listing_time,
        eligible_from=eligible_from,
    )
    digest = compute_observation_digest(interim)
    return SourceObservationRecordV1(
        input_contract_version=interim.input_contract_version,
        source_id=interim.source_id,
        source_trust_level=interim.source_trust_level,
        source_priority=interim.source_priority,
        source_snapshot_ref=interim.source_snapshot_ref,
        source_snapshot_digest=interim.source_snapshot_digest,
        source_observed_at=interim.source_observed_at,
        source_effective_at=interim.source_effective_at,
        venue_id=interim.venue_id,
        venue_timezone=interim.venue_timezone,
        market_type=interim.market_type,
        contract_type=interim.contract_type,
        base_asset=interim.base_asset,
        quote_asset=interim.quote_asset,
        settlement_asset=interim.settlement_asset,
        observation_kind=interim.observation_kind,
        observation_digest=digest,
        venue_symbol=interim.venue_symbol,
        native_instrument_id=interim.native_instrument_id,
        listing_time=interim.listing_time,
        eligible_from=interim.eligible_from,
    )


def build_lifecycle_source_observations_v1(
    snapshot: OkxLifecycleSourceSnapshotV1,
) -> tuple[SourceObservationRecordV1, ...]:
    """Build LISTING observations with conservative eligible_from=listTime semantics."""
    records: list[SourceObservationRecordV1] = []
    for metadata in snapshot.eligible_instruments:
        listing = metadata.list_time_utc
        records.append(
            _build_observation_record(
                metadata,
                observation_kind=ObservationKind.LISTING.value,
                source_snapshot_ref=snapshot.source_snapshot_ref,
                source_snapshot_digest=snapshot.raw_snapshot_digest,
                source_observed_at=snapshot.retrieval_timestamp_utc,
                source_effective_at=listing,
                listing_time=listing,
                eligible_from=listing,
            )
        )
    return tuple(records)

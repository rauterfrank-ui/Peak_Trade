"""OKX Historical Funding Archive ↔ PIT lifecycle registry integration v0.

Narrow adapter connecting archive funding ingest with the canonical lifecycle
registry for Point-in-Time universe membership gating. Research-only; no I/O,
network, runtime, or authority effect. Archive settlement timestamps express
coverage only — listing/delisting authority remains with the lifecycle registry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.missing_funding_policy_v0 import (
    MISSING_FUNDING_FAIL_CLOSED,
    MISSING_FUNDING_VALUE,
)
from src.research.okx_historical_funding_archive_ingest_v0 import (
    NormalizedFundingEventV0,
    pit_join_funding_rate_v0,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    InstrumentLifecycleIntervalV1,
    QueryState,
    RegistrySnapshotV1,
    query_lifecycle_at_snapshot_v1,
)

PACKAGE_MARKER = "OKX_HISTORICAL_FUNDING_ARCHIVE_LIFECYCLE_INTEGRATION_V0=true"
INTEGRATION_VERSION = "okx_historical_funding_archive_lifecycle_integration.v0"
LIFECYCLE_REGISTRY_OWNER = "pit_futures_instrument_lifecycle_registry_v1"
ARCHIVE_INGEST_OWNER = "okx_historical_funding_archive_ingest_v0"

HISTORICAL_UNIVERSE_LIFECYCLE_PASS = True
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
CARRY_ZERO_FALLBACK_PRESENT = False

_ELIGIBLE_QUERY_STATES = frozenset({QueryState.ELIGIBLE.value})


class ArchiveLifecycleGateReason(str, Enum):
    LIFECYCLE_ELIGIBLE = "LIFECYCLE_ELIGIBLE"
    NOT_LISTED_AT_DECISION_INSTANT = "NOT_LISTED_AT_DECISION_INSTANT"
    DELISTED_AT_DECISION_INSTANT = "DELISTED_AT_DECISION_INSTANT"
    EXPIRED_AT_DECISION_INSTANT = "EXPIRED_AT_DECISION_INSTANT"
    SUSPENDED_AT_DECISION_INSTANT = "SUSPENDED_AT_DECISION_INSTANT"
    LISTED_INELIGIBLE_AT_DECISION_INSTANT = "LISTED_INELIGIBLE_AT_DECISION_INSTANT"
    UNKNOWN_LIFECYCLE_STATE = "UNKNOWN_LIFECYCLE_STATE"
    MISSING_LIFECYCLE_EVIDENCE = "MISSING_LIFECYCLE_EVIDENCE"
    MISSING_LIFECYCLE_BEGIN = "MISSING_LIFECYCLE_BEGIN"
    MISSING_LIFECYCLE_END_FOR_TERMINATED = "MISSING_LIFECYCLE_END_FOR_TERMINATED"
    MISSING_FUNDING_NO_PRIOR_SETTLEMENT = "MISSING_FUNDING_NO_PRIOR_SETTLEMENT"
    ARCHIVE_COVERAGE_NON_AUTHORITATIVE = "ARCHIVE_COVERAGE_NON_AUTHORITATIVE"
    VENUE_SYMBOL_MAPPING_MISMATCH = "VENUE_SYMBOL_MAPPING_MISMATCH"


@dataclass(frozen=True)
class ArchiveCoverageWindowV0:
    instrument_id: str
    venue_symbol: str
    first_settlement_time_ms: int
    last_settlement_time_ms: int
    settlement_count: int
    coverage_non_authoritative: bool = True


@dataclass(frozen=True)
class ArchiveLifecycleGateResultV0:
    allowed: bool
    instrument_id: str
    venue_symbol: str | None
    decision_bar_time_ms: int
    decision_instant_utc: str
    lifecycle_query_state: str
    funding_rate: str | None
    reason_code: str | None
    registry_snapshot_digest: str
    result_digest: str


@dataclass(frozen=True)
class ArchiveLifecycleIntegrationContractV0:
    historical_universe_lifecycle_pass: bool
    missing_funding_fail_closed: bool
    carry_zero_fallback_present: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    lifecycle_registry_owner: str
    archive_ingest_owner: str
    integration_version: str


def _utc_ms_to_rfc3339(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _gate_reason_for_query_state(query_state: str) -> ArchiveLifecycleGateReason:
    mapping = {
        QueryState.NOT_LISTED.value: ArchiveLifecycleGateReason.NOT_LISTED_AT_DECISION_INSTANT,
        QueryState.DELISTED.value: ArchiveLifecycleGateReason.DELISTED_AT_DECISION_INSTANT,
        QueryState.EXPIRED.value: ArchiveLifecycleGateReason.EXPIRED_AT_DECISION_INSTANT,
        QueryState.SUSPENDED.value: ArchiveLifecycleGateReason.SUSPENDED_AT_DECISION_INSTANT,
        QueryState.LISTED_INELIGIBLE.value: (
            ArchiveLifecycleGateReason.LISTED_INELIGIBLE_AT_DECISION_INSTANT
        ),
        QueryState.UNKNOWN.value: ArchiveLifecycleGateReason.UNKNOWN_LIFECYCLE_STATE,
    }
    return mapping.get(query_state, ArchiveLifecycleGateReason.UNKNOWN_LIFECYCLE_STATE)


def resolve_archive_venue_symbol_to_instrument_id_v0(
    snapshot: RegistrySnapshotV1,
    *,
    venue_symbol: str,
) -> tuple[str | None, str | None]:
    """Deterministic venue_symbol → canonical instrument_id mapping via registry intervals."""
    normalized = venue_symbol.strip()
    if not normalized:
        return None, ArchiveLifecycleGateReason.VENUE_SYMBOL_MAPPING_MISMATCH.value
    matches = sorted(
        {
            interval.instrument_id
            for interval in snapshot.intervals
            if interval.superseded_by_version is None and interval.venue_symbol == normalized
        }
    )
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, ArchiveLifecycleGateReason.VENUE_SYMBOL_MAPPING_MISMATCH.value
    return None, ArchiveLifecycleGateReason.VENUE_SYMBOL_MAPPING_MISMATCH.value


def derive_archive_coverage_window_v0(
    events: Sequence[NormalizedFundingEventV0],
    *,
    instrument_id: str,
) -> ArchiveCoverageWindowV0 | None:
    """Derive archive settlement coverage; explicitly non-authoritative for lifecycle bounds."""
    instrument_events = sorted(
        (event for event in events if event.instrument_id == instrument_id),
        key=lambda item: item.funding_time,
    )
    if not instrument_events:
        return None
    first = instrument_events[0]
    last = instrument_events[-1]
    return ArchiveCoverageWindowV0(
        instrument_id=instrument_id,
        venue_symbol=first.instrument_id,
        first_settlement_time_ms=first.funding_time,
        last_settlement_time_ms=last.funding_time,
        settlement_count=len(instrument_events),
        coverage_non_authoritative=True,
    )


def validate_terminated_interval_lifecycle_end_v0(
    interval: InstrumentLifecycleIntervalV1,
    *,
    query_state: str,
) -> str | None:
    """Fail-closed when a terminated contract lacks explicit lifecycle end evidence."""
    if query_state not in {
        QueryState.DELISTED.value,
        QueryState.EXPIRED.value,
    }:
        return None
    if interval.listing_time is None or interval.eligible_from is None:
        return ArchiveLifecycleGateReason.MISSING_LIFECYCLE_BEGIN.value
    if query_state == QueryState.EXPIRED.value and interval.expiry_time is None:
        return ArchiveLifecycleGateReason.MISSING_LIFECYCLE_END_FOR_TERMINATED.value
    if query_state == QueryState.DELISTED.value:
        if interval.delisting_time is None and interval.eligible_until is None:
            return ArchiveLifecycleGateReason.MISSING_LIFECYCLE_END_FOR_TERMINATED.value
    return None


def evaluate_lifecycle_membership_at_instant_v0(
    snapshot: RegistrySnapshotV1,
    *,
    instrument_id: str,
    decision_bar_time_ms: int,
) -> tuple[bool, str, str | None, InstrumentLifecycleIntervalV1 | None]:
    decision_instant = _utc_ms_to_rfc3339(decision_bar_time_ms)
    query = query_lifecycle_at_snapshot_v1(
        snapshot,
        instrument_id=instrument_id,
        query_instant=decision_instant,
    )
    if query.error_codes:
        if "UNKNOWN_LIFECYCLE_STATE" in query.error_codes:
            return (
                False,
                QueryState.UNKNOWN.value,
                (ArchiveLifecycleGateReason.MISSING_LIFECYCLE_EVIDENCE.value),
                None,
            )
        return (
            False,
            query.query_state,
            ArchiveLifecycleGateReason.MISSING_LIFECYCLE_EVIDENCE.value,
            query.interval,
        )
    if query.interval is not None:
        end_issue = validate_terminated_interval_lifecycle_end_v0(
            query.interval,
            query_state=query.query_state,
        )
        if end_issue is not None:
            return False, query.query_state, end_issue, query.interval
        if query.interval.listing_time is None or query.interval.eligible_from is None:
            return (
                False,
                query.query_state,
                ArchiveLifecycleGateReason.MISSING_LIFECYCLE_BEGIN.value,
                query.interval,
            )
    if query.query_state in _ELIGIBLE_QUERY_STATES:
        return (
            True,
            query.query_state,
            ArchiveLifecycleGateReason.LIFECYCLE_ELIGIBLE.value,
            (query.interval),
        )
    return (
        False,
        query.query_state,
        _gate_reason_for_query_state(query.query_state).value,
        (query.interval),
    )


def evaluate_archive_funding_lifecycle_gate_v0(
    snapshot: RegistrySnapshotV1,
    events: Sequence[NormalizedFundingEventV0],
    *,
    instrument_id: str,
    decision_bar_time_ms: int,
    venue_symbol: str | None = None,
) -> ArchiveLifecycleGateResultV0:
    """PIT gate: lifecycle registry membership first, then archive funding backward-asof join."""
    decision_instant = _utc_ms_to_rfc3339(decision_bar_time_ms)
    resolved_symbol = venue_symbol
    if resolved_symbol is None and events:
        matching = sorted({event.instrument_id for event in events if event.instrument_id})
        resolved_symbol = matching[0] if len(matching) == 1 else instrument_id

    allowed, query_state, reason, _interval = evaluate_lifecycle_membership_at_instant_v0(
        snapshot,
        instrument_id=instrument_id,
        decision_bar_time_ms=decision_bar_time_ms,
    )
    funding_rate: str | None = None
    final_reason = reason
    if allowed:
        instrument_events = tuple(
            event for event in events if event.instrument_id == (resolved_symbol or instrument_id)
        )
        funding_rate, funding_reason = pit_join_funding_rate_v0(
            instrument_events,
            decision_bar_time_ms,
        )
        if funding_rate is None:
            allowed = False
            final_reason = funding_reason or (
                ArchiveLifecycleGateReason.MISSING_FUNDING_NO_PRIOR_SETTLEMENT.value
            )
        else:
            final_reason = ArchiveLifecycleGateReason.LIFECYCLE_ELIGIBLE.value

    result_payload = {
        "allowed": allowed,
        "instrument_id": instrument_id,
        "decision_instant_utc": decision_instant,
        "lifecycle_query_state": query_state,
        "funding_rate": funding_rate,
        "reason_code": final_reason,
        "registry_snapshot_digest": snapshot.registry_snapshot_digest,
    }
    return ArchiveLifecycleGateResultV0(
        allowed=allowed,
        instrument_id=instrument_id,
        venue_symbol=resolved_symbol,
        decision_bar_time_ms=decision_bar_time_ms,
        decision_instant_utc=decision_instant,
        lifecycle_query_state=query_state,
        funding_rate=funding_rate,
        reason_code=final_reason,
        registry_snapshot_digest=snapshot.registry_snapshot_digest,
        result_digest=_stable_digest(result_payload),
    )


def evaluate_archive_funding_lifecycle_gate_by_venue_symbol_v0(
    snapshot: RegistrySnapshotV1,
    events: Sequence[NormalizedFundingEventV0],
    *,
    venue_symbol: str,
    decision_bar_time_ms: int,
) -> ArchiveLifecycleGateResultV0:
    instrument_id, mapping_reason = resolve_archive_venue_symbol_to_instrument_id_v0(
        snapshot,
        venue_symbol=venue_symbol,
    )
    if instrument_id is None:
        decision_instant = _utc_ms_to_rfc3339(decision_bar_time_ms)
        payload = {
            "allowed": False,
            "instrument_id": venue_symbol,
            "decision_instant_utc": decision_instant,
            "lifecycle_query_state": QueryState.UNKNOWN.value,
            "funding_rate": None,
            "reason_code": mapping_reason,
            "registry_snapshot_digest": snapshot.registry_snapshot_digest,
        }
        return ArchiveLifecycleGateResultV0(
            allowed=False,
            instrument_id=venue_symbol,
            venue_symbol=venue_symbol,
            decision_bar_time_ms=decision_bar_time_ms,
            decision_instant_utc=decision_instant,
            lifecycle_query_state=QueryState.UNKNOWN.value,
            funding_rate=None,
            reason_code=mapping_reason,
            registry_snapshot_digest=snapshot.registry_snapshot_digest,
            result_digest=_stable_digest(payload),
        )
    return evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        events,
        instrument_id=instrument_id,
        decision_bar_time_ms=decision_bar_time_ms,
        venue_symbol=venue_symbol,
    )


def integration_contract_v0() -> ArchiveLifecycleIntegrationContractV0:
    return ArchiveLifecycleIntegrationContractV0(
        historical_universe_lifecycle_pass=HISTORICAL_UNIVERSE_LIFECYCLE_PASS,
        missing_funding_fail_closed=MISSING_FUNDING_FAIL_CLOSED,
        carry_zero_fallback_present=CARRY_ZERO_FALLBACK_PRESENT,
        futures_only=FUTURES_ONLY,
        bitcoin_direction_allowed=BITCOIN_DIRECTION_ALLOWED,
        lifecycle_registry_owner=LIFECYCLE_REGISTRY_OWNER,
        archive_ingest_owner=ARCHIVE_INGEST_OWNER,
        integration_version=INTEGRATION_VERSION,
    )


def compute_integration_contract_digest_v0() -> str:
    contract = integration_contract_v0()
    return _stable_digest(
        {
            "historical_universe_lifecycle_pass": contract.historical_universe_lifecycle_pass,
            "missing_funding_fail_closed": contract.missing_funding_fail_closed,
            "carry_zero_fallback_present": contract.carry_zero_fallback_present,
            "futures_only": contract.futures_only,
            "bitcoin_direction_allowed": contract.bitcoin_direction_allowed,
            "lifecycle_registry_owner": contract.lifecycle_registry_owner,
            "archive_ingest_owner": contract.archive_ingest_owner,
            "integration_version": contract.integration_version,
        }
    )

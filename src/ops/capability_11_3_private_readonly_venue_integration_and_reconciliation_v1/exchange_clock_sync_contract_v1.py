"""Exchange clock synchronization contract (schema only; no venue access)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXCHANGE_CLOCK_SYNC_OWNER,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    NETWORK_SESSION_STARTED,
    OWNER,
)


class ExchangeClockSyncContractError(ValueError):
    """Fail-closed exchange clock sync contract violation."""


@dataclass(frozen=True)
class ExchangeClockSyncRecordV1:
    venue: str
    local_clock_utc: str
    exchange_clock_utc: str
    offset_ms: int
    sync_status: str
    classification: str = "EPHEMERAL_CONNECTION_STATE"
    owner: str = EXCHANGE_CLOCK_SYNC_OWNER
    contract_version: str = CONTRACT_VERSION


ALLOWED_SYNC_STATUSES: tuple[str, ...] = (
    "UNSYNCED",
    "SYNCED",
    "DRIFT_DETECTED",
    "SYNC_FAILED",
)


def build_exchange_clock_sync_record_v1(
    *,
    venue: str,
    local_clock_utc: str,
    exchange_clock_utc: str,
    offset_ms: int,
    sync_status: str,
) -> ExchangeClockSyncRecordV1:
    if not venue or not local_clock_utc or not exchange_clock_utc:
        raise ExchangeClockSyncContractError("EXCHANGE_CLOCK_SYNC_FIELDS_INCOMPLETE")
    if sync_status not in ALLOWED_SYNC_STATUSES:
        raise ExchangeClockSyncContractError(f"UNKNOWN_SYNC_STATUS:{sync_status}")
    return ExchangeClockSyncRecordV1(
        venue=venue,
        local_clock_utc=local_clock_utc,
        exchange_clock_utc=exchange_clock_utc,
        offset_ms=int(offset_ms),
        sync_status=sync_status,
    )


def refuse_live_exchange_clock_query_v1(record: ExchangeClockSyncRecordV1) -> dict[str, Any]:
    raise ExchangeClockSyncContractError(
        "EXCHANGE_CLOCK_QUERY_FORBIDDEN_IN_CAPABILITY_11_3:" + record.venue
    )


def prove_exchange_clock_sync_contract_v1() -> dict[str, Any]:
    record = build_exchange_clock_sync_record_v1(
        venue="OKX",
        local_clock_utc="1970-01-01T00:00:00Z",
        exchange_clock_utc="1970-01-01T00:00:00Z",
        offset_ms=0,
        sync_status="UNSYNCED",
    )
    query_blocked = False
    try:
        refuse_live_exchange_clock_query_v1(record)
    except ExchangeClockSyncContractError as exc:
        query_blocked = "CLOCK_QUERY_FORBIDDEN" in str(exc)

    unknown_blocked = False
    try:
        build_exchange_clock_sync_record_v1(
            venue="OKX",
            local_clock_utc="1970-01-01T00:00:00Z",
            exchange_clock_utc="1970-01-01T00:00:00Z",
            offset_ms=0,
            sync_status="TELEPATHIC",
        )
    except ExchangeClockSyncContractError as exc:
        unknown_blocked = "UNKNOWN_SYNC_STATUS" in str(exc)

    ok = all(
        [
            record.owner == OWNER,
            query_blocked,
            unknown_blocked,
            NETWORK_SESSION_STARTED is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
        ]
    )
    return {
        "ok": ok,
        "EXCHANGE_CLOCK_SYNC_SCHEMA_BOUND": True,
        "EXCHANGE_CLOCK_QUERY_PERFORMED": False,
        "query_blocked": query_blocked,
        "unknown_sync_status_blocked": unknown_blocked,
        "allowed_sync_statuses": list(ALLOWED_SYNC_STATUSES),
        "OWNER": EXCHANGE_CLOCK_SYNC_OWNER,
    }

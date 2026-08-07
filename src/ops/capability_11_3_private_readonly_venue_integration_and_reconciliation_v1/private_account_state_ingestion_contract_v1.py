"""Private account-state ingestion contract (fixture/schema only; no fetch)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    NETWORK_SESSION_STARTED,
    OWNER,
    PRIVATE_ACCOUNT_STATE_INGESTION_OWNER,
    PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3,
)


class PrivateAccountStateIngestionError(ValueError):
    """Fail-closed private account-state ingestion contract violation."""


ALLOWED_SNAPSHOT_KINDS: tuple[str, ...] = (
    "accounts",
    "open_positions",
    "open_orders",
    "balances_equity_margin",
)


@dataclass(frozen=True)
class PrivateAccountStateSnapshotV1:
    """Normalized private account-state snapshot schema.

    Cap 11.3 accepts fixture/normalized payloads only. Network fetch and
    credential-backed ingestion remain forbidden.
    """

    snapshot_kind: str
    venue: str
    account_identity: str
    observed_at_utc: str
    payload: dict[str, Any]
    source: str = "FIXTURE_ONLY"
    classification: str = "DURABLE_ECONOMIC_STATE"
    owner: str = PRIVATE_ACCOUNT_STATE_INGESTION_OWNER
    contract_version: str = CONTRACT_VERSION


def build_private_account_state_snapshot_v1(
    *,
    snapshot_kind: str,
    venue: str,
    account_identity: str,
    observed_at_utc: str,
    payload: dict[str, Any],
    source: str = "FIXTURE_ONLY",
) -> PrivateAccountStateSnapshotV1:
    if snapshot_kind not in ALLOWED_SNAPSHOT_KINDS:
        raise PrivateAccountStateIngestionError(f"UNKNOWN_SNAPSHOT_KIND:{snapshot_kind}")
    if not venue or not account_identity or not observed_at_utc:
        raise PrivateAccountStateIngestionError("PRIVATE_ACCOUNT_STATE_FIELDS_INCOMPLETE")
    if source != "FIXTURE_ONLY":
        raise PrivateAccountStateIngestionError(
            "NON_FIXTURE_PRIVATE_ACCOUNT_SOURCE_FORBIDDEN_IN_CAPABILITY_11_3"
        )
    if not isinstance(payload, dict):
        raise PrivateAccountStateIngestionError("PRIVATE_ACCOUNT_STATE_PAYLOAD_MUST_BE_OBJECT")
    return PrivateAccountStateSnapshotV1(
        snapshot_kind=snapshot_kind,
        venue=venue,
        account_identity=account_identity,
        observed_at_utc=observed_at_utc,
        payload=dict(payload),
        source=source,
    )


def refuse_network_private_account_ingestion_v1(*, snapshot_kind: str) -> dict[str, Any]:
    if snapshot_kind not in ALLOWED_SNAPSHOT_KINDS:
        raise PrivateAccountStateIngestionError(f"UNKNOWN_SNAPSHOT_KIND:{snapshot_kind}")
    raise PrivateAccountStateIngestionError(
        "PRIVATE_ACCOUNT_NETWORK_INGESTION_FORBIDDEN_IN_CAPABILITY_11_3"
    )


def prove_private_account_state_ingestion_contract_v1() -> dict[str, Any]:
    snapshot = build_private_account_state_snapshot_v1(
        snapshot_kind="accounts",
        venue="OKX",
        account_identity="acct-uid-demo",
        observed_at_utc="1970-01-01T00:00:00Z",
        payload={"equity": "0", "available_margin": "0"},
    )

    network_blocked = False
    try:
        refuse_network_private_account_ingestion_v1(snapshot_kind="open_positions")
    except PrivateAccountStateIngestionError as exc:
        network_blocked = "NETWORK_INGESTION_FORBIDDEN" in str(exc)

    non_fixture_blocked = False
    try:
        build_private_account_state_snapshot_v1(
            snapshot_kind="accounts",
            venue="OKX",
            account_identity="acct-uid-demo",
            observed_at_utc="1970-01-01T00:00:00Z",
            payload={},
            source="LIVE_NETWORK",
        )
    except PrivateAccountStateIngestionError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    unknown_blocked = False
    try:
        build_private_account_state_snapshot_v1(
            snapshot_kind="withdrawals",
            venue="OKX",
            account_identity="acct-uid-demo",
            observed_at_utc="1970-01-01T00:00:00Z",
            payload={},
        )
    except PrivateAccountStateIngestionError as exc:
        unknown_blocked = "UNKNOWN_SNAPSHOT_KIND" in str(exc)

    ok = all(
        [
            snapshot.source == "FIXTURE_ONLY",
            snapshot.owner == OWNER,
            network_blocked,
            non_fixture_blocked,
            unknown_blocked,
            PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3 is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
        ]
    )
    return {
        "ok": ok,
        "PRIVATE_ACCOUNT_STATE_SCHEMA_BOUND": True,
        "PRIVATE_ACCOUNT_NETWORK_INGESTION_PERFORMED": False,
        "FIXTURE_ONLY_SOURCE_REQUIRED": True,
        "network_ingestion_blocked": network_blocked,
        "non_fixture_blocked": non_fixture_blocked,
        "unknown_snapshot_kind_blocked": unknown_blocked,
        "allowed_snapshot_kinds": list(ALLOWED_SNAPSHOT_KINDS),
        "OWNER": PRIVATE_ACCOUNT_STATE_INGESTION_OWNER,
    }

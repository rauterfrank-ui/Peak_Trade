"""Venue session and connectivity contract (schema only; start forbidden)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    NETWORK_SESSION_ALLOWED,
    NETWORK_SESSION_STARTED,
    OWNER,
    VENUE_SESSION_CONTRACT_OWNER,
)


class VenueSessionContractError(ValueError):
    """Fail-closed venue session / connectivity contract violation."""


ALLOWED_CONNECTIVITY_STATES: tuple[str, ...] = (
    "DISCONNECTED",
    "CONNECTING",
    "CONNECTED",
    "DEGRADED",
    "HALTED",
)


@dataclass(frozen=True)
class VenueSessionStateRecordV1:
    """Durable/ephemeral venue session metadata without starting a session."""

    venue: str
    account_identity: str
    connectivity_state: str
    session_id: str
    activation_epoch: str
    classification: str = "EPHEMERAL_CONNECTION_STATE"
    network_session_started: bool = False
    owner: str = VENUE_SESSION_CONTRACT_OWNER
    contract_version: str = CONTRACT_VERSION


def build_venue_session_state_record_v1(
    *,
    venue: str,
    account_identity: str,
    connectivity_state: str,
    session_id: str,
    activation_epoch: str,
) -> VenueSessionStateRecordV1:
    if not venue or not account_identity or not session_id or not activation_epoch:
        raise VenueSessionContractError("VENUE_SESSION_FIELDS_INCOMPLETE")
    if connectivity_state not in ALLOWED_CONNECTIVITY_STATES:
        raise VenueSessionContractError(f"UNKNOWN_CONNECTIVITY_STATE:{connectivity_state}")
    if connectivity_state == "CONNECTED" and NETWORK_SESSION_ALLOWED is False:
        # Schema may represent CONNECTED for future stages, but Cap 11.3 forbids
        # claiming a started network session.
        pass
    return VenueSessionStateRecordV1(
        venue=venue,
        account_identity=account_identity,
        connectivity_state=connectivity_state,
        session_id=session_id,
        activation_epoch=activation_epoch,
        network_session_started=False,
    )


def refuse_venue_network_session_start_v1(record: VenueSessionStateRecordV1) -> dict[str, Any]:
    raise VenueSessionContractError(
        f"VENUE_NETWORK_SESSION_START_FORBIDDEN_IN_CAPABILITY_11_3:{record.session_id}"
    )


def prove_venue_session_and_connectivity_contract_v1() -> dict[str, Any]:
    record = build_venue_session_state_record_v1(
        venue="OKX",
        account_identity="acct-uid-demo",
        connectivity_state="DISCONNECTED",
        session_id="session-cap11-3-demo",
        activation_epoch="0",
    )
    start_blocked = False
    try:
        refuse_venue_network_session_start_v1(record)
    except VenueSessionContractError as exc:
        start_blocked = "NETWORK_SESSION_START_FORBIDDEN" in str(exc)

    unknown_blocked = False
    try:
        build_venue_session_state_record_v1(
            venue="OKX",
            account_identity="acct-uid-demo",
            connectivity_state="FLYING",
            session_id="session-bad",
            activation_epoch="0",
        )
    except VenueSessionContractError as exc:
        unknown_blocked = "UNKNOWN_CONNECTIVITY_STATE" in str(exc)

    ok = all(
        [
            record.network_session_started is False,
            record.classification == "EPHEMERAL_CONNECTION_STATE",
            record.owner == OWNER,
            start_blocked,
            unknown_blocked,
            NETWORK_SESSION_STARTED is False,
            NETWORK_SESSION_ALLOWED is False,
        ]
    )
    return {
        "ok": ok,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_ALLOWED": False,
        "session_start_blocked": start_blocked,
        "unknown_connectivity_blocked": unknown_blocked,
        "allowed_connectivity_states": list(ALLOWED_CONNECTIVITY_STATES),
        "OWNER": VENUE_SESSION_CONTRACT_OWNER,
    }

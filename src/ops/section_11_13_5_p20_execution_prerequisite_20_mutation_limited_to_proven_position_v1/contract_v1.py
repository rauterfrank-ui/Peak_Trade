"""Fail-closed EXECUTION_PREREQUISITE_20 mutation-limited-to-proven-position contract.

Named dependency: mutation limited to a proven nonzero target position.
Offline-closable as a gate contract. Send-time still needs a fresh proven
position. Runtime permit issuance, network session, and flatten execute
remain unauthorized.

Does not GET, POST, flatten, set LIVE_AUTHORIZED, or open a network session.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
EXECUTION_PREREQUISITE_20_STATUS = "PASS_OFFLINE_CONTRACT"
P20_NAMED_MUTATION_LIMITED_TO_PROVEN_POSITION_CONTRACT_CLOSED = True
P20_MUTATION_SCOPE_GATE_IMPLEMENTED = True
PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN = False
PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED = False
PREREQUISITE_20_FLATTEN_EXECUTE_AUTHORIZED = False
P20_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
P20_DOES_NOT_SET_LIVE_AUTHORIZED = True
P20_DOES_NOT_AUTHORIZE_FLATTEN = True
P20_DOES_NOT_GRANT_EXECUTION_READINESS = True
P20_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
FAIL_CLOSED_IF_PREREQUISITE_20_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE = True
P16_TEXT_REWRITTEN = False
PROVEN_POSITION_CLASSIFIER = "classify_target_position_state_v1"
PROVEN_POSITION_STATE = "TARGET_POSITION_NONZERO_PROVEN"
MUTATION_OBJECT = "VENUE_NATIVE_FLATTEN_PLACE_ORDER_BODY"
FLATTEN_QTY_RULE = "FULL_FLATTEN_EQUALS_ABS_OBSERVED_POS"


class MutationLimitedToProvenPositionContractError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_20 contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise MutationLimitedToProvenPositionContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_PROVEN_POSITION"
        )


def assert_runtime_mutation_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN") is True:
        raise MutationLimitedToProvenPositionContractError(
            "SEND_TIME_REOBSERVATION_CLAIMED_FROM_OFFLINE_CODE"
        )
    if payload.get("PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED") is True:
        raise MutationLimitedToProvenPositionContractError("NETWORK_SESSION_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise MutationLimitedToProvenPositionContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise MutationLimitedToProvenPositionContractError("POST_CLAIMED")

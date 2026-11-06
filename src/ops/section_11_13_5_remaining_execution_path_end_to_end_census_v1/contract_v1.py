"""Fail-closed remaining execution-path census offline contract.

Closes named residuals BOUNDED_RUNTIME_PERMIT_ISSUANCE, FLATTEN_EXECUTE, and
NETWORK_SESSION as CASE_B offline contracts. Runtime issuance, network
session, flatten execute, GET, and POST remain unauthorized.

Does not GET, POST, flatten, issue a runtime permit, or open a network session.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
BOUNDED_RUNTIME_PERMIT_ISSUANCE_STATUS = "PASS_OFFLINE_CONTRACT"
FLATTEN_EXECUTE_STATUS = "PASS_OFFLINE_CONTRACT"
NETWORK_SESSION_STATUS = "PASS_OFFLINE_CONTRACT"
REMAINING_EXECUTION_PATH_CENSUS_STATUS = "PASS_OFFLINE_CONTRACT"
BRPI_NAMED_ISSUANCE_CONTRACT_CLOSED = True
FLATTEN_EXECUTE_NAMED_CONTRACT_CLOSED = True
NETWORK_SESSION_NAMED_CONTRACT_CLOSED = True
CENSUS_COMPLETE = True
CENSUS_EXHAUSTION_PROVEN = True
LATENT_GAP_CENSUS_COMPLETE = True
BRPI_RUNTIME_PROVEN = False
FLATTEN_EXECUTE_AUTHORIZED = False
NETWORK_SESSION_AUTHORIZED = False
NETWORK_PROVEN = False
CREDENTIAL_USE_PROVEN = False
PRIVATE_GET_PROVEN = False
POST_PROVEN = False
RUNTIME_PERMIT_ISSUED = False
CENSUS_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
CENSUS_DOES_NOT_SET_LIVE_AUTHORIZED = True
CENSUS_DOES_NOT_AUTHORIZE_FLATTEN = True
CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS = True
CENSUS_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
CENSUS_DOES_NOT_AUTHORIZE_GET = True
CENSUS_DOES_NOT_AUTHORIZE_POST = True
FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE = True
STPR_TEXT_REWRITTEN = False
APT_TEXT_REWRITTEN = False
STP_TEXT_REWRITTEN = False
P25_TEXT_REWRITTEN = False
P20_TEXT_REWRITTEN = False
P16_TEXT_REWRITTEN = False
POSITION_GET_REQUIRED_THIS_PERSIST = False
POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO = False


class RemainingExecutionPathCensusContractError(RuntimeError):
    """Fail-closed remaining execution-path census contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise RemainingExecutionPathCensusContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_REMAINING_EXECUTION_PATH_CENSUS"
        )


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN") is True:
        raise RemainingExecutionPathCensusContractError("RUNTIME_PERMIT_ISSUANCE_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise RemainingExecutionPathCensusContractError("RUNTIME_PERMIT_BOOLEAN_TRUE_FORBIDDEN")
    if payload.get("FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise RemainingExecutionPathCensusContractError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("NETWORK_SESSION_AUTHORIZED") is True:
        raise RemainingExecutionPathCensusContractError("NETWORK_SESSION_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise RemainingExecutionPathCensusContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise RemainingExecutionPathCensusContractError("POST_CLAIMED")
    if payload.get("GET_PERFORMED_THIS_PERSIST") is True:
        raise RemainingExecutionPathCensusContractError("GET_CLAIMED")
    if payload.get("RUNTIME_PERMIT_ISSUED") is True:
        raise RemainingExecutionPathCensusContractError("RUNTIME_PERMIT_ISSUED_CLAIMED")

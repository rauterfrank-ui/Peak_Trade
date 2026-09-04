"""Fail-closed PR #6252 merge-closeout contract.

Consumes the stale OWNER_MERGE_GO pointer after squash-merge of PR #6252.
Does not rewrite PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION text. Does not
close G12. Does not promote empty data to zero. Does not authorize §11.14.
Does not GET, POST, retry, flatten, fund, or merge.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
PR_6252_STATUS = "SQUASH_MERGED"
OWNER_MERGE_GO_STATUS = "CONSUMED_CLOSED"
PRODUCTIVE_FLATTEN_TEXT_REWRITTEN = False
STALE_NEXT_POINTER_CORRECTED = True
STALE_POINTER_WAS = "OWNER_MERGE_GO"
G12_STATUS = "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
TARGET_POSITION_ZERO_PROVEN = False
LIVE_FLATTEN_PROVABILITY_PROVEN = False
RECOVERY_POSITION_SEMANTICS = "CASE_C_EMPTY_DATA_NOT_ZERO"
EMPTY_DATA_IS_ZERO = False
SECTION_11_14_AUTHORIZED = False
RETRY_ALLOWED = False
GET_PERFORMED_THIS_PERSIST = False
POST_PERFORMED = False
PRIVATE_AUTH_USED = False
MERGE_AUTHORIZED_BY_THIS_PERSIST = False
CLOSEOUT_DOES_NOT_SET_LIVE_AUTHORIZED = True
CLOSEOUT_DOES_NOT_SET_CANARY_AUTHORIZED = True
CLOSEOUT_DOES_NOT_AUTHORIZE_GET = True
CLOSEOUT_DOES_NOT_AUTHORIZE_POST = True
CLOSEOUT_DOES_NOT_AUTHORIZE_RETRY = True
CLOSEOUT_DOES_NOT_AUTHORIZE_FLATTEN = True
CLOSEOUT_DOES_NOT_AUTHORIZE_SECTION_11_14 = True
FAIL_CLOSED_IF_G12_MARKED_CLOSED = True
FAIL_CLOSED_IF_EMPTY_DATA_PROMOTED_TO_ZERO = True
FAIL_CLOSED_IF_SECTION_11_14_AUTHORIZED = True


class Pr6252MergeCloseoutContractError(RuntimeError):
    """Fail-closed PR #6252 merge-closeout contract violation."""


def assert_preserved_flatten_residuals_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("G12_STATUS") != G12_STATUS:
        raise Pr6252MergeCloseoutContractError("G12_MUST_REMAIN_OPEN")
    if payload.get("TARGET_POSITION_ZERO_PROVEN") is True:
        raise Pr6252MergeCloseoutContractError("TARGET_POSITION_ZERO_MUST_REMAIN_UNPROVEN")
    if payload.get("LIVE_FLATTEN_PROVABILITY_PROVEN") is True:
        raise Pr6252MergeCloseoutContractError("LIVE_FLATTEN_PROVABILITY_MUST_REMAIN_UNPROVEN")
    if payload.get("RECOVERY_POSITION_SEMANTICS") != RECOVERY_POSITION_SEMANTICS:
        raise Pr6252MergeCloseoutContractError("RECOVERY_SEMANTICS_MUST_REMAIN_CASE_C")
    if payload.get("EMPTY_DATA_IS_ZERO") is True:
        raise Pr6252MergeCloseoutContractError("EMPTY_DATA_MUST_NOT_BE_ZERO")
    if payload.get("SECTION_11_14_AUTHORIZED") is True:
        raise Pr6252MergeCloseoutContractError("SECTION_11_14_MUST_REMAIN_UNAUTHORIZED")
    if payload.get("RETRY_ALLOWED") is True:
        raise Pr6252MergeCloseoutContractError("RETRY_MUST_REMAIN_FORBIDDEN")


def assert_no_runtime_authority_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("GET_PERFORMED_THIS_PERSIST") is True:
        raise Pr6252MergeCloseoutContractError("GET_CLAIMED")
    if payload.get("POST_PERFORMED") is True:
        raise Pr6252MergeCloseoutContractError("POST_CLAIMED")
    if payload.get("PRIVATE_AUTH_USED") is True:
        raise Pr6252MergeCloseoutContractError("PRIVATE_AUTH_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise Pr6252MergeCloseoutContractError("LIVE_AUTHORIZED_CLAIMED")
    if payload.get("CANARY_AUTHORIZED") is True:
        raise Pr6252MergeCloseoutContractError("CANARY_AUTHORIZED_CLAIMED")
    if payload.get("MERGE_AUTHORIZED_BY_THIS_PERSIST") is True:
        raise Pr6252MergeCloseoutContractError("MERGE_CLAIMED")
    if payload.get("PRODUCTIVE_FLATTEN_TEXT_REWRITTEN") is True:
        raise Pr6252MergeCloseoutContractError("FLATTEN_TEXT_REWRITTEN")

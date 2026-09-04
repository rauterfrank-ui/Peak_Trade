"""Fail-closed contract invariants for the offline §11.14 surface."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AMEND_ALLOWED,
    AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX,
    CANCEL_ALLOWED,
    CASE_ADJUDICATION,
    COLLECTOR_ACTIVATED,
    CREDENTIAL_USE_ALLOWED,
    FLATTEN_EXECUTE_ALLOWED,
    FUNDING_ALLOWED,
    LADDER_FIELD_COUNT,
    LADDER_FIELD_DEFAULTS,
    LADDER_FIELDS,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_FILL_OBSERVED,
    LIVE_FEE_OBSERVED,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_SUBMIT_ACK_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND,
    LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND,
    MANDATORY_LIVE_METRIC_COUNT,
    MANDATORY_LIVE_METRICS,
    OBSERVED_OR_PROVEN_FIELDS_MUST_REMAIN_FALSE,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    PUBLIC_GET_ALLOWED,
    RETRY_DEFAULT,
    SECOND_SUBMIT_DEFAULT,
    SECTION_11_14_AUTHORIZED,
    SECTION_11_14_COMPLETE,
    SECTION_11_14_LIVE_EVIDENCE_COLLECTION_AUTHORIZED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)


class Section1114OfflineSurfaceError(RuntimeError):
    """Fail-closed §11.14 offline-surface violation."""


def assert_contract_invariants_v1(payload: Mapping[str, Any] | None = None) -> None:
    if len(LADDER_FIELDS) != LADDER_FIELD_COUNT:
        raise Section1114OfflineSurfaceError("LADDER_FIELD_COUNT_MISMATCH")
    if len(MANDATORY_LIVE_METRICS) != MANDATORY_LIVE_METRIC_COUNT:
        raise Section1114OfflineSurfaceError("MANDATORY_LIVE_METRIC_COUNT_MISMATCH")
    if len(set(LADDER_FIELDS)) != LADDER_FIELD_COUNT:
        raise Section1114OfflineSurfaceError("LADDER_FIELD_DUPLICATE")
    if len(set(MANDATORY_LIVE_METRICS)) != MANDATORY_LIVE_METRIC_COUNT:
        raise Section1114OfflineSurfaceError("MANDATORY_LIVE_METRIC_DUPLICATE")
    if SECTION_11_14_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("SECTION_11_14_MUST_REMAIN_UNAUTHORIZED")
    if SECTION_11_14_COMPLETE is True:
        raise Section1114OfflineSurfaceError("SECTION_11_14_MUST_REMAIN_INCOMPLETE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("SECTION_11_14_RUNTIME_MUST_REMAIN_UNAUTHORIZED")
    if SECTION_11_14_LIVE_EVIDENCE_COLLECTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("LIVE_EVIDENCE_COLLECTION_MUST_REMAIN_UNAUTHORIZED")
    if LIVE_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if LIVE_ENABLED is True:
        raise Section1114OfflineSurfaceError("LIVE_ENABLED_MUST_REMAIN_FALSE")
    if LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("LIVE_ARMED_MUST_REMAIN_FALSE")
    if SUBMIT_UNLOCKED is True:
        raise Section1114OfflineSurfaceError("SUBMIT_UNLOCKED_MUST_REMAIN_FALSE")
    if TESTNET_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("TESTNET_AUTHORIZED_MUST_REMAIN_FALSE")
    if POST_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    if ORDER_SUBMIT_ALLOWED is True:
        raise Section1114OfflineSurfaceError("ORDER_SUBMIT_MUST_REMAIN_FORBIDDEN")
    if CANCEL_ALLOWED is True:
        raise Section1114OfflineSurfaceError("CANCEL_MUST_REMAIN_FORBIDDEN")
    if AMEND_ALLOWED is True:
        raise Section1114OfflineSurfaceError("AMEND_MUST_REMAIN_FORBIDDEN")
    if FLATTEN_EXECUTE_ALLOWED is True:
        raise Section1114OfflineSurfaceError("FLATTEN_MUST_REMAIN_FORBIDDEN")
    if FUNDING_ALLOWED is True:
        raise Section1114OfflineSurfaceError("FUNDING_MUST_REMAIN_FORBIDDEN")
    if PUBLIC_GET_ALLOWED is not True:
        raise Section1114OfflineSurfaceError("CONDITIONAL_PUBLIC_GET_MUST_BE_ALLOWED")
    if COLLECTOR_ACTIVATED is True:
        raise Section1114OfflineSurfaceError("LIVE_COLLECTOR_MUST_REMAIN_INACTIVE")
    if LIVE_EXECUTION_CODE_EXISTS is not True:
        raise Section1114OfflineSurfaceError("LIVE_EXECUTION_CODE_EXISTS_MUST_BE_TRUE")
    if LIVE_EXECUTION_PATH_REACHABLE is not True:
        raise Section1114OfflineSurfaceError("LIVE_EXECUTION_PATH_REACHABLE_MUST_BE_TRUE")
    if LIVE_PRIVATE_READ_ONLY_PROVEN is not True:
        raise Section1114OfflineSurfaceError("LIVE_PRIVATE_READ_ONLY_PROVEN_MUST_BE_TRUE")
    if LIVE_ORDER_PLAN_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("LIVE_ORDER_PLAN_OBSERVED_MUST_BE_TRUE")
    if LIVE_SUBMIT_ACK_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("LIVE_SUBMIT_ACK_OBSERVED_MUST_BE_TRUE")
    if LIVE_FILL_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("LIVE_FILL_OBSERVED_MUST_BE_TRUE")
    if LIVE_FEE_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("LIVE_FEE_OBSERVED_MUST_BE_TRUE")
    if AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX != 1:
        raise Section1114OfflineSurfaceError("SUBMIT_COUNT_MAX_DRIFT")
    if RETRY_DEFAULT is True or SECOND_SUBMIT_DEFAULT is True:
        raise Section1114OfflineSurfaceError("RETRY_OR_SECOND_SUBMIT_DEFAULT_TRUE")
    if CASE_ADJUDICATION != "CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE":
        raise Section1114OfflineSurfaceError("CASE_ADJUDICATION_DRIFT")
    if LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND is not True:
        raise Section1114OfflineSurfaceError("ACK_PROOF_CRITERION_MUST_BE_BOUND")
    if LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND is not True:
        raise Section1114OfflineSurfaceError("ACK_PRODUCER_MUST_BE_BOUND")
    if LIVE_EXECUTION_PATH_REACHABLE is True and LIVE_EXECUTION_CODE_EXISTS is not True:
        raise Section1114OfflineSurfaceError("PATH_REACHABLE_WITHOUT_CODE_EXISTS")
    if CREDENTIAL_USE_ALLOWED is not True:
        raise Section1114OfflineSurfaceError("CONDITIONAL_CREDENTIAL_USE_MUST_BE_ALLOWED")
    if PRIVATE_GET_ALLOWED is not True:
        raise Section1114OfflineSurfaceError("CONDITIONAL_PRIVATE_GET_MUST_BE_ALLOWED")
    for field_name in OBSERVED_OR_PROVEN_FIELDS_MUST_REMAIN_FALSE:
        if LADDER_FIELD_DEFAULTS[field_name] is True:
            raise Section1114OfflineSurfaceError(f"OBSERVED_FIELD_MUST_REMAIN_FALSE:{field_name}")
    if payload is None:
        return
    if payload.get("SECTION_11_14_AUTHORIZED") is True:
        raise Section1114OfflineSurfaceError("SECTION_11_14_PROMOTED_TO_AUTHORIZED")
    if payload.get("SECTION_11_14_COMPLETE") is True:
        raise Section1114OfflineSurfaceError("SECTION_11_14_PROMOTED_TO_COMPLETE")
    if payload.get("COLLECTOR_ACTIVATED") is True:
        raise Section1114OfflineSurfaceError("LIVE_COLLECTOR_ACTIVATED")
    if payload.get("LIVE_EXECUTION_CODE_EXISTS") is not True:
        raise Section1114OfflineSurfaceError("LIVE_EXECUTION_CODE_EXISTS_PAYLOAD_MUST_BE_TRUE")
    if payload.get("LIVE_SUBMIT_ACK_OBSERVED") is not True:
        raise Section1114OfflineSurfaceError("LIVE_SUBMIT_ACK_OBSERVED_PAYLOAD_MUST_BE_TRUE")
    if payload.get("LIVE_FILL_OBSERVED") is not True:
        raise Section1114OfflineSurfaceError("LIVE_FILL_OBSERVED_PAYLOAD_MUST_BE_TRUE")
    if payload.get("LIVE_FEE_OBSERVED") is not True:
        raise Section1114OfflineSurfaceError("LIVE_FEE_OBSERVED_PAYLOAD_MUST_BE_TRUE")
    if (
        payload.get("LIVE_EXECUTION_PATH_REACHABLE") is True
        and payload.get("LIVE_EXECUTION_CODE_EXISTS") is not True
    ):
        raise Section1114OfflineSurfaceError("PATH_REACHABLE_WITHOUT_CODE_EXISTS")
    if (
        payload.get("LIVE_PRIVATE_READ_ONLY_PROVEN") is True
        and payload.get("LIVE_EXECUTION_PATH_REACHABLE") is not True
    ):
        raise Section1114OfflineSurfaceError("PRIVATE_READ_ONLY_WITHOUT_PATH_REACHABLE")
    if (
        payload.get("LIVE_ORDER_PLAN_OBSERVED") is True
        and payload.get("LIVE_PRIVATE_READ_ONLY_PROVEN") is not True
    ):
        raise Section1114OfflineSurfaceError("ORDER_PLAN_WITHOUT_PRIVATE_READ_ONLY")
    if payload.get("POST_USED") is True or payload.get("POST") is True:
        if payload.get("LIVE_SUBMIT_ACK_OBSERVED") is not True:
            raise Section1114OfflineSurfaceError("POST_WITHOUT_ACK_FIELD")
    allowed_true = {
        "LIVE_EXECUTION_CODE_EXISTS",
        "LIVE_EXECUTION_PATH_REACHABLE",
        "LIVE_PRIVATE_READ_ONLY_PROVEN",
        "LIVE_ORDER_PLAN_OBSERVED",
        "LIVE_SUBMIT_ACK_OBSERVED",
        "LIVE_FILL_OBSERVED",
        "LIVE_FEE_OBSERVED",
    }
    for field_name in LADDER_FIELDS:
        if field_name in allowed_true:
            continue
        if payload.get(field_name) is True:
            raise Section1114OfflineSurfaceError(f"LADDER_FIELD_PROMOTED_TRUE:{field_name}")

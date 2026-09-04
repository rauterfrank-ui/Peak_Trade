"""Fail-closed contract invariants for the offline §11.14 surface."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AMEND_ALLOWED,
    CANCEL_ALLOWED,
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
    MANDATORY_LIVE_METRIC_COUNT,
    MANDATORY_LIVE_METRICS,
    OBSERVED_OR_PROVEN_FIELDS_MUST_REMAIN_FALSE,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    PUBLIC_GET_ALLOWED,
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
    if CREDENTIAL_USE_ALLOWED is True:
        raise Section1114OfflineSurfaceError("CREDENTIAL_USE_MUST_REMAIN_FORBIDDEN")
    if PUBLIC_GET_ALLOWED is True:
        raise Section1114OfflineSurfaceError("PUBLIC_GET_MUST_REMAIN_FORBIDDEN")
    if PRIVATE_GET_ALLOWED is True:
        raise Section1114OfflineSurfaceError("PRIVATE_GET_MUST_REMAIN_FORBIDDEN")
    if COLLECTOR_ACTIVATED is True:
        raise Section1114OfflineSurfaceError("LIVE_COLLECTOR_MUST_REMAIN_INACTIVE")
    if LIVE_EXECUTION_CODE_EXISTS is True:
        raise Section1114OfflineSurfaceError("LIVE_EXECUTION_CODE_EXISTS_MUST_REMAIN_FALSE")
    if LIVE_EXECUTION_PATH_REACHABLE is True:
        raise Section1114OfflineSurfaceError("LIVE_EXECUTION_PATH_REACHABLE_MUST_REMAIN_FALSE")
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
    for field_name in LADDER_FIELDS:
        if payload.get(field_name) is True:
            raise Section1114OfflineSurfaceError(f"LADDER_FIELD_PROMOTED_TRUE:{field_name}")

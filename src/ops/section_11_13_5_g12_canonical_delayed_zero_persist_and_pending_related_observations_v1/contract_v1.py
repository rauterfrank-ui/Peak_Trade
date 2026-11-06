"""Fail-closed flags for canonical delayed-zero persist and P7/P9 observations."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    ABSENT_TARGET_ROW_IS_ZERO,
    CANCEL_ALLOWED,
    DELAYED_ZERO_DOES_NOT_IMPLY_PENDING_EMPTY,
    DELAYED_ZERO_DOES_NOT_IMPLY_RELATED_EMPTY,
    EMPTY_DATA_IS_ZERO,
    FLATTEN_EXECUTE_ALLOWED,
    FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL,
    FUNDING_ALLOWED,
    MERGE_AUTHORIZED_BY_THIS_PERSIST,
    ORDER_MUTATION_ALLOWED,
    POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS,
    POST_ALLOWED,
    RETRY_ALLOWED,
    SECTION_11_14_AUTHORIZED,
)


class G12CanonicalDelayedZeroPersistError(RuntimeError):
    """Fail-closed canonical delayed-zero persist / P7/P9 violation."""


def assert_contract_invariants_v1(payload: Mapping[str, Any] | None = None) -> None:
    if EMPTY_DATA_IS_ZERO is True:
        raise G12CanonicalDelayedZeroPersistError("EMPTY_DATA_MUST_NOT_BE_ZERO")
    if ABSENT_TARGET_ROW_IS_ZERO is True:
        raise G12CanonicalDelayedZeroPersistError("ABSENT_TARGET_MUST_NOT_BE_ZERO")
    if DELAYED_ZERO_DOES_NOT_IMPLY_PENDING_EMPTY is not True:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_MUST_NOT_IMPLY_PENDING")
    if DELAYED_ZERO_DOES_NOT_IMPLY_RELATED_EMPTY is not True:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_MUST_NOT_IMPLY_RELATED")
    if POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS is not True:
        raise G12CanonicalDelayedZeroPersistError("POSID_FILTER_MUST_NOT_PROVE_RELATED")
    if FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL is not True:
        raise G12CanonicalDelayedZeroPersistError("OPS_LOCAL_MUST_REMAIN_NON_CANONICAL")
    if SECTION_11_14_AUTHORIZED is True:
        raise G12CanonicalDelayedZeroPersistError("SECTION_11_14_MUST_REMAIN_UNAUTHORIZED")
    if POST_ALLOWED is True:
        raise G12CanonicalDelayedZeroPersistError("POST_MUST_REMAIN_FORBIDDEN")
    if ORDER_MUTATION_ALLOWED is True:
        raise G12CanonicalDelayedZeroPersistError("ORDER_MUTATION_MUST_REMAIN_FORBIDDEN")
    if CANCEL_ALLOWED is True:
        raise G12CanonicalDelayedZeroPersistError("CANCEL_MUST_REMAIN_FORBIDDEN")
    if FLATTEN_EXECUTE_ALLOWED is True:
        raise G12CanonicalDelayedZeroPersistError("FLATTEN_MUST_REMAIN_FORBIDDEN")
    if FUNDING_ALLOWED is True:
        raise G12CanonicalDelayedZeroPersistError("FUNDING_MUST_REMAIN_FORBIDDEN")
    if RETRY_ALLOWED is True:
        raise G12CanonicalDelayedZeroPersistError("RETRY_MUST_REMAIN_FORBIDDEN")
    if MERGE_AUTHORIZED_BY_THIS_PERSIST is True:
        raise G12CanonicalDelayedZeroPersistError("MERGE_MUST_REMAIN_UNAUTHORIZED")
    if payload is None:
        return
    if payload.get("forensic_local_treated_as_canonical") is True:
        raise G12CanonicalDelayedZeroPersistError("FORENSIC_LOCAL_PROMOTED_TO_CANONICAL")
    if payload.get("EMPTY_DATA_IS_ZERO") is True:
        raise G12CanonicalDelayedZeroPersistError("EMPTY_DATA_PROMOTED_TO_ZERO")
    if payload.get("full_conjunction_proven") is not True and payload.get(
        "LIVE_FLATTEN_PROVABILITY_PROVEN"
    ):
        raise G12CanonicalDelayedZeroPersistError("PROVABILITY_CLAIMED_WITHOUT_FULL_CONJUNCTION")
    if (
        payload.get("G12_STATUS") == "CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN"
        and payload.get("full_conjunction_proven") is not True
    ):
        raise G12CanonicalDelayedZeroPersistError("G12_CLOSED_WITHOUT_FULL_CONJUNCTION")

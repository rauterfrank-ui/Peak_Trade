"""Fail-closed flags for the delayed G12 conjunction contract.

Does not rewrite the same-session CHOICE_B evaluator. Does not close G12
by delayed-zero alone. Does not GET or POST.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.constants_v1 import (
    ABSENT_TARGET_ROW_IS_ZERO,
    CANONICAL_SSOT_LIVE_FLATTEN_PROVABILITY_PROVEN,
    CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN,
    CAUSAL_LINEAGE_IS_NOT_SAME_SESSION_READBACK,
    DELAYED_ZERO_DOES_NOT_IMPLY_LIVE_FLATTEN_PROVEN,
    DELAYED_ZERO_DOES_NOT_IMPLY_PENDING_EMPTY,
    DELAYED_ZERO_DOES_NOT_IMPLY_RELATED_EMPTY,
    EMPTY_DATA_IS_ZERO,
    FILL_IS_NOT_POSITION_ZERO_PROVEN,
    FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL,
    G12_STATUS,
    HISTORICAL_PENDING_IS_NOT_CURRENT_PENDING,
    IDENTITY_EQUALITY_IS_NOT_CAUSAL_LINEAGE,
    INSTID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS,
    ORDER_FILLED_IS_NOT_POSITION_ZERO_PROVEN,
    POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS,
    POST_READBACK_IDENTITY_REQUIRED_FOR_DELAYED_PROOF,
    SECTION_11_14_AUTHORIZED,
)


class DelayedG12ConjunctionContractError(RuntimeError):
    """Fail-closed delayed G12 conjunction contract violation."""


def assert_contract_invariants_v1(payload: Mapping[str, Any] | None = None) -> None:
    if EMPTY_DATA_IS_ZERO is True:
        raise DelayedG12ConjunctionContractError("EMPTY_DATA_MUST_NOT_BE_ZERO")
    if ABSENT_TARGET_ROW_IS_ZERO is True:
        raise DelayedG12ConjunctionContractError("ABSENT_TARGET_MUST_NOT_BE_ZERO")
    if DELAYED_ZERO_DOES_NOT_IMPLY_LIVE_FLATTEN_PROVEN is not True:
        raise DelayedG12ConjunctionContractError("DELAYED_ZERO_MUST_NOT_IMPLY_LIVE_FLATTEN")
    if FILL_IS_NOT_POSITION_ZERO_PROVEN is not True:
        raise DelayedG12ConjunctionContractError("FILL_MUST_NOT_BE_ZERO")
    if ORDER_FILLED_IS_NOT_POSITION_ZERO_PROVEN is not True:
        raise DelayedG12ConjunctionContractError("ORDER_FILLED_MUST_NOT_BE_ZERO")
    if POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS is not True:
        raise DelayedG12ConjunctionContractError("POSID_FILTER_MUST_NOT_PROVE_RELATED")
    if INSTID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS is not True:
        raise DelayedG12ConjunctionContractError("INSTID_FILTER_MUST_NOT_PROVE_RELATED")
    if DELAYED_ZERO_DOES_NOT_IMPLY_PENDING_EMPTY is not True:
        raise DelayedG12ConjunctionContractError("DELAYED_ZERO_MUST_NOT_IMPLY_PENDING")
    if DELAYED_ZERO_DOES_NOT_IMPLY_RELATED_EMPTY is not True:
        raise DelayedG12ConjunctionContractError("DELAYED_ZERO_MUST_NOT_IMPLY_RELATED")
    if HISTORICAL_PENDING_IS_NOT_CURRENT_PENDING is not True:
        raise DelayedG12ConjunctionContractError("HISTORICAL_PENDING_MUST_NOT_BECOME_CURRENT")
    if IDENTITY_EQUALITY_IS_NOT_CAUSAL_LINEAGE is not True:
        raise DelayedG12ConjunctionContractError("IDENTITY_MUST_NOT_EQUAL_CAUSAL_LINEAGE")
    if CAUSAL_LINEAGE_IS_NOT_SAME_SESSION_READBACK is not True:
        raise DelayedG12ConjunctionContractError("CAUSAL_LINEAGE_MUST_NOT_BE_SAME_SESSION")
    if POST_READBACK_IDENTITY_REQUIRED_FOR_DELAYED_PROOF is True:
        raise DelayedG12ConjunctionContractError("DELAYED_PROOF_MUST_NOT_REQUIRE_IDENTITY_EQUALITY")
    if FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL is not True:
        raise DelayedG12ConjunctionContractError("OPS_LOCAL_MUST_REMAIN_NON_CANONICAL")
    if G12_STATUS != "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN":
        raise DelayedG12ConjunctionContractError("CANONICAL_G12_MUST_REMAIN_OPEN")
    if CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN is True:
        raise DelayedG12ConjunctionContractError("CANONICAL_ZERO_MUST_REMAIN_UNPROVEN")
    if CANONICAL_SSOT_LIVE_FLATTEN_PROVABILITY_PROVEN is True:
        raise DelayedG12ConjunctionContractError("CANONICAL_PROVABILITY_MUST_REMAIN_UNPROVEN")
    if SECTION_11_14_AUTHORIZED is True:
        raise DelayedG12ConjunctionContractError("SECTION_11_14_MUST_REMAIN_UNAUTHORIZED")
    if payload is None:
        return
    if payload.get("G12_STATUS") == "CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN":
        raise DelayedG12ConjunctionContractError("G12_MUST_NOT_BE_MARKED_CLOSED_BY_THIS_CONTRACT")
    if payload.get("forensic_local_treated_as_canonical") is True:
        raise DelayedG12ConjunctionContractError("FORENSIC_LOCAL_PROMOTED_TO_CANONICAL")

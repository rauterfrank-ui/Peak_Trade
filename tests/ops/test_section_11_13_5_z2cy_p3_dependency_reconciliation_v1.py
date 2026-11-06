"""§11.13.5.Z2CY post-Z2CX P3 dependency reconciliation. Offline only."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2cx_p3_dependency_reconciliation_v1 import (
    ADJUDICATION,
    BLOCKER_CLASS,
    CLASS_D_CONSUMED,
    COVER_USDC_ADJUDICATED,
    COVER_USDC_STATUS,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_READY,
    FX_REOPENED,
    FX_STATUS,
    LiveCanaryPostZ2cxP3DependencyReconciliationError,
    NEXT_ACTIONABLE_BLOCKER,
    NEXT_AUTHORITY_BOUNDARY,
    NOT_REPROVEN_Z2AR_CLASSES,
    OFFLINE_RESOLUTION_POSSIBLE,
    OPEN_DEPENDENCY_COUNT,
    OWNER_GO,
    REMAINING_UNADJUDICATED_Z2AR_UNRANKED_CLASSES,
    REMAINING_UNRANKED_AFTER_Z2CX,
    THIS_GO_AUTHORIZES_FLATTEN,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    UNIQUE_CANONICAL_NEXT_TRACK,
    Z2AP_CONSUMED,
    adjudicate_post_z2cx_p3_dependency_reconciliation_v1,
    reject_busywork_remainder_v1,
    reject_offline_substitute_for_08_v1,
    reject_remaining_unranked_still_open_v1,
    reject_unique_canonical_next_invention_v1,
)


def test_reconciliation_constants_are_fail_closed() -> None:
    assert ADJUDICATION == "CRITICAL_PATH_BLOCKER_IDENTIFIED_NO_UNIQUE_CANONICAL_NEXT"
    assert UNIQUE_CANONICAL_NEXT_TRACK == "NONE"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == NEXT_ACTIONABLE_BLOCKER
    assert NEXT_ACTIONABLE_BLOCKER == ("EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN")
    assert BLOCKER_CLASS == "NEW_FIRST_PARTY_GET_REQUIRED"
    assert OFFLINE_RESOLUTION_POSSIBLE is False
    assert REMAINING_UNRANKED_AFTER_Z2CX == "NONE"
    assert REMAINING_UNADJUDICATED_Z2AR_UNRANKED_CLASSES == ()
    assert NOT_REPROVEN_Z2AR_CLASSES == (
        "COVER_USDC",
        "FX",
        "ROUNDING",
        "FINISHED_RISK_ENVELOPE_NUMERIC",
        "USD_USDC_ACCOUNT_SETTLEMENT",
    )
    assert OPEN_DEPENDENCY_COUNT == 10
    assert FX_STATUS == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert FX_REOPENED is False
    assert COVER_USDC_ADJUDICATED is False
    assert COVER_USDC_STATUS == "UNINSTANTIATED"
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert THIS_GO_AUTHORIZES_FLATTEN is False
    assert CLASS_D_CONSUMED is False
    assert Z2AP_CONSUMED is False
    assert EXECUTION_READY is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert "GET_ACCOUNT_POSITIONS" in NEXT_AUTHORITY_BOUNDARY


def test_census_does_not_treat_exhausted_unranked_as_next() -> None:
    result = adjudicate_post_z2cx_p3_dependency_reconciliation_v1()
    assert result["OFFLINE_RESOLUTION_POSSIBLE"] is False
    assert result["REMAINING_UNRANKED_AFTER_Z2CX"] == "NONE"
    dispositions = {row["TRACK_ID"]: row["DISPOSITION"] for row in result["census"]}
    assert (
        dispositions["P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"]
        == "EXHAUSTED_OFFLINE_REPROOF_SURFACE"
    )
    assert (
        dispositions["P3_PREREQUISITE_08_UNFILTERED_POSITION_REOBSERVATION"]
        == "ELIGIBLE_NEXT_REQUIRES_SEPARATE_GET_GO"
    )
    assert dispositions["P3_CLASS_D_PRODUCTIVE_FLATTEN_MUTATION"] == "BLOCKED"
    assert dispositions["P3_Z2AP_PRODUCTIVE_LIVE_FLATTEN_PROOF"] == "BLOCKED"
    assert (
        dispositions["P3_POST_ACTION_READBACK_FRESHNESS_POLICY"]
        == "ELIGIBLE_OFFLINE_NOT_CRITICAL_PATH"
    )


def test_unique_next_offline_substitute_and_busywork_fail_closed() -> None:
    assert (
        reject_unique_canonical_next_invention_v1(claimed_unique=None)
        == "UNIQUE_CANONICAL_NEXT_TRACK_NONE_BY_P3_POLICY"
    )
    with pytest.raises(LiveCanaryPostZ2cxP3DependencyReconciliationError):
        reject_unique_canonical_next_invention_v1(
            claimed_unique="P3_POST_ACTION_READBACK_FRESHNESS_POLICY"
        )
    assert (
        reject_offline_substitute_for_08_v1(claimed_offline_resolves_08=False)
        == "OFFLINE_RESOLUTION_OF_08_IMPOSSIBLE"
    )
    with pytest.raises(LiveCanaryPostZ2cxP3DependencyReconciliationError):
        reject_offline_substitute_for_08_v1(claimed_offline_resolves_08=True)
    assert (
        reject_busywork_remainder_v1(selected_non_critical_offline=False)
        == "NON_CRITICAL_OFFLINE_REMAINDER_NOT_SELECTED"
    )
    with pytest.raises(LiveCanaryPostZ2cxP3DependencyReconciliationError):
        reject_busywork_remainder_v1(selected_non_critical_offline=True)
    assert (
        reject_remaining_unranked_still_open_v1(claimed_remaining_unranked="NONE")
        == "REMAINING_UNRANKED_AFTER_Z2CX_NONE"
    )
    with pytest.raises(LiveCanaryPostZ2cxP3DependencyReconciliationError):
        reject_remaining_unranked_still_open_v1(claimed_remaining_unranked="FX")
    with pytest.raises(LiveCanaryPostZ2cxP3DependencyReconciliationError):
        adjudicate_post_z2cx_p3_dependency_reconciliation_v1(reopen_fx=True)
    with pytest.raises(LiveCanaryPostZ2cxP3DependencyReconciliationError):
        adjudicate_post_z2cx_p3_dependency_reconciliation_v1(adjudicate_cover_usdc=True)

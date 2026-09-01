"""§11.13.5.Z2DA post-Z2CZ semantic rebind. Offline only."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2cz_position_creation_autonomy_semantic_rebind_v1 import (
    ADJUDICATION,
    ADDENDUM_CONSUMED,
    ADDENDUM_ID,
    AI_CAN_DIRECTLY_SUBMIT_ORDER,
    AI_PRODUCTIVE_COMPONENT_COUNT,
    ATLAS_MUTATION,
    AUTONOMY_ORCHESTRATOR_FOUND,
    BLOCKER_CLASS,
    BLOCKS_NEW_ENTRY_DRIFT_STATUS,
    CAN_SYSTEM_AUTONOMOUSLY_TRADE_END_TO_END_TODAY,
    CLASS_D_CONSUMED,
    CORE_AI_BASED,
    EARLIEST_REAL_UNRESOLVED_DEPENDENCY,
    EXECUTION_READY,
    FULL_AUTONOMY_IS_SECOND_TRADING_AUTHORITY,
    LIVE_RECONCILIATION_PROVEN_DRIFT_STATUS,
    LIVE_VENUE_BRANCH,
    LiveCanaryPostZ2czSemanticRebindError,
    NEXT_ACTIONABLE_BLOCKER,
    NO_ORDER_OWNER_GRAPH,
    OWNER_GO,
    PARENT_PERSIST_PLAN_VERDICT,
    POSITION_CREATION_CURRENTLY_AUTHORIZED,
    POSITION_CREATION_PRODUCER,
    POSITION_CREATION_SEAM_STATUS,
    PREREQUISITE_08_CREATES_POSITION,
    PREREQUISITE_08_EXPECTS_PREEXISTING_POSITION,
    SELF_LEARNING_CLOSED_LOOP_EXISTS,
    SELF_LEARNING_EQUALS_SELF_AUTHORIZING,
    THIS_GO_AUTHORIZES_FLATTEN,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    Z2AP_CONSUMED,
    adjudicate_post_z2cz_position_creation_autonomy_semantic_rebind_v1,
    reject_08_as_isolated_primary_blocker_v1,
    reject_08_creates_position_v1,
    reject_empty_windows_causal_overclaim_v1,
    reject_full_autonomy_as_second_core_v1,
    reject_identical_get_as_high_value_next_v1,
    reject_invented_position_creation_producer_v1,
    reject_self_learning_self_authorizing_v1,
)


def test_rebind_constants_are_fail_closed() -> None:
    assert ADJUDICATION == "UPSTREAM_POSITION_CREATION_SEAM_REBOUND_BEFORE_PREREQUISITE_08"
    assert PREREQUISITE_08_CREATES_POSITION is False
    assert PREREQUISITE_08_EXPECTS_PREEXISTING_POSITION is True
    assert POSITION_CREATION_SEAM_STATUS == "MISSING_OR_UNAUTHORIZED"
    assert POSITION_CREATION_PRODUCER == "CURRENTLY_NONE_AUTHORIZED_REACHABLE"
    assert POSITION_CREATION_CURRENTLY_AUTHORIZED is False
    assert EARLIEST_REAL_UNRESOLVED_DEPENDENCY == NEXT_ACTIONABLE_BLOCKER
    assert BLOCKER_CLASS == "ARCHITECTURAL_MISSING_UPSTREAM_SEAM"
    assert FULL_AUTONOMY_IS_SECOND_TRADING_AUTHORITY is False
    assert SELF_LEARNING_EQUALS_SELF_AUTHORIZING is False
    assert BLOCKS_NEW_ENTRY_DRIFT_STATUS == "NOT_A_CONTRADICTION"
    assert LIVE_RECONCILIATION_PROVEN_DRIFT_STATUS == "NOT_A_CONTRADICTION"
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert THIS_GO_AUTHORIZES_FLATTEN is False
    assert CLASS_D_CONSUMED is False
    assert Z2AP_CONSUMED is False
    assert EXECUTION_READY is False
    assert ATLAS_MUTATION is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert ADDENDUM_ID == (
        "PEAK_TRADE_FULL_AUTONOMY_AI_LAYER_PRE_PERSIST_READ_ONLY_CENSUS_ADDENDUM_V1"
    )
    assert ADDENDUM_CONSUMED is True
    assert PARENT_PERSIST_PLAN_VERDICT == "NEEDS_ADDITIVE_REFINEMENT"
    assert AUTONOMY_ORCHESTRATOR_FOUND is False
    assert CORE_AI_BASED is False
    assert AI_PRODUCTIVE_COMPONENT_COUNT == 0
    assert AI_CAN_DIRECTLY_SUBMIT_ORDER is False
    assert CAN_SYSTEM_AUTONOMOUSLY_TRADE_END_TO_END_TODAY is False
    assert SELF_LEARNING_CLOSED_LOOP_EXISTS == "PARTIAL_OFFLINE_NON_APPLYING"
    assert NO_ORDER_OWNER_GRAPH[0] == "Selection"
    assert NO_ORDER_OWNER_GRAPH[-1].startswith("SimulatedExecutionPort")
    submit = next(row for row in LIVE_VENUE_BRANCH if row["NODE"] == "Venue Submit")
    assert submit["EDGE_TO_NEXT"] == "AUTHORITY_BLOCKED"
    producer = next(row for row in LIVE_VENUE_BRANCH if row["NODE"] == "Nonzero Venue Position")
    assert producer["EDGE_TO_NEXT"] == "MISSING_OR_UNAUTHORIZED_PRODUCER"


def test_census_does_not_treat_08_as_isolated_primary() -> None:
    result = adjudicate_post_z2cz_position_creation_autonomy_semantic_rebind_v1()
    assert result["PREREQUISITE_08_EXPECTS_PREEXISTING_POSITION"] is True
    assert result["BLOCKER_CLASS"] == "ARCHITECTURAL_MISSING_UPSTREAM_SEAM"
    assert result["ADDENDUM_CONSUMED"] is True
    assert result["PARENT_PERSIST_PLAN_VERDICT"] == "NEEDS_ADDITIVE_REFINEMENT"
    assert result["AUTONOMY_ORCHESTRATOR_FOUND"] is False
    assert result["CORE_AI_BASED"] is False
    assert result["AI_CAN_DIRECTLY_SUBMIT_ORDER"] is False
    assert result["TOKENS"]["08_ISOLATED"] == (
        "PREREQUISITE_08_REBOUND_DOWNSTREAM_OF_POSITION_CREATION_SEAM"
    )


def test_reject_isolated_08_and_invented_producer() -> None:
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_08_as_isolated_primary_blocker_v1(treat_08_as_isolated_primary=True)
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_08_creates_position_v1(claimed_08_creates_position=True)
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_invented_position_creation_producer_v1(claimed_producer="FAKE_PRODUCER")
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_identical_get_as_high_value_next_v1(claimed_high_information_get=True)
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_empty_windows_causal_overclaim_v1(
            claimed_never_held=True,
            claimed_zero=False,
            claimed_causal=False,
        )
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_full_autonomy_as_second_core_v1(claimed_second_trading_authority=True)
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        reject_self_learning_self_authorizing_v1(claimed_self_authorizing=True)
    with pytest.raises(LiveCanaryPostZ2czSemanticRebindError):
        adjudicate_post_z2cz_position_creation_autonomy_semantic_rebind_v1(atlas_mutated=True)

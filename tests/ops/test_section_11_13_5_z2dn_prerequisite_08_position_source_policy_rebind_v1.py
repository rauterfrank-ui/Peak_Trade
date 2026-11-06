"""§11.13.5.Z2DN Prerequisite-08 position-source policy rebind. Offline only."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2cz_position_creation_autonomy_semantic_rebind_v1 import (
    POSITION_MUST_BE_CREATED_BY_PEAK_TRADE as Z2DA_POSITION_MUST_BE_CREATED_BY_PEAK_TRADE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    classify_target_position_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_position_source_policy_rebind_v1 import (
    ADJUDICATION,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    EXTERNAL_POSITION_ALLOWED,
    LiveCanaryPrerequisite08PositionSourcePolicyError,
    OWNER_GO,
    OWNER_POLICY_DECISION,
    POSITION_MUST_BE_CREATED_BY_PEAK_TRADE,
    POSITION_SOURCE_IDENTITY_IS_NOT_PART_OF_PREREQUISITE_08_PROPOSITION,
    POSITION_SOURCE_POLICY,
    PREREQUISITE_08_CLOSED,
    PREREQUISITE_08_CREATES_POSITION,
    PREREQUISITE_08_GRANTS_CANARY_AUTHORITY,
    PREREQUISITE_08_GRANTS_EXECUTION_AUTHORITY,
    PREREQUISITE_08_GRANTS_LIVE_AUTHORITY,
    PREREQUISITE_08_GRANTS_POSITION_CREATION_AUTHORITY,
    SOURCE_PROVENANCE_REQUIRED_FOR_PREREQUISITE_08,
    SUPERSESSION_RELATION,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    THIS_SLICE,
    Z2DA_FIELD_HISTORICAL_VALUE,
    Z2DA_TEXT_REWRITTEN,
    adjudicate_prerequisite_08_position_source_policy_v1,
    reject_08_closed_or_nonzero_proof_claim_v1,
    reject_authority_grants_v1,
    reject_classifier_source_injection_v1,
    reject_general_external_position_allowed_claim_v1,
    reject_peak_trade_creation_required_claim_v1,
    reject_z2da_historical_field_rewrite_v1,
)


def test_current_policy_resolves_z2da_without_rewriting_it() -> None:
    assert THIS_SLICE == "11.13.5.Z2DN"
    assert OWNER_POLICY_DECISION == (
        "PEAK_TRADE_OWNER_POLICY_DECISION_PREREQUISITE_08_POSITION_SOURCE_V1"
    )
    assert POSITION_SOURCE_POLICY == ("SOURCE_IRRELEVANT_TO_PREREQUISITE_08_IF_NONZERO_PROVEN")
    assert POSITION_MUST_BE_CREATED_BY_PEAK_TRADE is False
    assert SOURCE_PROVENANCE_REQUIRED_FOR_PREREQUISITE_08 is False
    assert EXTERNAL_POSITION_ALLOWED is False
    assert POSITION_SOURCE_IDENTITY_IS_NOT_PART_OF_PREREQUISITE_08_PROPOSITION is True
    assert PREREQUISITE_08_CREATES_POSITION is False
    assert PREREQUISITE_08_CLOSED is False
    assert PREREQUISITE_08_GRANTS_POSITION_CREATION_AUTHORITY is False
    assert PREREQUISITE_08_GRANTS_EXECUTION_AUTHORITY is False
    assert PREREQUISITE_08_GRANTS_LIVE_AUTHORITY is False
    assert PREREQUISITE_08_GRANTS_CANARY_AUTHORITY is False
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert Z2DA_TEXT_REWRITTEN is False
    assert Z2DA_POSITION_MUST_BE_CREATED_BY_PEAK_TRADE == Z2DA_FIELD_HISTORICAL_VALUE
    assert Z2DA_POSITION_MUST_BE_CREATED_BY_PEAK_TRADE == "UNPROVEN_LEFT_OPEN"
    assert SUPERSESSION_RELATION.startswith("Z2DN_RESOLVES_Z2DA_")
    assert CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY == (
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"
    )
    assert ADJUDICATION.startswith("Z2DA_POSITION_SOURCE_UNPROVEN_LEFT_OPEN_RESOLVED")
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_adjudication_pass_tokens() -> None:
    result = adjudicate_prerequisite_08_position_source_policy_v1()
    assert result["POSITION_SOURCE_POLICY"] == POSITION_SOURCE_POLICY
    assert result["POSITION_MUST_BE_CREATED_BY_PEAK_TRADE"] is False
    assert result["EXTERNAL_POSITION_ALLOWED"] is False
    assert result["PREREQUISITE_08_CLOSED"] is False
    assert result["Z2DA_HISTORICAL_CONSTANT"] == "UNPROVEN_LEFT_OPEN"
    assert result["TOKENS"]["HISTORICAL"] == "Z2DA_HISTORICAL_UNPROVEN_LEFT_OPEN_PRESERVED"
    assert result["TOKENS"]["CLASSIFIER"] == (
        "POSITION_SOURCE_IDENTITY_IS_NOT_PART_OF_PREREQUISITE_08_PROPOSITION"
    )


def test_reject_overclaims() -> None:
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_z2da_historical_field_rewrite_v1(claimed_z2da_rewritten=True)
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_general_external_position_allowed_claim_v1(claimed_external_position_allowed=True)
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_08_closed_or_nonzero_proof_claim_v1(
            claimed_08_closed=True,
            claimed_productive_nonzero_proof=False,
        )
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_authority_grants_v1(claimed_create=True)
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_authority_grants_v1(claimed_get=True)
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_classifier_source_injection_v1(claimed_classifier_requires_source=True)
    with pytest.raises(LiveCanaryPrerequisite08PositionSourcePolicyError):
        reject_peak_trade_creation_required_claim_v1(claimed_peak_trade_required=True)


def test_classifier_still_ignores_source_identity() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": []},
        instrument_id="SUI-USD_UM_XPERP-310404",
    )
    assert classified.state == "TARGET_POSITION_NOT_OBSERVED"
    assert "source" not in classified.to_dict()
    assert SOURCE_PROVENANCE_REQUIRED_FOR_PREREQUISITE_08 is False

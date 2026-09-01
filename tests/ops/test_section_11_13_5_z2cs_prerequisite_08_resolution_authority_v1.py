"""§11.13.5.Z2CS Prerequisite-08 resolution-authority adjudication. Offline only."""

from __future__ import annotations

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    Z2CN_COMMITTED_BODY_SHA256,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_resolution_authority_adjudication_v1 import (
    ABSENT_ROW_08_IMPOSSIBILITY_CLASS,
    ABSENT_ROW_MAKES_08_IMPOSSIBLE,
    ADJUDICATION,
    AUTHORIZED_RESOLUTION_PATH,
    AUTHORIZED_RESOLUTION_PATH_COUNT,
    CAN_08_BE_SATISFIED_WITHOUT_FURTHER_RUNTIME_OBSERVATION,
    CLASS_D_CONSUMED,
    CONTRACT_GAP_CLASS,
    CURRENT_UNCONSUMED_RUNTIME_GO_FOR_RESOLUTION_PATH,
    EMPTY_DATA_IS_ZERO,
    EXECUTION_READY,
    FILTERED_INSTID_GET_IS_NOT_08_RESOLUTION_PATH,
    LAST_CANONICALLY_CLOSED_11_13_5_SLICE,
    LiveCanaryPrerequisite08ResolutionAuthorityError,
    MINIMUM_FUTURE_RUNTIME_AUTHORITY,
    NON_RESOLUTION_PATHS,
    NOT_OBSERVED_EXPOSES_ZERO_SEMANTICS_CONTRACT_GAP_FOR_08,
    OMISSION_OF_INSTRUMENT_ROW_MEANS_ZERO_CANONICAL_RULE,
    OWNER_GO,
    POSITION_QTY_UNIT_STATUS,
    PREREQUISITE_08_REQUIRED_PROPOSITION,
    THIS_GO_AUTHORIZES_FLATTEN,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CR_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE,
    Z2CL_CHOICE_B_IS_NOT_PRE_SEND_08_PATH,
    Z2CR_EMPTY_ENVELOPE_SHA256,
    adjudicate_prerequisite_08_resolution_authority_v1,
    reject_absent_or_empty_as_08_proof_v1,
    reject_non_resolution_path_v1,
)


def test_adjudication_constants_are_fail_closed() -> None:
    assert ADJUDICATION == "RESOLUTION_PATH_ALREADY_EXISTS"
    assert CONTRACT_GAP_CLASS == "NONE"
    assert AUTHORIZED_RESOLUTION_PATH_COUNT == 1
    assert AUTHORIZED_RESOLUTION_PATH.startswith("UNFILTERED_GET_API_V5_ACCOUNT_POSITIONS")
    assert CURRENT_UNCONSUMED_RUNTIME_GO_FOR_RESOLUTION_PATH == "NONE"
    assert EMPTY_DATA_IS_ZERO is False
    assert OMISSION_OF_INSTRUMENT_ROW_MEANS_ZERO_CANONICAL_RULE == "NONE"
    assert POSITION_QTY_UNIT_STATUS == "UNPROVEN"
    assert CAN_08_BE_SATISFIED_WITHOUT_FURTHER_RUNTIME_OBSERVATION is False
    assert ABSENT_ROW_MAKES_08_IMPOSSIBLE is True
    assert ABSENT_ROW_08_IMPOSSIBILITY_CLASS.startswith("PREREQUISITE_DEFINITION_POSITIVE_NONZERO")
    assert NOT_OBSERVED_EXPOSES_ZERO_SEMANTICS_CONTRACT_GAP_FOR_08 is False
    assert FILTERED_INSTID_GET_IS_NOT_08_RESOLUTION_PATH is True
    assert Z2CL_CHOICE_B_IS_NOT_PRE_SEND_08_PATH is True
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert THIS_GO_AUTHORIZES_FLATTEN is False
    assert CLASS_D_CONSUMED is False
    assert EXECUTION_READY is False
    assert LAST_CANONICALLY_CLOSED_11_13_5_SLICE == "SECTION_11_13_5_Z2CR"
    assert THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CR_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE is True
    assert EARLIEST_UNRESOLVED_DEPENDENCY == PREREQUISITE_08_REQUIRED_PROPOSITION
    assert Z2CR_EMPTY_ENVELOPE_SHA256 == Z2CN_COMMITTED_BODY_SHA256
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert "SEPARATE_SCOPED_OWNER_GO" in MINIMUM_FUTURE_RUNTIME_AUTHORITY


def test_empty_unfiltered_payload_is_not_observed_not_08() -> None:
    result = adjudicate_prerequisite_08_resolution_authority_v1(
        positions_payload={"code": "0", "data": [], "msg": ""},
        claimed_body_sha256=Z2CN_COMMITTED_BODY_SHA256,
    )
    assert result["classifier_state"] == TARGET_POSITION_NOT_OBSERVED
    assert result["prerequisite_08_proven"] is False
    assert result["08_PROOF_DENY_TOKEN"] == "HISTORICAL_EMPTY_ENVELOPE_IS_NOT_CURRENT_08_PROOF"
    assert result["empty_data_is_zero"] is False
    assert result["ADJUDICATION"] == "RESOLUTION_PATH_ALREADY_EXISTS"


def test_explicit_zero_row_does_not_satisfy_08() -> None:
    token = reject_absent_or_empty_as_08_proof_v1(
        classifier_state=TARGET_POSITION_ZERO_PROVEN,
    )
    assert token == "ZERO_ROW_DOES_NOT_SATISFY_PREREQUISITE_08"


def test_not_observed_does_not_satisfy_08() -> None:
    token = reject_absent_or_empty_as_08_proof_v1(
        classifier_state=TARGET_POSITION_NOT_OBSERVED,
    )
    assert token == "NOT_OBSERVED_DOES_NOT_SATISFY_PREREQUISITE_08"


def test_window_nonzero_is_not_send_time_or_class_d_proof() -> None:
    token = reject_absent_or_empty_as_08_proof_v1(
        classifier_state=TARGET_POSITION_NONZERO_PROVEN,
    )
    assert token == "WINDOW_NONZERO_IS_NOT_SEND_TIME_OR_CLASS_D_PROOF"


def test_empty_promoted_to_zero_fails_closed() -> None:
    try:
        reject_absent_or_empty_as_08_proof_v1(
            classifier_state=TARGET_POSITION_NOT_OBSERVED,
            empty_data_is_zero_claim=True,
        )
    except LiveCanaryPrerequisite08ResolutionAuthorityError as exc:
        assert str(exc) == "EMPTY_DATA_MUST_NOT_BE_PROMOTED_TO_ZERO"
    else:
        raise AssertionError("expected fail-closed empty-to-zero")


def test_named_non_paths_cannot_resolve_08() -> None:
    assert reject_non_resolution_path_v1(claimed_path=AUTHORIZED_RESOLUTION_PATH) == (
        "CANONICAL_PATH_IDENTIFIED_CURRENT_RUNTIME_GO_NONE"
    )
    for path in NON_RESOLUTION_PATHS:
        token = reject_non_resolution_path_v1(claimed_path=path)
        assert token == f"NOT_AN_08_RESOLUTION_PATH:{path}"
    try:
        reject_non_resolution_path_v1(claimed_path="INVENTED_PATH")
    except LiveCanaryPrerequisite08ResolutionAuthorityError as exc:
        assert str(exc) == "UNKNOWN_CLAIMED_RESOLUTION_PATH"
    else:
        raise AssertionError("expected unknown path fail-closed")

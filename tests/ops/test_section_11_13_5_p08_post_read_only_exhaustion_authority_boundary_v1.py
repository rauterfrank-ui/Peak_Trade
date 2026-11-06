"""P08 post-read-only-exhaustion authority-boundary unit tests. Offline only."""

from __future__ import annotations

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.assemble_v1 import (
    assemble_p08_authority_boundary_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.authority_boundary_v1 import (
    adjudicate_minimum_higher_authority_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.closure_condition_v1 import (
    prove_p08_closure_condition_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    EMPTY_DATA_IS_ZERO,
    EXPECTED_ORIGIN_MAIN_SHA,
    FUTURE_GO_AUTHORIZES_FLATTEN,
    FUTURE_GO_AUTHORIZES_POST,
    MINIMUM_HIGHER_AUTHORITY,
    OWNER_GO,
    P08_NEXT_AUTHORITY_RESULT,
    POST_ALLOWED,
    TARGET_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.mechanism_census_v1 import (
    census_state_appearance_mechanisms_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.readiness_v1 import (
    adjudicate_current_execution_readiness_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.safety_v1 import (
    prove_safety_invariants_v1,
)


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_post() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert FUTURE_GO_AUTHORIZES_POST is False
    assert FUTURE_GO_AUTHORIZES_FLATTEN is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert EMPTY_DATA_IS_ZERO is False


def test_closure_condition_empty_data_does_not_close_p08() -> None:
    proof = prove_p08_closure_condition_v1(positions_payload={"code": "0", "msg": "", "data": []})
    assert proof["P08_CLOSURE_CONDITION_STATUS"] == "PROVEN"
    assert proof["P08_CLOSED"] is False
    assert proof["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert proof["EMPTY_DATA_IS_ZERO"] is False
    assert proof["UNFILTERED_ACCOUNT_POSITIONS_TARGET_ROW_SUFFICIENT"] is True
    assert proof["FILTERED_INSTID_GET_SUFFICIENT"] is False
    assert proof["ROW_MUST_BE_GENERATED_BY_PEAK_TRADE"] is False
    assert proof["TARGET_INSTRUMENT_ID"] == TARGET_INSTRUMENT_ID
    assert "EMPTY_DATA_IS_NOT_ZERO" in proof["FAIL_CLOSED_CONDITIONS"]


def test_mechanism_census_external_only_viable() -> None:
    census = census_state_appearance_mechanisms_v1()
    assert census["STATE_APPEARANCE_MECHANISM_COUNT"] == 15
    assert census["VIABLE_MECHANISM_COUNT"] == 1
    assert census["VIABLE_MECHANISM_IDS"] == ["M02_EXTERNAL_MANUAL_VENUE_UI_POSITION"]
    assert census["TESTNET_CAN_SATISFY_P08"] is False
    assert census["CANARY_FIRST_PARTY_CREATE_CURRENTLY_VIABLE"] is False
    assert census["LIVE_FIRST_PARTY_CREATE_CURRENTLY_VIABLE"] is False
    assert census["PEAK_TRADE_CREATION_REQUIRED_FOR_P08"] is False
    by_id = {row["mechanism_id"]: row for row in census["MECHANISMS"]}
    assert by_id["M06_OKX_EEA_DEMO_TESTNET_EXECUTION"]["disposition"] == "NOT_P08_CAPABLE"
    assert (
        by_id["M04_LIVE_CANARY_MINIMUM_EXPOSURE_ENTRY_SUBMIT"]["currently_viable_for_p08"] is False
    )
    assert by_id["M02_EXTERNAL_MANUAL_VENUE_UI_POSITION"]["currently_viable_for_p08"] is True


def test_readiness_reuses_historical_packs_and_keeps_gates_false() -> None:
    readiness = adjudicate_current_execution_readiness_v1()
    assert readiness["SELECTED_BOUND_TARGET_INSTRUMENT"] == TARGET_INSTRUMENT_ID
    assert readiness["POS_MODE"] == "net_mode"
    assert readiness["LIVE_ENABLED"] is False
    assert readiness["LIVE_ARMED"] is False
    assert readiness["SUBMIT_UNLOCKED"] is False
    assert readiness["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert readiness["GET_PERFORMED_THIS_PERSIST"] is False
    assert readiness["VENUE_NONZERO_CAPACITY"] == "PROVEN_ZERO"
    assert "G_POSMODE_SUBMIT_BODY_UNPROVEN" in readiness["CURRENT_BLOCKERS"]
    assert readiness["OPEN_CONTRADICTIONS"] == []


def test_minimum_authority_is_external_manual_appearance() -> None:
    census = census_state_appearance_mechanisms_v1()
    readiness = adjudicate_current_execution_readiness_v1()
    boundary = adjudicate_minimum_higher_authority_v1(census=census, readiness=readiness)
    assert boundary["P08_NEXT_AUTHORITY_RESULT"] == P08_NEXT_AUTHORITY_RESULT
    assert boundary["MINIMUM_HIGHER_AUTHORITY"] == MINIMUM_HIGHER_AUTHORITY
    assert boundary["REJECTED_TESTNET_BECAUSE_SAFER"] is False
    assert boundary["REJECTED_LIVE_BECAUSE_AVAILABLE_IN_ARCHITECTURE"] is False
    assert boundary["FUNDING_DOES_NOT_CHANGE_MINIMUM_CLASS"] is True


def test_safety_proof_denies_submit_and_flatten() -> None:
    safety = prove_safety_invariants_v1()
    assert safety["NO_ACCIDENTAL_SUBMIT_PATH_UNDER_CURRENT_STATE"] is True
    assert safety["NO_HIDDEN_LIVE_ENABLED_OR_ARMED_MUTATION"] is True
    assert safety["P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS"] is True
    assert safety["NO_SECOND_TRADING_AUTHORITY_INTRODUCED"] is True
    assert "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in safety["FLATTEN_DENY_REASONS"]
    assert any("OWNER_GO_MISMATCH" in reason for reason in safety["SUBMIT_DENY_REASONS"])


def test_assemble_without_persist_is_offline_and_unclosed() -> None:
    result = assemble_p08_authority_boundary_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert result["summary"]["GET_REQUEST_COUNT"] == 0
    assert result["summary"]["POST_COUNT"] == 0
    assert result["summary"]["P08_CLOSED"] is False
    assert result["adjudication"]["P08_NEXT_AUTHORITY_RESULT"] == (
        "EXTERNAL_STATE_APPEARANCE_SUFFICIENT"
    )
    assert result["future_go"]["PEAK_TRADE_POST_AUTHORIZED"] is False
    assert result["future_go"]["SEPARATE_FLATTEN_AUTHORITY_REQUIRED"] is True

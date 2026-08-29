"""§11.13.5.Z2CO flatten-action eligibility contract.

Locks prerequisite 08 as flatten-POST-branch only. NOT_OBSERVED is a
resolved no-action / no-POST branch, not zero and not an unresolved
phase blocker. Offline only. No venue access.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_action_eligibility_v1 import (
    ABSENCE_TO_ZERO_INFERENCE_ALLOWED,
    EQUIVALENT_UNFILTERED_GET_RESOLVES_NOT_OBSERVED,
    FLATTEN_ACTION_BRANCH_NO_ACTION,
    FLATTEN_ACTION_BRANCH_POST,
    FLATTEN_ACTION_BRANCH_UNKNOWN,
    HTTP_OK_IMPLIES_COMPLETENESS,
    NOT_OBSERVED_IS_UNRESOLVED_PHASE_BLOCKER,
    PREREQUISITE_08_FAIL_NOT_NONZERO_POST_BRANCH_ONLY,
    PREREQUISITE_08_IS_FLATTEN_POST_BRANCH_ONLY,
    PREREQUISITE_08_PASS_NONZERO,
    PREREQUISITE_08_UNREACHABLE_UNKNOWN,
    QUERY_COMPLETENESS_PROVEN,
    classify_flatten_action_eligibility_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
)

CURRENT_SUI = "SUI-USD_UM_XPERP-310404"
Z2CO_OWNER_GO = "PEAK_TRADE_POST_Z2CN_MAXIMUM_LEVERAGE_CANONICAL_PROGRESSION_V1"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CO_ELIGIBILITY_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_standing_safety_flags_and_gate_names_unchanged() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert PREREQUISITE_08_IS_FLATTEN_POST_BRANCH_ONLY is True
    assert NOT_OBSERVED_IS_UNRESOLVED_PHASE_BLOCKER is False
    assert ABSENCE_TO_ZERO_INFERENCE_ALLOWED is False
    assert EQUIVALENT_UNFILTERED_GET_RESOLVES_NOT_OBSERVED is False
    assert QUERY_COMPLETENESS_PROVEN is False
    assert HTTP_OK_IMPLIES_COMPLETENESS is False


def test_empty_data_is_no_action_not_zero_and_08_fail_post_only() -> None:
    eligibility = classify_flatten_action_eligibility_v1(
        positions_payload={"code": "0", "data": []},
        instrument_id=CURRENT_SUI,
    )
    assert eligibility.position_state == TARGET_POSITION_NOT_OBSERVED
    assert eligibility.branch == FLATTEN_ACTION_BRANCH_NO_ACTION
    assert eligibility.execution_prerequisite_08_status == (
        PREREQUISITE_08_FAIL_NOT_NONZERO_POST_BRANCH_ONLY
    )
    assert eligibility.flatten_post_candidate_constructable is False
    assert eligibility.unique_actionable_flatten_candidate is False
    assert eligibility.flatten_post_permitted is False
    assert eligibility.target_position_zero_proven is False
    assert eligibility.target_position_nonzero_proven is False
    assert eligibility.query_completeness_proven is False
    assert eligibility.absence_to_zero_inference_allowed is False
    assert eligibility.equivalent_unfiltered_get_resolves_not_observed is False
    assert eligibility.reason == "NO_ACTIONABLE_FLATTEN_CANDIDATE_NOT_OBSERVED_NOT_ZERO"


def test_explicit_zero_row_is_no_action_zero_proven_and_still_no_post() -> None:
    eligibility = classify_flatten_action_eligibility_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "0"}]},
        instrument_id=CURRENT_SUI,
    )
    assert eligibility.position_state == TARGET_POSITION_ZERO_PROVEN
    assert eligibility.branch == FLATTEN_ACTION_BRANCH_NO_ACTION
    assert eligibility.execution_prerequisite_08_status == (
        PREREQUISITE_08_FAIL_NOT_NONZERO_POST_BRANCH_ONLY
    )
    assert eligibility.target_position_zero_proven is True
    assert eligibility.target_position_nonzero_proven is False
    assert eligibility.flatten_post_permitted is False
    assert eligibility.unique_actionable_flatten_candidate is False


def test_nonzero_row_is_post_branch_08_pass_but_post_still_unauthorized() -> None:
    eligibility = classify_flatten_action_eligibility_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "1"}]},
        instrument_id=CURRENT_SUI,
    )
    assert eligibility.position_state == TARGET_POSITION_NONZERO_PROVEN
    assert eligibility.branch == FLATTEN_ACTION_BRANCH_POST
    assert eligibility.execution_prerequisite_08_status == PREREQUISITE_08_PASS_NONZERO
    assert eligibility.flatten_post_candidate_constructable is True
    assert eligibility.unique_actionable_flatten_candidate is True
    assert eligibility.flatten_post_permitted is False
    assert eligibility.target_position_zero_proven is False
    assert eligibility.target_position_nonzero_proven is True


def test_data_none_is_unknown_not_not_observed() -> None:
    eligibility = classify_flatten_action_eligibility_v1(
        positions_payload={"code": "0", "data": None},
        instrument_id=CURRENT_SUI,
    )
    assert eligibility.position_state == TARGET_POSITION_UNKNOWN
    assert eligibility.branch == FLATTEN_ACTION_BRANCH_UNKNOWN
    assert eligibility.execution_prerequisite_08_status == PREREQUISITE_08_UNREACHABLE_UNKNOWN
    assert eligibility.flatten_post_permitted is False
    assert eligibility.target_position_zero_proven is False


def test_missing_payload_is_unknown_not_not_observed() -> None:
    eligibility = classify_flatten_action_eligibility_v1(
        positions_payload=None,
        instrument_id=CURRENT_SUI,
    )
    assert eligibility.position_state == TARGET_POSITION_UNKNOWN
    assert eligibility.branch == FLATTEN_ACTION_BRANCH_UNKNOWN
    assert eligibility.execution_prerequisite_08_status == PREREQUISITE_08_UNREACHABLE_UNKNOWN


def test_this_owner_go_is_not_flatten_execute_authority() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token="I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE",
        purpose="SECTION_11_13_5_FLATTEN_EXECUTE",
        owner_go=Z2CO_OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in reasons
    assert Z2CO_OWNER_GO != FLATTEN_EXECUTE_OWNER_GO_CANONICAL

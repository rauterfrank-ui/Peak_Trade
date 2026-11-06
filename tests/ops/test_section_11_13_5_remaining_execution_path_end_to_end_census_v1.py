"""BOUNDED_RUNTIME_PERMIT_ISSUANCE and remaining-path census evaluation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_runtime_permit_issuance_v1 import (
    NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_MISSING_REMAINING,
    REASON_MISSING_STPR,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_ISSUANCE_CLAIM,
    REASON_STPR_NOT_PASS,
    evaluate_bounded_runtime_permit_issuance_v1,
)
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.remaining_execution_path_census_v1 import (
    START_NODE,
    TERMINAL_EXECUTION_ENDPOINT,
    remaining_execution_path_census_summary_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_position_reobservation_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.adjudicate_v1 import (
    RemainingExecutionPathCensusAdjudicationError,
    adjudicate_remaining_execution_path_end_to_end_census_v1,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    MINIMUM_ADDITIONAL_OWNER_GO_COUNT,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
    WORKPACKAGE_COUNT,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.contract_v1 import (
    SEND_TIME_POSITION_REOBSERVATION_STATUS,
)

TARGET = "SUI-USD_UM_XPERP-310404"


def test_standing_flags_remain_false() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert GET_ALLOWED is False
    assert POST_ALLOWED is False
    assert PRIVATE_AUTH_USED is False
    assert THIS_GO_GET_COUNT == 0
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_named_remaining_after_stpr_stays_frozen() -> None:
    assert NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION == (
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
        "FLATTEN_EXECUTE",
        "NETWORK_SESSION",
    )


def test_named_remaining_after_census() -> None:
    assert NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE == (
        "AUTHENTICATED_PRIVATE_RUNTIME_READ",
        "RUNTIME_PERMIT_ISSUANCE",
        "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
    )
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "AUTHENTICATED_PRIVATE_RUNTIME_READ"
    assert NEXT_AUTHORITY_BOUNDARY == "SEPARATE_OWNER_GO_FOR_AUTHENTICATED_PRIVATE_RUNTIME_READ"
    assert LAST_CANONICALLY_CLOSED_STEP == (
        "SECTION_11_13_5_REMAINING_EXECUTION_PATH_END_TO_END_CENSUS"
    )
    assert THIS_SLICE == "11.13.5.REMAINING_EXECUTION_PATH_END_TO_END_CENSUS"
    assert WORKPACKAGE_COUNT == 3
    assert MINIMUM_ADDITIONAL_OWNER_GO_COUNT == 2


def test_gate_names_include_brpi() -> None:
    assert "BOUNDED_RUNTIME_PERMIT_ISSUANCE" in GATE_NAMES
    assert "SEND_TIME_POSITION_REOBSERVATION" in GATE_NAMES


def test_terminal_endpoint_is_live_flatten_provability() -> None:
    assert START_NODE == "BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    assert TERMINAL_EXECUTION_ENDPOINT == "LIVE_FLATTEN_PROVABILITY_PROVEN"
    summary = remaining_execution_path_census_summary_v1()
    assert summary["TOTAL_REMAINING_NODE_COUNT"] == 17
    assert summary["TOTAL_EDGE_COUNT"] == 19
    assert summary["TOTAL_KNOWN_GAP_COUNT"] == 13
    assert summary["LATENT_OFFLINE_GAPS_CLOSED"] == 4
    assert summary["LATENT_OFFLINE_GAPS_REMAINING"] == 2
    assert summary["RUNTIME_GAPS_REMAINING"] == 7
    assert summary["OWNER_DECISIONS_REMAINING"] == 8


def test_brpi_denies_unproven_stpr_and_runtime_issuance() -> None:
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=None,
        claimed_remaining_after_census=NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert REASON_MISSING_STPR in reasons
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status="UNPROVEN",
        claimed_remaining_after_census=NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert REASON_STPR_NOT_PASS in reasons
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=SEND_TIME_POSITION_REOBSERVATION_STATUS,
        claimed_remaining_after_census=None,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert REASON_MISSING_REMAINING in reasons
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=SEND_TIME_POSITION_REOBSERVATION_STATUS,
        claimed_remaining_after_census=("FLATTEN_EXECUTE",),
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert REASON_REMAINING_MISMATCH in reasons
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=SEND_TIME_POSITION_REOBSERVATION_STATUS,
        claimed_remaining_after_census=NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        runtime_permit_issuance_claim=True,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert REASON_RUNTIME_ISSUANCE_CLAIM in reasons
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=SEND_TIME_POSITION_REOBSERVATION_STATUS,
        claimed_remaining_after_census=NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        flatten_execute_owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert REASON_IMPLEMENTATION_GO_AS_EXECUTE in reasons


def test_matching_brpi_contract_passes_without_runtime_issuance() -> None:
    ok, reasons = evaluate_bounded_runtime_permit_issuance_v1(
        stpr_status=SEND_TIME_POSITION_REOBSERVATION_STATUS,
        claimed_remaining_after_census=NAMED_REMAINING_AFTER_BOUNDED_RUNTIME_PERMIT_ISSUANCE,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
    )
    assert ok is True
    assert reasons == ()


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text
    gate = Path(
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "bounded_runtime_permit_issuance_v1.py"
    ).read_text(encoding="utf-8")
    assert "urlopen" not in gate
    assert "requests" not in gate


def test_live_window_nonzero_advances_to_authenticated_private_runtime_read() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "AUTHENTICATED_PRIVATE_RUNTIME_READ"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(
        RemainingExecutionPathCensusAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        adjudicate_remaining_execution_path_end_to_end_census_v1(origin_main_sha="deadbeef")


def test_adjudication_closes_named_residuals_without_runtime() -> None:
    verdict = adjudicate_remaining_execution_path_end_to_end_census_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] == "PASS_OFFLINE_CONTRACT"
    assert verdict["BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN"] is False
    assert verdict["FLATTEN_EXECUTE"] == "PASS_OFFLINE_CONTRACT"
    assert verdict["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert verdict["NETWORK_SESSION"] == "PASS_OFFLINE_CONTRACT"
    assert verdict["NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["CENSUS_EXHAUSTION_PROVEN"] is True
    assert verdict["TERMINAL_EXECUTION_ENDPOINT"] == "LIVE_FLATTEN_PROVABILITY_PROVEN"
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == "AUTHENTICATED_PRIVATE_RUNTIME_READ"
    assert verdict["POST_PERFORMED"] is False
    assert verdict["GET_PERFORMED_THIS_PERSIST"] is False
    assert verdict["RUNTIME_PERMIT_ISSUED"] is False
    assert verdict["MINIMUM_ADDITIONAL_OWNER_GO_COUNT"] == 2

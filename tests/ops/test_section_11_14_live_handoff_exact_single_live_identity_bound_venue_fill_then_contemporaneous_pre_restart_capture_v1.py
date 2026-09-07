"""Exact-single identity-bound venue-fill then PRE-RESTART capture tests.

Offline only. Does not submit, wire-send, mutate position, restart, GET,
or POST. Historical BOUND_* and TEST_FIXTURE remain inadmissible.
Slice-level contemporaneous productive capture remains false.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_SIDE,
    OWNER_GO_EXECUTE,
    POSITION_COUNT_LIMIT,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    SUI_OPERATIVE_ORDER_SZ,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    OWNER_GO,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    TESTNET_AUTHORIZED,
    THIS_SLICE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    INPUT_CLASS_TEST_FIXTURE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_execute_v1 import (
    AFTER_REPAIR_OWNER_GO_PROPOSED_TOKEN,
    execute_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1 import (
    CASE_ADJUDICATION,
    CODE_GAP_ID,
    LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER,
    PROPOSED_NEXT_SLICE,
    TERMINAL_STATE,
    bind_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1,
    bind_minimal_economic_action_contract_v1,
    census_contemporaneous_live_fill_readiness_matrix_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1 import (
    FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN,
    GATE_NAMES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_current_slice_and_owner_go_match_this_workpackage() -> None:
    assert THIS_SLICE == (
        "11.14.LIVE_HANDOFF_EXACT_SINGLE_LIVE_IDENTITY_BOUND_VENUE_FILL_"
        "THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE"
    )
    assert OWNER_GO.endswith(
        "LIVE_IDENTITY_BOUND_VENUE_FILL_THEN_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_V1"
    )
    assert OWNER_GO == FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN
    assert OWNER_GO != OWNER_GO_EXECUTE
    assert EXPECTED_ORIGIN_MAIN_SHA == "6d25cd2ced346f760db26ca488183b45d19b3d73"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False


def test_bind_proves_code_gap_and_does_not_submit(tmp_path: Path) -> None:
    result = bind_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
        repo_root=REPO_ROOT,
        storage_root=tmp_path,
    )
    assert result["TERMINAL_STATE"] == TERMINAL_STATE
    assert result["TERMINAL_STATE"] == "CODE_GAP_FOUND"
    assert result["CODE_CHANGE_REQUIRED"] is True
    assert result["LIVE_FILL_READINESS"] is False
    assert result["EXACT_ECONOMIC_ACTION_CONTRACT_STATUS"] == "BLOCKED"
    assert result["LIVE_SUBMIT_EXECUTED"] is False
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["POSITION_MUTATION_EXECUTED"] is False
    assert result["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert result["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER"] == (
        LIVE_IDENTITY_BOUND_VENUE_FILL_PRODUCER
    )
    assert result["LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN"] is True
    assert result["CAPTURE_CALLER_ACCEPTS_HISTORICAL_FILL"] is False
    assert result["CAPTURE_CALLER_ACCEPTS_FIXTURE_FILL"] is False
    assert result["CAPTURE_CALLER_ACCEPTS_SYNTHETIC_FILL"] is False
    assert result["OWNER_GO_SCOPE_MATCH"] is True
    assert result["non_execution"]["GET_PERFORMED"] is False
    assert result["non_execution"]["POST_USED"] is False
    assert result["code_gap"]["CODE_GAP_ID"] == CODE_GAP_ID
    assert result["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert result["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE


def test_contemporaneous_matrix_unknown_is_blocking() -> None:
    matrix = census_contemporaneous_live_fill_readiness_matrix_v1()
    assert matrix["LIVE_FILL_READINESS"] is False
    assert matrix["LIVE_FILL_READINESS_MATRIX_STATUS"] == "COMPLETE"
    assert matrix["OWNER_GO_IS_NOT_GATE_BYPASS"] is True
    assert matrix["HISTORICAL_MATRIX_IS_NOT_CONTEMPORANEOUS_PASS"] is True
    by_name = {row["GATE"]: row for row in matrix["rows"]}
    assert tuple(by_name) == GATE_NAMES
    assert by_name["OWNER_EXECUTION_PERMIT"]["GATE_STATUS"] == "PASS"
    assert by_name["LIVE_ENABLED"]["GATE_STATUS"] == "BLOCKED"
    assert by_name["INSTRUMENT_STATE"]["GATE_STATUS"] == "UNKNOWN"
    assert by_name["INSTRUMENT_STATE"]["BLOCKING"] is True
    assert "LIVE_ENABLED" in matrix["BLOCKING_GATES"]
    assert "INSTRUMENT_STATE" in matrix["BLOCKING_GATES"]
    assert matrix["BLOCKING_GATE_COUNT"] >= 24


def test_economic_contract_does_not_estimate_unknown_fields() -> None:
    contract = bind_minimal_economic_action_contract_v1()
    assert contract["EXACT_ECONOMIC_ACTION_CONTRACT_STATUS"] == "BLOCKED"
    assert contract["VENUE"] == REUSED_BINDING_REST_HOST
    assert contract["INSTRUMENT_ID"] == DEFAULT_INSTRUMENT_ID
    assert contract["SIDE"] == DEFAULT_SIDE
    assert contract["ORDER_TYPE"] == DEFAULT_ORDER_TYPE
    assert contract["ORDER_QTY"] == SUI_OPERATIVE_ORDER_SZ
    assert contract["MAX_POSITION_COUNT"] == POSITION_COUNT_LIMIT
    assert contract["EXECUTION_LIMIT_PRICE"] == "UNKNOWN"
    assert contract["EXECUTION_MAX_NOTIONAL"] == "UNKNOWN"
    assert contract["AUTHORIZED_BY_THIS_GO"] is False
    assert contract["EXECUTED"] is False


def test_default_productive_input_remains_unauthorized(tmp_path: Path) -> None:
    result = bind_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
        repo_root=REPO_ROOT,
        storage_root=tmp_path,
    )
    error = result["code_gap"]["semantics"]["DEFAULT_PRODUCTIVE_INPUT_ERROR"]
    assert "RUNTIME_EXECUTION_UNAUTHORIZED" in error
    assert (
        "FIXTURE_FILL_NOT_PRODUCTIVE" in result["code_gap"]["semantics"]["AUTHORIZED_FIXTURE_ERROR"]
    )
    assert (
        "HISTORICAL_EVIDENCE_IS_NOT_CURRENT_RUNTIME"
        in result["code_gap"]["semantics"]["AUTHORIZED_HISTORICAL_ERROR"]
    )
    assert result["code_gap"]["semantics"]["INVOCATION_SCOPED_SEAM_PROVEN"] is True
    assert result["code_gap"]["semantics"]["INVOCATION_SCOPED_SEAM_IS_NOT_LIVE_CAPTURE"] is True
    assert result["code_gap"]["semantics"]["STANDING_RUNTIME_EXECUTION_AUTHORIZED"] is False


def test_hook_default_refuses_productive_input_without_invocation_flag(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
        build_contemporaneous_field_provenance_from_bound_fill_v1,
    )
    from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
        CANONICAL_BOUND_FILL_KIND,
    )
    from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
        ADMISSIBLE_POS_SOURCE_KIND,
    )
    from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
        POS_UNIT,
    )

    identity = {
        "clOrdId": "ptprodidentityclordidseam000002",
        "ordId": "1888000777666555445",
        "instId": "ETH-USD_UM_XPERP-SEAM",
        "posSide": "net",
        "fillSz": "1",
    }
    kwargs = {
        "storage_root": tmp_path,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": identity,
        "peak_trade_owned_resulting_current_position_qty": "1",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": "2026-09-07T18:45:00Z",
        "capture_started_at": "2026-09-07T18:45:01Z",
        "attempt_identity": "unit-default-unauthorized",
        "input_class": INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        "lifecycle_id": "unit-default-unauthorized-lifecycle",
        "field_provenance": build_contemporaneous_field_provenance_from_bound_fill_v1(
            bound_fill_identity=identity,
            peak_trade_owned_resulting_current_position_qty="1",
            lifecycle_id="unit-default-unauthorized-lifecycle",
            input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        ),
    }
    with pytest.raises(Section1114OfflineSurfaceError, match="RUNTIME_EXECUTION_UNAUTHORIZED"):
        run_capture_hook_after_bound_fill_before_restart_v1(**kwargs)
    with pytest.raises(Section1114OfflineSurfaceError, match="FIXTURE_FILL_NOT_PRODUCTIVE"):
        run_capture_hook_after_bound_fill_before_restart_v1(
            **{
                **kwargs,
                "input_class": INPUT_CLASS_TEST_FIXTURE,
                "runtime_execution_authorized": True,
                "field_provenance": build_contemporaneous_field_provenance_from_bound_fill_v1(
                    bound_fill_identity=identity,
                    peak_trade_owned_resulting_current_position_qty="1",
                    lifecycle_id="unit-fixture-rejected-lifecycle",
                    input_class=INPUT_CLASS_TEST_FIXTURE,
                ),
                "lifecycle_id": "unit-fixture-rejected-lifecycle",
            }
        )


def test_execute_remains_non_executing_and_code_gap_terminal(tmp_path: Path) -> None:
    result = execute_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T184500Z-test",
        storage_root=tmp_path,
    )
    summary = result["summary"]
    adjudication = result["adjudication"]
    assert adjudication["TERMINAL_STATE"] == "CODE_GAP_FOUND"
    assert summary["TERMINAL_STATE"] == "CODE_GAP_FOUND"
    assert summary["CODE_CHANGE_REQUIRED"] is True
    assert summary["LIVE_SUBMIT_EXECUTED"] is False
    assert summary["WIRE_SEND_EXECUTED"] is False
    assert summary["POSITION_MUTATION_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["NEXT_SLICE_AUTHORIZED"] is False
    assert summary["REPAIR_MERGE_AUTHORIZED"] is False
    assert summary["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert summary["FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN"] == (
        AFTER_REPAIR_OWNER_GO_PROPOSED_TOKEN
    )
    assert result["raw_exchanges"] == []
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_exact_single_live_identity_bound_venue_fill_then_contemporaneous_pre_restart_capture_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            storage_root=tmp_path,
        )

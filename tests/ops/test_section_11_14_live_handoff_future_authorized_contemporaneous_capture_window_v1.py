"""Future-authorized contemporaneous capture-window adjudication tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_FUTURE_CAPTURE_WINDOW_OWNER_GO,
    HISTORICAL_FUTURE_CAPTURE_WINDOW_SHA,
    LIVE_RESTART_RECONSTRUCTED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_execute_v1 import (
    execute_live_handoff_future_authorized_contemporaneous_capture_window_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    CASE_ADJUDICATION,
    COMPLETE_CAPTURE_SEAM,
    MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE,
    MISSING_PREDICATES,
    PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE,
    PRODUCTIVE_BINDING_IMPLEMENTED,
    PRODUCTIVE_CAPTURE_HOOK_STATUS,
    PRODUCTIVE_CAPTURE_OWNER_STATUS,
    PROPOSED_NEXT_SLICE,
    bind_authorization_surface_matrix_v1,
    bind_bound_fill_semantics_v1,
    bind_capture_window_semantics_v1,
    bind_future_authorized_contemporaneous_capture_window_v1,
    bind_minimum_future_capture_window_v1,
    bind_productive_binding_decision_v1,
    census_productive_runtime_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_productive_runtime_caller_counts_keep_producer_internal() -> None:
    graph = census_productive_runtime_graph_v1(repo_root=REPO_ROOT)
    assert graph["CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_emit_s05_handoff_pos_v1"] == 0
    assert graph["INTERNAL_WRITER_TO_PRODUCER_CALL_PRESENT"] is True
    assert graph["CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME"] is False
    assert graph["PRODUCTIVE_S05_QTY_SOURCE_STATUS"] == "ABSENT"


def test_bound_fill_is_historical_live_venue_fill_not_s05() -> None:
    bound_fill = bind_bound_fill_semantics_v1()
    assert bound_fill["BOUND_FILL_CANONICAL_SYMBOL"] == (
        "LIVE_FILL_OBSERVED_IDENTITY_BOUND_VENUE_FILL"
    )
    assert bound_fill["BOUND_FILL_IS_PRODUCTIVE_RUNTIME_EVENT"] is True
    assert bound_fill["BOUND_FILL_IS_CURRENT_RUNTIME_EVENT"] is False
    assert bound_fill["BOUND_FILL_REQUIRES_VENUE_ACK"] is True
    assert bound_fill["BOUND_FILL_REQUIRES_WIRE_SEND"] is True
    assert bound_fill["BOUND_FILL_CAN_EXIST_OFFLINE"] is False
    assert bound_fill["BOUND_FILL_CAN_EXIST_IN_SHADOW"] is False
    assert bound_fill["BOUND_FILL_CAN_EXIST_IN_TESTNET"] is False
    assert bound_fill["BOUND_FILL_CAN_EXIST_WITHOUT_ORDER_SUBMIT"] is False
    assert bound_fill["FILL_SZ_IS_NOT_S05"] is True
    assert (
        bound_fill["FUTURE_FILL_WITH_NEW_ORDID_IS_IDENTITY_MISMATCH_UNDER_CURRENT_PRODUCER"] is True
    )


def test_capture_window_ordering_remains_unproven() -> None:
    window = bind_capture_window_semantics_v1()
    assert window["CAPTURE_WINDOW_ORDERING"] == "UNPROVEN"
    assert window["BOUND_FILL_TIMESTAMP_LT_CAPTURE_LE_WRITE_LT_RESTART"] == "UNPROVEN"
    assert window["NO_BOUND_FILL_TIMESTAMP_FIELD_ON_HANDOFF_RECORD"] is True
    assert window["CALLER_SUPPLIED_GUARDS_ARE_NOT_PRODUCTIVE_RUNTIME_PROOF"] is True
    assert window["WINDOW_OWNER"] == "ABSENT_NO_PRODUCTIVE_RUNTIME_OWNER"


def test_no_authorization_surface_is_sufficient() -> None:
    surfaces = bind_authorization_surface_matrix_v1()
    assert surfaces["SUFFICIENT_SURFACE_COUNT"] == 0
    live = next(row for row in surfaces["rows"] if row["SURFACE"] == "LIVE_ORDER_CANARY")
    assert live["EXISTS"] is True
    assert live["CAN_PRODUCE_CANONICAL_BOUND_FILL"] is True
    assert live["CAN_OPEN_CANONICAL_CAPTURE_WINDOW"] is False
    assert live["CURRENTLY_AUTHORIZED"] is False
    assert live["SUFFICIENT_FOR_SECTION_11_14_PROOF"] is False
    offline = next(row for row in surfaces["rows"] if row["SURFACE"] == "OFFLINE")
    assert offline["SUFFICIENT_FOR_SECTION_11_14_PROOF"] is False
    testnet = next(row for row in surfaces["rows"] if row["SURFACE"] == "TESTNET")
    assert testnet["SUFFICIENT_FOR_SECTION_11_14_PROOF"] is False


def test_minimum_future_surface_remains_unproven_and_selects_offline_contract() -> None:
    minimum = bind_minimum_future_capture_window_v1()
    assert minimum["MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE"] == MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE
    assert minimum["MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE"] == "UNPROVEN"
    assert minimum["SELECTED_NEXT_VARIANT"] == "OPTION_A"
    assert minimum["SELECTED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE
    assert minimum["LIVE_ENABLED_REQUIRED"] is True
    assert minimum["WIRE_SEND_REQUIRED"] is True
    assert minimum["VENUE_FILL_REQUIRED"] is True
    assert minimum["CURRENT_LIVE_ENABLED"] is False
    assert minimum["CURRENT_CANARY_AUTHORIZED"] is False


def test_productive_binding_is_forbidden_because_owner_and_hook_are_absent() -> None:
    decision = bind_productive_binding_decision_v1()
    assert decision["PRODUCTIVE_CAPTURE_OWNER_STATUS"] == PRODUCTIVE_CAPTURE_OWNER_STATUS
    assert decision["PRODUCTIVE_CAPTURE_HOOK_STATUS"] == PRODUCTIVE_CAPTURE_HOOK_STATUS
    assert decision["PRODUCTIVE_CAPTURE_OWNER_STATUS"] == "ABSENT"
    assert decision["PRODUCTIVE_CAPTURE_HOOK_STATUS"] == "ABSENT"
    assert decision["PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE"] is False
    assert decision["PRODUCTIVE_BINDING_IMPLEMENTED"] is False
    assert "PRODUCTIVE_CAPTURE_OWNER_UNIQUE" in decision["MISSING_PREDICATES"]
    assert "PRODUCTIVE_CAPTURE_HOOK_UNIQUE" in decision["MISSING_PREDICATES"]
    for name in MISSING_PREDICATES:
        assert name in decision["MISSING_PREDICATES"]


def test_slice_adjudication_closes_without_capture_or_restart() -> None:
    adjudication = bind_future_authorized_contemporaneous_capture_window_v1(repo_root=REPO_ROOT)
    assert adjudication["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert adjudication["SELECTED_CAPTURE_TRIGGER"] == REQUIRED_CAPTURE_TRIGGER
    assert adjudication["PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE"] is False
    assert adjudication["PRODUCTIVE_BINDING_IMPLEMENTED"] is False
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == COMPLETE_CAPTURE_SEAM
    assert adjudication["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE is False
    assert PRODUCTIVE_BINDING_IMPLEMENTED is False


def test_execute_is_offline_and_does_not_bind_or_capture() -> None:
    result = execute_live_handoff_future_authorized_contemporaneous_capture_window_v1(
        owner_go=HISTORICAL_FUTURE_CAPTURE_WINDOW_OWNER_GO,
        origin_main_sha=HISTORICAL_FUTURE_CAPTURE_WINDOW_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T062800Z-test",
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE"] is False
    assert summary["PRODUCTIVE_BINDING_IMPLEMENTED"] is False
    assert summary["PRODUCTIVE_CAPTURE_OWNER_STATUS"] == "ABSENT"
    assert summary["PRODUCTIVE_CAPTURE_HOOK_STATUS"] == "ABSENT"
    assert summary["MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE"] == "UNPROVEN"
    assert summary["CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER"] == 0
    assert summary["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert summary["LIVE_RESTART_RECONSTRUCTED"] is False
    assert summary["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert summary["PRODUCTIVE_CAPTURE_WRITE_EXECUTED"] is False
    assert summary["HANDOFF_WRITTEN"] is False
    assert summary["RESTART_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["WIRE_SEND"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["IMPLEMENTATION_AUTHORIZED"] is False
    assert result["raw_exchanges"] == []
    assert result["safety"]["PRODUCTIVE_BINDING_IMPLEMENTED"] is False

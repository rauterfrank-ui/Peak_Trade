"""Productive capture-owner and lifecycle-hook binding tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_OWNER_GO,
    HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SHA,
    LIVE_RESTART_RECONSTRUCTED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_owner_and_lifecycle_hook_binding_execute_v1 import (
    execute_live_handoff_productive_capture_owner_and_lifecycle_hook_binding_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_owner_and_lifecycle_hook_binding_v1 import (
    AUTHORIZED_RUNTIME_SURFACE,
    AUTHORIZED_RUNTIME_SURFACE_PROVEN,
    BINDING_CASE,
    BOUND_FILL_BEFORE_HOOK_PROVEN,
    CASE_ADJUDICATION,
    HOOK_BEFORE_RESTART_PROVEN,
    HOOK_ORDERING_PROVEN,
    MINIMAL_FAIL_CLOSED_BINDING_ALLOWED,
    MISSING_PREDICATES,
    PRODUCTIVE_BINDING_IMPLEMENTED,
    PRODUCTIVE_CAPTURE_OWNER_STATUS,
    PRODUCTIVE_LIFECYCLE_HOOK_STATUS,
    bind_authorization_surface_matrix_v1,
    bind_productive_binding_adjudication_v1,
    bind_productive_capture_owner_and_lifecycle_hook_binding_v1,
    census_productive_capture_owner_candidates_v1,
    census_productive_lifecycle_hook_candidates_v1,
    census_productive_path_graph_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_productive_path_distinguishes_ack_fill_position_and_bound_fill() -> None:
    graph = census_productive_path_graph_v1(repo_root=REPO_ROOT)
    assert graph["PRODUCER_PRODUCTIVE_RUNTIME_CALLER_COUNT"] == 0
    assert graph["CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME"] is False
    assert graph["distinctions"]["ORDER_ACK_IS_NOT_FILL"] is True
    assert graph["distinctions"]["FILL_IS_NOT_POSITION_OBSERVATION"] is True
    assert graph["distinctions"]["POSITION_OBSERVATION_IS_NOT_BOUND_FILL"] is True
    assert graph["distinctions"]["SIMULATED_FILL_IS_NOT_PRODUCTIVE_BOUND_FILL"] is True
    assert graph["distinctions"]["REPLAY_FILL_IS_NOT_LIVE_BOUND_FILL"] is True
    bound = next(stage for stage in graph["stages"] if stage["STAGE_ID"] == "BOUND_FILL")
    ack = next(stage for stage in graph["stages"] if stage["STAGE_ID"] == "VENUE_ACK")
    fill = next(stage for stage in graph["stages"] if stage["STAGE_ID"] == "FILL_EVENT")
    pos = next(stage for stage in graph["stages"] if stage["STAGE_ID"] == "POSITION_OBSERVATION")
    assert bound["IS_CANONICAL_BOUND_FILL"] is True
    assert ack["IS_CANONICAL_BOUND_FILL"] is False
    assert fill["IS_CANONICAL_BOUND_FILL"] is False
    assert pos["IS_CANONICAL_BOUND_FILL"] is False


def test_unique_productive_capture_owner_is_refuted() -> None:
    owner = census_productive_capture_owner_candidates_v1(repo_root=REPO_ROOT)
    assert owner["PRODUCTIVE_CAPTURE_OWNER_STATUS"] == PRODUCTIVE_CAPTURE_OWNER_STATUS
    assert owner["PRODUCTIVE_CAPTURE_OWNER_STATUS"] == "REFUTED"
    assert owner["PRODUCTIVE_CAPTURE_OWNER"] == "NONE"
    assert owner["UNIQUE_OWNER_COUNT"] == 0
    assert owner["OWNER_CANDIDATE_CONFLICT"] is False
    assert owner["STORAGE_OWNER_IS_NOT_PRODUCTIVE_CAPTURE_OWNER"] is True
    asserting = [
        row
        for row in owner["candidates"]
        if row["OWNS_BOUND_FILL_PROVEN_AND_RESTART_NOT_YET_OCCURRED"]
    ]
    assert asserting == []


def test_unique_productive_lifecycle_hook_is_refuted() -> None:
    hook = census_productive_lifecycle_hook_candidates_v1(repo_root=REPO_ROOT)
    assert hook["PRODUCTIVE_LIFECYCLE_HOOK_STATUS"] == PRODUCTIVE_LIFECYCLE_HOOK_STATUS
    assert hook["PRODUCTIVE_LIFECYCLE_HOOK"] == "NONE"
    assert hook["HOOK_ORDERING_PROVEN"] is False
    assert hook["BOUND_FILL_BEFORE_HOOK_PROVEN"] is False
    assert hook["HOOK_BEFORE_RESTART_PROVEN"] is False
    assert hook["UNIQUE_HOOK_COUNT"] == 0


def test_no_currently_authorized_surface_can_fire_the_hook() -> None:
    surfaces = bind_authorization_surface_matrix_v1()
    assert surfaces["AUTHORIZED_RUNTIME_SURFACE"] == AUTHORIZED_RUNTIME_SURFACE
    assert surfaces["AUTHORIZED_RUNTIME_SURFACE"] == "NONE"
    assert surfaces["AUTHORIZED_RUNTIME_SURFACE_PROVEN"] is False
    assert surfaces["SUFFICIENT_SURFACE_COUNT"] == 0
    live = next(row for row in surfaces["rows"] if row["SURFACE"] == "LIVE_ORDER")
    assert live["SURFACE_PRESENT"] is True
    assert live["BOUND_FILL_SEMANTICS_PRODUCTIVE"] is True
    assert live["HOOK_REACHABLE"] is False
    assert live["CURRENTLY_AUTHORIZED"] is False
    offline = next(row for row in surfaces["rows"] if row["SURFACE"] == "OFFLINE")
    assert offline["CURRENTLY_AUTHORIZED"] is True
    assert offline["HOOK_REACHABLE"] is False
    assert offline["BOUND_FILL_SEMANTICS_PRODUCTIVE"] is False


def test_case_b_forbids_productive_binding() -> None:
    decision = bind_productive_binding_adjudication_v1()
    assert decision["BINDING_CASE"] == BINDING_CASE
    assert decision["BINDING_CASE"] == "CASE_B"
    assert decision["MINIMAL_FAIL_CLOSED_BINDING_ALLOWED"] is False
    assert decision["PRODUCTIVE_BINDING_IMPLEMENTED"] is False
    assert "PRODUCTIVE_CAPTURE_OWNER_UNIQUE" in decision["MISSING_PREDICATES"]
    assert "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE" in decision["MISSING_PREDICATES"]
    assert "AUTHORIZED_RUNTIME_SURFACE_PROVEN" in decision["MISSING_PREDICATES"]
    for name in MISSING_PREDICATES:
        assert name in decision["MISSING_PREDICATES"]


def test_slice_adjudication_closes_without_capture_or_restart() -> None:
    adjudication = bind_productive_capture_owner_and_lifecycle_hook_binding_v1(repo_root=REPO_ROOT)
    assert adjudication["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert adjudication["SELECTED_CAPTURE_TRIGGER"] == REQUIRED_CAPTURE_TRIGGER
    assert adjudication["BINDING_CASE"] == "CASE_B"
    assert adjudication["MINIMAL_FAIL_CLOSED_BINDING_ALLOWED"] is False
    assert adjudication["PRODUCTIVE_BINDING_IMPLEMENTED"] is False
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == "UNPROVEN"
    assert adjudication["CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED"] is False
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert MINIMAL_FAIL_CLOSED_BINDING_ALLOWED is False
    assert PRODUCTIVE_BINDING_IMPLEMENTED is False
    assert HOOK_ORDERING_PROVEN is False
    assert BOUND_FILL_BEFORE_HOOK_PROVEN is False
    assert HOOK_BEFORE_RESTART_PROVEN is False
    assert AUTHORIZED_RUNTIME_SURFACE_PROVEN is False


def test_execute_is_offline_and_does_not_bind_or_capture() -> None:
    result = execute_live_handoff_productive_capture_owner_and_lifecycle_hook_binding_v1(
        owner_go=HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_OWNER_GO,
        origin_main_sha=HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T081200Z-test",
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["BINDING_CASE"] == "CASE_B"
    assert summary["MINIMAL_FAIL_CLOSED_BINDING_ALLOWED"] is False
    assert summary["PRODUCTIVE_BINDING_IMPLEMENTED"] is False
    assert summary["PRODUCTIVE_CAPTURE_OWNER_STATUS"] == "REFUTED"
    assert summary["PRODUCTIVE_LIFECYCLE_HOOK_STATUS"] == "REFUTED"
    assert summary["AUTHORIZED_RUNTIME_SURFACE"] == "NONE"
    assert summary["AUTHORIZED_RUNTIME_SURFACE_PROVEN"] is False
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
    assert result["safety"]["MINIMAL_FAIL_CLOSED_BINDING_ALLOWED"] is False

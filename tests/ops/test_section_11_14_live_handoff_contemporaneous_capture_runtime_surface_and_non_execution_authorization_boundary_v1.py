"""Contemporaneous capture runtime-surface and authorization-boundary tests.

Offline only. Does not execute productive Live capture, submit, wire send,
restart, canary, or testnet. TEST_FIXTURE is not productive provenance.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    PRODUCTIVE_HOOK_CALLER,
    build_contemporaneous_field_provenance_from_bound_fill_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    run_live_order_pre_restart_handoff_capture_v1,
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
    build_test_fixture_field_provenance_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_execute_v1 import (
    execute_live_handoff_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1 import (
    CAPTURE_POINT,
    CASE_ADJUDICATION,
    MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    UNAVOIDABLE_EXTERNAL_EFFECTS,
    bind_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1,
    census_gates_v1,
    census_input_preconditions_v1,
    census_productive_entrypoint_candidates_v1,
    census_side_effects_v1,
    census_transitive_capture_callgraph_v1,
    prove_capture_point_timeline_v1,
    prove_non_execution_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_FIXTURE_IDENTITY = {
    "clOrdId": "pttestfixtureclordid000000002",
    "ordId": "1110002223334445557",
    "instId": "ETH-USD_UM_XPERP-FIXTURE-SURFACE",
    "posSide": "net",
    "fillSz": "2",
}


def _fixture_kwargs(tmp_path: Path, **overrides: object) -> dict[str, object]:
    lifecycle_id = "test-fixture-runtime-surface-lifecycle-v1"
    payload: dict[str, object] = {
        "storage_root": tmp_path,
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": dict(TEST_FIXTURE_IDENTITY),
        "peak_trade_owned_resulting_current_position_qty": "2",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": "2026-09-07T16:00:00Z",
        "capture_started_at": "2026-09-07T16:00:01Z",
        "attempt_identity": "test-fixture-runtime-surface-attempt",
        "input_class": INPUT_CLASS_TEST_FIXTURE,
        "lifecycle_id": lifecycle_id,
        "lifecycle_event": REQUIRED_CAPTURE_TRIGGER,
        "field_provenance": build_test_fixture_field_provenance_v1(
            bound_fill_identity=TEST_FIXTURE_IDENTITY,
            lifecycle_id=lifecycle_id,
        ),
    }
    payload.update(overrides)
    return payload


def test_current_slice_and_owner_go_match_this_workpackage() -> None:
    assert THIS_SLICE == (
        "11.14.LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_"
        "NON_EXECUTION_AUTHORIZATION_BOUNDARY"
    )
    assert OWNER_GO.endswith(
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_NON_EXECUTION_AUTHORIZATION_BOUNDARY_V1"
    )
    assert EXPECTED_ORIGIN_MAIN_SHA == "f1ce2505cae738ee88d5ce65e2852fcd4a978cb4"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False


def test_productive_caller_symbol_census_and_reachability() -> None:
    census = census_productive_entrypoint_candidates_v1(repo_root=REPO_ROOT)
    assert census["PRODUCTIVE_HOOK_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert census["PRODUCTIVE_RUNTIME_ENTRYPOINT"] == PRODUCTIVE_RUNTIME_ENTRYPOINT
    assert census["CANARY_EXECUTE_INVOKES_CAPTURE"] is False
    assert census["CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE"] is False
    assert census["HOST_JOIN_PRODUCTIVE_CALLER_COUNT"] == 0
    assert census["UNIQUE_PRODUCTIVE_CALLER_OF_HOOK_COUNT"] == 1
    assert census["CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME"] is False
    classifications = {row["ENTRYPOINT_SYMBOL"]: row["CLASSIFICATION"] for row in census["rows"]}
    assert classifications[PRODUCTIVE_RUNTIME_ENTRYPOINT] == "DECLARED"
    assert classifications[PRODUCTIVE_HOOK_CALLER] == "PRODUCTIVE_REACHABLE"
    assert classifications["run_section_11_13_5_live_canary_minimum_exposure_v1"] == (
        "PRODUCTIVE_REACHABLE"
    )
    assert classifications["prove_offline_capture_roundtrip_v1"] == "OFFLINE_ONLY"


def test_transitive_callgraph_and_irreversible_predecessor() -> None:
    graph = census_transitive_capture_callgraph_v1(repo_root=REPO_ROOT)
    assert graph["TRANSITIVE_CALLGRAPH_COMPLETE"] is True
    assert graph["PRODUCTIVE_CAPTURE_CALLER"] == PRODUCTIVE_HOOK_CALLER
    assert graph["CAPTURE_POINT"] == CAPTURE_POINT
    assert graph["IRREVERSIBLE_EFFECT_BEFORE_CAPTURE_CALLER"] == ("LIVE_IDENTITY_BOUND_VENUE_FILL")
    symbols = [row["SYMBOL"] for row in graph["nodes"]]
    assert PRODUCTIVE_RUNTIME_ENTRYPOINT in symbols
    assert PRODUCTIVE_HOOK_CALLER in symbols
    assert "commit_handoff_after_bound_fill_before_restart_v1" in symbols
    assert "SupervisorLifecycle.restart" in symbols


def test_capture_point_temporal_ordering() -> None:
    timeline = prove_capture_point_timeline_v1()
    assert timeline["UNDERLYING_FILL_ALREADY_EXTERNALLY_EXECUTED"] is True
    assert timeline["BOUND_FILL_ONLY_AFTER_SUCCESSFUL_EXCHANGE_FILL"] is True
    assert timeline["CAPTURE_RELATIVE_TO_ORDER_SUBMIT"] == "AFTER"
    assert timeline["CAPTURE_RELATIVE_TO_FILL_CONFIRMATION"] == "AFTER"
    assert (
        timeline["PRODUCTIVE_CONTEMPORANEOUS_CAPTURE_REQUIRES_PRIOR_LIVE_OR_VENUE_ACTION"] is True
    )
    ids = [row["ID"] for row in timeline["steps"]]
    assert ids.index("T3") < ids.index("CAPTURE_POINT")
    assert ids.index("CAPTURE_POINT") < ids.index("Tn")
    assert timeline["steps"][ids.index("T1")]["REQUIRED_FOR_CAPTURE"] is True
    assert timeline["steps"][ids.index("Tn")]["REQUIRED_FOR_CAPTURE"] is False


def test_side_effect_and_gate_and_input_censuses() -> None:
    effects = census_side_effects_v1(repo_root=REPO_ROOT)
    assert effects["SIDE_EFFECT_CENSUS_COMPLETE"] is True
    assert effects["CAPTURE_SURFACE_NETWORK_IMPORTS"] == []
    assert effects["UNAVOIDABLE_EXTERNAL_EFFECTS"] == UNAVOIDABLE_EXTERNAL_EFFECTS
    names = {row["EFFECT"] for row in effects["rows"]}
    assert "EXCHANGE_SUBMIT" in names
    assert "FILESYSTEM_WRITE" in names
    assert "RESTART" in names
    gates = census_gates_v1()
    assert gates["GATE_CENSUS_COMPLETE"] is True
    assert gates["GATE_MUTATION_PERFORMED"] is False
    gate_names = {row["GATE_NAME"] for row in gates["rows"]}
    assert "LIVE_ENABLED" in gate_names
    assert "HOOK_INPUT_CLASS_TEST_FIXTURE_ONLY" in gate_names
    inputs = census_input_preconditions_v1()
    assert inputs["INPUT_PRECONDITION_CENSUS_COMPLETE"] is True
    assert inputs["TEST_FIXTURE_IS_NOT_PRODUCTIVE_PROVENANCE"] is True
    productive_valid = [
        row["VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE"] for row in inputs["rows"]
    ]
    assert True not in productive_valid


def test_fixture_is_not_productive_contemporaneous_evidence(tmp_path: Path) -> None:
    result = run_live_order_pre_restart_handoff_capture_v1(**_fixture_kwargs(tmp_path))
    assert result["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert result["hook_result"]["INPUT_CLASS"] == INPUT_CLASS_TEST_FIXTURE
    assert result["hook_result"]["TEST_FIXTURE"] is True


def test_productive_input_class_remains_unauthorized(tmp_path: Path) -> None:
    lifecycle_id = "productive-input-unauthorized-lifecycle"
    provenance = build_contemporaneous_field_provenance_from_bound_fill_v1(
        bound_fill_identity=TEST_FIXTURE_IDENTITY,
        peak_trade_owned_resulting_current_position_qty="2",
        lifecycle_id=lifecycle_id,
        input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    )
    kwargs = _fixture_kwargs(
        tmp_path,
        input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        lifecycle_id=lifecycle_id,
        field_provenance=provenance,
    )
    hook_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key not in {"lifecycle_event", "capture_adapter", "capture_owner"}
    }
    with pytest.raises(Section1114OfflineSurfaceError, match="RUNTIME_EXECUTION_UNAUTHORIZED"):
        run_capture_hook_after_bound_fill_before_restart_v1(**hook_kwargs)


def test_non_execution_and_isolation_adjudication(tmp_path: Path) -> None:
    proof = prove_non_execution_v1(repo_root=REPO_ROOT, storage_root=tmp_path)
    assert proof["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert proof["LIVE_SUBMIT_EXECUTED"] is False
    assert proof["WIRE_SEND_EXECUTED"] is False
    assert proof["RESTART_EXECUTED"] is False
    assert proof["HOST_CRASH_EXECUTED"] is False
    assert proof["TESTNET_EXECUTED"] is False
    assert proof["CANARY_EXECUTED"] is False
    assert proof["PRODUCTIVE_INPUT_CLASS_REJECTED"] is True
    adjudication = (
        bind_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1(
            repo_root=REPO_ROOT,
            storage_root=tmp_path,
        )
    )
    assert adjudication["CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE"] == "PROVEN"
    assert adjudication["CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY"] == "PROVEN"
    assert adjudication["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is False
    assert adjudication["CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE"] is True
    assert adjudication["MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT"] == (
        MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT
    )
    assert adjudication["COMPLETE_CAPTURE_SEAM"] == "PROVEN"
    assert adjudication["PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"] is True
    assert adjudication["CASE_ADJUDICATION"] == CASE_ADJUDICATION


def test_execute_is_offline_and_does_not_claim_productive_capture(tmp_path: Path) -> None:
    result = execute_live_handoff_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T160000Z-test",
        storage_root=tmp_path,
    )
    summary = result["summary"]
    assert summary["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert summary["COMPLETE_CAPTURE_SEAM"] == "PROVEN"
    assert summary["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is False
    assert summary["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert summary["LIVE_SUBMIT_EXECUTED"] is False
    assert summary["WIRE_SEND_EXECUTED"] is False
    assert summary["RESTART_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert result["raw_exchanges"] == []
    assert result["safety"]["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is False

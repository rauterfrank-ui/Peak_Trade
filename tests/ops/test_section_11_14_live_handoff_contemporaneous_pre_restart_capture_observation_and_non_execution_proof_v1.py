"""Contemporaneous PRE-RESTART capture observation and non-execution proof tests.

Offline only. Does not execute productive Live capture, submit, wire send,
restart, canary, or testnet. Does not treat TEST_FIXTURE as productive
provenance. Does not backfill or synthesize a capture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    PRODUCTIVE_HOOK_CALLER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO,
    HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_execute_v1 import (
    execute_live_handoff_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1 import (
    AUTHORIZATION_MATRIX_STATUS,
    CASE_ADJUDICATION,
    CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION,
    EFFECT_NAMES,
    PROPOSED_NEXT_SLICE,
    adjudicate_observation_admissibility_v1,
    build_authorization_matrix_v1,
    census_required_runtime_state_v1,
    prove_capture_was_not_executed_v1,
    reprove_productive_capture_call_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_historical_slice_owner_go_and_gates_remain_bound() -> None:
    assert HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO.endswith(
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_AND_NON_EXECUTION_PROOF_V1"
    )
    assert HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA == (
        "d0f5afc4c119aef4b9e2a6c18ca7acbca570dfd7"
    )
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False


def test_call_path_reproof_reproves_isolation_false() -> None:
    call_path = reprove_productive_capture_call_path_v1(repo_root=REPO_ROOT)
    assert call_path["CAPTURE_OWNER"] == PRODUCTIVE_CAPTURE_OWNER
    assert call_path["CAPTURE_LIFECYCLE_HOOK"] == PRODUCTIVE_LIFECYCLE_HOOK
    assert call_path["PRODUCTIVE_CALLER_COUNT"] == 1
    assert call_path["PRODUCTIVE_CALLERS"] == (PRODUCTIVE_HOOK_CALLER,)
    assert call_path["PRE_RESTART_CALL_SITE"].endswith(PRODUCTIVE_HOOK_CALLER)
    assert call_path["CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_REPROVEN"] == "PROVEN"
    assert call_path["CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY_REPROVEN"] == "PROVEN"
    assert call_path["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is False
    assert call_path["CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE"] is True
    assert call_path["entrypoints"]["UNIQUE_PRODUCTIVE_CALLER_OF_HOOK_COUNT"] == 1
    assert call_path["entrypoints"]["HOST_JOIN_PRODUCTIVE_CALLER_COUNT"] == 0
    assert call_path["entrypoints"]["CANARY_EXECUTE_INVOKES_CAPTURE"] is False
    assert call_path["entrypoints"]["CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE"] is False


def test_authorization_matrix_covers_all_bound3_effects_and_forbids_non_capture() -> None:
    matrix = build_authorization_matrix_v1()
    assert matrix["AUTHORIZATION_MATRIX_STATUS"] == AUTHORIZATION_MATRIX_STATUS
    assert matrix["NON_CAPTURE_SIDE_EFFECTS_AUTHORIZED"] is False
    names = tuple(row["EFFECT"] for row in matrix["rows"])
    assert names == EFFECT_NAMES
    by_name = {row["EFFECT"]: row for row in matrix["rows"]}
    capture = by_name["CAPTURE_PERSIST"]
    assert capture["AUTHORIZED_BY_THIS_OWNER_GO"] is True
    assert capture["MAY_OCCUR_THIS_WORKPACKAGE"] is False
    for name in EFFECT_NAMES:
        if name == "CAPTURE_PERSIST":
            continue
        row = by_name[name]
        assert row["AUTHORIZED_BY_THIS_OWNER_GO"] is False
        assert row["MAY_OCCUR_THIS_WORKPACKAGE"] is False
        assert row["STATUS"] == "NOT_AUTHORIZED"


def test_observation_admissibility_fails_closed_on_all_four_conjuncts(tmp_path: Path) -> None:
    admissibility = adjudicate_observation_admissibility_v1(
        repo_root=REPO_ROOT,
        storage_root=tmp_path,
    )
    assert admissibility["ADMISSIBLE"] is False
    assert admissibility["CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION"] == "NOT_EXECUTED"
    assert admissibility["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert admissibility["OWNER_GO_IS_NOT_GATE_BYPASS"] is True
    assert admissibility["BACKFILL_USED"] is False
    assert admissibility["RETROACTIVE_SYNTHESIS_USED"] is False
    answers = {row["ID"]: row for row in admissibility["conjuncts"]}
    assert set(answers) == {"A", "B", "C", "D"}
    for row in admissibility["conjuncts"]:
        assert row["ANSWER"] is False
        assert row["PROVABLE"] is True
        assert str(row["BLOCKER"]).strip() != ""
    state = census_required_runtime_state_v1(repo_root=REPO_ROOT)
    assert state["LIVE_ENABLED"] is False
    assert state["LIVE_ARMED"] is False
    assert state["CURRENT_PROCESS_HAS_CONTEMPORANEOUS_BOUND_FILL"] is False
    assert state["PRODUCTIVE_DURABLE_HANDOFF_PRESENT"] is False
    assert state["HOOK_REJECTS_PRODUCTIVE_BOUND_FILL_INPUT"] is True


def test_non_execution_proof_does_not_synthesize_or_submit(tmp_path: Path) -> None:
    proof = prove_capture_was_not_executed_v1(repo_root=REPO_ROOT, storage_root=tmp_path)
    assert proof["CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION"] == "NOT_EXECUTED"
    assert proof["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert proof["CAPTURE_TIMESTAMP"] is None
    assert proof["CAPTURE_ARTIFACT_ID"] is None
    assert proof["CAPTURE_ARTIFACT_HASH"] is None
    assert proof["CAPTURE_PROVENANCE_VALIDATED"] is False
    assert proof["BACKFILL_USED"] is False
    assert proof["RETROACTIVE_SYNTHESIS_USED"] is False
    assert proof["LIVE_SUBMIT_EXECUTED"] is False
    assert proof["WIRE_SEND_EXECUTED"] is False
    assert proof["RESTART_EXECUTED"] is False
    assert proof["CRASH_INJECTION_EXECUTED"] is False
    assert proof["POSITION_MUTATION_EXECUTED"] is False
    assert proof["LIVE_ENABLED_MUTATED"] is False
    assert proof["LIVE_ARMED_MUTATED"] is False
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False
    assert proof["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert proof["INPUT_CLASS_PRODUCTIVE_REJECTED"] is True


def test_bind_and_execute_close_observation_as_not_executed(tmp_path: Path) -> None:
    result = execute_live_handoff_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1(
        owner_go=HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_OWNER_GO,
        origin_main_sha=HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T171500Z-test",
        storage_root=tmp_path,
    )
    summary = result["summary"]
    adjudication = result["adjudication"]
    assert adjudication["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert adjudication["CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION"] == (
        CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
    )
    assert adjudication["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is False
    assert adjudication["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert adjudication["LIVE_RESTART_RECONSTRUCTED"] is False
    assert adjudication["HOST_CRASH_DURABILITY"] == "UNPROVEN"
    assert adjudication["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE
    assert summary["CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION"] == "NOT_EXECUTED"
    assert summary["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert summary["LIVE_SUBMIT_EXECUTED"] is False
    assert summary["WIRE_SEND_EXECUTED"] is False
    assert summary["RESTART_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert result["raw_exchanges"] == []
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_live_handoff_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1(
            owner_go="WRONG",
            origin_main_sha=HISTORICAL_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_SHA,
            repo_root=REPO_ROOT,
            storage_root=tmp_path,
        )

"""LIVE_IDENTITY_BOUND_VENUE_FILL readiness and exact execution contract tests.

Offline only. Does not submit, wire-send, mutate position, restart, GET,
POST, or consume a future execution Owner-GO. Does not treat historical
BOUND_* or TEST_FIXTURE as a current Live fill.
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
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    INPUT_CLASS_TEST_FIXTURE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_execute_v1 import (
    execute_live_handoff_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1 import (
    CASE_ADJUDICATION,
    FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN,
    GATE_NAMES,
    PROPOSED_NEXT_SLICE,
    SIDE_EFFECT_NAMES,
    bind_future_execution_owner_go_contract_v1,
    bind_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1,
    bind_minimal_economic_action_contract_v1,
    census_execution_side_effect_graph_v1,
    census_live_fill_readiness_matrix_v1,
    prove_fill_producer_call_path_v1,
    prove_fixture_is_not_live_fill_v1,
    prove_historical_fill_is_not_current_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_current_slice_and_owner_go_match_this_workpackage() -> None:
    assert THIS_SLICE == (
        "11.14.LIVE_HANDOFF_LIVE_IDENTITY_BOUND_VENUE_FILL_READINESS_AND_EXACT_EXECUTION_CONTRACT"
    )
    assert OWNER_GO.endswith(
        "LIVE_IDENTITY_BOUND_VENUE_FILL_READINESS_AND_EXACT_EXECUTION_CONTRACT_V1"
    )
    assert OWNER_GO != OWNER_GO_EXECUTE
    assert EXPECTED_ORIGIN_MAIN_SHA == "f0b2cb34d60d2404edbb90a6a025f69534bbe6b1"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert LIVE_RESTART_RECONSTRUCTED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False


def test_readiness_proof_does_not_submit_or_wire_send(tmp_path: Path) -> None:
    result = bind_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1(
        repo_root=REPO_ROOT,
        storage_root=tmp_path,
    )
    assert result["LIVE_FILL_EXECUTION_AUTHORIZED"] is False
    assert result["LIVE_FILL_EXECUTED"] is False
    assert result["LIVE_SUBMIT_EXECUTED"] is False
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["POSITION_MUTATION_EXECUTED"] is False
    assert result["non_execution"]["GET_PERFORMED"] is False
    assert result["non_execution"]["POST_USED"] is False
    assert result["non_execution"]["WIRE_SEND"] is False
    for row in result["side_effects"]["rows"]:
        assert row["CURRENTLY_AUTHORIZED"] is False
    for row in result["readiness_matrix"]["rows"]:
        assert row["MUTATION_AUTHORIZED_BY_THIS_GO"] is False


def test_no_gate_bypass_and_missing_freshness_blocks() -> None:
    matrix = census_live_fill_readiness_matrix_v1()
    assert matrix["LIVE_FILL_READINESS"] is False
    assert matrix["THIS_GO_IS_NOT_GATE_BYPASS"] is True
    assert matrix["BLOCKING_GATE_COUNT"] >= 1
    by_name = {row["GATE"]: row for row in matrix["rows"]}
    assert tuple(by_name) == GATE_NAMES
    for name in (
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "CANARY_AUTHORIZED",
        "RUNTIME_EXECUTION_AUTHORIZED",
        "OWNER_EXECUTION_PERMIT",
        "SESSION_AUTH",
        "PRIVATE_GET_AUTH",
        "INSTRUMENT_STATE",
        "EXISTING_POSITION_STATE",
        "WIRE_SEND_GATE",
    ):
        assert by_name[name]["SATISFIED"] is False
        assert by_name[name]["BLOCKING"] is True
        assert by_name[name]["MUTATION_AUTHORIZED_BY_THIS_GO"] is False
    stale = [row for row in matrix["rows"] if row["FRESHNESS"] == "NO_CURRENT_GET"]
    assert stale
    for row in stale:
        assert row["SATISFIED"] is False


def test_historical_fill_is_not_current_fill_evidence() -> None:
    rejection = prove_historical_fill_is_not_current_v1(
        candidate={
            "ordId": BOUND_ORDID,
            "clOrdId": BOUND_CLORDID,
            "instId": BOUND_INSTID,
        }
    )
    assert rejection["HISTORICAL_BOUND_FILL_IS_CURRENT_FILL"] is False
    assert rejection["HISTORICAL_BOUND_FILL_ADMISSIBLE_AS_CONTEMPORANEOUS_CAPTURE_INPUT"] is False


def test_fixture_is_not_live_fill() -> None:
    rejection = prove_fixture_is_not_live_fill_v1(input_class=INPUT_CLASS_TEST_FIXTURE)
    assert rejection["TEST_FIXTURE_IS_LIVE_FILL"] is False
    assert rejection["TEST_FIXTURE_ADMISSIBLE_AS_PRODUCTIVE_CONTEMPORANEOUS_CAPTURE_INPUT"] is False
    with pytest.raises(Section1114OfflineSurfaceError, match="PRODUCTIVE_FILL_INPUT_MUST_REMAIN"):
        prove_fixture_is_not_live_fill_v1(input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT)


def test_future_execution_contract_is_fail_closed_and_max_one_economic_action() -> None:
    future = bind_future_execution_owner_go_contract_v1()
    assert future["CONSUMED_BY_THIS_GO"] is False
    assert future["FAIL_CLOSED"] is True
    assert future["NEXT_SLICE_AUTHORIZED"] is False
    assert future["FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN"] == (
        FUTURE_EXECUTION_OWNER_GO_PROPOSED_TOKEN
    )
    assert future["bindings"]["MAX_ORDERS"] == 1
    assert future["bindings"]["MAX_QUANTITY"] == SUI_OPERATIVE_ORDER_SZ
    assert future["bindings"]["MAX_POSITIONS"] == 1
    assert future["bindings"]["SECOND_POSITION"] is False
    assert future["bindings"]["RETRY_WITH_ECONOMIC_DUPLICATION"] is False
    assert future["bindings"]["GATE_BYPASS"] is False
    effects = census_execution_side_effect_graph_v1()
    assert effects["MAX_ECONOMIC_ACTIONS_IF_LATER_AUTHORIZED"] == 1
    assert tuple(row["EFFECT"] for row in effects["rows"]) == SIDE_EFFECT_NAMES


def test_fill_producer_call_path_is_proven_and_not_joined_from_execute() -> None:
    producer = prove_fill_producer_call_path_v1(repo_root=REPO_ROOT)
    assert producer["LIVE_IDENTITY_BOUND_VENUE_FILL_REQUIRED"] is True
    assert producer["LIVE_IDENTITY_BOUND_VENUE_FILL_CALL_PATH_PROVEN"] is True
    assert producer["CANARY_EXECUTE_INVOKES_CAPTURE"] is False
    assert producer["CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE"] is False
    assert producer["HISTORICAL_BOUND_FILL_ADMISSIBLE"] is False
    ids = [row["id"] for row in producer["nodes"]]
    assert ids[0] == "SELECTED_BOUND_INSTRUMENT"
    assert ids[-1] == "CAPTURE_OWNER"
    assert "LIVE_IDENTITY_BOUND_VENUE_FILL" in ids


def test_economic_contract_does_not_estimate_unknown_fields() -> None:
    contract = bind_minimal_economic_action_contract_v1()
    assert contract["MINIMAL_ECONOMIC_ACTION_CONTRACT_STATUS"] == "BLOCKED"
    assert contract["VENUE"] == REUSED_BINDING_REST_HOST
    assert contract["INSTRUMENT_ID"] == DEFAULT_INSTRUMENT_ID
    assert contract["SIDE"] == DEFAULT_SIDE
    assert contract["ORDER_TYPE"] == DEFAULT_ORDER_TYPE
    assert contract["ORDER_QTY"] == SUI_OPERATIVE_ORDER_SZ
    assert contract["MAX_POSITION_COUNT"] == POSITION_COUNT_LIMIT
    assert contract["EXPECTED_MAX_NOTIONAL"] == "UNKNOWN"
    assert contract["PRICE_OR_PRICE_POLICY"] == "UNKNOWN"
    assert contract["LEVERAGE"] == "UNKNOWN"
    assert contract["AUTHORIZED_BY_THIS_GO"] is False
    assert contract["EXECUTED"] is False


def test_bind_and_execute_remain_non_executing(tmp_path: Path) -> None:
    result = execute_live_handoff_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        run_id="20260907T181000Z-test",
        storage_root=tmp_path,
    )
    summary = result["summary"]
    adjudication = result["adjudication"]
    assert adjudication["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert adjudication["LIVE_FILL_READINESS"] is False
    assert adjudication["LIVE_FILL_EXECUTION_AUTHORIZED"] is False
    assert adjudication["PROPOSED_NEXT_SLICE"] == PROPOSED_NEXT_SLICE
    assert summary["LIVE_SUBMIT_EXECUTED"] is False
    assert summary["WIRE_SEND_EXECUTED"] is False
    assert summary["POSITION_MUTATION_EXECUTED"] is False
    assert summary["GET_PERFORMED"] is False
    assert summary["POST_USED"] is False
    assert summary["LIVE_ACTION"] == "NONE"
    assert summary["NEXT_SLICE_AUTHORIZED"] is False
    assert result["raw_exchanges"] == []
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_live_handoff_live_identity_bound_venue_fill_readiness_and_exact_execution_contract_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            storage_root=tmp_path,
        )

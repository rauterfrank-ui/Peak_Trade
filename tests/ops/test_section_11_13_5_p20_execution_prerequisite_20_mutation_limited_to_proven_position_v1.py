"""P20 EXECUTION_PREREQUISITE_20 mutation-limited-to-proven-position tests. Offline only."""

from __future__ import annotations

from pathlib import Path

import pytest

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.mutation_limited_to_proven_position_v1 import (
    REASON_INSTRUMENT_MISMATCH,
    REASON_LIVE_AUTHORIZED_SUBSTITUTE,
    REASON_MUTATION_BODY_MISSING,
    REASON_NO_PROVEN_POSITION,
    REASON_OVERSIZE,
    REASON_PARTIAL,
    REASON_SIDE_MISMATCH,
    REASON_ZERO_POSITION,
    evaluate_mutation_limited_to_proven_position_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.adjudicate_v1 import (
    P20MutationLimitedToProvenPositionAdjudicationError,
    adjudicate_execution_prerequisite_20_mutation_limited_to_proven_position_v1,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P16_CLOSED,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)

TARGET = "SUI-USD_UM_XPERP-310404"


def _body(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "clOrdId": "pt20offline0000000000000001",
        "instId": TARGET,
        "side": "SELL",
        "ordType": "limit",
        "sz": "1",
        "tdMode": "cross",
        "px": "0.8209",
        "reduceOnly": True,
    }
    payload.update(overrides)
    return payload


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_runtime() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert GET_ALLOWED is False
    assert PRIVATE_AUTH_USED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert THIS_SLICE == "11.13.5.P20"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P20"
    assert P16_CLOSED is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == (
        "EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED"
    )
    assert NEXT_AUTHORITY_BOUNDARY == (
        "SEPARATE_OWNER_GO_FOR_EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED"
    )
    assert "MUTATION_LIMITED_TO_PROVEN_POSITION" in GATE_NAMES


def test_missing_zero_partial_oversize_side_and_instrument_deny() -> None:
    missing_ok, missing = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": []},
        instrument_id=TARGET,
        mutation_body=_body(),
    )
    assert missing_ok is False
    assert REASON_NO_PROVEN_POSITION in missing
    zero_ok, zero = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "0"}]},
        instrument_id=TARGET,
        mutation_body=_body(),
    )
    assert zero_ok is False
    assert REASON_ZERO_POSITION in zero
    none_ok, none_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        instrument_id=TARGET,
        mutation_body=None,
    )
    assert none_ok is False
    assert REASON_MUTATION_BODY_MISSING in none_reasons
    inst_ok, inst_reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        instrument_id=TARGET,
        mutation_body=_body(instId="BTC-USD_UM_XPERP-000000"),
    )
    assert inst_ok is False
    assert REASON_INSTRUMENT_MISMATCH in inst_reasons
    partial_ok, partial = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        instrument_id=TARGET,
        mutation_body=_body(sz="0.5"),
    )
    assert partial_ok is False
    assert REASON_PARTIAL in partial
    oversize_ok, oversize = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        instrument_id=TARGET,
        mutation_body=_body(sz="2"),
    )
    assert oversize_ok is False
    assert REASON_OVERSIZE in oversize
    side_ok, side = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        instrument_id=TARGET,
        mutation_body=_body(side="BUY"),
    )
    assert side_ok is False
    assert REASON_SIDE_MISMATCH in side


def test_live_authorized_cannot_substitute_for_missing_proven_position() -> None:
    ok, reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": []},
        instrument_id=TARGET,
        mutation_body=None,
        live_authorized_claim=True,
    )
    assert ok is False
    assert REASON_NO_PROVEN_POSITION in reasons
    assert REASON_LIVE_AUTHORIZED_SUBSTITUTE in reasons


def test_matching_mutation_passes_without_being_runtime_mutation() -> None:
    ok, reasons = evaluate_mutation_limited_to_proven_position_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        instrument_id=TARGET,
        mutation_body=_body(),
    )
    assert ok is True
    assert reasons == ()
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text
    gate = Path(
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "mutation_limited_to_proven_position_v1.py"
    ).read_text(encoding="utf-8")
    assert "urlopen" not in gate
    assert "requests" not in gate


def test_live_window_nonzero_advances_to_send_time_pass() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "SEND_TIME_PASS_18_19_21_24"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(
        P20MutationLimitedToProvenPositionAdjudicationError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        adjudicate_execution_prerequisite_20_mutation_limited_to_proven_position_v1(
            origin_main_sha="deadbeef"
        )


def test_adjudication_closes_named_p20_contract_without_runtime() -> None:
    verdict = adjudicate_execution_prerequisite_20_mutation_limited_to_proven_position_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict["EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"] == (
        "PASS_OFFLINE_CONTRACT"
    )
    assert verdict["PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN"] is False
    assert verdict["PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND"] is True
    assert verdict["POST_PERFORMED"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["NO_PROVEN_POSITION_DENIES"] is True
    assert verdict["PARTIAL_FLATTEN_DENIES"] is True
    assert verdict["GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES"] is True
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert verdict["P20_DOES_NOT_ISSUE_RUNTIME_PERMIT"] is True

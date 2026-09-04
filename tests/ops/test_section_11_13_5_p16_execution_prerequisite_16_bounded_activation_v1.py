"""P16 EXECUTION_PREREQUISITE_16 bounded activation contract tests. Offline only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    BOUNDED_ACTIVATION_OWNER_GO_CANONICAL,
    BoundedActivationPermitV1,
    evaluate_bounded_activation_permit_v1,
    offline_contract_proof_bounded_activation_permit_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.adjudicate_v1 import (
    P16BoundedActivationAdjudicationError,
    adjudicate_execution_prerequisite_16_bounded_activation_v1,
)
from src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P13_CLOSED,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)

TARGET = "SUI-USD_UM_XPERP-310404"


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
    assert THIS_SLICE == "11.13.5.P16"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P16"
    assert P13_CLOSED is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == (
        "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"
    )
    assert NEXT_AUTHORITY_BOUNDARY == (
        "SEPARATE_OWNER_GO_FOR_EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"
    )
    assert "BOUNDED_ACTIVATION_PERMIT" in GATE_NAMES


def test_missing_expired_stale_and_implementation_go_deny() -> None:
    missing_ok, missing = evaluate_bounded_activation_permit_v1(
        permit=None,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        evaluation_monotonic_ms=0,
    )
    assert missing_ok is False
    assert "BOUNDED_ACTIVATION_PERMIT_MISSING" in missing
    forbidden = BoundedActivationPermitV1(
        kind="BOUNDED_ACTIVATION",
        purpose="SECTION_11_13_5_BOUNDED_ACTIVATION",
        owner_go=OWNER_GO,
        bound_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        not_after_monotonic_ms=1_000_000,
    )
    forbidden_ok, forbidden_reasons = evaluate_bounded_activation_permit_v1(
        permit=forbidden,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        evaluation_monotonic_ms=0,
    )
    assert forbidden_ok is False
    assert "BOUNDED_ACTIVATION_OWNER_GO_FORBIDDEN" in forbidden_reasons
    expired = BoundedActivationPermitV1(
        kind="BOUNDED_ACTIVATION",
        purpose="SECTION_11_13_5_BOUNDED_ACTIVATION",
        owner_go=BOUNDED_ACTIVATION_OWNER_GO_CANONICAL,
        bound_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        not_after_monotonic_ms=0,
    )
    expired_ok, expired_reasons = evaluate_bounded_activation_permit_v1(
        permit=expired,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        evaluation_monotonic_ms=1,
    )
    assert expired_ok is False
    assert "BOUNDED_ACTIVATION_PERMIT_EXPIRED" in expired_reasons
    stale = BoundedActivationPermitV1(
        kind="BOUNDED_ACTIVATION",
        purpose="SECTION_11_13_5_BOUNDED_ACTIVATION",
        owner_go=BOUNDED_ACTIVATION_OWNER_GO_CANONICAL,
        bound_origin_main_sha="b" * 40,
        instrument_id=TARGET,
        not_after_monotonic_ms=1_000_000,
    )
    stale_ok, stale_reasons = evaluate_bounded_activation_permit_v1(
        permit=stale,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        evaluation_monotonic_ms=0,
    )
    assert stale_ok is False
    assert "BOUNDED_ACTIVATION_BOUND_SHA_STALE" in stale_reasons


def test_fixture_permit_accepts_without_being_runtime_activation() -> None:
    permit = offline_contract_proof_bounded_activation_permit_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
    )
    ok, reasons = evaluate_bounded_activation_permit_v1(
        permit=permit,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET,
        evaluation_monotonic_ms=0,
    )
    assert ok is True
    assert reasons == ()
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_p16_execution_prerequisite_16_bounded_activation_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text


def test_live_window_nonzero_advances_to_prerequisite_20() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "AUTHENTICATED_PRODUCTIVE_TRANSPORT"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(P16BoundedActivationAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_execution_prerequisite_16_bounded_activation_v1(origin_main_sha="deadbeef")


def test_adjudication_closes_named_p16_contract_without_runtime() -> None:
    verdict = adjudicate_execution_prerequisite_16_bounded_activation_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict[
        "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED"
    ] == ("PASS_OFFLINE_CONTRACT")
    assert verdict["PREREQUISITE_16_BOUNDED_RUNTIME_ACTIVATION_PROVEN"] is False
    assert verdict["PREREQUISITE_16_NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["GLOBAL_LIVE_AUTHORIZED_REQUIRED"] is False
    assert verdict["STRUCTURAL_BOUNDED_PATH_ALLOWED_WITHOUT_LIVE_AUTHORIZED"] is True
    assert verdict["STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND"] is True
    assert verdict["POST_PERFORMED"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["MISSING_PERMIT_DENIES"] is True
    assert verdict["GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES"] is True
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY

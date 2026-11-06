"""SEND_TIME_POSITION_REOBSERVATION offline evaluation tests. Offline only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_authenticated_productive_transport_v1.contract_v1 import (
    AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    REASON_STALE,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.send_time_position_reobservation_v1 import (
    NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION,
    PRODUCER_CLASS_AUTHENTICATED_PRIVATE_GET,
    PRODUCER_CLASS_CALLER_SUPPLIED,
    REASON_APT_NOT_PASS,
    REASON_AUTHENTICATED_GET_PRODUCER,
    REASON_EMPTY_DATA_NOT_ZERO,
    REASON_FAKE_COUNTED_AS_GET,
    REASON_GET,
    REASON_HISTORICAL_REUSE,
    REASON_IMPLEMENTATION_GO_AS_EXECUTE,
    REASON_INSTRUMENT_MISMATCH,
    REASON_MISSING_APT,
    REASON_MISSING_REMAINING,
    REASON_OBSERVATION_MISSING,
    REASON_PROVEN_AT_SEND_CLAIM,
    REASON_REMAINING_MISMATCH,
    REASON_RUNTIME_OBSERVATION_CLAIM,
    REASON_TARGET_NOT_OBSERVED,
    REASON_ZERO_POSITION,
    RecordingSendTimePositionReobservationProducerV1,
    evaluate_send_time_position_reobservation_v1,
    send_time_reobservation_clock_doc_v1,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.adjudicate_v1 import (
    SendTimePositionReobservationAdjudicationError,
    adjudicate_send_time_position_reobservation_v1,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.constants_v1 import (
    APT_CLOSED,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)

TARGET = "SUI-USD_UM_XPERP-310404"
DECISION_ID = "stpr-offline-contract-decision"


def _freshness() -> PositionObservationFreshnessEvidenceV1:
    return PositionObservationFreshnessEvidenceV1(
        response_received_monotonic_ms=0,
        decision_id=DECISION_ID,
        evidence_kind=PRE_SEND_EVIDENCE_KIND,
        observation_get_identity="FAKE_OFFLINE_FIXTURE",
    )


def _eval(**overrides: object) -> tuple[bool, tuple[str, ...]]:
    payload: dict[str, object] = {
        "apt_status": AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
        "positions_payload": {"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        "instrument_id": TARGET,
        "expected_instrument_id": TARGET,
        "freshness_evidence": _freshness(),
        "evaluation_monotonic_ms": 0,
        "current_decision_id": DECISION_ID,
        "claimed_remaining_after_send_time_position_reobservation": (
            NAMED_REMAINING_AFTER_SEND_TIME_POSITION_REOBSERVATION
        ),
        "producer_class": PRODUCER_CLASS_CALLER_SUPPLIED,
        "observation_identity": "FAKE_OFFLINE_FIXTURE",
        "historical_reuse_claim": False,
        "runtime_observation_proven_claim": False,
        "proven_at_send_18": False,
        "proven_at_send_19": False,
        "proven_at_send_21": False,
        "proven_at_send_24": False,
        "live_authorized_claim": False,
        "runtime_permit_issuance_claim": False,
        "flatten_execute_authorized_claim": False,
        "network_session_authorized_claim": False,
        "post_performed_claim": False,
        "get_performed_claim": False,
        "private_get_proven_claim": False,
        "credential_use_proven_claim": False,
        "empty_data_treated_as_zero_claim": False,
        "flatten_execute_owner_go": None,
        "predecessor_lineage_ok": True,
        "transport_error": None,
        "authentication_failure": None,
    }
    payload.update(overrides)
    return evaluate_send_time_position_reobservation_v1(**payload)


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
    assert THIS_SLICE == "11.13.5.SEND_TIME_POSITION_REOBSERVATION"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_SEND_TIME_POSITION_REOBSERVATION"
    assert APT_CLOSED is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    assert NEXT_AUTHORITY_BOUNDARY == "SEPARATE_OWNER_GO_FOR_BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    assert "SEND_TIME_POSITION_REOBSERVATION" in GATE_NAMES
    assert "AUTHENTICATED_PRODUCTIVE_TRANSPORT" in GATE_NAMES


def test_missing_unproven_mismatch_and_authority_claims_deny() -> None:
    missing_apt_ok, missing_apt = _eval(apt_status=None)
    assert missing_apt_ok is False
    assert REASON_MISSING_APT in missing_apt
    unproven_apt_ok, unproven_apt = _eval(apt_status="UNPROVEN")
    assert unproven_apt_ok is False
    assert REASON_APT_NOT_PASS in unproven_apt
    missing_remaining_ok, missing_remaining = _eval(
        claimed_remaining_after_send_time_position_reobservation=None
    )
    assert missing_remaining_ok is False
    assert REASON_MISSING_REMAINING in missing_remaining
    mismatch_ok, mismatch = _eval(
        claimed_remaining_after_send_time_position_reobservation=("FLATTEN_EXECUTE",)
    )
    assert mismatch_ok is False
    assert REASON_REMAINING_MISMATCH in mismatch
    missing_ok, missing = _eval(positions_payload=None)
    assert missing_ok is False
    assert REASON_OBSERVATION_MISSING in missing
    empty_ok, empty_reasons = _eval(positions_payload={"code": "0", "data": []})
    assert empty_ok is False
    assert REASON_EMPTY_DATA_NOT_ZERO in empty_reasons
    assert REASON_TARGET_NOT_OBSERVED in empty_reasons
    inst_ok, inst_reasons = _eval(instrument_id="BTC-USD_UM_XPERP-000000")
    assert inst_ok is False
    assert REASON_INSTRUMENT_MISMATCH in inst_reasons
    not_obs_ok, not_obs = _eval(
        positions_payload={"code": "0", "data": [{"instId": "BTC-USD_UM_XPERP-000000", "pos": "1"}]}
    )
    assert not_obs_ok is False
    assert REASON_TARGET_NOT_OBSERVED in not_obs
    zero_ok, zero_reasons = _eval(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "0"}]}
    )
    assert zero_ok is False
    assert REASON_ZERO_POSITION in zero_reasons
    hist_ok, hist_reasons = _eval(observation_identity="20260903T223726Z")
    assert hist_ok is False
    assert REASON_HISTORICAL_REUSE in hist_reasons
    get_producer_ok, get_producer = _eval(producer_class=PRODUCER_CLASS_AUTHENTICATED_PRIVATE_GET)
    assert get_producer_ok is False
    assert REASON_AUTHENTICATED_GET_PRODUCER in get_producer
    runtime_ok, runtime_reasons = _eval(runtime_observation_proven_claim=True)
    assert runtime_ok is False
    assert REASON_RUNTIME_OBSERVATION_CLAIM in runtime_reasons
    proven_ok, proven_reasons = _eval(proven_at_send_18=True)
    assert proven_ok is False
    assert REASON_PROVEN_AT_SEND_CLAIM in proven_reasons
    get_ok, get_reasons = _eval(get_performed_claim=True)
    assert get_ok is False
    assert REASON_GET in get_reasons
    assert REASON_FAKE_COUNTED_AS_GET in get_reasons
    go_ok, go_reasons = _eval(flatten_execute_owner_go=OWNER_GO)
    assert go_ok is False
    assert REASON_IMPLEMENTATION_GO_AS_EXECUTE in go_reasons
    matching_ok, matching_reasons = _eval()
    assert matching_ok is True
    assert matching_reasons == ()


def test_stale_observation_denies() -> None:
    stale_ok, stale_reasons = _eval(evaluation_monotonic_ms=5001)
    assert stale_ok is False
    assert REASON_STALE in stale_reasons


def test_boundary_age_equal_to_max_is_allowed() -> None:
    ok, reasons = _eval(evaluation_monotonic_ms=5000)
    assert ok is True
    assert reasons == ()


def test_fake_producer_never_gets() -> None:
    producer = RecordingSendTimePositionReobservationProducerV1()
    observation = producer.observe()
    assert producer.last_get_attempted is False
    assert producer.network_session_authorized is False
    assert observation.producer_class == "FAKE_OFFLINE_NO_WIRE"
    clock = send_time_reobservation_clock_doc_v1()
    assert clock["EMPTY_DATA_IS_NOT_ZERO"] is True
    assert clock["CANONICAL_POSITION_GET_ENDPOINT"] == "/api/v5/account/positions"
    assert clock["SEND_TIME_EVALUATION_POINT"] == (
        "IMMEDIATELY_BEFORE_FLATTEN_SEND_PERMIT_DECISION"
    )


def test_adjudicate_module_has_no_network_side_effect() -> None:
    import src.ops.section_11_13_5_send_time_position_reobservation_v1.adjudicate_v1 as adj

    text = Path(adj.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in text
    assert "requests" not in text
    gate = Path(
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
        "send_time_position_reobservation_v1.py"
    ).read_text(encoding="utf-8")
    assert "urlopen" not in gate
    assert "requests" not in gate


def test_live_window_nonzero_advances_to_bounded_runtime_permit_issuance() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "AUTHENTICATED_PRIVATE_RUNTIME_READ"
    assert result["EXECUTION_READY"] is False


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(
        SendTimePositionReobservationAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        adjudicate_send_time_position_reobservation_v1(origin_main_sha="deadbeef")


def test_adjudication_closes_named_reobservation_contract_without_runtime() -> None:
    verdict = adjudicate_send_time_position_reobservation_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
    assert verdict["SEND_TIME_POSITION_REOBSERVATION"] == "PASS_OFFLINE_CONTRACT"
    assert verdict["SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN"] is False
    assert verdict["PREREQUISITE_18_PROVEN_AT_SEND"] is False
    assert verdict["PREREQUISITE_19_PROVEN_AT_SEND"] is False
    assert verdict["PREREQUISITE_21_PROVEN_AT_SEND"] is False
    assert verdict["PREREQUISITE_24_PROVEN_AT_SEND"] is False
    assert verdict["NETWORK_PROVEN"] is False
    assert verdict["CREDENTIAL_USE_PROVEN"] is False
    assert verdict["PRIVATE_GET_PROVEN"] is False
    assert verdict["POST_PROVEN"] is False
    assert verdict["STPR_FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert verdict["STPR_NETWORK_SESSION_AUTHORIZED"] is False
    assert verdict["STRUCTURAL_ALLOW_IS_NOT_WIRE_SEND"] is True
    assert verdict["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] is False
    assert verdict["POST_PERFORMED"] is False
    assert verdict["POSITION_GET_REQUIRED_THIS_PERSIST"] is False
    assert verdict["POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO"] is False

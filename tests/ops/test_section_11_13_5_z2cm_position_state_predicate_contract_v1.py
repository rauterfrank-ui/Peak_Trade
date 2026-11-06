"""§11.13.5.Z2CM fail-closed target position-state predicate.

Locks absent vs empty vs explicit zero vs nonzero. Offline only.
Does not GET, POST, flatten, live-arm, or consume Class D.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    FILTERED_EMPTY_IS_NOT_ZERO,
    HTTP_OK_DOES_NOT_PROVE_COMPLETENESS,
    POSITION_STATE_ENDPOINT,
    QUERY_COMPLETENESS_PROVEN,
    THIS_BUILDER_DOES_NOT_GET,
    UNFILTERED_EMPTY_IS_NOT_ZERO,
    LiveCanaryAccountPositionsQueryGrammarError,
    build_account_positions_query_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
    LiveCanaryPositionObservationError,
    classify_target_position_state_v1,
    observe_target_position_flatten_candidate_v1,
    signed_nonzero_positions_by_instrument_v1,
)

CURRENT_SUI = "SUI-USD_UM_XPERP-310404"
OTHER = "BTC-USD_UM_XPERP-999999"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CM_POSITION_STATE_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_standing_flags_remain_fail_closed() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES


def test_empty_data_array_is_not_observed_not_zero() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": []},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_NOT_OBSERVED
    assert classified.reason == "TARGET_INSTRUMENT_NOT_OBSERVED"
    assert classified.empty_data_is_zero is False
    assert classified.query_completeness_proven is False
    with pytest.raises(LiveCanaryPositionObservationError, match="TARGET_INSTRUMENT_NOT_OBSERVED"):
        observe_target_position_flatten_candidate_v1(
            positions_payload={"code": "0", "data": []},
            instrument_id=CURRENT_SUI,
        )


def test_data_none_is_unknown_not_not_observed() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": None},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_UNKNOWN
    assert classified.reason == "EXCHANGE_STATE_DATA_NONE"
    with pytest.raises(LiveCanaryPositionObservationError, match="EXCHANGE_STATE_DATA_NONE"):
        observe_target_position_flatten_candidate_v1(
            positions_payload={"code": "0", "data": None},
            instrument_id=CURRENT_SUI,
        )


def test_missing_data_field_is_unknown_not_empty() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0"},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_UNKNOWN
    assert classified.reason == "EXCHANGE_STATE_DATA_MISSING"


def test_api_error_is_unknown() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "50001", "data": []},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_UNKNOWN
    assert classified.reason == "EXCHANGE_STATE_PAYLOAD_NOT_OK"


def test_explicit_zero_row_is_zero_proven_not_not_observed() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "0"}]},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_ZERO_PROVEN
    assert classified.signed_pos == "0"
    with pytest.raises(LiveCanaryPositionObservationError, match="ZERO_POSITION_NO_FLATTEN_ORDER"):
        observe_target_position_flatten_candidate_v1(
            positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "0"}]},
            instrument_id=CURRENT_SUI,
        )


def test_explicit_nonzero_is_nonzero_proven() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "1"}]},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_NONZERO_PROVEN
    candidate = observe_target_position_flatten_candidate_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "1"}]},
        instrument_id=CURRENT_SUI,
    )
    assert candidate.candidate_flatten_side == "SELL"
    assert str(candidate.candidate_flatten_qty) == "1"


def test_wrong_instrument_is_not_observed_for_target() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": [{"instId": OTHER, "pos": "2"}]},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_NOT_OBSERVED
    assert classified.reason == "TARGET_INSTRUMENT_NOT_OBSERVED"


def test_duplicate_target_rows_are_unknown() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={
            "code": "0",
            "data": [
                {"instId": CURRENT_SUI, "pos": "1"},
                {"instId": CURRENT_SUI, "pos": "2"},
            ],
        },
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_UNKNOWN
    assert classified.reason == "AMBIGUOUS_TARGET_POSITION_ROWS"


def test_malformed_pos_is_unknown() -> None:
    classified = classify_target_position_state_v1(
        positions_payload={"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "not-a-number"}]},
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_UNKNOWN
    assert classified.reason == "POSITION_SIZE_UNPARSEABLE"


def test_missing_payload_is_unknown() -> None:
    classified = classify_target_position_state_v1(
        positions_payload=None,
        instrument_id=CURRENT_SUI,
    )
    assert classified.state == TARGET_POSITION_UNKNOWN
    assert classified.reason == "POSITIONS_PAYLOAD_MISSING"


def test_signed_nonzero_empty_array_does_not_invent_zero_membership() -> None:
    mapped = signed_nonzero_positions_by_instrument_v1({"code": "0", "data": []})
    assert CURRENT_SUI not in mapped


def test_signed_nonzero_rejects_data_none() -> None:
    with pytest.raises(Exception, match="EXCHANGE_STATE_DATA_NONE"):
        signed_nonzero_positions_by_instrument_v1({"code": "0", "data": None})


def test_query_grammar_unfiltered_does_not_claim_zero_or_completeness() -> None:
    query = build_account_positions_query_v1()
    assert query.endpoint == POSITION_STATE_ENDPOINT
    assert query.inst_id_filter_present is False
    assert query.completeness_proven is False
    assert query.empty_result_is_zero is False
    assert UNFILTERED_EMPTY_IS_NOT_ZERO is True
    assert FILTERED_EMPTY_IS_NOT_ZERO is True
    assert HTTP_OK_DOES_NOT_PROVE_COMPLETENESS is True
    assert QUERY_COMPLETENESS_PROVEN is False
    assert THIS_BUILDER_DOES_NOT_GET is True


def test_query_grammar_instid_filter_is_not_zero_proof() -> None:
    query = build_account_positions_query_v1(inst_id=CURRENT_SUI, inst_type="FUTURES")
    assert query.inst_id_filter_present is True
    assert "instId=" in query.path_with_query()
    assert query.empty_result_is_zero is False
    assert query.completeness_proven is False


def test_query_grammar_rejects_too_many_instids() -> None:
    too_many = ",".join(f"INST-{i}" for i in range(11))
    with pytest.raises(
        LiveCanaryAccountPositionsQueryGrammarError, match="INSTID_COUNT_EXCEEDS_MAX"
    ):
        build_account_positions_query_v1(inst_id=too_many)

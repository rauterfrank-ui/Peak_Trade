"""Offline tests for the shared pre-submit second-open-instrument cap."""

from __future__ import annotations

import inspect

import pytest

from src.live.risk_limits import LiveRiskLimits
from src.ops.config_truth_alignment_contract_v1 import parse_phase1_max_open_positions
from src.ops.pre_submit_open_position_cap_v1 import (
    REASON_ALLOW_NO_OPEN_POSITION,
    REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN,
    REASON_DENY_AMBIGUOUS_POSITION_ROWS,
    REASON_DENY_INVALID_POSITION_PAYLOAD,
    REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT,
    REASON_DENY_POSITION_STATE_UNAVAILABLE,
    PreSubmitOpenPositionCapErrorV1,
    assert_pre_submit_open_position_cap_allows_v1,
    evaluate_pre_submit_open_position_cap_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import MAX_POSITIONS_EFFECTIVE

INSTR_A = "INST-A"
INSTR_B = "INST-B"
INSTR_C = "INST-C"


def _envelope(*rows: dict) -> dict:
    return {"code": "0", "data": list(rows)}


def test_t1_empty_positions_allows_no_open() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope(),
    )
    assert decision.admitted is True
    assert decision.reason_code == REASON_ALLOW_NO_OPEN_POSITION


def test_t2_open_other_instrument_denied() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope({"instId": INSTR_A, "pos": "1"}),
    )
    assert decision.admitted is False
    assert decision.reason_code == REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT
    with pytest.raises(
        PreSubmitOpenPositionCapErrorV1, match=REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT
    ):
        assert_pre_submit_open_position_cap_allows_v1(
            target_instrument_id=INSTR_B,
            positions_payload=_envelope({"instId": INSTR_A, "pos": "1"}),
        )


def test_t3_same_instrument_already_open_allows_without_sizing_policy() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_A,
        positions_payload=_envelope({"instId": INSTR_A, "pos": "-2"}),
    )
    assert decision.admitted is True
    assert decision.reason_code == REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN
    allowed = assert_pre_submit_open_position_cap_allows_v1(
        target_instrument_id=INSTR_A,
        positions_payload=_envelope({"instId": INSTR_A, "pos": "-2"}),
    )
    assert allowed.admitted is True


def test_t4_zero_size_row_is_not_open() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope({"instId": INSTR_A, "pos": "0"}),
    )
    assert decision.admitted is True
    assert decision.reason_code == REASON_ALLOW_NO_OPEN_POSITION


def test_t5_open_other_plus_zero_target_denied() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope(
            {"instId": INSTR_A, "pos": "1"},
            {"instId": INSTR_B, "pos": "0"},
        ),
    )
    assert decision.admitted is False
    assert decision.reason_code == REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT


def test_t6_two_distinct_nonzero_instruments_denied() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope(
            {"instId": INSTR_A, "pos": "1"},
            {"instId": INSTR_C, "pos": "2"},
        ),
    )
    assert decision.admitted is False
    assert decision.reason_code == REASON_DENY_OTHER_OPEN_INSTRUMENT_PRESENT


def test_t7_duplicate_nonzero_same_instid_ambiguous() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope(
            {"instId": INSTR_A, "pos": "1"},
            {"instId": INSTR_A, "pos": "2"},
        ),
    )
    assert decision.admitted is False
    assert decision.reason_code == REASON_DENY_AMBIGUOUS_POSITION_ROWS


def test_t8_malformed_payload_invalid() -> None:
    bad_pos = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope({"instId": INSTR_A, "pos": "not-a-number"}),
    )
    assert bad_pos.reason_code == REASON_DENY_INVALID_POSITION_PAYLOAD
    bad_data = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload={"code": "0", "data": "not-a-list"},
    )
    assert bad_data.reason_code == REASON_DENY_INVALID_POSITION_PAYLOAD
    bad_code = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload={"code": "1", "data": []},
    )
    assert bad_code.reason_code == REASON_DENY_INVALID_POSITION_PAYLOAD
    non_mapping_row = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload={"code": "0", "data": ["nope"]},
    )
    assert non_mapping_row.reason_code == REASON_DENY_INVALID_POSITION_PAYLOAD


def test_t9_missing_instid_on_nonzero_fail_closed() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=_envelope({"pos": "1"}),
    )
    assert decision.admitted is False
    assert decision.reason_code == REASON_DENY_INVALID_POSITION_PAYLOAD


def test_t10_unavailable_none_payload() -> None:
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_B,
        positions_payload=None,
    )
    assert decision.admitted is False
    assert decision.reason_code == REASON_DENY_POSITION_STATE_UNAVAILABLE
    with pytest.raises(
        PreSubmitOpenPositionCapErrorV1, match=REASON_DENY_POSITION_STATE_UNAVAILABLE
    ):
        assert_pre_submit_open_position_cap_allows_v1(
            target_instrument_id=INSTR_B,
            positions_payload=None,
        )


def test_reduce_close_same_instrument_is_not_blanket_blocked() -> None:
    """Count-only open>=1 reject-any-order is unsafe; same-instrument stays ALLOW."""
    decision = evaluate_pre_submit_open_position_cap_v1(
        target_instrument_id=INSTR_A,
        positions_payload=_envelope({"instId": INSTR_A, "posSize": "3"}),
    )
    assert decision.reason_code == REASON_ALLOW_TARGET_INSTRUMENT_ALREADY_OPEN


def test_regression_max_positions_effective_and_batch_symbol_semantics_untouched() -> None:
    assert MAX_POSITIONS_EFFECTIVE == 1
    source = inspect.getsource(LiveRiskLimits.check_orders)
    assert "n_symbols" in source
    assert "max_open_positions" in source
    assert parse_phase1_max_open_positions.__name__ == "parse_phase1_max_open_positions"

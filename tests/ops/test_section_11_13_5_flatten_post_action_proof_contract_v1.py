"""Offline flatten post-action proof contract. No network, no submit."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    ORDER_COUNT_LIMIT,
    POSITION_COUNT_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED,
    P7_3_EMPTY_DATA_IS_ZERO,
    POSITION_OBSERVATION_FRESHNESS_POLICY,
    POST_ACTION_MISSING_TARGET_MAY_SATISFY_POS_EQ_0,
    POST_ACTION_REQUIRES_CAUSAL_SUBMIT_BINDING,
    POST_ACTION_REQUIRES_EXPLICIT_PRE_NONZERO,
    POST_ACTION_SCOPE,
    POST_ACTION_SUCCESS_PREDICATE_STATUS,
    FlattenPostActionSubmitEvidenceV1,
    LiveCanaryFlattenPostActionProofError,
    evaluate_canary_flatten_post_action_proof_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)

TARGET = DEFAULT_INSTRUMENT_ID
OTHER = "BTC-USD_UM_XPERP-999999"


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _evaluate(**overrides: Any) -> Any:
    payload: dict[str, Any] = {
        "pre_positions_payload": _positions({"instId": TARGET, "pos": "1"}),
        "post_positions_payload": _positions({"instId": TARGET, "pos": "0"}),
        "post_pending_orders_payload": _pending(),
        "instrument_id": TARGET,
    }
    payload.update(overrides)
    return evaluate_canary_flatten_post_action_proof_contract_v1(**payload)


def _submit_evidence(**overrides: Any) -> FlattenPostActionSubmitEvidenceV1:
    payload: dict[str, Any] = {
        "receipt_allowed": True,
        "approved_request_identity": "abc" * 8 + "defg",
        "gate_digest": "digest-1",
        "instrument_id": TARGET,
        "send_attempted": True,
        "wire_attempted": True,
        "transport_call_completed": True,
        "send_completed": True,
        "http_status": 200,
        "post_readback_after_submit": True,
        "flatten_position_proven": False,
        "venue_acceptance_proven": False,
    }
    payload.update(overrides)
    return FlattenPostActionSubmitEvidenceV1(**payload)


def test_contract_flags_remain_fail_closed() -> None:
    assert FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED is True
    assert LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert LIVE_AUTHORIZED is False
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert ORDER_COUNT_LIMIT == 1
    assert POSITION_COUNT_LIMIT == 1
    assert POST_ACTION_SUCCESS_PREDICATE_STATUS == "BOUND_CHOICE_B"
    assert POST_ACTION_MISSING_TARGET_MAY_SATISFY_POS_EQ_0 is True
    assert POST_ACTION_REQUIRES_EXPLICIT_PRE_NONZERO is True
    assert POST_ACTION_REQUIRES_CAUSAL_SUBMIT_BINDING is True
    assert POST_ACTION_SCOPE == "FLATTEN_POST_ACTION_SUCCESS_EVALUATOR_ONLY"
    assert P7_3_EMPTY_DATA_IS_ZERO is False
    assert POSITION_OBSERVATION_FRESHNESS_POLICY == (
        "POLICY_BOUND_ENFORCEMENT_IMPLEMENTED_OFFLINE_SEND_TIME_UNPROVEN"
    )


def test_offline_satisfied_pre_nonzero_post_flat_pending_empty() -> None:
    verdict = _evaluate()
    assert verdict.offline_contract_satisfied is True
    assert verdict.already_flat_noop is False
    assert verdict.pre_pos_nonzero is True
    assert verdict.post_pos_zero is True
    assert verdict.pending_empty is True
    assert verdict.no_flip is True
    assert verdict.no_unexpected_related_instrument_position is True
    assert verdict.submit_authorized is False
    assert verdict.submit_reachable is False
    assert verdict.live_flatten_provability == "UNPROVEN"
    assert verdict.productive_sequence_required is True
    assert verdict.network_effect == "none"
    assert "PRODUCTIVE_LIVE_FLATTEN_SEQUENCE_NOT_EXECUTED" in verdict.blocking_reasons


def test_already_flat_is_noop_not_submit() -> None:
    verdict = _evaluate(pre_positions_payload=_positions())
    assert verdict.already_flat_noop is True
    assert verdict.offline_contract_satisfied is False
    assert verdict.submit_authorized is False
    assert "ZERO_POSITION_NO_FLATTEN_ORDER" in verdict.blocking_reasons
    assert verdict.live_flatten_provability == "UNPROVEN"


def test_post_not_flat_fails() -> None:
    verdict = _evaluate(post_positions_payload=_positions({"instId": TARGET, "pos": "1"}))
    assert verdict.offline_contract_satisfied is False
    assert "POST_NOT_FLAT" in verdict.blocking_reasons


def test_pending_not_empty_fails() -> None:
    verdict = _evaluate(post_pending_orders_payload=_pending({"instId": TARGET, "clOrdId": "abc"}))
    assert verdict.pending_empty is False
    assert "PENDING_NOT_EMPTY" in verdict.blocking_reasons
    assert verdict.offline_contract_satisfied is False


def test_flip_detected_fails() -> None:
    verdict = _evaluate(post_positions_payload=_positions({"instId": TARGET, "pos": "-1"}))
    assert verdict.no_flip is False
    assert "FLIP_DETECTED" in verdict.blocking_reasons
    assert "POST_NOT_FLAT" in verdict.blocking_reasons


def test_related_instrument_contamination_fails() -> None:
    verdict = _evaluate(
        post_positions_payload=_positions({"instId": OTHER, "pos": "1"}),
    )
    assert verdict.no_unexpected_related_instrument_position is False
    assert "UNEXPECTED_RELATED_INSTRUMENT_POSITION" in verdict.blocking_reasons


def test_pre_related_instrument_contamination_fails() -> None:
    verdict = _evaluate(
        pre_positions_payload=_positions(
            {"instId": TARGET, "pos": "1"},
            {"instId": OTHER, "pos": "2"},
        )
    )
    assert "UNEXPECTED_RELATED_INSTRUMENT_POSITION_PRE" in verdict.blocking_reasons
    assert verdict.offline_contract_satisfied is False


def test_pre_open_order_fails() -> None:
    verdict = _evaluate(
        pre_pending_orders_payload=_pending({"instId": TARGET, "clOrdId": "entry1"})
    )
    assert "OPEN_ORDER_PRESENT_BEFORE_FLATTEN" in verdict.blocking_reasons
    assert verdict.offline_contract_satisfied is False


def test_malformed_positions_fail_closed() -> None:
    verdict = _evaluate(pre_positions_payload={"code": "1", "data": []})
    assert verdict.contract_state == "FLATTEN_PROOF_FAIL_CLOSED"
    assert verdict.offline_contract_satisfied is False


def test_wrong_instrument_binding_rejected() -> None:
    with pytest.raises(LiveCanaryFlattenPostActionProofError, match="INSTRUMENT_BINDING_MISMATCH"):
        _evaluate(instrument_id=OTHER)


def test_short_pre_flatten_buy_side_offline_satisfied() -> None:
    verdict = _evaluate(pre_positions_payload=_positions({"instId": TARGET, "pos": "-1"}))
    assert verdict.offline_contract_satisfied is True
    assert verdict.pre_signed_pos == "-1"
    assert verdict.post_signed_pos == "0"
    assert verdict.live_flatten_provability == "UNPROVEN"


def test_choice_b_pre_nonzero_post_missing_without_submit_is_fail_closed() -> None:
    verdict = _evaluate(post_positions_payload=_positions())
    assert verdict.offline_contract_satisfied is False
    assert verdict.already_flat_noop is False
    assert verdict.post_pos_zero is False
    assert verdict.no_flip is False
    assert verdict.choice_b_pos_eq_0 is False
    assert "POST_TARGET_NOT_OBSERVED" in verdict.blocking_reasons
    assert "AUTHORIZED_FLATTEN_MUTATION_UNPROVEN" in verdict.blocking_reasons
    assert "NO_FLIP_UNPROVEN_TARGET_MISSING" in verdict.blocking_reasons
    assert verdict.submit_authorized is False
    assert verdict.live_flatten_provability == "UNPROVEN"


def test_choice_b_pre_missing_post_missing_is_not_productive_success() -> None:
    verdict = _evaluate(pre_positions_payload=_positions(), post_positions_payload=_positions())
    assert verdict.already_flat_noop is True
    assert verdict.offline_contract_satisfied is False
    assert "ZERO_POSITION_NO_FLATTEN_ORDER" in verdict.blocking_reasons
    assert verdict.submit_authorized is False


def test_choice_b_post_explicit_nonzero_is_not_flat() -> None:
    verdict = _evaluate(post_positions_payload=_positions({"instId": TARGET, "pos": "1"}))
    assert verdict.offline_contract_satisfied is False
    assert "POST_NOT_FLAT" in verdict.blocking_reasons


def test_choice_b_explicit_zero_row_satisfies_offline_sequence() -> None:
    missing = _evaluate(post_positions_payload=_positions())
    explicit_zero = _evaluate(post_positions_payload=_positions({"instId": TARGET, "pos": "0"}))
    assert missing.offline_contract_satisfied is False
    assert explicit_zero.offline_contract_satisfied is True
    assert missing.post_pos_zero is False
    assert explicit_zero.post_pos_zero is True
    assert missing.no_flip is False
    assert explicit_zero.no_flip is True
    assert missing.live_flatten_provability == "UNPROVEN"
    assert explicit_zero.live_flatten_provability == "UNPROVEN"


def test_choice_b_missing_with_causal_bind_does_not_prove_no_flip() -> None:
    verdict = _evaluate(
        post_positions_payload=_positions(),
        submit_evidence=_submit_evidence(),
    )
    assert verdict.choice_b_pos_eq_0 is True
    assert verdict.post_pos_zero is True
    assert verdict.no_flip is False
    assert verdict.offline_contract_satisfied is False
    assert "NO_FLIP_UNPROVEN_TARGET_MISSING" in verdict.blocking_reasons
    assert verdict.causal_submit_bound is True


def test_choice_b_send_failure_cannot_enter_success() -> None:
    verdict = _evaluate(
        post_positions_payload=_positions(),
        submit_evidence=_submit_evidence(
            send_completed=False, wire_attempted=False, http_status=None
        ),
    )
    assert verdict.offline_contract_satisfied is False
    assert verdict.choice_b_pos_eq_0 is False
    assert "TRANSPORT_FAILURE_BEFORE_WIRE" in verdict.blocking_reasons or (
        "TRANSPORT_SEND_NOT_COMPLETED" in verdict.blocking_reasons
    )


def test_choice_b_data_none_is_not_empty_success() -> None:
    verdict = _evaluate(post_positions_payload={"code": "0", "data": None})
    assert verdict.offline_contract_satisfied is False
    assert verdict.already_flat_noop is False
    assert "POST_DATA_NONE" in verdict.blocking_reasons


def test_choice_b_parse_failure_cannot_become_empty_success() -> None:
    verdict = _evaluate(post_positions_payload={"code": "0", "data": "not-a-list"})
    assert verdict.offline_contract_satisfied is False
    assert "POST_DATA_NOT_LIST" in verdict.blocking_reasons


def test_http_non_2xx_submit_evidence_cannot_choice_b_missing_success() -> None:
    verdict = _evaluate(
        post_positions_payload=_positions(),
        submit_evidence=_submit_evidence(http_status=401, send_completed=True, wire_attempted=True),
    )
    assert verdict.offline_contract_satisfied is False
    assert verdict.choice_b_pos_eq_0 is False
    assert "TRANSPORT_HTTP_NOT_2XX" in verdict.blocking_reasons

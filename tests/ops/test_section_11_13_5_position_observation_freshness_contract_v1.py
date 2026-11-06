"""§11.13.5.Z2CP position-observation freshness enforcement. Offline only."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_POLICY,
    FlattenPostActionSubmitEvidenceV1,
    evaluate_canary_flatten_post_action_proof_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    CLOCK_DOMAIN,
    OBSERVATION_TIMESTAMP_FIELD,
    POSITION_OBSERVATION_FRESHNESS_ALSO_APPLIES_TO_POST_ACTION_READBACK,
    POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED,
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    POST_ACTION_READBACK_EVIDENCE_KIND,
    PRE_SEND_EVIDENCE_KIND,
    REASON_ASSOCIATION_UNPROVEN,
    REASON_CROSS_DECISION,
    REASON_FRESHNESS_UNKNOWN,
    REASON_MALFORMED_TIMESTAMP,
    REASON_NEGATIVE_AGE,
    REASON_POST_ACTION_CONSUME,
    REASON_POST_ACTION_KIND,
    REASON_SAME_GET_DUAL_USE,
    REASON_STALE,
    Z2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED,
    PositionObservationFreshnessEvidenceV1,
    evaluate_position_observation_freshness_v1,
    reject_same_get_pre_send_and_post_readback_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "d45a3c0b4ed64e4632a7b92d827818a1fd054361"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
DECISION_A = "flatten-pre-send-decision-a"
DECISION_B = "flatten-pre-send-decision-b"
THIS_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_POSITION_OBSERVATION_FRESHNESS_PERSIST_IMPLEMENT_PR_V1"
)


class _MonoClock:
    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value

    def advance(self, ms: int) -> None:
        self.value += ms


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price() -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side="SELL",
        observed_signed_pos="1",
        bid="64805.6",
        ask="64805.7",
        quote_timestamp_ms=QUOTE_TS,
        evaluation_timestamp_ms=EVAL_TS,
        tick_sz="0.1",
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _evidence(
    *,
    received_ms: Any = 0,
    decision_id: str | None = DECISION_A,
    evidence_kind: str = PRE_SEND_EVIDENCE_KIND,
    consumed_as_post_action_readback: bool = False,
    observation_get_identity: str | None = "get-1",
) -> PositionObservationFreshnessEvidenceV1:
    return PositionObservationFreshnessEvidenceV1(
        response_received_monotonic_ms=received_ms,
        decision_id=decision_id,
        evidence_kind=evidence_kind,
        consumed_as_post_action_readback=consumed_as_post_action_readback,
        observation_get_identity=observation_get_identity,
    )


def _gate(**overrides: Any) -> FlattenPreSendGateInputV1:
    clock = overrides.pop("monotonic_ms_clock", _MonoClock(0))
    payload: dict[str, Any] = {
        "live_authorized": False,
        "live_enabled": True,
        "live_armed": True,
        "flatten_live_wire_enabled": True,
        "allow_productive_wire_send": True,
        "flatten_execute_token": FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        "flatten_execute_purpose": FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        "flatten_execute_owner_go": FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        "positions_payload": _positions({"instId": TARGET, "pos": "1"}),
        "pending_orders_payload": _pending(),
        "price_input": _price(),
        "owner_go": OWNER_GO,
        "origin_main_sha": ORIGIN_SHA,
        "flatten_execute_bound_origin_main_sha": ORIGIN_SHA,
        "instrument_id": TARGET,
        "one_shot_no_retry": True,
        "duplicate_post_protection": True,
        "flatten_pre_send_decision_id": DECISION_A,
        "position_observation_freshness_evidence": _evidence(),
        "monotonic_ms_clock": clock,
        "bounded_activation_permit": offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=ORIGIN_SHA,
            instrument_id=TARGET,
        ),
    }
    payload.update(overrides)
    return FlattenPreSendGateInputV1(**payload)


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


def test_policy_constants_are_owner_ratified_and_not_quote_lock_transfer() -> None:
    assert POSITION_OBSERVATION_FRESHNESS_POLICY == (
        "POLICY_BOUND_ENFORCEMENT_IMPLEMENTED_OFFLINE_SEND_TIME_UNPROVEN"
    )
    assert POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED is True
    assert POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS == 5000
    assert CLOCK_DOMAIN == "LOCAL_MONOTONIC_ELAPSED_TIME"
    assert OBSERVATION_TIMESTAMP_FIELD == "LOCAL_RESPONSE_RECEIVED_AT"
    assert POSITION_OBSERVATION_FRESHNESS_ALSO_APPLIES_TO_POST_ACTION_READBACK is False
    assert Z2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED is False
    assert "POSITION_OBSERVATION_FRESHNESS" in GATE_NAMES
    assert "CATEGORY_C" not in GATE_NAMES
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert THIS_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert (
        "PEAK_TRADE_OWNER_DECISION_POSITION_OBSERVATION_FRESHNESS_POLICY_V1"
        in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    )


@pytest.mark.parametrize(
    ("age_ms", "allowed", "reason"),
    [
        (0, True, ""),
        (1, True, ""),
        (4999, True, ""),
        (5000, True, ""),
        (5001, False, REASON_STALE),
    ],
)
def test_age_boundary_matrix(age_ms: int, allowed: bool, reason: str) -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=_evidence(received_ms=10_000),
        evaluation_monotonic_ms=10_000 + age_ms,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is allowed
    assert verdict.age_ms == age_ms
    assert verdict.reject_reason == reason


def test_missing_evidence_is_freshness_unknown_not_default_fresh() -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=None,
        evaluation_monotonic_ms=0,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is False
    assert verdict.reject_reason == REASON_FRESHNESS_UNKNOWN


@pytest.mark.parametrize(
    "raw",
    [None, "", "   ", "abc", "12.5", True, False, 1.5, object()],
)
def test_malformed_or_missing_observation_sample_rejects(raw: Any) -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=_evidence(received_ms=raw),
        evaluation_monotonic_ms=0,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is False
    assert verdict.reject_reason in {REASON_FRESHNESS_UNKNOWN, REASON_MALFORMED_TIMESTAMP}


def test_negative_age_and_future_observation_sample_reject() -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=_evidence(received_ms=5_000),
        evaluation_monotonic_ms=4_999,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is False
    assert verdict.reject_reason == REASON_NEGATIVE_AGE
    assert verdict.age_ms == -1


def test_same_decision_reuse_while_fresh_allows() -> None:
    clock = _MonoClock(100)
    evidence = _evidence(received_ms=100)
    first = evaluate_flatten_pre_send_gate_v1(
        _gate(
            position_observation_freshness_evidence=evidence,
            monotonic_ms_clock=clock,
        )
    )
    assert first.allowed is True
    clock.advance(4000)
    second = evaluate_flatten_pre_send_gate_v1(
        _gate(
            position_observation_freshness_evidence=evidence,
            flatten_pre_send_decision_id=DECISION_A,
            monotonic_ms_clock=clock,
        )
    )
    assert second.allowed is True
    assert "FRESHNESS_UNKNOWN" not in second.reasons


def test_same_decision_reuse_after_expiry_rejects() -> None:
    clock = _MonoClock(100)
    evidence = _evidence(received_ms=100)
    first = evaluate_flatten_pre_send_gate_v1(
        _gate(
            position_observation_freshness_evidence=evidence,
            monotonic_ms_clock=clock,
        )
    )
    assert first.allowed is True
    clock.advance(5001)
    expired = evaluate_flatten_pre_send_gate_v1(
        _gate(
            position_observation_freshness_evidence=evidence,
            monotonic_ms_clock=clock,
        )
    )
    assert expired.allowed is False
    assert REASON_STALE in expired.reasons


def test_cross_decision_reuse_rejects() -> None:
    evidence = _evidence(received_ms=0, decision_id=DECISION_A)
    receipt = evaluate_flatten_pre_send_gate_v1(
        _gate(
            position_observation_freshness_evidence=evidence,
            flatten_pre_send_decision_id=DECISION_B,
            monotonic_ms_clock=_MonoClock(0),
        )
    )
    assert receipt.allowed is False
    assert REASON_CROSS_DECISION in receipt.reasons


def test_missing_decision_association_rejects() -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=_evidence(decision_id=None),
        evaluation_monotonic_ms=0,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is False
    assert verdict.reject_reason == REASON_ASSOCIATION_UNPROVEN


def test_absence_of_caller_freshness_metadata_fail_closes_pre_send() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(
        _gate(
            position_observation_freshness_evidence=None,
            flatten_pre_send_decision_id=DECISION_A,
            monotonic_ms_clock=_MonoClock(0),
        )
    )
    assert receipt.allowed is False
    assert REASON_FRESHNESS_UNKNOWN in receipt.reasons
    assert receipt.productive_venue_proof is False


def test_no_silent_default_clock_or_true_freshness() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(
        FlattenPreSendGateInputV1(
            live_authorized=True,
            live_enabled=True,
            live_armed=True,
            flatten_live_wire_enabled=True,
            allow_productive_wire_send=True,
            flatten_execute_token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
            flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
            flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
            positions_payload=_positions({"instId": TARGET, "pos": "1"}),
            pending_orders_payload=_pending(),
            price_input=_price(),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
            flatten_execute_bound_origin_main_sha=ORIGIN_SHA,
        )
    )
    assert receipt.allowed is False
    assert REASON_FRESHNESS_UNKNOWN in receipt.reasons or REASON_ASSOCIATION_UNPROVEN in (
        receipt.reasons
    )


def test_post_action_kind_cannot_pass_pre_send_freshness() -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=_evidence(evidence_kind=POST_ACTION_READBACK_EVIDENCE_KIND),
        evaluation_monotonic_ms=0,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is False
    assert verdict.reject_reason == REASON_POST_ACTION_KIND


def test_consumed_as_post_action_readback_rejects() -> None:
    verdict = evaluate_position_observation_freshness_v1(
        evidence=_evidence(consumed_as_post_action_readback=True),
        evaluation_monotonic_ms=0,
        current_decision_id=DECISION_A,
    )
    assert verdict.allowed is False
    assert verdict.reject_reason == REASON_POST_ACTION_CONSUME


def test_post_action_cannot_consume_pre_send_freshness_evidence() -> None:
    verdict = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        post_positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        post_pending_orders_payload=_pending(),
        submit_evidence=_submit_evidence(pre_send_freshness_evidence=_evidence()),
    )
    assert verdict.offline_contract_satisfied is False
    assert REASON_POST_ACTION_CONSUME in verdict.blocking_reasons
    assert verdict.submit_authorized is False


def test_same_get_cannot_serve_pre_send_and_post_readback() -> None:
    assert (
        reject_same_get_pre_send_and_post_readback_v1(
            pre_send_get_identity="get-1",
            post_readback_get_identity="get-1",
        )
        == REASON_SAME_GET_DUAL_USE
    )
    verdict = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        post_positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        post_pending_orders_payload=_pending(),
        submit_evidence=_submit_evidence(
            pre_send_get_identity="get-1",
            post_readback_get_identity="get-1",
        ),
    )
    assert verdict.offline_contract_satisfied is False
    assert REASON_SAME_GET_DUAL_USE in verdict.blocking_reasons


def test_duplicate_post_protection_not_regressed() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(duplicate_post_protection=False))
    assert receipt.allowed is False
    assert "DUPLICATE_POST_PROTECTION_REQUIRED" in receipt.reasons


def test_fresh_pre_send_does_not_add_positive_execution_authority() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate())
    assert receipt.allowed is True
    assert receipt.live_flatten_provability == "UNPROVEN"
    assert receipt.productive_venue_proof is False
    assert receipt.permit is not None
    assert receipt.permit.submit_reachable is False

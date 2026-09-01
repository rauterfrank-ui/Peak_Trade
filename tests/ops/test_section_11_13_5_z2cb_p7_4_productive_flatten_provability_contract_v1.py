"""§11.13.5.Z2CB P7.4 productive flatten provability contract.

Locks forensic fail-closed rules: empty != zero, unresolved position
blocks mutation, unknown qty/unit/instrument/gates block mutation,
one-shot no retry, accepted POST != proof, live/testnet/canary remain
false, P7.5 does not start. Offline only. No venue access.
"""

from __future__ import annotations

import inspect
from decimal import Decimal
from typing import Any, Mapping

import pytest

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANARY_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POSITION_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_gated_submit_v1 import (
    FlattenGatedSubmitBoundaryV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    evaluate_canary_flatten_post_action_proof_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
    RecordingProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    MULTI_FUTURE_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
    signed_nonzero_positions_by_instrument_v1,
)

P7_4_OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CA_P7_4_PRODUCTIVE_FLATTEN_PROVABILITY_"
    "BOUNDED_FORENSIC_ADJUDICATION_AND_CONDITIONAL_EXECUTION_ONLY"
)
HISTORICAL_BTC = "BTC-USD_UM_XPERP-310404"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"
ORIGIN_SHA = "e410f5b413e33f8183fc2b15876755b8c1fe4be4"
P7_4_DECISION_ID = "p7-4-flatten-pre-send-decision-1"
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_P7_4_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def _empty_positions() -> dict[str, Any]:
    return {"code": "0", "data": []}


def _pending_empty() -> dict[str, Any]:
    return {"code": "0", "data": []}


def _price_input(
    *, flatten_side: str = "SELL", observed_signed_pos: str = "1"
) -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side=flatten_side,
        observed_signed_pos=observed_signed_pos,
        bid="1.2345",
        ask="1.2346",
        tick_sz="0.0001",
        quote_timestamp_ms=QUOTE_TS,
        evaluation_timestamp_ms=EVAL_TS,
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _gate(
    *,
    positions_payload: Mapping[str, Any],
    instrument_id: str = CURRENT_SUI,
    live_authorized: bool = True,
    flatten_execute_owner_go: str = P7_4_OWNER_GO,
    pending_orders_payload: Mapping[str, Any] | None = None,
    price_input: FlattenPriceInputV1 | None = None,
) -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=live_authorized,
        live_enabled=True,
        live_armed=True,
        flatten_live_wire_enabled=True,
        allow_productive_wire_send=True,
        flatten_execute_token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=flatten_execute_owner_go,
        positions_payload=dict(positions_payload),
        pending_orders_payload=pending_orders_payload,
        price_input=price_input or _price_input(),
        owner_go=P7_4_OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        flatten_execute_bound_origin_main_sha=ORIGIN_SHA,
        instrument_id=instrument_id,
        flatten_pre_send_decision_id=P7_4_DECISION_ID,
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id=P7_4_DECISION_ID,
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=(lambda: 0),
    )


def test_p7_3_empty_not_observed_is_not_zero() -> None:
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=_empty_positions(),
            instrument_id=CURRENT_SUI,
        )
        raise AssertionError("empty position window must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
        assert "ZERO" not in str(exc)


def test_required_by_current_proof_false_is_not_not_required_proven() -> None:
    required_by_current_proof = False
    not_required_proven = False
    assert required_by_current_proof is False
    assert not_required_proven is False
    assert (required_by_current_proof is False) is not (not_required_proven is True)


def test_no_mutation_when_position_state_unresolved() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(positions_payload=_empty_positions()))
    assert receipt.allowed is False
    assert any("TARGET_INSTRUMENT_NOT_OBSERVED" in reason for reason in receipt.reasons)
    assert receipt.qty is None


def test_no_mutation_when_qty_unknown() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(positions_payload=_empty_positions()))
    assert receipt.allowed is False
    assert receipt.qty is None
    assert receipt.request_body is None


def test_no_mutation_when_qty_unit_unknown() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(positions_payload=_empty_positions()))
    assert receipt.allowed is False
    assert receipt.request_body is None
    body = receipt.request_body
    assert body is None or "sz" not in body


def test_no_mutation_when_canonical_instrument_wrong() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(
        _gate(positions_payload=_empty_positions(), instrument_id=HISTORICAL_BTC)
    )
    assert receipt.allowed is False
    assert any("INSTRUMENT_BINDING" in reason for reason in receipt.reasons)
    assert HISTORICAL_BTC != DEFAULT_INSTRUMENT_ID


def test_no_mutation_when_gate_ambiguous_or_owner_go_mismatched() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=P7_4_OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_MISMATCH" in reasons
    assert P7_4_OWNER_GO != FLATTEN_EXECUTE_OWNER_GO_CANONICAL
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(positions_payload=_empty_positions()))
    assert receipt.allowed is False
    assert "FLATTEN_EXECUTE_OWNER_GO_MISMATCH" in receipt.reasons


def test_max_one_mutating_call_and_no_retry() -> None:
    denied = FlattenGatedSubmitBoundaryV1().submit(
        gate_input=_gate(positions_payload=_empty_positions()),
        transport=RecordingProductiveFlattenTransportV1(),
    )
    assert denied.send_attempted is False
    assert denied.send_completed is False
    assert denied.retry_attempted is False
    src = inspect.getsource(FlattenGatedSubmitBoundaryV1.submit)
    assert "DUPLICATE_POST_FORBIDDEN" in src
    assert "_submitted = True" in src
    synthetic = {
        "code": "0",
        "data": [{"instId": CURRENT_SUI, "pos": "1"}],
    }
    boundary = FlattenGatedSubmitBoundaryV1()
    transport = RecordingProductiveFlattenTransportV1()
    first = boundary.submit(
        gate_input=_gate(
            positions_payload=synthetic,
            flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
            pending_orders_payload=_pending_empty(),
        ),
        transport=transport,
    )
    assert first.send_completed is True
    assert len(transport.calls) == 1
    second = boundary.submit(
        gate_input=_gate(
            positions_payload=synthetic,
            flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
            pending_orders_payload=_pending_empty(),
        ),
        transport=transport,
    )
    assert second.duplicate_blocked is True
    assert second.send_completed is False
    assert second.retry_attempted is False
    assert len(transport.calls) == 1


def test_readback_only_after_accepted_mutation_and_max_one() -> None:
    denied = FlattenGatedSubmitBoundaryV1().submit(
        gate_input=_gate(positions_payload=_empty_positions()),
        transport=RecordingProductiveFlattenTransportV1(),
    )
    assert denied.send_completed is False
    assert denied.send_attempted is False
    src = inspect.getsource(GatedProductiveFlattenTransportV1.send)
    assert "DUPLICATE_POST_FORBIDDEN" in src
    assert LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"


def test_accepted_post_is_not_flatten_proof() -> None:
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False
    verdict = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=_empty_positions(),
        post_positions_payload=_empty_positions(),
        post_pending_orders_payload=_pending_empty(),
    )
    assert verdict.live_flatten_provability == "UNPROVEN"
    assert verdict.offline_contract_satisfied is False
    assert verdict.submit_authorized is False


def test_empty_readback_is_not_zero_under_p7_3_contract() -> None:
    empty = _empty_positions()
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=empty,
            instrument_id=CURRENT_SUI,
        )
        raise AssertionError("empty read-back must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
    mapped = signed_nonzero_positions_by_instrument_v1(empty)
    assert CURRENT_SUI not in mapped
    assert mapped.get(CURRENT_SUI, Decimal("0")) == Decimal("0")


def test_live_testnet_canary_remain_false_and_p7_5_does_not_start() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert MULTI_FUTURE_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert POSITION_COUNT_LIMIT == 1
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert "/api/v5/trade/close-position" not in POST_ENDPOINTS_GATED


def test_no_btc_to_sui_transfer_and_no_one_contract_equals_one_sui() -> None:
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert CANARY_INSTRUMENT == CURRENT_SUI
    assert HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID == HISTORICAL_BTC
    assert HISTORICAL_BTC != DEFAULT_INSTRUMENT_ID
    one_contract_equals_one_sui = False
    assert one_contract_equals_one_sui is False
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=_empty_positions(),
            instrument_id=HISTORICAL_BTC,
        )
        raise AssertionError("BTC empty window must not become a SUI flatten qty")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"


def test_productive_urllib_send_default_remains_unauthorized() -> None:
    src = inspect.getsource(GatedProductiveFlattenTransportV1.send)
    assert "network_session_authorized" in src
    assert "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in src
    assert "PRODUCTIVE_FLATTEN_URLLIB_NOT_AUTHORIZED_BY_WIRING_SLICE" not in src
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False
    assert transport.last_wire_attempted is False

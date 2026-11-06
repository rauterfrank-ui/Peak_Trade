"""§11.13.5.Z2CQ EXECUTION_PREREQUISITE_08 cluster contract. Offline only."""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    REASON_DEPENDENT_BLOCKED,
    Z2CN_COMMITTED_BODY_SHA256,
    dependent_prerequisites_blocked_unless_08_nonzero_v1,
    evaluate_execution_prerequisite_08_cluster_v1,
    reject_z2cn_snapshot_as_current_08_proof_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
)

CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _deny(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1.urlopen",
        _deny,
        raising=False,
    )


def _empty_positions() -> dict[str, Any]:
    return {"code": "0", "data": []}


def _zero_row() -> dict[str, Any]:
    return {"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "0"}]}


def _nonzero_row() -> dict[str, Any]:
    return {"code": "0", "data": [{"instId": CURRENT_SUI, "pos": "1"}]}


def _price() -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side="SELL",
        observed_signed_pos="1",
        bid="64805.6",
        ask="64805.7",
        quote_timestamp_ms="1787145055768",
        evaluation_timestamp_ms="1787145056000",
        tick_sz="0.1",
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _gate(positions_payload: dict[str, Any]) -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=True,
        live_enabled=True,
        live_armed=True,
        flatten_live_wire_enabled=True,
        allow_productive_wire_send=True,
        flatten_execute_token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        positions_payload=positions_payload,
        pending_orders_payload={"code": "0", "data": []},
        price_input=_price(),
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="6e7cfce9854f340cbc6ba2a63f93acc8883aad1c",
        flatten_execute_bound_origin_main_sha="6e7cfce9854f340cbc6ba2a63f93acc8883aad1c",
        instrument_id=DEFAULT_INSTRUMENT_ID,
        flatten_pre_send_decision_id="z2cq-test",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="z2cq-test",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=lambda: 0,
    )


def test_empty_envelope_is_not_08_and_blocks_dependents() -> None:
    verdict = evaluate_execution_prerequisite_08_cluster_v1(
        positions_payload=_empty_positions(),
        claimed_body_sha256=Z2CN_COMMITTED_BODY_SHA256,
    )
    assert verdict.target_position_state == TARGET_POSITION_NOT_OBSERVED
    assert verdict.prerequisite_08_status == "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"
    assert verdict.prerequisite_08_proven is False
    assert verdict.prerequisite_09_status == REASON_DEPENDENT_BLOCKED
    assert verdict.prerequisite_12_status == REASON_DEPENDENT_BLOCKED
    assert verdict.prerequisite_20_status == REASON_DEPENDENT_BLOCKED
    assert verdict.z2cn_snapshot_is_current_08_proof is False
    assert verdict.class_d_consumed is False
    assert verdict.execution_ready is False
    assert dependent_prerequisites_blocked_unless_08_nonzero_v1(verdict.target_position_state)


def test_z2cn_sha_is_never_current_08_proof() -> None:
    reason = reject_z2cn_snapshot_as_current_08_proof_v1(body_sha256=Z2CN_COMMITTED_BODY_SHA256)
    assert reason == "Z2CN_COMMITTED_SNAPSHOT_IS_NOT_CURRENT_08_PROOF"


def test_zero_row_is_not_08_nonzero() -> None:
    verdict = evaluate_execution_prerequisite_08_cluster_v1(positions_payload=_zero_row())
    assert verdict.target_position_state == TARGET_POSITION_ZERO_PROVEN
    assert verdict.prerequisite_08_proven is False
    assert verdict.prerequisite_09_status == REASON_DEPENDENT_BLOCKED


def test_data_none_is_unknown_not_not_observed() -> None:
    verdict = evaluate_execution_prerequisite_08_cluster_v1(
        positions_payload={"code": "0", "data": None}
    )
    assert verdict.target_position_state == TARGET_POSITION_UNKNOWN
    assert verdict.prerequisite_08_proven is False
    assert "UNKNOWN" in verdict.prerequisite_08_status


def test_fixture_nonzero_is_not_productive_08_proof() -> None:
    verdict = evaluate_execution_prerequisite_08_cluster_v1(positions_payload=_nonzero_row())
    assert verdict.target_position_state == TARGET_POSITION_NONZERO_PROVEN
    assert verdict.prerequisite_08_proven is False
    assert verdict.prerequisite_08_status == "OBSERVED_NONZERO_THIS_PAYLOAD_NOT_SEND_TIME_PROVEN"
    assert not dependent_prerequisites_blocked_unless_08_nonzero_v1(verdict.target_position_state)
    assert verdict.live_flatten_provability == "UNPROVEN"
    assert verdict.send_time_pass_18_19_21_24 == "UNPROVEN"


def test_pre_send_records_target_position_state_independently_on_empty() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(_empty_positions()))
    assert receipt.allowed is False
    decisions = dict(receipt.audit_decisions)
    assert "TARGET_POSITION_STATE" in decisions
    assert "DENY:TARGET_INSTRUMENT_NOT_OBSERVED" in decisions["TARGET_POSITION_STATE"]
    assert any("TARGET_INSTRUMENT_NOT_OBSERVED" in reason for reason in receipt.reasons)
    assert receipt.qty is None
    assert receipt.request_body is None


def test_pre_send_records_target_position_state_on_zero_row() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_gate(_zero_row()))
    assert receipt.allowed is False
    decisions = dict(receipt.audit_decisions)
    assert "DENY:ZERO_POSITION_NO_FLATTEN_ORDER" in decisions["TARGET_POSITION_STATE"]

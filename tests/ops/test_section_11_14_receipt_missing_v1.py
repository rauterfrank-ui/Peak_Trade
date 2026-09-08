"""Offline RECEIPT_MISSING attachable-mint contract tests.

Hard-network-blocked. No HMAC generation. No GET. No urllib POST. No
wire-send. No durable consume. No position mutation. No standing Live
flag mutation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
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
    FlattenPreSendGateReceiptV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.receipt_missing_v1 import (
    FIRST_DENY_AFTER_ATTACHED_RECEIPT,
    FlattenPreSendReceiptMissingError,
    attach_flatten_pre_send_receipt_once_v1,
    first_deny_after_attached_unsigned_send_v1,
    mint_flatten_pre_send_attachable_receipt_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/ops/specs/SECTION_11_14_RECEIPT_MISSING_V1.md"
_FX = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "a738004fda83f9b7df477400b8664949589bb52e"
STALE_SHA = "287ed348d000bdda2ced929b1940284729b5c66e"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
URLLIB_PATCH = (
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
    "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1"
)


def _boom_wire(*_a: Any, **_k: Any) -> Any:
    raise AssertionError("WIRE")


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_RECEIPT_MISSING_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)


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


def _valid_gate(*, origin_main_sha: str = ORIGIN_SHA) -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=False,
        live_enabled=True,
        live_armed=True,
        flatten_live_wire_enabled=True,
        allow_productive_wire_send=True,
        flatten_execute_token=_FX,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        pending_orders_payload=_pending(),
        price_input=_price(),
        owner_go=OWNER_GO,
        origin_main_sha=origin_main_sha,
        flatten_execute_bound_origin_main_sha=origin_main_sha,
        instrument_id=TARGET,
        one_shot_no_retry=True,
        duplicate_post_protection=True,
        flatten_pre_send_decision_id="receipt-missing-pre-send-1",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="receipt-missing-pre-send-1",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=(lambda: 0),
        bounded_activation_permit=offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=origin_main_sha,
            instrument_id=TARGET,
        ),
    )


def _denied_gate() -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=False,
        live_enabled=False,
        live_armed=False,
        flatten_live_wire_enabled=False,
        allow_productive_wire_send=False,
        flatten_execute_token=None,
        flatten_execute_purpose=None,
        flatten_execute_owner_go=None,
        positions_payload={},
        pending_orders_payload=None,
        price_input=FlattenPriceInputV1(),
        owner_go="",
        origin_main_sha=ORIGIN_SHA,
    )


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False


def test_happy_path_mint_attach_stops_at_unsigned_headers() -> None:
    receipt = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=ORIGIN_SHA,
    )
    assert isinstance(receipt, FlattenPreSendGateReceiptV1)
    assert receipt.allowed is True
    assert receipt.send_lease.consumed is False
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    attached = attach_flatten_pre_send_receipt_once_v1(transport, receipt)
    assert attached is receipt
    deny = first_deny_after_attached_unsigned_send_v1(transport, receipt)
    assert deny == FIRST_DENY_AFTER_ATTACHED_RECEIPT
    assert deny == "UNSIGNED_PRODUCTIVE_HEADERS"
    assert receipt.send_lease.consumed is False
    assert transport._sent is False
    assert transport.last_wire_attempted is False


def test_missing_gate_input_denies() -> None:
    with pytest.raises(FlattenPreSendReceiptMissingError, match="GATE_INPUT_MISSING"):
        mint_flatten_pre_send_attachable_receipt_v1(None)


def test_malformed_gate_type_denies() -> None:
    with pytest.raises(FlattenPreSendReceiptMissingError, match="GATE_INPUT_TYPE_INVALID"):
        mint_flatten_pre_send_attachable_receipt_v1("not-a-gate")  # type: ignore[arg-type]


def test_denied_producer_receipt_cannot_mint() -> None:
    producer = evaluate_flatten_pre_send_gate_v1(_denied_gate())
    assert producer.allowed is False
    with pytest.raises(FlattenPreSendReceiptMissingError, match="RECEIPT_NOT_ALLOWED"):
        mint_flatten_pre_send_attachable_receipt_v1(_denied_gate())


def test_stale_origin_main_sha_denies_before_mint() -> None:
    with pytest.raises(FlattenPreSendReceiptMissingError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        mint_flatten_pre_send_attachable_receipt_v1(
            _valid_gate(origin_main_sha=STALE_SHA),
            expected_origin_main_sha=ORIGIN_SHA,
        )


def test_missing_receipt_cannot_attach() -> None:
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    with pytest.raises(FlattenPreSendReceiptMissingError, match="RECEIPT_MISSING"):
        attach_flatten_pre_send_receipt_once_v1(transport, None)


def test_denied_receipt_cannot_attach() -> None:
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    denied = evaluate_flatten_pre_send_gate_v1(_denied_gate())
    with pytest.raises(FlattenPreSendReceiptMissingError, match="RECEIPT_NOT_ALLOWED"):
        attach_flatten_pre_send_receipt_once_v1(transport, denied)
    assert transport._receipt is None


def test_duplicate_attach_does_not_rewrite() -> None:
    first = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=ORIGIN_SHA,
    )
    second = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=ORIGIN_SHA,
    )
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    attach_flatten_pre_send_receipt_once_v1(transport, first)
    with pytest.raises(
        FlattenPreSendReceiptMissingError, match="RECEIPT_ALREADY_ATTACHED_NO_REWRITE"
    ):
        attach_flatten_pre_send_receipt_once_v1(transport, first)
    with pytest.raises(
        FlattenPreSendReceiptMissingError, match="RECEIPT_ALREADY_ATTACHED_NO_REWRITE"
    ):
        attach_flatten_pre_send_receipt_once_v1(transport, second)
    assert transport._receipt is first
    assert first.send_lease.consumed is False
    assert second.send_lease.consumed is False


def test_already_consumed_lease_cannot_attach() -> None:
    receipt = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=ORIGIN_SHA,
    )
    receipt.send_lease.consumed = True
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    with pytest.raises(FlattenPreSendReceiptMissingError, match="RECEIPT_LEASE_ALREADY_CONSUMED"):
        attach_flatten_pre_send_receipt_once_v1(transport, receipt)
    assert transport._receipt is None


def test_hmac_headers_forbidden_in_this_slice() -> None:
    receipt = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=ORIGIN_SHA,
    )
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    attach_flatten_pre_send_receipt_once_v1(transport, receipt)
    signed = live_canary_http_request_from_flatten_receipt_v1(
        receipt,
        headers={
            "OK-ACCESS-KEY": "fixture-key",
            "OK-ACCESS-SIGN": "fixture-sign",
            "OK-ACCESS-TIMESTAMP": "2026-09-08T12:00:00.000Z",
            "OK-ACCESS-PASSPHRASE": "fixture-pass",
            "User-Agent": "PeakTrade-Section-11-13-5-LiveCanary/1",
        },
    )
    with pytest.raises(
        FlattenPreSendReceiptMissingError, match="HMAC_HEADERS_FORBIDDEN_IN_THIS_SLICE"
    ):
        first_deny_after_attached_unsigned_send_v1(transport, receipt, signed)
    assert receipt.send_lease.consumed is False
    assert transport.last_wire_attempted is False


def test_closed_durable_consume_success_object_still_imported() -> None:
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.durable_consume_success_object_v1 import (
        FlattenProductiveSendSuccessObjectV1,
        mint_flatten_productive_send_success_object_v1,
    )

    assert mint_flatten_productive_send_success_object_v1 is not None
    assert FlattenProductiveSendSuccessObjectV1 is not None


def test_receipt_missing_spec_non_execution() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_RECEIPT_MISSING_V1" in text
    assert "RECEIPT_MISSING=PROVEN" in text
    assert "RUNTIME_RECEIPT_MINT_EXECUTED=true" in text
    assert "HMAC_GENERATION_WIRED=false" in text
    assert "POST_PERFORMED=false" in text
    assert "WIRE_SEND_EXECUTED=false" in text
    assert "REAL_POST_COUNT=0" in text
    assert "NEXT_OWNER_AUTHORITY_REQUIRED=HMAC_GENERATION" in text
    assert "CURRENT_CANONICAL_BOUNDARY=UNSIGNED_PRODUCTIVE_HEADERS" in text

"""Offline forensic tests for LIVE_SUBMIT_ACK_OBSERVED contract and mutation boundary."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_SUBMIT,
    OWNER_GO_EXECUTE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX,
    CASE_ADJUDICATION,
    LIVE_SUBMIT_ACK_OBSERVED,
    RETRY_DEFAULT,
    SECOND_SUBMIT_DEFAULT,
    TIMEOUT_MUST_NOT_AUTO_POST,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_contract_v1 import (
    adjudicate_submit_ack_forensic_v1,
    build_exact_mutation_contract_v1,
    build_failure_matrix_v1,
    build_post_submit_recon_contract_v1,
    classify_injected_submit_ack_evidence_v1,
    refuse_live_submit_ack_observed_true_v1,
)


def test_single_submit_safety_constants() -> None:
    assert AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX == 1
    assert RETRY_DEFAULT is False
    assert SECOND_SUBMIT_DEFAULT is False
    assert TIMEOUT_MUST_NOT_AUTO_POST is True
    assert LIVE_SUBMIT_ACK_OBSERVED is True
    assert CASE_ADJUDICATION == "CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE"


def test_refuse_ack_true_promotion() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="MUST_REMAIN_FALSE"):
        refuse_live_submit_ack_observed_true_v1(claimed_true=True)


def test_timeout_after_possible_send_never_retries() -> None:
    classified = classify_injected_submit_ack_evidence_v1(
        send_attempted=True,
        entry_submit_count=0,
        transport_error="UNKNOWN_SUBMIT_TIMEOUT",
    )
    assert classified["case"] == "TIMEOUT_AFTER_POSSIBLE_SEND"
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert classified["RETRY_ALLOWED"] is False
    assert classified["SECOND_SUBMIT_ALLOWED"] is False


def test_transport_ok_is_not_section_1114_ack() -> None:
    classified = classify_injected_submit_ack_evidence_v1(
        send_attempted=True,
        entry_submit_count=1,
        http_status=200,
        okx_code="0",
        json_parse_ok=True,
        ord_id="1",
        s_code="0",
    )
    assert classified["case"] == "UNIQUE_TRANSPORT_OK"
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False


def test_code_zero_without_ordid_is_not_ack() -> None:
    classified = classify_injected_submit_ack_evidence_v1(
        send_attempted=True,
        entry_submit_count=1,
        http_status=200,
        okx_code="0",
        json_parse_ok=True,
        ord_id="",
        s_code="0",
    )
    assert classified["case"] == "VENUE_CODE_ZERO_WITHOUT_ACK_IDENTITY"
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False


def test_failure_matrix_never_allows_second_submit() -> None:
    matrix = build_failure_matrix_v1()
    assert matrix["row_count"] == 11
    for row in matrix["rows"]:
        assert row["LIVE_SUBMIT_ACK_OBSERVED"] is False
        assert row["RETRY_ALLOWED"] is False
        assert row["SECOND_SUBMIT_ALLOWED"] is False


def test_exact_mutation_contract_is_post_trade_order_limit() -> None:
    contract = build_exact_mutation_contract_v1()
    assert contract["endpoint"] == ENDPOINT_SUBMIT == "/api/v5/trade/order"
    assert contract["http_method"] == "POST"
    assert contract["instrument"] == DEFAULT_INSTRUMENT_ID
    assert contract["side"] == "buy"
    assert contract["ordType"] == "limit"
    assert contract["sz"] == "1"
    assert contract["tdMode"] == "cross"
    assert contract["historical_order_plan_artifact_reuse_for_post"] is False
    assert contract["fresh_plan_required_at_post_time"] is True
    assert contract["POST_AUTHORIZED_BY_THIS_GO"] is False
    assert "posSide" not in contract["request_body_keys"]
    assert contract["auth_header_values_persisted"] is False
    assert "AUTH_KEY_HEADER_PRESENT" in contract["auth_header_presence_keys"]
    assert not any(
        str(item).lower().startswith(("ok-access-", "plaintext:", "sk-"))
        for item in contract["auth_header_presence_keys"]
    )


def test_post_submit_recon_unknown_sequence_is_pending_then_history() -> None:
    recon = build_post_submit_recon_contract_v1()
    assert recon["sequence_if_unknown_after_send_attempted"] == [
        "/api/v5/trade/orders-pending",
        "/api/v5/trade/orders-history",
    ]
    assert recon["identity_for_unknown_resolution"] == "clOrdId from the just-built plan"
    assert recon["LIVE_FILL_OBSERVED"] is False
    assert recon["unknown_resolution_is_not_live_submit_ack_observed"] is True


def test_case_a_forensic_adjudication_after_proof_criterion_bind() -> None:
    proof = adjudicate_submit_ack_forensic_v1()
    assert proof["CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO"] is True
    assert proof["CASE_C_CANONICAL_SEMANTIC_GAP"] is False
    assert proof["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert proof["HARD_STOP"] is True


def test_http_client_timeout_cannot_second_post() -> None:
    permit = CanaryEntrySubmitPermitV1(
        owner_go=OWNER_GO_EXECUTE, clordid="ptokxeproddeadbeef", permit_id="p1"
    )
    timeout_transport = RecordingFakeCanaryTransportV1(raise_timeout_on_post=True)
    timeout_client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=timeout_transport,
    )
    with pytest.raises(LiveCanaryHttpError, match="UNKNOWN_SUBMIT_TIMEOUT"):
        timeout_client.post_entry_order(
            permit=permit, body_text="{}", headers={"Content-Type": "application/json"}
        )
    with pytest.raises(LiveCanaryHttpError, match="UNKNOWN_SUBMIT_NO_BLIND_RETRY"):
        timeout_client.post_entry_order(
            permit=permit, body_text="{}", headers={"Content-Type": "application/json"}
        )
    assert timeout_client.counters.entry_submit_count == 0

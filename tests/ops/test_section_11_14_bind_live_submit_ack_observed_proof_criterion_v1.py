"""Offline tests for the bound LIVE_SUBMIT_ACK_OBSERVED proof criterion."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CASE_ADJUDICATION,
    HISTORICAL_ACK_CASE_ADJUDICATION,
    LADDER_FIELD_DEFAULTS,
    LIVE_FEE_OBSERVED,
    LIVE_FILL_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED_PRODUCER,
    LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.ladder_order_v1 import (
    assert_ladder_order_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_observed_adjudication_v1 import (
    adjudicate_live_submit_ack_observed_v1,
    assert_injected_success_cannot_promote_live_field_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_observed_predicate_v1 import (
    ACK_FIELD_CONSTITUENTS,
    ACK_RESPONSE_CONSTITUENTS,
    ADMISSIBLE_SOURCE_KIND,
    CLASS_ACK_SUCCESS,
    CLASS_EXPLICIT_REJECT,
    CLASS_UNKNOWN,
    INJECTED_EVIDENCE_SOURCE_KIND,
    classify_submit_response_v1,
    evaluate_ack_response_conjunction_v1,
    evaluate_live_submit_ack_observed_conjunction_v1,
    response_constituents_from_evidence_v1,
)


def _success_kwargs(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "send_attempted": True,
        "entry_submit_count": 1,
        "http_status": 200,
        "okx_code": "0",
        "json_parse_ok": True,
        "redirect_followed": False,
        "redirectish": False,
        "data_count": 1,
        "s_code": "0",
        "ord_id": "2412345678901234567",
        "returned_clordid": "ptokxeproddeadbeef",
        "sent_clordid": "ptokxeproddeadbeef",
        "transport_error": None,
        "POST_USED": False,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "LIVE_FILL_OBSERVED": False,
    }
    payload.update(overrides)
    return payload


def _classify(**overrides: object) -> dict[str, object]:
    kwargs = _success_kwargs(**overrides)
    return classify_submit_response_v1(
        send_attempted=bool(kwargs["send_attempted"]),
        entry_submit_count=int(kwargs["entry_submit_count"]),
        http_status=kwargs.get("http_status"),  # type: ignore[arg-type]
        okx_code=kwargs.get("okx_code"),  # type: ignore[arg-type]
        json_parse_ok=kwargs.get("json_parse_ok"),  # type: ignore[arg-type]
        redirect_followed=bool(kwargs.get("redirect_followed")),
        redirectish=bool(kwargs.get("redirectish")),
        data_count=kwargs.get("data_count"),  # type: ignore[arg-type]
        s_code=kwargs.get("s_code"),  # type: ignore[arg-type]
        ord_id=kwargs.get("ord_id"),  # type: ignore[arg-type]
        returned_clordid=kwargs.get("returned_clordid"),  # type: ignore[arg-type]
        sent_clordid=kwargs.get("sent_clordid"),  # type: ignore[arg-type]
        transport_error=kwargs.get("transport_error"),  # type: ignore[arg-type]
    )


def test_producer_and_criterion_are_bound_without_promoting_ack() -> None:
    assert LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND is True
    assert HISTORICAL_ACK_CASE_ADJUDICATION == "CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE"
    assert CASE_ADJUDICATION == "CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE"
    assert LIVE_SUBMIT_ACK_OBSERVED is True
    assert LIVE_FILL_OBSERVED is True
    assert LIVE_FEE_OBSERVED is True
    assert LIVE_SUBMIT_ACK_OBSERVED_PRODUCER.endswith(
        "submit_ack_observed_adjudication_v1.py::adjudicate_live_submit_ack_observed_v1"
    )


def test_success_conjunction_requires_all_nine_response_constituents() -> None:
    values = response_constituents_from_evidence_v1(
        http_status=200,
        okx_code="0",
        json_parse_ok=True,
        redirect_followed=False,
        redirectish=False,
        data_count=1,
        s_code="0",
        ord_id="2412345678901234567",
        returned_clordid="ptokxeproddeadbeef",
        sent_clordid="ptokxeproddeadbeef",
    )
    assert set(values) == set(ACK_RESPONSE_CONSTITUENTS)
    proof = evaluate_ack_response_conjunction_v1(constituent_values=values)
    assert proof["claim_value"] is True
    classified = _classify()
    assert classified["classification"] == CLASS_ACK_SUCCESS
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert classified["RETRY_ALLOWED"] is False
    assert classified["SECOND_SUBMIT_ALLOWED"] is False


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"json_parse_ok": False}, "PARSE_FAILURE"),
        ({"http_status": 201}, "HTTP_STATUS_NOT_200"),
        ({"http_status": 204}, "HTTP_STATUS_NOT_200"),
        ({"redirect_followed": True}, "REDIRECT_IS_UNKNOWN_NOT_ACK"),
        ({"data_count": 0}, "DATA_CARDINALITY_NOT_EXACTLY_ONE"),
        ({"data_count": 2}, "DATA_CARDINALITY_NOT_EXACTLY_ONE"),
        ({"s_code": None}, "SCODE_MISSING_OR_UNCLEAR"),
        ({"ord_id": ""}, "ORDID_MISSING"),
        ({"returned_clordid": ""}, "RETURNED_CLORDID_MISSING"),
        ({"returned_clordid": "other"}, "CLORDID_IDENTITY_MISMATCH"),
        ({"sent_clordid": ""}, "CLORDID_IDENTITY_MISMATCH"),
        ({"entry_submit_count": 2}, "SUBMIT_COUNT_NOT_ONE"),
        ({"transport_error": "UNKNOWN_SUBMIT_TIMEOUT"}, "TIMEOUT_AFTER_POSSIBLE_SEND"),
    ],
)
def test_missing_success_conjunct_is_unknown_not_ack(
    override: dict[str, object], reason: str
) -> None:
    classified = _classify(**override)
    assert classified["classification"] == CLASS_UNKNOWN
    assert classified["reason"] == reason
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert classified["RETRY_ALLOWED"] is False
    assert classified["SECOND_SUBMIT_ALLOWED"] is False


def test_top_level_code_not_zero_is_explicit_reject() -> None:
    classified = _classify(okx_code="51000")
    assert classified["classification"] == CLASS_EXPLICIT_REJECT
    assert classified["reason"] == "TOP_LEVEL_CODE_NOT_ZERO"
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert classified["RETRY_ALLOWED"] is False


def test_scode_not_zero_is_explicit_reject() -> None:
    classified = _classify(s_code="51008")
    assert classified["classification"] == CLASS_EXPLICIT_REJECT
    assert classified["reason"] == "SCODE_NOT_ZERO"
    assert classified["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert classified["RETRY_ALLOWED"] is False


def test_http_non_200_without_reject_code_is_unknown() -> None:
    classified = _classify(http_status=500, okx_code="0")
    assert classified["classification"] == CLASS_UNKNOWN
    assert classified["reason"] == "HTTP_STATUS_NOT_200"


def test_adjudicator_never_promotes_standing_field_on_injected_success() -> None:
    proof = adjudicate_live_submit_ack_observed_v1(submit_ack_evidence=_success_kwargs())
    assert proof["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["claim_value"] is False
    assert proof["classification"]["classification"] == CLASS_ACK_SUCCESS
    assert proof["field_constituent_values"]["CURRENT_PRODUCTIVE_POST_OF_FRESH_PLAN"] is False
    assert proof["field_conjunction"]["claim_value"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE"


def test_injected_source_cannot_satisfy_live_field() -> None:
    assert_injected_success_cannot_promote_live_field_v1()
    with pytest.raises(
        Section1114OfflineSurfaceError, match="INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD"
    ):
        evaluate_live_submit_ack_observed_conjunction_v1(
            constituent_values={name: True for name in ACK_FIELD_CONSTITUENTS},
            source_kind=INJECTED_EVIDENCE_SOURCE_KIND,
        )


def test_governed_live_post_conjunction_is_bound_and_observed() -> None:
    proof = evaluate_live_submit_ack_observed_conjunction_v1(
        constituent_values={name: True for name in ACK_FIELD_CONSTITUENTS},
        source_kind=ADMISSIBLE_SOURCE_KIND,
    )
    assert proof["claim_value"] is True
    assert LIVE_SUBMIT_ACK_OBSERVED is True


def test_read_only_recon_match_cannot_reclassify_as_ack() -> None:
    proof = adjudicate_live_submit_ack_observed_v1(
        submit_ack_evidence=_success_kwargs(
            read_only_recon_clordid_match=True,
            json_parse_ok=False,
            transport_error="UNKNOWN_SUBMIT_TIMEOUT",
        )
    )
    assert proof["classification"]["classification"] == CLASS_UNKNOWN
    assert proof["read_only_recon_clordid_match"] is True
    assert proof["read_only_recon_clordid_match_is_not_ack"] is True
    assert proof["LIVE_SUBMIT_ACK_OBSERVED"] is False


def test_restart_remains_ineligible_after_accounting() -> None:
    values = dict(LADDER_FIELD_DEFAULTS)
    values["LIVE_AUTONOMOUS_RECOVERY_OBSERVED"] = True
    with pytest.raises(
        Section1114OfflineSurfaceError,
        match="LADDER_ORDER_VIOLATION:LIVE_AUTONOMOUS_RECOVERY_OBSERVED",
    ):
        assert_ladder_order_v1(values)
    assert_ladder_order_v1(LADDER_FIELD_DEFAULTS)
    assert LIVE_FILL_OBSERVED is True
    assert LIVE_FEE_OBSERVED is True
    assert LADDER_FIELD_DEFAULTS["LIVE_POSITION_RECONCILED"] is True
    assert LADDER_FIELD_DEFAULTS["LIVE_ACCOUNTING_RECONSTRUCTED"] is True
    assert LADDER_FIELD_DEFAULTS["LIVE_RESTART_RECONSTRUCTED"] is False


def test_post_evidence_is_refused_by_this_go() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_submit_ack_observed_v1(submit_ack_evidence=_success_kwargs(POST_USED=True))


def test_governed_live_post_source_can_satisfy_ack_without_recon() -> None:
    proof = adjudicate_live_submit_ack_observed_v1(
        submit_ack_evidence=_success_kwargs(
            POST_USED=True,
            source_kind=ADMISSIBLE_SOURCE_KIND,
            CURRENT_PRODUCTIVE_POST_OF_FRESH_PLAN=True,
            historical_plan_reused=False,
        )
    )
    assert proof["LIVE_SUBMIT_ACK_OBSERVED"] is True
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["ACK_SOURCE_KIND"] == ADMISSIBLE_SOURCE_KIND
    assert proof["classification"]["RETRY_ALLOWED"] is False


def test_timeout_after_possible_send_cannot_second_post() -> None:
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
    classified = _classify(
        send_attempted=True,
        entry_submit_count=0,
        json_parse_ok=None,
        http_status=None,
        transport_error="UNKNOWN_SUBMIT_TIMEOUT",
    )
    assert classified["classification"] == CLASS_UNKNOWN
    assert classified["SECOND_SUBMIT_ALLOWED"] is False

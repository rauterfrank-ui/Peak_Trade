"""LIVE_FEE_OBSERVED producer, identity bind, and read-only GET tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_FEE_OBSERVED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fee_observed_adjudication_v1 import (
    adjudicate_live_fee_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fee_observed_gets_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    THIS_OWNER_GO,
    execute_fee_observed_gets_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fee_observed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    classify_identity_bound_fee_rows_v1,
    evaluate_live_fee_observed_conjunction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_gets_v1 import (
    bound_fills_get_endpoint_v1,
    bound_order_get_endpoint_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_fee_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_kind": ADMISSIBLE_SOURCE_KIND,
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FILLS_GET_PERFORMED": True,
        "fills_http_status": 200,
        "fills_okx_code": "0",
        "fills_json_parse_ok": True,
        "fills_redirect_followed": False,
        "fills_method": "GET",
        "fills_rows": [
            {
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "tradeId": "1055244",
                "fillSz": "1",
                "fillPx": "0.748",
                "fee": "-0.000374",
                "feeCcy": "USDC",
            }
        ],
        "order_row": {
            "ordId": BOUND_ORDID,
            "clOrdId": BOUND_CLORDID,
            "instId": BOUND_INSTID,
            "state": "filled",
            "sz": "1",
            "accFillSz": "1",
        },
        "LIVE_POSITION_RECONCILED": False,
    }
    payload.update(overrides)
    return payload


def test_identity_bound_actual_fee_satisfies_criterion() -> None:
    proof = adjudicate_live_fee_observed_v1(fee_evidence=_live_fee_evidence())
    assert proof["LIVE_FEE_OBSERVED"] is True
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE"
    assert proof["RAW_FEE_IF_OBSERVED"] == "-0.000374"
    assert proof["RAW_FEE_CCY_IF_OBSERVED"] == "USDC"
    assert proof["FEE_SUM_COMPUTED"] is False
    assert proof["FEE_INFERRED_FROM_RATE"] is False
    assert proof["FEE_INFERRED_FROM_PRICE_TIMES_QTY"] is False
    assert "actual venue-reported fee" in LIVE_FEE_OBSERVED_CANONICAL_DEFINITION


def test_injected_evidence_cannot_promote_live_fee() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence={
            "source_kind": "GOVERNED_OFFLINE_CONTRACT",
            "FILLS_GET_PERFORMED": True,
            "fills_http_status": 200,
            "fills_okx_code": "0",
            "fills_json_parse_ok": True,
            "fills_redirect_followed": False,
            "fills_method": "GET",
            "fills_rows": [
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fee": "-0.000374",
                    "feeCcy": "USDC",
                }
            ],
        }
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["adjudicated_value"] is False


def test_injected_true_field_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FEE_FIELD_PROMOTED_BY_INJECTED"):
        adjudicate_live_fee_observed_v1(
            fee_evidence=_live_fee_evidence(
                source_kind="GOVERNED_OFFLINE_CONTRACT",
                LIVE_FEE_OBSERVED=True,
            )
        )


def test_missing_fee_is_not_observed() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fillPx": "0.748",
                    "feeCcy": "USDC",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FEE_NOT_OBSERVED"
    assert proof["UNRESOLVED_REASON"] == "FEE_FIELD_MISSING_OR_EMPTY"


def test_empty_fee_is_not_observed() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fee": "",
                    "feeCcy": "USDC",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["UNRESOLVED_REASON"] == "FEE_FIELD_MISSING_OR_EMPTY"


def test_unparseable_fee_fails_closed() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fee": "not-a-decimal",
                    "feeCcy": "USDC",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["UNRESOLVED_REASON"] == "FEE_FIELD_UNPARSEABLE"


def test_missing_fee_ccy_fails_closed() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fee": "-0.000374",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["UNRESOLVED_REASON"] == "FEE_CCY_MISSING_OR_EMPTY"


def test_unrelated_instrument_is_identity_mismatch() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": "BTC-USD_UM_XPERP-310404",
                    "fillSz": "1",
                    "fee": "-0.000374",
                    "feeCcy": "USDC",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FEE_IDENTITY_MISMATCH_FAIL_CLOSED"


def test_competing_fee_field_is_schema_ambiguous() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fee": "-0.000374",
                    "feeCcy": "USDC",
                    "fillFee": "-0.001",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FEE_AMBIGUOUS_FAIL_CLOSED"


def test_price_times_qty_is_not_used_as_fee() -> None:
    classified = classify_identity_bound_fee_rows_v1(
        rows=[
            {
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "fillSz": "1",
                "fillPx": "0.748",
            }
        ]
    )
    assert classified["ACTUAL_FEE_OBSERVED"] is False
    assert classified["FEE_INFERRED_FROM_PRICE_TIMES_QTY"] is False
    assert classified["FEE_FIELD_MISSING_OR_EMPTY"] is True
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fillPx": "0.748",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["RAW_FEE_IF_OBSERVED"] is None


def test_zero_fee_present_is_observed() -> None:
    proof = adjudicate_live_fee_observed_v1(
        fee_evidence=_live_fee_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "fillSz": "1",
                    "fee": "0",
                    "feeCcy": "USDC",
                }
            ]
        )
    )
    assert proof["LIVE_FEE_OBSERVED"] is True
    assert proof["RAW_FEE_IF_OBSERVED"] == "0"


def test_post_in_fee_evidence_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_fee_observed_v1(fee_evidence=_live_fee_evidence(POST_USED=True))


def test_injected_true_constituents_cannot_satisfy_live_field() -> None:
    values = {
        "LIVE_FILL_OBSERVED": True,
        "CURRENT_GOVERNED_PRIVATE_FILLS_GET": True,
        "FILLS_HTTP_CONJUNCTION_SATISFIED": True,
        "AT_LEAST_ONE_IDENTITY_BOUND_FILL_ROW": True,
        "IDENTITY_BOUND_ACTUAL_FEE_PRESENT_PARSEABLE": True,
        "FEE_CCY_PRESENT_NONEMPTY": True,
        "NO_FEE_SCHEMA_AMBIGUITY": True,
        "ADMISSIBLE_PRIVATE_GET_SOURCE": True,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "FEE_NOT_INFERRED": True,
    }
    with pytest.raises(Section1114OfflineSurfaceError, match="INJECTED_EVIDENCE"):
        evaluate_live_fee_observed_conjunction_v1(
            constituent_values=values,
            source_kind="GOVERNED_OFFLINE_CONTRACT",
        )


def test_fake_transport_gets_are_get_only_and_identity_scoped() -> None:
    order_body = {
        "code": "0",
        "data": [
            {
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "state": "filled",
                "sz": "1",
                "accFillSz": "1",
            }
        ],
    }
    fills_body = {
        "code": "0",
        "data": [
            {
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "fillSz": "1",
                "fee": "-0.000374",
                "feeCcy": "USDC",
            }
        ],
    }
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/trade/order": json.dumps(order_body).encode("utf-8"),
            "/api/v5/trade/fills": json.dumps(fills_body).encode("utf-8"),
        }
    )
    pack = execute_fee_observed_gets_v1(
        owner_go=THIS_OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        transport=transport,
    )
    assert pack["POST_USED"] is False
    assert pack["GET_REQUEST_COUNT"] == 2
    assert pack["ENDPOINTS"] == [
        bound_order_get_endpoint_v1(),
        bound_fills_get_endpoint_v1(),
    ]
    assert "ordId=3893505043080286208" in pack["ENDPOINTS"][0]
    assert "ordId=3893505043080286208" in pack["ENDPOINTS"][1]
    proof = adjudicate_live_fee_observed_v1(fee_evidence=pack)
    assert proof["LIVE_FEE_OBSERVED"] is True
    assert proof["RAW_FEE_IF_OBSERVED"] == "-0.000374"
    assert all(call.method == "GET" for call in transport.calls)


def test_owner_go_and_sha_mismatch_fail_closed() -> None:
    transport = RecordingFakeCanaryTransportV1()
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_fee_observed_gets_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            transport=transport,
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_fee_observed_gets_v1(
            owner_go=THIS_OWNER_GO,
            origin_main_sha="deadbeef",
            transport=transport,
        )

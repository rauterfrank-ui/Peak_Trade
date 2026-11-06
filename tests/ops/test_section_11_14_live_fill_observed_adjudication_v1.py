"""LIVE_FILL_OBSERVED producer, identity bind, and read-only GET tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_adjudication_v1 import (
    adjudicate_live_fill_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_gets_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    THIS_OWNER_GO,
    bound_fills_get_endpoint_v1,
    bound_order_get_endpoint_v1,
    execute_fill_observed_gets_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    exact_identity_match_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    LIVE_FILL_OBSERVED_CANONICAL_DEFINITION,
    classify_identity_bound_fill_rows_v1,
    evaluate_live_fill_observed_conjunction_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_fill_evidence(**overrides: object) -> dict[str, object]:
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
                "tradeId": "tr-1",
                "fillSz": "1",
                "fillPx": "0.7483",
                "ts": "1725460000000",
                "side": "buy",
            }
        ],
        "order_row": {
            "ordId": BOUND_ORDID,
            "clOrdId": BOUND_CLORDID,
            "instId": BOUND_INSTID,
            "state": "filled",
            "sz": "1",
            "accFillSz": "1",
            "avgPx": "0.7483",
        },
        "LIVE_FEE_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
    }
    payload.update(overrides)
    return payload


def test_bound_identity_is_exact_and_rejects_nearest_clordid() -> None:
    match = exact_identity_match_v1(
        ord_id=BOUND_ORDID,
        clordid=BOUND_CLORDID,
        inst_id=BOUND_INSTID,
    )
    assert match["ORDER_IDENTITY_MATCH"] is True
    near = exact_identity_match_v1(
        ord_id=BOUND_ORDID,
        clordid=BOUND_CLORDID[:-1] + "1",
        inst_id=BOUND_INSTID,
    )
    assert near["ORDER_IDENTITY_MATCH"] is False
    assert near["CLORDID_MATCH"] is False


def test_unrelated_instrument_fill_is_not_identity_bound() -> None:
    classified = classify_identity_bound_fill_rows_v1(
        rows=[
            {
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": "BTC-USD_UM_XPERP-310404",
                "tradeId": "other",
                "fillSz": "1",
            }
        ]
    )
    assert classified["AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW"] is False


def test_injected_evidence_cannot_promote_live_fill() -> None:
    proof = adjudicate_live_fill_observed_v1(
        fill_evidence={
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
                    "tradeId": "tr-1",
                }
            ],
        }
    )
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["adjudicated_value"] is False


def test_live_identity_bound_fill_row_satisfies_criterion() -> None:
    proof = adjudicate_live_fill_observed_v1(fill_evidence=_live_fill_evidence())
    assert proof["LIVE_FILL_OBSERVED"] is True
    assert proof["FULL_FILL_OBSERVED"] is True
    assert proof["PARTIAL_FILL_OBSERVED"] is False
    assert proof["NO_FILL_OBSERVED"] is False
    assert proof["LIVE_FEE_OBSERVED"] is False
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FILL_OBSERVED_FEE_INELIGIBLE"
    assert "at least one admissible executed fill" in LIVE_FILL_OBSERVED_CANONICAL_DEFINITION
    assert proof["RAW_REMAINING_QTY_IF_OBSERVED"] is None
    assert proof["RAW_ORDER_SZ_IF_OBSERVED"] == "1"


def test_remaining_qty_is_not_inferred_from_sz() -> None:
    proof = adjudicate_live_fill_observed_v1(fill_evidence=_live_fill_evidence())
    assert proof["RAW_REMAINING_QTY_IF_OBSERVED"] is None
    assert proof["RAW_ORDER_SZ_IF_OBSERVED"] == "1"
    assert proof["ORDER_ACCFILLSZ"] == "1"


def test_partial_fill_is_not_normalized_to_full() -> None:
    proof = adjudicate_live_fill_observed_v1(
        fill_evidence=_live_fill_evidence(
            fills_rows=[
                {
                    "ordId": BOUND_ORDID,
                    "clOrdId": BOUND_CLORDID,
                    "instId": BOUND_INSTID,
                    "tradeId": "tr-p",
                    "fillSz": "0.5",
                    "fillPx": "0.7483",
                }
            ],
            order_row={
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "state": "partially_filled",
                "sz": "1",
                "accFillSz": "0.5",
            },
        )
    )
    assert proof["LIVE_FILL_OBSERVED"] is True
    assert proof["PARTIAL_FILL_OBSERVED"] is True
    assert proof["FULL_FILL_OBSERVED"] is False


def test_ack_alone_is_not_a_fill() -> None:
    proof = adjudicate_live_fill_observed_v1(fill_evidence=None)
    assert proof["LIVE_FILL_OBSERVED"] is False


def test_empty_fills_and_unfilled_working_order_is_no_fill() -> None:
    proof = adjudicate_live_fill_observed_v1(
        fill_evidence=_live_fill_evidence(
            fills_rows=[],
            order_row={
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "state": "live",
                "sz": "1",
                "accFillSz": "0",
            },
        )
    )
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["NO_FILL_OBSERVED"] is True
    assert proof["CASE_ADJUDICATION"] == "CASE_NO_FILL_OBSERVED"


def test_order_state_filled_without_fill_row_is_contradictory() -> None:
    proof = adjudicate_live_fill_observed_v1(
        fill_evidence=_live_fill_evidence(
            fills_rows=[],
            order_row={
                "ordId": BOUND_ORDID,
                "clOrdId": BOUND_CLORDID,
                "instId": BOUND_INSTID,
                "state": "filled",
                "sz": "1",
                "accFillSz": "1",
            },
        )
    )
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["CONTRADICTORY_FILL_EVIDENCE"] is True
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FILL_CONTRADICTORY_FAIL_CLOSED"


def test_empty_fills_and_missing_order_is_unresolved() -> None:
    proof = adjudicate_live_fill_observed_v1(
        fill_evidence=_live_fill_evidence(fills_rows=[], order_row={})
    )
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["NO_FILL_OBSERVED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_FILL_UNRESOLVED_FAIL_CLOSED"


def test_post_in_fill_evidence_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_fill_observed_v1(fill_evidence=_live_fill_evidence(POST_USED=True))


def test_injected_true_constituents_cannot_satisfy_live_field() -> None:
    values = {
        "LIVE_SUBMIT_ACK_OBSERVED": True,
        "CURRENT_GOVERNED_PRIVATE_FILLS_GET": True,
        "FILLS_HTTP_CONJUNCTION_SATISFIED": True,
        "AT_LEAST_ONE_IDENTITY_BOUND_NONEMPTY_FILLSZ_ROW": True,
        "ADMISSIBLE_PRIVATE_GET_SOURCE": True,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
    }
    with pytest.raises(Section1114OfflineSurfaceError, match="INJECTED_EVIDENCE"):
        evaluate_live_fill_observed_conjunction_v1(
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
                "state": "live",
                "sz": "1",
                "accFillSz": "0",
            }
        ],
    }
    fills_body = {"code": "0", "data": []}
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/trade/order": json.dumps(order_body).encode("utf-8"),
            "/api/v5/trade/fills": json.dumps(fills_body).encode("utf-8"),
        }
    )
    pack = execute_fill_observed_gets_v1(
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
    proof = adjudicate_live_fill_observed_v1(fill_evidence=pack)
    assert proof["LIVE_FILL_OBSERVED"] is False
    assert proof["NO_FILL_OBSERVED"] is True
    assert all(call.method == "GET" for call in transport.calls)


def test_owner_go_and_sha_mismatch_fail_closed() -> None:
    transport = RecordingFakeCanaryTransportV1()
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_fill_observed_gets_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            transport=transport,
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_fill_observed_gets_v1(
            owner_go=THIS_OWNER_GO,
            origin_main_sha="deadbeef",
            transport=transport,
        )

"""LIVE_POSITION_RECONCILED producer, identity bind, and read-only GET tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.position_reconciled_adjudication_v1 import (
    adjudicate_live_position_reconciled_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.position_reconciled_gets_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    THIS_OWNER_GO,
    bound_positions_get_endpoint_v1,
    execute_position_reconciled_gets_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.position_reconciled_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    EMPTY_DATA_IS_ZERO,
    evaluate_live_position_reconciled_conjunction_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_position_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_kind": ADMISSIBLE_SOURCE_KIND,
        "POST_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "POSITIONS_GET_PERFORMED": True,
        "positions_http_status": 200,
        "positions_okx_code": "0",
        "positions_json_parse_ok": True,
        "positions_redirect_followed": False,
        "positions_method": "GET",
        "positions_data_is_list": True,
        "position_rows": [
            {
                "instId": BOUND_INSTID,
                "instType": "FUTURES",
                "posSide": BOUND_POS_SIDE,
                "posId": "3893505043080286999",
                "pos": BOUND_FILL_SZ,
                "mgnMode": "cross",
            }
        ],
        "LIVE_ACCOUNTING_RECONSTRUCTED": False,
    }
    payload.update(overrides)
    return payload


def test_identity_bound_pos_equals_fill_sz_satisfies_criterion() -> None:
    proof = adjudicate_live_position_reconciled_v1(position_evidence=_live_position_evidence())
    assert proof["LIVE_POSITION_RECONCILED"] is True
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["SECTION_11_14_COMPLETE"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE"
    assert proof["RAW_POSITION_QTY_IF_OBSERVED"] == "1"
    assert proof["POSITION_SEMANTICS_STATUS"] == "RECONCILED"
    assert proof["EMPTY_DATA_IS_ZERO"] is False
    assert "current venue-reported position reconciled" in (
        LIVE_POSITION_RECONCILED_CANONICAL_DEFINITION
    )


def test_injected_evidence_cannot_promote_live_position() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(source_kind="GOVERNED_OFFLINE_CONTRACT")
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["adjudicated_value"] is False


def test_injected_true_field_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POSITION_FIELD_PROMOTED_BY_INJECTED"):
        adjudicate_live_position_reconciled_v1(
            position_evidence=_live_position_evidence(
                source_kind="GOVERNED_OFFLINE_CONTRACT",
                LIVE_POSITION_RECONCILED=True,
            )
        )


def test_empty_data_is_not_zero_and_not_reconciled() -> None:
    assert EMPTY_DATA_IS_ZERO is False
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[],
            positions_data_is_list=True,
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_EMPTY_DATA_NOT_ZERO"
    assert proof["UNRESOLVED_REASON"] == "EMPTY_DATA_NOT_ZERO"
    assert proof["POSITION_SEMANTICS_STATUS"] == "EMPTY_DATA_NOT_ZERO"
    assert proof["EMPTY_DATA_OBSERVED"] is True
    assert proof["EMPTY_DATA_IS_ZERO"] is False


def test_pos_zero_row_is_not_reconciled() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "pos": "0",
                    "posId": "1",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_POS_ZERO_ROW_NOT_RECONCILED"
    assert proof["POSITION_SEMANTICS_STATUS"] == "ROW_WITH_POS_ZERO"
    assert proof["RAW_POSITION_QTY_IF_OBSERVED"] == "0"


def test_qty_divergence_is_not_reconciled() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "pos": "2",
                    "posId": "1",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["UNRESOLVED_REASON"] == "POS_QTY_DIVERGES_FROM_BOUND_FILL_SZ"
    assert proof["POSITION_SEMANTICS_STATUS"] == "QTY_DIVERGENCE"


def test_unrelated_instrument_is_identity_mismatch() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": "BTC-USD_UM_XPERP-310404",
                    "posSide": BOUND_POS_SIDE,
                    "pos": "1",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_POSITION_IDENTITY_MISMATCH_FAIL_CLOSED"
    assert proof["POSITION_SEMANTICS_STATUS"] == "IDENTITY_MISMATCH"


def test_pos_side_mismatch_is_identity_mismatch() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": "long",
                    "pos": "1",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_POSITION_IDENTITY_MISMATCH_FAIL_CLOSED"


def test_missing_pos_is_not_reconciled() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "posId": "1",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["UNRESOLVED_REASON"] == "POS_FIELD_MISSING_OR_EMPTY"


def test_unparseable_pos_fails_closed() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "pos": "not-a-decimal",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["UNRESOLVED_REASON"] == "POS_FIELD_UNPARSEABLE"


def test_ambiguous_duplicate_rows_fail_closed() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "pos": "1",
                    "posId": "a",
                },
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "pos": "1",
                    "posId": "b",
                },
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_POSITION_AMBIGUOUS_FAIL_CLOSED"


def test_competing_pos_field_is_schema_ambiguous() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(
            position_rows=[
                {
                    "instId": BOUND_INSTID,
                    "posSide": BOUND_POS_SIDE,
                    "pos": "1",
                    "posSize": "2",
                }
            ]
        )
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_POSITION_AMBIGUOUS_FAIL_CLOSED"


def test_fill_qty_alone_is_not_position() -> None:
    proof = adjudicate_live_position_reconciled_v1(
        position_evidence=_live_position_evidence(position_rows=[], positions_data_is_list=True)
    )
    assert proof["LIVE_POSITION_RECONCILED"] is False
    assert proof["RAW_POSITION_QTY_IF_OBSERVED"] is None


def test_post_in_position_evidence_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_position_reconciled_v1(
            position_evidence=_live_position_evidence(POST_USED=True)
        )


def test_injected_true_constituents_cannot_satisfy_live_field() -> None:
    values = {
        "LIVE_FEE_OBSERVED": True,
        "CURRENT_GOVERNED_PRIVATE_POSITIONS_GET": True,
        "POSITIONS_HTTP_CONJUNCTION_SATISFIED": True,
        "EXACTLY_ONE_IDENTITY_BOUND_POSITION_ROW": True,
        "IDENTITY_BOUND_POS_PRESENT_PARSEABLE": True,
        "POS_EQUALS_BOUND_FILL_SZ": True,
        "EMPTY_DATA_NOT_TREATED_AS_ZERO": True,
        "ADMISSIBLE_PRIVATE_GET_SOURCE": True,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
        "NOT_INFERRED_FROM_FILL_FEE_OR_ORDER_STATE": True,
    }
    with pytest.raises(Section1114OfflineSurfaceError, match="INJECTED_EVIDENCE"):
        evaluate_live_position_reconciled_conjunction_v1(
            constituent_values=values,
            source_kind="GOVERNED_OFFLINE_CONTRACT",
        )


def test_fake_transport_get_is_get_only_and_identity_scoped() -> None:
    body = {
        "code": "0",
        "data": [
            {
                "instId": BOUND_INSTID,
                "instType": "FUTURES",
                "posSide": BOUND_POS_SIDE,
                "pos": "1",
                "posId": "3893505043080286999",
                "mgnMode": "cross",
            }
        ],
    }
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/account/positions": json.dumps(body).encode("utf-8"),
        }
    )
    pack = execute_position_reconciled_gets_v1(
        owner_go=THIS_OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        transport=transport,
    )
    assert pack["POST_USED"] is False
    assert pack["GET_REQUEST_COUNT"] == 1
    assert pack["ENDPOINTS"] == [bound_positions_get_endpoint_v1()]
    assert "instId=SUI-USD_UM_XPERP-310404" in pack["ENDPOINTS"][0]
    assert "instType=FUTURES" in pack["ENDPOINTS"][0]
    proof = adjudicate_live_position_reconciled_v1(position_evidence=pack)
    assert proof["LIVE_POSITION_RECONCILED"] is True
    assert proof["RAW_POSITION_QTY_IF_OBSERVED"] == "1"
    assert all(call.method == "GET" for call in transport.calls)


def test_owner_go_and_sha_mismatch_fail_closed() -> None:
    transport = RecordingFakeCanaryTransportV1()
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_position_reconciled_gets_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            transport=transport,
        )
    with pytest.raises(Section1114OfflineSurfaceError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_position_reconciled_gets_v1(
            owner_go=THIS_OWNER_GO,
            origin_main_sha="deadbeef",
            transport=transport,
        )

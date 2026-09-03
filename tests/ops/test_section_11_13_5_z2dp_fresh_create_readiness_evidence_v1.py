"""§11.13.5.Z2DP fresh create-readiness GET package tests. Recording transport only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    REQUIRED_SECRETREF_URI,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.adjudicate_v1 import (
    adjudicate_create_readiness_v1,
    adjudicate_position_mode_submit_body_semantics_v1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.constants_v1 import (
    AUTHORIZED_HOST,
    EXPECTED_ORIGIN_MAIN_SHA,
    FUNDING_GET_REQUIRED,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    POST_ALLOWED,
    PREDECESSOR_SLICE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.execute_v1 import (
    Z2DPCreateReadinessGetError,
    execute_fresh_create_readiness_evidence_v1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.persist_claims_v1 import (
    CLAIMS,
)

INSTRUMENTS = {
    "code": "0",
    "data": [
        {
            "instId": DEFAULT_INSTRUMENT_ID,
            "instType": "FUTURES",
            "ruleType": "xperp",
            "minSz": "1",
            "lotSz": "1",
            "tickSz": "0.0001",
            "ctVal": "1",
            "ctValCcy": "SUI",
            "settleCcy": "USDC",
            "state": "live",
            "maxLmtSz": "100000000",
            "maxMktSz": "100000",
        }
    ],
}
TICKER = {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "last": "0.8209"}]}
EMPTY = {"code": "0", "data": []}
MAX_AVAILABLE = {
    "code": "0",
    "data": [{"instId": DEFAULT_INSTRUMENT_ID, "maxBuy": "100", "maxSell": "100"}],
}
PRICE_BAND = {
    "code": "0",
    "data": [
        {
            "instId": DEFAULT_INSTRUMENT_ID,
            "instType": "FUTURES",
            "buyLmt": "2.0000",
            "sellLmt": "0.0001",
            "ts": "1725000000000",
            "enabled": True,
        }
    ],
}
LEVERAGE = {
    "code": "0",
    "data": [
        {
            "instId": DEFAULT_INSTRUMENT_ID,
            "ccy": "",
            "mgnMode": "cross",
            "posSide": "net",
            "lever": "5",
        }
    ],
}
POS_MODE = {
    "code": "0",
    "data": [
        {
            "uid": "856964404452495999",
            "mainUid": "856964404452495999",
            "acctLv": "2",
            "posMode": "net_mode",
            "perm": "read_only,trade",
            "settleCcy": "USDC",
            "label": "PeakTrade-Live-Canary-MinExp",
        }
    ],
}
AVAILABLE_MARGIN = {
    "code": "0",
    "msg": "",
    "data": [
        {
            "adjEq": "12.5",
            "availEq": "12.5",
            "totalEq": "12.5",
            "uTime": "1788042908790",
            "details": [
                {
                    "ccy": "USDC",
                    "availEq": "10.25",
                    "availBal": "10.10",
                    "eq": "10.25",
                    "cashBal": "10.25",
                    "uTime": "1788042908790",
                }
            ],
        }
    ],
}


def _transport() -> RecordingFakeCanaryTransportV1:
    return RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/public/instruments": json.dumps(INSTRUMENTS).encode(),
            "/api/v5/market/ticker": json.dumps(TICKER).encode(),
            "/api/v5/public/price-limit": json.dumps(PRICE_BAND).encode(),
            "/api/v5/account/config": json.dumps(POS_MODE).encode(),
            "/api/v5/account/positions": json.dumps(EMPTY).encode(),
            "/api/v5/account/leverage-info": json.dumps(LEVERAGE).encode(),
            "/api/v5/account/balance": json.dumps(AVAILABLE_MARGIN).encode(),
            "/api/v5/account/max-size": json.dumps(MAX_AVAILABLE).encode(),
            "/api/v5/trade/orders-pending": json.dumps(EMPTY).encode(),
            "/api/v5/trade/orders-algo-pending": json.dumps(EMPTY).encode(),
        }
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO.endswith("POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1")
    assert THIS_SLICE == "11.13.5.Z2DP"
    assert PREDECESSOR_SLICE == "11.13.5.Z2DO"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert MAX_NETWORK_REQUEST_COUNT == 15
    assert FUNDING_GET_REQUIRED is False
    assert POST_ALLOWED is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["CURRENT_PRODUCTIVE_WIRE_REACHABLE"] is False
    assert CLAIMS["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert CLAIMS["POSITION_MODE_SUBMIT_BODY_SEMANTICS_STANDING"] == "UNPROVEN"
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert REQUIRED_SECRETREF_URI.endswith("/okx")
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_position_mode_remains_unproven_without_inventing_posside() -> None:
    result = adjudicate_position_mode_submit_body_semantics_v1(pos_mode_raw="net_mode")
    assert result["POSITION_MODE_SUBMIT_BODY_SEMANTICS"] == "UNPROVEN"
    assert result["POSITION_MODE_FAIL_CLOSED"] is True
    assert result["POSITION_MODE_READY"] is False


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(Z2DPCreateReadinessGetError, match="OWNER_GO_MISMATCH"):
        execute_fresh_create_readiness_evidence_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=_transport(),
        )
    with pytest.raises(Z2DPCreateReadinessGetError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_fresh_create_readiness_evidence_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path,
            transport=_transport(),
        )


def test_fixture_package_collects_gets_without_post(tmp_path: Path) -> None:
    transport = _transport()
    result = execute_fresh_create_readiness_evidence_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    summary = result["summary"]
    assert summary["POST_COUNT"] == 0
    assert summary["FUNDING_GET_PERFORMED"] is False
    assert summary["POSITIONS_GET_PERFORMED"] is True
    assert summary["POSITION_MODE_SUBMIT_BODY_SEMANTICS"] == "UNPROVEN"
    assert summary["POSITION_MODE_FAIL_CLOSED"] is True
    assert summary["PREREQUISITE_08_CLOSED"] is False
    assert summary["CURRENT_PRODUCTIVE_WIRE_REACHABLE"] is False
    assert summary["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert summary["CREATE_ACCOUNT_IDENTITY_READY"] is True
    assert summary["VENUE_NONZERO_CAPACITY"] == "PROVEN_POSITIVE"
    assert summary["CURRENT_ROUTE_C_QUANTITY_ADMISSIBILITY"] == (
        "POTENTIALLY_ADMISSIBLE_SUBJECT_TO_29P"
    )
    methods = {call.method for call in transport.calls}
    assert methods == {"GET"}
    assert all(
        "/trade/order" != call.endpoint.split("?", 1)[0] or call.method == "GET"
        for call in transport.calls
    )
    assert not any(call.method == "POST" for call in transport.calls)
    pack = Path(result["EVIDENCE_PACK"])
    snapshot = json.loads((pack / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8"))
    assert snapshot["SECRET_VALUES_INCLUDED"] is False
    assert snapshot["WRITE_REQUEST_COUNT"] == 0
    text = json.dumps(snapshot)
    assert "api_secret" not in text
    assert "passphrase" not in text.lower() or "OK-ACCESS-PASSPHRASE" not in text


def test_nonzero_position_hard_stops_after_persist(tmp_path: Path) -> None:
    transport = _transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {
            "code": "0",
            "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1", "mgnMode": "cross"}],
        }
    ).encode()
    with pytest.raises(Z2DPCreateReadinessGetError, match="NONZERO_TARGET_POSITION_HARD_STOP"):
        execute_fresh_create_readiness_evidence_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=transport,
        )
    packs = list(tmp_path.iterdir())
    assert packs
    adjudication = json.loads((packs[0] / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["PREREQUISITE_08_CLOSED"] is True
    assert adjudication["TARGET_POSITION_STATE"] == "TARGET_POSITION_NONZERO_PROVEN"


def test_adjudication_blocks_on_position_mode_when_other_gates_green() -> None:
    result = adjudicate_create_readiness_v1(
        observations={
            "ACCOUNT_IDENTITY_OBSERVED": True,
            "ACCOUNT_UID": "856964404452495999",
            "ACCOUNT_CONFIG_OK": True,
            "POS_MODE_RAW": "net_mode",
            "POSITIONS_OK": True,
            "TARGET_POSITION_STATE": "TARGET_POSITION_NOT_OBSERVED",
            "OPEN_POSITION_CAP": {
                "admitted": True,
                "reason_code": "ALLOW_NO_OPEN_POSITION",
                "open_instrument_ids": [],
            },
            "LEVERAGE_OK": True,
            "AVAILABLE_MARGIN_OK": True,
            "AVAIL_EQ_STATUS": "OBSERVED",
            "AVAIL_EQ_RAW": "10.25",
            "MAX_AVAILABLE_OK": True,
            "MAX_BUY_RAW": "100",
            "MAX_SELL_RAW": "100",
            "MAX_SIZE_OK": True,
            "INSTRUMENT_STATE_OK": True,
            "PRICE_BAND_OK": True,
            "TICKER_OK": True,
            "PENDING_ORDINARY_OK": True,
            "PENDING_ORDINARY_COUNT": 0,
            "CATEGORY_C_OK": True,
            "CATEGORY_C_OUTCOME": "TARGET_CATEGORY_C_NOT_OBSERVED",
        }
    )
    assert result["CREATE_ACCOUNT_IDENTITY_READY"] is True
    assert result["PRETRADE_GATES_READY"] is True
    assert result["FUNDING_EXPOSURE_READY"] is True
    assert result["POSITION_MODE_READY"] is False
    assert result["CREATE_READINESS_AFTER_FRESH_EVIDENCE"] == ("BLOCKED_BY_POSITION_MODE_SEMANTICS")
    assert result["PREREQUISITE_08_CLOSED"] is False
    assert result["FRESHNESS_MATRIX"]["FUNDING_ACCOUNT"] == "NOT_APPLICABLE"
    assert result["FRESHNESS_MATRIX"]["AVAILABLE_MARGIN"] == (
        "PROVEN_CURRENT_BUT_SENDTIME_REFRESH_REQUIRED"
    )

"""§11.13.5.Z2DS post-Z2DR runtime read-only evidence tests. Recording transport only."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NOT_OBSERVED,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.adjudicate_v1 import (
    adjudicate_runtime_read_only_evidence_v1,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.constants_v1 import (
    AUTHORIZED_HOST,
    EXPECTED_ORIGIN_MAIN_SHA,
    OBSERVATION_AUTH_FAILED,
    OBSERVATION_OBSERVED,
    OWNER_GO,
    POST_ALLOWED,
    PREDECESSOR_SLICE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.execute_v1 import (
    Z2DSRuntimeReadOnlyEvidenceGetError,
    execute_runtime_read_only_evidence_v1,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.persist_claims_v1 import (
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
AUTH_FAILED_BODY = json.dumps({"code": "50110", "msg": "IP whitelist", "data": []}).encode()


def _transport_ok() -> RecordingFakeCanaryTransportV1:
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
    assert OWNER_GO.endswith("POST_Z2DR_RUNTIME_READ_ONLY_EVIDENCE_MAX_LEVERAGE_V1")
    assert PREDECESSOR_SLICE == "11.13.5.Z2DR"
    assert THIS_SLICE == "11.13.5.Z2DS"
    assert POST_ALLOWED is False
    assert CLAIMS["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False


def test_owner_go_and_origin_sha_gates() -> None:
    with pytest.raises(Z2DSRuntimeReadOnlyEvidenceGetError, match="OWNER_GO_MISMATCH"):
        execute_runtime_read_only_evidence_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=Path("/tmp/z2ds-evidence"),
            transport=_transport_ok(),
        )


def test_execute_get_only_with_recording_transport(tmp_path: Path) -> None:
    result = execute_runtime_read_only_evidence_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=_transport_ok(),
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert result["summary"]["POST_COUNT"] == 0
    assert result["summary"]["WRITE_REQUEST_COUNT"] == 0
    assert result["adjudication"]["POSITION_MODE_SUBMIT_BODY_SEMANTICS"] == "UNPROVEN"
    assert result["adjudication"]["MAX_SAFE_READ_ONLY_RUNTIME_BUNDLE_REMAINING"] == 0


def test_adjudicate_auth_failure_on_private_gets() -> None:
    snapshot = {
        "REQUESTS": [
            {
                "ENDPOINT": "/api/v5/account/positions",
                "HTTP_STATUS": 401,
                "OKX_CODE": "50110",
                "PARSER_RESULT": "AUTH_FAILED",
            }
        ]
    }
    out = adjudicate_runtime_read_only_evidence_v1(
        observations={"TARGET_POSITION_STATE": TARGET_POSITION_NOT_OBSERVED},
        snapshot=snapshot,
    )
    assert out["TARGET_POSITION_OBSERVATION"] == OBSERVATION_AUTH_FAILED
    assert out["EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"] is False


def test_adjudicate_public_observations_without_private_auth() -> None:
    out = adjudicate_runtime_read_only_evidence_v1(
        observations={
            "INSTRUMENT_STATE_OK": True,
            "PRICE_BAND_OK": True,
        },
        snapshot={"REQUESTS": []},
    )
    assert out["INSTRUMENT_STATE_CURRENT"] == OBSERVATION_OBSERVED
    assert out["PRICE_LIMIT_CURRENT"] == OBSERVATION_OBSERVED


def test_authorized_host_is_eea() -> None:
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert REQUIRED_SECRETREF_URI.startswith("secretref://")

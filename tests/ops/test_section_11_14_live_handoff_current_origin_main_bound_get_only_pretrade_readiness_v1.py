"""GET-only current-origin/main pretrade readiness tests. No live network."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.constants_v1 import (
    ENDPOINT_PATH_ALLOWLIST,
    EXISTING_SURFACE_CENSUS,
    FORBIDDEN_IMPORT_MARKERS,
    OBSOLETE_FROZEN_ORIGIN_MAIN_SHA,
    PATH_ACCOUNT_CONFIG,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.http_get_only_v1 import (
    GetOnlyHttpClientV1,
    GetOnlyHttpError,
    RecordingFakeGetOnlyTransportV1,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.orchestrator_v1 import (
    GetOnlyPretradeError,
    persist_get_only_pretrade_evidence_v1,
    run_get_only_pretrade_readiness_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)

PACKAGE_DIR = Path(
    "src/ops/section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1"
)
ORIGIN_SHA = "7f8dcf6d120f0ec59bcb932f5f6d1e8a6360b663"

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
            "acctLv": "2",
            "posMode": "net_mode",
            "perm": "read_only,trade",
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


TRADE_FEE = {
    "code": "0",
    "data": [
        {
            "instType": "FUTURES",
            "instFamily": "SUI-USD_UM_XPERP",
            "taker": "-0.0005",
            "maker": "-0.0002",
            "takerUSDC": "-0.0005",
            "makerUSDC": "-0.0002",
            "delivery": "0.0003",
        }
    ],
}


def _bodies() -> dict[str, bytes]:
    return {
        "/api/v5/public/instruments": json.dumps(INSTRUMENTS).encode(),
        "/api/v5/market/ticker": json.dumps(TICKER).encode(),
        "/api/v5/public/price-limit": json.dumps(PRICE_BAND).encode(),
        "/api/v5/account/positions": json.dumps(EMPTY).encode(),
        "/api/v5/account/max-size": json.dumps(MAX_AVAILABLE).encode(),
        "/api/v5/account/leverage-info": json.dumps(LEVERAGE).encode(),
        "/api/v5/account/config": json.dumps(POS_MODE).encode(),
        "/api/v5/account/balance": json.dumps(AVAILABLE_MARGIN).encode(),
        "/api/v5/account/trade-fee": json.dumps(TRADE_FEE).encode(),
    }


def _run(**overrides: object) -> tuple[dict, RecordingFakeGetOnlyTransportV1]:
    transport = RecordingFakeGetOnlyTransportV1(bodies_by_path=_bodies())
    kwargs: dict = {
        "origin_main_sha": ORIGIN_SHA,
        "origin_main_tree": "21b04907f77ac84c9eb52d994c91deaf9a827168",
        "transport": transport,
        "header_provider": lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
    }
    kwargs.update(overrides)
    return run_get_only_pretrade_readiness_v1(**kwargs), transport


def test_package_source_has_no_post_or_submit_imports() -> None:
    for path in PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported.append(str(node.module or ""))
                imported.extend(alias.name for alias in node.names)
        blob = " ".join(imported)
        for marker in FORBIDDEN_IMPORT_MARKERS:
            assert marker not in blob, f"{path}:{marker}"
        assert "submit_transport_v1" not in blob
        assert "section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1" not in blob


def test_post_is_fail_closed_before_wire() -> None:
    client = GetOnlyHttpClientV1(transport=RecordingFakeGetOnlyTransportV1())
    with pytest.raises(GetOnlyHttpError, match="HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST"):
        client.post(endpoint=PATH_ACCOUNT_CONFIG)
    with pytest.raises(GetOnlyHttpError, match="HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST"):
        client.request(method="POST", endpoint=PATH_ACCOUNT_CONFIG)
    assert client.counters.write_request_count == 0
    assert client.counters.get_request_count == 0


def test_mutation_endpoint_is_blocked() -> None:
    client = GetOnlyHttpClientV1(transport=RecordingFakeGetOnlyTransportV1())
    with pytest.raises(GetOnlyHttpError, match="MUTATION_ENDPOINT_HARD_BLOCK"):
        client.get(endpoint="/api/v5/trade/order")


def test_unallowlisted_endpoint_is_blocked() -> None:
    client = GetOnlyHttpClientV1(transport=RecordingFakeGetOnlyTransportV1())
    with pytest.raises(GetOnlyHttpError, match="ENDPOINT_NOT_ALLOWLISTED"):
        client.get(endpoint="/api/v5/public/time")


def test_orchestrator_has_no_owner_go_parameter() -> None:
    params = inspect.signature(run_get_only_pretrade_readiness_v1).parameters
    assert "owner_go" not in params
    result, _transport = _run()
    assert result["OWNER_GO_CONSUMED"] is False
    assert result["OWNER_GO_PARAMETER_PRESENT"] is False


def test_obsolete_sha_is_not_an_invocation_gate() -> None:
    other = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    result, _transport = _run(origin_main_sha=other)
    assert result["RECORDED_ORIGIN_MAIN_SHA"] == other
    assert result["OBSOLETE_SHA_GATE_USED"] is False
    assert result["OBSOLETE_FROZEN_ORIGIN_MAIN_SHA"] == OBSOLETE_FROZEN_ORIGIN_MAIN_SHA


def test_happy_path_get_only_fixture_completes_non_executing_envelope() -> None:
    result, transport = _run()
    assert all(call.method == "GET" for call in transport.calls)
    assert result["GET_ONLY_SURFACE_POST_REACHABLE"] is False
    assert result["GET_ONLY_SURFACE_SUBMIT_REACHABLE"] is False
    assert result["COUNTERS"]["WRITE_REQUEST_COUNT"] == 0
    assert result["GET_ENDPOINT_COUNT"] == 9
    assert result["GET_SUCCESS_COUNT"] == 9
    assert result["PREDICATES"]["ACCOUNT_MODE_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["POSITION_MODE_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["INSTRUMENT_STATE_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["PRICE_SOURCE_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["PRICE_BAND_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["LEVERAGE_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["AVAILABLE_MARGIN_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["MAX_AVAILABLE_MAX_SIZE_CURRENT"]["status"] == "PASS"
    assert result["PREDICATES"]["EXACT_PRICE_SEMANTICS_BOUND"]["status"] == "PASS"
    assert result["PREDICATES"]["FEE_POLICY_BOUND"]["status"] == "PASS"
    assert result["PREDICATES"]["SLIPPAGE_POLICY_BOUND"]["status"] == "PASS"
    assert result["PREDICATES"]["MARGIN_MODE_CURRENT"]["status"] == "NOT_OBSERVED"
    assert result["PREDICATES"]["EXPECTED_PRE_EXISTING_POSITION"]["status"] == "NOT_OBSERVED"
    assert result["EXPECTED_FEES"] != "UNKNOWN"
    assert result["SLIPPAGE_BOUND"] != "UNKNOWN"
    assert result["EXACT_EXECUTION_ENVELOPE_COMPLETE"] is True
    assert result["TECHNICAL_EXECUTION_READY"] is True
    assert result["OWNER_EXECUTION_AUTHORIZED"] is False
    assert result["PREDICATES"]["OWNER_EXECUTION_AUTHORIZED"]["status"] == "FAIL_CLOSED"
    assert result["PREDICATES"]["LIVE_EXECUTION_AUTHORIZED"]["status"] == "FAIL_CLOSED"
    assert result["OFFLINE_EXACT_ORDER_PLAN"]["WIRE_SEND_BLOCKED"] is True
    assert result["OFFLINE_EXACT_ORDER_PLAN"]["WIRE_SEND_EXECUTED"] is False
    assert result["LIVE_SUBMIT_EXECUTED"] is False
    for item in result["GETS"]:
        assert item["observed_at_utc"]
        assert item["method"] == "GET"


def test_invalid_response_is_not_implicit_pass() -> None:
    bodies = _bodies()
    bodies["/api/v5/account/config"] = b'{"code":"1","data":[]}'
    transport = RecordingFakeGetOnlyTransportV1(bodies_by_path=bodies)
    result = run_get_only_pretrade_readiness_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test"},
    )
    assert result["PREDICATES"]["ACCOUNT_MODE_CURRENT"]["status"] != "PASS"
    assert result["TECHNICAL_EXECUTION_READY"] is False


def test_historical_reuse_flag_rejected() -> None:
    with pytest.raises(GetOnlyPretradeError, match="HISTORICAL_EVIDENCE_MUST_NOT_BE_CURRENT"):
        _run(historical_reuse=True)


def test_timeout_is_indeterminate_not_pass() -> None:
    transport = RecordingFakeGetOnlyTransportV1(
        bodies_by_path=_bodies(),
        raise_timeout_paths={"/api/v5/account/leverage-info"},
    )
    result = run_get_only_pretrade_readiness_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test"},
    )
    assert result["PREDICATES"]["LEVERAGE_CURRENT"]["status"] == "INDETERMINATE_TIMEOUT"
    assert result["GET_TIMEOUT_COUNT"] == 1
    assert result["PREDICATES"]["LEVERAGE_CURRENT"]["status"] != "PASS"


def test_standing_flags_remain_false() -> None:
    result, _transport = _run()
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert result["STANDING_FLAGS"]["LIVE_ENABLED"] is False
    assert result["STANDING_FLAGS"]["POST_ALLOWED"] is False


def test_no_secrets_in_result() -> None:
    result, _transport = _run()
    blob = json.dumps(result).lower()
    assert "api_secret" not in blob
    assert "passphrase" not in blob
    assert "ok-access-sign" not in blob
    assert "ok-access-passphrase" not in blob


def test_allowlist_is_explicit_and_census_rejects_mixed_transport() -> None:
    assert "/api/v5/account/leverage-info" in ENDPOINT_PATH_ALLOWLIST
    assert "/api/v5/account/trade-fee" in ENDPOINT_PATH_ALLOWLIST
    assert "/api/v5/trade/order" not in ENDPOINT_PATH_ALLOWLIST
    dispositions = {row["disposition"] for row in EXISTING_SURFACE_CENSUS}
    assert "REJECT_FOR_THIS_WP" in dispositions


def test_submit_transport_not_loaded_by_this_package_source() -> None:
    text = (PACKAGE_DIR / "orchestrator_v1.py").read_text(encoding="utf-8")
    assert "submit_transport_v1" not in text
    assert "run_canary_submit_transport_v1" not in text


def test_missing_trade_fee_keeps_envelope_incomplete() -> None:
    bodies = _bodies()
    del bodies["/api/v5/account/trade-fee"]
    transport = RecordingFakeGetOnlyTransportV1(bodies_by_path=bodies)
    result = run_get_only_pretrade_readiness_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test"},
    )
    assert result["PREDICATES"]["FEE_POLICY_BOUND"]["status"] != "PASS"
    assert result["EXACT_EXECUTION_ENVELOPE_COMPLETE"] is False
    assert result["TECHNICAL_EXECUTION_READY"] is False
    assert result["OWNER_EXECUTION_AUTHORIZED"] is False
    assert result["LIVE_SUBMIT_EXECUTED"] is False


def test_persist_manifest_rc_zero(tmp_path: Path) -> None:
    result, _transport = _run()
    verify = persist_get_only_pretrade_evidence_v1(root=tmp_path, result=result)
    assert int(verify["MANIFEST_VERIFY_RC"]) == 0
    assert (tmp_path / "SUMMARY.json").is_file()
    assert (tmp_path / "MANIFEST.sha256").is_file()

"""Offline Envelope reprice / freshness-at-send tests.

Fake transport only. Hard-network-blocked except the GET-only client under
test, which is structurally POST-incapable. Rebuilds envelope when required.
No receipt attach. No HMAC POST. No urllib POST.
"""

from __future__ import annotations

import ast
import json
import socket
import time
import urllib.request
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
    flatten_productive_transport_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    FLATTEN_HTTP_ENDPOINT,
    INSTRUMENT_ID,
    PATH_ACCOUNT_MAX_SIZE,
    PATH_ACCOUNT_POSITIONS,
    PATH_ACCOUNT_TRADE_FEE,
    PATH_MARKET_TICKER,
    PATH_ORDERS_PENDING,
    PATH_PUBLIC_INSTRUMENTS,
    PATH_PUBLIC_PRICE_LIMIT,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_reprice_or_freshness_at_send_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    FROZEN_LIMIT_PX,
    prove_get_path_cannot_post_v1,
    prove_place_order_get_is_blocked_v1,
    required_reprice_get_contract_v1,
    run_envelope_reprice_or_freshness_at_send_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_http_v1 import (
    FlattenGetOnlyHttpClientV1,
    FlattenGetOnlyHttpError,
    RecordingFakeFlattenGetOnlyTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
    / "envelope_reprice_or_freshness_at_send_v1.py"
)
CLI_PATH = REPO_ROOT / "scripts/ops/run_section_11_14_envelope_reprice_or_freshness_at_send_v1.py"
ORIGIN_SHA = EXPECTED_ORIGIN_MAIN_SHA

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


def _install_network_hard_fail(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    attempts: list[str] = []

    def _hard_fail(name: str):
        def _boom(*_args: object, **_kwargs: object) -> None:
            attempts.append(name)
            raise AssertionError("NETWORK_CALL_ATTEMPTED")

        return _boom

    monkeypatch.setattr(urllib.request, "urlopen", _hard_fail("urlopen"))
    monkeypatch.setattr(socket, "create_connection", _hard_fail("create_connection"))
    monkeypatch.setattr(
        flatten_productive_transport_v1,
        "open_productive_flatten_urllib_post_v1",
        _hard_fail("open_productive_flatten_urllib_post_v1"),
    )
    return attempts


def _bodies(*, bid: str = "0.8200", pos: str = "1", sell_lmt: str = "0.0001") -> dict[str, bytes]:
    now_ms = str(int(time.time() * 1000))
    ticker = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "bidPx": bid,
                "askPx": "0.8349" if bid == "0.8343" else "0.8201",
                "last": bid,
                "ts": now_ms,
            }
        ],
    }
    instruments = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "instType": "FUTURES",
                "ruleType": "xperp",
                "minSz": "1",
                "lotSz": "1",
                "tickSz": "0.0001",
                "ctVal": "1",
                "ctValCcy": "SUI",
                "settleCcy": "USDC",
                "state": "live",
            }
        ],
    }
    price_band = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "instType": "FUTURES",
                "buyLmt": "2.0000",
                "sellLmt": sell_lmt,
                "ts": now_ms,
                "enabled": True,
            }
        ],
    }
    positions = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "pos": pos,
                "posSide": "net",
                "mgnMode": "cross",
            }
        ],
    }
    max_size = {"code": "0", "data": [{"instId": INSTRUMENT_ID, "maxBuy": "9", "maxSell": "9"}]}
    pending = {"code": "0", "data": []}
    return {
        PATH_PUBLIC_INSTRUMENTS: json.dumps(instruments).encode(),
        PATH_MARKET_TICKER: json.dumps(ticker).encode(),
        PATH_PUBLIC_PRICE_LIMIT: json.dumps(price_band).encode(),
        PATH_ACCOUNT_POSITIONS: json.dumps(positions).encode(),
        PATH_ACCOUNT_TRADE_FEE: json.dumps(TRADE_FEE).encode(),
        PATH_ACCOUNT_MAX_SIZE: json.dumps(max_size).encode(),
        PATH_ORDERS_PENDING: json.dumps(pending).encode(),
    }


def test_module_does_not_import_post_or_receipt_attach() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert "open_productive_flatten_urllib_post_v1" not in imported
    assert "attach_pre_send_receipt" not in imported
    assert "build_flatten_sell_envelope_v1" in imported


def test_required_reprice_get_contract_is_defined() -> None:
    contract = required_reprice_get_contract_v1()
    assert contract["GET_CONTRACT_STATUS"] == "DEFINED"
    assert contract["REPRICE_CONTRACT_STATUS"] == "DEFINED"
    assert contract["ALWAYS_REQUIRED_GET_COUNT"] == 6
    assert contract["MAX_GET_CALL_COUNT"] == 7
    assert contract["ROUNDING_RULE"] == "SELL_ROUND_DOWN_TO_TICK"
    assert contract["SIDE_QUOTE_RULE"] == "SELL_SELECTS_BID"
    assert (
        contract["ENVELOPE_REBUILD_SEMANTICS"] == "FULL_REBUILD_NEW_IDENTITY_NO_IN_PLACE_MUTATION"
    )
    endpoints = contract["ALWAYS_REQUIRED_GET_ENDPOINTS"]
    assert PATH_ACCOUNT_POSITIONS in endpoints
    assert any(PATH_MARKET_TICKER in item for item in endpoints)
    assert PATH_ORDERS_PENDING in endpoints
    assert any(PATH_PUBLIC_INSTRUMENTS in item for item in endpoints)
    assert any(PATH_PUBLIC_PRICE_LIMIT in item for item in endpoints)
    assert any(PATH_ACCOUNT_TRADE_FEE in item for item in endpoints)
    assert contract["HISTORICAL_VALUES_REUSED_AS_FRESH"] is False
    assert contract["POST_FORBIDDEN"] is True


def test_get_client_post_and_place_order_are_hard_blocked() -> None:
    transport = RecordingFakeFlattenGetOnlyTransportV1()
    client = FlattenGetOnlyHttpClientV1(transport=transport)
    blocked = prove_get_path_cannot_post_v1(client=client)
    assert "HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST" in blocked
    place = prove_place_order_get_is_blocked_v1(client=client)
    assert "MUTATION_ENDPOINT_HARD_BLOCK" in place
    with pytest.raises(FlattenGetOnlyHttpError, match="HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST"):
        client.post(endpoint=FLATTEN_HTTP_ENDPOINT)
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert POST_ALLOWED is False


def test_reprice_rebuilds_new_envelope_when_quantized_px_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=_bodies(bid="0.8200"))
    result = run_envelope_reprice_or_freshness_at_send_v1(
        origin_main_sha=ORIGIN_SHA,
        origin_main_tree="test-tree",
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert attempts == []
    assert result["GET_EXECUTED"] is True
    assert result["GET_CALL_COUNT"] == 7
    assert result["ENVELOPE_FRESHNESS_STATUS"] == "REPRICE_REQUIRED"
    assert result["REPRICE_REQUIRED"] is True
    assert result["REPRICE_EXECUTED"] is True
    assert result["ENVELOPE_REBUILD_EXECUTED"] is True
    assert result["COMPUTED_LIMIT_PX"] == "0.8200"
    assert result["NEW_LIMIT_PRICE"] == "0.8200"
    assert result["OLD_LIMIT_PRICE"] == FROZEN_LIMIT_PX
    assert result["OLD_ENVELOPE_ID"] == BOUND_FROZEN_ENVELOPE_ID
    assert result["NEW_ENVELOPE_ID"] != BOUND_FROZEN_ENVELOPE_ID
    assert result["NEW_ENVELOPE_ID"] != "NONE"
    assert result["FLATTEN_ENVELOPE"]["FLATTEN_ENVELOPE_ID"] == result["NEW_ENVELOPE_ID"]
    assert result["FLATTEN_ENVELOPE"]["LIMIT_PRICE"] == "0.8200"
    assert result["FLATTEN_ENVELOPE"]["ORIGIN_MAIN_SHA"] == ORIGIN_SHA
    assert result["RECEIPT_MINTED"] is False
    assert result["RECEIPT_ATTACHED"] is False
    assert result["RECEIPT_ALLOWED"] is False
    assert result["HTTP_POST_EXECUTED"] is False
    assert result["PRODUCTIVE_URLLIB_POST_EXECUTED"] is False
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["HMAC_HEADER_GENERATED"] is False
    assert result["LEASE_CONSUMED"] is False
    assert result["POSITION_MUTATION"] is False
    assert result["ENVELOPE_FRESHNESS_STATUS_AFTER"] == "VALID_WITH_FRESH_GET"
    assert result["CURRENT_CANONICAL_BOUNDARY_AFTER"] == "RECEIPT_MISSING"
    assert result["NEXT_OWNER_AUTHORITY_REQUIRED"] == "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER"
    assert result["CLIENT_COUNTERS"]["WRITE_REQUEST_COUNT"] == 0
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert (tmp_path / "FLATTEN_ENVELOPE.json").is_file()
    assert (tmp_path / "FROZEN_ENVELOPE_REF.json").is_file()
    raw = json.loads((tmp_path / "GET_RESULTS.sanitized.json").read_text(encoding="utf-8"))
    assert "payload" not in str(raw["GETS"])
    max_ep = next(item["endpoint"] for item in result["GETS"] if item["name"] == "MAX_SIZE")
    assert "px=0.8200" in max_ep
    assert all(item["method"] == "GET" for item in result["GETS"])


def test_no_rebuild_when_computed_matches_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_network_hard_fail(monkeypatch)
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=_bodies(bid="0.8343"))
    result = run_envelope_reprice_or_freshness_at_send_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert result["ENVELOPE_FRESHNESS_STATUS"] == "VALID_WITH_FRESH_GET"
    assert result["COMPUTED_LIMIT_PX"] == FROZEN_LIMIT_PX
    assert result["REPRICE_EXECUTED"] is False
    assert result["ENVELOPE_REBUILD_EXECUTED"] is False
    assert result["FLATTEN_ENVELOPE"] is None
    assert result["NEW_ENVELOPE_ID"] == "NONE"
    assert result["RECEIPT_MINTED"] is False
    assert result["HTTP_POST_EXECUTED"] is False
    assert result["NEXT_OWNER_AUTHORITY_REQUIRED"] == "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER"
    assert not (tmp_path / "FLATTEN_ENVELOPE.json").is_file()


def test_sell_lmt_violation_does_not_rebuild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_network_hard_fail(monkeypatch)
    transport = RecordingFakeFlattenGetOnlyTransportV1(
        bodies_by_path=_bodies(bid="0.8200", sell_lmt="0.8300")
    )
    result = run_envelope_reprice_or_freshness_at_send_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert result["ENVELOPE_FRESHNESS_STATUS"] == "REPRICE_REQUIRED"
    assert result["REPRICE_EXECUTED"] is False
    assert result["ENVELOPE_REBUILD_EXECUTED"] is False
    assert "SELL_LMT_VIOLATION" in str(result["ENVELOPE_ERROR"])
    assert result["HTTP_POST_EXECUTED"] is False
    assert result["RECEIPT_MINTED"] is False
    assert result["NEXT_OWNER_AUTHORITY_REQUIRED"] == "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"


def test_empty_positions_is_not_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_hard_fail(monkeypatch)
    bodies = _bodies()
    bodies[PATH_ACCOUNT_POSITIONS] = json.dumps({"code": "0", "data": []}).encode()
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=bodies)
    result = run_envelope_reprice_or_freshness_at_send_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert result["CURRENT_POSITION_STATE"] == "TARGET_POSITION_NOT_OBSERVED"
    assert result["REPRICE_EXECUTED"] is False
    assert result["RECEIPT_ALLOWED"] is False
    assert result["HTTP_POST_EXECUTED"] is False


def test_pending_order_blocks_rebuild(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_hard_fail(monkeypatch)
    bodies = _bodies()
    bodies[PATH_ORDERS_PENDING] = json.dumps(
        {"code": "0", "data": [{"instId": INSTRUMENT_ID, "ordId": "1"}]}
    ).encode()
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=bodies)
    result = run_envelope_reprice_or_freshness_at_send_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert result["PENDING_ORDER_GATE"]["PENDING_ORDER_GATE_PASS"] is False
    assert result["REPRICE_EXECUTED"] is False
    assert result["HTTP_POST_EXECUTED"] is False


def test_cli_source_is_get_only_and_default_is_dry() -> None:
    text = CLI_PATH.read_text(encoding="utf-8")
    assert "--execute" in text
    assert "No POST" in text
    assert "execute_envelope_reprice_or_freshness_at_send_v1" in text

"""Offline Fresh Pre-Submit GET / freshness adjudication tests.

Fake transport only. Hard-network-blocked except the GET-only client under
test, which is structurally POST-incapable. No envelope rebuild. No receipt
attach. No HMAC POST. No urllib POST.
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
    FLATTEN_HTTP_ENDPOINT,
    INSTRUMENT_ID,
    PATH_ACCOUNT_POSITIONS,
    PATH_MARKET_TICKER,
    PATH_ORDERS_PENDING,
    PATH_PUBLIC_INSTRUMENTS,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.fresh_pre_submit_get_and_freshness_adjudication_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    FROZEN_LIMIT_PX,
    GET_CONTRACT_CANDIDATES,
    REQUIRED_FRESH_GETS,
    THIS_SLICE,
    classify_envelope_freshness_v1,
    prove_get_path_cannot_post_v1,
    prove_place_order_get_is_blocked_v1,
    required_fresh_get_contract_v1,
    run_fresh_pre_submit_gets_v1,
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
    / "fresh_pre_submit_get_and_freshness_adjudication_v1.py"
)
ORIGIN_SHA = EXPECTED_ORIGIN_MAIN_SHA


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


def _bodies(*, bid: str = "0.8200", pos: str = "1", ts: str | None = None) -> dict[str, bytes]:
    now_ms = ts or str(int(time.time() * 1000))
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
    pending = {"code": "0", "data": []}
    return {
        PATH_PUBLIC_INSTRUMENTS: json.dumps(instruments).encode(),
        PATH_MARKET_TICKER: json.dumps(ticker).encode(),
        PATH_ACCOUNT_POSITIONS: json.dumps(positions).encode(),
        PATH_ORDERS_PENDING: json.dumps(pending).encode(),
    }


def test_module_does_not_import_envelope_rebuild_or_post() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert "build_flatten_sell_envelope_v1" not in imported
    assert "open_productive_flatten_urllib_post_v1" not in imported
    assert "run_flatten_get_only_preflight_v1" not in imported
    assert "attach_pre_send_receipt" not in imported


def test_required_fresh_get_contract_is_defined() -> None:
    contract = required_fresh_get_contract_v1()
    assert contract["GET_CONTRACT_STATUS"] == "DEFINED"
    assert contract["GET_CONTRACT_CANDIDATE_COUNT"] == 12
    assert contract["REQUIRED_FRESH_GET_COUNT"] == 4
    endpoints = contract["REQUIRED_FRESH_GET_ENDPOINTS"]
    assert PATH_ACCOUNT_POSITIONS in endpoints
    assert any(PATH_MARKET_TICKER in item for item in endpoints)
    assert PATH_ORDERS_PENDING in endpoints
    assert any(PATH_PUBLIC_INSTRUMENTS in item for item in endpoints)
    assert PATH_ACCOUNT_POSITIONS in GET_CONTRACT_CANDIDATES
    assert "/api/v5/public/mark-price" in GET_CONTRACT_CANDIDATES
    assert "/api/v5/market/books" in GET_CONTRACT_CANDIDATES
    assert len(REQUIRED_FRESH_GETS) == 4


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


def test_fresh_get_reprice_required_when_quantized_px_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts = _install_network_hard_fail(monkeypatch)
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=_bodies(bid="0.8200"))
    result = run_fresh_pre_submit_gets_v1(
        origin_main_sha=ORIGIN_SHA,
        origin_main_tree="test-tree",
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert attempts == []
    assert result["GET_EXECUTED"] is True
    assert result["GET_CALL_COUNT"] == 4
    assert result["ENVELOPE_REBUILT"] is False
    assert result["REPRICE_EXECUTED"] is False
    assert result["RECEIPT_ATTACHED"] is False
    assert result["RECEIPT_MINTED"] is False
    assert result["RECEIPT_ALLOWED"] is False
    assert result["HTTP_POST_EXECUTED"] is False
    assert result["HMAC_HEADER_GENERATED"] is False
    assert result["ENVELOPE_FRESHNESS_STATUS"] == "REPRICE_REQUIRED"
    assert result["COMPUTED_LIMIT_PX"] != FROZEN_LIMIT_PX
    assert result["FIRST_DENY_AFTER_FRESH_GET"] == "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
    assert result["NEXT_OWNER_AUTHORITY_REQUIRED"] == "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
    assert result["FLATTEN_ENVELOPE"] is None if "FLATTEN_ENVELOPE" in result else True
    assert "FLATTEN_ENVELOPE" not in result
    assert result["THIS_SLICE"] == THIS_SLICE
    assert all(item["method"] == "GET" for item in result["GETS"])
    assert result["CLIENT_COUNTERS"]["WRITE_REQUEST_COUNT"] == 0
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert (tmp_path / "GET_RESULTS.sanitized.json").is_file()
    raw = json.loads((tmp_path / "GET_RESULTS.sanitized.json").read_text(encoding="utf-8"))
    assert "payload" not in str(raw["GETS"])


def test_fresh_get_valid_with_fresh_get_when_quantized_px_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_network_hard_fail(monkeypatch)
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=_bodies(bid="0.8343"))
    result = run_fresh_pre_submit_gets_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert result["ENVELOPE_FRESHNESS_STATUS"] == "VALID_WITH_FRESH_GET"
    assert result["COMPUTED_LIMIT_PX"] == FROZEN_LIMIT_PX
    assert result["REPRICE_EXECUTED"] is False
    assert result["RECEIPT_MINTED"] is False
    assert result["RECEIPT_ATTACHED"] is False
    assert result["RECEIPT_ALLOWED"] is False
    assert result["NEXT_OWNER_AUTHORITY_REQUIRED"] == "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"


def test_empty_positions_is_not_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_network_hard_fail(monkeypatch)
    bodies = _bodies()
    bodies[PATH_ACCOUNT_POSITIONS] = json.dumps({"code": "0", "data": []}).encode()
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=bodies)
    result = run_fresh_pre_submit_gets_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
        vault_file=tmp_path / "missing-vault.json",
    )
    assert result["CURRENT_POSITION_STATE"] == "TARGET_POSITION_NOT_OBSERVED"
    assert result["POSITION_OBSERVED"] is False
    assert result["RECEIPT_ALLOWED"] is False


def test_envelope_freshness_classifier_contract() -> None:
    assert (
        classify_envelope_freshness_v1(
            price_permit_issued=True,
            computed_limit_px="0.8200",
            frozen_limit_px="0.8343",
            quote_freshness_valid=True,
            reject_reasons=(),
        )
        == "REPRICE_REQUIRED"
    )
    assert (
        classify_envelope_freshness_v1(
            price_permit_issued=True,
            computed_limit_px="0.8343",
            frozen_limit_px="0.8343",
            quote_freshness_valid=True,
            reject_reasons=(),
        )
        == "VALID_WITH_FRESH_GET"
    )
    assert (
        classify_envelope_freshness_v1(
            price_permit_issued=False,
            computed_limit_px="",
            frozen_limit_px="0.8343",
            quote_freshness_valid=False,
            reject_reasons=("STALE_QUOTE",),
        )
        == "REPRICE_REQUIRED"
    )

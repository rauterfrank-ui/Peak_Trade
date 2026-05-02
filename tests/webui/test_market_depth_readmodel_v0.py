from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.webui.market_depth_readmodel_v0 import (
    MarketDepthReadmodelError,
    build_market_depth_readmodel_v0,
    to_json_dict,
)


FIXTURE_ROOT = Path("tests/fixtures/market_depth_readmodel_v0")


def test_market_depth_readmodel_builds_json_native_offline_bundle() -> None:
    readmodel = build_market_depth_readmodel_v0(
        bundle_root=FIXTURE_ROOT / "complete_minimal",
        generated_at_iso="2026-05-02T16:00:00Z",
    )

    payload = to_json_dict(readmodel)

    assert payload["readmodel_id"] == "market_depth_readmodel.v0"
    assert payload["symbol"] == "BTC/EUR"
    assert payload["source"] == "dummy"
    assert payload["limit"] == 3
    assert payload["generated_at_iso"] == "2026-05-02T16:00:00Z"
    assert payload["runtime_source_status"] == "offline_bundle"
    assert payload["stale"] is True
    assert payload["stale_reason"] == "offline_bundle_scan"

    assert payload["depth"]["level_limit"] == 3
    assert payload["depth"]["levels_returned"] == {"bids": 3, "asks": 3}
    assert [level["price"] for level in payload["depth"]["bids"]] == [
        "63010",
        "63000",
        "62990",
    ]
    assert [level["price"] for level in payload["depth"]["asks"]] == [
        "63020",
        "63030",
        "63040",
    ]
    assert payload["depth"]["bids"][0]["notional"] == "12602"
    assert json.loads(json.dumps(payload)) == payload


def test_market_depth_readmodel_explicit_limit_truncates_sorted_levels() -> None:
    payload = to_json_dict(
        build_market_depth_readmodel_v0(
            bundle_root=FIXTURE_ROOT / "complete_minimal",
            limit=1,
            generated_at_iso="2026-05-02T16:00:00Z",
        )
    )

    assert payload["limit"] == 1
    assert payload["depth"]["levels_returned"] == {"bids": 1, "asks": 1}
    assert payload["depth"]["bids"][0]["price"] == "63010"
    assert payload["depth"]["asks"][0]["price"] == "63020"


def test_market_depth_readmodel_rejects_missing_bundle_root() -> None:
    with pytest.raises(MarketDepthReadmodelError, match="bundle_root does not exist"):
        build_market_depth_readmodel_v0(bundle_root=FIXTURE_ROOT / "does_not_exist")


def test_market_depth_readmodel_rejects_malformed_levels() -> None:
    with pytest.raises(MarketDepthReadmodelError, match=r"bids\[0\]\.price must be positive"):
        build_market_depth_readmodel_v0(bundle_root=FIXTURE_ROOT / "malformed_levels")


def test_market_depth_readmodel_module_has_no_runtime_provider_imports() -> None:
    source = Path("src/webui/market_depth_readmodel_v0/builder.py").read_text(encoding="utf-8")

    forbidden_tokens = [
        "ccxt",
        "kraken",
        "requests",
        "httpx",
        "aiohttp",
        "subprocess",
        "os.environ",
    ]

    for token in forbidden_tokens:
        assert token not in source


_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "readmodel_id",
        "symbol",
        "source",
        "limit",
        "generated_at_iso",
        "runtime_source_status",
        "stale",
        "stale_reason",
        "depth",
    }
)

_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "live_authorization",
        "live_ready",
        "testnet_ready",
        "trading_ready",
        "execute",
        "execution",
        "order",
        "orders",
        "approve",
        "approved",
        "promote",
        "sign_off",
        "enable_live",
        "confirm_token",
    }
)


def _collect_object_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            _collect_object_keys(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


def test_market_depth_readmodel_rejects_missing_depth_json(tmp_path: Path) -> None:
    empty_root = tmp_path / "bundle"
    empty_root.mkdir()
    with pytest.raises(MarketDepthReadmodelError, match="missing depth fixture"):
        build_market_depth_readmodel_v0(bundle_root=empty_root)


def test_market_depth_readmodel_rejects_invalid_depth_json(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "depth.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(MarketDepthReadmodelError, match="malformed depth fixture JSON"):
        build_market_depth_readmodel_v0(bundle_root=root)


def test_market_depth_readmodel_stable_top_level_keys_and_no_authority_keys() -> None:
    payload = to_json_dict(
        build_market_depth_readmodel_v0(
            bundle_root=FIXTURE_ROOT / "complete_minimal",
            generated_at_iso="2026-05-02T16:00:00Z",
        )
    )
    assert set(payload.keys()) == _EXPECTED_TOP_LEVEL_KEYS
    depth_keys = set(payload["depth"].keys())
    assert depth_keys == frozenset({"bids", "asks", "levels_returned", "level_limit"})
    collected: set[str] = set()
    _collect_object_keys(payload, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_market_depth_empty_sides_remain_sorted_and_json_native(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    fixture = {
        "symbol": "ETH/EUR",
        "source": "dummy",
        "limit": 5,
        "bids": [],
        "asks": [],
    }
    (root / "depth.json").write_text(json.dumps(fixture), encoding="utf-8")
    payload = to_json_dict(
        build_market_depth_readmodel_v0(
            bundle_root=root,
            generated_at_iso="2026-05-02T17:00:00Z",
        )
    )
    assert payload["depth"]["bids"] == []
    assert payload["depth"]["asks"] == []
    assert payload["depth"]["levels_returned"] == {"bids": 0, "asks": 0}
    assert json.loads(json.dumps(payload)) == payload

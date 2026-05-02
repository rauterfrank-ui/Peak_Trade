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

"""Focused tests: governed OKX archive sibling discovery for Market Landscape."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.webui.workflow_dashboard_archive_root_v1 import (
    ENV_ARCHIVE_ROOT,
    OKX_OHLCV_READMODEL_RELATIVE,
    PRECEDENCE_CHAIN,
    PRECEDENCE_DISCOVERED_GOVERNED_OKX,
    UNIVERSE_SELECTION_READMODEL_RELATIVE,
    archive_root_has_governed_okx_futures_readmodels,
    canonical_default_workflow_dashboard_archive_root,
    discover_governed_okx_workflow_dashboard_archive,
    resolve_workflow_dashboard_archive_root,
)

REPO = Path(__file__).resolve().parents[2]


def _write_okx_archive(
    root: Path,
    *,
    instrument_id: str = "ETH-USDT-SWAP",
    venue: str = "okx",
    market_type: str = "perpetual",
    fixture_only: bool = False,
    fixture_marked: bool = False,
    bar_count: int = 3,
    include_bars: bool = True,
    write_manifest: bool = True,
) -> Path:
    from scripts.ops.primary_evidence_retention_v0 import (
        write_manifest_sha256 as _write_manifest_sha256,
    )

    readmodels = root / "readmodels"
    readmodels.mkdir(parents=True, exist_ok=True)
    exchange = venue.upper() if venue.lower() == "okx" else venue
    universe = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": "2026-07-26T00:00:00Z",
        "source_run_id": "discovery_test",
        "source_stage": "paper",
        "non_authorizing": True,
        "fixture_marked": fixture_marked,
        "universe": [
            {
                "row_id": "u1",
                "symbol": instrument_id,
                "rank": 1,
                "exchange": exchange,
            }
        ],
        "ranking": [
            {
                "row_id": "r1",
                "symbol": instrument_id,
                "rank": 1,
                "exchange": exchange,
                "display_score": 1.0,
            }
        ],
        "selected_future": {
            "row_id": "s1",
            "symbol": instrument_id,
            "rank": 1,
            "truth_status": "PERSISTED",
            "selection_reason": "test",
        },
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "governed_producer",
            "snapshot_id": "snap-1",
            "exchange": exchange,
            "captured_at": "2026-07-26T00:00:00Z",
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED",
            "selected_future": "PERSISTED",
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
    }
    bars = []
    if include_bars:
        for i in range(bar_count):
            bars.append(
                {
                    "ts": f"2026-07-26T00:0{i}:00Z",
                    "open": str(1.0 + i),
                    "high": str(2.0 + i),
                    "low": str(0.5 + i),
                    "close": str(1.5 + i),
                    "volume": str(10 + i),
                    "confirm": True,
                }
            )
    ohlcv = {
        "schema_name": "okx_selected_instrument_ohlcv_readmodel.v1",
        "schema_version": 1,
        "non_authorizing": True,
        "fixture_only": fixture_only,
        "venue": venue.lower(),
        "market_type": market_type,
        "interval": "1m",
        "instrument_id": instrument_id,
        "provider_instrument_id": instrument_id,
        "selection_bundle_id": "bundle-1",
        "captured_at": "2026-07-26T00:03:00Z",
        "effective_at": "2026-07-26T00:03:00Z",
        "freshness_state": "fresh",
        "is_stale": False,
        "bar_count": bar_count,
        "closed_bar_count": bar_count,
        "gap_count": 0,
        "bars": bars,
    }
    (readmodels / Path(UNIVERSE_SELECTION_READMODEL_RELATIVE).name).write_text(
        json.dumps(universe, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (readmodels / Path(OKX_OHLCV_READMODEL_RELATIVE).name).write_text(
        json.dumps(ohlcv, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if write_manifest:
        _write_manifest_sha256(readmodels)
    return root


def test_precedence_chain_includes_discovered_okx() -> None:
    assert PRECEDENCE_DISCOVERED_GOVERNED_OKX in PRECEDENCE_CHAIN
    assert PRECEDENCE_CHAIN[-1] == PRECEDENCE_DISCOVERED_GOVERNED_OKX


def test_missing_canonical_and_no_siblings_remains_none(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = durable_isolated_home(monkeypatch, request, label="okx_disc_missing")
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    assert not default.exists()
    assert (
        resolve_workflow_dashboard_archive_root(
            home=home, platform="darwin", environ={}, repo_root=REPO
        )
        is None
    )


def test_discovers_newest_governed_okx_sibling_when_canonical_absent(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = durable_isolated_home(monkeypatch, request, label="okx_disc_sibling")
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    parent = default.parent
    parent.mkdir(parents=True, exist_ok=True)
    older = _write_okx_archive(
        parent / "workflow_dashboard_v1_okx_older", instrument_id="ETH-USDT-SWAP"
    )
    newer = _write_okx_archive(
        parent / "workflow_dashboard_v1_okx_newer", instrument_id="SATS-USDT-SWAP"
    )
    # Ensure newer mtime wins.
    newer_ohlcv = newer / OKX_OHLCV_READMODEL_RELATIVE
    older_ohlcv = older / OKX_OHLCV_READMODEL_RELATIVE
    older_ohlcv.touch()
    newer_ohlcv.touch()

    discovered = discover_governed_okx_workflow_dashboard_archive(search_parent=parent)
    assert discovered == newer.resolve()
    resolved = resolve_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    assert resolved == newer.resolve()
    assert archive_root_has_governed_okx_futures_readmodels(resolved)


def test_canonical_default_directory_wins_over_siblings(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = durable_isolated_home(monkeypatch, request, label="okx_disc_canonical_wins")
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    parent = default.parent
    parent.mkdir(parents=True, exist_ok=True)
    _write_okx_archive(parent / "workflow_dashboard_v1_okx_sibling")
    default.mkdir(parents=True, exist_ok=True)
    resolved = resolve_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    assert resolved == default.resolve()


def test_rejects_btc_spot_fixture_and_schema_mismatch(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = durable_isolated_home(monkeypatch, request, label="okx_disc_reject")
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    parent = default.parent
    parent.mkdir(parents=True, exist_ok=True)

    btc = _write_okx_archive(parent / "workflow_dashboard_v1_btc", instrument_id="BTC-USDT-SWAP")
    spot = _write_okx_archive(
        parent / "workflow_dashboard_v1_spot",
        instrument_id="ETH-USDT",
        market_type="spot",
    )
    fixture = _write_okx_archive(parent / "workflow_dashboard_v1_fixture", fixture_only=True)
    bad = parent / "workflow_dashboard_v1_bad"
    bad.mkdir(parents=True)
    (bad / "readmodels").mkdir()
    (bad / UNIVERSE_SELECTION_READMODEL_RELATIVE).write_text("{}", encoding="utf-8")

    assert not archive_root_has_governed_okx_futures_readmodels(btc)
    assert not archive_root_has_governed_okx_futures_readmodels(spot)
    assert not archive_root_has_governed_okx_futures_readmodels(fixture)
    assert not archive_root_has_governed_okx_futures_readmodels(bad)
    assert (
        resolve_workflow_dashboard_archive_root(
            home=home, platform="darwin", environ={}, repo_root=REPO
        )
        is None
    )


def test_env_override_missing_path_does_not_fall_through_to_discovery(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    home = durable_isolated_home(monkeypatch, request, label="okx_disc_env_missing")
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    parent = default.parent
    parent.mkdir(parents=True, exist_ok=True)
    _write_okx_archive(parent / "workflow_dashboard_v1_okx_sibling")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(parent / "does_not_exist"))
    assert (
        resolve_workflow_dashboard_archive_root(
            home=home, platform="darwin", environ=None, repo_root=REPO
        )
        is None
    )


def test_page_and_ohlcv_api_bind_discovered_archive(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    from fastapi.testclient import TestClient

    from src.webui.app import app
    from tests.webui.archive_root_durable_home_v1 import durable_isolated_home

    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = durable_isolated_home(monkeypatch, request, label="okx_disc_api_bind")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO
    )
    parent = default.parent
    parent.mkdir(parents=True, exist_ok=True)
    archive = _write_okx_archive(
        parent / "workflow_dashboard_v1_okx_bind", instrument_id="ETH-USDT-SWAP"
    )
    assert (
        resolve_workflow_dashboard_archive_root(
            home=home, platform="darwin", environ={}, repo_root=REPO
        )
        == archive.resolve()
    )
    assert resolve_workflow_dashboard_archive_root() == archive.resolve()

    def _no_network_refresh(**kwargs):  # type: ignore[no-untyped-def]
        return {
            "status": "SKIPPED_TEST",
            "refresh_attempted": False,
            "refresh_error": None,
            "fabricated": False,
        }

    monkeypatch.setattr(
        "src.ops.okx_selected_instrument_ohlcv_readmodel_v1.refresh_selected_okx_ohlcv_readmodel_from_archive_v1",
        _no_network_refresh,
    )

    client = TestClient(app)
    market = client.get("/market")
    assert market.status_code == 200
    body = market.text
    assert "ETH-USDT-SWAP" in body
    assert "OKX" in body
    assert 'data-mdl-chart-has-series="true"' in body
    chart_chrome = body.split("data-mdl-chart=", 1)[1][:700]
    # Identical connection/availability labels must not both render.
    assert chart_chrome.count("data-mdl-chart-availability=") == 0 or (
        'data-connection-state="MISSING_SOURCE"' not in chart_chrome
        or 'data-mdl-chart-availability="true">MISSING_SOURCE' not in chart_chrome
    )

    api = client.get("/api/market/landscape/ohlcv")
    assert api.status_code == 200
    payload = api.json()
    assert payload["venue"] == "OKX"
    assert payload["selected_instrument_id"] == "ETH-USDT-SWAP"
    assert payload.get("browser_payload") is not None
    assert (payload.get("browser_payload") or {}).get("bar_count", 0) >= 1

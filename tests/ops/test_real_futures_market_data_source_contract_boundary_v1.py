"""Docs/env boundary for Real Futures Market Data Source Contract v1 (U5 charter)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MARKET_DATA_SOURCE_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md"
)
REAL_SOURCE_CHARTER_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md"
)


def test_real_futures_market_data_source_contract_doc_exists_and_markers() -> None:
    assert MARKET_DATA_SOURCE_DOC.is_file()
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_MARKET_DATA_WIRING_AUTHORIZED=false" in doc
    assert "PROVIDER_PROBE_AUTHORIZED=false" in doc
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc
    assert "Evidence != Approval/Lift/Live" in doc
    assert "FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false" in doc
    assert "SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true" in doc
    assert "kraken_futures_public_market_data_only" in doc
    assert "/derivatives/api/v3/instruments" in doc
    assert "/derivatives/api/v3/tickers" in doc
    assert "api.kraken.com" in doc
    assert "market_ranking_funnel_readmodel.v0" in doc
    assert "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md" in doc


def test_real_source_charter_links_market_data_source_contract() -> None:
    doc = REAL_SOURCE_CHARTER_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md" in doc


def test_market_data_source_contract_forbids_dummy_substitution() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    forbidden = (
        "market_surface_dummy",
        "get_market_dummy",
        "btc_usd_dummy_default",
        "fixture_only=true",
    )
    for marker in forbidden:
        assert marker in doc


def test_market_data_source_contract_no_runtime_wiring_claims() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "PROVIDER_POLLING_DAEMON_AUTHORIZED=false" in doc
    assert "DASHBOARD_PROVIDER_WIRING_AUTHORIZED=false" in doc
    assert "no daemon" in doc.lower() or "no daemon" in doc
    assert "scheduler" in doc.lower()


def test_market_data_source_contract_links_u5b_probe_module() -> None:
    doc = MARKET_DATA_SOURCE_DOC.read_text(encoding="utf-8")
    assert "probe_kraken_futures_public_market_data_v1.py" in doc
    assert "CONFIRM_VIEW_ONLY_PUBLIC_MARKET_DATA_PROBE_V1" in doc
    assert "test_probe_kraken_futures_public_market_data_v1.py" in doc

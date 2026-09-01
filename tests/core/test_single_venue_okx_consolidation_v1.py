"""Contracts for single operative venue OKX EEA and Kraken operative decommission.

No network. No activation. No venue relabel of historical clients.
"""

from __future__ import annotations

import inspect

import pytest
import toml
from pathlib import Path

from src.core.peak_config import PeakConfig
from src.exchange import build_exchange_client_from_config, build_trading_client_from_config
from src.exchange.operative_venue_boundary_v1 import (
    NoncanonicalVenueRejectedError,
    assert_operative_ccxt_venue_id,
)
from src.execution.adapters.registry_v1 import build_adapter_registry_v1

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_default_exchange_is_okx_europe_eea() -> None:
    cfg = toml.loads((REPO_ROOT / "config" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["exchange"]["default_type"] == "dummy"
    assert cfg["testnet_session"]["default_exchange"] == "okx_europe_eea"
    live_profile = cfg.get("live_profile") or {}
    switch = (live_profile.get("strategy_switch") or {}) if isinstance(live_profile, dict) else {}
    if "exchange" in switch:
        assert switch["exchange"] == "okx_europe_eea"
    assert "kraken_testnet" not in (cfg.get("exchange") or {})
    assert "kraken_live" not in (cfg.get("exchange") or {})


def test_trading_factory_dummy_only_rejects_noncanonical() -> None:
    dummy = build_trading_client_from_config(
        PeakConfig(raw={"exchange": {"default_type": "dummy"}})
    )
    assert dummy.get_name()  # simulation client, not a venue
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        build_trading_client_from_config(
            PeakConfig(raw={"exchange": {"default_type": "kraken_live"}})
        )
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        build_trading_client_from_config(
            PeakConfig(raw={"exchange": {"default_type": "kraken_testnet"}})
        )


def test_ccxt_factory_maps_only_existing_okx_ids() -> None:
    pytest.importorskip("ccxt")
    assert assert_operative_ccxt_venue_id("okx_europe_eea") == "okx"
    assert assert_operative_ccxt_venue_id("OKX_EEA") == "okx"
    with pytest.raises(NoncanonicalVenueRejectedError):
        assert_operative_ccxt_venue_id("kraken")
    with pytest.raises(ValueError):
        build_exchange_client_from_config(PeakConfig(raw={"exchange": {"id": "kraken"}}))


def test_adapter_registry_has_no_removed_brand_adapter() -> None:
    reg = build_adapter_registry_v1()
    assert "mock" in reg
    assert "okx" in reg
    assert set(reg) <= {"mock", "okx", "bybit"}


def test_kraken_live_and_testnet_constructors_fail_closed() -> None:
    from src.exchange.kraken_live import KrakenLiveClient, KrakenLiveConfig
    from src.exchange.kraken_testnet import KrakenTestnetClient, KrakenTestnetConfig

    with pytest.raises(NoncanonicalVenueRejectedError):
        KrakenLiveClient(KrakenLiveConfig())
    with pytest.raises(NoncanonicalVenueRejectedError):
        KrakenTestnetClient(KrakenTestnetConfig())


def test_create_kraken_factories_fail_closed() -> None:
    from src.exchange.kraken_live import create_kraken_live_client_from_config
    from src.exchange.kraken_testnet import create_kraken_testnet_client_from_config
    from src.orders.testnet_executor import create_testnet_executor_from_config

    cfg = PeakConfig(raw={})
    with pytest.raises(NoncanonicalVenueRejectedError):
        create_kraken_live_client_from_config(cfg)
    with pytest.raises(NoncanonicalVenueRejectedError):
        create_kraken_testnet_client_from_config(cfg)
    with pytest.raises(NoncanonicalVenueRejectedError):
        create_testnet_executor_from_config(cfg)


def test_kraken_ohlcv_and_pipeline_fail_closed() -> None:
    from src.data.kraken import fetch_ohlcv_df, get_kraken_client
    from src.data.kraken_pipeline import KrakenDataPipeline, fetch_kraken_data
    from src.data.kraken_live import KrakenLiveCandleSource, create_kraken_source_from_config

    with pytest.raises(NoncanonicalVenueRejectedError):
        get_kraken_client()
    with pytest.raises(NoncanonicalVenueRejectedError):
        fetch_ohlcv_df("BTC/EUR")
    with pytest.raises(NoncanonicalVenueRejectedError):
        KrakenDataPipeline()
    with pytest.raises(NoncanonicalVenueRejectedError):
        fetch_kraken_data("BTC/EUR")
    with pytest.raises(NoncanonicalVenueRejectedError):
        KrakenLiveCandleSource()
    with pytest.raises(NoncanonicalVenueRejectedError):
        create_kraken_source_from_config(None, None)  # type: ignore[arg-type]


def test_data_backend_registry_has_no_kraken_factory_key() -> None:
    from src.data.backend import REGISTRY

    assert REGISTRY == {}


def test_trading_factory_signature_has_no_kraken_branches() -> None:
    src = inspect.getsource(build_trading_client_from_config)
    assert "kraken_live" not in src
    assert "kraken_testnet" not in src

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
    assert set(reg) == {"mock", "okx"}


def test_removed_kraken_client_modules_are_absent() -> None:
    with pytest.raises(ModuleNotFoundError):
        __import__("src.exchange.kraken_live")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.exchange.kraken_testnet")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.data.kraken")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.data.kraken_pipeline")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.data.kraken_live")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.data.providers.kraken_ccxt_backend")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.data.kraken_cache_loader")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.ops.kraken_futures_demo_credential_presence_contract_v0")
    with pytest.raises(ModuleNotFoundError):
        __import__("src.webui.workflow_dashboard_readmodel_v1.kraken_metadata_coverage_reader_v1")
    assert not (
        REPO_ROOT / "scripts/ops/check_kraken_futures_demo_credentials_presence_readonly_v0.py"
    ).is_file()
    assert not (REPO_ROOT / "scripts/ops/probe_kraken_futures_public_market_data_v1.py").is_file()
    assert not (
        REPO_ROOT / "scripts/ops/transform_kraken_futures_raw_to_u2c_candidate_v1.py"
    ).is_file()
    assert not (REPO_ROOT / "scripts/demo_kraken_simple.py").is_file()


def test_data_backend_registry_has_no_kraken_factory_key() -> None:
    from src.data.backend import REGISTRY

    assert REGISTRY == {}


def test_trading_factory_signature_has_no_kraken_branches() -> None:
    src = inspect.getsource(build_trading_client_from_config)
    assert "kraken_live" not in src
    assert "kraken_testnet" not in src

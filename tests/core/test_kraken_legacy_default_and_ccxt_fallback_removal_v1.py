"""Negative contracts for PEAK_TRADE_KRAKEN_LEGACY_DEFAULT_AND_CCXT_FALLBACK_REMOVAL_V1.

No network. No venue substitution. No activation.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import toml
from pathlib import Path

import pytest

from src.autonomous.monitors import MarketMonitor
from src.core.config_pydantic import LiveConfig
from src.core.peak_config import PeakConfig
from src.data.feeds.live_feed import FeedConfig
from src.data.shadow.models import Tick
from src.exchange import build_exchange_client_from_config
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    FORBIDDEN_VENUE_FALLBACKS as EEA_FORBIDDEN_VENUE_FALLBACKS,
)
from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.constants_v1 import (
    FORBIDDEN_VENUE_FALLBACKS as GLOBAL_FORBIDDEN_VENUE_FALLBACKS,
)
from src.risk_layer.kill_switch import exchange_probe as ep

REPO_ROOT = Path(__file__).resolve().parents[2]
WP_A6_PATH = REPO_ROOT / "tests" / "core" / "test_wp_a6_negative_quarantine_boundary_v1.py"
WP_A6_SHA256 = "7926a2dbd9fb8f917814b40ce56ff2d6165c63a778d66be4ae1eb78caa3993cd"

_IMPLICIT_VENUE_VALUES = frozenset(
    {
        "kraken",
        "okx",
        "kraken_ws",
        "okx_ws",
        "okx_europe_eea",
    }
)


def _assert_no_implicit_venue_default(value: object) -> None:
    if value is inspect.Parameter.empty or value is dataclasses.MISSING:
        return
    if isinstance(value, str) and value in _IMPLICIT_VENUE_VALUES:
        raise AssertionError(f"implicit venue default is not authorized: {value!r}")


def test_a_resilient_exchange_client_requires_explicit_exchange_id() -> None:
    from src.data.exchange_client import ResilientExchangeClient as ShimClient

    shim_param = inspect.signature(ShimClient.__init__).parameters["exchange_id"]
    assert shim_param.default is inspect.Parameter.empty
    _assert_no_implicit_venue_default(shim_param.default)

    with pytest.raises(TypeError):
        ShimClient()
    with pytest.raises(ValueError, match="exchange_id is required"):
        ShimClient(exchange_id="")
    with pytest.raises(ValueError, match="exchange_id is required"):
        ShimClient(exchange_id="   ")

    impl_src = (
        REPO_ROOT / "src" / "data" / "providers" / "resilient_ccxt_exchange_client.py"
    ).read_text(encoding="utf-8")
    shim_src = (REPO_ROOT / "src" / "data" / "exchange_client.py").read_text(encoding="utf-8")
    for src in (impl_src, shim_src):
        assert 'exchange_id: str = "kraken"' not in src
        assert 'exchange_id: str = "okx"' not in src


def test_a_impl_resilient_exchange_client_requires_explicit_exchange_id() -> None:
    pytest.importorskip("ccxt")
    from src.data.providers.resilient_ccxt_exchange_client import (
        ResilientExchangeClient as ImplClient,
    )

    impl_param = inspect.signature(ImplClient.__init__).parameters["exchange_id"]
    assert impl_param.default is inspect.Parameter.empty
    _assert_no_implicit_venue_default(impl_param.default)
    with pytest.raises(TypeError):
        ImplClient()
    with pytest.raises(ValueError, match="exchange_id is required"):
        ImplClient(exchange_id="")
    with pytest.raises(ValueError, match="exchange_id is required"):
        ImplClient(exchange_id="   ")


def test_b_ccxt_factory_missing_exchange_id_fail_closed() -> None:
    with pytest.raises(ValueError, match="exchange.id is required"):
        build_exchange_client_from_config(PeakConfig(raw={}))
    with pytest.raises(ValueError, match="exchange.id is required"):
        build_exchange_client_from_config(PeakConfig(raw={"exchange": {}}))
    with pytest.raises(ValueError, match="exchange.id is required"):
        build_exchange_client_from_config(PeakConfig(raw={"exchange": {"id": ""}}))
    with pytest.raises(ValueError, match="exchange.id is required"):
        build_exchange_client_from_config(PeakConfig(raw={"exchange": {"id": "   "}}))


def test_c_liveconfig_has_no_kraken_or_other_venue_default() -> None:
    field = LiveConfig.model_fields["exchange"]
    _assert_no_implicit_venue_default(field.default)
    cfg = LiveConfig()
    assert cfg.exchange == ""
    assert cfg.exchange not in _IMPLICIT_VENUE_VALUES


def test_d_kill_switch_probe_without_url_does_not_request(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[object] = []

    def _fake_urlopen(req, timeout=None):
        called.append((req, timeout))
        raise AssertionError("urlopen must not run without explicit probe URL")

    monkeypatch.setattr(ep.urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.delenv("PEAK_KILL_SWITCH_EXCHANGE_PROBE_URL", raising=False)
    ok, meta = ep.probe_exchange_http_public()
    assert ok is False
    assert called == []
    assert meta["probe_error"] == "probe_url_not_configured"
    assert "kraken" not in str(meta).lower()
    assert "api.kraken.com" not in str(meta).lower()
    probe_src = (REPO_ROOT / "src" / "risk_layer" / "kill_switch" / "exchange_probe.py").read_text(
        encoding="utf-8"
    )
    assert "api.kraken.com" not in probe_src
    assert not hasattr(ep, "_DEFAULT_PROBE_URL")


def test_e_health_dashboard_has_no_kraken_instantiation() -> None:
    src = (REPO_ROOT / "scripts" / "health_dashboard.py").read_text(encoding="utf-8")
    assert "ResilientExchangeClient" not in src
    assert 'exchange_id="kraken"' not in src
    assert "exchange_id='kraken'" not in src


def test_f_live_feed_requires_explicit_exchange() -> None:
    field = {f.name: f for f in dataclasses.fields(FeedConfig)}["exchange"]
    assert field.default is dataclasses.MISSING
    _assert_no_implicit_venue_default(field.default)
    with pytest.raises(TypeError):
        FeedConfig()  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="exchange is required"):
        FeedConfig(exchange="")
    with pytest.raises(ValueError, match="exchange is required"):
        FeedConfig(exchange="   ")


def test_g_shadow_tick_requires_explicit_source() -> None:
    field = {f.name: f for f in dataclasses.fields(Tick)}["source"]
    assert field.default is dataclasses.MISSING
    _assert_no_implicit_venue_default(field.default)
    with pytest.raises(TypeError):
        Tick(ts_ms=1000, price=1.0, volume=1.0, symbol="BTC/EUR")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="source is required"):
        Tick(ts_ms=1000, price=1.0, volume=1.0, symbol="BTC/EUR", source="")
    tick = Tick(ts_ms=1000, price=1.0, volume=1.0, symbol="BTC/EUR", source="test")
    assert tick.source == "test"
    assert tick.source not in {"kraken_ws", "okx_ws"}


def test_h_autonomous_monitor_requires_explicit_exchange() -> None:
    param = inspect.signature(MarketMonitor.is_market_hours).parameters["exchange"]
    assert param.default is inspect.Parameter.empty
    _assert_no_implicit_venue_default(param.default)
    monitor = MarketMonitor()
    with pytest.raises(TypeError):
        monitor.is_market_hours()  # type: ignore[call-arg]


def test_i_slice1_introduces_no_replacement_venue_defaults() -> None:
    root_exchange = toml.loads((REPO_ROOT / "config.toml").read_text(encoding="utf-8")).get(
        "exchange", {}
    )
    assert "id" not in root_exchange

    factory_src = (REPO_ROOT / "src" / "exchange" / "__init__.py").read_text(encoding="utf-8")
    for venue in _IMPLICIT_VENUE_VALUES:
        assert f'cfg.get("exchange.id", "{venue}")' not in factory_src

    live_feed_src = (REPO_ROOT / "src" / "data" / "feeds" / "live_feed.py").read_text(
        encoding="utf-8"
    )
    assert 'exchange: str = "kraken"' not in live_feed_src
    assert 'exchange: str = "okx"' not in live_feed_src

    models_src = (REPO_ROOT / "src" / "data" / "shadow" / "models.py").read_text(encoding="utf-8")
    assert 'source: str = "kraken_ws"' not in models_src
    assert 'source: str = "okx_ws"' not in models_src

    monitors_src = (REPO_ROOT / "src" / "autonomous" / "monitors.py").read_text(encoding="utf-8")
    assert 'exchange: str = "kraken"' not in monitors_src
    assert 'exchange: str = "okx"' not in monitors_src

    pydantic_src = (REPO_ROOT / "src" / "core" / "config_pydantic.py").read_text(encoding="utf-8")
    assert 'default="kraken"' not in pydantic_src
    assert 'default="okx"' not in pydantic_src


def test_j_forbidden_venue_fallbacks_preserved() -> None:
    assert "kraken_futures_demo" in EEA_FORBIDDEN_VENUE_FALLBACKS
    assert "kraken_futures_demo" in GLOBAL_FORBIDDEN_VENUE_FALLBACKS


def test_k_master_v2_and_double_play_paths_unmodified() -> None:
    master_v2 = REPO_ROOT / "src" / "trading" / "master_v2"
    assert master_v2.is_dir()
    wiring = master_v2 / "double_play_core_wiring_v1.py"
    assert wiring.is_file()
    forbidden_touch = [
        "src/trading/master_v2/",
        "src/exchange/kraken_live.py",
        "src/exchange/kraken_testnet.py",
        "src/orders/testnet_executor.py",
        "src/execution/live_session.py",
        "src/live/testnet_orchestrator.py",
        "pyproject.toml",
        "config/config.toml",
    ]
    # Presence-only: this GO must not delete these surfaces.
    for rel in forbidden_touch:
        path = REPO_ROOT / rel
        assert path.exists(), rel


def test_l_wp_a6_file_untouched() -> None:
    assert WP_A6_PATH.is_file()
    digest = hashlib.sha256(WP_A6_PATH.read_bytes()).hexdigest()
    assert digest == WP_A6_SHA256

"""v0 contract: Shadow no-order proof markers stay declarative; canonical env defaults stay safe."""

from __future__ import annotations

from pathlib import Path

from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.shadow_no_order_proof import markers_v0

_FORBIDDEN_SOURCE_MARKERS = (
    "requests",
    "httpx",
    "urllib.request",
    "socket",
    "subprocess",
    "ccxt",
    "aiohttp",
    "if __name__",
)


def test_shadow_no_order_markers_are_all_false_and_tagged() -> None:
    assert markers_v0.SHADOW_NO_ORDER_PROOF_V0 == "shadow_no_order_proof_v0"
    assert markers_v0.SHADOW_MODE_ALLOWED is False
    assert markers_v0.ORDER_SUBMISSION_ALLOWED is False
    assert markers_v0.BROKER_ALLOWED is False
    assert markers_v0.EXCHANGE_ALLOWED is False
    assert markers_v0.EXECUTABLE_COMMAND_CREATED is False
    assert markers_v0.LIVE_ALLOWED is False
    assert markers_v0.TESTNET_ALLOWED is False
    assert markers_v0.PAPER_ORDER_PATH_ALLOWED is False
    assert markers_v0.SCHEDULER_ALLOWED is False
    assert markers_v0.RUNTIME_ALLOWED is False


def test_markers_module_source_has_no_execution_or_network_tokens() -> None:
    path = Path(markers_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    low = text.lower()
    for needle in _FORBIDDEN_SOURCE_MARKERS:
        assert needle.lower() not in low, f"unexpected token {needle!r} in {path}"


def test_environment_config_defaults_remain_paper_and_gated() -> None:
    """Canonical owner: src.core.environment.EnvironmentConfig defaults."""
    cfg = EnvironmentConfig()
    assert cfg.environment == TradingEnvironment.PAPER
    assert cfg.enable_live_trading is False
    assert cfg.testnet_dry_run is True
    assert cfg.live_mode_armed is False
    assert cfg.live_dry_run_mode is True

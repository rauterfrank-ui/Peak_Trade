# tests/test_regime_aware_portfolio_component_overrides_v0.py
"""RegimeAwarePortfolioStrategy: nested vol_regime_filter config overrides (research v0)."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from src.core.peak_config import load_config
from src.strategies.registry import get_strategy_spec
from src.strategies.regime_aware_portfolio import (
    RegimeAwarePortfolioStrategy,
    generate_signals as regime_aware_generate_signals,
)
from src.strategies.vol_regime_filter import VolRegimeFilter


def _minimal_ohlcv(n: int = 120) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    close = pd.Series(50000.0, index=idx) + pd.Series(range(n), index=idx) * 0.1
    df = pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.001,
            "low": close * 0.999,
            "close": close,
            "volume": 100.0,
        },
        index=idx,
    )
    return df


@pytest.fixture
def cfg():
    return load_config()


@pytest.fixture
def portfolio_section() -> str:
    return "portfolio.regime_aware_breakout_rsi"


class TestRegimePortfolioComponentOverrides:
    def test_default_vol_regime_filter_regime_mode_from_config(
        self, cfg, portfolio_section: str
    ) -> None:
        spec = get_strategy_spec("vol_regime_filter")
        expected_regime_mode = VolRegimeFilter.from_config(
            cfg, section=spec.config_section
        ).regime_mode
        strat = RegimeAwarePortfolioStrategy.from_config(
            cfg, section=portfolio_section, param_overrides={}
        )
        df = _minimal_ohlcv()
        strat.generate_signals(df)
        assert strat._regime_strategy is not None
        assert strat._regime_strategy.regime_mode is expected_regime_mode

    def test_override_short_key_reaches_embedded_vol_regime_filter(
        self, cfg, portfolio_section: str
    ) -> None:
        strat = RegimeAwarePortfolioStrategy.from_config(
            cfg,
            section=portfolio_section,
            param_overrides={"vol_regime_filter.regime_mode": True},
        )
        df = _minimal_ohlcv()
        strat.generate_signals(df)
        assert getattr(strat._regime_strategy, "regime_mode", None) is True

    def test_override_full_strategy_key_reaches_embedded_vol_regime_filter(
        self, cfg, portfolio_section: str
    ) -> None:
        strat = RegimeAwarePortfolioStrategy.from_config(
            cfg,
            section=portfolio_section,
            param_overrides={"strategy.vol_regime_filter.regime_mode": True},
        )
        df = _minimal_ohlcv()
        strat.generate_signals(df)
        assert getattr(strat._regime_strategy, "regime_mode", None) is True

    def test_portfolio_level_overrides_still_apply(self, cfg, portfolio_section: str) -> None:
        strat = RegimeAwarePortfolioStrategy.from_config(
            cfg,
            section=portfolio_section,
            param_overrides={"neutral_scale": 0.37},
        )
        assert strat.neutral_scale == pytest.approx(0.37)

    def test_config_dict_nested_keys_after_engine_merge(self, cfg, portfolio_section: str) -> None:
        strat = RegimeAwarePortfolioStrategy.from_config(
            cfg, section=portfolio_section, param_overrides={}
        )
        strat.config["vol_regime_filter.regime_mode"] = True
        df = _minimal_ohlcv()
        strat.generate_signals(df)
        assert getattr(strat._regime_strategy, "regime_mode", None) is True

    def test_legacy_generate_signals_applies_vol_regime_overrides(
        self, cfg, portfolio_section: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Walk-forward / load_strategy path uses module generate_signals(df, params)."""
        base = RegimeAwarePortfolioStrategy.from_config(
            cfg, section=portfolio_section, param_overrides={}
        )
        params = {
            "components": base.components,
            "base_weights": base.base_weights,
            "regime_strategy": base.regime_strategy_name,
            "mode": base.mode,
            "risk_on_scale": base.risk_on_scale,
            "neutral_scale": base.neutral_scale,
            "risk_off_scale": base.risk_off_scale,
            "signal_threshold": base.signal_threshold,
            "strategy.vol_regime_filter.regime_mode": True,
        }
        df = _minimal_ohlcv()
        with caplog.at_level(logging.WARNING, logger="src.strategies.regime_aware_portfolio"):
            regime_aware_generate_signals(df, params)
        assert not any("regime_mode=False" in rec.message for rec in caplog.records), caplog.text

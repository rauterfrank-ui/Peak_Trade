# tests/test_r_and_d_strategy_gating.py
"""
Tests für R&D-Strategy Gating-Logic.

Testet das 3-stufige Gate-System in src/strategies/registry.py:
- Gate A: Live-Mode Hard-Gate (IS_LIVE_READY=False)
- Gate B: R&D-Tier-Gate (TIER="r_and_d" + allow_r_and_d_strategies)
- Gate C: Allowed-Environments-Gate (ALLOWED_ENVIRONMENTS)

Testet außerdem Stub-Verhalten der Research-Strategien:
- Ehlers: generate_signals() → pd.Series(0)
- Meta-Labeling: generate_signals() → pd.Series(0)
- VolRegimeOverlay: generate_signals() → NotImplementedError
- BouchaudMicrostructure: generate_signals() → NotImplementedError
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.registry import create_strategy_from_config


# =============================================================================
# DUMMY CONFIG (Minimal Config-Objekt mit .get() Methode)
# =============================================================================


class DummyConfig:
    """
    Minimales Config-Objekt für Tests.

    Implementiert nur .get() Methode, um registry.create_strategy_from_config()
    zu unterstützen.
    """

    def __init__(self, d: dict):
        self.d = d

    def get(self, key: str, default=None):
        """Holt Wert aus Config-Dict mit Fallback."""
        keys = key.split(".")
        val = self.d
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val


# =============================================================================
# HELPER: Test-DataFrame erstellen
# =============================================================================


def create_test_df(n_bars: int = 150) -> pd.DataFrame:
    """
    Erzeugt Test-DataFrame mit OHLCV-Daten.

    Args:
        n_bars: Anzahl Bars

    Returns:
        DataFrame mit Spalten: open, high, low, close, volume
    """
    df = pd.DataFrame(
        {
            "open": [100.0 + i * 0.1 for i in range(n_bars)],
            "high": [100.5 + i * 0.1 for i in range(n_bars)],
            "low": [99.5 + i * 0.1 for i in range(n_bars)],
            "close": [100.0 + i * 0.1 for i in range(n_bars)],
            "volume": [1000.0] * n_bars,
        }
    )
    df.index = pd.date_range("2024-01-01", periods=n_bars, freq="1h")
    return df


# =============================================================================
# TESTS: Gate A – Live-Mode Hard-Gate (IS_LIVE_READY=False)
# =============================================================================


def test_gate_a_ehlers_blocked_in_live_mode():
    """
    Test Gate A: Ehlers Cycle Filter (IS_LIVE_READY=False) in live mode → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "live"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                    "min_cycle_length": 6,
                    "max_cycle_length": 50,
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("ehlers_cycle_filter", cfg)

    assert "cannot be used in LIVE mode" in str(excinfo.value)
    assert "IS_LIVE_READY=False" in str(excinfo.value)


def test_gate_a_meta_labeling_blocked_in_live_mode():
    """
    Test Gate A: Meta-Labeling (IS_LIVE_READY=False) in live mode → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "live"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "meta_labeling": {
                    "base_strategy_id": "rsi_reversion",
                    "take_profit": 0.02,
                    "stop_loss": 0.01,
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("meta_labeling", cfg)

    assert "cannot be used in LIVE mode" in str(excinfo.value)


def test_gate_a_vol_regime_blocked_in_live_mode():
    """
    Test Gate A: Vol-Regime-Overlay (IS_LIVE_READY=False) in live mode → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "live"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("vol_regime_overlay", cfg)

    assert "cannot be used in LIVE mode" in str(excinfo.value)


def test_gate_a_bouchaud_blocked_in_live_mode():
    """
    Test Gate A: Bouchaud Microstructure (IS_LIVE_READY=False) in live mode → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "live"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "bouchaud_microstructure": {
                    "use_orderbook_imbalance": True,
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("bouchaud_microstructure", cfg)

    assert "cannot be used in LIVE mode" in str(excinfo.value)


# =============================================================================
# TESTS: Gate B – R&D-Tier-Gate (allow_r_and_d_strategies)
# =============================================================================


def test_gate_b_ehlers_blocked_without_rnd_flag():
    """
    Test Gate B: Ehlers (TIER=r_and_d) ohne allow_r_and_d_strategies → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": False},  # BLOCKED
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("ehlers_cycle_filter", cfg)

    assert "R&D-only" in str(excinfo.value)
    assert "TIER=r_and_d" in str(excinfo.value)
    assert "allow_r_and_d_strategies" in str(excinfo.value)


def test_gate_b_ehlers_allowed_with_rnd_flag():
    """
    Test Gate B: Ehlers (TIER=r_and_d) MIT allow_r_and_d_strategies → OK.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": True},  # ALLOWED
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    # Sollte NICHT raisen
    strategy = create_strategy_from_config("ehlers_cycle_filter", cfg)
    assert strategy is not None
    assert strategy.KEY == "ehlers_cycle_filter"


def test_gate_b_meta_labeling_blocked_without_rnd_flag():
    """
    Test Gate B: Meta-Labeling (TIER=r_and_d) ohne allow_r_and_d_strategies → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": False},  # BLOCKED
            "strategy": {
                "meta_labeling": {
                    "base_strategy_id": "rsi_reversion",
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("meta_labeling", cfg)

    assert "R&D-only" in str(excinfo.value)


def test_gate_b_meta_labeling_allowed_with_rnd_flag():
    """
    Test Gate B: Meta-Labeling (TIER=r_and_d) MIT allow_r_and_d_strategies → OK.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": True},  # ALLOWED
            "strategy": {
                "meta_labeling": {
                    "base_strategy_id": "rsi_reversion",
                }
            },
        }
    )

    strategy = create_strategy_from_config("meta_labeling", cfg)
    assert strategy is not None
    assert strategy.KEY == "meta_labeling"


# =============================================================================
# TESTS: Gate C – Allowed-Environments-Gate
# =============================================================================


def test_gate_c_ehlers_blocked_in_paper_mode():
    """
    Test Gate C: Ehlers (ALLOWED_ENVIRONMENTS=["offline_backtest", "research"])
    in "paper" mode → ValueError.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "paper"},  # NOT in ALLOWED_ENVIRONMENTS
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("ehlers_cycle_filter", cfg)

    assert "not allowed in environment" in str(excinfo.value)
    assert "paper" in str(excinfo.value)


def test_gate_c_ehlers_allowed_in_research_mode():
    """
    Test Gate C: Ehlers in "research" mode → OK (in ALLOWED_ENVIRONMENTS).
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "research"},  # ALLOWED
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    strategy = create_strategy_from_config("ehlers_cycle_filter", cfg)
    assert strategy is not None


# =============================================================================
# TESTS: Stub-Verhalten – Flat-Signal (Ehlers, Meta-Labeling)
# =============================================================================


def test_ehlers_stub_returns_flat_signal():
    """
    Test: Ehlers generate_signals() gibt pd.Series(0) zurück (Stub-Implementierung).
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                    "lookback": 100,
                }
            },
        }
    )

    strategy = create_strategy_from_config("ehlers_cycle_filter", cfg)
    df = create_test_df(n_bars=150)

    signals = strategy.generate_signals(df)

    # Stub: Alle Signale = 0 (flat)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(df)
    assert (signals == 0).all()


def test_meta_labeling_stub_returns_flat_signal():
    """
    Test: Meta-Labeling generate_signals() gibt pd.Series(0) zurück (Stub-Implementierung).
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "meta_labeling": {
                    "base_strategy_id": "rsi_reversion",
                    "take_profit": 0.02,
                }
            },
        }
    )

    strategy = create_strategy_from_config("meta_labeling", cfg)
    df = create_test_df(n_bars=150)

    signals = strategy.generate_signals(df)

    # Stub: Alle Signale = 0 (flat)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(df)
    assert (signals == 0).all()


# =============================================================================
# TESTS: Skeleton-Verhalten – NotImplementedError (VolRegime, Bouchaud)
# =============================================================================


def test_vol_regime_overlay_raises_not_implemented():
    """
    Test: Vol-Regime-Overlay generate_signals() wirft NotImplementedError (Skeleton).
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                }
            },
        }
    )

    strategy = create_strategy_from_config("vol_regime_overlay", cfg)
    df = create_test_df(n_bars=150)

    # Skeleton: NotImplementedError
    with pytest.raises(NotImplementedError) as excinfo:
        strategy.generate_signals(df)

    assert "Meta-Layer" in str(excinfo.value) or "NOT IMPLEMENTED" in str(excinfo.value)


def test_bouchaud_microstructure_raises_not_implemented():
    """
    Test: Bouchaud Microstructure generate_signals() wirft NotImplementedError (Skeleton).
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "bouchaud_microstructure": {
                    "use_orderbook_imbalance": True,
                }
            },
        }
    )

    strategy = create_strategy_from_config("bouchaud_microstructure", cfg)
    df = create_test_df(n_bars=150)

    # Skeleton: NotImplementedError
    with pytest.raises(NotImplementedError) as excinfo:
        strategy.generate_signals(df)

    assert "Platzhalter" in str(excinfo.value) or "SKELETON" in str(excinfo.value)


# =============================================================================
# TESTS: Edge Cases – Config-Fallbacks
# =============================================================================


def test_gate_env_fallback_env_mode():
    """
    Test: Environment-Mode-Fallback auf env.mode funktioniert.
    """
    cfg = DummyConfig(
        {
            "env": {"mode": "live"},  # Fallback-Key
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    # Sollte raisen, da env.mode="live" erkannt wird
    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("ehlers_cycle_filter", cfg)

    assert "cannot be used in LIVE mode" in str(excinfo.value)


def test_gate_env_fallback_runtime_environment():
    """
    Test: Environment-Mode-Fallback auf runtime.environment funktioniert.
    """
    cfg = DummyConfig(
        {
            "runtime": {"environment": "live"},  # Fallback-Key
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    # Sollte raisen, da runtime.environment="live" erkannt wird
    with pytest.raises(ValueError) as excinfo:
        create_strategy_from_config("ehlers_cycle_filter", cfg)

    assert "cannot be used in LIVE mode" in str(excinfo.value)


def test_gate_default_env_offline_backtest():
    """
    Test: Default Environment ist "offline_backtest" wenn nicht gesetzt.
    """
    cfg = DummyConfig(
        {
            # Kein environment.mode / env.mode / runtime.environment
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {
                "ehlers_cycle_filter": {
                    "smoother_type": "super_smoother",
                }
            },
        }
    )

    # Sollte NICHT raisen (offline_backtest ist allowed)
    strategy = create_strategy_from_config("ehlers_cycle_filter", cfg)
    assert strategy is not None


# =============================================================================
# TESTS: Produktive Strategien – Sollten NICHT von allow_r_and_d abhängen
# =============================================================================


def test_productive_strategy_not_affected_by_rnd_flag():
    """
    Test: Produktive Strategie (z.B. ma_crossover) funktioniert unabhängig
    vom allow_r_and_d_strategies Flag.
    """
    cfg = DummyConfig(
        {
            "environment": {"mode": "offline_backtest"},
            "research": {"allow_r_and_d_strategies": False},  # R&D disabled
            "strategy": {
                "ma_crossover": {
                    "fast_window": 10,
                    "slow_window": 50,
                }
            },
        }
    )

    # Sollte NICHT raisen (productive strategy, kein TIER=r_and_d)
    strategy = create_strategy_from_config("ma_crossover", cfg)
    assert strategy is not None
    assert strategy.KEY == "ma_crossover"


# =============================================================================
# RUN (wenn direkt ausgeführt)
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

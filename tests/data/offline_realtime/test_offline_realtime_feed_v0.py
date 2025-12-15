"""
Tests für OfflineRealtimeFeedV0
================================

Testet:
1. Smoke-Test: Grundlegende Funktionalität
2. Regime-Verhalten: Unterschiedliche Volatilitäten pro Regime
3. Reproduzierbarkeit: Gleicher Seed → gleiche Sequenz

WICHTIG: Diese Tests sind für Offline-Simulation.
         Niemals für Live-Trading verwenden!
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
import pytest

from src.data.offline_realtime import (
    GarchRegimeModelV0,
    GarchRegimeState,
    OfflineRealtimeFeedV0,
    OfflineRealtimeFeedV0Config,
    RegimeParams,
    SyntheticTick,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def simple_config() -> OfflineRealtimeFeedV0Config:
    """Einfache 2-Regime Konfiguration für Tests."""
    return OfflineRealtimeFeedV0Config(
        base_price=50000.0,
        dt=timedelta(seconds=1),
        num_ticks=1000,
        regime_params=[
            RegimeParams(omega=1e-6, alpha=0.05, beta=0.90, nu=5.0, name="low_vol"),
            RegimeParams(omega=1e-5, alpha=0.10, beta=0.85, nu=4.0, name="high_vol"),
        ],
        transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
        seed=42,
        initial_regime=0,
    )


@pytest.fixture
def high_vol_contrast_config() -> OfflineRealtimeFeedV0Config:
    """Konfiguration mit stark unterschiedlichen Volatilitäten für Regime-Tests."""
    return OfflineRealtimeFeedV0Config(
        base_price=100.0,
        dt=timedelta(seconds=1),
        num_ticks=10000,
        regime_params=[
            # Regime 0: Sehr ruhig
            RegimeParams(omega=1e-8, alpha=0.01, beta=0.98, nu=10.0, name="calm"),
            # Regime 1: Sehr wild
            RegimeParams(omega=1e-4, alpha=0.20, beta=0.70, nu=3.5, name="wild"),
        ],
        transition_matrix=[[0.95, 0.05], [0.10, 0.90]],
        seed=123,
        initial_regime=0,
    )


# ==============================================================================
# GarchRegimeModelV0 Tests
# ==============================================================================


class TestGarchRegimeModelV0:
    """Tests für das GARCH-Regime-Modell."""

    def test_model_creation(self):
        """Modell kann erstellt werden."""
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )
        assert model.n_regimes == 1
        assert model.current_regime == 0

    def test_step_returns_state(self):
        """step() gibt GarchRegimeState zurück."""
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )
        state = model.step()

        assert isinstance(state, GarchRegimeState)
        assert state.regime_id == 0
        assert state.sigma_t > 0
        assert state.sigma_sq_t > 0
        assert state.step_idx == 0

    def test_multiple_steps(self):
        """Mehrere Schritte funktionieren."""
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        states = [model.step() for _ in range(100)]

        assert len(states) == 100
        assert states[0].step_idx == 0
        assert states[99].step_idx == 99

    def test_regime_switching(self):
        """Regime wechselt bei nicht-trivialer Transition-Matrix."""
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
                {"omega": 5e-5, "alpha": 0.15, "beta": 0.80, "nu": 4.0},
            ],
            transition_matrix=[[0.90, 0.10], [0.10, 0.90]],
            seed=42,
        )

        regime_ids = [model.step().regime_id for _ in range(1000)]

        assert 0 in regime_ids
        assert 1 in regime_ids

    def test_reset(self):
        """reset() setzt das Modell zurück."""
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        # Generiere einige Steps
        states1 = [model.step() for _ in range(10)]

        # Reset
        model.reset()

        # Generiere nochmal
        states2 = [model.step() for _ in range(10)]

        # Sollte identisch sein
        for s1, s2 in zip(states1, states2):
            assert s1.return_t == s2.return_t

    def test_generate_returns(self):
        """generate_returns() funktioniert."""
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
                {"omega": 5e-5, "alpha": 0.15, "beta": 0.80, "nu": 4.0},
            ],
            transition_matrix=[[0.95, 0.05], [0.10, 0.90]],
            seed=42,
        )

        returns, regime_ids = model.generate_returns(1000)

        assert len(returns) == 1000
        assert len(regime_ids) == 1000
        assert returns.dtype == np.float64
        assert regime_ids.dtype == np.int32


class TestGarchRegimeModelValidation:
    """Tests für Parameter-Validierung."""

    def test_empty_regimes_raises(self):
        """Leere Regime-Liste wird abgelehnt."""
        with pytest.raises(ValueError, match="Mindestens ein Regime"):
            GarchRegimeModelV0(
                regime_params=[],
                transition_matrix=[],
            )

    def test_negative_omega_raises(self):
        """Negatives omega wird abgelehnt."""
        with pytest.raises(ValueError, match="omega"):
            GarchRegimeModelV0(
                regime_params=[
                    {"omega": -1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
                ],
                transition_matrix=[[1.0]],
            )

    def test_invalid_nu_raises(self):
        """nu <= 2 wird abgelehnt."""
        with pytest.raises(ValueError, match="nu"):
            GarchRegimeModelV0(
                regime_params=[
                    {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 2.0},
                ],
                transition_matrix=[[1.0]],
            )

    def test_transition_matrix_size_mismatch(self):
        """Falsche Transition-Matrix-Größe wird abgelehnt."""
        with pytest.raises(ValueError, match="transition_matrix"):
            GarchRegimeModelV0(
                regime_params=[
                    {"omega": 1e-5, "alpha": 0.1, "beta": 0.85, "nu": 5.0},
                ],
                transition_matrix=[[0.5, 0.5]],  # 1 Regime, aber 2 Spalten
            )


# ==============================================================================
# SyntheticTick Tests
# ==============================================================================


class TestSyntheticTick:
    """Tests für SyntheticTick Dataclass."""

    def test_tick_creation(self):
        """Tick kann erstellt werden."""
        ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        tick = SyntheticTick(
            timestamp=ts,
            price=50000.0,
            ret=0.001,
            regime_id=0,
            volume=100.0,
            is_synthetic=True,
            sigma=0.01,
            sim_run_id="test-123",
        )

        assert tick.timestamp == ts
        assert tick.price == 50000.0
        assert tick.ret == 0.001
        assert tick.regime_id == 0
        assert tick.is_synthetic is True

    def test_is_synthetic_always_true(self):
        """is_synthetic ist IMMER True, auch wenn False übergeben wird."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        tick = SyntheticTick(
            timestamp=ts,
            price=100.0,
            ret=0.0,
            regime_id=0,
            volume=50.0,
            is_synthetic=False,  # Versuche False
            sigma=0.01,
            sim_run_id="test",
        )

        # MUSS trotzdem True sein (Safety-Feature)
        assert tick.is_synthetic is True

    def test_tick_repr(self):
        """__repr__ funktioniert."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        tick = SyntheticTick(
            timestamp=ts,
            price=50000.0,
            ret=0.001,
            regime_id=1,
            volume=100.0,
            is_synthetic=True,
            sigma=0.01,
            sim_run_id="test-123",
        )

        repr_str = repr(tick)
        assert "SyntheticTick" in repr_str
        assert "50000" in repr_str
        assert "regime=1" in repr_str


# ==============================================================================
# RegimeParams Tests
# ==============================================================================


class TestRegimeParams:
    """Tests für RegimeParams."""

    def test_valid_params(self):
        """Gültige Parameter werden akzeptiert."""
        params = RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0)
        assert params.omega == 1e-5
        assert params.alpha == 0.1

    def test_to_dict(self):
        """to_dict() funktioniert."""
        params = RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0)
        d = params.to_dict()

        assert d["omega"] == 1e-5
        assert d["alpha"] == 0.1
        assert d["beta"] == 0.85
        assert d["nu"] == 5.0

    def test_negative_omega_raises(self):
        """Negatives omega wird abgelehnt."""
        with pytest.raises(ValueError, match="omega"):
            RegimeParams(omega=-1e-5, alpha=0.1, beta=0.85, nu=5.0)

    def test_invalid_alpha_raises(self):
        """alpha außerhalb [0, 1] wird abgelehnt."""
        with pytest.raises(ValueError, match="alpha"):
            RegimeParams(omega=1e-5, alpha=1.5, beta=0.85, nu=5.0)

    def test_invalid_nu_raises(self):
        """nu <= 2 wird abgelehnt."""
        with pytest.raises(ValueError, match="nu"):
            RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=1.5)


# ==============================================================================
# OfflineRealtimeFeedV0Config Tests
# ==============================================================================


class TestOfflineRealtimeFeedV0Config:
    """Tests für Feed-Konfiguration."""

    def test_valid_config(self, simple_config):
        """Gültige Konfiguration wird akzeptiert."""
        assert simple_config.base_price == 50000.0
        assert simple_config.num_ticks == 1000
        assert simple_config.n_regimes == 2

    def test_invalid_base_price(self):
        """base_price <= 0 wird abgelehnt."""
        with pytest.raises(ValueError, match="base_price"):
            OfflineRealtimeFeedV0Config(
                base_price=0,
                dt=timedelta(seconds=1),
                num_ticks=100,
                regime_params=[RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0)],
                transition_matrix=[[1.0]],
            )

    def test_invalid_num_ticks(self):
        """num_ticks <= 0 wird abgelehnt."""
        with pytest.raises(ValueError, match="num_ticks"):
            OfflineRealtimeFeedV0Config(
                base_price=100.0,
                dt=timedelta(seconds=1),
                num_ticks=0,
                regime_params=[RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0)],
                transition_matrix=[[1.0]],
            )


# ==============================================================================
# Smoke Tests
# ==============================================================================


class TestSmokeTests:
    """Smoke-Tests: Grundlegende Funktionalität."""

    def test_generate_10000_ticks(self, simple_config):
        """10.000 Ticks ohne Exception generieren."""
        config = OfflineRealtimeFeedV0Config(
            base_price=50000.0,
            dt=timedelta(seconds=1),
            num_ticks=10000,
            regime_params=[
                RegimeParams(omega=1e-6, alpha=0.05, beta=0.90, nu=5.0),
                RegimeParams(omega=1e-5, alpha=0.10, beta=0.85, nu=4.0),
            ],
            transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)
        ticks = list(feed.generate_ticks())

        # Keine Exception, korrekte Anzahl
        assert len(ticks) == 10000

    def test_all_ticks_synthetic(self, simple_config):
        """Alle Ticks haben is_synthetic=True."""
        feed = OfflineRealtimeFeedV0(simple_config)
        ticks = list(feed.generate_ticks())

        assert all(t.is_synthetic for t in ticks), "ALLE Ticks MÜSSEN is_synthetic=True haben!"

    def test_prices_positive(self, simple_config):
        """Alle Preise bleiben positiv."""
        feed = OfflineRealtimeFeedV0(simple_config)
        ticks = list(feed.generate_ticks())

        assert all(t.price > 0 for t in ticks), "Alle Preise müssen > 0 sein!"

    def test_timestamps_increasing(self, simple_config):
        """Timestamps sind streng aufsteigend."""
        feed = OfflineRealtimeFeedV0(simple_config)
        ticks = list(feed.generate_ticks())

        for i in range(1, len(ticks)):
            assert ticks[i].timestamp > ticks[i - 1].timestamp

    def test_to_dataframe(self, simple_config):
        """to_dataframe() funktioniert."""
        feed = OfflineRealtimeFeedV0(simple_config)
        df = feed.to_dataframe()

        assert len(df) == simple_config.num_ticks
        assert "price" in df.columns
        assert "ret" in df.columns
        assert "regime_id" in df.columns
        assert "is_synthetic" in df.columns
        assert df["is_synthetic"].all()


# ==============================================================================
# Regime-Verhalten Tests
# ==============================================================================


class TestRegimeBehavior:
    """Tests für Regime-Verhalten."""

    def test_regime_ids_valid(self, simple_config):
        """Regime-IDs sind im gültigen Bereich."""
        feed = OfflineRealtimeFeedV0(simple_config)
        ticks = list(feed.generate_ticks())

        for tick in ticks:
            assert 0 <= tick.regime_id < simple_config.n_regimes

    def test_multiple_regimes_occur(self, simple_config):
        """Bei 2 Regimes treten beide auf."""
        feed = OfflineRealtimeFeedV0(simple_config)
        ticks = list(feed.generate_ticks())

        regime_ids = {t.regime_id for t in ticks}
        assert len(regime_ids) >= 2, "Bei 2 Regimes sollten beide auftreten"

    def test_high_vol_regime_has_higher_variance(self, high_vol_contrast_config):
        """Regime 1 (wild) hat höhere empirische Varianz als Regime 0 (calm)."""
        feed = OfflineRealtimeFeedV0(high_vol_contrast_config)
        ticks = list(feed.generate_ticks())

        # Returns pro Regime sammeln
        returns_regime_0 = [t.ret for t in ticks if t.regime_id == 0]
        returns_regime_1 = [t.ret for t in ticks if t.regime_id == 1]

        # Sicherstellen, dass beide Regimes genug Samples haben
        assert len(returns_regime_0) > 100, "Zu wenig Samples für Regime 0"
        assert len(returns_regime_1) > 100, "Zu wenig Samples für Regime 1"

        # Empirische Varianz berechnen
        var_regime_0 = np.var(returns_regime_0)
        var_regime_1 = np.var(returns_regime_1)

        # Regime 1 (wild) sollte höhere Varianz haben
        assert var_regime_1 > var_regime_0, (
            f"Regime 1 (wild) sollte höhere Varianz haben. "
            f"Var(Regime 0) = {var_regime_0:.2e}, Var(Regime 1) = {var_regime_1:.2e}"
        )


# ==============================================================================
# Reproduzierbarkeit Tests
# ==============================================================================


class TestReproducibility:
    """Tests für Reproduzierbarkeit."""

    def test_same_seed_same_sequence(self):
        """Gleicher Seed → identische Sequenz."""
        config1 = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=100,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=12345,
        )

        config2 = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=100,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=12345,
        )

        feed1 = OfflineRealtimeFeedV0(config1)
        feed2 = OfflineRealtimeFeedV0(config2)

        ticks1 = list(feed1.generate_ticks())
        ticks2 = list(feed2.generate_ticks())

        for t1, t2 in zip(ticks1, ticks2):
            assert t1.price == t2.price, "Preise sollten identisch sein"
            assert t1.ret == t2.ret, "Returns sollten identisch sein"
            assert t1.regime_id == t2.regime_id, "Regime-IDs sollten identisch sein"

    def test_different_seed_different_sequence(self):
        """Verschiedene Seeds → verschiedene Sequenzen."""
        config1 = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=100,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=11111,
        )

        config2 = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=100,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=22222,
        )

        feed1 = OfflineRealtimeFeedV0(config1)
        feed2 = OfflineRealtimeFeedV0(config2)

        ticks1 = list(feed1.generate_ticks())
        ticks2 = list(feed2.generate_ticks())

        # Mindestens einige Preise sollten unterschiedlich sein
        different_prices = sum(1 for t1, t2 in zip(ticks1, ticks2) if t1.price != t2.price)
        assert different_prices > 0, "Verschiedene Seeds sollten verschiedene Sequenzen erzeugen"

    def test_reset_restores_sequence(self):
        """reset() stellt die ursprüngliche Sequenz wieder her."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=50,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)

        # Erste Sequenz
        ticks1 = list(feed.generate_ticks())

        # Reset und zweite Sequenz
        feed.reset()
        ticks2 = list(feed.generate_ticks())

        for t1, t2 in zip(ticks1, ticks2):
            assert t1.price == t2.price


# ==============================================================================
# Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests für Randfälle."""

    def test_single_tick(self):
        """Einzelner Tick funktioniert."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=1,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)
        ticks = list(feed.generate_ticks())

        assert len(ticks) == 1
        assert ticks[0].is_synthetic is True

    def test_single_regime(self):
        """Einzelnes Regime funktioniert."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=100,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)
        ticks = list(feed.generate_ticks())

        assert all(t.regime_id == 0 for t in ticks)

    def test_four_regimes(self):
        """4 Regimes funktionieren."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=5000,
            regime_params=[
                RegimeParams(omega=1e-6, alpha=0.05, beta=0.90, nu=6.0),
                RegimeParams(omega=5e-6, alpha=0.08, beta=0.88, nu=5.0),
                RegimeParams(omega=1e-5, alpha=0.10, beta=0.85, nu=4.5),
                RegimeParams(omega=5e-5, alpha=0.15, beta=0.80, nu=4.0),
            ],
            transition_matrix=[
                [0.90, 0.05, 0.03, 0.02],
                [0.05, 0.85, 0.07, 0.03],
                [0.03, 0.07, 0.85, 0.05],
                [0.02, 0.03, 0.05, 0.90],
            ],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)
        ticks = list(feed.generate_ticks())

        regime_ids = {t.regime_id for t in ticks}
        # Bei 5000 Ticks sollten alle 4 Regimes auftreten
        assert len(regime_ids) == 4

    def test_millisecond_dt(self):
        """100ms Zeitschritt funktioniert."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(milliseconds=100),
            num_ticks=100,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)
        ticks = list(feed.generate_ticks())

        # Prüfe Zeitabstand
        dt_actual = (ticks[1].timestamp - ticks[0].timestamp).total_seconds()
        assert dt_actual == pytest.approx(0.1)

    def test_minute_dt(self):
        """1min Zeitschritt funktioniert."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(minutes=1),
            num_ticks=10,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        feed = OfflineRealtimeFeedV0(config)
        ticks = list(feed.generate_ticks())

        # Prüfe Zeitabstand
        dt_actual = (ticks[1].timestamp - ticks[0].timestamp).total_seconds()
        assert dt_actual == pytest.approx(60.0)

    def test_sim_run_id_unique(self):
        """Jede Feed-Instanz hat eine eindeutige sim_run_id."""
        config = OfflineRealtimeFeedV0Config(
            base_price=100.0,
            dt=timedelta(seconds=1),
            num_ticks=10,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.1, beta=0.85, nu=5.0),
            ],
            transition_matrix=[[1.0]],
            seed=42,
        )

        feed1 = OfflineRealtimeFeedV0(config)
        feed2 = OfflineRealtimeFeedV0(config)

        assert feed1.sim_run_id != feed2.sim_run_id

    def test_repr_str(self, simple_config):
        """__repr__ und __str__ funktionieren."""
        feed = OfflineRealtimeFeedV0(simple_config)

        repr_str = repr(feed)
        str_str = str(feed)

        assert "OfflineRealtimeFeedV0" in repr_str
        assert "OfflineRealtimeFeedV0" in str_str
        assert "1000" in str_str  # num_ticks

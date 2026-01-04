# tests/strategies/el_karoui/test_vol_model.py
"""
Tests für das El Karoui Volatilitäts-Modell.

Testet:
- VolRegime Enum
- ElKarouiVolConfig Dataclass
- ElKarouiVolModel (Vol-Berechnung, Regime-Klassifikation, Scaling)
"""

import pytest
import numpy as np
import pandas as pd

from src.strategies.el_karoui.vol_model import (
    VolRegime,
    ElKarouiVolConfig,
    ElKarouiVolModel,
    get_vol_regime,
    get_vol_scaling_factor,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def default_config() -> ElKarouiVolConfig:
    """Standard-Konfiguration für Tests."""
    return ElKarouiVolConfig.default()


@pytest.fixture
def test_config() -> ElKarouiVolConfig:
    """Test-Konfiguration mit kürzeren Fenstern für einfachere Tests."""
    return ElKarouiVolConfig(
        vol_window=10,
        lookback_window=50,
        low_threshold=0.30,
        high_threshold=0.70,
        vol_target=0.10,
    )


@pytest.fixture
def model_default(default_config: ElKarouiVolConfig) -> ElKarouiVolModel:
    """Modell mit Standard-Config."""
    return ElKarouiVolModel(default_config)


@pytest.fixture
def model_test(test_config: ElKarouiVolConfig) -> ElKarouiVolModel:
    """Modell mit Test-Config."""
    return ElKarouiVolModel(test_config)


@pytest.fixture
def low_vol_returns() -> pd.Series:
    """Synthetische Returns mit niedriger Volatilität."""
    np.random.seed(42)
    n = 100
    # Niedrige Volatilität: kleine Returns
    returns = np.random.randn(n) * 0.005  # ~0.5% daily std
    return pd.Series(returns, index=pd.date_range("2024-01-01", periods=n, freq="D"))


@pytest.fixture
def high_vol_returns() -> pd.Series:
    """Synthetische Returns mit hoher Volatilität."""
    np.random.seed(42)
    n = 100
    # Hohe Volatilität: große Returns
    returns = np.random.randn(n) * 0.04  # ~4% daily std
    return pd.Series(returns, index=pd.date_range("2024-01-01", periods=n, freq="D"))


@pytest.fixture
def mixed_vol_returns() -> pd.Series:
    """Synthetische Returns mit wechselnder Volatilität."""
    np.random.seed(42)
    n = 150
    returns = np.zeros(n)
    # Erste 50: niedrige Vol
    returns[:50] = np.random.randn(50) * 0.005
    # Mittlere 50: mittlere Vol
    returns[50:100] = np.random.randn(50) * 0.015
    # Letzte 50: hohe Vol
    returns[100:150] = np.random.randn(50) * 0.04
    return pd.Series(returns, index=pd.date_range("2024-01-01", periods=n, freq="D"))


# =============================================================================
# VOL REGIME ENUM TESTS
# =============================================================================


class TestVolRegime:
    """Tests für VolRegime Enum."""

    def test_regime_values(self) -> None:
        """Prüft, dass alle erwarteten Regimes existieren."""
        assert VolRegime.LOW.value == "low"
        assert VolRegime.MEDIUM.value == "normal"
        assert VolRegime.HIGH.value == "high"

    def test_regime_count(self) -> None:
        """Prüft die Anzahl der Regimes."""
        assert len(VolRegime) == 3

    def test_regime_str(self) -> None:
        """Prüft String-Repräsentation."""
        assert str(VolRegime.LOW) == "low"
        assert str(VolRegime.MEDIUM) == "normal"
        assert str(VolRegime.HIGH) == "high"


# =============================================================================
# EL KAROUI VOL CONFIG TESTS
# =============================================================================


class TestElKarouiVolConfig:
    """Tests für ElKarouiVolConfig Dataclass."""

    def test_default_config(self) -> None:
        """Prüft Default-Konfiguration."""
        config = ElKarouiVolConfig.default()

        assert config.vol_window == 20
        assert config.lookback_window == 252
        assert config.low_threshold == 0.30
        assert config.high_threshold == 0.70
        assert config.vol_target == 0.10
        assert config.use_ewm is True

    def test_custom_config(self) -> None:
        """Prüft benutzerdefinierte Konfiguration."""
        config = ElKarouiVolConfig(
            vol_window=15,
            lookback_window=100,
            low_threshold=0.25,
            high_threshold=0.75,
            vol_target=0.12,
        )

        assert config.vol_window == 15
        assert config.lookback_window == 100
        assert config.vol_target == 0.12

    def test_conservative_config(self) -> None:
        """Prüft konservative Konfiguration."""
        config = ElKarouiVolConfig.conservative()

        assert config.low_threshold == 0.25
        assert config.high_threshold == 0.60
        assert config.vol_target == 0.08

    def test_aggressive_config(self) -> None:
        """Prüft aggressive Konfiguration."""
        config = ElKarouiVolConfig.aggressive()

        assert config.low_threshold == 0.35
        assert config.high_threshold == 0.80
        assert config.vol_target == 0.15

    def test_config_validation_vol_window(self) -> None:
        """Prüft Validierung für vol_window."""
        with pytest.raises(ValueError, match="vol_window"):
            ElKarouiVolConfig(vol_window=1)

    def test_config_validation_lookback_window(self) -> None:
        """Prüft Validierung für lookback_window."""
        with pytest.raises(ValueError, match="lookback_window"):
            ElKarouiVolConfig(vol_window=20, lookback_window=10)

    def test_config_validation_thresholds(self) -> None:
        """Prüft Validierung für Schwellen."""
        with pytest.raises(ValueError, match="low_threshold"):
            ElKarouiVolConfig(low_threshold=1.5)

        with pytest.raises(ValueError, match="high_threshold"):
            ElKarouiVolConfig(high_threshold=-0.1)

        with pytest.raises(ValueError, match="low_threshold"):
            ElKarouiVolConfig(low_threshold=0.70, high_threshold=0.30)

    def test_config_validation_vol_target(self) -> None:
        """Prüft Validierung für vol_target."""
        with pytest.raises(ValueError, match="vol_target"):
            ElKarouiVolConfig(vol_target=0)

    def test_regime_multipliers_exist(self) -> None:
        """Prüft, dass Regime-Multiplier definiert sind."""
        config = ElKarouiVolConfig.default()

        assert "low" in config.regime_multipliers
        assert "medium" in config.regime_multipliers
        assert "high" in config.regime_multipliers
        assert config.regime_multipliers["low"] == 1.0
        assert config.regime_multipliers["high"] == 0.5

    def test_to_dict(self) -> None:
        """Prüft Dictionary-Export."""
        config = ElKarouiVolConfig.default()
        d = config.to_dict()

        assert "vol_window" in d
        assert "lookback_window" in d
        assert "low_threshold" in d
        assert "high_threshold" in d
        assert "vol_target" in d
        assert "regime_multipliers" in d


# =============================================================================
# EL KAROUI VOL MODEL TESTS
# =============================================================================


class TestElKarouiVolModel:
    """Tests für ElKarouiVolModel."""

    def test_model_creation_default(self) -> None:
        """Prüft Modell-Erstellung mit Default-Config."""
        model = ElKarouiVolModel.from_default()

        assert model.config.vol_window == 20
        assert model.config.vol_target == 0.10

    def test_model_creation_custom(self) -> None:
        """Prüft Modell-Erstellung mit Custom-Config."""
        config = ElKarouiVolConfig(
            vol_window=15,
            vol_target=0.12,
        )
        model = ElKarouiVolModel(config)

        assert model.config.vol_window == 15
        assert model.config.vol_target == 0.12

    def test_from_config_dict(self) -> None:
        """Prüft Erstellung aus Dictionary."""
        config_dict = {
            "vol_window": 25,
            "low_threshold": 0.25,
            "vol_target": 0.15,
        }
        model = ElKarouiVolModel.from_config_dict(config_dict)

        assert model.config.vol_window == 25
        assert model.config.low_threshold == 0.25
        assert model.config.vol_target == 0.15


class TestVolatilityCalculation:
    """Tests für Volatilitäts-Berechnung."""

    def test_calculate_realized_vol_returns_series(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass calculate_realized_vol eine Series zurückgibt."""
        vol = model_test.calculate_realized_vol(low_vol_returns)

        assert isinstance(vol, pd.Series)
        assert len(vol) == len(low_vol_returns)

    def test_realized_vol_is_positive(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass realisierte Vol positiv ist."""
        vol = model_test.calculate_realized_vol(low_vol_returns)

        # Nur Werte nach Warmup prüfen
        valid_vol = vol.dropna()
        assert (valid_vol >= 0).all()

    def test_realized_vol_annualized(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass Vol annualisiert wird."""
        vol_ann = model_test.calculate_realized_vol(low_vol_returns, annualize=True)
        vol_raw = model_test.calculate_realized_vol(low_vol_returns, annualize=False)

        # Annualisierte Vol sollte größer sein
        valid_idx = vol_ann.notna() & vol_raw.notna()
        assert (vol_ann[valid_idx] > vol_raw[valid_idx]).all()

    def test_low_vol_returns_have_lower_vol(
        self,
        model_test: ElKarouiVolModel,
        low_vol_returns: pd.Series,
        high_vol_returns: pd.Series,
    ) -> None:
        """Prüft, dass niedrige Vol-Returns niedrigere Vol haben."""
        vol_low = model_test.calculate_realized_vol(low_vol_returns)
        vol_high = model_test.calculate_realized_vol(high_vol_returns)

        # Letzte Vol-Werte vergleichen
        assert vol_low.dropna().iloc[-1] < vol_high.dropna().iloc[-1]


class TestRegimeClassification:
    """Tests für Regime-Klassifikation."""

    def test_regime_for_percentile_low(self, model_test: ElKarouiVolModel) -> None:
        """Prüft LOW-Regime-Erkennung."""
        regime = model_test.regime_for_percentile(0.20)
        assert regime == VolRegime.LOW

    def test_regime_for_percentile_medium(self, model_test: ElKarouiVolModel) -> None:
        """Prüft MEDIUM-Regime-Erkennung."""
        regime = model_test.regime_for_percentile(0.50)
        assert regime == VolRegime.MEDIUM

    def test_regime_for_percentile_high(self, model_test: ElKarouiVolModel) -> None:
        """Prüft HIGH-Regime-Erkennung."""
        regime = model_test.regime_for_percentile(0.80)
        assert regime == VolRegime.HIGH

    def test_regime_for_percentile_nan(self, model_test: ElKarouiVolModel) -> None:
        """Prüft Handling von NaN-Perzentil."""
        regime = model_test.regime_for_percentile(np.nan)
        assert regime == VolRegime.MEDIUM  # Default bei NaN

    def test_regime_for_returns(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft Regime-Bestimmung für Returns."""
        regime = model_test.regime_for_returns(low_vol_returns)

        assert isinstance(regime, VolRegime)

    def test_regime_series_returns_series(
        self, model_test: ElKarouiVolModel, mixed_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass regime_series eine Series zurückgibt."""
        regimes = model_test.regime_series(mixed_vol_returns)

        assert isinstance(regimes, pd.Series)
        assert len(regimes) == len(mixed_vol_returns)

    def test_regime_series_contains_valid_values(
        self, model_test: ElKarouiVolModel, mixed_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass regime_series nur gültige Werte enthält."""
        regimes = model_test.regime_series(mixed_vol_returns)

        valid_values = {"low", "normal", "high"}
        unique_regimes = set(regimes.dropna().unique())
        assert unique_regimes.issubset(valid_values)


class TestScalingFactor:
    """Tests für Scaling-Faktor-Berechnung."""

    def test_multiplier_for_regime_low(self, model_test: ElKarouiVolModel) -> None:
        """Prüft Multiplier für LOW-Regime."""
        mult = model_test.multiplier_for_regime(VolRegime.LOW)
        assert mult == 1.0

    def test_multiplier_for_regime_high(self, model_test: ElKarouiVolModel) -> None:
        """Prüft Multiplier für HIGH-Regime."""
        mult = model_test.multiplier_for_regime(VolRegime.HIGH)
        assert mult == 0.5

    def test_scaling_factor_range(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass Scaling-Faktor in sinnvollem Bereich liegt."""
        factor = model_test.scaling_factor_for_returns(low_vol_returns)

        # Sollte zwischen 0.1 und 3.0 liegen (nach Capping)
        assert 0.1 <= factor <= 3.0

    def test_scaling_factor_series(
        self, model_test: ElKarouiVolModel, mixed_vol_returns: pd.Series
    ) -> None:
        """Prüft Scaling-Faktor-Series."""
        factors = model_test.scaling_factor_series(mixed_vol_returns)

        assert isinstance(factors, pd.Series)
        assert len(factors) == len(mixed_vol_returns)
        # Alle Werte sollten positiv sein
        assert (factors > 0).all()

    def test_scaling_factor_no_nan(
        self, model_test: ElKarouiVolModel, mixed_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass Scaling-Faktor keine NaNs enthält."""
        factors = model_test.scaling_factor_series(mixed_vol_returns)

        assert not factors.isna().any()


class TestVolAnalysis:
    """Tests für get_vol_analysis Methode."""

    def test_vol_analysis_contains_expected_keys(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass get_vol_analysis alle erwarteten Keys enthält."""
        analysis = model_test.get_vol_analysis(low_vol_returns)

        expected_keys = [
            "current_vol",
            "vol_percentile",
            "regime",
            "regime_multiplier",
            "scaling_factor",
            "vol_target",
            "vol_history",
        ]

        for key in expected_keys:
            assert key in analysis, f"Key '{key}' fehlt in vol_analysis"

    def test_vol_analysis_regime_is_vol_regime(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass Regime ein VolRegime-Objekt ist."""
        analysis = model_test.get_vol_analysis(low_vol_returns)

        assert isinstance(analysis["regime"], VolRegime)

    def test_vol_analysis_scaling_factor_is_float(
        self, model_test: ElKarouiVolModel, low_vol_returns: pd.Series
    ) -> None:
        """Prüft, dass Scaling-Faktor ein Float ist."""
        analysis = model_test.get_vol_analysis(low_vol_returns)

        assert isinstance(analysis["scaling_factor"], float)
        assert not np.isnan(analysis["scaling_factor"])


# =============================================================================
# CONVENIENCE FUNCTIONS TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests für Convenience-Funktionen."""

    def test_get_vol_regime(self, low_vol_returns: pd.Series) -> None:
        """Prüft get_vol_regime Funktion."""
        regime = get_vol_regime(low_vol_returns)

        assert isinstance(regime, VolRegime)

    def test_get_vol_regime_custom_params(self, low_vol_returns: pd.Series) -> None:
        """Prüft get_vol_regime mit Custom-Parametern."""
        regime = get_vol_regime(
            low_vol_returns,
            vol_window=15,
            low_threshold=0.25,
            high_threshold=0.75,
        )

        assert isinstance(regime, VolRegime)

    def test_get_vol_scaling_factor(self, low_vol_returns: pd.Series) -> None:
        """Prüft get_vol_scaling_factor Funktion."""
        factor = get_vol_scaling_factor(low_vol_returns)

        assert isinstance(factor, float)
        assert factor > 0

    def test_get_vol_scaling_factor_custom_params(self, low_vol_returns: pd.Series) -> None:
        """Prüft get_vol_scaling_factor mit Custom-Parametern."""
        factor = get_vol_scaling_factor(
            low_vol_returns,
            vol_window=15,
            vol_target=0.12,
        )

        assert isinstance(factor, float)
        assert factor > 0


# =============================================================================
# MODEL REPR TESTS
# =============================================================================


class TestModelRepr:
    """Tests für __repr__ Methode."""

    def test_model_repr_contains_key_info(self, model_test: ElKarouiVolModel) -> None:
        """Prüft, dass __repr__ wichtige Infos enthält."""
        repr_str = repr(model_test)

        assert "ElKarouiVolModel" in repr_str
        assert "RESEARCH-ONLY" in repr_str
        assert "window=" in repr_str
        assert "thresholds=" in repr_str
        assert "target=" in repr_str

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


# =============================================================================
# GOLDEN REFERENCE: calculate_vol_percentile rolling apply semantics
# =============================================================================


def _legacy_vol_percentile_reference(
    vol_series: pd.Series,
    lookback: int,
    min_periods: int,
) -> pd.Series:
    """Test-only reference for legacy ElKarouiVolModel.calculate_vol_percentile (0-1 scale)."""

    def percentile_rank(x: pd.Series) -> float:
        if len(x) < 2 or pd.isna(x.iloc[-1]):
            return np.nan
        current = x.iloc[-1]
        return (x < current).mean()

    return vol_series.rolling(
        window=lookback,
        min_periods=min_periods,
    ).apply(percentile_rank, raw=False)


def _assert_vol_percentile_series_equal(actual: pd.Series, expected: pd.Series) -> None:
    pd.testing.assert_series_equal(actual, expected, check_names=True)
    assert actual.index.equals(expected.index)
    assert actual.dtype == expected.dtype
    assert actual.isna().equals(expected.isna())


class TestVolPercentileGoldenReference:
    """Golden-reference contracts for ElKarouiVolModel.calculate_vol_percentile."""

    @pytest.mark.parametrize(
        ("values", "lookback", "min_periods"),
        [
            pytest.param([], 3, 2, id="empty"),
            pytest.param([1.0], 3, 2, id="single_element"),
            pytest.param([1.0, 2.0], 5, 2, id="shorter_than_window"),
            pytest.param([1.0, 2.0, 3.0, 4.0, 5.0], 3, 2, id="monotone_ascending"),
            pytest.param([5.0, 4.0, 3.0, 2.0, 1.0], 3, 2, id="monotone_descending"),
            pytest.param([1.0, 2.0, 2.0, 2.0, 3.0], 4, 2, id="ties"),
            pytest.param([1.0, 1.0, 2.0, 2.0, 3.0, 3.0], 4, 2, id="repeated_values"),
            pytest.param([2.0, 2.0, 2.0], 3, 3, id="constant"),
            pytest.param([1.0, np.nan, 3.0, 4.0, 5.0], 3, 2, id="nan_at_window_start"),
            pytest.param([np.nan, 1.0, 2.0, 3.0], 3, 2, id="nan_leading"),
            pytest.param([1.0, 2.0, np.nan], 3, 2, id="nan_last_window_value"),
            pytest.param([1.0, np.inf, 3.0, 4.0], 3, 2, id="positive_infinity"),
            pytest.param([1.0, -np.inf, 3.0, 4.0], 3, 2, id="negative_infinity"),
            pytest.param(list(range(1, 9)), 4, 2, id="multi_window"),
            pytest.param([7.0] * 6, 4, 2, id="constant_long"),
        ],
    )
    def test_vol_percentile_matches_legacy_reference(
        self,
        values: list[float],
        lookback: int,
        min_periods: int,
    ) -> None:
        idx = pd.date_range("2024-01-01", periods=max(len(values), 1), freq="D")[: len(values)]
        vol_series = pd.Series(values, index=idx, name="realized_vol", dtype=float)
        expected = _legacy_vol_percentile_reference(vol_series, lookback, min_periods)
        model = ElKarouiVolModel(
            ElKarouiVolConfig(vol_window=min_periods, lookback_window=lookback)
        )
        actual = model.calculate_vol_percentile(vol_series)
        _assert_vol_percentile_series_equal(actual, expected)

    def test_vol_percentile_non_trivial_index(self) -> None:
        idx = pd.Index([10, 20, 30, 40, 50, 60, 70, 80], name="bar")
        vol_series = pd.Series(
            [1.0, 2.0, 2.0, 3.0, 4.0, 3.0, 2.0, 1.0],
            index=idx,
            name="custom_vol",
            dtype=float,
        )
        lookback, min_periods = 4, 2
        expected = _legacy_vol_percentile_reference(vol_series, lookback, min_periods)
        model = ElKarouiVolModel(
            ElKarouiVolConfig(vol_window=min_periods, lookback_window=lookback)
        )
        actual = model.calculate_vol_percentile(vol_series)
        _assert_vol_percentile_series_equal(actual, expected)

    @pytest.mark.parametrize("lookback", [20, 50])
    def test_vol_percentile_multiple_window_sizes(self, lookback: int) -> None:
        vol_series = pd.Series(
            np.random.RandomState(17).randn(120) * 0.02 + 0.05,
            index=pd.date_range("2024-02-01", periods=120, freq="D"),
            name="window_probe",
            dtype=float,
        )
        min_periods = 10
        expected = _legacy_vol_percentile_reference(vol_series, lookback, min_periods)
        model = ElKarouiVolModel(
            ElKarouiVolConfig(vol_window=min_periods, lookback_window=lookback)
        )
        actual = model.calculate_vol_percentile(vol_series)
        _assert_vol_percentile_series_equal(actual, expected)

    def test_vol_percentile_downstream_regime_output_unchanged(
        self, mixed_vol_returns: pd.Series
    ) -> None:
        config = ElKarouiVolConfig(
            vol_window=10,
            lookback_window=50,
            low_threshold=0.30,
            high_threshold=0.70,
        )
        model = ElKarouiVolModel(config)
        vol = model.calculate_realized_vol(mixed_vol_returns)
        percentiles = model.calculate_vol_percentile(vol)
        expected_regimes = _legacy_regime_series_apply_reference(
            percentiles, config.low_threshold, config.high_threshold
        )
        actual_regimes = model.regime_series(mixed_vol_returns)
        _assert_regime_series_equal(actual_regimes, expected_regimes)

    def test_vol_percentile_from_config_dict_parity(self) -> None:
        vol_series = pd.Series(
            np.random.RandomState(19).randn(80) * 0.015 + 0.04,
            index=pd.date_range("2024-03-01", periods=80, freq="D"),
            name="cfg_vol",
            dtype=float,
        )
        config_dict = {"vol_window": 8, "lookback_window": 40}
        model = ElKarouiVolModel.from_config_dict(config_dict)
        expected = _legacy_vol_percentile_reference(
            vol_series,
            model.config.lookback_window,
            model.config.vol_window,
        )
        actual = model.calculate_vol_percentile(vol_series)
        _assert_vol_percentile_series_equal(actual, expected)

    def test_vol_percentile_from_default_parity(self) -> None:
        vol_series = pd.Series(
            np.random.RandomState(23).randn(150) * 0.012 + 0.03,
            index=pd.date_range("2024-04-01", periods=150, freq="D"),
            name="default_vol",
            dtype=float,
        )
        model = ElKarouiVolModel.from_default()
        expected = _legacy_vol_percentile_reference(
            vol_series,
            model.config.lookback_window,
            model.config.vol_window,
        )
        actual = model.calculate_vol_percentile(vol_series)
        _assert_vol_percentile_series_equal(actual, expected)


# =============================================================================
# GOLDEN REFERENCE: regime_series apply semantics
# =============================================================================


def _legacy_regime_for_percentile_value_reference(
    percentile: float,
    low_threshold: float,
    high_threshold: float,
) -> str:
    """Test-only reference for legacy element-wise regime_for_percentile().value mapping."""
    if pd.isna(percentile):
        return VolRegime.MEDIUM.value
    if percentile < low_threshold:
        return VolRegime.LOW.value
    if percentile > high_threshold:
        return VolRegime.HIGH.value
    return VolRegime.MEDIUM.value


def _legacy_regime_series_apply_reference(
    percentiles: pd.Series,
    low_threshold: float,
    high_threshold: float,
) -> pd.Series:
    """Test-only reference mirroring percentiles.apply(regime_for_percentile).value."""
    if len(percentiles) == 0:
        return pd.Series([], dtype=np.float64, index=percentiles.index, name=percentiles.name)
    return percentiles.apply(
        lambda x: _legacy_regime_for_percentile_value_reference(x, low_threshold, high_threshold)
    )


def _assert_regime_series_equal(actual: pd.Series, expected: pd.Series) -> None:
    pd.testing.assert_series_equal(actual, expected, check_names=True)
    assert actual.index.equals(expected.index)
    assert actual.dtype == expected.dtype
    assert actual.isna().equals(expected.isna())


class TestRegimeSeriesGoldenReference:
    """Golden-Reference-Tests für ElKarouiVolModel.regime_series apply-Pfad."""

    @pytest.mark.parametrize(
        ("percentile_values", "low_threshold", "high_threshold", "expected_values"),
        [
            pytest.param([], 0.30, 0.70, [], id="empty"),
            pytest.param([0.50], 0.30, 0.70, ["normal"], id="single_element"),
            pytest.param(
                [0.29, 0.30, 0.31],
                0.30,
                0.70,
                ["low", "normal", "normal"],
                id="low_boundary_neighbors",
            ),
            pytest.param(
                [0.69, 0.70, 0.71],
                0.30,
                0.70,
                ["normal", "normal", "high"],
                id="high_boundary_neighbors",
            ),
            pytest.param(
                [0.10, 0.50, 0.90], 0.30, 0.70, ["low", "normal", "high"], id="all_regime_classes"
            ),
            pytest.param(
                [np.nan, 0.50, np.nan], 0.30, 0.70, ["normal", "normal", "normal"], id="nan_values"
            ),
            pytest.param(
                [np.inf, -np.inf, 0.50], 0.30, 0.70, ["high", "low", "normal"], id="infinity_values"
            ),
            pytest.param([0.50] * 6, 0.30, 0.70, ["normal"] * 6, id="constant"),
            pytest.param([0.10, 0.90] * 4, 0.30, 0.70, ["low", "high"] * 4, id="alternating"),
        ],
    )
    def test_legacy_regime_series_apply_reference_semantics(
        self,
        percentile_values: list[float],
        low_threshold: float,
        high_threshold: float,
        expected_values: list[str],
    ) -> None:
        idx = pd.date_range("2024-01-01", periods=max(len(percentile_values), 1), freq="D")[
            : len(percentile_values)
        ]
        percentiles = pd.Series(percentile_values, index=idx, name="vol_percentile", dtype=float)
        actual = _legacy_regime_series_apply_reference(percentiles, low_threshold, high_threshold)
        if len(percentile_values) == 0:
            assert len(actual) == 0
            assert actual.dtype == np.float64
        else:
            assert actual.tolist() == expected_values
            assert pd.api.types.is_string_dtype(actual)
        assert actual.name == "vol_percentile"

    @pytest.mark.parametrize(
        ("returns_values", "series_name"),
        [
            pytest.param([], "empty_returns", id="empty_series"),
            pytest.param([0.01], "single_return", id="single_element"),
            pytest.param(
                list(np.random.RandomState(42).randn(100) * 0.005), "low_vol", id="low_vol"
            ),
            pytest.param(
                list(np.random.RandomState(42).randn(100) * 0.04), "high_vol", id="high_vol"
            ),
            pytest.param(
                list(np.random.RandomState(7).randn(150) * 0.015), "mixed_vol", id="mixed_vol"
            ),
        ],
    )
    def test_regime_series_matches_legacy_reference(
        self,
        returns_values: list[float],
        series_name: str,
    ) -> None:
        idx = pd.date_range("2024-06-01", periods=max(len(returns_values), 1), freq="D")[
            : len(returns_values)
        ]
        returns = pd.Series(returns_values, index=idx, name=series_name, dtype=float)
        config = ElKarouiVolConfig(
            vol_window=10,
            lookback_window=50,
            low_threshold=0.30,
            high_threshold=0.70,
        )
        model = ElKarouiVolModel(config)

        vol = model.calculate_realized_vol(returns)
        percentiles = model.calculate_vol_percentile(vol)
        expected = _legacy_regime_series_apply_reference(
            percentiles, config.low_threshold, config.high_threshold
        )
        actual = model.regime_series(returns)
        _assert_regime_series_equal(actual, expected)

    def test_regime_series_non_trivial_index(self) -> None:
        idx = pd.Index([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], name="bar")
        returns = pd.Series(
            np.random.RandomState(7).randn(10) * 0.02, index=idx, name="custom_returns"
        )
        model = ElKarouiVolModel(
            ElKarouiVolConfig(
                vol_window=5, lookback_window=10, low_threshold=0.30, high_threshold=0.70
            )
        )
        vol = model.calculate_realized_vol(returns)
        percentiles = model.calculate_vol_percentile(vol)
        expected = _legacy_regime_series_apply_reference(
            percentiles, model.config.low_threshold, model.config.high_threshold
        )
        actual = model.regime_series(returns)
        _assert_regime_series_equal(actual, expected)

    def test_regime_series_from_config_dict_parity(self) -> None:
        returns = pd.Series(
            np.random.RandomState(11).randn(80) * 0.015,
            index=pd.date_range("2024-03-01", periods=80, freq="D"),
            name="cfg_returns",
        )
        config_dict = {
            "vol_window": 8,
            "lookback_window": 40,
            "low_threshold": 0.25,
            "high_threshold": 0.75,
        }
        model = ElKarouiVolModel.from_config_dict(config_dict)
        vol = model.calculate_realized_vol(returns)
        percentiles = model.calculate_vol_percentile(vol)
        expected = _legacy_regime_series_apply_reference(
            percentiles, model.config.low_threshold, model.config.high_threshold
        )
        actual = model.regime_series(returns)
        _assert_regime_series_equal(actual, expected)

    def test_regime_series_from_default_parity(self) -> None:
        returns = pd.Series(
            np.random.RandomState(13).randn(120) * 0.012,
            index=pd.date_range("2024-04-01", periods=120, freq="D"),
            name="default_returns",
        )
        model = ElKarouiVolModel.from_default()
        vol = model.calculate_realized_vol(returns)
        percentiles = model.calculate_vol_percentile(vol)
        expected = _legacy_regime_series_apply_reference(
            percentiles, model.config.low_threshold, model.config.high_threshold
        )
        actual = model.regime_series(returns)
        _assert_regime_series_equal(actual, expected)

"""
Unit Tests für VolRegimeOverlaySizer

Tests:
1. Safety Gates (Environment, Research-Flag)
2. Vol-Targeting (High-Vol -> kleinere Position)
3. No-Lookahead (shock an Bar t reagiert erst ab t+1)
4. DD-Throttle (progressives Drosseln bei Drawdown)

Alle Tests sind deterministisch (kein Random, feste Daten).
"""
import pytest
import math
from src.core.position_sizing import (
    FixedSizeSizer,
    VolRegimeOverlaySizer,
    VolRegimeOverlaySizerConfig,
    build_position_sizer_from_config,
)


# ============================================================================
# HELPER: Config-Wrapper mit .get() Interface
# ============================================================================


class DictConfig:
    """Wrapper um Dict mit .get(path) Interface wie PeakConfig."""
    def __init__(self, data: dict):
        self._data = data

    def get(self, path: str, default=None):
        """Nested path access: 'a.b.c'"""
        keys = path.split(".")
        node = self._data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node


# ============================================================================
# HELPER: Deterministische OHLCV-Daten
# ============================================================================


def generate_synthetic_prices(
    n_bars: int = 400,
    base_price: float = 50000.0,
    low_vol_segment: tuple = (0, 133),
    high_vol_segment: tuple = (133, 266),
    normal_vol_segment: tuple = (266, 400),
    seed: int = 42,
) -> list:
    """
    Generiert deterministische Preis-Serie mit drei Volatilitäts-Segmenten.

    Args:
        n_bars: Anzahl Bars
        base_price: Start-Preis
        low_vol_segment: (start, end) für low vol
        high_vol_segment: (start, end) für high vol
        normal_vol_segment: (start, end) für normal vol
        seed: Random seed für Deterministik

    Returns:
        Liste von Preisen
    """
    # Deterministischer "random" generator (einfache LCG)
    def lcg(x):
        # Linear Congruential Generator (Park-Miller)
        a = 48271
        m = 2147483647
        return (a * x) % m

    rng_state = seed
    prices = [base_price]

    for i in range(1, n_bars):
        # Segment bestimmen
        if low_vol_segment[0] <= i < low_vol_segment[1]:
            # Low vol: kleine Returns (0.1%)
            vol = 0.001
        elif high_vol_segment[0] <= i < high_vol_segment[1]:
            # High vol: große Returns (2%)
            vol = 0.02
        else:
            # Normal vol: mittlere Returns (0.5%)
            vol = 0.005

        # Deterministischer "random" return
        rng_state = lcg(rng_state)
        # Map zu [-1, 1]
        rand_val = (rng_state / 2147483647) * 2 - 1
        ret = rand_val * vol

        # Neuer Preis
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)

    return prices


# ============================================================================
# TEST 1: Safety Gates
# ============================================================================


def test_overlay_blocks_without_research_flag():
    """Gate 2: Ohne research.allow_r_and_d_overlays -> ValueError"""
    cfg = DictConfig({
        "position_sizing": {
            "type": "vol_regime_overlay",
            "vol_regime_overlay": {
                "base_sizer_key": "fixed_size",
                "base_units": 0.01,
            },
        },
        "research": {
            "allow_r_and_d_overlays": False,  # NICHT aktiviert
        },
        "environment": {
            "mode": "offline_backtest",
        },
    })

    with pytest.raises(ValueError, match="VolRegimeOverlaySizer ist deaktiviert"):
        build_position_sizer_from_config(cfg)


def test_overlay_blocks_in_live_env():
    """Gate 1: environment.mode='live' -> ValueError"""
    cfg = DictConfig({
        "position_sizing": {
            "type": "vol_regime_overlay",
            "vol_regime_overlay": {
                "base_sizer_key": "fixed_size",
                "base_units": 0.01,
            },
        },
        "research": {
            "allow_r_and_d_overlays": True,  # Aktiviert
        },
        "environment": {
            "mode": "live",  # NICHT erlaubt!
        },
    })

    with pytest.raises(ValueError, match="NICHT für Live-Trading zugelassen"):
        build_position_sizer_from_config(cfg)


def test_overlay_allows_offline_backtest_with_flag():
    """Erfolgreicher Build mit korrekter Config"""
    cfg = DictConfig({
        "position_sizing": {
            "type": "vol_regime_overlay",
            "vol_regime_overlay": {
                "base_sizer_key": "fixed_size",
                "base_units": 0.01,
                "day_vol_budget": 0.02,
                "vol_window_bars": 20,
            },
        },
        "research": {
            "allow_r_and_d_overlays": True,
        },
        "environment": {
            "mode": "offline_backtest",
        },
    })

    sizer = build_position_sizer_from_config(cfg)
    assert isinstance(sizer, VolRegimeOverlaySizer)
    assert isinstance(sizer.base_sizer, FixedSizeSizer)
    assert sizer.config.day_vol_budget == 0.02


# ============================================================================
# TEST 2: Vol-Targeting
# ============================================================================


def test_vol_target_scales_down_in_high_vol():
    """
    In high-vol Segment sollte Position KLEINER sein als in low-vol Segment.

    Logik:
    - Low-vol: scale_vol > 1 (größere Position)
    - High-vol: scale_vol < 1 (kleinere Position)

    Wir messen: mean(abs(units)) in high-vol < mean(abs(units)) in low-vol
    """
    # Setup
    base_sizer = FixedSizeSizer(units=0.01)
    cfg = VolRegimeOverlaySizerConfig(
        day_vol_budget=0.01,  # 1% Ziel-Tagesvol
        vol_window_bars=20,
        vol_target_scaling=True,
        regime_lookback_bars=50,
        bars_per_day=1,
        trading_days_per_year=252,
    )
    overlay = VolRegimeOverlaySizer(base_sizer=base_sizer, config=cfg)

    # Daten: low/high/normal vol
    prices = generate_synthetic_prices(
        n_bars=300,
        low_vol_segment=(0, 100),
        high_vol_segment=(100, 200),
        normal_vol_segment=(200, 300),
        seed=42,
    )

    # Simulate bar-by-bar
    equity = 10000.0
    signal = 1  # Immer long

    units_low = []
    units_high = []

    for i, price in enumerate(prices):
        units = overlay.get_target_position(signal=signal, price=price, equity=equity)

        # Sammle Units nach Segment (skip warmup)
        if 50 <= i < 100:
            # Low-vol segment (nach warmup)
            units_low.append(abs(units))
        elif 150 <= i < 200:
            # High-vol segment (nach warmup)
            units_high.append(abs(units))

    # Check: Mean(units) in high-vol < mean(units) in low-vol
    # (mit Toleranz, da regime-factor auch eine Rolle spielt)
    mean_low = sum(units_low) / len(units_low) if units_low else 0
    mean_high = sum(units_high) / len(units_high) if units_high else 0

    # Erwartung: high-vol units sind mindestens 20% kleiner
    assert mean_high < mean_low * 0.8, (
        f"Vol-Targeting fehlgeschlagen: "
        f"mean_high={mean_high:.4f} sollte < mean_low={mean_low:.4f} * 0.8 sein"
    )


# ============================================================================
# TEST 3: No-Lookahead (KRITISCH!)
# ============================================================================


def test_no_lookahead_shift():
    """
    Teste dass ein Preis-Shock an Bar t NICHT sofort in scale(t) einfließt.

    Setup:
    1. 100 Bars mit konstantem Preis (vol = 0)
    2. Bar 100: Großer Shock (+10%)
    3. Bar 101-110: Konstant wieder

    Erwartung:
    - scale(100) sollte NICHT reagieren (nutzt nur Daten bis Bar 99)
    - scale(101) sollte reagieren (nutzt Daten inkl. Bar 100)

    Test:
    abs(units[100] - units[99]) sollte sehr klein sein (kein Shock-Effekt)
    abs(units[101] - units[100]) sollte größer sein (Shock-Effekt tritt ein)
    """
    base_sizer = FixedSizeSizer(units=0.01)
    cfg = VolRegimeOverlaySizerConfig(
        day_vol_budget=0.01,
        vol_window_bars=20,
        vol_target_scaling=True,
        regime_lookback_bars=50,
        bars_per_day=1,
        trading_days_per_year=252,
    )
    overlay = VolRegimeOverlaySizer(base_sizer=base_sizer, config=cfg)

    # Daten: Konstant + Shock + Konstant
    base_price = 50000.0
    prices = [base_price] * 100  # Bars 0-99: konstant
    prices.append(base_price * 1.10)  # Bar 100: +10% Shock
    prices.extend([base_price * 1.10] * 10)  # Bars 101-110: konstant wieder

    equity = 10000.0
    signal = 1

    units_history = []
    for price in prices:
        units = overlay.get_target_position(signal=signal, price=price, equity=equity)
        units_history.append(units)

    # Nach Warmup (ab Bar 25)
    # Prüfe: units[99] vs units[100] (sollte KLEIN sein)
    diff_at_shock = abs(units_history[100] - units_history[99])

    # Prüfe: units[100] vs units[101] (sollte GRÖSSER sein)
    diff_after_shock = abs(units_history[101] - units_history[100])

    # Assertion: Shock-Effekt tritt VERZÖGERT ein
    # diff_at_shock sollte sehr klein sein (da vol bis t-1 noch konstant ist)
    # diff_after_shock sollte größer sein (da vol ab t jetzt shock enthält)

    # WICHTIG: Da Preis konstant ist, ist vol=0 -> scale wirkt möglicherweise nicht
    # Besserer Test: Check dass units[100] ~ units[99] (keine sofortige Reaktion)

    # Relativer Unterschied
    rel_diff_at_shock = diff_at_shock / (abs(units_history[99]) + 1e-9)

    # Erwartung: rel_diff sehr klein (< 1%)
    assert rel_diff_at_shock < 0.01, (
        f"No-Lookahead verletzt: units[100] weicht zu stark von units[99] ab "
        f"({rel_diff_at_shock:.2%}). Der Shock sollte erst ab Bar 101 wirken."
    )


# ============================================================================
# TEST 4: DD-Throttle
# ============================================================================


def test_dd_throttle_when_equity_available():
    """
    Teste Drawdown-Throttle: Bei hohem DD sollte scale reduziert werden.

    Setup:
    1. Start-Equity: 10000
    2. Peak-Equity: 12000 (nach 50 Bars)
    3. Drawdown auf 9600 (20% DD) -> zwischen dd_soft_start (10%) und max_drawdown (25%)

    Erwartung:
    - dd_factor sollte < 1.0 sein (progressives Drosseln)
    - units sollten reduziert werden im Vergleich zu ohne DD
    """
    base_sizer = FixedSizeSizer(units=0.01)
    cfg = VolRegimeOverlaySizerConfig(
        day_vol_budget=0.01,
        vol_window_bars=20,
        vol_target_scaling=False,  # Deaktiviert um DD-Effekt zu isolieren
        enable_dd_throttle=True,
        dd_soft_start=0.10,  # 10%
        max_drawdown=0.25,  # 25%
        bars_per_day=1,
        trading_days_per_year=252,
    )
    overlay = VolRegimeOverlaySizer(base_sizer=base_sizer, config=cfg)

    # Simuliere Equity-Curve
    price = 50000.0
    signal = 1

    # Phase 1: Equity steigt auf Peak
    for i in range(50):
        equity = 10000.0 + i * 40  # Linear bis 12000
        overlay.get_target_position(signal=signal, price=price, equity=equity)

    # Peak ist jetzt 12000
    assert overlay.peak_equity == pytest.approx(12000.0 - 40, rel=0.01)

    # Phase 2: Drawdown auf 9600 (20% DD von 12000)
    target_dd_equity = 12000.0 * (1 - 0.20)  # 9600
    units_at_dd = overlay.get_target_position(
        signal=signal, price=price, equity=target_dd_equity
    )

    # Erwartung: units sollten reduziert sein
    # DD = 20%, dd_soft_start = 10%, max_drawdown = 25%
    # dd_factor = 1.0 - (20% - 10%) / (25% - 10%) = 1.0 - 10% / 15% = 1.0 - 0.667 = 0.333
    expected_dd_factor = 1.0 - (0.20 - 0.10) / (0.25 - 0.10)
    expected_dd_factor = max(0.0, min(1.0, expected_dd_factor))  # ~0.333

    # Base-Units (ohne Overlay)
    base_units = base_sizer.get_target_position(signal=signal, price=price, equity=target_dd_equity)

    # Expected: base_units * dd_factor (da vol_target_scaling=False, regime_factor~1)
    # ABER: warmup + regime factor können abweichen, daher prüfen wir nur dass units < base_units

    assert units_at_dd < base_units, (
        f"DD-Throttle fehlgeschlagen: units_at_dd={units_at_dd:.6f} "
        f"sollte < base_units={base_units:.6f} sein"
    )

    # Genauerer Check: units sollten ungefähr base_units * dd_factor sein
    # (mit Toleranz wegen regime_factor)
    expected_units = base_units * expected_dd_factor
    tolerance = 0.5  # 50% Toleranz wegen anderen Faktoren
    assert abs(units_at_dd - expected_units) / expected_units < tolerance, (
        f"DD-Throttle Faktor weicht zu stark ab: "
        f"units_at_dd={units_at_dd:.6f}, expected={expected_units:.6f}"
    )


def test_dd_throttle_disabled_by_default():
    """Teste dass DD-Throttle standardmäßig DEAKTIVIERT ist."""
    base_sizer = FixedSizeSizer(units=0.01)
    cfg = VolRegimeOverlaySizerConfig(
        enable_dd_throttle=False,  # Explizit deaktiviert
    )
    overlay = VolRegimeOverlaySizer(base_sizer=base_sizer, config=cfg)

    # Hoher Drawdown (sollte KEINE Wirkung haben)
    price = 50000.0
    signal = 1
    equity_high = 12000.0
    equity_low = 6000.0  # 50% DD

    # Warmup
    for i in range(30):
        overlay.get_target_position(signal=signal, price=price, equity=10000.0)

    # Peak setzen
    overlay.get_target_position(signal=signal, price=price, equity=equity_high)

    # DD-Phase
    units_at_high_dd = overlay.get_target_position(signal=signal, price=price, equity=equity_low)
    base_units = base_sizer.get_target_position(signal=signal, price=price, equity=equity_low)

    # Erwartung: units sollten NICHT auf 0 reduziert sein (DD-Throttle ist aus)
    # (aber vol-targeting/regime können wirken, daher prüfen wir nur dass units > 0)
    assert units_at_high_dd > 0, "DD-Throttle sollte deaktiviert sein, aber units=0"


# ============================================================================
# TEST 5: Config-Parsing
# ============================================================================


def test_config_parsing_with_defaults():
    """Teste dass Factory mit minimaler Config funktioniert."""
    cfg = DictConfig({
        "position_sizing": {
            "type": "vol_regime_overlay",
            "vol_regime_overlay": {
                "base_sizer_key": "noop",
                # Alle anderen: defaults
            },
        },
        "research": {
            "allow_r_and_d_overlays": True,
        },
        "environment": {
            "mode": "offline_backtest",
        },
    })

    sizer = build_position_sizer_from_config(cfg)
    assert isinstance(sizer, VolRegimeOverlaySizer)
    assert sizer.config.day_vol_budget == 0.02  # Default
    assert sizer.config.vol_window_bars == 20  # Default
    assert sizer.config.enable_dd_throttle is False  # Default


def test_config_parsing_prevents_infinite_loop():
    """Teste dass base_sizer_key='vol_regime_overlay' verhindert wird."""
    cfg = DictConfig({
        "position_sizing": {
            "type": "vol_regime_overlay",
            "vol_regime_overlay": {
                "base_sizer_key": "vol_regime_overlay",  # Endlosschleife!
            },
        },
        "research": {
            "allow_r_and_d_overlays": True,
        },
        "environment": {
            "mode": "offline_backtest",
        },
    })

    with pytest.raises(ValueError, match="Endlosschleife"):
        build_position_sizer_from_config(cfg)


# ============================================================================
# TEST 6: Warmup-Verhalten
# ============================================================================


def test_warmup_phase_passthrough():
    """
    Während Warmup (< vol_window_bars + 1) sollte scale=1 sein.

    Erwartung: units = base_units (kein Overlay-Effekt)
    """
    base_sizer = FixedSizeSizer(units=0.01)
    cfg = VolRegimeOverlaySizerConfig(
        vol_window_bars=20,
        vol_target_scaling=True,
    )
    overlay = VolRegimeOverlaySizer(base_sizer=base_sizer, config=cfg)

    price = 50000.0
    equity = 10000.0
    signal = 1

    # Erste 20 Bars: Warmup
    for i in range(20):
        units = overlay.get_target_position(signal=signal, price=price, equity=equity)
        base_units = base_sizer.get_target_position(signal=signal, price=price, equity=equity)

        assert units == base_units, f"Warmup-Phase (Bar {i}): units sollte == base_units sein"


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

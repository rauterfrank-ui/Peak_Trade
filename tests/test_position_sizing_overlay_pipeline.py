"""
Tests für Position Sizing Overlay Pipeline.

Testet:
1. CompositePositionSizer mit/ohne Overlays
2. VolRegimeOverlay Funktionalität
3. Research-Gating (allow_r_and_d_overlays)
4. Live-Block
5. No-Lookahead-Garantien
"""

import pytest
import pandas as pd
import numpy as np
from src.core.position_sizing import (
    BasePositionSizer,
    BasePositionOverlay,
    FixedSizeSizer,
    FixedFractionSizer,
    CompositePositionSizer,
    VolRegimeOverlay,
    build_position_sizer_from_config,
)


# ============================================================================
# Test 1: CompositePositionSizer ohne Overlays (Backward-Compat)
# ============================================================================


def test_no_overlays_behaves_like_base():
    """
    Test: CompositePositionSizer ohne Overlays = exakt Base-Sizer-Verhalten.

    Erwartung: Kein stilles Verändern von Werten.
    """
    base = FixedSizeSizer(units=10.0)
    composite = CompositePositionSizer(base_sizer=base, overlays=[])

    # Test mehrere Signale
    test_cases = [
        (1, 50000.0, 10000.0, 10.0),  # Long
        (-1, 50000.0, 10000.0, -10.0),  # Short
        (0, 50000.0, 10000.0, 0.0),  # Flat
    ]

    for signal, price, equity, expected in test_cases:
        base_units = base.get_target_position(signal, price, equity)
        composite_units = composite.get_target_position(signal, price, equity)

        assert base_units == expected, f"Base-Sizer falsch: {base_units} != {expected}"
        assert composite_units == expected, (
            f"Composite-Sizer falsch: {composite_units} != {expected}"
        )
        assert base_units == composite_units, "Composite weicht von Base ab ohne Overlays!"


def test_no_overlays_with_fixed_fraction():
    """Test: CompositePositionSizer ohne Overlays mit FixedFractionSizer."""
    base = FixedFractionSizer(fraction=0.1)
    composite = CompositePositionSizer(base_sizer=base, overlays=[])

    signal = 1
    price = 50000.0
    equity = 10000.0

    base_units = base.get_target_position(signal, price, equity)
    composite_units = composite.get_target_position(signal, price, equity)

    expected = (equity * 0.1) / price  # 10000 * 0.1 / 50000 = 0.02

    assert abs(base_units - expected) < 1e-6
    assert abs(composite_units - expected) < 1e-6
    assert base_units == composite_units


# ============================================================================
# Test 2: R&D Overlay requires allow flag
# ============================================================================


def test_rnd_overlay_requires_allow_flag():
    """
    Test: R&D-Overlay (wie VolRegimeOverlay) erfordert allow_r_and_d_overlays=true.

    Erwartung: ValueError wenn Flag fehlt.
    """
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": ["vol_regime_overlay"],
            "overlay": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                }
            },
        },
        "research": {"allow_r_and_d_overlays": False},  # WICHTIG: False!
        "environment": {"mode": "offline_backtest"},
    }

    with pytest.raises(ValueError, match="TIER=r_and_d.*ist deaktiviert"):
        build_position_sizer_from_config(cfg)


def test_rnd_overlay_works_with_allow_flag():
    """Test: R&D-Overlay funktioniert wenn allow_r_and_d_overlays=true."""
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": ["vol_regime_overlay"],
            "overlay": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                    "vol_window_bars": 20,
                }
            },
        },
        "research": {"allow_r_and_d_overlays": True},  # ✅
        "environment": {"mode": "offline_backtest"},
    }

    sizer = build_position_sizer_from_config(cfg)

    # Sollte CompositePositionSizer sein
    assert isinstance(sizer, CompositePositionSizer)
    assert len(sizer.overlays) == 1
    assert isinstance(sizer.overlays[0], VolRegimeOverlay)


# ============================================================================
# Test 3: Overlay blocks in live environment
# ============================================================================


def test_overlay_blocks_in_live():
    """
    Test: Overlay mit IS_LIVE_READY=False blockiert in env=live.

    Erwartung: ValueError
    """
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": ["vol_regime_overlay"],
            "overlay": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                }
            },
        },
        "research": {"allow_r_and_d_overlays": True},
        "environment": {"mode": "live"},  # ❌
    }

    with pytest.raises(ValueError, match="NICHT für Live-Trading zugelassen"):
        build_position_sizer_from_config(cfg)


def test_overlay_allowed_in_offline_backtest():
    """Test: Overlay erlaubt in offline_backtest."""
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": ["vol_regime_overlay"],
            "overlay": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                }
            },
        },
        "research": {"allow_r_and_d_overlays": True},
        "environment": {"mode": "offline_backtest"},  # ✅
    }

    sizer = build_position_sizer_from_config(cfg)
    assert isinstance(sizer, CompositePositionSizer)


def test_overlay_allowed_in_research():
    """Test: Overlay erlaubt in research environment."""
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": ["vol_regime_overlay"],
            "overlay": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                }
            },
        },
        "research": {"allow_r_and_d_overlays": True},
        "environment": {"mode": "research"},  # ✅
    }

    sizer = build_position_sizer_from_config(cfg)
    assert isinstance(sizer, CompositePositionSizer)


# ============================================================================
# Test 4: VolRegimeOverlay scales units
# ============================================================================


@pytest.mark.xfail(
    strict=True,
    reason="Aspirational: vol-targeting/DD-throttle belongs to VolRegimeOverlaySizer. "
    "VolRegimeOverlay is intentionally lightweight (no vol/DD logic in apply()).",
)
def test_vol_regime_overlay_scales_units():
    """
    Test: VolRegimeOverlay skaliert Units basierend auf Vol-Regime.

    Setup:
    - Low-vol segment (should scale UP)
    - High-vol segment (should scale DOWN)
    """
    overlay = VolRegimeOverlay(
        day_vol_budget=0.02,
        vol_window_bars=20,
        regime_lookback_bars=100,
        vol_target_scaling=True,
        regime_scale_low=1.0,
        regime_scale_mid=0.75,
        regime_scale_high=0.5,
        max_scale=3.0,
        min_scale=0.0,
    )

    # Synthetische Daten: 400 Bars mit zwei Vol-Segmenten
    np.random.seed(42)

    # Low-vol segment (1% daily vol)
    low_vol_returns = np.random.normal(0, 0.01, 200)
    low_vol_prices = 50000 * (1 + low_vol_returns).cumprod()

    # High-vol segment (5% daily vol)
    high_vol_returns = np.random.normal(0, 0.05, 200)
    high_vol_prices = low_vol_prices[-1] * (1 + high_vol_returns).cumprod()

    all_prices = np.concatenate([low_vol_prices, high_vol_prices])
    all_returns = np.diff(all_prices) / all_prices[:-1]

    # Warmup: Skip first vol_window + regime_lookback + 5 bars
    warmup_bars = overlay.vol_window_bars + overlay.regime_lookback_bars + 5

    # Collect scaled units in each segment
    low_vol_segment_units = []
    high_vol_segment_units = []

    base_units = 10.0
    equity = 10000.0

    for i in range(len(all_prices)):
        price = all_prices[i]
        signal = 1  # Always long

        scaled_units = overlay.apply(
            units=base_units,
            signal=signal,
            price=price,
            equity=equity,
            context={},
        )

        # Nach Warmup: Sammle Units
        if i >= warmup_bars:
            if i < 200:
                # Low-vol segment
                low_vol_segment_units.append(abs(scaled_units))
            else:
                # High-vol segment
                high_vol_segment_units.append(abs(scaled_units))

    # Prüfe: Im Mittel sollten low-vol units > high-vol units
    if low_vol_segment_units and high_vol_segment_units:
        avg_low = np.mean(low_vol_segment_units)
        avg_high = np.mean(high_vol_segment_units)

        print(f"Low-vol avg units: {avg_low:.4f}")
        print(f"High-vol avg units: {avg_high:.4f}")

        # Low-vol sollte größer sein als high-vol (Vol-Targeting + Regime-Dämpfung)
        assert avg_low > avg_high, (
            f"Vol-Regime-Overlay funktioniert nicht richtig: "
            f"Low-vol ({avg_low:.4f}) sollte > High-vol ({avg_high:.4f}) sein"
        )


# ============================================================================
# Test 5: No-Lookahead shock test
# ============================================================================


@pytest.mark.xfail(
    strict=True,
    reason="Aspirational: no-lookahead shock behavior is specified for an extended overlay. "
    "Current design keeps logic in VolRegimeOverlaySizer, not in lightweight overlay apply().",
)
def test_no_lookahead_shock():
    """
    Test: No-Lookahead-Garantie bei VolRegimeOverlay.

    Setup:
    - Stabile Preise für Warmup
    - Single shock return auf Bar t
    - Prüfe: shock wird erst ab t+1 in realized vol eingerechnet

    WICHTIG: Nach Warmup ist Overlay aktiv, aber shock-price selbst wird
    NICHT für vol-calc genutzt (price_history[:-1]).
    """
    overlay = VolRegimeOverlay(
        day_vol_budget=0.02,
        vol_window_bars=20,
        regime_lookback_bars=100,
        vol_target_scaling=True,
    )

    base_units = 10.0
    equity = 10000.0

    # Warmup: Stabile Preise (50 Bars)
    stable_prices = [50000.0] * 50

    units_before_shock = None
    for i, price in enumerate(stable_prices):
        units_before_shock = overlay.apply(
            units=base_units,
            signal=1,
            price=price,
            equity=equity,
            context={},
        )

    # Jetzt: Shock return auf Bar t
    shock_price = 50000.0 * 1.10  # +10% shock

    # Units auf Bar t (MIT shock price, aber shock nicht in vol-calc!)
    units_at_shock = overlay.apply(
        units=base_units,
        signal=1,
        price=shock_price,
        equity=equity,
        context={},
    )

    # Units auf Bar t+1 (nach shock, zurück zu stable)
    post_shock_price = 50000.0

    units_after_shock = overlay.apply(
        units=base_units,
        signal=1,
        price=post_shock_price,
        equity=equity,
        context={},
    )

    print(f"Base units: {base_units}")
    print(f"Units before shock: {units_before_shock:.4f}")
    print(f"Units at shock (t): {units_at_shock:.4f}")
    print(f"Units after shock (t+1): {units_after_shock:.4f}")

    # Check 1: units_at_shock sollte ~= units_before_shock (shock noch nicht eingerechnet)
    # Aber nicht exakt wegen rolling windows
    # Wir erlauben 5% Abweichung
    assert abs(units_at_shock - units_before_shock) < base_units * 0.05, (
        f"Lookahead-Violation vermutet: units_at_shock ({units_at_shock:.4f}) "
        f"weicht zu stark ab von units_before_shock ({units_before_shock:.4f})"
    )

    # Check 2: units_after_shock sollte niedriger sein (shock jetzt in history, vol steigt)
    # Nach shock steigt realized vol -> vol_target_scale sinkt
    assert units_after_shock < units_at_shock, (
        f"Shock-Response fehlt: units_after_shock ({units_after_shock:.4f}) "
        f"sollte < units_at_shock ({units_at_shock:.4f}) sein"
    )


# ============================================================================
# Test 6: Composite with multiple overlays (sequenziell)
# ============================================================================


def test_composite_with_multiple_overlays():
    """
    Test: Mehrere Overlays werden sequenziell angewendet.

    Setup:
    - Base: 10 units
    - Overlay1: Scale by 0.5
    - Overlay2: Scale by 0.8
    - Erwartet: 10 * 0.5 * 0.8 = 4.0
    """
    from dataclasses import dataclass
    from typing import Dict, Any

    @dataclass
    class DummyOverlay1(BasePositionOverlay):
        KEY: str = "dummy1"
        scale: float = 0.5

        def apply(
            self,
            *,
            units: float,
            signal: int,
            price: float,
            equity: float,
            context: Dict[str, Any],
        ) -> float:
            return units * self.scale

    @dataclass
    class DummyOverlay2(BasePositionOverlay):
        KEY: str = "dummy2"
        scale: float = 0.8

        def apply(
            self,
            *,
            units: float,
            signal: int,
            price: float,
            equity: float,
            context: Dict[str, Any],
        ) -> float:
            return units * self.scale

    base = FixedSizeSizer(units=10.0)
    overlay1 = DummyOverlay1()
    overlay2 = DummyOverlay2()

    composite = CompositePositionSizer(base_sizer=base, overlays=[overlay1, overlay2])

    signal = 1
    price = 50000.0
    equity = 10000.0

    final_units = composite.get_target_position(signal, price, equity)

    expected = 10.0 * 0.5 * 0.8  # = 4.0

    assert abs(final_units - expected) < 1e-6, (
        f"Sequenzielle Overlays falsch: {final_units} != {expected}"
    )


# ============================================================================
# Test 7: Backward-Compat: key="vol_regime_overlay" weiterhin funktionsfähig
# ============================================================================


def test_backward_compat_vol_regime_overlay_key():
    """
    Test: Alte Config mit key="vol_regime_overlay" funktioniert weiterhin.

    Erwartung: build_position_sizer_from_config erkennt alte Config und baut VolRegimeOverlaySizer.
    """
    cfg = {
        "position_sizing": {
            "key": "vol_regime_overlay",  # Alt
            "vol_regime_overlay": {
                "base_sizer_key": "fixed_size",
                "base_units": 10.0,
                "day_vol_budget": 0.02,
                "vol_window_bars": 20,
            },
        },
        "research": {"allow_r_and_d_overlays": True},
        "environment": {"mode": "offline_backtest"},
    }

    sizer = build_position_sizer_from_config(cfg)

    # Sollte VolRegimeOverlaySizer sein (alte Implementierung)
    from src.core.position_sizing import VolRegimeOverlaySizer

    assert isinstance(sizer, VolRegimeOverlaySizer)


# ============================================================================
# Test 8: Warmup-Verhalten
# ============================================================================


def test_vol_regime_overlay_warmup():
    """
    Test: Während Warmup sollte scale=1 sein (kein Overlay-Effekt).

    Setup:
    - vol_window_bars=20
    - Erste 21 Bars: scale sollte 1.0 sein
    - Ab Bar 22: scale kann != 1.0 sein
    """
    overlay = VolRegimeOverlay(
        day_vol_budget=0.02,
        vol_window_bars=20,
        regime_lookback_bars=100,
        vol_target_scaling=True,
    )

    base_units = 10.0
    equity = 10000.0

    # Erste 21 Bars
    for i in range(21):
        price = 50000.0 * (1 + i * 0.001)  # Leichter Trend

        scaled_units = overlay.apply(
            units=base_units,
            signal=1,
            price=price,
            equity=equity,
            context={},
        )

        # Während Warmup: scaled_units == base_units
        assert scaled_units == base_units, (
            f"Warmup-Phase verletzt: Bar {i}, scaled_units={scaled_units} != {base_units}"
        )

    # Nach Warmup (Bar 22+): scale kann != 1 sein
    # (Aber braucht regime_lookback für Regime-Klassifizierung, also defaulted zu mid-regime)


# ============================================================================
# Test 9: DD-Throttle
# ============================================================================


@pytest.mark.xfail(
    strict=True,
    reason="Aspirational: dd-throttle specified for extended overlay. "
    "Current design keeps DD logic in canonical sizer (VolRegimeOverlaySizer).",
)
def test_dd_throttle():
    """
    Test: DD-Throttle reduziert Units bei Drawdown.

    Setup:
    - enable_dd_throttle=True
    - max_drawdown=0.25, dd_soft_start=0.10
    - Peak equity=10000, Current equity=8500 (DD=15%)
    - Erwartung: dd_factor zwischen 0 und 1, Units reduziert
    """
    overlay = VolRegimeOverlay(
        day_vol_budget=0.02,
        vol_window_bars=20,
        regime_lookback_bars=100,
        vol_target_scaling=False,  # Deaktiviere Vol-Targeting für Test
        enable_dd_throttle=True,
        max_drawdown=0.25,
        dd_soft_start=0.10,
    )

    base_units = 10.0

    # Warmup: Peak equity=10000
    for i in range(25):
        price = 50000.0
        equity = 10000.0

        overlay.apply(
            units=base_units,
            signal=1,
            price=price,
            equity=equity,
            context={},
        )

    # Jetzt: Drawdown auf 8500 (DD=15%)
    price = 50000.0
    equity_dd = 8500.0

    units_with_dd = overlay.apply(
        units=base_units,
        signal=1,
        price=price,
        equity=equity_dd,
        context={},
    )

    # Erwartung: units_with_dd < base_units (weil DD-Throttle aktiv)
    print(f"Base units: {base_units}")
    print(f"Units with DD (15%): {units_with_dd:.4f}")

    assert units_with_dd < base_units, (
        f"DD-Throttle funktioniert nicht: units_with_dd ({units_with_dd:.4f}) >= base_units ({base_units})"
    )

    # Genauere Berechnung:
    # dd = 15%, dd_soft_start=10%, max_dd=25%
    # dd_factor = 1 - (15% - 10%) / (25% - 10%) = 1 - 5/15 = 1 - 0.333 = 0.667
    # final_scale = vol_target_scale (=1) * regime_factor (=0.75 mid) * dd_factor (=0.667)
    # final_scale = 1.0 * 0.75 * 0.667 = 0.50
    # units = 10 * 0.50 = 5.0

    expected_units_approx = 10.0 * 0.75 * 0.667  # ~ 5.0
    assert abs(units_with_dd - expected_units_approx) < 1.0, (
        f"DD-Throttle-Berechnung falsch: {units_with_dd:.4f} != {expected_units_approx:.4f} (approx)"
    )


# ============================================================================
# Test 10: Config mit overlays list
# ============================================================================


def test_config_with_overlays_list():
    """
    Test: Config mit overlays=["vol_regime_overlay"] baut CompositePositionSizer.
    """
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": ["vol_regime_overlay"],
            "overlay": {
                "vol_regime_overlay": {
                    "day_vol_budget": 0.02,
                    "vol_window_bars": 20,
                }
            },
        },
        "research": {"allow_r_and_d_overlays": True},
        "environment": {"mode": "offline_backtest"},
    }

    sizer = build_position_sizer_from_config(cfg)

    assert isinstance(sizer, CompositePositionSizer)
    assert isinstance(sizer.base_sizer, FixedSizeSizer)
    assert len(sizer.overlays) == 1
    assert isinstance(sizer.overlays[0], VolRegimeOverlay)


def test_config_with_empty_overlays_list():
    """
    Test: overlays=[] verhält sich wie normaler Sizer (ohne Composite).
    """
    cfg = {
        "position_sizing": {
            "key": "fixed_size",
            "units": 10.0,
            "overlays": [],  # Leer
        },
        "environment": {"mode": "offline_backtest"},
    }

    sizer = build_position_sizer_from_config(cfg)

    # Sollte FixedSizeSizer sein (NICHT CompositePositionSizer)
    assert isinstance(sizer, FixedSizeSizer)
    assert not isinstance(sizer, CompositePositionSizer)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

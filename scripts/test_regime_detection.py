#!/usr/bin/env python3
"""
Quick Test: Regime Detection
==============================
Testet die Regime-Detection-Funktionalität.
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_backtest import load_ohlcv_data
from src.core.peak_config import load_config
from src.core.regime import (
    build_regime_config_from_config,
    label_trend_regime,
    label_vol_regime,
    label_combined_regime,
    summarize_regime_distribution,
)


def main():
    print("\n🧪 Regime Detection Test\n")
    print("=" * 70)

    # Config laden
    print("\n1️⃣ Lade Config...")
    try:
        cfg = load_config("config.toml")
        print("   ✅ Config geladen")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return

    # Regime-Config bauen
    print("\n2️⃣ Baue Regime-Config...")
    try:
        regime_cfg = build_regime_config_from_config(cfg)
        print(f"   ✅ Regime-Config: {regime_cfg}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return

    # Test-Daten erstellen
    print("\n3️⃣ Erstelle Test-Daten...")
    df = load_ohlcv_data(None, None, None, n_bars=200)
    print(f"   ✅ {len(df)} Bars erstellt")
    print(f"   📊 Preis-Range: {df['close'].min():.2f} - {df['close'].max():.2f}")

    # Regime-Labels berechnen
    print("\n4️⃣ Berechne Regime-Labels...")
    try:
        trend_labels = label_trend_regime(df, regime_cfg)
        vol_labels = label_vol_regime(df, regime_cfg)
        combined_labels = label_combined_regime(trend_labels, vol_labels)

        print(f"   ✅ {len(combined_labels)} Labels berechnet")
        print(f"   📈 Trend-Regimes: {trend_labels.unique()}")
        print(f"   📊 Vol-Regimes: {vol_labels.unique()}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return

    # Verteilung berechnen
    print("\n5️⃣ Berechne Regime-Verteilung...")
    try:
        dist = summarize_regime_distribution(combined_labels)
        print("   ✅ Verteilung:")
        for regime, pct in sorted(dist.items(), key=lambda x: x[1], reverse=True):
            print(f"      {regime:25s}: {pct:6.2%}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n" + "=" * 70)
    print("✅ Regime Detection Test erfolgreich!\n")


if __name__ == "__main__":
    main()

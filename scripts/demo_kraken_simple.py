#!/usr/bin/env python3
"""
Peak_Trade Kraken Integration Demo
====================================
Einfaches Demo für Kraken → Normalizer → Cache → Backtest Pipeline.

Usage:
    python scripts/demo_kraken_simple.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data import (
    KrakenDataPipeline,
    fetch_kraken_data,
    test_kraken_connection,
)


def main():
    """Hauptfunktion."""
    print("\n" + "=" * 70)
    print("KRAKEN DATA PIPELINE DEMO")
    print("=" * 70)

    # 1. Verbindung testen
    print("\n🔌 Teste Kraken-Verbindung...")
    if not test_kraken_connection():
        print("❌ Keine Verbindung zu Kraken.")
        print("   Bitte Internetverbindung prüfen.")
        return

    # 2. Pipeline erstellen
    print("\n📡 Erstelle Pipeline...")
    pipeline = KrakenDataPipeline(use_cache=True)

    # 3. Daten holen (wird gecacht)
    print("\n📥 Hole BTC/USD 1h Daten (100 Bars)...")
    df = pipeline.fetch_and_prepare(symbol="BTC/USD", timeframe="1h", limit=100)

    print(f"\n✅ Daten geladen:")
    print(f"  Bars:      {len(df)}")
    print(f"  Zeitraum:  {df.index[0]} bis {df.index[-1]}")
    print(f"  Spalten:   {list(df.columns)}")

    print("\n📊 Erste 5 Zeilen:")
    print(df.head().to_string())

    print("\n📈 Statistiken:")
    print(df.describe().to_string())

    # 4. Nochmal holen (sollte aus Cache kommen)
    print("\n📦 Hole nochmal (sollte aus Cache kommen)...")
    df2 = pipeline.fetch_and_prepare(symbol="BTC/USD", timeframe="1h", limit=100)

    print(f"  ✅ Aus Cache: {len(df2)} Bars")
    print(f"  Identisch: {df.equals(df2)}")

    # 5. Resampling-Demo
    print("\n🔄 Resampling-Demo (1h → 4h)...")
    df_4h = pipeline.fetch_and_resample(
        symbol="BTC/USD",
        source_timeframe="1h",
        target_timeframe="4h",
        limit=200,  # 200 Stunden = ~50 4h-Bars
    )

    print(f"  ✅ Resampled: {len(df_4h)} Bars (4h)")
    print("\n📊 Erste 3 Zeilen (4h):")
    print(df_4h.head(3).to_string())

    # 6. Convenience-Funktion
    print("\n⚡ Convenience-Funktion Test...")
    df_quick = fetch_kraken_data("ETH/USD", "1h", limit=50)
    print(f"  ✅ ETH/USD geladen: {len(df_quick)} Bars")

    print("\n" + "=" * 70)
    print("✅ KRAKEN-PIPELINE DEMO ABGESCHLOSSEN!")
    print("=" * 70)

    print("\n📝 Verwendung im Code:")
    print("""
    from src.data import fetch_kraken_data

    # Einfach:
    df = fetch_kraken_data("BTC/USD", "1h", limit=720)

    # Erweitert:
    from src.data import KrakenDataPipeline

    pipeline = KrakenDataPipeline()
    df = pipeline.fetch_and_prepare("BTC/USD", "1h", limit=720)
    df_4h = pipeline.fetch_and_resample("BTC/USD", "1h", "4h", limit=1000)
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen.")
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()

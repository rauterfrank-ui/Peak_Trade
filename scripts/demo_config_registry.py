#!/usr/bin/env python3
"""
Demo: Peak_Trade Strategien-Registry
=====================================
Zeigt die neuen Registry-Funktionen in Aktion.

Run:
    cd ~/Peak_Trade
    python scripts/demo_config_registry.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config_registry import (
    get_config,
    get_active_strategies,
    get_strategy_config,
    list_strategies,
    get_strategies_by_regime,
)


def print_section(title: str):
    """Formatierte Section-Header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_basic_config():
    """Zeigt Basis-Config-Zugriff."""
    print_section("1. BASIS-KONFIGURATION")

    cfg = get_config()

    print(f"📊 Backtest Initial Cash: ${cfg['backtest']['initial_cash']:,.2f}")
    print(f"⚠️  Risk per Trade: {cfg['risk']['risk_per_trade']:.1%}")
    print(f"🛡️  Max Position Size: {cfg['risk']['max_position_size']:.0%}")
    print(f"🚦 Max Positions: {cfg['risk']['max_positions']}")
    print(f"📁 Data Dir: {cfg['data']['data_dir']}")


def demo_active_strategies():
    """Zeigt Active-Strategien."""
    print_section("2. AKTIVE STRATEGIEN")

    active = get_active_strategies()
    print(f"🎯 {len(active)} aktive Strategien:")
    for i, name in enumerate(active, 1):
        print(f"   {i}. {name}")


def demo_strategy_details():
    """Zeigt Details einer Strategie mit Defaults-Merging."""
    print_section("3. STRATEGIE-DETAILS (mit Defaults-Merging)")

    name = "ma_crossover"
    cfg = get_strategy_config(name)

    print(f"📌 Strategie: {cfg.name}")
    print(f"✅ Aktiv: {cfg.active}")
    print()
    print(f"Strategie-spezifische Parameter:")
    for key, value in cfg.params.items():
        print(f"   • {key}: {value}")
    print()
    print(f"Wichtige Werte (mit Defaults-Fallback):")
    print(f"   • stop_pct: {cfg.get('stop_pct'):.1%}")
    print(f"   • take_profit_pct: {cfg.get('take_profit_pct'):.1%}")
    print(f"   • position_fraction: {cfg.get('position_fraction'):.0%}")
    print(f"   • min_hold_bars: {cfg.get('min_hold_bars')}")
    print(f"   • max_hold_bars: {cfg.get('max_hold_bars')}")

    if cfg.metadata:
        print()
        print(f"Metadata:")
        print(f"   • Typ: {cfg.metadata['type']}")
        print(f"   • Risk-Level: {cfg.metadata['risk_level']}")
        print(f"   • Best Regime: {cfg.metadata['best_market_regime']}")
        print(f"   • Timeframes: {', '.join(cfg.metadata['recommended_timeframes'])}")


def demo_all_strategies():
    """Liste aller Strategien."""
    print_section("4. ALLE VERFÜGBAREN STRATEGIEN")

    all_strats = list_strategies()
    active = get_active_strategies()

    print(f"📚 {len(all_strats)} Strategien definiert:\n")

    for name in all_strats:
        is_active = "🟢" if name in active else "⚪"
        cfg = get_strategy_config(name)

        meta_info = ""
        if cfg.metadata:
            meta_info = f" ({cfg.metadata['type']}, {cfg.metadata['best_market_regime']})"

        print(f"{is_active} {name}{meta_info}")


def demo_regime_filtering():
    """Filtert Strategien nach Marktregime."""
    print_section("5. STRATEGIE-SELEKTION NACH MARKTREGIME")

    for regime in ["trending", "ranging", "any"]:
        strategies = get_strategies_by_regime(regime)
        print(f"📊 {regime.upper()}-Strategien:")
        for name in strategies:
            cfg = get_strategy_config(name)
            is_active = "✅" if cfg.active else "  "
            print(f"   {is_active} {name}")
        print()


def demo_merged_config():
    """Zeigt Merged Config für alle aktiven Strategien."""
    print_section("6. MERGED CONFIGS FÜR ALLE AKTIVEN STRATEGIEN")

    for name in get_active_strategies():
        cfg = get_strategy_config(name)
        merged = cfg.to_dict()

        print(f"📋 {name}:")
        print(
            f"   Stop: {merged['stop_pct']:.1%} | "
            f"TP: {merged.get('take_profit_pct', 'N/A')} | "
            f"Pos: {merged['position_fraction']:.0%} | "
            f"Hold: {merged['min_hold_bars']}-{merged['max_hold_bars']} bars"
        )
        print()


def main():
    """Hauptfunktion."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     Peak_Trade Strategien-Registry Demo                         ║
║     ========================================                      ║
║                                                                  ║
║     Zeigt die neue Registry-Funktionalität                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    try:
        demo_basic_config()
        demo_active_strategies()
        demo_strategy_details()
        demo_all_strategies()
        demo_regime_filtering()
        demo_merged_config()

        print_section("✅ DEMO ERFOLGREICH")
        print("Die Registry funktioniert! 🚀")
        print("\nNächste Schritte:")
        print("1. Nutze die Registry in deinen Backtest-Skripten")
        print("2. Siehe docs/CONFIG_REGISTRY_USAGE.md für API-Referenz")
        print("3. Passe config.toml an (strategies.active-Liste)")

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

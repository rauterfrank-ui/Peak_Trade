#!/usr/bin/env python3
"""
Peak_Trade Risk Limits Demo
============================
Demonstriert die neue RiskLimits Klasse mit allen Check-Methoden.

Usage:
    python scripts/demo_risk_limits.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.risk import RiskLimits, RiskLimitsConfig


def demo_drawdown_check():
    """Demo: Drawdown-Check."""
    print("\n" + "=" * 70)
    print("DEMO 1: Drawdown Check")
    print("=" * 70)

    limits = RiskLimits()

    # Scenario 1: Alles OK
    print("\n✅ Scenario 1: Drawdown unter Limit")
    equity_curve = [10000, 10500, 10200, 9800, 9900]
    max_dd_pct = 20.0

    result = limits.check_drawdown(equity_curve, max_dd_pct)

    # Berechne tatsächlichen Drawdown
    import numpy as np

    equity_arr = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_arr)
    drawdown_pct = (equity_arr - running_max) / running_max * 100.0
    actual_dd = abs(np.min(drawdown_pct))

    print(f"  Equity-Curve: {equity_curve}")
    print(f"  Max Drawdown Limit: {max_dd_pct}%")
    print(f"  Aktueller Drawdown: {actual_dd:.1f}%")
    print(f"  Result: {'✅ OK' if result else '❌ BLOCKED'}")

    # Scenario 2: Limit überschritten
    print("\n❌ Scenario 2: Drawdown über Limit")
    equity_curve = [10000, 10500, 8000, 7500, 7800]
    max_dd_pct = 20.0

    result = limits.check_drawdown(equity_curve, max_dd_pct)

    equity_arr = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_arr)
    drawdown_pct = (equity_arr - running_max) / running_max * 100.0
    actual_dd = abs(np.min(drawdown_pct))

    print(f"  Equity-Curve: {equity_curve}")
    print(f"  Max Drawdown Limit: {max_dd_pct}%")
    print(f"  Aktueller Drawdown: {actual_dd:.1f}%")
    print(f"  Result: {'✅ OK' if result else '❌ BLOCKED'}")


def demo_daily_loss_check():
    """Demo: Daily Loss Check."""
    print("\n" + "=" * 70)
    print("DEMO 2: Daily Loss Check")
    print("=" * 70)

    limits = RiskLimits()

    # Scenario 1: Alles OK
    print("\n✅ Scenario 1: Daily Loss unter Limit")
    returns = [0.5, -1.2, 0.3, -1.5, 0.8]  # in %
    max_loss_pct = 5.0

    result = limits.check_daily_loss(returns, max_loss_pct)

    import numpy as np

    returns_arr = np.array(returns)
    losses = returns_arr[returns_arr < 0]
    total_loss = abs(np.sum(losses))

    print(f"  Tages-Returns: {returns}%")
    print(f"  Max Loss Limit: {max_loss_pct}%")
    print(f"  Tatsächlicher Loss: {total_loss:.1f}% (nur negative Returns)")
    print(f"  Result: {'✅ OK' if result else '❌ BLOCKED'}")

    # Scenario 2: Limit überschritten
    print("\n❌ Scenario 2: Daily Loss über Limit")
    returns = [0.5, -2.5, 0.3, -3.2, 0.8]  # in %
    max_loss_pct = 5.0

    result = limits.check_daily_loss(returns, max_loss_pct)

    returns_arr = np.array(returns)
    losses = returns_arr[returns_arr < 0]
    total_loss = abs(np.sum(losses))

    print(f"  Tages-Returns: {returns}%")
    print(f"  Max Loss Limit: {max_loss_pct}%")
    print(f"  Tatsächlicher Loss: {total_loss:.1f}%")
    print(f"  Result: {'✅ OK' if result else '❌ BLOCKED'}")


def demo_position_size_check():
    """Demo: Position Size Check."""
    print("\n" + "=" * 70)
    print("DEMO 3: Position Size Check")
    print("=" * 70)

    limits = RiskLimits()

    # Scenario 1: Alles OK
    print("\n✅ Scenario 1: Position unter Limit")
    size_nominal = 2000
    capital = 10000
    max_pct = 25.0

    result = limits.check_position_size(size_nominal, capital, max_pct)

    actual_pct = (size_nominal / capital) * 100.0

    print(f"  Position Nominal: ${size_nominal:,.2f}")
    print(f"  Capital: ${capital:,.2f}")
    print(f"  Max Position %: {max_pct}%")
    print(f"  Aktuelle Position: {actual_pct:.1f}%")
    print(f"  Result: {'✅ OK' if result else '❌ BLOCKED'}")

    # Scenario 2: Limit überschritten
    print("\n❌ Scenario 2: Position über Limit")
    size_nominal = 3000
    capital = 10000
    max_pct = 25.0

    result = limits.check_position_size(size_nominal, capital, max_pct)

    actual_pct = (size_nominal / capital) * 100.0

    print(f"  Position Nominal: ${size_nominal:,.2f}")
    print(f"  Capital: ${capital:,.2f}")
    print(f"  Max Position %: {max_pct}%")
    print(f"  Aktuelle Position: {actual_pct:.1f}%")
    print(f"  Result: {'✅ OK' if result else '❌ BLOCKED'}")


def demo_check_all():
    """Demo: Kombinierter Check aller Limits."""
    print("\n" + "=" * 70)
    print("DEMO 4: check_all() - Kombinierter Check")
    print("=" * 70)

    config = RiskLimitsConfig(
        max_drawdown_pct=20.0, max_position_pct=25.0, daily_loss_limit_pct=5.0
    )
    limits = RiskLimits(config)

    # Scenario 1: Alle Limits OK
    print("\n✅ Scenario 1: Alle Limits OK")
    result = limits.check_all(
        equity_curve=[10000, 10200, 10500, 10300],
        returns_today_pct=[0.5, -1.0, 0.3],
        new_position_nominal=2000,
        capital=10300,
    )

    print(f"  Equity-Curve: [10000, 10200, 10500, 10300]")
    print(f"  Tages-Returns: [0.5, -1.0, 0.3]%")
    print(f"  Neue Position: $2,000")
    print(f"  Capital: $10,300")
    print(f"  Result: {'✅ TRADE ALLOWED' if result else '❌ TRADE BLOCKED'}")

    # Scenario 2: Daily Loss Limit überschritten
    print("\n❌ Scenario 2: Daily Loss Limit überschritten")
    result = limits.check_all(
        equity_curve=[10000, 10200, 10500, 9800],
        returns_today_pct=[-2.5, 0.3, -3.5, 0.2],
        new_position_nominal=2000,
        capital=9800,
    )

    print(f"  Equity-Curve: [10000, 10200, 10500, 9800]")
    print(f"  Tages-Returns: [-2.5, 0.3, -3.5, 0.2]% (Total Loss: 6.0%)")
    print(f"  Neue Position: $2,000")
    print(f"  Capital: $9,800")
    print(f"  Result: {'✅ TRADE ALLOWED' if result else '❌ TRADE BLOCKED'}")

    # Scenario 3: Position Size zu groß
    print("\n❌ Scenario 3: Position Size zu groß")
    result = limits.check_all(
        equity_curve=[10000, 10200, 10500, 10300],
        returns_today_pct=[0.5, -1.0, 0.3],
        new_position_nominal=3000,  # 29% von 10300
        capital=10300,
    )

    print(f"  Equity-Curve: [10000, 10200, 10500, 10300]")
    print(f"  Tages-Returns: [0.5, -1.0, 0.3]%")
    print(f"  Neue Position: $3,000 (29% von Capital)")
    print(f"  Capital: $10,300")
    print(f"  Result: {'✅ TRADE ALLOWED' if result else '❌ TRADE BLOCKED'}")

    # Scenario 4: Drawdown zu hoch
    print("\n❌ Scenario 4: Drawdown zu hoch")
    result = limits.check_all(
        equity_curve=[10000, 10500, 8000, 7800],
        returns_today_pct=[0.5, -1.0],
        new_position_nominal=1500,
        capital=7800,
    )

    print(f"  Equity-Curve: [10000, 10500, 8000, 7800] (Drawdown: ~26%)")
    print(f"  Tages-Returns: [0.5, -1.0]%")
    print(f"  Neue Position: $1,500")
    print(f"  Capital: $7,800")
    print(f"  Result: {'✅ TRADE ALLOWED' if result else '❌ TRADE BLOCKED'}")


def demo_custom_config():
    """Demo: Eigene Config."""
    print("\n" + "=" * 70)
    print("DEMO 5: Custom Config")
    print("=" * 70)

    # Aggressive Config
    print("\n🔴 Aggressive Config:")
    aggressive_config = RiskLimitsConfig(
        max_drawdown_pct=30.0,  # 30% DD erlaubt
        max_position_pct=50.0,  # 50% Position erlaubt
        daily_loss_limit_pct=10.0,  # 10% Daily Loss erlaubt
    )
    print(f"  Max Drawdown: {aggressive_config.max_drawdown_pct}%")
    print(f"  Max Position: {aggressive_config.max_position_pct}%")
    print(f"  Daily Loss Limit: {aggressive_config.daily_loss_limit_pct}%")

    # Conservative Config
    print("\n🟢 Conservative Config:")
    conservative_config = RiskLimitsConfig(
        max_drawdown_pct=10.0,  # 10% DD erlaubt
        max_position_pct=5.0,  # 5% Position erlaubt
        daily_loss_limit_pct=2.0,  # 2% Daily Loss erlaubt
    )
    print(f"  Max Drawdown: {conservative_config.max_drawdown_pct}%")
    print(f"  Max Position: {conservative_config.max_position_pct}%")
    print(f"  Daily Loss Limit: {conservative_config.daily_loss_limit_pct}%")

    # Test mit beiden Configs
    print("\n📊 Test: Position $2000 bei Capital $10000")
    equity_curve = [10000, 10200, 10500]
    returns_today = [0.5, -1.0]

    aggressive = RiskLimits(aggressive_config)
    conservative = RiskLimits(conservative_config)

    result_agg = aggressive.check_all(
        equity_curve=equity_curve,
        returns_today_pct=returns_today,
        new_position_nominal=2000,
        capital=10000,
    )

    result_cons = conservative.check_all(
        equity_curve=equity_curve,
        returns_today_pct=returns_today,
        new_position_nominal=2000,
        capital=10000,
    )

    print(f"  Aggressive: {'✅ ALLOWED' if result_agg else '❌ BLOCKED'}")
    print(f"  Conservative: {'✅ ALLOWED' if result_cons else '❌ BLOCKED'}")
    print(f"  (Position = 20% von Capital)")


def main():
    """Hauptfunktion."""
    print("\n" + "=" * 70)
    print("PEAK_TRADE RISK LIMITS DEMO")
    print("=" * 70)
    print("\nDemonstriert die neue RiskLimits Klasse:")
    print("  - check_drawdown()")
    print("  - check_daily_loss()")
    print("  - check_position_size()")
    print("  - check_all()")

    try:
        demo_drawdown_check()
        demo_daily_loss_check()
        demo_position_size_check()
        demo_check_all()
        demo_custom_config()

        print("\n" + "=" * 70)
        print("✅ ALLE DEMOS ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 70)

        print("\n📝 Verwendung im Code:")
        print("""
from src.risk import RiskLimits, RiskLimitsConfig

# Config erstellen
config = RiskLimitsConfig(
    max_drawdown_pct=20.0,
    max_position_pct=10.0,
    daily_loss_limit_pct=5.0
)

limits = RiskLimits(config)

# Vor Trade: Alle Limits prüfen
ok = limits.check_all(
    equity_curve=equity_history,
    returns_today_pct=today_returns,
    new_position_nominal=position_value,
    capital=current_capital
)

if not ok:
    print("Trade blocked by risk limits!")
else:
    # Trade ausführen
    pass
        """)

    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

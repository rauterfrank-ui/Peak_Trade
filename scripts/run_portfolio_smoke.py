#!/usr/bin/env python3
"""
Peak_Trade Portfolio Smoke Test (v1.1)
=======================================
Führt einen schnellen Smoke-Test für asset-basierte Portfolios durch.

Features:
- Lädt Portfolio-Config aus config/portfolios/
- Validiert Config-Struktur und Universe-Referenzen
- Führt Mini-Backtest mit Dummy-Daten durch (schnell, deterministisch)
- Prüft Health-Expectations (Trades, Returns, Drawdown, Runtime)
- Exit-Codes für TestHealth-Integration

Usage:
    python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_EUR_V1
    python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_USDT_V1 --verbose
    python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_EUR_V1 --validate-only

Exit Codes:
    0 = PASS (alle Expectations erfüllt)
    1 = FAIL (harte Expectation verletzt oder Exception)
    2 = WARN (weiche Expectation verletzt, aber kein Fail)
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Projekt-Root zum Python-Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import tomllib  # Python 3.11+
except ImportError:
    import toml as tomllib  # Fallback für Python < 3.11


# ============================================================================
# Psychology Helper (inline für Standalone-Betrieb)
# ============================================================================


def derive_psychology(
    total_return_pct: float,
    max_drawdown_pct: float,
    trades_count: int,
) -> Dict[str, Any]:
    """
    Leitet Psychologie-Annotation aus Portfolio-Metriken ab.

    Returns dict mit: level, level_emoji, notes, und Metriken.
    """
    notes: List[str] = []

    # Basis-Level anhand Max-Drawdown
    if max_drawdown_pct <= 30:
        level = "CALM"
    elif max_drawdown_pct <= 60:
        level = "MEDIUM"
    else:
        level = "SPICY"
        notes.append(
            f"Hoher Max-Drawdown ({max_drawdown_pct:.1f}%) – "
            "psychologisch anspruchsvoll, nur für erfahrene Operatoren."
        )

    # Extrem gute Performance → Overconfidence-Risiko
    if total_return_pct >= 150:
        notes.append(
            f"Sehr hohe Performance ({total_return_pct:.1f}%) – Gefahr von Overconfidence."
        )
    elif total_return_pct >= 100:
        notes.append(
            f"Starke Performance ({total_return_pct:.1f}%) – nicht als Normalfall interpretieren."
        )

    # Extrem schlechte Performance → Panic-Risiko
    if total_return_pct <= -40:
        notes.append(f"Starke Verluste ({total_return_pct:.1f}%) – Gefahr von Panic-Reaktionen.")
        if level == "CALM":
            level = "MEDIUM"

    # Trade-Anzahl
    if trades_count < 3:
        notes.append(f"Sehr wenige Trades ({trades_count}) – psychologische Aussagekraft begrenzt.")
    elif trades_count > 100:
        notes.append(f"Viele Trades ({trades_count}) – Gefahr von Overtrading & Decision-Fatigue.")

    # Default-Notes
    if not notes:
        if level == "CALM":
            notes.append("Ruhiges Profil – psychologisch gut beherrschbar.")
        elif level == "MEDIUM":
            notes.append("Mittlere Schwankungen – bewusstes Risikomanagement nötig.")
        else:
            notes.append("Spicy Profil – nur für erfahrene Operatoren geeignet.")

    level_emoji = {"CALM": "🧘", "MEDIUM": "⚠️", "SPICY": "🔥"}.get(level, "❓")

    return {
        "level": level,
        "level_emoji": level_emoji,
        "notes": notes,
        "max_drawdown_pct": max_drawdown_pct,
        "total_return_pct": total_return_pct,
        "trades_count": trades_count,
    }


# ============================================================================
# Expectations Configuration
# ============================================================================


@dataclass
class PortfolioExpectations:
    """
    Health-Expectations für Portfolio-Smoketests.

    Konservative Defaults für Stabilität (keine Outperformance-Optimierung).
    """

    # Runtime
    max_runtime_warn: float = 90.0  # Sekunden
    max_runtime_fail: float = 150.0

    # Trades
    min_trades_warn: int = 3  # weniger als 3 = WARN
    min_trades_fail: int = 1  # 0 Trades = FAIL

    # Returns (in %)
    min_return_warn: float = -40.0  # schlechter als -40% = WARN
    min_return_fail: float = -80.0  # schlechter als -80% = FAIL
    max_return_warn: float = 150.0  # mehr als +150% = WARN
    max_return_fail: float = 500.0  # mehr als +500% = FAIL

    # Drawdown (in %, als positive Zahl)
    max_drawdown_warn: float = 60.0  # >60% DD = WARN
    max_drawdown_fail: float = 80.0  # >80% DD = FAIL

    # Exceptions
    allow_exceptions: bool = False


# Default-Expectations (konservativ)
DEFAULT_EXPECTATIONS = PortfolioExpectations()


# ============================================================================
# Core Functions
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Portfolio Smoke Test (v1.1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Core EUR Portfolio testen
  python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_EUR_V1

  # Core USDT Portfolio (verbose)
  python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_USDT_V1 --verbose

  # Nur Validierung (kein Backtest)
  python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_EUR_V1 --validate-only

  # Mit custom Expectations
  python scripts/run_portfolio_smoke.py --portfolio-id PORTFOLIO_CORE_EUR_V1 --min-trades 5 --max-runtime 120

Exit Codes:
  0 = PASS (alle Expectations erfüllt)
  1 = FAIL (harte Expectation verletzt oder Exception)
  2 = WARN (weiche Expectation verletzt)
        """,
    )

    parser.add_argument(
        "--portfolio-id", type=str, required=True, help="Portfolio-ID (z.B. PORTFOLIO_CORE_EUR_V1)"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Nur Config validieren, keinen Backtest durchführen",
    )

    parser.add_argument("--verbose", action="store_true", help="Verbose Output")

    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Lookback-Tage für Backtest (überschreibt Config-Default)",
    )

    # Expectations (CLI-Override)
    exp_group = parser.add_argument_group("Expectations (optional)")
    exp_group.add_argument(
        "--max-runtime", type=float, default=None, help="Max. Runtime in Sekunden (Fail-Schwelle)"
    )
    exp_group.add_argument(
        "--min-trades", type=int, default=None, help="Min. Trades (Fail-Schwelle)"
    )
    exp_group.add_argument(
        "--min-return", type=float, default=None, help="Min. Return %% (Fail-Schwelle)"
    )
    exp_group.add_argument(
        "--max-return", type=float, default=None, help="Max. Return %% (Fail-Schwelle)"
    )
    exp_group.add_argument(
        "--max-drawdown", type=float, default=None, help="Max. Drawdown %% (Fail-Schwelle)"
    )

    return parser.parse_args()


def find_portfolio_config(portfolio_id: str) -> Optional[Path]:
    """Findet die Portfolio-Config-Datei für eine gegebene ID."""
    portfolios_dir = project_root / "config" / "portfolios"
    if not portfolios_dir.exists():
        return None

    for toml_file in portfolios_dir.glob("*.toml"):
        try:
            try:
                with open(toml_file, "rb") as f:
                    config = tomllib.load(f)
            except TypeError:
                config = tomllib.load(str(toml_file))
            if config.get("portfolio", {}).get("portfolio_id") == portfolio_id:
                return toml_file
        except Exception:
            continue

    return None


def load_portfolio_config(config_path: Path) -> Dict[str, Any]:
    """Lädt Portfolio-Config aus TOML-Datei."""
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except TypeError:
        return tomllib.load(str(config_path))


def validate_portfolio_config(config: Dict[str, Any], verbose: bool = False) -> List[str]:
    """Validiert Portfolio-Config-Struktur."""
    errors = []
    portfolio = config.get("portfolio", {})

    required_fields = ["portfolio_id", "portfolio_name", "universe_id"]
    for field in required_fields:
        if not portfolio.get(field):
            errors.append(f"Pflichtfeld fehlt: portfolio.{field}")

    assets = portfolio.get("assets", [])
    if not assets:
        errors.append("Keine Assets definiert (portfolio.assets ist leer)")
    else:
        total_weight = 0.0
        for i, asset in enumerate(assets):
            if not asset.get("symbol"):
                errors.append(f"Asset #{i + 1}: symbol fehlt")
            weight = asset.get("weight", 0)
            if not isinstance(weight, (int, float)) or weight <= 0:
                errors.append(f"Asset #{i + 1}: ungültiges weight={weight}")
            total_weight += weight

        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Asset-Gewichte summieren sich zu {total_weight:.2f} (erwartet: 1.0)")

    universe_id = portfolio.get("universe_id")
    if universe_id:
        universe_path = project_root / "config" / "markets"
        if universe_path.exists():
            found = False
            for yaml_file in universe_path.glob("*.yaml"):
                try:
                    import yaml

                    with open(yaml_file, "r") as f:
                        universe = yaml.safe_load(f)
                    if universe.get("universe_id") == universe_id:
                        found = True
                        if verbose:
                            print(f"  ✓ Universe gefunden: {yaml_file.name}")
                        break
                except Exception:
                    continue
            if not found:
                errors.append(f"Universe '{universe_id}' nicht gefunden in config/markets/")
        else:
            errors.append("config/markets/ Verzeichnis existiert nicht")

    return errors


def run_mini_backtest(
    config: Dict[str, Any], lookback_days: int = 30, verbose: bool = False
) -> Dict[str, Any]:
    """
    Führt einen minimalen Backtest mit Dummy-Daten durch.

    Erweitert um: Trade-Counting, Drawdown-Berechnung, detaillierte Metriken.
    """
    import numpy as np
    import pandas as pd

    portfolio = config.get("portfolio", {})
    assets = portfolio.get("assets", [])

    results = {
        "portfolio_id": portfolio.get("portfolio_id"),
        "assets_tested": [],
        "total_return_pct": 0.0,
        "total_trades": 0,
        "max_drawdown_pct": 0.0,
        "success": True,
        "errors": [],
        "exceptions": [],
    }

    n_bars = lookback_days * 24  # Hourly data
    np.random.seed(42)  # Deterministisch

    portfolio_equity = []
    all_signals = []

    for asset in assets:
        symbol = asset.get("symbol", "UNKNOWN")
        weight = asset.get("weight", 0)

        if verbose:
            print(f"  → Teste {symbol} (weight={weight:.2f})...")

        try:
            # Dummy-Daten generieren
            dates = pd.date_range(end=datetime.now(), periods=n_bars, freq="1h")

            base_price = 1000 if "BTC" not in symbol else 50000
            if "ETH" in symbol:
                base_price = 3000
            elif "SOL" in symbol:
                base_price = 150

            # Simple Random Walk
            returns = np.random.randn(n_bars) * 0.01
            prices = base_price * np.exp(np.cumsum(returns))

            df = pd.DataFrame(
                {
                    "open": prices * (1 + np.random.randn(n_bars) * 0.001),
                    "high": prices * (1 + abs(np.random.randn(n_bars)) * 0.005),
                    "low": prices * (1 - abs(np.random.randn(n_bars)) * 0.005),
                    "close": prices,
                    "volume": np.random.randint(100, 10000, n_bars),
                },
                index=dates,
            )

            # Simple MA-Crossover Signal
            df["sma_fast"] = df["close"].rolling(10).mean()
            df["sma_slow"] = df["close"].rolling(30).mean()
            df["signal"] = (df["sma_fast"] > df["sma_slow"]).astype(int)

            # Trade-Counting (Signal-Wechsel)
            df["signal_change"] = df["signal"].diff().abs()
            asset_trades = int(df["signal_change"].sum())

            # Strategy Returns
            df["strategy_return"] = df["signal"].shift(1) * df["close"].pct_change()
            df["equity"] = (1 + df["strategy_return"]).cumprod()

            # Asset Return
            asset_return = (df["equity"].iloc[-1] - 1) * 100  # in %

            # Drawdown für dieses Asset
            df["rolling_max"] = df["equity"].expanding().max()
            df["drawdown"] = (df["equity"] - df["rolling_max"]) / df["rolling_max"] * 100
            asset_max_dd = abs(df["drawdown"].min())

            results["assets_tested"].append(
                {
                    "symbol": symbol,
                    "weight": weight,
                    "return_pct": float(asset_return),
                    "trades": asset_trades,
                    "max_drawdown_pct": float(asset_max_dd),
                    "n_bars": n_bars,
                }
            )

            # Aggregieren (gewichtet)
            results["total_return_pct"] += asset_return * weight
            results["total_trades"] += asset_trades
            results["max_drawdown_pct"] = max(results["max_drawdown_pct"], asset_max_dd)

            if verbose:
                print(
                    f"    ✓ Return: {asset_return:+.2f}% | Trades: {asset_trades} | MaxDD: {asset_max_dd:.1f}%"
                )

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"{symbol}: {str(e)}")
            results["exceptions"].append(str(e))
            if verbose:
                print(f"    ✗ Error: {e}")

    return results


def evaluate_expectations(
    results: Dict[str, Any],
    runtime_seconds: float,
    expectations: PortfolioExpectations,
    verbose: bool = False,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Evaluiert die Backtest-Ergebnisse gegen Expectations.

    Returns:
        Tuple von (status, violations)
        status: "PASS", "WARN", "FAIL"
        violations: Liste von Verletzungen mit Details
    """
    violations = []
    has_fail = False
    has_warn = False

    # 1. Exceptions
    if results.get("exceptions") and not expectations.allow_exceptions:
        violations.append(
            {
                "type": "exception",
                "severity": "FAIL",
                "message": f"Exceptions aufgetreten: {results['exceptions']}",
            }
        )
        has_fail = True

    # 2. Runtime
    if runtime_seconds > expectations.max_runtime_fail:
        violations.append(
            {
                "type": "runtime",
                "severity": "FAIL",
                "message": f"Runtime {runtime_seconds:.1f}s > Fail-Schwelle {expectations.max_runtime_fail}s",
            }
        )
        has_fail = True
    elif runtime_seconds > expectations.max_runtime_warn:
        violations.append(
            {
                "type": "runtime",
                "severity": "WARN",
                "message": f"Runtime {runtime_seconds:.1f}s > Warn-Schwelle {expectations.max_runtime_warn}s",
            }
        )
        has_warn = True

    # 3. Trades
    total_trades = results.get("total_trades", 0)
    if total_trades < expectations.min_trades_fail:
        violations.append(
            {
                "type": "trades",
                "severity": "FAIL",
                "message": f"Trades {total_trades} < Fail-Schwelle {expectations.min_trades_fail}",
            }
        )
        has_fail = True
    elif total_trades < expectations.min_trades_warn:
        violations.append(
            {
                "type": "trades",
                "severity": "WARN",
                "message": f"Trades {total_trades} < Warn-Schwelle {expectations.min_trades_warn}",
            }
        )
        has_warn = True

    # 4. Returns (Min)
    total_return = results.get("total_return_pct", 0)
    if total_return < expectations.min_return_fail:
        violations.append(
            {
                "type": "return_min",
                "severity": "FAIL",
                "message": f"Return {total_return:.1f}% < Fail-Schwelle {expectations.min_return_fail}%",
            }
        )
        has_fail = True
    elif total_return < expectations.min_return_warn:
        violations.append(
            {
                "type": "return_min",
                "severity": "WARN",
                "message": f"Return {total_return:.1f}% < Warn-Schwelle {expectations.min_return_warn}%",
            }
        )
        has_warn = True

    # 5. Returns (Max)
    if total_return > expectations.max_return_fail:
        violations.append(
            {
                "type": "return_max",
                "severity": "FAIL",
                "message": f"Return {total_return:.1f}% > Fail-Schwelle {expectations.max_return_fail}% (verdächtig hoch)",
            }
        )
        has_fail = True
    elif total_return > expectations.max_return_warn:
        violations.append(
            {
                "type": "return_max",
                "severity": "WARN",
                "message": f"Return {total_return:.1f}% > Warn-Schwelle {expectations.max_return_warn}% (ungewöhnlich)",
            }
        )
        has_warn = True

    # 6. Drawdown
    max_dd = results.get("max_drawdown_pct", 0)
    if max_dd > expectations.max_drawdown_fail:
        violations.append(
            {
                "type": "drawdown",
                "severity": "FAIL",
                "message": f"Drawdown {max_dd:.1f}% > Fail-Schwelle {expectations.max_drawdown_fail}%",
            }
        )
        has_fail = True
    elif max_dd > expectations.max_drawdown_warn:
        violations.append(
            {
                "type": "drawdown",
                "severity": "WARN",
                "message": f"Drawdown {max_dd:.1f}% > Warn-Schwelle {expectations.max_drawdown_warn}%",
            }
        )
        has_warn = True

    # Status bestimmen
    if has_fail:
        status = "FAIL"
    elif has_warn:
        status = "WARN"
    else:
        status = "PASS"

    return status, violations


def main():
    """Main Entry Point."""
    args = parse_args()
    start_time = time.time()

    print("\n" + "=" * 65)
    print("  Peak_Trade Portfolio Smoke Test (v1.1)")
    print("=" * 65)

    # Expectations aufbauen (mit CLI-Overrides)
    expectations = PortfolioExpectations()
    if args.max_runtime:
        expectations.max_runtime_fail = args.max_runtime
    if args.min_trades:
        expectations.min_trades_fail = args.min_trades
    if args.min_return:
        expectations.min_return_fail = args.min_return
    if args.max_return:
        expectations.max_return_fail = args.max_return
    if args.max_drawdown:
        expectations.max_drawdown_fail = args.max_drawdown

    # 1. Portfolio-Config finden
    print(f"\n📂 Suche Portfolio: {args.portfolio_id}")
    config_path = find_portfolio_config(args.portfolio_id)

    if not config_path:
        print(f"❌ Portfolio '{args.portfolio_id}' nicht gefunden in config/portfolios/")
        sys.exit(1)

    print(f"   → Gefunden: {config_path.name}")

    # 2. Config laden
    try:
        config = load_portfolio_config(config_path)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Config: {e}")
        sys.exit(1)

    portfolio = config.get("portfolio", {})
    print(f"   → Name: {portfolio.get('portfolio_name', 'N/A')}")
    print(f"   → Universe: {portfolio.get('universe_id', 'N/A')}")
    print(f"   → Assets: {len(portfolio.get('assets', []))}")

    # 3. Validierung
    print("\n🔍 Validiere Config...")
    errors = validate_portfolio_config(config, verbose=args.verbose)

    if errors:
        print("❌ Validierungsfehler:")
        for err in errors:
            print(f"   • {err}")
        sys.exit(1)

    print("   ✓ Config ist valide")

    if args.validate_only:
        print("\n✅ Validierung erfolgreich (--validate-only)")
        sys.exit(0)

    # 4. Mini-Backtest
    lookback = args.lookback_days or portfolio.get("backtest_defaults", {}).get("lookback_days", 30)
    print(f"\n🧪 Führe Mini-Backtest durch (lookback={lookback}d)...")

    results = run_mini_backtest(config, lookback_days=lookback, verbose=args.verbose)
    runtime_seconds = time.time() - start_time

    # 5. Expectations evaluieren
    print("\n📊 Evaluiere Expectations...")
    status, violations = evaluate_expectations(results, runtime_seconds, expectations, args.verbose)

    # 6. Psychologie-Annotation berechnen
    psychology = derive_psychology(
        total_return_pct=results.get("total_return_pct", 0),
        max_drawdown_pct=results.get("max_drawdown_pct", 0),
        trades_count=results.get("total_trades", 0),
    )

    # 7. Ergebnis ausgeben
    print("\n" + "-" * 65)
    print("ERGEBNIS")
    print("-" * 65)

    print(f"   Portfolio:      {results['portfolio_id']}")
    print(f"   Assets:         {len(results['assets_tested'])}")
    print(f"   Total Trades:   {results['total_trades']}")
    print(f"   Total Return:   {results['total_return_pct']:+.2f}%")
    print(f"   Max Drawdown:   {results['max_drawdown_pct']:.2f}%")
    print(f"   Runtime:        {runtime_seconds:.2f}s")
    print()

    if status == "PASS":
        print("✅ Status: PASS – Alle Expectations erfüllt")
        exit_code = 0
    elif status == "WARN":
        print("⚠️  Status: WARN – Weiche Expectations verletzt")
        exit_code = 2
    else:
        print("❌ Status: FAIL – Harte Expectations verletzt")
        exit_code = 1

    if violations:
        print("\n   Violations:")
        for v in violations:
            icon = "❌" if v["severity"] == "FAIL" else "⚠️"
            print(f"   {icon} [{v['severity']}] {v['message']}")

    # 8. Psychologie-Sektion ausgeben
    print("\n" + "-" * 65)
    print(f"PSYCHOLOGIE: {psychology['level_emoji']} {psychology['level']}")
    print("-" * 65)
    for note in psychology["notes"]:
        print(f"   • {note}")

    # 9. JSON-Summary für maschinelle Verarbeitung (in stdout, markiert)
    import json

    json_summary = {
        "portfolio_id": results["portfolio_id"],
        "status": status,
        "metrics": {
            "total_return_pct": results["total_return_pct"],
            "max_drawdown_pct": results["max_drawdown_pct"],
            "total_trades": results["total_trades"],
            "runtime_seconds": runtime_seconds,
        },
        "psychology": psychology,
        "violations": violations,
    }
    print("\n" + "-" * 65)
    print("JSON_SUMMARY_START")
    print(json.dumps(json_summary, indent=2))
    print("JSON_SUMMARY_END")

    print("\n" + "=" * 65)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

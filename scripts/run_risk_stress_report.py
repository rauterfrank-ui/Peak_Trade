#!/usr/bin/env python3
"""
Peak_Trade Risk Layer v1 - Stress-Testing Report Script
=========================================================
Läuft Stress-Szenarien auf Portfolio-Returns und generiert Report.

Usage:
    python scripts/run_risk_stress_report.py --config config/config.toml
    python scripts/run_risk_stress_report.py --symbol BTC/EUR --days 365
    python scripts/run_risk_stress_report.py --output reports/stress_report.csv
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.peak_config import load_config
from src.risk import StressScenario, run_stress_suite, historical_var, historical_cvar


def load_ohlcv_sample(symbol: str = "BTC/EUR", days: int = 365) -> pd.DataFrame:
    """
    Lädt OHLCV-Sample für Stress-Testing.

    Args:
        symbol: Trading-Symbol
        days: Anzahl Tage zurück

    Returns:
        DataFrame mit OHLCV-Daten

    Note:
        Nutzt vorhandenen Data-Loader falls vorhanden, sonst synthetische Daten.
    """
    try:
        # Versuche, echten Data-Loader zu nutzen
        from src.data.loader import load_market_data

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = load_market_data(
            symbol=symbol, start_date=start_date, end_date=end_date, timeframe="1d"
        )

        if df is not None and not df.empty:
            print(f"✓ Loaded {len(df)} bars for {symbol} (real data)")
            return df

    except (ImportError, Exception) as e:
        print(f"⚠ Could not load real data ({e}), using synthetic data")

    # Fallback: Synthetische Daten
    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
    np.random.seed(42)

    closes = 50000 + np.cumsum(np.random.normal(0, 1000, days))
    closes = np.clip(closes, 10000, 100000)

    df = pd.DataFrame(
        {
            "open": closes + np.random.normal(0, 100, days),
            "high": closes + np.abs(np.random.normal(0, 200, days)),
            "low": closes - np.abs(np.random.normal(0, 200, days)),
            "close": closes,
            "volume": np.random.uniform(100, 1000, days),
        },
        index=dates,
    )

    print(f"✓ Generated {len(df)} synthetic bars")
    return df


def define_stress_scenarios() -> list[StressScenario]:
    """
    Definiert Standard-Stress-Szenarien.

    Returns:
        Liste von StressScenarios
    """
    scenarios = [
        # Baseline
        StressScenario(
            name="baseline",
            kind="shock",
            params={"shock_pct": 0.0},
            description="Keine Änderung (Baseline)",
        ),
        # Shocks
        StressScenario(
            name="crash_10pct",
            kind="shock",
            params={"shock_pct": -0.10, "days": 5},
            description="10% Crash über 5 Tage",
        ),
        StressScenario(
            name="crash_20pct",
            kind="shock",
            params={"shock_pct": -0.20, "days": 5},
            description="20% Crash über 5 Tage",
        ),
        StressScenario(
            name="crash_30pct",
            kind="shock",
            params={"shock_pct": -0.30, "days": 10},
            description="30% Crash über 10 Tage",
        ),
        # Volatility
        StressScenario(
            name="vol_spike_2x",
            kind="vol_spike",
            params={"multiplier": 2.0},
            description="Volatilität 2x",
        ),
        StressScenario(
            name="vol_spike_3x",
            kind="vol_spike",
            params={"multiplier": 3.0},
            description="Volatilität 3x",
        ),
        # Flash Crash
        StressScenario(
            name="flash_crash_20pct",
            kind="flash_crash",
            params={"crash_pct": -0.20, "recovery_days": 10},
            description="20% Flash-Crash + 10-Tage-Recovery",
        ),
        # Regime Bear
        StressScenario(
            name="bear_market_2pct",
            kind="regime_bear",
            params={"drift_pct": -0.02, "duration_days": 60},
            description="Bärenmarkt: -2%/Tag für 60 Tage",
        ),
        # Regime Sideways
        StressScenario(
            name="sideways_2x_chop",
            kind="regime_sideways",
            params={"chop_factor": 2.0, "duration_days": 30},
            description="Seitwärts: 2x Choppiness für 30 Tage",
        ),
    ]

    return scenarios


def compute_baseline_metrics(returns: pd.Series, alpha: float = 0.05) -> dict:
    """
    Berechnet Baseline-Metriken für Returns.

    Args:
        returns: Return-Series
        alpha: VaR/CVaR-Alpha

    Returns:
        Dict mit Metriken
    """
    return {
        "mean": returns.mean(),
        "std": returns.std(),
        "min": returns.min(),
        "max": returns.max(),
        "var_hist": historical_var(returns, alpha),
        "cvar_hist": historical_cvar(returns, alpha),
        "total_return": (1 + returns).prod() - 1,
    }


def format_report(
    results_df: pd.DataFrame, baseline_metrics: dict, symbol: str, alpha: float
) -> str:
    """
    Formatiert Report als Text.

    Args:
        results_df: Stress-Test-Ergebnisse
        baseline_metrics: Baseline-Metriken
        symbol: Trading-Symbol
        alpha: VaR/CVaR-Alpha

    Returns:
        Formatierter Report-String
    """
    lines = []
    lines.append("=" * 80)
    lines.append("PEAK_TRADE RISK LAYER V1 - STRESS-TESTING REPORT")
    lines.append("=" * 80)
    lines.append(f"Symbol: {symbol}")
    lines.append(f"Alpha: {alpha:.2%} (VaR/CVaR Confidence Level)")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Baseline Metrics
    lines.append("BASELINE METRICS (Actual Returns)")
    lines.append("-" * 80)
    lines.append(f"  Mean Return:     {baseline_metrics['mean']:>10.2%}")
    lines.append(f"  Std Deviation:   {baseline_metrics['std']:>10.2%}")
    lines.append(f"  Min Return:      {baseline_metrics['min']:>10.2%}")
    lines.append(f"  Max Return:      {baseline_metrics['max']:>10.2%}")
    lines.append(f"  VaR({alpha:.0%}):         {baseline_metrics['var_hist']:>10.2%}")
    lines.append(f"  CVaR({alpha:.0%}):        {baseline_metrics['cvar_hist']:>10.2%}")
    lines.append(f"  Total Return:    {baseline_metrics['total_return']:>10.2%}")
    lines.append("")

    # Stress Scenarios
    lines.append("STRESS SCENARIOS")
    lines.append("-" * 80)
    lines.append(
        f"{'Scenario':<25} {'VaR':>10} {'CVaR':>10} {'Mean':>10} {'Std':>10} {'Min':>10} {'Total':>10}"
    )
    lines.append("-" * 80)

    for _, row in results_df.iterrows():
        lines.append(
            f"{row['scenario']:<25} "
            f"{row['var']:>9.2%} "
            f"{row['cvar']:>9.2%} "
            f"{row['mean']:>9.2%} "
            f"{row['std']:>9.2%} "
            f"{row['min']:>9.2%} "
            f"{row['total_return']:>9.2%}"
        )

    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Peak_Trade Risk Layer v1 - Stress-Testing Report"
    )
    parser.add_argument(
        "--config", type=str, default="config/config.toml", help="Path to config.toml"
    )
    parser.add_argument(
        "--symbol", type=str, default="BTC/EUR", help="Trading symbol"
    )
    parser.add_argument(
        "--days", type=int, default=365, help="Number of days to load"
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05, help="VaR/CVaR alpha (default: 0.05)"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output CSV path (optional)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("PEAK_TRADE RISK LAYER V1 - STRESS-TESTING REPORT")
    print("=" * 80)
    print(f"Symbol: {args.symbol}")
    print(f"Days: {args.days}")
    print(f"Alpha: {args.alpha:.2%}")
    print("")

    # 1. Load OHLCV Data
    print("📊 Loading OHLCV data...")
    df = load_ohlcv_sample(symbol=args.symbol, days=args.days)

    if df.empty:
        print("❌ Error: No data loaded")
        return 1

    # 2. Compute Returns
    print("📈 Computing returns...")
    returns = df["close"].pct_change().dropna()

    if len(returns) < 30:
        print(f"⚠ Warning: Only {len(returns)} returns available (min 30 recommended)")

    print(f"✓ {len(returns)} returns computed")
    print("")

    # 3. Baseline Metrics
    print("🔍 Computing baseline metrics...")
    baseline_metrics = compute_baseline_metrics(returns, alpha=args.alpha)
    print(f"✓ Baseline VaR({args.alpha:.0%}): {baseline_metrics['var_hist']:.2%}")
    print(f"✓ Baseline CVaR({args.alpha:.0%}): {baseline_metrics['cvar_hist']:.2%}")
    print("")

    # 4. Define Stress Scenarios
    print("💣 Running stress scenarios...")
    scenarios = define_stress_scenarios()
    print(f"✓ {len(scenarios)} scenarios defined")

    # 5. Run Stress Suite
    results_df = run_stress_suite(returns, scenarios, alpha=args.alpha)

    if results_df.empty:
        print("❌ Error: Stress suite returned empty results")
        return 1

    print(f"✓ {len(results_df)} scenarios completed")
    print("")

    # 6. Format Report
    report = format_report(results_df, baseline_metrics, args.symbol, args.alpha)
    print(report)

    # 7. Optional: Save CSV
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        results_df.to_csv(output_path, index=False)
        print(f"\n✓ CSV saved to: {output_path}")

        # Save Text Report too
        txt_path = output_path.with_suffix(".txt")
        txt_path.write_text(report)
        print(f"✓ Text report saved to: {txt_path}")

    print("\n✅ Stress-Testing Report completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())


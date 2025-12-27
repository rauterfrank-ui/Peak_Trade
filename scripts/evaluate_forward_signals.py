#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/evaluate_forward_signals.py
"""
Peak_Trade: Evaluation von Forward-/Paper-Trading-Signalen
===========================================================

Führt einen Paper-Backtest auf historischen Daten basierend auf gespeicherten
Forward-Signalen durch.

Usage:
    python scripts/evaluate_forward_signals.py reports/forward/forward_demo_signals.csv
    python scripts/evaluate_forward_signals.py reports/forward/forward_demo_signals.csv --horizon-bars 1
    python scripts/evaluate_forward_signals.py reports/forward/forward_demo_signals.csv --horizon-bars 5 --output-dir reports/forward
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from src.core.peak_config import load_config
from src.core.experiments import log_generic_experiment
from src.forward.signals import FORWARD_SIGNALS_COLUMNS


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Evaluation von Forward-/Paper-Trading-Signalen.",
    )
    parser.add_argument(
        "signals_csv",
        help="Pfad zur Signal-CSV (erzeugt von generate_forward_signals.py).",
    )
    parser.add_argument(
        "--horizon-bars",
        type=int,
        default=1,
        help="Anzahl Bars nach dem Signaltime, nach der die Position geschlossen wird. Default: 1.",
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/forward",
        help="Zielverzeichnis für Evaluations-Outputs. Default: reports/forward.",
    )
    return parser.parse_args(argv)


def load_signal_df(path: Path | str) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Signals-CSV nicht gefunden: {path}")
    df = pd.read_csv(path)
    # Minimale Spaltenprüfung
    required = {"symbol", "as_of", "direction"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Signals-CSV fehlt Spalten: {missing}")
    return df


def load_price_data(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Lädt Preisdaten für ein Symbol (Dummy-Implementierung analog zu generate_forward_signals.py).

    TODO: Später mit echten Kraken-Daten synchron halten.
    """
    # Symbol-spezifischer Seed
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Preis-Simulation
    if "BTC" in symbol:
        base_price = 50000
        volatility = 0.003
    elif "ETH" in symbol:
        base_price = 3000
        volatility = 0.004
    elif "LTC" in symbol:
        base_price = 100
        volatility = 0.005
    else:
        base_price = 1000
        volatility = 0.003

    trend = np.linspace(0, base_price * 0.06, n_bars)
    cycle = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * base_price * 0.04
    noise = np.random.randn(n_bars).cumsum() * base_price * volatility

    close_prices = base_price + trend + cycle + noise

    df = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.randn(n_bars) * volatility),
            "high": close_prices * (1 + abs(np.random.randn(n_bars)) * volatility * 1.5),
            "low": close_prices * (1 - abs(np.random.randn(n_bars)) * volatility * 1.5),
            "close": close_prices,
            "volume": np.random.randint(10, 100, n_bars),
        },
        index=dates,
    )

    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)

    return df


def evaluate_signals_for_symbol(
    df_sig_sym: pd.DataFrame,
    symbol: str,
    horizon_bars: int,
) -> pd.DataFrame:
    """
    Evaluierung der Signale für ein Symbol.

    Simplifizierte Logik:
    - Entry: nächste Bar nach as_of (Index-Position + 1)
    - Exit: Entry + horizon_bars - 1 (oder letzte verfügbare Bar)
    - Return-Formel:
        long:  (close_exit / close_entry) - 1
        short: (close_entry / close_exit) - 1
        flat:  0
    """
    data = load_price_data(symbol, n_bars=200)
    if data.empty:
        raise ValueError(f"Keine Preisdaten für Symbol {symbol}.")

    if "close" not in data.columns:
        raise ValueError(f"Preisdaten für {symbol} enthalten keine 'close'-Spalte.")

    closes = data["close"]

    rows: List[Dict[str, Any]] = []

    for _, row in df_sig_sym.iterrows():
        as_of = pd.to_datetime(row["as_of"])
        direction = float(row["direction"])

        # Passende Position im Kursindex finden
        # Wir nehmen die erste Bar mit Index >= as_of
        try:
            # Versuche moderne pandas API
            pos = closes.index.get_indexer([as_of], method="backfill")[0]
        except Exception:
            # Fallback für ältere pandas-Versionen
            try:
                pos = closes.index.searchsorted(as_of)
            except Exception:
                continue

        if pos < 0 or pos >= len(closes):
            # Kein passender Punkt -> Signal kann nicht evaluiert werden
            continue

        entry_pos = pos + 1  # nächste Bar nach as_of
        if entry_pos >= len(closes):
            # Keine nächste Bar → nicht auswertbar
            continue

        exit_pos = min(entry_pos + horizon_bars - 1, len(closes) - 1)

        entry_ts = closes.index[entry_pos]
        exit_ts = closes.index[exit_pos]
        entry_price = float(closes.iloc[entry_pos])
        exit_price = float(closes.iloc[exit_pos])

        if direction > 0:
            ret = (exit_price / entry_price) - 1.0
        elif direction < 0:
            ret = (entry_price / exit_price) - 1.0
        else:
            ret = 0.0

        rows.append(
            {
                "symbol": symbol,
                "as_of": as_of,
                "direction": direction,
                "entry_ts": entry_ts,
                "exit_ts": exit_ts,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "horizon_bars": horizon_bars,
                "return": ret,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol",
                "as_of",
                "direction",
                "entry_ts",
                "exit_ts",
                "entry_price",
                "exit_price",
                "horizon_bars",
                "return",
            ]
        )

    return pd.DataFrame(rows)


def compute_eval_stats(df_eval: pd.DataFrame) -> Dict[str, Any]:
    if df_eval.empty:
        return {
            "n_trades": 0,
            "total_return": 0.0,
            "avg_return": 0.0,
            "winrate": None,
            "sharpe": None,
        }

    rets = df_eval["return"].astype(float)
    n = len(rets)
    total_return = float((1.0 + rets).prod() - 1.0)
    avg_return = float(rets.mean())
    winrate = float((rets > 0).mean())

    # sehr einfache Sharpe-Approx (ohne Risk-Free, annualisiert wäre extra)
    std = float(rets.std(ddof=1)) if n > 1 else 0.0
    sharpe_like = float(avg_return / std) if std > 0 else None

    return {
        "n_trades": int(n),
        "total_return": total_return,
        "avg_return": avg_return,
        "winrate": winrate,
        "sharpe": sharpe_like,
    }


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n📊 Peak_Trade Forward Signal Evaluator")
    print("=" * 70)

    cfg = load_config(args.config_path)
    sig_path = Path(args.signals_csv)
    df_sig = load_signal_df(sig_path)

    horizon_bars = args.horizon_bars

    print(f"\n⚙️  Konfiguration:")
    print(f"  Signals:       {sig_path}")
    print(f"  Horizon bars:  {horizon_bars}")
    print(f"  Signale total: {len(df_sig)}")

    # Nach Symbol gruppieren
    all_rows: List[pd.DataFrame] = []
    stats_per_symbol: Dict[str, Dict[str, Any]] = {}

    for symbol, df_sym in df_sig.groupby("symbol"):
        print(f"\n📈 Evaluierung für Symbol: {symbol}")
        df_eval_sym = evaluate_signals_for_symbol(
            df_sig_sym=df_sym,
            symbol=symbol,
            horizon_bars=horizon_bars,
        )
        if df_eval_sym.empty:
            print("  ⚠️  Keine auswertbaren Signale.")
            continue

        stats = compute_eval_stats(df_eval_sym)
        stats_per_symbol[symbol] = stats
        print(f"  Trades:        {stats['n_trades']}")
        print(f"  Total Return:  {stats['total_return']:.4f}")
        print(f"  Avg Return:    {stats['avg_return']:.6f}")
        if stats["winrate"] is not None:
            print(f"  Winrate:       {stats['winrate']:.2%}")
        else:
            print(f"  Winrate:       n/a")
        if stats["sharpe"] is not None:
            print(f"  Sharpe-like:   {stats['sharpe']:.4f}")
        else:
            print(f"  Sharpe-like:   n/a")

        all_rows.append(df_eval_sym)

    if not all_rows:
        print("\n⚠️  Keine auswertbaren Signale gefunden – Evaluation bricht ab.")
        return

    df_eval_all = pd.concat(all_rows, ignore_index=True)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = sig_path.stem
    eval_csv_path = out_dir / f"{base_name}_eval_h{horizon_bars}_{ts_label}.csv"

    df_eval_all.to_csv(eval_csv_path, index=False)
    print(f"\n💾 Forward-Evaluation gespeichert: {eval_csv_path}")

    # Aggregierte Gesamt-Stats über alle Symbole
    overall_stats = compute_eval_stats(df_eval_all)
    print(f"\n📊 Gesamt-Stats über alle Symbole:")
    print("=" * 70)
    print(f"  Trades:        {overall_stats['n_trades']}")
    print(f"  Total Return:  {overall_stats['total_return']:.4f}")
    print(f"  Avg Return:    {overall_stats['avg_return']:.6f}")
    if overall_stats["winrate"] is not None:
        print(f"  Winrate:       {overall_stats['winrate']:.2%}")
    else:
        print(f"  Winrate:       n/a")
    if overall_stats["sharpe"] is not None:
        print(f"  Sharpe-like:   {overall_stats['sharpe']:.4f}")
    else:
        print(f"  Sharpe-like:   n/a")

    # Experiment-Registry-Log
    log_generic_experiment(
        run_type="forward_eval",
        run_name=f"{base_name}_h{horizon_bars}",
        strategy_key=None,  # kann bei Bedarf aus Signals-CSV extrahiert werden
        symbol=None,
        stats={
            "total_return": overall_stats["total_return"],
            "avg_return": overall_stats["avg_return"],
            "winrate": overall_stats["winrate"],
            "sharpe": overall_stats["sharpe"],
            "n_trades": overall_stats["n_trades"],
        },
        report_dir=out_dir,
        report_prefix=f"{base_name}_eval_h{horizon_bars}",
        extra_metadata={
            "runner": "evaluate_forward_signals.py",
            "signals_csv": str(sig_path),
            "horizon_bars": horizon_bars,
            "stats_per_symbol": stats_per_symbol,
            "eval_csv": str(eval_csv_path),
        },
    )
    print(f"\n📝 Forward-Evaluation in Registry geloggt (run_type='forward_eval')")
    print(f"✅ Forward-Evaluation abgeschlossen!\n")


if __name__ == "__main__":
    main()

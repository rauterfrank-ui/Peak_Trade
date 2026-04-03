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
    python scripts/evaluate_forward_signals.py signals.csv --n-bars 200
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Projekt-Root und scripts/-Verzeichnis (shared OHLCV-Loader) zum Python-Path
_root = Path(__file__).resolve().parent.parent
_scripts = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_scripts))

import pandas as pd

from _shared_forward_args import add_shared_ohlcv_cli_group, append_forward_ohlcv_scope_epilog
from _shared_ohlcv_loader import OHLCV_SOURCE_DUMMY, load_ohlcv_with_meta
from _forward_run_manifest import (
    python_version_short,
    try_git_sha,
    write_forward_run_manifest,
)
from src.core.peak_config import load_config
from src.core.experiments import log_generic_experiment


def parse_as_of_to_utc(value: Any) -> pd.Timestamp:
    """
    Parst einen Signal-Zeitstempel aus CSV/Row und liefert einen UTC-``Timestamp``.

    Preisreihen aus ``load_dummy_ohlcv`` nutzen einen UTC-``DatetimeIndex``; ohne
    Normalisierung würden naive ``as_of``-Werte mit tz-aware Indizes schlecht
    vergleichbar sein (pandas-Verhalten / implizite lokale TZ).
    """
    ts = pd.to_datetime(value, utc=True)
    if isinstance(ts, pd.Series):
        raise TypeError("parse_as_of_to_utc erwartet einen Skalar, keine Series.")
    if pd.isna(ts):
        raise ValueError(f"as_of ist kein gültiger Zeitstempel: {value!r}")
    if not isinstance(ts, pd.Timestamp):
        ts = pd.Timestamp(ts)
    if ts.tz is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Peak_Trade: Evaluation von Forward-/Paper-Trading-Signalen.\n\n"
            "NO-LIVE: kein Live-Handel, keine Order-Ausführung; nur Auswertung/Artefakte."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    add_shared_ohlcv_cli_group(parser)
    append_forward_ohlcv_scope_epilog(parser)
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
    df = df.copy()
    df["as_of"] = df["as_of"].apply(parse_as_of_to_utc)
    return df


def _print_ohlcv_load_observability(meta: Dict[str, Any]) -> None:
    """Stdout: J1-Observability für UTC-/Fenster-Debugging (Evaluate-Pfad)."""
    pag = meta.get("kraken_pagination_used")
    if pag is None:
        pag_s = "n/a (dummy)"
    else:
        pag_s = "ja" if pag else "nein"
    sf = meta.get("kraken_bars_shortfall")
    if sf is None:
        sf_s = "n/a (dummy)"
    else:
        sf_s = "ja" if sf else "nein"
    print(
        f"  📡 OHLCV-Load: {meta['symbol']} | Quelle={meta['ohlcv_source']} | "
        f"TF={meta['timeframe']} | n_bars={meta['n_bars_requested']} | "
        f"geladen={meta['bars_loaded']} | Kraken-Pagination={pag_s} | "
        f"Kraken-Shortfall={sf_s}"
    )


def evaluate_signals_for_symbol(
    df_sig_sym: pd.DataFrame,
    symbol: str,
    horizon_bars: int,
    n_bars: int = 200,
    *,
    ohlcv_source: str = OHLCV_SOURCE_DUMMY,
    timeframe: str = "1h",
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluierung der Signale für ein Symbol.

    Simplifizierte Logik:
    - Entry: nächste Bar nach as_of (Index-Position + 1)
    - Exit: Entry + horizon_bars - 1 (oder letzte verfügbare Bar)
    - Return-Formel:
        long:  (close_exit / close_entry) - 1
        short: (close_entry / close_exit) - 1
        flat:  0

    Args:
        n_bars: Länge der OHLCV-Preisreihe (``load_ohlcv_with_meta``).
        ohlcv_source: ``dummy`` | ``kraken`` (mit ``generate_forward_signals`` abstimmen).
        timeframe: Kraken-Timeframe; Dummy siehe Loader.

    Returns:
        (Evaluations-DataFrame, Observability-Dict für Loader/J1).
    """
    data, ohlcv_meta = load_ohlcv_with_meta(
        symbol,
        n_bars=n_bars,
        source=ohlcv_source,
        timeframe=timeframe,
    )
    if data.empty:
        raise ValueError(f"Keine Preisdaten für Symbol {symbol}.")

    if "close" not in data.columns:
        raise ValueError(f"Preisdaten für {symbol} enthalten keine 'close'-Spalte.")

    closes = data["close"]

    rows: List[Dict[str, Any]] = []

    for _, row in df_sig_sym.iterrows():
        as_of = parse_as_of_to_utc(row["as_of"])
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
        return (
            pd.DataFrame(
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
            ),
            ohlcv_meta,
        )

    return pd.DataFrame(rows), ohlcv_meta


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


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.output_dir)
    sig_path = Path(args.signals_csv)
    base_name = sig_path.stem
    manifest_path = out_dir / f"{base_name}_eval_run_manifest.json"

    def write_manifest(
        exit_code: int,
        *,
        df_sig: pd.DataFrame | None = None,
        error: str | None = None,
        eval_csv: str | None = None,
    ) -> None:
        strategy_val: str | None = None
        symbols_val: List[str] = []
        if df_sig is not None and not df_sig.empty:
            if "strategy_key" in df_sig.columns:
                sk = df_sig["strategy_key"].dropna()
                if len(sk):
                    strategy_val = str(sk.iloc[0])
            symbols_val = sorted({str(s) for s in df_sig["symbol"].unique()})
        payload: Dict[str, Any] = {
            "script_name": "evaluate_forward_signals.py",
            "git_sha": try_git_sha(),
            "python_version": python_version_short(),
            "argv": list(sys.argv),
            "config_path": str(args.config_path),
            "strategy": strategy_val,
            "symbols": symbols_val,
            "signals_csv": str(sig_path),
            "ohlcv_source": args.ohlcv_source,
            "n_bars": args.n_bars,
            "timeframe": args.timeframe,
            "horizon_bars": args.horizon_bars,
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "exit_code": exit_code,
        }
        if error is not None:
            payload["error"] = error
        if eval_csv is not None:
            payload["eval_csv"] = eval_csv
        write_forward_run_manifest(manifest_path, payload)

    print("\n📊 Peak_Trade Forward Signal Evaluator")
    print("=" * 70)

    df_sig: pd.DataFrame | None = None

    try:
        load_config(args.config_path)
    except (ValueError, FileNotFoundError) as e:
        print(f"\n❌ {e}", file=sys.stderr)
        write_manifest(1, error=str(e))
        return 1
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler (Config): {e}", file=sys.stderr)
        write_manifest(2, error=str(e))
        return 2

    horizon_bars = args.horizon_bars
    n_bars = args.n_bars
    if n_bars < 1:
        msg = "--n-bars muss >= 1 sein."
        print(f"\n❌ {msg}", file=sys.stderr)
        write_manifest(1, error=msg)
        return 1

    try:
        df_sig = load_signal_df(sig_path)
    except (ValueError, FileNotFoundError) as e:
        print(f"\n❌ {e}", file=sys.stderr)
        write_manifest(1, error=str(e))
        return 1
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler (Signals-CSV): {e}", file=sys.stderr)
        write_manifest(2, error=str(e))
        return 2

    if df_sig.empty:
        msg = "Signals-CSV enthält keine Zeilen."
        print(f"\n❌ {msg}", file=sys.stderr)
        write_manifest(1, df_sig=df_sig, error=msg)
        return 1

    print(f"\n⚙️  Konfiguration:")
    print(f"  Signals:       {sig_path}")
    print(f"  Horizon bars:  {horizon_bars}")
    print(f"  n-bars (OHLCV): {n_bars}")
    print(f"  Timeframe:      {args.timeframe}")
    print(f"  OHLCV-Quelle:  {args.ohlcv_source}")
    print(f"  Signale total: {len(df_sig)}")

    # Nach Symbol gruppieren
    all_rows: List[pd.DataFrame] = []
    stats_per_symbol: Dict[str, Dict[str, Any]] = {}
    ohlcv_load_by_symbol: Dict[str, Dict[str, Any]] = {}

    try:
        for symbol, df_sym in df_sig.groupby("symbol"):
            print(f"\n📈 Evaluierung für Symbol: {symbol}")
            df_eval_sym, ohlcv_meta = evaluate_signals_for_symbol(
                df_sig_sym=df_sym,
                symbol=symbol,
                horizon_bars=horizon_bars,
                n_bars=n_bars,
                ohlcv_source=args.ohlcv_source,
                timeframe=args.timeframe,
            )
            ohlcv_load_by_symbol[symbol] = ohlcv_meta
            _print_ohlcv_load_observability(ohlcv_meta)
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
            msg = "Keine auswertbaren Signale (fachlich)."
            print(f"\n⚠️  {msg} Evaluation beendet.")
            write_manifest(1, df_sig=df_sig, error=msg)
            return 1

        df_eval_all = pd.concat(all_rows, ignore_index=True)

        out_dir.mkdir(parents=True, exist_ok=True)

        ts_label = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
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
                "n_bars": n_bars,
                "ohlcv_source": args.ohlcv_source,
                "timeframe": args.timeframe,
                "ohlcv_load_by_symbol": ohlcv_load_by_symbol,
                "stats_per_symbol": stats_per_symbol,
                "eval_csv": str(eval_csv_path),
            },
        )
        print(f"\n📝 Forward-Evaluation in Registry geloggt (run_type='forward_eval')")
        print(f"✅ Forward-Evaluation abgeschlossen!\n")

        write_manifest(0, df_sig=df_sig, eval_csv=str(eval_csv_path))
        return 0

    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        write_manifest(2, df_sig=df_sig if df_sig is not None else None, error=str(e))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/generate_forward_signals.py
"""
Peak_Trade: Forward-/Paper-Trading-Signale für ein Symbol-Universum erzeugen
=============================================================================

Erzeugt Forward-Signale für eine Strategie über ein Symbol-Universum.
Die Signale werden als CSV gespeichert und in der Experiment-Registry geloggt.

Usage:
    python scripts/generate_forward_signals.py --strategy ma_crossover
    python scripts/generate_forward_signals.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR
    python scripts/generate_forward_signals.py --strategy ma_crossover --run-name forward_daily_2025-12-04
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Projekt-Root und scripts/-Verzeichnis (shared loader) zum Python-Path
_root = Path(__file__).resolve().parent.parent
_scripts = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_scripts))

import pandas as pd

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import log_generic_experiment
from src.forward.signals import ForwardSignal, save_signals_to_csv
from src.strategies.registry import create_strategy_from_config, get_available_strategy_keys
from src.analytics.risk_monitor import (
    RiskPolicy,
    load_experiments_df as load_experiments_df_risk,
    filter_by_lookback,
    annotate_runs_with_risk,
    aggregate_strategy_risk,
)
from src.analytics.filter_flow import SelectionPolicy, build_strategy_selection
from _shared_forward_args import add_shared_ohlcv_cli_group, append_forward_ohlcv_scope_epilog
from _shared_ohlcv_loader import OHLCV_SOURCE_DUMMY, load_ohlcv_with_meta
from _forward_run_manifest import (
    compute_deterministic_run_id,
    python_version_short,
    try_git_sha,
    write_forward_run_manifest,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Peak_Trade: Forward-/Paper-Trading-Signale für ein Symbol-Universum erzeugen.\n\n"
            "NO-LIVE: kein Live-Handel, keine Order-Ausführung; nur Signale/Artefakte."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--strategy",
        required=True,
        help="Strategy-Key (wie in der Registry), z.B. ma_crossover.",
    )
    parser.add_argument(
        "--symbols",
        help=(
            "Kommagetrennte Liste von Symbolen, z.B. 'BTC/EUR,ETH/EUR'. "
            "Wenn nicht gesetzt, wird versucht, [scan].universe aus config.toml zu verwenden."
        ),
    )
    parser.add_argument(
        "--run-name",
        help="Name dieses Forward-Runs (z.B. forward_daily_2025-12-04).",
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/forward",
        help="Zielverzeichnis für Signal-CSV (Default: reports/forward).",
    )
    parser.add_argument(
        "--enforce-selection",
        action="store_true",
        help=(
            "Wenn gesetzt, wird der angegebene Strategy-Key gegen den Filter-Flow geprüft "
            "und nur zugelassen, wenn selection_status='APPROVED' ist."
        ),
    )
    add_shared_ohlcv_cli_group(parser)
    append_forward_ohlcv_scope_epilog(parser)
    return parser.parse_args(argv)


def format_as_of_iso_utc(ts: Any) -> str:
    """
    Wandelt einen Strategie-/Daten-Index-Zeitstempel in ISO-8601 **UTC** mit ``Z``-Suffix.

    Gleiche Sekundenauflösung wie ``generated_at``; konsistent mit ``evaluate_forward_signals.parse_as_of_to_utc``.
    """
    t = pd.Timestamp(ts)
    if pd.isna(t):
        raise ValueError(f"as_of-Zeitstempel ungültig: {ts!r}")
    if t.tz is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _print_ohlcv_load_observability(
    meta: Dict[str, Any], *, run_id: str | None = None
) -> None:
    """Stdout: J1-Observability für UTC-/Fenster-Debugging (Generate-Pfad)."""
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
    tail = (
        f"Kraken-Shortfall={sf_s}"
        + (f" | run_id={run_id}" if run_id else "")
    )
    print(
        f"  📡 OHLCV-Load: {meta['symbol']} | Quelle={meta['ohlcv_source']} | "
        f"TF={meta['timeframe']} | n_bars={meta['n_bars_requested']} | "
        f"geladen={meta['bars_loaded']} | Kraken-Pagination={pag_s} | "
        f"{tail}"
    )


def load_data_for_symbol(
    symbol: str,
    n_bars: int = 200,
    *,
    ohlcv_source: str = OHLCV_SOURCE_DUMMY,
    timeframe: str = "1h",
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Lädt Daten für ein bestimmtes Symbol.

    J1 Slice 1–3: Dummy; J1 Slice 4: optional Kraken über ``load_ohlcv_with_meta`` (gleicher Vertrag).

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl Bars
        ohlcv_source: ``dummy`` | ``kraken`` (CLI: ``--ohlcv-source``).
        timeframe: Kraken-Timeframe; Dummy bleibt 1h-synthetisch (siehe Loader).

    Returns:
        (DataFrame mit OHLCV-Daten, Observability-Dict für Loader/J1)
    """
    return load_ohlcv_with_meta(symbol, n_bars=n_bars, source=ohlcv_source, timeframe=timeframe)


def determine_universe(cfg: Any, symbols_arg: str | None) -> List[str]:
    if symbols_arg:
        return [s.strip() for s in symbols_arg.split(",") if s.strip()]

    # Fallback: [scan].universe aus config.toml
    universe = cfg.get("scan.universe", [])
    if not universe:
        raise ValueError(
            "Keine Symbole angegeben und [scan].universe in config.toml ist leer. "
            "Bitte --symbols setzen oder scan.universe konfigurieren."
        )
    return list(universe)


def enforce_strategy_selection(cfg: PeakConfig, strategy_key: str) -> None:
    """
    Prüft, ob eine Strategie laut Filter-Flow als APPROVED gilt.
    Falls nicht, wird eine ValueError geworfen.
    """
    risk_policy = RiskPolicy.from_config(cfg)
    sel_policy = SelectionPolicy.from_config(cfg)

    df = load_experiments_df_risk()
    df = filter_by_lookback(df, risk_policy)
    if df.empty:
        raise ValueError(
            "Filter-Flow Enforcement: Keine Experimente im Lookback – kann Strategie nicht bewerten."
        )

    df_runs = annotate_runs_with_risk(df, risk_policy)
    df_strat_risk = aggregate_strategy_risk(df_runs, risk_policy)

    df_sel = build_strategy_selection(df_runs, df_strat_risk, sel_policy)

    row = df_sel[df_sel["strategy_key"] == strategy_key]
    if row.empty:
        raise ValueError(
            f"Filter-Flow Enforcement: Strategy-Key {strategy_key!r} hat keine Daten im Lookback."
        )

    status = row["selection_status"].iloc[0]
    reasons = row["selection_reasons"].iloc[0]
    if status != "APPROVED":
        raise ValueError(
            f"Filter-Flow Enforcement: Strategy-Key {strategy_key!r} ist nicht APPROVED "
            f"(selection_status={status}, reasons={reasons})."
        )

    print(
        f"Filter-Flow Enforcement: Strategy-Key {strategy_key!r} ist APPROVED (reasons={reasons})."
    )


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.output_dir)
    strategy_key = args.strategy
    run_name: str | None = None
    universe: List[str] = []

    def manifest_path() -> Path:
        if run_name:
            return out_dir / f"{run_name}_run_manifest.json"
        return out_dir / "generate_forward_run_manifest.json"

    def write_manifest(
        exit_code: int,
        *,
        universe_override: List[str] | None = None,
        error: str | None = None,
        output_csv: str | None = None,
    ) -> None:
        sym = universe_override if universe_override is not None else universe
        payload: Dict[str, Any] = {
            "script_name": "generate_forward_signals.py",
            "git_sha": try_git_sha(),
            "python_version": python_version_short(),
            "argv": list(sys.argv),
            "config_path": str(args.config_path),
            "strategy": strategy_key,
            "symbols": sym,
            "ohlcv_source": args.ohlcv_source,
            "n_bars": args.n_bars,
            "timeframe": args.timeframe,
            "run_name": run_name,
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "exit_code": exit_code,
        }
        if error is not None:
            payload["error"] = error
        if output_csv is not None:
            payload["output_csv"] = output_csv
        payload["run_id"] = compute_deterministic_run_id(
            script_name=payload["script_name"],
            argv=payload["argv"],
            config_path=str(payload["config_path"]),
            git_sha=payload.get("git_sha"),
        )
        write_forward_run_manifest(manifest_path(), payload)

    print("\n🔮 Peak_Trade Forward Signal Generator")
    print("=" * 70)

    try:
        cfg = load_config(args.config_path)

        available = get_available_strategy_keys()
        if strategy_key not in available:
            raise ValueError(f"Unbekannter Strategy-Key {strategy_key!r}. Verfügbar: {available}")

        # Filter-Flow Enforcement (optional)
        if args.enforce_selection:
            enforce_strategy_selection(cfg, strategy_key)

        universe = determine_universe(cfg, args.symbols)
        run_name = (
            args.run_name
            or f"forward_{strategy_key}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )

        _git_for_run_id = try_git_sha()
        deterministic_run_id = compute_deterministic_run_id(
            script_name="generate_forward_signals.py",
            argv=list(sys.argv),
            config_path=str(args.config_path),
            git_sha=_git_for_run_id,
        )

        print(f"\n⚙️  Konfiguration:")
        print(f"  Strategy:      {strategy_key}")
        print(f"  Universe:      {universe}")
        print(f"  Run-Name:      {run_name}")
        print(f"  Bars:          {args.n_bars}")
        print(f"  Timeframe:     {args.timeframe}")
        print(f"  OHLCV-Quelle:  {args.ohlcv_source}")

        signals: List[ForwardSignal] = []
        ohlcv_load_by_symbol: Dict[str, Dict[str, Any]] = {}

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for symbol in universe:
            print(f"\n📊 Verarbeite Symbol: {symbol}")
            data, ohlcv_meta = load_data_for_symbol(
                symbol,
                n_bars=args.n_bars,
                ohlcv_source=args.ohlcv_source,
                timeframe=args.timeframe,
            )
            ohlcv_load_by_symbol[symbol] = ohlcv_meta
            _print_ohlcv_load_observability(
                ohlcv_meta, run_id=deterministic_run_id
            )
            if data.empty:
                print(f"  ⚠️  Keine Daten für {symbol}, überspringe.")
                continue

            strategy = create_strategy_from_config(strategy_key, cfg)

            if not hasattr(strategy, "generate_signals"):
                raise AttributeError(
                    f"Strategy {strategy!r} hat keine Methode generate_signals(data). "
                    "Bitte sicherstellen, dass die Strategie diese API unterstützt."
                )

            # Vollständige Signale berechnen
            signals_series = strategy.generate_signals(data)
            if signals_series is None or signals_series.empty:
                print(f"  ⚠️  generate_signals() liefert keine Signale für {symbol}, überspringe.")
                continue

            # Letztes Signal als Forward-Signal verwenden
            last_ts = signals_series.index[-1]
            last_val = float(signals_series.iloc[-1])

            print(f"  ✅ Letztes Signal: {last_val} @ {last_ts}")

            sig = ForwardSignal(
                generated_at=generated_at,
                as_of=format_as_of_iso_utc(last_ts),
                strategy_key=strategy_key,
                run_name=run_name,
                symbol=symbol,
                direction=last_val,
                size_hint=None,
                comment=None,
                extra={
                    "raw_last_signal": last_val,
                },
            )
            signals.append(sig)

        if not signals:
            print("\n⚠️  Keine Forward-Signale erzeugt – nichts zu speichern.")
            write_manifest(1)
            return 1

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{run_name}_signals.csv"

        df_signals = save_signals_to_csv(signals, out_path)
        print(f"\n💾 Forward-Signale gespeichert: {out_path}")
        print(f"\n📋 Generierte Signale:")
        print(df_signals.to_string(index=False))

        # Experiment-Registry-Log (ohne klassische Backtest-Stats)
        log_generic_experiment(
            run_type="forward_signals",
            run_name=run_name,
            strategy_key=strategy_key,
            symbol=None,  # mehrere Symbole → im metadata-Block
            stats=None,
            report_dir=out_dir,
            report_prefix=run_name,
            extra_metadata={
                "runner": "generate_forward_signals.py",
                "universe": universe,
                "signal_csv": str(out_path),
                "n_signals": len(signals),
                "ohlcv_source": args.ohlcv_source,
                "timeframe": args.timeframe,
                "ohlcv_load_by_symbol": ohlcv_load_by_symbol,
            },
        )
        print(f"\n📝 Forward-Signal-Run in Registry geloggt (run_type='forward_signals')")
        print(f"✅ Forward-Signal-Generierung abgeschlossen!\n")

        write_manifest(0, output_csv=str(out_path))
        return 0

    except (ValueError, FileNotFoundError, AttributeError) as e:
        print(f"\n❌ {e}", file=sys.stderr)
        write_manifest(1, error=str(e))
        return 1
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        write_manifest(2, error=str(e))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

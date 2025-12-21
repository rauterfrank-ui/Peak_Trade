#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/report_paper_risk.py
"""
Peak_Trade: Paper-Risk-Dashboard (HTML) fuer einen Paper-Trade-Run.

Erzeugt ein HTML-Dashboard mit:
- Trading-Aktivitaet (Anzahl Orders, Notional)
- Fees & Slippage
- PnL-Struktur (Realized, Unrealized, Net)
- Symbol-Exposures

Usage:
    python scripts/report_paper_risk.py --run-name paper_fees_demo
    python scripts/report_paper_risk.py --trades reports/paper/paper_trades_...csv
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import sys

import numpy as np
import pandas as pd

# Pfad-Setup wie in anderen Scripts
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import EXPERIMENTS_CSV, log_generic_experiment


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Paper-Risk-Dashboard (HTML) fuer einen Paper-Trade-Run.",
    )
    parser.add_argument(
        "--run-name",
        help=(
            "Name eines paper_trade-Runs aus der Experiment-Registry. "
            "Wenn gesetzt, werden trades/positions aus der Registry gelesen."
        ),
    )
    parser.add_argument(
        "--trades",
        dest="trades_csv",
        help=(
            "Pfad zur paper_trades-CSV (z.B. reports/paper/paper_trades_...csv). "
            "Wenn gesetzt, hat Vorrang vor --run-name."
        ),
    )
    parser.add_argument(
        "--positions",
        dest="positions_csv",
        help=(
            "Pfad zur paper_positions-CSV (z.B. reports/paper/paper_positions_...csv). "
            "Wenn nicht gesetzt, wird versucht, diesen Pfad aus trades-Name abzuleiten "
            "(trades_ -> positions_)."
        ),
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/paper",
        help="Verzeichnis fuer den HTML-Report (Default: reports/paper).",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=20,
        help="Maximale Anzahl Symbole in den Tabellen (Default: 20).",
    )
    parser.add_argument(
        "--run-label",
        help=(
            "Optionaler Label fuer den Report (z.B. 'paper_fees_demo'). "
            "Wenn nicht gesetzt, wird aus run_name oder trades-CSV abgeleitet."
        ),
    )
    return parser.parse_args(argv)


def _resolve_from_experiments(run_name: str) -> Tuple[Path, Optional[Path]]:
    """
    Findet trades/positions-CSV fuer einen paper_trade-Run ueber die Registry.
    Erwartet, dass die Registry Spalten 'run_type', 'run_name',
    sowie 'metadata_json' enthaelt (dort 'trades_csv' und 'positions_csv').
    """
    import json

    df = pd.read_csv(EXPERIMENTS_CSV)

    if "run_type" not in df.columns or "run_name" not in df.columns:
        raise SystemExit(
            f"Experiment-Registry {EXPERIMENTS_CSV} enthaelt nicht die Spalten 'run_type' und 'run_name'."
        )

    mask = (df["run_type"] == "paper_trade") & (df["run_name"] == run_name)
    df_sel = df[mask].copy()

    if df_sel.empty:
        raise SystemExit(
            f"Kein paper_trade-Run mit run_name={run_name!r} in Registry {EXPERIMENTS_CSV} gefunden."
        )

    # Falls mehrere Eintraege existieren: den letzten (neuester)
    if "timestamp" in df_sel.columns:
        df_sel = df_sel.sort_values(by="timestamp")
    row = df_sel.iloc[-1]

    # Parse metadata_json to get trades_csv and positions_csv
    trades_path: Optional[Path] = None
    positions_path: Optional[Path] = None

    if "metadata_json" in row.index and not pd.isna(row["metadata_json"]):
        try:
            metadata = json.loads(row["metadata_json"])
            if "trades_csv" in metadata:
                trades_path = Path(str(metadata["trades_csv"])).expanduser()
            if "positions_csv" in metadata:
                positions_path = Path(str(metadata["positions_csv"])).expanduser()
        except (json.JSONDecodeError, TypeError):
            pass

    if trades_path is None:
        raise SystemExit(
            "Registry-Eintrag enthaelt keine 'trades_csv' in metadata_json. "
            "Bitte trades/positions-CSV manuell per --trades/--positions angeben."
        )

    return trades_path, positions_path


def _infer_positions_from_trades(trades_path: Path) -> Optional[Path]:
    """
    Versucht, aus dem Dateinamen der Trades-CSV die Positions-CSV herzuleiten
    (paper_trades_... -> paper_positions_...).
    """
    stem = trades_path.name
    if "trades_" in stem:
        positions_name = stem.replace("trades_", "positions_", 1)
        candidate = trades_path.with_name(positions_name)
        if candidate.is_file():
            return candidate
    return None


def _load_trades_positions(
    trades_path: Path,
    positions_path: Optional[Path],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not trades_path.is_file():
        raise SystemExit(f"Trades-CSV nicht gefunden: {trades_path}")

    trades_df = pd.read_csv(trades_path)

    if positions_path is None:
        positions_path = _infer_positions_from_trades(trades_path)

    if positions_path is not None and positions_path.is_file():
        positions_df = pd.read_csv(positions_path)
    else:
        positions_df = pd.DataFrame(
            columns=[
                "symbol",
                "quantity",
                "avg_price",
                "last_price",
                "market_value",
                "unrealized_pnl",
                "realized_pnl",
            ]
        )

    return trades_df, positions_df


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def compute_summary(
    trades_df: pd.DataFrame,
    positions_df: pd.DataFrame,
) -> dict:
    """
    Berechnet zentrale Kennzahlen fuer einen Paper-Run.
    """
    df_t = trades_df.copy()
    df_p = positions_df.copy()

    # Notional & Fees
    if "notional" in df_t.columns:
        notional_abs = _to_float(df_t["notional"]).abs()
    else:
        notional_abs = pd.Series([], dtype=float)

    total_notional = float(notional_abs.sum()) if not notional_abs.empty else 0.0
    avg_notional = float(notional_abs.mean()) if not notional_abs.empty else 0.0
    max_notional = float(notional_abs.max()) if not notional_abs.empty else 0.0

    if "fee" in df_t.columns:
        total_fees = float(_to_float(df_t["fee"]).fillna(0.0).sum())
    else:
        total_fees = 0.0

    # Slippage-Stats
    if "slippage_bps" in df_t.columns:
        slippage = _to_float(df_t["slippage_bps"]).dropna()
        if not slippage.empty:
            slippage_mean = float(slippage.mean())
            slippage_min = float(slippage.min())
            slippage_max = float(slippage.max())
        else:
            slippage_mean = slippage_min = slippage_max = float("nan")
    else:
        slippage_mean = slippage_min = slippage_max = float("nan")

    # Positions-Stats
    if not df_p.empty:
        market_value = float(_to_float(df_p["market_value"]).fillna(0.0).sum())
        realized_pnl_total = float(_to_float(df_p["realized_pnl"]).fillna(0.0).sum())
        unrealized_pnl_total = float(_to_float(df_p["unrealized_pnl"]).fillna(0.0).sum())
        n_positions = int(len(df_p))
    else:
        market_value = 0.0
        realized_pnl_total = 0.0
        unrealized_pnl_total = 0.0
        n_positions = 0

    realized_pnl_net = realized_pnl_total - total_fees

    return {
        "n_orders": int(len(df_t)),
        "n_positions": n_positions,
        "total_notional": total_notional,
        "avg_notional": avg_notional,
        "max_notional": max_notional,
        "total_fees": total_fees,
        "slippage_mean_bps": slippage_mean,
        "slippage_min_bps": slippage_min,
        "slippage_max_bps": slippage_max,
        "market_value": market_value,
        "realized_pnl_total": realized_pnl_total,
        "unrealized_pnl_total": unrealized_pnl_total,
        "realized_pnl_net": realized_pnl_net,
    }


def build_exposure_table(
    positions_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Baut eine Exposures-Tabelle auf Basis der Positions-CSV.
    """
    if positions_df.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "quantity",
                "avg_price",
                "last_price",
                "market_value",
                "gross_exposure",
                "exposure_pct",
                "realized_pnl",
                "unrealized_pnl",
            ]
        )

    df = positions_df.copy()
    for col in [
        "quantity",
        "avg_price",
        "last_price",
        "market_value",
        "realized_pnl",
        "unrealized_pnl",
    ]:
        if col in df.columns:
            df[col] = _to_float(df[col])

    df["gross_exposure"] = df["market_value"].abs()
    total_gross = float(df["gross_exposure"].sum()) if df["gross_exposure"].sum() != 0 else 1.0
    df["exposure_pct"] = df["gross_exposure"] / total_gross

    cols = [
        "symbol",
        "quantity",
        "avg_price",
        "last_price",
        "market_value",
        "gross_exposure",
        "exposure_pct",
        "realized_pnl",
        "unrealized_pnl",
    ]
    for col in cols:
        if col not in df.columns:
            df[col] = np.nan

    df = df[cols].sort_values(by="gross_exposure", ascending=False)
    return df


def build_symbol_trade_stats(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregiert Trades pro Symbol:
    - Anzahl Trades
    - Gesamt-Notional
    - Durchschnitts-Notional
    - Gesamt-Fees
    - durchschnittliche Slippage (bps)
    """
    if trades_df.empty or "symbol" not in trades_df.columns:
        return pd.DataFrame(
            columns=[
                "symbol",
                "n_trades",
                "total_notional",
                "avg_notional",
                "total_fees",
                "avg_slippage_bps",
            ]
        )

    df = trades_df.copy()

    if "notional" in df.columns:
        df["notional_abs"] = _to_float(df["notional"]).abs()
    else:
        df["notional_abs"] = 0.0

    if "fee" in df.columns:
        df["fee"] = _to_float(df["fee"]).fillna(0.0)
    else:
        df["fee"] = 0.0

    if "slippage_bps" in df.columns:
        df["slippage_bps"] = _to_float(df["slippage_bps"])
    else:
        df["slippage_bps"] = np.nan

    grouped = df.groupby("symbol")

    records = []
    for symbol, grp in grouped:
        n_trades = int(len(grp))
        total_notional = float(grp["notional_abs"].sum())
        avg_notional = float(grp["notional_abs"].mean()) if n_trades > 0 else 0.0
        total_fees = float(grp["fee"].sum())
        sl = grp["slippage_bps"].dropna()
        avg_slippage_bps = float(sl.mean()) if not sl.empty else float("nan")

        records.append(
            {
                "symbol": symbol,
                "n_trades": n_trades,
                "total_notional": total_notional,
                "avg_notional": avg_notional,
                "total_fees": total_fees,
                "avg_slippage_bps": avg_slippage_bps,
            }
        )

    df_out = pd.DataFrame(records)
    return df_out.sort_values(by="total_notional", ascending=False)


def _df_to_html_table(df: pd.DataFrame, table_class: str = "table") -> str:
    if df.empty:
        return "<p><em>Keine Daten.</em></p>"

    return df.to_html(
        index=False,
        border=0,
        classes=table_class,
        float_format=lambda x: f"{x:.6g}",
    )


def build_html_dashboard(
    run_label: str,
    cfg: PeakConfig,
    trades_path: Path,
    positions_path: Optional[Path],
    summary: dict,
    exposure_df: pd.DataFrame,
    symbol_stats_df: pd.DataFrame,
    trades_df: pd.DataFrame,
) -> str:
    base_currency = str(cfg.get("live.base_currency", "EUR"))
    ts_now = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    html_exposure = _df_to_html_table(exposure_df, "paper-table paper-table-exposure")
    html_symbol_stats = _df_to_html_table(symbol_stats_df, "paper-table paper-table-symbols")

    # Fuer einen groben Blick: nur die ersten 50 Trades anzeigen
    trades_preview = trades_df.copy()
    if len(trades_preview) > 50:
        trades_preview = trades_preview.head(50)
    html_trades = _df_to_html_table(trades_preview, "paper-table paper-table-trades")

    # Determine highlight class for realized_pnl_net
    pnl_class = "highlight-good" if summary["realized_pnl_net"] >= 0 else "highlight-bad"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Peak_Trade - Paper Risk Dashboard - {run_label}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 2rem;
            background-color: #111;
            color: #eee;
        }}
        h1, h2, h3 {{
            color: #fff;
        }}
        a {{
            color: #4ea1ff;
        }}
        .meta {{
            margin-bottom: 1.5rem;
        }}
        .meta p {{
            margin: 0.2rem 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background-color: #1a1a1a;
            border-radius: 0.75rem;
            padding: 1rem 1.2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .card h3 {{
            margin-top: 0;
            margin-bottom: 0.4rem;
        }}
        .card p {{
            margin: 0.2rem 0;
        }}
        .section {{
            margin-bottom: 2.5rem;
        }}
        table.paper-table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 1200px;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }}
        table.paper-table th, table.paper-table td {{
            border: 1px solid #444;
            padding: 0.35rem 0.5rem;
        }}
        table.paper-table th {{
            background-color: #222;
        }}
        .highlight-good {{
            color: #8df7a0;
        }}
        .highlight-bad {{
            color: #ff8a8a;
        }}
        code {{
            background-color: #222;
            padding: 0.15rem 0.3rem;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Peak_Trade - Paper Risk Dashboard</h1>

    <div class="meta">
        <p><strong>Run:</strong> {run_label}</p>
        <p><strong>Base Currency:</strong> {base_currency}</p>
        <p><strong>Trades CSV:</strong> {trades_path}</p>
        <p><strong>Positions CSV:</strong> {positions_path or "n/a"}</p>
        <p><strong>Generated at (UTC):</strong> {ts_now}</p>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Volumen & Aktivitaet</h3>
            <p><strong>Anzahl Orders:</strong> {summary["n_orders"]}</p>
            <p><strong>Anzahl Positionen:</strong> {summary["n_positions"]}</p>
            <p><strong>Total Notional:</strong> {summary["total_notional"]:.2f} {base_currency}</p>
            <p><strong>Avg Notional pro Trade:</strong> {summary["avg_notional"]:.2f} {base_currency}</p>
            <p><strong>Max Notional pro Trade:</strong> {summary["max_notional"]:.2f} {base_currency}</p>
        </div>
        <div class="card">
            <h3>PnL & Fees</h3>
            <p><strong>Realized PnL (Price):</strong> {summary["realized_pnl_total"]:.2f} {base_currency}</p>
            <p><strong>Total Fees:</strong> {summary["total_fees"]:.2f} {base_currency}</p>
            <p><strong>Realized PnL (Netto):</strong> <span class="{pnl_class}">{summary["realized_pnl_net"]:.2f} {base_currency}</span></p>
            <p><strong>Unrealized PnL:</strong> {summary["unrealized_pnl_total"]:.2f} {base_currency}</p>
            <p><strong>Market Value:</strong> {summary["market_value"]:.2f} {base_currency}</p>
        </div>
        <div class="card">
            <h3>Slippage</h3>
            <p><strong>Avg Slippage:</strong> {summary["slippage_mean_bps"]:.2f} bp</p>
            <p><strong>Min Slippage:</strong> {summary["slippage_min_bps"]:.2f} bp</p>
            <p><strong>Max Slippage:</strong> {summary["slippage_max_bps"]:.2f} bp</p>
            <p><small>bp = Basis-Punkte (1 bp = 0,01%)</small></p>
        </div>
    </div>

    <div class="section">
        <h2>1. Positions-Exposures</h2>
        <p>Offene Positionen (falls vorhanden), sortiert nach gross_exposure.</p>
        {html_exposure}
    </div>

    <div class="section">
        <h2>2. Symbol-Statistiken (Trades)</h2>
        <p>Aggregierte Trading-Aktivitaet pro Symbol.</p>
        {html_symbol_stats}
    </div>

    <div class="section">
        <h2>3. Trade-Preview</h2>
        <p>Erste 50 Trades dieses Paper-Runs.</p>
        {html_trades}
    </div>
</body>
</html>
"""


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    if not args.trades_csv and not args.run_name:
        raise SystemExit(
            "Bitte entweder --trades <pfad> oder --run-name <paper_trade_run_name> angeben."
        )

    cfg = load_config(args.config_path)

    # trades/positions aufloesen
    trades_path: Path
    positions_path: Optional[Path] = None

    if args.trades_csv:
        trades_path = Path(args.trades_csv)
        positions_path = Path(args.positions_csv) if args.positions_csv else None
    else:
        trades_path, positions_path = _resolve_from_experiments(args.run_name)

    trades_df, positions_df = _load_trades_positions(trades_path, positions_path)

    if trades_df.empty:
        print("Trades-CSV enthaelt keine Zeilen - nichts zu reporten.")
        return

    summary = compute_summary(trades_df, positions_df)
    exposure_df = build_exposure_table(positions_df)
    symbol_stats_df = build_symbol_trade_stats(trades_df)

    # Run-Label bestimmen
    if args.run_label:
        run_label = args.run_label
    elif args.run_name:
        run_label = args.run_name
    else:
        run_label = trades_path.stem

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    html = build_html_dashboard(
        run_label=run_label,
        cfg=cfg,
        trades_path=trades_path,
        positions_path=positions_path,
        summary=summary,
        exposure_df=exposure_df.head(args.max_symbols),
        symbol_stats_df=symbol_stats_df.head(args.max_symbols),
        trades_df=trades_df,
    )

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    html_path = out_dir / f"paper_risk_{run_label}_{ts_label}.html"
    html_path.write_text(html, encoding="utf-8")

    print(f"\nPaper-Risk-Dashboard gespeichert unter: {html_path}")

    # Experiment-Logging
    stats = {
        "n_orders": summary["n_orders"],
        "n_positions": summary["n_positions"],
        "total_notional": summary["total_notional"],
        "avg_notional": summary["avg_notional"],
        "max_notional": summary["max_notional"],
        "total_fees": summary["total_fees"],
        "realized_pnl_total": summary["realized_pnl_total"],
        "realized_pnl_net": summary["realized_pnl_net"],
        "unrealized_pnl_total": summary["unrealized_pnl_total"],
        "market_value": summary["market_value"],
        "slippage_mean_bps": summary["slippage_mean_bps"],
        "slippage_min_bps": summary["slippage_min_bps"],
        "slippage_max_bps": summary["slippage_max_bps"],
    }

    log_generic_experiment(
        run_type="paper_risk_report",
        run_name=f"paper_risk_{run_label}_{ts_label}",
        stats=stats,
        report_dir=out_dir,
        report_prefix=f"paper_risk_{run_label}_{ts_label}",
        extra_metadata={
            "runner": "report_paper_risk.py",
            "trades_csv": str(trades_path),
            "positions_csv": str(positions_path) if positions_path else None,
            "html_path": str(html_path),
            "base_currency": cfg.get("live.base_currency", "EUR"),
            "source_run_name": args.run_name,
        },
    )
    print("Paper-Risk-Report in Registry geloggt (run_type='paper_risk_report').\n")


if __name__ == "__main__":
    main()

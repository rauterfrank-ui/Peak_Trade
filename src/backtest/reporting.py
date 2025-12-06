# src/backtest/reporting.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend für Server/CI
import matplotlib.pyplot as plt
import pandas as pd

if TYPE_CHECKING:
    from .result import BacktestResult


def ensure_dir(path: str | Path) -> Path:
    """Erstellt Verzeichnis falls nicht vorhanden."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_equity_and_drawdown(
    result: "BacktestResult",
    output_dir: str | Path,
    run_name: str,
) -> None:
    """
    Speichert Equity & Drawdown als CSV.

    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis
        run_name: Name des Runs (für Dateinamen)
    """
    out_dir = ensure_dir(output_dir)

    eq_path = out_dir / f"{run_name}_equity.csv"
    dd_path = out_dir / f"{run_name}_drawdown.csv"

    result.equity_curve.to_frame(name="equity").to_csv(eq_path, index=True)
    result.drawdown.to_frame(name="drawdown").to_csv(dd_path, index=True)


def save_trades(
    result: "BacktestResult",
    output_dir: str | Path,
    run_name: str,
) -> None:
    """
    Speichert Trades als CSV (falls vorhanden).

    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis
        run_name: Name des Runs
    """
    if result.trades is None:
        return

    out_dir = ensure_dir(output_dir)
    trades_path = out_dir / f"{run_name}_trades.csv"
    result.trades.to_csv(trades_path, index=False)


def save_stats_json(
    result: "BacktestResult",
    output_dir: str | Path,
    run_name: str,
) -> None:
    """
    Speichert Stats & Metadata als JSON.

    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis
        run_name: Name des Runs
    """
    out_dir = ensure_dir(output_dir)
    stats_path = out_dir / f"{run_name}_stats.json"

    payload: dict[str, Any] = {
        "stats": result.stats,
        "metadata": result.metadata,
    }

    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def save_regime_distribution(
    result: "BacktestResult",
    output_dir: str | Path,
    run_name: str,
) -> None:
    """
    Speichert Regime-Verteilung als separate CSV (optional).
    
    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis
        run_name: Name des Runs
    """
    regime_dist = result.metadata.get('regime_distribution', {})
    if not regime_dist:
        return
    
    out_dir = ensure_dir(output_dir)
    regime_path = out_dir / f"{run_name}_regime_distribution.csv"
    
    # Als DataFrame speichern
    df = pd.DataFrame([
        {'regime': k, 'percentage': v}
        for k, v in regime_dist.items()
    ])
    df = df.sort_values('percentage', ascending=False)
    df.to_csv(regime_path, index=False)


def save_plots(
    result: "BacktestResult",
    output_dir: str | Path,
    run_name: str,
) -> None:
    """
    Erstellt und speichert Plots für Equity & Drawdown.

    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis
        run_name: Name des Runs
    """
    out_dir = ensure_dir(output_dir)

    # Equity-Curve
    eq_fig_path = out_dir / f"{run_name}_equity.png"
    plt.figure(figsize=(12, 6))
    result.equity_curve.plot()
    plt.title(f"Equity Curve – {run_name}")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(eq_fig_path, dpi=150)
    plt.close()

    # Drawdown
    dd_fig_path = out_dir / f"{run_name}_drawdown.png"
    plt.figure(figsize=(12, 6))
    result.drawdown.plot(color='red')
    plt.title(f"Drawdown – {run_name}")
    plt.xlabel("Time")
    plt.ylabel("Drawdown")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(dd_fig_path, dpi=150)
    plt.close()


def generate_html_report(
    result: "BacktestResult",
    output_dir: str | Path,
    run_name: str,
) -> Path:
    """
    Erzeugt einen HTML-Report für einen Backtest-Run.

    Inhalt:
    - Titel + Meta-Infos
    - Stats als Tabelle
    - Regime-Distribution (falls vorhanden)
    - eingebettete Plots (Equity/Drawdown) als <img>-Tags
    - Links auf CSV/JSON-Artefakte

    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis
        run_name: Name des Runs

    Returns:
        Path zum erstellten HTML-Report
    """
    out_dir = ensure_dir(output_dir)
    html_path = out_dir / f"{run_name}_report.html"

    stats = result.stats or {}
    metadata = result.metadata or {}

    name = metadata.get("name", run_name)
    symbol = metadata.get("symbol", "n/a")
    strategy_key = metadata.get("strategy_key", metadata.get("strategy", "n/a"))
    params = metadata.get("params", {})

    regime_dist = metadata.get("regime_distribution", {})
    regime_cfg = metadata.get("regime_config", {})

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Pfadnamen der bekannten Artefakte
    equity_csv = f"{run_name}_equity.csv"
    drawdown_csv = f"{run_name}_drawdown.csv"
    trades_csv = f"{run_name}_trades.csv"
    stats_json = f"{run_name}_stats.json"
    equity_png = f"{run_name}_equity.png"
    drawdown_png = f"{run_name}_drawdown.png"

    # Stats-HTML-Tabelle
    stats_rows = "".join(
        f"<tr><td>{key}</td><td>{value}</td></tr>"
        for key, value in stats.items()
    )

    # Params-HTML-Tabelle
    params_rows = "".join(
        f"<tr><td>{key}</td><td>{value}</td></tr>"
        for key, value in params.items()
    ) or "<tr><td colspan='2'><em>Keine expliziten Strategy-Parameter in metadata['params'] hinterlegt.</em></td></tr>"

    # Regime-Distribution-Tabelle
    regime_rows = "".join(
        f"<tr><td>{regime}</td><td>{frac:.2%}</td></tr>"
        for regime, frac in regime_dist.items()
    ) or "<tr><td colspan='2'><em>Keine Regime-Informationen verfügbar.</em></td></tr>"

    regime_cfg_rows = "".join(
        f"<tr><td>{key}</td><td>{value}</td></tr>"
        for key, value in regime_cfg.items()
    ) or "<tr><td colspan='2'><em>Keine Regime-Konfiguration in metadata['regime_config'] hinterlegt.</em></td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Peak_Trade Report – {name}</title>
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
        table {{
            border-collapse: collapse;
            margin-bottom: 1.5rem;
            width: 100%;
            max-width: 900px;
        }}
        th, td {{
            border: 1px solid #444;
            padding: 0.4rem 0.6rem;
            font-size: 0.9rem;
        }}
        th {{
            background-color: #222;
            text-align: left;
        }}
        .section {{
            margin-bottom: 2rem;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.5rem 1.5rem;
            max-width: 900px;
            margin-bottom: 1rem;
        }}
        .meta-item span.label {{
            font-size: 0.8rem;
            color: #aaa;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .meta-item div.value {{
            font-size: 1rem;
        }}
        img {{
            max-width: 900px;
            width: 100%;
            border-radius: 8px;
            border: 1px solid #333;
            background-color: #000;
        }}
        .img-row {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            max-width: 900px;
        }}
        code {{
            background-color: #222;
            padding: 0.15rem 0.3rem;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Peak_Trade Backtest Report</h1>
    <div class="section">
        <div class="meta-grid">
            <div class="meta-item">
                <span class="label">Name</span>
                <div class="value">{name}</div>
            </div>
            <div class="meta-item">
                <span class="label">Strategie</span>
                <div class="value">{strategy_key}</div>
            </div>
            <div class="meta-item">
                <span class="label">Symbol</span>
                <div class="value">{symbol}</div>
            </div>
            <div class="meta-item">
                <span class="label">Run-Name</span>
                <div class="value">{run_name}</div>
            </div>
            <div class="meta-item">
                <span class="label">Generiert</span>
                <div class="value">{generated_at}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>1. Kennzahlen (Stats)</h2>
        <table>
            <thead>
                <tr><th>Metric</th><th>Wert</th></tr>
            </thead>
            <tbody>
                {stats_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>2. Strategie-Parameter</h2>
        <table>
            <thead>
                <tr><th>Parameter</th><th>Wert</th></tr>
            </thead>
            <tbody>
                {params_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>3. Regime-Analyse</h2>
        <h3>3.1 Regime-Verteilung</h3>
        <table>
            <thead>
                <tr><th>Regime</th><th>Anteil</th></tr>
            </thead>
            <tbody>
                {regime_rows}
            </tbody>
        </table>

        <h3>3.2 Regime-Konfiguration</h3>
        <table>
            <thead>
                <tr><th>Parameter</th><th>Wert</th></tr>
            </thead>
            <tbody>
                {regime_cfg_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>4. Equity & Drawdown</h2>
        <div class="img-row">
            <div>
                <h3>4.1 Equity Curve</h3>
                <img src="{equity_png}" alt="Equity Curve" />
            </div>
            <div>
                <h3>4.2 Drawdown</h3>
                <img src="{drawdown_png}" alt="Drawdown" />
            </div>
        </div>
    </div>

    <div class="section">
        <h2>5. Rohdaten & Artefakte</h2>
        <ul>
            <li>Equity (CSV): <code>{equity_csv}</code></li>
            <li>Drawdown (CSV): <code>{drawdown_csv}</code></li>
            <li>Trades (CSV): <code>{trades_csv}</code> (falls vorhanden)</li>
            <li>Stats (JSON): <code>{stats_json}</code></li>
            <li>Equity-Plot (PNG): <code>{equity_png}</code></li>
            <li>Drawdown-Plot (PNG): <code>{drawdown_png}</code></li>
        </ul>
        <p>
            Hinweis: Diese Dateinamen sind relativ zu diesem HTML-Report und liegen im selben Verzeichnis.
        </p>
    </div>
</body>
</html>
"""

    html_path.write_text(html, encoding="utf-8")
    return html_path


def save_full_report(
    result: "BacktestResult",
    output_dir: str | Path = "reports",
    run_name: str = "run",
    save_plots_flag: bool = True,
    save_html_flag: bool = True,
) -> None:
    """
    Speichert alle relevanten Report-Artefakte in output_dir:
    - Equity & Drawdown (CSV)
    - Trades (CSV, falls vorhanden)
    - Stats + Metadata (JSON)
    - Plots (optional, PNG)
    - HTML-Report (optional)

    Args:
        result: BacktestResult-Objekt
        output_dir: Output-Verzeichnis (default: "reports")
        run_name: Name des Runs (für Dateinamen)
        save_plots_flag: Ob Plots erstellt werden sollen
        save_html_flag: Ob HTML-Report erstellt werden soll

    Example:
        >>> from src.backtest.result import BacktestResult
        >>> from src.backtest.reporting import save_full_report
        >>>
        >>> result = BacktestResult(...)
        >>> save_full_report(result, output_dir="reports", run_name="ma_crossover_demo")
    """
    save_equity_and_drawdown(result, output_dir, run_name)
    save_trades(result, output_dir, run_name)
    save_stats_json(result, output_dir, run_name)
    save_regime_distribution(result, output_dir, run_name)

    if save_plots_flag:
        try:
            save_plots(result, output_dir, run_name)
        except Exception as e:
            # Falls Matplotlib nicht verfügbar oder andere Plot-Fehler
            print(f"Warning: Konnte Plots nicht erstellen: {e}")

    if save_html_flag:
        try:
            generate_html_report(result, output_dir, run_name)
        except Exception as e:
            print(f"Warning: Konnte HTML-Report nicht erstellen: {e}")

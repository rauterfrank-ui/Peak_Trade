#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/create_notebook_templates.py
"""
Peak_Trade: Generator für Jupyter-Notebook-Templates
=====================================================

Erstellt drei vorkonfigurierte Jupyter-Notebooks im notebooks/ Verzeichnis:
- Experiments_Overview.ipynb
- Sweep_Analysis.ipynb
- Portfolio_Analysis.ipynb

Usage:
    python scripts/create_notebook_templates.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


NOTEBOOKS_DIR = Path("notebooks")


def make_notebook(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Baut ein minimales Jupyter-Notebook-JSON (nbformat 4).
    """
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
            },
            "orig_nbformat": 4,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def md_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(True),
    }


def code_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source.splitlines(True),
    }


def write_notebook(path: Path, nb: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)


def create_experiments_overview() -> None:
    path = NOTEBOOKS_DIR / "Experiments_Overview.ipynb"
    cells: List[Dict[str, Any]] = []

    cells.append(
        md_cell(
            "# Peak_Trade – Experiments Overview\n\n"
            "Dieses Notebook lädt die Experiment-Registry und bietet erste Auswertungen:\n\n"
            "- Überblick über alle Runs\n"
            "- Filter nach run_type / Strategy / Symbol / Portfolio\n"
            "- Grundlegende Kennzahlen-Verteilung (z.B. Sharpe)\n"
        )
    )

    cells.append(
        code_cell(
            "import pandas as pd\n"
            "from src.analytics.notebook_helpers import (\n"
            "    load_experiments,\n"
            "    filter_experiments,\n"
            "    describe_metric_distribution,\n"
            "    print_headline,\n"
            ")\n\n"
            "df = load_experiments()\n"
            "print_headline('Experiments – Head')\n"
            "df.head()"
        )
    )

    cells.append(
        code_cell(
            "# Beispiel: nur Single-Backtests für eine bestimmte Strategie/Symbol filtern\n"
            "run_type = 'single_backtest'\n"
            "strategy = 'ma_crossover'\n"
            "symbol = 'BTC/EUR'\n\n"
            "df_filtered = filter_experiments(\n"
            "    df,\n"
            "    run_type=run_type,\n"
            "    strategy=strategy,\n"
            "    symbol=symbol,\n"
            ")\n"
            "print_headline(f'Filtered: run_type={run_type}, strategy={strategy}, symbol={symbol}')\n"
            "df_filtered.head()"
        )
    )

    cells.append(
        code_cell(
            "# Verteilung der Sharpe-Ratio für alle Experimente\n"
            "print_headline('Sharpe Distribution – All Experiments')\n"
            "desc = describe_metric_distribution(df, metric='sharpe')\n"
            "desc"
        )
    )

    nb = make_notebook(cells)
    write_notebook(path, nb)


def create_sweep_analysis() -> None:
    path = NOTEBOOKS_DIR / "Sweep_Analysis.ipynb"
    cells: List[Dict[str, Any]] = []

    cells.append(
        md_cell(
            "# Peak_Trade – Sweep Analysis\n\n"
            "Dieses Notebook dient zur Analyse von Hyperparameter-Sweeps:\n\n"
            "- Laden einer Sweep-CSV aus `reports/sweeps/`\n"
            "- Scatterplots: Metrik vs. Parameter\n"
            "- Heatmaps: 2D-Parameter-Raum → Metrik\n"
        )
    )

    cells.append(
        code_cell(
            "from pathlib import Path\n\n"
            "from src.analytics.notebook_helpers import (\n"
            "    load_sweep,\n"
            "    sweep_scatter,\n"
            "    sweep_heatmap,\n"
            "    print_headline,\n"
            ")\n\n"
            "# Pfad zu deiner Sweep-CSV anpassen:\n"
            "sweep_csv = Path('reports/sweeps') / 'sweep_ma_crossover_ma_crossover_window_sweep.csv'\n"
            "df_sweep = load_sweep(sweep_csv)\n"
            "print_headline('Sweep – Head')\n"
            "df_sweep.head()"
        )
    )

    cells.append(
        code_cell(
            "# Scatter: Sharpe vs fast_window\n"
            "print_headline('Scatter: Sharpe vs fast_window')\n"
            "sweep_scatter(df_sweep, x_param='fast_window', metric='sharpe')"
        )
    )

    cells.append(
        code_cell(
            "# Heatmap: Sharpe über (fast_window, slow_window)\n"
            "print_headline('Heatmap: Sharpe – slow_window vs fast_window')\n"
            "sweep_heatmap(\n"
            "    df_sweep,\n"
            "    x_param='fast_window',\n"
            "    y_param='slow_window',\n"
            "    metric='sharpe',\n"
            "    aggfunc='mean',\n"
            ")"
        )
    )

    nb = make_notebook(cells)
    write_notebook(path, nb)


def create_portfolio_analysis() -> None:
    path = NOTEBOOKS_DIR / "Portfolio_Analysis.ipynb"
    cells: List[Dict[str, Any]] = []

    cells.append(
        md_cell(
            "# Peak_Trade – Portfolio Analysis\n\n"
            "Dieses Notebook analysiert Portfolio-Runs aus der Experiment-Registry:\n\n"
            "- Filter run_type == 'portfolio'\n"
            "- Top-Portfolios nach Sharpe/Return\n"
            "- Vergleich verschiedener Portfolio-Konfigurationen\n"
        )
    )

    cells.append(
        code_cell(
            "from src.analytics.notebook_helpers import (\n"
            "    load_experiments,\n"
            "    filter_portfolio_runs,\n"
            "    top_portfolios,\n"
            "    print_headline,\n"
            ")\n\n"
            "df = load_experiments()\n"
            "df_portfolios = filter_portfolio_runs(df)\n"
            "print_headline('Portfolio Runs – Head')\n"
            "df_portfolios.head()"
        )
    )

    cells.append(
        code_cell(
            "# Top-10 Portfolios nach Sharpe\n"
            "print_headline('Top Portfolios by Sharpe')\n"
            "top_sharpe = top_portfolios(df, metric='sharpe', top_n=10, ascending=False)\n"
            "top_sharpe"
        )
    )

    cells.append(
        code_cell(
            "# Beispiel: Nur bestimmtes Portfolio filtern (Name anpassen)\n"
            "portfolio_name = 'core_portfolio'\n"
            "df_core = filter_portfolio_runs(df, portfolio_name=portfolio_name)\n"
            "print_headline(f'Portfolio Runs – {portfolio_name}')\n"
            "df_core.sort_values('sharpe', ascending=False).head(10)"
        )
    )

    nb = make_notebook(cells)
    write_notebook(path, nb)


def main() -> None:
    print("\n📓 Peak_Trade Notebook Template Generator")
    print("=" * 70)

    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Erstelle Notebooks in {NOTEBOOKS_DIR}/...")

    create_experiments_overview()
    print(f"  ✅ Experiments_Overview.ipynb")

    create_sweep_analysis()
    print(f"  ✅ Sweep_Analysis.ipynb")

    create_portfolio_analysis()
    print(f"  ✅ Portfolio_Analysis.ipynb")

    print(f"\n🎉 Notebook-Templates erfolgreich erstellt!")
    print(f"\n📚 Nächste Schritte:")
    print(f"  1. Starte Jupyter: jupyter lab")
    print(f"  2. Öffne notebooks/Experiments_Overview.ipynb")
    print(f"  3. Führe alle Zellen aus (Run All)\n")


if __name__ == "__main__":
    main()

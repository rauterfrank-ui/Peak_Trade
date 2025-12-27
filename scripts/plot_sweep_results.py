#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/plot_sweep_results.py
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import List

# Projekt-Root zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Plots fuer Sweep-Ergebnisse (z.B. Sharpe vs. Parameter).",
    )
    parser.add_argument(
        "csv_path",
        help="Pfad zur Sweep-CSV (z.B. reports/sweeps/sweep_ma_crossover_xxx.csv).",
    )
    parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik, die geplottet werden soll (Default: sharpe).",
    )
    parser.add_argument(
        "--x-param",
        required=True,
        help="Name des Parameter-Feldes fuer die x-Achse.",
    )
    parser.add_argument(
        "--y-param",
        help="Optional: zweiter Parameter fuer 2D-Heatmap.",
    )
    parser.add_argument(
        "--output-dir",
        help="Zielverzeichnis fuer Plots. Default: wie CSV-Verzeichnis.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n📊 Peak_Trade Sweep Plot Generator")
    print("=" * 70)

    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV-Datei nicht gefunden: {csv_path}")

    print(f"\n📁 Lade Sweep-CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)} Zeilen geladen")

    metric = args.metric
    x_param = args.x_param
    y_param = args.y_param

    out_dir = Path(args.output_dir) if args.output_dir else csv_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if metric not in df.columns:
        raise ValueError(
            f"Metrik-Spalte {metric!r} nicht in CSV vorhanden. Spalten: {list(df.columns)}"
        )

    if x_param not in df.columns:
        raise ValueError(f"x-Parameter-Spalte {x_param!r} nicht in CSV vorhanden.")

    print(f"\n📈 Erstelle Plots...")
    print(f"  - Metrik: {metric}")
    print(f"  - X-Parameter: {x_param}")
    if y_param:
        print(f"  - Y-Parameter: {y_param}")

    # Scatterplot: Metric vs x_param
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_param], df[metric], alpha=0.7, s=50)
    plt.xlabel(x_param, fontsize=12)
    plt.ylabel(metric, fontsize=12)
    plt.title(f"{metric} vs {x_param}", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    scatter_path = out_dir / f"{csv_path.stem}_{metric}_vs_{x_param}.png"
    plt.savefig(scatter_path, dpi=150)
    plt.close()
    print(f"  ✅ Scatterplot: {scatter_path}")

    # Optional Heatmap fuer 2D-Parameter
    if y_param:
        if y_param not in df.columns:
            raise ValueError(f"y-Parameter-Spalte {y_param!r} nicht in CSV vorhanden.")

        # Pivot-Tabelle fuer Heatmap bauen
        pivot = df.pivot_table(
            index=y_param,
            columns=x_param,
            values=metric,
            aggfunc="mean",
        )

        plt.figure(figsize=(12, 8))
        im = plt.imshow(pivot.values, aspect="auto", origin="lower", cmap="viridis")
        plt.colorbar(im, label=metric)
        plt.xticks(
            ticks=np.arange(len(pivot.columns)), labels=pivot.columns, rotation=45, ha="right"
        )
        plt.yticks(ticks=np.arange(len(pivot.index)), labels=pivot.index)
        plt.xlabel(x_param, fontsize=12)
        plt.ylabel(y_param, fontsize=12)
        plt.title(f"{metric} Heatmap – {y_param} vs {x_param}", fontsize=14)
        plt.tight_layout()
        heatmap_path = out_dir / f"{csv_path.stem}_{metric}_heatmap_{y_param}_vs_{x_param}.png"
        plt.savefig(heatmap_path, dpi=150)
        plt.close()
        print(f"  ✅ Heatmap: {heatmap_path}")

    print(f"\n✅ Sweep-Plot-Generation abgeschlossen!\n")


if __name__ == "__main__":
    main()

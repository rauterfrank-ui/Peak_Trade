#!/usr/bin/env python3
"""
Peak_Trade R&D Experiment Analysis Template
============================================

Dieses Skript dient als wiederverwendbares Analyse-Template für R&D-Experimente.
Es lädt die JSON-Daten aus dem R&D-Experiments-Verzeichnis und bietet:

- DataFrame-Erstellung aus Experiment-JSONs
- Filterfunktionen analog zum CLI (`view_r_and_d_experiments.py`)
- Basis-Statistiken und Aggregationen
- Optional: Visualisierungen

Usage:
    # Direkt als Skript ausführen:
    python notebooks/r_and_d_experiment_analysis_template.py

    # In Jupyter/IPython als Template nutzen:
    # -> Sektionen als einzelne Zellen übernehmen

Autor: Peak_Trade Team
Datum: 2025-12-09
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# KONFIGURATION
# =============================================================================

# Projekt-Root bestimmen (relativ zu diesem Skript)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Standard-Verzeichnis für R&D-Experimente
DEFAULT_EXPERIMENTS_DIR = PROJECT_ROOT / "reports" / "r_and_d_experiments"

# Alternative: Überschreiben via Umgebungsvariable
EXPERIMENTS_DIR = Path(
    os.environ.get("PEAK_TRADE_RND_EXPERIMENTS_DIR", str(DEFAULT_EXPERIMENTS_DIR))
)

# =============================================================================
# IMPORTS (Data Science Stack)
# =============================================================================

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas nicht installiert. DataFrame-Funktionen nicht verfügbar.")

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib nicht installiert. Plot-Funktionen nicht verfügbar.")


# =============================================================================
# SEKTION 1: DATEN LADEN
# =============================================================================


def load_experiment_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Lädt eine einzelne Experiment-JSON-Datei.

    Args:
        filepath: Pfad zur JSON-Datei

    Returns:
        Experiment-Dict mit Metadaten oder None bei Fehler
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Metadaten hinzufügen
        data["_filepath"] = str(filepath)
        data["_filename"] = filepath.name
        return data
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON-Fehler in {filepath.name}: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Fehler beim Laden von {filepath.name}: {e}")
        return None


def load_experiments_from_dir(dir_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lädt alle R&D-Experimente aus einem Verzeichnis.

    Args:
        dir_path: Pfad zum Experiment-Verzeichnis (default: EXPERIMENTS_DIR)

    Returns:
        Liste von Experiment-Dicts, sortiert nach Timestamp (neueste zuerst)
    """
    experiments_dir = Path(dir_path) if dir_path else EXPERIMENTS_DIR

    if not experiments_dir.exists():
        print(f"⚠️  Verzeichnis nicht gefunden: {experiments_dir}")
        return []

    experiments: List[Dict[str, Any]] = []
    json_files = list(experiments_dir.glob("*.json"))

    print(f"📂 Lade Experimente aus: {experiments_dir}")
    print(f"   Gefundene JSON-Dateien: {len(json_files)}")

    for json_file in json_files:
        data = load_experiment_json(json_file)
        if data is not None:
            experiments.append(data)

    # Sortiere nach Timestamp (neueste zuerst)
    def get_timestamp(exp: Dict[str, Any]) -> str:
        return exp.get("experiment", {}).get("timestamp", "")

    experiments.sort(key=get_timestamp, reverse=True)

    print(f"   Erfolgreich geladen: {len(experiments)} Experimente")
    return experiments


def load_experiments_from_cli() -> List[Dict[str, Any]]:
    """
    Lädt Experimente via CLI-Tool (subprocess).

    Alternative Methode, die das CLI `view_r_and_d_experiments.py` nutzt.
    Nützlich, wenn man die gleiche Filter-Logik wie das CLI verwenden möchte.

    Returns:
        Liste von Experiment-Dicts

    Hinweis:
        Erfordert subprocess-Aufruf. In Notebooks evtl. weniger praktisch.
        Für interaktive Nutzung empfehlen wir `load_experiments_from_dir()`.
    """
    import subprocess

    cli_path = PROJECT_ROOT / "scripts" / "view_r_and_d_experiments.py"

    try:
        result = subprocess.run(
            [sys.executable, str(cli_path), "--output", "json"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"⚠️  CLI-Fehler: {result.stderr}")
            return []
    except Exception as e:
        print(f"⚠️  Fehler beim CLI-Aufruf: {e}")
        return []


# =============================================================================
# SEKTION 2: DATAFRAME-ERSTELLUNG
# =============================================================================


def extract_flat_record(exp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrahiert relevante Felder aus einem Experiment-Dict in ein flaches Format.

    Args:
        exp: Experiment-Dictionary (aus JSON)

    Returns:
        Flaches Dict mit den wichtigsten Feldern
    """
    experiment = exp.get("experiment", {})
    results = exp.get("results", {})
    meta = exp.get("meta", {})

    return {
        "filename": exp.get("_filename", ""),
        "timestamp": experiment.get("timestamp", ""),
        "tag": experiment.get("tag", ""),
        "preset_id": experiment.get("preset_id", ""),
        "strategy": experiment.get("strategy", ""),
        "symbol": experiment.get("symbol", ""),
        "timeframe": experiment.get("timeframe", ""),
        "from_date": experiment.get("from_date", ""),
        "to_date": experiment.get("to_date", ""),
        "total_return": results.get("total_return", 0.0),
        "max_drawdown": results.get("max_drawdown", 0.0),
        "sharpe": results.get("sharpe", 0.0),
        "total_trades": results.get("total_trades", 0),
        "win_rate": results.get("win_rate", 0.0),
        "profit_factor": results.get("profit_factor", 0.0),
        "sortino": results.get("sortino", 0.0),
        "calmar": results.get("calmar", 0.0),
        "use_dummy_data": meta.get("use_dummy_data", False),
        "tier": meta.get("tier", ""),
        "experimental": meta.get("experimental", False),
    }


def to_dataframe(experiments: List[Dict[str, Any]]) -> "pd.DataFrame":
    """
    Konvertiert eine Liste von Experiment-Dicts in einen pandas DataFrame.

    Args:
        experiments: Liste von Experiment-Dicts

    Returns:
        pandas DataFrame mit allen relevanten Spalten

    Raises:
        ImportError: Wenn pandas nicht installiert ist
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas ist erforderlich für DataFrame-Operationen")

    records = [extract_flat_record(exp) for exp in experiments]
    df = pd.DataFrame(records)

    # Datentypen setzen
    numeric_cols = [
        "total_return",
        "max_drawdown",
        "sharpe",
        "win_rate",
        "profit_factor",
        "sortino",
        "calmar",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "total_trades" in df.columns:
        df["total_trades"] = (
            pd.to_numeric(df["total_trades"], errors="coerce").fillna(0).astype(int)
        )

    # Timestamp parsen (falls möglich)
    if "timestamp" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(
            df["timestamp"], format="%Y%m%d_%H%M%S", errors="coerce"
        )

    return df


# =============================================================================
# SEKTION 3: FILTER-FUNKTIONEN
# =============================================================================


def filter_by_preset(df: "pd.DataFrame", preset: str) -> "pd.DataFrame":
    """Filtert DataFrame nach Preset-ID (exakter Match)."""
    return df[df["preset_id"] == preset].copy()


def filter_by_tag_substr(df: "pd.DataFrame", substr: str) -> "pd.DataFrame":
    """Filtert DataFrame nach Substring im Tag (case-insensitive)."""
    mask = df["tag"].str.lower().str.contains(substr.lower(), na=False)
    return df[mask].copy()


def filter_by_strategy(df: "pd.DataFrame", strategy: str) -> "pd.DataFrame":
    """Filtert DataFrame nach Strategy-ID (exakter Match)."""
    return df[df["strategy"] == strategy].copy()


def filter_by_date_range(
    df: "pd.DataFrame", date_from: Optional[str] = None, date_to: Optional[str] = None
) -> "pd.DataFrame":
    """
    Filtert DataFrame nach Datumsbereich.

    Args:
        df: DataFrame mit timestamp_dt Spalte
        date_from: Start-Datum (YYYY-MM-DD), optional
        date_to: End-Datum (YYYY-MM-DD), optional

    Returns:
        Gefilterter DataFrame
    """
    result = df.copy()

    if "timestamp_dt" not in result.columns:
        print("⚠️  timestamp_dt-Spalte nicht vorhanden. Datumsfilter übersprungen.")
        return result

    if date_from:
        try:
            from_dt = pd.to_datetime(date_from)
            result = result[result["timestamp_dt"] >= from_dt]
        except Exception:
            print(f"⚠️  Ungültiges Datum: {date_from}")

    if date_to:
        try:
            to_dt = pd.to_datetime(date_to)
            result = result[result["timestamp_dt"] <= to_dt]
        except Exception:
            print(f"⚠️  Ungültiges Datum: {date_to}")

    return result


def filter_with_trades(df: "pd.DataFrame") -> "pd.DataFrame":
    """Filtert DataFrame auf Experimente mit mindestens 1 Trade."""
    return df[df["total_trades"] > 0].copy()


def apply_filters(
    df: "pd.DataFrame",
    preset: Optional[str] = None,
    tag_substr: Optional[str] = None,
    strategy: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    with_trades: bool = False,
) -> "pd.DataFrame":
    """
    Wendet mehrere Filter kombiniert auf den DataFrame an.

    Args:
        df: Input-DataFrame
        preset: Filter nach Preset-ID
        tag_substr: Filter nach Tag-Substring
        strategy: Filter nach Strategy-ID
        date_from: Filter ab Datum (YYYY-MM-DD)
        date_to: Filter bis Datum (YYYY-MM-DD)
        with_trades: Nur Experimente mit Trades

    Returns:
        Gefilterter DataFrame
    """
    result = df.copy()

    if preset:
        result = filter_by_preset(result, preset)
    if tag_substr:
        result = filter_by_tag_substr(result, tag_substr)
    if strategy:
        result = filter_by_strategy(result, strategy)
    if date_from or date_to:
        result = filter_by_date_range(result, date_from, date_to)
    if with_trades:
        result = filter_with_trades(result)

    return result


# =============================================================================
# SEKTION 4: BASIS-ANALYSEN & AGGREGATIONEN
# =============================================================================


def summary_stats(df: "pd.DataFrame") -> Dict[str, Any]:
    """
    Berechnet Zusammenfassungsstatistiken für den DataFrame.

    Args:
        df: Experiment-DataFrame

    Returns:
        Dict mit Statistiken
    """
    if df.empty:
        return {"total": 0, "message": "Keine Experimente vorhanden"}

    return {
        "total_experiments": len(df),
        "unique_presets": df["preset_id"].nunique(),
        "unique_strategies": df["strategy"].nunique(),
        "experiments_with_trades": (df["total_trades"] > 0).sum(),
        "experiments_with_dummy_data": df["use_dummy_data"].sum(),
        "avg_sharpe": df["sharpe"].mean(),
        "avg_return": df["total_return"].mean(),
        "avg_max_drawdown": df["max_drawdown"].mean(),
        "total_trades_sum": df["total_trades"].sum(),
    }


def print_summary(df: "pd.DataFrame") -> None:
    """Gibt eine formatierte Zusammenfassung aus."""
    stats = summary_stats(df)

    print("\n" + "=" * 60)
    print("R&D EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"  Gesamt-Experimente:       {stats.get('total_experiments', 0)}")
    print(f"  Einzigartige Presets:     {stats.get('unique_presets', 0)}")
    print(f"  Einzigartige Strategies:  {stats.get('unique_strategies', 0)}")
    print(f"  Experimente mit Trades:   {stats.get('experiments_with_trades', 0)}")
    print(f"  Experimente mit Dummy:    {stats.get('experiments_with_dummy_data', 0)}")
    print("-" * 60)
    print(f"  Ø Sharpe:                 {stats.get('avg_sharpe', 0):.4f}")
    print(f"  Ø Return:                 {stats.get('avg_return', 0):.2%}")
    print(f"  Ø Max Drawdown:           {stats.get('avg_max_drawdown', 0):.2%}")
    print(f"  Summe Trades:             {stats.get('total_trades_sum', 0)}")
    print("=" * 60 + "\n")


def group_by_preset(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Aggregiert Metriken gruppiert nach Preset.

    Args:
        df: Experiment-DataFrame

    Returns:
        Aggregierter DataFrame
    """
    if df.empty:
        return df

    agg_df = df.groupby("preset_id").agg(
        {
            "total_return": ["mean", "std", "min", "max"],
            "sharpe": ["mean", "std", "min", "max"],
            "max_drawdown": ["mean", "min"],
            "win_rate": ["mean"],
            "total_trades": ["sum", "mean"],
            "tag": "count",
        }
    )

    # Spalten flach machen
    agg_df.columns = ["_".join(col).strip() for col in agg_df.columns.values]
    agg_df = agg_df.rename(columns={"tag_count": "experiment_count"})

    return agg_df.round(4)


def group_by_strategy(df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Aggregiert Metriken gruppiert nach Strategy.

    Args:
        df: Experiment-DataFrame

    Returns:
        Aggregierter DataFrame
    """
    if df.empty:
        return df

    agg_df = df.groupby("strategy").agg(
        {
            "total_return": ["mean", "std"],
            "sharpe": ["mean", "std"],
            "max_drawdown": ["mean"],
            "total_trades": ["sum"],
            "tag": "count",
        }
    )

    agg_df.columns = ["_".join(col).strip() for col in agg_df.columns.values]
    agg_df = agg_df.rename(columns={"tag_count": "experiment_count"})

    return agg_df.round(4)


def top_n_by_sharpe(df: "pd.DataFrame", n: int = 10) -> "pd.DataFrame":
    """
    Gibt die Top-N Experimente nach Sharpe Ratio zurück.

    Args:
        df: Experiment-DataFrame
        n: Anzahl der Top-Experimente

    Returns:
        Top-N DataFrame
    """
    cols = [
        "tag",
        "preset_id",
        "strategy",
        "sharpe",
        "total_return",
        "max_drawdown",
        "total_trades",
    ]
    available_cols = [c for c in cols if c in df.columns]
    return df.nlargest(n, "sharpe")[available_cols]


def top_n_by_return(df: "pd.DataFrame", n: int = 10) -> "pd.DataFrame":
    """
    Gibt die Top-N Experimente nach Return zurück.

    Args:
        df: Experiment-DataFrame
        n: Anzahl der Top-Experimente

    Returns:
        Top-N DataFrame
    """
    cols = [
        "tag",
        "preset_id",
        "strategy",
        "total_return",
        "sharpe",
        "max_drawdown",
        "total_trades",
    ]
    available_cols = [c for c in cols if c in df.columns]
    return df.nlargest(n, "total_return")[available_cols]


# =============================================================================
# SEKTION 5: VISUALISIERUNGEN (OPTIONAL)
# =============================================================================


def plot_sharpe_distribution(df: "pd.DataFrame", title: str = "Sharpe Ratio Distribution") -> None:
    """
    Erstellt ein Histogramm der Sharpe-Ratio-Verteilung.

    Args:
        df: Experiment-DataFrame
        title: Plot-Titel
    """
    if not MATPLOTLIB_AVAILABLE:
        print("⚠️  matplotlib nicht verfügbar. Plot übersprungen.")
        return

    if df.empty or "sharpe" not in df.columns:
        print("⚠️  Keine Daten für Sharpe-Plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    df["sharpe"].hist(bins=20, ax=ax, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Sharpe Ratio")
    ax.set_ylabel("Anzahl Experimente")
    ax.set_title(title)
    ax.axvline(
        df["sharpe"].mean(), color="red", linestyle="--", label=f"Mean: {df['sharpe'].mean():.2f}"
    )
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_return_by_preset(df: "pd.DataFrame", title: str = "Return by Preset") -> None:
    """
    Erstellt ein Boxplot der Returns gruppiert nach Preset.

    Args:
        df: Experiment-DataFrame
        title: Plot-Titel
    """
    if not MATPLOTLIB_AVAILABLE:
        print("⚠️  matplotlib nicht verfügbar. Plot übersprungen.")
        return

    if df.empty or "total_return" not in df.columns:
        print("⚠️  Keine Daten für Return-Plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    presets = df["preset_id"].unique()

    data = [df[df["preset_id"] == p]["total_return"].dropna() for p in presets]
    ax.boxplot(data, labels=presets)
    ax.set_xlabel("Preset")
    ax.set_ylabel("Total Return")
    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


def plot_sharpe_vs_return_scatter(df: "pd.DataFrame", title: str = "Sharpe vs Return") -> None:
    """
    Erstellt ein Scatter-Plot von Sharpe vs. Return.

    Args:
        df: Experiment-DataFrame
        title: Plot-Titel
    """
    if not MATPLOTLIB_AVAILABLE:
        print("⚠️  matplotlib nicht verfügbar. Plot übersprungen.")
        return

    if df.empty:
        print("⚠️  Keine Daten für Scatter-Plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    # Farben nach Preset
    presets = df["preset_id"].unique()
    colors = plt.cm.tab10(range(len(presets)))
    preset_color_map = dict(zip(presets, colors))

    for preset in presets:
        subset = df[df["preset_id"] == preset]
        ax.scatter(
            subset["total_return"],
            subset["sharpe"],
            label=preset[:20],  # Kürzen für Lesbarkeit
            alpha=0.7,
            s=50,
        )

    ax.set_xlabel("Total Return")
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title(title)
    ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
    ax.axvline(0, color="gray", linestyle="--", alpha=0.5)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


# =============================================================================
# SEKTION 6: MAIN / USAGE BEISPIELE
# =============================================================================


def main() -> None:
    """
    Hauptfunktion mit Beispiel-Workflow.

    Demonstriert den typischen Analyse-Flow:
    1. Daten laden
    2. DataFrame erstellen
    3. Filter anwenden
    4. Statistiken ausgeben
    5. Optional: Visualisierungen
    """
    print("\n" + "=" * 70)
    print("  Peak_Trade R&D Experiment Analysis Template")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # SCHRITT 1: Experimente laden
    # -------------------------------------------------------------------------
    print("\n📥 SCHRITT 1: Experimente laden...")
    experiments = load_experiments_from_dir()

    if not experiments:
        print("❌ Keine Experimente gefunden. Beende.")
        return

    # -------------------------------------------------------------------------
    # SCHRITT 2: DataFrame erstellen
    # -------------------------------------------------------------------------
    print("\n📊 SCHRITT 2: DataFrame erstellen...")

    if not PANDAS_AVAILABLE:
        print("❌ pandas nicht verfügbar. DataFrame-Erstellung nicht möglich.")
        return

    df = to_dataframe(experiments)
    print(f"   DataFrame-Shape: {df.shape}")
    print(f"   Spalten: {list(df.columns)}")

    # -------------------------------------------------------------------------
    # SCHRITT 3: Zusammenfassung
    # -------------------------------------------------------------------------
    print("\n📋 SCHRITT 3: Zusammenfassung...")
    print_summary(df)

    # -------------------------------------------------------------------------
    # SCHRITT 4: Beispiel-Filter
    # -------------------------------------------------------------------------
    print("\n🔍 SCHRITT 4: Beispiel-Filter...")

    # Beispiel A: Nur Experimente mit Trades
    df_with_trades = filter_with_trades(df)
    print(f"   Experimente mit Trades: {len(df_with_trades)}")

    # Beispiel B: Nach Tag-Substring filtern (z.B. "wave2")
    if df["tag"].str.contains("wave", case=False).any():
        df_wave = filter_by_tag_substr(df, "wave")
        print(f"   Experimente mit 'wave' im Tag: {len(df_wave)}")

    # Beispiel C: Kombinierte Filter
    # ➜ Hier eigene Filter einbauen!
    # df_filtered = apply_filters(df, preset="ehlers_super_smoother_v1", with_trades=True)

    # -------------------------------------------------------------------------
    # SCHRITT 5: Aggregationen
    # -------------------------------------------------------------------------
    print("\n📈 SCHRITT 5: Aggregationen...")

    # Nach Preset gruppieren
    if not df.empty:
        print("\n   Metriken nach Preset:")
        print("-" * 60)
        preset_stats = group_by_preset(df)
        if not preset_stats.empty:
            print(preset_stats.to_string())
        else:
            print("   (keine Daten)")

    # Top-5 nach Sharpe
    if not df.empty:
        print("\n   Top-5 nach Sharpe Ratio:")
        print("-" * 60)
        top5 = top_n_by_sharpe(df, n=5)
        if not top5.empty:
            print(top5.to_string(index=False))
        else:
            print("   (keine Daten)")

    # -------------------------------------------------------------------------
    # SCHRITT 6: Visualisierungen (optional)
    # -------------------------------------------------------------------------
    # Auskommentiert per Default – in Notebooks aktivieren:
    #
    # print("\n📊 SCHRITT 6: Visualisierungen...")
    # plot_sharpe_distribution(df)
    # plot_return_by_preset(df)
    # plot_sharpe_vs_return_scatter(df)

    # -------------------------------------------------------------------------
    # ABSCHLUSS
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  ✅ Analyse-Template abgeschlossen!")
    print("=" * 70)
    print(
        """
    Nächste Schritte:
    -----------------
    1. Eigene Filter hinzufügen (z.B. nach spezifischen Presets/Tags)
    2. Aggregationen erweitern (z.B. nach Symbol, Timeframe)
    3. Visualisierungen aktivieren (Plots auskommentieren)
    4. In Jupyter Notebook überführen:
       → Sektionen als einzelne Zellen kopieren
       → %matplotlib inline hinzufügen
    """
    )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()

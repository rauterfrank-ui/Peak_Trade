#!/usr/bin/env python3
"""
Peak_Trade R&D Experiments Viewer CLI
======================================

Leichtgewichtiges CLI-Tool zum Durchsuchen und Anzeigen von R&D-Experimenten.

Verwendung:
    # Standard-Übersicht
    python scripts/view_r_and_d_experiments.py

    # Verbose mit zusätzlichen Spalten
    python scripts/view_r_and_d_experiments.py -v

    # Filter nach Preset
    python scripts/view_r_and_d_experiments.py --preset ehlers_super_smoother_v1

    # Filter nach Tag-Substring
    python scripts/view_r_and_d_experiments.py --tag-substr wave2

    # Nur Experimente mit Trades
    python scripts/view_r_and_d_experiments.py --with-trades

    # Detail-Ansicht für eine Run-ID
    python scripts/view_r_and_d_experiments.py --run-id exp_rnd_w2_ehlers_v1_20251208_233254

    # JSON-Output
    python scripts/view_r_and_d_experiments.py --output json --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Default-Verzeichnis für R&D-Experimente
DEFAULT_EXPERIMENTS_DIR = project_root / "reports" / "r_and_d_experiments"


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================


def get_safe(data: Any, *keys: str, default: Any = "-") -> Any:
    """
    Holt verschachtelte Werte aus einem Dictionary sicher.

    Args:
        data: Das Dictionary (oder None)
        *keys: Die Schlüssel-Pfade
        default: Default-Wert bei fehlendem Key

    Returns:
        Der Wert oder default

    Beispiel:
        get_safe({"a": {"b": 42}}, "a", "b") -> 42
        get_safe({"a": 1}, "b") -> "-"
    """
    current = data
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
    return current if current is not None else default


def truncate(text: Any, max_length: int) -> str:
    """
    Kürzt einen String auf maximale Länge.

    Args:
        text: Der zu kürzende Text
        max_length: Maximale Länge

    Returns:
        Gekürzter String oder "-" bei None/leer
    """
    if text is None or text == "":
        return "-"
    text_str = str(text)
    if len(text_str) <= max_length:
        return text_str
    return text_str[: max_length - 1] + "…"


def format_percent(value: Any) -> str:
    """
    Formatiert einen numerischen Wert als Prozent.

    Args:
        value: Float (0.15 -> 15.0%) oder None

    Returns:
        Formatierter String oder "-"
    """
    if value is None or value == "-":
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return "-"


def format_number(value: Any, decimals: int = 2) -> str:
    """
    Formatiert eine Zahl mit fester Anzahl Dezimalstellen.

    Args:
        value: Numerischer Wert
        decimals: Anzahl Dezimalstellen

    Returns:
        Formatierter String oder "-"
    """
    if value is None:
        return "-"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "-"


def format_timestamp(timestamp: Any) -> str:
    """
    Formatiert einen Timestamp für die Anzeige.

    Args:
        timestamp: Timestamp im Format YYYYMMDD_HHMMSS

    Returns:
        Formatierter String (YYYY-MM-DD HH:MM) oder "-"
    """
    if not timestamp:
        return "-"
    try:
        dt = datetime.strptime(str(timestamp), "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return "-"


def extract_date_from_timestamp(timestamp: Any) -> Optional[datetime]:
    """
    Extrahiert ein datetime-Objekt aus einem Timestamp.

    Args:
        timestamp: Timestamp im Format YYYYMMDD_HHMMSS

    Returns:
        datetime-Objekt oder None
    """
    if not timestamp:
        return None
    try:
        full_dt = datetime.strptime(str(timestamp), "%Y%m%d_%H%M%S")
        # Nur Datum (ohne Zeit)
        return datetime(full_dt.year, full_dt.month, full_dt.day)
    except (ValueError, TypeError):
        return None


def determine_status(experiment: dict[str, Any]) -> str:
    """
    Bestimmt den Status eines Experiments.

    Args:
        experiment: Experiment-Dictionary

    Returns:
        Status-String: "ok", "no_trades", etc.
    """
    results = experiment.get("results", {})
    total_trades = results.get("total_trades", 0)

    if total_trades == 0:
        return "no_trades"
    return "ok"


# =============================================================================
# LADEN VON EXPERIMENTEN
# =============================================================================


def load_experiment_json(filepath: Path) -> Optional[dict[str, Any]]:
    """
    Lädt eine einzelne Experiment-JSON-Datei.

    Args:
        filepath: Pfad zur JSON-Datei

    Returns:
        Experiment-Dictionary mit _filepath und _filename oder None
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Metadaten hinzufügen
        data["_filepath"] = str(filepath)
        data["_filename"] = filepath.name
        return data
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        return None


def load_all_experiments(experiments_dir: Path) -> list[dict[str, Any]]:
    """
    Lädt alle Experiment-JSONs aus einem Verzeichnis.

    Args:
        experiments_dir: Pfad zum Experiment-Verzeichnis

    Returns:
        Liste von Experiment-Dictionaries, sortiert nach Timestamp (neueste zuerst)
    """
    if not experiments_dir.exists():
        return []

    experiments: list[dict[str, Any]] = []
    json_files = list(experiments_dir.glob("*.json"))

    for json_file in json_files:
        data = load_experiment_json(json_file)
        if data is not None:
            experiments.append(data)

    # Sortiere nach Timestamp (neueste zuerst)
    def get_timestamp(exp: dict[str, Any]) -> str:
        return get_safe(exp, "experiment", "timestamp", default="")

    experiments.sort(key=get_timestamp, reverse=True)
    return experiments


def filter_experiments(
    experiments: list[dict[str, Any]],
    preset: Optional[str] = None,
    tag_substr: Optional[str] = None,
    strategy: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    with_trades: bool = False,
) -> list[dict[str, Any]]:
    """
    Filtert Experimente nach verschiedenen Kriterien.

    Args:
        experiments: Liste von Experiment-Dicts
        preset: Filter nach preset_id (exakt)
        tag_substr: Filter nach Substring im Tag
        strategy: Filter nach Strategy-ID (exakt)
        date_from: Filter ab Datum (YYYY-MM-DD)
        date_to: Filter bis Datum (YYYY-MM-DD)
        with_trades: Nur Experimente mit mindestens 1 Trade

    Returns:
        Gefilterte Liste
    """
    filtered = []

    # Parse date filters
    date_from_dt = None
    date_to_dt = None
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass

    for exp in experiments:
        experiment = exp.get("experiment", {})
        results = exp.get("results", {})

        # Preset-Filter
        if preset and experiment.get("preset_id") != preset:
            continue

        # Strategy-Filter
        if strategy and experiment.get("strategy") != strategy:
            continue

        # Tag-Substring-Filter
        if tag_substr:
            tag = experiment.get("tag", "")
            if tag_substr.lower() not in tag.lower():
                continue

        # Trades-Filter
        if with_trades and results.get("total_trades", 0) == 0:
            continue

        # Date-Filter
        timestamp = experiment.get("timestamp", "")
        ts_dt = extract_date_from_timestamp(timestamp)
        if ts_dt:
            if date_from_dt and ts_dt < date_from_dt:
                continue
            if date_to_dt and ts_dt > date_to_dt:
                continue

        filtered.append(exp)

    return filtered


# =============================================================================
# FORMATIERUNG
# =============================================================================


def format_table(
    experiments: list[dict[str, Any]],
    verbose: bool = False,
    limit: Optional[int] = None,
) -> str:
    """
    Formatiert die Experimente als Tabelle.

    Args:
        experiments: Liste von Experiment-Dicts
        verbose: Zeigt zusätzliche Spalten
        limit: Maximale Anzahl Einträge

    Returns:
        Formatierte Tabelle als String
    """
    if not experiments:
        return "Keine Experimente gefunden."

    if limit:
        experiments = experiments[:limit]

    # Define columns
    if verbose:
        headers = [
            "Timestamp",
            "Tag",
            "Preset",
            "Strategy",
            "Symbol",
            "TF",
            "Trades",
            "Return",
            "Sharpe",
            "MaxDD",
            "WinRate",
            "Dummy",
            "Status",
        ]
    else:
        headers = [
            "Timestamp",
            "Tag",
            "Preset",
            "TF",
            "Trades",
            "Return",
            "Sharpe",
            "Dummy",
            "Status",
        ]

    rows: list[list[str]] = []
    for exp in experiments:
        experiment = exp.get("experiment", {})
        results = exp.get("results", {})
        meta = exp.get("meta", {})

        timestamp = experiment.get("timestamp", "")
        ts_display = timestamp[:8] if len(timestamp) >= 8 else timestamp or "-"
        tag = experiment.get("tag", "-")
        tag_short = truncate(tag, 28)
        preset_id = experiment.get("preset_id", "-")
        preset_short = truncate(preset_id, 23)
        timeframe = experiment.get("timeframe", "?")
        total_trades = results.get("total_trades", 0)
        total_return = results.get("total_return", 0.0)
        sharpe = results.get("sharpe", 0.0)
        max_drawdown = results.get("max_drawdown", 0.0)
        win_rate = results.get("win_rate", 0.0)
        use_dummy_data = meta.get("use_dummy_data", False)
        status = determine_status(exp)

        dummy_str = "✓" if use_dummy_data else ""

        if verbose:
            strategy = experiment.get("strategy", "-")
            strategy_short = truncate(strategy, 21)
            symbol = experiment.get("symbol", "-")
            rows.append(
                [
                    ts_display,
                    tag_short,
                    preset_short,
                    strategy_short,
                    symbol,
                    timeframe,
                    str(total_trades),
                    f"{total_return:.2%}",
                    f"{sharpe:.2f}",
                    f"{max_drawdown:.2%}",
                    f"{win_rate:.1%}",
                    dummy_str,
                    status,
                ]
            )
        else:
            rows.append(
                [
                    ts_display,
                    tag_short,
                    preset_short,
                    timeframe,
                    str(total_trades),
                    f"{total_return:.2%}",
                    f"{sharpe:.2f}",
                    dummy_str,
                    status,
                ]
            )

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    # Build table
    lines: list[str] = []

    # Header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Rows
    for row in rows:
        row_line = " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
        lines.append(row_line)

    # Footer
    lines.append("-" * len(header_line))
    lines.append(f"Gesamt: {len(experiments)} Experiment(e)")

    return "\n".join(lines)


def format_detail(experiment: dict[str, Any]) -> str:
    """
    Formatiert ein einzelnes Experiment als Detail-Ansicht.

    Args:
        experiment: Experiment-Dictionary

    Returns:
        Formatierte Detail-Ansicht als String
    """
    exp_data = experiment.get("experiment", {})
    results = experiment.get("results", {})
    meta = experiment.get("meta", {})

    run_id = Path(experiment.get("_filepath", "unknown")).stem
    preset_id = exp_data.get("preset_id", "unknown")
    strategy = exp_data.get("strategy", "unknown")
    symbol = exp_data.get("symbol", "unknown")
    timeframe = exp_data.get("timeframe", "?")
    from_date = exp_data.get("from_date", "")
    to_date = exp_data.get("to_date", "")
    tag = exp_data.get("tag", "")
    timestamp = exp_data.get("timestamp", "")
    total_return = results.get("total_return", 0.0)
    max_drawdown = results.get("max_drawdown", 0.0)
    sharpe = results.get("sharpe", 0.0)
    total_trades = results.get("total_trades", 0)
    win_rate = results.get("win_rate", 0.0)
    profit_factor = results.get("profit_factor", 0.0)
    use_dummy_data = meta.get("use_dummy_data", False)
    status = determine_status(experiment)
    filepath = experiment.get("_filepath", "?")

    lines = [
        "=" * 60,
        f"R&D Experiment Detail: {run_id}",
        "=" * 60,
        "",
        "📋 Experiment",
        f"   Preset:      {preset_id}",
        f"   Strategy:    {strategy}",
        f"   Symbol:      {symbol}",
        f"   Timeframe:   {timeframe}",
        f"   Zeitraum:    {from_date} → {to_date}",
        f"   Tag:         {tag}",
        f"   Timestamp:   {timestamp}",
        "",
        "📊 Ergebnisse",
        f"   Total Return:    {total_return:.2%}",
        f"   Max Drawdown:    {max_drawdown:.2%}",
        f"   Sharpe Ratio:    {sharpe:.2f}",
        f"   Trades:          {total_trades}",
        f"   Win Rate:        {win_rate:.1%}",
        f"   Profit Factor:   {profit_factor:.2f}",
        "",
        "🔧 Meta",
        f"   Dummy Data:      {'Ja' if use_dummy_data else 'Nein'}",
        f"   Status:          {status}",
        f"   Datei:           {filepath}",
        "",
        "📄 Raw JSON:",
        "-" * 40,
        json.dumps(experiment, indent=2, ensure_ascii=False),
    ]
    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den Argument-Parser."""
    parser = argparse.ArgumentParser(
        description="R&D Experiments Viewer – Durchsuchen und Anzeigen von R&D-Experimenten",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Übersicht
  python scripts/view_r_and_d_experiments.py

  # Verbose mit allen Spalten
  python scripts/view_r_and_d_experiments.py -v

  # Filtern nach Preset
  python scripts/view_r_and_d_experiments.py --preset ehlers_super_smoother_v1

  # Nur Experimente mit Trades
  python scripts/view_r_and_d_experiments.py --with-trades

  # Detail-Ansicht
  python scripts/view_r_and_d_experiments.py --run-id exp_rnd_w2_ehlers_v1_20251208_233254

  # JSON-Output
  python scripts/view_r_and_d_experiments.py --output json --limit 10
""",
    )

    # Display options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Zeigt zusätzliche Spalten (Strategy, Symbol, MaxDD, WinRate)",
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Output-Format: table (default) oder json",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximale Anzahl der angezeigten Experimente",
    )

    # Filter options
    filter_group = parser.add_argument_group("Filter")
    filter_group.add_argument(
        "--preset",
        type=str,
        default=None,
        help="Filtert nach Preset-ID (exakt)",
    )
    filter_group.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Filtert nach Strategy-ID (exakt)",
    )
    filter_group.add_argument(
        "--tag-substr",
        type=str,
        default=None,
        help="Filtert nach Substring im Tag",
    )
    filter_group.add_argument(
        "--date-from",
        type=str,
        default=None,
        help="Filtert ab Datum (YYYY-MM-DD)",
    )
    filter_group.add_argument(
        "--date-to",
        type=str,
        default=None,
        help="Filtert bis Datum (YYYY-MM-DD)",
    )
    filter_group.add_argument(
        "--with-trades",
        action="store_true",
        help="Zeigt nur Experimente mit mindestens einem Trade",
    )

    # Detail options
    detail_group = parser.add_argument_group("Detail-Ansicht")
    detail_group.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Zeigt Details zu einer Run-ID",
    )
    detail_group.add_argument(
        "--file",
        type=str,
        default=None,
        help="Zeigt Details zu einer JSON-Datei (direkter Pfad)",
    )

    # Directory option
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help=f"Experiment-Verzeichnis (default: {DEFAULT_EXPERIMENTS_DIR})",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Hauptfunktion."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Experiment-Verzeichnis
    experiments_dir = Path(args.dir) if args.dir else DEFAULT_EXPERIMENTS_DIR

    # Detail-Ansicht für einzelne Datei?
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"⚠️  Datei nicht gefunden: {filepath}", file=sys.stderr)
            return 1
        experiment = load_experiment_json(filepath)
        if experiment is None:
            print(f"⚠️  Fehler beim Laden: {filepath}", file=sys.stderr)
            return 1
        # JSON-Output für Detail
        print(json.dumps(experiment, indent=2, ensure_ascii=False))
        return 0

    # Detail-Ansicht für Run-ID?
    if args.run_id:
        # Suche im Experiments-Verzeichnis
        all_experiments = load_all_experiments(experiments_dir)
        matches = [
            exp
            for exp in all_experiments
            if args.run_id in exp.get("_filename", "")
            or args.run_id in get_safe(exp, "experiment", "timestamp", default="")
        ]

        if len(matches) == 0:
            print(f"⚠️  Kein Experiment gefunden für: {args.run_id}", file=sys.stderr)
            return 1
        if len(matches) > 1:
            print(
                f"⚠️  Mehrere Experimente gefunden für '{args.run_id}':",
                file=sys.stderr,
            )
            for m in matches:
                print(f"    - {m.get('_filename', '?')}", file=sys.stderr)
            return 1

        experiment = matches[0]
        # JSON-Output für Detail
        print(json.dumps(experiment, indent=2, ensure_ascii=False))
        return 0

    # Liste laden
    all_experiments = load_all_experiments(experiments_dir)
    filtered = filter_experiments(
        all_experiments,
        preset=args.preset,
        strategy=args.strategy,
        tag_substr=args.tag_substr,
        date_from=args.date_from,
        date_to=args.date_to,
        with_trades=args.with_trades,
    )

    # Output
    if args.output == "json":
        output_experiments = filtered[: args.limit] if args.limit else filtered
        print(json.dumps(output_experiments, indent=2, ensure_ascii=False))
    else:
        print(format_table(filtered, verbose=args.verbose, limit=args.limit))

    return 0


if __name__ == "__main__":
    sys.exit(main())

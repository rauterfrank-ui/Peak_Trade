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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Default-Verzeichnis für R&D-Experimente
DEFAULT_EXPERIMENTS_DIR = project_root / "reports" / "r_and_d_experiments"


@dataclass
class ExperimentRecord:
    """Repräsentiert ein geladenes R&D-Experiment."""

    file_path: Path
    preset_id: str
    strategy: str
    symbol: str
    timeframe: str
    from_date: str
    to_date: str
    tag: str
    timestamp: str
    total_return: float
    max_drawdown: float
    sharpe: float
    total_trades: int
    win_rate: float
    profit_factor: float
    use_dummy_data: bool
    status: str
    raw_data: dict[str, Any]

    @classmethod
    def from_json(cls, file_path: Path, data: dict[str, Any]) -> "ExperimentRecord":
        """Erstellt einen ExperimentRecord aus JSON-Daten."""
        experiment = data.get("experiment", {})
        results = data.get("results", {})
        meta = data.get("meta", {})

        return cls(
            file_path=file_path,
            preset_id=experiment.get("preset_id", "unknown"),
            strategy=experiment.get("strategy", "unknown"),
            symbol=experiment.get("symbol", "unknown"),
            timeframe=experiment.get("timeframe", "?"),
            from_date=experiment.get("from_date", ""),
            to_date=experiment.get("to_date", ""),
            tag=experiment.get("tag", ""),
            timestamp=experiment.get("timestamp", ""),
            total_return=results.get("total_return", 0.0),
            max_drawdown=results.get("max_drawdown", 0.0),
            sharpe=results.get("sharpe", 0.0),
            total_trades=results.get("total_trades", 0),
            win_rate=results.get("win_rate", 0.0),
            profit_factor=results.get("profit_factor", 0.0),
            use_dummy_data=meta.get("use_dummy_data", False),
            status="ok",
            raw_data=data,
        )

    @property
    def run_id(self) -> str:
        """Generiert eine Run-ID aus dem Dateinamen."""
        return self.file_path.stem

    @property
    def parsed_timestamp(self) -> Optional[datetime]:
        """Parst den Timestamp in ein datetime-Objekt."""
        if not self.timestamp:
            return None
        try:
            return datetime.strptime(self.timestamp, "%Y%m%d_%H%M%S")
        except ValueError:
            return None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu einem Dictionary für JSON-Export."""
        return {
            "run_id": self.run_id,
            "preset_id": self.preset_id,
            "strategy": self.strategy,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "tag": self.tag,
            "timestamp": self.timestamp,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "sharpe": self.sharpe,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "use_dummy_data": self.use_dummy_data,
            "status": self.status,
        }


def load_experiments(
    experiments_dir: Path,
    preset_filter: Optional[str] = None,
    strategy_filter: Optional[str] = None,
    tag_substr: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    with_trades: bool = False,
) -> list[ExperimentRecord]:
    """
    Lädt alle R&D-Experimente aus dem angegebenen Verzeichnis.

    Args:
        experiments_dir: Pfad zum Experiment-Verzeichnis
        preset_filter: Filtert nach Preset-ID (exakt)
        strategy_filter: Filtert nach Strategy-ID (exakt)
        tag_substr: Filtert nach Substring im Tag
        date_from: Filtert ab Datum (YYYY-MM-DD)
        date_to: Filtert bis Datum (YYYY-MM-DD)
        with_trades: Nur Experimente mit mindestens 1 Trade

    Returns:
        Liste von ExperimentRecord-Objekten
    """
    if not experiments_dir.exists():
        print(f"⚠️  Verzeichnis nicht gefunden: {experiments_dir}", file=sys.stderr)
        return []

    records: list[ExperimentRecord] = []
    json_files = sorted(experiments_dir.glob("*.json"), reverse=True)

    # Parse date filters
    date_from_dt = None
    date_to_dt = None
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            print(f"⚠️  Ungültiges Datumsformat für --date-from: {date_from}", file=sys.stderr)
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            print(f"⚠️  Ungültiges Datumsformat für --date-to: {date_to}", file=sys.stderr)

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            record = ExperimentRecord.from_json(json_file, data)

            # Apply filters
            if preset_filter and record.preset_id != preset_filter:
                continue
            if strategy_filter and record.strategy != strategy_filter:
                continue
            if tag_substr and tag_substr.lower() not in record.tag.lower():
                continue
            if with_trades and record.total_trades == 0:
                continue

            # Date filters
            if date_from_dt or date_to_dt:
                ts = record.parsed_timestamp
                if ts:
                    if date_from_dt and ts < date_from_dt:
                        continue
                    if date_to_dt and ts > date_to_dt:
                        continue

            records.append(record)

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON-Fehler in {json_file.name}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Fehler beim Laden von {json_file.name}: {e}", file=sys.stderr)

    return records


def load_single_experiment(
    run_id: Optional[str] = None,
    file_path: Optional[str] = None,
    experiments_dir: Path = DEFAULT_EXPERIMENTS_DIR,
) -> Optional[ExperimentRecord]:
    """
    Lädt ein einzelnes Experiment nach Run-ID oder Dateipfad.

    Args:
        run_id: Run-ID (Dateiname ohne .json)
        file_path: Direkter Pfad zur JSON-Datei
        experiments_dir: Verzeichnis für Run-ID-Suche

    Returns:
        ExperimentRecord oder None
    """
    target_path: Optional[Path] = None

    if file_path:
        target_path = Path(file_path)
    elif run_id:
        # Suche im Experiments-Verzeichnis
        candidate = experiments_dir / f"{run_id}.json"
        if candidate.exists():
            target_path = candidate
        else:
            # Suche nach Teilübereinstimmung
            matches = list(experiments_dir.glob(f"*{run_id}*.json"))
            if len(matches) == 1:
                target_path = matches[0]
            elif len(matches) > 1:
                print(f"⚠️  Mehrere Dateien gefunden für '{run_id}':", file=sys.stderr)
                for m in matches:
                    print(f"    - {m.name}", file=sys.stderr)
                return None

    if not target_path or not target_path.exists():
        print(f"⚠️  Datei nicht gefunden: {run_id or file_path}", file=sys.stderr)
        return None

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ExperimentRecord.from_json(target_path, data)
    except Exception as e:
        print(f"⚠️  Fehler beim Laden: {e}", file=sys.stderr)
        return None


def format_table(
    records: list[ExperimentRecord],
    verbose: bool = False,
    limit: Optional[int] = None,
) -> str:
    """
    Formatiert die Experimente als Tabelle.

    Args:
        records: Liste von ExperimentRecord-Objekten
        verbose: Zeigt zusätzliche Spalten
        limit: Maximale Anzahl Einträge

    Returns:
        Formatierte Tabelle als String
    """
    if not records:
        return "Keine Experimente gefunden."

    if limit:
        records = records[:limit]

    # Define columns
    if verbose:
        headers = ["Timestamp", "Tag", "Preset", "Strategy", "Symbol", "TF", "Trades", "Return", "Sharpe", "MaxDD", "WinRate", "Dummy", "Status"]
    else:
        headers = ["Timestamp", "Tag", "Preset", "TF", "Trades", "Return", "Sharpe", "Dummy", "Status"]

    rows: list[list[str]] = []
    for r in records:
        ts_display = r.timestamp[:8] if len(r.timestamp) >= 8 else r.timestamp
        tag_short = r.tag[:25] + "..." if len(r.tag) > 28 else r.tag
        preset_short = r.preset_id[:20] + "..." if len(r.preset_id) > 23 else r.preset_id
        dummy_str = "✓" if r.use_dummy_data else ""

        if verbose:
            strategy_short = r.strategy[:18] + "..." if len(r.strategy) > 21 else r.strategy
            rows.append([
                ts_display,
                tag_short,
                preset_short,
                strategy_short,
                r.symbol,
                r.timeframe,
                str(r.total_trades),
                f"{r.total_return:.2%}",
                f"{r.sharpe:.2f}",
                f"{r.max_drawdown:.2%}",
                f"{r.win_rate:.1%}",
                dummy_str,
                r.status,
            ])
        else:
            rows.append([
                ts_display,
                tag_short,
                preset_short,
                r.timeframe,
                str(r.total_trades),
                f"{r.total_return:.2%}",
                f"{r.sharpe:.2f}",
                dummy_str,
                r.status,
            ])

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
    lines.append(f"Gesamt: {len(records)} Experiment(e)")

    return "\n".join(lines)


def format_detail(record: ExperimentRecord) -> str:
    """
    Formatiert ein einzelnes Experiment als Detail-Ansicht.

    Args:
        record: ExperimentRecord

    Returns:
        Formatierte Detail-Ansicht als String
    """
    lines = [
        "=" * 60,
        f"R&D Experiment Detail: {record.run_id}",
        "=" * 60,
        "",
        "📋 Experiment",
        f"   Preset:      {record.preset_id}",
        f"   Strategy:    {record.strategy}",
        f"   Symbol:      {record.symbol}",
        f"   Timeframe:   {record.timeframe}",
        f"   Zeitraum:    {record.from_date} → {record.to_date}",
        f"   Tag:         {record.tag}",
        f"   Timestamp:   {record.timestamp}",
        "",
        "📊 Ergebnisse",
        f"   Total Return:    {record.total_return:.2%}",
        f"   Max Drawdown:    {record.max_drawdown:.2%}",
        f"   Sharpe Ratio:    {record.sharpe:.2f}",
        f"   Trades:          {record.total_trades}",
        f"   Win Rate:        {record.win_rate:.1%}",
        f"   Profit Factor:   {record.profit_factor:.2f}",
        "",
        "🔧 Meta",
        f"   Dummy Data:      {'Ja' if record.use_dummy_data else 'Nein'}",
        f"   Status:          {record.status}",
        f"   Datei:           {record.file_path}",
        "",
        "📄 Raw JSON:",
        "-" * 40,
        json.dumps(record.raw_data, indent=2, ensure_ascii=False),
    ]
    return "\n".join(lines)


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
        "-v", "--verbose",
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

    # Detail-Ansicht?
    if args.run_id or args.file:
        record = load_single_experiment(
            run_id=args.run_id,
            file_path=args.file,
            experiments_dir=experiments_dir,
        )
        if record:
            if args.output == "json":
                print(json.dumps(record.raw_data, indent=2, ensure_ascii=False))
            else:
                print(format_detail(record))
            return 0
        return 1

    # Liste laden
    records = load_experiments(
        experiments_dir=experiments_dir,
        preset_filter=args.preset,
        strategy_filter=args.strategy,
        tag_substr=args.tag_substr,
        date_from=args.date_from,
        date_to=args.date_to,
        with_trades=args.with_trades,
    )

    # Output
    if args.output == "json":
        output_records = records[:args.limit] if args.limit else records
        output_data = [r.to_dict() for r in output_records]
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
    else:
        print(format_table(records, verbose=args.verbose, limit=args.limit))

    return 0


if __name__ == "__main__":
    sys.exit(main())

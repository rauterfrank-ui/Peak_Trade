# src/webui/r_and_d_api.py
"""
Peak_Trade: R&D Dashboard API v1.3 (Phase 78)
=============================================

API-Endpoints für das R&D-Dashboard:
- GET /api/r_and_d/experiments - Liste aller R&D-Experimente (mit Filtern)
- GET /api/r_and_d/experiments/{run_id} - Detail eines Experiments (v1.2: mit Report-Links)
- GET /api/r_and_d/experiments/batch - Batch-Abfrage mehrerer Experimente (v1.3: Phase 78)
- GET /api/r_and_d/summary - Aggregierte Summary-Statistiken
- GET /api/r_and_d/presets - Aggregation nach Preset
- GET /api/r_and_d/strategies - Aggregation nach Strategy
- GET /api/r_and_d/stats - Globale Statistiken
- GET /api/r_and_d/today - Heute fertige Experimente (Daily R&D View)
- GET /api/r_and_d/running - Aktuell laufende Experimente

v1.3 Änderungen (Phase 78):
- Batch-Endpoint für Multi-Run-Comparison
- Unterstützung für 2-10 Run-IDs pro Request
- Rückgabe von found/not_found IDs für Transparenz

v1.2 Änderungen (Phase 77):
- Report-Links (HTML/Markdown) in Detail-Endpoint
- Erweiterte Meta-Daten mit Laufzeit-Infos
- Strukturierte Response für Detail-View

v1.1 Änderungen:
- run_type und tier Felder prominenter
- Status: success, running, failed, no_trades
- Today-Filter für "Was ist heute fertig geworden?"
- Experiment-Kategorien nach R&D-Taxonomie

Basis: reports/r_and_d_experiments/, view_r_and_d_experiments.py, Notebook-Template
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# =============================================================================
# KONFIGURATION
# =============================================================================

# Batch-Endpoint Limits (zentral konfigurierbar)
BATCH_MIN_RUN_IDS: int = 2
BATCH_MAX_RUN_IDS: int = 10


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================


class BestMetricsDict(TypedDict, total=False):
    """
    Typisierung für Best-Metrics-Ergebnis (v1.3 / Phase 78).

    total=False bedeutet, dass alle Felder optional sind.
    Felder werden nur gesetzt, wenn mindestens ein gültiger Wert existiert.
    """
    total_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int


# =============================================================================
# ARCHITEKTUR-NOTE: Helper-Funktionen (R&D-API v1.3 / Phase 78)
# =============================================================================
#
# Das Helper-Set ist nach folgenden Prinzipien aufgebaut:
#
# 1. LOOKUP-LAYER: `find_experiment_by_run_id()`
#    - Zentralisiert alle Match-Logik an einer Stelle
#    - Verhindert Inkonsistenzen zwischen API- und HTML-Endpoints
#    - Strict-Match-only (kein Substring-Match) für Vorhersehbarkeit
#
# 2. TRANSFORMATION-LAYER: `build_experiment_detail()`
#    - Einheitlicher Payload für Detail- und Batch-Endpoints
#    - Kombiniert raw JSON mit berechneten Feldern (status, run_type, report_links)
#    - Flache Metrik-Felder für einfaches Frontend-Binding
#
# 3. AGGREGATION-LAYER: `compute_best_metrics()`
#    - Berechnet "Winner" pro Metrik für Comparison-Highlighting
#    - Drawdown-Sonderlogik: der Wert nächste zu 0 gewinnt (nicht der mathematisch
#      größte Verlust)
#
# 4. VALIDATION-LAYER: `parse_and_validate_run_ids()`
#    - Input-Sanitization + Business-Rule-Validierung in einem Schritt
#    - Deduplizierung vor Validierung (verhindert User-Verwirrung bei mehrfach
#      eingegebenen IDs)
#    - Framework-agnostisch: wirft ValueError (Umwandlung in HTTPException im Endpoint)
#
# Änderungen an der Match-Logik sollten in `find_experiment_by_run_id()` erfolgen,
# nicht in einzelnen Endpoints. So bleibt das Verhalten API-weit konsistent.
# =============================================================================


# Standard-Verzeichnis für R&D-Experimente (relativ zum Repo-Root)
# Wird von außen über BASE_DIR gesetzt
_BASE_DIR: Path | None = None


def set_base_dir(base_dir: Path) -> None:
    """Setzt das Basis-Verzeichnis für R&D-Experimente."""
    global _BASE_DIR
    _BASE_DIR = base_dir


def get_r_and_d_dir() -> Path:
    """Gibt das R&D-Experiments-Verzeichnis zurück."""
    if _BASE_DIR is None:
        # Fallback: relativ zu diesem Modul
        return Path(__file__).resolve().parents[2] / "reports" / "r_and_d_experiments"
    return _BASE_DIR / "reports" / "r_and_d_experiments"


# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class RnDExperimentSummary(BaseModel):
    """Zusammenfassung eines R&D-Experiments für Listen-Ansicht (v1.1)."""
    filename: str
    run_id: str
    timestamp: str
    tag: str
    preset_id: str
    strategy: str
    symbol: str
    timeframe: str
    total_return: float
    sharpe: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    status: str  # success, running, failed, no_trades
    use_dummy_data: bool = False
    # v1.1: Neue Felder für bessere Taxonomie
    tier: str = "r_and_d"  # r_and_d, core, aux, legacy
    run_type: str = "backtest"  # backtest, sweep, monte_carlo, walkforward
    experiment_category: str = ""  # cycles, volatility, ml, microstructure
    date_str: str = ""  # YYYY-MM-DD für einfache Filterung


class RnDReportLink(BaseModel):
    """Report-Link für ein R&D-Experiment (v1.2)."""
    type: str  # html, markdown, json, png
    label: str
    path: str
    url: str  # Relative URL für Web-Zugriff
    exists: bool = True


class RnDExperimentDetail(BaseModel):
    """Vollständige Details eines R&D-Experiments (v1.2)."""
    filename: str
    run_id: str
    experiment: dict[str, Any]
    results: dict[str, Any]
    meta: dict[str, Any]
    parameters: dict[str, Any] | None = None
    raw: dict[str, Any]
    # v1.2: Report-Links
    report_links: list[dict[str, Any]] = []
    # v1.2: Erweiterte Felder
    status: str = ""
    run_type: str = ""
    tier: str = ""
    experiment_category: str = ""
    duration_info: dict[str, Any] | None = None


class RnDSummary(BaseModel):
    """Aggregierte Summary über alle R&D-Experimente."""
    total_experiments: int
    experiments_with_trades: int
    experiments_with_dummy_data: int
    unique_presets: int
    unique_strategies: int
    by_status: dict[str, int]


class RnDPresetStats(BaseModel):
    """Statistiken für ein einzelnes Preset."""
    preset_id: str
    experiment_count: int
    experiments_with_trades: int
    avg_return: float
    avg_sharpe: float
    avg_max_drawdown: float
    avg_win_rate: float
    total_trades: int


class RnDStrategyStats(BaseModel):
    """Statistiken für eine einzelne Strategy."""
    strategy: str
    experiment_count: int
    experiments_with_trades: int
    avg_return: float
    avg_sharpe: float
    avg_max_drawdown: float
    total_trades: int


class RnDGlobalStats(BaseModel):
    """Globale R&D-Statistiken."""
    total_experiments: int
    unique_presets: int
    unique_strategies: int
    unique_symbols: int
    experiments_with_trades: int
    avg_sharpe: float
    avg_return: float
    avg_max_drawdown: float
    median_sharpe: float
    median_return: float


class RnDBatchResponse(BaseModel):
    """Response für Batch-Abfrage mehrerer Experimente (v1.3)."""
    experiments: list[dict[str, Any]]
    requested_ids: list[str]
    found_ids: list[str]
    not_found_ids: list[str]
    total_requested: int
    total_found: int
    best_metrics: dict[str, Any] = {}  # v1.3: Für Comparison-Highlighting


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================


def load_experiment_json(filepath: Path) -> dict[str, Any] | None:
    """
    Lädt eine einzelne Experiment-JSON-Datei.

    Args:
        filepath: Pfad zur JSON-Datei

    Returns:
        Experiment-Dict mit Metadaten oder None bei Fehler
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        data["_filepath"] = str(filepath)
        data["_filename"] = filepath.name
        return data
    except (OSError, json.JSONDecodeError, FileNotFoundError):
        return None


def load_experiments_from_dir(dir_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Lädt alle R&D-Experimente aus dem Verzeichnis.

    Args:
        dir_path: Pfad zum Experiment-Verzeichnis (default: get_r_and_d_dir())

    Returns:
        Liste von Experiment-Dicts, sortiert nach Timestamp (neueste zuerst)
    """
    experiments_dir = dir_path or get_r_and_d_dir()

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
        return exp.get("experiment", {}).get("timestamp", "")

    experiments.sort(key=get_timestamp, reverse=True)
    return experiments


def extract_flat_fields(exp: dict[str, Any]) -> dict[str, Any]:
    """Extrahiert flache Felder aus einem Experiment-Dict (v1.1)."""
    experiment = exp.get("experiment", {})
    results = exp.get("results", {})
    meta = exp.get("meta", {})

    timestamp = experiment.get("timestamp", "")
    filename = exp.get("_filename", "")

    # Run-ID aus Filename oder Timestamp generieren
    run_id = filename.replace(".json", "") if filename else timestamp

    # v1.1: Date-String für einfache Filterung extrahieren (YYYY-MM-DD)
    date_str = ""
    if timestamp and len(timestamp) >= 8:
        try:
            date_str = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
        except (IndexError, ValueError):
            date_str = ""

    # v1.1: Run-Type und Tier aus Meta/Tag ableiten
    run_type = meta.get("run_type", "")
    if not run_type:
        # Heuristik basierend auf Tag
        tag = experiment.get("tag", "").lower()
        if "sweep" in tag:
            run_type = "sweep"
        elif "monte" in tag or "mc_" in tag:
            run_type = "monte_carlo"
        elif "walkforward" in tag or "wf_" in tag:
            run_type = "walkforward"
        else:
            run_type = "backtest"

    # v1.1: Experiment-Kategorie aus Preset/Strategy ableiten
    experiment_category = meta.get("category", "")
    if not experiment_category:
        strategy = experiment.get("strategy", "").lower()
        preset = experiment.get("preset_id", "").lower()
        if "ehlers" in strategy or "ehlers" in preset or "armstrong" in strategy or "armstrong" in preset:
            experiment_category = "cycles"
        elif "meta_labeling" in strategy or "lopez" in preset:
            experiment_category = "ml"
        elif "el_karoui" in strategy or "vol" in preset:
            experiment_category = "volatility"
        else:
            experiment_category = "general"

    return {
        "filename": filename,
        "run_id": run_id,
        "timestamp": timestamp,
        "tag": experiment.get("tag", ""),
        "preset_id": experiment.get("preset_id", ""),
        "strategy": experiment.get("strategy", ""),
        "symbol": experiment.get("symbol", ""),
        "timeframe": experiment.get("timeframe", ""),
        "total_return": float(results.get("total_return", 0.0)),
        "sharpe": float(results.get("sharpe", 0.0)),
        "max_drawdown": float(results.get("max_drawdown", 0.0)),
        "total_trades": int(results.get("total_trades", 0)),
        "win_rate": float(results.get("win_rate", 0.0)),
        "profit_factor": float(results.get("profit_factor", 0.0)),
        "use_dummy_data": bool(meta.get("use_dummy_data", False)),
        "status": determine_status(exp),
        # v1.1: Neue Felder
        "tier": meta.get("tier", "r_and_d"),
        "run_type": run_type,
        "experiment_category": experiment_category,
        "date_str": date_str,
    }


def determine_status(exp: dict[str, Any]) -> str:
    """
    Bestimmt den Status eines Experiments (v1.1).

    Status-Werte:
    - success: Abgeschlossen mit Trades > 0
    - running: Noch laufend (meta.status == "running")
    - failed: Fehlgeschlagen (meta.status == "failed" oder error vorhanden)
    - no_trades: Abgeschlossen aber 0 Trades
    """
    meta = exp.get("meta", {})
    results = exp.get("results", {})

    # Expliziter Status aus Meta (v1.1)
    meta_status = meta.get("status", "")
    if meta_status == "running":
        return "running"
    if meta_status == "failed" or meta.get("error"):
        return "failed"

    # Fallback auf Trade-basierte Bestimmung
    total_trades = results.get("total_trades", 0)
    if total_trades == 0:
        return "no_trades"
    return "success"


def parse_date(date_str: str) -> datetime | None:
    """Parst ein Datum im Format YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def find_report_links(run_id: str, experiment: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Sucht nach zugehörigen Report-Dateien für ein Experiment (v1.2).

    Sucht in verschiedenen Reports-Verzeichnissen nach:
    - HTML-Reports (_report.html)
    - Markdown-Reports (_report.md, .md)
    - Stats-JSON (_stats.json)
    - Equity-Charts (_equity.png)
    - Drawdown-Charts (_drawdown.png)

    Args:
        run_id: Run-ID des Experiments
        experiment: Experiment-Dict mit Meta-Daten

    Returns:
        Liste von Report-Link-Dicts
    """
    report_links: list[dict[str, Any]] = []
    base_dir = _BASE_DIR or Path(__file__).resolve().parents[2]

    # Extrahiere mögliche Dateinamen-Präfixe
    exp_data = experiment.get("experiment", {})
    tag = exp_data.get("tag", "")
    preset_id = exp_data.get("preset_id", "")
    strategy = exp_data.get("strategy", "")
    timestamp = exp_data.get("timestamp", "")

    # Mögliche Präfixe für Report-Suche
    prefixes = [run_id]
    if tag:
        prefixes.append(tag)
    if preset_id and timestamp:
        prefixes.append(f"{preset_id}_{timestamp}")
    if strategy and timestamp:
        prefixes.append(f"{strategy}_{timestamp}")

    # Report-Verzeichnisse durchsuchen
    report_dirs = [
        base_dir / "reports",
        base_dir / "reports" / "r_and_d_experiments",
        base_dir / "reports" / "portfolio",
        base_dir / "reports" / "ideas",
    ]

    # Report-Typen mit Labels
    report_patterns = [
        ("_report.html", "html", "📄 HTML Report"),
        ("_report.md", "markdown", "📝 Markdown Report"),
        (".md", "markdown", "📝 Markdown"),
        ("_stats.json", "json", "📊 Stats JSON"),
        ("_equity.png", "png", "📈 Equity Chart"),
        ("_drawdown.png", "png", "📉 Drawdown Chart"),
    ]

    found_paths: set = set()  # Verhindere Duplikate

    for report_dir in report_dirs:
        if not report_dir.exists():
            continue

        for prefix in prefixes:
            for suffix, rtype, label in report_patterns:
                # Direkte Datei
                report_path = report_dir / f"{prefix}{suffix}"
                if report_path.exists() and str(report_path) not in found_paths:
                    found_paths.add(str(report_path))
                    rel_path = report_path.relative_to(base_dir)
                    report_links.append({
                        "type": rtype,
                        "label": label,
                        "path": str(rel_path),
                        "url": f"/static/{rel_path}",
                        "exists": True,
                    })

                # Auch in Unterverzeichnissen suchen (z.B. ideas/idea_*/...)
                for subdir in report_dir.iterdir():
                    if subdir.is_dir():
                        sub_report = subdir / f"{prefix}{suffix}"
                        if sub_report.exists() and str(sub_report) not in found_paths:
                            found_paths.add(str(sub_report))
                            rel_path = sub_report.relative_to(base_dir)
                            report_links.append({
                                "type": rtype,
                                "label": f"{label} ({subdir.name})",
                                "path": str(rel_path),
                                "url": f"/static/{rel_path}",
                                "exists": True,
                            })

    # Meta-Links aus dem Experiment selbst (falls vorhanden)
    meta = experiment.get("meta", {})
    if meta.get("report_path"):
        report_path = Path(meta["report_path"])
        if report_path.exists():
            suffix = report_path.suffix.lower()
            rtype = {"html": "html", ".md": "markdown", ".json": "json"}.get(suffix, "file")
            report_links.append({
                "type": rtype,
                "label": f"📎 Meta Report ({report_path.name})",
                "path": str(report_path),
                "url": f"/static/{report_path.relative_to(base_dir)}",
                "exists": True,
            })

    return report_links


def compute_duration_info(experiment: dict[str, Any]) -> dict[str, Any] | None:
    """
    Berechnet Laufzeit-Informationen für ein Experiment (v1.2).

    Args:
        experiment: Experiment-Dict

    Returns:
        Dict mit start_time, end_time, duration_seconds oder None
    """
    meta = experiment.get("meta", {})
    exp_data = experiment.get("experiment", {})

    start_time = meta.get("start_time") or exp_data.get("timestamp")
    end_time = meta.get("end_time")

    if not start_time:
        return None

    result: dict[str, Any] = {"start_time": start_time}

    if end_time:
        result["end_time"] = end_time
        # Versuche Duration zu berechnen
        try:
            if len(start_time) >= 15 and len(end_time) >= 15:
                start_dt = datetime.strptime(start_time[:15], "%Y%m%d_%H%M%S")
                end_dt = datetime.strptime(end_time[:15], "%Y%m%d_%H%M%S")
                duration = (end_dt - start_dt).total_seconds()
                result["duration_seconds"] = duration
                result["duration_human"] = format_duration(duration)
        except (ValueError, TypeError):
            pass

    return result


def format_duration(seconds: float) -> str:
    """Formatiert Sekunden in menschenlesbare Form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def find_experiment_by_run_id(
    experiments: list[dict[str, Any]],
    run_id: str
) -> dict[str, Any] | None:
    """
    Findet ein Experiment anhand der Run-ID (v1.3).

    Zentralisierte Lookup-Logik für konsistentes Matching.

    Args:
        experiments: Liste aller Experimente
        run_id: Gesuchte Run-ID

    Returns:
        Experiment-Dict oder None wenn nicht gefunden
    """
    if not run_id or not run_id.strip():
        return None

    run_id = run_id.strip()

    for exp in experiments:
        filename = exp.get("_filename", "")
        exp_run_id = filename.replace(".json", "") if filename else ""

        # Exakter Match auf Run-ID oder Filename (präferiert)
        if run_id in (exp_run_id, filename):
            return exp

        # Match auf Timestamp nur wenn exakte Übereinstimmung
        timestamp = exp.get("experiment", {}).get("timestamp", "")
        if timestamp and run_id == timestamp:
            return exp

    return None


def compute_best_metrics(experiments: list[dict[str, Any]]) -> BestMetricsDict:
    """
    Berechnet die besten Werte pro Metrik für Comparison-Highlighting (v1.3).

    Für jede Metrik wird der "beste" Wert ermittelt:
    - "higher_is_better": total_return, sharpe, win_rate, profit_factor, total_trades
    - max_drawdown: der Wert am nächsten bei 0 gewinnt (also max(), da Drawdown negativ)

    Args:
        experiments: Liste von Experiment-Dicts mit flachen Metrik-Feldern

    Returns:
        BestMetricsDict mit besten Werten pro Metrik (nur gesetzte Felder)
    """
    if not experiments:
        return {}

    best_metrics: BestMetricsDict = {}

    # Metriken wo höher = besser
    higher_is_better = ["total_return", "sharpe", "win_rate", "profit_factor", "total_trades"]

    for metric in higher_is_better:
        values = [e.get(metric) for e in experiments if e.get(metric) is not None]
        if values:
            best_metrics[metric] = max(values)  # type: ignore[literal-required]

    # Max Drawdown: nächste zu 0 ist am besten (Drawdown ist typisch negativ)
    drawdowns = [e.get("max_drawdown") for e in experiments if e.get("max_drawdown") is not None]
    if drawdowns:
        best_metrics["max_drawdown"] = max(drawdowns)  # am wenigsten negativ

    return best_metrics


def extract_date_from_timestamp(timestamp: str) -> datetime | None:
    """Extrahiert ein Datum aus einem Timestamp im Format YYYYMMDD_HHMMSS."""
    if not timestamp or len(timestamp) < 8:
        return None
    try:
        return datetime.strptime(timestamp[:8], "%Y%m%d")
    except ValueError:
        return None


def filter_experiments(
    experiments: list[dict[str, Any]],
    preset: str | None = None,
    tag_substr: str | None = None,
    strategy: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
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

    date_from_dt = parse_date(date_from) if date_from else None
    date_to_dt = parse_date(date_to) if date_to else None

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


def compute_summary(experiments: list[dict[str, Any]]) -> dict[str, Any]:
    """Berechnet Summary-Statistiken."""
    by_status: dict[str, int] = defaultdict(int)
    experiments_with_trades = 0
    experiments_with_dummy = 0
    presets: set = set()
    strategies: set = set()

    for exp in experiments:
        flat = extract_flat_fields(exp)
        by_status[flat["status"]] += 1
        if flat["total_trades"] > 0:
            experiments_with_trades += 1
        if flat["use_dummy_data"]:
            experiments_with_dummy += 1
        if flat["preset_id"]:
            presets.add(flat["preset_id"])
        if flat["strategy"]:
            strategies.add(flat["strategy"])

    return {
        "total_experiments": len(experiments),
        "experiments_with_trades": experiments_with_trades,
        "experiments_with_dummy_data": experiments_with_dummy,
        "unique_presets": len(presets),
        "unique_strategies": len(strategies),
        "by_status": dict(by_status),
    }


def compute_preset_stats(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Berechnet Statistiken gruppiert nach Preset."""
    by_preset: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for exp in experiments:
        flat = extract_flat_fields(exp)
        preset_id = flat["preset_id"]
        if preset_id:
            by_preset[preset_id].append(flat)

    result = []
    for preset_id, exps in sorted(by_preset.items()):
        n = len(exps)
        with_trades = sum(1 for e in exps if e["total_trades"] > 0)
        total_trades = sum(e["total_trades"] for e in exps)

        returns = [e["total_return"] for e in exps]
        sharpes = [e["sharpe"] for e in exps]
        drawdowns = [e["max_drawdown"] for e in exps]
        win_rates = [e["win_rate"] for e in exps]

        result.append({
            "preset_id": preset_id,
            "experiment_count": n,
            "experiments_with_trades": with_trades,
            "avg_return": sum(returns) / n if n > 0 else 0.0,
            "avg_sharpe": sum(sharpes) / n if n > 0 else 0.0,
            "avg_max_drawdown": sum(drawdowns) / n if n > 0 else 0.0,
            "avg_win_rate": sum(win_rates) / n if n > 0 else 0.0,
            "total_trades": total_trades,
        })

    return result


def compute_strategy_stats(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Berechnet Statistiken gruppiert nach Strategy."""
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for exp in experiments:
        flat = extract_flat_fields(exp)
        strategy = flat["strategy"]
        if strategy:
            by_strategy[strategy].append(flat)

    result = []
    for strategy, exps in sorted(by_strategy.items()):
        n = len(exps)
        with_trades = sum(1 for e in exps if e["total_trades"] > 0)
        total_trades = sum(e["total_trades"] for e in exps)

        returns = [e["total_return"] for e in exps]
        sharpes = [e["sharpe"] for e in exps]
        drawdowns = [e["max_drawdown"] for e in exps]

        result.append({
            "strategy": strategy,
            "experiment_count": n,
            "experiments_with_trades": with_trades,
            "avg_return": sum(returns) / n if n > 0 else 0.0,
            "avg_sharpe": sum(sharpes) / n if n > 0 else 0.0,
            "avg_max_drawdown": sum(drawdowns) / n if n > 0 else 0.0,
            "total_trades": total_trades,
        })

    return result


def compute_global_stats(experiments: list[dict[str, Any]]) -> dict[str, Any]:
    """Berechnet globale Statistiken."""
    if not experiments:
        return {
            "total_experiments": 0,
            "unique_presets": 0,
            "unique_strategies": 0,
            "unique_symbols": 0,
            "experiments_with_trades": 0,
            "avg_sharpe": 0.0,
            "avg_return": 0.0,
            "avg_max_drawdown": 0.0,
            "median_sharpe": 0.0,
            "median_return": 0.0,
        }

    presets: set = set()
    strategies: set = set()
    symbols: set = set()
    with_trades = 0

    returns: list[float] = []
    sharpes: list[float] = []
    drawdowns: list[float] = []

    for exp in experiments:
        flat = extract_flat_fields(exp)
        if flat["preset_id"]:
            presets.add(flat["preset_id"])
        if flat["strategy"]:
            strategies.add(flat["strategy"])
        if flat["symbol"]:
            symbols.add(flat["symbol"])
        if flat["total_trades"] > 0:
            with_trades += 1

        returns.append(flat["total_return"])
        sharpes.append(flat["sharpe"])
        drawdowns.append(flat["max_drawdown"])

    n = len(experiments)

    # Median berechnen
    sorted_sharpes = sorted(sharpes)
    sorted_returns = sorted(returns)
    median_sharpe = sorted_sharpes[n // 2] if n > 0 else 0.0
    median_return = sorted_returns[n // 2] if n > 0 else 0.0

    return {
        "total_experiments": n,
        "unique_presets": len(presets),
        "unique_strategies": len(strategies),
        "unique_symbols": len(symbols),
        "experiments_with_trades": with_trades,
        "avg_sharpe": sum(sharpes) / n if n > 0 else 0.0,
        "avg_return": sum(returns) / n if n > 0 else 0.0,
        "avg_max_drawdown": sum(drawdowns) / n if n > 0 else 0.0,
        "median_sharpe": median_sharpe,
        "median_return": median_return,
    }


# =============================================================================
# API ROUTER
# =============================================================================


router = APIRouter(
    prefix="/api/r_and_d",
    tags=["r_and_d"],
)


@router.get(
    "/experiments",
    response_model=dict[str, Any],
    summary="Liste aller R&D-Experimente",
    description=(
        "Liefert eine Liste aller R&D-Experimente mit optionalen Filtern. "
        "Analog zu `scripts/view_r_and_d_experiments.py`."
    ),
)
async def list_experiments(
    preset: str | None = Query(None, description="Filter nach Preset-ID (exakt)"),
    tag_substr: str | None = Query(None, description="Filter nach Substring im Tag"),
    strategy: str | None = Query(None, description="Filter nach Strategy-ID (exakt)"),
    date_from: str | None = Query(None, description="Filter ab Datum (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter bis Datum (YYYY-MM-DD)"),
    with_trades: bool = Query(False, description="Nur Experimente mit Trades > 0"),
    limit: int = Query(200, ge=1, le=5000, description="Maximale Anzahl (1-5000)"),
) -> dict[str, Any]:
    """
    Liste aller R&D-Experimente mit Filtern.

    Returns:
        Dict mit:
        - items: Liste von Experiment-Summaries
        - total: Gesamtanzahl nach Filtern
        - filtered: Anzahl nach Filtern (vor Limit)
    """
    experiments = load_experiments_from_dir()

    # Filter anwenden
    filtered = filter_experiments(
        experiments,
        preset=preset,
        tag_substr=tag_substr,
        strategy=strategy,
        date_from=date_from,
        date_to=date_to,
        with_trades=with_trades,
    )

    filtered_count = len(filtered)

    # Limit anwenden
    limited = filtered[:limit]

    # In Summary-Format konvertieren
    items = [extract_flat_fields(exp) for exp in limited]

    return {
        "items": items,
        "total": len(experiments),
        "filtered": filtered_count,
        "returned": len(items),
    }


def parse_and_validate_run_ids(
    run_ids_str: str,
    min_ids: int = BATCH_MIN_RUN_IDS,
    max_ids: int = BATCH_MAX_RUN_IDS,
) -> list[str]:
    """
    Parst, dedupliziert und validiert eine komma-separierte Liste von Run-IDs (v1.3).

    - Entfernt Whitespace
    - Entfernt leere Strings
    - Dedupliziert unter Beibehaltung der Reihenfolge

    Args:
        run_ids_str: Komma-separierte Run-IDs (z.B. "run_1, run_2, run_3").
        min_ids: Minimale Anzahl an IDs nach Deduplizierung.
        max_ids: Maximale Anzahl an IDs nach Deduplizierung.

    Returns:
        Liste der eindeutigen Run-IDs.

    Raises:
        ValueError: Wenn nach Deduplizierung weniger als min_ids oder mehr als max_ids IDs.
    """
    # Parse und bereinige: Nur nicht-leere, getrimmte IDs
    raw_ids = [id.strip() for id in run_ids_str.split(",") if id.strip()]

    # Deduplizierung (Reihenfolge beibehalten)
    unique_ids = list(dict.fromkeys(raw_ids))

    # Validierung (Framework-agnostisch: ValueError statt HTTPException)
    if len(unique_ids) < min_ids:
        raise ValueError(f"Mindestens {min_ids} Run-IDs erforderlich")
    if len(unique_ids) > max_ids:
        raise ValueError(f"Maximal {max_ids} Run-IDs erlaubt")

    return unique_ids


def build_experiment_detail(exp: dict[str, Any]) -> dict[str, Any]:
    """
    Baut ein vollständiges Experiment-Detail-Dict (v1.3).

    Zentralisierte Logik für Detail- und Batch-Endpoints.

    Args:
        exp: Raw-Experiment-Dict aus JSON

    Returns:
        Aufbereitetes Detail-Dict
    """
    filename = exp.get("_filename", "")
    exp_run_id = filename.replace(".json", "") if filename else ""

    flat = extract_flat_fields(exp)
    report_links = find_report_links(exp_run_id, exp)
    duration_info = compute_duration_info(exp)

    return {
        "filename": filename,
        "run_id": exp_run_id,
        "experiment": exp.get("experiment", {}),
        "results": exp.get("results", {}),
        "meta": exp.get("meta", {}),
        "parameters": exp.get("parameters"),
        "report_links": report_links,
        "status": flat["status"],
        "run_type": flat["run_type"],
        "tier": flat["tier"],
        "experiment_category": flat["experiment_category"],
        "duration_info": duration_info,
        # Flache Felder für Comparison-View
        "total_return": flat["total_return"],
        "sharpe": flat["sharpe"],
        "max_drawdown": flat["max_drawdown"],
        "total_trades": flat["total_trades"],
        "win_rate": flat["win_rate"],
        "profit_factor": flat["profit_factor"],
        "preset_id": flat["preset_id"],
        "strategy": flat["strategy"],
        "symbol": flat["symbol"],
        "timeframe": flat["timeframe"],
        "tag": flat["tag"],
        "timestamp": flat["timestamp"],
    }


@router.get(
    "/experiments/batch",
    response_model=RnDBatchResponse,
    summary="Batch-Abfrage mehrerer Experimente (v1.3)",
    description=(
        "Liefert Details für mehrere Experimente in einer Abfrage. "
        "v1.3 (Phase 78): Für Multi-Run-Comparison. "
        "Unterstützt 2-10 Run-IDs pro Request."
    ),
)
async def get_experiments_batch(
    run_ids: str = Query(
        ...,
        description="Komma-separierte Liste von Run-IDs (2-10 IDs erforderlich)",
    ),
) -> RnDBatchResponse:
    """
    Batch-Endpoint für mehrere Experimente (v1.3 / Phase 78).

    Ermöglicht den Vergleich mehrerer R&D-Experimente in einer Abfrage.
    Ideal für Multi-Run-Comparison-Views.

    Args:
        run_ids: Komma-separierte Liste von Run-IDs

    Returns:
        RnDBatchResponse mit:
        - experiments: Liste der gefundenen Experiment-Details
        - requested_ids: Alle angeforderten IDs
        - found_ids: Erfolgreich gefundene IDs
        - not_found_ids: Nicht gefundene IDs
        - best_metrics: Beste Werte pro Metrik für Highlighting

    Raises:
        HTTPException 400: Weniger als 2 oder mehr als 10 IDs
        HTTPException 404: Keine gültigen Experimente gefunden
    """
    # Validiere und parse IDs (ValueError → HTTPException 400)
    try:
        unique_ids = parse_and_validate_run_ids(run_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Lade alle Experimente
    all_experiments = load_experiments_from_dir()

    # Suche nach den angeforderten IDs
    found_experiments: list[dict[str, Any]] = []
    found_ids: list[str] = []
    not_found_ids: list[str] = []

    for requested_id in unique_ids:
        exp = find_experiment_by_run_id(all_experiments, requested_id)

        if exp:
            experiment_data = build_experiment_detail(exp)
            found_experiments.append(experiment_data)
            found_ids.append(requested_id)
        else:
            not_found_ids.append(requested_id)

    # Wenn keine Experimente gefunden: 404
    if not found_experiments:
        raise HTTPException(
            status_code=404,
            detail=f"Keine gültigen Experimente gefunden für: {', '.join(unique_ids)}",
        )

    # Berechne Best-Metrics für Highlighting
    best_metrics = compute_best_metrics(found_experiments)

    return RnDBatchResponse(
        experiments=found_experiments,
        requested_ids=unique_ids,
        found_ids=found_ids,
        not_found_ids=not_found_ids,
        total_requested=len(unique_ids),
        total_found=len(found_experiments),
        best_metrics=best_metrics,
    )


@router.get(
    "/experiments/{run_id}",
    response_model=dict[str, Any],
    summary="Detail eines R&D-Experiments (v1.3)",
    description=(
        "Liefert alle Details eines einzelnen Experiments nach Run-ID. "
        "v1.3: Nutzt zentralisierte Lookup-Logik."
    ),
)
async def get_experiment_detail(run_id: str) -> dict[str, Any]:
    """
    Detail-Endpoint für ein einzelnes Experiment (v1.3).

    Args:
        run_id: Run-ID (Dateiname ohne .json oder exakter Timestamp)

    Returns:
        Vollständige Experiment-Details inkl.:
        - Raw-JSON
        - Report-Links (HTML/Markdown/PNG)
        - Status, Run-Type, Tier
        - Duration-Info

    Raises:
        HTTPException 404: Wenn Experiment nicht gefunden
    """
    experiments = load_experiments_from_dir()

    # Zentralisierte Lookup-Logik
    exp = find_experiment_by_run_id(experiments, run_id)

    if exp is None:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {run_id}")

    # Baue Detail-Response
    detail = build_experiment_detail(exp)
    # Füge raw hinzu (nur im Detail-Endpoint)
    detail["raw"] = exp

    return detail


@router.get(
    "/summary",
    response_model=RnDSummary,
    summary="Aggregierte Summary-Statistiken",
    description="Liefert aggregierte Statistiken über alle R&D-Experimente.",
)
async def get_summary() -> RnDSummary:
    """
    Summary-Statistiken über alle Experimente.

    Returns:
        RnDSummary mit Anzahlen und Status-Verteilung
    """
    experiments = load_experiments_from_dir()
    summary = compute_summary(experiments)
    return RnDSummary(**summary)


@router.get(
    "/presets",
    response_model=list[RnDPresetStats],
    summary="Statistiken nach Preset",
    description="Liefert aggregierte Statistiken gruppiert nach Preset-ID.",
)
async def get_presets() -> list[RnDPresetStats]:
    """
    Statistiken gruppiert nach Preset.

    Returns:
        Liste von RnDPresetStats pro Preset
    """
    experiments = load_experiments_from_dir()
    preset_stats = compute_preset_stats(experiments)
    return [RnDPresetStats(**s) for s in preset_stats]


@router.get(
    "/strategies",
    response_model=list[RnDStrategyStats],
    summary="Statistiken nach Strategy",
    description="Liefert aggregierte Statistiken gruppiert nach Strategy-ID.",
)
async def get_strategies() -> list[RnDStrategyStats]:
    """
    Statistiken gruppiert nach Strategy.

    Returns:
        Liste von RnDStrategyStats pro Strategy
    """
    experiments = load_experiments_from_dir()
    strategy_stats = compute_strategy_stats(experiments)
    return [RnDStrategyStats(**s) for s in strategy_stats]


@router.get(
    "/stats",
    response_model=RnDGlobalStats,
    summary="Globale R&D-Statistiken",
    description="Liefert globale Statistiken über alle R&D-Experimente.",
)
async def get_stats() -> RnDGlobalStats:
    """
    Globale Statistiken.

    Returns:
        RnDGlobalStats mit Durchschnitts- und Median-Werten
    """
    experiments = load_experiments_from_dir()
    stats = compute_global_stats(experiments)
    return RnDGlobalStats(**stats)


# =============================================================================
# v1.1 NEUE ENDPOINTS: Today & Running
# =============================================================================


@router.get(
    "/today",
    response_model=dict[str, Any],
    summary="Heute fertige Experimente (v1.1)",
    description=(
        "Liefert Experimente, die heute abgeschlossen wurden. "
        "Ideal für Daily R&D Review: 'Was ist heute fertig geworden?'"
    ),
)
async def get_today_experiments(
    limit: int = Query(50, ge=1, le=500, description="Max. Anzahl"),
) -> dict[str, Any]:
    """
    Experimente, die heute abgeschlossen wurden (v1.1).

    Returns:
        Dict mit:
        - items: Liste der heute fertigen Experimente
        - count: Anzahl
        - date: Heutiges Datum
    """
    from datetime import date

    today_str = date.today().strftime("%Y-%m-%d")
    experiments = load_experiments_from_dir()

    # Filter auf heute
    today_experiments = []
    for exp in experiments:
        flat = extract_flat_fields(exp)
        if flat["date_str"] == today_str and flat["status"] != "running":
            today_experiments.append(flat)

    # Limit anwenden
    limited = today_experiments[:limit]

    return {
        "items": limited,
        "count": len(today_experiments),
        "date": today_str,
        "success_count": sum(1 for e in today_experiments if e["status"] == "success"),
        "failed_count": sum(1 for e in today_experiments if e["status"] == "failed"),
    }


@router.get(
    "/running",
    response_model=dict[str, Any],
    summary="Aktuell laufende Experimente (v1.1)",
    description=(
        "Liefert Experimente, die aktuell noch laufen. "
        "Für 'Was läuft gerade?' Übersicht."
    ),
)
async def get_running_experiments() -> dict[str, Any]:
    """
    Aktuell laufende Experimente (v1.1).

    Returns:
        Dict mit:
        - items: Liste der laufenden Experimente
        - count: Anzahl
    """
    experiments = load_experiments_from_dir()

    running = []
    for exp in experiments:
        flat = extract_flat_fields(exp)
        if flat["status"] == "running":
            running.append(flat)

    return {
        "items": running,
        "count": len(running),
    }


@router.get(
    "/categories",
    response_model=dict[str, Any],
    summary="Experiment-Kategorien (v1.1)",
    description="Liefert verfügbare Experiment-Kategorien mit Counts.",
)
async def get_categories() -> dict[str, Any]:
    """
    Verfügbare Experiment-Kategorien (v1.1).

    Returns:
        Dict mit Kategorien und deren Experiment-Anzahl
    """
    experiments = load_experiments_from_dir()

    categories: dict[str, int] = {}
    run_types: dict[str, int] = {}

    for exp in experiments:
        flat = extract_flat_fields(exp)
        cat = flat.get("experiment_category", "general")
        rt = flat.get("run_type", "backtest")

        categories[cat] = categories.get(cat, 0) + 1
        run_types[rt] = run_types.get(rt, 0) + 1

    return {
        "categories": categories,
        "run_types": run_types,
        "category_labels": {
            "cycles": "Cycles & Timing",
            "volatility": "Volatility Models",
            "ml": "Machine Learning",
            "microstructure": "Microstructure",
            "general": "General",
        },
        "run_type_labels": {
            "backtest": "Backtest",
            "sweep": "Parameter Sweep",
            "monte_carlo": "Monte Carlo",
            "walkforward": "Walk-Forward",
        },
    }

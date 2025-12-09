# src/webui/r_and_d_api.py
"""
Peak_Trade: R&D Dashboard API v1.1 (Phase 76)
=============================================

API-Endpoints für das R&D-Dashboard:
- GET /api/r_and_d/experiments - Liste aller R&D-Experimente (mit Filtern)
- GET /api/r_and_d/experiments/{run_id} - Detail eines Experiments
- GET /api/r_and_d/summary - Aggregierte Summary-Statistiken
- GET /api/r_and_d/presets - Aggregation nach Preset
- GET /api/r_and_d/strategies - Aggregation nach Strategy
- GET /api/r_and_d/stats - Globale Statistiken
- GET /api/r_and_d/today - Heute fertige Experimente (Daily R&D View)
- GET /api/r_and_d/running - Aktuell laufende Experimente

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
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel


# =============================================================================
# KONFIGURATION
# =============================================================================

# Standard-Verzeichnis für R&D-Experimente (relativ zum Repo-Root)
# Wird von außen über BASE_DIR gesetzt
_BASE_DIR: Optional[Path] = None


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


class RnDExperimentDetail(BaseModel):
    """Vollständige Details eines R&D-Experiments."""
    filename: str
    run_id: str
    experiment: Dict[str, Any]
    results: Dict[str, Any]
    meta: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None
    raw: Dict[str, Any]


class RnDSummary(BaseModel):
    """Aggregierte Summary über alle R&D-Experimente."""
    total_experiments: int
    experiments_with_trades: int
    experiments_with_dummy_data: int
    unique_presets: int
    unique_strategies: int
    by_status: Dict[str, int]


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


# =============================================================================
# HILFSFUNKTIONEN
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
        data["_filepath"] = str(filepath)
        data["_filename"] = filepath.name
        return data
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        return None


def load_experiments_from_dir(dir_path: Optional[Path] = None) -> List[Dict[str, Any]]:
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

    experiments: List[Dict[str, Any]] = []
    json_files = list(experiments_dir.glob("*.json"))

    for json_file in json_files:
        data = load_experiment_json(json_file)
        if data is not None:
            experiments.append(data)

    # Sortiere nach Timestamp (neueste zuerst)
    def get_timestamp(exp: Dict[str, Any]) -> str:
        return exp.get("experiment", {}).get("timestamp", "")

    experiments.sort(key=get_timestamp, reverse=True)
    return experiments


def extract_flat_fields(exp: Dict[str, Any]) -> Dict[str, Any]:
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
        if "ehlers" in strategy or "ehlers" in preset:
            experiment_category = "cycles"
        elif "armstrong" in strategy or "armstrong" in preset:
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


def determine_status(exp: Dict[str, Any]) -> str:
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


def parse_date(date_str: str) -> Optional[datetime]:
    """Parst ein Datum im Format YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def extract_date_from_timestamp(timestamp: str) -> Optional[datetime]:
    """Extrahiert ein Datum aus einem Timestamp im Format YYYYMMDD_HHMMSS."""
    if not timestamp or len(timestamp) < 8:
        return None
    try:
        return datetime.strptime(timestamp[:8], "%Y%m%d")
    except ValueError:
        return None


def filter_experiments(
    experiments: List[Dict[str, Any]],
    preset: Optional[str] = None,
    tag_substr: Optional[str] = None,
    strategy: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    with_trades: bool = False,
) -> List[Dict[str, Any]]:
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


def compute_summary(experiments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Berechnet Summary-Statistiken."""
    by_status: Dict[str, int] = defaultdict(int)
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


def compute_preset_stats(experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Berechnet Statistiken gruppiert nach Preset."""
    by_preset: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

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


def compute_strategy_stats(experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Berechnet Statistiken gruppiert nach Strategy."""
    by_strategy: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

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


def compute_global_stats(experiments: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    returns: List[float] = []
    sharpes: List[float] = []
    drawdowns: List[float] = []

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
    response_model=Dict[str, Any],
    summary="Liste aller R&D-Experimente",
    description=(
        "Liefert eine Liste aller R&D-Experimente mit optionalen Filtern. "
        "Analog zu `scripts/view_r_and_d_experiments.py`."
    ),
)
async def list_experiments(
    preset: Optional[str] = Query(None, description="Filter nach Preset-ID (exakt)"),
    tag_substr: Optional[str] = Query(None, description="Filter nach Substring im Tag"),
    strategy: Optional[str] = Query(None, description="Filter nach Strategy-ID (exakt)"),
    date_from: Optional[str] = Query(None, description="Filter ab Datum (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter bis Datum (YYYY-MM-DD)"),
    with_trades: bool = Query(False, description="Nur Experimente mit Trades > 0"),
    limit: int = Query(200, ge=1, le=5000, description="Maximale Anzahl (1-5000)"),
) -> Dict[str, Any]:
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


@router.get(
    "/experiments/{run_id}",
    response_model=Dict[str, Any],
    summary="Detail eines R&D-Experiments",
    description="Liefert alle Details eines einzelnen Experiments nach Run-ID.",
)
async def get_experiment_detail(run_id: str) -> Dict[str, Any]:
    """
    Detail-Endpoint für ein einzelnes Experiment.

    Args:
        run_id: Run-ID (Dateiname ohne .json oder Timestamp-Substring)

    Returns:
        Vollständige Experiment-Details inkl. Raw-JSON

    Raises:
        HTTPException 404: Wenn Experiment nicht gefunden
    """
    experiments = load_experiments_from_dir()

    for exp in experiments:
        filename = exp.get("_filename", "")
        exp_run_id = filename.replace(".json", "") if filename else ""
        timestamp = exp.get("experiment", {}).get("timestamp", "")

        # Match auf Run-ID oder Timestamp-Substring
        if run_id == exp_run_id or run_id in filename or run_id in timestamp:
            return {
                "filename": filename,
                "run_id": exp_run_id,
                "experiment": exp.get("experiment", {}),
                "results": exp.get("results", {}),
                "meta": exp.get("meta", {}),
                "parameters": exp.get("parameters"),
                "raw": exp,
            }

    raise HTTPException(status_code=404, detail=f"Experiment not found: {run_id}")


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
    response_model=List[RnDPresetStats],
    summary="Statistiken nach Preset",
    description="Liefert aggregierte Statistiken gruppiert nach Preset-ID.",
)
async def get_presets() -> List[RnDPresetStats]:
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
    response_model=List[RnDStrategyStats],
    summary="Statistiken nach Strategy",
    description="Liefert aggregierte Statistiken gruppiert nach Strategy-ID.",
)
async def get_strategies() -> List[RnDStrategyStats]:
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
    response_model=Dict[str, Any],
    summary="Heute fertige Experimente (v1.1)",
    description=(
        "Liefert Experimente, die heute abgeschlossen wurden. "
        "Ideal für Daily R&D Review: 'Was ist heute fertig geworden?'"
    ),
)
async def get_today_experiments(
    limit: int = Query(50, ge=1, le=500, description="Max. Anzahl"),
) -> Dict[str, Any]:
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
    response_model=Dict[str, Any],
    summary="Aktuell laufende Experimente (v1.1)",
    description=(
        "Liefert Experimente, die aktuell noch laufen. "
        "Für 'Was läuft gerade?' Übersicht."
    ),
)
async def get_running_experiments() -> Dict[str, Any]:
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
    response_model=Dict[str, Any],
    summary="Experiment-Kategorien (v1.1)",
    description="Liefert verfügbare Experiment-Kategorien mit Counts.",
)
async def get_categories() -> Dict[str, Any]:
    """
    Verfügbare Experiment-Kategorien (v1.1).

    Returns:
        Dict mit Kategorien und deren Experiment-Anzahl
    """
    experiments = load_experiments_from_dir()

    categories: Dict[str, int] = {}
    run_types: Dict[str, int] = {}

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

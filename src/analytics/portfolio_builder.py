# src/analytics/portfolio_builder.py
"""
Peak_Trade – Auto-Portfolio-Builder
====================================
Erzeugt automatisch Portfolio-Kandidaten aus Sweep- und Market-Scan-Ergebnissen.

Features:
- Selektion der besten Sweep-Ergebnisse pro Strategie/Symbol
- Kombination mit Market-Scan-Signalen
- Export als TOML-Configs für run_portfolio_backtest.py

Usage:
    from src.analytics.portfolio_builder import (
        build_portfolio_candidates_from_sweeps_and_scans,
        write_portfolio_candidate_to_toml,
    )
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from src.analytics.experiments_analysis import (
    filter_sweeps,
    filter_market_scans,
)


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class PortfolioComponentCandidate:
    """
    Ein einzelner Bestandteil eines Portfolio-Kandidaten.

    Attributes:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        strategy_key: Strategie-Name (z.B. "ma_crossover")
        timeframe: Timeframe (z.B. "1h")
        weight: Gewichtung im Portfolio (0.0 - 1.0)
        source_run_id: Run-ID aus der Registry
        metric_score: Wert der Selektionsmetrik (z.B. Sharpe)
        params: Strategie-Parameter aus Sweep
    """

    symbol: str
    strategy_key: str
    timeframe: str
    weight: float
    source_run_id: str
    metric_score: float
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioCandidate:
    """
    Ein automatisch generierter Portfolio-Kandidat.

    Attributes:
        name: Name des Portfolios (z.B. "auto_ma_core")
        components: Liste von PortfolioComponentCandidate
        allocation_method: Allokationsmethode (z.B. "equal", "sharpe_weighted")
        initial_equity: Anfangskapital
        created_at: Erstellungszeitpunkt
        source_tag: Tag der Quell-Runs
    """

    name: str
    components: List[PortfolioComponentCandidate]
    allocation_method: str = "equal"
    initial_equity: float = 10000.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z")
    source_tag: Optional[str] = None


# =============================================================================
# SELECTION FUNCTIONS
# =============================================================================


def select_top_sweep_components(
    df: pd.DataFrame,
    *,
    metric: str = "sharpe",
    max_per_symbol: int = 1,
    max_per_strategy: int = 3,
    max_total: int = 10,
    strategy_keys: Optional[Sequence[str]] = None,
    symbols: Optional[Sequence[str]] = None,
    timeframes: Optional[Sequence[str]] = None,
    min_sharpe: Optional[float] = None,
    min_return: Optional[float] = None,
    tag: Optional[str] = None,
) -> List[PortfolioComponentCandidate]:
    """
    Selektiert die besten Sweep-Ergebnisse als Portfolio-Komponenten.

    Args:
        df: DataFrame mit Experiment-Daten (wird auf sweeps gefiltert)
        metric: Sortiermetrik ("sharpe", "total_return", "cagr")
        max_per_symbol: Maximale Komponenten pro Symbol
        max_per_strategy: Maximale Komponenten pro Strategie
        max_total: Maximale Gesamtanzahl Komponenten
        strategy_keys: Filter auf bestimmte Strategien
        symbols: Filter auf bestimmte Symbole
        timeframes: Filter auf bestimmte Timeframes
        min_sharpe: Minimaler Sharpe-Wert
        min_return: Minimaler Total-Return
        tag: Filter auf bestimmten Tag (aus metadata_json)

    Returns:
        Liste von PortfolioComponentCandidate
    """
    # Nur Sweeps filtern
    df_sweeps = filter_sweeps(df)

    if df_sweeps.empty:
        return []

    # Strategie-Filter
    if strategy_keys is not None and "strategy_key" in df_sweeps.columns:
        df_sweeps = df_sweeps[df_sweeps["strategy_key"].isin(strategy_keys)]

    # Symbol-Filter
    if symbols is not None and "symbol" in df_sweeps.columns:
        df_sweeps = df_sweeps[df_sweeps["symbol"].isin(symbols)]

    # Timeframe-Filter (aus metadata_json extrahieren)
    if timeframes is not None and "metadata_json" in df_sweeps.columns:

        def get_timeframe(meta_json: str) -> Optional[str]:
            try:
                meta = json.loads(meta_json) if meta_json else {}
                return meta.get("timeframe")
            except (json.JSONDecodeError, TypeError):
                return None

        df_sweeps = df_sweeps.copy()
        df_sweeps["_timeframe"] = df_sweeps["metadata_json"].apply(get_timeframe)
        df_sweeps = df_sweeps[df_sweeps["_timeframe"].isin(timeframes)]

    # Tag-Filter
    if tag is not None and "metadata_json" in df_sweeps.columns:

        def get_tag(meta_json: str) -> Optional[str]:
            try:
                meta = json.loads(meta_json) if meta_json else {}
                return meta.get("tag")
            except (json.JSONDecodeError, TypeError):
                return None

        df_sweeps = df_sweeps.copy()
        df_sweeps["_tag"] = df_sweeps["metadata_json"].apply(get_tag)
        df_sweeps = df_sweeps[df_sweeps["_tag"] == tag]

    # Metriken numerisch konvertieren
    for col in ["sharpe", "total_return", "cagr", "max_drawdown"]:
        if col in df_sweeps.columns:
            df_sweeps[col] = pd.to_numeric(df_sweeps[col], errors="coerce")

    # Minimum-Filter
    if min_sharpe is not None and "sharpe" in df_sweeps.columns:
        df_sweeps = df_sweeps[df_sweeps["sharpe"] >= min_sharpe]

    if min_return is not None and "total_return" in df_sweeps.columns:
        df_sweeps = df_sweeps[df_sweeps["total_return"] >= min_return]

    if df_sweeps.empty:
        return []

    # Nach Metrik sortieren (absteigend)
    if metric not in df_sweeps.columns:
        metric = "sharpe"  # Fallback

    df_sweeps = df_sweeps.sort_values(by=metric, ascending=False)

    # Komponenten extrahieren
    candidates: List[PortfolioComponentCandidate] = []
    symbol_counts: Dict[str, int] = {}
    strategy_counts: Dict[str, int] = {}

    for _, row in df_sweeps.iterrows():
        symbol = str(row.get("symbol", ""))
        strategy_key = str(row.get("strategy_key", ""))

        # Limits prüfen
        if symbol_counts.get(symbol, 0) >= max_per_symbol:
            continue
        if strategy_counts.get(strategy_key, 0) >= max_per_strategy:
            continue
        if len(candidates) >= max_total:
            break

        # Timeframe aus metadata extrahieren
        timeframe = "1h"  # Default
        try:
            meta = json.loads(row.get("metadata_json", "{}") or "{}")
            timeframe = meta.get("timeframe", "1h")
        except (json.JSONDecodeError, TypeError):
            pass

        # Parameter aus params_json extrahieren
        params = {}
        try:
            params = json.loads(row.get("params_json", "{}") or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        # Metrik-Score
        metric_score = float(row.get(metric, 0) or 0)

        candidate = PortfolioComponentCandidate(
            symbol=symbol,
            strategy_key=strategy_key,
            timeframe=timeframe,
            weight=0.0,  # Wird später berechnet
            source_run_id=str(row.get("run_id", "")),
            metric_score=metric_score,
            params=params,
        )
        candidates.append(candidate)

        # Zähler aktualisieren
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        strategy_counts[strategy_key] = strategy_counts.get(strategy_key, 0) + 1

    return candidates


def select_top_market_scan_components(
    df: pd.DataFrame,
    *,
    mode: str = "backtest-lite",
    metric: str = "sharpe",
    max_per_symbol: int = 1,
    max_total: int = 10,
    strategy_keys: Optional[Sequence[str]] = None,
    symbols: Optional[Sequence[str]] = None,
    min_sharpe: Optional[float] = None,
    min_return: Optional[float] = None,
    tag: Optional[str] = None,
) -> List[PortfolioComponentCandidate]:
    """
    Selektiert die besten Market-Scan-Ergebnisse als Portfolio-Komponenten.

    Funktioniert primär für mode="backtest-lite", wo Stats verfügbar sind.

    Args:
        df: DataFrame mit Experiment-Daten
        mode: Scan-Modus ("forward" oder "backtest-lite")
        metric: Sortiermetrik ("sharpe", "total_return")
        max_per_symbol: Maximale Komponenten pro Symbol
        max_total: Maximale Gesamtanzahl
        strategy_keys: Filter auf bestimmte Strategien
        symbols: Filter auf bestimmte Symbole
        min_sharpe: Minimaler Sharpe
        min_return: Minimaler Total-Return
        tag: Filter auf Tag

    Returns:
        Liste von PortfolioComponentCandidate
    """
    # Nur Market-Scans filtern
    df_scans = filter_market_scans(df)

    if df_scans.empty:
        return []

    # Mode-Filter
    if "metadata_json" in df_scans.columns:

        def get_mode(meta_json: str) -> Optional[str]:
            try:
                meta = json.loads(meta_json) if meta_json else {}
                return meta.get("mode")
            except (json.JSONDecodeError, TypeError):
                return None

        df_scans = df_scans.copy()
        df_scans["_mode"] = df_scans["metadata_json"].apply(get_mode)
        df_scans = df_scans[df_scans["_mode"] == mode]

    # Strategie-Filter
    if strategy_keys is not None and "strategy_key" in df_scans.columns:
        df_scans = df_scans[df_scans["strategy_key"].isin(strategy_keys)]

    # Symbol-Filter
    if symbols is not None and "symbol" in df_scans.columns:
        df_scans = df_scans[df_scans["symbol"].isin(symbols)]

    # Tag-Filter
    if tag is not None and "metadata_json" in df_scans.columns:

        def get_tag(meta_json: str) -> Optional[str]:
            try:
                meta = json.loads(meta_json) if meta_json else {}
                return meta.get("tag")
            except (json.JSONDecodeError, TypeError):
                return None

        df_scans["_tag"] = df_scans["metadata_json"].apply(get_tag)
        df_scans = df_scans[df_scans["_tag"] == tag]

    # Stats aus stats_json extrahieren
    def extract_stats(stats_json: str) -> Dict[str, Any]:
        try:
            return json.loads(stats_json) if stats_json else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    df_scans = df_scans.copy()
    df_scans["_stats"] = df_scans.get("stats_json", "{}").apply(extract_stats)
    df_scans["_sharpe"] = df_scans["_stats"].apply(lambda s: s.get("sharpe", 0) or 0)
    df_scans["_total_return"] = df_scans["_stats"].apply(lambda s: s.get("total_return", 0) or 0)

    # Minimum-Filter
    if min_sharpe is not None:
        df_scans = df_scans[df_scans["_sharpe"] >= min_sharpe]

    if min_return is not None:
        df_scans = df_scans[df_scans["_total_return"] >= min_return]

    if df_scans.empty:
        return []

    # Nach Metrik sortieren
    sort_col = f"_{metric}" if f"_{metric}" in df_scans.columns else "_sharpe"
    df_scans = df_scans.sort_values(by=sort_col, ascending=False)

    # Komponenten extrahieren
    candidates: List[PortfolioComponentCandidate] = []
    symbol_counts: Dict[str, int] = {}

    for _, row in df_scans.iterrows():
        symbol = str(row.get("symbol", ""))
        strategy_key = str(row.get("strategy_key", ""))

        if symbol_counts.get(symbol, 0) >= max_per_symbol:
            continue
        if len(candidates) >= max_total:
            break

        # Timeframe aus metadata
        timeframe = "1h"
        try:
            meta = json.loads(row.get("metadata_json", "{}") or "{}")
            timeframe = meta.get("timeframe", "1h")
        except (json.JSONDecodeError, TypeError):
            pass

        # Metric Score
        stats = row.get("_stats", {})
        metric_score = float(stats.get(metric, 0) or 0)

        candidate = PortfolioComponentCandidate(
            symbol=symbol,
            strategy_key=strategy_key,
            timeframe=timeframe,
            weight=0.0,
            source_run_id=str(row.get("run_id", "")),
            metric_score=metric_score,
            params={},  # Market-Scans haben keine optimierten Params
        )
        candidates.append(candidate)
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    return candidates


# =============================================================================
# PORTFOLIO BUILDER
# =============================================================================


def build_portfolio_candidates_from_sweeps_and_scans(
    *,
    df_sweeps: pd.DataFrame,
    df_scans: Optional[pd.DataFrame] = None,
    metric: str = "sharpe",
    max_components: int = 5,
    min_sharpe: Optional[float] = None,
    min_return: Optional[float] = None,
    name_prefix: str = "auto_portfolio",
    allocation_method: str = "equal",
    initial_equity: float = 10000.0,
    tag: Optional[str] = None,
    prefer_sweeps: bool = True,
) -> List[PortfolioCandidate]:
    """
    Erzeugt automatische Portfolio-Kandidaten aus Sweep- und Market-Scan-Ergebnissen.

    Strategie:
    1. Aus Sweeps die beste Parameterkombination pro Strategie/Symbol wählen
    2. Optional aus Market-Scans Symbole ergänzen
    3. Gewichte berechnen (equal oder metric-based)
    4. PortfolioCandidate erstellen

    Args:
        df_sweeps: DataFrame mit Sweep-Daten
        df_scans: Optional DataFrame mit Market-Scan-Daten
        metric: Selektionsmetrik ("sharpe", "total_return")
        max_components: Maximale Anzahl Komponenten pro Portfolio
        min_sharpe: Minimaler Sharpe für Selektion
        min_return: Minimaler Total-Return
        name_prefix: Präfix für Portfolio-Namen
        allocation_method: "equal" oder "metric_weighted"
        initial_equity: Anfangskapital
        tag: Filter auf bestimmten Tag
        prefer_sweeps: Sweep-Ergebnisse bevorzugen (vs. Scans)

    Returns:
        Liste von PortfolioCandidate
    """
    all_components: List[PortfolioComponentCandidate] = []

    # 1. Sweep-Komponenten sammeln
    if not df_sweeps.empty:
        sweep_components = select_top_sweep_components(
            df_sweeps,
            metric=metric,
            max_per_symbol=1,
            max_per_strategy=max_components,
            max_total=max_components,
            min_sharpe=min_sharpe,
            min_return=min_return,
            tag=tag,
        )
        all_components.extend(sweep_components)

    # 2. Optional Scan-Komponenten ergänzen
    if df_scans is not None and not df_scans.empty and len(all_components) < max_components:
        remaining = max_components - len(all_components)
        existing_symbols = {c.symbol for c in all_components}

        scan_components = select_top_market_scan_components(
            df_scans,
            mode="backtest-lite",
            metric=metric,
            max_per_symbol=1,
            max_total=remaining,
            min_sharpe=min_sharpe,
            min_return=min_return,
            tag=tag,
        )

        # Nur Symbole hinzufügen, die noch nicht im Portfolio sind
        for comp in scan_components:
            if comp.symbol not in existing_symbols:
                all_components.append(comp)
                existing_symbols.add(comp.symbol)
                if len(all_components) >= max_components:
                    break

    if not all_components:
        return []

    # 3. Gewichte berechnen
    n = len(all_components)

    if allocation_method == "equal":
        weight = 1.0 / n
        for comp in all_components:
            comp.weight = weight

    elif allocation_method == "metric_weighted":
        total_score = sum(max(c.metric_score, 0.0) for c in all_components)
        if total_score > 0:
            for comp in all_components:
                comp.weight = max(comp.metric_score, 0.0) / total_score
        else:
            # Fallback auf equal
            weight = 1.0 / n
            for comp in all_components:
                comp.weight = weight

    else:
        # Default: equal
        weight = 1.0 / n
        for comp in all_components:
            comp.weight = weight

    # 4. Portfolio-Kandidat erstellen
    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    portfolio_name = f"{name_prefix}_{n}comp_{ts_label}"

    candidate = PortfolioCandidate(
        name=portfolio_name,
        components=all_components,
        allocation_method=allocation_method,
        initial_equity=initial_equity,
        source_tag=tag,
    )

    return [candidate]


def build_multiple_portfolio_candidates(
    *,
    df: pd.DataFrame,
    strategies: Optional[Sequence[str]] = None,
    metric: str = "sharpe",
    max_components_per_portfolio: int = 5,
    min_sharpe: Optional[float] = None,
    name_prefix: str = "auto",
    initial_equity: float = 10000.0,
) -> List[PortfolioCandidate]:
    """
    Erzeugt mehrere Portfolio-Kandidaten, gruppiert nach Strategie.

    Erstellt pro Strategie ein separates Portfolio mit den besten Symbolen.

    Args:
        df: DataFrame mit Experiment-Daten
        strategies: Liste von Strategien (None = alle)
        metric: Selektionsmetrik
        max_components_per_portfolio: Max. Komponenten pro Portfolio
        min_sharpe: Minimaler Sharpe
        name_prefix: Präfix für Portfolio-Namen
        initial_equity: Anfangskapital

    Returns:
        Liste von PortfolioCandidate (eines pro Strategie)
    """
    df_sweeps = filter_sweeps(df)

    if df_sweeps.empty:
        return []

    # Strategien ermitteln
    if strategies is None:
        strategies = df_sweeps["strategy_key"].unique().tolist()

    candidates: List[PortfolioCandidate] = []

    for strategy_key in strategies:
        # Nur Sweeps dieser Strategie
        df_strat = df_sweeps[df_sweeps["strategy_key"] == strategy_key]

        if df_strat.empty:
            continue

        # Komponenten für diese Strategie
        components = select_top_sweep_components(
            df_strat,
            metric=metric,
            max_per_symbol=1,
            max_per_strategy=max_components_per_portfolio,
            max_total=max_components_per_portfolio,
            min_sharpe=min_sharpe,
        )

        if not components:
            continue

        # Gewichte berechnen
        n = len(components)
        for comp in components:
            comp.weight = 1.0 / n

        # Portfolio erstellen
        ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        portfolio_name = f"{name_prefix}_{strategy_key}_{n}sym_{ts_label}"

        candidate = PortfolioCandidate(
            name=portfolio_name,
            components=components,
            allocation_method="equal",
            initial_equity=initial_equity,
        )
        candidates.append(candidate)

    return candidates


# =============================================================================
# TOML EXPORT
# =============================================================================


def write_portfolio_candidate_to_toml(
    candidate: PortfolioCandidate,
    path: Path,
) -> None:
    """
    Schreibt einen PortfolioCandidate in eine TOML-Datei.

    Die erzeugte Datei ist kompatibel mit run_portfolio_backtest.py.

    Args:
        candidate: PortfolioCandidate zu exportieren
        path: Zielpfad der TOML-Datei

    Example Output:
        [portfolio]
        name = "auto_ma_core_3comp_20250104_120000"
        initial_equity = 10000.0
        allocation_method = "equal"

        [[portfolio.symbols]]
        symbol = "BTC/EUR"
        strategy = "ma_crossover"
        timeframe = "1h"
        weight = 0.33
        # source_run_id = "abc-123"
        # metric_score = 1.5
        # params = { short_window = 10, long_window = 50 }
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    # Header-Kommentar
    lines.append(f"# Auto-Generated Portfolio: {candidate.name}")
    lines.append(f"# Created: {candidate.created_at}")
    if candidate.source_tag:
        lines.append(f"# Source Tag: {candidate.source_tag}")
    lines.append("")

    # [portfolio] Section
    lines.append("[portfolio]")
    lines.append(f'name = "{candidate.name}"')
    lines.append(f"initial_equity = {candidate.initial_equity}")
    lines.append(f'allocation_method = "{candidate.allocation_method}"')
    lines.append("")

    # Symbols-Liste für Kompatibilität mit run_portfolio_backtest.py
    symbols = [comp.symbol for comp in candidate.components]
    symbols_str = ", ".join(f'"{s}"' for s in symbols)
    lines.append(f"symbols = [{symbols_str}]")
    lines.append("")

    # Asset-Weights
    weights = [comp.weight for comp in candidate.components]
    weights_str = ", ".join(f"{w:.4f}" for w in weights)
    lines.append(f"asset_weights = [{weights_str}]")
    lines.append("")

    # Default-Strategie (erste Komponente)
    if candidate.components:
        default_strategy = candidate.components[0].strategy_key
        lines.append(f'strategy_key = "{default_strategy}"')
        lines.append("")

    # Symbol-spezifische Strategien
    lines.append("[portfolio.strategies]")
    for comp in candidate.components:
        symbol_escaped = comp.symbol.replace("/", "_")
        lines.append(f'"{comp.symbol}" = "{comp.strategy_key}"')
    lines.append("")

    # Detaillierte Komponenten-Infos als Kommentare
    lines.append("# ==========================================================")
    lines.append("# Component Details (for reference)")
    lines.append("# ==========================================================")
    lines.append("")

    for i, comp in enumerate(candidate.components, 1):
        lines.append(f"# Component {i}: {comp.symbol}")
        lines.append(f"#   Strategy: {comp.strategy_key}")
        lines.append(f"#   Timeframe: {comp.timeframe}")
        lines.append(f"#   Weight: {comp.weight:.4f}")
        lines.append(f"#   Metric Score: {comp.metric_score:.4f}")
        lines.append(f"#   Source Run ID: {comp.source_run_id}")
        if comp.params:
            params_str = ", ".join(f"{k}={v}" for k, v in comp.params.items())
            lines.append(f"#   Params: {{ {params_str} }}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def format_portfolio_candidate_summary(candidate: PortfolioCandidate) -> str:
    """
    Formatiert einen PortfolioCandidate für Console-Ausgabe.

    Args:
        candidate: PortfolioCandidate

    Returns:
        Formatierter String
    """
    lines = []
    lines.append(f"Portfolio: {candidate.name}")
    lines.append(f"  Components: {len(candidate.components)}")
    lines.append(f"  Allocation: {candidate.allocation_method}")
    lines.append(f"  Initial Equity: {candidate.initial_equity:,.2f}")
    lines.append("")

    lines.append("  Components:")
    for comp in candidate.components:
        lines.append(
            f"    - {comp.symbol:<12} {comp.strategy_key:<18} "
            f"weight={comp.weight:.2%} score={comp.metric_score:.3f}"
        )
        if comp.params:
            params_str = ", ".join(f"{k}={v}" for k, v in list(comp.params.items())[:3])
            lines.append(f"      params: {params_str}")

    return "\n".join(lines)

# src/experiments/topn_promotion.py
"""
Peak_Trade Top-N Promotion (Phase 42)
=====================================

Automatische Auswahl und Export der Top-N Konfigurationen aus Sweep-Ergebnissen.

Komponenten:
- TopNPromotionConfig: Konfiguration für Top-N Promotion
- load_sweep_results: Lädt Sweep-Ergebnisse
- select_top_n: Wählt Top-N Konfigurationen nach Metrik
- export_top_n: Exportiert Top-N in TOML-Format

Usage:
    from src.experiments.topn_promotion import (
        TopNPromotionConfig,
        load_sweep_results,
        select_top_n,
        export_top_n,
    )

    config = TopNPromotionConfig(
        sweep_name="rsi_reversion_basic",
        metric_primary="metric_sharpe_ratio",
        top_n=5,
    )
    df = load_sweep_results(config)
    df_top = select_top_n(df, config)
    output_path = export_top_n(df_top, config)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import toml

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class TopNPromotionConfig:
    """
    Konfiguration für Top-N Promotion.

    Attributes:
        sweep_name: Name des Sweeps (z.B. "rsi_reversion_basic")
        metric_primary: Primäre Metrik für Sortierung (default: "metric_sharpe_ratio")
        metric_fallback: Fallback-Metrik falls primary fehlt (default: "metric_total_return")
        top_n: Anzahl der Top-Konfigurationen (default: 5)
        output_path: Ausgabe-Verzeichnis (default: "reports/sweeps")
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen (default: "reports/experiments")
    """

    sweep_name: str
    metric_primary: str = "metric_sharpe_ratio"
    metric_fallback: str = "metric_total_return"
    top_n: int = 5
    output_path: Path = field(default_factory=lambda: Path("reports/sweeps"))
    experiments_dir: Path = field(default_factory=lambda: Path("reports/experiments"))

    def __post_init__(self) -> None:
        """Normalisiert Pfade."""
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if isinstance(self.experiments_dir, str):
            self.experiments_dir = Path(self.experiments_dir)


# =============================================================================
# LOAD RESULTS
# =============================================================================


def find_sweep_results(sweep_name: str, experiments_dir: Path) -> Optional[Path]:
    """
    Sucht nach der neuesten Ergebnis-Datei für einen Sweep.

    Args:
        sweep_name: Name des Sweeps
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen

    Returns:
        Pfad zur Datei oder None
    """
    if not experiments_dir.exists():
        return None

    # Suche nach passenden CSV-Dateien (mit sweep_name im Dateinamen)
    pattern = f"*{sweep_name}*.csv"
    matches = sorted(experiments_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if matches:
        return matches[0]

    # Suche nach Parquet-Dateien
    pattern = f"*{sweep_name}*.parquet"
    matches = sorted(experiments_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if matches:
        return matches[0]

    # Fallback: Versuche strategy_name zu extrahieren
    parts = sweep_name.split("_")
    if len(parts) >= 2:
        strategy_name = "_".join(parts[:-1])
        pattern = f"*{strategy_name}*.csv"
        matches = sorted(experiments_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]

    return None


def load_sweep_results(config: TopNPromotionConfig) -> pd.DataFrame:
    """
    Lädt Sweep-Ergebnisse aus CSV oder Parquet.

    Args:
        config: TopNPromotionConfig

    Returns:
        DataFrame mit Sweep-Ergebnissen

    Raises:
        FileNotFoundError: Wenn keine Ergebnisse gefunden werden
        ValueError: Bei ungültigem Dateiformat
    """
    filepath = find_sweep_results(config.sweep_name, config.experiments_dir)

    if filepath is None:
        raise FileNotFoundError(
            f"Keine Ergebnisse gefunden für Sweep '{config.sweep_name}' in {config.experiments_dir}. "
            f"Führe zuerst einen Sweep aus: "
            f"python scripts/run_strategy_sweep.py --sweep-name {config.sweep_name}"
        )

    logger.info(f"Lade Sweep-Ergebnisse aus: {filepath}")

    # Lade Datei
    if filepath.suffix == ".parquet":
        df = pd.read_parquet(filepath)
    elif filepath.suffix == ".csv":
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")

    logger.info(f"Geladen: {len(df)} Runs")
    return df


# =============================================================================
# SELECT TOP N
# =============================================================================


def select_top_n(
    df: pd.DataFrame, config: TopNPromotionConfig
) -> Tuple[pd.DataFrame, str]:
    """
    Wählt Top-N Konfigurationen nach Metrik aus.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
        config: TopNPromotionConfig

    Returns:
        Tuple von (DataFrame mit Top-N Runs, verwendete Metrik)

    Raises:
        ValueError: Wenn keine gültige Metrik gefunden wird oder keine Daten übrig sind
    """
    # Bestimme Metrik (primary oder fallback)
    metric_used = config.metric_primary
    if metric_used not in df.columns:
        logger.warning(
            f"Metrik '{config.metric_primary}' nicht gefunden, verwende Fallback: {config.metric_fallback}"
        )
        metric_used = config.metric_fallback

    if metric_used not in df.columns:
        available = [c for c in df.columns if c.startswith("metric_")]
        raise ValueError(
            f"Weder '{config.metric_primary}' noch '{config.metric_fallback}' gefunden. "
            f"Verfügbare Metriken: {available}"
        )

    # Filtere NaN-Werte
    df_valid = df[df[metric_used].notna()].copy()

    if len(df_valid) == 0:
        raise ValueError(
            f"Keine gültigen Runs mit Metrik '{metric_used}' gefunden (alle NaN)"
        )

    logger.info(f"Verwende Metrik: {metric_used} ({len(df_valid)} gültige Runs)")

    # Sortiere absteigend und nimm Top-N
    df_top = df_valid.nlargest(config.top_n, metric_used).copy()

    # Füge Rank hinzu
    df_top.insert(0, "rank", range(1, len(df_top) + 1))

    logger.info(f"Top {len(df_top)} Konfigurationen ausgewählt")
    return df_top, metric_used


# =============================================================================
# EXPORT TOP N
# =============================================================================


def export_top_n(
    df_top: pd.DataFrame, config: TopNPromotionConfig
) -> Path:
    """
    Exportiert Top-N Konfigurationen in TOML-Format.

    Args:
        df_top: DataFrame mit Top-N Runs (muss "rank" Spalte enthalten)
        config: TopNPromotionConfig
        metric_used: Die verwendete Metrik (aus select_top_n)

    Returns:
        Pfad zur erzeugten TOML-Datei
    """
    # Erstelle Output-Verzeichnis
    config.output_path.mkdir(parents=True, exist_ok=True)

    # Bestimme verwendete Metrik (aus Config oder DataFrame)
    metric_used = config.metric_primary
    if metric_used not in df_top.columns:
        metric_used = config.metric_fallback

    # Baue TOML-Struktur
    toml_data: Dict[str, Any] = {
        "meta": {
            "sweep_name": config.sweep_name,
            "metric_used": metric_used,
            "top_n": len(df_top),
            "generated_at": datetime.now().isoformat(),
        },
        "candidates": [],
    }

    # Extrahiere Param- und Metrik-Spalten
    param_cols = [c for c in df_top.columns if c.startswith("param_")]
    metric_cols = [c for c in df_top.columns if c.startswith("metric_")]

    # Erstelle Einträge für jeden Kandidaten
    for _, row in df_top.iterrows():
        candidate: Dict[str, Any] = {
            "rank": int(row["rank"]),
        }

        # Experiment-ID falls vorhanden
        if "experiment_id" in row.index:
            candidate["experiment_id"] = str(row["experiment_id"])

        # Metriken
        for col in metric_cols:
            val = row[col]
            if pd.notna(val):
                # Entferne "metric_" Prefix für TOML
                key = col.replace("metric_", "")
                candidate[key] = float(val)

        # Parameter
        params: Dict[str, Any] = {}
        for col in param_cols:
            val = row[col]
            if pd.notna(val):
                # Entferne "param_" Prefix für TOML
                key = col.replace("param_", "")
                # Konvertiere zu Python-Typen
                if isinstance(val, (int, float)):
                    params[key] = float(val) if isinstance(val, float) else int(val)
                elif isinstance(val, bool):
                    params[key] = bool(val)
                elif isinstance(val, str):
                    params[key] = str(val)
                else:
                    params[key] = str(val)

        candidate["params"] = params

        toml_data["candidates"].append(candidate)

    # Schreibe TOML-Datei
    output_file = config.output_path / f"{config.sweep_name}_top_candidates.toml"
    with open(output_file, "w") as f:
        toml.dump(toml_data, f)

    logger.info(f"Top-N Kandidaten exportiert: {output_file}")
    return output_file


# =============================================================================
# LOAD TOP N CONFIGS FOR WALK-FORWARD
# =============================================================================


def load_top_n_configs_for_sweep(
    sweep_name: str,
    n: int,
    *,
    metric_primary: str = "metric_sharpe_ratio",
    metric_fallback: str = "metric_total_return",
    experiments_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Lädt die Top-N-Strategiekonfigurationen für einen gegebenen Sweep.

    Diese Funktion kann entweder:
    1. Top-N direkt aus Sweep-Ergebnissen auswählen (wenn TOML nicht existiert)
    2. Top-N aus bereits exportierter TOML-Datei laden (falls vorhanden)

    Args:
        sweep_name: Name des Sweeps (z.B. "rsi_reversion_basic")
        n: Anzahl der Top-Konfigurationen
        metric_primary: Primäre Metrik für Sortierung (default: "metric_sharpe_ratio")
        metric_fallback: Fallback-Metrik falls primary fehlt (default: "metric_total_return")
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen (default: "reports/experiments")
        output_path: Verzeichnis für Top-N-TOML (default: "reports/sweeps")

    Returns:
        Liste von Dicts, jeder enthält:
        - "config_id": Eindeutige ID (z.B. "config_1" oder experiment_id)
        - "strategy_name": Name der Strategie (aus sweep_name abgeleitet)
        - "params": Parameter-Dict (ohne "param_" Prefix)
        - "metrics": Metriken-Dict (ohne "metric_" Prefix)
        - "rank": Rang (1-basiert)

    Raises:
        FileNotFoundError: Wenn keine Sweep-Ergebnisse gefunden werden
        ValueError: Bei ungültigen Daten oder fehlenden Metriken

    Example:
        >>> configs = load_top_n_configs_for_sweep("rsi_reversion_basic", top_n=3)
        >>> for config in configs:
        ...     print(f"Rank {config['rank']}: {config['config_id']}")
        ...     print(f"  Params: {config['params']}")
    """
    if experiments_dir is None:
        experiments_dir = Path("reports/experiments")
    if output_path is None:
        output_path = Path("reports/sweeps")

    # Versuche zuerst, aus TOML zu laden (falls bereits exportiert)
    toml_file = output_path / f"{sweep_name}_top_candidates.toml"
    if toml_file.exists():
        logger.info(f"Lade Top-N-Konfigurationen aus TOML: {toml_file}")
        return _load_configs_from_toml(toml_file, n)

    # Fallback: Lade direkt aus Sweep-Ergebnissen
    logger.info(f"TOML nicht gefunden, lade Top-N direkt aus Sweep-Ergebnissen")
    config = TopNPromotionConfig(
        sweep_name=sweep_name,
        metric_primary=metric_primary,
        metric_fallback=metric_fallback,
        top_n=n,
        experiments_dir=experiments_dir,
        output_path=output_path,
    )

    # Lade Sweep-Ergebnisse
    df = load_sweep_results(config)

    # Wähle Top-N
    df_top, metric_used = select_top_n(df, config)

    # Konvertiere zu Config-Dicts
    configs = _dataframe_to_config_dicts(df_top, sweep_name, metric_used)

    return configs


def _load_configs_from_toml(toml_file: Path, n: int) -> List[Dict[str, Any]]:
    """
    Lädt Top-N-Konfigurationen aus TOML-Datei.

    Args:
        toml_file: Pfad zur TOML-Datei
        n: Anzahl der Konfigurationen (maximal)

    Returns:
        Liste von Config-Dicts
    """
    import toml

    with open(toml_file, "r") as f:
        toml_data = toml.load(f)

    candidates = toml_data.get("candidates", [])
    meta = toml_data.get("meta", {})

    # Extrahiere Strategiename aus sweep_name (z.B. "rsi_reversion_basic" -> "rsi_reversion")
    sweep_name = meta.get("sweep_name", "")
    strategy_name = _extract_strategy_name(sweep_name)

    configs = []
    for i, candidate in enumerate(candidates[:n], 1):
        config_id = candidate.get("experiment_id", f"config_{i}")
        config = {
            "config_id": config_id,
            "strategy_name": strategy_name,
            "params": candidate.get("params", {}),
            "metrics": {k: v for k, v in candidate.items() if k not in ["rank", "experiment_id", "params"]},
            "rank": candidate.get("rank", i),
        }
        configs.append(config)

    logger.info(f"{len(configs)} Konfigurationen aus TOML geladen")
    return configs


def _parse_string_value(val: Any) -> Any:
    """
    Konvertiert String-Repräsentationen von Listen/Dicts zurück zu Python-Objekten.

    CSV-Dateien speichern komplexe Typen als Strings. Diese Funktion erkennt
    solche Strings und konvertiert sie zurück.

    Args:
        val: Wert aus DataFrame (kann String, int, float, etc. sein)

    Returns:
        Konvertierter Wert oder Original

    Examples:
        >>> _parse_string_value("['a', 'b']")
        ['a', 'b']
        >>> _parse_string_value("{'x': 1}")
        {'x': 1}
        >>> _parse_string_value("hello")
        'hello'
    """
    if not isinstance(val, str):
        return val

    val_stripped = val.strip()

    # Prüfe auf Liste (beginnt mit [ und endet mit ])
    if val_stripped.startswith("[") and val_stripped.endswith("]"):
        try:
            import ast
            return ast.literal_eval(val_stripped)
        except (ValueError, SyntaxError):
            return val

    # Prüfe auf Dict (beginnt mit { und endet mit })
    if val_stripped.startswith("{") and val_stripped.endswith("}"):
        try:
            import ast
            return ast.literal_eval(val_stripped)
        except (ValueError, SyntaxError):
            return val

    # Prüfe auf Tuple (beginnt mit ( und endet mit ))
    if val_stripped.startswith("(") and val_stripped.endswith(")"):
        try:
            import ast
            return ast.literal_eval(val_stripped)
        except (ValueError, SyntaxError):
            return val

    return val


def _dataframe_to_config_dicts(
    df_top: pd.DataFrame, sweep_name: str, metric_used: str
) -> List[Dict[str, Any]]:
    """
    Konvertiert DataFrame mit Top-N Runs zu Config-Dicts.

    Args:
        df_top: DataFrame mit Top-N Runs (muss "rank" Spalte enthalten)
        sweep_name: Name des Sweeps
        metric_used: Verwendete Metrik

    Returns:
        Liste von Config-Dicts
    """
    strategy_name = _extract_strategy_name(sweep_name)

    # Extrahiere Spalten
    param_cols = [c for c in df_top.columns if c.startswith("param_")]
    metric_cols = [c for c in df_top.columns if c.startswith("metric_")]

    configs = []
    for _, row in df_top.iterrows():
        # Config-ID (experiment_id falls vorhanden, sonst rank-basiert)
        config_id = str(row.get("experiment_id", f"config_{int(row['rank'])}"))

        # Parameter (ohne "param_" Prefix)
        params = {}
        for col in param_cols:
            val = row[col]
            if pd.notna(val):
                key = col.replace("param_", "")
                # Konvertiere zu Python-Typen
                # Zuerst: Prüfe ob String-Repräsentation von Liste/Dict
                parsed_val = _parse_string_value(val)
                if isinstance(parsed_val, (list, dict, tuple)):
                    params[key] = parsed_val
                elif isinstance(val, (int, float)):
                    params[key] = float(val) if isinstance(val, float) else int(val)
                elif isinstance(val, bool):
                    params[key] = bool(val)
                else:
                    params[key] = str(val)

        # Metriken (ohne "metric_" Prefix)
        metrics = {}
        for col in metric_cols:
            val = row[col]
            if pd.notna(val):
                key = col.replace("metric_", "")
                metrics[key] = float(val)

        config = {
            "config_id": config_id,
            "strategy_name": strategy_name,
            "params": params,
            "metrics": metrics,
            "rank": int(row["rank"]),
        }
        configs.append(config)

    return configs


def _extract_strategy_name(sweep_name: str) -> str:
    """
    Extrahiert Strategiename aus Sweep-Namen.

    Beispiel:
        "rsi_reversion_basic" -> "rsi_reversion"
        "ma_crossover_medium" -> "ma_crossover"
    """
    # Entferne typische Suffixe (_basic, _medium, _large, etc.)
    parts = sweep_name.split("_")
    if len(parts) >= 2:
        # Versuche, Suffix zu erkennen
        known_suffixes = ["basic", "medium", "large", "small", "full", "conservative", "aggressive", "fine", "coarse"]
        if parts[-1] in known_suffixes:
            return "_".join(parts[:-1])
    return sweep_name


# =============================================================================
# POLICY CRITIC INTEGRATION EXAMPLE (Phase G2)
# =============================================================================

def export_top_n_with_policy_check(
    df_top: pd.DataFrame,
    config: TopNPromotionConfig,
    auto_apply: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, Dict[str, Any]]:
    """
    Export Top-N configs with optional policy critic check for auto-apply.

    This demonstrates Phase G2 integration: Before any automated config
    application (auto-apply), the policy critic MUST be consulted.

    Args:
        df_top: DataFrame with top-N runs
        config: TopNPromotionConfig
        auto_apply: If True, attempt automated application (requires policy approval)
        context: Optional context for policy critic (justification, test_plan, etc.)

    Returns:
        Tuple of (output_path, governance_report)

    Example:
        >>> df_top, metric = select_top_n(df, config)
        >>> output_path, gov_report = export_top_n_with_policy_check(
        ...     df_top,
        ...     config,
        ...     auto_apply=True,
        ...     context={
        ...         "run_id": "promo-123",
        ...         "source": "topn_promotion",
        ...         "justification": "Based on 6-month backtest results",
        ...         "test_plan": "Shadow mode verification for 24h",
        ...     }
        ... )
        >>> if not gov_report["auto_apply_decision"]["allowed"]:
        ...     logger.warning("Auto-apply blocked by policy critic")
    """
    # Standard export (always happens)
    output_path = export_top_n(df_top, config)

    # Initialize governance report
    governance_report = {
        "export_path": str(output_path),
        "auto_apply_requested": auto_apply,
        "auto_apply_decision": None,
        "policy_critic": None,
    }

    # If auto-apply requested, check policy critic
    if auto_apply:
        try:
            from src.governance.policy_critic.auto_apply_gate import (
                evaluate_policy_critic_before_apply,
            )

            # Generate diff from TOML export (simplified - in real scenario,
            # this would be diff of actual config changes to be applied)
            with open(output_path, "r") as f:
                new_config_content = f.read()

            # Simplified diff (in real scenario, compare against current config)
            diff_text = f"+++ b/config/promoted_configs.toml\n{new_config_content}"
            changed_files = [str(output_path.relative_to(Path.cwd()))]

            # Evaluate policy critic
            decision = evaluate_policy_critic_before_apply(
                diff_text=diff_text,
                changed_files=changed_files,
                context=context or {},
                fail_closed=True,  # Always fail-closed
            )

            # Update governance report
            governance_report["auto_apply_decision"] = decision.to_dict()

            # Log decision
            if decision.allowed:
                logger.info(f"Policy critic ALLOWS auto-apply: {decision.reason}")
            else:
                logger.warning(f"Policy critic BLOCKS auto-apply: {decision.reason}")
                logger.warning(f"Mode: {decision.mode.value}")

        except ImportError:
            # Policy critic not available - fail-closed
            logger.warning("Policy critic not available - failing closed (manual only)")
            governance_report["auto_apply_decision"] = {
                "allowed": False,
                "mode": "manual_only",
                "reason": "Policy critic module not available (fail-closed)",
                "decided_at": datetime.now().isoformat(),
            }
        except Exception as e:
            # Any error - fail-closed
            logger.error(f"Policy critic evaluation failed: {e}", exc_info=True)
            governance_report["auto_apply_decision"] = {
                "allowed": False,
                "mode": "manual_only",
                "reason": f"Policy critic evaluation error (fail-closed): {str(e)}",
                "decided_at": datetime.now().isoformat(),
            }

    return output_path, governance_report


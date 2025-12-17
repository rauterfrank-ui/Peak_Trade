# src/experiments/strategy_profiles.py
"""
Peak_Trade Strategy Profiles (Phase 41B)
=========================================

Zentrales Modul für Strategy-Robustness-Profile und Tiering.

Features:
- StrategyProfile Datenmodell mit Performance, Robustness und Regime-Metriken
- Tiering-System (core, aux, legacy)
- JSON/Markdown Export
- Integration mit bestehender Sweep/Monte-Carlo/Stress-Test Infrastruktur

Usage:
    from src.experiments.strategy_profiles import (
        StrategyProfile,
        StrategyProfileBuilder,
        load_tiering_config,
        generate_strategy_profile,
    )

    # Profil generieren
    profile = generate_strategy_profile(
        strategy_id="rsi_reversion",
        config_path="config/config.toml",
        with_regime=True,
        with_montecarlo=True,
        with_stress=True,
    )

    # Als JSON exportieren
    profile.to_json("reports/strategy_profiles/rsi_reversion_profile_v1.json")

    # Als Markdown exportieren
    profile.to_markdown("docs/strategy_profiles/RSI_REVERSION_PROFILE_v1.md")
"""
from __future__ import annotations

import json
import logging

# tomllib ist erst ab Python 3.11 verfügbar, Fallback zu tomli
import tomllib  # type: ignore
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

PROFILE_VERSION = "v1"
# Tier-Typen für Strategy-Klassifikation:
# - core: Primäre Strategien für Hauptportfolio (Live-fähig nach Freigabe)
# - aux: Ergänzende Strategien mit spezifischen Stärken
# - legacy: Ältere Strategien, nur zu Vergleichszwecken
# - r_and_d: Research & Development - NICHT für Live-Trading freigegeben
# - unclassified: Noch nicht klassifiziert
TIER_TYPES = Literal["core", "aux", "legacy", "r_and_d", "unclassified"]

# Label-Mapping für Dashboard-Anzeige
TIER_LABELS = {
    "core": "Core",
    "aux": "Auxiliary",
    "legacy": "Legacy",
    "r_and_d": "R&D / Research",
    "unclassified": "Unclassified",
}


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class Metadata:
    """
    Metadaten eines Strategy-Profils.

    Attributes:
        strategy_id: Eindeutiger Strategie-Identifier (z.B. "rsi_reversion")
        profile_version: Version des Profil-Formats (z.B. "v1")
        created_at: Erstellungszeitpunkt
        data_range: Datenbereich für Backtests (z.B. "2018-01-01..2024-12-31")
        symbols: Liste der getesteten Symbole
        timeframe: Zeitrahmen (z.B. "1h", "4h")
    """

    strategy_id: str
    profile_version: str = PROFILE_VERSION
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    data_range: str | None = None
    symbols: list[str] = field(default_factory=list)
    timeframe: str = "1h"

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "profile_version": self.profile_version,
            "created_at": self.created_at,
            "data_range": self.data_range,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
        }


@dataclass
class PerformanceMetrics:
    """
    Baseline-Performance-Metriken einer Strategie.

    Attributes:
        sharpe: Sharpe Ratio (annualisiert)
        cagr: Compound Annual Growth Rate
        max_drawdown: Maximaler Drawdown (negativ, z.B. -0.15 = -15%)
        volatility: Annualisierte Volatilität
        winrate: Win-Rate (0.0 - 1.0)
        avg_trade: Durchschnittlicher Trade-Return
        trade_count: Gesamtanzahl der Trades
        total_return: Gesamt-Return
        sortino: Sortino Ratio (optional)
        calmar: Calmar Ratio (optional)
        profit_factor: Profit Factor (optional)
    """

    sharpe: float = 0.0
    cagr: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    winrate: float | None = None
    avg_trade: float | None = None
    trade_count: int = 0
    total_return: float = 0.0
    sortino: float | None = None
    calmar: float | None = None
    profit_factor: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "sharpe": self.sharpe,
            "cagr": self.cagr,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "winrate": self.winrate,
            "avg_trade": self.avg_trade,
            "trade_count": self.trade_count,
            "total_return": self.total_return,
            "sortino": self.sortino,
            "calmar": self.calmar,
            "profit_factor": self.profit_factor,
        }

    @classmethod
    def from_backtest_stats(cls, stats: dict[str, Any]) -> PerformanceMetrics:
        """
        Erstellt PerformanceMetrics aus Backtest-Stats.

        Args:
            stats: Dict mit Backtest-Metriken (z.B. von compute_backtest_stats)

        Returns:
            PerformanceMetrics-Objekt
        """
        return cls(
            sharpe=float(stats.get("sharpe", stats.get("sharpe_ratio", 0.0))),
            cagr=float(stats.get("cagr", 0.0)),
            max_drawdown=float(stats.get("max_drawdown", 0.0)),
            volatility=float(stats.get("volatility", 0.0)),
            winrate=stats.get("win_rate", stats.get("winrate")),
            avg_trade=stats.get("avg_trade", stats.get("expectancy")),
            trade_count=int(stats.get("total_trades", stats.get("trade_count", 0))),
            total_return=float(stats.get("total_return", 0.0)),
            sortino=stats.get("sortino"),
            calmar=stats.get("calmar"),
            profit_factor=stats.get("profit_factor"),
        )


@dataclass
class RobustnessMetrics:
    """
    Robustness-Metriken basierend auf Monte-Carlo und Stress-Tests.

    Attributes:
        param_sensitivity_index: Parameter-Sensitivitäts-Index (0 = robust, 1 = sensitiv)
        montecarlo_p5: Monte-Carlo 5%-Perzentil Return
        montecarlo_p50: Monte-Carlo Median Return
        montecarlo_p95: Monte-Carlo 95%-Perzentil Return
        montecarlo_sharpe_p5: Monte-Carlo 5%-Perzentil Sharpe
        montecarlo_sharpe_p95: Monte-Carlo 95%-Perzentil Sharpe
        stress_min: Minimaler Return unter Stress-Szenarien
        stress_max: Maximaler Return unter Stress-Szenarien
        stress_avg: Durchschnittlicher Return unter Stress-Szenarien
        num_montecarlo_runs: Anzahl Monte-Carlo-Runs
        num_stress_scenarios: Anzahl Stress-Szenarien
    """

    param_sensitivity_index: float | None = None
    montecarlo_p5: float | None = None
    montecarlo_p50: float | None = None
    montecarlo_p95: float | None = None
    montecarlo_sharpe_p5: float | None = None
    montecarlo_sharpe_p95: float | None = None
    stress_min: float | None = None
    stress_max: float | None = None
    stress_avg: float | None = None
    num_montecarlo_runs: int = 0
    num_stress_scenarios: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "param_sensitivity_index": self.param_sensitivity_index,
            "montecarlo_p5": self.montecarlo_p5,
            "montecarlo_p50": self.montecarlo_p50,
            "montecarlo_p95": self.montecarlo_p95,
            "montecarlo_sharpe_p5": self.montecarlo_sharpe_p5,
            "montecarlo_sharpe_p95": self.montecarlo_sharpe_p95,
            "stress_min": self.stress_min,
            "stress_max": self.stress_max,
            "stress_avg": self.stress_avg,
            "num_montecarlo_runs": self.num_montecarlo_runs,
            "num_stress_scenarios": self.num_stress_scenarios,
        }


@dataclass
class SingleRegimeProfile:
    """
    Profil für ein einzelnes Marktregime.

    Attributes:
        name: Regime-Name (z.B. "risk_on", "neutral", "risk_off")
        contribution_return: Return-Beitrag dieses Regimes (absolut)
        time_share: Zeitanteil in diesem Regime (0.0 - 1.0)
        efficiency_ratio: Effizienz (contribution / time_share)
        trade_count: Anzahl Trades in diesem Regime
        avg_return: Durchschnittlicher Return pro Trade in diesem Regime
    """

    name: str
    contribution_return: float = 0.0
    time_share: float = 0.0
    efficiency_ratio: float = 0.0
    trade_count: int = 0
    avg_return: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "name": self.name,
            "contribution_return": self.contribution_return,
            "time_share": self.time_share,
            "efficiency_ratio": self.efficiency_ratio,
            "trade_count": self.trade_count,
            "avg_return": self.avg_return,
        }


@dataclass
class RegimeProfile:
    """
    Aggregiertes Regime-Profil mit allen Regime-Analysen.

    Attributes:
        regimes: Liste von SingleRegimeProfile
        dominant_regime: Regime mit höchstem Return-Beitrag
        weakest_regime: Regime mit niedrigstem Return-Beitrag
    """

    regimes: list[SingleRegimeProfile] = field(default_factory=list)
    dominant_regime: str | None = None
    weakest_regime: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "regimes": [r.to_dict() for r in self.regimes],
            "dominant_regime": self.dominant_regime,
            "weakest_regime": self.weakest_regime,
        }


@dataclass
class StrategyTieringInfo:
    """
    Tiering-Informationen für eine Strategie.

    Attributes:
        tier: Tier-Level ("core", "aux", "legacy", "unclassified")
        reason: Begründung für das Tiering
        recommended_config_id: Empfohlene Config-ID für diese Strategie
        allow_live: Ob Live-Trading erlaubt ist
        notes: Zusätzliche Anmerkungen
    """

    tier: TIER_TYPES = "unclassified"
    reason: str = ""
    recommended_config_id: str | None = None
    allow_live: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "tier": self.tier,
            "reason": self.reason,
            "recommended_config_id": self.recommended_config_id,
            "allow_live": self.allow_live,
            "notes": self.notes,
        }


@dataclass
class StrategyProfile:
    """
    Zentrales Datenmodell für ein vollständiges Strategy-Profil.

    Kombiniert:
    - Metadaten
    - Performance-Metriken (Baseline)
    - Robustness-Metriken (Monte-Carlo, Stress-Tests)
    - Regime-Profil
    - Tiering-Informationen

    Attributes:
        metadata: Metadaten des Profils
        performance: Baseline-Performance-Metriken
        robustness: Robustness-Metriken
        regimes: Optionales Regime-Profil
        tiering: Optionale Tiering-Informationen
    """

    metadata: Metadata
    performance: PerformanceMetrics
    robustness: RobustnessMetrics = field(default_factory=RobustnessMetrics)
    regimes: RegimeProfile | None = None
    tiering: StrategyTieringInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary für JSON-Export."""
        result = {
            "metadata": self.metadata.to_dict(),
            "performance": self.performance.to_dict(),
            "robustness": self.robustness.to_dict(),
        }

        if self.regimes is not None:
            result["regimes"] = self.regimes.to_dict()

        if self.tiering is not None:
            result["tiering"] = self.tiering.to_dict()

        return result

    def to_json(self, filepath: str | Path, indent: int = 2) -> None:
        """
        Exportiert das Profil als JSON-Datei.

        Args:
            filepath: Pfad zur Ausgabedatei
            indent: JSON-Indentation
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

        logger.info(f"Strategy-Profil exportiert: {filepath}")

    @classmethod
    def from_json(cls, filepath: str | Path) -> StrategyProfile:
        """
        Lädt ein Profil aus einer JSON-Datei.

        Args:
            filepath: Pfad zur JSON-Datei

        Returns:
            StrategyProfile-Objekt
        """
        filepath = Path(filepath)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyProfile:
        """
        Erstellt ein Profil aus einem Dictionary.

        Args:
            data: Dictionary mit Profil-Daten

        Returns:
            StrategyProfile-Objekt
        """
        metadata = Metadata(
            strategy_id=data["metadata"]["strategy_id"],
            profile_version=data["metadata"].get("profile_version", PROFILE_VERSION),
            created_at=data["metadata"].get("created_at", datetime.now().isoformat()),
            data_range=data["metadata"].get("data_range"),
            symbols=data["metadata"].get("symbols", []),
            timeframe=data["metadata"].get("timeframe", "1h"),
        )

        perf_data = data.get("performance", {})
        performance = PerformanceMetrics(
            sharpe=perf_data.get("sharpe", 0.0),
            cagr=perf_data.get("cagr", 0.0),
            max_drawdown=perf_data.get("max_drawdown", 0.0),
            volatility=perf_data.get("volatility", 0.0),
            winrate=perf_data.get("winrate"),
            avg_trade=perf_data.get("avg_trade"),
            trade_count=perf_data.get("trade_count", 0),
            total_return=perf_data.get("total_return", 0.0),
            sortino=perf_data.get("sortino"),
            calmar=perf_data.get("calmar"),
            profit_factor=perf_data.get("profit_factor"),
        )

        rob_data = data.get("robustness", {})
        robustness = RobustnessMetrics(
            param_sensitivity_index=rob_data.get("param_sensitivity_index"),
            montecarlo_p5=rob_data.get("montecarlo_p5"),
            montecarlo_p50=rob_data.get("montecarlo_p50"),
            montecarlo_p95=rob_data.get("montecarlo_p95"),
            montecarlo_sharpe_p5=rob_data.get("montecarlo_sharpe_p5"),
            montecarlo_sharpe_p95=rob_data.get("montecarlo_sharpe_p95"),
            stress_min=rob_data.get("stress_min"),
            stress_max=rob_data.get("stress_max"),
            stress_avg=rob_data.get("stress_avg"),
            num_montecarlo_runs=rob_data.get("num_montecarlo_runs", 0),
            num_stress_scenarios=rob_data.get("num_stress_scenarios", 0),
        )

        regimes = None
        if data.get("regimes"):
            regime_data = data["regimes"]
            regime_list = [
                SingleRegimeProfile(
                    name=r["name"],
                    contribution_return=r.get("contribution_return", 0.0),
                    time_share=r.get("time_share", 0.0),
                    efficiency_ratio=r.get("efficiency_ratio", 0.0),
                    trade_count=r.get("trade_count", 0),
                    avg_return=r.get("avg_return", 0.0),
                )
                for r in regime_data.get("regimes", [])
            ]
            regimes = RegimeProfile(
                regimes=regime_list,
                dominant_regime=regime_data.get("dominant_regime"),
                weakest_regime=regime_data.get("weakest_regime"),
            )

        tiering = None
        if data.get("tiering"):
            tier_data = data["tiering"]
            tiering = StrategyTieringInfo(
                tier=tier_data.get("tier", "unclassified"),
                reason=tier_data.get("reason", ""),
                recommended_config_id=tier_data.get("recommended_config_id"),
                allow_live=tier_data.get("allow_live", False),
                notes=tier_data.get("notes", ""),
            )

        return cls(
            metadata=metadata,
            performance=performance,
            robustness=robustness,
            regimes=regimes,
            tiering=tiering,
        )

    def to_markdown(self, filepath: str | Path) -> None:
        """
        Exportiert das Profil als Markdown-Datei.

        Args:
            filepath: Pfad zur Ausgabedatei
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        md_content = generate_markdown_profile(self)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Markdown-Profil exportiert: {filepath}")


# =============================================================================
# TIERING CONFIG
# =============================================================================


def load_tiering_config(
    config_path: str | Path = "config/strategy_tiering.toml",
) -> dict[str, StrategyTieringInfo]:
    """
    Lädt die Tiering-Konfiguration aus einer TOML-Datei.

    Args:
        config_path: Pfad zur TOML-Datei

    Returns:
        Dict mit strategy_id -> StrategyTieringInfo

    Example:
        >>> tiering = load_tiering_config()
        >>> info = tiering.get("rsi_reversion")
        >>> print(f"Tier: {info.tier}")
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Tiering-Config nicht gefunden: {config_path}")
        return {}

    if tomllib is None:
        logger.warning("tomllib/tomli nicht verfügbar, kann Tiering-Config nicht laden")
        return {}

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    result: dict[str, StrategyTieringInfo] = {}

    strategies = data.get("strategy", {})
    for strategy_id, info in strategies.items():
        result[strategy_id] = StrategyTieringInfo(
            tier=info.get("tier", "unclassified"),
            reason=info.get("notes", ""),
            recommended_config_id=info.get("recommended_config_id"),
            allow_live=info.get("allow_live", False),
            notes=info.get("notes", ""),
        )

    logger.info(f"Tiering-Config geladen: {len(result)} Strategien")
    return result


def get_tiering_for_strategy(
    strategy_id: str,
    tiering_config: dict[str, StrategyTieringInfo] | None = None,
) -> StrategyTieringInfo:
    """
    Holt Tiering-Info für eine Strategie.

    Args:
        strategy_id: Strategie-ID
        tiering_config: Optionale vorkonfigurierte Tiering-Config

    Returns:
        StrategyTieringInfo (oder Default wenn nicht gefunden)
    """
    if tiering_config is None:
        tiering_config = load_tiering_config()

    return tiering_config.get(
        strategy_id,
        StrategyTieringInfo(
            tier="unclassified",
            reason="Kein Tiering-Eintrag vorhanden",
        ),
    )


# =============================================================================
# MARKDOWN GENERATION
# =============================================================================


def _format_percent(value: float | None, digits: int = 2) -> str:
    """Formatiert einen Wert als Prozent."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def _format_number(value: float | None, digits: int = 2) -> str:
    """Formatiert eine Zahl."""
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def generate_markdown_profile(profile: StrategyProfile) -> str:
    """
    Generiert Markdown-Content aus einem StrategyProfile.

    Args:
        profile: StrategyProfile-Objekt

    Returns:
        Markdown-String
    """
    meta = profile.metadata
    perf = profile.performance
    rob = profile.robustness

    lines = [
        f"# Strategy Profile - {meta.strategy_id.upper()}",
        "",
        "## 1. Meta",
        "",
        f"- **Strategy ID:** `{meta.strategy_id}`",
        f"- **Version:** {meta.profile_version}",
        f"- **Erstellt:** {meta.created_at}",
        f"- **Daten:** {meta.data_range or 'N/A'}",
        f"- **Universe:** {', '.join(meta.symbols) if meta.symbols else 'N/A'}",
        f"- **Timeframe:** {meta.timeframe}",
        "",
        "---",
        "",
        "## 2. Performance (Baseline)",
        "",
        "| Metrik | Wert |",
        "|--------|------|",
        f"| Sharpe | {_format_number(perf.sharpe)} |",
        f"| CAGR | {_format_percent(perf.cagr)} |",
        f"| Max Drawdown | {_format_percent(perf.max_drawdown)} |",
        f"| Volatilität | {_format_percent(perf.volatility)} |",
        f"| Total Return | {_format_percent(perf.total_return)} |",
        f"| Winrate | {_format_percent(perf.winrate)} |",
        f"| Avg. Trade | {_format_percent(perf.avg_trade)} |",
        f"| Trades | {perf.trade_count} |",
    ]

    if perf.sortino is not None:
        lines.append(f"| Sortino | {_format_number(perf.sortino)} |")
    if perf.calmar is not None:
        lines.append(f"| Calmar | {_format_number(perf.calmar)} |")
    if perf.profit_factor is not None:
        lines.append(f"| Profit Factor | {_format_number(perf.profit_factor)} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Robustness",
            "",
        ]
    )

    # Parameter-Sensitivität
    if rob.param_sensitivity_index is not None:
        lines.append(
            f"- **Parameter-Sensitivität (Index):** {_format_number(rob.param_sensitivity_index)}"
        )
        lines.append("")

    # Monte-Carlo
    if rob.num_montecarlo_runs > 0:
        lines.extend(
            [
                "### Monte-Carlo-Analyse",
                "",
                f"- **Runs:** {rob.num_montecarlo_runs}",
                f"- **Return p5/p50/p95:** {_format_percent(rob.montecarlo_p5)} / {_format_percent(rob.montecarlo_p50)} / {_format_percent(rob.montecarlo_p95)}",
            ]
        )
        if rob.montecarlo_sharpe_p5 is not None and rob.montecarlo_sharpe_p95 is not None:
            lines.append(
                f"- **Sharpe p5/p95:** {_format_number(rob.montecarlo_sharpe_p5)} / {_format_number(rob.montecarlo_sharpe_p95)}"
            )
        lines.append("")

    # Stress-Tests
    if rob.num_stress_scenarios > 0:
        lines.extend(
            [
                "### Stress-Tests",
                "",
                f"- **Szenarien:** {rob.num_stress_scenarios}",
                f"- **Min/Avg/Max Return:** {_format_percent(rob.stress_min)} / {_format_percent(rob.stress_avg)} / {_format_percent(rob.stress_max)}",
                "",
            ]
        )

    # Regime-Profil
    if profile.regimes is not None and profile.regimes.regimes:
        lines.extend(
            [
                "---",
                "",
                "## 4. Regime-Profil",
                "",
                "| Regime | Contribution% | Time% | Effizienz (C/T) | Trades | Avg Return |",
                "|--------|---------------|-------|-----------------|--------|------------|",
            ]
        )

        for regime in profile.regimes.regimes:
            lines.append(
                f"| {regime.name} | {_format_percent(regime.contribution_return)} | "
                f"{_format_percent(regime.time_share)} | {_format_number(regime.efficiency_ratio)} | "
                f"{regime.trade_count} | {_format_percent(regime.avg_return)} |"
            )

        lines.append("")

        if profile.regimes.dominant_regime:
            lines.append(
                f"**Dominantes Regime:** {profile.regimes.dominant_regime}"
            )
        if profile.regimes.weakest_regime:
            lines.append(
                f"**Schwächstes Regime:** {profile.regimes.weakest_regime}"
            )

        lines.append("")

    # Tiering
    if profile.tiering is not None:
        tier = profile.tiering
        tier_emoji = {
            "core": "**Core**",
            "aux": "Aux",
            "legacy": "_Legacy_",
            "r_and_d": "🔬 **R&D/Research**",
        }.get(tier.tier, tier.tier)

        lines.extend(
            [
                "---",
                "",
                "## 5. Tiering & Empfehlung",
                "",
                f"- **Tier:** {tier_emoji}",
            ]
        )

        if tier.recommended_config_id:
            lines.append(f"- **Empfohlene Config:** `{tier.recommended_config_id}`")

        if tier.allow_live:
            lines.append("- **Live-Trading:** Erlaubt")
        else:
            lines.append("- **Live-Trading:** Nicht freigegeben")

        if tier.notes:
            lines.append(f"- **Kommentar:** {tier.notes}")

        lines.append("")

    # Fazit
    lines.extend(
        [
            "---",
            "",
            "## 6. Fazit & Next Steps",
            "",
            _generate_conclusion(profile),
            "",
            "---",
            "",
            f"*Generiert am {meta.created_at} - Peak_Trade Strategy Profiling*",
        ]
    )

    return "\n".join(lines)


def _generate_conclusion(profile: StrategyProfile) -> str:
    """Generiert ein kurzes Fazit basierend auf den Profil-Daten."""
    perf = profile.performance
    rob = profile.robustness
    tiering = profile.tiering

    points = []

    # Performance-Bewertung
    if perf.sharpe >= 1.5:
        points.append("Gute risikoadjustierte Performance (Sharpe >= 1.5)")
    elif perf.sharpe >= 1.0:
        points.append("Akzeptable risikoadjustierte Performance (Sharpe >= 1.0)")
    else:
        points.append("Schwache risikoadjustierte Performance (Sharpe < 1.0)")

    # Drawdown-Bewertung
    if perf.max_drawdown >= -0.10:
        points.append("Niedriger Max-Drawdown (< 10%)")
    elif perf.max_drawdown >= -0.20:
        points.append("Moderater Max-Drawdown (10-20%)")
    else:
        points.append("Hoher Max-Drawdown (> 20%)")

    # Robustness-Bewertung
    if rob.num_montecarlo_runs > 0:
        if rob.montecarlo_p5 is not None and rob.montecarlo_p5 > 0:
            points.append("Monte-Carlo zeigt positive Returns auch im 5%-Perzentil")
        elif rob.montecarlo_p5 is not None:
            points.append("Monte-Carlo zeigt Risiko negativer Returns im Tail")

    # Tiering-Hinweis
    if tiering is not None:
        if tiering.tier == "core":
            points.append("Als Core-Strategie klassifiziert - geeignet für Hauptportfolio")
        elif tiering.tier == "aux":
            points.append("Als Aux-Strategie klassifiziert - als Ergänzung geeignet")
        elif tiering.tier == "legacy":
            points.append("Als Legacy-Strategie klassifiziert - nur zu Vergleichszwecken")

    if not points:
        return "Keine automatische Bewertung verfügbar. Manuelle Analyse empfohlen."

    return "\n".join([f"- {p}" for p in points])


# =============================================================================
# PROFILE BUILDER
# =============================================================================


class StrategyProfileBuilder:
    """
    Builder-Klasse für schrittweise Erstellung von StrategyProfile.

    Ermöglicht flexible Profil-Erstellung mit optionalen Komponenten.

    Example:
        >>> builder = StrategyProfileBuilder("rsi_reversion")
        >>> builder.set_performance(sharpe=1.5, cagr=0.15, max_drawdown=-0.12)
        >>> builder.set_tiering("core", "Robust über mehrere Regime")
        >>> profile = builder.build()
    """

    def __init__(
        self,
        strategy_id: str,
        timeframe: str = "1h",
        symbols: list[str] | None = None,
    ):
        """
        Initialisiert den Builder.

        Args:
            strategy_id: Strategie-ID
            timeframe: Zeitrahmen
            symbols: Liste der Symbole
        """
        self.metadata = Metadata(
            strategy_id=strategy_id,
            timeframe=timeframe,
            symbols=symbols or [],
        )
        self.performance = PerformanceMetrics()
        self.robustness = RobustnessMetrics()
        self.regimes: RegimeProfile | None = None
        self.tiering: StrategyTieringInfo | None = None

    def set_data_range(self, start: str, end: str) -> StrategyProfileBuilder:
        """Setzt den Datenbereich."""
        self.metadata.data_range = f"{start}..{end}"
        return self

    def set_performance(self, **kwargs: Any) -> StrategyProfileBuilder:
        """
        Setzt Performance-Metriken.

        Args:
            **kwargs: Beliebige Performance-Metriken
        """
        for key, value in kwargs.items():
            if hasattr(self.performance, key):
                setattr(self.performance, key, value)
        return self

    def set_performance_from_stats(
        self, stats: dict[str, Any]
    ) -> StrategyProfileBuilder:
        """Setzt Performance aus Backtest-Stats."""
        self.performance = PerformanceMetrics.from_backtest_stats(stats)
        return self

    def set_robustness(self, **kwargs: Any) -> StrategyProfileBuilder:
        """
        Setzt Robustness-Metriken.

        Args:
            **kwargs: Beliebige Robustness-Metriken
        """
        for key, value in kwargs.items():
            if hasattr(self.robustness, key):
                setattr(self.robustness, key, value)
        return self

    def set_montecarlo_results(
        self,
        p5: float,
        p50: float,
        p95: float,
        num_runs: int,
        sharpe_p5: float | None = None,
        sharpe_p95: float | None = None,
    ) -> StrategyProfileBuilder:
        """
        Setzt Monte-Carlo-Ergebnisse.

        Args:
            p5: 5%-Perzentil Return
            p50: Median Return
            p95: 95%-Perzentil Return
            num_runs: Anzahl Runs
            sharpe_p5: 5%-Perzentil Sharpe (optional)
            sharpe_p95: 95%-Perzentil Sharpe (optional)
        """
        self.robustness.montecarlo_p5 = p5
        self.robustness.montecarlo_p50 = p50
        self.robustness.montecarlo_p95 = p95
        self.robustness.num_montecarlo_runs = num_runs
        self.robustness.montecarlo_sharpe_p5 = sharpe_p5
        self.robustness.montecarlo_sharpe_p95 = sharpe_p95
        return self

    def set_stress_results(
        self,
        min_return: float,
        max_return: float,
        avg_return: float,
        num_scenarios: int,
    ) -> StrategyProfileBuilder:
        """
        Setzt Stress-Test-Ergebnisse.

        Args:
            min_return: Minimaler Return
            max_return: Maximaler Return
            avg_return: Durchschnittlicher Return
            num_scenarios: Anzahl Szenarien
        """
        self.robustness.stress_min = min_return
        self.robustness.stress_max = max_return
        self.robustness.stress_avg = avg_return
        self.robustness.num_stress_scenarios = num_scenarios
        return self

    def add_regime(
        self,
        name: str,
        contribution_return: float,
        time_share: float,
        trade_count: int = 0,
        avg_return: float = 0.0,
    ) -> StrategyProfileBuilder:
        """
        Fügt ein Regime zum Profil hinzu.

        Args:
            name: Regime-Name
            contribution_return: Return-Beitrag
            time_share: Zeitanteil
            trade_count: Anzahl Trades
            avg_return: Durchschnittlicher Return
        """
        if self.regimes is None:
            self.regimes = RegimeProfile()

        efficiency = contribution_return / time_share if time_share > 0 else 0.0

        self.regimes.regimes.append(
            SingleRegimeProfile(
                name=name,
                contribution_return=contribution_return,
                time_share=time_share,
                efficiency_ratio=efficiency,
                trade_count=trade_count,
                avg_return=avg_return,
            )
        )
        return self

    def finalize_regimes(self) -> StrategyProfileBuilder:
        """
        Finalisiert Regime-Analyse (berechnet dominant/weakest).
        """
        if self.regimes is None or not self.regimes.regimes:
            return self

        sorted_regimes = sorted(
            self.regimes.regimes,
            key=lambda r: r.contribution_return,
            reverse=True,
        )

        self.regimes.dominant_regime = sorted_regimes[0].name
        self.regimes.weakest_regime = sorted_regimes[-1].name

        return self

    def set_tiering(
        self,
        tier: TIER_TYPES,
        reason: str = "",
        recommended_config_id: str | None = None,
        allow_live: bool = False,
        notes: str = "",
    ) -> StrategyProfileBuilder:
        """
        Setzt Tiering-Informationen.

        Args:
            tier: Tier-Level
            reason: Begründung
            recommended_config_id: Empfohlene Config-ID
            allow_live: Ob Live-Trading erlaubt
            notes: Zusätzliche Anmerkungen
        """
        self.tiering = StrategyTieringInfo(
            tier=tier,
            reason=reason,
            recommended_config_id=recommended_config_id,
            allow_live=allow_live,
            notes=notes,
        )
        return self

    def set_tiering_from_config(
        self,
        config_path: str | Path = "config/strategy_tiering.toml",
    ) -> StrategyProfileBuilder:
        """
        Lädt Tiering aus Config-Datei.

        Args:
            config_path: Pfad zur Tiering-Config
        """
        self.tiering = get_tiering_for_strategy(
            self.metadata.strategy_id,
            load_tiering_config(config_path),
        )
        return self

    def build(self) -> StrategyProfile:
        """
        Erstellt das finale StrategyProfile.

        Returns:
            StrategyProfile-Objekt
        """
        return StrategyProfile(
            metadata=self.metadata,
            performance=self.performance,
            robustness=self.robustness,
            regimes=self.regimes,
            tiering=self.tiering,
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Constants
    "PROFILE_VERSION",
    "TIER_LABELS",
    "TIER_TYPES",
    # Data Models
    "Metadata",
    "PerformanceMetrics",
    "RegimeProfile",
    "RobustnessMetrics",
    "SingleRegimeProfile",
    "StrategyProfile",
    # Builder
    "StrategyProfileBuilder",
    "StrategyTieringInfo",
    # Markdown
    "generate_markdown_profile",
    "get_tiering_for_strategy",
    # Config
    "load_tiering_config",
]

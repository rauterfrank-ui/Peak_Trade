# src/live/live_gates.py
"""
Peak_Trade Live-Gating & Eligibility Checks (Phase 83)
=======================================================

Prüft, ob Strategien und Portfolios für Shadow/Testnet/Live-Runs eligible sind.

Features:
- Strategy-Eligibility basierend auf Tiering + Metriken
- Portfolio-Eligibility basierend auf Komponenten + Diversifikation
- Integration mit StrategyProfile und Tiering-Config
- Policy-basierte Grenzwerte aus config/live_policies.toml

Usage:
    from src.live.live_gates import (
        check_strategy_live_eligibility,
        check_portfolio_live_eligibility,
        LiveGateResult,
    )

    # Einzelne Strategie prüfen
    result = check_strategy_live_eligibility("rsi_reversion")
    if result.is_eligible:
        print("Strategie ist eligible")
    else:
        print(f"Nicht eligible: {result.reasons}")

    # Portfolio prüfen
    result = check_portfolio_live_eligibility("core_balanced")
    print(result)
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# tomllib Import
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from src.experiments.strategy_profiles import (
    StrategyProfile,
    StrategyTieringInfo,
    load_tiering_config,
    get_tiering_for_strategy,
)
from src.live.data_quality_gate import evaluate_data_quality
from src.live.dynamic_leverage_live import evaluate_dynamic_leverage_for_live
from src.ops.double_play.specialists import evaluate_double_play

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_POLICIES_PATH = Path("config/live_policies.toml")
DEFAULT_TIERING_PATH = Path("config/strategy_tiering.toml")
DEFAULT_PRESETS_DIR = Path("config/portfolio_presets")

# R&D-Tier ist NIEMALS für Live/Paper/Testnet freigegeben
R_AND_D_TIER = "r_and_d"
BLOCKED_MODES_FOR_R_AND_D = ["live", "paper", "testnet", "shadow"]


# =============================================================================
# EXCEPTIONS
# =============================================================================


class RnDLiveTradingBlockedError(Exception):
    """
    Exception wenn eine R&D-Strategie in Live/Paper/Testnet ausgeführt werden soll.

    R&D-Strategien (tier="r_and_d") sind ausschließlich für Research und
    Offline-Backtests freigegeben. Diese Exception wird geworfen, wenn
    versucht wird, eine solche Strategie in einem nicht-erlaubten Modus
    zu starten.

    Attributes:
        strategy_id: ID der blockierten Strategie
        mode: Der versuchte Ausführungsmodus
        message: Detaillierte Fehlermeldung
    """

    def __init__(
        self,
        strategy_id: str,
        mode: str,
        message: Optional[str] = None,
    ) -> None:
        self.strategy_id = strategy_id
        self.mode = mode
        self.message = message or (
            f"R&D-Strategie '{strategy_id}' ist für Modus '{mode}' NICHT freigegeben. "
            f"R&D-Strategien sind ausschließlich für Research/Backtests vorgesehen. "
            f"Erlaubte Modi: offline_backtest, research."
        )
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class LiveGateResult:
    """
    Ergebnis einer Live-Eligibility-Prüfung.

    Attributes:
        entity_id: ID der geprüften Entität (Strategy oder Portfolio)
        entity_type: Typ ("strategy" oder "portfolio")
        is_eligible: Ob die Entität live-eligible ist
        reasons: Liste von Gründen für Nicht-Eligibility
        details: Zusätzliche Details zur Prüfung
        tier: Tier der Strategie (nur bei entity_type="strategy")
        allow_live_flag: allow_live Flag aus Tiering (nur bei entity_type="strategy")
    """

    entity_id: str
    entity_type: str  # "strategy" oder "portfolio"
    is_eligible: bool
    reasons: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    tier: Optional[str] = None
    allow_live_flag: Optional[bool] = None

    def __str__(self) -> str:
        status = "✅ ELIGIBLE" if self.is_eligible else "❌ NOT ELIGIBLE"
        lines = [
            f"Live Gate Check: {self.entity_id} ({self.entity_type})",
            f"Status: {status}",
        ]
        if self.tier:
            lines.append(f"Tier: {self.tier}")
        if self.allow_live_flag is not None:
            lines.append(f"allow_live: {self.allow_live_flag}")
        if self.reasons:
            lines.append("Reasons:")
            for reason in self.reasons:
                lines.append(f"  - {reason}")
        return "\n".join(lines)


@dataclass
class LivePolicies:
    """
    Live-Policies aus Konfiguration.

    Attributes:
        min_sharpe_core: Minimum Sharpe für Core-Strategien
        min_sharpe_aux: Minimum Sharpe für Aux-Strategien
        max_maxdd_core: Maximum MaxDD für Core-Strategien (negativ)
        max_maxdd_aux: Maximum MaxDD für Aux-Strategien (negativ)
        allow_legacy: Ob Legacy-Strategien erlaubt sind
        require_allow_live_flag: Ob allow_live=True erforderlich ist
        require_diversification: Ob Portfolio-Diversifikation geprüft wird
        max_concentration: Maximale Gewichtung einer einzelnen Strategie
    """

    min_sharpe_core: float = 1.5
    min_sharpe_aux: float = 1.0
    max_maxdd_core: float = -0.15  # -15%
    max_maxdd_aux: float = -0.20  # -20%
    allow_legacy: bool = False
    require_allow_live_flag: bool = False  # Phase 83: noch nicht enforced
    require_diversification: bool = True
    max_concentration: float = 0.6  # 60%

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LivePolicies":
        """Erstellt LivePolicies aus Dictionary."""
        return cls(
            min_sharpe_core=data.get("min_sharpe_core", 1.5),
            min_sharpe_aux=data.get("min_sharpe_aux", 1.0),
            max_maxdd_core=data.get("max_maxdd_core", -0.15),
            max_maxdd_aux=data.get("max_maxdd_aux", -0.20),
            allow_legacy=data.get("allow_legacy", False),
            require_allow_live_flag=data.get("require_allow_live_flag", False),
            require_diversification=data.get("require_diversification", True),
            max_concentration=data.get("max_concentration", 0.6),
        )


# =============================================================================
# POLICY LOADING
# =============================================================================


def load_live_policies(
    policies_path: Path = DEFAULT_POLICIES_PATH,
) -> LivePolicies:
    """
    Lädt Live-Policies aus TOML-Datei.

    Args:
        policies_path: Pfad zur Policies-Datei

    Returns:
        LivePolicies-Objekt (Default-Werte wenn Datei nicht existiert)
    """
    if not policies_path.exists():
        logger.info(f"Live policies file not found ({policies_path}), using defaults")
        return LivePolicies()

    if tomllib is None:
        logger.warning("tomllib/tomli not available, using default policies")
        return LivePolicies()

    try:
        with open(policies_path, "rb") as f:
            data = tomllib.load(f)

        policy_data = data.get("live_policy", data.get("live_policy_v1", {}))
        return LivePolicies.from_dict(policy_data)

    except Exception as e:
        logger.error(f"Error loading live policies: {e}")
        return LivePolicies()


# =============================================================================
# STRATEGY ELIGIBILITY
# =============================================================================


def check_strategy_live_eligibility(
    strategy_id: str,
    profile: Optional[StrategyProfile] = None,
    policies: Optional[LivePolicies] = None,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
    asof_utc: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> LiveGateResult:
    """
    Prüft, ob eine Strategie für Live-Runs eligible ist.

    Kriterien:
    1. Tier muss "core" oder "aux" sein (kein "legacy")
    2. allow_live Flag (wenn require_allow_live_flag=True in Policies)
    3. Performance-Metriken (Sharpe, MaxDD) erfüllen Tier-spezifische Grenzen

    Args:
        strategy_id: Strategy-ID
        profile: Optionales StrategyProfile (wenn bereits geladen)
        policies: Optionale LivePolicies (wenn bereits geladen)
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        LiveGateResult mit Eligibility-Status und Details

    Example:
        >>> result = check_strategy_live_eligibility("rsi_reversion")
        >>> print(result.is_eligible)
        True
    """
    reasons: List[str] = []
    details: Dict[str, Any] = {}

    # DQ Hard Gate (fail-closed when asof_utc provided in live context)
    if asof_utc is not None:
        dq_result = check_data_quality_gate(asof_utc=asof_utc, context=context or {})
        if not dq_result.is_eligible:
            return LiveGateResult(
                entity_id=strategy_id,
                entity_type="strategy",
                is_eligible=False,
                reasons=["dq_freshness_gap_failed"] + dq_result.reasons,
                details={"dq_gate": dq_result.details},
                tier=None,
                allow_live_flag=None,
            )

    # Policies laden
    if policies is None:
        policies = load_live_policies()

    # Tiering laden
    tiering = load_tiering_config(tiering_config_path)
    tiering_info = tiering.get(strategy_id)

    if tiering_info is None:
        reasons.append(f"Strategy '{strategy_id}' not found in tiering config")
        return LiveGateResult(
            entity_id=strategy_id,
            entity_type="strategy",
            is_eligible=False,
            reasons=reasons,
            tier="unclassified",
        )

    tier = tiering_info.tier
    allow_live = tiering_info.allow_live
    details["tier"] = tier
    details["allow_live"] = allow_live

    # Check 1: Tier-Anforderung
    # R&D-Strategien sind NIEMALS für Live/Paper/Testnet freigegeben
    if tier == R_AND_D_TIER:
        reasons.append(
            f"R&D-Strategien sind ausschließlich für Research/Backtests freigegeben "
            f"(tier={tier}). Live/Paper/Testnet ist blockiert."
        )

    if tier == "legacy" and not policies.allow_legacy:
        reasons.append(f"Legacy-tier strategies are not eligible (tier={tier})")

    if tier == "unclassified":
        reasons.append(f"Unclassified strategies are not eligible (tier={tier})")

    # Check 2: allow_live Flag
    if policies.require_allow_live_flag and not allow_live:
        reasons.append(f"allow_live flag is False (required by policy)")

    # Check 3: Performance-Metriken (nur wenn Profile vorhanden)
    if profile is not None:
        perf = profile.performance
        details["sharpe"] = perf.sharpe
        details["max_drawdown"] = perf.max_drawdown

        if tier == "core":
            if perf.sharpe < policies.min_sharpe_core:
                reasons.append(
                    f"Sharpe ({perf.sharpe:.2f}) below core minimum ({policies.min_sharpe_core})"
                )
            if perf.max_drawdown < policies.max_maxdd_core:
                reasons.append(
                    f"MaxDD ({perf.max_drawdown:.1%}) worse than core limit ({policies.max_maxdd_core:.1%})"
                )
        elif tier == "aux":
            if perf.sharpe < policies.min_sharpe_aux:
                reasons.append(
                    f"Sharpe ({perf.sharpe:.2f}) below aux minimum ({policies.min_sharpe_aux})"
                )
            if perf.max_drawdown < policies.max_maxdd_aux:
                reasons.append(
                    f"MaxDD ({perf.max_drawdown:.1%}) worse than aux limit ({policies.max_maxdd_aux:.1%})"
                )

    is_eligible = len(reasons) == 0

    if is_eligible:
        logger.debug(f"Strategy '{strategy_id}' is live-eligible (tier={tier})")
    else:
        logger.info(f"Strategy '{strategy_id}' is NOT live-eligible: {reasons}")

    # Dynamic leverage sizing hint (SAFE DEFAULT OFF; does not change eligibility)
    dl_decision = evaluate_dynamic_leverage_for_live(context=context or {})
    details["dynamic_leverage"] = dl_decision.details

    # Double-play specialist selection (SAFE DEFAULT OFF; annotate only)
    dp_decision = evaluate_double_play(context=context or {})
    details["double_play"] = dp_decision.details

    return LiveGateResult(
        entity_id=strategy_id,
        entity_type="strategy",
        is_eligible=is_eligible,
        reasons=reasons,
        details=details,
        tier=tier,
        allow_live_flag=allow_live,
    )


def get_eligible_strategies(
    policies: Optional[LivePolicies] = None,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
) -> List[str]:
    """
    Gibt alle live-eligible Strategien zurück.

    Args:
        policies: Optionale LivePolicies
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Liste der eligible Strategy-IDs
    """
    if policies is None:
        policies = load_live_policies()

    tiering = load_tiering_config(tiering_config_path)
    eligible = []

    for strategy_id in tiering.keys():
        result = check_strategy_live_eligibility(
            strategy_id,
            policies=policies,
            tiering_config_path=tiering_config_path,
        )
        if result.is_eligible:
            eligible.append(strategy_id)

    return eligible


# =============================================================================
# PORTFOLIO ELIGIBILITY
# =============================================================================


def check_portfolio_live_eligibility(
    portfolio_id: str,
    strategies: Optional[List[str]] = None,
    weights: Optional[List[float]] = None,
    policies: Optional[LivePolicies] = None,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
    presets_dir: Path = DEFAULT_PRESETS_DIR,
    asof_utc: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> LiveGateResult:
    """
    Prüft, ob ein Portfolio für Live-Runs eligible ist.

    Kriterien:
    1. Alle Strategien im Portfolio sind live-eligible
    2. Keine übermäßige Konzentration auf eine Strategie
    3. Mindestens 1 Strategie im Portfolio

    Args:
        portfolio_id: Portfolio-ID (Preset-Name)
        strategies: Liste der Strategy-IDs (wenn bereits bekannt)
        weights: Liste der Gewichte (wenn bereits bekannt)
        policies: Optionale LivePolicies
        tiering_config_path: Pfad zur Tiering-Config
        presets_dir: Verzeichnis mit Portfolio-Presets

    Returns:
        LiveGateResult mit Eligibility-Status und Details

    Example:
        >>> result = check_portfolio_live_eligibility("core_balanced")
        >>> print(result.is_eligible)
        True
    """
    reasons: List[str] = []
    details: Dict[str, Any] = {}

    # DQ Hard Gate (fail-closed when asof_utc provided in live context)
    if asof_utc is not None:
        dq_result = check_data_quality_gate(asof_utc=asof_utc, context=context or {})
        if not dq_result.is_eligible:
            return LiveGateResult(
                entity_id=portfolio_id,
                entity_type="portfolio",
                is_eligible=False,
                reasons=["dq_freshness_gap_failed"] + dq_result.reasons,
                details={"dq_gate": dq_result.details},
            )

    # Policies laden
    if policies is None:
        policies = load_live_policies()

    # Strategien und Gewichte ermitteln
    if strategies is None or weights is None:
        # Versuche Preset zu laden
        try:
            from src.experiments.portfolio_recipes import load_portfolio_recipes

            preset_file = presets_dir / f"{portfolio_id}.toml"
            if preset_file.exists():
                recipes = load_portfolio_recipes(preset_file)
                recipe = recipes.get(portfolio_id)
                if recipe:
                    strategies = recipe.strategies or []
                    weights = recipe.weights
        except Exception as e:
            logger.warning(f"Could not load preset {portfolio_id}: {e}")

    if strategies is None:
        strategies = []
    if weights is None:
        weights = [1.0 / len(strategies)] * len(strategies) if strategies else []

    details["strategies"] = strategies
    details["weights"] = weights
    details["num_strategies"] = len(strategies)

    # Check 1: Mindestens 1 Strategie
    if len(strategies) == 0:
        reasons.append("Portfolio has no strategies")
        return LiveGateResult(
            entity_id=portfolio_id,
            entity_type="portfolio",
            is_eligible=False,
            reasons=reasons,
            details=details,
        )

    # Check 2: Alle Strategien müssen eligible sein
    ineligible_strategies = []
    for strategy_id in strategies:
        result = check_strategy_live_eligibility(
            strategy_id,
            policies=policies,
            tiering_config_path=tiering_config_path,
        )
        if not result.is_eligible:
            ineligible_strategies.append(strategy_id)

    if ineligible_strategies:
        reasons.append(f"Portfolio contains ineligible strategies: {ineligible_strategies}")
        details["ineligible_strategies"] = ineligible_strategies

    # Check 3: Konzentrations-Check
    if policies.require_diversification and len(weights) > 0:
        max_weight = max(weights)
        details["max_weight"] = max_weight
        if max_weight > policies.max_concentration:
            reasons.append(
                f"Single strategy concentration ({max_weight:.1%}) exceeds limit ({policies.max_concentration:.1%})"
            )

    is_eligible = len(reasons) == 0

    if is_eligible:
        logger.debug(f"Portfolio '{portfolio_id}' is live-eligible")
    else:
        logger.info(f"Portfolio '{portfolio_id}' is NOT live-eligible: {reasons}")

    # Dynamic leverage sizing hint (SAFE DEFAULT OFF; does not change eligibility)
    dl_decision = evaluate_dynamic_leverage_for_live(context=context or {})
    details["dynamic_leverage"] = dl_decision.details

    # Double-play specialist selection (SAFE DEFAULT OFF; annotate only)
    dp_decision = evaluate_double_play(context=context or {})
    details["double_play"] = dp_decision.details

    return LiveGateResult(
        entity_id=portfolio_id,
        entity_type="portfolio",
        is_eligible=is_eligible,
        reasons=reasons,
        details=details,
    )


# =============================================================================
# DATA QUALITY HARD GATE
# =============================================================================


def check_data_quality_gate(
    *,
    asof_utc: str,
    context: Optional[Dict[str, Any]] = None,
) -> LiveGateResult:
    """Evaluate DQ freshness/gap gate. Fail-closed: FAIL → no-trade.

    Call before strategy/portfolio eligibility when in live context.
    """
    ctx = context or {}
    d = evaluate_data_quality(asof_utc=asof_utc, context=ctx)
    return LiveGateResult(
        entity_id=d.gate_id,
        entity_type="data_quality",
        is_eligible=(d.status == "PASS"),
        reasons=d.reasons,
        details=d.details,
    )


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================


def assert_strategy_eligible(
    strategy_id: str,
    policies: Optional[LivePolicies] = None,
) -> None:
    """
    Stellt sicher, dass eine Strategie eligible ist. Wirft Exception bei Nicht-Eligibility.

    Args:
        strategy_id: Strategy-ID
        policies: Optionale LivePolicies

    Raises:
        ValueError: Wenn Strategie nicht eligible ist
    """
    result = check_strategy_live_eligibility(strategy_id, policies=policies)
    if not result.is_eligible:
        raise ValueError(f"Strategy '{strategy_id}' is not live-eligible: {result.reasons}")


def assert_portfolio_eligible(
    portfolio_id: str,
    strategies: Optional[List[str]] = None,
    weights: Optional[List[float]] = None,
    policies: Optional[LivePolicies] = None,
) -> None:
    """
    Stellt sicher, dass ein Portfolio eligible ist. Wirft Exception bei Nicht-Eligibility.

    Args:
        portfolio_id: Portfolio-ID
        strategies: Optionale Strategy-Liste
        weights: Optionale Gewichte
        policies: Optionale LivePolicies

    Raises:
        ValueError: Wenn Portfolio nicht eligible ist
    """
    result = check_portfolio_live_eligibility(
        portfolio_id,
        strategies=strategies,
        weights=weights,
        policies=policies,
    )
    if not result.is_eligible:
        raise ValueError(f"Portfolio '{portfolio_id}' is not live-eligible: {result.reasons}")


def get_eligibility_summary() -> Dict[str, Any]:
    """
    Gibt eine Zusammenfassung der Eligibility aller Strategien zurück.

    Returns:
        Dict mit Eligibility-Status pro Strategie und Zusammenfassung
    """
    policies = load_live_policies()
    tiering = load_tiering_config()

    summary = {
        "total_strategies": len(tiering),
        "eligible": [],
        "ineligible": [],
        "by_tier": {
            "core": {"eligible": [], "ineligible": []},
            "aux": {"eligible": [], "ineligible": []},
            "legacy": {"eligible": [], "ineligible": []},
        },
    }

    for strategy_id in tiering.keys():
        result = check_strategy_live_eligibility(strategy_id, policies=policies)

        if result.is_eligible:
            summary["eligible"].append(strategy_id)
            if result.tier in summary["by_tier"]:
                summary["by_tier"][result.tier]["eligible"].append(strategy_id)
        else:
            summary["ineligible"].append(strategy_id)
            if result.tier in summary["by_tier"]:
                summary["by_tier"][result.tier]["ineligible"].append(strategy_id)

    summary["num_eligible"] = len(summary["eligible"])
    summary["num_ineligible"] = len(summary["ineligible"])

    return summary


# =============================================================================
# R&D TIER GATING
# =============================================================================


def check_r_and_d_tier_for_mode(
    strategy_id: str,
    mode: str,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
) -> bool:
    """
    Prüft, ob eine R&D-Strategie für einen bestimmten Modus blockiert ist.

    R&D-Strategien (tier="r_and_d") sind ausschließlich für "offline_backtest"
    und "research" freigegeben. Alle anderen Modi werden blockiert.

    Args:
        strategy_id: Strategy-ID
        mode: Ausführungsmodus (live, paper, testnet, shadow, offline_backtest, research)
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        True wenn blockiert (R&D + nicht-erlaubter Modus), False sonst

    Example:
        >>> is_blocked = check_r_and_d_tier_for_mode("armstrong_cycle", "live")
        >>> print(is_blocked)
        True
    """
    tiering = load_tiering_config(tiering_config_path)
    tiering_info = tiering.get(strategy_id)

    if tiering_info is None:
        return False  # Unbekannte Strategie, nicht blockiert

    if tiering_info.tier != R_AND_D_TIER:
        return False  # Nicht R&D, nicht blockiert

    # R&D-Strategie: Prüfe Modus
    return mode.lower() in BLOCKED_MODES_FOR_R_AND_D


def assert_strategy_not_r_and_d_for_live(
    strategy_id: str,
    mode: str,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
) -> None:
    """
    Stellt sicher, dass eine R&D-Strategie nicht in Live/Paper/Testnet läuft.

    Wirft RnDLiveTradingBlockedError wenn die Strategie R&D-Tier hat
    und der Modus nicht erlaubt ist.

    Args:
        strategy_id: Strategy-ID
        mode: Ausführungsmodus
        tiering_config_path: Pfad zur Tiering-Config

    Raises:
        RnDLiveTradingBlockedError: Wenn R&D-Strategie in nicht-erlaubtem Modus

    Example:
        >>> # Wirft Exception
        >>> assert_strategy_not_r_and_d_for_live("armstrong_cycle", "live")
        RnDLiveTradingBlockedError: R&D-Strategie 'armstrong_cycle' ist für Modus 'live' NICHT freigegeben...

        >>> # OK, keine Exception
        >>> assert_strategy_not_r_and_d_for_live("armstrong_cycle", "offline_backtest")
    """
    if check_r_and_d_tier_for_mode(strategy_id, mode, tiering_config_path):
        raise RnDLiveTradingBlockedError(strategy_id, mode)

    logger.debug(f"Strategy '{strategy_id}' is allowed for mode '{mode}'")


def get_strategy_tier(
    strategy_id: str,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
) -> str:
    """
    Gibt den Tier einer Strategie zurück.

    Args:
        strategy_id: Strategy-ID
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Tier-String (core, aux, legacy, r_and_d, unclassified)

    Example:
        >>> tier = get_strategy_tier("armstrong_cycle")
        >>> print(tier)
        r_and_d
    """
    tiering = load_tiering_config(tiering_config_path)
    tiering_info = tiering.get(strategy_id)

    if tiering_info is None:
        return "unclassified"

    return tiering_info.tier


def log_strategy_tier_info(
    strategy_id: str,
    tiering_config_path: Path = DEFAULT_TIERING_PATH,
) -> Dict[str, Any]:
    """
    Gibt Tier-Informationen für Logs/Reports zurück.

    Args:
        strategy_id: Strategy-ID
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Dict mit Tier-Informationen

    Example:
        >>> info = log_strategy_tier_info("armstrong_cycle")
        >>> print(info)
        {'strategy_id': 'armstrong_cycle', 'tier': 'r_and_d', 'is_r_and_d': True, ...}
    """
    tiering = load_tiering_config(tiering_config_path)
    tiering_info = tiering.get(strategy_id)

    if tiering_info is None:
        return {
            "strategy_id": strategy_id,
            "tier": "unclassified",
            "is_r_and_d": False,
            "allow_live": False,
            "notes": "Kein Tiering-Eintrag vorhanden",
        }

    return {
        "strategy_id": strategy_id,
        "tier": tiering_info.tier,
        "is_r_and_d": tiering_info.tier == R_AND_D_TIER,
        "allow_live": tiering_info.allow_live,
        "notes": tiering_info.notes,
        "recommended_config_id": tiering_info.recommended_config_id,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Exceptions
    "RnDLiveTradingBlockedError",
    # Data Quality Gate
    "check_data_quality_gate",
    # Data Models
    "LiveGateResult",
    "LivePolicies",
    # Policy Loading
    "load_live_policies",
    # Strategy Eligibility
    "check_strategy_live_eligibility",
    "get_eligible_strategies",
    # Portfolio Eligibility
    "check_portfolio_live_eligibility",
    # Integration Helpers
    "assert_strategy_eligible",
    "assert_portfolio_eligible",
    "get_eligibility_summary",
    # R&D Tier Gating
    "check_r_and_d_tier_for_mode",
    "assert_strategy_not_r_and_d_for_live",
    "get_strategy_tier",
    "log_strategy_tier_info",
    # Constants
    "R_AND_D_TIER",
    "BLOCKED_MODES_FOR_R_AND_D",
]

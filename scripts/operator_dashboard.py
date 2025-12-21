#!/usr/bin/env python3
# scripts/operator_dashboard.py
"""
Peak_Trade Operator Dashboard CLI (Phase 84)
=============================================

CLI-Dashboard für Operatoren mit Übersicht über:
- Strategien + Tiering + Live-Eligibility
- Portfolio-Presets + Compliance-Status
- Profil-/Research-Run-Freshness
- Alerts & Warnungen

Usage:
    # Vollständiges Dashboard
    python scripts/operator_dashboard.py

    # Nur Strategien
    python scripts/operator_dashboard.py --view strategies

    # Nur Portfolios
    python scripts/operator_dashboard.py --view portfolios

    # Nur Alerts/Warnungen
    python scripts/operator_dashboard.py --view alerts

    # JSON-Output
    python scripts/operator_dashboard.py --format json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.live.live_gates import (
    check_strategy_live_eligibility,
    check_portfolio_live_eligibility,
    get_eligibility_summary,
    load_live_policies,
    LivePolicies,
)
from src.experiments.strategy_profiles import load_tiering_config
from src.experiments.portfolio_presets import (
    get_all_tiered_strategies,
    validate_preset_tiering_compliance,
)
from src.experiments.portfolio_recipes import load_portfolio_recipes

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

PRESETS_DIR = PROJECT_ROOT / "config" / "portfolio_presets"
PROFILES_DIR = PROJECT_ROOT / "reports" / "strategy_profiles"
PROFILE_MAX_AGE_DAYS = 30  # Profile älter als X Tage sind "stale"


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class StrategyStatus:
    """Status einer Strategie."""

    strategy_id: str
    tier: str
    is_eligible: bool
    allow_live: bool
    has_profile: bool
    profile_age_days: Optional[int]
    is_profile_stale: bool
    eligibility_reasons: List[str] = field(default_factory=list)


@dataclass
class PortfolioStatus:
    """Status eines Portfolios."""

    portfolio_id: str
    num_strategies: int
    is_eligible: bool
    is_compliant: bool
    strategies: List[str]
    weights: List[float]
    eligibility_reasons: List[str] = field(default_factory=list)
    compliance_violations: List[str] = field(default_factory=list)


@dataclass
class Alert:
    """Ein Alert/Warnung."""

    level: str  # "error", "warning", "info"
    category: str  # "profile", "eligibility", "compliance", "config"
    message: str
    entity_id: Optional[str] = None


@dataclass
class DashboardData:
    """Gesamte Dashboard-Daten."""

    timestamp: str
    strategies: List[StrategyStatus]
    portfolios: List[PortfolioStatus]
    alerts: List[Alert]
    summary: Dict[str, Any]


# =============================================================================
# DATA COLLECTION
# =============================================================================


def get_profile_info(strategy_id: str) -> tuple[bool, Optional[int]]:
    """
    Prüft ob ein Profil existiert und wie alt es ist.

    Returns:
        (has_profile, age_in_days)
    """
    profile_patterns = [
        PROFILES_DIR / f"{strategy_id}_profile_v1.json",
        PROFILES_DIR / f"{strategy_id}_profile.json",
        PROFILES_DIR / f"{strategy_id}.json",
    ]

    for pattern in profile_patterns:
        if pattern.exists():
            mtime = datetime.fromtimestamp(pattern.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            return True, age_days

    return False, None


def collect_strategy_statuses() -> List[StrategyStatus]:
    """Sammelt Status aller Strategien."""
    tiering = load_tiering_config()
    statuses = []

    for strategy_id, info in tiering.items():
        eligibility = check_strategy_live_eligibility(strategy_id)
        has_profile, profile_age = get_profile_info(strategy_id)
        is_stale = profile_age is not None and profile_age > PROFILE_MAX_AGE_DAYS

        status = StrategyStatus(
            strategy_id=strategy_id,
            tier=info.tier,
            is_eligible=eligibility.is_eligible,
            allow_live=info.allow_live,
            has_profile=has_profile,
            profile_age_days=profile_age,
            is_profile_stale=is_stale,
            eligibility_reasons=eligibility.reasons,
        )
        statuses.append(status)

    # Sortieren: Core zuerst, dann Aux, dann Legacy
    tier_order = {"core": 0, "aux": 1, "legacy": 2, "unclassified": 3}
    statuses.sort(key=lambda s: (tier_order.get(s.tier, 4), s.strategy_id))

    return statuses


def collect_portfolio_statuses() -> List[PortfolioStatus]:
    """Sammelt Status aller Portfolio-Presets."""
    statuses = []

    if not PRESETS_DIR.exists():
        return statuses

    for preset_file in PRESETS_DIR.glob("*.toml"):
        preset_name = preset_file.stem

        try:
            recipes = load_portfolio_recipes(preset_file)
            for recipe_id, recipe in recipes.items():
                strategies = recipe.strategies or []
                weights = recipe.weights or []

                # Eligibility prüfen
                eligibility = check_portfolio_live_eligibility(
                    recipe_id,
                    strategies=strategies,
                    weights=weights,
                )

                # Compliance prüfen
                if preset_name.startswith("core_plus_aux") or preset_name.startswith("core_aux"):
                    allowed_tiers = ["core", "aux"]
                elif preset_name.startswith("core_"):
                    allowed_tiers = ["core"]
                else:
                    allowed_tiers = ["core", "aux"]

                compliance = validate_preset_tiering_compliance(
                    recipe_id,
                    allowed_tiers=allowed_tiers,
                    recipe=recipe,
                )

                status = PortfolioStatus(
                    portfolio_id=recipe_id,
                    num_strategies=len(strategies),
                    is_eligible=eligibility.is_eligible,
                    is_compliant=compliance.is_compliant,
                    strategies=strategies,
                    weights=weights,
                    eligibility_reasons=eligibility.reasons,
                    compliance_violations=compliance.violations,
                )
                statuses.append(status)

        except Exception as e:
            logger.warning(f"Could not load preset {preset_name}: {e}")

    return statuses


def collect_alerts(
    strategies: List[StrategyStatus],
    portfolios: List[PortfolioStatus],
) -> List[Alert]:
    """Generiert Alerts basierend auf Status-Daten."""
    alerts = []

    # Strategy Alerts
    for s in strategies:
        # Stale Profile
        if s.is_profile_stale:
            alerts.append(
                Alert(
                    level="warning",
                    category="profile",
                    message=f"Profile is {s.profile_age_days} days old (max: {PROFILE_MAX_AGE_DAYS})",
                    entity_id=s.strategy_id,
                )
            )

        # Missing Profile für Core/Aux
        if not s.has_profile and s.tier in ["core", "aux"]:
            alerts.append(
                Alert(
                    level="warning",
                    category="profile",
                    message=f"No profile found for {s.tier}-tier strategy",
                    entity_id=s.strategy_id,
                )
            )

        # Not eligible trotz Core-Tier
        if not s.is_eligible and s.tier == "core":
            alerts.append(
                Alert(
                    level="error",
                    category="eligibility",
                    message=f"Core strategy is NOT eligible: {s.eligibility_reasons}",
                    entity_id=s.strategy_id,
                )
            )

    # Portfolio Alerts
    for p in portfolios:
        if not p.is_compliant:
            alerts.append(
                Alert(
                    level="error",
                    category="compliance",
                    message=f"Portfolio not compliant: {p.compliance_violations}",
                    entity_id=p.portfolio_id,
                )
            )

        if not p.is_eligible:
            alerts.append(
                Alert(
                    level="warning",
                    category="eligibility",
                    message=f"Portfolio not eligible: {p.eligibility_reasons}",
                    entity_id=p.portfolio_id,
                )
            )

    # Config Alerts
    policies = load_live_policies()
    if policies.allow_legacy:
        alerts.append(
            Alert(
                level="warning",
                category="config",
                message="allow_legacy is TRUE in live_policies.toml - Legacy strategies could go live!",
            )
        )

    return alerts


def collect_summary(
    strategies: List[StrategyStatus],
    portfolios: List[PortfolioStatus],
    alerts: List[Alert],
) -> Dict[str, Any]:
    """Erstellt Zusammenfassung."""
    by_tier = {"core": 0, "aux": 0, "legacy": 0, "unclassified": 0}
    eligible_count = 0

    for s in strategies:
        if s.tier in by_tier:
            by_tier[s.tier] += 1
        if s.is_eligible:
            eligible_count += 1

    return {
        "total_strategies": len(strategies),
        "strategies_by_tier": by_tier,
        "strategies_eligible": eligible_count,
        "strategies_with_profiles": sum(1 for s in strategies if s.has_profile),
        "strategies_with_stale_profiles": sum(1 for s in strategies if s.is_profile_stale),
        "total_portfolios": len(portfolios),
        "portfolios_eligible": sum(1 for p in portfolios if p.is_eligible),
        "portfolios_compliant": sum(1 for p in portfolios if p.is_compliant),
        "alerts_error": sum(1 for a in alerts if a.level == "error"),
        "alerts_warning": sum(1 for a in alerts if a.level == "warning"),
        "alerts_info": sum(1 for a in alerts if a.level == "info"),
    }


def collect_dashboard_data() -> DashboardData:
    """Sammelt alle Dashboard-Daten."""
    strategies = collect_strategy_statuses()
    portfolios = collect_portfolio_statuses()
    alerts = collect_alerts(strategies, portfolios)
    summary = collect_summary(strategies, portfolios, alerts)

    return DashboardData(
        timestamp=datetime.now().isoformat(),
        strategies=strategies,
        portfolios=portfolios,
        alerts=alerts,
        summary=summary,
    )


# =============================================================================
# OUTPUT FORMATTERS
# =============================================================================


def format_tier_badge(tier: str) -> str:
    """Formatiert Tier als Badge."""
    badges = {
        "core": "[CORE]",
        "aux": "[AUX]",
        "legacy": "[LEGACY]",
        "unclassified": "[?]",
    }
    return badges.get(tier, f"[{tier}]")


def format_eligibility(is_eligible: bool) -> str:
    """Formatiert Eligibility-Status."""
    return "OK" if is_eligible else "BLOCKED"


def print_header(title: str) -> None:
    """Druckt Header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_strategies_view(strategies: List[StrategyStatus]) -> None:
    """Druckt Strategien-Ansicht."""
    print_header("STRATEGIES")

    print(f"\n{'Strategy':<25} {'Tier':<10} {'Eligible':<10} {'Profile':<15}")
    print("-" * 70)

    for s in strategies:
        profile_status = "OK"
        if not s.has_profile:
            profile_status = "MISSING"
        elif s.is_profile_stale:
            profile_status = f"STALE ({s.profile_age_days}d)"

        eligibility = format_eligibility(s.is_eligible)
        tier = format_tier_badge(s.tier)

        print(f"{s.strategy_id:<25} {tier:<10} {eligibility:<10} {profile_status:<15}")


def print_portfolios_view(portfolios: List[PortfolioStatus]) -> None:
    """Druckt Portfolio-Ansicht."""
    print_header("PORTFOLIOS")

    if not portfolios:
        print("\n  No portfolio presets found.")
        return

    print(f"\n{'Portfolio':<30} {'Strategies':<12} {'Eligible':<10} {'Compliant':<10}")
    print("-" * 70)

    for p in portfolios:
        eligible = format_eligibility(p.is_eligible)
        compliant = "OK" if p.is_compliant else "FAILED"

        print(f"{p.portfolio_id:<30} {p.num_strategies:<12} {eligible:<10} {compliant:<10}")


def print_alerts_view(alerts: List[Alert]) -> None:
    """Druckt Alerts-Ansicht."""
    print_header("ALERTS & WARNINGS")

    if not alerts:
        print("\n  No alerts or warnings.")
        return

    # Sortieren: Errors zuerst
    level_order = {"error": 0, "warning": 1, "info": 2}
    sorted_alerts = sorted(alerts, key=lambda a: level_order.get(a.level, 3))

    for alert in sorted_alerts:
        level_icon = {"error": "[!]", "warning": "[?]", "info": "[i]"}.get(alert.level, "[-]")
        entity = f" ({alert.entity_id})" if alert.entity_id else ""

        print(f"\n  {level_icon} [{alert.category.upper()}]{entity}")
        print(f"      {alert.message}")


def print_summary_view(summary: Dict[str, Any]) -> None:
    """Druckt Summary-Ansicht."""
    print_header("SUMMARY")

    print(f"""
  Strategies:
    Total:        {summary["total_strategies"]}
    Core:         {summary["strategies_by_tier"]["core"]}
    Aux:          {summary["strategies_by_tier"]["aux"]}
    Legacy:       {summary["strategies_by_tier"]["legacy"]}
    Eligible:     {summary["strategies_eligible"]}
    With Profile: {summary["strategies_with_profiles"]}
    Stale:        {summary["strategies_with_stale_profiles"]}

  Portfolios:
    Total:        {summary["total_portfolios"]}
    Eligible:     {summary["portfolios_eligible"]}
    Compliant:    {summary["portfolios_compliant"]}

  Alerts:
    Errors:       {summary["alerts_error"]}
    Warnings:     {summary["alerts_warning"]}
    Info:         {summary["alerts_info"]}
""")


def print_full_dashboard(data: DashboardData) -> None:
    """Druckt vollständiges Dashboard."""
    print()
    print("=" * 70)
    print("  PEAK_TRADE OPERATOR DASHBOARD")
    print(f"  Generated: {data.timestamp}")
    print("=" * 70)

    print_summary_view(data.summary)
    print_strategies_view(data.strategies)
    print_portfolios_view(data.portfolios)
    print_alerts_view(data.alerts)

    print()
    print("=" * 70)


def output_json(data: DashboardData) -> None:
    """Gibt Dashboard als JSON aus."""
    output = {
        "timestamp": data.timestamp,
        "summary": data.summary,
        "strategies": [
            {
                "strategy_id": s.strategy_id,
                "tier": s.tier,
                "is_eligible": s.is_eligible,
                "allow_live": s.allow_live,
                "has_profile": s.has_profile,
                "profile_age_days": s.profile_age_days,
                "is_profile_stale": s.is_profile_stale,
                "eligibility_reasons": s.eligibility_reasons,
            }
            for s in data.strategies
        ],
        "portfolios": [
            {
                "portfolio_id": p.portfolio_id,
                "num_strategies": p.num_strategies,
                "is_eligible": p.is_eligible,
                "is_compliant": p.is_compliant,
                "strategies": p.strategies,
                "eligibility_reasons": p.eligibility_reasons,
            }
            for p in data.portfolios
        ],
        "alerts": [
            {
                "level": a.level,
                "category": a.category,
                "message": a.message,
                "entity_id": a.entity_id,
            }
            for a in data.alerts
        ],
    }
    print(json.dumps(output, indent=2))


# =============================================================================
# MAIN
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Peak_Trade Operator Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full dashboard
  python scripts/operator_dashboard.py

  # Only strategies
  python scripts/operator_dashboard.py --view strategies

  # JSON output
  python scripts/operator_dashboard.py --format json
        """,
    )

    parser.add_argument(
        "--view",
        choices=["all", "strategies", "portfolios", "alerts", "summary"],
        default="all",
        help="Which view to display (default: all)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Daten sammeln
    data = collect_dashboard_data()

    # Ausgabe
    if args.format == "json":
        output_json(data)
    else:
        if args.view == "all":
            print_full_dashboard(data)
        elif args.view == "strategies":
            print_strategies_view(data.strategies)
        elif args.view == "portfolios":
            print_portfolios_view(data.portfolios)
        elif args.view == "alerts":
            print_alerts_view(data.alerts)
        elif args.view == "summary":
            print_summary_view(data.summary)

    # Exit Code basierend auf Alerts
    if data.summary["alerts_error"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# src/live/drills.py
"""
Peak_Trade: Live-Dry-Run Drills & Safety-Validation (Phase 73)
================================================================

Framework für Sicherheits-Drills im Dry-Run-Modus.

Ziel:
    Systematische Prüfung, ob Gating + Dry-Run-Verhalten korrekt greifen,
    kein Pfad zu echten Orders existiert, und is_live_execution_allowed()
    konsistent mit der Safety-Policy ist.

WICHTIG: Phase 73 - Read-Only Simulation
    - Keine Config-Dateien ändern
    - Keine echten Orders
    - Keine Exchange-API-Calls
    - Nur Simulation & Validierung
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.core.environment import (
    LIVE_CONFIRM_TOKEN,
    EnvironmentConfig,
    TradingEnvironment,
    create_default_environment,
)
from src.live.safety import SafetyGuard, is_live_execution_allowed

logger = logging.getLogger(__name__)


# =============================================================================
# Datamodel
# =============================================================================


@dataclass
class LiveDrillScenario:
    """
    Ein Live-Drill-Szenario.

    Definiert ein Test-Szenario für die Validierung von Gating- und
    Safety-Mechanismen im Dry-Run-Modus.

    Attributes:
        name: Kurzer Name des Szenarios (z.B. "A - Voll gebremst")
        description: Beschreibung des Szenarios
        env_overrides: Dict mit Overrides für EnvironmentConfig
                      (z.B. {"enable_live_trading": False})
        risk_config_overrides: Optional Dict mit Overrides für LiveRiskConfig
        expected_is_live_execution_allowed: Erwartetes Ergebnis von
                                           is_live_execution_allowed()
        expected_reasons: Liste von erwarteten Reason-Strings
                         (z.B. ["enable_live_trading=False"])
        simulated_orders: Optional Liste von simulierten Orders für Risk-Checks
        simulated_daily_pnl: Optional simulierter Tages-PnL für Risk-Checks
    """

    name: str
    description: str
    env_overrides: dict[str, Any] = field(default_factory=dict)
    risk_config_overrides: dict[str, Any] | None = None
    expected_is_live_execution_allowed: bool = False
    expected_reasons: list[str] = field(default_factory=list)
    simulated_orders: list[dict[str, Any]] | None = None
    simulated_daily_pnl: float | None = None


@dataclass
class LiveDrillResult:
    """
    Ergebnis eines Live-Drills.

    Attributes:
        scenario_name: Name des Szenarios
        passed: Ob der Drill bestanden wurde
        is_live_execution_allowed: Tatsächliches Ergebnis von
                                   is_live_execution_allowed()
        reason: Reason-String von is_live_execution_allowed()
        effective_mode: Effektiver Modus aus SafetyGuard
        notes: Liste von Notizen (Gates, Limits, etc.)
        violations: Liste von Verletzungen (wo Erwartung ≠ Realität)
    """

    scenario_name: str
    passed: bool
    is_live_execution_allowed: bool
    reason: str
    effective_mode: str
    notes: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


# =============================================================================
# Drill Runner
# =============================================================================


class LiveDrillRunner:
    """
    Runner für Live-Dry-Run-Drills.

    Führt Drill-Szenarien aus und validiert die Gating- und Safety-Mechanismen.
    """

    def __init__(self) -> None:
        """Initialisiert den Drill-Runner."""
        self._results: list[LiveDrillResult] = []

    def run_scenario(
        self,
        scenario: LiveDrillScenario,
        base_env_config: EnvironmentConfig | None = None,
    ) -> LiveDrillResult:
        """
        Führt ein Drill-Szenario aus.

        Args:
            scenario: Das Drill-Szenario
            base_env_config: Basis-EnvironmentConfig (Default: create_default_environment())

        Returns:
            LiveDrillResult mit Ergebnis des Drills

        Note:
            Alle Änderungen sind rein im Speicher - keine Datei-Änderungen.
        """
        # Basis-EnvironmentConfig erstellen (im Speicher)
        if base_env_config is None:
            base_env_config = create_default_environment()

        # EnvironmentConfig mit Overrides erstellen
        env_dict = {
            "environment": base_env_config.environment,
            "enable_live_trading": base_env_config.enable_live_trading,
            "require_confirm_token": base_env_config.require_confirm_token,
            "confirm_token": base_env_config.confirm_token,
            "testnet_dry_run": base_env_config.testnet_dry_run,
            "log_all_orders": base_env_config.log_all_orders,
            "live_mode_armed": base_env_config.live_mode_armed,
            "live_dry_run_mode": base_env_config.live_dry_run_mode,
            "max_live_notional_per_order": base_env_config.max_live_notional_per_order,
            "max_live_notional_total": base_env_config.max_live_notional_total,
            "live_trade_min_size": base_env_config.live_trade_min_size,
        }
        env_dict.update(scenario.env_overrides)
        env_config = EnvironmentConfig(**env_dict)

        # SafetyGuard erstellen
        safety_guard = SafetyGuard(env_config=env_config)

        # is_live_execution_allowed() prüfen
        allowed, reason = is_live_execution_allowed(env_config)
        effective_mode = safety_guard.get_effective_mode()

        # Notizen sammeln
        notes: list[str] = []
        notes.append(f"Mode: {env_config.environment.value}")
        notes.append(f"Effective Mode: {effective_mode}")
        notes.append(f"enable_live_trading: {env_config.enable_live_trading}")
        notes.append(f"live_mode_armed: {env_config.live_mode_armed}")
        notes.append(f"live_dry_run_mode: {env_config.live_dry_run_mode}")
        if env_config.confirm_token:
            token_valid = env_config.confirm_token == LIVE_CONFIRM_TOKEN
            notes.append(f"confirm_token: {'SET (valid)' if token_valid else 'SET (invalid)'}")
        else:
            notes.append("confirm_token: NOT SET")

        # Optional: LiveRiskLimits prüfen (wenn simuliert)
        if scenario.risk_config_overrides or scenario.simulated_orders:
            # Risk-Limits-Check würde hier erfolgen (für zukünftige Erweiterung)
            notes.append("Risk-Limits: Simuliert (nicht vollständig implementiert in Phase 73)")

        # Violations prüfen
        violations: list[str] = []
        if allowed != scenario.expected_is_live_execution_allowed:
            violations.append(
                f"is_live_execution_allowed mismatch: "
                f"expected={scenario.expected_is_live_execution_allowed}, "
                f"actual={allowed}"
            )

        # Erwartete Reasons prüfen
        for expected_reason in scenario.expected_reasons:
            if expected_reason not in reason:
                violations.append(
                    f"Expected reason not found: '{expected_reason}' "
                    f"(actual reason: '{reason}')"
                )

        # Drill bestanden?
        passed = len(violations) == 0

        result = LiveDrillResult(
            scenario_name=scenario.name,
            passed=passed,
            is_live_execution_allowed=allowed,
            reason=reason,
            effective_mode=effective_mode,
            notes=notes,
            violations=violations,
        )

        self._results.append(result)
        return result

    def run_all(
        self,
        scenarios: list[LiveDrillScenario],
        base_env_config: EnvironmentConfig | None = None,
    ) -> list[LiveDrillResult]:
        """
        Führt alle Drill-Szenarien aus.

        Args:
            scenarios: Liste von Drill-Szenarien
            base_env_config: Basis-EnvironmentConfig (Default: create_default_environment())

        Returns:
            Liste von LiveDrillResult-Objekten
        """
        results = []
        for scenario in scenarios:
            result = self.run_scenario(scenario, base_env_config)
            results.append(result)
        return results

    def get_results(self) -> list[LiveDrillResult]:
        """Gibt alle bisherigen Ergebnisse zurück."""
        return list(self._results)

    def clear_results(self) -> None:
        """Löscht alle bisherigen Ergebnisse."""
        self._results.clear()


# =============================================================================
# Standard-Drills
# =============================================================================


def get_default_live_drill_scenarios() -> list[LiveDrillScenario]:
    """
    Gibt die Standard-Live-Drill-Szenarien zurück.

    Returns:
        Liste von LiveDrillScenario-Objekten

    Szenarien:
        A: Voll gebremst (Default-Safety)
        B: Gate 1 ok, Gate 2 fehlt
        C: Alles armed, aber Dry-Run aktiv
        D: Confirm-Token fehlt
        E: Risk-Limits schlagen an (optional, für zukünftige Erweiterung)
        F: Nicht-Live-Modus (Testnet/Paper)
    """
    scenarios = []

    # Drill A – Voll gebremst (Default-Safety)
    scenarios.append(
        LiveDrillScenario(
            name="A - Voll gebremst (Default-Safety)",
            description=(
                "Live-Modus, aber enable_live_trading=False. "
                "Erwartung: is_live_execution_allowed=False, "
                "Reason enthält Hinweis auf enable_live_trading."
            ),
            env_overrides={
                "environment": TradingEnvironment.LIVE,
                "enable_live_trading": False,
                "live_mode_armed": False,
                "live_dry_run_mode": True,
            },
            expected_is_live_execution_allowed=False,
            expected_reasons=["enable_live_trading=False"],
        )
    )

    # Drill B – Gate 1 ok, Gate 2 fehlt
    scenarios.append(
        LiveDrillScenario(
            name="B - Gate 1 ok, Gate 2 fehlt",
            description=(
                "Live-Modus, enable_live_trading=True, aber live_mode_armed=False. "
                "Erwartung: is_live_execution_allowed=False, "
                "Reason enthält live_mode_armed."
            ),
            env_overrides={
                "environment": TradingEnvironment.LIVE,
                "enable_live_trading": True,
                "live_mode_armed": False,
                "live_dry_run_mode": True,
            },
            expected_is_live_execution_allowed=False,
            expected_reasons=["live_mode_armed=False"],
        )
    )

    # Drill C – Alles armed, aber Dry-Run aktiv
    scenarios.append(
        LiveDrillScenario(
            name="C - Alles armed, aber Dry-Run aktiv",
            description=(
                "Live-Modus, alle Gates offen, aber live_dry_run_mode=True. "
                "Erwartung: is_live_execution_allowed=False, "
                "Reason enthält live_dry_run_mode=True. "
                "Ziel: Sicherstellen, dass Dry-Run im Report klar erkennbar ist."
            ),
            env_overrides={
                "environment": TradingEnvironment.LIVE,
                "enable_live_trading": True,
                "live_mode_armed": True,
                "live_dry_run_mode": True,  # Phase 71/72: Blockiert
                "confirm_token": LIVE_CONFIRM_TOKEN,
            },
            expected_is_live_execution_allowed=False,
            expected_reasons=["live_dry_run_mode=True"],
        )
    )

    # Drill D – Confirm-Token fehlt
    scenarios.append(
        LiveDrillScenario(
            name="D - Confirm-Token fehlt",
            description=(
                "Live-Modus, alle Gates offen, aber confirm_token ungültig/nicht gesetzt. "
                "Erwartung: is_live_execution_allowed=False, "
                "Reason: fehlendes/inkorrektes confirm_token."
            ),
            env_overrides={
                "environment": TradingEnvironment.LIVE,
                "enable_live_trading": True,
                "live_mode_armed": True,
                "live_dry_run_mode": False,  # Theoretisches Szenario
                "require_confirm_token": True,
                "confirm_token": "WRONG_TOKEN",
            },
            expected_is_live_execution_allowed=False,
            expected_reasons=["confirm_token"],
        )
    )

    # Drill E – Risk-Limits schlagen an (optional, für zukünftige Erweiterung)
    scenarios.append(
        LiveDrillScenario(
            name="E - Risk-Limits schlagen an (Design)",
            description=(
                "Alle Gates so gesetzt, dass Execution theoretisch möglich wäre. "
                "Risk-Limits würden blockieren (z.B. max_live_notional_total überschritten). "
                "Erwartung: is_live_execution_allowed kann True sein (Gating), "
                "aber Risk-Limits würden in späteren Phasen blockieren."
            ),
            env_overrides={
                "environment": TradingEnvironment.LIVE,
                "enable_live_trading": True,
                "live_mode_armed": True,
                "live_dry_run_mode": False,  # Theoretisches Szenario
                "confirm_token": LIVE_CONFIRM_TOKEN,
            },
            risk_config_overrides={
                "max_live_notional_total": 1000.0,  # Niedriges Limit
            },
            simulated_orders=[
                {"symbol": "BTC/EUR", "notional": 2000.0},  # Überschreitet Limit
            ],
            expected_is_live_execution_allowed=True,  # Gating erlaubt, aber Risk würde blockieren
            expected_reasons=[],
        )
    )

    # Drill F – Nicht-Live-Modus
    scenarios.append(
        LiveDrillScenario(
            name="F - Nicht-Live-Modus (Testnet)",
            description=(
                "Testnet-Modus. "
                "Erwartung: is_live_execution_allowed=False, "
                "Reason erklärt, dass Environment nicht LIVE ist."
            ),
            env_overrides={
                "environment": TradingEnvironment.TESTNET,
                "enable_live_trading": False,
                "live_mode_armed": False,
                "live_dry_run_mode": True,
            },
            expected_is_live_execution_allowed=False,
            expected_reasons=["nicht LIVE"],
        )
    )

    # Drill G – Paper-Modus
    scenarios.append(
        LiveDrillScenario(
            name="G - Paper-Modus",
            description=(
                "Paper-Modus. "
                "Erwartung: is_live_execution_allowed=False, "
                "Reason erklärt, dass Environment nicht LIVE ist."
            ),
            env_overrides={
                "environment": TradingEnvironment.PAPER,
                "enable_live_trading": False,
                "live_mode_armed": False,
                "live_dry_run_mode": True,
            },
            expected_is_live_execution_allowed=False,
            expected_reasons=["nicht LIVE"],
        )
    )

    return scenarios









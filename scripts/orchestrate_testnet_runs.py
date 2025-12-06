#!/usr/bin/env python3
"""
Peak_Trade: Testnet-Orchestrator CLI (Phase 37)
===============================================

Command-Line-Interface zur kontrollierten Orchestrierung von Testnet-Sessions.
Kombiniert Profile, Limits und automatische Reports in einem einheitlichen Workflow.

Features:
- Profile-basierter Start von Testnet-Sessions
- Limit-Checks vor Session-Start (Run-Limits, Daily-Limits, Symbol-Whitelist)
- Dry-Run-Modus zur Vorschau
- Optionale Auto-Report-Generierung
- Overrides fuer Laufzeit, Notional, etc.

Usage:
    # Profil auflisten
    python -m scripts.orchestrate_testnet_runs --list

    # Profil starten
    python -m scripts.orchestrate_testnet_runs --profile ma_crossover_small

    # Dry-Run (nur Checks, kein Start)
    python -m scripts.orchestrate_testnet_runs --profile ma_crossover_small --dry-run

    # Mit Overrides
    python -m scripts.orchestrate_testnet_runs --profile ma_crossover_small \\
        --override-duration 30 --override-max-notional 300.0

    # Aktuelles Budget anzeigen
    python -m scripts.orchestrate_testnet_runs --budget

Voraussetzungen:
    - Environment-Variablen KRAKEN_TESTNET_API_KEY und KRAKEN_TESTNET_API_SECRET
    - config/config.toml mit [testnet_limits], [testnet_profiles], [testnet_orchestration]
    - config/config.toml mit [environment] mode = "testnet"

WICHTIG: Nur Testnet-Trading! Keine echten Live-Trades!
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config, PeakConfig
from src.live.testnet_limits import (
    TestnetLimitsController,
    TestnetCheckResult,
    load_testnet_limits_from_config,
)
from src.live.testnet_profiles import (
    TestnetSessionProfile,
    load_testnet_profiles,
    get_profiles_summary,
    validate_profile,
)


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging fuer CLI."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Weniger Noise von requests/urllib3
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return logging.getLogger("testnet_orchestrator")


# =============================================================================
# Orchestration Config
# =============================================================================


@dataclass
class OrchestrationConfig:
    """Konfiguration fuer den Orchestrator."""
    runs_base_dir: Path
    reports_dir: Path
    auto_generate_report: bool
    report_format: str
    usage_retention_days: int

    @classmethod
    def from_config(cls, cfg: PeakConfig) -> "OrchestrationConfig":
        """Laedt OrchestrationConfig aus PeakConfig."""
        return cls(
            runs_base_dir=Path(cfg.get("testnet_orchestration.runs_base_dir", "test_runs/")),
            reports_dir=Path(cfg.get("testnet_orchestration.reports_dir", "test_results/reports/")),
            auto_generate_report=cfg.get("testnet_orchestration.auto_generate_report", False),
            report_format=cfg.get("testnet_orchestration.report_format", "markdown"),
            usage_retention_days=int(cfg.get("testnet_orchestration.usage_retention_days", 30)),
        )


# =============================================================================
# Orchestration Result
# =============================================================================


@dataclass
class OrchestrationResult:
    """Ergebnis einer Orchestrierung."""
    success: bool
    profile_id: str
    run_id: Optional[str] = None
    check_result: Optional[TestnetCheckResult] = None
    session_summary: Optional[Dict[str, Any]] = None
    report_path: Optional[Path] = None
    error: Optional[str] = None
    dry_run: bool = False


# =============================================================================
# Testnet Orchestrator
# =============================================================================


class TestnetOrchestrator:
    """
    Orchestriert Testnet-Sessions mit Profilen und Limits.

    Workflow:
    1. Profil laden
    2. Overrides anwenden
    3. Limits pruefen (Symbol, Run, Daily)
    4. Session starten (oder Dry-Run)
    5. Verbrauch registrieren
    6. Optional: Report generieren
    """

    def __init__(
        self,
        cfg: PeakConfig,
        limits_controller: TestnetLimitsController,
        orch_config: OrchestrationConfig,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialisiert den Orchestrator.

        Args:
            cfg: PeakConfig-Instanz
            limits_controller: TestnetLimitsController
            orch_config: OrchestrationConfig
            logger: Optionaler Logger
        """
        self._cfg = cfg
        self._limits = limits_controller
        self._orch_config = orch_config
        self._logger = logger or logging.getLogger(__name__)

        # Profile laden
        self._profiles = load_testnet_profiles(cfg)

        self._logger.info(
            f"[ORCHESTRATOR] Initialisiert mit {len(self._profiles)} Profilen"
        )

    @property
    def profiles(self) -> Dict[str, TestnetSessionProfile]:
        """Zugriff auf geladene Profile."""
        return self._profiles

    @property
    def limits_controller(self) -> TestnetLimitsController:
        """Zugriff auf Limits-Controller."""
        return self._limits

    def get_profile(self, profile_id: str) -> Optional[TestnetSessionProfile]:
        """Holt ein Profil nach ID."""
        return self._profiles.get(profile_id)

    def list_profiles(self) -> List[str]:
        """Listet alle Profil-IDs."""
        return sorted(self._profiles.keys())

    def check_profile(
        self,
        profile: TestnetSessionProfile,
    ) -> TestnetCheckResult:
        """
        Prueft ein Profil gegen alle Limits.

        Args:
            profile: Das zu pruefende Profil

        Returns:
            TestnetCheckResult
        """
        return self._limits.check_run_allowed(
            symbol=profile.symbol,
            planned_notional=profile.max_notional,
            planned_trades=profile.max_trades,
            planned_duration_minutes=profile.duration_minutes,
        )

    def run_profile(
        self,
        profile_id: str,
        dry_run: bool = False,
        override_duration: Optional[int] = None,
        override_max_notional: Optional[float] = None,
        override_max_trades: Optional[int] = None,
    ) -> OrchestrationResult:
        """
        Fuehrt ein Profil aus.

        Args:
            profile_id: ID des Profils
            dry_run: Nur Checks, kein Start
            override_duration: Override fuer Laufzeit
            override_max_notional: Override fuer max Notional
            override_max_trades: Override fuer max Trades

        Returns:
            OrchestrationResult
        """
        # 1. Profil laden
        profile = self.get_profile(profile_id)
        if profile is None:
            return OrchestrationResult(
                success=False,
                profile_id=profile_id,
                error=f"Profil '{profile_id}' nicht gefunden. "
                      f"Verfuegbar: {self.list_profiles()}",
                dry_run=dry_run,
            )

        # 2. Overrides anwenden
        if override_duration is not None or override_max_notional is not None or override_max_trades is not None:
            overrides = {}
            if override_duration is not None:
                overrides["duration_minutes"] = override_duration
            if override_max_notional is not None:
                overrides["max_notional"] = override_max_notional
            if override_max_trades is not None:
                overrides["max_trades"] = override_max_trades

            profile = profile.with_overrides(**overrides)
            self._logger.info(f"[ORCHESTRATOR] Overrides angewendet: {overrides}")

        # 3. Limits pruefen
        check_result = self.check_profile(profile)
        if not check_result.allowed:
            self._logger.warning(
                f"[ORCHESTRATOR] Limit-Verletzung: {check_result.reasons}"
            )
            return OrchestrationResult(
                success=False,
                profile_id=profile_id,
                check_result=check_result,
                error=f"Limit-Verletzung: {'; '.join(check_result.reasons)}",
                dry_run=dry_run,
            )

        self._logger.info(f"[ORCHESTRATOR] Limit-Checks bestanden fuer '{profile_id}'")

        # 4. Dry-Run?
        if dry_run:
            self._logger.info("[ORCHESTRATOR] Dry-Run: Kein Session-Start")
            return OrchestrationResult(
                success=True,
                profile_id=profile_id,
                check_result=check_result,
                dry_run=True,
            )

        # 5. Session starten
        try:
            session_summary, run_id = self._start_session(profile)
        except Exception as e:
            self._logger.error(f"[ORCHESTRATOR] Session-Start fehlgeschlagen: {e}")
            return OrchestrationResult(
                success=False,
                profile_id=profile_id,
                check_result=check_result,
                error=f"Session-Start fehlgeschlagen: {e}",
                dry_run=dry_run,
            )

        # 6. Verbrauch registrieren
        actual_notional = session_summary.get("total_notional", profile.max_notional or 0)
        actual_trades = session_summary.get("total_orders", profile.max_trades or 0)

        self._limits.register_run_consumption(
            notional=actual_notional,
            trades=actual_trades,
        )

        # 7. Optional: Report generieren
        report_path = None
        if self._orch_config.auto_generate_report:
            try:
                report_path = self._generate_report(profile, run_id, session_summary)
            except Exception as e:
                self._logger.warning(f"[ORCHESTRATOR] Report-Generierung fehlgeschlagen: {e}")

        return OrchestrationResult(
            success=True,
            profile_id=profile_id,
            run_id=run_id,
            check_result=check_result,
            session_summary=session_summary,
            report_path=report_path,
            dry_run=False,
        )

    def _start_session(
        self,
        profile: TestnetSessionProfile,
    ) -> tuple[Dict[str, Any], str]:
        """
        Startet eine Testnet-Session fuer ein Profil.

        Args:
            profile: Das auszufuehrende Profil

        Returns:
            Tuple von (session_summary, run_id)
        """
        from scripts.run_testnet_session import build_testnet_session

        # Run-ID generieren
        now = datetime.now(timezone.utc)
        run_id = f"testnet_{profile.id}_{now.strftime('%Y%m%d_%H%M%S')}"

        self._logger.info(
            f"[ORCHESTRATOR] Starte Session: "
            f"profile={profile.id}, run_id={run_id}, "
            f"duration={profile.duration_minutes}min"
        )

        # Session bauen
        session = build_testnet_session(
            cfg=self._cfg,
            strategy_name=profile.strategy,
            symbol_override=profile.symbol,
            timeframe_override=profile.timeframe,
            run_id=run_id,
            enable_logging=True,
            log_dir_override=str(self._orch_config.runs_base_dir),
            logger=self._logger,
        )

        # Warmup
        session.warmup()

        # Session ausfuehren
        if profile.duration_minutes:
            session.run_for_duration(profile.duration_minutes)
        else:
            # Ohne Duration: kurzer Test-Run (5 Minuten)
            session.run_for_duration(5)

        # Summary holen
        summary = session.get_execution_summary()

        return summary, run_id

    def _generate_report(
        self,
        profile: TestnetSessionProfile,
        run_id: str,
        session_summary: Dict[str, Any],
    ) -> Path:
        """
        Generiert einen Report fuer einen Run.

        Args:
            profile: Das verwendete Profil
            run_id: Die Run-ID
            session_summary: Session-Summary

        Returns:
            Pfad zum generierten Report
        """
        # Reports-Verzeichnis erstellen
        self._orch_config.reports_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        report_name = f"testnet_report_{profile.id}_{now.strftime('%Y%m%d_%H%M%S')}.md"
        report_path = self._orch_config.reports_dir / report_name

        # Einfacher Markdown-Report
        lines = [
            f"# Testnet Run Report: {profile.id}",
            "",
            f"**Run-ID:** {run_id}",
            f"**Datum:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Profil",
            "",
            f"- **Strategie:** {profile.strategy}",
            f"- **Symbol:** {profile.symbol}",
            f"- **Timeframe:** {profile.timeframe}",
            f"- **Laufzeit:** {profile.duration_minutes} Minuten",
            f"- **Max Notional:** {profile.max_notional}",
            f"- **Max Trades:** {profile.max_trades}",
            "",
            "## Session Summary",
            "",
        ]

        # Session-Metriken
        if "session_metrics" in session_summary:
            metrics = session_summary["session_metrics"]
            lines.extend([
                f"- **Steps:** {metrics.get('steps', 'N/A')}",
                f"- **Total Orders:** {metrics.get('total_orders', 'N/A')}",
                f"- **Filled Orders:** {metrics.get('filled_orders', 'N/A')}",
                f"- **Rejected Orders:** {metrics.get('rejected_orders', 'N/A')}",
                f"- **Fill Rate:** {metrics.get('fill_rate', 0):.1%}",
            ])

        lines.extend([
            "",
            "---",
            "",
            f"*Report generiert am {now.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        ])

        # Report schreiben
        with open(report_path, "w") as f:
            f.write("\n".join(lines))

        self._logger.info(f"[ORCHESTRATOR] Report generiert: {report_path}")
        return report_path


# =============================================================================
# CLI Functions
# =============================================================================


def cmd_list_profiles(cfg: PeakConfig, logger: logging.Logger) -> int:
    """Listet alle verfuegbaren Profile."""
    print(get_profiles_summary(cfg))
    return 0


def cmd_show_budget(cfg: PeakConfig, logger: logging.Logger) -> int:
    """Zeigt das aktuelle Tages-Budget an."""
    controller = load_testnet_limits_from_config(cfg)
    budget = controller.get_remaining_budget()

    print("\n=== Testnet Tages-Budget ===")
    print(f"Datum: {budget['day']}")
    print()
    print("Verbraucht heute:")
    print(f"  Notional:  {budget['notional_used']:.2f}")
    print(f"  Trades:    {budget['trades_executed']}")
    print(f"  Runs:      {budget['runs_completed']}")
    print()
    print("Verbleibend:")
    if budget['remaining_notional'] is not None:
        print(f"  Notional:  {budget['remaining_notional']:.2f}")
    else:
        print("  Notional:  unbegrenzt")
    if budget['remaining_trades'] is not None:
        print(f"  Trades:    {budget['remaining_trades']}")
    else:
        print("  Trades:    unbegrenzt")
    print()
    print("Limits:")
    limits = budget['limits']
    print(f"  Max Notional/Tag:  {limits.get('max_notional_per_day', 'N/A')}")
    print(f"  Max Trades/Tag:    {limits.get('max_trades_per_day', 'N/A')}")
    print("=" * 30)

    return 0


def cmd_run_profile(
    cfg: PeakConfig,
    profile_id: str,
    dry_run: bool,
    override_duration: Optional[int],
    override_max_notional: Optional[float],
    override_max_trades: Optional[int],
    logger: logging.Logger,
) -> int:
    """Fuehrt ein Profil aus."""
    # Orchestrator erstellen
    limits_controller = load_testnet_limits_from_config(cfg)
    orch_config = OrchestrationConfig.from_config(cfg)

    orchestrator = TestnetOrchestrator(
        cfg=cfg,
        limits_controller=limits_controller,
        orch_config=orch_config,
        logger=logger,
    )

    # Profil pruefen
    profile = orchestrator.get_profile(profile_id)
    if profile is None:
        print(f"\nFehler: Profil '{profile_id}' nicht gefunden.")
        print(f"Verfuegbare Profile: {orchestrator.list_profiles()}")
        return 1

    # Profil-Info anzeigen
    print(f"\n=== Profil: {profile_id} ===")
    print(f"Strategie:  {profile.strategy}")
    print(f"Symbol:     {profile.symbol}")
    print(f"Timeframe:  {profile.timeframe}")
    print(f"Laufzeit:   {profile.duration_minutes} Minuten")
    print(f"Max Notional: {profile.max_notional}")
    print(f"Max Trades:   {profile.max_trades}")
    if profile.description:
        print(f"Beschreibung: {profile.description}")
    print()

    # Overrides anzeigen
    if override_duration or override_max_notional or override_max_trades:
        print("Overrides:")
        if override_duration:
            print(f"  --override-duration: {override_duration}")
        if override_max_notional:
            print(f"  --override-max-notional: {override_max_notional}")
        if override_max_trades:
            print(f"  --override-max-trades: {override_max_trades}")
        print()

    # Dry-Run oder echte Ausfuehrung
    if dry_run:
        print("[DRY-RUN] Pruefe Limits...")

        # Overrides anwenden fuer Check
        check_profile = profile
        if override_duration or override_max_notional or override_max_trades:
            overrides = {}
            if override_duration:
                overrides["duration_minutes"] = override_duration
            if override_max_notional:
                overrides["max_notional"] = override_max_notional
            if override_max_trades:
                overrides["max_trades"] = override_max_trades
            check_profile = profile.with_overrides(**overrides)

        check_result = orchestrator.check_profile(check_profile)

        if check_result.allowed:
            print("[OK] Alle Limit-Checks bestanden.")
            print("\nAktueller Usage-Stand:")
            if check_result.current_usage:
                print(f"  Notional heute: {check_result.current_usage.get('notional_used', 0):.2f}")
                print(f"  Trades heute:   {check_result.current_usage.get('trades_executed', 0)}")
            print("\n[DRY-RUN] Session wuerde gestartet werden.")
            return 0
        else:
            print("[BLOCKED] Limit-Verletzung!")
            for reason in check_result.reasons:
                print(f"  - {reason}")
            return 1

    # Echte Ausfuehrung
    print("Starte Testnet-Session...")
    print("=" * 50)

    result = orchestrator.run_profile(
        profile_id=profile_id,
        dry_run=False,
        override_duration=override_duration,
        override_max_notional=override_max_notional,
        override_max_trades=override_max_trades,
    )

    print("=" * 50)

    if result.success:
        print(f"\n[SUCCESS] Session abgeschlossen.")
        print(f"Run-ID: {result.run_id}")
        if result.session_summary:
            metrics = result.session_summary.get("session_metrics", {})
            print(f"Total Orders: {metrics.get('total_orders', 'N/A')}")
            print(f"Filled: {metrics.get('filled_orders', 'N/A')}")
        if result.report_path:
            print(f"Report: {result.report_path}")
        return 0
    else:
        print(f"\n[ERROR] Session fehlgeschlagen: {result.error}")
        return 1


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """Haupteinstiegspunkt fuer Testnet-Orchestrator CLI."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Testnet-Orchestrator (Phase 37)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Profile auflisten
  python -m scripts.orchestrate_testnet_runs --list

  # Profil starten
  python -m scripts.orchestrate_testnet_runs --profile ma_crossover_small

  # Dry-Run (nur Checks)
  python -m scripts.orchestrate_testnet_runs --profile ma_crossover_small --dry-run

  # Mit Overrides
  python -m scripts.orchestrate_testnet_runs --profile ma_crossover_small \\
      --override-duration 30 --override-max-notional 300.0

  # Budget anzeigen
  python -m scripts.orchestrate_testnet_runs --budget

WICHTIG: Nur Testnet-Trading! Keine echten Live-Trades!
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste alle verfuegbaren Profile",
    )
    parser.add_argument(
        "--budget",
        action="store_true",
        help="Zeige aktuelles Tages-Budget",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Profil-ID zum Starten",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Limit-Checks, kein Session-Start",
    )
    parser.add_argument(
        "--override-duration",
        type=int,
        default=None,
        help="Override: Laufzeit in Minuten",
    )
    parser.add_argument(
        "--override-max-notional",
        type=float,
        default=None,
        help="Override: Max Notional",
    )
    parser.add_argument(
        "--override-max-trades",
        type=int,
        default=None,
        help="Override: Max Trades",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )

    args = parser.parse_args()

    # Logging setup
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("Peak_Trade Testnet-Orchestrator (Phase 37)")
    logger.info("=" * 60)

    # Config laden
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Fehler: Config-Datei nicht gefunden: {config_path}")
        return 1

    try:
        cfg = load_config(config_path)
    except Exception as e:
        print(f"Fehler beim Laden der Config: {e}")
        return 1

    # Command ausfuehren
    if args.list:
        return cmd_list_profiles(cfg, logger)

    if args.budget:
        return cmd_show_budget(cfg, logger)

    if args.profile:
        return cmd_run_profile(
            cfg=cfg,
            profile_id=args.profile,
            dry_run=args.dry_run,
            override_duration=args.override_duration,
            override_max_notional=args.override_max_notional,
            override_max_trades=args.override_max_trades,
            logger=logger,
        )

    # Keine Aktion angegeben
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

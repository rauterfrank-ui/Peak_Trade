#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/check_live_readiness.py
"""
Peak_Trade: Live-Readiness-Check (Phase 39)
============================================

Prüft, ob das System für eine bestimmte Stufe (Shadow, Testnet, Live) bereit ist.

Checks:
- Config vorhanden und gültig
- Environment-Variable / Modus korrekt
- Risk-Limits konfiguriert
- Exchange-Config (für Testnet/Live)
- Baseline-Tests (optional)

Usage:
    python scripts/check_live_readiness.py --stage shadow
    python scripts/check_live_readiness.py --stage testnet
    python scripts/check_live_readiness.py --stage testnet --run-tests
    python scripts/check_live_readiness.py --stage live --verbose

Exit Codes:
    0 = Alle Checks bestanden
    1 = Mindestens ein Check fehlgeschlagen
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Pfad-Setup
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.live.risk_limits import LiveRiskLimits

# =============================================================================
# Check Results
# =============================================================================


@dataclass
class CheckResult:
    """Ergebnis eines einzelnen Checks."""
    name: str
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)


@dataclass
class WarningResult:
    """Ergebnis eines Soft-Checks (Warnung, kein Blocker)."""
    name: str
    message: str
    details: List[str] = field(default_factory=list)


@dataclass
class ReadinessReport:
    """Gesamtbericht aller Checks."""
    stage: str
    checks: List[CheckResult]
    warnings: List[WarningResult] = field(default_factory=list)
    
    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)
    
    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)


# =============================================================================
# Individual Checks
# =============================================================================


def check_config_exists(config_path: Path) -> CheckResult:
    """Prüft, ob die Config-Datei existiert."""
    if config_path.exists():
        return CheckResult(
            name="Config-Datei",
            passed=True,
            message=f"Vorhanden: {config_path}",
        )
    return CheckResult(
        name="Config-Datei",
        passed=False,
        message=f"Nicht gefunden: {config_path}",
        details=["Bitte config/config.toml erstellen oder PEAK_TRADE_CONFIG_PATH setzen"],
    )


def check_config_valid(config_path: Path) -> CheckResult:
    """Prüft, ob die Config gültig ist."""
    try:
        cfg = load_config(config_path)
        return CheckResult(
            name="Config-Validität",
            passed=True,
            message="Config erfolgreich geladen",
        )
    except Exception as e:
        return CheckResult(
            name="Config-Validität",
            passed=False,
            message=f"Config ungültig: {e}",
        )


def check_risk_limits(cfg: PeakConfig) -> CheckResult:
    """Prüft, ob Risk-Limits konfiguriert sind."""
    details = []
    issues = []
    
    # Live-Risk-Limits prüfen
    max_order = cfg.get("live_risk.max_order_notional")
    max_daily_loss = cfg.get("live_risk.max_daily_loss_abs")
    max_daily_pct = cfg.get("live_risk.max_daily_loss_pct")
    
    if max_order is not None:
        details.append(f"max_order_notional: {max_order}")
    else:
        issues.append("max_order_notional nicht gesetzt")
    
    if max_daily_loss is not None:
        details.append(f"max_daily_loss_abs: {max_daily_loss}")
    
    if max_daily_pct is not None:
        details.append(f"max_daily_loss_pct: {max_daily_pct}")
    
    # Mindestens ein Limit muss gesetzt sein
    if max_order is None and max_daily_loss is None and max_daily_pct is None:
        issues.append("Keine Live-Risk-Limits konfiguriert")
    
    if issues:
        return CheckResult(
            name="Risk-Limits",
            passed=False,
            message="; ".join(issues),
            details=details,
        )
    
    return CheckResult(
        name="Risk-Limits",
        passed=True,
        message="Risk-Limits konfiguriert",
        details=details,
    )


def check_shadow_config(cfg: PeakConfig) -> CheckResult:
    """Prüft Shadow-spezifische Config."""
    details = []
    
    shadow_enabled = cfg.get("shadow.enabled", False)
    fee_rate = cfg.get("shadow.fee_rate", None)
    
    details.append(f"shadow.enabled: {shadow_enabled}")
    if fee_rate is not None:
        details.append(f"shadow.fee_rate: {fee_rate}")
    
    if shadow_enabled:
        return CheckResult(
            name="Shadow-Config",
            passed=True,
            message="Shadow aktiviert",
            details=details,
        )
    
    return CheckResult(
        name="Shadow-Config",
        passed=True,  # Optional - Shadow kann auch ohne explizite Config laufen
        message="Shadow nicht explizit aktiviert (kann trotzdem funktionieren)",
        details=details,
    )


def check_exchange_config(cfg: PeakConfig, stage: str) -> CheckResult:
    """Prüft Exchange-Config für Testnet/Live."""
    details = []
    
    exchange_type = cfg.get("exchange.default_type", "dummy")
    details.append(f"exchange.default_type: {exchange_type}")
    
    if stage == "testnet":
        # Für Testnet: dummy oder kraken_testnet OK
        if exchange_type in ("dummy", "kraken_testnet"):
            return CheckResult(
                name="Exchange-Config",
                passed=True,
                message=f"Exchange-Type: {exchange_type}",
                details=details,
            )
        return CheckResult(
            name="Exchange-Config",
            passed=False,
            message=f"Unerwarteter Exchange-Type für Testnet: {exchange_type}",
            details=details + ["Erwartet: 'dummy' oder 'kraken_testnet'"],
        )
    
    elif stage == "live":
        # Für Live: kraken_live oder ähnlich
        if exchange_type.endswith("_live") or exchange_type == "kraken":
            return CheckResult(
                name="Exchange-Config",
                passed=True,
                message=f"Live-Exchange-Type: {exchange_type}",
                details=details,
            )
        return CheckResult(
            name="Exchange-Config",
            passed=False,
            message=f"Exchange-Type nicht für Live geeignet: {exchange_type}",
            details=details,
        )
    
    # Shadow braucht keine spezielle Exchange-Config
    return CheckResult(
        name="Exchange-Config",
        passed=True,
        message=f"Exchange-Type: {exchange_type} (Shadow benötigt keine spezielle Konfiguration)",
        details=details,
    )


def check_api_credentials(stage: str) -> CheckResult:
    """Prüft, ob API-Credentials gesetzt sind (nur für Testnet/Live)."""
    if stage == "shadow":
        return CheckResult(
            name="API-Credentials",
            passed=True,
            message="Nicht erforderlich für Shadow",
        )
    
    details = []
    
    # Testnet
    testnet_key = os.environ.get("KRAKEN_TESTNET_API_KEY")
    testnet_secret = os.environ.get("KRAKEN_TESTNET_API_SECRET")
    
    if testnet_key:
        details.append("KRAKEN_TESTNET_API_KEY: ✓ gesetzt")
    else:
        details.append("KRAKEN_TESTNET_API_KEY: ✗ nicht gesetzt")
    
    if testnet_secret:
        details.append("KRAKEN_TESTNET_API_SECRET: ✓ gesetzt")
    else:
        details.append("KRAKEN_TESTNET_API_SECRET: ✗ nicht gesetzt")
    
    if stage == "testnet":
        # Für Testnet mit DummyClient sind Keys optional
        return CheckResult(
            name="API-Credentials",
            passed=True,  # Nicht kritisch bei DummyClient
            message="API-Keys geprüft (optional bei DummyClient)",
            details=details,
        )
    
    elif stage == "live":
        # Live-Keys prüfen
        live_key = os.environ.get("KRAKEN_API_KEY")
        live_secret = os.environ.get("KRAKEN_API_SECRET")
        
        if live_key:
            details.append("KRAKEN_API_KEY: ✓ gesetzt")
        else:
            details.append("KRAKEN_API_KEY: ✗ nicht gesetzt")
        
        if live_secret:
            details.append("KRAKEN_API_SECRET: ✓ gesetzt")
        else:
            details.append("KRAKEN_API_SECRET: ✗ nicht gesetzt")
        
        if not live_key or not live_secret:
            return CheckResult(
                name="API-Credentials",
                passed=False,
                message="Live-API-Keys fehlen",
                details=details,
            )
    
    return CheckResult(
        name="API-Credentials",
        passed=True,
        message="API-Credentials geprüft",
        details=details,
    )


def check_tests(run_tests: bool) -> CheckResult:
    """Führt optionale Baseline-Tests aus."""
    if not run_tests:
        return CheckResult(
            name="Baseline-Tests",
            passed=True,
            message="Übersprungen (--run-tests nicht angegeben)",
        )
    
    try:
        result = subprocess.run(
            ["pytest", "-q", "--tb=no"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=300,  # 5 Minuten Timeout
        )
        
        # Letzte Zeile enthält Summary
        summary_line = result.stdout.strip().split("\n")[-1] if result.stdout else ""
        
        if result.returncode == 0:
            return CheckResult(
                name="Baseline-Tests",
                passed=True,
                message=f"Tests bestanden: {summary_line}",
            )
        else:
            return CheckResult(
                name="Baseline-Tests",
                passed=False,
                message=f"Tests fehlgeschlagen: {summary_line}",
                details=[result.stderr[:500] if result.stderr else ""],
            )
    
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="Baseline-Tests",
            passed=False,
            message="Tests abgebrochen (Timeout nach 5 Minuten)",
        )
    except Exception as e:
        return CheckResult(
            name="Baseline-Tests",
            passed=False,
            message=f"Tests konnten nicht ausgeführt werden: {e}",
        )


def check_environment_mode(cfg: PeakConfig, stage: str) -> CheckResult:
    """Prüft, ob der Environment-Modus zur Stufe passt."""
    env_mode = cfg.get("environment.mode", "paper")
    
    expected_modes = {
        "shadow": ["paper", "shadow"],
        "testnet": ["testnet"],
        "live": ["live"],
    }
    
    expected = expected_modes.get(stage, [])
    
    if env_mode in expected or stage == "shadow":
        # Shadow ist flexibel
        return CheckResult(
            name="Environment-Mode",
            passed=True,
            message=f"Mode: {env_mode}",
        )
    
    return CheckResult(
        name="Environment-Mode",
        passed=False,
        message=f"Mode '{env_mode}' passt nicht zu Stufe '{stage}'",
        details=[f"Erwartet für {stage}: {expected}"],
    )


def check_live_risk_config_loadable(cfg: PeakConfig, stage: str) -> CheckResult:
    """
    Hard-Check: Prüft, ob die Live-Risk-Konfiguration gültig geladen werden kann.
    
    Dieser Check ist für Testnet und Live PFLICHT.
    Er versucht, LiveRiskLimits.from_config() aufzurufen, ohne echte Trades auszulösen.
    
    Args:
        cfg: Geladene PeakConfig
        stage: Aktuelle Stufe (shadow/testnet/live)
    
    Returns:
        CheckResult mit passed=True wenn Konfiguration ladbar, sonst False
    """
    # Für Shadow ist dieser Check optional/informativ
    if stage == "shadow":
        # Trotzdem prüfen, aber nicht blocken
        try:
            from src.live.risk_limits import LiveRiskLimits
            _ = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)
            return CheckResult(
                name="Live-Risk-Config",
                passed=True,
                message="Live-Risk-Config ladbar (optional für Shadow)",
            )
        except Exception as e:
            return CheckResult(
                name="Live-Risk-Config",
                passed=True,  # Für Shadow nicht blockierend
                message=f"Live-Risk-Config nicht vollständig (optional für Shadow): {e}",
            )
    
    # Für Testnet und Live: PFLICHT
    try:
        from src.live.risk_limits import LiveRiskLimits
        
        # Prüfen, ob [live_risk]-Block existiert
        live_risk_block = cfg.get("live_risk")
        if live_risk_block is None:
            return CheckResult(
                name="Live-Risk-Config",
                passed=False,
                message="ERROR: [live_risk]-Block fehlt in der Config",
                details=[
                    "Bitte [live_risk]-Sektion in config.toml hinzufügen.",
                    "Siehe docs/SAFETY_POLICY_TESTNET_AND_LIVE.md für Details.",
                    "Mindestens max_order_notional sollte gesetzt sein.",
                ],
            )
        
        # Versuchen, LiveRiskLimits zu erstellen
        # starting_cash ist für den Test nicht kritisch, wir prüfen nur die Struktur
        risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)
        
        # Erfolg - Details über die geladenen Limits ausgeben
        details = []
        if risk_limits.config.max_order_notional:
            details.append(f"max_order_notional: {risk_limits.config.max_order_notional}")
        if risk_limits.config.max_daily_loss_abs:
            details.append(f"max_daily_loss_abs: {risk_limits.config.max_daily_loss_abs}")
        if risk_limits.config.max_daily_loss_pct:
            details.append(f"max_daily_loss_pct: {risk_limits.config.max_daily_loss_pct}")
        
        return CheckResult(
            name="Live-Risk-Config",
            passed=True,
            message="Live-Risk-Config erfolgreich geladen",
            details=details,
        )
        
    except ImportError as e:
        return CheckResult(
            name="Live-Risk-Config",
            passed=False,
            message=f"ERROR: Live-Risk-Modul nicht importierbar: {e}",
            details=[
                "Das Modul src.live.risk_limits konnte nicht geladen werden.",
                "Möglicherweise fehlen Abhängigkeiten oder es gibt einen Import-Fehler.",
            ],
        )
    except TypeError as e:
        return CheckResult(
            name="Live-Risk-Config",
            passed=False,
            message=f"ERROR: Live-Risk-Config ungültige Typen: {e}",
            details=[
                "Die Werte in [live_risk] haben ungültige Typen.",
                "Prüfen Sie, ob alle Werte korrekte Zahlen sind.",
                "Siehe docs/SAFETY_POLICY_TESTNET_AND_LIVE.md für Details.",
            ],
        )
    except ValueError as e:
        return CheckResult(
            name="Live-Risk-Config",
            passed=False,
            message=f"ERROR: Live-Risk-Config ungültige Werte: {e}",
            details=[
                "Die Werte in [live_risk] sind ungültig.",
                "Prüfen Sie die Grenzwerte und Einheiten.",
                "Siehe docs/SAFETY_POLICY_TESTNET_AND_LIVE.md für Details.",
            ],
        )
    except Exception as e:
        return CheckResult(
            name="Live-Risk-Config",
            passed=False,
            message=f"ERROR: Live-Risk-Config konnte nicht geladen werden: {e}",
            details=[
                "Ein unerwarteter Fehler beim Laden der Live-Risk-Konfiguration.",
                "Siehe docs/SAFETY_POLICY_TESTNET_AND_LIVE.md für Details.",
                f"Fehlertyp: {type(e).__name__}",
            ],
        )


def check_documentation_exists() -> List[WarningResult]:
    """
    Soft-Check: Prüft, ob wichtige Dokumentationsdateien existieren und nicht leer sind.
    
    Gibt Warnungen zurück, blockiert aber nicht die Readiness.
    Dies ist Teil der Gatekeeper-Philosophie: Doku ist Teil der Produktionsreife.
    
    Returns:
        Liste von WarningResult-Objekten für fehlende/leere Dateien
    """
    warnings: List[WarningResult] = []
    
    # Zu prüfende Dokumentationsdateien
    doc_files = [
        ("LIVE_DEPLOYMENT_PLAYBOOK.md", "Deployment-Stufenplan und Verfahren"),
        ("LIVE_OPERATIONAL_RUNBOOKS.md", "Ops-Runbooks für Testnet/Live"),
        ("LIVE_READINESS_CHECKLISTS.md", "Readiness-Checklisten für Stufen-Übergänge"),
    ]
    
    docs_dir = ROOT_DIR / "docs"
    
    for filename, description in doc_files:
        file_path = docs_dir / filename
        
        if not file_path.exists():
            warnings.append(WarningResult(
                name=f"Doku: {filename}",
                message=f"WARN: {filename} fehlt – {description}",
                details=[
                    f"Erwartet unter: {file_path}",
                    "Diese Dokumentation ist Teil der Produktionsreife.",
                ],
            ))
        elif file_path.stat().st_size == 0:
            warnings.append(WarningResult(
                name=f"Doku: {filename}",
                message=f"WARN: {filename} ist leer – {description}",
                details=[
                    f"Datei existiert, aber hat 0 Bytes.",
                    "Bitte Inhalt hinzufügen.",
                ],
            ))
        elif file_path.stat().st_size < 100:
            # Sehr kurze Dateien sind verdächtig (weniger als 100 Bytes)
            warnings.append(WarningResult(
                name=f"Doku: {filename}",
                message=f"WARN: {filename} ist sehr kurz ({file_path.stat().st_size} Bytes)",
                details=[
                    "Die Datei scheint unvollständig zu sein.",
                    "Bitte Inhalt prüfen und vervollständigen.",
                ],
            ))
    
    return warnings


# =============================================================================
# Main Check Runner
# =============================================================================


def run_readiness_checks(
    stage: str,
    config_path: Path,
    run_tests: bool = False,
) -> ReadinessReport:
    """
    Führt alle Readiness-Checks für eine Stufe aus.
    
    Args:
        stage: "shadow", "testnet", oder "live"
        config_path: Pfad zur Config-Datei
        run_tests: Ob Baseline-Tests ausgeführt werden sollen
    
    Returns:
        ReadinessReport mit allen Check-Ergebnissen und Warnungen
    """
    checks: List[CheckResult] = []
    warnings: List[WarningResult] = []
    
    # 1. Config existiert?
    checks.append(check_config_exists(config_path))
    
    # 2. Config gültig?
    config_result = check_config_valid(config_path)
    checks.append(config_result)
    
    # Wenn Config ungültig, können weitere Checks nicht laufen
    if not config_result.passed:
        return ReadinessReport(stage=stage, checks=checks, warnings=warnings)
    
    cfg = load_config(config_path)
    
    # 3. Environment-Mode
    checks.append(check_environment_mode(cfg, stage))
    
    # 4. Risk-Limits (einfacher Check)
    checks.append(check_risk_limits(cfg))
    
    # 5. Live-Risk-Config ladbar? (Hard-Check für testnet/live)
    checks.append(check_live_risk_config_loadable(cfg, stage))
    
    # 6. Stage-spezifische Checks
    if stage == "shadow":
        checks.append(check_shadow_config(cfg))
    
    # 7. Exchange-Config (für alle Stufen)
    checks.append(check_exchange_config(cfg, stage))
    
    # 8. API-Credentials (nur Testnet/Live)
    if stage in ("testnet", "live"):
        checks.append(check_api_credentials(stage))
    
    # 9. Baseline-Tests (optional)
    checks.append(check_tests(run_tests))
    
    # 10. Soft-Checks: Dokumentation (Warnungen, kein Blocker)
    warnings.extend(check_documentation_exists())
    
    return ReadinessReport(stage=stage, checks=checks, warnings=warnings)


# =============================================================================
# CLI
# =============================================================================


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Live-Readiness-Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Stufen:
  shadow   - Shadow-Execution (Dry-Run, keine API)
  testnet  - Testnet mit DummyClient oder Testnet-API
  live     - Echtes Live-Trading (ACHTUNG: nicht implementiert!)

Beispiele:
  python scripts/check_live_readiness.py --stage shadow
  python scripts/check_live_readiness.py --stage testnet --verbose
  python scripts/check_live_readiness.py --stage testnet --run-tests
        """,
    )
    
    parser.add_argument(
        "--stage",
        choices=["shadow", "testnet", "live"],
        default="shadow",
        help="Zu prüfende Stufe (Default: shadow)",
    )
    
    parser.add_argument(
        "--config",
        dest="config_path",
        default=None,
        help="Pfad zur Config-Datei (Default: config/config.toml oder PEAK_TRADE_CONFIG_PATH)",
    )
    
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Baseline-Tests ausführen (pytest -q --tb=no)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe mit Details",
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Nur Ergebnis (PASSED/FAILED) ausgeben",
    )
    
    return parser.parse_args(argv)


def print_report(report: ReadinessReport, verbose: bool, quiet: bool) -> None:
    """Gibt den Report aus."""
    
    if quiet:
        # Nur Ergebnis
        if report.all_passed:
            print("PASSED")
        else:
            print("FAILED")
        return
    
    # Header
    print()
    print("=" * 70)
    print(f"  Peak_Trade Readiness-Check: {report.stage.upper()}")
    print("=" * 70)
    print()
    
    # Checks
    for check in report.checks:
        icon = "✅" if check.passed else "❌"
        print(f"  {icon} {check.name}: {check.message}")
        
        if verbose and check.details:
            for detail in check.details:
                print(f"      └─ {detail}")
    
    # Warnungen (Soft-Checks)
    if report.warnings:
        print()
        print("  ─── Warnungen (Soft-Checks, kein Blocker) ───")
        for warning in report.warnings:
            print(f"  ⚠️  {warning.name}: {warning.message}")
            if verbose and warning.details:
                for detail in warning.details:
                    print(f"      └─ {detail}")
    
    # Summary
    print()
    print("-" * 70)
    if report.all_passed:
        status_msg = f"  ✅ Readiness-Check BESTANDEN ({report.passed_count}/{len(report.checks)} Checks)"
        if report.warning_count > 0:
            status_msg += f" – {report.warning_count} Warnung(en)"
        print(status_msg)
    else:
        print(f"  ❌ Readiness-Check FEHLGESCHLAGEN ({report.failed_count} von {len(report.checks)} Checks fehlgeschlagen)")
    print()


def main(argv: Optional[List[str]] = None) -> int:
    """
    Hauptfunktion.
    
    Returns:
        Exit-Code: 0 = alle Checks bestanden, 1 = mindestens ein Check fehlgeschlagen
    """
    args = parse_args(argv)
    
    # Config-Pfad bestimmen
    if args.config_path:
        config_path = Path(args.config_path)
    else:
        # Default: config/config.toml im Projekt-Root
        config_path = ROOT_DIR / "config" / "config.toml"
    
    # Checks ausführen
    report = run_readiness_checks(
        stage=args.stage,
        config_path=config_path,
        run_tests=args.run_tests,
    )
    
    # Report ausgeben
    print_report(report, verbose=args.verbose, quiet=args.quiet)
    
    # Exit-Code
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


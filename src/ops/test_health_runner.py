#!/usr/bin/env python3
"""
Peak_Trade Test Health Runner (v1)
===================================

Automatisiertes Test-Health-Check-System mit:
  - TOML-basierte Profile-Konfiguration
  - Gewichteter Health-Score (0-100)
  - JSON/Markdown/HTML Reports
  - CLI-Integration
  - v1: Strategy-Coverage-Checks
  - v1: Strategy-Switch Sanity Check (Governance)
  - v1: Erweiterte Slack-Notifications

Autor: Peak_Trade Ops Team
Stand: Dezember 2024
Version: v1
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

# Python 3.11+: tomllib ist built-in
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError(
            "Python <3.11 benötigt 'tomli' package: pip install tomli"
        )


# ============================================================================
# Type Definitions
# ============================================================================

HealthStatus = Literal["PASS", "FAIL", "SKIPPED"]
TriggerViolationSeverity = Literal["info", "warning", "error"]


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TestHealthTriggers:
    """
    Trigger-Bedingungen für ein Test-Health-Profil.
    
    Attributes:
        min_total_runs: Mindestanzahl an Runs im Zeitfenster
        max_fail_rate: Maximale Fail-Rate (0.0 - 1.0)
        max_consecutive_failures: Max. aufeinanderfolgende Failures
        max_hours_since_last_run: Max. Stunden seit letztem Run (None = deaktiviert)
        require_critical_green: Ob kritische Testgruppen grün sein müssen
    """

    min_total_runs: int = 0
    max_fail_rate: float = 1.0
    max_consecutive_failures: int = 999999
    max_hours_since_last_run: Optional[int] = None
    require_critical_green: bool = False


@dataclass
class TestHealthStats:
    """
    Statistiken über Test-Health-Runs (für Trigger-Evaluierung).
    
    Diese Daten kommen typischerweise aus der Historie oder dem aktuellen Run.
    
    Attributes:
        total_runs: Anzahl Runs im Zeitfenster
        failed_runs: Anzahl fehlgeschlagener Runs
        max_consecutive_failures: Längste Serie aufeinanderfolgender Failures
        hours_since_last_run: Stunden seit letztem Run (None wenn erster Run)
        all_critical_groups_green: Ob alle kritischen Testgruppen grün sind
    """

    total_runs: int
    failed_runs: int
    max_consecutive_failures: int
    hours_since_last_run: Optional[float]
    all_critical_groups_green: bool


@dataclass
class TriggerViolation:
    """
    Eine Verletzung einer Trigger-Bedingung.
    
    Attributes:
        severity: Schweregrad ("info", "warning", "error")
        trigger_name: Name des Triggers (z.B. "max_fail_rate")
        message: Menschenlesbare Beschreibung
        actual_value: Tatsächlicher Wert
        threshold_value: Schwellenwert
    """

    severity: TriggerViolationSeverity
    trigger_name: str
    message: str
    actual_value: Any
    threshold_value: Any


# ============================================================================
# v1: Strategy-Coverage Data Classes
# ============================================================================


@dataclass
class StrategyCoverageConfig:
    """
    Konfiguration für Strategy-Coverage-Checks (v1).
    
    Attributes:
        enabled: Ob Strategy-Coverage-Checks aktiviert sind
        window_days: Zeitraum für Run-Zählung
        min_backtests_per_strategy: Mindestanzahl Backtests pro Strategie
        min_paper_runs_per_strategy: Mindestanzahl Paper-Runs pro Strategie
        link_to_strategy_switch_allowed: Nur Strategien aus allowed prüfen
        runs_directory: Verzeichnis mit Experiment-Runs
    """
    
    enabled: bool = True
    window_days: int = 7
    min_backtests_per_strategy: int = 3
    min_paper_runs_per_strategy: int = 1
    link_to_strategy_switch_allowed: bool = True
    runs_directory: str = "reports/experiments"


@dataclass
class StrategyCoverageStats:
    """
    Coverage-Statistiken für eine einzelne Strategie (v1).
    
    Attributes:
        strategy_id: ID der Strategie
        n_backtests: Anzahl Backtests im Zeitfenster
        n_paper_runs: Anzahl Paper-Runs im Zeitfenster
        violations: Liste von Verletzungen
    """
    
    strategy_id: str
    n_backtests: int
    n_paper_runs: int
    violations: list[str] = field(default_factory=list)


@dataclass
class StrategyCoverageResult:
    """
    Gesamtergebnis der Strategy-Coverage-Prüfung (v1).
    
    Attributes:
        enabled: Ob Coverage-Check aktiviert war
        strategies_checked: Anzahl geprüfter Strategien
        strategies_with_violations: Anzahl Strategien mit Violations
        coverage_stats: Liste von StrategyCoverageStats
        all_violations: Alle Violations aggregiert
        is_healthy: True wenn keine Violations
    """
    
    enabled: bool
    strategies_checked: int
    strategies_with_violations: int
    coverage_stats: list[StrategyCoverageStats]
    all_violations: list[str]
    is_healthy: bool


# ============================================================================
# v1: Switch-Sanity Data Classes
# ============================================================================


@dataclass
class SwitchSanityConfig:
    """
    Konfiguration für Strategy-Switch Sanity Check (v1).
    
    Attributes:
        enabled: Ob Sanity-Check aktiviert ist
        config_path: Pfad zur Live-Config
        section_path: TOML-Pfad für strategy_switch Sektion
        allow_r_and_d_in_allowed: Ob R&D-Strategien in allowed erlaubt sind
        require_active_in_allowed: active_strategy_id muss in allowed sein
        require_non_empty_allowed: allowed darf nicht leer sein
        r_and_d_strategy_keys: Liste von R&D-Strategie-Keys
    """
    
    enabled: bool = True
    config_path: str = "config/config.toml"
    section_path: str = "live_profile.strategy_switch"
    allow_r_and_d_in_allowed: bool = False
    require_active_in_allowed: bool = True
    require_non_empty_allowed: bool = True
    r_and_d_strategy_keys: list[str] = field(default_factory=lambda: [
        "armstrong_cycle",
        "el_karoui_vol_model",
        "ehlers_cycle_filter",
        "meta_labeling",
        "bouchaud_microstructure",
        "vol_regime_overlay",
    ])


@dataclass
class SwitchSanityResult:
    """
    Ergebnis des Strategy-Switch Sanity Checks (v1).
    
    Attributes:
        enabled: Ob Check aktiviert war
        is_ok: True wenn keine Violations
        violations: Liste von Violation-Beschreibungen
        active_strategy_id: Aktuell aktive Strategie-ID
        allowed: Liste der erlaubten Strategien
        config_path: Verwendeter Config-Pfad
    """
    
    enabled: bool
    is_ok: bool
    violations: list[str]
    active_strategy_id: str
    allowed: list[str]
    config_path: str


@dataclass
class TestCheckConfig:
    """Konfiguration eines einzelnen Test-Checks."""

    id: str
    name: str
    cmd: str
    weight: int
    category: str


@dataclass
class TestCheckResult:
    """Ergebnis eines einzelnen Test-Checks."""

    id: str
    name: str
    category: str
    cmd: str
    status: HealthStatus
    weight: int
    started_at: dt.datetime
    finished_at: dt.datetime
    duration_seconds: float
    return_code: Optional[int] = None
    error_message: Optional[str] = None
    stdout: Optional[str] = None  # P2: Stdout-Capture
    stderr: Optional[str] = None  # P2: Stderr-Capture


@dataclass
class PortfolioPsychology:
    """
    Psychologie-Annotation für Portfolio-Profile (v0).
    
    Attributes:
        level: Psychologisches Risikoprofil ("CALM", "MEDIUM", "SPICY")
        notes: Liste von kurzen Hinweisen/Warnungen
        max_drawdown_pct: Verwendeter Max-Drawdown
        total_return_pct: Verwendeter Return
        trades_count: Verwendete Trade-Anzahl
    """
    
    level: str  # "CALM" | "MEDIUM" | "SPICY"
    notes: list[str]
    max_drawdown_pct: Optional[float] = None
    total_return_pct: Optional[float] = None
    trades_count: Optional[int] = None
    
    @property
    def level_emoji(self) -> str:
        """Gibt Emoji für das Level zurück."""
        return {"CALM": "🧘", "MEDIUM": "⚠️", "SPICY": "🔥"}.get(self.level, "❓")


@dataclass
class TestHealthSummary:
    """Aggregiertes Summary aller Test-Checks eines Profils."""

    profile_name: str
    started_at: dt.datetime
    finished_at: dt.datetime
    checks: list[TestCheckResult]
    health_score: float  # 0.0 - 100.0
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    total_weight: int
    passed_weight: int
    trigger_violations: list[TriggerViolation] = None  # Trigger-Violations
    # v1: Strategy-Coverage und Switch-Sanity
    strategy_coverage: Optional[StrategyCoverageResult] = None
    switch_sanity: Optional[SwitchSanityResult] = None
    # v1.1: Portfolio-Psychologie (nur für portfolio-Profile)
    psychology: Optional[PortfolioPsychology] = None
    
    def __post_init__(self):
        """Initialisiert trigger_violations falls None."""
        if self.trigger_violations is None:
            self.trigger_violations = []
    
    def has_trigger_violations(self) -> bool:
        """Prüft ob Trigger-Violations existieren."""
        return len(self.trigger_violations) > 0
    
    def has_critical_violations(self) -> bool:
        """Prüft ob es kritische (error) Violations gibt."""
        return any(v.severity == "error" for v in self.trigger_violations)
    
    def has_strategy_coverage_violations(self) -> bool:
        """Prüft ob Strategy-Coverage-Violations existieren (v1)."""
        if self.strategy_coverage is None:
            return False
        return not self.strategy_coverage.is_healthy
    
    def has_switch_sanity_violations(self) -> bool:
        """Prüft ob Switch-Sanity-Violations existieren (v1)."""
        if self.switch_sanity is None:
            return False
        return not self.switch_sanity.is_ok
    
    def has_any_violations(self) -> bool:
        """Prüft ob irgendwelche Violations existieren (v1)."""
        return (
            self.has_trigger_violations()
            or self.has_strategy_coverage_violations()
            or self.has_switch_sanity_violations()
        )
    
    def has_psychology(self) -> bool:
        """Prüft ob Psychologie-Annotation vorhanden ist (v1.1)."""
        return self.psychology is not None


# ============================================================================
# Core Functions
# ============================================================================


def load_test_health_profile(
    config_path: Path, profile_name: str
) -> tuple[list[TestCheckConfig], TestHealthTriggers]:
    """
    Lädt ein Test-Health-Profil aus der TOML-Konfiguration.

    Parameters
    ----------
    config_path : Path
        Pfad zur test_health_profiles.toml
    profile_name : str
        Name des zu ladenden Profils (z.B. "weekly_core")

    Returns
    -------
    tuple[list[TestCheckConfig], TestHealthTriggers]
        (Liste der Check-Konfigurationen, Trigger-Config)

    Raises
    ------
    FileNotFoundError
        Wenn config_path nicht existiert
    ValueError
        Wenn Profil nicht gefunden oder ungültig konfiguriert
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config nicht gefunden: {config_path}")

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Profil finden
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        available = list(profiles.keys())
        raise ValueError(
            f"Profil '{profile_name}' nicht gefunden. "
            f"Verfügbar: {', '.join(available)}"
        )

    profile = profiles[profile_name]

    # Checks extrahieren
    checks_raw = profile.get("checks", [])
    if not checks_raw:
        raise ValueError(f"Profil '{profile_name}' hat keine Checks definiert.")

    checks = []
    for i, check_dict in enumerate(checks_raw):
        # Validierung
        for required_field in ["id", "name", "cmd", "weight", "category"]:
            if required_field not in check_dict:
                raise ValueError(
                    f"Check #{i} in Profil '{profile_name}' fehlt Feld '{required_field}'"
                )

        check_id = check_dict["id"]
        name = check_dict["name"]
        cmd = check_dict["cmd"]
        weight = check_dict["weight"]
        category = check_dict["category"]

        # Zusätzliche Validierungen
        if not isinstance(check_id, str) or not check_id.strip():
            raise ValueError(f"Check #{i}: 'id' muss nicht-leerer String sein.")
        if not isinstance(cmd, str) or not cmd.strip():
            raise ValueError(f"Check #{i}: 'cmd' muss nicht-leerer String sein.")
        if not isinstance(weight, int) or weight <= 0:
            raise ValueError(f"Check #{i}: 'weight' muss positiver Integer sein.")

        checks.append(
            TestCheckConfig(
                id=check_id,
                name=name,
                cmd=cmd,
                weight=weight,
                category=category,
            )
        )
    
    # Triggers laden (optional)
    triggers_dict = profile.get("triggers", {})
    triggers = TestHealthTriggers(
        min_total_runs=triggers_dict.get("min_total_runs", 0),
        max_fail_rate=triggers_dict.get("max_fail_rate", 1.0),
        max_consecutive_failures=triggers_dict.get("max_consecutive_failures", 999999),
        max_hours_since_last_run=triggers_dict.get("max_hours_since_last_run"),
        require_critical_green=triggers_dict.get("require_critical_green", False),
    )

    return checks, triggers


def run_single_check(check: TestCheckConfig) -> TestCheckResult:
    """
    Führt einen einzelnen Test-Check aus.

    Parameters
    ----------
    check : TestCheckConfig
        Check-Konfiguration

    Returns
    -------
    TestCheckResult
        Ergebnis mit Status, Dauer, Returncode, Stdout/Stderr (P2)
    """
    started_at = dt.datetime.utcnow()
    status: HealthStatus = "FAIL"
    return_code: Optional[int] = None
    error_message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    try:
        result = subprocess.run(
            check.cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 Minuten Timeout
        )
        return_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr

        if return_code == 0:
            status = "PASS"
        else:
            status = "FAIL"
            error_message = (
                f"Command exited with code {return_code}.\n"
                f"STDOUT (last 500 chars):\n{result.stdout[-500:]}\n"
                f"STDERR (last 500 chars):\n{result.stderr[-500:]}"
            )

    except subprocess.TimeoutExpired as e:
        status = "FAIL"
        error_message = f"Command timeout nach 600s: {check.cmd}"
        # Versuche partial output zu erfassen
        if hasattr(e, 'stdout') and e.stdout:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
        if hasattr(e, 'stderr') and e.stderr:
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr

    except Exception as e:
        status = "FAIL"
        error_message = f"Fehler beim Ausführen von '{check.cmd}': {e}"

    finished_at = dt.datetime.utcnow()
    duration_seconds = (finished_at - started_at).total_seconds()

    return TestCheckResult(
        id=check.id,
        name=check.name,
        category=check.category,
        cmd=check.cmd,
        status=status,
        weight=check.weight,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        return_code=return_code,
        error_message=error_message,
        stdout=stdout,
        stderr=stderr,
    )


def aggregate_health(
    profile_name: str, results: list[TestCheckResult]
) -> TestHealthSummary:
    """
    Aggregiert Check-Resultate zu einem Health-Summary.

    Parameters
    ----------
    profile_name : str
        Name des Profils
    results : list[TestCheckResult]
        Liste der Check-Resultate

    Returns
    -------
    TestHealthSummary
        Summary mit Health-Score (0-100)
    """
    if not results:
        return TestHealthSummary(
            profile_name=profile_name,
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=0.0,
            passed_checks=0,
            failed_checks=0,
            skipped_checks=0,
            total_weight=0,
            passed_weight=0,
        )

    passed_checks = sum(1 for r in results if r.status == "PASS")
    failed_checks = sum(1 for r in results if r.status == "FAIL")
    skipped_checks = sum(1 for r in results if r.status == "SKIPPED")

    total_weight = sum(r.weight for r in results)
    passed_weight = sum(r.weight for r in results if r.status == "PASS")

    # Health-Score: Gewichteter Anteil der erfolgreich bestandenen Checks
    if total_weight > 0:
        health_score = (passed_weight / total_weight) * 100.0
    else:
        health_score = 0.0

    # Zeitfenster bestimmen (nur nicht-None Werte)
    start_times = [r.started_at for r in results if r.started_at is not None]
    finish_times = [r.finished_at for r in results if r.finished_at is not None]
    started_at = min(start_times) if start_times else dt.datetime.utcnow()
    finished_at = max(finish_times) if finish_times else dt.datetime.utcnow()

    return TestHealthSummary(
        profile_name=profile_name,
        started_at=started_at,
        finished_at=finished_at,
        checks=results,
        health_score=health_score,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        skipped_checks=skipped_checks,
        total_weight=total_weight,
        passed_weight=passed_weight,
    )


def evaluate_triggers(
    triggers: TestHealthTriggers, stats: TestHealthStats
) -> list[TriggerViolation]:
    """
    Evaluiert Trigger-Bedingungen und gibt Violations zurück.
    
    Parameters
    ----------
    triggers : TestHealthTriggers
        Trigger-Config für das Profil
    stats : TestHealthStats
        Statistiken über Test-Runs
    
    Returns
    -------
    list[TriggerViolation]
        Liste von Violations (leer = alles ok)
    
    Examples
    --------
    >>> triggers = TestHealthTriggers(min_total_runs=5, max_fail_rate=0.2)
    >>> stats = TestHealthStats(total_runs=3, failed_runs=1, ...)
    >>> violations = evaluate_triggers(triggers, stats)
    >>> assert len(violations) > 0  # min_total_runs nicht erfüllt
    """
    violations: list[TriggerViolation] = []
    
    # Check 1: min_total_runs
    if stats.total_runs < triggers.min_total_runs:
        violations.append(
            TriggerViolation(
                severity="warning",
                trigger_name="min_total_runs",
                message=f"Zu wenige Runs im Zeitfenster: {stats.total_runs} < {triggers.min_total_runs}",
                actual_value=stats.total_runs,
                threshold_value=triggers.min_total_runs,
            )
        )
    
    # Check 2: max_fail_rate
    if stats.total_runs > 0:
        fail_rate = stats.failed_runs / stats.total_runs
        if fail_rate > triggers.max_fail_rate:
            violations.append(
                TriggerViolation(
                    severity="error",
                    trigger_name="max_fail_rate",
                    message=(
                        f"Fail-Rate zu hoch: {fail_rate:.2%} > {triggers.max_fail_rate:.2%} "
                        f"({stats.failed_runs}/{stats.total_runs} Runs failed)"
                    ),
                    actual_value=fail_rate,
                    threshold_value=triggers.max_fail_rate,
                )
            )
    
    # Check 3: max_consecutive_failures
    if stats.max_consecutive_failures > triggers.max_consecutive_failures:
        violations.append(
            TriggerViolation(
                severity="error",
                trigger_name="max_consecutive_failures",
                message=(
                    f"Zu viele Failures in Folge: "
                    f"{stats.max_consecutive_failures} > {triggers.max_consecutive_failures}"
                ),
                actual_value=stats.max_consecutive_failures,
                threshold_value=triggers.max_consecutive_failures,
            )
        )
    
    # Check 4: max_hours_since_last_run
    if (
        triggers.max_hours_since_last_run is not None
        and stats.hours_since_last_run is not None
    ):
        if stats.hours_since_last_run > triggers.max_hours_since_last_run:
            violations.append(
                TriggerViolation(
                    severity="warning",
                    trigger_name="max_hours_since_last_run",
                    message=(
                        f"Zu lange kein Run: "
                        f"{stats.hours_since_last_run:.1f}h > {triggers.max_hours_since_last_run}h"
                    ),
                    actual_value=stats.hours_since_last_run,
                    threshold_value=triggers.max_hours_since_last_run,
                )
            )
    
    # Check 5: require_critical_green
    if triggers.require_critical_green and not stats.all_critical_groups_green:
        violations.append(
            TriggerViolation(
                severity="error",
                trigger_name="require_critical_green",
                message="Kritische Testgruppen sind nicht grün",
                actual_value=False,
                threshold_value=True,
            )
        )
    
    return violations


# ============================================================================
# v1: Strategy-Coverage Functions
# ============================================================================


def load_strategy_coverage_config(config_path: Path) -> StrategyCoverageConfig:
    """
    Lädt die Strategy-Coverage-Konfiguration aus der TOML-Datei (v1).
    
    Parameters
    ----------
    config_path : Path
        Pfad zur test_health_profiles.toml
    
    Returns
    -------
    StrategyCoverageConfig
        Coverage-Konfiguration
    """
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    coverage_cfg = config.get("strategy_coverage", {})
    
    return StrategyCoverageConfig(
        enabled=coverage_cfg.get("enabled", True),
        window_days=coverage_cfg.get("window_days", 7),
        min_backtests_per_strategy=coverage_cfg.get("min_backtests_per_strategy", 3),
        min_paper_runs_per_strategy=coverage_cfg.get("min_paper_runs_per_strategy", 1),
        link_to_strategy_switch_allowed=coverage_cfg.get("link_to_strategy_switch_allowed", True),
        runs_directory=coverage_cfg.get("runs_directory", "reports/experiments"),
    )


def _load_allowed_strategies(config_path: str, section_path: str) -> list[str]:
    """
    Lädt die Liste der erlaubten Strategien aus der Live-Config.
    
    Parameters
    ----------
    config_path : str
        Pfad zur Config-Datei
    section_path : str
        TOML-Pfad zur strategy_switch Sektion
    
    Returns
    -------
    list[str]
        Liste der erlaubten Strategie-IDs
    """
    path = Path(config_path)
    if not path.exists():
        return []
    
    with open(path, "rb") as f:
        config = tomllib.load(f)
    
    # Navigiere durch den section_path
    parts = section_path.split(".")
    current = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return []
    
    if isinstance(current, dict):
        return current.get("allowed", [])
    
    return []


def _count_experiment_runs(
    runs_directory: Path,
    strategy_id: str,
    window_days: int,
    now: dt.datetime,
) -> tuple[int, int]:
    """
    Zählt Backtests und Paper-Runs für eine Strategie im Zeitfenster.
    
    Parameters
    ----------
    runs_directory : Path
        Verzeichnis mit Experiment-Runs
    strategy_id : str
        ID der Strategie
    window_days : int
        Zeitfenster in Tagen
    now : dt.datetime
        Aktueller Zeitpunkt
    
    Returns
    -------
    tuple[int, int]
        (n_backtests, n_paper_runs)
    """
    n_backtests = 0
    n_paper_runs = 0
    
    if not runs_directory.exists():
        return n_backtests, n_paper_runs
    
    cutoff = now - dt.timedelta(days=window_days)
    
    # Suche nach JSON-Dateien (rekursiv, aber dedupliziert)
    seen_files: set[Path] = set()
    
    for run_file in runs_directory.rglob("*.json"):
        # Deduplizierung
        abs_path = run_file.resolve()
        if abs_path in seen_files:
            continue
        seen_files.add(abs_path)
        
        try:
            # Prüfe Modifikationszeit
            mtime = dt.datetime.fromtimestamp(run_file.stat().st_mtime)
            if mtime < cutoff:
                continue
            
            # Lade JSON und prüfe strategy_id und run_type
            with open(run_file, "r") as f:
                data = json.load(f)
            
            file_strategy_id = data.get("strategy_id") or data.get("strategy")
            run_type = data.get("run_type") or data.get("type", "")
            
            if file_strategy_id != strategy_id:
                continue
            
            if run_type.lower() in ("backtest", "offline_backtest", "backtest_run"):
                n_backtests += 1
            elif run_type.lower() in ("paper_trade", "paper", "paper_run", "shadow"):
                n_paper_runs += 1
                
        except (json.JSONDecodeError, OSError, KeyError):
            continue
    
    return n_backtests, n_paper_runs


def compute_strategy_coverage(
    config: StrategyCoverageConfig,
    strategy_ids: list[str],
    now: Optional[dt.datetime] = None,
) -> StrategyCoverageResult:
    """
    Berechnet Strategy-Coverage für alle gegebenen Strategien (v1).
    
    Parameters
    ----------
    config : StrategyCoverageConfig
        Coverage-Konfiguration
    strategy_ids : list[str]
        Liste der zu prüfenden Strategie-IDs
    now : Optional[dt.datetime]
        Aktueller Zeitpunkt (default: utcnow)
    
    Returns
    -------
    StrategyCoverageResult
        Coverage-Ergebnis mit Stats pro Strategie
    
    Examples
    --------
    >>> config = StrategyCoverageConfig(min_backtests_per_strategy=3)
    >>> result = compute_strategy_coverage(config, ["ma_crossover", "rsi_reversion"])
    >>> print(result.is_healthy)
    """
    if now is None:
        now = dt.datetime.utcnow()
    
    if not config.enabled:
        return StrategyCoverageResult(
            enabled=False,
            strategies_checked=0,
            strategies_with_violations=0,
            coverage_stats=[],
            all_violations=[],
            is_healthy=True,
        )
    
    runs_dir = Path(config.runs_directory)
    coverage_stats: list[StrategyCoverageStats] = []
    all_violations: list[str] = []
    
    for strategy_id in strategy_ids:
        n_backtests, n_paper_runs = _count_experiment_runs(
            runs_dir, strategy_id, config.window_days, now
        )
        
        violations: list[str] = []
        
        if n_backtests < config.min_backtests_per_strategy:
            msg = (
                f"Strategy '{strategy_id}': only {n_backtests}/{config.min_backtests_per_strategy} "
                f"backtests in last {config.window_days} days"
            )
            violations.append(msg)
            all_violations.append(msg)
        
        if n_paper_runs < config.min_paper_runs_per_strategy:
            msg = (
                f"Strategy '{strategy_id}': only {n_paper_runs}/{config.min_paper_runs_per_strategy} "
                f"paper runs in last {config.window_days} days"
            )
            violations.append(msg)
            all_violations.append(msg)
        
        coverage_stats.append(
            StrategyCoverageStats(
                strategy_id=strategy_id,
                n_backtests=n_backtests,
                n_paper_runs=n_paper_runs,
                violations=violations,
            )
        )
    
    strategies_with_violations = sum(1 for s in coverage_stats if s.violations)
    
    return StrategyCoverageResult(
        enabled=True,
        strategies_checked=len(strategy_ids),
        strategies_with_violations=strategies_with_violations,
        coverage_stats=coverage_stats,
        all_violations=all_violations,
        is_healthy=(len(all_violations) == 0),
    )


# ============================================================================
# v1: Switch-Sanity Functions
# ============================================================================


def load_switch_sanity_config(config_path: Path) -> SwitchSanityConfig:
    """
    Lädt die Switch-Sanity-Konfiguration aus der TOML-Datei (v1).
    
    Parameters
    ----------
    config_path : Path
        Pfad zur test_health_profiles.toml
    
    Returns
    -------
    SwitchSanityConfig
        Sanity-Check-Konfiguration
    """
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    sanity_cfg = config.get("switch_sanity", {})
    
    return SwitchSanityConfig(
        enabled=sanity_cfg.get("enabled", True),
        config_path=sanity_cfg.get("config_path", "config/config.toml"),
        section_path=sanity_cfg.get("section_path", "live_profile.strategy_switch"),
        allow_r_and_d_in_allowed=sanity_cfg.get("allow_r_and_d_in_allowed", False),
        require_active_in_allowed=sanity_cfg.get("require_active_in_allowed", True),
        require_non_empty_allowed=sanity_cfg.get("require_non_empty_allowed", True),
        r_and_d_strategy_keys=sanity_cfg.get("r_and_d_strategy_keys", [
            "armstrong_cycle",
            "el_karoui_vol_model",
            "ehlers_cycle_filter",
            "meta_labeling",
            "bouchaud_microstructure",
            "vol_regime_overlay",
        ]),
    )


def run_switch_sanity_check(cfg: SwitchSanityConfig) -> SwitchSanityResult:
    """
    Führt den Strategy-Switch Sanity Check durch (v1).
    
    Prüft die [live_profile.strategy_switch]-Sektion der Config.
    Führt KEIN Umschalten durch - nur statische Validierung!
    
    Parameters
    ----------
    cfg : SwitchSanityConfig
        Sanity-Check-Konfiguration
    
    Returns
    -------
    SwitchSanityResult
        Ergebnis mit Violations und aktiver Strategie
    
    Examples
    --------
    >>> config = SwitchSanityConfig(config_path="config/config.toml")
    >>> result = run_switch_sanity_check(config)
    >>> print(result.is_ok)
    """
    if not cfg.enabled:
        return SwitchSanityResult(
            enabled=False,
            is_ok=True,
            violations=[],
            active_strategy_id="",
            allowed=[],
            config_path=cfg.config_path,
        )
    
    violations: list[str] = []
    active_strategy_id = ""
    allowed: list[str] = []
    
    # 1. Config laden
    config_path = Path(cfg.config_path)
    if not config_path.exists():
        return SwitchSanityResult(
            enabled=True,
            is_ok=False,
            violations=[f"Config file not found: {cfg.config_path}"],
            active_strategy_id="",
            allowed=[],
            config_path=cfg.config_path,
        )
    
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        return SwitchSanityResult(
            enabled=True,
            is_ok=False,
            violations=[f"Failed to parse config: {e}"],
            active_strategy_id="",
            allowed=[],
            config_path=cfg.config_path,
        )
    
    # 2. Navigiere zum section_path
    parts = cfg.section_path.split(".")
    current = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return SwitchSanityResult(
                enabled=True,
                is_ok=False,
                violations=[f"Section '{cfg.section_path}' not found in config"],
                active_strategy_id="",
                allowed=[],
                config_path=cfg.config_path,
            )
    
    if not isinstance(current, dict):
        return SwitchSanityResult(
            enabled=True,
            is_ok=False,
            violations=[f"Section '{cfg.section_path}' is not a table"],
            active_strategy_id="",
            allowed=[],
            config_path=cfg.config_path,
        )
    
    # 3. Werte extrahieren
    active_strategy_id = current.get("active_strategy_id", "")
    allowed = current.get("allowed", [])
    
    # 4. Checks durchführen
    
    # Check: require_non_empty_allowed
    if cfg.require_non_empty_allowed and not allowed:
        violations.append("allowed list must not be empty")
    
    # Check: require_active_in_allowed
    if cfg.require_active_in_allowed and active_strategy_id:
        if active_strategy_id not in allowed:
            violations.append(
                f"active_strategy_id '{active_strategy_id}' not in allowed list"
            )
    
    # Check: allow_r_and_d_in_allowed
    if not cfg.allow_r_and_d_in_allowed:
        for strategy_id in allowed:
            if strategy_id in cfg.r_and_d_strategy_keys:
                violations.append(
                    f"Strategy '{strategy_id}' is tier r_and_d but present in allowed list"
                )
    
    return SwitchSanityResult(
        enabled=True,
        is_ok=(len(violations) == 0),
        violations=violations,
        active_strategy_id=active_strategy_id,
        allowed=allowed,
        config_path=cfg.config_path,
    )


# ============================================================================
# Report Writers
# ============================================================================


def _datetime_to_iso(obj):
    """Helper: Konvertiert datetime zu ISO-String für JSON-Serialisierung."""
    if isinstance(obj, dt.datetime):
        return obj.isoformat()
    if isinstance(obj, TestCheckResult):
        d = asdict(obj)
        d["started_at"] = d["started_at"].isoformat() if d["started_at"] else None
        d["finished_at"] = d["finished_at"].isoformat() if d["finished_at"] else None
        return d
    if isinstance(obj, TestHealthSummary):
        d = asdict(obj)
        d["started_at"] = d["started_at"].isoformat() if d["started_at"] else None
        d["finished_at"] = d["finished_at"].isoformat() if d["finished_at"] else None
        d["checks"] = [_datetime_to_iso(c) for c in d["checks"]]
        return d
    return obj


def write_test_health_json(summary: TestHealthSummary, path: Path) -> None:
    """
    Schreibt TestHealthSummary als JSON-Datei.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary-Objekt
    path : Path
        Ausgabepfad für JSON
    """
    # Konvertiere Summary zu dict und dann datetime zu ISO-Strings
    def json_serial(obj):
        """JSON serializer für datetime-Objekte."""
        if isinstance(obj, dt.datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    data = asdict(summary)
    
    # P2: Truncate stdout/stderr in checks für kleinere JSON-Dateien
    MAX_OUTPUT_LEN = 5000  # 5k chars max
    for check in data.get("checks", []):
        if check.get("stdout") and len(check["stdout"]) > MAX_OUTPUT_LEN:
            check["stdout"] = check["stdout"][-MAX_OUTPUT_LEN:] + f"\n\n[truncated, showing last {MAX_OUTPUT_LEN} chars]"
        if check.get("stderr") and len(check["stderr"]) > MAX_OUTPUT_LEN:
            check["stderr"] = check["stderr"][-MAX_OUTPUT_LEN:] + f"\n\n[truncated, showing last {MAX_OUTPUT_LEN} chars]"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=json_serial)


def write_test_health_markdown(summary: TestHealthSummary, path: Path) -> None:
    """
    Schreibt TestHealthSummary als Markdown-Datei.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary-Objekt
    path : Path
        Ausgabepfad für Markdown
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ampel-Interpretation
    score = summary.health_score
    if score >= 80:
        ampel = "🟢 Grün (gesund)"
    elif score >= 50:
        ampel = "🟡 Gelb (teilweise gesund / genauer hinsehen)"
    else:
        ampel = "🔴 Rot (kritisch)"

    duration = (summary.finished_at - summary.started_at).total_seconds()

    md_lines = [
        f"# Test Health Report: {summary.profile_name}",
        "",
        f"**Health-Score**: {summary.health_score:.1f} / 100.0",
        f"**Ampel**: {ampel}",
        "",
        "## Übersicht",
        "",
        f"- **Profil**: `{summary.profile_name}`",
        f"- **Gestartet**: {summary.started_at.isoformat()}",
        f"- **Beendet**: {summary.finished_at.isoformat()}",
        f"- **Dauer**: {duration:.1f}s",
        "",
        f"- **Passed Checks**: {summary.passed_checks}",
        f"- **Failed Checks**: {summary.failed_checks}",
        f"- **Skipped Checks**: {summary.skipped_checks}",
        "",
        f"- **Passed Weight**: {summary.passed_weight} / {summary.total_weight}",
        "",
    ]
    
    # Trigger-Violations (falls vorhanden)
    if summary.has_trigger_violations():
        md_lines.extend([
            "## ⚠️ Trigger Violations",
            "",
            f"**Anzahl Violations**: {len(summary.trigger_violations)}",
            "",
        ])
        
        for v in summary.trigger_violations:
            severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(
                v.severity, "?"
            )
            md_lines.extend([
                f"### {severity_emoji} {v.trigger_name} [{v.severity.upper()}]",
                "",
                f"- **Message**: {v.message}",
                f"- **Actual**: {v.actual_value}",
                f"- **Threshold**: {v.threshold_value}",
                "",
            ])
    
    # v1: Strategy-Coverage (falls vorhanden)
    if summary.strategy_coverage and summary.strategy_coverage.enabled:
        coverage = summary.strategy_coverage
        coverage_status = "✅ Healthy" if coverage.is_healthy else "❌ Violations"
        
        md_lines.extend([
            "## 📊 Strategy Coverage (v1)",
            "",
            f"**Status**: {coverage_status}",
            f"**Strategies Checked**: {coverage.strategies_checked}",
            f"**With Violations**: {coverage.strategies_with_violations}",
            "",
        ])
        
        if coverage.coverage_stats:
            md_lines.extend([
                "| Strategy | Backtests | Paper Runs | Status |",
                "|----------|-----------|------------|--------|",
            ])
            
            for stat in coverage.coverage_stats:
                status = "✅" if not stat.violations else "❌"
                md_lines.append(
                    f"| `{stat.strategy_id}` | {stat.n_backtests} | {stat.n_paper_runs} | {status} |"
                )
            md_lines.append("")
        
        if coverage.all_violations:
            md_lines.extend([
                "### Coverage Violations",
                "",
            ])
            for violation in coverage.all_violations:
                md_lines.append(f"- ❌ {violation}")
            md_lines.append("")
    
    # v1: Switch-Sanity (falls vorhanden)
    if summary.switch_sanity and summary.switch_sanity.enabled:
        sanity = summary.switch_sanity
        sanity_status = "✅ OK" if sanity.is_ok else "❌ Violations"
        
        md_lines.extend([
            "## 🔒 Strategy-Switch Sanity (v1)",
            "",
            f"**Status**: {sanity_status}",
            f"**Active Strategy**: `{sanity.active_strategy_id}`",
            f"**Allowed Strategies**: {', '.join(f'`{s}`' for s in sanity.allowed) or '(none)'}",
            f"**Config Path**: `{sanity.config_path}`",
            "",
        ])
        
        if sanity.violations:
            md_lines.extend([
                "### Sanity Violations",
                "",
            ])
            for violation in sanity.violations:
                md_lines.append(f"- ❌ {violation}")
            md_lines.append("")
    
    # v1.1: Portfolio-Psychologie (falls vorhanden)
    if summary.has_psychology():
        psych = summary.psychology
        psych_emoji = psych.level_emoji
        
        md_lines.extend([
            f"## {psych_emoji} Portfolio-Psychologie (v1.1)",
            "",
            f"**Level**: {psych_emoji} **{psych.level}**",
            "",
        ])
        
        if psych.notes:
            md_lines.append("**Hinweise:**")
            md_lines.append("")
            for note in psych.notes:
                md_lines.append(f"- {note}")
            md_lines.append("")
        
        # Metriken-Kontext
        md_lines.append("*Basierend auf:*")
        if psych.max_drawdown_pct is not None:
            md_lines.append(f"- Max-Drawdown: {psych.max_drawdown_pct:.1f}%")
        if psych.total_return_pct is not None:
            md_lines.append(f"- Return: {psych.total_return_pct:+.1f}%")
        if psych.trades_count is not None:
            md_lines.append(f"- Trades: {psych.trades_count}")
        md_lines.append("")
    
    md_lines.extend([
        "## Check-Details",
        "",
        "| ID | Name | Category | Status | Duration (s) | Weight |",
        "|----|----- |----------|--------|--------------|--------|",
    ])

    for check in summary.checks:
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIPPED": "⏭️",
        }.get(check.status, "❓")

        md_lines.append(
            f"| `{check.id}` | {check.name} | {check.category} | "
            f"{status_icon} {check.status} | {check.duration_seconds:.2f} | {check.weight} |"
        )

    # P2: Failed Checks mit Stdout/Stderr
    failed_checks = [c for c in summary.checks if c.status == "FAIL"]
    if failed_checks:
        md_lines.extend(
            [
                "",
                "## ❌ Fehlgeschlagene Checks (Details)",
                "",
            ]
        )
        for check in failed_checks:
            md_lines.extend(
                [
                    f"### {check.name} (`{check.id}`)",
                    "",
                    f"- **Status**: ❌ FAIL",
                    f"- **Return Code**: {check.return_code}",
                    f"- **Duration**: {check.duration_seconds:.2f}s",
                    f"- **Command**: `{check.cmd}`",
                    "",
                ]
            )
            
            if check.error_message:
                md_lines.extend(
                    [
                        "**Error Message**:",
                        "```",
                        check.error_message,
                        "```",
                        "",
                    ]
                )
            
            # Stdout (truncate to 2000 chars)
            if check.stdout:
                stdout_display = check.stdout[-2000:] if len(check.stdout) > 2000 else check.stdout
                truncated_note = " (showing last 2000 chars)" if len(check.stdout) > 2000 else ""
                md_lines.extend(
                    [
                        f"**Stdout{truncated_note}**:",
                        "```",
                        stdout_display,
                        "```",
                        "",
                    ]
                )
            
            # Stderr (truncate to 2000 chars)
            if check.stderr:
                stderr_display = check.stderr[-2000:] if len(check.stderr) > 2000 else check.stderr
                truncated_note = " (showing last 2000 chars)" if len(check.stderr) > 2000 else ""
                md_lines.extend(
                    [
                        f"**Stderr{truncated_note}**:",
                        "```",
                        stderr_display,
                        "```",
                        "",
                    ]
                )

    md_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- **Grün (80-100)**: Alle kritischen Systeme laufen einwandfrei.",
            "- **Gelb (50-80)**: Teilweise Probleme, genauer hinsehen.",
            "- **Rot (<50)**: Kritische Probleme, sofortiges Handeln erforderlich.",
            "",
        ]
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def write_test_health_html(summary: TestHealthSummary, path: Path) -> None:
    """
    Schreibt TestHealthSummary als HTML-Datei.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary-Objekt
    path : Path
        Ausgabepfad für HTML
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ampel-Farbe bestimmen
    score = summary.health_score
    if score >= 80:
        color_class = "green"
        ampel_text = "Grün (gesund)"
    elif score >= 50:
        color_class = "yellow"
        ampel_text = "Gelb (teilweise gesund)"
    else:
        color_class = "red"
        ampel_text = "Rot (kritisch)"

    duration = (summary.finished_at - summary.started_at).total_seconds()

    # HTML-Template
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Health Report: {summary.profile_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .health-score {{
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .health-score.green {{ background-color: #d4edda; color: #155724; }}
        .health-score.yellow {{ background-color: #fff3cd; color: #856404; }}
        .health-score.red {{ background-color: #f8d7da; color: #721c24; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        .status-PASS {{ color: #28a745; font-weight: bold; }}
        .status-FAIL {{ color: #dc3545; font-weight: bold; }}
        .status-SKIPPED {{ color: #6c757d; font-weight: bold; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 14px;
        }}
        /* v1.1: Portfolio-Psychologie */
        .psychology-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .psychology-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            font-size: 18px;
        }}
        .psychology-CALM {{ background-color: #28a745; }}
        .psychology-MEDIUM {{ background-color: #ffc107; color: #333; }}
        .psychology-SPICY {{ background-color: #dc3545; }}
        .psychology-notes {{
            margin-top: 15px;
            padding-left: 20px;
        }}
        .psychology-notes li {{
            margin: 8px 0;
            color: #555;
        }}
        .psychology-metrics {{
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>🏥 Test Health Report: {summary.profile_name}</h1>
    
    <div class="health-score {color_class}">
        {summary.health_score:.1f} / 100.0
        <div style="font-size: 18px; margin-top: 10px;">{ampel_text}</div>
    </div>

    <div class="summary">
        <h2>Übersicht</h2>
        <p><strong>Profil:</strong> <code>{summary.profile_name}</code></p>
        <p><strong>Gestartet:</strong> {summary.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Beendet:</strong> {summary.finished_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Dauer:</strong> {duration:.1f}s</p>
        <hr>
        <p><strong>Passed Checks:</strong> {summary.passed_checks}</p>
        <p><strong>Failed Checks:</strong> {summary.failed_checks}</p>
        <p><strong>Skipped Checks:</strong> {summary.skipped_checks}</p>
        <p><strong>Passed Weight:</strong> {summary.passed_weight} / {summary.total_weight}</p>
    </div>
"""

    # v1.1: Portfolio-Psychologie (falls vorhanden)
    if summary.has_psychology():
        psych = summary.psychology
        notes_html = ""
        if psych.notes:
            notes_items = "".join(f"<li>{note}</li>" for note in psych.notes)
            notes_html = f"<ul class='psychology-notes'>{notes_items}</ul>"
        
        metrics_html = "<div class='psychology-metrics'><em>Basierend auf: "
        metrics_parts = []
        if psych.max_drawdown_pct is not None:
            metrics_parts.append(f"Max-DD: {psych.max_drawdown_pct:.1f}%")
        if psych.total_return_pct is not None:
            metrics_parts.append(f"Return: {psych.total_return_pct:+.1f}%")
        if psych.trades_count is not None:
            metrics_parts.append(f"Trades: {psych.trades_count}")
        metrics_html += ", ".join(metrics_parts) + "</em></div>"
        
        html += f"""
    <div class="psychology-section">
        <h2>{psych.level_emoji} Portfolio-Psychologie</h2>
        <span class="psychology-badge psychology-{psych.level}">{psych.level}</span>
        {notes_html}
        {metrics_html}
    </div>
"""

    html += """
    <h2>Check-Details</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Category</th>
                <th>Status</th>
                <th>Duration (s)</th>
                <th>Weight</th>
            </tr>
        </thead>
        <tbody>
"""

    for check in summary.checks:
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIPPED": "⏭️",
        }.get(check.status, "❓")

        html += f"""
            <tr>
                <td><code>{check.id}</code></td>
                <td>{check.name}</td>
                <td>{check.category}</td>
                <td class="status-{check.status}">{status_icon} {check.status}</td>
                <td>{check.duration_seconds:.2f}</td>
                <td>{check.weight}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>

    <div class="footer">
        <p>Generated by Peak_Trade Test Health Automation v0</p>
    </div>
</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ============================================================================
# Main Runner Function
# ============================================================================


def run_test_health_profile(
    profile_name: str,
    config_path: Path,
    report_root: Path,
    skip_strategy_coverage: bool = False,
    skip_switch_sanity: bool = False,
) -> tuple[TestHealthSummary, Path]:
    """
    Führt ein komplettes Test-Health-Profil aus und erzeugt Reports (v1).

    Parameters
    ----------
    profile_name : str
        Name des Profils (z.B. "weekly_core")
    config_path : Path
        Pfad zur test_health_profiles.toml
    report_root : Path
        Basis-Verzeichnis für Reports (z.B. reports/test_health)
    skip_strategy_coverage : bool
        v1: Strategy-Coverage überspringen (default: False)
    skip_switch_sanity : bool
        v1: Switch-Sanity überspringen (default: False)

    Returns
    -------
    tuple[TestHealthSummary, Path]
        (summary, report_directory)
    """
    # 1) Profil und Trigger-Config laden
    checks, triggers = load_test_health_profile(config_path, profile_name)

    # 2) Checks ausführen
    results = []
    for i, check in enumerate(checks, start=1):
        print(f"[{i}/{len(checks)}] Führe Check aus: {check.name} ({check.id})")
        result = run_single_check(check)
        results.append(result)
        status_icon = "✅" if result.status == "PASS" else "❌"
        print(
            f"         {status_icon} {result.status} "
            f"(Duration: {result.duration_seconds:.2f}s)"
        )

    # 3) Summary aggregieren
    summary = aggregate_health(profile_name, results)
    
    # 3b) Trigger-Evaluierung (basierend auf aktuellem Run + Historie)
    # Für jetzt: Stats aus aktuellem Run ableiten
    # TODO P2: Historie mit einbeziehen für längerfristige Trends
    stats = TestHealthStats(
        total_runs=1,  # Aktueller Run
        failed_runs=1 if summary.failed_checks > 0 else 0,
        max_consecutive_failures=1 if summary.failed_checks > 0 else 0,
        hours_since_last_run=None,  # Erster Run (Historie TODO)
        all_critical_groups_green=(summary.failed_checks == 0),
    )
    
    violations = evaluate_triggers(triggers, stats)
    summary.trigger_violations = violations
    
    if violations:
        print(f"\n⚠️  {len(violations)} Trigger-Violation(s) erkannt:")
        for v in violations:
            severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(
                v.severity, "?"
            )
            print(f"  {severity_icon} [{v.severity.upper()}] {v.message}")
    
    # v1: Strategy-Coverage-Check
    if not skip_strategy_coverage:
        try:
            coverage_cfg = load_strategy_coverage_config(config_path)
            if coverage_cfg.enabled:
                print("\n📊 Führe Strategy-Coverage-Check durch...")
                
                # Strategien bestimmen
                if coverage_cfg.link_to_strategy_switch_allowed:
                    sanity_cfg = load_switch_sanity_config(config_path)
                    strategy_ids = _load_allowed_strategies(
                        sanity_cfg.config_path, sanity_cfg.section_path
                    )
                else:
                    # Fallback: Alle bekannten Strategien
                    strategy_ids = []
                
                if strategy_ids:
                    coverage_result = compute_strategy_coverage(
                        coverage_cfg, strategy_ids
                    )
                    summary.strategy_coverage = coverage_result
                    
                    if coverage_result.is_healthy:
                        print(f"   ✅ Strategy Coverage OK ({coverage_result.strategies_checked} strategies)")
                    else:
                        print(f"   ❌ Strategy Coverage: {len(coverage_result.all_violations)} violation(s)")
                        for v in coverage_result.all_violations[:5]:
                            print(f"      - {v}")
                else:
                    print("   ⚠️  Keine Strategien zu prüfen (allowed list leer oder nicht gefunden)")
        except Exception as e:
            print(f"   ⚠️  Strategy-Coverage-Check fehlgeschlagen: {e}")
    
    # v1: Switch-Sanity-Check
    if not skip_switch_sanity:
        try:
            sanity_cfg = load_switch_sanity_config(config_path)
            if sanity_cfg.enabled:
                print("\n🔒 Führe Strategy-Switch Sanity Check durch...")
                sanity_result = run_switch_sanity_check(sanity_cfg)
                summary.switch_sanity = sanity_result
                
                if sanity_result.is_ok:
                    print(f"   ✅ Switch Sanity OK (active: {sanity_result.active_strategy_id})")
                else:
                    print(f"   ❌ Switch Sanity: {len(sanity_result.violations)} violation(s)")
                    for v in sanity_result.violations:
                        print(f"      - {v}")
        except Exception as e:
            print(f"   ⚠️  Switch-Sanity-Check fehlgeschlagen: {e}")

    # 4) Report-Verzeichnis erstellen
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = report_root / f"{timestamp}_{profile_name}"
    report_dir.mkdir(parents=True, exist_ok=True)

    # 5) Reports schreiben
    write_test_health_json(summary, report_dir / "summary.json")
    write_test_health_markdown(summary, report_dir / "summary.md")
    write_test_health_html(summary, report_dir / "summary.html")

    # 6) Historie aktualisieren
    try:
        from .test_health_history import append_to_history
        history_path = append_to_history(summary, report_dir)
        print(f"📊 Historie aktualisiert: {history_path}")
    except Exception as e:
        print(f"⚠️ Historie konnte nicht aktualisiert werden: {e}")
    
    # 7) Slack-Notification (falls konfiguriert und Failures vorhanden)
    _send_slack_notification_if_needed(
        config_path=config_path,
        summary=summary,
        report_dir=report_dir,
    )

    print(f"\n✅ Reports erzeugt: {report_dir}")

    return summary, report_dir


def _send_slack_notification_if_needed(
    config_path: Path, summary: TestHealthSummary, report_dir: Path
) -> None:
    """
    Sendet Slack-Notification falls konfiguriert und Bedingungen erfüllt (v1).
    
    Parameters
    ----------
    config_path : Path
        Pfad zur Config (für Slack-Settings)
    summary : TestHealthSummary
        Test-Health-Summary
    report_dir : Path
        Report-Verzeichnis
    """
    try:
        # Lade Slack-Config
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        
        slack_config = config.get("notifications", {}).get("slack", {})
        enabled = slack_config.get("enabled", False)
        
        if not enabled:
            return
        
        # Min-Severity prüfen
        min_severity = slack_config.get("min_severity", "warning")
        webhook_env_var = slack_config.get(
            "webhook_env_var", "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH"
        )
        include_strategy_coverage = slack_config.get("include_strategy_coverage", True)
        include_switch_sanity = slack_config.get("include_switch_sanity", True)
        
        # Entscheide ob Notification nötig
        should_notify = False
        
        # Notification bei Failed Checks
        if summary.failed_checks > 0:
            should_notify = True
        
        # Notification bei Trigger-Violations (severity >= min_severity)
        if summary.has_trigger_violations():
            severity_levels = {"info": 0, "warning": 1, "error": 2}
            min_level = severity_levels.get(min_severity, 1)
            
            for v in summary.trigger_violations:
                if severity_levels.get(v.severity, 0) >= min_level:
                    should_notify = True
                    break
        
        # v1: Notification bei Strategy-Coverage-Violations
        if summary.has_strategy_coverage_violations():
            should_notify = True
        
        # v1: Notification bei Switch-Sanity-Violations
        if summary.has_switch_sanity_violations():
            should_notify = True
        
        if not should_notify:
            return
        
        # v1: Erweiterte Slack-Nachricht bauen
        message = _build_slack_message_v1(
            summary=summary,
            report_dir=report_dir,
            include_strategy_coverage=include_strategy_coverage,
            include_switch_sanity=include_switch_sanity,
        )
        
        # Sende Notification
        from src.notifications.slack import send_test_health_slack_notification_v1
        
        send_test_health_slack_notification_v1(
            message=message,
            webhook_env_var=webhook_env_var,
        )
        
        print(f"📱 Slack-Notification versendet")
    
    except Exception as e:
        # Fail-safe: Slack-Fehler killen nicht die Pipeline
        print(f"⚠️  Slack-Notification fehlgeschlagen: {e}")


def _build_slack_message_v1(
    summary: TestHealthSummary,
    report_dir: Path,
    include_strategy_coverage: bool = True,
    include_switch_sanity: bool = True,
) -> str:
    """
    Baut eine Slack-Nachricht für TestHealth v1.
    
    Parameters
    ----------
    summary : TestHealthSummary
        Test-Health-Summary
    report_dir : Path
        Report-Verzeichnis
    include_strategy_coverage : bool
        Strategy-Coverage in Nachricht aufnehmen
    include_switch_sanity : bool
        Switch-Sanity in Nachricht aufnehmen
    
    Returns
    -------
    str
        Formatierte Slack-Nachricht
    """
    # Status-Emoji
    if summary.health_score >= 80 and not summary.has_any_violations():
        status_emoji = "🟢"
        status_text = "HEALTHY"
    elif summary.health_score >= 50:
        status_emoji = "🟡"
        status_text = "DEGRADED"
    else:
        status_emoji = "🔴"
        status_text = "FAILED"
    
    lines = [
        f"[Peak_Trade · TestHealth v1] Status: {status_text}",
        "",
        f"*Profile*: {summary.profile_name}",
        f"*Health Score*: {summary.health_score:.1f}/100",
        f"*Passed Checks*: {summary.passed_checks}",
        f"*Failed Checks*: {summary.failed_checks}",
    ]
    
    # Trigger-Violations
    if summary.has_trigger_violations():
        lines.extend([
            "",
            f"*Trigger Violations*: {len(summary.trigger_violations)}",
        ])
        for v in summary.trigger_violations[:3]:
            severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(
                v.severity, "?"
            )
            lines.append(f"  {severity_emoji} {v.message}")
        if len(summary.trigger_violations) > 3:
            lines.append(f"  ... und {len(summary.trigger_violations) - 3} weitere")
    
    # v1: Strategy-Coverage
    if include_strategy_coverage and summary.strategy_coverage:
        coverage = summary.strategy_coverage
        if coverage.enabled and not coverage.is_healthy:
            lines.extend([
                "",
                f"*Strategy Coverage* ({coverage.strategies_checked} checked):",
            ])
            for v in coverage.all_violations[:3]:
                lines.append(f"  ❌ {v}")
            if len(coverage.all_violations) > 3:
                lines.append(f"  ... und {len(coverage.all_violations) - 3} weitere")
    
    # v1: Switch-Sanity
    if include_switch_sanity and summary.switch_sanity:
        sanity = summary.switch_sanity
        if sanity.enabled and not sanity.is_ok:
            lines.extend([
                "",
                "*Switch Sanity Violations*:",
            ])
            for v in sanity.violations:
                lines.append(f"  ❌ {v}")
    
    # Report-Link
    lines.extend([
        "",
        f"*Report*: `{report_dir}`",
    ])
    
    return "\n".join(lines)

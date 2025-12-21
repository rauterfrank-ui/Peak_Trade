#!/usr/bin/env python3
"""
Peak_Trade Offline Daily Suite
================================

Tägliche Test-Suite für Peak_Trade – komplett offline, keine Live-Orders.

Jobs:
  1. Pytest-Run (schnelle Tests)
  2. OfflineSynthSession (klein: 1000 Steps)
  3. OfflineSynthSession (mittel: 5000 Steps)
  4. OfflineRealtimeFeed (Baseline: MA-Crossover)
  5. OfflineRealtimeFeed (R&D-Strategie)
  6. Trigger-Training Drill (mit Psychology-Heatmap)

Usage:
    python scripts/automation/run_offline_daily_suite.py
    python scripts/automation/run_offline_daily_suite.py --dry-run
    python scripts/automation/run_offline_daily_suite.py --no-pytest
    python scripts/automation/run_offline_daily_suite.py --only-trigger
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Python-Path anpassen für src-Import
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Imports für OfflineSynthSession & OfflineRealtimeFeed
from scripts.run_offline_realtime_ma_crossover import (
    OfflineSynthSessionConfig,
    run_offline_synth_session,
    OfflineRealtimeFeedConfig,
    OfflineRealtimeFeed,
    build_offline_ma_crossover_pipeline,
    run_pipeline as run_ma_crossover_pipeline,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Job Result Model
# =============================================================================


@dataclass
class JobResult:
    """Ergebnis eines einzelnen Jobs."""

    job_name: str
    status: str  # "ok", "failed", "skipped"
    duration_sec: float
    extra: Dict[str, Any] = field(default_factory=dict)
    error_msg: Optional[str] = None


@dataclass
class SuiteResult:
    """Ergebnis der gesamten Suite."""

    run_id: str
    run_type: str  # "daily_suite"
    started_at: datetime
    finished_at: datetime
    duration_sec: float
    jobs: List[JobResult]
    summary: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Job Implementations
# =============================================================================


def job_pytest_fast(dry_run: bool = False) -> JobResult:
    """
    Job 1: Pytest-Run (schnelle Tests).

    Führt Pytest mit `-q` (quiet) und optional einem Marker wie `-m "offline_fast"` aus.
    """
    job_name = "pytest_fast"
    logger.info(f"[JOB] {job_name}: Starting...")

    if dry_run:
        logger.info(f"[JOB] {job_name}: DRY-RUN – skipped")
        return JobResult(
            job_name=job_name,
            status="skipped",
            duration_sec=0.0,
            extra={"reason": "dry_run"},
        )

    start_time = time.perf_counter()

    try:
        # Pytest-Kommando (anpassen je nach vorhandenen Markern)
        # Versuche erst mit Marker, falls nicht vorhanden, ohne Marker
        result = subprocess.run(
            ["pytest", "-q", "-x", "--tb=short"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,  # 2 Minuten Timeout
        )

        duration = time.perf_counter() - start_time

        if result.returncode == 0:
            logger.info(f"[JOB] {job_name}: OK ({duration:.2f}s)")
            return JobResult(
                job_name=job_name,
                status="ok",
                duration_sec=duration,
                extra={
                    "returncode": result.returncode,
                    "stdout_lines": len(result.stdout.splitlines()),
                },
            )
        else:
            logger.warning(f"[JOB] {job_name}: FAILED (returncode={result.returncode})")
            return JobResult(
                job_name=job_name,
                status="failed",
                duration_sec=duration,
                extra={"returncode": result.returncode},
                error_msg=result.stderr[:500] if result.stderr else None,
            )

    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start_time
        logger.error(f"[JOB] {job_name}: TIMEOUT")
        return JobResult(
            job_name=job_name,
            status="failed",
            duration_sec=duration,
            error_msg="Pytest timeout after 120s",
        )

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.exception(f"[JOB] {job_name}: ERROR: {e}")
        return JobResult(
            job_name=job_name,
            status="failed",
            duration_sec=duration,
            error_msg=str(e),
        )


def job_offline_synth_session(
    n_steps: int,
    job_suffix: str = "",
    dry_run: bool = False,
) -> JobResult:
    """
    Job 2/3: OfflineSynthSession.

    Args:
        n_steps: Anzahl der Synth-Steps
        job_suffix: Suffix für Job-Name (z.B. "small", "medium")
        dry_run: Dry-Run-Modus
    """
    job_name = f"offline_synth_{job_suffix}" if job_suffix else f"offline_synth_{n_steps}"
    logger.info(f"[JOB] {job_name}: Starting (n_steps={n_steps})...")

    if dry_run:
        logger.info(f"[JOB] {job_name}: DRY-RUN – skipped")
        return JobResult(
            job_name=job_name,
            status="skipped",
            duration_sec=0.0,
            extra={"reason": "dry_run", "n_steps": n_steps},
        )

    start_time = time.perf_counter()

    try:
        config = OfflineSynthSessionConfig(
            n_steps=n_steps,
            n_regimes=3,
            seed=42,
        )

        result = run_offline_synth_session(
            config=config,
            symbol="BTCEUR",
        )

        duration = time.perf_counter() - start_time
        ticks_per_sec = n_steps / duration if duration > 0 else 0

        logger.info(f"[JOB] {job_name}: OK ({duration:.2f}s, {ticks_per_sec:.1f} ticks/s)")

        return JobResult(
            job_name=job_name,
            status="ok",
            duration_sec=duration,
            extra={
                "n_steps": n_steps,
                "n_regimes": config.n_regimes,
                "ticks_per_sec": round(ticks_per_sec, 2),
                "run_id": result.run_id,
            },
        )

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.exception(f"[JOB] {job_name}: ERROR: {e}")
        return JobResult(
            job_name=job_name,
            status="failed",
            duration_sec=duration,
            error_msg=str(e),
        )


def job_offline_realtime_feed(
    symbol: str,
    strategy_label: str,
    n_steps: int = 1000,
    fast_window: int = 20,
    slow_window: int = 50,
    dry_run: bool = False,
) -> JobResult:
    """
    Job 4/5: OfflineRealtimeFeed.

    Args:
        symbol: Trading-Symbol (z.B. "BTC/EUR")
        strategy_label: Label für die Strategie (z.B. "baseline", "r_and_d")
        n_steps: Anzahl der Synth-Steps
        fast_window: Fast-MA-Window
        slow_window: Slow-MA-Window
        dry_run: Dry-Run-Modus
    """
    job_name = f"offline_realtime_{strategy_label}"
    logger.info(
        f"[JOB] {job_name}: Starting (symbol={symbol}, fast={fast_window}, slow={slow_window})..."
    )

    if dry_run:
        logger.info(f"[JOB] {job_name}: DRY-RUN – skipped")
        return JobResult(
            job_name=job_name,
            status="skipped",
            duration_sec=0.0,
            extra={"reason": "dry_run", "symbol": symbol},
        )

    start_time = time.perf_counter()

    try:
        # Erstelle ein Namespace-Objekt wie bei argparse
        class Args:
            pass

        args = Args()
        args.symbol = symbol
        args.n_steps = n_steps
        args.n_regimes = 3
        args.seed = 42
        args.fast_window = fast_window
        args.slow_window = slow_window
        args.playback_mode = "fast_forward"
        args.speed_factor = 10.0
        args.output_dir = None

        # Pipeline bauen
        components = build_offline_ma_crossover_pipeline(args)

        # Pipeline ausführen
        perf_metrics = run_ma_crossover_pipeline(
            pipeline=components["pipeline"],
            strategy=components["strategy"],
            feed=components["feed"],
            symbol=components["internal_symbol"],
        )

        duration = time.perf_counter() - start_time

        logger.info(
            f"[JOB] {job_name}: OK ({duration:.2f}s, "
            f"{perf_metrics['n_orders']} orders, "
            f"{perf_metrics['n_trades']} trades)"
        )

        return JobResult(
            job_name=job_name,
            status="ok",
            duration_sec=duration,
            extra={
                "symbol": symbol,
                "strategy_label": strategy_label,
                "n_ticks": perf_metrics["n_ticks"],
                "n_orders": perf_metrics["n_orders"],
                "n_trades": perf_metrics["n_trades"],
                "net_pnl": round(perf_metrics["net_pnl"], 2),
                "run_id": components["run_id"],
            },
        )

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.exception(f"[JOB] {job_name}: ERROR: {e}")
        return JobResult(
            job_name=job_name,
            status="failed",
            duration_sec=duration,
            error_msg=str(e),
        )


def job_trigger_training_drill(dry_run: bool = False) -> JobResult:
    """
    Job 6: Trigger-Training Drill.

    Führt einen Trigger-Training-Drill aus und generiert:
    - Offline-Paper-Report
    - Trigger-Training-Report
    - Psychology-Heatmap
    """
    job_name = "trigger_training_drill"
    logger.info(f"[JOB] {job_name}: Starting...")

    if dry_run:
        logger.info(f"[JOB] {job_name}: DRY-RUN – skipped")
        return JobResult(
            job_name=job_name,
            status="skipped",
            duration_sec=0.0,
            extra={"reason": "dry_run"},
        )

    start_time = time.perf_counter()

    try:
        # Trigger-Training-Script als Subprocess ausführen
        session_id = f"DAILY_DRILL_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "run_offline_trigger_training_drill_example.py"),
                "--session-id",
                session_id,
                "--symbol",
                "BTCEUR",
                "--timeframe",
                "1m",
                "--environment",
                "offline_paper_trade",
                "--reports-dir",
                "reports/automation/daily/trigger_training",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,  # 5 Minuten Timeout
        )

        duration = time.perf_counter() - start_time

        # Parse Output für Stats (falls vorhanden)
        extra = {
            "session_id": session_id,
            "returncode": result.returncode,
        }

        # Versuche, Reaktionszeit-Stats aus dem Output zu extrahieren
        if "Total Signale:" in result.stdout:
            lines = result.stdout.splitlines()
            for line in lines:
                if "Total Signale:" in line:
                    extra["total_signals"] = int(line.split(":")[-1].strip())
                elif "Missed:" in line:
                    extra["missed_signals"] = int(line.split(":")[-1].strip())
                elif "Avg Reaktionszeit:" in line:
                    try:
                        extra["avg_reaction_ms"] = float(
                            line.split(":")[-1].replace("ms", "").strip()
                        )
                    except ValueError:
                        pass

        if result.returncode == 0:
            logger.info(f"[JOB] {job_name}: OK ({duration:.2f}s)")
            return JobResult(
                job_name=job_name,
                status="ok",
                duration_sec=duration,
                extra=extra,
            )
        else:
            logger.warning(f"[JOB] {job_name}: FAILED (returncode={result.returncode})")
            return JobResult(
                job_name=job_name,
                status="failed",
                duration_sec=duration,
                extra=extra,
                error_msg=result.stderr[:500] if result.stderr else None,
            )

    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start_time
        logger.error(f"[JOB] {job_name}: TIMEOUT")
        return JobResult(
            job_name=job_name,
            status="failed",
            duration_sec=duration,
            error_msg="Trigger-Training timeout after 300s",
        )

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.exception(f"[JOB] {job_name}: ERROR: {e}")
        return JobResult(
            job_name=job_name,
            status="failed",
            duration_sec=duration,
            error_msg=str(e),
        )


# =============================================================================
# Suite Runner
# =============================================================================


def run_daily_suite(args: argparse.Namespace) -> SuiteResult:
    """
    Führt die Daily-Suite aus.

    Args:
        args: CLI-Argumente

    Returns:
        SuiteResult mit allen Job-Ergebnissen
    """
    run_id = f"daily_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    started_at = datetime.now(timezone.utc)

    logger.info("=" * 80)
    logger.info("PEAK_TRADE OFFLINE DAILY SUITE")
    logger.info("=" * 80)
    logger.info(f"Run-ID: {run_id}")
    logger.info(f"Started: {started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"Dry-Run: {args.dry_run}")
    logger.info("=" * 80)

    # Job-Liste definieren
    jobs: List[JobResult] = []

    # Job 1: Pytest
    if not args.no_pytest and not args.only_trigger:
        jobs.append(job_pytest_fast(dry_run=args.dry_run))

    # Job 2: OfflineSynthSession (klein)
    if not args.only_trigger:
        jobs.append(
            job_offline_synth_session(
                n_steps=1000,
                job_suffix="small",
                dry_run=args.dry_run,
            )
        )

    # Job 3: OfflineSynthSession (mittel)
    if not args.only_trigger:
        jobs.append(
            job_offline_synth_session(
                n_steps=5000,
                job_suffix="medium",
                dry_run=args.dry_run,
            )
        )

    # Job 4: OfflineRealtimeFeed (Baseline)
    if not args.only_trigger:
        jobs.append(
            job_offline_realtime_feed(
                symbol="BTC/EUR",
                strategy_label="baseline",
                n_steps=1000,
                fast_window=20,
                slow_window=50,
                dry_run=args.dry_run,
            )
        )

    # Job 5: OfflineRealtimeFeed (R&D)
    if not args.only_trigger:
        jobs.append(
            job_offline_realtime_feed(
                symbol="BTC/EUR",
                strategy_label="r_and_d",
                n_steps=1000,
                fast_window=10,
                slow_window=30,
                dry_run=args.dry_run,
            )
        )

    # Job 6: Trigger-Training Drill
    if not args.no_trigger:
        jobs.append(job_trigger_training_drill(dry_run=args.dry_run))

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    # Summary erstellen
    summary = {
        "total_jobs": len(jobs),
        "jobs_ok": sum(1 for j in jobs if j.status == "ok"),
        "jobs_failed": sum(1 for j in jobs if j.status == "failed"),
        "jobs_skipped": sum(1 for j in jobs if j.status == "skipped"),
    }

    logger.info("=" * 80)
    logger.info("SUITE COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total Jobs: {summary['total_jobs']}")
    logger.info(f"  OK:       {summary['jobs_ok']}")
    logger.info(f"  Failed:   {summary['jobs_failed']}")
    logger.info(f"  Skipped:  {summary['jobs_skipped']}")
    logger.info(f"Duration: {duration:.2f}s")
    logger.info("=" * 80)

    return SuiteResult(
        run_id=run_id,
        run_type="daily_suite",
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=duration,
        jobs=jobs,
        summary=summary,
    )


def write_suite_log(result: SuiteResult, output_dir: Path) -> Path:
    """
    Schreibt ein JSON-Log für die Suite.

    Args:
        result: SuiteResult
        output_dir: Output-Verzeichnis

    Returns:
        Pfad zum JSON-Log
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    log_filename = f"automation_daily_{result.started_at.strftime('%Y%m%d_%H%M%S')}.json"
    log_path = output_dir / log_filename

    # Konvertiere zu Dict mit datetime-Serialisierung
    log_data = {
        "run_id": result.run_id,
        "run_type": result.run_type,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
        "duration_sec": result.duration_sec,
        "summary": result.summary,
        "jobs": [
            {
                "job_name": j.job_name,
                "status": j.status,
                "duration_sec": j.duration_sec,
                "extra": j.extra,
                "error_msg": j.error_msg,
            }
            for j in result.jobs
        ],
    }

    log_path.write_text(json.dumps(log_data, indent=2), encoding="utf-8")
    logger.info(f"[LOG] Suite-Log geschrieben: {log_path}")

    return log_path


# =============================================================================
# CLI Parser
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parsed CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Offline Daily Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard-Run (alle Jobs)
  python scripts/automation/run_offline_daily_suite.py

  # Dry-Run (nur anzeigen, was laufen würde)
  python scripts/automation/run_offline_daily_suite.py --dry-run

  # Ohne Pytest
  python scripts/automation/run_offline_daily_suite.py --no-pytest

  # Nur Trigger-Training
  python scripts/automation/run_offline_daily_suite.py --only-trigger
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-Run-Modus: Zeigt nur an, welche Jobs laufen würden",
    )

    parser.add_argument(
        "--no-pytest",
        action="store_true",
        help="Überspringt Pytest-Run",
    )

    parser.add_argument(
        "--no-trigger",
        action="store_true",
        help="Überspringt Trigger-Training-Drill",
    )

    parser.add_argument(
        "--only-trigger",
        action="store_true",
        help="Führt nur Trigger-Training-Drill aus (überspringt alle anderen Jobs)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output-Verzeichnis für Logs (Standard: reports/automation/daily)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Aktiviert verbose Logging",
    )

    return parser.parse_args()


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    """
    Main-Einstiegspunkt.

    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    args = parse_args()

    # Logging konfigurieren
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # Suite ausführen
        result = run_daily_suite(args)

        # Log schreiben
        if args.output_dir:
            output_dir = args.output_dir
        else:
            output_dir = project_root / "reports" / "automation" / "daily"

        log_path = write_suite_log(result, output_dir)

        logger.info(f"✓ Daily Suite abgeschlossen: {log_path}")

        # Exit-Code basierend auf Job-Ergebnissen
        if result.summary["jobs_failed"] > 0:
            logger.warning(f"⚠️  {result.summary['jobs_failed']} Job(s) failed")
            return 1

        return 0

    except Exception as e:
        logger.exception(f"[MAIN] Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

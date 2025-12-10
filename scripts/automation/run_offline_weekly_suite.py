#!/usr/bin/env python3
"""
Peak_Trade Offline Weekly Suite
=================================

Wöchentliche Test-Suite für Peak_Trade – komplett offline, keine Live-Orders.

Jobs:
  1. Lange OfflineSynthSession (20.000 Steps)
  2. OfflineRealtimeFeed (BTCEUR, Baseline)
  3. OfflineRealtimeFeed (BTCEUR, R&D)
  4. OfflineRealtimeFeed (BTCUSD, Baseline)
  5. OfflineRealtimeFeed (ETHEUR, Baseline)
  6. Trigger-Training Drill (FOMO-Szenario)
  7. Trigger-Training Drill (Overtrading-Szenario)
  8. Trigger-Training Drill (Freeze-Szenario)

Usage:
    python scripts/automation/run_offline_weekly_suite.py
    python scripts/automation/run_offline_weekly_suite.py --dry-run
    python scripts/automation/run_offline_weekly_suite.py --quick-mode
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Python-Path anpassen für src-Import
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Imports für OfflineSynthSession & OfflineRealtimeFeed
from scripts.run_offline_realtime_ma_crossover import (
    OfflineSynthSessionConfig,
    run_offline_synth_session,
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
    run_type: str  # "weekly_suite"
    started_at: datetime
    finished_at: datetime
    duration_sec: float
    jobs: List[JobResult]
    summary: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Job Implementations
# =============================================================================

def job_offline_synth_session_long(dry_run: bool = False) -> JobResult:
    """
    Job 1: Lange OfflineSynthSession (20.000 Steps).
    """
    job_name = "offline_synth_long"
    n_steps = 20000
    
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
            n_regimes=5,
            seed=42,
        )
        
        result = run_offline_synth_session(
            config=config,
            symbol="BTCEUR",
        )
        
        duration = time.perf_counter() - start_time
        ticks_per_sec = n_steps / duration if duration > 0 else 0
        
        logger.info(
            f"[JOB] {job_name}: OK ({duration:.2f}s, "
            f"{ticks_per_sec:.1f} ticks/s)"
        )
        
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
    n_steps: int = 2000,
    fast_window: int = 20,
    slow_window: int = 50,
    dry_run: bool = False,
) -> JobResult:
    """
    Job 2-5: OfflineRealtimeFeed für verschiedene Symbole/Strategien.
    """
    job_name = f"offline_realtime_{symbol.replace('/', '').lower()}_{strategy_label}"
    logger.info(
        f"[JOB] {job_name}: Starting (symbol={symbol}, "
        f"fast={fast_window}, slow={slow_window})..."
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


def job_trigger_training_drill(
    scenario_label: str,
    dry_run: bool = False,
) -> JobResult:
    """
    Job 6-8: Trigger-Training Drill für verschiedene Szenarien.
    
    Args:
        scenario_label: Label für das Szenario (z.B. "fomo", "overtrading", "freeze")
        dry_run: Dry-Run-Modus
    """
    job_name = f"trigger_training_{scenario_label}"
    logger.info(f"[JOB] {job_name}: Starting...")
    
    if dry_run:
        logger.info(f"[JOB] {job_name}: DRY-RUN – skipped")
        return JobResult(
            job_name=job_name,
            status="skipped",
            duration_sec=0.0,
            extra={"reason": "dry_run", "scenario": scenario_label},
        )
    
    start_time = time.perf_counter()
    
    try:
        # Trigger-Training-Script als Subprocess ausführen
        session_id = f"WEEKLY_DRILL_{scenario_label.upper()}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / "scripts" / "run_offline_trigger_training_drill_example.py"),
                "--session-id", session_id,
                "--symbol", "BTCEUR",
                "--timeframe", "1m",
                "--environment", "offline_paper_trade",
                "--reports-dir", f"reports/automation/weekly/trigger_training_{scenario_label}",
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
            "scenario": scenario_label,
            "returncode": result.returncode,
        }
        
        # Versuche, Reaktionszeit-Stats aus dem Output zu extrahieren
        if "Total Signale:" in result.stdout:
            lines = result.stdout.splitlines()
            for line in lines:
                if "Total Signale:" in line:
                    try:
                        extra["total_signals"] = int(line.split(":")[-1].strip())
                    except ValueError:
                        pass
                elif "Missed:" in line:
                    try:
                        extra["missed_signals"] = int(line.split(":")[-1].strip())
                    except ValueError:
                        pass
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

def run_weekly_suite(args: argparse.Namespace) -> SuiteResult:
    """
    Führt die Weekly-Suite aus.
    
    Args:
        args: CLI-Argumente
    
    Returns:
        SuiteResult mit allen Job-Ergebnissen
    """
    run_id = f"weekly_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    started_at = datetime.now(timezone.utc)
    
    logger.info("=" * 80)
    logger.info("PEAK_TRADE OFFLINE WEEKLY SUITE")
    logger.info("=" * 80)
    logger.info(f"Run-ID: {run_id}")
    logger.info(f"Started: {started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"Dry-Run: {args.dry_run}")
    logger.info(f"Quick-Mode: {args.quick_mode}")
    logger.info("=" * 80)
    
    # Job-Liste definieren
    jobs: List[JobResult] = []
    
    # Job 1: Lange OfflineSynthSession
    jobs.append(job_offline_synth_session_long(dry_run=args.dry_run))
    
    # Jobs 2-5: OfflineRealtimeFeed für verschiedene Symbole
    symbols = [
        ("BTC/EUR", "baseline", 20, 50),
        ("BTC/EUR", "r_and_d", 10, 30),
        ("BTC/USD", "baseline", 20, 50),
        ("ETH/EUR", "baseline", 15, 40),
    ]
    
    if args.quick_mode:
        # Im Quick-Mode nur BTCEUR
        symbols = [("BTC/EUR", "baseline", 20, 50)]
    
    for symbol, strategy_label, fast_window, slow_window in symbols:
        jobs.append(
            job_offline_realtime_feed(
                symbol=symbol,
                strategy_label=strategy_label,
                n_steps=2000,
                fast_window=fast_window,
                slow_window=slow_window,
                dry_run=args.dry_run,
            )
        )
    
    # Jobs 6-8: Trigger-Training Drills für verschiedene Szenarien
    scenarios = ["fomo", "overtrading", "freeze"]
    
    if args.quick_mode:
        # Im Quick-Mode nur ein Szenario
        scenarios = ["fomo"]
    
    for scenario in scenarios:
        jobs.append(job_trigger_training_drill(scenario, dry_run=args.dry_run))
    
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
    logger.info(f"Duration: {duration:.2f}s ({duration / 60:.1f} min)")
    logger.info("=" * 80)
    
    return SuiteResult(
        run_id=run_id,
        run_type="weekly_suite",
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
    
    log_filename = f"automation_weekly_{result.started_at.strftime('%Y%m%d_%H%M%S')}.json"
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


def write_suite_summary_markdown(result: SuiteResult, output_dir: Path) -> Path:
    """
    Schreibt eine Markdown-Zusammenfassung für die Suite.
    
    Args:
        result: SuiteResult
        output_dir: Output-Verzeichnis
    
    Returns:
        Pfad zur Markdown-Datei
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    md_filename = f"automation_weekly_{result.started_at.strftime('%Y%m%d_%H%M%S')}.md"
    md_path = output_dir / md_filename
    
    # Markdown-Content erstellen
    md_lines = [
        f"# Peak_Trade Weekly Suite – {result.started_at.strftime('%Y-%m-%d')}",
        "",
        f"**Run-ID**: `{result.run_id}`",
        f"**Started**: {result.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Finished**: {result.finished_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Duration**: {result.duration_sec:.2f}s ({result.duration_sec / 60:.1f} min)",
        "",
        "## 📊 Summary",
        "",
        f"- **Total Jobs**: {result.summary['total_jobs']}",
        f"- **OK**: {result.summary['jobs_ok']} ✅",
        f"- **Failed**: {result.summary['jobs_failed']} ❌",
        f"- **Skipped**: {result.summary['jobs_skipped']} ⏭️",
        "",
        "## 📋 Jobs",
        "",
        "| Job | Status | Duration | Details |",
        "|-----|--------|----------|---------|",
    ]
    
    for job in result.jobs:
        status_emoji = "✅" if job.status == "ok" else "❌" if job.status == "failed" else "⏭️"
        duration_str = f"{job.duration_sec:.2f}s"
        
        # Details aus extra zusammenstellen
        details = []
        if "n_steps" in job.extra:
            details.append(f"Steps: {job.extra['n_steps']:,}")
        if "ticks_per_sec" in job.extra:
            details.append(f"Ticks/s: {job.extra['ticks_per_sec']:.1f}")
        if "n_orders" in job.extra:
            details.append(f"Orders: {job.extra['n_orders']}")
        if "n_trades" in job.extra:
            details.append(f"Trades: {job.extra['n_trades']}")
        if "net_pnl" in job.extra:
            details.append(f"PnL: {job.extra['net_pnl']:.2f}")
        if "total_signals" in job.extra:
            details.append(f"Signals: {job.extra['total_signals']}")
        if "missed_signals" in job.extra:
            details.append(f"Missed: {job.extra['missed_signals']}")
        if "avg_reaction_ms" in job.extra:
            details.append(f"Avg Reaction: {job.extra['avg_reaction_ms']:.1f}ms")
        
        details_str = ", ".join(details) if details else "-"
        
        md_lines.append(
            f"| `{job.job_name}` | {status_emoji} {job.status} | {duration_str} | {details_str} |"
        )
    
    md_lines.extend([
        "",
        "## 🎯 Key Metrics",
        "",
    ])
    
    # Aggregiere Metriken
    total_ticks = sum(j.extra.get("n_ticks", 0) for j in result.jobs)
    total_orders = sum(j.extra.get("n_orders", 0) for j in result.jobs)
    total_trades = sum(j.extra.get("n_trades", 0) for j in result.jobs)
    total_signals = sum(j.extra.get("total_signals", 0) for j in result.jobs)
    total_missed = sum(j.extra.get("missed_signals", 0) for j in result.jobs)
    
    md_lines.extend([
        f"- **Total Ticks verarbeitet**: {total_ticks:,}",
        f"- **Total Orders**: {total_orders}",
        f"- **Total Trades**: {total_trades}",
        f"- **Total Signale**: {total_signals}",
        f"- **Total Missed**: {total_missed}",
    ])
    
    if total_signals > 0:
        missed_rate = (total_missed / total_signals) * 100
        md_lines.append(f"- **Missed Trigger Rate**: {missed_rate:.1f}%")
    
    md_lines.extend([
        "",
        "---",
        "",
        f"*Generated by Peak_Trade Automation – {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
    ])
    
    md_content = "\n".join(md_lines)
    md_path.write_text(md_content, encoding="utf-8")
    logger.info(f"[SUMMARY] Markdown-Summary geschrieben: {md_path}")
    
    return md_path


# =============================================================================
# CLI Parser
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parsed CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Offline Weekly Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard-Run (alle Jobs)
  python scripts/automation/run_offline_weekly_suite.py
  
  # Dry-Run (nur anzeigen, was laufen würde)
  python scripts/automation/run_offline_weekly_suite.py --dry-run
  
  # Quick-Mode (weniger Jobs für schnellere Ausführung)
  python scripts/automation/run_offline_weekly_suite.py --quick-mode
        """,
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-Run-Modus: Zeigt nur an, welche Jobs laufen würden",
    )
    
    parser.add_argument(
        "--quick-mode",
        action="store_true",
        help="Quick-Mode: Weniger Jobs für schnellere Ausführung",
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output-Verzeichnis für Logs (Standard: reports/automation/weekly)",
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
        result = run_weekly_suite(args)
        
        # Output-Verzeichnis bestimmen
        if args.output_dir:
            output_dir = args.output_dir
        else:
            output_dir = project_root / "reports" / "automation" / "weekly"
        
        # JSON-Log schreiben
        log_path = write_suite_log(result, output_dir)
        
        # Markdown-Summary schreiben
        md_path = write_suite_summary_markdown(result, output_dir)
        
        logger.info("=" * 80)
        logger.info("✓ Weekly Suite abgeschlossen")
        logger.info(f"  JSON-Log: {log_path}")
        logger.info(f"  Summary:  {md_path}")
        logger.info("=" * 80)
        
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

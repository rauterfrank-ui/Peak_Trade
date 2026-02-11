#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peak_Trade: Unified Sweep Pipeline CLI
======================================

Ein einziges CLI für den Sweep-Workflow: --run | --report | --promote.
Artefakte werden unter out/research/<sweep_id>/ abgelegt.
Idempotent: Neuer run_id pro Aufruf, sofern nicht --sweep-id gesetzt.

Verwendung:
    # Alle Schritte (run → report → promote)
    python scripts/run_sweep_pipeline.py --sweep-name rsi_reversion_basic --run --report --promote

    # Nur Sweep ausführen
    python scripts/run_sweep_pipeline.py --sweep-name rsi_reversion_basic --run

    # Report aus bestehendem Sweep-Output
    python scripts/run_sweep_pipeline.py --sweep-name rsi_reversion_basic --sweep-id my_run --report

    # Mit fester sweep-id (idempotent: gleicher Ordner bei erneutem Aufruf)
    python scripts/run_sweep_pipeline.py --sweep-id my_sweep_001 --sweep-name rsi_reversion_basic --run --report --promote

Siehe auch: docs/ops/runbooks/RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md (Block A).
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Projekt-Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESEARCH_BASE = PROJECT_ROOT / "out" / "research"
SCRIPTS = PROJECT_ROOT / "scripts"

LOG = logging.getLogger(__name__)


def _ensure_sweep_id(sweep_id: Optional[str], sweep_name: str) -> str:
    """Erzeugt sweep_id falls nicht gesetzt (timestamp-basiert)."""
    if sweep_id:
        return sweep_id
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{sweep_name}_{ts}"


def _artifact_dir(sweep_id: str) -> Path:
    """Basis-Artefaktverzeichnis für diesen Sweep."""
    d = RESEARCH_BASE / sweep_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Führt Kommando aus, gibt Exit-Code zurück."""
    env = {"PYTHONPATH": str(PROJECT_ROOT)}
    r = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        env={**__import__("os").environ, **env},
    )
    return r.returncode


def _do_run(sweep_name: str, sweep_id: str, config: str, verbose: bool) -> int:
    """Führt Strategy-Sweep aus, schreibt nach out/research/<sweep_id>/sweep/."""
    out = _artifact_dir(sweep_id) / "sweep"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(SCRIPTS / "research_cli.py"),
        "sweep",
        "--sweep-name",
        sweep_name,
        "--config",
        config,
        "--output-dir",
        str(out),
    ]
    if verbose:
        cmd.append("--verbose")
    LOG.info("run_sweep_pipeline: executing sweep -> %s", out)
    return _run_cmd(cmd)


def _latest_sweep_csv(sweep_dir: Path, sweep_name: str) -> Optional[Path]:
    """Findet die neueste Sweep-CSV im Verzeichnis."""
    if not sweep_dir.exists():
        return None
    candidates = list(sweep_dir.glob(f"{sweep_name}_*.csv"))
    if not candidates:
        candidates = list(sweep_dir.glob("*.csv"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _do_report(
    sweep_name: str,
    sweep_id: str,
    config: str,
    top_n: int,
    with_plots: bool,
    verbose: bool,
) -> int:
    """Generiert Report aus Sweep-Ergebnissen in out/research/<sweep_id>/sweep/."""
    sweep_dir = _artifact_dir(sweep_id) / "sweep"
    input_csv = _latest_sweep_csv(sweep_dir, sweep_name)
    if not input_csv or not input_csv.exists():
        LOG.error("No sweep results found under %s for sweep_name=%s", sweep_dir, sweep_name)
        return 1
    out = _artifact_dir(sweep_id) / "report"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(SCRIPTS / "research_cli.py"),
        "report",
        "--input",
        str(input_csv),
        "--output-dir",
        str(out),
        "--format",
        "both",
        "--top-n",
        str(top_n),
    ]
    if with_plots:
        cmd.append("--with-plots")
    if verbose:
        cmd.append("--verbose")
    LOG.info("run_sweep_pipeline: generating report -> %s (input: %s)", out, input_csv)
    return _run_cmd(cmd)


def _do_promote(
    sweep_name: str,
    sweep_id: str,
    config: str,
    top_n: int,
    verbose: bool,
) -> int:
    """Promotet Top-N aus Sweep-Ergebnissen; Output nach out/research/<sweep_id>/promote/."""
    sweep_dir = _artifact_dir(sweep_id) / "sweep"
    experiments_dir = str(sweep_dir)
    out_dir = _artifact_dir(sweep_id) / "promote"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(SCRIPTS / "research_cli.py"),
        "promote",
        "--sweep-name",
        sweep_name,
        "--top-n",
        str(top_n),
        "--output",
        str(out_dir),
        "--experiments-dir",
        experiments_dir,
    ]
    if verbose:
        cmd.append("--verbose")
    LOG.info("run_sweep_pipeline: promote -> %s", out_dir)
    return _run_cmd(cmd)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_sweep_pipeline",
        description="Unified Sweep Pipeline: run → report → promote with artifacts under out/research/<sweep_id>/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--sweep-name",
        "-s",
        type=str,
        required=True,
        help="Name des Sweeps (z.B. rsi_reversion_basic)",
    )
    p.add_argument(
        "--sweep-id",
        type=str,
        default=None,
        help="Optionale feste Run-ID. Ohne Angabe: auto (sweep_name_timestamp)",
    )
    p.add_argument(
        "--run",
        action="store_true",
        help="Sweep ausführen",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Report aus Sweep-Ergebnissen erzeugen",
    )
    p.add_argument(
        "--promote",
        action="store_true",
        help="Top-N in Registry/Presets promoten",
    )
    p.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config (default: config/config.toml)",
    )
    p.add_argument(
        "--top-n",
        "-n",
        type=int,
        default=5,
        help="Top-N für Report und Promotion (default: 5)",
    )
    p.add_argument(
        "--with-plots",
        action="store_true",
        help="Report mit Plots/Heatmaps erzeugen",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose Logging",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = _build_parser().parse_args(argv)
    if not (args.run or args.report or args.promote):
        # Default: alle drei
        args.run = args.report = args.promote = True
    sweep_id = _ensure_sweep_id(args.sweep_id, args.sweep_name)
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
    LOG.info("sweep_id=%s artifact_base=%s", sweep_id, _artifact_dir(sweep_id))

    if args.run:
        rc = _do_run(args.sweep_name, sweep_id, args.config, args.verbose)
        if rc != 0:
            return rc
    if args.report:
        rc = _do_report(
            args.sweep_name,
            sweep_id,
            args.config,
            args.top_n,
            args.with_plots,
            args.verbose,
        )
        if rc != 0:
            return rc
    if args.promote:
        rc = _do_promote(args.sweep_name, sweep_id, args.config, args.top_n, args.verbose)
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())

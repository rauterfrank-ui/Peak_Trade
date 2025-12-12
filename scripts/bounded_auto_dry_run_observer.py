#!/usr/bin/env python3
"""
bounded_auto Dry-Run Observer (POC v0)
======================================

Proof-of-concept observer for bounded_auto learning promotion system.

This POC performs data quality checks on sweep outputs and determines
whether the sweep data is suitable for bounded_auto promotion decisions.

Key Features:
- Data quality gate: checks for trade count variance
- Heuristic-based usability assessment
- Does NOT execute actual bounded_auto learning (future work)
- Outputs structured decision artifacts

Usage:
    python scripts/bounded_auto_dry_run_observer.py \\
        --sweep-dir reports/experiments \\
        --min-trades 10

Example Output:
    - summary.json: Structured decision data
    - summary.md: Human-readable report
    - Status: SUCCESS | BLOCKED
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ObserverRun:
    """Results of a bounded_auto observer run."""
    run_ts: str
    sweep_dir: str
    baseline_stdout_log: Optional[str]
    snapshot_dir: Optional[str]
    status: str  # SUCCESS | BLOCKED | FAILED
    block_reason: Optional[str]
    recommendation: str  # PROMOTE | BASELINE_ONLY | NO_PROMOTION
    trade_count_stats: Dict[str, Any]
    outputs: Dict[str, str]
    notes: List[str]


def analyze_sweep_trade_counts(sweep_dir: Path, min_trades: int) -> Dict[str, Any]:
    """
    Analyze trade counts from sweep JSON summaries.

    Args:
        sweep_dir: Path to sweep data directory
        min_trades: Minimum trade count to consider a run "usable"

    Returns:
        Dict with trade count statistics and usability assessment
    """
    trade_counts = []
    files_analyzed = 0

    # Recursively find all JSON files that might contain trade counts
    for json_file in sweep_dir.rglob("*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            continue

        files_analyzed += 1

        # Try multiple possible keys for trade count
        for key in ("trade_count", "num_trades", "trades", "fills", "orders"):
            if key in obj and isinstance(obj[key], (int, float)):
                trade_counts.append(int(obj[key]))
                break

    if not trade_counts:
        return {
            "files_analyzed": files_analyzed,
            "trade_counts_found": 0,
            "min": None,
            "max": None,
            "mean": None,
            "variance": None,
            "usable_runs": 0,
            "usable_pct": 0.0,
            "is_usable": False,
        }

    usable_runs = sum(1 for tc in trade_counts if tc >= min_trades)
    usable_pct = (usable_runs / len(trade_counts)) * 100 if trade_counts else 0.0

    # Calculate variance
    mean_tc = sum(trade_counts) / len(trade_counts)
    variance = sum((tc - mean_tc) ** 2 for tc in trade_counts) / len(trade_counts)

    return {
        "files_analyzed": files_analyzed,
        "trade_counts_found": len(trade_counts),
        "min": min(trade_counts),
        "max": max(trade_counts),
        "mean": round(mean_tc, 2),
        "variance": round(variance, 2),
        "usable_runs": usable_runs,
        "usable_pct": round(usable_pct, 1),
        "is_usable": usable_runs >= 10 and variance > 0,  # At least 10 usable runs with variance
        "unique_counts": len(set(trade_counts)),
    }


def main() -> int:
    """Main entry point for bounded_auto observer."""
    parser = argparse.ArgumentParser(
        description="bounded_auto dry-run observer (POC v0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--sweep-dir",
        type=Path,
        default=Path("reports/sweeps"),
        help="Path to sweep data directory (default: reports/sweeps)",
    )
    parser.add_argument(
        "--baseline-stdout-log",
        type=Path,
        default=None,
        help="Path to baseline builder stdout log (optional)",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=None,
        help="Path to sweep snapshot directory (optional)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("reports/bounded_auto_real_runs"),
        help="Output directory (default: reports/bounded_auto_real_runs)",
    )
    parser.add_argument(
        "--min-trades",
        type=int,
        default=10,
        help="Minimum trade count to consider a run usable (default: 10)",
    )
    args = parser.parse_args()

    # Create run timestamp and output directory
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out_dir)
    out_run = out_root / f"{run_ts}_REAL_SWEEP_RUN_002"
    out_run.mkdir(parents=True, exist_ok=True)

    print(f"[bounded_auto observer] POC v0")
    print(f"[sweep_dir] {args.sweep_dir}")
    print(f"[out_dir] {out_run}")
    print()

    # Analyze trade counts from sweep data
    print("[1/3] Analyzing sweep trade counts...")
    trade_stats = analyze_sweep_trade_counts(args.sweep_dir, args.min_trades)

    print(f"  Files analyzed: {trade_stats['files_analyzed']}")
    print(f"  Trade counts found: {trade_stats['trade_counts_found']}")

    if trade_stats['trade_counts_found'] > 0:
        print(f"  Trade count range: {trade_stats['min']} - {trade_stats['max']}")
        print(f"  Mean: {trade_stats['mean']}, Variance: {trade_stats['variance']}")
        print(f"  Unique counts: {trade_stats['unique_counts']}")
        print(f"  Usable runs (≥{args.min_trades} trades): {trade_stats['usable_runs']} ({trade_stats['usable_pct']}%)")
    print()

    # Determine status and recommendation
    print("[2/3] Data quality assessment...")

    is_usable = trade_stats.get("is_usable", False)
    status = "SUCCESS" if is_usable else "BLOCKED"
    block_reason = None

    if not is_usable:
        if trade_stats['trade_counts_found'] == 0:
            block_reason = "No trade_count metrics found in sweep data"
        elif trade_stats['variance'] == 0:
            block_reason = f"Zero variance in trade counts (all runs identical: {trade_stats['min']} trades)"
        elif trade_stats['usable_runs'] < 10:
            block_reason = f"Insufficient usable runs: {trade_stats['usable_runs']} < 10"
        else:
            block_reason = "Data quality checks failed"

    recommendation = "BASELINE_ONLY" if is_usable else "NO_PROMOTION"

    print(f"  Status: {status}")
    if block_reason:
        print(f"  Block reason: {block_reason}")
    print(f"  Recommendation: {recommendation}")
    print()

    # Create notes
    notes = [
        "POC observer v0: data quality gate only",
        "Does NOT execute actual bounded_auto learning (future work)",
        "If BLOCKED: fix parameter wiring and regenerate sweeps",
        "If SUCCESS: baseline recommendation can proceed to live candidate pool",
        "Next: integrate bounded_auto triggers and learning signals",
    ]

    # Create run summary
    run = ObserverRun(
        run_ts=run_ts,
        sweep_dir=str(args.sweep_dir.resolve()),
        baseline_stdout_log=str(args.baseline_stdout_log.resolve()) if args.baseline_stdout_log else None,
        snapshot_dir=str(args.snapshot_dir.resolve()) if args.snapshot_dir else None,
        status=status,
        block_reason=block_reason,
        recommendation=recommendation,
        trade_count_stats=trade_stats,
        outputs={
            "run_dir": str(out_run),
            "summary_json": str(out_run / "summary.json"),
            "summary_md": str(out_run / "summary.md"),
        },
        notes=notes,
    )

    # Write JSON summary
    print("[3/3] Writing outputs...")
    summary_json = out_run / "summary.json"
    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(asdict(run), f, indent=2)
    print(f"  ✓ {summary_json}")

    # Write Markdown summary
    md_lines = [
        "# bounded_auto Dry-Run Observer · REAL_SWEEP_RUN_002 (POC v0)",
        "",
        f"**Run TS:** `{run_ts}`  ",
        f"**Status:** `{status}`  ",
        f"**Recommendation:** `{recommendation}`  ",
        "",
        "---",
        "",
        "## Inputs",
        "",
        f"- **Sweep dir:** `{args.sweep_dir}`",
        f"- **Snapshot dir:** `{args.snapshot_dir or 'N/A'}`",
        f"- **Baseline stdout log:** `{args.baseline_stdout_log or 'N/A'}`",
        "",
        "## Trade Count Analysis",
        "",
        f"- Files analyzed: {trade_stats['files_analyzed']}",
        f"- Trade counts found: {trade_stats['trade_counts_found']}",
    ]

    if trade_stats['trade_counts_found'] > 0:
        md_lines.extend([
            f"- Range: {trade_stats['min']} - {trade_stats['max']}",
            f"- Mean: {trade_stats['mean']}",
            f"- Variance: {trade_stats['variance']}",
            f"- Unique counts: {trade_stats['unique_counts']}",
            f"- Usable runs (≥{args.min_trades} trades): {trade_stats['usable_runs']} ({trade_stats['usable_pct']}%)",
        ])

    md_lines.extend([
        "",
        "## Decision",
        "",
        f"**Status:** {status}",
    ])

    if block_reason:
        md_lines.append(f"**Block reason:** {block_reason}")

    md_lines.extend([
        "",
        f"**Recommendation:** {recommendation}",
        "",
        "## Notes",
        "",
    ])

    for note in notes:
        md_lines.append(f"- {note}")

    md_lines.extend([
        "",
        "---",
        "",
        f"*Generated by bounded_auto observer POC v0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    summary_md = out_run / "summary.md"
    with summary_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"  ✓ {summary_md}")
    print()

    # Final verdict
    if status == "SUCCESS":
        print("✅ [SUCCESS] Sweep data quality sufficient for baseline promotion")
        return 0
    else:
        print(f"❌ [BLOCKED] {block_reason}")
        print("   → See CALIBRATION_ISSUES_REPORT_v0.md for fix plan")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

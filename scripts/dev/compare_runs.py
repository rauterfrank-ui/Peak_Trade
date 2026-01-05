#!/usr/bin/env python3
"""
Compare Runs CLI Tool
=====================

Fast, local comparison of experiment runs.
Works without MLflow by reading run_summary.json files.

Examples:
    # Compare latest 10 runs
    python scripts/dev/compare_runs.py --n 10

    # Compare runs with baseline
    python scripts/dev/compare_runs.py --baseline abc123 --candidate def456

    # Output as JSON
    python scripts/dev/compare_runs.py --format json

    # Use custom results directory
    python scripts/dev/compare_runs.py --dir /path/to/results
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from experiments.tracking.run_summary import RunSummary

logger = logging.getLogger(__name__)


def find_summary_files(
    results_dir: Path,
    n: Optional[int] = None,
) -> List[Path]:
    """
    Find run summary JSON files in results directory.

    Args:
        results_dir: Directory containing run_summary_*.json files
        n: Maximum number of files to return (most recent)

    Returns:
        List of paths to summary files, sorted by modification time (newest first)
    """
    if not results_dir.exists():
        logger.warning(f"Results directory not found: {results_dir}")
        return []

    # Find all run_summary_*.json files
    summary_files = list(results_dir.glob("run_summary_*.json"))

    # Sort by modification time (newest first)
    summary_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Limit to n most recent
    if n is not None:
        summary_files = summary_files[:n]

    return summary_files


def load_summaries(paths: List[Path]) -> List[RunSummary]:
    """
    Load RunSummary objects from files.

    Args:
        paths: List of paths to summary JSON files

    Returns:
        List of RunSummary objects (skips invalid files)
    """
    summaries = []

    for path in paths:
        try:
            summary = RunSummary.read_json(path)
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")

    return summaries


def format_table(summaries: List[RunSummary], key_metrics: Optional[List[str]] = None) -> str:
    """
    Format summaries as ASCII table.

    Args:
        summaries: List of RunSummary objects
        key_metrics: List of metric keys to display (default: all)

    Returns:
        Formatted table string
    """
    if not summaries:
        return "No runs found."

    # Determine which metrics to show
    if key_metrics is None:
        # Collect all unique metric keys
        all_metrics = set()
        for s in summaries:
            all_metrics.update(s.metrics.keys())
        key_metrics = sorted(all_metrics)

    # Build rows
    rows = []
    header = ["run_id", "started_at", "status", "git_sha", "worktree", "backend"]
    header.extend(key_metrics)

    for s in summaries:
        row = [
            s.run_id[:8],  # Short ID
            s.started_at_utc[:19],  # Date + time without fractional seconds
            s.status,
            (s.git_sha[:8] if s.git_sha else "-"),
            (s.worktree if s.worktree else "-"),
            s.tracking_backend,
        ]

        # Add metrics
        for metric_key in key_metrics:
            value = s.metrics.get(metric_key)
            if value is not None:
                row.append(f"{value:.4f}")
            else:
                row.append("-")

        rows.append(row)

    # Calculate column widths
    col_widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Format table
    lines = []

    # Header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(header, col_widths))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        lines.append(row_line)

    return "\n".join(lines)


def format_diff(
    baseline: RunSummary,
    candidate: RunSummary,
) -> str:
    """
    Format diff between two runs.

    Args:
        baseline: Baseline run
        candidate: Candidate run

    Returns:
        Formatted diff string
    """
    lines = []
    lines.append(f"Baseline:  {baseline.run_id} ({baseline.started_at_utc})")
    lines.append(f"Candidate: {candidate.run_id} ({candidate.started_at_utc})")
    lines.append("")

    # Status diff
    if baseline.status != candidate.status:
        lines.append(f"Status: {baseline.status} -> {candidate.status}")
        lines.append("")

    # Git diff
    if baseline.git_sha != candidate.git_sha:
        lines.append("Git:")
        lines.append(f"  Baseline:  {baseline.git_sha}")
        lines.append(f"  Candidate: {candidate.git_sha}")
        lines.append("")

    # Params diff
    all_param_keys = set(baseline.params.keys()) | set(candidate.params.keys())
    changed_params = []

    for key in sorted(all_param_keys):
        base_val = baseline.params.get(key, "-")
        cand_val = candidate.params.get(key, "-")
        if base_val != cand_val:
            changed_params.append((key, base_val, cand_val))

    if changed_params:
        lines.append("Changed Parameters:")
        for key, base_val, cand_val in changed_params:
            lines.append(f"  {key}: {base_val} -> {cand_val}")
        lines.append("")

    # Metrics diff
    all_metric_keys = set(baseline.metrics.keys()) | set(candidate.metrics.keys())
    changed_metrics = []

    for key in sorted(all_metric_keys):
        base_val = baseline.metrics.get(key)
        cand_val = candidate.metrics.get(key)

        if base_val is not None and cand_val is not None:
            diff = cand_val - base_val
            pct_change = (diff / abs(base_val) * 100) if base_val != 0 else float("inf")
            changed_metrics.append((key, base_val, cand_val, diff, pct_change))
        elif base_val != cand_val:
            # One is None
            changed_metrics.append((key, base_val, cand_val, None, None))

    if changed_metrics:
        lines.append("Metrics:")
        lines.append(
            f"  {'Metric':<20} {'Baseline':<15} {'Candidate':<15} {'Diff':<15} {'% Change':<10}"
        )
        lines.append("  " + "-" * 75)

        for item in changed_metrics:
            key = item[0]
            base_val = item[1]
            cand_val = item[2]
            diff = item[3]
            pct = item[4]

            base_str = f"{base_val:.4f}" if base_val is not None else "-"
            cand_str = f"{cand_val:.4f}" if cand_val is not None else "-"

            if diff is not None and pct is not None:
                diff_str = f"{diff:+.4f}"
                pct_str = f"{pct:+.2f}%"
            else:
                diff_str = "-"
                pct_str = "-"

            lines.append(f"  {key:<20} {base_str:<15} {cand_str:<15} {diff_str:<15} {pct_str:<10}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare Peak Trade experiment runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of recent runs to display (default: 10)",
    )

    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("results"),
        help="Results directory (default: results/)",
    )

    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "--baseline",
        help="Baseline run ID for diff mode",
    )

    parser.add_argument(
        "--candidate",
        help="Candidate run ID for diff mode",
    )

    parser.add_argument(
        "--metrics",
        nargs="+",
        help="Specific metrics to display (default: all)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Diff mode
    if args.baseline and args.candidate:
        # Find the specific runs
        baseline_path = args.dir / f"run_summary_{args.baseline}.json"
        candidate_path = args.dir / f"run_summary_{args.candidate}.json"

        if not baseline_path.exists():
            # Try to find by prefix
            matches = list(args.dir.glob(f"run_summary_{args.baseline}*.json"))
            if matches:
                baseline_path = matches[0]
            else:
                print(f"Error: Baseline run not found: {args.baseline}", file=sys.stderr)
                return 1

        if not candidate_path.exists():
            # Try to find by prefix
            matches = list(args.dir.glob(f"run_summary_{args.candidate}*.json"))
            if matches:
                candidate_path = matches[0]
            else:
                print(f"Error: Candidate run not found: {args.candidate}", file=sys.stderr)
                return 1

        try:
            baseline = RunSummary.read_json(baseline_path)
            candidate = RunSummary.read_json(candidate_path)

            print(format_diff(baseline, candidate))
            return 0

        except Exception as e:
            print(f"Error loading runs: {e}", file=sys.stderr)
            return 1

    # List mode
    summary_files = find_summary_files(args.dir, n=args.n)

    if not summary_files:
        print(f"No run summaries found in {args.dir}", file=sys.stderr)
        return 1

    summaries = load_summaries(summary_files)

    if not summaries:
        print("No valid run summaries loaded", file=sys.stderr)
        return 1

    # Output
    if args.format == "table":
        print(format_table(summaries, key_metrics=args.metrics))
    elif args.format == "json":
        output = [s.to_json_dict() for s in summaries]
        print(json.dumps(output, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())

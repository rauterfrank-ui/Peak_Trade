#!/usr/bin/env python3
"""
Offline Package M — EXPERIMENT LineageRef producer from explicit manifest directory.

Produces a validated, deterministic EXPERIMENT LineageRef JSON artifact only.
No experiment start, backtest start, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_experiment_lineage_ref_producer_v1.py \\
        --manifest-dir reports/experiments/identity-run-001 \\
        --output reports/lineage_refs/experiment_run-001.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    ExperimentLineageRefProducerError,
    produce_experiment_lineage_ref_v1_to_path,
)

EXIT_OK = 0
EXIT_PRODUCER_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package M EXPERIMENT LineageRef producer: explicit manifest "
            "directory to validated reference-only JSON artifact."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        required=True,
        help=("Explicit path to a directory containing experiment_identity_manifest_v1.json."),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination path for the validated EXPERIMENT LineageRef JSON file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = produce_experiment_lineage_ref_v1_to_path(
            manifest_dir=args.manifest_dir,
            output_path=args.output,
            fail_closed_if_exists=True,
        )
    except ExperimentLineageRefProducerError as exc:
        print(f"[experiment_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR
    except OSError as exc:
        print(f"[experiment_lineage_ref] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR

    print(
        "[experiment_lineage_ref] wrote validated EXPERIMENT LineageRef to "
        f"{args.output} (ref_id={result.ref.ref_id}, digest={result.ref.digest})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
